#!/usr/bin/env python3
"""
Pipeline Step 9: Validate the pool SQLite database against 6 quality gates.

Runs schema-conformance, kp-completeness, question-linkage, id-uniqueness,
difficulty-range, kp-coverage. Outputs ERROR/WARNING report. --json for
machine-readable output.

Usage:
    python pipeline/scripts/validate-pool.py \
        --db pool/dld-ch02.db \
        --chapter ch02 \
        [--json]

Exit codes:
    0 — all gates PASS (no ERROR-level failures)
    1 — invocation error
    2 — at least one ERROR-level gate failure
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List


KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")

VALID_KNOWLEDGE_TYPES: List[str] = [
    "concept-property", "method-modeling", "formula-calculation",
    "algorithm-process", "code-implementation", "system-timing",
    "lab-implementation", "memory-recall",
]
VALID_IMPORTANCE: List[str] = ["core", "supplementary", "optional"]
VALID_MASTERY_KP: List[str] = ["new", "confused", "grasping", "stable", "faded"]
VALID_MASTERY_Q: List[str] = ["new", "confused", "misleaded", "familiar", "mastered"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate the lesson-kit pool against 6 quality gates.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter identifier (e.g. ch02). Filters KP rows whose kp_id starts with <course>-<chapter>-.",
    )
    parser.add_argument(
        "--course",
        default=None,
        help="Course prefix (e.g. dld). Defaults to chapter row scanning with --chapter only if not provided.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report.",
    )
    return parser.parse_args(argv)


def run_gates(conn: sqlite3.Connection, course: str, chapter: str) -> List[Dict[str, Any]]:
    """Run all 6 gates and return list of {gate, level, message} dicts."""
    findings: List[Dict[str, Any]] = []
    course = course or ""

    if course:
        prefix = f"{course}-{chapter}-"
        kp_filter_sql = "WHERE kp_id LIKE ?"
        kp_filter_arg = (prefix + "%",)
    else:
        kp_filter_sql = ""
        kp_filter_arg = ()

    kp_rows = conn.execute(
        f"SELECT kp_id, knowledge_item, knowledge_type, importance, "
        f"difficulty, fragile, related_kp_ids FROM knowledge_points {kp_filter_sql}",
        kp_filter_arg,
    ).fetchall() if kp_filter_sql else conn.execute(
        "SELECT kp_id, knowledge_item, knowledge_type, importance, "
        "difficulty, fragile, related_kp_ids FROM knowledge_points"
    ).fetchall()

    # Gate 1: schema-conformance
    for row in kp_rows:
        kp_id = row[0]
        if row[2] not in VALID_KNOWLEDGE_TYPES:
            findings.append({
                "gate": "schema-conformance",
                "level": "ERROR",
                "message": f"{kp_id}: knowledge_type '{row[2]}' not in {VALID_KNOWLEDGE_TYPES}",
            })
        if row[3] not in VALID_IMPORTANCE:
            findings.append({
                "gate": "schema-conformance",
                "level": "ERROR",
                "message": f"{kp_id}: importance '{row[3]}' not in {VALID_IMPORTANCE}",
            })

    # Gate 2: kp-completeness
    for row in kp_rows:
        kp_id, knowledge_item, _, importance, _, _, _ = row
        if not kp_id or not knowledge_item or not importance:
            findings.append({
                "gate": "kp-completeness",
                "level": "ERROR",
                "message": f"{kp_id}: missing required field (kp_id/knowledge_item/importance)",
            })

    # Gate 3: question-linkage
    if course:
        q_rows = conn.execute(
            "SELECT q_id, kp_id FROM questions WHERE kp_id LIKE ?",
            (prefix + "%",),
        ).fetchall()
    else:
        q_rows = conn.execute("SELECT q_id, kp_id FROM questions").fetchall()

    kp_ids_set = {row[0] for row in kp_rows}
    for q_id, kp_id in q_rows:
        if kp_id not in kp_ids_set:
            findings.append({
                "gate": "question-linkage",
                "level": "ERROR",
                "message": f"{q_id}: kp_id '{kp_id}' not found in knowledge_points",
            })

    # Gate 4: id-uniqueness
    seen: Dict[str, str] = {}
    for row in kp_rows:
        kp_id = row[0]
        if kp_id in seen:
            findings.append({
                "gate": "id-uniqueness",
                "level": "ERROR",
                "message": f"duplicate kp_id '{kp_id}'",
            })
        seen[kp_id] = "kp"

    q_seen: Dict[str, str] = {}
    for q_id, _ in q_rows:
        if q_id in q_seen:
            findings.append({
                "gate": "id-uniqueness",
                "level": "ERROR",
                "message": f"duplicate q_id '{q_id}'",
            })
        q_seen[q_id] = "q"

    # Gate 5: difficulty-range
    for row in kp_rows:
        kp_id = row[0]
        difficulty = row[4]
        if difficulty is not None and (difficulty < 1 or difficulty > 5):
            findings.append({
                "gate": "difficulty-range",
                "level": "ERROR",
                "message": f"{kp_id}: difficulty {difficulty} out of range 1-5",
            })
        fragile = row[5]
        if fragile is not None and fragile not in (0, 1):
            findings.append({
                "gate": "difficulty-range",
                "level": "ERROR",
                "message": f"{kp_id}: fragile {fragile} not 0 or 1",
            })

    # Gate 6: kp-coverage — WARNING only
    # Without source-scope.md we can't fully verify "every source_unit has at least one KP".
    # This gate emits a WARNING when no KP rows exist for the chapter (clear gap).
    if not kp_rows:
        findings.append({
            "gate": "kp-coverage",
            "level": "WARNING",
            "message": f"no knowledge_points rows for chapter {chapter}",
        })
    else:
        findings.append({
            "gate": "kp-coverage",
            "level": "WARNING",
            "message": (
                "cannot verify per-source-unit coverage without source-scope.md; "
                "manual review recommended"
            ),
        })

    return findings


def main(argv=None) -> int:
    args = parse_args(argv)

    if not os.path.isfile(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    try:
        findings = run_gates(conn, args.course or "", args.chapter)
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    error_count = sum(1 for f in findings if f["level"] == "ERROR")
    warn_count = sum(1 for f in findings if f["level"] == "WARNING")

    report = {
        "db": args.db,
        "chapter": args.chapter,
        "course": args.course,
        "summary": {
            "errors": error_count,
            "warnings": warn_count,
            "status": "FAIL" if error_count > 0 else "PASS",
        },
        "findings": findings,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== Pool validation report ===")
        print(f"DB:      {args.db}")
        print(f"Chapter: {args.chapter}")
        if args.course:
            print(f"Course:  {args.course}")
        print(f"\nResult: {report['summary']['status']}")
        print(f"  - ERROR:   {error_count}")
        print(f"  - WARNING: {warn_count}")

        if findings:
            print(f"\n=== Findings ===")
            for f in findings:
                marker = "❌" if f["level"] == "ERROR" else "⚠️"
                print(f"  {marker} [{f['gate']}] {f['message']}")

    return 2 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())