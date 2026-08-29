"""Pull engine tests (TDD, red first)."""

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
        """
    )
    pool_schema.ensure_workbench_schema(conn)
    conn.executemany(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, knowledge_type, importance)"
        " VALUES (?, ?, ?, ?)",
        [
            ("dmath-ch06-kp-001", "A", "concept-property", "core"),
            ("dmath-ch06-kp-002", "B", "method-modeling", "core"),
            ("dmath-ch06-kp-003", "C", "concept-property", "core"),
        ],
    )
    conn.executemany(
        "INSERT INTO problems"
        " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "P1", "S1", "calculation", "textbook"),
            ("dmath-ch06-prob-002", '["dmath-ch06-kp-001","dmath-ch06-kp-002"]', "P2", "S2", "proof", "textbook"),
            ("dmath-ch06-prob-003", '["dmath-ch06-kp-003"]', "P3", "S3", "calculation", "final"),
        ],
    )
    conn.execute(
        "INSERT INTO candidate_problems"
        " (candidate_id, kp_ids, problem_text, solution, status,"
        " structure_gate_status, audit_gate_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-cand-001", '["dmath-ch06-kp-003"]', "C1", "CS1",
         "gate_passed", "pass", "pass"),
    )
    conn.commit()


class PullTests(unittest.TestCase):
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
        from domain import pull as pull_mod
        self.pool = pool_mod.Pool(
            root=self.ws_root, db_path=self.db_path, course="dmath", chapter="ch06",
        )
        self.pull = pull_mod

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_weak_mode_orders_multi_kp_hits_first(self):
        result = self.pull.select(
            self.pool, ["dmath-ch06-kp-001", "dmath-ch06-kp-002"], n=10, mode="weak"
        )
        ids = [p["problem_id"] for p in result["problems"]]
        self.assertEqual(ids[0], "dmath-ch06-prob-002")

    def test_source_kind_filter(self):
        result = self.pull.select(
            self.pool, ["dmath-ch06-kp-001"], n=10, mode="weak",
            source_kind="final",
        )
        self.assertEqual(result["problems"], [])

    def test_exclude_ids_dedup(self):
        result = self.pull.select(
            self.pool, ["dmath-ch06-kp-001"], n=10, mode="weak",
            exclude_ids={"dmath-ch06-prob-001"},
        )
        self.assertNotIn("dmath-ch06-prob-001",
                         [p["problem_id"] for p in result["problems"]])

    def test_candidate_fallback(self):
        result = self.pull.select(
            self.pool, ["dmath-ch06-kp-003"], n=5, mode="weak"
        )
        candidate_ids = [c["candidate_id"] for c in result["candidates"]]
        self.assertIn("dmath-ch06-cand-001", candidate_ids)

    def test_shortage_reported(self):
        result = self.pull.select(
            self.pool, ["dmath-ch06-kp-003"], n=10, mode="weak"
        )
        self.assertIn("dmath-ch06-kp-003", result["shortage"])

    def test_mode_all_returns_all_problems(self):
        result = self.pull.select(self.pool, [], n=10, mode="all")
        self.assertEqual(len(result["problems"]), 3)

    def test_practice_modes_do_not_silently_fall_back(self):
        class ExplicitModePool:
            def problems_for_kps(self, kp_ids, source_kind=None):
                return [
                    {"problem_id": "exam", "kp_ids": ["kp-1"]},
                    {"problem_id": "card", "kp_ids": ["kp-1"], "practice_mode": "micro"},
                    {"problem_id": "judge", "kp_ids": ["kp-1"], "practice_mode": "yes_no"},
                ]

            def gate_passed_candidates(self, kp_ids):
                return []

        pool = ExplicitModePool()
        self.assertEqual(
            [p["problem_id"] for p in self.pull.select(pool, ["kp-1"], 10, mode="exam")["problems"]],
            ["exam"],
        )
        self.assertEqual(
            [p["problem_id"] for p in self.pull.select(pool, ["kp-1"], 10, mode="micro")["problems"]],
            ["card"],
        )
        self.assertEqual(
            [p["problem_id"] for p in self.pull.select(pool, ["kp-1"], 10, mode="yes_no")["problems"]],
            ["judge"],
        )


if __name__ == "__main__":
    unittest.main()
