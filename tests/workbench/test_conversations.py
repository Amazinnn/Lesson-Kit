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
            },
        })
        kwargs = apply_batch.call_args.kwargs
        self.assertEqual(kwargs["source"], "bridge")
        self.assertTrue(str(kwargs["backup_path"]).endswith(
            f"{conversation['conversation_id']}-{turn['turn_id']}-ingest-backup"))

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
            "上一轮出题动作已成功入库：批次 batch-007（flash-card-patch，3 条）。"
            "不要重复提交相同内容。",
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
            "上一轮出题动作被门禁拒收（零写入），逐条原因：\n"
            + error
            + "\n请修正 manifest 后重新提交完整的 lessonkit-action 区块。",
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
            "上一轮出题动作区块无效：action block is not valid JSON。"
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
        return conversations._extract_action(answer, context)

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

    def test_malformed_json_is_disclosed_as_ignored(self):
        cleaned, action = self._run(self._answer("{oops}"), {"goal_intent": True})
        self.assertEqual(action, {"ignored": "no block matched the active intent"})
        self.assertNotIn("lessonkit-action", cleaned)


class CheckIngestActionExtractionTests(unittest.TestCase):
    def _run(self, body, context):
        from workbench.bridge import conversations

        answer = "已生成。\n```lessonkit-action\n" + body + "\n```"
        return conversations._extract_action(answer, context)

    def _extract(self, answer, context):
        from workbench.bridge import conversations

        return conversations._extract_action(answer, context)

    def test_prompt_describes_check_ingest_manifest_contract(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("帮我补池", {"check_intent": True})
        self.assertIn("flash-card-patch", prompt)
        self.assertIn("micro-quiz-patch", prompt)
        self.assertIn("source_evidence", prompt)
        self.assertIn("对话内出题一律用 lessonkit-action 区块", prompt)
        self.assertIn("禁止直接运行 wb ingest", prompt)
        self.assertIn("topic_label", prompt)
        self.assertIn("数学乘号一律用 ×", prompt)
        self.assertIn('"card_id":"dmath-ch06-fc-901"', prompt)
        self.assertIn('"problem_id":"dmath-ch06-mq-901"', prompt)
        self.assertIn(
            "若上下文含 last_check_outcome：成功则不要重复提交相同内容；"
            "被拒收则按逐条原因\n修正后重新提交完整区块。",
            prompt,
        )

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

    def test_without_check_intent_block_is_disclosed_as_ignored(self):
        cleaned, action = self._run(
            '{"type":"check_ingest","manifest":{"kind":"flash-card-patch",'
            '"items":[{"card_id":"card-001"}]}}',
            {"check_intent": False},
        )
        self.assertEqual(action, {"ignored": "no block matched the active intent"})
        self.assertNotIn("lessonkit-action", cleaned)

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
            "error": "manifest kind must be flash-card-patch or micro-quiz-patch",
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

    def test_bad_json_without_check_intent_is_disclosed_as_ignored(self):
        cleaned, action = self._run("{oops}", {"check_intent": False})
        self.assertEqual(action, {"ignored": "no block matched the active intent"})
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
