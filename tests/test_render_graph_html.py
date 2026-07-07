import contextlib
import importlib.util
import json
import math
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_graph_html",
    REPO_ROOT / "pool" / "scripts" / "render-graph-html.py",
)
render_graph_html = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["render_graph_html"] = render_graph_html
SPEC.loader.exec_module(render_graph_html)


class RenderGraphHtmlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT,
                source_location TEXT,
                knowledge_type TEXT,
                related_kp_ids TEXT,
                importance TEXT,
                learning_action TEXT,
                body TEXT,
                difficulty TEXT,
                fragile TEXT
            );
            CREATE TABLE kp_progress (
                kp_id TEXT PRIMARY KEY,
                mastery_state TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT,
                problem_text TEXT,
                solution TEXT,
                problem_type TEXT,
                source_kind TEXT
            );
            """
        )
        self.conn.executemany(
            "INSERT INTO knowledge_points VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "dmath-ch06-kp-001",
                    "乘法规则",
                    "§6-1",
                    "definition",
                    '["dmath-ch06-kp-002"]',
                    "core",
                    "practice",
                    "Use product rule for staged choices.",
                    "easy",
                    "",
                ),
                (
                    "dmath-ch06-kp-002",
                    "加法规则",
                    "§6-1",
                    "definition",
                    '["dmath-ch06-kp-001", "missing-kp"]',
                    "core",
                    "practice",
                    "Use sum rule for disjoint alternatives.",
                    "easy",
                    "Confusing overlap breaks this rule.",
                ),
                (
                    "dmath-ch06-kp-003",
                    "二项式定理",
                    "§6-4",
                    "theorem",
                    "[]",
                    "core",
                    "derive",
                    "Expansion with binomial coefficients.</script>",
                    "medium",
                    "",
                ),
            ],
        )
        self.conn.executemany(
            "INSERT INTO kp_progress VALUES (?, ?)",
            [
                ("dmath-ch06-kp-001", "mastered"),
                ("dmath-ch06-kp-003", "reviewing"),
            ],
        )
        self.conn.executemany(
            "INSERT INTO problems VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    "dmath-ch06-prob-001",
                    '["dmath-ch06-kp-001", "dmath-ch06-kp-002"]',
                    "problem",
                    "solution",
                    "short-answer",
                    "textbook",
                ),
                (
                    "dmath-ch06-prob-002",
                    '["dmath-ch06-kp-002"]',
                    "problem",
                    "solution",
                    "short-answer",
                    "quiz",
                ),
            ],
        )
        self.conn.commit()

    def test_build_graph_data_extracts_nodes_edges_and_status(self):
        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )

        self.assertEqual(graph["meta"]["node_count"], 3)
        self.assertEqual(graph["meta"]["edge_count"], 1)
        by_id = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(by_id["dmath-ch06-kp-001"]["status"], "mastered")
        self.assertEqual(by_id["dmath-ch06-kp-001"]["degree"], 1)
        self.assertEqual(by_id["dmath-ch06-kp-002"]["degree"], 1)
        self.assertEqual(by_id["dmath-ch06-kp-003"]["degree"], 0)
        self.assertEqual(by_id["dmath-ch06-kp-002"]["problem_count"], 2)
        self.assertEqual(len(by_id["dmath-ch06-kp-002"]["problem_groups"]["new"]), 2)
        self.assertEqual(by_id["dmath-ch06-kp-002"]["section"], "§6-1")
        self.assertIn("x", by_id["dmath-ch06-kp-003"])
        self.assertIn("y", by_id["dmath-ch06-kp-003"])
        self.assertNotIn("solution", json.dumps(graph, ensure_ascii=False))

    def test_problem_text_is_not_truncated_in_graph_data(self):
        full_text = (
            "Use the binomial theorem to find the coefficient of "
            "$x ^ { 5 } y ^ { 8 }$ in $( x + y ) ^ { 13 }$ after collecting terms."
        )
        self.conn.execute(
            "UPDATE problems SET problem_text = ? WHERE problem_id = ?",
            (full_text, "dmath-ch06-prob-002"),
        )
        self.conn.commit()

        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )

        node = {item["id"]: item for item in graph["nodes"]}["dmath-ch06-kp-002"]
        texts = [problem["text"] for problem in node["problem_groups"]["new"]]
        self.assertIn(full_text, texts)
        self.assertNotIn("…", json.dumps(texts, ensure_ascii=False))

    def test_graph_label_column_is_used_when_present(self):
        self.conn.execute("ALTER TABLE knowledge_points ADD COLUMN graph_label TEXT")
        long_label = "数字逻辑设计_波形与时序分析"
        self.conn.execute(
            "UPDATE knowledge_points SET knowledge_item = ? WHERE kp_id = ?",
            (long_label, "dmath-ch06-kp-002"),
        )
        self.conn.execute(
            "UPDATE knowledge_points SET graph_label = ? WHERE kp_id = ?",
            ("乘法", "dmath-ch06-kp-001"),
        )
        self.conn.commit()

        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )

        by_id = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(by_id["dmath-ch06-kp-001"]["graph_label"], "乘法")
        self.assertEqual(by_id["dmath-ch06-kp-002"]["graph_label"], long_label)

    def test_layout_respects_minimum_node_distance_for_sample(self):
        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )
        nodes = graph["nodes"]

        for i, first in enumerate(nodes):
            for second in nodes[i + 1:]:
                distance = math.hypot(first["x"] - second["x"], first["y"] - second["y"])
                self.assertGreaterEqual(distance, render_graph_html.MIN_NODE_DISTANCE - 0.01)

    def test_future_problem_progress_overlays_wrong_status(self):
        self.conn.executescript(
            """
            CREATE TABLE problem_progress (
                problem_id TEXT PRIMARY KEY,
                status TEXT
            );
            INSERT INTO problem_progress VALUES ('dmath-ch06-prob-001', 'wrong');
            """
        )
        self.conn.commit()

        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )

        by_id = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(by_id["dmath-ch06-kp-001"]["status"], "wrong")
        self.assertEqual(by_id["dmath-ch06-kp-001"]["problem_states"]["wrong"], 1)
        self.assertEqual(by_id["dmath-ch06-kp-002"]["problem_states"]["wrong"], 1)

    def test_malformed_related_ids_are_ignored_with_warning(self):
        self.conn.execute(
            "UPDATE knowledge_points SET related_kp_ids = ? WHERE kp_id = ?",
            ("not-json", "dmath-ch06-kp-003"),
        )
        self.conn.commit()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            graph = render_graph_html.build_graph_data(
                self.conn,
                "dmath",
                "ch06",
                "Discrete Math",
            )

        self.assertEqual(graph["meta"]["node_count"], 3)
        self.assertIn("invalid JSON in related_kp_ids", stderr.getvalue())

    def test_render_html_is_standalone_and_contains_focus_interaction(self):
        graph = render_graph_html.build_graph_data(
            self.conn,
            "dmath",
            "ch06",
            "Discrete Math",
        )

        content = render_graph_html.render_html(graph)

        self.assertIn('id="graph-data" type="application/json"', content)
        self.assertIn("hoverId", content)
        self.assertIn("pinnedId", content)
        self.assertIn("neighbors", content)
        self.assertIn("dimmed", content)
        self.assertIn("statusFilter", content)
        self.assertIn("problem-groups", content)
        self.assertIn("zoomIn", content)
        self.assertIn("scaleBadge", content)
        self.assertIn("renderLatex", content)
        self.assertIn("renderRichText", content)
        self.assertIn("labelLines", content)
        self.assertIn("appendNodeLabel", content)
        self.assertIn('class="math block"', content)
        self.assertIn("halo.setAttribute('class', 'halo')", content)
        self.assertIn('<details class="problem-group"', content)
        self.assertIn("showToast", content)
        self.assertIn('<link rel="icon" href="data:,">', content)
        self.assertIn("<\\/script>", content)
        self.assertNotIn("<script src=", content)
        self.assertNotIn('rel="stylesheet"', content)
        self.assertNotIn("https://", content)

    def test_write_graph_html_writes_expected_file(self):
        out_dir = self.root / "output" / "dmath" / "ch06"

        target = render_graph_html.write_graph_html(
            self.db_path,
            "dmath",
            "ch06",
            "Discrete Math",
            out_dir,
        )

        self.assertEqual(target, out_dir / "ch06-graph.html")
        self.assertTrue(target.is_file())
        content = target.read_text(encoding="utf-8")
        self.assertIn("章节知识地图", content)
        self.assertIn("dmath-ch06-kp-001", content)


if __name__ == "__main__":
    unittest.main()
