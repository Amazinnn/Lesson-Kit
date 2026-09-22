"""Keep current entry documents aligned while OpenSpec changes are active."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT_ENTRIES = (
    "docs/REQUIREMENTS.md",
    "FILE_CONTRACT.md",
    "TASK_ROUTER.md",
    ".claude/CLAUDE.md",
    "CONTRIBUTING.md",
    "openspec/config.yaml",
    "docs/ARCHITECTURE.md",
    "docs/PRODUCT-MANUAL.md",
    "README.md",
)
RETIRED_MARKERS = (
    "generate-problem-candidates",
    ".lessonkit/explain",
    "difficulty_basis",
    "v1 operation: explain only",
    "Diagnose operation",
    "does **not** install a `lesson-kit`",
)


class CurrentDocumentationTests(unittest.TestCase):
    def test_entry_documents_do_not_restore_retired_contracts(self):
        for relative in CURRENT_ENTRIES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for marker in RETIRED_MARKERS:
                with self.subTest(file=relative, marker=marker):
                    self.assertNotIn(marker, text)

    def test_current_difficulty_and_provenance_terms_are_present(self):
        glossary = (ROOT / "docs/GLOSSARY.md").read_text(encoding="utf-8")
        requirements = (ROOT / "docs/REQUIREMENTS.md").read_text(encoding="utf-8")
        for marker in (
            "客观题目难度 / Objective Problem Difficulty",
            "个人难度 / Learner Difficulty",
            "题目来源方式 / Origin Kind",
            "来源便捷组 / Source Group",
        ):
            self.assertIn(marker, glossary)
        for marker in (
            "cognitive-v1-equal-mean",
            "source_kind",
            "origin_kind",
            "lesson-kit difficulty",
        ):
            self.assertIn(marker, requirements)

    def test_active_reconciliation_declares_every_pending_live_removal(self):
        change = ROOT / "openspec/changes/pre-release-contract-reconciliation/specs"
        if change.is_dir():
            review = (change / "review-workbench/spec.md").read_text(encoding="utf-8")
            ui = (change / "workbench-ui/spec.md").read_text(encoding="utf-8")
            page = (change / "review-page/spec.md").read_text(encoding="utf-8")
            for title in (
                "Step-level stuck marking",
                "Answer text capture for open problems",
                "Unified Agent data CLI",
                "Readable content sequences",
                "Semantic graph attraction",
            ):
                self.assertIn(f"### Requirement: {title}", review)
            self.assertIn("### Requirement: AI column with priority context", ui)
            self.assertIn("## REMOVED Requirements", page)
            return

        self.assertFalse((ROOT / "openspec/specs/review-page").exists())
        # A retired capability must not survive as a live requirement. Prose is
        # not the test: the current specs legitimately say candidate promotion
        # SHALL NOT exist and reject it, so only requirement titles are checked.
        retired = ("candidate", "explain", "diagnose", "review page")
        for path in (ROOT / "openspec/specs").glob("*/spec.md"):
            titles = re.findall(
                r"^### Requirement: (.+)$", path.read_text(encoding="utf-8"), re.M
            )
            for title in titles:
                for word in retired:
                    with self.subTest(spec=path.parent.name, title=title):
                        self.assertNotIn(word, title.lower())


if __name__ == "__main__":
    unittest.main()
