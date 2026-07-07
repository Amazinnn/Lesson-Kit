#!/usr/bin/env python3
"""Lightweight Lesson-Kit runtime state and guard CLI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


STATE_PATH = Path(".lessonkit") / "state.yaml"

STATE_FIELDS = [
    "schema_version",
    "active_course",
    "active_chapter",
    "active_command",
    "phase",
    "required_artifacts",
    "last_gate_name",
    "last_gate_status",
    "last_gate_report",
    "last_gate_checked_at",
    "blocked_reason",
    "next_action",
    "updated_at",
]

PHASES = {"idle", "active", "blocked", "complete"}
POOL_GUARD_COMMANDS = {"extract-chapter", "extract-problems"}


@dataclass(frozen=True)
class CommandContract:
    base: str
    required: tuple[str, ...]
    checks: tuple[str, ...]
    outputs: tuple[str, ...] = ()


CONTRACTS = {
    "extract-chapter": CommandContract(
        base="intermediate/{course}/extraction/{chapter}",
        required=(
            "01_inputs/source-scope.md",
            "02_analysis/knowledge-points.md",
            "02_analysis/knowledge-relationship-analysis.md",
            "02_analysis/kp-consolidation-analysis.md",
            "02_analysis/coverage-check.md",
            "02_analysis/pool-insert-manifest.json",
            "04_checks/pool-validation-report.md",
        ),
        checks=(
            "02_analysis/coverage-check.md",
            "04_checks/pool-validation-report.md",
        ),
    ),
    "extract-problems": CommandContract(
        base="intermediate/{course}/problem_extraction/{chapter}",
        required=(
            "01_inputs/kp-query-result.json",
            "01_inputs/full-problem-bank.md",
            "02_analysis/problem-insert-manifest.json",
            "04_checks/problem-pool-validation-report.md",
        ),
        checks=("04_checks/problem-pool-validation-report.md",),
    ),
    "problem-set": CommandContract(
        base="intermediate/{course}-{chapter}/problem-set",
        required=(
            "01_inputs/view-scope.md",
            "02_analysis/problem-query-result.json",
            "03_plans/selection-plan.md",
            "04_checks/problem-set-check.md",
            "04_checks/solution-sync-check.md",
        ),
        checks=(
            "04_checks/problem-set-check.md",
            "04_checks/solution-sync-check.md",
        ),
        outputs=(
            "output/{course}/{chapter}/{chapter}-problem-set.md",
            "output/{course}/{chapter}/{chapter}-solutions.md",
        ),
    ),
}

BLOCKING_MARKERS = (
    re.compile(r"\b(?:Result|Status)\s*:\s*(?:FAIL|ERROR)\b", re.IGNORECASE),
    re.compile(r"\|\s*(?:FAIL|ERROR)\s*\|", re.IGNORECASE),
    re.compile(r"\bERROR\s*:\s*[1-9]\d*\b", re.IGNORECASE),
    re.compile(r"^\s*FAIL\b", re.IGNORECASE | re.MULTILINE),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "FILE_CONTRACT.md").exists():
            return candidate
        if (candidate / ".git").exists() and (candidate / "README.md").exists():
            return candidate
    return current


def state_file(root: Path) -> Path:
    return root / STATE_PATH


def default_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "active_course": "",
        "active_chapter": "",
        "active_command": "",
        "phase": "idle",
        "required_artifacts": [],
        "last_gate_name": "",
        "last_gate_status": "",
        "last_gate_report": "",
        "last_gate_checked_at": "",
        "blocked_reason": "",
        "next_action": "",
        "updated_at": utc_now(),
    }


def parse_scalar(raw: str) -> object:
    raw = raw.strip()
    if raw == "":
        return ""
    if raw in {"[]", "null"}:
        return [] if raw == "[]" else ""
    if raw.startswith('"') and raw.endswith('"'):
        return json.loads(raw)
    if raw.isdigit():
        return int(raw)
    return raw


def read_state(root: Path) -> dict[str, object]:
    path = state_file(root)
    if not path.exists():
        raise FileNotFoundError(path)

    state = default_state()
    current_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise ValueError(f"List item without key in {path}: {line}")
            value = parse_scalar(line[4:])
            state.setdefault(current_list_key, [])
            if not isinstance(state[current_list_key], list):
                raise ValueError(f"Field is not a list in {path}: {current_list_key}")
            state[current_list_key].append(value)
            continue
        if ":" not in line:
            raise ValueError(f"Invalid state line in {path}: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if value.strip() == "":
            state[key] = []
            current_list_key = key
        else:
            state[key] = parse_scalar(value)
            current_list_key = None
    return state


def yaml_scalar(value: object) -> str:
    if value is None:
        return '""'
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def write_state(root: Path, state: dict[str, object]) -> None:
    path = state_file(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = default_state()
    merged.update(state)
    merged["updated_at"] = utc_now()

    lines: list[str] = []
    for field in STATE_FIELDS:
        value = merged.get(field, "")
        if isinstance(value, list):
            lines.append(f"{field}:")
            for item in value:
                lines.append(f"  - {yaml_scalar(item)}")
        else:
            lines.append(f"{field}: {yaml_scalar(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_paths(command: str, course: str, chapter: str) -> tuple[list[str], list[str]]:
    contract = CONTRACTS[command]
    base = contract.base.format(course=course, chapter=chapter)
    required = [f"{base}/{item}" for item in contract.required]
    outputs = [
        item.format(course=course, chapter=chapter)
        for item in contract.outputs
    ]
    return required, outputs


def check_paths(command: str, course: str, chapter: str) -> list[str]:
    contract = CONTRACTS[command]
    base = contract.base.format(course=course, chapter=chapter)
    return [f"{base}/{item}" for item in contract.checks]


def next_action_for(command: str, course: str, chapter: str) -> str:
    if command == "extract-chapter":
        return f"Run extract-problems for {course} {chapter}."
    if command == "extract-problems":
        return f"Render and guard a problem-set view for {course} {chapter}."
    if command == "problem-set":
        return f"Review the rendered output for {course} {chapter}, then commit if accepted."
    return "Choose the next Lesson-Kit command."


def find_blocking_marker(text: str) -> str | None:
    for pattern in BLOCKING_MARKERS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return None


def evaluate_guard(
    root: Path,
    command: str,
    course: str,
    chapter: str,
    db_path: str | None = None,
) -> tuple[bool, list[str], list[str], list[str]]:
    required, outputs = render_paths(command, course, chapter)
    expected = required + outputs
    missing = [path for path in expected if not (root / path).exists()]

    failures: list[str] = []
    notes: list[str] = []
    for relative in check_paths(command, course, chapter):
        path = root / relative
        if not path.exists():
            continue
        marker = find_blocking_marker(path.read_text(encoding="utf-8"))
        if marker:
            failures.append(f"{relative}: {marker}")

    if db_path:
        pool_failure = run_pool_validation(root, db_path, course, chapter)
        if pool_failure:
            failures.append(pool_failure)
        else:
            notes.append(f"Pool validation passed: {db_path}")

    return not missing and not failures, missing, failures, notes


def resolve_path(root: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def run_pool_validation(root: Path, db_path: str, course: str, chapter: str) -> str | None:
    db = resolve_path(root, db_path)
    if not db.exists():
        return f"pool validation: DB not found: {db_path}"

    script = root / "pipeline" / "scripts" / "validate-pool.py"
    if not script.exists():
        return "pool validation: missing pipeline/scripts/validate-pool.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--db",
            str(db),
            "--course",
            course,
            "--chapter",
            chapter,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode == 0:
        return None

    detail = best_failure_line(result.stdout, result.stderr)
    if detail:
        return f"pool validation failed (exit {result.returncode}): {detail}"
    return f"pool validation failed (exit {result.returncode})"


def best_failure_line(stdout: str, stderr: str) -> str:
    combined = stdout.splitlines() + stderr.splitlines()
    for line in combined:
        stripped = line.strip()
        if (
            stripped.startswith("Result:")
            or stripped.startswith("SQLite error:")
            or stripped.startswith("ERROR:")
            or " ERROR " in f" {stripped} "
        ):
            return stripped
    for line in combined:
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def guard_report(
    command: str,
    course: str,
    chapter: str,
    passed: bool,
    missing: Iterable[str],
    failures: Iterable[str],
    notes: Iterable[str],
) -> str:
    lines = [
        f"Gate: {command}",
        f"Course: {course}",
        f"Chapter: {chapter}",
        f"Result: {'PASS' if passed else 'FAIL'}",
    ]

    missing = list(missing)
    failures = list(failures)
    if missing:
        lines.append("")
        lines.append("Missing artifacts:")
        lines.extend(f"- {item}" for item in missing)
    if failures:
        lines.append("")
        lines.append("Blocking issues:")
        lines.extend(f"- {item}" for item in failures)
    notes = list(notes)
    if notes:
        lines.append("")
        lines.append("Additional checks:")
        lines.extend(f"- {item}" for item in notes)
    if passed:
        lines.append("")
        lines.append("All required artifacts exist and check files contain no blocking markers.")
    return "\n".join(lines)


def status_text(state: dict[str, object]) -> str:
    required = state.get("required_artifacts", [])
    required_count = len(required) if isinstance(required, list) else 0
    lines = [
        "Lesson-Kit Runtime State",
        f"course: {state.get('active_course', '')}",
        f"chapter: {state.get('active_chapter', '')}",
        f"command: {state.get('active_command', '')}",
        f"phase: {state.get('phase', '')}",
        f"required_artifacts: {required_count}",
        f"last_gate: {state.get('last_gate_name', '')} {state.get('last_gate_status', '')}".rstrip(),
        f"last_gate_report: {state.get('last_gate_report', '')}",
        f"blocked_reason: {state.get('blocked_reason', '')}",
        f"next_action: {state.get('next_action', '')}",
        f"updated_at: {state.get('updated_at', '')}",
    ]
    return "\n".join(lines)


def load_state_or_default(root: Path) -> dict[str, object]:
    try:
        return read_state(root)
    except FileNotFoundError:
        return default_state()


def command_init(args: argparse.Namespace, root: Path) -> int:
    required, outputs = render_paths(args.command, args.course, args.chapter)
    state = default_state()
    state.update(
        {
            "active_course": args.course,
            "active_chapter": args.chapter,
            "active_command": args.command,
            "phase": "active",
            "required_artifacts": required + outputs,
            "next_action": f"Run lessonkit.py guard {args.command} --course {args.course} --chapter {args.chapter}.",
        }
    )
    write_state(root, state)
    print(f"Initialized {STATE_PATH} for {args.command} {args.course} {args.chapter}.")
    return 0


def command_status(args: argparse.Namespace, root: Path) -> int:
    try:
        state = read_state(root)
    except FileNotFoundError:
        print(f"No runtime state found at {STATE_PATH}. Run lessonkit.py init first.")
        return 1
    print(status_text(state))
    return 0


def command_set(args: argparse.Namespace, root: Path) -> int:
    state = load_state_or_default(root)
    if args.phase is not None:
        if args.phase not in PHASES:
            print(f"Invalid phase: {args.phase}. Expected one of: {', '.join(sorted(PHASES))}.")
            return 1
        state["phase"] = args.phase
    if args.next_action is not None:
        state["next_action"] = args.next_action
    if args.blocked_reason is not None:
        state["blocked_reason"] = args.blocked_reason
    write_state(root, state)
    print(f"Updated {STATE_PATH}.")
    return 0


def command_guard(args: argparse.Namespace, root: Path) -> int:
    state = load_state_or_default(root)
    course = args.course or str(state.get("active_course") or "")
    chapter = args.chapter or str(state.get("active_chapter") or "")
    if not course or not chapter:
        print("Guard requires --course and --chapter, or an initialized runtime state.")
        return 1
    if args.db and args.command not in POOL_GUARD_COMMANDS:
        print("--db is only supported for extract-chapter and extract-problems guards.")
        return 1

    passed, missing, failures, notes = evaluate_guard(root, args.command, course, chapter, args.db)
    print(guard_report(args.command, course, chapter, passed, missing, failures, notes))

    if args.apply:
        required, outputs = render_paths(args.command, course, chapter)
        report_paths = check_paths(args.command, course, chapter)
        if args.db:
            report_paths = report_paths + [f"validate-pool.py --db {args.db}"]
        state.update(
            {
                "active_course": course,
                "active_chapter": chapter,
                "active_command": args.command,
                "required_artifacts": required + outputs,
                "last_gate_name": args.command,
                "last_gate_status": "PASS" if passed else "FAIL",
                "last_gate_report": "; ".join(report_paths),
                "last_gate_checked_at": utc_now(),
            }
        )
        if passed:
            state["phase"] = "complete"
            state["blocked_reason"] = ""
            state["next_action"] = next_action_for(args.command, course, chapter)
        else:
            state["phase"] = "blocked"
            first_issue = (missing + failures)[0] if (missing or failures) else "unknown guard failure"
            state["blocked_reason"] = first_issue
            state["next_action"] = f"Repair {first_issue}, then rerun guard {args.command}."
        write_state(root, state)

    return 0 if passed else 2


def command_resume(args: argparse.Namespace, root: Path) -> int:
    try:
        state = read_state(root)
    except FileNotFoundError:
        print(f"No runtime state found at {STATE_PATH}. Run lessonkit.py init first.")
        return 1

    phase = str(state.get("phase") or "")
    print(status_text(state))
    print("")
    if phase == "blocked":
        print(f"Resume action: {state.get('next_action', '')}")
    elif phase == "complete":
        print(f"Resume action: {state.get('next_action', '')}")
    elif phase == "active":
        command = state.get("active_command", "")
        course = state.get("active_course", "")
        chapter = state.get("active_chapter", "")
        print(f"Resume action: run lessonkit.py guard {command} --course {course} --chapter {chapter}.")
    else:
        print("Resume action: initialize or select the next Lesson-Kit command.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lesson-Kit runtime state and guard CLI.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize runtime state.")
    init_parser.add_argument("--course", required=True)
    init_parser.add_argument("--chapter", required=True)
    init_parser.add_argument("--command", required=True, choices=sorted(CONTRACTS))
    init_parser.set_defaults(func=command_init)

    status_parser = subparsers.add_parser("status", help="Show runtime state.")
    status_parser.set_defaults(func=command_status)

    set_parser = subparsers.add_parser("set", help="Update selected runtime fields.")
    set_parser.add_argument("--phase", choices=sorted(PHASES))
    set_parser.add_argument("--next-action")
    set_parser.add_argument("--blocked-reason")
    set_parser.set_defaults(func=command_set)

    guard_parser = subparsers.add_parser("guard", help="Validate command artifacts.")
    guard_parser.add_argument("command", choices=sorted(CONTRACTS))
    guard_parser.add_argument("--course")
    guard_parser.add_argument("--chapter")
    guard_parser.add_argument(
        "--db",
        help="Optional SQLite pool path for extract-chapter/extract-problems guards.",
    )
    guard_parser.add_argument("--apply", action="store_true")
    guard_parser.set_defaults(func=command_guard)

    resume_parser = subparsers.add_parser("resume", help="Show the recovery action.")
    resume_parser.set_defaults(func=command_resume)

    return parser


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = root.resolve() if root is not None else find_repo_root()
    return args.func(args, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
