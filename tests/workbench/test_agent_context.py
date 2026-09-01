"""Authoritative page-context reconstruction for Agent turns."""

import sqlite3
import unittest
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


class AgentContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_kp_context_is_rebuilt_from_sqlite_not_browser_dom(self):
        from workbench.server import context

        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "UPDATE knowledge_points SET body=?, fragile=? WHERE kp_id=?",
            ("Authoritative body", "Common confusion", "dmath-ch06-kp-001"),
        )
        conn.execute(
            "INSERT INTO learning_current_state (item_type, item_id, state) VALUES (?, ?, ?)",
            ("kp", "dmath-ch06-kp-001", "review"),
        )
        conn.commit()
        conn.close()

        result = context.build(self.pool, self.workspace, {
            "route": "/w/dmath/kp/dmath-ch06-kp-001",
            "page_type": "kp",
            "kp_id": "dmath-ch06-kp-001",
            "dom": "FAKE BROWSER CONTENT",
        })

        self.assertEqual(result["workspace"]["name"], "dmath")
        self.assertEqual(result["workspace"]["course"], "dmath")
        self.assertEqual(result["current"]["kp"]["body"], "Authoritative body")
        self.assertEqual(result["current"]["current_state"]["state"], "review")
        self.assertNotIn("dom", result)
        self.assertNotIn("FAKE BROWSER CONTENT", str(result))

    def test_practice_draft_is_private_unless_explicitly_included(self):
        from workbench.server import context

        payload = {
            "route": "/w/dmath/practice",
            "page_type": "practice",
            "problem_id": "dmath-ch06-prob-001",
            "practice_mode": "immediate",
            "progress": {"seen": 2, "completed": 1},
            "draft_answer": "private answer",
            "draft_note": "private note",
        }
        private = context.build(self.pool, self.workspace, payload)
        attached = context.build(
            self.pool, self.workspace, {**payload, "include_draft": True}
        )

        self.assertNotIn("draft", private["current"])
        self.assertEqual(attached["current"]["draft"]["answer"], "private answer")
        self.assertEqual(attached["current"]["draft"]["note"], "private note")
        self.assertEqual(attached["current"]["problem"]["problem_id"], "dmath-ch06-prob-001")

    def test_graph_and_three_recent_distinct_objects_are_authoritative(self):
        from workbench.server import context

        result = context.build(self.pool, self.workspace, {
            "route": "/w/dmath/graph",
            "page_type": "graph",
            "selected_kp_id": "dmath-ch06-kp-001",
            "graph_filter": {"query": "count", "states": ["review", "mastered"]},
            "recent_objects": [
                {"type": "kp", "id": "dmath-ch06-kp-001"},
                {"type": "kp", "id": "dmath-ch06-kp-001"},
                {"type": "problem", "id": "dmath-ch06-prob-001"},
                {"type": "problem", "id": "missing"},
                {"type": "kp", "id": "missing"},
            ],
        })

        self.assertEqual(result["current"]["filter"]["query"], "count")
        self.assertEqual(result["current"]["filter"]["states"], ["review", "mastered"])
        self.assertEqual(result["current"]["selected"]["kp"]["kp_id"], "dmath-ch06-kp-001")
        self.assertEqual(
            [(item["type"], item["id"]) for item in result["recent_objects"]],
            [("kp", "dmath-ch06-kp-001"), ("problem", "dmath-ch06-prob-001")],
        )

    def test_check_intent_is_rebuilt_from_the_request_payload(self):
        from workbench.server import context

        result = context.build(self.pool, self.workspace, {"check_intent": True})
        self.assertTrue(result["check_intent"])
        result = context.build(self.pool, self.workspace, {})
        self.assertFalse(result["check_intent"])

    def test_goal_intent_is_rebuilt_from_the_request_payload(self):
        from workbench.server import context

        result = context.build(self.pool, self.workspace, {"goal_intent": True})
        self.assertTrue(result["goal_intent"])
        result = context.build(self.pool, self.workspace, {})
        self.assertFalse(result["goal_intent"])

    def test_check_intent_context_carries_next_free_ids(self):
        from workbench.server import context

        conn = sqlite3.connect(self.fixture.db_path)
        conn.executemany(
            "INSERT INTO flash_cards (card_id, kp_id, front, back, source_evidence) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                ("dmath-ch06-fc-001", "dmath-ch06-kp-001", "f", "b", "s"),
                ("dmath-ch06-fc-009", "dmath-ch06-kp-001", "f", "b", "s"),
            ],
        )
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text) VALUES (?, ?, ?)",
            ("dmath-ch06-mq-004", '["dmath-ch06-kp-001"]', "题干"),
        )
        conn.commit()
        conn.close()

        result = context.build(self.pool, self.workspace, {"check_intent": True})
        self.assertEqual(
            result["next_free_ids"],
            {"flash_card": "dmath-ch06-fc-010", "micro_quiz": "dmath-ch06-mq-005"},
        )
        without = context.build(self.pool, self.workspace, {})
        self.assertNotIn("next_free_ids", without)

    def test_context_asks_the_data_layer_for_next_ids(self):
        from workbench.server import context

        with mock.patch.object(
            self.pool, "next_free_content_ids",
            return_value={"flash_card": "fc-next", "micro_quiz": "mq-next"},
        ) as next_ids:
            result = context.build(
                self.pool, self.workspace, {"check_intent": True}
            )

        next_ids.assert_called_once_with("dmath-ch06")
        self.assertEqual(result["next_free_ids"]["flash_card"], "fc-next")


if __name__ == "__main__":
    unittest.main()
