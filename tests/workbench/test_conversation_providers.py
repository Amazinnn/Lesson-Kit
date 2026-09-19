"""Provider discovery, native command, and event normalization contracts."""

import unittest
from unittest import mock


class ConversationProviderTests(unittest.TestCase):
    @mock.patch("workbench.bridge.conversation_providers.registry.load_bridges")
    @mock.patch("workbench.bridge.conversation_providers.shutil.which")
    def test_configured_command_wins_and_other_overrides_stay_limited(self, which, load_bridges):
        from workbench.bridge import conversation_providers

        which.side_effect = lambda name: f"C:/bin/{name}.cmd" if name in {"codex", "claude", "pi"} else None
        load_bridges.return_value = {
            "providers": {
                "codex": {
                    "command": "C:/pinned/codex.exe",
                    "args": ["--profile", "teacher"],
                    "model": "gpt-test",
                    "timeout_s": 42,
                    "cwd_mode": "elsewhere",
                }
            }
        }

        providers = {item["name"]: item for item in conversation_providers.discover()}

        self.assertEqual(providers["codex"]["command"], "C:/pinned/codex.exe")
        self.assertEqual(providers["codex"]["args"], ["--profile", "teacher"])
        self.assertEqual(providers["codex"]["model"], "gpt-test")
        self.assertEqual(providers["codex"]["timeout_s"], 42)
        self.assertNotIn("cwd_mode", providers["codex"])
        self.assertEqual(providers["claude"]["command"], "C:/bin/claude.cmd")
        self.assertEqual(providers["pi"]["command"], "C:/bin/pi.cmd")

    @mock.patch("workbench.bridge.conversation_providers.registry.load_bridges")
    @mock.patch("workbench.bridge.conversation_providers.shutil.which")
    def test_configured_command_is_discovered_without_path(self, which, load_bridges):
        from workbench.bridge import conversation_providers

        which.return_value = None
        load_bridges.return_value = {
            "providers": {"pi": {"command": "C:/npm-global/pi.cmd", "model": "minimax/MiniMax-M2.7"}}
        }

        providers = {item["name"]: item for item in conversation_providers.discover()}

        self.assertEqual(list(providers), ["pi"])
        self.assertEqual(providers["pi"]["command"], "C:/npm-global/pi.cmd")
        self.assertEqual(providers["pi"]["model"], "minimax/MiniMax-M2.7")

    def test_pi_uses_print_json_and_native_session_resume(self):
        from workbench.bridge import conversation_providers

        provider = {
            "name": "pi", "command": "pi", "args": [], "model": "minimax/MiniMax-M2.7",
        }
        new = conversation_providers.build_command(provider)
        resumed = conversation_providers.build_command(provider, "01a0af85-5427")

        self.assertEqual(
            new,
            ["pi", "--print", "--mode", "json", "--model", "minimax/MiniMax-M2.7"],
        )
        self.assertEqual(
            resumed,
            ["pi", "--print", "--mode", "json", "--model", "minimax/MiniMax-M2.7",
             "--session", "01a0af85-5427"],
        )

    def test_normalizes_pi_session_and_text_delta(self):
        from workbench.bridge import conversation_providers

        header = conversation_providers.normalize_event(
            "pi", {"type": "session", "version": 3, "id": "pi-session-1", "cwd": "D:/ws"}
        )
        delta = conversation_providers.normalize_event("pi", {
            "type": "message_update", "usage": {"input": 11},
            "assistantMessageEvent": {"type": "text_delta", "contentIndex": 0, "delta": "Part"},
        })

        self.assertEqual(header["provider_session_id"], "pi-session-1")
        self.assertEqual(header["kind"], "phase")
        self.assertEqual(delta, {"kind": "text", "text": "Part"})

    def test_pi_user_message_is_never_treated_as_the_answer(self):
        from workbench.bridge import conversation_providers

        echoed = conversation_providers.normalize_event("pi", {
            "type": "message_end",
            "message": {"role": "user", "content": [{"type": "text", "text": "学生的问题"}]},
        })

        self.assertEqual(echoed["kind"], "phase")

    def test_pi_reports_stream_error_even_when_the_process_succeeds(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "message_end",
            "message": {
                "role": "assistant", "content": [], "stopReason": "error",
                "errorMessage": "401 invalid api key",
            },
        })

        self.assertEqual(event, {"kind": "error", "text": "401 invalid api key"})

    def test_pi_final_answer_comes_from_the_authoritative_message(self):
        from workbench.bridge import conversation_providers

        message = {
            "role": "assistant",
            "content": [{"type": "text", "text": "结论：先数重复。"}],
            "stopReason": "stop",
        }
        ended = conversation_providers.normalize_event(
            "pi", {"type": "message_end", "message": message}
        )
        settled = conversation_providers.normalize_event(
            "pi", {"type": "agent_end", "messages": [message], "willRetry": False}
        )

        self.assertEqual(ended, {"kind": "result", "text": "结论：先数重复。"})
        self.assertEqual(settled, {"kind": "result", "text": "结论：先数重复。"})

    def test_normalizes_pi_command_and_tool_updates_as_one_activity(self):
        from workbench.bridge import conversation_providers

        started = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_start",
            "toolCallId": "call-9", "toolName": "bash", "args": {"command": "lesson-kit pull"},
        })
        completed = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end",
            "toolCallId": "call-9", "toolName": "bash",
            "result": {"content": [{"type": "text", "text": "2 problems"}], "details": {}},
            "isError": False,
        })

        self.assertEqual(started["activity_id"], "call-9")
        self.assertEqual(started["activity_type"], "command")
        self.assertEqual(started["label"], "运行命令")
        self.assertEqual(started["detail"], "lesson-kit pull")
        self.assertEqual(started["status"], "running")
        self.assertEqual(completed["activity_id"], "call-9")
        self.assertEqual(completed["status"], "done")
        self.assertEqual(completed["output"], "2 problems")

    def test_pi_tool_output_is_readable_text_not_a_json_envelope(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end",
            "toolCallId": "call-10", "toolName": "read",
            "result": {"content": [{"type": "text", "text": "line one\nline two"}],
                       "details": {"bytes": 18}},
            "isError": False,
        })

        self.assertEqual(event["output"], "line one\nline two")
        self.assertNotIn("{", event["output"])

    def test_pi_failed_tool_call_is_marked_failed(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end",
            "toolCallId": "call-11", "toolName": "bash",
            "result": {"content": [{"type": "text", "text": "No such file"}], "details": {}},
            "isError": True,
        })

        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["output"], "No such file")

    def test_pi_partial_tool_output_updates_the_same_running_row(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_update",
            "toolCallId": "call-12", "toolName": "bash", "args": {"command": "ls -la"},
            "partialResult": {"content": [{"type": "text", "text": "total 8"}], "details": {}},
        })

        self.assertEqual(event["activity_id"], "call-12")
        self.assertEqual(event["status"], "running")
        self.assertEqual(event["detail"], "ls -la")
        self.assertEqual(event["output"], "total 8")

    def test_pi_reasoning_activity_never_contains_reasoning_text(self):
        from workbench.bridge import conversation_providers

        started = conversation_providers.normalize_event("pi", {
            "type": "message_update",
            "assistantMessageEvent": {"type": "thinking_start"},
        })
        delta = conversation_providers.normalize_event("pi", {
            "type": "message_update",
            "assistantMessageEvent": {"type": "thinking_delta", "delta": "private reasoning"},
        })
        ended = conversation_providers.normalize_event("pi", {
            "type": "message_update",
            "assistantMessageEvent": {"type": "thinking_end"},
        })

        self.assertEqual(started["label"], "分析任务")
        self.assertEqual(started["status"], "running")
        self.assertEqual(ended["status"], "done")
        for event in (started, ended):
            self.assertNotIn("detail", event)
            self.assertNotIn("output", event)
        self.assertIsNone(delta)

    def test_pi_emits_one_reasoning_row_per_block_not_one_per_delta(self):
        from workbench.bridge import conversation_providers

        events = [
            conversation_providers.normalize_event("pi", {
                "type": "message_update",
                "assistantMessageEvent": {"type": "thinking_delta", "delta": str(index)},
            })
            for index in range(25)
        ]

        self.assertEqual(set(events), {None})

    def test_pi_protocol_noise_is_dropped_not_logged(self):
        from workbench.bridge import conversation_providers

        for marker in ("text_start", "text_end", "toolcall_delta"):
            event = conversation_providers.normalize_event("pi", {
                "type": "message_update",
                "assistantMessageEvent": {"type": marker, "delta": ""},
            })
            self.assertIsNone(event)

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
