"""
Network & Coordinated Inauthentic Behavior (CIB) Engine for ELECT-SENTINEL OSINT.
Constructs multi-relational graphs of actors, narratives, hashtags, and platforms
using NetworkX to uncover astroturfing rings, amplification hubs, and cross-platform spread.
"""

import json
import sqlite3
import re
import networkx as nx
from typing import Dict, Any, List
from backend.database import get_db


def build_propagation_network() -> Dict[str, Any]:
    """
    Generates a full graph representation of accounts, narratives, hashtags,
    and cross-platform linkages for interactive intelligence visualization.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Query recent posts
    cursor.execute("""
    SELECT id, text, author_handle, author_followers, source_platform, 
           confusion_score, bot_probability, narrative_id, category, timestamp
    FROM posts
    ORDER BY timestamp DESC
    LIMIT 200
    """)
    posts = cursor.fetchall()

    # Query active narratives
    cursor.execute("SELECT id, title, category, lifecycle, confusion_index, total_volume FROM narratives")
    narratives = cursor.fetchall()
    conn.close()

    G = nx.Graph()

    # Add narrative nodes
    for n in narratives:
        n_id = n["id"]
        G.add_node(
            n_id,
            id=n_id,
            label=n["title"][:24] + ("..." if len(n["title"]) > 24 else ""),
            type="narrative",
            category=n["category"],
            lifecycle=n["lifecycle"],
            confusion=n["confusion_index"],
            size=max(18, min(40, 15 + n["total_volume"] * 2)),
            color="#ef4444" if n["confusion_index"] > 75 else ("#f59e0b" if n["confusion_index"] > 50 else "#3b82f6")
        )

    # Add accounts, hashtags, and edges from posts
    account_posts = {}
    hashtags_map = {}

    for p in posts:
        handle = p["author_handle"]
        if not handle:
            continue

        # Add or update Account Node
        if handle not in G:
            bot_prob = p["bot_probability"] or 0.0
            is_bot = bot_prob > 0.55
            G.add_node(
                handle,
                id=handle,
                label=handle,
                type="account",
                platform=p["source_platform"],
                bot_probability=bot_prob,
                followers=p["author_followers"] or 0,
                size=12 if not is_bot else 10,
                color="#dc2626" if is_bot else "#10b981"
            )
            account_posts[handle] = []

        account_posts[handle].append(p["text"])

        # Link Account to Narrative
        n_id = p["narrative_id"]
        if n_id and n_id in G:
            if G.has_edge(handle, n_id):
                G[handle][n_id]["weight"] += 1
            else:
                G.add_edge(handle, n_id, weight=1, type="POSTED_IN")

        # Extract Hashtags
        tags = re.findall(r'#(\w+)', p["text"])
        for tag in tags[:3]:
            tag_node = f"#{tag.lower()}"
            if tag_node not in G:
                G.add_node(
                    tag_node,
                    id=tag_node,
                    label=tag_node,
                    type="hashtag",
                    size=10,
                    color="#8b5cf6"
                )
            if G.has_edge(handle, tag_node):
                G[handle][tag_node]["weight"] += 1
            else:
                G.add_edge(handle, tag_node, weight=1, type="USED_HASHTAG")

    # Detect Coordinated Inauthentic Behavior (CIB) - Copypasta / Bot Rings
    bot_handles = [h for h in account_posts if G.nodes[h].get("bot_probability", 0) > 0.5]
    cib_clusters_count = 0

    # Cross-compare text similarity between suspicious accounts
    for i in range(len(bot_handles)):
        for j in range(i + 1, min(len(bot_handles), i + 8)):
            h1 = bot_handles[i]
            h2 = bot_handles[j]
            t1 = " ".join(account_posts[h1])[:100].lower()
            t2 = " ".join(account_posts[h2])[:100].lower()
            
            # Simple word overlap or length match
            common_words = set(t1.split()) & set(t2.split())
            if len(common_words) >= 5 and not G.has_edge(h1, h2):
                G.add_edge(h1, h2, weight=3, type="COORDINATED_SWARM")
                cib_clusters_count += 1

    # Format JSON payload for visualization
    nodes = []
    for node_id, data in G.nodes(data=True):
        node_data = {"id": node_id}
        node_data.update(data)
        nodes.append(node_data)

    links = []
    for u, v, data in G.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1),
            "type": data.get("type", "CONNECTED")
        })

    # Centrality Calculation for Key Actors
    degree_dict = dict(G.degree())
    top_influencer_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "nodes": nodes,
        "links": links,
        "metrics": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "cib_swarms_detected": cib_clusters_count,
            "top_hubs": [{"node": n, "connections": d} for n, d in top_influencer_nodes]
        }
    }
