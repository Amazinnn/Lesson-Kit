#!/usr/bin/env python3
"""Run or record a Candidate Practice Session."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from learner_signals import upsert_learner_signal  # noqa: E402
from pool_schema import PROBLEM_STATES, ensure_problem_candidate_schema  # noqa: E402


def normalize_cli_input(value: str) -> str:
    """Normalize interactive and piped console input on Windows."""
    return value.strip().lstrip("\ufeff").strip()


def record_candidate_attempt(
    db_path: Path | str,
    candidate_id: str,
    status: str,
    selected_option_id: Optional[str] = None,
    note: str = "",
) -> dict[str, Any]:
    if status not in PROBLEM_STATES:
        raise ValueError(f"invalid status: {status}")
    db_path = Path(db_path)
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_problem_candidate_schema(conn)
        row = conn.execute(
            "SELECT * FROM candidate_problems WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"candidate not found: {candidate_id}")
        if row["status"] != "gate_passed":
            raise ValueError(
                f"candidate is not eligible for practice: {candidate_id} ({row['status']})"
            )

        options = json.loads(row["options_json"]) if row["options_json"] else []
        option_by_id = {str(option["id"]): option for option in options}
        is_correct: Optional[bool] = None
        selected_option = None
        if row["interaction_type"] == "free_response":
            if selected_option_id:
                raise ValueError("free_response attempts cannot select an option")
        elif selected_option_id:
            selected_option = option_by_id.get(selected_option_id)
            if selected_option is None:
                raise ValueError(f"unknown option id: {selected_option_id}")
            is_correct = selected_option_id == row["correct_option_id"]
            if is_correct and status in {"wrong", "stuck"}:
                raise ValueError("correct selected option conflicts with wrong/stuck status")
            if not is_correct and status == "mastered":
                raise ValueError("wrong selected option conflicts with mastered status")

        clean_note = note.strip() or None
        cursor = conn.execute(
            """
            INSERT INTO candidate_attempts (
                candidate_id, status, selected_option_id, is_correct, note
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                status,
                selected_option_id,
                None if is_correct is None else int(is_correct),
                clean_note,
            ),
        )

        signal_ids: list[str] = []
        if status in {"wrong", "stuck"}:
            for kp_id in json.loads(row["kp_ids"]):
                signal_ids.append(
                    upsert_learner_signal(
                        conn,
                        "node",
                        kp_id,
                        "weak_node",
                        note,
                        "candidate",
                        candidate_id,
                    )
                )
            lure = selected_option.get("error_lure") if selected_option else None
            if isinstance(lure, dict):
                signal_ids.append(
                    upsert_learner_signal(
                        conn,
                        str(lure["target_type"]),
                        str(lure["target_id"]),
                        str(lure["signal_type"]),
                        str(lure.get("note", "")),
                        "candidate",
                        candidate_id,
                    )
                )

        conn.commit()
        return {
            "attempt_id": cursor.lastrowid,
            "candidate_id": candidate_id,
            "status": status,
            "selected_option_id": selected_option_id,
            "is_correct": is_correct,
            "signal_ids": signal_ids,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def eligible_candidates(db_path: Path, candidate_ids: Sequence[str] | None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_problem_candidate_schema(conn)
        if candidate_ids:
            placeholders = ", ".join("?" for _ in candidate_ids)
            rows = conn.execute(
                f"SELECT * FROM candidate_problems WHERE candidate_id IN ({placeholders}) "
                "ORDER BY candidate_id",
                tuple(candidate_ids),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM candidate_problems WHERE status = 'gate_passed' "
                "ORDER BY candidate_id"
            ).fetchall()
        result = [dict(row) for row in rows]
        ineligible = [row["candidate_id"] for row in result if row["status"] != "gate_passed"]
        if ineligible:
            raise ValueError(f"candidates are not eligible: {', '.join(ineligible)}")
        return result
    finally:
        conn.close()


def run_session(db_path: Path, candidate_ids: Sequence[str] | None = None) -> int:
    rows = eligible_candidates(db_path, candidate_ids)
    if not rows:
        print("No gate-passed candidates found.")
        return 0
    for row in rows:
        print(f"\n[{row['candidate_id']}]\n{row['problem_text']}\n")
        options = json.loads(row["options_json"]) if row["options_json"] else []
        for option in options:
            print(f"{option['id']}. {option['text']}")

        if row["interaction_type"] == "free_response":
            input("Write or think through your answer, then press Enter to reveal the solution. ")
            print(f"\nSolution\n{row['solution']}\n")
            status = normalize_cli_input(input("Status [wrong/stuck/reviewing/mastered]: "))
            note = normalize_cli_input(input("Note (optional): "))
            record_candidate_attempt(db_path, row["candidate_id"], status, None, note)
            continue

        selected = normalize_cli_input(input("Answer option, or ? if stuck: "))
        if selected == "?":
            note = normalize_cli_input(input("What blocked you? "))
            record_candidate_attempt(db_path, row["candidate_id"], "stuck", None, note)
        else:
            correct = selected == row["correct_option_id"]
            print("Correct." if correct else f"Incorrect. Correct option: {row['correct_option_id']}")
            selected_option = next(
                (option for option in options if str(option["id"]) == selected), None
            )
            if selected_option:
                print(selected_option["explanation"])
            note = normalize_cli_input(input("Note (optional): "))
            record_candidate_attempt(
                db_path,
                row["candidate_id"],
                "mastered" if correct else "wrong",
                selected,
                note,
            )
    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Practice gate-passed Problem Candidates.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--candidate", action="append")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        return run_session(Path(args.db), args.candidate)
    except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
