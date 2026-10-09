"""Read-only adapter and the narrow legacy validator typesetting hook."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workbench.domain import typesetting

try:
    from workbench.data import typesetting as typesetting_data
except ImportError:
    typesetting_data = None


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "pipeline" / "scripts" / "validate-pool.py"


class PoolTypesettingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "dmath.db"
        sqlite3.connect(self.db_path).close()

    def tearDown(self):
        self.tmp.cleanup()

    def seed(self, sql):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    def connect_ro(self):
        return sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True)

    def run_validator(self, *options):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--db", str(self.db_path),
             "--course", "dmath", "--chapter", "ch06", *options],
            cwd=self.root, env={**os.environ, "PYTHONUTF8": "1"},
            capture_output=True, text=True, encoding="utf-8")

    def test_adapter_is_scoped_read_only_and_preserves_rows_schema_and_batches(self):
        self.assertIsNotNone(typesetting_data, "read-only typesetting adapter is missing")
        self.seed("""
            CREATE TABLE knowledge_points(kp_id TEXT, body TEXT, fragile TEXT, learning_action TEXT);
            INSERT INTO knowledge_points VALUES('dmath-ch06-kp-001', 'short', 'x', 'x');
            INSERT INTO knowledge_points VALUES('dmath-ch07-kp-001', 'other chapter', NULL, NULL);
            CREATE TABLE ingest_batches(batch_id TEXT);
            INSERT INTO ingest_batches VALUES('batch-001');
        """)
        conn = self.connect_ro()
        try:
            before = list(conn.iterdump())
            changes = conn.total_changes
            conn.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in
                                {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ,
                                 sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_PRAGMA} else sqlite3.SQLITE_DENY)
            rows = typesetting_data.read_rows(conn, "dmath-ch06-")
            self.assertEqual(rows, [{"kp_id": "dmath-ch06-kp-001", "body": "short"}])
            report = typesetting.check(rows)
            self.assertEqual(report["summary"]["knowledge_points"], 1)
            conn.set_authorizer(None)
            self.assertEqual(conn.total_changes, changes)
            self.assertEqual(list(conn.iterdump()), before)
        finally:
            conn.close()

    def test_missing_table_or_body_is_explicitly_unavailable(self):
        self.assertIsNotNone(typesetting_data, "read-only typesetting adapter is missing")
        conn = self.connect_ro()
        try:
            self.assertIsNone(typesetting_data.read_rows(conn))
        finally:
            conn.close()
        self.seed("CREATE TABLE knowledge_points(kp_id TEXT);")
        conn = self.connect_ro()
        try:
            self.assertIsNone(typesetting_data.read_rows(conn))
        finally:
            conn.close()
        result = self.run_validator("--json")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(json.loads(result.stdout)["typesetting"]["available"])

    def test_null_legacy_id_without_course_keeps_schema_errors(self):
        self.seed("CREATE TABLE knowledge_points(kp_id TEXT,body TEXT); "
                  "INSERT INTO knowledge_points VALUES(NULL,'short');")
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--db", str(self.db_path), "--chapter", "ch06", "--json"],
            cwd=self.root, env={**os.environ, "PYTHONUTF8": "1"},
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"]["errors"], 9)
        self.assertEqual(report["summary"]["warnings"], 0)
        self.assertIsNone(report["typesetting"]["short"][0]["kp_id"])

    def test_schema_failure_preserves_original_errors_exit_and_still_reports_body(self):
        self.seed("""
            CREATE TABLE knowledge_points(kp_id TEXT, body TEXT);
            INSERT INTO knowledge_points VALUES('dmath-ch06-kp-001', 'short');
        """)
        before = self.db_path.read_bytes()
        result = self.run_validator("--json")
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"]["errors"], 9)
        self.assertEqual(report["summary"]["warnings"], 0)
        self.assertEqual({row["gate"] for row in report["findings"]}, {"schema-conformance"})
        self.assertIn("typesetting", report)
        self.assertEqual(report["typesetting"]["short"][0]["kp_id"], "dmath-ch06-kp-001")
        text = self.run_validator()
        self.assertEqual(text.returncode, 2, text.stderr)
        self.assertIn(typesetting.render_text(report["typesetting"]), text.stdout)
        self.assertEqual(self.db_path.read_bytes(), before)

    def test_advisories_do_not_change_legacy_pass_or_warning_count(self):
        self.seed("""
            CREATE TABLE knowledge_points(kp_id TEXT, body TEXT, knowledge_item TEXT,
                knowledge_type TEXT, importance TEXT, difficulty INTEGER, fragile TEXT, related_kp_ids TEXT);
            INSERT INTO knowledge_points VALUES('dmath-ch06-kp-001', 'short', 'Concept',
                'concept-property', 'core', NULL, NULL, NULL);
            CREATE TABLE questions(q_id TEXT, kp_id TEXT);
            CREATE TABLE kp_progress(kp_id TEXT);
            CREATE TABLE question_progress(q_id TEXT);
            CREATE TABLE problems(problem_id TEXT, kp_ids TEXT, problem_text TEXT,
                solution TEXT, problem_type TEXT, source_kind TEXT);
            CREATE TABLE problem_progress(problem_id TEXT, status TEXT);
            CREATE TABLE problem_attempts(problem_id TEXT, status TEXT);
            CREATE TABLE candidate_problems(candidate_id TEXT, kp_ids TEXT, options_json TEXT,
                source_evidence_json TEXT, interaction_type TEXT, status TEXT, structure_gate_status TEXT,
                audit_gate_status TEXT, gate_report TEXT, imported_problem_id TEXT);
            CREATE TABLE candidate_attempts(candidate_id TEXT, status TEXT);
            CREATE TABLE learner_signals(signal_id TEXT, target_type TEXT, target_id TEXT);
        """)
        result = self.run_validator("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"], {"errors": 0, "warnings": 1, "status": "PASS"})
        self.assertEqual(report["typesetting"]["summary"]["short"]["knowledge_points"], 1)

    def test_standalone_validator_imports_helpers_from_its_own_checkout(self):
        code = """
import json, runpy, sqlite3, sys
namespace = runpy.run_path(sys.argv[1])
assert '_run_typesetting_check' in namespace, 'typesetting hook is missing'
conn = sqlite3.connect(':memory:')
try:
    namespace['_run_typesetting_check'](conn, '', '')
finally:
    conn.close()
print(json.dumps([sys.modules[name].__file__ for name in
                  ('workbench.domain.typesetting', 'workbench.data.typesetting')]))
"""
        result = subprocess.run([sys.executable, "-c", code, str(VALIDATOR)],
                                cwd=self.root, env={**os.environ, "PYTHONUTF8": "1"},
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([Path(path).resolve() for path in json.loads(result.stdout)],
                         [REPO_ROOT / "workbench/domain/typesetting.py",
                          REPO_ROOT / "workbench/data/typesetting.py"])

    def test_missing_db_invocation_exit_is_unchanged(self):
        result = subprocess.run([sys.executable, str(VALIDATOR), "--db",
                                 str(self.root / "missing.db"), "--chapter", "ch06"],
                                cwd=self.root, env={**os.environ, "PYTHONUTF8": "1"},
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1)
        self.assertIn("DB not found", result.stderr)
