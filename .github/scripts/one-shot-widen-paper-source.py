from pathlib import Path

schema_path = Path("pool/scripts/pool_schema.py")
schema = schema_path.read_text(encoding="utf-8")

old_check = "source_kind IN ('quick', 'practice_set', 'agent')"
new_check = "source_kind IN ('paper', 'quick', 'practice_set', 'agent')"
if schema.count(old_check) != 2:
    raise SystemExit(f"expected exactly two legacy practice source checks, got {schema.count(old_check)}")
schema = schema.replace(old_check, new_check)

marker = "def _widen_content_sequences_check(conn, create_sql):\n"
if marker not in schema:
    raise SystemExit("helper insertion marker not found")
helper = '''def _widen_practice_source_kind_check(conn, table):
    """Add canonical Paper execution source without discarding legacy rows."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not row:
        return []
    create_sql = row[0] or ""
    if "'paper'" in create_sql:
        return []
    legacy = "source_kind IN ('quick', 'practice_set', 'agent')"
    if legacy not in create_sql:
        raise sqlite3.OperationalError(
            f"cannot widen {table}.source_kind: unrecognized CHECK constraint"
        )

    old_table = f"{table}_paper_source_old"
    if table_exists(conn, old_table):
        raise sqlite3.OperationalError(
            f"cannot widen {table}.source_kind: stale migration table {old_table} exists"
        )

    widened_sql = create_sql.replace(
        legacy,
        "source_kind IN ('paper', 'quick', 'practice_set', 'agent')",
        1,
    )
    conn.execute(f"ALTER TABLE {table} RENAME TO {old_table}")
    conn.execute(widened_sql)

    old_columns = column_names(conn, old_table)
    new_columns = set(column_names(conn, table))
    common = [column for column in old_columns if column in new_columns]
    quoted = ", ".join(f'"{column}"' for column in common)
    conn.execute(
        f"INSERT INTO {table} ({quoted}) SELECT {quoted} FROM {old_table}"
    )
    conn.execute(f"DROP TABLE {old_table}")
    return [f"{table}.source_kind-paper"]


'''
schema = schema.replace(marker, helper + marker, 1)

active_marker = '''    changes.extend(
        ensure_columns(conn, "active_practice", [("source_label", "TEXT")])
    )
'''
if schema.count(active_marker) != 1:
    raise SystemExit("active_practice widening insertion point not found exactly once")
schema = schema.replace(
    active_marker,
    active_marker + '    changes.extend(_widen_practice_source_kind_check(conn, "active_practice"))\n',
    1,
)

runs_marker = '''        changes.append("practice_runs")

    if not table_exists(conn, "learning_current_state"):
'''
if schema.count(runs_marker) != 1:
    raise SystemExit("practice_runs widening insertion point not found exactly once")
schema = schema.replace(
    runs_marker,
    '''        changes.append("practice_runs")
    changes.extend(_widen_practice_source_kind_check(conn, "practice_runs"))

    if not table_exists(conn, "learning_current_state"):
''',
    1,
)

schema_path.write_text(schema, encoding="utf-8")

test_path = Path("tests/workbench/test_paper_source_schema.py")
test_path.write_text('''import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import load_script


class PaperSourceSchemaTests(unittest.TestCase):
    def test_legacy_execution_tables_are_widened_without_losing_rows(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(
                """
                CREATE TABLE active_practice (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    source_kind TEXT NOT NULL CHECK (
                        source_kind IN ('quick', 'practice_set', 'agent')
                    ),
                    source_ref TEXT,
                    source_label TEXT,
                    kp_ids_json TEXT NOT NULL DEFAULT '[]',
                    practice_mode TEXT NOT NULL,
                    rating_mode TEXT NOT NULL,
                    cursor INTEGER NOT NULL DEFAULT 0 CHECK (cursor >= 0),
                    started_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE practice_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_kind TEXT NOT NULL CHECK (
                        source_kind IN ('quick', 'practice_set', 'agent')
                    ),
                    source_ref TEXT,
                    source_label TEXT,
                    kp_ids_json TEXT NOT NULL DEFAULT '[]',
                    practice_mode TEXT NOT NULL,
                    rating_mode TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('completed', 'abandoned')),
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO active_practice
                    (singleton, source_kind, kp_ids_json, practice_mode, rating_mode)
                    VALUES (1, 'quick', '[]', 'exam', 'immediate');
                INSERT INTO practice_runs
                    (source_kind, kp_ids_json, practice_mode, rating_mode, items_json,
                     status, started_at)
                    VALUES ('practice_set', '[]', 'exam', 'immediate', '[]',
                            'completed', datetime('now'));
                """
            )
            schema = load_script(
                "pool_schema_paper_source_test", Path("pool/scripts/pool_schema.py")
            )
            changes = schema.ensure_workbench_schema(conn)

            self.assertIn("active_practice.source_kind-paper", changes)
            self.assertIn("practice_runs.source_kind-paper", changes)
            self.assertEqual(
                conn.execute("SELECT source_kind FROM active_practice").fetchone()[0],
                "quick",
            )
            self.assertEqual(
                conn.execute("SELECT source_kind FROM practice_runs").fetchone()[0],
                "practice_set",
            )

            conn.execute("UPDATE active_practice SET source_kind='paper'")
            conn.execute("UPDATE practice_runs SET source_kind='paper'")
            self.assertEqual(
                conn.execute("SELECT source_kind FROM active_practice").fetchone()[0],
                "paper",
            )
            self.assertEqual(
                conn.execute("SELECT source_kind FROM practice_runs").fetchone()[0],
                "paper",
            )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

Path(".github/workflows/one-shot-widen-paper-source.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-widen-paper-source.py").unlink()
