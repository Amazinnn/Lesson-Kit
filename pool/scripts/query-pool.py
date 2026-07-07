#!/usr/bin/env python3
"""
Pool Query Script — lesson-kit SQLite knowledge pool extractor.

Queries knowledge_points, legacy companion questions, problems, kp_progress,
and question_progress for a given chapter prefix from the SQLite pool
database. Outputs structured JSON to stdout for downstream Agent rendering
steps.

Usage:
    python pool/scripts/query-pool.py --db pool/dmath.db \
        --chapter dmath-ch06 --view problem-set --source-kind textbook

The --view flag controls which tables are included:
  - first-pass: knowledge_points, questions, kp_progress, question_progress
  - problem-set: all the above + problems
"""

import argparse
import json
import sqlite3
import sys
from typing import Any, Dict, List, Optional


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the lesson-kit SQLite knowledge pool for a chapter."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the SQLite database file (e.g., pool/dld.db).",
    )
    parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter identifier used as kp_id prefix (e.g., 'dld-ch02').",
    )
    parser.add_argument(
        "--view",
        required=True,
        help="View type: 'first-pass', 'knowledge-guide', 'problem-set', or future extensions.",
    )
    parser.add_argument(
        "--source-kind",
        default=None,
        choices=["textbook", "quiz", "midterm", "final", "makeup", "other"],
        help="Optional problem-set filter for problems.source_kind.",
    )
    return parser.parse_args(argv)


def query_knowledge_points(
    conn: sqlite3.Connection, chapter: str
) -> List[Dict[str, Any]]:
    """
    Query all KPs whose kp_id starts with the chapter prefix.

    The related_kp_ids column stores a JSON array as TEXT. Each value is
    parsed with json.loads() so the output contains native lists.
    Returns an empty list if the table does not exist.
    """
    try:
        cur = conn.execute(
            "SELECT kp_id, knowledge_item, source_location, knowledge_type, "
            "related_kp_ids, importance, learning_action, body, difficulty, fragile "
            "FROM knowledge_points "
            "WHERE kp_id LIKE ?",
            (f"{chapter}-%",),
        )
    except sqlite3.OperationalError as exc:
        print(
            f"Error: failed to query knowledge_points table. {exc}",
            file=sys.stderr,
        )
        return []

    rows = cur.fetchall()
    kps = []
    for row in rows:
        (
            kp_id,
            knowledge_item,
            source_location,
            knowledge_type,
            related_kp_ids_raw,
            importance,
            learning_action,
            body,
            difficulty,
            fragile,
        ) = row

        # Parse the JSON-encoded related_kp_ids column
        related_kp_ids = None
        if related_kp_ids_raw is not None:
            try:
                related_kp_ids = json.loads(related_kp_ids_raw)
            except json.JSONDecodeError:
                print(
                    f"Warning: invalid JSON in related_kp_ids for {kp_id}: "
                    f"{related_kp_ids_raw}",
                    file=sys.stderr,
                )
                related_kp_ids = related_kp_ids_raw  # Pass through as-is

        kps.append({
            "kp_id": kp_id,
            "knowledge_item": knowledge_item,
            "source_location": source_location,
            "knowledge_type": knowledge_type,
            "importance": importance,
            "difficulty": difficulty,
            "fragile": fragile,
            "learning_action": learning_action,
            "body": body,
            "related_kp_ids": related_kp_ids,
        })

    return kps


def query_questions(
    conn: sqlite3.Connection, chapter: str
) -> List[Dict[str, Any]]:
    """
    Query all questions linked to KPs in the given chapter.

    Joins with knowledge_points on kp_id to ensure we only return questions
    belonging to the chapter-scoped KPs.
    """
    try:
        cur = conn.execute(
            "SELECT q.q_id, q.question_text, q.answer_key, "
            "q.answer_explanation, q.kp_id, q.difficulty "
            "FROM questions q "
            "INNER JOIN knowledge_points k ON q.kp_id = k.kp_id "
            "WHERE k.kp_id LIKE ?",
            (f"{chapter}-%",),
        )
    except sqlite3.OperationalError as exc:
        print(
            f"Error: failed to query questions table. {exc}",
            file=sys.stderr,
        )
        return []

    questions = []
    for row in cur.fetchall():
        (
            q_id,
            question_text,
            answer_key,
            answer_explanation,
            kp_id,
            difficulty,
        ) = row
        questions.append({
            "q_id": q_id,
            "question_text": question_text,
            "answer_key": answer_key,
            "answer_explanation": answer_explanation,
            "kp_id": kp_id,
            "difficulty": difficulty,
        })

    return questions


def query_kp_progress(
    conn: sqlite3.Connection, chapter: str
) -> Dict[str, str]:
    """
    Query mastery state for each KP in the chapter.

    Returns a dict mapping kp_id → mastery_state. Returns an empty dict
    if the kp_progress table is missing or has no rows.
    """
    try:
        cur = conn.execute(
            "SELECT p.kp_id, p.mastery_state "
            "FROM kp_progress p "
            "INNER JOIN knowledge_points k ON p.kp_id = k.kp_id "
            "WHERE k.kp_id LIKE ?",
            (f"{chapter}-%",),
        )
    except sqlite3.OperationalError:
        # Table likely does not exist yet — this is a normal state.
        return {}

    return {kp_id: mastery_state for kp_id, mastery_state in cur.fetchall()}


