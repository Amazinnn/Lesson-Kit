"""Direct Paper actions and legacy pending-approval reconciliation (WP03).

Baseline failure checks for retire-project-approval-gates: actions that
formerly required a project approval apply directly after validating actual
inputs, and a persisted legacy pending approval reconciles at most once when
the service opens the old conversation. These tests pin the target behavior
from the direct-project-actions / practice-set-export deltas; they fail
against the current approval-gated implementation until 2.1/2.2 land.
"""

import json
import unittest

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class DirectPaperActionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        import sys
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.bridge import conversations
        from workbench.data import practice_sets
        from workbench.data.pool import Pool

        self.conversations = conversations
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
        for problem_id in ("dmath-ch06-prob-002", "dmath-ch06-prob-003"):
            self.pool.connect().execute(
                "INSERT INTO problems "
                "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (problem_id, '["dmath-ch06-kp-001"]', problem_id[-3:], "S",
                 "calculation", "textbook"),
            )
        self.pool.commit()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def paper(self, ids, title="卷子"):
        return self.practice_sets.create_saved(self.pool, title, ids)[
            "practice_set_id"]

    def saved_order(self, paper_id):
        path = (self.fixture.ws / ".lessonkit" / "practice-sets"
                / f"{paper_id}.json")
        plan = json.loads(path.read_text(encoding="utf-8"))["plan"]
        return [item["problem_id"] for item in plan["items"]]

    @staticmethod
    def proposal_answer(paper_id, problem_ids):
        return "```lessonkit-action\n" + json.dumps({
            "type": "paper_update_proposal",
            "practice_set_id": paper_id,
            "problem_ids": problem_ids,
        }) + "\n```"

    def propose(self, paper_id, problem_ids, turn_id="turn-001"):
        folder = self.pool.jobs_dir() / "conv-001"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "conversation.json").write_text(json.dumps({
            "conversation_id": "conv-001", "provider": "codex",
            "status": "running", "current_turn_id": turn_id,
            "queue_paused": False, "created_at": "now", "updated_at": "now",
        }), encoding="utf-8")
        (folder / f"{turn_id}.json").write_text(json.dumps({
            "turn_id": turn_id, "status": "running",
            "message": "请重排试卷", "accepted_message": "请重排试卷",
            "context": {}, "created_at": "now", "updated_at": "now",
        }), encoding="utf-8")
        self.conversations._store_answer(
            folder, folder / "conversation.json", folder / f"{turn_id}.json",
            folder / f"{turn_id}.events.jsonl", self.fixture.ws,
            self.workspace, "conv-001", turn_id, "请重排试卷", {},
            self.proposal_answer(paper_id, problem_ids),
        )

    def turn(self, turn_id="turn-001"):
        path = self.pool.jobs_dir() / "conv-001" / f"{turn_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def conversation(self):
        path = self.pool.jobs_dir() / "conv-001" / "conversation.json"
        return json.loads(path.read_text(encoding="utf-8"))

    # -- 2.1 direct execution -------------------------------------------------

    def test_agent_paper_update_applies_directly_without_approval_or_pause(self):
        paper_id = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        self.propose(paper_id, ["dmath-ch06-prob-002", "dmath-ch06-prob-001"])
        self.assertEqual(
            self.saved_order(paper_id),
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
            "a valid requested Paper update applies at the commit point",
        )
        self.assertNotIn("paper_approval", self.turn(),
                         "no approval state is created for a direct action")
        self.assertNotEqual(self.conversation().get("queue_paused"), True,
                            "no approval-driven dispatch pause")
        record = self.conversations.get(self.pool, "conv-001")
        self.assertIsNone(record.get("pending_paper_approval"))

    def test_direct_update_with_missing_paper_fails_without_approval_state(self):
        self.propose("ps-999", ["dmath-ch06-prob-001"])
        turn = self.turn()
        self.assertNotIn("paper_approval", turn,
                         "an unresolved target is missing input, not an approval")
        self.assertNotEqual(self.conversation().get("queue_paused"), True)
        self.assertTrue(
            (turn.get("error") or turn.get("action_error")
             or turn.get("action", {}).get("error")),
            "the failure is reported truthfully on the turn",
        )

    # -- 2.2 legacy pending approval reconciles once --------------------------

    def legacy_pending(self, paper_id, problem_ids):
        """Freeze a faithful legacy pending approval artifact (pre-WP03 shape)."""
        try:
            preview = self.practice_sets.preview_update(
                self.pool, paper_id, problem_ids=list(problem_ids))
            confirmation = preview["confirmation"]
        except Exception:
            confirmation = None
        folder = self.pool.jobs_dir() / "conv-001"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "conversation.json").write_text(json.dumps({
            "conversation_id": "conv-001", "provider": "codex",
            "status": "running", "current_turn_id": "turn-001",
            "queue_paused": True, "created_at": "now", "updated_at": "now",
        }), encoding="utf-8")
        approval = {
            "conversation_id": "conv-001", "turn_id": "turn-001",
            "workspace_name": "dmath", "status": "pending", "revision": 1,
            "proposal": {"practice_set_id": paper_id,
                         "problem_ids": list(problem_ids)},
            "confirmation": confirmation,
        }
        (folder / "turn-001.json").write_text(json.dumps({
            "turn_id": "turn-001", "status": "done",
            "message": "请重排试卷", "accepted_message": "请重排试卷",
            "context": {}, "created_at": "now", "updated_at": "now",
            "paper_approval": approval,
        }), encoding="utf-8")
        return approval

    def test_legacy_pending_approval_reconciles_once_on_open(self):
        paper_id = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        approval = self.legacy_pending(paper_id, [
            "dmath-ch06-prob-002", "dmath-ch06-prob-001",
        ])
        self.assertEqual(self.saved_order(paper_id),
                         ["dmath-ch06-prob-001", "dmath-ch06-prob-002"],
                         "fixture precondition: the legacy action never wrote")
        record = self.conversations.get(self.pool, "conv-001")
        self.assertIsNone(record.get("pending_paper_approval"),
                          "the legacy pending state is consumed, not restored")
        self.assertEqual(
            self.saved_order(paper_id),
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
            "a still-valid unapplied action executes once during recovery",
        )
        self.assertNotEqual(self.conversation().get("queue_paused"), True)
        self.conversations.get(self.pool, "conv-001")
        self.assertEqual(
            self.saved_order(paper_id),
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
            "reopening the conversation cannot write a second time",
        )
        self.assertEqual(approval["proposal"]["practice_set_id"], paper_id)

    def test_legacy_pending_approval_with_missing_target_records_incomplete(self):
        self.legacy_pending("ps-999", ["dmath-ch06-prob-001"])
        record = self.conversations.get(self.pool, "conv-001")
        self.assertIsNone(record.get("pending_paper_approval"))
        turn = self.turn()
        self.assertTrue(
            (turn.get("error") or turn.get("action_error")
             or turn.get("action", {}).get("error")
             or "paper_approval" not in turn),
            "the invalid input is recorded truthfully instead of restored",
        )
        self.assertNotEqual(self.conversation().get("queue_paused"), True)

    def test_operational_failure_preserves_legacy_action_for_recovery(self):
        from unittest import mock
        for operation in ("preview_update", "update_saved"):
            with self.subTest(operation=operation):
                paper_id = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
                target = ["dmath-ch06-prob-002", "dmath-ch06-prob-001"]
                self.legacy_pending(paper_id, target)
                path = self.pool.jobs_dir() / "conv-001" / "turn-001.json"
                before = json.loads(path.read_text(encoding="utf-8"))["paper_approval"]
                with mock.patch.object(self.practice_sets, operation,
                                       side_effect=OSError("temporary disk failure")):
                    with self.assertRaisesRegex(OSError, "temporary disk failure"):
                        self.conversations.get(self.pool, "conv-001")
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["paper_approval"], before)
                self.conversations.get(self.pool, "conv-001")
                self.assertEqual(self.saved_order(paper_id), target)
                with mock.patch.object(self.practice_sets, "update_saved") as update:
                    self.conversations.get(self.pool, "conv-001")
                    update.assert_not_called()

    def test_obsolete_resolved_callback_performs_no_write(self):
        paper_id = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        approval = self.legacy_pending(paper_id, [
            "dmath-ch06-prob-002", "dmath-ch06-prob-001",
        ])
        approval["status"] = "cancelled"
        folder = self.pool.jobs_dir() / "conv-001"
        turn_path = folder / "turn-001.json"
        turn = json.loads(turn_path.read_text(encoding="utf-8"))
        turn["paper_approval"] = approval
        turn_path.write_text(json.dumps(turn), encoding="utf-8")
        before = self.saved_order(paper_id)
        self.conversations.get(self.pool, "conv-001")
        self.assertEqual(self.saved_order(paper_id), before,
                         "an obsolete callback repeats no operation")
        self.assertIsNone(
            self.conversations.get(self.pool, "conv-001")
            .get("pending_paper_approval"),
            "no new approval state is created",
        )

    def test_publication_file_disappearing_is_not_a_missing_paper(self):
        from unittest import mock
        paper_id = self.paper(["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        target = ["dmath-ch06-prob-002", "dmath-ch06-prob-001"]
        self.legacy_pending(paper_id, target)
        path = self.pool.jobs_dir() / "conv-001" / "turn-001.json"
        before = json.loads(path.read_text(encoding="utf-8"))["paper_approval"]
        with mock.patch.object(self.practice_sets, "_atomic_json",
                               side_effect=FileNotFoundError("temporary publication path")):
            with self.assertRaisesRegex(FileNotFoundError, "temporary publication path"):
                self.conversations.get(self.pool, "conv-001")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["paper_approval"], before)
        self.conversations.get(self.pool, "conv-001")
        self.assertEqual(self.saved_order(paper_id), target)
        with mock.patch.object(self.practice_sets, "update_saved") as update:
            self.conversations.get(self.pool, "conv-001")
            update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
