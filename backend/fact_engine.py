"""
Official Ground Truth & Contradiction Detection Engine for ELECT-SENTINEL OSINT.
Cross-verifies incoming online claims against official election regulations,
polling rules, and voting security protocols to automatically detect contradictions
and synthesize counter-messaging evidence notes.
"""

import sqlite3
import re
from typing import Dict, Any, List, Optional
from backend.database import get_db


def get_all_ground_truth() -> List[Dict[str, Any]]:
    """Retrieve all official ground truth records."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ground_truth_facts ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_ground_truth(category: str, topic: str, official_rule: str,
                     jurisdiction: str, verification_source: str,
                     debunk_template: str) -> str:
    """Add a new official rule into ground truth knowledge base."""
    import uuid
    from datetime import datetime, timezone
    conn = get_db()
    cursor = conn.cursor()
    new_id = f"GT-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO ground_truth_facts 
    (id, category, topic, official_rule, jurisdiction, verification_source, debunk_template, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (new_id, category, topic, official_rule, jurisdiction, verification_source, debunk_template, now))
    conn.commit()
    conn.close()
    return new_id


def check_contradiction(text: str, category: str) -> Dict[str, Any]:
    """
    Checks if a given post directly contradicts verified election facts.
    Returns contradiction flag, matched fact ID, rule summary, and debunk rebuttal.
    """
    text_lower = text.lower()
    conn = get_db()
    cursor = conn.cursor()
    
    # Query relevant facts
    if category != "legitimate_news":
        cursor.execute("SELECT * FROM ground_truth_facts WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM ground_truth_facts")
    facts = cursor.fetchall()
    conn.close()

    # Heuristic contradiction detectors
    for fact in facts:
        f_id = fact["id"]
        topic = fact["topic"]
        rule = fact["official_rule"]
        debunk = fact["debunk_template"]
        source = fact["verification_source"]
        
        # Rule 1: Polling hours
        if "closing" in topic.lower() or "hours" in topic.lower():
            if re.search(r"\b(closed early|close at \d|shut down at \d|leave the line|not allowed to vote if in line)\b", text_lower):
                return {
                    "contradicts": True,
                    "fact_id": f_id,
                    "topic": topic,
                    "official_rule": rule,
                    "verification_source": source,
                    "debunk_text": debunk,
                    "contradiction_reason": "Claim alleges early poll closures or disenfranchisement of in-line voters, which violates federal voting standards."
                }
                
        # Rule 2: ID & Fee requirements
        if "identification" in topic.lower() or "id" in topic.lower():
            if re.search(r"\b(special barcode|fee to vote|digital pass required|pay \$|mandatory qr card)\b", text_lower):
                return {
                    "contradicts": True,
                    "fact_id": f_id,
                    "topic": topic,
                    "official_rule": rule,
                    "verification_source": source,
                    "debunk_text": debunk,
                    "contradiction_reason": "Claim introduces fictitious paid card or digital barcode prerequisite designed to suppress turnout."
                }

        # Rule 3: Machine internet connection & tampering
        if "machine" in topic.lower() or "air-gap" in topic.lower() or "security" in topic.lower():
            if re.search(r"\b(connected to internet|wifi connected|cellular modem in|hacked remotely|algorithm switched)\b", text_lower):
                return {
                    "contradicts": True,
                    "fact_id": f_id,
                    "topic": topic,
                    "official_rule": rule,
                    "verification_source": source,
                    "debunk_text": debunk,
                    "contradiction_reason": "Claim asserts voting machines are connected to internet, contradicting certified air-gap hardware mandates."
                }

        # Rule 4: Election date change / postponement
        if "election date" in topic.lower() or "candidate status" in topic.lower():
            if re.search(r"\b(election postponed|date moved|vote wednesday|vote tomorrow|election cancelled)\b", text_lower):
                return {
                    "contradicts": True,
                    "fact_id": f_id,
                    "topic": topic,
                    "official_rule": rule,
                    "verification_source": source,
                    "debunk_text": debunk,
                    "contradiction_reason": "Claim purports election date change, which is unconstitutional and federally fixed by statute."
                }

        # Rule 5: Drop box / Maricopa county
        if "drop box" in topic.lower() or "maricopa" in topic.lower():
            if re.search(r"\b(drop boxes removed|all drop boxes sealed|boxes destroyed in maricopa)\b", text_lower):
                return {
                    "contradicts": True,
                    "fact_id": f_id,
                    "topic": topic,
                    "official_rule": rule,
                    "verification_source": source,
                    "debunk_text": debunk,
                    "contradiction_reason": "Claim falsifies status of official 24/7 video-monitored county drop box locations."
                }

    # If general high-risk keywords but no specific rule matched:
    if any(k in text_lower for k in ["rigged", "fraud", "stolen", "switched votes", "deepfake"]):
        return {
            "contradicts": True,
            "fact_id": "GT-004",
            "topic": "Paper Ballot Audit Trail & Tabulation Integrity",
            "official_rule": "All certified jurisdictions maintain voter-verified paper audit trails subject to mandatory bipartisan risk-limiting audits.",
            "verification_source": "U.S. Election Assistance Commission (EAC)",
            "debunk_text": "FACT CHECK: Paper ballot audit trails ensure every electronic tally is backed by verifiable physical paper ballots in secure bipartisan custody.",
            "contradiction_reason": "Allegation of untraceable vote manipulation contradicts mandatory physical paper audit trail standards."
        }

    return {
        "contradicts": False,
        "fact_id": None,
        "topic": None,
        "official_rule": None,
        "verification_source": None,
        "debunk_text": None,
        "contradiction_reason": None
    }
