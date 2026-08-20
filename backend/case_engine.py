"""
Case Management & Intelligence Dossier Generator for ELECT-SENTINEL OSINT.
Enables analysts to package flagged disinformation narratives, digital evidence,
and actor networks into formal Intelligence Briefings.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.database import get_db


def create_case(title: str, narrative_ids: List[str], post_ids: List[str],
                threat_level: str = "high", analyst: str = "Lead OSINT Analyst",
                executive_summary: str = "", recommended_action: str = "") -> str:
    """Creates a new analyst case dossier."""
    conn = get_db()
    cursor = conn.cursor()
    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
    INSERT INTO cases 
    (id, title, narrative_ids, post_ids, threat_level, analyst, status,
     executive_summary, recommended_action, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
    """, (
        case_id, title, json.dumps(narrative_ids), json.dumps(post_ids),
        threat_level, analyst, executive_summary, recommended_action, now, now
    ))

    conn.commit()
    conn.close()
    return case_id


def get_all_cases() -> List[Dict[str, Any]]:
    """Retrieves all cases with details."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()

    cases = []
    for r in rows:
        item = dict(r)
        item["narrative_ids"] = json.loads(item["narrative_ids"])
        item["post_ids"] = json.loads(item["post_ids"])
        cases.append(item)
    return cases


def generate_intelligence_report(case_id: str) -> Dict[str, Any]:
    """
    Synthesizes a full, publication-ready OSINT Intelligence Briefing
    with executive summary, propagation timeline, forensic SHA-256 evidence,
    and counter-messaging recommendations.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    case_row = cursor.fetchone()
    
    if not case_row:
        conn.close()
        return {"error": "Case not found"}

    case = dict(case_row)
    narrative_ids = json.loads(case["narrative_ids"])
    post_ids = json.loads(case["post_ids"])

    # Retrieve associated narratives
    narratives = []
    for n_id in narrative_ids:
        cursor.execute("SELECT * FROM narratives WHERE id = ?", (n_id,))
        n_row = cursor.fetchone()
        if n_row:
            n_data = dict(n_row)
            n_data["platforms_involved"] = json.loads(n_data["platforms_involved"])
            n_data["keywords"] = json.loads(n_data["keywords"])
            narratives.append(n_data)

    # Retrieve associated posts & evidence
    posts = []
    if post_ids:
        placeholders = ','.join(['?'] * len(post_ids))
        cursor.execute(f"SELECT * FROM posts WHERE id IN ({placeholders}) ORDER BY timestamp ASC", post_ids)
        posts = [dict(p) for p in cursor.fetchall()]
    elif narrative_ids:
        placeholders = ','.join(['?'] * len(narrative_ids))
        cursor.execute(f"SELECT * FROM posts WHERE narrative_id IN ({placeholders}) ORDER BY timestamp ASC LIMIT 25", narrative_ids)
        posts = [dict(p) for p in cursor.fetchall()]

    conn.close()

    # Calculate aggregate intelligence metrics
    mean_confusion = round(sum(p["confusion_score"] for p in posts) / len(posts), 1) if posts else 0.0
    bot_percentage = round((sum(1 for p in posts if (p["bot_probability"] or 0) > 0.5) / len(posts)) * 100, 1) if posts else 0.0
    platforms = list(set(p["source_platform"] for p in posts))
    districts = list(set(p["location_district"] for p in posts if p["location_district"] != "National"))

    # Generate Markdown Report Content
    md_report = f"""# ELECTION THREAT INTELLIGENCE BRIEFING: {case['title']}
**Document Reference:** {case['id']}  
**Classification:** RESTRICTED // LAW ENFORCEMENT & ELECTION SECURITY OVERSIGHT  
**Date Generated:** {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}  
**Lead Analyst:** {case['analyst']}  
**Overall Threat Assessment:** {case['threat_level'].upper()} (Confusion Index: {mean_confusion}/100)

---

## 1. Executive Threat Summary
{case['executive_summary'] or 'This intelligence brief documents an active, multi-channel election disinformation narrative exhibiting characteristics of coordinated inauthentic amplification, factual contradiction with statutory voting rules, and potential voter disenfranchisement.'}

- **Primary Vector / Category:** {narratives[0]['category'].replace('_', ' ').title() if narratives else 'Voter Confusion'}
- **Platforms Impacted:** {', '.join([p.upper() for p in platforms]) if platforms else 'Cross-Platform'}
- **Focal Jurisdictions:** {', '.join(districts) if districts else 'National Scope'}
- **Inauthentic / Bot Participation:** {bot_percentage}% of sampled accounts

---

## 2. Tracked Narrative Clusters & Lifecycle State
"""

    for n in narratives:
        md_report += f"""### [{n['id']}] {n['title']}
- **Lifecycle Stage:** `{n['lifecycle'].upper()}` | **Total Volume:** {n['total_volume']} posts | **Velocity:** {n['velocity']} posts/hr
- **Platforms:** {', '.join(n['platforms_involved'])}
- **Keywords / Anchors:** {', '.join(n['keywords'])}
- **Summary:** {n['summary']}

"""

    md_report += """---

## 3. Ground Truth Verification & Contradiction Analysis
"""
    contradiction_found = False
    for p in posts:
        if p["contradiction_flag"]:
            contradiction_found = True
            md_report += f"""- **Contradiction Detected in Post [{p['id']}]:** {p['contradiction_detail']}  
  *Debunk Directive:* Reiterate verified standards via official state secretary of state communication channels.
"""
    if not contradiction_found:
        md_report += "No statutory contradictions logged; narrative relies primarily on speculative uncertainty and emotional urgency triggers.\n"

    md_report += f"""
---

## 4. Digital Forensics & Chain of Custody (Sampled Posts)

| Post ID | Platform | Author | Confusion | Bot Prob | Timestamp | Evidence SHA-256 Hash |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
"""
    for p in posts[:10]:
        md_report += f"| `{p['id']}` | {p['source_platform'].title()} | `{p['author_handle']}` | {p['confusion_score']} | {p['bot_probability']} | {p['timestamp'][:19]} | `{p['sha256_hash'][:16]}...` |\n"

    md_report += f"""
---

## 5. Recommended Counter-Disinformation Actions
{case['recommended_action'] or '''1. **Rapid Counter-Messaging:** Deploy official fact cards across affected social platforms clarifying exact polling hours and certified air-gapped equipment protocols.
2. **Platform Trust & Safety Escalation:** Request expedited review of identified automated bot clusters exhibiting coordinated copypasta.
3. **Field Observer Notice:** Alert precinct judges in target jurisdictions to expect voter inquiries regarding the debunked rumor.'''}

---
*Report synthesized autonomously by ELECT-SENTINEL OSINT Intelligence Platform.*
"""

    return {
        "case_id": case_id,
        "title": case["title"],
        "threat_level": case["threat_level"],
        "analyst": case["analyst"],
        "mean_confusion": mean_confusion,
        "bot_percentage": bot_percentage,
        "platforms": platforms,
        "districts": districts,
        "narratives": narratives,
        "post_count": len(posts),
        "markdown_report": md_report
    }
