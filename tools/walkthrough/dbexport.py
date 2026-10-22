"""Persistence / learning-projection export and diff — G-2, G-3, G-4, G-6.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §4 (persistence and learning projection) and
``acceptance.md`` §0 G-2/G-3/G-4/G-6.

The gates
---------
========  =========================================================================
gate     what it proves
========  =========================================================================
G-2       the practice's persisted result is unchanged: ``problem_attempts`` /
          ``feedback_events`` / ``practice_runs`` have the same row count and
          the same key columns
G-3       the learning projection is unchanged: ``learning_current_state`` /
          ``review_schedule`` / ``problem_progress`` / ``learner_signals``
G-4       the review suggestions are unchanged: the ``/due`` set and the
          ``/weak`` ordering
G-6       the pool schema did not change: no new column, no new row
========  =========================================================================

Two properties make the comparison meaningful and they are the reason this
module exists at all:

**Normalisation (§4.1, §4.2).**  Wall-clock timestamps and random ids
differ on every run, so they are replaced by placeholders before the diff.
``draft_sequence`` is deliberately **kept**: it counts how many times a
draft was written, so a change in the interaction rhythm shows up as a
persistence difference instead of hiding behind a normalised field.

**Stable ordering (§4.3).**  Rows are sorted by their primary key and the
columns are a fixed list, so a diff is a line diff and not a reshuffle.

**G-6 is a negative assertion.**  The pool must not have gained a column
or a row.  The schema is read from ``sqlite_master`` and the row counts
of every table are compared, so "the change added a column" and "the
change wrote a row" are both caught.

Red lines (§8.3): the pool is opened **read-only** (``mode=ro``) and the
export never writes to it.  The diff runs on the two exported snapshots,
not on the live pool.
"""

import argparse
import json
import sqlite3
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────
# the export plan (§4.1)
# ─────────────────────────────────────────────────────────────────────────

#: ``table -> (columns, sort key)``.  The columns are the *key columns*
#: the gates compare (§4.1); the sort key makes the row order stable.
TABLES = {
    # G-2 — the practice's persisted result.
    "problem_attempts": (["id", "problem_id", "status", "note", "created_at"], "id"),
    "feedback_events": (["id", "item_type", "item_id", "rating", "note", "created_at"], "id"),
    "practice_runs": (["id", "source_kind", "source_ref", "source_label", "kp_ids_json",
                        "practice_mode", "rating_mode", "items_json", "status",
                        "started_at", "finished_at"], "id"),
    # G-3 — the learning projection.
    "learning_current_state": (["item_type", "item_id", "state", "updated_at"],
                                "item_type, item_id"),
    "review_schedule": (["item_type", "item_id", "direction", "state", "repetitions",
                         "ease", "interval_days", "due_at", "last_rating",
                         "last_reviewed_at"], "item_type, item_id, direction"),
    "problem_progress": (["problem_id", "status", "note", "updated_at"], "problem_id"),
    "learner_signals": (["signal_id", "target_type", "target_id", "signal_type", "weight",
                         "evidence_count", "note", "last_practice_kind", "last_practice_ref",
                         "created_at", "updated_at"], "signal_id"),
}

#: Tables whose row *count* must not change (G-6's "零新增行").  The
#: practice tables are included on purpose: the exercise writes a fixed
#: number of rows, so a drift there is a real difference.
ROW_COUNT_TABLES = (
    "problem_attempts", "feedback_events", "practice_runs",
    "learning_current_state", "review_schedule", "problem_progress", "learner_signals",
    "active_practice", "active_practice_items", "paper_state",
)

#: Fields replaced by a placeholder before the diff (§4.1, §4.2).
#: ``request_id`` is a fresh uuid per request, the execution id is a fresh
#: rowid, and every timestamp is wall-clock.
PLACEHOLDER_FIELDS = {
    "request_id": "<RID>",
    "execution_id": "<EXEC>",
    "created_at": "<TS>",
    "updated_at": "<TS>",
    "started_at": "<TS>",
    "finished_at": "<TS>",
    "last_reviewed_at": "<TS>",
}

#: §4.2 replaces the attempt id with a placeholder **only when its value
#: varies between the two runs**.  An attempt id is a rowid, so it moves
#: whenever a different number of rows was written before it; it is not a
#: learning fact.  The diff therefore relaxes it *only* when the two sides
#: disagree on it, and reports the relaxation in the diff detail.
VOLATILE_FIELDS = ("attempt_id",)

#: ``due_at`` is a *date*; §4.1 says only its date part takes part in the
#: comparison, because it is derived from ``datetime('now')``.
DUE_AT_DATE_LENGTH = 10


