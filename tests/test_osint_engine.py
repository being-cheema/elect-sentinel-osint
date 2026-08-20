"""
Automated Test Suite for ELECT-SENTINEL OSINT Platform (Global Live).
Tests database, NLP scoring, ground truth contradiction detection,
narrative clustering, network graph generation, and global live connectors.
"""

import os
import sys
import unittest

# Add workspace root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, get_db
from backend.nlp_engine import analyze_text
from backend.fact_engine import check_contradiction, get_all_ground_truth
from backend.clustering_engine import find_or_create_narrative, get_all_narratives
from backend.network_engine import build_propagation_network
from backend.ingest_engine import ingest_post_record, resolve_global_location, fetch_all_live_global_feeds
from backend.case_engine import create_case, generate_intelligence_report


class TestElectSentinelGlobal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_initialization(self):
        facts = get_all_ground_truth()
        self.assertGreaterEqual(len(facts), 5, "Should have seeded ground truth facts")

    def test_global_location_resolution(self):
        t1 = "Breaking: Clashes reported outside election tabulation center in New Delhi during counting."
        l1 = resolve_global_location(t1)
        self.assertEqual(l1["district"], "India")

        t2 = "UK Electoral Commission releases update on parliamentary by-election voting in London."
        l2 = resolve_global_location(t2)
        self.assertEqual(l2["district"], "United Kingdom")

        t3 = "French National Assembly debates new election security protocols in Paris."
        l3 = resolve_global_location(t3)
        self.assertEqual(l3["district"], "France")

    def test_nlp_voter_suppression_detection(self):
        text = "URGENT: Polling stations are closed early at 4 PM! You must pay $25 digital barcode fee to vote!"
        res = analyze_text(text, author_handle="@bot_user_9921", author_followers=5, author_age_days=10, platform="twitter")
        
        self.assertEqual(res["category"], "voter_suppression")
        self.assertGreaterEqual(res["confusion_score"], 60.0, "Confusion score should be high")
        self.assertGreaterEqual(res["bot_probability"], 0.5, "Bot score should be elevated")

    def test_nlp_machine_rigging_detection(self):
        text = "ALERT: Smartmatic voting machines caught switching votes via cellular modems live on camera in precinct 12!"
        res = analyze_text(text, platform="telegram")
        self.assertEqual(res["category"], "integrity_tampering")
        self.assertGreaterEqual(res["confusion_score"], 60.0)

    def test_ground_truth_contradiction(self):
        text = "Polls closed early today at 5pm, anyone left in line will not be allowed to cast a ballot."
        check = check_contradiction(text, "voter_suppression")
        self.assertTrue(check["contradicts"], "Should detect polling hour contradiction")
        self.assertIsNotNone(check["debunk_text"])

    def test_narrative_clustering(self):
        p1 = ingest_post_record(
            text="Dominion machines are switching votes to candidate B in Wayne county! Check your paper receipts!",
            author_handle="@audit_now_11",
            platform="twitter"
        )
        p2 = ingest_post_record(
            text="Another voting machine switched ballot tallies! Rigged election!",
            author_handle="@patriot_scout",
            platform="telegram"
        )
        self.assertIsNotNone(p1["narrative_id"])
        self.assertIsNotNone(p2["narrative_id"])

    def test_network_graph_generation(self):
        net = build_propagation_network()
        self.assertIn("nodes", net)
        self.assertIn("links", net)
        self.assertIn("metrics", net)

    def test_case_and_report_generation(self):
        case_id = create_case(
            title="Global Investigation into Coordinated Election Disinformation",
            narrative_ids=[],
            post_ids=[],
            threat_level="critical",
            executive_summary="Targeted attack suppressing turnout across multiple global jurisdictions."
        )
        self.assertTrue(case_id.startswith("CASE-"))
        report = generate_intelligence_report(case_id)
        self.assertIn("markdown_report", report)


if __name__ == "__main__":
    unittest.main()
