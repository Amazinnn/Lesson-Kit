"""Pool data-layer tests (TDD, red first)."""

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
    """Fresh full-schema pool with minimal dmath-ch06 rows."""
    conn.executescript(
        """
        CREATE TABLE knowledge_points (
            kp_id TEXT PRIMARY KEY,
            knowledge_item TEXT NOT NULL,
            body TEXT,
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
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE candidate_problems (
            candidate_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            status TEXT NOT NULL,
            structure_gate_status TEXT NOT NULL DEFAULT 'pending',
            audit_gate_status TEXT NOT NULL DEFAULT 'pending'
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
        CREATE TABLE knowledge_relations (
            relation_id TEXT PRIMARY KEY,
            source_kp_id TEXT NOT NULL,
            target_kp_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            strength TEXT NOT NULL
        );
        """
    )
    pool_schema.ensure_workbench_schema(conn)
    conn.executemany(
        "INSERT INTO knowledge_points"
        " (kp_id, knowledge_item, body, knowledge_type, importance)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            ("dmath-ch06-kp-001", "Counting basis", "body", "concept-property", "core"),
            ("dmath-ch06-kp-002", "Pigeonhole", "body", "method-modeling", "core"),
        ],
    )
    conn.executemany(
        "INSERT INTO problems"
        " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "P1", "S1", "calculation", "textbook"),
            ("dmath-ch06-prob-002", '["dmath-ch06-kp-002"]', "P2", "S2", "proof", "final"),
        ],
    )
    conn.execute(
        "INSERT INTO candidate_problems"
        " (candidate_id, kp_ids, problem_text, solution, status,"
        " structure_gate_status, audit_gate_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-cand-001", '["dmath-ch06-kp-001"]', "C1", "CS1",
         "gate_passed", "pass", "pass"),
    )
    conn.execute(
        "INSERT INTO learner_signals VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-sig-001", "node", "dmath-ch06-kp-002", "weak_node", "high", 2, "note"),
    )
    conn.execute(
        "INSERT INTO knowledge_relations VALUES (?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-rel-001", "dmath-ch06-kp-001", "dmath-ch06-kp-002",
         "prerequisite", "directed", "high"),
    )
    conn.commit()


class PoolTests(unittest.TestCase):
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
        self.pool_mod = pool_mod
        self.pool = pool_mod.Pool(
            root=self.ws_root,
            db_path=self.db_path,
            course="dmath",
            chapter="ch06",
        )

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_kps_filtered_by_prefix(self):
        kps = self.pool.kps("dmath-ch06")
        self.assertEqual(len(kps), 2)

    def test_problems_for_kps(self):
        problems = self.pool.problems_for_kps(["dmath-ch06-kp-002"])
        self.assertEqual([p["problem_id"] for p in problems], ["dmath-ch06-prob-002"])

    def test_problem_detail(self):
        problem = self.pool.problem("dmath-ch06-prob-001")
        self.assertEqual(problem["problem_id"], "dmath-ch06-prob-001")
        self.assertEqual(problem["kp_ids"], ["dmath-ch06-kp-001"])

    def test_gate_passed_candidates(self):
        candidates = self.pool.gate_passed_candidates()
        self.assertEqual([c["candidate_id"] for c in candidates], ["dmath-ch06-cand-001"])

    def test_signals_and_relations(self):
        signals = self.pool.signals()
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["weight"], "high")
        relations = self.pool.relations()
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]["relation_type"], "prerequisite")

    def test_schedule_upsert_and_get(self):
        self.pool.schedule_upsert({
            "item_type": "problem",
            "item_id": "dmath-ch06-prob-001",
            "direction": "",
            "state": "learning",
            "repetitions": 0,
            "ease": 2.5,
            "interval_days": 0.0,
            "due_at": None,
            "last_rating": None,
            "last_reviewed_at": None,
        })
        row = self.pool.schedule_get("problem", "dmath-ch06-prob-001")
        self.assertEqual(row["repetitions"], 0)
        self.pool.schedule_upsert({
            "item_type": "problem",
            "item_id": "dmath-ch06-prob-001",
            "direction": "",
            "state": "review",
            "repetitions": 1,
            "ease": 2.6,
            "interval_days": 3.0,
            "due_at": "2026-08-20",
            "last_rating": 4,
            "last_reviewed_at": "2026-08-16",
        })
        row = self.pool.schedule_get("problem", "dmath-ch06-prob-001")
        self.assertEqual(row["state"], "review")
        self.assertEqual(row["repetitions"], 1)

    def test_insert_attempt_with_answer_text(self):
        self.pool.insert_attempt(
            "dmath-ch06-prob-001", "wrong", "note", "my answer text"
        )
        row = self.pool.attempts("dmath-ch06-prob-001")[0]
        self.assertEqual(row["answer_text"], "my answer text")

    def test_insert_feedback_event(self):
        self.pool.insert_feedback_event("kp", "dmath-ch06-kp-002", 2, "confused")
        rows = self.pool.feedback_events("kp", "dmath-ch06-kp-002")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rating"], 2)

    def test_current_state_overwrites_in_place(self):
        self.pool.upsert_current_state(
            "kp", "dmath-ch06-kp-002", "needs_work"
        )
        self.pool.upsert_current_state(
            "kp", "dmath-ch06-kp-002", "mastered"
        )
        rows = self.pool.current_states()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "mastered")

    def test_runtime_paths(self):
        self.assertEqual(
            self.pool.figures_dir(),
            self.ws_root / ".lessonkit" / "figures" / "dmath" / "ch06",
        )
        self.assertEqual(self.pool.jobs_dir(), self.ws_root / ".lessonkit" / "jobs")


if __name__ == "__main__":
    unittest.main()