def _placeholder_for(column):
    return PLACEHOLDER_FIELDS.get(column)


def _normalise_row(row, columns):
    """Replace the volatile fields of one row with their placeholders."""
    out = {}
    for column in columns:
        value = row.get(column)
        if column == "due_at" and isinstance(value, str):
            # §4.1: only the date part participates.
            value = value[:DUE_AT_DATE_LENGTH]
        elif column == "items_json" and isinstance(value, str):
            value = _normalise_items_json(value)
        placeholder = _placeholder_for(column)
        if placeholder is not None and value is not None:
            value = placeholder
        out[column] = value
    return out


def _normalise_items_json(raw):
    """§4.2 — normalise the archived run's item list.

    The random request id and the wall-clock fields are replaced; the draft
    sequence is **kept** (it counts the draft writes) and the attempt id is
    kept raw so the diff can apply the "only when it varies" rule.
    """
    try:
        items = json.loads(raw)
    except (TypeError, ValueError):
        return raw
    if not isinstance(items, list):
        return raw
    for item in items:
        if not isinstance(item, dict):
            continue
        draft = item.get("draft")
        if isinstance(draft, dict):
            for key in ("request_id", "updated_at", "reference_viewed_at"):
                if key in draft:
                    draft[key] = "<RID>" if key == "request_id" else "<TS>"
            # ``draft_sequence`` stays: it is the draft-write count (§4.2).
    return json.dumps(items, sort_keys=True, ensure_ascii=False)


def _read_table(connection, table, columns, sort_key):
    """Read one table's key columns, normalised and stably ordered."""
    try:
        rows = connection.execute(f"SELECT * FROM {table}").fetchall()
    except sqlite3.OperationalError:
        return []
    records = []
    for row in rows:
        record = dict(row)
        for key in list(record):
            if key not in columns:
                del record[key]
        records.append(_normalise_row(record, columns))
    keys = [part.strip() for part in sort_key.split(",")]
    records.sort(key=lambda row: tuple(str(row.get(key)) for key in keys))
    return records


def read_schema(connection):
    """The pool's schema — G-6's "零新增列" half."""
    rows = connection.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
    return [{"type": row[0], "name": row[1], "sql": row[2]} for row in rows]


