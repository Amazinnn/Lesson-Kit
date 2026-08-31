"""Provider discovery, native command, and event normalization contracts."""

import unittest
from unittest import mock


class ConversationProviderTests(unittest.TestCase):
    @mock.patch("workbench.bridge.conversation_providers.registry.load_bridges")
    @mock.patch("workbench.bridge.conversation_providers.shutil.which")
    def test_discovers_path_providers_and_limits_overrides(self, which, load_bridges):
        from workbench.bridge import conversation_providers

        which.side_effect = lambda name: f"C:/bin/{name}.cmd" if name in {"codex", "claude"} else None
        load_bridges.return_value = {
            "providers": {
                "codex": {
                    "command": "C:/unsafe/custom.exe",
                    "args": ["--profile", "teacher"],
                    "model": "gpt-test",
                    "timeout_s": 42,
                    "cwd_mode": "elsewhere",
                }
            }
        }

        providers = {item["name"]: item for item in conversation_providers.discover()}

        self.assertEqual(providers["codex"]["command"], "C:/bin/codex.cmd")
        self.assertEqual(providers["codex"]["args"], ["--profile", "teacher"])
        self.assertEqual(providers["codex"]["model"], "gpt-test")
        self.assertEqual(providers["codex"]["timeout_s"], 42)
        self.assertNotIn("cwd_mode", providers["codex"])
        self.assertEqual(providers["claude"]["command"], "C:/bin/claude.cmd")

    def test_codex_uses_stable_new_and_resume_commands(self):
        from workbench.bridge import conversation_providers

        provider = {
            "name": "codex", "command": "codex", "args": ["--profile", "teacher"],
            "model": "gpt-test", "timeout_s": 30,
        }
        new = conversation_providers.build_command(provider)
        resumed = conversation_providers.build_command(provider, "session-123")

        self.assertEqual(
            new,
            ["codex", "exec", "--skip-git-repo-check", "--json", "--model", "gpt-test", "--profile", "teacher", "-"],
        )
        self.assertEqual(
            resumed,
            ["codex", "exec", "--skip-git-repo-check", "resume", "--json", "--model", "gpt-test", "--profile", "teacher", "session-123", "-"],
        )

    def test_claude_uses_print_stream_json_and_resume(self):
        from workbench.bridge import conversation_providers

        provider = {"name": "claude", "command": "claude", "args": [], "model": None}
        new = conversation_providers.build_command(provider)
        resumed = conversation_providers.build_command(provider, "session-456")

        self.assertEqual(
            new,
            ["claude", "--print", "--output-format", "stream-json", "--verbose", "--include-partial-messages"],
        )
        self.assertEqual(
            resumed,
            ["claude", "--print", "--output-format", "stream-json", "--verbose", "--include-partial-messages", "--resume", "session-456"],
        )

    def test_normalizes_codex_session_text_and_turn_activity(self):
        from workbench.bridge import conversation_providers

        started = conversation_providers.normalize_event(
            "codex", {"type": "thread.started", "thread_id": "thread-1"}
        )
        message = conversation_providers.normalize_event(
            "codex",
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Answer"}},
        )
        phase = conversation_providers.normalize_event(
            "codex", {"type": "turn.started"}
        )

        self.assertEqual(started["provider_session_id"], "thread-1")
        self.assertEqual(message, {"kind": "text", "text": "Answer"})
        self.assertEqual(phase, {
            "kind": "activity", "activity_id": "provider-turn",
            "activity_type": "progress", "status": "running",
            "label": "Agent 正在处理",
        })

    def test_normalizes_codex_command_updates_as_one_activity(self):
        from workbench.bridge import conversation_providers

        started = conversation_providers.normalize_event("codex", {
            "type": "item.started",
            "item": {"id": "item-7", "type": "command_execution", "command": "wb pull"},
        })
        completed = conversation_providers.normalize_event("codex", {
            "type": "item.completed",
            "item": {
                "id": "item-7", "type": "command_execution", "command": "wb pull",
                "aggregated_output": "2 problems", "exit_code": 0,
            },
        })

        self.assertEqual(started["activity_id"], "item-7")
        self.assertEqual(started["status"], "running")
        self.assertEqual(started["label"], "运行命令")
        self.assertEqual(completed["activity_id"], "item-7")
        self.assertEqual(completed["status"], "done")
        self.assertEqual(completed["output"], "2 problems")

    def test_normalizes_claude_bash_and_tool_result(self):
        from workbench.bridge import conversation_providers

        started = conversation_providers.normalize_event("claude", {
            "type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": "tool-2", "name": "Bash",
                "input": {"command": "python -m pytest"},
            }]},
        })
        completed = conversation_providers.normalize_event("claude", {
            "type": "user", "message": {"content": [{
                "type": "tool_result", "tool_use_id": "tool-2", "content": "12 passed",
            }]},
        })

        self.assertEqual(started["activity_type"], "command")
        self.assertEqual(started["detail"], "python -m pytest")
        self.assertEqual(completed["activity_id"], "tool-2")
        self.assertEqual(completed["status"], "done")
        self.assertEqual(completed["output"], "12 passed")
        self.assertNotIn("label", completed)

    def test_reasoning_activity_never_contains_reasoning_text(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("codex", {
            "type": "item.completed",
            "item": {"id": "thought-1", "type": "reasoning", "text": "private reasoning"},
        })

        self.assertEqual(event["label"], "分析任务")
        self.assertNotIn("detail", event)
        self.assertNotIn("output", event)

    def test_normalizes_claude_partial_and_session(self):
        from workbench.bridge import conversation_providers

        partial = conversation_providers.normalize_event(
            "claude",
            {
                "type": "stream_event",
                "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Part"}},
            },
        )
        initialized = conversation_providers.normalize_event(
            "claude", {"type": "system", "subtype": "init", "session_id": "claude-1"}
        )
        self.assertEqual(partial, {"kind": "text", "text": "Part"})
        self.assertEqual(initialized["provider_session_id"], "claude-1")

    def test_explicit_result_title_is_preserved(self):
        from workbench.bridge import conversation_providers

        codex = conversation_providers.normalize_event(
            "codex",
            {"type": "item.completed", "item": {
                "type": "agent_message", "text": "Answer", "title": "组合计数"
            }},
        )
        claude = conversation_providers.normalize_event(
            "claude",
            {"type": "result", "result": "Answer", "session_id": "s-1", "title": "组合计数"},
        )
        self.assertEqual(codex["title"], "组合计数")
        self.assertEqual(claude["title"], "组合计数")


if __name__ == "__main__":
    unittest.main()