def query_question_progress(
    conn: sqlite3.Connection, chapter: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Query progress records for questions in the chapter.

    Returns a dict mapping q_id → list of {note, mastery_state, created_at}.
    Uses the latest progress record per question (max id).
    Returns an empty dict if the table is missing.
    """
    try:
        cur = conn.execute(
            "SELECT qp.q_id, qp.note, qp.mastery_state, qp.created_at "
            "FROM question_progress qp "
            "INNER JOIN questions q ON qp.q_id = q.q_id "
            "INNER JOIN knowledge_points k ON q.kp_id = k.kp_id "
            "WHERE k.kp_id LIKE ? "
            "ORDER BY qp.q_id, qp.id",
            (f"{chapter}-%",),
        )
    except sqlite3.OperationalError:
        # Table likely does not exist yet — this is a normal state.
        return {}

    question_states: Dict[str, List[Dict[str, Any]]] = {}
    for row in cur.fetchall():
        q_id, note, mastery_state, created_at = row
        record = {
            "note": note,
            "mastery_state": mastery_state,
            "created_at": created_at,
        }
        question_states.setdefault(q_id, []).append(record)

    return question_states


def query_problems(
    conn: sqlite3.Connection, chapter: str, source_kind: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query durable problems whose problem_id starts with the chapter prefix.

    Parses the kp_ids JSON column into a native list.
    Returns an empty list if the table does not exist.
    """
    where = "WHERE problem_id LIKE ?"
    params: List[Any] = [f"{chapter}-%"]
    if source_kind:
        where += " AND source_kind = ?"
        params.append(source_kind)

    try:
        cur = conn.execute(
            "SELECT problem_id, kp_ids, problem_text, solution, problem_type, source_kind "
            "FROM problems "
            f"{where} "
            "ORDER BY problem_id",
            params,
        )
    except sqlite3.OperationalError as exc:
        print(
            f"Error: failed to query problems table. {exc}",
            file=sys.stderr,
        )
        return []

    problems = []
    for row in cur.fetchall():
        problem_id, kp_ids_raw, problem_text, solution, problem_type, source_kind_value = row

        kp_ids = None
        if kp_ids_raw is not None:
            try:
                kp_ids = json.loads(kp_ids_raw)
            except json.JSONDecodeError:
                kp_ids = kp_ids_raw

        problems.append({
            "problem_id": problem_id,
            "kp_ids": kp_ids,
            "problem_text": problem_text,
            "solution": solution,
            "problem_type": problem_type,
            "source_kind": source_kind_value,
        })

    return problems


def build_output(
    kps: List[Dict[str, Any]],
    questions: List[Dict[str, Any]],
    kp_states: Dict[str, str],
    question_states: Dict[str, List[Dict[str, Any]]],
    problems: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Assemble the final output dictionary."""
    result: Dict[str, Any] = {
        "kps": kps,
        "questions": questions,
        "progress": {
            "kp_states": kp_states,
            "question_states": question_states,
        },
    }
    if problems is not None:
        result["problems"] = problems
    return result


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point. Returns 0 on success, 1 on error."""
    args = parse_args(argv)

    # Validate --view argument
    valid_views = {"first-pass", "knowledge-guide", "problem-set"}
    if args.view not in valid_views:
        print(
            f"Error: --view must be one of {valid_views}, got '{args.view}'",
            file=sys.stderr,
        )
        return 1

    # Open database
    try:
        conn = sqlite3.connect(args.db)
    except sqlite3.OperationalError as exc:
        print(
            f"Error: cannot open database '{args.db}'. {exc}",
            file=sys.stderr,
        )
        print(
            "Hint: the SQLite file must be created by the extraction pipeline "
            "before this script can query it. The pool must exist before the "
            "view.",
            file=sys.stderr,
        )
        return 1

    try:
        # Query all four core tables / logical data groups
        kps = query_knowledge_points(conn, args.chapter)
        questions = query_questions(conn, args.chapter)
        kp_states = query_kp_progress(conn, args.chapter)
        question_states = query_question_progress(conn, args.chapter)

        # problem-set view also queries the durable problem pool.
        problems = None
        if args.view == "problem-set":
            problems = query_problems(conn, args.chapter, args.source_kind)

        # Warn if no KPs found for the given chapter prefix
        if not kps:
            print(
                f"Warning: no knowledge_points found for chapter "
                f"'{args.chapter}'. Check that the --chapter argument matches "
                f"the kp_id prefix in the database.",
                file=sys.stderr,
            )
            print(
                "Hint: run this query to see available chapter prefixes:",
                file=sys.stderr,
            )
            print(
                "  SELECT DISTINCT substr(kp_id, 1, "
                "instr(kp_id || '-', '-') - 1) FROM knowledge_points;",
                file=sys.stderr,
            )

        output = build_output(
            kps, questions, kp_states, question_states,
            problems,
        )
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
