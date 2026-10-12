"""Synthetic retrieval cases that measure facts, evidence quality, and read cost."""

import unittest

from tests.workbench.fixtures import WorkspaceFixture


class RetrievalEvalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)
        conn = self.pool.connect()
        with conn:
            conn.execute(
                "INSERT INTO knowledge_points"
                " (kp_id, knowledge_item, body, knowledge_type, importance)"
                " VALUES (?, ?, ?, ?, ?)",
                ("dmath-ch07-kp-001", "Pigeonhole Principle",
                 "If more objects than boxes are placed into boxes, one box repeats.",
                 "concept-property", "core"),
            )
            conn.execute(
                "INSERT INTO problems"
                " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                ("dmath-ch07-prob-001", '["dmath-ch07-kp-001"]',
                 "Pigeonhole seating problem", "Use the pigeonhole principle.",
                 "proof", "textbook"),
            )
            conn.execute(
                "INSERT INTO problem_attempts"
                " (problem_id, status, note, created_at) VALUES (?, ?, ?, ?)",
                ("dmath-ch06-prob-001", "wrong", "Forgot an ordering condition.",
                 "2026-10-01 09:00:00"),
            )
            conn.execute(
                "INSERT INTO problem_attempts"
                " (problem_id, status, note, created_at) VALUES (?, ?, ?, ?)",
                ("dmath-ch07-prob-001", "mastered", "Recognized the box/object mapping.",
                 "2026-10-02 09:00:00"),
            )

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def manifest(self):
        return {"scenarios": [
            {
                "name": "find another knowledge point",
                "kind": "search",
                "entity": "kp",
                "query": "Pigeonhole Principle",
                "expected_ids": ["dmath-ch07-kp-001"],
            },
            {
                "name": "compare knowledge points across chapters",
                "kind": "compare",
                "entity": "kp",
                "left_query": "Counting",
                "right_query": "Pigeonhole Principle",
                "expected_ids": ["dmath-ch06-kp-001", "dmath-ch07-kp-001"],
            },
            {
                "name": "explain whether I used to miss this knowledge point",
                "kind": "kp_history",
                "kp_id": "dmath-ch06-kp-001",
                "expected_problem_text": "P1",
            },
        ]}

    def test_baseline_separates_recall_from_historical_evidence(self):
        from workbench.experiments import retrieval

        report = retrieval.evaluate(self.pool, self.manifest())

        # Current exact-keyword retrieval already handles another KP and a
        # cross-chapter comparison. The known gap is historical learner evidence:
        # one KP history read does not yet carry the text of attempted problems.
        self.assertEqual(report["summary"], {
            "scenarios": 3,
            "passed": 2,
            "failed": 1,
            "recall": 0.75,
            "primitive_reads": 4,
        })
        history = report["results"][2]
        self.assertFalse(history["passed"])
        self.assertEqual(history["detail"]["human_evidence_rows"], 0)
        self.assertIn("problem text", history["detail"]["requirement"])

    def test_evaluation_is_read_only(self):
        from workbench.experiments import retrieval

        conn = self.pool.connect()
        before = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("knowledge_points", "problems", "problem_attempts",
                          "feedback_events", "learner_signals")
        }

        retrieval.evaluate(self.pool, self.manifest())

        after = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in before
        }
        self.assertEqual(after, before)

    def test_human_evidence_check_does_not_require_an_internal_field_name(self):
        from workbench.experiments import retrieval

        rows = retrieval._human_problem_evidence({
            "anything": [{
                "problem_text": "Readable question",
                "status": "wrong",
                "internal_id": "opaque-123",
            }]
        })
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["problem_text"], "Readable question")

    def test_invalid_manifest_is_rejected_without_guessing(self):
        from workbench.experiments import retrieval

        with self.assertRaisesRegex(ValueError, "unknown kind"):
            retrieval.evaluate(self.pool, {"scenarios": [{"kind": "semantic_magic"}]})


if __name__ == "__main__":
    unittest.main()
