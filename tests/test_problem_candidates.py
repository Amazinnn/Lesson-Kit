import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "pool" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("candidate_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script("candidate_create_tables", Path("pipeline/scripts/create-tables.py"))
migrate_progress = load_script("candidate_migrate_progress", Path("pool/scripts/migrate-progress.py"))


class ProblemCandidateSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT NOT NULL
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT,
                problem_type TEXT NOT NULL,
                source_kind TEXT NOT NULL
            );
            INSERT INTO knowledge_points VALUES (
                'dmath-ch06-kp-001', 'Product rule'
            );
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def test_candidate_schema_migration_is_complete_and_idempotent(self):
        conn = self.connect()
        try:
            first = pool_schema.ensure_problem_candidate_schema(conn)
            conn.commit()
            second = pool_schema.ensure_problem_candidate_schema(conn)
            conn.commit()

            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            candidate_columns = set(pool_schema.column_names(conn, "candidate_problems"))
            attempt_columns = set(pool_schema.column_names(conn, "candidate_attempts"))
            signal_columns = set(pool_schema.column_names(conn, "learner_signals"))
            indexes = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
        finally:
            conn.close()

        self.assertEqual(
            first,
            ["candidate_problems", "candidate_attempts", "learner_signals"],
        )
        self.assertEqual(second, [])
        self.assertTrue(
            {"candidate_problems", "candidate_attempts", "learner_signals"}
            <= tables
        )
        self.assertTrue(
            {
                "candidate_id",
                "kp_ids",
                "problem_text",
                "options_json",
                "correct_option_id",
                "solution",
                "problem_type",
                "interaction_type",
                "generation_purpose",
                "origin_kind",
                "source_kind",
                "source_evidence_json",
                "status",
                "structure_gate_status",
                "audit_gate_status",
                "gate_report",
                "imported_problem_id",
                "created_at",
                "updated_at",
            }
            <= candidate_columns
        )
        self.assertTrue(
            {
                "id",
                "candidate_id",
                "status",
                "selected_option_id",
                "is_correct",
                "note",
                "created_at",
            }
            <= attempt_columns
        )
        self.assertTrue(
            {
                "signal_id",
                "target_type",
                "target_id",
                "signal_type",
                "weight",
                "evidence_count",
                "note",
                "last_practice_kind",
                "last_practice_ref",
                "created_at",
                "updated_at",
            }
            <= signal_columns
        )
        self.assertTrue(
            {
                "idx_candidate_status",
                "idx_candidate_attempts_candidate_id",
                "idx_learner_signals_target",
                "idx_learner_signals_weight",
            }
            <= indexes
        )

    def test_candidate_schema_rejects_invalid_lifecycle_values(self):
        conn = self.connect()
        try:
            pool_schema.ensure_problem_candidate_schema(conn)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO candidate_problems (
                        candidate_id, kp_ids, problem_text, problem_type,
                        interaction_type, generation_purpose, origin_kind,
                        source_kind, source_evidence_json, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "dmath-ch06-cand-001",
                        '["dmath-ch06-kp-001"]',
                        "Choose the valid count.",
                        "calculation",
                        "multiple_choice",
                        "first_pass_check",
                        "generated_grounded",
                        "textbook",
                        "[]",
                        "draft",
                    ),
                )
        finally:
            conn.close()

    def test_fresh_create_and_existing_pool_migration_include_candidate_tables(self):
        fresh_path = Path(self.tmp.name) / "fresh.db"
        self.assertEqual(create_tables.main(["--db", str(fresh_path)]), 0)

        fresh_conn = sqlite3.connect(fresh_path)
        try:
            fresh_tables = {
                row[0]
                for row in fresh_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            fresh_conn.close()

        changes = migrate_progress.migrate_db(self.db_path)
        migrated_conn = self.connect()
        try:
            migrated_tables = {
                row[0]
                for row in migrated_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            migrated_conn.close()

        expected = {"candidate_problems", "candidate_attempts", "learner_signals"}
        self.assertTrue(expected <= fresh_tables)
        self.assertTrue(expected <= migrated_tables)
        self.assertTrue(expected <= set(changes))


if __name__ == "__main__":
    unittest.main()
