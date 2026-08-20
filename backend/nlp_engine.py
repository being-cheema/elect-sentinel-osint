"""
NLP & Disinformation Detection Engine for ELECT-SENTINEL OSINT.
Analyzes election-related text for confusion patterns, categories, threat velocity,
epistemic uncertainty, bot characteristics, and sentiment.
"""

import re
import math
from typing import Dict, Any, List, Tuple

# Comprehensive flexible linguistic pattern dictionaries
PATTERNS = {
    "voter_suppression": [
        r"\b(polls?|polling stations?|voting locations?)\b.{0,25}\b(closed? early|shut down|locked out|closure|delayed)\b",
        r"\b(voting date|election date)\b.{0,25}\b(moved|postponed|cancelled|tomorrow|rescheduled|next week)\b",
        r"\b(pay fee|digital barcode|special barcode|barcode fee|fee to vote|poll tax|registration cancelled|suspended status)\b",
        r"\b(leave the line|turn around|locked doors|not allowed to vote|provisional discarded)\b",
        r"\b(vote by text|vote via sms|vote online via|vote via app)\b",
        r"\b(ice agents|border patrol|warrants? check|police checkpoint)\b.{0,25}\b(polling|precinct|outside polls)\b"
    ],
    "integrity_tampering": [
        r"\b(voting machines?|tabulators?|scanners?|dominion|smartmatic)\b.{0,30}\b(rigged|glitch|switch(ing|ed)? votes?|flipped|hacked|cellular modems?|connected to internet|wifi)\b",
        r"\b(suitcases? of ballots|dumpster ballots|shredded ballots|fake water pipe|midnight stoppage|unmarked vans)\b",
        r"\b(stolen flash drives?|counterfeit ballots|watermark on ballots|tampering with machines?)\b",
        r"\b(algorithm flip|calibration hack|switching votes|flip votes|remote access open)\b",
        r"\b(ballot stuffing|fake ballots dropped|dead people voting)\b"
    ],
    "synthetic_deepfake": [
        r"\b(deepfake|ai generated|cloned voice|ai audio|synthetic speech|doctored video|faked video|ai hologram)\b",
        r"\b(secret recording|leaked audio|leaked video|hot mic)\b.{0,30}\b(concession|drops? out|admits defeat|postponed)\b"
    ],
    "impersonation": [
        r"\b(official election notice|verify your ballot at|voter status suspended|fec emergency bulletin|state election commission official text)\b",
        r"\b(re-register now|submit ssn to vote|confirm vote via link|click here to verify)\b"
    ],
    "premature_results": [
        r"\b(race called for|landslide declared|100% precincts reporting|victory declared already|refuse to concede)\b",
        r"\b(counting halted|counting stopped|unmarked white vans|dumped in dumpster)\b"
    ],
    "voter_intimidation": [
        r"\b(armed watchers|blockade outside|patrolling polling|surrounding the precinct|photographing license plates)\b",
        r"\b(militia monitoring|warning to voters in|intimidation at precinct|confronting voters)\b"
    ]
}

UNCERTAINTY_PATTERNS = [
    r"\b(heard from a friend|insider told me|secret source|unverified but|whistleblower claims|they don't want you to know|before they delete this|spread this before it's taken down|rumor has it|someone on telegram said|supposedly|allegedly|they are hiding)\b"
]

URGENCY_PATTERNS = [
    r"\b(breaking|urgent|emergency|alert|share immediately|retweet fast|do not ignore|warning|critical update|must see|share now|red alert|pass it on|demand a paper ballot)\b",
    r"(!{2,}|\?{2,}|\b[A-Z]{4,}\b)"
]

SENTIMENT_POLARITY_WORDS = {
    "negative": ["fraud", "steal", "stolen", "corrupt", "rigged", "illegal", "threat", "chaos", "panic", "destroyed", "disaster", "scam", "shame", "treason", "fake", "glitch", "hack", "tamper"],
    "positive": ["secure", "fair", "smooth", "certified", "record turnout", "verified", "protected", "bipartisan", "transparent", "accurate", "official", "peaceful"]
}


