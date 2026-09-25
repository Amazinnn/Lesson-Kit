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

    @mock.patch("workbench.bridge.conversation_providers.registry.load_bridges")
    @mock.patch("workbench.bridge.conversation_providers.shutil.which")
    def test_turn_budgets_stay_inside_what_each_provider_can_honor(self, which, load_bridges):
        from workbench.bridge import conversation_providers

        which.return_value = None
        load_bridges.return_value = {
            "providers": {
                "codex": {"command": "codex"},
                "claude": {"command": "claude", "timeout_s": 3600},
                "pi": {"command": "pi", "timeout_s": 600, "tool_timeout_s": 99999},
            }
        }

        providers = {item["name"]: item for item in conversation_providers.discover()}

        # Defaults: a silence budget of 5 minutes, 20 for a command in flight.
        self.assertEqual(providers["codex"]["timeout_s"], 300)
        self.assertEqual(providers["codex"]["tool_timeout_s"], 1200)
        # A silence budget above the tool default raises the tool budget with it,
        # so a running command is never cut off sooner than an idle turn.
        self.assertEqual(providers["claude"]["timeout_s"], 3600)
        self.assertEqual(providers["claude"]["tool_timeout_s"], 3600)
        # Pi is capped below the RPC idle window that recycles its process.
        self.assertEqual(providers["pi"]["timeout_s"], 600)
        self.assertLess(providers["pi"]["tool_timeout_s"],
                        conversation_providers.IDLE_SECONDS)

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

    def test_normalizes_pi_lesson_kit_command_updates_as_one_activity(self):
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
        self.assertEqual(started["activity_type"], "lesson-kit")
        self.assertEqual(started["label"], "操作 Lesson Kit")
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

    def test_pi_classifies_concrete_tools_without_exposing_write_contents(self):
        from workbench.bridge import conversation_providers

        cases = [
            ("read", {"path": "docs/GLOSSARY.md"}, "file-read", "读取文件"),
            ("view", {"file_path": "diagram.png"}, "file-read", "读取文件"),
            ("write", {"path": "notes.md", "content": "private body"},
             "file-write", "更新文件"),
            ("apply_patch", {"file_path": "app.py", "patch": "private patch"},
             "file-write", "更新文件"),
            ("grep", {"pattern": "origin_kind"}, "search", "搜索"),
            ("custom_tool", {"value": "not shown"}, "tool", "调用 custom_tool"),
        ]

        for index, (name, args, activity_type, label) in enumerate(cases):
            with self.subTest(name=name):
                event = conversation_providers.normalize_event("pi", {
                    "type": "tool_execution_start", "toolCallId": f"call-{index}",
                    "toolName": name, "args": args,
                })
                self.assertEqual(event["activity_type"], activity_type)
                self.assertEqual(event["label"], label)
                self.assertNotIn("private", event.get("detail", ""))
                self.assertNotIn("not shown", event.get("detail", ""))

    def test_pi_activity_details_and_output_are_redacted_and_bounded(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "secret-call",
            "toolName": "bash",
            "args": {"command": "TOKEN=abc123 " + ("x" * 800)},
            "result": {"content": [{"type": "text",
                                     "text": "MINIMAX_API_KEY=very-secret " + ("y" * 5000)}]},
            "isError": False,
        })

        self.assertNotIn("abc123", event["detail"])
        self.assertNotIn("very-secret", event["output"])
        self.assertLessEqual(len(event["detail"]), 500)
        self.assertLessEqual(len(event["output"]), 4000)

    def test_failed_pi_activity_carries_a_visible_bounded_summary(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-1", "toolName": "bash",
            "args": {"command": "lesson-kit data create kp --input manifest.json"},
            "result": {"content": [{"type": "text", "text":
                                    "usage: lesson-kit data [-h] ...\n"
                                    "lesson-kit data: error: argument action: invalid choice: 'kp'"}]},
            "isError": True,
        })

        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["summary"],
                         "lesson-kit data: error: argument action: invalid choice: 'kp'")
        self.assertLessEqual(len(event["summary"]), 240)
        # the command stays visible and the full output stays folded
        self.assertIn("lesson-kit data create kp", event["detail"])
        self.assertIn("usage: lesson-kit data", event["output"])

    def test_failed_pi_activity_summary_is_redacted_and_bounded(self):
        from workbench.bridge import conversation_providers

        # the secret sits inside the summary window, so redaction must happen
        # before the bound is applied
        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-2", "toolName": "bash",
            "args": {"command": "lesson-kit data dmath create kp --input m.json"},
            "result": {"content": [{"type": "text", "text":
                                    "MINIMAX_API_KEY=very-secret-value " + ("z" * 400)}]},
            "isError": True,
        })

        self.assertEqual(event["status"], "failed")
        self.assertLessEqual(len(event["summary"]), 240)
        self.assertIn("[REDACTED]", event["summary"])
        self.assertNotIn("very-secret-value", event["summary"])
        self.assertNotIn("very-secret-value", event["output"])

    def test_failed_pi_activity_summary_keeps_a_long_error_line_bounded(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-2b", "toolName": "bash",
            "args": {"command": "lesson-kit data dmath create kp --input m.json"},
            "result": {"content": [{"type": "text", "text":
                                    "lesson-kit data: error: " + ("detail " * 80)}]},
            "isError": True,
        })

        self.assertEqual(event["status"], "failed")
        self.assertLessEqual(len(event["summary"]), 240)
        # the diagnostic lead-in survives the bound
        self.assertTrue(event["summary"].startswith("lesson-kit data: error:"))

    def test_failed_pi_activity_without_output_shows_a_generic_summary(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-3", "toolName": "bash",
            "args": {"command": "lesson-kit data dmath create kp --input m.json"},
            "result": {"content": []},
            "isError": True,
        })

        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["summary"], "执行失败，未返回诊断信息")

    def test_successful_pi_activity_never_gets_a_failure_summary(self):
        from workbench.bridge import conversation_providers

        event = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-4", "toolName": "bash",
            "args": {"command": "lesson-kit data dmath list kp"},
            "result": {"content": [{"type": "text", "text":
                                    '{"error": null, "items": []}  # no error, honestly'}]},
            "isError": False,
        })

        self.assertEqual(event["status"], "done")
        self.assertNotIn("summary", event)

    def test_a_corrected_invocation_keeps_its_own_outcome(self):
        from workbench.bridge import conversation_providers

        failed = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-5", "toolName": "bash",
            "args": {"command": "lesson-kit data create kp --input m.json"},
            "result": {"content": [{"type": "text", "text": "usage: ... error: invalid choice"}]},
            "isError": True,
        })
        corrected = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_end", "toolCallId": "call-6", "toolName": "bash",
            "args": {"command": "lesson-kit data dmath create kp --input m.json"},
            "result": {"content": [{"type": "text", "text": '{"kp_id": "dmath-ch06-kp-777"}'}]},
            "isError": False,
        })

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(corrected["status"], "done")
        self.assertNotEqual(failed["activity_id"], corrected["activity_id"])
        self.assertIn("summary", failed)
        self.assertNotIn("summary", corrected)

    def test_pi_shell_path_containing_lesson_kit_is_not_a_cli_invocation(self):
        from workbench.bridge import conversation_providers

        ordinary = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_start", "toolCallId": "write-via-shell",
            "toolName": "bash",
            "args": {"command": (
                "cd /tmp/lesson-kit-pre-release-123 && "
                "printf marker > acceptance-output.txt"
            )},
        })
        module = conversation_providers.normalize_event("pi", {
            "type": "tool_execution_start", "toolCallId": "module-cli",
            "toolName": "bash",
            "args": {"command": "python -m workbench.cli.main pull acceptance --n 1"},
        })

        self.assertEqual(ordinary["activity_type"], "command")
        self.assertEqual(ordinary["label"], "运行命令")
        self.assertEqual(module["activity_type"], "lesson-kit")
        self.assertEqual(module["label"], "操作 Lesson Kit")

    def test_pi_reasoning_lifecycle_has_no_learner_facing_activity(self):
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

        self.assertIsNone(started)
        self.assertIsNone(ended)
        self.assertIsNone(delta)

    def test_pi_generic_lifecycle_has_no_activity_row(self):
        from workbench.bridge import conversation_providers

        self.assertIsNone(conversation_providers.normalize_event(
            "pi", {"type": "turn_start"}
        ))
        self.assertIsNone(conversation_providers.normalize_event(
            "pi", {"type": "message_start", "message": {"role": "assistant"}}
        ))

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
