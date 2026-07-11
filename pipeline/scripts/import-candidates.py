#!/usr/bin/env python3
"""Import double-gated Problem Candidates into the durable problem pool."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
POOL_SCRIPT_DIR = SCRIPT_DIR.parents[1] / "pool" / "scripts"
if str(POOL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(POOL_SCRIPT_DIR))

from pool_schema import (  # noqa: E402
    ensure_learning_state_schema,
    ensure_problem_candidate_schema,
)


PROBLEM_ID_PATTERN = re.compile(r"^(?P<prefix>[a-z0-9]+-ch\d{2})-prob-(?P<number>\d{3})$")
CANDIDATE_ID_PATTERN = re.compile(r"^(?P<prefix>[a-z0-9]+-ch\d{2})-cand-\d{3}$")
BLOCK_DUPLICATE_RATIO = 0.92
WARN_HOMOGENEITY_RATIO = 0.75


def normalize_stem(text: str) -> str:
    return re.sub(r"[^\w]+", "", text.casefold(), flags=re.UNICODE)


def render_official_problem(row: sqlite3.Row) -> tuple[str, Optional[str]]:
    stem = str(row["problem_text"]).strip()
    solution = str(row["solution"]).strip() if row["solution"] else None
    if row["interaction_type"] == "free_response":
        return stem, solution

    options = json.loads(row["options_json"] or "[]")
    rendered_options = "\n\n".join(
        f"{option['id']}. {str(option['text']).strip()}" for option in options
    )
    problem_text = f"{stem}\n\n{rendered_options}"
    explanation = "\n\n".join(
        f"{option['id']}. {str(option['explanation']).strip()}" for option in options
    )
    sections = [f"Correct answer: {row['correct_option_id']}"]
    if solution:
        sections.extend(["Worked solution", solution])
    sections.extend(["Option explanations", explanation])
    return problem_text, "\n\n".join(sections)


def next_problem_id(conn: sqlite3.Connection, candidate_id: str) -> str:
    match = CANDIDATE_ID_PATTERN.match(candidate_id)
    if not match:
        raise ValueError(f"invalid candidate_id: {candidate_id}")
    prefix = match.group("prefix")
    maximum = 0
    for (problem_id,) in conn.execute(
        "SELECT problem_id FROM problems WHERE problem_id LIKE ?",
        (f"{prefix}-prob-%",),
    ):
        problem_match = PROBLEM_ID_PATTERN.match(str(problem_id))
        if problem_match and problem_match.group("prefix") == prefix:
            maximum = max(maximum, int(problem_match.group("number")))
    return f"{prefix}-prob-{maximum + 1:03d}"


def duplicate_check(
    conn: sqlite3.Connection,
    kp_ids_json: str,
    problem_text: str,
) -> tuple[Optional[str], Optional[str]]:
    candidate_kps = sorted(json.loads(kp_ids_json))
    normalized = normalize_stem(problem_text)
    strongest: tuple[float, str] = (0.0, "")
    for problem_id, existing_kps_json, existing_text in conn.execute(
        "SELECT problem_id, kp_ids, problem_text FROM problems"
    ):
        try:
            existing_kps = sorted(json.loads(existing_kps_json))
        except (TypeError, json.JSONDecodeError):
            continue
        if existing_kps != candidate_kps:
            continue
        ratio = SequenceMatcher(None, normalized, normalize_stem(str(existing_text))).ratio()
        if ratio > strongest[0]:
            strongest = (ratio, str(problem_id))
    if strongest[0] >= BLOCK_DUPLICATE_RATIO:
        return (
            f"near-duplicate of {strongest[1]} for the same kp_ids "
            f"(similarity {strongest[0]:.2f})",
            None,
        )
    if strongest[0] >= WARN_HOMOGENEITY_RATIO:
        return (
            None,
            f"homogeneous with {strongest[1]} for the same kp_ids "
            f"(similarity {strongest[0]:.2f})",
        )
    return None, None


def migrate_attempt_summary(
    conn: sqlite3.Connection,
    candidate_id: str,
    problem_id: str,
) -> None:
    attempts = conn.execute(
        """
        SELECT status, note FROM candidate_attempts
        WHERE candidate_id = ? ORDER BY id
        """,
        (candidate_id,),
    ).fetchall()
    if not attempts:
        return
    ensure_learning_state_schema(conn)
    final_status = str(attempts[-1]["status"])
    final_note = str(attempts[-1]["note"] or "").strip()
    misses = sum(1 for row in attempts if row["status"] in {"wrong", "stuck"})
    summary = (
        f"Candidate practice summary: {len(attempts)} attempts; "
        f"wrong/stuck: {misses}."
    )
    if final_note:
        summary += f" Final note: {final_note}"
    conn.execute(
        """
        INSERT INTO problem_progress (problem_id, status, note, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(problem_id) DO UPDATE SET
            status = excluded.status,
            note = excluded.note,
            updated_at = datetime('now')
        """,
        (problem_id, final_status, summary),
    )
    conn.execute(
        "INSERT INTO problem_attempts (problem_id, status, note) VALUES (?, ?, ?)",
        (problem_id, final_status, summary),
    )


def import_candidates(
    db_path: Path | str,
    candidate_ids: Optional[Sequence[str]] = None,
) -> tuple[list[str], list[str], list[str]]:
    db_path = Path(db_path)
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_problem_candidate_schema(conn)
        requested = list(dict.fromkeys(candidate_ids or []))
        if requested:
            placeholders = ", ".join("?" for _ in requested)
            rows = conn.execute(
                f"SELECT * FROM candidate_problems WHERE candidate_id IN ({placeholders})",
                tuple(requested),
            ).fetchall()
            row_by_id = {str(row["candidate_id"]): row for row in rows}
            ordered_rows = [row_by_id[item] for item in requested if item in row_by_id]
            errors = [f"{item}: candidate not found" for item in requested if item not in row_by_id]
        else:
            ordered_rows = conn.execute(
                "SELECT * FROM candidate_problems WHERE status = 'gate_passed' "
                "ORDER BY candidate_id"
            ).fetchall()
            errors = []

        imported: list[str] = []
        warnings: list[str] = []
        for row in ordered_rows:
            candidate_id = str(row["candidate_id"])
            if row["status"] == "imported":
                warnings.append(
                    f"{candidate_id}: already imported as {row['imported_problem_id']}"
                )
                continue
            if not (
                row["status"] == "gate_passed"
                and row["structure_gate_status"] == "pass"
                and row["audit_gate_status"] == "pass"
            ):
                errors.append(f"{candidate_id}: import requires double PASS and gate_passed status")
                continue

            duplicate_error, homogeneity_warning = duplicate_check(
                conn, str(row["kp_ids"]), str(row["problem_text"])
            )
            if duplicate_error:
                errors.append(f"{candidate_id}: {duplicate_error}")
                continue
            if homogeneity_warning:
                warnings.append(f"{candidate_id}: {homogeneity_warning}")

            problem_id = next_problem_id(conn, candidate_id)
            problem_text, solution = render_official_problem(row)
            conn.execute(
                """
                INSERT INTO problems (
                    problem_id, kp_ids, problem_text, solution,
                    problem_type, source_kind
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    problem_id,
                    row["kp_ids"],
                    problem_text,
                    solution,
                    row["problem_type"],
                    row["source_kind"],
                ),
            )
            migrate_attempt_summary(conn, candidate_id, problem_id)
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = 'imported', imported_problem_id = ?,
                    updated_at = datetime('now')
                WHERE candidate_id = ?
                """,
                (problem_id, candidate_id),
            )
            imported.append(problem_id)

        conn.commit()
        return imported, warnings, errors
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import gated candidates as durable Problems.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--candidate", action="append")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        imported, warnings, errors = import_candidates(args.db, args.candidate)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Candidate import: imported={len(imported)} warnings={len(warnings)} errors={len(errors)}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
