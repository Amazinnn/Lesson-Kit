"""Terminology gate: 「自评」 is retired to 「评价」 in live surfaces.

Allowed residues: the GLOSSARY old-name alias / _Avoid_ guard lines and dated
historical entries in ACTION-GRAPH. Anything else in live docs, live specs, or
the Agent prompt/contract surface is a rename regression.
"""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

LIVE_DOCS = [
    "docs/GLOSSARY.md",
    "docs/PRODUCT-MANUAL.md",
    "docs/REQUIREMENTS.md",
    "docs/DATA_MODEL.md",
    "docs/ARCHITECTURE.md",
    "docs/ACTION-GRAPH.md",
    *(str(p.relative_to(REPO)) for p in (REPO / "docs/action-graph").glob("*.md")),
]
LIVE_SPECS = [str(p.relative_to(REPO)) for p in (REPO / "openspec/specs").glob("**/spec.md")]


def _alias_line(line: str) -> bool:
    return ("旧称「自评」" in line
            or line.lstrip().startswith("_Avoid_")
            or "不要写成「自评」" in line)


def _historical_line(line: str) -> bool:
    return line.lstrip().startswith("- 20")


class TerminologyGateTests(unittest.TestCase):
    def test_live_docs_keep_only_alias_and_historical_hits(self):
        offenders = []
        for rel in LIVE_DOCS:
            path = REPO / rel
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "自评" in line and not _alias_line(line) and not _historical_line(line):
                    offenders.append(f"{rel}:{number}: {line.strip()[:100]}")
        self.assertEqual(offenders, [],
                         "「自评」 remains outside the alias/historical allowance:\n"
                         + "\n".join(offenders))

    def test_live_specs_carry_no_ziping(self):
        offenders = []
        for rel in LIVE_SPECS:
            path = REPO / rel
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "自评" in line:
                    offenders.append(f"{rel}:{number}: {line.strip()[:100]}")
        self.assertEqual(offenders, [],
                         "live specs must use 「评价」:\n" + "\n".join(offenders))

    def test_agent_contract_and_prompt_say_pingjia(self):
        from workbench.bridge import agent_contracts, conversations

        for topic in ("attempts", "grading", "commands"):
            text = agent_contracts.get(topic)
            self.assertNotIn("自评", text, f"contract topic {topic} still says 自评")
        prompt = conversations._prompt("这道题为什么错？", {
            "workspace": {"name": "dmath", "course": "dmath", "chapter": "ch06"},
        })
        self.assertNotIn("自评", prompt)
        self.assertIn("评价", prompt)


if __name__ == "__main__":
    unittest.main()
