"""Focused tests for persisted conversation queue order and direct handoff."""

import json
import threading
import unittest
import urllib.request
from pathlib import Path
from urllib.error import HTTPError
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


class QueueBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)
        from workbench.bridge import conversations
        self.conversations = conversations

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def create(self):
        with mock.patch.object(self.conversations.conversation_providers, "get",
                               return_value={"name": "codex"}), \
                mock.patch.object(self.conversations, "_resolve_target", return_value={
                    "provider": "codex", "model": None, "args": [], "entry": None,
                }):
            return self.conversations.create(self.pool, "codex")

    def record(self, conversation_id):
        path = self.pool.jobs_dir() / conversation_id / "conversation.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write_turn(self, conversation_id, turn_id, *, status="queued", message=None,
                   queue_action="queue", **fields):
        path = self.pool.jobs_dir() / conversation_id / f"{turn_id}.json"
        turn = {
            "turn_id": turn_id,
            "status": status,
            "message": message or turn_id,
            "accepted_message": message or turn_id,
            "context": {"anchor": {"route": f"/{turn_id}"}},
            "queue_revision": 1,
            "queue_action": queue_action,
            **fields,
        }
        self.conversations._write_json(path, turn)
        return turn

    def running_turn(self, conversation_id, turn_id="turn-001"):
        folder = self.pool.jobs_dir() / conversation_id
        conversation_path, conversation = self.record(conversation_id)
        conversation.update({
            "status": "running", "current_turn_id": turn_id,
            "queue_paused": False,
        })
        conversation.setdefault("queue_order", [])
        self.conversations._write_json(conversation_path, conversation)
        self.write_turn(conversation_id, turn_id, status="running")
        key = (str(folder), turn_id)
        self.conversations._ACTIVE_TURNS.add(key)
        self.addCleanup(self.conversations._ACTIVE_TURNS.discard, key)
        return key

    def test_session_reads_fifo_queue_order_and_current_revisions(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        self.running_turn(conversation_id)

        b = self.conversations.start_turn(
            self.pool, self.workspace, conversation_id, "B", {"route": "/b"},
        )
        c = self.conversations.start_turn(
            self.pool, self.workspace, conversation_id, "C", {"route": "/c"},
        )

        session = self.conversations.get(self.pool, conversation_id)
        self.assertEqual(session["queue_order"], [b["turn_id"], c["turn_id"]])
        revisions = {
            item["turn_id"]: item["queue_revision"]
            for item in session["messages"] if item.get("role") == "user"
        }
        self.assertEqual(revisions[b["turn_id"]], 1)
        self.assertEqual(revisions[c["turn_id"]], 1)

    def test_legacy_session_reads_numeric_fifo_without_rewriting(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        path, record = self.record(conversation_id)
        record.pop("queue_order", None)
        self.conversations._write_json(path, record)
        self.write_turn(conversation_id, "turn-010")
        self.write_turn(conversation_id, "turn-002")
        before = path.read_bytes()

        session = self.conversations.get(self.pool, conversation_id)

        self.assertEqual(session["queue_order"], ["turn-002", "turn-010"])
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn("queue_order", json.loads(path.read_text(encoding="utf-8")))

    def test_reorder_uses_expected_order_cas_and_persists_the_permutation(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        self.running_turn(conversation_id)
        b = self.conversations.start_turn(self.pool, self.workspace, conversation_id, "B", {})
        c = self.conversations.start_turn(self.pool, self.workspace, conversation_id, "C", {})

        result = self.conversations.reorder_queue(
            self.pool, conversation_id, [b["turn_id"], c["turn_id"]],
            [c["turn_id"], b["turn_id"]],
        )
        self.assertEqual(result, {
            "conversation_id": conversation_id,
            "queue_order": [c["turn_id"], b["turn_id"]],
        })
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [c["turn_id"], b["turn_id"]])

        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.reorder_queue(
                self.pool, conversation_id, [b["turn_id"], c["turn_id"]],
                [b["turn_id"], c["turn_id"]],
            )
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [c["turn_id"], b["turn_id"]])

        old_key = (str(self.pool.jobs_dir() / conversation_id), "turn-001")
        self.conversations._finish(
            self.pool.jobs_dir() / conversation_id, conversation_id, "turn-001", "done", None,
        )
        self.conversations._ACTIVE_TURNS.discard(old_key)
        with mock.patch.object(threading.Thread, "start", return_value=None):
            dispatched = self.conversations._dispatch_next(
                self.pool.root, self.pool.jobs_dir(), self.workspace, conversation_id,
            )
        self.assertEqual(dispatched["turn_id"], c["turn_id"])
        self.assertEqual(dispatched["status"], "running")
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [b["turn_id"]])
        self.conversations.remove_pending(
            self.pool, conversation_id, b["turn_id"], expected_revision=1,
        )
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"], [])

    def test_send_now_keeps_identity_and_is_idempotent_after_a_later_turn_starts(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        old_key = self.running_turn(conversation_id)
        b = self.conversations.start_turn(
            self.pool, self.workspace, conversation_id, "B original", {"route": "/captured"},
            submission_id="submission-B", submitted_fields={"page_type": "kp"},
        )
        c = self.conversations.start_turn(self.pool, self.workspace, conversation_id, "C", {})
        self.conversations.edit_pending(
            self.pool, conversation_id, b["turn_id"], "B edited", expected_revision=1,
        )
        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.interrupt_pending(
                self.pool, self.workspace, conversation_id, b["turn_id"],
                expected_revision=1,
            )

        promoted = self.conversations.interrupt_pending(
            self.pool, self.workspace, conversation_id, b["turn_id"],
            expected_revision=2,
        )
        record = self.conversations._get_turn_record(self.pool, conversation_id, b["turn_id"])
        self.assertEqual(promoted["status"], "waiting_for_stop")
        self.assertEqual(promoted["turn_id"], b["turn_id"])
        self.assertEqual(promoted["message"], "B edited")
        self.assertEqual(record["accepted_message"], "B original")
        self.assertEqual(record["context"], {"route": "/captured"})
        self.assertEqual(record["submission_id"], "submission-B")
        self.assertTrue(record["promoted_from_queue"])
        self.assertEqual(record["interrupt_target_turn_id"], "turn-001")
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [c["turn_id"]])

        self.conversations._ACTIVE_TURNS.discard(old_key)
        later_key = (str(self.pool.jobs_dir() / conversation_id), b["turn_id"])
        self.conversations._ACTIVE_TURNS.add(later_key)
        self.addCleanup(self.conversations._ACTIVE_TURNS.discard, later_key)
        conversation_path, current = self.record(conversation_id)
        current.update({"status": "running", "current_turn_id": b["turn_id"]})
        self.conversations._write_json(conversation_path, current)
        record.update({"status": "running"})
        self.conversations._write_json(
            self.pool.jobs_dir() / conversation_id / f"{b['turn_id']}.json", record,
        )

        repeated = self.conversations.interrupt_pending(
            self.pool, self.workspace, conversation_id, b["turn_id"],
            expected_revision=2,
        )
        self.assertEqual(repeated["status"], "running")
        self.assertEqual(repeated["turn_id"], b["turn_id"])
        self.assertNotIn(later_key, self.conversations._CANCEL_REQUESTS)

    def test_send_now_conflicts_after_an_ordinary_target_starts(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        folder = self.pool.jobs_dir() / conversation_id
        target = self.write_turn(conversation_id, "turn-001", status="running", message="B")
        conversation_path, record = self.record(conversation_id)
        record.update({"status": "running", "current_turn_id": target["turn_id"]})
        self.conversations._write_json(conversation_path, record)
        key = (str(folder), target["turn_id"])
        self.conversations._ACTIVE_TURNS.add(key)
        self.addCleanup(self.conversations._ACTIVE_TURNS.discard, key)

        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.interrupt_pending(
                self.pool, self.workspace, conversation_id, target["turn_id"],
                expected_revision=1,
            )

        current = json.loads((folder / f"{target['turn_id']}.json").read_text(encoding="utf-8"))
        self.assertEqual(current["status"], "running")
        self.assertNotIn(key, self.conversations._CANCEL_REQUESTS)

    def test_send_now_racing_with_finish_waits_for_worker_release(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        folder = self.pool.jobs_dir() / conversation_id
        old_key = self.running_turn(conversation_id)
        b = self.conversations.start_turn(self.pool, self.workspace, conversation_id, "B", {})
        c = self.conversations.start_turn(self.pool, self.workspace, conversation_id, "C", {})

        self.conversations._finish(folder, conversation_id, "turn-001", "done", None)
        promoted = self.conversations.interrupt_pending(
            self.pool, self.workspace, conversation_id, b["turn_id"],
            expected_revision=1,
        )
        self.assertEqual(promoted["status"], "waiting_for_stop")
        self.assertEqual(promoted["interrupt_target_turn_id"], "turn-001")
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [c["turn_id"]])

        self.conversations._ACTIVE_TURNS.discard(old_key)
        with mock.patch.object(self.conversations, "_start_turn_locked",
                               return_value={"turn_id": b["turn_id"], "status": "running"}) as start:
            dispatched = self.conversations._dispatch_next(
                self.pool.root, self.pool.jobs_dir(), self.workspace, conversation_id,
            )
        self.assertEqual(dispatched["turn_id"], b["turn_id"])
        self.assertEqual(start.call_args.args[-1]["turn_id"], b["turn_id"])

    def test_direct_interrupt_during_terminal_cleanup_waits_for_owner_release(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        folder = self.pool.jobs_dir() / conversation_id
        old_key = self.running_turn(conversation_id)
        # _finish persists the old worker's terminal result before its thread
        # releases ownership in _run_turn_safely.finally.
        self.conversations._finish(folder, conversation_id, "turn-001", "done", None)

        handoff = self.conversations.start_turn(
            self.pool, self.workspace, conversation_id, "D", {},
            queue_action="interrupt",
        )

        self.assertEqual(handoff["status"], "waiting_for_stop")
        self.assertEqual(handoff["interrupt_target_turn_id"], "turn-001")
        self.assertIsNone(self.conversations._dispatch_next(
            self.pool.root, self.pool.jobs_dir(), self.workspace, conversation_id,
        ))
        self.conversations._ACTIVE_TURNS.discard(old_key)
        with mock.patch.object(self.conversations, "_start_turn_locked",
                               return_value={"turn_id": handoff["turn_id"],
                                             "status": "running"}) as start:
            dispatched = self.conversations._dispatch_next(
                self.pool.root, self.pool.jobs_dir(), self.workspace, conversation_id,
            )
        self.assertEqual(dispatched["turn_id"], handoff["turn_id"])
        self.assertEqual(start.call_args.args[-1]["turn_id"], handoff["turn_id"])

    def test_new_interrupt_starts_directly_when_idle_with_paused_queue(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        folder = self.pool.jobs_dir() / conversation_id
        self.write_turn(conversation_id, "turn-001", message="B")
        conversation_path, record = self.record(conversation_id)
        record.update({"queue_paused": True, "queue_order": ["turn-001"]})
        self.conversations._write_json(conversation_path, record)

        def start_direct(_root, _jobs_dir, _workspace, _conversation_id, turn):
            turn_path = folder / f"{turn['turn_id']}.json"
            current_turn = json.loads(turn_path.read_text(encoding="utf-8"))
            current_turn["status"] = "running"
            self.conversations._write_json(turn_path, current_turn)
            current = json.loads(conversation_path.read_text(encoding="utf-8"))
            current.update({"status": "running", "current_turn_id": turn["turn_id"]})
            self.conversations._write_json(conversation_path, current)
            return self.conversations._turn_response(current_turn)

        with mock.patch.object(self.conversations, "_start_turn_locked", side_effect=start_direct):
            result = self.conversations.start_turn(
                self.pool, self.workspace, conversation_id, "D", {},
                queue_action="interrupt",
            )

        self.assertEqual(result["status"], "running")
        self.assertEqual(result["queue_action"], "interrupt")
        self.assertNotIn(result["turn_id"], self.conversations.get(
            self.pool, conversation_id,
        )["queue_order"])
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         ["turn-001"])
        self.assertTrue(self.conversations.get(self.pool, conversation_id)["queue_paused"])

    def test_send_now_starts_directly_when_idle_without_unpausing_peers(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        folder = self.pool.jobs_dir() / conversation_id
        b = self.write_turn(conversation_id, "turn-001", message="B")
        c = self.write_turn(conversation_id, "turn-002", message="C")
        conversation_path, record = self.record(conversation_id)
        record.update({"queue_paused": True, "queue_order": ["turn-001", "turn-002"]})
        self.conversations._write_json(conversation_path, record)

        def start_direct(_root, _jobs_dir, _workspace, _conversation_id, turn):
            turn_path = folder / f"{turn['turn_id']}.json"
            current_turn = json.loads(turn_path.read_text(encoding="utf-8"))
            current_turn["status"] = "running"
            self.conversations._write_json(turn_path, current_turn)
            current = json.loads(conversation_path.read_text(encoding="utf-8"))
            current.update({"status": "running", "current_turn_id": turn["turn_id"]})
            self.conversations._write_json(conversation_path, current)
            return self.conversations._turn_response(current_turn)

        with mock.patch.object(self.conversations, "_start_turn_locked", side_effect=start_direct) as start:
            result = self.conversations.interrupt_pending(
                self.pool, self.workspace, conversation_id, b["turn_id"],
                expected_revision=1,
            )

        self.assertEqual(result["status"], "running")
        self.assertEqual(start.call_args.args[-1]["turn_id"], b["turn_id"])
        current = json.loads(conversation_path.read_text(encoding="utf-8"))
        self.assertTrue(current["queue_paused"])
        self.assertEqual(current["queue_order"], [c["turn_id"]])
        self.assertEqual(json.loads((folder / f"{c['turn_id']}.json").read_text(
            encoding="utf-8"))["status"], "queued")

    def test_approval_rejects_interrupt_and_send_now_before_mutation(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        self.write_turn(
            conversation_id, "turn-001", status="done", message="proposer",
            paper_approval={"status": "pending", "revision": 1},
        )
        target = self.write_turn(conversation_id, "turn-002", message="B")
        conversation_path, record = self.record(conversation_id)
        record["queue_order"] = [target["turn_id"]]
        self.conversations._write_json(conversation_path, record)
        before = json.loads((self.pool.jobs_dir() / conversation_id / "turn-002.json")
                            .read_text(encoding="utf-8"))

        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.interrupt_pending(
                self.pool, self.workspace, conversation_id, target["turn_id"],
                expected_revision=1,
            )
        with self.assertRaises(self.conversations.ConversationConflict):
            self.conversations.start_turn(
                self.pool, self.workspace, conversation_id, "new interrupt", {},
                submission_id="interrupt-id", queue_action="interrupt",
            )

        after = json.loads((self.pool.jobs_dir() / conversation_id / "turn-002.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual(after, before)
        self.assertFalse((self.pool.jobs_dir() / conversation_id / "turn-003.json").exists())
        self.assertEqual(self.conversations.get(self.pool, conversation_id)["queue_order"],
                         [target["turn_id"]])

    def test_recovery_fails_unstarted_interrupt_instead_of_queueing_or_replaying(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        old_key = self.running_turn(conversation_id)
        self.conversations._ACTIVE_TURNS.discard(old_key)
        handoff = self.write_turn(
            conversation_id, "turn-002", status="waiting_for_stop", message="D",
            queue_action="interrupt", interrupt_target_turn_id="turn-001",
        )
        queued = self.write_turn(conversation_id, "turn-003", message="B")
        conversation_path, record = self.record(conversation_id)
        record["queue_order"] = [queued["turn_id"]]
        self.conversations._write_json(conversation_path, record)

        session = self.conversations.get(self.pool, conversation_id)

        self.assertEqual(self.conversations.get_turn(
            self.pool, conversation_id, handoff["turn_id"],
        )["status"], "failed")
        self.assertEqual(session["queue_order"], [queued["turn_id"]])
        self.assertTrue(session["queue_paused"])

    def test_recovery_does_not_leave_a_legacy_queued_interrupt_behind_live_owner(self):
        conversation = self.create()
        conversation_id = conversation["conversation_id"]
        self.running_turn(conversation_id)
        orphan = self.write_turn(
            conversation_id, "turn-002", status="queued", message="D",
            queue_action="interrupt", interrupt_target_turn_id="turn-001",
        )
        conversation_path, record = self.record(conversation_id)
        record["queue_order"] = [orphan["turn_id"]]
        self.conversations._write_json(conversation_path, record)

        session = self.conversations.get(self.pool, conversation_id)

        recovered = self.conversations.get_turn(
            self.pool, conversation_id, orphan["turn_id"],
        )
        self.assertEqual(recovered["status"], "failed")
        self.assertEqual(session["status"], "running")
        self.assertEqual(session["current_turn_id"], "turn-001")
        self.assertEqual(session["queue_order"], [])
        self.assertTrue(session["queue_paused"])


class QueueApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server import app
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
            method=method,
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def error(self, method, path, payload):
        with self.assertRaises(HTTPError) as ctx:
            self.request(method, path, payload)
        return ctx.exception.code, json.loads(ctx.exception.read().decode("utf-8"))

    def create_session(self):
        from workbench.bridge import conversation_providers
        target = {"provider": "codex", "model": None, "args": [], "entry": None}
        with mock.patch.object(conversation_providers, "get", return_value={"name": "codex"}), \
                mock.patch.object(conversation_providers, "resolve_target", return_value=target):
            return self.request("POST", "/api/w/dmath/ai/sessions", {"provider": "codex"})[1]

    def artifacts(self, conversation_id):
        from workbench import registry
        from workbench.server.api import _pool_for
        pool = _pool_for(registry.get_workspace("dmath"))
        folder = pool.jobs_dir() / conversation_id
        return pool, folder

    def write_turn(self, folder, turn_id, message=None, **fields):
        turn = {
            "turn_id": turn_id, "status": "queued", "message": message or turn_id,
            "accepted_message": message or turn_id,
            "context": {"anchor": {"route": f"/{turn_id}"}},
            "queue_action": "queue", "queue_revision": 1, **fields,
        }
        (folder / f"{turn_id}.json").write_text(
            json.dumps(turn), encoding="utf-8",
        )
        return turn

    def test_reorder_route_returns_confirmed_order_and_rejects_invalid_or_stale_requests(self):
        created = self.create_session()
        conversation_id = created["conversation_id"]
        pool, folder = self.artifacts(conversation_id)
        try:
            self.write_turn(folder, "turn-002")
            self.write_turn(folder, "turn-010")
            conversation_path = folder / "conversation.json"
            record = json.loads(conversation_path.read_text(encoding="utf-8"))
            record.pop("queue_order", None)
            conversation_path.write_text(json.dumps(record), encoding="utf-8")
            base = f"/api/w/dmath/ai/sessions/{conversation_id}"

            _, session = self.request("GET", base)
            self.assertEqual(session["queue_order"], ["turn-002", "turn-010"])
            self.assertEqual(session["messages"][1]["queue_revision"], 1)

            status, result = self.request("POST", base + "/queue/reorder", {
                "expected_order": ["turn-002", "turn-010"],
                "turn_ids": ["turn-010", "turn-002"],
            })
            self.assertEqual(status, 200)
            self.assertEqual(result, {
                "conversation_id": conversation_id,
                "queue_order": ["turn-010", "turn-002"],
            })
            self.assertEqual(self.error("POST", base + "/queue/reorder", {
                "expected_order": ["turn-002", "turn-010"],
                "turn_ids": ["turn-002", "turn-010"],
            })[0], 409)
            self.assertEqual(self.error("POST", base + "/queue/reorder", {
                "expected_order": ["turn-010", "turn-002"],
                "turn_ids": ["turn-010"],
            })[0], 400)
            self.assertEqual(json.loads(conversation_path.read_text(encoding="utf-8"))[
                "queue_order"], ["turn-010", "turn-002"])
        finally:
            pool.close()

    def test_send_now_route_is_top_level_idempotent_and_rejects_boolean_revision(self):
        created = self.create_session()
        conversation_id = created["conversation_id"]
        pool, folder = self.artifacts(conversation_id)
        try:
            target = self.write_turn(folder, "turn-001", "B edited", submission_id="B-id",
                                     accepted_message="B original", queue_revision=2)
            self.write_turn(folder, "turn-002", "C")
            conversation_path = folder / "conversation.json"
            record = json.loads(conversation_path.read_text(encoding="utf-8"))
            record.update({"queue_paused": True, "queue_order": ["turn-001", "turn-002"]})
            conversation_path.write_text(json.dumps(record), encoding="utf-8")
            base = f"/api/w/dmath/ai/sessions/{conversation_id}/turns/turn-001/interrupt"

            self.assertEqual(self.error("POST", base, {"expected_revision": True})[0], 400)

            from workbench.bridge import conversations
            starts = []

            def start_direct(_root, _jobs, _workspace, _conversation_id, turn):
                starts.append(turn["turn_id"])
                current = json.loads((folder / f"{turn['turn_id']}.json").read_text(
                    encoding="utf-8"))
                current["status"] = "running"
                conversations._write_json(folder / f"{turn['turn_id']}.json", current)
                record = json.loads(conversation_path.read_text(encoding="utf-8"))
                record.update({"status": "running", "current_turn_id": turn["turn_id"]})
                conversations._write_json(conversation_path, record)
                return conversations._turn_response(current)

            with mock.patch.object(conversations, "_start_turn_locked",
                                   side_effect=start_direct):
                status, result = self.request("POST", base, {"expected_revision": 2})
                self.assertEqual(status, 200)
                self.assertEqual(result["turn_id"], target["turn_id"])
                self.assertEqual(result["status"], "running")
                self.assertEqual(result["message"], "B edited")
                _, repeated = self.request("POST", base, {"expected_revision": 2})

            self.assertEqual(repeated["turn_id"], target["turn_id"])
            self.assertEqual(starts, [target["turn_id"]])
            record = json.loads(conversation_path.read_text(encoding="utf-8"))
            self.assertTrue(record["queue_paused"])
            self.assertEqual(record["queue_order"], ["turn-002"])
        finally:
            pool.close()


if __name__ == "__main__":
    unittest.main()
