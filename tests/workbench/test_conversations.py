"""Provider-locked conversation lifecycle and minimal mirror tests."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


FAKE_TURN = r'''import json, sys, time
mode = sys.argv[1]
prompt = sys.stdin.read()
print(json.dumps({"type":"thread.started","thread_id":"native-123"}), flush=True)
print(json.dumps({"type":"turn.started"}), flush=True)
if mode == "slow":
    time.sleep(20)
elif mode == "fail":
    print(json.dumps({"type":"error","message":"provider exploded"}), flush=True)
    raise SystemExit(3)
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


if __name__ == "__main__":
    unittest.main()
