"""Managed Paper handoff is a validated presentation action, not model navigation."""

import unittest

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


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


class VerifiedPaperArtifactTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.root = self.fixture.ws
        self.workspace = {
            "path": str(self.fixture.ws),
            "db": "pool/dmath.db",
            "active_course": "dmath",
            "active_chapter": "ch06",
        }
        self.events = self.fixture.ws / ".lessonkit" / "jobs" / "conv-001" / "events.jsonl"
        self.events.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.fixture.cleanup()

    def _verify(self, notice):
        from workbench.bridge import conversations

        return conversations._verified_paper_artifact(
            notice, self.root, self.workspace, self.events)

    def test_managed_record_supplies_identity_title_and_count(self):
        from workbench.data import practice_sets
        from workbench.data.pool import Pool

        pool = Pool(root=self.fixture.ws, db_path=self.fixture.db_path,
                    course="dmath", chapter="ch06")
        try:
            practice_sets.create_saved(pool, "受管试卷", ["dmath-ch06-prob-001"])
        finally:
            pool.close()

        notice = self._verify({
            "type": "paper_artifact", "practice_set_id": "ps-001",
            "title": "模型自称", "item_count": 987, "summary": "receipt",
        })

        self.assertEqual(notice["practice_set_id"], "ps-001")
        self.assertEqual(notice["title"], "受管试卷")
        self.assertEqual(notice["item_count"], 1)
        self.assertEqual(notice["summary"], "receipt")

    def test_unknown_paper_id_is_dropped_and_recorded(self):
        notice = self._verify({
            "type": "paper_artifact", "practice_set_id": "ps-999999",
            "title": "FAKE TITLE", "item_count": 987,
        })

        self.assertIsNone(notice)
        recorded = self.events.read_text(encoding="utf-8")
        self.assertIn("ps-999999", recorded)
        self.assertIn("error", recorded)


if __name__ == "__main__":
    unittest.main()
