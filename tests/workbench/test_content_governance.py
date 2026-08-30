"""Current-content governance contracts for Agent-facing data operations."""

import importlib.util
import json
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


pool_schema = load_script("content_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script(
    "content_create_tables", Path("pipeline/scripts/create-tables.py")
)


class ContentGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_problem_candidate_schema(conn)
        pool_schema.ensure_workbench_schema(conn)
        conn.execute(
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, knowledge_type, importance) VALUES (?, ?, ?, ?)",
            ("dmath-ch06-kp-001", "乘法规则", "concept-property", "core"),
        )
        conn.execute(
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, knowledge_type, importance) VALUES (?, ?, ?, ?)",
            ("dmath-ch06-kp-004", "加法规则", "concept-property", "core"),
        )
        conn.execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "dmath-ch06-prob-003",
                json.dumps(["dmath-ch06-kp-001", "dmath-ch06-kp-004"]),
                "How many ordered pairs?",
                "Multiply the choices.",
                "calculation",
                "textbook",
            ),
        )
        conn.execute(
            "INSERT INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "dmath-ch06-rel-002",
                "dmath-ch06-kp-001",
                "dmath-ch06-kp-004",
                "contrasts",
                "symmetric",
                "medium",
            ),
        )
        conn.commit()
        conn.close()

        from workbench.data.pool import Pool

        self.pool = Pool(self.tmp.name, self.db_path, "dmath", "ch06")

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_scoped_sequence_starts_after_existing_and_never_reuses(self):
        from workbench.data import content

        self.assertEqual(content.next_id(self.pool, "kp"), "dmath-ch06-kp-005")
        self.assertEqual(content.next_id(self.pool, "relation"), "dmath-ch06-rel-003")
        content.delete(self.pool, "kp", "dmath-ch06-kp-004")
        self.assertEqual(content.next_id(self.pool, "kp"), "dmath-ch06-kp-006")
        self.assertEqual(content.next_id(self.pool, "problem"), "dmath-ch06-prob-004")
        self.assertEqual(content.next_id(self.pool, "candidate"), "dmath-ch06-cand-001")

    def test_get_list_search_and_history_are_zero_write(self):
        from workbench.data import content

        conn = self.pool.connect()
        before = conn.total_changes
        self.assertEqual(content.get(self.pool, "kp", "dmath-ch06-kp-001")["knowledge_item"], "乘法规则")
        self.assertEqual(len(content.list_items(self.pool, "problem")), 1)
        self.assertEqual(content.search(self.pool, "kp", "乘法")[0]["kp_id"], "dmath-ch06-kp-001")
        self.assertEqual(content.history(self.pool, "problem", "dmath-ch06-prob-003")["attempts"], [])
        self.assertEqual(conn.total_changes, before)

    def test_problem_delete_atomically_clears_dependent_learning_rows(self):
        from workbench.data import content

        conn = self.pool.connect()
        problem_id = "dmath-ch06-prob-003"
        conn.execute(
            "INSERT INTO problem_progress (problem_id, status) VALUES (?, ?)",
            (problem_id, "wrong"),
        )
        conn.execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text) VALUES (?, ?, ?)",
            (problem_id, "wrong", "draft"),
        )
        conn.execute(
            "INSERT INTO feedback_events (item_type, item_id, rating) VALUES (?, ?, ?)",
            ("problem", problem_id, 1),
        )
        conn.execute(
            "INSERT INTO review_schedule (item_type, item_id) VALUES (?, ?)",
            ("problem", problem_id),
        )
        conn.execute(
            "INSERT INTO learning_current_state (item_type, item_id, state) VALUES (?, ?, ?)",
            ("problem", problem_id, "needs_work"),
        )
        conn.execute(
            "INSERT INTO learner_signals "
            "(signal_id, target_type, target_id, signal_type) VALUES (?, ?, ?, ?)",
            ("sig-problem", "node", problem_id, "confusion"),
        )
        conn.commit()

        content.delete(self.pool, "problem", problem_id)

        for table, column in (
            ("problems", "problem_id"),
            ("problem_progress", "problem_id"),
            ("problem_attempts", "problem_id"),
            ("feedback_events", "item_id"),
            ("review_schedule", "item_id"),
            ("learning_current_state", "item_id"),
            ("learner_signals", "target_id"),
        ):
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (problem_id,)
            ).fetchone()[0]
            self.assertEqual(count, 0, table)

    def test_kp_delete_removes_membership_and_deletes_zero_owner_problem(self):
        from workbench.data import content

        conn = self.pool.connect()
        conn.execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "dmath-ch06-prob-004",
                json.dumps(["dmath-ch06-kp-001"]),
                "Only product rule",
                "calculation",
                "textbook",
            ),
        )
        conn.commit()

        content.delete(self.pool, "kp", "dmath-ch06-kp-001")

        shared = json.loads(
            conn.execute(
                "SELECT kp_ids FROM problems WHERE problem_id='dmath-ch06-prob-003'"
            ).fetchone()[0]
        )
        self.assertEqual(shared, ["dmath-ch06-kp-004"])
        self.assertIsNone(
            conn.execute(
                "SELECT 1 FROM problems WHERE problem_id='dmath-ch06-prob-004'"
            ).fetchone()
        )
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM knowledge_relations WHERE source_kp_id=? OR target_kp_id=?",
                ("dmath-ch06-kp-001", "dmath-ch06-kp-001"),
            ).fetchone()[0],
            0,
        )

    def test_kp_delete_clears_cards_and_legacy_dependents(self):
        from workbench.data import content

        conn = self.pool.connect()
        kp_id = "dmath-ch06-kp-001"
        card_id = "dmath-ch06-fc-001"
        conn.execute(
            "INSERT INTO flash_cards"
            " (card_id, kp_id, front, back, source_evidence) VALUES (?, ?, ?, ?, ?)",
            (card_id, kp_id, "front", "back", "source"),
        )
        conn.execute(
            "INSERT INTO feedback_events (item_type, item_id, rating) VALUES ('card', ?, 2)",
            (card_id,),
        )
        conn.execute(
            "INSERT INTO review_schedule (item_type, item_id) VALUES ('card', ?)",
            (card_id,),
        )
        conn.execute(
            "INSERT INTO learner_signals"
            " (signal_id, target_type, target_id, signal_type) VALUES (?, 'node', ?, 'weak_node')",
            (card_id + "-sig", card_id),
        )
        conn.execute(
            "INSERT INTO questions (q_id, question_text, answer_key, kp_id)"
            " VALUES ('q-001', 'question', 'answer', ?)",
            (kp_id,),
        )
        conn.execute(
            "INSERT INTO question_progress (q_id, note) VALUES ('q-001', 'note')"
        )
        conn.execute(
            "INSERT INTO kp_progress (kp_id, mastery_state) VALUES (?, 'grasping')",
            (kp_id,),
        )
        conn.commit()

        content.delete(self.pool, "kp", kp_id)

        for table, column, value in (
            ("flash_cards", "card_id", card_id),
            ("feedback_events", "item_id", card_id),
            ("review_schedule", "item_id", card_id),
            ("learner_signals", "target_id", card_id),
            ("questions", "q_id", "q-001"),
            ("question_progress", "q_id", "q-001"),
            ("kp_progress", "kp_id", kp_id),
        ):
            self.assertEqual(
                conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (value,)
                ).fetchone()[0],
                0,
                table,
            )

    def test_failed_delete_rolls_back_the_whole_cascade(self):
        from workbench.data import content

        conn = self.pool.connect()
        conn.executescript(
            """
            CREATE TRIGGER reject_problem_delete BEFORE DELETE ON problems
            BEGIN SELECT RAISE(ABORT, 'stop'); END;
            """
        )
        conn.execute(
            "INSERT INTO problem_progress (problem_id, status) VALUES (?, ?)",
            ("dmath-ch06-prob-003", "wrong"),
        )
        conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            content.delete(self.pool, "problem", "dmath-ch06-prob-003")

        self.assertIsNotNone(
            conn.execute(
                "SELECT 1 FROM problem_progress WHERE problem_id='dmath-ch06-prob-003'"
            ).fetchone()
        )


if __name__ == "__main__":
    unittest.main()
