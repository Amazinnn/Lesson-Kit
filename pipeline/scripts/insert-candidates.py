#!/usr/bin/env python3
"""Validate and insert source-grounded Problem Candidates into a course pool."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
POOL_SCRIPT_DIR = SCRIPT_DIR.parents[1] / "pool" / "scripts"
for path in (SCRIPT_DIR, POOL_SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from candidate_contract import fetch_relation_ids, validate_candidate  # noqa: E402
from pool_schema import ensure_problem_candidate_schema  # noqa: E402


def insert_candidates(
    db_path: Path | str,
    manifest_path: Path | str,
    upsert: bool = False,
) -> tuple[int, int, list[str]]:
    db_path = Path(db_path)
    manifest_path = Path(manifest_path)
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict):
        return 0, 0, ["manifest root must be an object"]
    metadata = manifest.get("metadata", {})
    if not isinstance(metadata, dict):
        return 0, 0, ["manifest metadata must be an object"]
    course = str(metadata.get("course", "")).strip()
    chapter = str(metadata.get("chapter", "")).strip()
    candidates = manifest.get("candidates")
    if not course or not chapter:
        return 0, 0, ["manifest metadata requires course and chapter"]
    if not isinstance(candidates, list):
        return 0, 0, ["manifest.candidates must be a list"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_problem_candidate_schema(conn)
        kp_ids = {str(row[0]) for row in conn.execute("SELECT kp_id FROM knowledge_points")}
        relation_ids = fetch_relation_ids(conn)
        cleaned_rows = []
        errors: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                errors.append("candidate entry must be an object")
                continue
            candidate_id = str(candidate.get("candidate_id", ""))
            if candidate_id in seen:
                errors.append(f"{candidate_id}: duplicate candidate_id in manifest")
                continue
            seen.add(candidate_id)
            valid, cleaned, row_errors = validate_candidate(
                candidate, course, chapter, kp_ids, relation_ids
            )
            errors.extend(row_errors)
            if valid:
                cleaned_rows.append(cleaned)

        if errors:
            conn.rollback()
            return 0, 0, errors

        inserted = 0
        skipped = 0
        fields = (
            "candidate_id", "kp_ids", "problem_text", "options_json",
            "correct_option_id", "solution", "problem_type", "interaction_type",
            "generation_purpose", "origin_kind", "source_kind",
            "source_evidence_json",
        )
        for row in cleaned_rows:
            existing = conn.execute(
                "SELECT status FROM candidate_problems WHERE candidate_id = ?",
                (row["candidate_id"],),
            ).fetchone()
            if existing and not upsert:
                skipped += 1
                continue
            if existing and existing["status"] == "imported":
                errors.append(f"{row['candidate_id']}: imported candidate cannot be overwritten")
                continue
            placeholders = ", ".join("?" for _ in fields)
            if existing:
                assignments = ", ".join(f"{field} = excluded.{field}" for field in fields[1:])
                sql = (
                    f"INSERT INTO candidate_problems ({', '.join(fields)}) VALUES ({placeholders}) "
                    f"ON CONFLICT(candidate_id) DO UPDATE SET {assignments}, "
                    "status = 'draft', structure_gate_status = 'pending', "
                    "audit_gate_status = 'pending', gate_report = NULL, updated_at = datetime('now')"
                )
            else:
                sql = f"INSERT INTO candidate_problems ({', '.join(fields)}) VALUES ({placeholders})"
            conn.execute(sql, tuple(row[field] for field in fields))
            inserted += 1

        if errors:
            conn.rollback()
            return 0, skipped, errors
        conn.commit()
        return inserted, skipped, []
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Insert Problem Candidates into a pool.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--upsert", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        inserted, skipped, errors = insert_candidates(args.db, args.manifest, args.upsert)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Candidates: inserted={inserted} skipped={skipped} errors={len(errors)}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
