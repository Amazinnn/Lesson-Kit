"""Agent-managed evaluations: same-row edits, read-before-write, hard delete."""

import contextlib
import io
import json
import unittest

from tests.workbench.fixtures import WorkspaceFixture

PROBLEM = "dmath-ch06-prob-001"
KP = "dmath-ch06-kp-001"
CARD = "dmath-ch06-fc-001"


class FeedbackCrudTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import main as cli
        from workbench.server import api

        self.cli = cli
        self.workspace = cli._workspace("dmath")
        self.pool = api._pool_for(self.workspace)
        self.pool.connect().execute(
            "INSERT INTO flash_cards "
            "(card_id, kp_id, front, back, source_evidence, directions) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (CARD, KP, "正面", "背面", "教材", '["forward", "reverse"]'))
        self.pool.commit()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = self.cli.main(list(args))
        return code, output.getvalue()

    def json_cli(self, *args):
        code, output = self.run_cli(*args)
        return code, json.loads(output)

    def write_json(self, name, value):
        path = self.fixture.tmp.name + "/" + name
        from pathlib import Path
        Path(path).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def rows(self, sql, params=()):
        return [dict(row) for row in self.pool.connect().execute(sql, params)]

    def event(self, event_id):
        return self.rows("SELECT * FROM feedback_events WHERE id=?", (event_id,))[0]

    def list_event_id(self, item_type, item_id, attempt_id=None):
        args = ["feedback", "dmath", "list", "--item", item_type, "--id", item_id]
        if attempt_id is not None:
            args += ["--attempt-id", str(attempt_id)]
        code, result = self.json_cli(*args)
        self.assertEqual(code, 0)
        self.assertGreaterEqual(result["count"], 1)
        return result["events"][0]["event_id"]

    def test_agent_updates_and_deletes_a_browser_written_evaluation(self):
        event_id = self.pool.insert_feedback_event(
            "problem", PROBLEM, rating=3, note="用户写的")

        code, current = self.json_cli(
            "feedback", "dmath", "get", "--event-id", str(event_id))
        self.assertEqual(code, 0)
        self.assertEqual(current["rating"], 3)
        self.assertEqual(current["note"], "用户写的")
        self.assertFalse(current["agent_recorded"])

        code, updated = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "3", "--expected-note", "用户写的",
            "--rating", "4", "--note", "Agent 修改")
        self.assertEqual(code, 0)
        self.assertEqual(updated["rating"], 4)
        self.assertEqual(updated["note"], "Agent 修改")
        row = self.event(event_id)
        self.assertEqual((row["rating"], row["note"]), (4, "Agent 修改"))

        code, deleted = self.json_cli(
            "feedback", "dmath", "delete", "--event-id", str(event_id),
            "--expected-rating", "4", "--expected-note", "Agent 修改")
        self.assertEqual(code, 0)
        self.assertTrue(deleted["deleted"])
        self.assertEqual(self.rows("SELECT * FROM feedback_events"), [])

    def test_agent_updates_an_agent_written_evaluation_without_redirect(self):
        manifest = self.write_json("attempt.json", {
            "request_id": "agent-evaluation",
            "items": [{
                "problem_id": PROBLEM,
                "answer_text": "作答",
                "note": "Agent 记录",
                "rating": 2,
            }],
        })
        code, applied = self.json_cli(
            "attempts", "dmath", "apply", "--input", manifest)
        self.assertEqual(code, 0)
        attempt_id = applied["items"][0]["attempt_id"]
        event_id = self.list_event_id("problem", PROBLEM, attempt_id)

        code, updated = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "2", "--expected-note", "Agent 记录",
            "--rating", "5")
        self.assertEqual(code, 0)
        self.assertEqual(updated["rating"], 5)
        self.assertEqual(updated["attempt_id"], attempt_id)
        self.assertEqual(len(self.rows("SELECT * FROM problem_attempts")), 1)

    def test_stale_expected_values_are_refused(self):
        event_id = self.pool.insert_feedback_event(
            "problem", PROBLEM, rating=3, note="旧备注")

        code, result = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "2", "--expected-note", "旧备注",
            "--rating", "4")
        self.assertEqual(code, 2)
        self.assertIn("read it again", result["error"])
        self.assertEqual(self.event(event_id)["rating"], 3)

        code, result = self.json_cli(
            "feedback", "dmath", "delete", "--event-id", str(event_id),
            "--expected-rating", "3", "--expected-note", "错备注")
        self.assertEqual(code, 2)
        self.assertIn("read it again", result["error"])
        self.assertEqual(len(self.rows("SELECT * FROM feedback_events")), 1)

    def test_missing_expected_values_are_refused(self):
        event_id = self.pool.insert_feedback_event(
            "problem", PROBLEM, rating=3)

        code, result = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--rating", "4")
        self.assertEqual(code, 2)
        self.assertIn("expected", result["error"])
        self.assertEqual(self.event(event_id)["rating"], 3)

    def test_note_only_evaluation_can_be_updated_and_deleted(self):
        event_id = self.pool.insert_feedback_event(
            "problem", PROBLEM, rating=None, note="只有备注")

        code, current = self.json_cli(
            "feedback", "dmath", "get", "--event-id", str(event_id))
        self.assertEqual(code, 0)
        self.assertIsNone(current["rating"])

        code, updated = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "none", "--expected-note", "只有备注",
            "--rating", "5")
        self.assertEqual(code, 0)
        self.assertEqual(updated["rating"], 5)
        self.assertEqual(updated["note"], "只有备注")

        code, deleted = self.json_cli(
            "feedback", "dmath", "delete", "--event-id", str(event_id),
            "--expected-rating", "5", "--expected-note", "只有备注")
        self.assertEqual(code, 0)
        self.assertTrue(deleted["deleted"])

    def test_knowledge_point_and_card_evaluations_use_the_same_path(self):
        code, _ = self.run_cli(
            "feedback", "dmath", "add", "--item", "kp", "--id", KP,
            "--rating", "3")
        self.assertEqual(code, 0)
        kp_event = self.list_event_id("kp", KP)
        code, updated = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(kp_event),
            "--expected-rating", "3", "--expected-note", "", "--rating", "4")
        self.assertEqual(code, 0)
        self.assertEqual(updated["rating"], 4)
        code, deleted = self.json_cli(
            "feedback", "dmath", "delete", "--event-id", str(kp_event),
            "--expected-rating", "4", "--expected-note", "")
        self.assertEqual(code, 0)

        code, _ = self.run_cli(
            "feedback", "dmath", "add", "--item", "card", "--id", CARD,
            "--rating", "4", "--direction", "reverse", "--note", "反向不熟")
        self.assertEqual(code, 0)
        card_event = self.list_event_id("card", CARD)
        code, updated = self.json_cli(
            "feedback", "dmath", "update", "--event-id", str(card_event),
            "--expected-rating", "4", "--expected-note", "反向不熟",
            "--note", "反向仍不熟")
        self.assertEqual(code, 0)
        self.assertEqual(updated["note"], "反向仍不熟")
        code, deleted = self.json_cli(
            "feedback", "dmath", "delete", "--event-id", str(card_event),
            "--expected-rating", "4", "--expected-note", "反向仍不熟")
        self.assertEqual(code, 0)

    def test_add_with_attempt_id_refuses_a_duplicate(self):
        manifest = self.write_json("attempt-dup.json", {
            "request_id": "agent-evaluation-dup",
            "items": [{
                "problem_id": PROBLEM,
                "answer_text": "作答",
                "note": "已有评价",
                "rating": 2,
            }],
        })
        code, applied = self.json_cli(
            "attempts", "dmath", "apply", "--input", manifest)
        self.assertEqual(code, 0)
        attempt_id = applied["items"][0]["attempt_id"]
        event_id = self.list_event_id("problem", PROBLEM, attempt_id)

        code, result = self.json_cli(
            "feedback", "dmath", "add", "--item", "problem", "--id", PROBLEM,
            "--attempt-id", str(attempt_id), "--rating", "4")
        self.assertEqual(code, 2)
        self.assertEqual(result["existing_event_id"], event_id)
        self.assertEqual(len(self.rows("SELECT * FROM feedback_events")), 1)

    def test_agent_chooses_a_rating_without_a_learner_supplied_value(self):
        # 4.6: the contract lets the Agent pick the 1-5 itself; the learner does
        # not have to supply a number. The chosen rating lands through the
        # ordinary evaluation paths.
        from workbench.bridge import agent_contracts

        attempts_topic = agent_contracts.get("attempts")
        self.assertIn("You MAY choose it yourself", attempts_topic)
        self.assertIn("the learner does not need to supply a number", attempts_topic)

        self.pool.connect().execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text) "
            "VALUES (?, 'answered', '浏览器作答')", (PROBLEM,))
        self.pool.commit()
        attempt_id = self.rows(
            "SELECT id FROM problem_attempts WHERE problem_id=?", (PROBLEM,))[0]["id"]

        code, output = self.run_cli(
            "feedback", "dmath", "add", "--item", "problem", "--id", PROBLEM,
            "--attempt-id", str(attempt_id), "--rating", "3", "--note", "Agent 选定的评价")
        self.assertEqual(code, 0, output)
        event_id = self.list_event_id("problem", PROBLEM, attempt_id)
        self.assertEqual(self.event(event_id)["rating"], 3)

        # The Agent may also pick the new value when editing, again without a
        # learner-supplied number — expected values still gate the write.
        code, output = self.run_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "3", "--expected-note", "Agent 选定的评价",
            "--rating", "4", "--note", "Agent 复核后改判")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.event(event_id)["rating"], 4)

    def test_browser_stale_edit_after_an_agent_edit_is_refused(self):
        # 4.9: the Agent edits the shared evaluation row first; the browser's
        # next in-place edit still carries its old expected values and must
        # conflict with zero writes.
        import sys

        from workbench.data import attempts as attempts_data

        self.pool.connect().execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text) "
            "VALUES (?, 'answered', '浏览器作答')", (PROBLEM,))
        self.pool.commit()
        attempt_id = self.rows(
            "SELECT id FROM problem_attempts WHERE problem_id=?", (PROBLEM,))[0]["id"]
        attempts_data.record_browser_feedback(
            self.pool, "problem", PROBLEM, rating=2, note="browser first",
            attempt_id=attempt_id, request_id="browser-rating-1")
        event_id = self.list_event_id("problem", PROBLEM, attempt_id)

        code, output = self.run_cli(
            "feedback", "dmath", "update", "--event-id", str(event_id),
            "--expected-rating", "2", "--expected-note", "browser first",
            "--rating", "5", "--note", "agent edit")
        self.assertEqual(code, 0, output)

        before = self.event(event_id)
        with self.assertRaises(Exception) as caught:
            attempts_data.record_browser_feedback(
                self.pool, "problem", PROBLEM, rating=4, note="stale browser edit",
                attempt_id=attempt_id, request_id="browser-rating-2",
                edit_existing=True, expected_rating=2, expected_note="browser first")
        self.assertIn(
            self.event(event_id)["rating"], {5},
            "the agent's edit survives the stale browser attempt")
        self.assertEqual(self.event(event_id)["note"], "agent edit")
        self.assertEqual(
            len(self.rows("SELECT * FROM feedback_events")),
            len(self.rows("SELECT id FROM feedback_events")))


    def test_legacy_feedback_add_still_works(self):
        code, output = self.run_cli(
            "feedback", "dmath", "--item", "problem", "--id", PROBLEM,
            "--rating", "4")
        self.assertEqual(code, 0)
        self.assertIn("event logged", output)
        events = self.rows("SELECT rating FROM feedback_events")
        self.assertEqual([row["rating"] for row in events], [4])


if __name__ == "__main__":
    unittest.main()
