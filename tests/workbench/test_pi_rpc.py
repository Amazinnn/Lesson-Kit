"""Per-conversation Pi RPC lifecycle (TDD: red before implementation)."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture
from workbench.bridge import conversation_providers, conversations, pi_rpc


FAKE = Path(__file__).resolve().parent / "fake_pi_rpc.py"


class FakePiLauncher:
    """Launch the fake with a runnable argv while recording what was asked for.

    `python` would swallow pi's leading `--mode rpc`, so the fake cannot be
    launched through the real command line; the requested mode and session are
    recorded here and asserted instead.
    """

    def __init__(self, fake_mode="normal", log=None):
        self.fake_mode = fake_mode
        self.log = log
        self.modes = []
        self.sessions = []

    def __call__(self, provider, session_id=None, mode="print"):
        self.modes.append(mode)
        self.sessions.append(session_id)
        return [sys.executable, str(FAKE), self.fake_mode, str(self.log)]


class FakeClock:
    """A hand-driven monotonic clock, so idle expiry needs no sleeping."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class PiRpcProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "pi.log"
        self.provider = {
            "name": "pi", "command": sys.executable, "args": [], "model": None,
            "timeout_s": 30,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, mode="normal", clock=None):
        self.launcher = FakePiLauncher(mode, self.log_path)
        process = pi_rpc.PiRpcProcess(
            self.provider, self.tmp.name, clock=clock or time.monotonic)
        process._launcher = self.launcher
        self.build = mock.patch.object(
            conversation_providers, "build_command", self.launcher)
        self.build.start()
        self.addCleanup(self.build.stop)
        return process

    def entries(self, event=None):
        if not self.log_path.is_file():
            return []
        rows = [json.loads(line) for line in
                self.log_path.read_text(encoding="utf-8").splitlines()]
        return [row for row in rows if event is None or row.get("event") == event]

    def test_rpc_command_is_built_without_print_mode(self):
        command = conversation_providers.build_command(self.provider, None, mode="rpc")
        self.assertIn("--mode", command)
        self.assertEqual(command[command.index("--mode") + 1], "rpc")
        self.assertNotIn("--print", command)

    def test_rpc_command_resumes_the_saved_native_session(self):
        command = conversation_providers.build_command(
            self.provider, "pi-session-9", mode="rpc")
        self.assertEqual(command[command.index("--session") + 1], "pi-session-9")

    def test_the_bridge_asks_the_process_for_rpc_mode(self):
        process = self.make()
        try:
            process.start()
        finally:
            process.close()
        self.assertEqual(self.launcher.modes, ["rpc"])

    def test_prompt_streams_events_until_settled(self):
        process = self.make()
        try:
            process.start()
            self.assertEqual(process.session_id, "pi-rpc-session-1")
            process.prompt("第一轮")
            kinds = [record.get("type") for record in process.stream(10)]
        finally:
            process.close()
        self.assertEqual(kinds[-1], "agent_settled")
        self.assertIn("tool_execution_end", kinds)
        self.assertEqual([row["text"] for row in self.entries("prompt")], ["第一轮"])

    def test_rejected_prompt_is_reported_without_running(self):
        process = self.make(mode="reject")
        try:
            process.start()
            with self.assertRaises(pi_rpc.PiRpcError):
                process.prompt("被拒")
        finally:
            process.close()

    def test_crash_after_acceptance_ends_the_stream(self):
        process = self.make(mode="crash-after-accept")
        try:
            process.start()
            process.prompt("干活")
            with self.assertRaises(pi_rpc.PiRpcClosed):
                list(process.stream(10))
        finally:
            process.close()
        self.assertEqual(len(self.entries("prompt")), 1)

    def test_the_budget_measures_silence_not_duration(self):
        # The whole turn outlives its budget while no single gap does: a turn
        # that keeps reporting progress must run to completion.
        process = self.make(mode="chatty")
        try:
            process.start()
            process.prompt("长活")
            started = time.monotonic()
            kinds = [record.get("type") for record in process.stream(0.5)]
            elapsed = time.monotonic() - started
        finally:
            process.close()
        self.assertEqual(kinds[-1], "agent_settled")
        self.assertEqual(len(self.entries("turn")), 1)
        # It really did outlive the budget it was handed.
        self.assertGreater(elapsed, 0.5)

    def test_silence_past_the_budget_still_times_out(self):
        process = self.make(mode="quiet-command")
        try:
            process.start()
            process.prompt("静默")
            with self.assertRaises(pi_rpc.PiRpcTimeout):
                list(process.stream(0.2, 0.2))
        finally:
            process.close()

    def test_a_command_in_flight_gets_the_longer_budget(self):
        # 1s of silence from a running command: fatal under the idle budget,
        # ordinary under the tool budget.
        process = self.make(mode="quiet-command")
        try:
            process.start()
            process.prompt("慢命令")
            started = time.monotonic()
            kinds = [record.get("type") for record in process.stream(0.2, 5)]
            elapsed = time.monotonic() - started
        finally:
            process.close()
        self.assertEqual(kinds[-1], "agent_settled")
        self.assertIn("tool_execution_end", kinds)
        # The command stayed quiet for longer than the idle budget.
        self.assertGreater(elapsed, 0.2)

    def test_the_tool_budget_expires_like_any_other(self):
        # A command that never comes back is still a stall, not a licence to
        # hang: it fails by its own budget.
        process = self.make(mode="quiet-command")
        try:
            process.start()
            process.prompt("卡住的命令")
            with self.assertRaises(pi_rpc.PiRpcTimeout):
                list(process.stream(5, 0.2))
        finally:
            process.close()

    def test_abort_is_sent_as_an_rpc_command(self):
        process = self.make(mode="slow")
        try:
            process.start()
            process.prompt("慢活")
            deadline = time.time() + 10
            while time.time() < deadline and not self.entries("turn"):
                time.sleep(0.05)
            self.assertTrue(process.abort())
            deadline = time.time() + 10
            while time.time() < deadline and not self.entries("abort"):
                time.sleep(0.05)
            kinds = [record.get("type") for record in process.stream(10)]
        finally:
            process.close()
        self.assertEqual(len(self.entries("abort")), 1)
        self.assertEqual(kinds[-1], "agent_settled")

    def test_hidden_launch_kwargs_cover_windows(self):
        with mock.patch.object(os, "name", "nt"):
            kwargs = conversation_providers.hidden_launch_kwargs()
        self.assertIn("creationflags", kwargs)
        import subprocess as sp
        self.assertEqual(kwargs["creationflags"], sp.CREATE_NO_WINDOW)

    def test_non_windows_launch_adds_no_flags(self):
        with mock.patch.object(os, "name", "posix"):
            self.assertEqual(conversation_providers.hidden_launch_kwargs(), {})


class PiRpcRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "pi.log"
        self.clock = FakeClock()
        self.registry = pi_rpc.PiRpcRegistry(idle_seconds=1800, clock=self.clock)
        self.provider = {
            "name": "pi", "command": sys.executable, "args": [],
            "model": None, "timeout_s": 30,
        }
        self.launcher = FakePiLauncher("normal", self.log_path)
        self.build = mock.patch.object(
            conversation_providers, "build_command", self.launcher)
        self.build.start()
        self.addCleanup(self.build.stop)

    def tearDown(self):
        self.registry.close_all()
        self.tmp.cleanup()

    def entries(self, event=None):
        if not self.log_path.is_file():
            return []
        rows = [json.loads(line) for line in
                self.log_path.read_text(encoding="utf-8").splitlines()]
        return [row for row in rows if event is None or row.get("event") == event]

    def test_one_process_serves_many_turns(self):
        key = "conv-001"
        for index in range(3):
            process = self.registry.process(key, self.provider, self.tmp.name)
            process.prompt(f"第{index}轮")
            list(process.stream(10))
        pids = {row["pid"] for row in self.entries("prompt")}
        self.assertEqual(len(pids), 1)
        self.assertEqual(len(self.entries("handshake")), 1)

    def test_handshake_failure_leaves_no_child_behind(self):
        self.launcher.fake_mode = "handshake-fail"
        with self.assertRaises(pi_rpc.PiRpcError):
            self.registry.process("conv-fail", self.provider, self.tmp.name)
        pid = self.entries("handshake-failed")[0]["pid"]
        self.assertIsNotNone(pid)
        self.assertFalse(_pid_alive(pid))
        self.assertEqual(self.registry.active(), {})

    def test_handshake_failure_restarts_once(self):
        self.launcher.fake_mode = "handshake-fail"
        with self.assertRaises(pi_rpc.PiRpcError):
            self.registry.launch_with_retry("conv-002", self.provider, self.tmp.name)
        self.assertEqual(len(self.entries("handshake-failed")), 2)

    def test_idle_expiry_closes_and_a_later_turn_restarts(self):
        key = "conv-003"
        first = self.registry.process(key, self.provider, self.tmp.name)
        first.prompt("先来一轮")
        list(first.stream(10))
        first_pid = self.entries("prompt")[0]["pid"]

        self.clock.advance(1801)
        expired = self.registry.expire_idle()
        self.assertEqual(len(expired), 1)
        self.assertFalse(first.alive)
        self.assertEqual(self.registry.active(), {})

        second = self.registry.process(key, self.provider, self.tmp.name,
                                       session_id=first.session_id)
        second.prompt("再来一轮")
        list(second.stream(10))
        pids = [row["pid"] for row in self.entries("prompt")]
        self.assertEqual(len(pids), 2)
        self.assertNotEqual(pids[0], pids[1])
        # The saved native session is what the restart resumes.
        self.assertEqual(second.session_id, "pi-rpc-session-1")
        self.assertEqual(len(self.entries("handshake")), 2)
        self.assertEqual(self.launcher.sessions[0], None)
        self.assertEqual(self.launcher.sessions[1], "pi-rpc-session-1")

    def test_idle_process_is_reused_within_the_window(self):
        key = "conv-004"
        first = self.registry.process(key, self.provider, self.tmp.name)
        self.clock.advance(1799)
        second = self.registry.process(key, self.provider, self.tmp.name)
        self.assertIs(first, second)
        self.assertEqual(self.registry.expire_idle(), [])

    def test_close_all_retires_every_process(self):
        first = self.registry.process("conv-005", self.provider, self.tmp.name)
        second = self.registry.process("conv-006", self.provider, self.tmp.name)
        self.assertEqual(self.registry.close_all(), 2)
        self.assertFalse(first.alive)
        self.assertFalse(second.alive)
        self.assertEqual(self.registry.active(), {})


