#!/usr/bin/env python3
"""
Pipeline Step 7: Insert knowledge points into SQLite pool.

Reads pool-insert-manifest.json, validates each KP, and INSERTs into
the knowledge_points table. By default duplicates raise an error;
--upsert switches to INSERT OR REPLACE.

Usage:
    python pipeline/scripts/insert-knowledge-points.py \
        --db pool/dld-ch02.db \
        --manifest intermediate/dld/extraction/ch02/02_analysis/pool-insert-manifest.json \
        [--upsert]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Set, Tuple


VALID_KNOWLEDGE_TYPES: Set[str] = {
    "concept-property", "method-modeling", "formula-calculation",
    "algorithm-process", "code-implementation", "system-timing",
    "lab-implementation", "memory-recall",
}

VALID_IMPORTANCE: Set[str] = {"core", "supplementary", "optional"}

KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")
COLLAPSED_SUBPART_PATTERN = re.compile(r"[^\n][ \t]+[a-j]\s*\)[ \t]+")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Insert knowledge points into the lesson-kit pool DB.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to pool-insert-manifest.json.",
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


def validate_text_block_format(
    owner_id: str,
    field_name: str,
    value: Any,
    errors: List[str],
) -> bool:
    """
    Catch extracted Markdown blocks that collapsed subparts into one line.
    This keeps formatting responsibility in extraction, before rendering.
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