def clean_text(text: str) -> str:
    """Normalize and clean input text."""
    if not text:
        return ""
    cleaned = re.sub(r'http\S+|www\.\S+', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def analyze_text(text: str, author_handle: str = "", author_followers: int = 100,
                 author_age_days: int = 365, platform: str = "twitter") -> Dict[str, Any]:
    """
    Performs comprehensive OSINT NLP analysis on raw text.
    Returns category, confusion score (0-100), urgency, epistemic uncertainty,
    sentiment, bot probability, priority, and forensic markers.
    """
    raw_lower = text.lower()
    cleaned = clean_text(text)
    
    # 1. Category Classification & Match Weights
    category_scores = {}
    matched_markers = []
    
    for category, regex_list in PATTERNS.items():
        score = 0
        for regex in regex_list:
            matches = re.finditer(regex, raw_lower)
            for m in matches:
                matched_str = m.group(0)
                score += 40
                matched_markers.append(f"[{category}] {matched_str}")
        category_scores[category] = score

    # Determine highest scored category
    top_category = "legitimate_news"
    max_cat_score = 0
    for cat, score in category_scores.items():
        if score > max_cat_score:
            max_cat_score = score
            top_category = cat

    # 2. Epistemic Uncertainty & Rumor Multiplier
    uncertainty_score = 0.0
    for pattern in UNCERTAINTY_PATTERNS:
        matches = re.findall(pattern, raw_lower)
        if matches:
            uncertainty_score = min(1.0, uncertainty_score + len(matches) * 0.35)

    # 3. Urgency & Outrage Score
    urgency_score = 0.0
    for pattern in URGENCY_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            urgency_score = min(1.0, urgency_score + len(matches) * 0.30)

    # 4. Sentiment Polarity
    neg_count = sum(1 for word in SENTIMENT_POLARITY_WORDS["negative"] if word in raw_lower)
    pos_count = sum(1 for word in SENTIMENT_POLARITY_WORDS["positive"] if word in raw_lower)
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    # 5. Bot & Inauthentic Swarm Probability
    bot_score = 0.0
    # New accounts (< 30 days) have higher risk
    if author_age_days < 30:
        bot_score += 0.35
    elif author_age_days < 90:
        bot_score += 0.15
        
    # Low follower ratio with aggressive posting
    if author_followers < 15:
        bot_score += 0.20
        
    # Handle pattern: name followed by 4+ numbers (typical default bot pattern)
    if re.search(r'@[A-Za-z]+[0-9]{4,}', author_handle):
        bot_score += 0.30

    # High uppercase character ratio (screaming copypasta)
    caps_count = sum(1 for c in text if c.isupper())
    if len(text) > 20 and (caps_count / len(text)) > 0.25:
        bot_score += 0.15

    bot_probability = round(min(0.99, max(0.02, bot_score)), 2)

    # 6. Composite Confusion Score (0.0 to 100.0)
    if top_category == "legitimate_news":
        base_confusion = 5.0 + (uncertainty_score * 15.0)
    else:
        base_confusion = 55.0 + min(35.0, max_cat_score * 0.75)

    # Platform modifier
    platform_weights = {
        "4chan": 1.25,
        "telegram": 1.20,
        "tiktok": 1.15,
        "twitter": 1.10,
        "reddit": 1.0,
        "facebook": 1.05,
        "bluesky": 0.95,
        "news": 0.65
    }
    plat_mod = platform_weights.get(platform.lower(), 1.0)

    # Calculate final composite confusion index
    raw_confusion = (
        (base_confusion * 0.60) +
        (urgency_score * 20.0) +
        (uncertainty_score * 20.0) +
        (bot_probability * 15.0)
    ) * plat_mod

    confusion_score = round(min(99.5, max(1.0, raw_confusion)), 1)

    # 7. Priority Determination
    if confusion_score >= 75.0 or (confusion_score >= 60.0 and bot_probability > 0.5):
        priority = "P0"
    elif confusion_score >= 50.0:
        priority = "P1"
    elif confusion_score >= 25.0:
        priority = "P2"
    else:
        priority = "P3"

    # 8. Forensic Markers Summary
    return {
        "cleaned_text": cleaned,
        "category": top_category,
        "confusion_score": confusion_score,
        "urgency_score": round(urgency_score, 2),
        "epistemic_uncertainty": round(uncertainty_score, 2),
        "sentiment": sentiment,
        "bot_probability": bot_probability,
        "priority": priority,
        "matched_markers": matched_markers
    }
