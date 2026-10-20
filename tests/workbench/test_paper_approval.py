"""Human approval for Agent proposed saved Paper updates."""

import json
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class PaperApprovalTests(unittest.TestCase):
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

    def test_proposal_action_is_discovered_and_never_directly_updates_paper(self):
        from workbench.bridge import agent_contracts

        action_contract = agent_contracts.get("actions")
        prompt = self.conversations._prompt("reorder a saved paper", {
            "workspace": self.workspace,
        })
        self.assertIn('"type":"paper_update_proposal"', action_contract)
        self.assertIn("Do not run a `papers update` command", action_contract)
        self.assertIn("paper_update_proposal", prompt)
        self.assertIn("papers update", prompt)

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

    def queue_turn(self, folder, turn_id, message="继续"):
        (folder / f"{turn_id}.json").write_text(json.dumps({
            "turn_id": turn_id, "status": "queued", "message": message,
            "accepted_message": message, "context": {}, "queue_revision": 1,
            "queue_action": "queue", "created_at": "now", "updated_at": "now",
        }), encoding="utf-8")

    def test_proposal_persists_exact_preview_and_pauses_before_queued_turn(self):
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

        conversation = json.loads((folder / "conversation.json").read_text(encoding="utf-8"))
        proposing_turn = json.loads((folder / "turn-001.json").read_text(encoding="utf-8"))
        queued_turn = json.loads((folder / "turn-002.json").read_text(encoding="utf-8"))
        self.assertTrue(conversation["queue_paused"])
        self.assertEqual(proposing_turn["status"], "done")
        self.assertEqual(queued_turn["status"], "queued")
        self.assertEqual(proposing_turn["action"]["type"], "paper_update_proposal")
        approval = proposing_turn["paper_approval"]["projection"]
        self.assertEqual(approval["status"], "pending")
        self.assertEqual(approval["revision"], 1)
        self.assertEqual(approval["current_problem_ids"], [
            "dmath-ch06-prob-001", "dmath-ch06-prob-002",
        ])
        self.assertEqual(approval["proposed_problem_ids"], [
            "dmath-ch06-prob-002", "dmath-ch06-prob-001",
        ])
        self.assertTrue(approval["order_changed"])
        self.assertTrue(approval["resets_progress"])
        self.assertEqual(approval["completed_items"], 1)
        self.assertEqual(approval["draft_items"], 1)
        self.assertNotIn("confirmation", approval)
        self.assertIsNone(self.conversations._dispatch_next(
            self.fixture.ws, self.pool.jobs_dir(), self.workspace, "conv-001"))

    def test_pending_approval_queues_messages_blocks_continue_and_cancel_keeps_backlog_paused(self):
        paper = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        folder, answer = self.conversation(paper["practice_set_id"])
        self.propose(folder, answer)
        self.queue_turn(folder, "turn-002", "B")

        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.continue_queue(self.pool, self.workspace, "conv-001")
        queued = self.conversations.start_turn(
            self.pool, self.workspace, "conv-001", "C", {},
            queue_action="queue")
        self.assertEqual(queued["status"], "queued")
        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.start_turn(
                self.pool, self.workspace, "conv-001", "D", {},
                queue_action="interrupt")
        conversation = json.loads((folder / "conversation.json").read_text(encoding="utf-8"))
        queued_message = json.loads((folder / f"{queued['turn_id']}.json").read_text(
            encoding="utf-8"))
        self.assertEqual(conversation["queue_order"], ["turn-002", queued["turn_id"]])
        self.assertEqual(queued_message["message"], "C")
        self.assertFalse((folder / "turn-004.json").exists())
        self.assertEqual(
            json.loads((folder / "turn-001.json").read_text(encoding="utf-8"))[
                "paper_approval"]["projection"]["status"],
            "pending",
        )

        result = self.conversations.resolve_paper_approval(
            self.pool, self.workspace, "conv-001", "turn-001",
            expected_revision=1, decision="cancel")

        self.assertEqual(result["approval"]["status"], "cancelled")
        self.assertTrue(result["queue_paused"])
        self.assertEqual(
            [item["problem_id"] for item in self.practice_sets.get_saved(
                self.pool, paper["practice_set_id"])["plan"]["items"]],
            ["dmath-ch06-prob-001", "dmath-ch06-prob-002"],
        )
        with mock.patch.object(self.conversations.threading, "Thread") as thread:
            self.conversations.continue_queue(self.pool, self.workspace, "conv-001")
            thread.return_value.start.assert_called_once()
        conversation = json.loads((folder / "conversation.json").read_text(encoding="utf-8"))
        self.assertFalse(conversation["queue_paused"])

    def test_stale_preview_refreshes_without_write_then_approval_is_idempotent(self):
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
            self.pool, run["execution_id"], 1, {"answer": "before approval"},
            context=self.active_practice.submission_context(run, 1), sequence=1,
        )
        self.attempts.record_result(self.pool, first_id, "stuck", note="historical result")
        history_before = [tuple(row) for row in self.pool.connect().execute(
            "SELECT problem_id, status, note FROM problem_attempts ORDER BY id")]
        folder, answer = self.conversation(paper["practice_set_id"])
        self.propose(folder, answer)
        changed_draft = {"answer": "after proposal"}
        current = self.active_practice.current(self.pool)
        self.active_practice.save_draft(
            self.pool, current["execution_id"], 1, changed_draft,
            context=self.active_practice.submission_context(current, 1), sequence=2,
        )

        stale = self.conversations.resolve_paper_approval(
            self.pool, self.workspace, "conv-001", "turn-001",
            expected_revision=1, decision="approve")

        self.assertTrue(stale["stale"])
        self.assertEqual(stale["approval"]["status"], "pending")
        self.assertEqual(stale["approval"]["revision"], 2)
        self.assertEqual(stale["approval"]["draft_items"], 1)
        self.assertEqual([item["problem_id"] for item in self.practice_sets.get_saved(
            self.pool, paper["practice_set_id"])["plan"]["items"]], [first_id, second_id])
        self.assertEqual(self.active_practice.current(self.pool)["items"][1]["draft"],
                         changed_draft)

        approved = self.conversations.resolve_paper_approval(
            self.pool, self.workspace, "conv-001", "turn-001",
            expected_revision=2, decision="approve")
        saved = self.practice_sets.get_saved(self.pool, paper["practice_set_id"])
        updated_at = saved["updated_at"]
        duplicate = self.conversations.resolve_paper_approval(
            self.pool, self.workspace, "conv-001", "turn-001",
            expected_revision=2, decision="approve")

        self.assertEqual(approved["approval"]["status"], "approved")
        self.assertEqual(duplicate["approval"]["status"], "approved")
        self.assertEqual(self.practice_sets.get_saved(
            self.pool, paper["practice_set_id"])["updated_at"], updated_at)
        self.assertIsNone(self.active_practice.current(self.pool))
        self.assertEqual([tuple(row) for row in self.pool.connect().execute(
            "SELECT problem_id, status, note FROM problem_attempts ORDER BY id")], history_before)
        self.assertEqual(self.practice_sets.get_saved(
            self.pool, other["practice_set_id"])["progress"]["completed"], 1)
        self.assertEqual(
            [item["problem_id"] for item in saved["plan"]["items"]],
            [second_id, first_id],
        )

    def test_reload_restores_pending_projection_and_pause_without_dispatch(self):
        paper = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        folder, answer = self.conversation(paper["practice_set_id"])
        self.queue_turn(folder, "turn-002", "B")
        self.queue_turn(folder, "turn-003", "C")
        self.propose(folder, answer)
        record_path = folder / "conversation.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["queue_paused"] = False
        record_path.write_text(json.dumps(record), encoding="utf-8")

        restored = self.conversations.get(self.pool, "conv-001")

        self.assertTrue(restored["queue_paused"])
        self.assertEqual(restored["pending_paper_approval"]["status"], "pending")
        self.assertEqual(restored["pending_paper_approval"]["turn_id"], "turn-001")
        queued = json.loads((folder / "turn-002.json").read_text(encoding="utf-8"))
        self.assertEqual(queued["status"], "queued")

        approved = self.conversations.resolve_paper_approval(
            self.pool, self.workspace, "conv-001", "turn-001",
            expected_revision=1, decision="approve")
        self.assertEqual(approved["approval"]["status"], "approved")
        self.assertTrue(approved["queue_paused"])
        with mock.patch.object(self.conversations.threading, "Thread") as thread:
            continued = self.conversations.continue_queue(
                self.pool, self.workspace, "conv-001")
            thread.return_value.start.assert_called_once()
        self.assertEqual(continued["turn"]["turn_id"], "turn-002")
        self.assertEqual(json.loads((folder / "turn-003.json").read_text(
            encoding="utf-8"))["status"], "queued")

    def test_http_projection_and_paper_approval_route(self):
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
            self.assertEqual(
                session["pending_paper_approval"]["status"], "pending")
            self.assertNotIn(
                "confirmation", session["pending_paper_approval"])
            request = urllib.request.Request(
                base + "/api/w/dmath/ai/sessions/conv-001/paper-approval",
                data=json.dumps({
                    "turn_id": "turn-001", "expected_revision": 1,
                    "decision": "cancel",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(result["approval"]["status"], "cancelled")
            self.assertTrue(result["queue_paused"])
            self.assertIsNone(self.conversations.get(
                self.pool, "conv-001")["pending_paper_approval"])
        finally:
            server.shutdown()
            server.server_close()

    def test_api_rejects_non_string_decision(self):
        from workbench.server import api

        with self.assertRaises(api.ApiError) as caught:
            api.ai_paper_approval(
                self.pool, self.workspace, {"conversation_id": "conv-001"},
                {"turn_id": "turn-001", "expected_revision": 1, "decision": []},
            )
        self.assertEqual(caught.exception.status, 400)


if __name__ == "__main__":
    unittest.main()
