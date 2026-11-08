"""Direct saved-Paper updates from Agent proposals (Q098/S008).

The former approval gate is retired: a valid `paper_update_proposal` applies
at the Data commit point (preview + update_saved revalidation), reports an
invalid target truthfully without writes, and never creates an approval
state or an approval-driven dispatch pause. Legacy pending approvals that
still exist on disk reconcile once through the conversation-open path
(covered in test_direct_paper_actions.py).
"""

import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class DirectPaperUpdateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        import sys
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.bridge import conversations
        from workbench.data import active_practice, attempts, practice_sets
        from workbench.data.pool import Pool
        from workbench.server import api

        self.conversations = conversations
        self.active_practice = active_practice
        self.attempts = attempts
        self.practice_sets = practice_sets
        self.api = api
        self.workspace = {
            "name": "dmath",
            "path": str(self.fixture.ws),
            "db": "pool/dmath.db",
            "active_course": "dmath",
            "active_chapter": "ch06",
        }
        self.pool = Pool(
            root=self.fixture.ws,
            db_path=self.fixture.db_path,
            course="dmath",
            chapter="ch06",
        )
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-002", '["dmath-ch06-kp-001"]',
             "P2", "S2", "calculation", "textbook"),
        )
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-003", '["dmath-ch06-kp-001"]',
             "P3", "S3", "calculation", "textbook"),
        )
        self.pool.commit()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def paper(self, ids, title="卷子"):
        return self.practice_sets.create_saved(self.pool, title, ids)

    def saved_order(self, paper_id):
        return [item["problem_id"] for item in self.practice_sets.get_saved(
            self.pool, paper_id)["plan"]["items"]]

    def conversation(self, paper_id, *, queue_paused=False):
        folder = self.pool.jobs_dir() / "conv-001"
        folder.mkdir(parents=True, exist_ok=True)
        record = {
            "conversation_id": "conv-001", "provider": "codex",
            "status": "running", "current_turn_id": "turn-001",
            "queue_paused": queue_paused, "created_at": "now", "updated_at": "now",
        }
        (folder / "conversation.json").write_text(
            json.dumps(record), encoding="utf-8")
        turn = {
            "turn_id": "turn-001", "status": "running",
            "message": "请重排试卷", "accepted_message": "请重排试卷",
            "context": {}, "created_at": "now", "updated_at": "now",
        }
        (folder / "turn-001.json").write_text(
            json.dumps(turn), encoding="utf-8")
        return folder, self.action(paper_id, [
            "dmath-ch06-prob-002", "dmath-ch06-prob-001",
        ])

    @staticmethod
    def action(paper_id, problem_ids):
        return "```lessonkit-action\n" + json.dumps({
            "type": "paper_update_proposal",
            "practice_set_id": paper_id,
            "problem_ids": problem_ids,
        }) + "\n```"

    def propose(self, folder, answer):
        turn_path = folder / "turn-001.json"
        event_path = folder / "turn-001.events.jsonl"
        self.conversations._store_answer(
            folder, folder / "conversation.json", turn_path, event_path,
            self.fixture.ws, self.workspace, "conv-001", "turn-001",
            "请重排试卷", {}, answer,
        )

    def queue_turn(self, folder, turn_id, message="继续"):
        (folder / f"{turn_id}.json").write_text(json.dumps({
            "turn_id": turn_id, "status": "queued", "message": message,
            "accepted_message": message, "context": {}, "queue_revision": 1,
            "queue_action": "queue", "created_at": "now", "updated_at": "now",
        }), encoding="utf-8")

    def test_proposal_action_contract_states_direct_application(self):
        from workbench.bridge import agent_contracts

        action_contract = agent_contracts.get("actions")
        prompt = self.conversations._prompt("reorder a saved paper", {
            "workspace": self.workspace,
        })
        self.assertIn('"type":"paper_update_proposal"', action_contract)
        self.assertIn("no separate approval click", action_contract)
        self.assertIn("paper_update_proposal", prompt)
        self.assertIn("无需学生批准", prompt)

        answer = self.action("ps-001", ["dmath-ch06-prob-001"])
        _, actions, notice = self.conversations._extract_action(answer, {})
        self.assertEqual(actions, [])
        self.assertEqual(notice["type"], "paper_update_proposal")

    def test_unrelated_notice_keeps_legacy_precedence_over_single_content_action(self):
        paper = self.paper(["dmath-ch06-prob-001"])
        folder, _ = self.conversation(paper["practice_set_id"])
        notice = {"type": "existing_notice"}
        with mock.patch.object(
            self.conversations, "_extract_action",
            return_value=("answer", [{"type": "check_ingest"}], notice),
        ), mock.patch.object(self.conversations, "_apply_content_action"):
            self.conversations._store_answer(
                folder, folder / "conversation.json", folder / "turn-001.json",
                folder / "turn-001.events.jsonl", self.fixture.ws,
                self.workspace, "conv-001", "turn-001", "message", {}, "answer",
            )
        turn = json.loads((folder / "turn-001.json").read_text(encoding="utf-8"))
        self.assertEqual(turn["action"], notice)

    def test_proposal_applies_directly_and_preserves_unfinished_practice(self):
        paper = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        self.active_practice.start_saved(self.pool, paper["practice_set_id"])
        self.active_practice.mark(self.pool, 0, "stuck")
        run = self.active_practice.current(self.pool)
        self.active_practice.save_draft(
            self.pool, run["execution_id"], 1, {"answer": "draft"},
            context=self.active_practice.submission_context(run, 1), sequence=1,
        )
        folder, answer = self.conversation(paper["practice_set_id"])
        self.queue_turn(folder, "turn-002", "B")

        self.propose(folder, answer)

        conversation = json.loads(
            (folder / "conversation.json").read_text(encoding="utf-8"))
        proposing_turn = json.loads(
            (folder / "turn-001.json").read_text(encoding="utf-8"))
        queued_turn = json.loads(
            (folder / "turn-002.json").read_text(encoding="utf-8"))
        self.assertEqual(self.saved_order(paper["practice_set_id"]), [
            "dmath-ch06-prob-002", "dmath-ch06-prob-001",
        ], "the requested update applied without an approval click")
        self.assertNotIn("paper_approval", proposing_turn,
                         "no approval state is created")
        self.assertNotEqual(conversation.get("queue_paused"), True,
                            "no approval-driven dispatch pause")
        self.assertEqual(proposing_turn["status"], "done")
        self.assertEqual(proposing_turn["action"]["type"], "paper_update_proposal")
        self.assertEqual(proposing_turn["action"]["result"]["applied_problem_ids"],
                         ["dmath-ch06-prob-002", "dmath-ch06-prob-001"])
        self.assertEqual(queued_turn["status"], "queued",
                         "a queued message submitted before the update is retained")
        with mock.patch.object(self.conversations.threading, "Thread") as thread:
            dispatched = self.conversations._dispatch_next(
                self.fixture.ws, self.pool.jobs_dir(), self.workspace, "conv-001")
            thread.return_value.start.assert_called_once()
        self.assertIsNotNone(dispatched,
                             "the retained queue continues without an approval gate")
        # A reorder keeps the run, its progress mark and the draft.
        current = self.active_practice.current(self.pool)
        self.assertEqual([item["item_id"] for item in current["items"]],
                         ["dmath-ch06-prob-002", "dmath-ch06-prob-001"])
        self.assertEqual(current["items"][1]["state"], "stuck",
                         "the progress mark follows its item through the reorder")
        self.assertEqual(current["items"][0]["draft"], {"answer": "draft"})

    def test_commit_point_revalidation_fails_without_write(self):
        from workbench.data import attempts

        first_id = "dmath-ch06-prob-001"
        second_id = "dmath-ch06-prob-002"
        paper = self.paper([first_id, second_id])
        other = self.paper([first_id, second_id], title="另一份卷子")
        self.active_practice.start_saved(self.pool, other["practice_set_id"])
        self.active_practice.mark(self.pool, 0, "stuck")
        self.active_practice.start_saved(self.pool, paper["practice_set_id"])
        self.active_practice.mark(self.pool, 0, "stuck")
        run = self.active_practice.current(self.pool)
        self.active_practice.save_draft(
            self.pool, run["execution_id"], 1, {"answer": "before update"},
            context=self.active_practice.submission_context(run, 1), sequence=1,
        )
        self.attempts.record_result(self.pool, first_id, "stuck", note="historical result")
        history_before = [tuple(row) for row in self.pool.connect().execute(
            "SELECT problem_id, status, note FROM problem_attempts ORDER BY id")]
        folder, answer = self.conversation(paper["practice_set_id"])

        real_update = self.conversations.practice_sets.update_saved

        def conflicting_update(pool, practice_set_id, **fields):
            # The Paper changed between the preview and the commit point.
            raise ValueError(
                "confirm the current Paper update preview before changing its items")

        with mock.patch.object(self.conversations.practice_sets,
                               "update_saved", conflicting_update):
            self.propose(folder, answer)

        proposing_turn = json.loads(
            (folder / "turn-001.json").read_text(encoding="utf-8"))
        self.assertEqual(self.saved_order(paper["practice_set_id"]),
                         [first_id, second_id],
                         "a stale confirmation writes nothing")
        self.assertNotIn("paper_approval", proposing_turn)
        self.assertIn("confirm the current Paper update preview",
                      proposing_turn["action"]["error"])
        current = self.active_practice.current(self.pool)
        self.assertEqual(current["items"][1]["draft"], {"answer": "before update"})
        self.assertEqual([tuple(row) for row in self.pool.connect().execute(
            "SELECT problem_id, status, note FROM problem_attempts ORDER BY id")],
            history_before)

        self.propose(folder, answer)

        self.assertEqual(self.saved_order(paper["practice_set_id"]),
                         [second_id, first_id])
        current = self.active_practice.current(self.pool)
        self.assertEqual([item["item_id"] for item in current["items"]],
                         [second_id, first_id])
        self.assertEqual(current["items"][0]["draft"], {"answer": "before update"})
        self.assertEqual([tuple(row) for row in self.pool.connect().execute(
            "SELECT problem_id, status, note FROM problem_attempts ORDER BY id")],
            history_before)
        self.assertEqual(self.practice_sets.get_saved(
            self.pool, other["practice_set_id"])["progress"]["completed"], 1)

    def test_direct_update_with_missing_paper_reports_without_write(self):
        paper_id = "ps-999"
        folder, answer = self.conversation(paper_id)
        self.propose(folder, answer)
        turn = json.loads((folder / "turn-001.json").read_text(encoding="utf-8"))
        self.assertNotIn("paper_approval", turn)
        self.assertIn("error", turn["action"])
        record = self.conversations.get(self.pool, "conv-001")
        self.assertIsNone(record.get("pending_paper_approval"))

    def test_reload_shows_applied_result_without_pending_state(self):
        paper = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        folder, answer = self.conversation(paper["practice_set_id"])
        self.queue_turn(folder, "turn-002", "B")
        self.queue_turn(folder, "turn-003", "C")
        self.propose(folder, answer)

        restored = self.conversations.get(self.pool, "conv-001")

        self.assertIsNone(restored["pending_paper_approval"])
        self.assertNotEqual(restored["queue_paused"], True)
        actions = [message.get("action") for message in restored["messages"]
                   if message.get("role") == "assistant" and message.get("action")]
        self.assertTrue(actions and actions[0].get("result"),
                        "the applied update is visible through the conversation")
        self.assertEqual(json.loads((folder / "turn-002.json").read_text(
            encoding="utf-8"))["status"], "queued")

    def test_legacy_approval_route_reports_conflict_without_pending(self):
        from workbench.server import app

        paper = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        folder, answer = self.conversation(paper["practice_set_id"])
        self.propose(folder, answer)
        server = app.create_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urllib.request.urlopen(
                base + "/api/w/dmath/ai/sessions/conv-001") as response:
                session = json.loads(response.read().decode("utf-8"))
            self.assertIsNone(session["pending_paper_approval"])
            request = urllib.request.Request(
                base + "/api/w/dmath/ai/sessions/conv-001/paper-approval",
                data=json.dumps({
                    "turn_id": "turn-001", "expected_revision": 1,
                    "decision": "cancel",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code, 409,
                             "an obsolete callback resolves nothing and writes nothing")
            self.assertEqual(self.saved_order(paper["practice_set_id"]),
                             ["dmath-ch06-prob-002", "dmath-ch06-prob-001"])
        finally:
            server.shutdown()
            server.server_close()

    def test_api_rejects_non_string_decision(self):
        with self.assertRaises(self.api.ApiError) as caught:
            self.api.ai_paper_approval(
                self.pool, self.workspace, {"conversation_id": "conv-001"},
                {"turn_id": "turn-001", "expected_revision": 1, "decision": []},
            )
        self.assertEqual(caught.exception.status, 400)


if __name__ == "__main__":
    unittest.main()
