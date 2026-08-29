"""View-query tests (TDD, red first)."""

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
        "INSERT INTO learner_signals VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("sig-1", "node", "dmath-ch06-kp-002", "weak_node", "high", 2, "note"),
    )
    conn.execute(
        "INSERT INTO review_schedule"
        " (item_type, item_id, direction, state, repetitions, ease, interval_days,"
        " due_at, last_rating, last_reviewed_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("problem", "dmath-ch06-prob-001", "", "review", 2, 2.5, 5.0,
         "2026-08-10", 3, "2026-08-05"),
    )
    conn.execute(
        "INSERT INTO problem_attempts (problem_id, status, note, answer_text)"
        " VALUES (?, ?, ?, ?)",
        ("dmath-ch06-prob-002", "wrong", "stuck at step 2", "my proof"),
    )
    conn.commit()


class QueryTests(unittest.TestCase):
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
        from data import queries as queries_mod
        self.pool = pool_mod.Pool(
            root=self.ws_root, db_path=self.db_path, course="dmath", chapter="ch06",
        )
        self.queries = queries_mod

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_hub_stats(self):
        stats = self.queries.hub_stats(self.pool)
        self.assertEqual(stats["kps"], 2)
        self.assertEqual(stats["problems"], 2)
        self.assertNotIn("candidates", stats)
        self.assertEqual(stats["signals"], 1)
        self.assertEqual(stats["due"], 1)

    def test_due_list(self):
        items = self.queries.due_list(self.pool)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["item_id"], "dmath-ch06-prob-001")
        self.assertEqual(items[0]["label"], "P1")

    def test_due_item_label_shows_the_full_text_without_a_cap(self):
        long_text = "设集合 A 有 n 个元素，则 A 的子集共有 2 的 n 次方个，其中真子集要比子集少一个，这个结论在计数问题里反复出现。" * 2
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE problems SET problem_text = ? WHERE problem_id = ?",
            (long_text, "dmath-ch06-prob-001"),
        )
        conn.commit()
        conn.close()
        items = self.queries.due_list(self.pool)
        self.assertEqual(items[0]["label"], long_text)

    def test_problem_detail(self):
        detail = self.queries.problem_detail(self.pool, "dmath-ch06-prob-002")
        self.assertEqual(detail["problem"]["problem_id"], "dmath-ch06-prob-002")
        self.assertEqual(len(detail["attempts"]), 1)
        self.assertEqual(detail["attempts"][0]["answer_text"], "my proof")
        self.assertEqual(detail["schedule"], None)

    def test_graph_model_counts_formal_problems_and_merges_semantic_edges(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO knowledge_points"
                " (kp_id, knowledge_item, body, knowledge_type, importance)"
                " VALUES (?, ?, ?, ?, ?)",
                ("dmath-ch06-kp-003", "Binomial", "body", "concept-property", "core"),
            )
            conn.executemany(
                "INSERT INTO problems"
                " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("dmath-ch06-prob-003", '["dmath-ch06-kp-001", "dmath-ch06-kp-002"]',
                     "P3", "S3", "calculation", "textbook"),
                    ("dmath-ch06-prob-004", '["dmath-ch06-kp-002", "dmath-ch06-kp-003"]',
                     "P4", "S4", "calculation", "textbook"),
                ],
            )
            conn.execute(
                "INSERT INTO candidate_problems"
                " (candidate_id, kp_ids, problem_text, solution, status)"
                " VALUES (?, ?, ?, ?, ?)",
                ("candidate-001", '["dmath-ch06-kp-001"]', "candidate", "", "pending"),
            )
            conn.executemany(
                "INSERT INTO knowledge_relations VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("rel-1", "dmath-ch06-kp-001", "dmath-ch06-kp-002",
                     "prerequisite", "forward", "high"),
                    ("rel-2", "dmath-ch06-kp-002", "dmath-ch06-kp-001",
                     "related", "forward", "low"),
                ],
            )
            conn.commit()
        finally:
            conn.close()

        model = self.queries.graph_model(self.pool)
        counts = {node["id"]: node["problem_count"] for node in model["nodes"]}
        self.assertEqual(counts, {
            "dmath-ch06-kp-001": 2,
            "dmath-ch06-kp-002": 3,
            "dmath-ch06-kp-003": 1,
        })
        importance = {node["id"]: node["importance"] for node in model["nodes"]}
        self.assertEqual(importance["dmath-ch06-kp-003"], "core")
        self.assertEqual(len(model["edges"]), 1)
        edge = model["edges"][0]
        self.assertEqual({edge["source"], edge["target"]}, {
            "dmath-ch06-kp-001", "dmath-ch06-kp-002",
        })
        self.assertEqual(edge["strength"], "high")
        self.assertEqual(edge["shared_problem_count"], 1)
        self.assertAlmostEqual(edge["attraction"], 1.375)

    def test_graph_model_uses_the_strongest_signal_for_each_node(self):
        self.pool.connect().execute(
            "INSERT INTO learner_signals VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("zz-low", "node", "dmath-ch06-kp-002", "confusion", "low", 99, None),
        )
        self.pool.commit()
        from workbench.domain.signals import strongest_by_target
        weights = {
            target_id: row["weight"]
            for target_id, row in strongest_by_target(self.pool.signals()).items()
        }
        model = self.queries.graph_model(self.pool, weights)
        node = next(item for item in model["nodes"] if item["id"] == "dmath-ch06-kp-002")
        self.assertEqual(node["state"], "needs_work")

    def test_kp_detail(self):
        detail = self.queries.kp_detail(self.pool, "dmath-ch06-kp-002")
        self.assertEqual(detail["kp"]["kp_id"], "dmath-ch06-kp-002")
        self.assertEqual(len(detail["signals"]), 1)
        self.assertEqual(len(detail["problems"]), 1)
        self.assertEqual(detail["problems"][0]["problem_id"], "dmath-ch06-prob-002")

    def test_figures_list(self):
        figure_dir = self.pool.figures_dir()
        figure_dir.mkdir(parents=True)
        (figure_dir / "dmath-ch06-kp-001-fig-001.png").write_bytes(b"x")
        figures = self.queries.figures_list(self.pool)
        self.assertEqual(figures, ["dmath/ch06/dmath-ch06-kp-001-fig-001.png"])


if __name__ == "__main__":
    unittest.main()
