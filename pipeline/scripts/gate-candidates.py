#!/usr/bin/env python3
"""Apply structural and semantic audit gates to Problem Candidates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
POOL_SCRIPT_DIR = SCRIPT_DIR.parents[1] / "pool" / "scripts"
for path in (SCRIPT_DIR, POOL_SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from candidate_contract import fetch_relation_ids, row_to_candidate, validate_candidate  # noqa: E402
from pool_schema import ensure_problem_candidate_schema  # noqa: E402


REQUIRED_AUDIT_CHECKS = (
    "source_grounding",
    "answer_correctness",
    "training_usefulness",
    "option_plausibility",
)


def parse_candidate_scope(candidate_id: str) -> tuple[str, str]:
    parts = candidate_id.split("-")
    if len(parts) < 4:
        return "", ""
    return parts[0], parts[1]


def audit_passes(audit: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(audit, dict):
        return False, ["audit entry must be an object"]
    checks = audit.get("checks")
    if not isinstance(checks, dict):
        errors.append("audit checks must be an object")
        checks = {}
    for check in REQUIRED_AUDIT_CHECKS:
        if checks.get(check) not in {"PASS", "FAIL"}:
            errors.append(f"audit check {check} must be PASS or FAIL")
    if audit.get("status") not in {"PASS", "FAIL"}:
        errors.append("audit status must be PASS or FAIL")
    if not isinstance(audit.get("summary"), str) or not audit["summary"].strip():
        errors.append("audit summary is required")
    passed = (
        not errors
        and audit.get("status") == "PASS"
        and all(checks.get(check) == "PASS" for check in REQUIRED_AUDIT_CHECKS)
    )
    return passed, errors


def gate_candidates(
    db_path: Path | str,
    audit_path: Path | str,
    candidate_ids: Optional[Sequence[str]] = None,
) -> tuple[int, int, list[str]]:
    db_path = Path(db_path)
    audit_path = Path(audit_path)
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")
    if not audit_path.is_file():
        raise FileNotFoundError(f"audit report not found: {audit_path}")
    report = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    audits = report.get("audits")
    if not isinstance(audits, list):
        return 0, 0, ["audit report requires audits[]"]
    requested = set(candidate_ids or [])

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_problem_candidate_schema(conn)
        kp_ids = {str(row[0]) for row in conn.execute("SELECT kp_id FROM knowledge_points")}
        relation_ids = fetch_relation_ids(conn)
        passed_count = 0
        failed_count = 0
        errors: list[str] = []
        seen: set[str] = set()
        for audit in audits:
            candidate_id = str(audit.get("candidate_id", "")) if isinstance(audit, dict) else ""
            if requested and candidate_id not in requested:
                continue
            if not candidate_id or candidate_id in seen:
                errors.append(f"{candidate_id or '<missing>'}: missing or duplicate audit candidate_id")
                continue
            seen.add(candidate_id)
            row = conn.execute(
                "SELECT * FROM candidate_problems WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
            if row is None:
                errors.append(f"{candidate_id}: candidate not found")
                continue
            if row["status"] == "imported":
                errors.append(f"{candidate_id}: imported candidate cannot be gated")
                continue

            course, chapter = parse_candidate_scope(candidate_id)
            structure_passed, _cleaned, structure_errors = validate_candidate(
                row_to_candidate(row), course, chapter, kp_ids, relation_ids
            )
            semantic_passed, audit_errors = audit_passes(audit)
            all_passed = structure_passed and semantic_passed
            gate_report = json.dumps(
                {
                    "structure": {
                        "status": "PASS" if structure_passed else "FAIL",
                        "errors": structure_errors,
                    },
                    "audit": audit,
                    "audit_format_errors": audit_errors,
                },
                ensure_ascii=False,
            )
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = ?, structure_gate_status = ?, audit_gate_status = ?,
                    gate_report = ?, updated_at = datetime('now')
                WHERE candidate_id = ?
                """,
                (
                    "gate_passed" if all_passed else "needs_revision",
                    "pass" if structure_passed else "fail",
                    "pass" if semantic_passed else "fail",
                    gate_report,
                    candidate_id,
                ),
            )
            if all_passed:
                passed_count += 1
            else:
                failed_count += 1

        missing_requested = requested - seen
        errors.extend(f"{item}: no audit entry supplied" for item in sorted(missing_requested))
        conn.commit()
        return passed_count, failed_count, errors
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate Problem Candidates.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--candidate", action="append")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        passed, failed, errors = gate_candidates(args.db, args.audit, args.candidate)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Candidate gates: passed={passed} failed={failed} errors={len(errors)}")
    return 2 if failed or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
