"""Git-authored content-bundle entry into the governed ingest boundary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from workbench import ingest, registry


_ID_FIELDS = (
    ("knowledge_points", "kp_id"),
    ("problems", "problem_id"),
    ("flash_cards", "card_id"),
)


def _parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Check or apply a Git-authored content-bundle through Lesson-Kit's "
            "existing governed ingest boundary."
        ),
    )
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
    return parser


def _read_manifest(value: str) -> dict:
    text = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("content-bundle input must be a JSON object")
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


def main(argv=None, *, prog="lesson-kit ingest bundle") -> int:
    parser = _parser(prog)
    args = parser.parse_args(argv)
    if args.backup and not args.apply:
        parser.error("--backup requires --apply")

    try:
        manifest = _read_manifest(args.input)
        errors = _authored_identity_errors(manifest)
        if errors:
            result = {"ok": False, "errors": errors}
        else:
            _, database, course = _workspace_context(args.workspace)
            if args.apply:
                result = ingest.apply_batch(
                    database,
                    manifest,
                    source="cli",
                    backup_path=args.backup,
                    course=course,
                )
            else:
                result = _check(database, manifest, course)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, sqlite3.Error) as exc:
        result = {"ok": False, "errors": [str(exc)]}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