def validate_kp(
    kp: Dict[str, Any], chapter: str, errors: List[str]
) -> Tuple[bool, Dict[str, Any]]:
    """Validate one KP. Returns (is_valid, cleaned_row)."""
    ok = True
    kp_id = kp.get("kp_id")

    if not kp_id:
        errors.append("KP missing required field 'kp_id'")
        return False, {}

    if not KP_ID_PATTERN.match(kp_id):
        errors.append(
            f"{kp_id}: kp_id must match pattern <course>-ch<NN>-kp-<NNN>; "
            "chapter part must use zero-padded 2-digit number"
        )
        ok = False

    kp_chapter = kp_id.split("-", 1)[1].rsplit("-kp-", 1)[0] if "-kp-" in kp_id else ""
    expected_chapter = f"ch{chapter[2:]}" if chapter.startswith("ch") else chapter
    if ok and kp_chapter != expected_chapter:
        errors.append(
            f"{kp_id}: kp_id chapter part '{kp_chapter}' does not match "
            f"manifest metadata chapter '{chapter}'"
        )
        ok = False

    knowledge_item = kp.get("knowledge_item")
    if not knowledge_item or not str(knowledge_item).strip():
        errors.append(f"{kp_id}: missing or empty 'knowledge_item'")
        ok = False

    graph_label = kp.get("graph_label")
    if graph_label is not None:
        if not isinstance(graph_label, str):
            errors.append(
                f"{kp_id}: graph_label must be a short string or null, "
                f"got {type(graph_label).__name__}"
            )
            ok = False
            graph_label = None
        else:
            graph_label = graph_label.strip()
            if "\n" in graph_label or "\r" in graph_label:
                errors.append(f"{kp_id}: graph_label must be a single line")
                ok = False
            if len(graph_label) > 24:
                errors.append(f"{kp_id}: graph_label must be 24 characters or fewer")
                ok = False
            if not graph_label:
                graph_label = None

    knowledge_type = kp.get("knowledge_type")
    if knowledge_type not in VALID_KNOWLEDGE_TYPES:
        errors.append(
            f"{kp_id}: knowledge_type '{knowledge_type}' not in {sorted(VALID_KNOWLEDGE_TYPES)}"
        )
        ok = False

    importance = kp.get("importance")
    if importance not in VALID_IMPORTANCE:
        errors.append(
            f"{kp_id}: importance '{importance}' not in {sorted(VALID_IMPORTANCE)}"
        )
        ok = False

    difficulty = kp.get("difficulty", 2)
    if difficulty is None:
        difficulty = 2
    if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
        errors.append(f"{kp_id}: difficulty must be int 1-5, got {difficulty!r}")
        ok = False

    fragile = kp.get("fragile")  # None or Markdown string; NULL = not fragile
    if fragile is not None and not isinstance(fragile, str):
        errors.append(f"{kp_id}: fragile must be a string or null, got {type(fragile).__name__}")
        ok = False
    elif not validate_text_block_format(kp_id, "fragile", fragile, errors):
        ok = False

    for field_name in ("learning_action", "body"):
        if not validate_text_block_format(kp_id, field_name, kp.get(field_name), errors):
            ok = False

    related_kp_ids = kp.get("related_kp_ids", [])
    if not isinstance(related_kp_ids, list):
        errors.append(f"{kp_id}: related_kp_ids must be a list, got {type(related_kp_ids).__name__}")
        ok = False
        related_kp_ids = []

    for ref in related_kp_ids:
        if not isinstance(ref, str) or not KP_ID_PATTERN.match(ref):
            errors.append(
                f"{kp_id}: related_kp_ids contains invalid kp_id '{ref}'"
            )
            ok = False

    cleaned = {
        "kp_id": kp_id,
        "knowledge_item": knowledge_item,
        "graph_label": graph_label,
        "source_location": kp.get("source_location"),
        "knowledge_type": knowledge_type,
        "related_kp_ids": json.dumps(related_kp_ids, ensure_ascii=False),
        "importance": importance,
        "learning_action": kp.get("learning_action"),
        "body": kp.get("body"),
        "difficulty": difficulty,
        "fragile": fragile,
    }
    return ok, cleaned


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

    knowledge_points = manifest.get("knowledge_points", [])
    if not isinstance(knowledge_points, list):
        print("ERROR: manifest.knowledge_points must be a list", file=sys.stderr)
        return 1

    print(f"Validating {len(knowledge_points)} KP entries from {args.manifest}...")
    errors: List[str] = []
    cleaned_rows: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for kp in knowledge_points:
        kp_id = kp.get("kp_id", "<no-id>")
        if kp_id in seen_ids:
            errors.append(f"{kp_id}: duplicate kp_id in manifest")
            continue
        seen_ids.add(kp_id)
        ok, cleaned = validate_kp(kp, chapter, errors)
        if ok:
            cleaned_rows.append(cleaned)

    if errors:
        print("\n=== Validation errors ===", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        if args.strict:
            print(f"\n{len(errors)} validation errors. --strict set, aborting.", file=sys.stderr)
            return 3
        print(f"\n{len(errors)} validation errors. Continuing with valid rows only...", file=sys.stderr)

    if not cleaned_rows:
        print("No valid KP rows to insert.", file=sys.stderr)
        return 3

    conn = sqlite3.connect(args.db)
    try:
        insert_sql = (
            "INSERT OR REPLACE INTO knowledge_points "
            "(kp_id, knowledge_item, graph_label, source_location, knowledge_type, "
            "related_kp_ids, importance, learning_action, body, difficulty, fragile) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ) if args.upsert else (
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, graph_label, source_location, knowledge_type, "
            "related_kp_ids, importance, learning_action, body, difficulty, fragile) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )

        inserted = 0
        skipped = 0
        for row in cleaned_rows:
            try:
                conn.execute(insert_sql, (
                    row["kp_id"],
                    row["knowledge_item"],
                    row["graph_label"],
                    row["source_location"],
                    row["knowledge_type"],
                    row["related_kp_ids"],
                    row["importance"],
                    row["learning_action"],
                    row["body"],
                    row["difficulty"],
                    row["fragile"],
                ))
                inserted += 1
            except sqlite3.IntegrityError as exc:
                if args.upsert:
                    raise
                print(f"  SKIP {row['kp_id']}: {exc}", file=sys.stderr)
                skipped += 1

        conn.commit()

        total = conn.execute("SELECT COUNT(*) FROM knowledge_points").fetchone()[0]
        print(f"\n{'Upserted' if args.upsert else 'Inserted'}: {inserted} rows")
        if skipped:
            print(f"Skipped (duplicate kp_id): {skipped}")
        print(f"knowledge_points table now has {total} rows")
        return 0
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
