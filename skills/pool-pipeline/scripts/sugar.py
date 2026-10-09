"""Emit, parse and validate block markers ("sugar") for unstable source material.

Usage:
    python sugar.py emit   <questions.json> [--out out.md]
    python sugar.py parse  <file.md>        [--out out.json]
    python sugar.py check  <file.md>...
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import identity_hash  # noqa: E402

OPEN = re.compile(
    r"<!--\s*Q\s+id=(?P<id>\S+)\s+chapter=(?P<chapter>\S+)\s+mode=(?P<mode>\S+)"
    r"(?:\s+fp=(?P<fp>[0-9a-f]+))?\s*-->")
CLOSE = "<!-- /Q -->"
FIELD = re.compile(r"^(来源|来源题号|题干|答案证据|考点|标题):\s*(.*)$")
OPTION = re.compile(r"^([A-H])[.．、]\s*(.*)$")
MODES = {"yes_no", "single_choice", "multiple_choice", "exam"}


def parse(text: str) -> tuple[list[dict], list[str]]:
    """Return (questions, problems). Every block is parsed or reported."""
    questions, problems = [], []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = OPEN.match(lines[i].strip())
        if not match:
            if "<!--" in lines[i] and "Q " in lines[i]:
                problems.append(f"line {i + 1}: malformed opening comment")
            i += 1
            continue
        row = {
            "problem_id": match.group("id"), "chapter": match.group("chapter"),
            "mode": match.group("mode"), "fp": match.group("fp"), "options": [],
            "source": None, "source_number": None, "stem": None,
            "answer_evidence": None, "topic": None, "title": None,
        }
        i += 1
        in_options = False
        while i < len(lines) and lines[i].strip() != CLOSE:
            stripped = lines[i].strip()
            if stripped == "选项:":
                in_options = True
                i += 1
                continue
            option = OPTION.match(stripped)
            field = FIELD.match(stripped)
            if in_options and option:
                row["options"].append(option.group(2).strip())
            elif in_options and stripped and row["options"]:
                row["options"][-1] += " " + stripped
            elif stripped.startswith("续:"):
                row["stem"] = (row["stem"] or "") + "\n" + stripped[2:].strip()
            elif field:
                key, value = field.group(1), field.group(2).strip()
                target = {
                    "来源": "source", "来源题号": "source_number", "题干": "stem",
                    "答案证据": "answer_evidence", "考点": "topic", "标题": "title",
                }[key]
                row[target] = value
            i += 1
        if i >= len(lines):
            problems.append(f"{row['problem_id']}: missing {CLOSE}")
        questions.append(row)
        i += 1
    return questions, problems


def emit(rows: list[dict]) -> str:
    out = []
    for row in rows:
        stem = row.get("problem_text") or row.get("stem") or ""
        fp = row.get("fp") or row.get("fingerprint") or identity_hash(
            " ".join([stem] + (row.get("options") or [])))
        out.append(f"<!-- Q id={row['problem_id']} chapter={row.get('chapter', '')} "
                   f"mode={row.get('mode') or 'exam'} fp={fp} -->")
        for label, value in (
            ("来源", row.get("source") or row.get("source_evidence")),
            ("来源题号", row.get("source_number")),
            ("考点", row.get("topic")),
            ("标题", row.get("display_title")),
            ("题干", stem),
            ("答案证据", row.get("answer_evidence") or row.get("source_answer")),
        ):
            if value:
                out.append(f"{label}: {value.splitlines()[0]}")
        if row.get("options"):
            out.append("选项:")
            out.extend(f"{chr(65 + i)}. {option}" for i, option in enumerate(row["options"]))
        for extra in stem.splitlines()[1:]:
            out.append(f"续: {extra}")
        out.append(CLOSE)
        out.append("")
    return "\n".join(out)


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    questions, problems = parse(text)
    for question in questions:
        if question["mode"] not in MODES:
            problems.append(f"{question['problem_id']}: unknown mode {question['mode']!r}")
        if not question["stem"]:
            problems.append(f"{question['problem_id']}: no 题干 line")
        if not question["source"]:
            problems.append(f"{question['problem_id']}: no 来源 line (evidence must be pointable)")
        if question["mode"] in {"single_choice", "multiple_choice"} and not 2 <= len(question["options"]) <= 6:
            problems.append(f"{question['problem_id']}: {len(question['options'])} options for {question['mode']}")
        if question["fp"] is None:
            problems.append(f"{question['problem_id']}: no fp= (the ledger cannot skip re-runs)")
    print(f"{path.name}: {len(questions)} blocks, {len(problems)} problems")
    for problem in problems[:20]:
        print(f"  {problem}")
    return problems


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, path = sys.argv[1], Path(sys.argv[2])
    out_path = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    if cmd == "emit":
        text = emit(json.loads(path.read_text(encoding="utf-8")))
        destination = out_path or path.with_suffix(".md")
        destination.write_text(text, encoding="utf-8")
        print(f"wrote {destination.name}")
        return 0
    if cmd == "parse":
        questions, problems = parse(path.read_text(encoding="utf-8"))
        if out_path:
            out_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(questions)} blocks, {len(problems)} problems")
        for problem in problems[:20]:
            print(f"  {problem}")
        return 1 if problems else 0
    if cmd == "check":
        return 1 if check(path) else 0
    print(f"unknown subcommand {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
