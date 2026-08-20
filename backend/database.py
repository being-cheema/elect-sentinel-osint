"""
Database module for ELECT-SENTINEL OSINT Platform.
Uses SQLite for robust, zero-dependency, lightning-fast storage.
"""

import sqlite3
import json
import hashlib
import uuid
from datetime import datetime, timezone
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "elect_sentinel.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Posts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        text TEXT NOT NULL,
        cleaned_text TEXT,
        source_platform TEXT NOT NULL,
        author_handle TEXT NOT NULL,
        author_followers INTEGER DEFAULT 0,
        author_account_age_days INTEGER DEFAULT 365,
        timestamp TEXT NOT NULL,
        url TEXT,
        confusion_score REAL DEFAULT 0.0,
        category TEXT DEFAULT 'legitimate_news',
        viral_velocity REAL DEFAULT 0.0,
        bot_probability REAL DEFAULT 0.0,
        cib_cluster_id TEXT,
        narrative_id TEXT,
        sentiment TEXT DEFAULT 'neutral',
        urgency_score REAL DEFAULT 0.0,
        epistemic_uncertainty REAL DEFAULT 0.0,
        contradiction_flag INTEGER DEFAULT 0,
        contradiction_detail TEXT,
        triage_status TEXT DEFAULT 'new',
        analyst_notes TEXT DEFAULT '',
        priority TEXT DEFAULT 'P3',
        sha256_hash TEXT,
        location_district TEXT DEFAULT 'National',
        latitude REAL DEFAULT 39.8283,
        longitude REAL DEFAULT -98.5795
    )
    """)

    # Narratives Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS narratives (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        category TEXT NOT NULL,
        lifecycle TEXT DEFAULT 'emerging',
        confusion_index REAL DEFAULT 0.0,
        total_volume INTEGER DEFAULT 1,
        velocity REAL DEFAULT 0.0,
        first_spotted TEXT NOT NULL,
        last_activity TEXT NOT NULL,
        origin_platform TEXT NOT NULL,
        platforms_involved TEXT DEFAULT '[]',
        keywords TEXT DEFAULT '[]',
        debunk_response TEXT DEFAULT ''
    )
    """)

    # Ground Truth Facts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ground_truth_facts (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        topic TEXT NOT NULL,
        official_rule TEXT NOT NULL,
        jurisdiction TEXT DEFAULT 'National',
        verification_source TEXT NOT NULL,
        debunk_template TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Cases / Dossiers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        narrative_ids TEXT DEFAULT '[]',
        post_ids TEXT DEFAULT '[]',
        threat_level TEXT DEFAULT 'medium',
        analyst TEXT DEFAULT 'Lead Analyst',
        status TEXT DEFAULT 'active',
        executive_summary TEXT DEFAULT '',
        recommended_action TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # System Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT DEFAULT 'P2',
        related_id TEXT,
        timestamp TEXT NOT NULL,
        is_read INTEGER DEFAULT 0
    )
    """)

    # Ingestion Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingest_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        items_ingested INTEGER DEFAULT 0,
        status TEXT DEFAULT 'success',
        timestamp TEXT NOT NULL
    )
    """)

    conn.commit()
    seed_ground_truth(conn)
    conn.close()


def seed_ground_truth(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM ground_truth_facts")
    count = cursor.fetchone()["count"]
    if count > 0:
        return

    now = datetime.now(timezone.utc).isoformat()
    facts = [
        (
            "GT-001",
            "voter_suppression",
            "Polling Hours & Closing Times",
            "Official voting hours in all state precincts are 7:00 AM to 7:00 PM local time. If you are in line before 7:00 PM, you are legally entitled to cast your ballot.",
            "National",
            "Federal Election Commission / State Board of Elections",
            "FACT CHECK: Polls DO NOT close early. By federal and state law, any voter waiting in line by 7:00 PM local time is guaranteed the right to vote. Do not leave the line.",
            now
        ),
        (
            "GT-002",
            "voter_suppression",
            "Voter Identification Requirements",
            "Registered voters can present state driver's license, US passport, military ID, or official voter registration certificate. No fee or special barcode card is required.",
            "National",
            "National Association of State Election Directors",
            "FACT CHECK: Claims that voters need a paid 'Federal Digital Barcode' or additional proprietary card are false. Standard state ID or voter registration cards are valid.",
            now
        ),
        (
            "GT-003",
            "integrity_tampering",
            "Voting Machine Air-Gapping & Security",
            "All certified voting tabulators and ballot marking devices are strictly air-gapped and NEVER connected to the internet or cellular networks during election operations.",
            "National",
            "Cybersecurity and Infrastructure Security Agency (CISA)",
            "FACT CHECK: Certified voting tabulators are air-gapped from the internet. Pre-election Logic and Accuracy tests are conducted publicly, and paper backup ballots verify all counts.",
            now
        ),
        (
            "GT-004",
            "integrity_tampering",
            "Paper Ballot Audit Trail",
            "Over 95% of votes in the United States are cast on verifiable paper ballots or have a voter-verified paper audit trail (VVPAT) preserved for risk-limiting post-election audits.",
            "National",
            "U.S. Election Assistance Commission (EAC)",
            "FACT CHECK: Paper ballots are securely locked in bipartisan custody. Tabulator digital tallies are independently cross-audited against hand paper tallies in mandatory audits.",
            now
        ),
        (
            "GT-005",
            "synthetic_deepfake",
            "Candidate Status & Election Date Modifications",
            "Election Day is established by federal law as the first Tuesday after the first Monday in November. No candidate, executive order, or online announcement can unilaterally alter the date.",
            "National",
            "U.S. Constitution (Article II) / National Archives",
            "FACT CHECK: The election date is set by federal statute and cannot be postponed via executive declaration or social media announcements. Videos claiming postponement are synthetic deepfakes.",
            now
        ),
        (
            "GT-006",
            "premature_results",
            "Official Tabulation & Certification Timeline",
            "Official election results are certified by county and state election boards after all mail-in, provisional, and military overseas ballots are verified, taking several days.",
            "National",
            "National Conference of State Legislatures (NCSL)",
            "FACT CHECK: Early media projections and online claims of 100% finished counts on election night are unofficial. Official certification requires bipartisan canvas audits.",
            now
        ),
        (
            "GT-007",
            "voter_suppression",
            "Mail-in Ballot Drop Box Locations",
            "Official ballot drop boxes are monitored by 24/7 video surveillance and bipartisan retrieval teams. All official locations are listed strictly on official .gov election portals.",
            "Maricopa County, AZ",
            "Maricopa County Elections Department",
            "FACT CHECK: Official drop boxes in Maricopa County remain open through 7:00 PM on Election Day at verified county government centers. Beware of unofficial collection boxes.",
            now
        ),
        (
            "GT-008",
            "voter_intimidation",
            "Polling Station Protection & Law Enforcement",
            "Voter intimidation, unauthorized armed monitoring within 150 feet of a polling precinct, and harassing voters are federal and state felonies with immediate law enforcement response.",
            "National",
            "Department of Justice Voting Rights Section",
            "FACT CHECK: Polling locations have strict 150ft electioneering-free zones. Any voter encountering harassment should alert precinct election judges immediately.",
            now
        )
    ]

    cursor.executemany("""
    INSERT INTO ground_truth_facts 
    (id, category, topic, official_rule, jurisdiction, verification_source, debunk_template, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, facts)
    conn.commit()


def compute_hash(text: str, author: str, timestamp: str) -> str:
    payload = f"{text}_{author}_{timestamp}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()
