"""Check a patch manifest against the pool's data invariants before submitting it.

Usage:
    python preflight.py manifests/ch07.patch.json [--pool pool.json]

Exits non-zero and prints one line per violation. `--pool` (a JSON list of rows
dumped from the pool) lets the check fall back to the row's current values when
the manifest item does not carry a field it needs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LABEL_LIMITS = {"display_title": 40, "display_summary": 200}
QUIZ_TYPES = {"yes_no", "single_choice", "multiple_choice"}

_TAG = re.compile(r"</?(sup|sub)>")
_COMPLETE_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*/?>")
_UNTERMINATED_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*$")


def markup_errors(text: object) -> list[str]:
    """Faithful copy of the ingest markup boundary used by pool repair manifests."""
    if not isinstance(text, str):
        return ["is not text"]
    if "\ufffd" in text:
        return ["has suspicious formula damage (U+FFFD)"]
    errors: list[str] = []
    stack: list[str] = []
    index = 0
    while index < len(text):
        start = text.find("<", index)
        if start < 0:
            break
        match = _TAG.match(text, start)
        if match is None:
            tail = text[start:]
            if _COMPLETE_TAG.match(tail) or (
                (start == 0 or text[start - 1].isspace())
                and _UNTERMINATED_TAG.match(tail)
            ):
                errors.append("has unknown or unterminated HTML")
            index = start + 1
            continue
        tag = match.group(1)
        if text.startswith("</", start):
            if not stack or stack[-1] != tag:
                errors.append("has unbalanced sup/sub")
            else:
                stack.pop()
        else:
            stack.append(tag)
        index = match.end()
    return errors


def _maybe_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def check_item(item: dict, current: dict | None) -> list[str]:
    errs: list[str] = []

    def field(name):
        value = item[name] if name in item else (current or {}).get(name)
        return _maybe_json(value)

    text = field("problem_text")
    if not isinstance(text, str) or not text.strip():
        errs.append("problem_text is required")
    else:
        errs += markup_errors(text)

    for label, limit in LABEL_LIMITS.items():
        value = item.get(label)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errs.append(f"{label} must be a non-empty string of at most {limit} chars")

    payload = field("micro_quiz")
    if payload is None:
        return errs
    if not isinstance(payload, dict):
        return errs + ["micro_quiz must be an object or null"]

    quiz = payload.get("quiz_type")
    if quiz is None and not payload:
        return errs
    if quiz not in QUIZ_TYPES:
        return errs + [f"unknown quiz_type {quiz!r}"]
    if not isinstance(payload.get("source_evidence"), str) or not payload["source_evidence"].strip():
        errs.append("micro_quiz.source_evidence is required")

    key = payload.get("answer_key")
    options = payload.get("options")
    if quiz == "yes_no":
        if options not in (None, ["是", "否"]):
            errs.append(f"yes_no options must be omitted or the 是/否 pair, got {options!r}")
        if key is not None and key not in ("是", "否"):
            errs.append(f"yes_no answer_key must be 是 or 否, got {key!r}")
    else:
        if not isinstance(options, list) or not 2 <= len(options) <= 6:
            errs.append(f"choice options must be a list of 2–6 items, got {options!r}")
        else:
            if len(set(options)) != len(options):
                errs.append("options must be unique")
            if not all(isinstance(option, str) and option.strip() for option in options):
                errs.append("options must be non-empty strings")
            if key is not None:
                if quiz == "single_choice" and key not in options:
                    errs.append(f"single_choice key {key!r} must be one of the options verbatim")
                if quiz == "multiple_choice" and (
                    not isinstance(key, list) or not key or not set(key) <= set(options)
                ):
                    errs.append(f"multiple_choice key {key!r} must be a non-empty subset of options")
    if key is not None and not payload.get("error_reason"):
        errs.append("error_reason is required whenever an answer key is present")

    kp_ids = field("kp_ids")
    if isinstance(kp_ids, list) and len(kp_ids) != 1:
        errs.append(f"a micro quiz maps to exactly one knowledge point, got {len(kp_ids)}")
    return errs


def main() -> int:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    manifest_path = Path(args[0])
    pool_rows: dict[str, dict] = {}
    if "--pool" in sys.argv:
        pool_file = Path(sys.argv[sys.argv.index("--pool") + 1])
        pool_rows = {row["problem_id"]: row for row in json.loads(pool_file.read_text(encoding="utf-8"))}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest.get("items", manifest.get("problems", []))
    bad = 0
    for item in items:
        current = pool_rows.get(item.get("problem_id"))
        errs = check_item(item, current)
        if errs:
            bad += 1
            for error in errs:
                print(f"{item.get('problem_id')}: {error}")
        elif current is not None and all(
            item.get(key) == current.get(key) for key in item if key != "problem_id"
        ):
            print(f"{item.get('problem_id')}: nothing to change")
    print(f"checked {len(items)} items, {bad} with problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
