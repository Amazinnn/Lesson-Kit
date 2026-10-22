"""Git-authored content-bundle entry into the governed ingest boundary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from workbench import ingest, registry
from workbench.domain.practice_set import render_practice_set, render_solutions


_ID_FIELDS = (
    ("knowledge_points", "kp_id"),
    ("problems", "problem_id"),
    ("flash_cards", "card_id"),
)


def _parser(prog: str, *, include_workspace: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Check or apply a Git-authored content-bundle through Lesson-Kit's "
            "existing governed ingest boundary."
        ),
    )
    if include_workspace:
        parser.add_argument("workspace")
    parser.add_argument("--input", required=True, help="UTF-8 JSON file, or - for stdin")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply after the same complete bundle validation; default is read-only",
    )
    parser.add_argument(
        "--backup",
        help="optional recoverable database copy path; only valid with --apply",
    )
    parser.add_argument(
        "--selection",
        help=(
            "optional practice-set-selection JSON whose problem_key values refer to "
            "this bundle; it is a Git recipe, never a pool entity"
        ),
    )
    parser.add_argument("--student-out", help="write rendered student sheet after --apply")
    parser.add_argument("--solutions-out", help="write rendered solution sheet after --apply")
    return parser


def _read_json(value: str) -> dict:
    text = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("JSON input must be an object")
    return payload


def _read_manifest(value: str) -> dict:
    payload = _read_json(value)
    if payload.get("kind") != "content-bundle":
        raise ValueError("content-bundle input must have kind=content-bundle")
    return payload


def _authored_identity_errors(manifest: dict) -> list[str]:
    """A reviewed Git bundle proposes content; the pool owns canonical identity."""
    errors: list[str] = []
    for list_name, id_field in _ID_FIELDS:
        items = manifest.get(list_name)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items, 1):
            if isinstance(item, dict) and id_field in item:
                errors.append(
                    f"{list_name}[{index}]: {id_field} is not allowed in a Git-authored "
                    "bundle; use a bundle-local key and let governed ingest allocate "
                    "the canonical id"
                )
    return errors


def _workspace_context(name: str) -> tuple[dict, Path, str]:
    workspace = registry.get_workspace(name)
    root = Path(workspace["path"])
    database = (root / workspace["db"]).resolve()
    if not database.is_file():
        raise ValueError(f"pool database not found: {database}")
    course = str(workspace.get("active_course") or database.stem)
    return workspace, database, course


def _check(database: Path, manifest: dict, course: str) -> dict:
    uri = f"file:{database.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        return ingest._gate_content_bundle(conn, manifest, course)
    finally:
        conn.close()


def _selection_items(selection: dict, manifest: dict) -> list[dict]:
    if selection.get("kind") != "practice-set-selection":
        raise ValueError("selection must have kind=practice-set-selection")
    chapter = selection.get("chapter")
    if chapter and chapter != manifest.get("chapter"):
        raise ValueError("selection chapter does not match content bundle chapter")
    source_items = manifest.get("problems")
    if not isinstance(source_items, list):
        raise ValueError("content bundle problems must be a list")
    known = {
        item.get("key") for item in source_items
        if isinstance(item, dict) and isinstance(item.get("key"), str)
    }
    items = selection.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("selection items must be a non-empty list")
    seen = set()
    normalized = []
    total = 0
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"selection item {index} must be an object")
        key = item.get("problem_key")
        points = item.get("points")
        if key not in known:
            raise ValueError(f"selection item {index}: unknown problem_key {key}")
        if key in seen:
            raise ValueError(f"selection item {index}: duplicate problem_key {key}")
        if not isinstance(points, int) or isinstance(points, bool) or points <= 0:
            raise ValueError(f"selection item {index}: points must be a positive integer")
        seen.add(key)
        total += points
        normalized.append({"problem_key": key, "points": points})
    declared = selection.get("total_points")
    if declared is not None and declared != total:
        raise ValueError(f"selection total_points={declared} but item points sum to {total}")
    return normalized


def _planned_problem_map(manifest: dict, verified: dict) -> dict[str, str]:
    source = manifest.get("problems") or []
    plans = verified.get("problems") or []
    if len(source) != len(plans):
        raise ValueError("governed check did not return one problem plan per authored problem")
    return {
        item["key"]: plan["problem_id"]
        for item, plan in zip(source, plans)
        if isinstance(item, dict) and isinstance(item.get("key"), str)
    }


def _applied_problem_map(database: Path, batch_id: str, manifest: dict) -> tuple[dict[str, str], list[dict]]:
    source = manifest.get("problems") or []
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT problem_id, kp_ids, problem_text, solution FROM problems "
            "WHERE ingest_batch_id=? ORDER BY rowid",
            (batch_id,),
        ).fetchall()
    finally:
        conn.close()
    if len(rows) != len(source):
        raise ValueError(
            f"applied batch has {len(rows)} problems but bundle authored {len(source)}"
        )
    mapping = {}
    decoded = []
    for item, row in zip(source, rows):
        key = item.get("key") if isinstance(item, dict) else None
        if not isinstance(key, str):
            raise ValueError("every selected authored problem must have a local key")
        if row["problem_text"] != item.get("problem_text", item.get("stem")):
            raise ValueError(f"applied problem order mismatch at {key}")
        mapping[key] = row["problem_id"]
        decoded.append({
            "problem_id": row["problem_id"],
            "kp_ids": json.loads(row["kp_ids"] or "[]"),
            "problem_text": row["problem_text"] or "",
            "solution": row["solution"] or "",
        })
    return mapping, decoded


def _render_selection(selection: dict, items: list[dict], mapping: dict[str, str], rows: list[dict]):
    by_id = {row["problem_id"]: row for row in rows}
    problems = []
    resolved = []
    for item in items:
        problem_id = mapping[item["problem_key"]]
        problem = by_id[problem_id]
        problems.append(problem)
        resolved.append({**item, "problem_id": problem_id})
    title = str(selection.get("title") or "Practice Set")
    return resolved, render_practice_set(problems, title), render_solutions(problems, title)


def main(argv=None, *, prog="lesson-kit ingest bundle") -> int:
    parser = _parser(prog)
    args = parser.parse_args(argv)
    return run(args, parser)


def run(args, parser=None) -> int:
    parser = parser or _parser("lesson-kit ingest bundle")
    if args.backup and not args.apply:
        parser.error("--backup requires --apply")
    if (args.student_out or args.solutions_out) and not args.selection:
        parser.error("--student-out/--solutions-out require --selection")
    if (args.student_out or args.solutions_out) and not args.apply:
        parser.error("rendered output requires --apply")

    try:
        manifest = _read_manifest(args.input)
        errors = _authored_identity_errors(manifest)
        if errors:
            result = {"ok": False, "errors": errors}
        else:
            _, database, course = _workspace_context(args.workspace)
            verified = _check(database, manifest, course)
            if not verified.get("ok"):
                result = verified
            else:
                selection = _read_json(args.selection) if args.selection else None
                selected = _selection_items(selection, manifest) if selection else None
                if not args.apply:
                    result = verified
                    if selection:
                        planned = _planned_problem_map(manifest, verified)
                        result["selection"] = [
                            {**item, "problem_id": planned[item["problem_key"]]}
                            for item in selected
                        ]
                else:
                    result = ingest.apply_batch(
                        database,
                        manifest,
                        source="cli",
                        backup_path=args.backup,
                        course=course,
                    )
                    if selection and result.get("ok"):
                        batch_id = result.get("batch_id")
                        if not isinstance(batch_id, str):
                            raise ValueError("selection rendering requires a single-chapter bundle")
                        mapping, rows = _applied_problem_map(database, batch_id, manifest)
                        resolved, student, solutions = _render_selection(
                            selection, selected, mapping, rows
                        )
                        if args.student_out:
                            Path(args.student_out).write_text(student, encoding="utf-8")
                        if args.solutions_out:
                            Path(args.solutions_out).write_text(solutions, encoding="utf-8")
                        result["selection"] = {
                            "title": selection.get("title") or "Practice Set",
                            "total_points": sum(item["points"] for item in selected),
                            "items": resolved,
                            "student_out": args.student_out,
                            "solutions_out": args.solutions_out,
                        }
    except (OSError, ValueError, KeyError, json.JSONDecodeError, sqlite3.Error) as exc:
        result = {"ok": False, "errors": [str(exc)]}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
