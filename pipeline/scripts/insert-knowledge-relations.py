#!/usr/bin/env python3
"""Insert audited Course Learning Network relations into a lesson-kit pool."""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
POOL_SCRIPT_DIR = REPO_ROOT / "pool" / "scripts"
if str(POOL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(POOL_SCRIPT_DIR))

from pool_schema import (  # noqa: E402
    VALID_RELATION_DIRECTIONS,
    VALID_RELATION_STRENGTHS,
    VALID_RELATION_TYPES,
    ensure_course_network_schema,
)


KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert audited knowledge relations into the lesson-kit pool.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument("--manifest", required=True, help="Path to relation-insert-manifest.json.")
    parser.add_argument("--upsert", action="store_true", help="Overwrite existing relation rows.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any validation errors are found.",
    )
    return parser.parse_args(argv)


def generated_relation_id(source: str, target: str, relation_type: str) -> str:
    return f"rel:{source}:{relation_type}:{target}"


def normalize_relation(row: Dict[str, Any]) -> Dict[str, Any]:
    source = str(row.get("source_kp_id", "")).strip()
    target = str(row.get("target_kp_id", "")).strip()
    relation_type = str(row.get("relation_type", "")).strip()
    direction = str(row.get("direction", "")).strip()
    strength = str(row.get("strength", "")).strip()
    if direction == "symmetric" and source and target and target < source:
        source, target = target, source
    relation_id = str(row.get("relation_id") or generated_relation_id(source, target, relation_type)).strip()
    return {
        "relation_id": relation_id,
        "source_kp_id": source,
        "target_kp_id": target,
        "relation_type": relation_type,
        "direction": direction,
        "strength": strength,
    }


def validate_relation(
    relation: Dict[str, Any],
    kp_ids: Set[str],
    errors: List[str],
) -> bool:
    ok = True
    relation_id = relation["relation_id"] or "<no-id>"
    source = relation["source_kp_id"]
    target = relation["target_kp_id"]

    for field_name, value in (("source_kp_id", source), ("target_kp_id", target)):
        if not value or not KP_ID_PATTERN.match(value):
            errors.append(f"{relation_id}: {field_name} has invalid kp_id '{value}'")
            ok = False
        elif value not in kp_ids:
            errors.append(f"{relation_id}: {field_name} '{value}' not found in knowledge_points")
            ok = False

    if source == target:
        errors.append(f"{relation_id}: source_kp_id and target_kp_id must differ")
        ok = False
    if relation["relation_type"] not in VALID_RELATION_TYPES:
        errors.append(
            f"{relation_id}: relation_type '{relation['relation_type']}' not in {list(VALID_RELATION_TYPES)}"
        )
        ok = False
    if relation["direction"] not in VALID_RELATION_DIRECTIONS:
        errors.append(
            f"{relation_id}: direction '{relation['direction']}' not in {list(VALID_RELATION_DIRECTIONS)}"
        )
        ok = False
    if relation["strength"] not in VALID_RELATION_STRENGTHS:
        errors.append(
            f"{relation_id}: strength '{relation['strength']}' not in {list(VALID_RELATION_STRENGTHS)}"
        )
        ok = False
    return ok


def load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def insert_relations(
    db_path: str,
    manifest_path: str,
    *,
    upsert: bool = False,
    strict: bool = False,
) -> Tuple[int, int, List[str]]:
    manifest = load_manifest(manifest_path)
    relations_raw = manifest.get("relations", [])
    if not isinstance(relations_raw, list):
        raise ValueError("manifest.relations must be a list")

    conn = sqlite3.connect(db_path)
    try:
        ensure_course_network_schema(conn)
        kp_ids = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points").fetchall()}
        errors: List[str] = []
        cleaned: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()
        seen_keys: Set[Tuple[str, str, str]] = set()

        for row in relations_raw:
            if not isinstance(row, dict):
                errors.append(f"relation entry must be object, got {type(row).__name__}")
                continue
            relation = normalize_relation(row)
            relation_id = relation["relation_id"]
            key = (
                relation["source_kp_id"],
                relation["target_kp_id"],
                relation["relation_type"],
            )
            if relation_id in seen_ids:
                errors.append(f"{relation_id}: duplicate relation_id in manifest")
                continue
            if key in seen_keys:
                errors.append(f"{relation_id}: duplicate relation key {key}")
                continue
            seen_ids.add(relation_id)
            seen_keys.add(key)
            if validate_relation(relation, kp_ids, errors):
                cleaned.append(relation)

        if errors and strict:
            return 0, 0, errors
        if not cleaned:
            return 0, 0, errors or ["No valid relation rows to insert."]

        sql = (
            "INSERT OR REPLACE INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))"
        ) if upsert else (
            "INSERT INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )

        inserted = 0
        skipped = 0
        for relation in cleaned:
            try:
                conn.execute(
                    sql,
                    (
                        relation["relation_id"],
                        relation["source_kp_id"],
                        relation["target_kp_id"],
                        relation["relation_type"],
                        relation["direction"],
                        relation["strength"],
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError as exc:
                if upsert:
                    raise
                errors.append(f"{relation['relation_id']}: {exc}")
                skipped += 1

        conn.commit()
        return inserted, skipped, errors
    finally:
        conn.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if not os.path.isfile(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        return 1
    if not os.path.isfile(args.manifest):
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    try:
        inserted, skipped, errors = insert_relations(
            args.db,
            args.manifest,
            upsert=args.upsert,
            strict=args.strict,
        )
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("\n=== Validation / insert warnings ===", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        if args.strict:
            print("\n--strict set, aborting.", file=sys.stderr)
            return 3

    if inserted == 0 and skipped == 0:
        print("No relation rows inserted.", file=sys.stderr)
        return 3
    print(f"{'Upserted' if args.upsert else 'Inserted'}: {inserted} relations")
    if skipped:
        print(f"Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
