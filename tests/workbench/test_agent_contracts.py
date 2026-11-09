"""Small always-on Agent map with detailed contracts available on demand."""

import contextlib
import io
import unittest


class AgentContractTests(unittest.TestCase):
    def test_contract_topics_are_small_and_explicit(self):
        from workbench.bridge import agent_contracts

        self.assertEqual(
            agent_contracts.topics(),
            ["commands", "attempts", "practice", "actions", "content", "grading"],
        )
        content = agent_contracts.get("content")
        self.assertIn("content-bundle v2", content)
        self.assertIn("problem-patch", content)
        self.assertIn("staged_manifest_dir", content)
        self.assertIn("source_evidence", content)
        self.assertIn("zero-write", content)
        self.assertNotIn("entire submitted manifest is zero-write", content)
        self.assertNotIn("rejects the whole manifest", content)
        self.assertIn("Problem parts (综合题小问)", content)
        self.assertIn("Do not also declare `quiz_type`", content)

    def test_contract_module_is_a_read_only_discovery_cli(self):
        from workbench.bridge import agent_contracts

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = agent_contracts.main(["list"])
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue().splitlines(), agent_contracts.topics())

    def test_turn_prompt_is_a_map_not_the_full_manual(self):
        from workbench.bridge import agent_contracts, conversations

        prompt = conversations._prompt("我上一题为什么错了？", {
            "workspace": {"name": "dmath", "course": "dmath", "chapter": "ch06"},
            "anchor": {"page_type": "practice", "problem_id": "p2"},
            "focus": {
                "type": "problem", "problem_ids": ["p1"],
                "basis": "user_previous_reference",
            },
            "working_set": {"kind": "practice", "items": []},
        })
        self.assertNotIn("失败零写入", prompt)
        self.assertIn("独立有效项照常完成", prompt)

        self.assertIn("context.focus", prompt)
        self.assertIn("context.working_set", prompt)
        self.assertIn("主动读取 Lesson Kit 数据", prompt)
        self.assertIn("python -m workbench.bridge.agent_contracts list", prompt)
        self.assertIn("普通教学问答无需读取无关契约", prompt)
        self.assertIn("parts（综合题小问", prompt)
        for topic in agent_contracts.topics():
            self.assertIn(topic, prompt)
        # A normal turn should carry a map and a compact schema reminder, not
        # the many-page operational manual that existed before disclosure.
        self.assertLess(len(prompt), 7000)

    def test_problem_type_guidance_matches_the_machine_enum(self):
        from workbench import ingest
        from workbench.bridge import agent_contracts, conversations

        prompt = conversations._prompt("q", {})
        compact = prompt.split("6) 题目字段：", 1)[1].split("7) 练习题型", 1)[0]
        compact_values = compact.split("machine enum: ", 1)[1].split(";", 1)[0].split("/")
        content = agent_contracts.get("content")
        detailed = next(line for line in content.splitlines()
                        if "problem_type` (required; machine enum:" in line)
        detailed_values = (
            detailed.split("machine enum: ", 1)[1].split(";", 1)[0].split("/")
        )

        self.assertEqual(set(compact_values), ingest.PROBLEM_TYPES)
        self.assertEqual(set(detailed_values), ingest.PROBLEM_TYPES)
        self.assertIn("proof = 证明题", compact)
        self.assertIn("proof = 证明题", detailed)
        self.assertNotIn("证明题", compact_values)
        self.assertNotIn("证明题", detailed_values)

    def test_detailed_micro_contract_covers_new_and_in_place_items(self):
        from workbench.bridge import agent_contracts

        content = agent_contracts.get("content")
        self.assertIn(
            "Every new micro quiz and in-place micro conversion MUST map to "
            "exactly one knowledge point in `kp_ids`.",
            content,
        )
        self.assertIn(
            "`yes_no` answer key is one scalar option string",
            content,
        )
        self.assertIn(
            "`single_choice` answer key is one scalar option string contained in `options`",
            content,
        )
        self.assertIn(
            "`multiple_choice` answer key is a non-empty list of option strings",
            content,
        )

    def test_commands_contract_documents_read_only_evidence_access(self):
        from workbench.bridge import agent_contracts

        commands = agent_contracts.get("commands")
        self.assertIn(
            "lesson-kit evidence <workspace> kp <kp-id> [--limit 1..20]",
            commands,
        )
        self.assertIn("default 8, maximum 20", commands)
        self.assertIn("read-only", commands)
        self.assertIn("recorded facts", commands)
        self.assertIn("do not infer learning labels", commands)

    def test_historical_claims_require_human_readable_evidence(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("我是不是经常错这里？", {
            "workspace": {"name": "dmath", "course": "dmath", "chapter": "ch06"},
        })
        self.assertIn("必须先依据实际学习记录", prompt)
        self.assertIn("题目内容/主题、具体作答表现、练习时间或场景", prompt)
        self.assertIn("不要把数据库主键、哈希、内部文件名或实现路径当成主要证据", prompt)
        self.assertIn("1–3 个代表例子", prompt)
        self.assertIn("证据不足时降低结论强度", prompt)

    def test_attempts_contract_documents_paper_bound_import(self):
        from workbench.bridge import agent_contracts

        attempts = agent_contracts.get("attempts")
        # Explicit learner intent is the only import trigger; discussion is not.
        self.assertIn(
            "Use this contract only when the learner explicitly asks to record",
            attempts)
        self.assertIn("Ordinary tutoring and reading existing answers are "
                      "zero-write", attempts)
        self.assertIn("MUST NOT create attempts or ratings", attempts)
        # Manifest-level paper_id and the binding modes it selects.
        self.assertIn('"paper_id": "ps-001"', attempts)
        self.assertIn("`paper_id` is optional", attempts)
        self.assertIn("binds the answers to that Paper's progress in the same "
                      "transaction", attempts)
        self.assertIn("A selected Paper is updated in place", attempts)
        self.assertIn("parked checkpoint", attempts)
        self.assertIn("new `on_submit` checkpoint without becoming the active "
                      "practice", attempts)
        # Re-binding keeps history; ungraded import stops at execution progress.
        self.assertIn("new attempt appended and re-linked; the old attempt "
                      "remains", attempts)
        self.assertIn("changes only Paper execution progress, not learning "
                      "signals", attempts)
        # Completion follows the execution mode; a legacy Paper may archive.
        self.assertIn("legacy Paper may archive when its last pending item is "
                      "imported", attempts)
        self.assertIn("wait for the learner's explicit submission", attempts)

    def test_attempts_and_content_contracts_document_the_three_step_repair(self):
        from workbench.bridge import agent_contracts

        attempts = agent_contracts.get("attempts")
        content = agent_contracts.get("content")
        practice = agent_contracts.get("practice")
        for topic in (attempts, content, practice):
            self.assertIn("lesson-kit papers", topic)
            self.assertIn("append", topic)
        # Governed content creation first, never invented inside the manifest.
        self.assertIn("do not invent it inside the manifest", attempts)
        self.assertIn("governed content path", attempts)
        self.assertIn("truthful source evidence", attempts)
        self.assertIn("Never edit `.lessonkit/practice-sets/ps-*.json`", attempts)
        self.assertIn("ordinary governed content", content)
        self.assertIn("truthful `source_evidence`", content)
        self.assertIn("Do not invent the problem, its knowledge point, or its source",
                      content)

    def test_practice_contract_separates_append_from_membership_update(self):
        from workbench.bridge import agent_contracts

        practice = agent_contracts.get("practice")
        self.assertIn(
            "lesson-kit papers <workspace> append <ps-NNN> --problem <problem-id>",
            practice)
        self.assertIn("appends at the end, preserves every existing item's state",
                      practice)
        self.assertIn("idempotent", practice)
        self.assertIn("`papers update` remains the membership/order edit that "
                      "resets unfinished progress", practice)
        self.assertIn("do not use it for the missing-problem repair", practice)

    def test_prompt_carries_paper_import_and_repair_rule(self):
        from workbench.bridge import conversations

        prompt = conversations._prompt("把纸上写的答案导入试卷进度", {
            "workspace": {"name": "dmath", "course": "dmath", "chapter": "ch06"},
        })
        self.assertIn("导入纸上作答时，attempts 清单可带 paper_id 绑定已保存试卷", prompt)
        self.assertIn("题池缺题时先用 content-bundle", prompt)
        self.assertIn("papers append 追加到卷末，最后导入", prompt)
        self.assertIn("不得直接改试卷 JSON", prompt)


if __name__ == "__main__":
    unittest.main()
