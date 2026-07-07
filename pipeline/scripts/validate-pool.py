#!/usr/bin/env python3
"""
Pipeline: Validate the lesson-kit SQLite pool against quality gates.

Validates KP schema/completeness, legacy companion-question linkage,
coverage-check output, and the unified problems table. Problem solution text
is optional; final answers and explanations both live in solution when known.

Usage:
    python pipeline/scripts/validate-pool.py \
        --db pool/dld.db \
        --chapter ch02 \
        [--course dld] \
        [--json]

Exit codes:
    0 - all gates PASS (no ERROR-level failures)
    1 - invocation or SQLite error
    2 - at least one ERROR-level gate failure
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Set


KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")
PROBLEM_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-prob-\d{3}$")

VALID_KNOWLEDGE_TYPES: Set[str] = {
    "concept-property",
    "method-modeling",
    "formula-calculation",
    "algorithm-process",
    "code-implementation",
    "system-timing",
    "lab-implementation",
    "memory-recall",
}
VALID_IMPORTANCE: Set[str] = {"core", "supplementary", "optional"}
VALID_PROBLEM_TYPES: Set[str] = {
    "calculation",
    "proof",
    "modeling",
    "explanation",
    "experiment",
    "design",
    "application",
    "counterexample",
    "other",
}
VALID_SOURCE_KINDS: Set[str] = {
    "textbook",
    "quiz",
    "midterm",
    "final",
    "makeup",
    "other",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate the lesson-kit pool against quality gates.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter identifier, e.g. ch02. With --course, validates rows with <course>-<chapter>- prefix.",
    )
    parser.add_argument(
        "--course",
        default=None,
        help="Course prefix, e.g. dld. Recommended for chapter-scoped validation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report.",
    )
    return parser.parse_args(argv)


def finding(gate: str, level: str, message: str) -> Dict[str, Any]:
    return {"gate": gate, "level": level, "message": message}


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def get_prefix(course: str, chapter: str) -> str:
    return f"{course}-{chapter}-" if course else ""


def get_coverage_check_path(course: str, chapter: str) -> str:
    if not course:
        course = "unknown"
    return os.path.join(
        "intermediate",
        course,
        "extraction",
        chapter,
        "02_analysis",
        "coverage-check.md",
    )


def parse_coverage_check(markdown: str) -> List[str]:
    """Parse a coverage-check.md table. Return MISSING/FAIL categories."""
    missing: List[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        if "count" in stripped.lower() or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
        if len(cells) < 4:
            continue
        status = cells[3].upper()
        if "MISSING" in status or "FAIL" in status:
            missing.append(cells[0])
    return missing


def query_rows(
    conn: sqlite3.Connection,
    sql_all: str,
    sql_filtered: str,
    prefix: str,
) -> List[sqlite3.Row]:
    if prefix:
        return conn.execute(sql_filtered, (prefix + "%",)).fetchall()
    return conn.execute(sql_all).fetchall()


def run_schema_gate(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    required_tables = [
        "knowledge_points",
        "questions",
        "kp_progress",
        "question_progress",
        "problems",
    ]
    for table in required_tables:
        if not table_exists(conn, table):
            findings.append(
                finding("schema-conformance", "ERROR", f"missing required table '{table}'")
            )
    return findings


def run_kp_gates(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    prefix: str,
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    kp_rows = query_rows(
        conn,
        "SELECT kp_id, knowledge_item, knowledge_type, importance, difficulty, fragile, related_kp_ids "
        "FROM knowledge_points",
        "SELECT kp_id, knowledge_item, knowledge_type, importance, difficulty, fragile, related_kp_ids "
        "FROM knowledge_points WHERE kp_id LIKE ?",
        prefix,
    )

    if not kp_rows:
        findings.append(
            finding("kp-coverage", "ERROR", f"no knowledge_points rows for chapter {chapter}")
        )
        return findings

    seen: Set[str] = set()
    for row in kp_rows:
        kp_id, knowledge_item, knowledge_type, importance, difficulty, fragile, related_raw = row

        if kp_id in seen:
            findings.append(finding("id-uniqueness", "ERROR", f"duplicate kp_id '{kp_id}'"))
        seen.add(kp_id)

        if not kp_id or not KP_ID_PATTERN.match(kp_id):
            findings.append(finding("schema-conformance", "ERROR", f"{kp_id}: invalid kp_id"))
        if not knowledge_item or not importance:
            findings.append(
                finding(
                    "kp-completeness",
                    "ERROR",
                    f"{kp_id}: missing required field (kp_id/knowledge_item/importance)",
                )
            )
        if knowledge_type not in VALID_KNOWLEDGE_TYPES:
            findings.append(
                finding(
                    "schema-conformance",
                    "ERROR",
                    f"{kp_id}: knowledge_type '{knowledge_type}' not in {sorted(VALID_KNOWLEDGE_TYPES)}",
                )
            )
        if importance not in VALID_IMPORTANCE:
            findings.append(
                finding(
                    "schema-conformance",
                    "ERROR",
                    f"{kp_id}: importance '{importance}' not in {sorted(VALID_IMPORTANCE)}",
                )
            )
        if difficulty is not None and (difficulty < 1 or difficulty > 5):
            findings.append(
                finding("difficulty-range", "ERROR", f"{kp_id}: difficulty {difficulty} out of range 1-5")
            )
        if fragile is not None and not isinstance(fragile, str):
            findings.append(
                finding(
                    "schema-conformance",
                    "ERROR",
                    f"{kp_id}: fragile must be null or string, got {type(fragile).__name__}",
                )
            )
        if related_raw:
            try:
                related = json.loads(related_raw)
                if not isinstance(related, list):
                    findings.append(
                        finding("schema-conformance", "ERROR", f"{kp_id}: related_kp_ids is not a JSON array")
                    )
            except json.JSONDecodeError:
                findings.append(
                    finding("schema-conformance", "ERROR", f"{kp_id}: related_kp_ids is not valid JSON")
                )

    coverage_path = get_coverage_check_path(course, chapter)
    if os.path.isfile(coverage_path):
        try:
            with open(coverage_path, "r", encoding="utf-8") as handle:
                failures = parse_coverage_check(handle.read())
            for category in failures:
                findings.append(
                    finding(
                        "kp-coverage",
                        "ERROR",
                        f"coverage-check.md: missing coverage in '{category}' category",
                    )
                )
        except OSError as exc:
            findings.append(
                finding("kp-coverage", "WARNING", f"cannot read coverage-check.md: {exc}")
            )
    else:
        findings.append(
            finding(
                "kp-coverage",
                "WARNING",
                "no coverage-check.md found; cannot verify extraction coverage gate output",
            )
        )

    return findings


def run_legacy_question_gate(
    conn: sqlite3.Connection,
    prefix: str,
    chapter_kp_ids: Set[str],
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    q_rows = query_rows(
        conn,
        "SELECT q_id, kp_id FROM questions",
        "SELECT q_id, kp_id FROM questions WHERE kp_id LIKE ?",
        prefix,
    )
    seen: Set[str] = set()
    for q_id, kp_id in q_rows:
        if q_id in seen:
            findings.append(finding("id-uniqueness", "ERROR", f"duplicate q_id '{q_id}'"))
        seen.add(q_id)
        if kp_id not in chapter_kp_ids:
            findings.append(
                finding(
                    "question-linkage",
                    "ERROR",
                    f"{q_id}: kp_id '{kp_id}' not found in scoped knowledge_points",
                )
            )
    return findings


def run_problem_gates(
    conn: sqlite3.Connection,
    prefix: str,
    all_kp_ids: Set[str],
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    problem_rows = query_rows(
        conn,
        "SELECT problem_id, kp_ids, problem_text, solution, problem_type, source_kind FROM problems",
        "SELECT problem_id, kp_ids, problem_text, solution, problem_type, source_kind "
        "FROM problems WHERE problem_id LIKE ?",
        prefix,
    )

    seen: Set[str] = set()
    for row in problem_rows:
        problem_id, kp_ids_raw, problem_text, solution, problem_type, source_kind = row

        if problem_id in seen:
            findings.append(finding("id-uniqueness", "ERROR", f"duplicate problem_id '{problem_id}'"))
        seen.add(problem_id)

        if not problem_id or not PROBLEM_ID_PATTERN.match(problem_id):
            findings.append(
                finding("problem-completeness", "ERROR", f"{problem_id}: invalid problem_id")
            )
        if not problem_text or not str(problem_text).strip():
            findings.append(
                finding("problem-completeness", "ERROR", f"{problem_id}: missing problem_text")
            )
        if solution is not None and not isinstance(solution, str):
            findings.append(
                finding("problem-completeness", "ERROR", f"{problem_id}: solution must be text or null")
            )
        if problem_type not in VALID_PROBLEM_TYPES:
            findings.append(
                finding(
                    "problem-completeness",
                    "ERROR",
                    f"{problem_id}: problem_type '{problem_type}' not in {sorted(VALID_PROBLEM_TYPES)}",
                )
            )
        if source_kind not in VALID_SOURCE_KINDS:
            findings.append(
                finding(
                    "problem-completeness",
                    "ERROR",
                    f"{problem_id}: source_kind '{source_kind}' not in {sorted(VALID_SOURCE_KINDS)}",
                )
            )

        try:
            kp_ids = json.loads(kp_ids_raw) if kp_ids_raw else []
        except json.JSONDecodeError:
            findings.append(
                finding("problem-linkage", "ERROR", f"{problem_id}: kp_ids is not valid JSON")
            )
            continue

        if not isinstance(kp_ids, list) or not kp_ids:
            findings.append(
                finding("problem-linkage", "ERROR", f"{problem_id}: kp_ids must be a non-empty JSON array")
            )
            continue

        for kp_id in kp_ids:
            if not isinstance(kp_id, str) or not KP_ID_PATTERN.match(kp_id):
                findings.append(
                    finding("problem-linkage", "ERROR", f"{problem_id}: invalid kp_id '{kp_id}'")
                )
            elif kp_id not in all_kp_ids:
                findings.append(
                    finding("problem-linkage", "ERROR", f"{problem_id}: kp_id '{kp_id}' not found")
                )

    return findings


def run_gates(conn: sqlite3.Connection, course: str, chapter: str) -> List[Dict[str, Any]]:
    findings = run_schema_gate(conn)
    if any(f["level"] == "ERROR" and f["gate"] == "schema-conformance" for f in findings):
        return findings

    course = course or ""
    prefix = get_prefix(course, chapter)

    kp_findings = run_kp_gates(conn, course, chapter, prefix)
    findings.extend(kp_findings)

    all_kp_ids = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points").fetchall()}
    chapter_kp_ids = {
        row[0]
        for row in query_rows(
            conn,
            "SELECT kp_id FROM knowledge_points",
            "SELECT kp_id FROM knowledge_points WHERE kp_id LIKE ?",
            prefix,
        )
    }

    if chapter_kp_ids:
        findings.extend(run_legacy_question_gate(conn, prefix, chapter_kp_ids))
        findings.extend(run_problem_gates(conn, prefix, all_kp_ids))

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

    error_count = sum(1 for item in findings if item["level"] == "ERROR")
    warn_count = sum(1 for item in findings if item["level"] == "WARNING")

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
        print("\n=== Pool validation report ===")
        print(f"DB:      {args.db}")
        print(f"Chapter: {args.chapter}")
        if args.course:
            print(f"Course:  {args.course}")
        print(f"\nResult: {report['summary']['status']}")
        print(f"  - ERROR:   {error_count}")
        print(f"  - WARNING: {warn_count}")

        if findings:
            print("\n=== Findings ===")
            for item in findings:
                marker = "ERROR" if item["level"] == "ERROR" else "WARNING"
                print(f"  {marker} [{item['gate']}] {item['message']}")

    return 2 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