def read_row_counts(connection):
    """Every table's row count — G-6's "零新增行" half."""
    names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = {}
    for name in names:
        try:
            counts[name] = connection.execute(
                f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[name] = None
    return counts


def export_pool(pool_path):
    """Export the pool's key columns, schema and row counts.

    The database is opened **read-only**: the export must not be able to
    write to the pool it is describing.
    """
    pool_path = Path(pool_path)
    uri = f"file:{pool_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = {}
        for table, (columns, sort_key) in TABLES.items():
            tables[table] = _read_table(connection, table, columns, sort_key)
        return {
            "pool": str(pool_path),
            "tables": tables,
            "schema": read_schema(connection),
            "row_counts": read_row_counts(connection),
        }
    finally:
        connection.close()


def write_export(export, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for table, rows in export["tables"].items():
        (out_dir / f"db.{table}.json").write_text(
            json.dumps({"table": table, "row_count": len(rows), "rows": rows},
                       ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8")
    (out_dir / "db.schema.json").write_text(
        json.dumps(export["schema"], ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8")
    (out_dir / "db.row_counts.json").write_text(
        json.dumps(export["row_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8")
    # The whole snapshot in one file, so the diff needs one read per side.
    (out_dir / "db.all.json").write_text(
        json.dumps(export, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8")
    return out_dir


# ─────────────────────────────────────────────────────────────────────────
# the diff (§4.4)
# ─────────────────────────────────────────────────────────────────────────


def _row_key(table, row):
    if table in ("problem_attempts", "feedback_events", "practice_runs"):
        return str(row.get("id"))
    if table == "learning_current_state":
        return f"{row.get('item_type')}/{row.get('item_id')}"
    if table == "review_schedule":
        return f"{row.get('item_type')}/{row.get('item_id')}/{row.get('direction')}"
    if table == "problem_progress":
        return str(row.get("problem_id"))
    if table == "learner_signals":
        return str(row.get("signal_id"))
    return json.dumps(row, sort_keys=True, ensure_ascii=False)


def _relax_volatile(before_row, after_row):
    """§4.2 — an attempt id that differs is not a learning fact.

    The rule is "replace it **only when its value varies between the two
    runs**".  So the two rows are compared field by field, and a field
    listed in :data:`VOLATILE_FIELDS` is allowed to differ; the relaxation
    is reported so the diff never hides it.
    """
    relaxed = []
    for field in VOLATILE_FIELDS:
        if field not in before_row and field not in after_row:
            continue
        if before_row.get(field) != after_row.get(field):
            relaxed.append(field)
    if not relaxed:
        return before_row == after_row, []
    left = {key: value for key, value in before_row.items() if key not in relaxed}
    right = {key: value for key, value in after_row.items() if key not in relaxed}
    return left == right, relaxed


def _rows_equal(before_row, after_row):
    """Compare two rows, applying the volatile-field rule (§4.2)."""
    equal, relaxed = _relax_volatile(before_row, after_row)
    if equal:
        return True, relaxed
    # ``items_json`` embeds the archived attempt ids; relax them the same way.
    left = before_row.get("items_json")
    right = after_row.get("items_json")
    if isinstance(left, str) and isinstance(right, str):
        try:
            left_items = json.loads(left)
            right_items = json.loads(right)
        except ValueError:
            return False, relaxed
        if isinstance(left_items, list) and isinstance(right_items, list):
            stripped_left = json.dumps([_strip_attempt_ids(item) for item in left_items],
                                       sort_keys=True, ensure_ascii=False)
            stripped_right = json.dumps([_strip_attempt_ids(item) for item in right_items],
                                        sort_keys=True, ensure_ascii=False)
            if stripped_left == stripped_right:
                return True, relaxed + ["items_json.attempt_id"]
    return False, relaxed


def _strip_attempt_ids(item):
    if not isinstance(item, dict):
        return item
    copy = dict(item)
    if "attempt_id" in copy:
        copy["attempt_id"] = "<AID>"
    return copy


def diff_table(before_rows, after_rows):
    """Compare one table's rows (§4.4)."""
    before = {_row_key("x", row): row for row in before_rows}
    after = {_row_key("x", row): row for row in after_rows}
    changed = []
    relaxed = []
    for key in sorted(set(before) & set(after)):
        equal, freed = _rows_equal(before[key], after[key])
        if not equal:
            changed.append(key)
        elif freed:
            relaxed.append({"row": key, "fields": sorted(freed)})
    only_before = sorted(set(before) - set(after))
    only_after = sorted(set(after) - set(before))
    if not changed and not only_before and not only_after:
        return {"verdict": "PASS", "changed": [], "only_before": [], "only_after": [],
                "relaxed": relaxed}
    if len(before) != len(after):
        reason = f"row count differs: {len(before)} → {len(after)}"
    elif only_before or only_after:
        reason = f"{len(only_before)} row(s) only before, {len(only_after)} only after"
    else:
        reason = f"{len(changed)} row(s) differ"
    return {
        "verdict": "FAIL",
        "reason": reason,
        "changed": sorted(changed),
        "only_before": only_before,
        "only_after": only_after,
        "relaxed": relaxed,
    }


def diff_schema(before_schema, after_schema):
    """G-6 — the pool schema must not change."""
    before = {(row["type"], row["name"]): row["sql"] for row in before_schema}
    after = {(row["type"], row["name"]): row["sql"] for row in after_schema}
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(key for key in set(before) & set(after) if before[key] != after[key])
    if not added and not removed and not changed:
        return {"verdict": "PASS", "added": [], "removed": [], "changed": []}
    return {
        "verdict": "FAIL",
        "reason": (f"{len(added)} object(s) added, {len(removed)} removed, "
                   f"{len(changed)} changed"),
        "added": [list(key) for key in added],
        "removed": [list(key) for key in removed],
        "changed": [list(key) for key in changed],
    }


def diff_row_counts(before_counts, after_counts):
    """G-6 — no table may gain or lose rows."""
    added = {name: after_counts[name] for name in after_counts
             if name not in before_counts}
    removed = {name: before_counts[name] for name in before_counts
               if name not in after_counts}
    changed = {name: (before_counts[name], after_counts[name])
               for name in set(before_counts) & set(after_counts)
               if before_counts[name] != after_counts[name]}
    if not added and not removed and not changed:
        return {"verdict": "PASS", "added": {}, "removed": {}, "changed": {}}
    return {
        "verdict": "FAIL",
        "reason": (f"{len(added)} table(s) added, {len(removed)} removed, "
                   f"{len(changed)} with a different row count"),
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def diff_due(before_due, after_due):
    """G-4 — the due set must be identical (order included)."""
    before = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in before_due]
    after = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in after_due]
    if before == after:
        return {"verdict": "PASS", "count": len(before)}
    return {
        "verdict": "FAIL",
        "reason": f"the due set differs ({len(before)} → {len(after)} items)",
        "only_before": [item for item in before if item not in after],
        "only_after": [item for item in after if item not in before],
    }


def diff_weak(before_weak, after_weak):
    """G-4 — the weak ordering must be identical."""
    before = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in before_weak]
    after = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in after_weak]
    if before == after:
        return {"verdict": "PASS", "count": len(before)}
    return {
        "verdict": "FAIL",
        "reason": f"the weak ordering differs ({len(before)} → {len(after)} items)",
        "only_before": [item for item in before if item not in after],
        "only_after": [item for item in after if item not in before],
    }


# ─────────────────────────────────────────────────────────────────────────
# the gate verdicts
# ─────────────────────────────────────────────────────────────────────────

#: G-2's tables, G-3's tables.
G2_TABLES = ("problem_attempts", "feedback_events", "practice_runs")
G3_TABLES = ("learning_current_state", "review_schedule", "problem_progress", "learner_signals")


def build_gates(before, after, due_before, due_after, weak_before, weak_after):
    """Turn the diffs into the four gate verdicts."""
    tables = {}
    for table in list(G2_TABLES) + list(G3_TABLES):
        tables[table] = diff_table(before["tables"].get(table, []),
                                   after["tables"].get(table, []))

    g2 = {table: tables[table]["verdict"] for table in G2_TABLES}
    g3 = {table: tables[table]["verdict"] for table in G3_TABLES}

    schema = diff_schema(before["schema"], after["schema"])
    counts = diff_row_counts(before["row_counts"], after["row_counts"])
    due = diff_due(due_before, due_after)
    weak = diff_weak(weak_before, weak_after)

    gates = {
        "G-2": {
            "verdict": "PASS" if all(v == "PASS" for v in g2.values()) else "FAIL",
            "tables": g2,
            "detail": tables,
        },
        "G-3": {
            "verdict": "PASS" if all(v == "PASS" for v in g3.values()) else "FAIL",
            "tables": g3,
            "detail": tables,
        },
        "G-4": {
            "verdict": "PASS" if due["verdict"] == "PASS" and weak["verdict"] == "PASS" else "FAIL",
            "due": due,
            "weak": weak,
        },
        "G-6": {
            "verdict": "PASS" if schema["verdict"] == "PASS" and counts["verdict"] == "PASS" else "FAIL",
            "schema": schema,
            "row_counts": counts,
        },
    }
    return gates, tables


def diff_exports(before, after, due_before, due_after, weak_before, weak_after):
    gates, tables = build_gates(before, after, due_before, due_after, weak_before, weak_after)
    return {"gates": gates, "tables": tables}


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Export the pool's key columns and diff two sides.")
    sub = parser.add_subparsers(dest="command", required=True)

    export_parser = sub.add_parser("export", help="export one side's pool snapshot")
    export_parser.add_argument("--pool", required=True, help="the pool copy to read (read-only)")
    export_parser.add_argument("--out", required=True, help="output directory")

    diff_parser = sub.add_parser("diff", help="diff two exported snapshots")
    diff_parser.add_argument("--before", required=True, help="before export directory")
    diff_parser.add_argument("--after", required=True, help="after export directory")
    diff_parser.add_argument("--due-before", required=True, help="before due.json")
    diff_parser.add_argument("--due-after", required=True, help="after due.json")
    diff_parser.add_argument("--weak-before", required=True, help="before weak.json")
    diff_parser.add_argument("--weak-after", required=True, help="after weak.json")
    diff_parser.add_argument("--out", required=True, help="output directory")

    args = parser.parse_args(argv)

    if args.command == "export":
        export = export_pool(args.pool)
        write_export(export, args.out)
        print(json.dumps({
            "pool": export["pool"],
            "tables": {name: len(rows) for name, rows in export["tables"].items()},
            "schema_objects": len(export["schema"]),
        }, ensure_ascii=False, indent=2))
        return 0

    before = _read_json(Path(args.before) / "db.all.json")
    after = _read_json(Path(args.after) / "db.all.json")
    if before is None or after is None:
        print(json.dumps({"error": "missing db.all.json in one of the export directories"},
                         ensure_ascii=False))
        return 1
    result = diff_exports(before, after,
                          _read_json(args.due_before) or [],
                          _read_json(args.due_after) or [],
                          _read_json(args.weak_before) or [],
                          _read_json(args.weak_after) or [])
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "db.diff.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({gate: value["verdict"] for gate, value in result["gates"].items()},
                     ensure_ascii=False, indent=2))
    return 0 if all(value["verdict"] == "PASS" for value in result["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
