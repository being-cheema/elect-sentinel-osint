"""
Dynamic Narrative & Topic Clustering Engine for ELECT-SENTINEL OSINT.
Groups incoming posts into cohesive storylines, tracks narrative lifecycles
(Emerging -> Accelerating -> Critical Peak -> Debunked -> Dormant),
and extracts key entities and cross-platform spread metrics.
"""

import json
import sqlite3
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.database import get_db

STOP_WORDS = set([
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by",
    "is", "are", "was", "were", "be", "this", "that", "it", "from", "as", "have",
    "has", "had", "they", "we", "you", "i", "he", "she", "but", "not", "what", "all"
])


def extract_top_keywords(texts: List[str], top_n: int = 5) -> List[str]:
    """Extracts top representative keywords using TF-IDF."""
    if not texts:
        return []
    try:
        tfidf = TfidfVectorizer(max_features=50, stop_words='english', ngram_range=(1, 2))
        matrix = tfidf.fit_transform(texts)
        feature_names = tfidf.get_feature_names_out()
        sums = matrix.sum(axis=0).A1
        top_indices = sums.argsort()[::-1][:top_n]
        return [feature_names[i] for i in top_indices]
    except Exception:
        # Fallback to frequency count
        words = []
        for t in texts:
            for w in re.findall(r'\b[a-zA-Z]{4,}\b', t.lower()):
                if w not in STOP_WORDS:
                    words.append(w)
        from collections import Counter
        return [w for w, _ in Counter(words).most_common(top_n)]


def find_or_create_narrative(post_text: str, category: str, platform: str,
                             confusion_score: float, timestamp: str) -> str:
    """
    Matches an incoming post against active narratives using TF-IDF cosine similarity.
    If similarity > 0.35, attaches to existing narrative; otherwise creates a new narrative.
    Returns the narrative_id.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Retrieve active narratives within the same or broad category
    cursor.execute("""
    SELECT id, title, summary, category, total_volume, platforms_involved, keywords
    FROM narratives 
    WHERE lifecycle != 'dormant'
    """)
    narrative_rows = cursor.fetchall()

    best_narrative_id = None
    highest_similarity = 0.0

    if narrative_rows:
        narratives = [dict(r) for r in narrative_rows]
        # Query representative posts for each narrative
        for narr in narratives:
            n_id = narr["id"]
            cursor.execute("SELECT text FROM posts WHERE narrative_id = ? LIMIT 10", (n_id,))
            n_posts = [row["text"] for row in cursor.fetchall()]
            if not n_posts:
                n_posts = [narr["title"] + " " + (narr["summary"] or "")]

            corpus = [" ".join(n_posts), post_text]
            try:
                tfidf = TfidfVectorizer(stop_words='english')
                tfidf_matrix = tfidf.fit_transform(corpus)
                sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                if sim > highest_similarity:
                    highest_similarity = sim
                    best_narrative_id = n_id
            except Exception:
                pass

    # Threshold for matching existing narrative
    if highest_similarity >= 0.28 and best_narrative_id:
        narrative_id = best_narrative_id
        update_narrative_stats(conn, narrative_id, platform, confusion_score, timestamp)
    else:
        # Create a new narrative
        narrative_id = create_new_narrative(conn, post_text, category, platform, confusion_score, timestamp)

    conn.commit()
    conn.close()
    return narrative_id


def create_new_narrative(conn, post_text: str, category: str, platform: str,
                         confusion_score: float, timestamp: str) -> str:
    """Creates a new tracked narrative storyline."""
    import uuid
    cursor = conn.cursor()
    n_id = f"NAR-{datetime.now().strftime('%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    
    # Generate representative title from text
    title_words = [w for w in re.findall(r'\b[A-Za-z0-9\-\']+\b', post_text) if len(w) > 3 and w.lower() not in STOP_WORDS]
    if title_words:
        title = " ".join(title_words[:6]).title()
    else:
        title = f"Emerging {category.replace('_', ' ').title()} Signal"

    summary = post_text[:180] + "..." if len(post_text) > 180 else post_text
    keywords = json.dumps(extract_top_keywords([post_text], top_n=4))
    platforms = json.dumps([platform])

    cursor.execute("""
    INSERT INTO narratives 
    (id, title, summary, category, lifecycle, confusion_index, total_volume, velocity,
     first_spotted, last_activity, origin_platform, platforms_involved, keywords, debunk_response)
    VALUES (?, ?, ?, ?, 'emerging', ?, 1, 1.0, ?, ?, ?, ?, ?, '')
    """, (n_id, title, summary, category, confusion_score, timestamp, timestamp, platform, platforms, keywords))

    return n_id


def update_narrative_stats(conn, narrative_id: str, platform: str,
                           confusion_score: float, timestamp: str):
    """Updates volume, platforms, confusion index, and lifecycle of a narrative."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM narratives WHERE id = ?", (narrative_id,))
    row = cursor.fetchone()
    if not row:
        return

    total_vol = row["total_volume"] + 1
    current_conf = row["confusion_index"]
    new_conf = round(((current_conf * row["total_volume"]) + confusion_score) / total_vol, 1)

    platforms = json.loads(row["platforms_involved"])
    if platform not in platforms:
        platforms.append(platform)

    # Determine Lifecycle
    # Emerging -> Accelerating -> Critical Peak -> Debunked
    current_lifecycle = row["lifecycle"]
    new_lifecycle = current_lifecycle

    if current_lifecycle != "debunked":
        if total_vol >= 15 or (len(platforms) >= 3 and total_vol >= 8):
            new_lifecycle = "critical_peak"
        elif total_vol >= 4 or len(platforms) >= 2:
            new_lifecycle = "accelerating"
        else:
            new_lifecycle = "emerging"

    velocity = round(total_vol * 1.85, 1)

    cursor.execute("""
    UPDATE narratives
    SET total_volume = ?,
        confusion_index = ?,
        platforms_involved = ?,
        velocity = ?,
        last_activity = ?,
        lifecycle = ?
    WHERE id = ?
    """, (total_vol, new_conf, json.dumps(platforms), velocity, timestamp, new_lifecycle, narrative_id))


def get_all_narratives() -> List[Dict[str, Any]]:
    """Fetches all narratives with computed metrics and sample posts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM narratives ORDER BY total_volume DESC, velocity DESC")
    rows = cursor.fetchall()
    
    narratives = []
    for r in rows:
        item = dict(r)
        item["platforms_involved"] = json.loads(item["platforms_involved"])
        item["keywords"] = json.loads(item["keywords"])
        
        # Get sample post count and recent snippets
        cursor.execute("SELECT author_handle, text, source_platform, confusion_score FROM posts WHERE narrative_id = ? ORDER BY timestamp DESC LIMIT 3", (item["id"],))
        item["sample_posts"] = [dict(p) for p in cursor.fetchall()]
        narratives.append(item)

    conn.close()
    return narratives