class PiConversationTurnTests(unittest.TestCase):
    """The bridge must route Pi conversations through one persistent process."""

    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.bridge import conversation_providers as providers

        self.providers = providers
        self.tmp = Path(self.fixture.tmp.name)
        self.log_path = self.tmp / "pi.log"
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)
        self.provider = {
            "name": "pi", "command": sys.executable, "args": [],
            "model": None, "timeout_s": 30,
        }
        self.launcher = FakePiLauncher("normal", self.log_path)
        self.build = mock.patch.object(
            conversation_providers, "build_command", self.launcher)
        self.build.start()
        self.addCleanup(self.build.stop)
        self.registry = pi_rpc.PiRpcRegistry(idle_seconds=1800)
        self.patcher = mock.patch.object(conversations, "PI_RPC", self.registry)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.registry.close_all()
        self.pool.close()
        self.fixture.cleanup()

    def entries(self, event=None):
        if not self.log_path.is_file():
            return []
        rows = [json.loads(line) for line in
                self.log_path.read_text(encoding="utf-8").splitlines()]
        return [row for row in rows if event is None or row.get("event") == event]

    def wait_turn(self, conversation_id, turn_id, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            turn = conversations.get_turn(self.pool, conversation_id, turn_id)
            if turn["status"] not in {"queued", "running"}:
                return turn
            time.sleep(0.05)
        self.fail("turn did not finish")

    def test_three_turns_share_one_pid(self):
        with mock.patch.object(self.providers, "get", return_value=self.provider):
            conversation = conversations.create(self.pool, "pi")
            for index in range(3):
                turn = conversations.start_turn(
                    self.pool, self.workspace, conversation["conversation_id"],
                    f"第{index}轮", {"anchor": {"page_type": "kps"}},
                )
                done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])
                self.assertEqual(done["status"], "done")

        prompts = self.entries("prompt")
        self.assertEqual(
            [row["text"].split("学生消息：")[-1].strip() for row in prompts],
            ["第0轮", "第1轮", "第2轮"],
        )
        self.assertEqual(len({row["pid"] for row in prompts}), 1)
        restored = conversations.get(self.pool, conversation["conversation_id"])
        self.assertEqual(restored["provider_session_id"], "pi-rpc-session-1")
        self.assertEqual(len(restored["messages"]), 6)
        self.assertIn("第 3 轮回答", restored["messages"][-1]["content"])

    def test_cancel_sends_rpc_abort_and_mirrors_nothing(self):
        self.launcher.fake_mode = "slow"
        slow = self.provider
        with mock.patch.object(self.providers, "get", return_value=slow):
            conversation = conversations.create(self.pool, "pi")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"],
                "慢慢来", {"anchor": {"page_type": "kps"}},
            )
            # Wait until the fake is genuinely mid-turn, then cancel.
            deadline = time.time() + 10
            while time.time() < deadline and not self.entries("turn"):
                time.sleep(0.05)
            conversations.cancel(self.pool, conversation["conversation_id"])
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "cancelled", done)
        self.assertEqual(len(self.entries("abort")), 1)
        restored = conversations.get(self.pool, conversation["conversation_id"])
        self.assertEqual(restored["messages"], [])

    def test_crash_after_acceptance_is_not_replayed(self):
        self.launcher.fake_mode = "crash-after-accept"
        crash = self.provider
        with mock.patch.object(self.providers, "get", return_value=crash):
            conversation = conversations.create(self.pool, "pi")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"],
                "会崩", {"anchor": {"page_type": "kps"}},
            )
            done = self.wait_turn(conversation["conversation_id"], turn["turn_id"])

        self.assertEqual(done["status"], "failed")
        self.assertIn("rpc", (done["error"] or "").lower())
        self.assertEqual(len(self.entries("prompt")), 1)
        restored = conversations.get(self.pool, conversation["conversation_id"])
        self.assertEqual(restored["messages"], [])
        events = conversations.events(
            self.pool, conversation["conversation_id"], turn["turn_id"])
        self.assertIn("error", [event["kind"] for event in events])

    def test_the_turn_uses_rpc_mode(self):
        with mock.patch.object(self.providers, "get", return_value=self.provider):
            conversation = conversations.create(self.pool, "pi")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"],
                "一轮", {"anchor": {"page_type": "kps"}},
            )
            self.wait_turn(conversation["conversation_id"], turn["turn_id"])
        self.assertEqual(set(self.launcher.modes), {"rpc"})

    def test_shutting_the_workbench_closes_pi_processes(self):
        with mock.patch.object(self.providers, "get", return_value=self.provider):
            conversation = conversations.create(self.pool, "pi")
            turn = conversations.start_turn(
                self.pool, self.workspace, conversation["conversation_id"],
                "一轮", {"anchor": {"page_type": "kps"}},
            )
            self.wait_turn(conversation["conversation_id"], turn["turn_id"])
        self.assertEqual(len(self.registry.active()), 1)
        self.assertEqual(conversations.shutdown(), 1)
        self.assertEqual(self.registry.active(), {})


def _pid_alive(pid):
    """Whether a process id still exists (Windows: tasklist, POSIX: kill -0)."""
    if os.name == "nt":
        import subprocess as sp

        result = sp.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            **conversation_providers.hidden_launch_kwargs(),
        )
        return str(pid) in (result.stdout or "")
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
