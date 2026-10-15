"""Managed Paper handoff is a validated presentation action, not model navigation."""

import unittest


class PaperArtifactActionTests(unittest.TestCase):
    def test_valid_paper_artifact_is_cleaned_without_page_intent(self):
        from workbench.bridge import conversation_actions

        answer = """试卷已保存。\n```lessonkit-action
{"type":"paper_artifact","practice_set_id":"ps-017","title":"期中复习","item_count":12,"summary":"覆盖本章薄弱知识点。","url":"https://evil.invalid/"}
```"""
        visible, content, notice = conversation_actions.extract_action(answer, {})

        self.assertEqual(visible, "试卷已保存。")
        self.assertEqual(content, [])
        self.assertEqual(notice, {
            "type": "paper_artifact",
            "practice_set_id": "ps-017",
            "title": "期中复习",
            "summary": "覆盖本章薄弱知识点。",
            "item_count": 12,
        })
        self.assertNotIn("url", notice)

    def test_invalid_paper_identity_is_not_rendered(self):
        from workbench.bridge import conversation_actions

        answer = """完成。\n```lessonkit-action
{"type":"paper_artifact","practice_set_id":"../../admin","title":"x"}
```"""
        visible, content, notice = conversation_actions.extract_action(answer, {})

        self.assertEqual(visible, "完成。")
        self.assertEqual(content, [])
        self.assertIsNone(notice)

    def test_actions_contract_requires_receipt_derived_paper_handoff(self):
        from workbench.bridge import agent_contracts

        actions = agent_contracts.get("actions")
        self.assertIn('"type":"paper_artifact"', actions)
        self.assertIn("successful `lesson-kit papers", actions)
        self.assertIn("receipt", actions)
        self.assertIn("must not navigate automatically", actions)


if __name__ == "__main__":
    unittest.main()
