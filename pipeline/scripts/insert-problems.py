#!/usr/bin/env python3
"""
Pipeline: Insert problems into the lesson-kit SQLite pool.

Reads problem-insert-manifest.json, validates each problem, and inserts rows
into the unified problems table. Source-specific problem pools are represented
by source_kind, not by separate physical tables.

Usage:
    python pipeline/scripts/insert-problems.py \
        --db pool/dmath.db \
        --manifest intermediate/dmath/problem_extraction/ch06/02_analysis/problem-insert-manifest.json \
        [--upsert] [--strict]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Set, Tuple


PROBLEM_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-prob-\d{3}$")
KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")

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

COLLAPSED_SUBPART_PATTERN = re.compile(r"[^\n][ \t]+[a-j]\s*\)[ \t]+")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Insert problems into the lesson-kit pool DB.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to problem-insert-manifest.json.",
    )
    parser.add_argument(
        "--upsert",
        action="store_true",
        help="Use INSERT OR REPLACE (overwrites existing rows).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any validation errors are found.",
    )
    return parser.parse_args(argv)


def expected_chapter_from_metadata(chapter: str) -> str:
    if chapter.startswith("ch"):
        return chapter
    return f"ch{chapter}"


def validate_text_block_format(
    owner_id: str,
    field_name: str,
    value: Any,
    errors: List[str],
) -> bool:
    """
    Catch the most common extraction-stage formatting failure: subparts
    flattened into one line instead of preserved as Markdown paragraphs.
    """
    if value is None or not isinstance(value, str):
        return True
    if COLLAPSED_SUBPART_PATTERN.search(value):
        errors.append(
            f"{owner_id}: {field_name} has collapsed subparts; put each "
            "subpart at the start of its own paragraph separated by blank lines"
        )
        return False
    return True


def validate_problem(
    problem: Dict[str, Any],
    chapter: str,
    existing_kp_ids: Set[str],
    errors: List[str],
) -> Tuple[bool, Dict[str, Any]]:
    """Validate one problem. Returns (is_valid, cleaned_row)."""
    ok = True
    problem_id = problem.get("problem_id")

    if not problem_id:
        errors.append("problem missing required field 'problem_id'")
        return False, {}

    if not PROBLEM_ID_PATTERN.match(problem_id):
        errors.append(
            f"{problem_id}: problem_id must match pattern <course>-ch<NN>-prob-<NNN>"
        )
        ok = False

    problem_chapter = (
        problem_id.split("-", 1)[1].rsplit("-prob-", 1)[0]
        if "-prob-" in problem_id
        else ""
    )
    expected_chapter = expected_chapter_from_metadata(chapter)
    if ok and problem_chapter != expected_chapter:
        errors.append(
            f"{problem_id}: chapter part '{problem_chapter}' does not match "
            f"manifest metadata chapter '{chapter}'"
        )
        ok = False

    kp_ids = problem.get("kp_ids")
    if not isinstance(kp_ids, list) or not kp_ids:
        errors.append(f"{problem_id}: kp_ids must be a non-empty list")
        ok = False
        kp_ids = []

    for kp_id in kp_ids:
        if not isinstance(kp_id, str) or not KP_ID_PATTERN.match(kp_id):
            errors.append(f"{problem_id}: kp_ids contains invalid kp_id '{kp_id}'")
            ok = False
        elif kp_id not in existing_kp_ids:
            errors.append(f"{problem_id}: kp_id '{kp_id}' not found in knowledge_points")
            ok = False

    problem_text = problem.get("problem_text")
    if not problem_text or not str(problem_text).strip():
        errors.append(f"{problem_id}: missing or empty problem_text")
        ok = False
    elif not validate_text_block_format(problem_id, "problem_text", problem_text, errors):
        ok = False

    solution = problem.get("solution")
    if solution is not None and not isinstance(solution, str):
        errors.append(
            f"{problem_id}: solution must be a string or null, got {type(solution).__name__}"
        )
        ok = False
    elif not validate_text_block_format(problem_id, "solution", solution, errors):
        ok = False

    problem_type = problem.get("problem_type")
    if problem_type not in VALID_PROBLEM_TYPES:
        errors.append(
            f"{problem_id}: problem_type '{problem_type}' not in {sorted(VALID_PROBLEM_TYPES)}"
        )
        ok = False

    source_kind = problem.get("source_kind")
    if source_kind not in VALID_SOURCE_KINDS:
        errors.append(
            f"{problem_id}: source_kind '{source_kind}' not in {sorted(VALID_SOURCE_KINDS)}"
        )
        ok = False

    cleaned = {
        "problem_id": problem_id,
        "kp_ids": json.dumps(kp_ids, ensure_ascii=False),
        "problem_text": problem_text,
        "solution": solution,
        "problem_type": problem_type,
        "source_kind": source_kind,
    }
    return ok, cleaned


def load_existing_kp_ids(conn: sqlite3.Connection) -> Set[str]:
    rows = conn.execute("SELECT kp_id FROM knowledge_points").fetchall()
    return {row[0] for row in rows}


def main(argv=None) -> int:
    args = parse_args(argv)

    if not os.path.isfile(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        print("Run create-tables.py first.", file=sys.stderr)
        return 1

    if not os.path.isfile(args.manifest):
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    try:
        with open(args.manifest, "r", encoding="utf-8-sig") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"ERROR: manifest JSON parse error: {exc}", file=sys.stderr)
        return 1

    metadata = manifest.get("metadata", {})
    chapter = metadata.get("chapter", "")
    if not chapter:
        print("ERROR: manifest missing metadata.chapter", file=sys.stderr)
        return 1

    problems = manifest.get("problems", [])
    if not isinstance(problems, list):
        print("ERROR: manifest.problems must be a list", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    try:
        existing_kp_ids = load_existing_kp_ids(conn)
        errors: List[str] = []
        cleaned_rows: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        print(f"Validating {len(problems)} problem entries from {args.manifest}...")
        for problem in problems:
            problem_id = problem.get("problem_id", "<no-id>")
            if problem_id in seen_ids:
                errors.append(f"{problem_id}: duplicate problem_id in manifest")
                continue
            seen_ids.add(problem_id)
            ok, cleaned = validate_problem(problem, chapter, existing_kp_ids, errors)
            if ok:
                cleaned_rows.append(cleaned)

        if errors:
            print("\n=== Problem validation errors ===", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            if args.strict:
                print(f"\n{len(errors)} validation errors. --strict set, aborting.", file=sys.stderr)
                return 3
            print(f"\n{len(errors)} validation errors. Continuing with valid rows only...", file=sys.stderr)

        if not cleaned_rows:
            print("No valid problem rows to insert.", file=sys.stderr)
            return 3

        insert_sql = (
            "INSERT OR REPLACE INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        ) if args.upsert else (
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )

        inserted = 0
        skipped = 0
        for row in cleaned_rows:
            try:
                conn.execute(insert_sql, (
                    row["problem_id"],
                    row["kp_ids"],
                    row["problem_text"],
                    row["solution"],
                    row["problem_type"],
                    row["source_kind"],
                ))
                inserted += 1
            except sqlite3.IntegrityError as exc:
                if args.upsert:
                    raise
                print(f"  SKIP {row['problem_id']}: {exc}", file=sys.stderr)
                skipped += 1

        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        print(f"\n{'Upserted' if args.upsert else 'Inserted'}: {inserted} rows")
        if skipped:
            print(f"Skipped (duplicate problem_id): {skipped}")
        print(f"problems table now has {total} rows")
        return 0
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
