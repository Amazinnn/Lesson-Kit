"""Feedback mapping tests (TDD, red first)."""

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))


def build_fixture_db(conn):
    conn.executescript(
        """
        CREATE TABLE knowledge_points (
            kp_id TEXT PRIMARY KEY,
            knowledge_item TEXT NOT NULL,
            knowledge_type TEXT,
            importance TEXT
        );
        CREATE TABLE problems (
            problem_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            problem_type TEXT,
            source_kind TEXT
        );
        CREATE TABLE problem_progress (
            problem_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'new',
            note TEXT,
            updated_at TEXT
        );
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE learner_signals (
            signal_id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            weight TEXT NOT NULL DEFAULT 'medium',
            evidence_count INTEGER NOT NULL DEFAULT 1,
            note TEXT
        );
        """
    )
    pool_schema.ensure_workbench_schema(conn)
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, knowledge_type, importance)"
        " VALUES (?, ?, ?, ?)",
        ("dmath-ch06-kp-001", "A", "concept-property", "core"),
    )
    conn.commit()


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws_root = Path(self.tmp.name)
        self.db_path = self.ws_root / "pool" / "dmath.db"
        self.db_path.parent.mkdir()
        conn = sqlite3.connect(self.db_path)
        build_fixture_db(conn)
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from data import pool as pool_mod
        from domain import feedback as feedback_mod
        self.pool = pool_mod.Pool(
            root=self.ws_root, db_path=self.db_path, course="dmath", chapter="ch06",
        )
        self.feedback = feedback_mod

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_rating_two_raises_signal_to_high(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=2)
        signals = [s for s in self.pool.signals()
                   if s["target_id"] == "dmath-ch06-kp-001"]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["weight"], "high")

    def test_confusion_keyword_maps_to_confusion_type(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001",
                            note="这两个概念我混淆了")
        signals = [s for s in self.pool.signals()
                   if s["target_id"] == "dmath-ch06-kp-001"]
        self.assertEqual(signals[0]["signal_type"], "confusion")
        self.assertEqual(signals[0]["note"], "这两个概念我混淆了")

    def test_unknown_note_falls_back_to_weak_node(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", note="随便写的")
        signals = [s for s in self.pool.signals()
                   if s["target_id"] == "dmath-ch06-kp-001"]
        self.assertEqual(signals[0]["signal_type"], "weak_node")

    def test_rating_five_increments_existing_evidence(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=2)
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=5)
        signals = [s for s in self.pool.signals()
                   if s["target_id"] == "dmath-ch06-kp-001"]
        self.assertEqual(signals[0]["evidence_count"], 2)
        self.assertEqual(signals[0]["weight"], "high")
        self.assertEqual(
            self.pool.current_state("kp", "dmath-ch06-kp-001")["state"],
            "mastered",
        )

    def test_rating_four_downgrades_weight(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=2)
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=4)
        signals = [s for s in self.pool.signals()
                   if s["target_id"] == "dmath-ch06-kp-001"]
        self.assertEqual(signals[0]["weight"], "low")
        self.assertEqual(
            self.pool.current_state("kp", "dmath-ch06-kp-001")["state"],
            "review",
        )

    def test_event_logged(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001",
                            rating=3, note="还行")
        events = self.pool.feedback_events("kp", "dmath-ch06-kp-001")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["rating"], 3)
        self.assertEqual(events[0]["note"], "还行")

    def test_rating_sets_current_knowledge_state(self):
        self.feedback.apply(self.pool, "kp", "dmath-ch06-kp-001", rating=2)
        current = self.pool.current_state("kp", "dmath-ch06-kp-001")
        self.assertEqual(current["state"], "needs_work")


if __name__ == "__main__":
    unittest.main()
