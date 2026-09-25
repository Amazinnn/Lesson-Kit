"""Provider-locked conversation lifecycle and minimal mirror tests."""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


FAKE_TURN = r'''import json, sys, time
mode = sys.argv[1]
prompt = sys.stdin.read()
if mode == "pi-activities":
    print(json.dumps({"type":"session","id":"pi-native-1"}), flush=True)
    print(json.dumps({"type":"turn_start"}), flush=True)
    print(json.dumps({"type":"message_update","assistantMessageEvent":{"type":"thinking_start"}}), flush=True)
    print(json.dumps({"type":"message_update","assistantMessageEvent":{"type":"thinking_end"}}), flush=True)
    print(json.dumps({"type":"tool_execution_start","toolCallId":"read-1","toolName":"read","args":{"path":"docs/GLOSSARY.md"}}), flush=True)
    print(json.dumps({"type":"tool_execution_end","toolCallId":"read-1","toolName":"read","args":{"path":"docs/GLOSSARY.md"},"result":{"content":[{"type":"text","text":"file output"}]},"isError":False}), flush=True)
    message = {"role":"assistant","content":[{"type":"text","text":"Pi answer"}],"stopReason":"stop"}
    print(json.dumps({"type":"message_end","message":message}), flush=True)
    raise SystemExit(0)
print(json.dumps({"type":"thread.started","thread_id":"native-123"}), flush=True)
print(json.dumps({"type":"turn.started"}), flush=True)
if mode == "slow":
    time.sleep(20)
elif mode == "chatty":
    # Reports progress in small pieces, for longer in total than the turn
    # budget: duration alone must never stop the turn.
    for index in range(12):
        print(json.dumps({"type":"item.completed","item":{"id":"r%d" % index,"type":"reasoning","text":"思考 %d" % index}}), flush=True)
        time.sleep(0.05)
    print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"想完了"}}), flush=True)
    print(json.dumps({"type":"turn.completed"}), flush=True)
elif mode == "quiet-command":
    # A command that runs and prints nothing for longer than the idle budget.
    print(json.dumps({"type":"item.started","item":{"id":"cmd-9","type":"command_execution","command":"make -j8"}}), flush=True)
    time.sleep(1.0)
    print(json.dumps({"type":"item.completed","item":{"id":"cmd-9","type":"command_execution","command":"make -j8","aggregated_output":"build ok","exit_code":0}}), flush=True)
    print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"构建完成"}}), flush=True)
    print(json.dumps({"type":"turn.completed"}), flush=True)
elif mode == "fail":
    print(json.dumps({"type":"error","message":"provider exploded"}), flush=True)
    raise SystemExit(3)
elif mode == "activities":
    print(json.dumps({"type":"item.started","item":{"id":"cmd-1","type":"command_execution","command":"wb pull"}}), flush=True)
    print(json.dumps({"type":"item.completed","item":{"id":"cmd-1","type":"command_execution","command":"wb pull","aggregated_output":"2 problems","exit_code":0}}), flush=True)
    print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"Answer"}}), flush=True)
    print(json.dumps({"type":"turn.completed"}), flush=True)
else:
    print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"Answer: " + prompt.splitlines()[-1]}}), flush=True)
    print(json.dumps({"type":"turn.completed"}), flush=True)
'''


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)
        self.script = Path(self.fixture.tmp.name) / "fake_turn.py"
        self.script.write_text(FAKE_TURN, encoding="utf-8")
        self.provider = {
            "name": "codex", "command": sys.executable, "args": [],
            "model": None, "timeout_s": 2,
        }

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def wait_turn(self, conversation_id, turn_id, timeout=5):
        from workbench.bridge import conversations

        deadline = time.time() + timeout
        while time.time() < deadline:
            turn = conversations.get_turn(self.pool, conversation_id, turn_id)
            if turn["status"] not in {"queued", "running"}:
                return turn
            time.sleep(0.02)
        self.fail("turn did not finish")

    def command(self, mode, calls):
        def build(_provider, session_id=None):
            calls.append(session_id)
            return [sys.executable, str(self.script), mode]
        return build

    def test_json_mirror_serializes_reader_and_writer(self):
        from workbench.bridge import conversations

        path = Path(self.fixture.tmp.name) / "mirror.json"
        path.write_text('{"value": 1}', encoding="utf-8")
        read_started = threading.Event()
        release_read = threading.Event()
        replace_started = threading.Event()
        original_read = Path.read_text
        original_replace = Path.replace

        def blocking_read(current, *args, **kwargs):
            if current == path:
                read_started.set()
                release_read.wait(timeout=2)
            return original_read(current, *args, **kwargs)

        def observed_replace(current, target):
            replace_started.set()
            return original_replace(current, target)

        with mock.patch.object(Path, "read_text", blocking_read), mock.patch.object(
            Path, "replace", observed_replace
        ):
            reader = threading.Thread(target=conversations._read_json, args=(path,))
            writer = threading.Thread(
                target=conversations._write_json, args=(path, {"value": 2})
            )
            reader.start()
            self.assertTrue(read_started.wait(timeout=1))
            writer.start()
            try:
                self.assertFalse(replace_started.wait(timeout=0.1))
            finally:
                release_read.set()
                reader.join(timeout=2)
                writer.join(timeout=2)

        self.assertEqual(conversations._read_json(path), {"value": 2})

    def test_event_stream_serializes_reader_and_appender(self):
        from workbench.bridge import conversations

        folder = self.pool.jobs_dir() / "conv-001"
        folder.mkdir(parents=True)
        path = folder / "turn-001.events.jsonl"
        path.write_text('{"sequence": 1, "kind": "phase"}\n', encoding="utf-8")
        read_started = threading.Event()
        release_read = threading.Event()
        append_started = threading.Event()
        original_read = Path.read_text
        original_open = Path.open

        def blocking_read(current, *args, **kwargs):
            if current == path and threading.current_thread().name == "mirror-reader":
                read_started.set()
                release_read.wait(timeout=2)
            return original_read(current, *args, **kwargs)

        def observed_open(current, mode="r", *args, **kwargs):
            if current == path and "a" in mode:
                append_started.set()
            return original_open(current, mode, *args, **kwargs)

        with mock.patch.object(Path, "read_text", blocking_read), mock.patch.object(
            Path, "open", observed_open
        ):
            reader = threading.Thread(
                name="mirror-reader",
                target=conversations.events,
                args=(self.pool, "conv-001", "turn-001"),
            )
            writer = threading.Thread(
                name="mirror-writer",
                target=conversations._append_event,
                args=(path, "done"),
            )
            reader.start()
            self.assertTrue(read_started.wait(timeout=1))
            writer.start()
            try:
                self.assertFalse(append_started.wait(timeout=0.1))
            finally:
                release_read.set()
                reader.join(timeout=2)
                writer.join(timeout=2)

        self.assertEqual(
            [event["sequence"] for event in conversations.events(
                self.pool, "conv-001", "turn-001"
            )],
            [1, 2],
        )

    def write_transcript(self, conversation_id, lines):
        path = self.pool.jobs_dir() / conversation_id / "transcript.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def captured_start_context(self, conversations, conversation_id, context):
        with mock.patch.object(conversations.threading, "Thread") as thread_type:
            conversations.start_turn(
                self.pool, self.workspace, conversation_id, "Next question", context,
            )
        thread_type.return_value.start.assert_called_once_with()
        return thread_type.call_args.kwargs["args"][-1]

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_successful_turn_mirrors_exchange_and_second_turn_resumes(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        calls = []
        with mock.patch.object(conversation_providers, "build_command", self.command("success", calls)):
            conversation = conversations.create(self.pool, "codex")
            first = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "First question",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            first_done = self.wait_turn(conversation["conversation_id"], first["turn_id"])
            second = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Second question",
                {"anchor": {"page_type": "graph", "route": "/w/dmath/graph"}},
            )
            second_done = self.wait_turn(conversation["conversation_id"], second["turn_id"])

        self.assertEqual(first_done["status"], "done")
        self.assertEqual(second_done["status"], "done")
        self.assertEqual(calls, [None, "native-123"])
        restored = conversations.get(self.pool, conversation["conversation_id"])
        self.assertEqual(restored["provider"], "codex")
        self.assertEqual(restored["provider_session_id"], "native-123")
        self.assertEqual(len(restored["messages"]), 4)
        self.assertEqual(restored["messages"][0]["role"], "user")
        self.assertIn("First question", restored["messages"][1]["content"])
        sequences = [event["sequence"] for event in conversations.events(
            self.pool, conversation["conversation_id"], first["turn_id"], after=0
        )]
        self.assertEqual(sequences, sorted(set(sequences)))

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_successful_turn_restores_coalesced_execution_plan(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        with mock.patch.object(
            conversation_providers, "build_command", self.command("activities", [])
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Check",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        restored = conversations.get(self.pool, conversation["conversation_id"])
        activities = restored["messages"][1]["activities"]
        command = next(item for item in activities if item["activity_id"] == "cmd-1")
        provider_turn = next(
            item for item in activities if item["activity_id"] == "provider-turn"
        )
        self.assertEqual(command["status"], "done")
        self.assertEqual(command["detail"], "wb pull")
        self.assertEqual(command["output"], "2 problems")
        self.assertEqual(sum(item["activity_id"] == "cmd-1" for item in activities), 1)
        self.assertEqual(provider_turn["status"], "done")

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_successful_pi_turn_mirrors_only_concrete_activities(self, get_provider):
        # Pi runs over its persistent RPC process, and the mirror still keeps
        # only the concrete activities (no reasoning, no protocol noise).
        from workbench.bridge import conversation_providers, conversations, pi_rpc
        from tests.workbench.test_pi_rpc import FakePiLauncher

        launcher = FakePiLauncher("normal", Path(self.fixture.tmp.name) / "pi.log")
        registry = pi_rpc.PiRpcRegistry(idle_seconds=1800)
        get_provider.return_value = {**self.provider, "name": "pi", "args": []}
        with mock.patch.object(conversation_providers, "build_command", launcher),                 mock.patch.object(conversations, "PI_RPC", registry):
            conversation = conversations.create(self.pool, "pi")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Check",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])
            registry.close_all()

        self.assertEqual(done["status"], "done")
        restored = conversations.get(self.pool, conversation["conversation_id"])
        activities = restored["messages"][1]["activities"]
        self.assertEqual([item["activity_id"] for item in activities], ["call_1"])
        self.assertEqual(activities[0]["activity_type"], "file-read")
        self.assertEqual(activities[0]["status"], "done")
        self.assertEqual(launcher.modes, ["rpc"])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_failure_is_literal_and_not_mirrored(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        with mock.patch.object(conversation_providers, "build_command", self.command("fail", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Fail",
                {"anchor": {"page_type": "practice", "route": "/w/dmath/practice"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "failed")
        self.assertIn("exit code 3", done["error"])
        self.assertEqual(conversations.get(self.pool, conversation["conversation_id"])["messages"], [])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_running_turn_rejects_second_send_and_can_be_cancelled(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        with mock.patch.object(conversation_providers, "build_command", self.command("slow", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Slow",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            with self.assertRaises(conversations.ConversationConflict):
                conversations.start_turn(
                    self.pool, self.workspace, conversation["conversation_id"], "Second",
                    {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
                )
            conversations.cancel(self.pool, conversation["conversation_id"])
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "cancelled")
        self.assertEqual(conversations.get(self.pool, conversation["conversation_id"])["messages"], [])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_provider_launch_failure_does_not_leave_conversation_running(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        with mock.patch.object(
            conversation_providers, "build_command",
            return_value=[str(Path(self.fixture.tmp.name) / "missing-provider.exe")],
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Hello",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "failed")
        self.assertIn("launch failed", done["error"])
        self.assertEqual(conversations.get(self.pool, conversation["conversation_id"])["status"], "idle")

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_timeout_is_reported_without_a_transcript(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = {**self.provider, "timeout_s": 0.1}
        with mock.patch.object(conversation_providers, "build_command", self.command("slow", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Slow",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "failed")
        self.assertEqual(done["error"], "provider timed out")
        self.assertEqual(conversations.get(self.pool, conversation["conversation_id"])["messages"], [])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_output_past_the_budget_is_not_a_timeout(self, get_provider):
        # The turn outlives its 0.3s budget while never going quiet for that
        # long: it must finish, not be cut off for taking time.
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = {**self.provider, "timeout_s": 0.3}
        with mock.patch.object(conversation_providers, "build_command", self.command("chatty", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Chatty",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            started = time.monotonic()
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])
            elapsed = time.monotonic() - started

        self.assertEqual(done["status"], "done")
        self.assertGreater(elapsed, 0.3)
        self.assertIn("想完了", conversations.get(
            self.pool, conversation["conversation_id"])["messages"][-1]["content"])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_a_quiet_command_gets_the_tool_budget(self, get_provider):
        # One second of silence from a running command: fatal under the 0.3s
        # idle budget, ordinary under the tool budget.
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = {
            **self.provider, "timeout_s": 0.3, "tool_timeout_s": 10,
        }
        with mock.patch.object(conversation_providers, "build_command", self.command("quiet-command", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Quiet",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        self.assertIn("构建完成", conversations.get(
            self.pool, conversation["conversation_id"])["messages"][-1]["content"])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_a_quiet_command_still_fails_by_its_own_budget(self, get_provider):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = {
            **self.provider, "timeout_s": 5, "tool_timeout_s": 0.2,
        }
        with mock.patch.object(conversation_providers, "build_command", self.command("quiet-command", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Stuck",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "failed")
        self.assertEqual(done["error"], "provider timed out")

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_session_title_can_be_renamed_and_idle_mirror_deleted(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        self.assertEqual(conversation["title"], "")
        self.assertEqual(conversation["title_source"], "unset")

        renamed = conversations.rename(self.pool, conversation["conversation_id"], "组合计数复习")
        self.assertEqual(renamed["title"], "组合计数复习")
        self.assertEqual(renamed["title_source"], "user")
        self.assertEqual(
            conversations.get(self.pool, conversation["conversation_id"])["title"],
            "组合计数复习",
        )

        result = conversations.delete(self.pool, conversation["conversation_id"])
        self.assertEqual(result["conversation_id"], conversation["conversation_id"])
        self.assertFalse((self.pool.jobs_dir() / conversation["conversation_id"]).exists())

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_running_session_cannot_delete(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        path = self.pool.jobs_dir() / conversation["conversation_id"] / "conversation.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["status"] = "running"
        record["current_turn_id"] = "turn-001"
        path.write_text(json.dumps(record), encoding="utf-8")
        key = (str(path.parent), "turn-001")
        conversations._ACTIVE_TURNS.add(key)
        try:
            with self.assertRaises(conversations.ConversationConflict):
                conversations.delete(self.pool, conversation["conversation_id"])
            self.assertTrue(path.exists())
        finally:
            conversations._ACTIVE_TURNS.discard(key)

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_persisted_running_turn_is_recovered_after_restart(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        folder = self.pool.jobs_dir() / conversation["conversation_id"]
        record = json.loads((folder / "conversation.json").read_text(encoding="utf-8"))
        record.update({"status": "running", "current_turn_id": "turn-001"})
        (folder / "conversation.json").write_text(json.dumps(record), encoding="utf-8")
        (folder / "turn-001.json").write_text(json.dumps({
            "turn_id": "turn-001", "status": "running", "error": None,
        }), encoding="utf-8")

        restored = conversations.get(self.pool, conversation["conversation_id"])
        turn = conversations.get_turn(
            self.pool, conversation["conversation_id"], "turn-001"
        )

        self.assertEqual(restored["status"], "idle")
        self.assertIsNone(restored["current_turn_id"])
        self.assertEqual(turn["status"], "failed")
        self.assertIn("workbench restarted", turn["error"])
        self.assertEqual(
            conversations.events(
                self.pool, conversation["conversation_id"], "turn-001"
            )[-1]["kind"],
            "error",
        )

    def test_stop_escalates_to_kill_when_provider_ignores_terminate(self):
        from workbench.bridge import conversations

        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = [
            conversations.subprocess.TimeoutExpired("provider", 1),
            0,
        ]

        conversations._stop_process(process)

        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_explicit_provider_title_is_mirrored(self, get_provider, normalize_event):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-1"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "Answer", "title": "排列组合基础"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "Hello",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        restored = conversations.get(self.pool, conversation["conversation_id"])
        self.assertEqual(restored["title"], "排列组合基础")
        self.assertEqual(restored["title_source"], "agent")

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_practice_action_requires_explicit_intent_and_valid_ids(self, get_provider, normalize_event):
        from workbench.bridge import conversation_providers, conversations

        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-2"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "已安排。\n```lessonkit-action\n"
             "{\"type\":\"replace_practice_selection\",\"kp_ids\":[\"kp-001\",\"unknown\"]}\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        with mock.patch.object(conversation_providers, "build_command", self.command("success", [])):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "帮我安排练习",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"},
                 "practice_intent": True, "knowledge_point_ids": ["kp-001"]},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        self.assertEqual(done["action"], {
            "type": "replace_practice_selection", "kp_ids": ["kp-001"],
        })

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_check_ingest_success_is_stored_on_done_turn(self, get_provider, normalize_event):
        from workbench.bridge import conversation_providers, conversations

        manifest = {
            "kind": "flash-card-patch",
            "items": [{"card_id": "card-001"}],
        }
        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-3"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "已补池。\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": manifest}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        applied = {
            "ok": True,
            "batch_id": "batch-001",
            "kind": "flash-card-patch",
            "counts": {"flash_cards": 1},
            "backup_path": "pool/backups/batch-001.sqlite",
            "applied": ["card-001"],
        }
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ), mock.patch.object(
            conversations.ingest, "apply_batch", create=True, return_value=applied
        ) as apply_batch:
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "帮我补池",
                {"anchor": {"page_type": "kp", "route": "/w/dmath/kp/kp-001"},
                 "check_intent": True},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        self.assertEqual(done["action"], {
            "type": "check_ingest",
            "manifest": manifest,
            "result": {
                "batch_id": "batch-001",
                "kind": "flash-card-patch",
                "counts": {"flash_cards": 1},
                "backup_path": "pool/backups/batch-001.sqlite",
                "applied": ["card-001"],
                "workspace": "dmath",
            },
        })
        kwargs = apply_batch.call_args.kwargs
        self.assertEqual(kwargs["source"], "bridge")
        self.assertTrue(str(kwargs["backup_path"]).endswith(
            f"{conversation['conversation_id']}-{turn['turn_id']}-ingest-backup"))

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_two_content_actions_in_one_reply_are_both_applied(
            self, get_provider, normalize_event):
        """One turn may import two chapters: the second block is not dropped."""
        from workbench.bridge import conversation_providers, conversations

        def bundle(chapter):
            return {
                "kind": "content-bundle", "chapter": chapter,
                "problems": [{
                    "key": "p1", "problem_type": "calculation",
                    "problem_text": "题目", "kp_ids": ["dmath-ch06-kp-001"],
                    "source_kind": "textbook", "origin_kind": "source_problem",
                    "source_evidence": "教材 第12章 习题12-1",
                }],
            }

        first, second = bundle("ch12"), bundle("ch13")
        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-9"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "两章都导好了。"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": first}) + "\n```"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": second}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        applied = {
            "ok": True, "kind": "content-bundle", "applied": 2,
            "batch_id": "batch-010", "counts": {"problems": 3},
            "origins": {"source_problem": 3},
            "batches": [
                {"batch_id": "batch-010", "chapter": "ch12",
                 "counts": {"problems": 3}, "origins": {"source_problem": 3}},
                {"batch_id": "batch-011", "chapter": "ch13",
                 "counts": {"problems": 2}, "origins": {"source_problem": 2}},
            ],
            "backup_path": "pool/backups/one.sqlite",
        }
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ), mock.patch.object(
            conversations.ingest, "apply_batch", create=True, return_value=applied
        ) as apply_batch:
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "把 12、13 章都导进去",
                {"anchor": {"page_type": "kp", "route": "/w/dmath/kp/kp-001"},
                 "check_intent": True},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        self.assertEqual(apply_batch.call_count, 2, "every content block is applied")
        self.assertEqual(
            [action["manifest"]["chapter"] for action in done["actions"]],
            ["ch12", "ch13"],
        )
        self.assertEqual([batch["chapter"] for batch in
                          done["actions"][1]["result"]["batches"]], ["ch12", "ch13"])
        # No single action to show: the card renders every batch instead.
        self.assertNotIn("action", done)
        transcript = (Path(self.fixture.tmp.name) / "dmath" / ".lessonkit" / "jobs"
                      / conversation["conversation_id"] / "transcript.jsonl")
        exchange = json.loads(transcript.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(len(exchange["actions"]), 2)

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_two_real_actions_in_one_turn_keep_their_own_backups(
            self, get_provider, normalize_event):
        """Both blocks really apply: one recovery copy each, no name clash."""
        from workbench.bridge import conversation_providers, conversations

        def bundle(chapter):
            return {
                "kind": "content-bundle", "chapter": chapter,
                "problems": [{
                    "key": "p1", "chapter": chapter, "problem_type": "calculation",
                    "problem_text": chapter + " 题目",
                    "kp_ids": ["dmath-ch06-kp-001"],
                    "source_kind": "textbook", "origin_kind": "source_problem",
                    "source_evidence": "教材 第6章 习题6-1",
                }],
            }

        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-11"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "两章都导好了。"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": bundle("ch06")}) + "\n```"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": bundle("ch07")}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "把六、七章导进去",
                {"anchor": {"page_type": "kp", "route": "/w/dmath/kp/kp-001"},
                 "check_intent": True},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done", done.get("error"))
        batches = [batch for action in done["actions"]
                   for batch in action["result"]["batches"]]
        self.assertEqual([batch["chapter"] for batch in batches], ["ch06", "ch07"])
        self.assertEqual(len({batch["batch_id"] for batch in batches}), 2)
        ids = [row[0] for row in self.pool.connect().execute(
            "SELECT problem_id FROM problems WHERE problem_id LIKE 'dmath-ch0%'"
            " ORDER BY problem_id")]
        self.assertIn("dmath-ch07-prob-001", ids)
        backups = sorted(p.name for p in self.pool.db_path.parent.glob("*backup*"))
        self.assertEqual(len(backups), 2, backups)

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_a_keyless_objective_import_reports_its_count_next_turn(
            self, get_provider, normalize_event):
        """A 判断题 whose source lost its answer still lands — and is disclosed."""
        from workbench.bridge import conversation_providers, conversations

        manifest = {
            "kind": "content-bundle", "chapter": "ch06",
            "problems": [
                {"key": "m1", "chapter": "ch06", "problem_type": "other",
                 "stem": "1 是质数吗？", "quiz_type": "yes_no", "answer_key": None,
                 "kp_ids": ["dmath-ch06-kp-001"], "source_kind": "textbook",
                 "origin_kind": "source_problem",
                 "source_evidence": "教材 第6章 习题6-1"},
            ],
        }

        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-12"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "判断题导好了。"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "content-bundle", "manifest": manifest}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "把判断题导进去",
                {"anchor": {"page_type": "kps", "route": "/w/dmath/kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])
            outcome = conversations._last_check_outcome(
                conversations._conversation_dir(
                    self.pool, conversation["conversation_id"]))

        self.assertEqual(done["status"], "done", done.get("error"))
        row = self.pool.connect().execute(
            "SELECT practice_modes, micro_quiz FROM problems"
            " WHERE problem_id LIKE '%-mq-%'").fetchone()
        self.assertEqual(json.loads(row[0]), ["yes_no"])
        self.assertIsNone(json.loads(row[1])["answer_key"])
        self.assertIn("未录答案键 1", outcome)
        self.assertIn("不要让学生再说一次「继续」", outcome)

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_one_failing_content_action_leaves_the_other_applied(
            self, get_provider, normalize_event):
        from workbench.bridge import conversation_providers, conversations
        from workbench import ingest

        def bundle(chapter, kp_id):
            return {
                "kind": "content-bundle", "chapter": chapter,
                "problems": [{
                    "key": "p1", "problem_type": "calculation",
                    "problem_text": "题目", "kp_ids": [kp_id],
                    "source_kind": "textbook", "origin_kind": "source_problem",
                    "source_evidence": "教材 第12章 习题12-1",
                }],
            }

        good = bundle("ch12", "dmath-ch06-kp-001")
        bad = bundle("ch13", "kp-9")
        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-10"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "先导 12 章，13 章有问题。"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": good}) + "\n```"
             + "\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": bad}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        real_apply = ingest.apply_batch

        def apply(db_path, manifest, **kwargs):
            if manifest["chapter"] == "ch13":
                raise ValueError("problem 1: unknown knowledge point kp-9")
            return real_apply(db_path, manifest, **kwargs)

        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ), mock.patch.object(
            conversations.ingest, "apply_batch", side_effect=apply, create=True
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "把 12、13 章导进去",
                {"anchor": {"page_type": "kp", "route": "/w/dmath/kp/kp-001"},
                 "check_intent": True},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        actions = done["actions"]
        self.assertEqual(actions[0]["result"]["kind"], "content-bundle")
        self.assertIn("unknown knowledge point", actions[1]["error"])
        self.assertEqual(self.pool.connect().execute(
            "SELECT COUNT(*) FROM ingest_batches").fetchone()[0], 1)

    @mock.patch("workbench.bridge.conversation_providers.normalize_event")
    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_check_ingest_gate_failure_is_stored_on_done_turn(self, get_provider, normalize_event):
        from workbench.bridge import conversation_providers, conversations

        manifest = {
            "kind": "micro-quiz-patch",
            "items": [{"problem_id": "prob-001"}],
        }
        get_provider.return_value = self.provider
        normalize_event.side_effect = [
            {"kind": "phase", "label": "thread.started", "provider_session_id": "native-4"},
            {"kind": "phase", "label": "turn.started"},
            {"kind": "result", "text": "未能补池。\n```lessonkit-action\n"
             + json.dumps({"type": "check_ingest", "manifest": manifest}) + "\n```"},
            {"kind": "phase", "label": "turn.completed"},
        ]
        with mock.patch.object(
            conversation_providers, "build_command", self.command("success", [])
        ), mock.patch.object(
            conversations.ingest, "apply_batch", create=True,
            side_effect=ValueError("prob-001: answer_key is required"),
        ):
            conversation = conversations.create(self.pool, "codex")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"], "给这个知识点加题",
                {"anchor": {"page_type": "kp", "route": "/w/dmath/kp/kp-001"},
                 "check_intent": True},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "done")
        self.assertEqual(done["action"], {
            "type": "check_ingest",
            "manifest": manifest,
            "error": "prob-001: answer_key is required",
        })

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_start_turn_injects_successful_check_ingest_outcome(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        exchange = {
            "action": {
                "type": "check_ingest",
                "manifest": {"kind": "flash-card-patch", "items": []},
                "result": {
                    "batch_id": "batch-007",
                    "kind": "flash-card-patch",
                    "counts": {"flash_cards": 3},
                },
            },
        }
        self.write_transcript(
            conversation["conversation_id"],
            [json.dumps(exchange, ensure_ascii=False)],
        )
        original = {"anchor": {"page_type": "kp"}, "check_intent": True}

        captured = self.captured_start_context(
            conversations, conversation["conversation_id"], original,
        )

        self.assertEqual(
            captured["last_check_outcome"],
            "上一轮内容动作已成功入库：批次 batch-007（flash-card-patch，闪卡 3）。"
            "不要重复提交相同内容；若学生要求的内容还有未导入的章，直接继续提交剩余部分，"
            "不要让学生再说一次「继续」。",
        )
        self.assertIsNot(captured, original)
        self.assertIs(captured["anchor"], original["anchor"])
        self.assertNotIn("last_check_outcome", original)

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_start_turn_injects_rejected_check_ingest_outcome(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        error = "card-901: source_evidence is required\ncard-902: duplicate card_id"
        exchange = {
            "action": {
                "type": "check_ingest",
                "manifest": {"kind": "flash-card-patch", "items": []},
                "error": error,
            },
        }
        self.write_transcript(
            conversation["conversation_id"],
            [json.dumps(exchange, ensure_ascii=False)],
        )

        captured = self.captured_start_context(
            conversations, conversation["conversation_id"], {"check_intent": True},
        )

        self.assertEqual(
            captured["last_check_outcome"],
            "上一轮内容动作被门禁拒收（零写入），逐条原因：\n"
            + error
            + "\n请修正清单后重新提交完整的 lessonkit-action 区块。",
        )

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_start_turn_injects_invalid_check_ingest_block_outcome(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        conversation = conversations.create(self.pool, "codex")
        exchange = {
            "action": {
                "type": "check_ingest",
                "error": "action block is not valid JSON",
            },
        }
        self.write_transcript(
            conversation["conversation_id"],
            [json.dumps(exchange, ensure_ascii=False)],
        )

        captured = self.captured_start_context(
            conversations, conversation["conversation_id"], {"check_intent": True},
        )

        self.assertEqual(
            captured["last_check_outcome"],
            "上一轮内容动作区块无效：action block is not valid JSON。"
            "请重新提交符合契约的完整区块。",
        )

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_start_turn_skips_missing_or_unusable_previous_action(self, get_provider):
        from workbench.bridge import conversations

        get_provider.return_value = self.provider
        cases = {
            "no transcript": None,
            "empty transcript": [],
            "last line damaged": [
                json.dumps({"action": {"type": "check_ingest"}}),
                "{broken",
            ],
            "no action": [json.dumps({"assistant": "plain answer"})],
            "practice action": [json.dumps({
                "action": {"type": "replace_practice_selection", "kp_ids": ["kp-001"]},
            })],
            "goal action": [json.dumps({
                "action": {"type": "prefill_goal_form", "title": "复习"},
            }, ensure_ascii=False)],
        }
        for label, lines in cases.items():
            with self.subTest(label=label):
                conversation = conversations.create(self.pool, "codex")
                if lines is not None:
                    self.write_transcript(conversation["conversation_id"], lines)
                captured = self.captured_start_context(
                    conversations, conversation["conversation_id"], {"check_intent": True},
                )
                self.assertNotIn("last_check_outcome", captured)


class GoalFormActionExtractionTests(unittest.TestCase):
    """prefill_goal_form：意图门、字段契约、区块剥离。"""

    def _run(self, answer, context):
        from workbench.bridge import conversations

        cleaned, _, notice = conversations._extract_action(answer, context)
        return cleaned, notice

    def _answer(self, body):
        return "好的，我帮你填。\n```lessonkit-action\n" + body + "\n```"

    def test_goal_intent_with_valid_action_is_extracted_and_stripped(self):
        answer = self._answer('{"type":"prefill_goal_form","title":"期末掌握计数",'
                              '"kind":"stage","start_date":"2026-09-01",'
                              '"deadline":"2026-09-30","description":"重点：鸽巢与组合"}')
        cleaned, action = self._run(answer, {"goal_intent": True})
        self.assertEqual(action["type"], "prefill_goal_form")
        self.assertEqual(action["title"], "期末掌握计数")
        self.assertEqual(action["start_date"], "2026-09-01")
        self.assertEqual(action["deadline"], "2026-09-30")
        self.assertNotIn("lessonkit-action", cleaned)

    def test_without_goal_intent_block_is_disclosed_as_ignored(self):
        cleaned, action = self._run(
            self._answer('{"type":"prefill_goal_form","title":"x"}'),
            {"goal_intent": False})
        self.assertEqual(action, {"ignored": "no block matched the active intent"})
        self.assertNotIn("lessonkit-action", cleaned)

    def test_empty_title_is_discarded(self):
        _, action = self._run(
            self._answer('{"type":"prefill_goal_form","title":" "}'),
            {"goal_intent": True})
        self.assertIsNone(action)

    def test_bad_kind_and_deadline_are_normalized(self):
        _, action = self._run(
            self._answer('{"type":"prefill_goal_form","title":"T","kind":"weird",'
                         '"start_date":"九月","deadline":"九月"}'),
            {"goal_intent": True})
        self.assertEqual(action["kind"], "stage")
        self.assertEqual(action["start_date"], "")
        self.assertEqual(action["deadline"], "")

    def test_malformed_json_is_explicit(self):
        cleaned, action = self._run(self._answer("{oops}"), {"goal_intent": True})
        self.assertEqual(action, {
            "type": "check_ingest",
            "error": "action block is not valid JSON",
        })
        self.assertNotIn("lessonkit-action", cleaned)


class CheckIngestActionExtractionTests(unittest.TestCase):
    def _run(self, body, context, folder=None):
        from workbench.bridge import conversations

        answer = "已生成。\n```lessonkit-action\n" + body + "\n```"
        cleaned, content, notice = conversations._extract_action(
            answer, context, folder)
        return cleaned, (content[0] if content else notice)

    def _run_all(self, bodies, context, folder=None):
        """Every content action of one reply, in block order."""
        from workbench.bridge import conversations

        answer = "已生成。" + "".join(
            "\n```lessonkit-action\n" + body + "\n```" for body in bodies
        )
        cleaned, content, notice = conversations._extract_action(
            answer, context, folder)
        return cleaned, [*content, *([notice] if notice else [])]

    def _extract(self, answer, context):
        from workbench.bridge import conversations

        cleaned, content, notice = conversations._extract_action(answer, context)
        return cleaned, (content[0] if content else notice)

    def test_prompt_describes_the_content_bundle_contract(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("帮我补池", {
            "check_intent": True,
            "workspace": {"name": "大学物理", "course": "uphy2", "chapter": "ch07"},
            "staged_manifest_dir": ".lessonkit/jobs/conv-003",
        })
        self.assertIn("content-bundle", prompt)
        self.assertIn("staged_manifest", prompt)
        self.assertIn(".lessonkit/jobs/conv-003", prompt)
        self.assertIn("knowledge_points", prompt)
        self.assertIn("flash_cards", prompt)
        self.assertIn("source_evidence", prompt)
        self.assertIn("source_answer", prompt)
        self.assertIn("solution_origin", prompt)
        self.assertIn("directions", prompt)
        self.assertIn("figure:f1", prompt)
        self.assertIn("禁止直接运行 lesson-kit ingest", prompt)
        self.assertIn("source_kind", prompt)
        self.assertIn("origin_kind", prompt)
        self.assertIn("source_problem", prompt)
        self.assertIn("generated_grounded", prompt)
        self.assertIn("lesson-kit difficulty", prompt)
        self.assertNotIn("difficulty_basis", prompt)
        self.assertNotIn('"difficulty":1', prompt)
        self.assertIn("才可使用 lesson-kit data 写命令", prompt)
        self.assertNotIn("wb data", prompt)
        self.assertNotIn("wb ingest", prompt)
        self.assertIn("topic_label", prompt)
        self.assertIn("数学乘号一律用 ×", prompt)
        self.assertIn("证明题", prompt)
        self.assertNotIn("dmath", prompt)
        # The pre-release six-item ceiling and its id bookkeeping are gone.
        self.assertNotIn("3–6", prompt)
        self.assertNotIn("一次产出", prompt)
        self.assertNotIn("next_free_ids", prompt.split("服务端重建的当前上下文")[0])
        self.assertIn("last_check_outcome", prompt)

    def test_prompt_has_no_item_ceiling(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("q", {"workspace": {"course": "uphy2",
                                                          "chapter": "ch12"}})
        self.assertNotIn("3–6", prompt)
        self.assertIn("条数没有上限", prompt)
        # One manifest may span chapters and lands as one batch per chapter.
        self.assertIn("一份清单可以跨任意多章", prompt)
        self.assertIn("按章各记一个批次", prompt)
        self.assertIn("content-bundle 区块都会被依次应用", prompt)
        self.assertIn("不要只导一章就停下来", prompt)
        # The chapter rule is stated as implemented: no workspace fallback.
        self.assertIn("点名拒收", prompt)
        # The practice mode is chosen with fields, and a key may be missing.
        self.assertIn("练习题型三选一", prompt)
        self.assertIn("即使题源没有正确答案也照样入库", prompt)
        # A resumed session is told the contract takes precedence.
        self.assertIn("content-bundle 契约（v2", prompt)

    def test_prompt_teaches_workspace_arguments_and_independent_cli_calls(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("q", {"workspace": {
            "name": "大学物理乙II", "course": "c01", "chapter": "ch12"}})
        # the argument order the Agent got wrong: workspace right after the command
        self.assertIn("lesson-kit data 大学物理乙II create kp --input", prompt)
        # discover flags from help instead of guessing
        self.assertIn("--help", prompt)
        self.assertIn("不要猜", prompt)
        # an independent invocation keeps its own exit status
        self.assertIn("单独执行", prompt)
        self.assertIn("不要接管道", prompt)
        self.assertIn("退出码", prompt)
        # redirecting to a file keeps the output readable without losing status
        self.assertIn("> out.txt", prompt)
        self.assertIn("echo $?", prompt)
        # success may only be claimed from a successful result
        self.assertIn("不要谎报成功", prompt)

    def test_prompt_preserves_practice_and_goal_action_contracts(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("帮我补池", {"check_intent": True})
        self.assertIn(
            "若学生明确要求选择或安排练习范围，可在回答末尾附一个 lessonkit-action JSON 区块；"
            "普通问答不要附带动作。格式为 ```lessonkit-action "
            '{"type":"replace_practice_selection","kp_ids":["知识点ID"]} ```。',
            prompt,
        )
        self.assertIn(
            "若学生从目标表单发起一句话求助，可附 ```lessonkit-action "
            '{"type":"prefill_goal_form","title":"…","kind":"stage|long_term",'
            '"start_date":"YYYY-MM-DD或空","deadline":"YYYY-MM-DD或空",'
            '"description":"…"} ``` 代填目标字段'
            "（仅此意图可附，普通问答不得代填）。",
            prompt,
        )

    def test_append_action_runs_without_any_keyword_intent(self):
        manifest = {"kind": "flash-card-patch", "items": [{"card_id": "card-001"}]}
        cleaned, action = self._run(
            json.dumps({"type": "check_ingest", "manifest": manifest}),
            {"check_intent": False},
        )
        self.assertEqual(action, {"type": "check_ingest", "manifest": manifest})
        self.assertNotIn("lessonkit-action", cleaned)

    def test_bare_bundle_manifest_runs_without_intent(self):
        manifest = {
            "kind": "content-bundle",
            "problems": [{"key": "p1", "problem_type": "proof"}],
        }
        _, action = self._run(json.dumps(manifest), {})
        self.assertEqual(action, {"type": "check_ingest", "manifest": manifest})

    def test_an_inline_block_may_name_the_bundle_with_type(self):
        # The contract calls the block a content-bundle, so writing
        # {"type": "content-bundle", …} must not be refused over the key's name.
        _, action = self._run(json.dumps({
            "type": "content-bundle",
            "chapter": "ch07",
            "problems": [{"key": "p1", "problem_type": "proof", "chapter": "ch07"}],
        }), {})
        self.assertNotIn("error", action)
        self.assertEqual(action["manifest"]["kind"], "content-bundle")
        self.assertEqual(action["manifest"]["problems"][0]["key"], "p1")

    def test_a_staged_file_may_carry_only_the_lists(self):
        # The real Agent staged the manifest body without a wrapper key, because
        # the block already said which action it is.
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "conv-003"
            folder.mkdir()
            (folder / "bundle.json").write_text(json.dumps({
                "chapter": "ch07",
                "problems": [{"key": "p1", "problem_type": "proof",
                              "chapter": "ch07"}],
            }), encoding="utf-8")
            _, action = self._run(
                '{"type":"content-bundle","staged_manifest":"bundle.json"}',
                {}, folder,
            )
        self.assertNotIn("error", action)
        self.assertEqual(action["manifest"]["kind"], "content-bundle")
        self.assertEqual(action["manifest"]["problems"][0]["problem_type"], "proof")

    def test_a_list_with_no_entries_is_still_an_empty_bundle(self):
        _, action = self._run(json.dumps({"problems": []}), {})
        self.assertIn("requires at least one knowledge point", action["error"])

    def test_a_wrong_shape_is_still_refused(self):
        # A recognized block type with an empty manifest keeps its explicit error.
        _, action = self._run(
            json.dumps({"type": "content-bundle", "knowledge_points": []}), {})
        self.assertIn("at least one knowledge point", action["error"])
        # An unknown block type is refused as an unrecognized action.
        _, action = self._run(json.dumps({"type": "flash-card", "items": []}), {})
        self.assertIn("没有区块符合已知动作契约", action["error"])

    def test_staged_manifest_is_loaded_from_the_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "conv-002"
            folder.mkdir()
            manifest = {
                "kind": "content-bundle",
                "problems": [{"key": "p1", "problem_type": "calculation"}],
            }
            (folder / "bundle.json").write_text(
                json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            _, action = self._run(
                '{"type":"content-bundle","staged_manifest":"bundle.json"}',
                {}, folder,
            )
        self.assertEqual(action["staged_manifest"], "bundle.json")
        self.assertEqual(action["manifest"], manifest)
        self.assertNotIn("error", action)

    def test_staged_manifest_cannot_leave_the_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "conv-002"
            folder.mkdir()
            outside = Path(tmp) / "elsewhere.json"
            outside.write_text('{"kind":"content-bundle","problems":[{"key":"p"}]}',
                               encoding="utf-8")
            _, action = self._run(
                '{"type":"content-bundle","staged_manifest":"../elsewhere.json"}',
                {}, folder,
            )
        self.assertIn("error", action)
        self.assertIn("inside this conversation", action["error"])
        self.assertNotIn("manifest", action)

    def test_valid_manifest_is_extracted_and_stripped(self):
        manifest = {
            "kind": "flash-card-patch",
            "items": [{"card_id": "card-001"}],
        }
        cleaned, action = self._run(
            json.dumps({"type": "check_ingest", "manifest": manifest}),
            {"check_intent": True},
        )
        self.assertEqual(action, {"type": "check_ingest", "manifest": manifest})
        self.assertNotIn("lessonkit-action", cleaned)

    def test_invalid_kind_is_an_explicit_error(self):
        _, action = self._run(
            '{"type":"check_ingest","manifest":{"kind":"essay-patch","items":[{}]}}',
            {"check_intent": True},
        )
        self.assertEqual(action, {
            "type": "check_ingest",
            "error": "manifest kind must be flash-card-patch, micro-quiz-patch, "
                     "or content-bundle — a content-bundle carries "
                     "knowledge_points / problems / flash_cards",
        })

    def test_empty_items_are_an_explicit_error(self):
        _, action = self._run(
            '{"type":"check_ingest","manifest":{"kind":"micro-quiz-patch","items":[]}}',
            {"check_intent": True},
        )
        self.assertEqual(action, {
            "type": "check_ingest",
            "error": "manifest items must be a non-empty list",
        })

    def test_bad_json_is_explicit_with_check_intent(self):
        cleaned, action = self._run("{oops}", {"check_intent": True})
        self.assertEqual(action, {
            "type": "check_ingest",
            "error": "action block is not valid JSON",
        })
        self.assertNotIn("lessonkit-action", cleaned)

    def test_bad_json_is_explicit_without_any_intent(self):
        cleaned, action = self._run("{oops}", {"check_intent": False})
        self.assertEqual(action, {
            "type": "check_ingest",
            "error": "action block is not valid JSON",
        })
        self.assertNotIn("lessonkit-action", cleaned)

    def test_multi_block_reply_finds_the_matching_block(self):
        # conv-023 回放：Claude 同报「选区 + 裸 manifest」两个区块，
        # 练习意图缺席但出题意图在场——manifest 必须被解析而不是被首区块挡住。
        answer = (
            "格式确认。\n```lessonkit-action\n"
            '{"type":"replace_practice_selection","kp_ids":["dmath-ch06-kp-028"]}\n'
            "```\n```lessonkit-action\n"
            '{"kind":"flash-card-patch","items":[{"card_id":"dmath-ch06-fc-097",'
            '"kp_id":"dmath-ch06-kp-028","front":"f","back":"b",'
            '"source_evidence":"kp-028 §4"}]}\n```'
        )
        cleaned, action = self._extract(answer, {"check_intent": True, "practice_intent": False})
        self.assertEqual(action["type"], "check_ingest")
        self.assertEqual(action["manifest"]["items"][0]["card_id"], "dmath-ch06-fc-097")
        self.assertNotIn("lessonkit-action", cleaned)
        self.assertIn("格式确认", cleaned)

    def test_manifest_before_selection_block_is_still_found(self):
        answer = (
            "```lessonkit-action\n"
            '{"kind":"flash-card-patch","items":[{"card_id":"card-001"}]}\n'
            "```\n```lessonkit-action\n"
            '{"type":"replace_practice_selection","kp_ids":["kp-001"]}\n```'
        )
        _, action = self._extract(answer, {"check_intent": True, "practice_intent": True})
        self.assertEqual(action["type"], "check_ingest")


class IgnoredActionDisclosureTests(unittest.TestCase):
    """未被接受的区块必须进入下一轮上下文，堵住"已写入"幻觉。"""

    def _folder_with_transcript(self, tmp, exchange):
        folder = Path(tmp) / "conv-900"
        folder.mkdir()
        with (folder / "transcript.jsonl").open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(exchange, ensure_ascii=False) + "\n")
        return folder

    def test_ignored_action_is_disclosed_to_the_next_turn(self):
        from workbench.bridge import conversations

        with tempfile.TemporaryDirectory() as tmp:
            folder = self._folder_with_transcript(tmp, {
                "turn_id": "turn-001", "user": "q", "assistant": "a",
                "action": {"ignored": "no block matched the active intent"},
            })
            note = conversations._last_check_outcome(folder)
        self.assertIn("未被接受", note)
        self.assertIn("未写入任何内容", note)

    def test_plain_exchange_still_returns_none(self):
        from workbench.bridge import conversations

        with tempfile.TemporaryDirectory() as tmp:
            folder = self._folder_with_transcript(tmp, {
                "turn_id": "turn-001", "user": "q", "assistant": "a",
            })
            self.assertIsNone(conversations._last_check_outcome(folder))


if __name__ == "__main__":
    unittest.main()
