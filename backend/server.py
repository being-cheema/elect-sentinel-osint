"""
FastAPI Server & REST API / SSE Telemetry Router for ELECT-SENTINEL OSINT.
Operates exclusively on 100% real live global digital feeds from all countries.
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import get_db, init_db
from backend.nlp_engine import analyze_text
from backend.fact_engine import get_all_ground_truth, add_ground_truth, check_contradiction
from backend.clustering_engine import get_all_narratives
from backend.network_engine import build_propagation_network
from backend.ingest_engine import (
    ingest_post_record, fetch_all_live_global_feeds,
    purge_all_data, seed_initial_live_data, resolve_global_location
)
from backend.case_engine import create_case, get_all_cases, generate_intelligence_report

app = FastAPI(
    title="ELECT-SENTINEL OSINT API (Global Live)",
    description="Automated Global OSINT Platform for Election Disinformation & Public Confusion Monitoring",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup():
    init_db()
    seed_initial_live_data()


# -------------------------------------------------------------
# Frontend Root Route
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>ELECT-SENTINEL OSINT: Initializing Global Live Feed...</h1>")


# -------------------------------------------------------------
# Telemetry & Overview API
# -------------------------------------------------------------
@app.get("/api/telemetry/overview")
def get_overview_telemetry():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM posts")
    total_posts = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as active FROM narratives WHERE lifecycle != 'dormant'")
    active_narratives = cursor.fetchone()["active"]

    cursor.execute("SELECT COUNT(*) as alerts FROM alerts WHERE is_read = 0")
    unread_alerts = cursor.fetchone()["alerts"]

    cursor.execute("SELECT AVG(confusion_score) as avg_conf FROM posts")
    avg_conf_row = cursor.fetchone()["avg_conf"]
    avg_confusion = round(avg_conf_row if avg_conf_row else 0.0, 1)

    cursor.execute("SELECT COUNT(DISTINCT cib_cluster_id) as cib_count FROM posts WHERE cib_cluster_id IS NOT NULL")
    cib_count = cursor.fetchone()["cib_count"]

    # Category breakdown
    cursor.execute("SELECT category, COUNT(*) as count FROM posts GROUP BY category ORDER BY count DESC")
    categories = [dict(r) for r in cursor.fetchall()]

    # Platform breakdown
    cursor.execute("SELECT source_platform, COUNT(*) as count FROM posts GROUP BY source_platform ORDER BY count DESC")
    platforms = [dict(r) for r in cursor.fetchall()]

    # Recent Alerts
    cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 6")
    recent_alerts = [dict(r) for r in cursor.fetchall()]

    # Threat Level Evaluation
    if avg_confusion >= 60.0 or unread_alerts >= 3:
        threat_level = "CRITICAL (DEFCON 1)"
        threat_color = "#ef4444"
    elif avg_confusion >= 40.0 or unread_alerts >= 1:
        threat_level = "ELEVATED (DEFCON 2)"
        threat_color = "#f59e0b"
    else:
        threat_level = "NOMINAL (DEFCON 3)"
        threat_color = "#10b981"

    conn.close()

    return {
        "total_monitored_posts": total_posts,
        "active_narratives": active_narratives,
        "unread_alerts_count": unread_alerts,
        "mean_confusion_score": avg_confusion,
        "cib_swarms_detected": cib_count,
        "threat_level": threat_level,
        "threat_color": threat_color,
        "categories": categories,
        "platforms": platforms,
        "recent_alerts": recent_alerts
    }


# -------------------------------------------------------------
# Narratives API
# -------------------------------------------------------------
@app.get("/api/narratives")
def list_narratives():
    return get_all_narratives()


# -------------------------------------------------------------
# Posts & Triage API
# -------------------------------------------------------------
@app.get("/api/posts")
def list_posts(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    priority: Optional[str] = None,
    triage_status: Optional[str] = None,
    min_confusion: float = 0.0,
    search: Optional[str] = None,
    limit: int = 60,
    offset: int = 0
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM posts WHERE confusion_score >= ?"
    params = [min_confusion]

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    if platform and platform != "all":
        query += " AND source_platform = ?"
        params.append(platform)
    if priority and priority != "all":
        query += " AND priority = ?"
        params.append(priority)
    if triage_status and triage_status != "all":
        query += " AND triage_status = ?"
        params.append(triage_status)
    if search:
        query += " AND (text LIKE ? OR author_handle LIKE ? OR location_district LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    posts = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return posts


@app.get("/api/posts/{post_id}")
def get_post_details(post_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = dict(row)
    fact_check = check_contradiction(post["text"], post["category"])
    post["fact_verification"] = fact_check
    return post


class TriageUpdate(BaseModel):
    triage_status: str
    priority: Optional[str] = None
    analyst_notes: Optional[str] = None


@app.patch("/api/posts/{post_id}/triage")
def update_post_triage(post_id: str, payload: TriageUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    updates = ["triage_status = ?"]
    params = [payload.triage_status]

    if payload.priority:
        updates.append("priority = ?")
        params.append(payload.priority)
    if payload.analyst_notes is not None:
        updates.append("analyst_notes = ?")
        params.append(payload.analyst_notes)

    params.append(post_id)
    cursor.execute(f"UPDATE posts SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return {"status": "success", "post_id": post_id, "triage_status": payload.triage_status}


# -------------------------------------------------------------
# Network & CIB Propagation API
# -------------------------------------------------------------
@app.get("/api/network")
def get_network():
    return build_propagation_network()


# -------------------------------------------------------------
# Global Geospatial Threat Mapping API
# -------------------------------------------------------------
@app.get("/api/geospatial")
def get_geospatial_hotspots():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT location_district, latitude, longitude,
           COUNT(*) as post_count,
           AVG(confusion_score) as avg_confusion,
           MAX(category) as primary_category
    FROM posts
    WHERE location_district != 'Global / International'
    GROUP BY location_district, latitude, longitude
    ORDER BY post_count DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    hotspots = []
    for r in rows:
        hotspots.append({
            "district": r["location_district"],
            "lat": r["latitude"],
            "lon": r["longitude"],
            "post_count": r["post_count"],
            "avg_confusion": round(r["avg_confusion"], 1),
            "primary_category": r["primary_category"]
        })
    return hotspots


# -------------------------------------------------------------
# Live OSINT Scanner API
# -------------------------------------------------------------
class ScanRequest(BaseModel):
    text: str
    author: Optional[str] = "@analyst_investigation"
    platform: Optional[str] = "web"
    url: Optional[str] = ""


@app.post("/api/osint/scan")
def scan_custom_content(req: ScanRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    nlp_result = analyze_text(
        text=req.text,
        author_handle=req.author,
        author_followers=100,
        author_age_days=180,
        platform=req.platform
    )
    fact_check = check_contradiction(req.text, nlp_result["category"])
    loc = resolve_global_location(req.text)

    return {
        "analysis": nlp_result,
        "fact_check": fact_check,
        "resolved_location": loc,
        "sha256_fingerprint": compute_hash(req.text, req.author, datetime.now(timezone.utc).isoformat()),
        "recommended_action": "Publish counter-fact clarification" if fact_check["contradicts"] else "Monitor for acceleration"
    }


# -------------------------------------------------------------
# Ground Truth Knowledge Base API
# -------------------------------------------------------------
@app.get("/api/facts")
def list_ground_truth():
    return get_all_ground_truth()


class FactCreate(BaseModel):
    category: str
    topic: str
    official_rule: str
    jurisdiction: str = "National"
    verification_source: str
    debunk_template: str


@app.post("/api/facts")
def create_fact(payload: FactCreate):
    new_id = add_ground_truth(
        category=payload.category,
        topic=payload.topic,
        official_rule=payload.official_rule,
        jurisdiction=payload.jurisdiction,
        verification_source=payload.verification_source,
        debunk_template=payload.debunk_template
    )
    return {"status": "created", "fact_id": new_id}


# -------------------------------------------------------------
# Case Management & Dossiers API
# -------------------------------------------------------------
@app.get("/api/cases")
def list_cases():
    return get_all_cases()


class CaseCreate(BaseModel):
    title: str
    narrative_ids: List[str] = []
    post_ids: List[str] = []
    threat_level: str = "high"
    analyst: str = "Lead OSINT Analyst"
    executive_summary: str = ""
    recommended_action: str = ""


@app.post("/api/cases")
def create_new_case(payload: CaseCreate):
    case_id = create_case(
        title=payload.title,
        narrative_ids=payload.narrative_ids,
        post_ids=payload.post_ids,
        threat_level=payload.threat_level,
        analyst=payload.analyst,
        executive_summary=payload.executive_summary,
        recommended_action=payload.recommended_action
    )
    return {"status": "created", "case_id": case_id}


@app.get("/api/cases/{case_id}/report")
def get_case_report(case_id: str):
    report = generate_intelligence_report(case_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail="Case not found")
    return report


# -------------------------------------------------------------
# Global Live Stream Poller & Database Refresh
# -------------------------------------------------------------
@app.post("/api/ingest/refresh-live")
async def refresh_live_feeds(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_all_live_global_feeds)
    return {"status": "success", "message": "Global multi-source ingestion triggered across 25+ live feeds", "mode": "100% Live Global Stream"}


@app.post("/api/admin/purge-and-refresh")
async def purge_and_refresh_live(background_tasks: BackgroundTasks):
    """Wipes all historical content and fetches a completely fresh real-world global stream."""
    purge_all_data()
    background_tasks.add_task(fetch_all_live_global_feeds)
    return {
        "status": "success",
        "message": "Purged historical records. Ingesting fresh 100% real live global stream in background.",
        "mode": "100% Fresh Real Live Global Stream"
    }



# -------------------------------------------------------------
# Server-Sent Events (SSE) Live Telemetry Stream
# -------------------------------------------------------------
@app.get("/api/stream")
async def live_stream(request: Request):
    """
    Continuous SSE stream delivering newly ingested live global content.
    """
    async def event_generator():
        last_checked = datetime.now(timezone.utc).isoformat()
        while True:
            if await request.is_disconnected():
                break

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 6", (last_checked,))
            new_posts = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM alerts WHERE timestamp > ? AND is_read = 0 ORDER BY timestamp DESC", (last_checked,))
            new_alerts = [dict(r) for r in cursor.fetchall()]
            conn.close()

            last_checked = datetime.now(timezone.utc).isoformat()

            if new_posts or new_alerts:
                payload = {
                    "type": "update",
                    "timestamp": last_checked,
                    "new_posts": new_posts,
                    "new_alerts": new_alerts
                }
                yield f"data: {json.dumps(payload)}\n\n"

            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            await asyncio.sleep(3.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
