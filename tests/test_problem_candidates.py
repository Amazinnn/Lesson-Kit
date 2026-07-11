import importlib.util
import json
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


class ProblemCandidateWorkflowTests(unittest.TestCase):
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
        pool_schema.ensure_problem_candidate_schema(conn)
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def write_json(self, name, payload):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def candidate(self, **overrides):
        row = {
            "candidate_id": "dmath-ch06-cand-001",
            "kp_ids": ["dmath-ch06-kp-001"],
            "problem_text": "A task has three independent stages.\n\nHow many outcomes are possible?",
            "options": [
                {
                    "id": "A",
                    "text": "$3$",
                    "explanation": "This counts stages, not choices.",
                },
                {
                    "id": "B",
                    "text": "$2^3$",
                    "explanation": "Each of three stages has two choices.",
                },
            ],
            "correct_option_id": "B",
            "solution": "The choices are independent, so the product rule gives $2^3=8$.",
            "problem_type": "calculation",
            "interaction_type": "single_choice",
            "generation_purpose": "first_pass_check",
            "origin_kind": "generated_grounded",
            "source_kind": "textbook",
            "source_evidence": [
                {
                    "source": "Discrete Mathematics Chapter 6.md",
                    "location": "Section 6.1, product rule",
                    "basis": "The source states that independent stage counts multiply.",
                }
            ],
        }
        row.update(overrides)
        return row

    def manifest(self, candidates=None):
        return {
            "metadata": {"course": "dmath", "chapter": "ch06"},
            "candidates": candidates or [self.candidate()],
        }

    def insert_candidate(self, candidate=None, gate=True):
        insert_candidates = load_script(
            f"insert_candidates_helper_{id(self)}", Path("pipeline/scripts/insert-candidates.py")
        )
        payload = self.manifest([candidate or self.candidate()])
        manifest_path = self.write_json("candidate-helper.json", payload)
        self.assertEqual(
            insert_candidates.insert_candidates(self.db_path, manifest_path),
            (1, 0, []),
        )
        if not gate:
            return
        candidate_id = payload["candidates"][0]["candidate_id"]
        gate_candidates = load_script(
            f"gate_candidates_helper_{id(self)}", Path("pipeline/scripts/gate-candidates.py")
        )
        audit_path = self.write_json(
            "audit-helper.json",
            {
                "audits": [
                    {
                        "candidate_id": candidate_id,
                        "status": "PASS",
                        "checks": {
                            "source_grounding": "PASS",
                            "answer_correctness": "PASS",
                            "training_usefulness": "PASS",
                            "option_plausibility": "PASS",
                        },
                        "summary": "Verified for workflow test.",
                    }
                ]
            },
        )
        self.assertEqual(
            gate_candidates.gate_candidates(self.db_path, audit_path),
            (1, 0, []),
        )

    def test_insert_candidates_persists_valid_source_grounded_draft(self):
        insert_candidates = load_script(
            "insert_candidates_test", Path("pipeline/scripts/insert-candidates.py")
        )
        manifest_path = self.write_json("candidates.json", self.manifest())

        result = insert_candidates.insert_candidates(self.db_path, manifest_path)

        self.assertEqual(result, (1, 0, []))
        conn = self.connect()
        try:
            row = conn.execute(
                """
                SELECT candidate_id, options_json, source_evidence_json, status,
                       structure_gate_status, audit_gate_status
                FROM candidate_problems
                """
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(row[0], "dmath-ch06-cand-001")
        self.assertEqual(json.loads(row[1])[1]["id"], "B")
        self.assertEqual(json.loads(row[2])[0]["location"], "Section 6.1, product rule")
        self.assertEqual(row[3:], ("draft", "pending", "pending"))

    def test_candidate_json_entry_points_reject_non_object_roots(self):
        insert_candidates = load_script(
            "insert_candidates_root_test", Path("pipeline/scripts/insert-candidates.py")
        )
        gate_candidates = load_script(
            "gate_candidates_root_test", Path("pipeline/scripts/gate-candidates.py")
        )
        manifest_path = self.write_json("root-list.json", [])
        audit_path = self.write_json("audit-root-list.json", [])

        self.assertEqual(
            insert_candidates.insert_candidates(self.db_path, manifest_path),
            (0, 0, ["manifest root must be an object"]),
        )
        self.assertEqual(
            gate_candidates.gate_candidates(self.db_path, audit_path),
            (0, 0, ["audit report root must be an object"]),
        )

        bad_metadata_path = self.write_json(
            "bad-metadata.json",
            {"metadata": [], "candidates": []},
        )
        self.assertEqual(
            insert_candidates.insert_candidates(self.db_path, bad_metadata_path),
            (0, 0, ["manifest metadata must be an object"]),
        )

    def test_insert_candidates_rejects_bad_ids_links_shapes_and_evidence(self):
        insert_candidates = load_script(
            "insert_candidates_invalid_test", Path("pipeline/scripts/insert-candidates.py")
        )
        invalid = [
            self.candidate(candidate_id="wrong-id"),
            self.candidate(
                candidate_id="dmath-ch06-cand-002",
                kp_ids=["dmath-ch06-kp-999"],
            ),
            self.candidate(
                candidate_id="dmath-ch06-cand-003",
                correct_option_id="Z",
            ),
            self.candidate(
                candidate_id="dmath-ch06-cand-004",
                source_evidence=[],
            ),
            self.candidate(
                candidate_id="dmath-ch06-cand-005",
                problem_text="Collapsed stem a) first b) second",
            ),
        ]
        manifest_path = self.write_json("invalid.json", self.manifest(invalid))

        inserted, skipped, errors = insert_candidates.insert_candidates(
            self.db_path, manifest_path
        )

        self.assertEqual((inserted, skipped), (0, 0))
        self.assertGreaterEqual(len(errors), 5)
        joined = "\n".join(errors)
        self.assertIn("invalid candidate_id", joined)
        self.assertIn("unknown kp_id", joined)
        self.assertIn("correct_option_id", joined)
        self.assertIn("source_evidence", joined)
        self.assertIn("collapsed subparts", joined)

    def test_remediation_wrong_options_require_structured_error_lures(self):
        insert_candidates = load_script(
            "insert_candidates_lure_test", Path("pipeline/scripts/insert-candidates.py")
        )
        candidate = self.candidate(
            generation_purpose="remediation",
            options=[
                {
                    "id": "A",
                    "text": "$3$",
                    "explanation": "Counts stages only.",
                },
                {
                    "id": "B",
                    "text": "$8$",
                    "explanation": "Uses the product rule.",
                },
            ],
        )
        manifest_path = self.write_json("lure.json", self.manifest([candidate]))

        _inserted, _skipped, errors = insert_candidates.insert_candidates(
            self.db_path, manifest_path
        )

        self.assertIn("error_lure", "\n".join(errors))

    def test_double_gate_is_required_for_gate_passed_status(self):
        insert_candidates = load_script(
            "insert_candidates_gate_test", Path("pipeline/scripts/insert-candidates.py")
        )
        gate_candidates = load_script(
            "gate_candidates_test", Path("pipeline/scripts/gate-candidates.py")
        )
        manifest_path = self.write_json("candidates.json", self.manifest())
        self.assertEqual(
            insert_candidates.insert_candidates(self.db_path, manifest_path),
            (1, 0, []),
        )
        audit_path = self.write_json(
            "audit.json",
            {
                "audits": [
                    {
                        "candidate_id": "dmath-ch06-cand-001",
                        "status": "PASS",
                        "checks": {
                            "source_grounding": "PASS",
                            "answer_correctness": "PASS",
                            "training_usefulness": "PASS",
                            "option_plausibility": "PASS",
                        },
                        "summary": "Grounded and suitable for a first-pass check.",
                    }
                ]
            },
        )

        self.assertEqual(
            gate_candidates.gate_candidates(self.db_path, audit_path),
            (1, 0, []),
        )

        conn = self.connect()
        try:
            state = conn.execute(
                """
                SELECT status, structure_gate_status, audit_gate_status, gate_report
                FROM candidate_problems WHERE candidate_id = ?
                """,
                ("dmath-ch06-cand-001",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(state[:3], ("gate_passed", "pass", "pass"))
        self.assertEqual(
            json.loads(state[3])["audit"]["summary"],
            "Grounded and suitable for a first-pass check.",
        )

    def test_failed_semantic_audit_marks_candidate_for_revision(self):
        insert_candidates = load_script(
            "insert_candidates_failed_gate_test", Path("pipeline/scripts/insert-candidates.py")
        )
        gate_candidates = load_script(
            "gate_candidates_failed_test", Path("pipeline/scripts/gate-candidates.py")
        )
        manifest_path = self.write_json("candidates.json", self.manifest())
        insert_candidates.insert_candidates(self.db_path, manifest_path)
        audit_path = self.write_json(
            "audit-fail.json",
            {
                "audits": [
                    {
                        "candidate_id": "dmath-ch06-cand-001",
                        "status": "FAIL",
                        "checks": {
                            "source_grounding": "PASS",
                            "answer_correctness": "FAIL",
                            "training_usefulness": "PASS",
                            "option_plausibility": "PASS",
                        },
                        "summary": "The keyed answer is not justified.",
                    }
                ]
            },
        )

        self.assertEqual(
            gate_candidates.gate_candidates(self.db_path, audit_path),
            (0, 1, []),
        )
        conn = self.connect()
        try:
            state = conn.execute(
                """
                SELECT status, structure_gate_status, audit_gate_status
                FROM candidate_problems
                """
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(state, ("needs_revision", "pass", "fail"))

    def test_candidate_attempt_requires_gate_passed_and_is_append_only(self):
        practice = load_script(
            "practice_candidates_eligibility_test",
            Path("pool/scripts/practice-candidates.py"),
        )
        self.insert_candidate(gate=False)
        with self.assertRaisesRegex(ValueError, "not eligible"):
            practice.record_candidate_attempt(
                self.db_path,
                "dmath-ch06-cand-001",
                "wrong",
                "A",
                "counted stages",
            )

        conn = self.connect()
        try:
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = 'gate_passed', structure_gate_status = 'pass',
                    audit_gate_status = 'pass'
                WHERE candidate_id = 'dmath-ch06-cand-001'
                """
            )
            conn.commit()
        finally:
            conn.close()

        first = practice.record_candidate_attempt(
            self.db_path,
            "dmath-ch06-cand-001",
            "wrong",
            "A",
            "counted stages",
        )
        second = practice.record_candidate_attempt(
            self.db_path,
            "dmath-ch06-cand-001",
            "mastered",
            "B",
            "clean retry",
        )

        self.assertFalse(first["is_correct"])
        self.assertTrue(second["is_correct"])
        conn = self.connect()
        try:
            attempts = conn.execute(
                """
                SELECT status, selected_option_id, is_correct, note
                FROM candidate_attempts ORDER BY id
                """
            ).fetchall()
        finally:
            conn.close()
        self.assertEqual(
            attempts,
            [
                ("wrong", "A", 0, "counted stages"),
                ("mastered", "B", 1, "clean retry"),
            ],
        )

    def test_candidate_cli_normalizes_powershell_bom_input(self):
        practice = load_script(
            "practice_candidates_bom_test",
            Path("pool/scripts/practice-candidates.py"),
        )

        self.assertEqual(practice.normalize_cli_input("\ufeffA"), "A")

    def test_candidate_session_rejects_missing_db_and_candidate_ids(self):
        practice = load_script(
            "practice_candidates_scope_test",
            Path("pool/scripts/practice-candidates.py"),
        )
        missing_db = Path(self.tmp.name) / "missing.db"

        with self.assertRaises(FileNotFoundError):
            practice.eligible_candidates(missing_db, None)
        self.assertFalse(missing_db.exists())

        with self.assertRaisesRegex(ValueError, "candidate not found"):
            practice.eligible_candidates(
                self.db_path,
                ["dmath-ch06-cand-999"],
            )

    def test_signal_upsert_returns_existing_canonical_signal_id(self):
        learner_signals = load_script(
            "learner_signals_existing_id_test",
            Path("pool/scripts/learner_signals.py"),
        )
        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO learner_signals (
                    signal_id, target_type, target_id, signal_type,
                    weight, evidence_count, last_practice_kind
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "sig:human-readable",
                    "node",
                    "dmath-ch06-kp-001",
                    "weak_node",
                    "medium",
                    1,
                    "reflection",
                ),
            )
            returned_id = learner_signals.upsert_learner_signal(
                conn,
                "node",
                "dmath-ch06-kp-001",
                "weak_node",
                "practice miss",
                "candidate",
                "dmath-ch06-cand-001",
            )
            conn.commit()
        finally:
            conn.close()

        self.assertEqual(returned_id, "sig:human-readable")

    def test_wrong_candidate_attempt_strengthens_default_weak_node_signal(self):
        practice = load_script(
            "practice_candidates_signal_test",
            Path("pool/scripts/practice-candidates.py"),
        )
        self.insert_candidate()

        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "wrong", "A", "first miss"
        )
        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "stuck", None, "still unsure"
        )
        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "mastered", "B", "later success"
        )

        conn = self.connect()
        try:
            signal = conn.execute(
                """
                SELECT target_type, target_id, signal_type, weight,
                       evidence_count, note, last_practice_kind, last_practice_ref
                FROM learner_signals
                """
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(signal[:5], (
            "node", "dmath-ch06-kp-001", "weak_node", "high", 2
        ))
        self.assertEqual(signal[5:], (
            "still unsure", "candidate", "dmath-ch06-cand-001"
        ))

    def test_selected_remediation_lure_creates_specific_signal(self):
        practice = load_script(
            "practice_candidates_lure_signal_test",
            Path("pool/scripts/practice-candidates.py"),
        )
        candidate = self.candidate(
            generation_purpose="remediation",
            options=[
                {
                    "id": "A",
                    "text": "$3$",
                    "explanation": "Counts stages only.",
                    "error_lure": {
                        "signal_type": "confusion",
                        "target_type": "node",
                        "target_id": "dmath-ch06-kp-001",
                        "note": "Confuses number of stages with number of outcomes.",
                    },
                },
                {
                    "id": "B",
                    "text": "$8$",
                    "explanation": "Uses the product rule.",
                },
            ],
        )
        self.insert_candidate(candidate)

        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "wrong", "A", "chose stage count"
        )

        conn = self.connect()
        try:
            signals = conn.execute(
                """
                SELECT signal_type, weight, evidence_count, note
                FROM learner_signals ORDER BY signal_type
                """
            ).fetchall()
        finally:
            conn.close()
        self.assertEqual(
            signals,
            [
                (
                    "confusion",
                    "medium",
                    1,
                    "Confuses number of stages with number of outcomes.",
                ),
                ("weak_node", "medium", 1, "chose stage count"),
            ],
        )

    def test_import_renders_official_problem_and_migrates_attempt_summary(self):
        practice = load_script(
            "practice_candidates_import_test",
            Path("pool/scripts/practice-candidates.py"),
        )
        import_candidates = load_script(
            "import_candidates_test",
            Path("pipeline/scripts/import-candidates.py"),
        )
        self.insert_candidate()
        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "wrong", "A", "counted stages"
        )
        practice.record_candidate_attempt(
            self.db_path, "dmath-ch06-cand-001", "mastered", "B", "clean retry"
        )

        imported, warnings, errors = import_candidates.import_candidates(
            self.db_path, ["dmath-ch06-cand-001"]
        )

        self.assertEqual(imported, ["dmath-ch06-prob-001"])
        self.assertEqual(warnings, [])
        self.assertEqual(errors, [])
        conn = self.connect()
        try:
            problem = conn.execute(
                """
                SELECT problem_id, kp_ids, problem_text, solution,
                       problem_type, source_kind
                FROM problems
                """
            ).fetchone()
            candidate_state = conn.execute(
                """
                SELECT status, imported_problem_id FROM candidate_problems
                WHERE candidate_id = 'dmath-ch06-cand-001'
                """
            ).fetchone()
            progress = conn.execute(
                "SELECT status, note FROM problem_progress WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchone()
            attempts = conn.execute(
                "SELECT status, note FROM problem_attempts WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual(problem[0], "dmath-ch06-prob-001")
        self.assertEqual(json.loads(problem[1]), ["dmath-ch06-kp-001"])
        self.assertIn("\n\nA. $3$\n\nB. $2^3$", problem[2])
        self.assertIn("Correct answer: B", problem[3])
        self.assertIn("A. This counts stages, not choices.", problem[3])
        self.assertEqual(problem[4:], ("calculation", "textbook"))
        self.assertEqual(candidate_state, ("imported", "dmath-ch06-prob-001"))
        self.assertEqual(progress[0], "mastered")
        self.assertIn("2 attempts", progress[1])
        self.assertIn("wrong/stuck: 1", progress[1])
        self.assertEqual(attempts, [("mastered", progress[1])])

        second = import_candidates.import_candidates(
            self.db_path, ["dmath-ch06-cand-001"]
        )
        self.assertEqual(second[0], [])
        self.assertIn("already imported", "\n".join(second[1]))
        self.assertEqual(second[2], [])

    def test_import_requires_double_pass_and_blocks_same_kp_near_duplicates(self):
        import_candidates = load_script(
            "import_candidates_gate_duplicate_test",
            Path("pipeline/scripts/import-candidates.py"),
        )
        self.insert_candidate(gate=False)

        blocked = import_candidates.import_candidates(
            self.db_path, ["dmath-ch06-cand-001"]
        )
        self.assertEqual(blocked[0], [])
        self.assertIn("double PASS", "\n".join(blocked[2]))

        conn = self.connect()
        try:
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = 'gate_passed', structure_gate_status = 'pass',
                    audit_gate_status = 'pass'
                WHERE candidate_id = 'dmath-ch06-cand-001'
                """
            )
            conn.execute(
                """
                INSERT INTO problems (
                    problem_id, kp_ids, problem_text, solution,
                    problem_type, source_kind
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "dmath-ch06-prob-004",
                    '["dmath-ch06-kp-001"]',
                    "A task has three independent stages. How many outcomes are possible?",
                    "Eight.",
                    "calculation",
                    "textbook",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        duplicate = import_candidates.import_candidates(
            self.db_path, ["dmath-ch06-cand-001"]
        )
        self.assertEqual(duplicate[0], [])
        self.assertIn("near-duplicate", "\n".join(duplicate[2]))

    def test_pool_validator_reports_candidate_lifecycle_and_signal_target_errors(self):
        validate_pool = load_script(
            "validate_pool_candidates_test",
            Path("pipeline/scripts/validate-pool.py"),
        )
        self.insert_candidate(gate=False)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = 'gate_passed', structure_gate_status = 'pending',
                    audit_gate_status = 'pass'
                WHERE candidate_id = 'dmath-ch06-cand-001'
                """
            )
            conn.execute(
                """
                INSERT INTO learner_signals (
                    signal_id, target_type, target_id, signal_type, weight,
                    evidence_count, last_practice_kind
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "sig:missing-node",
                    "node",
                    "dmath-ch06-kp-999",
                    "weak_node",
                    "medium",
                    1,
                    "candidate",
                ),
            )
            conn.commit()
            findings = validate_pool.run_candidate_gates(
                conn,
                "dmath-ch06-",
                {"dmath-ch06-kp-001"},
                set(),
            )
        finally:
            conn.close()

        messages = "\n".join(item["message"] for item in findings)
        self.assertIn("gate_passed requires structure and audit PASS", messages)
        self.assertIn("signal target node does not exist", messages)

    def test_pool_validator_reports_imported_candidate_with_missing_problem(self):
        validate_pool = load_script(
            "validate_pool_imported_candidate_test",
            Path("pipeline/scripts/validate-pool.py"),
        )
        self.insert_candidate(gate=False)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute(
                """
                UPDATE candidate_problems
                SET status = 'imported', structure_gate_status = 'pass',
                    audit_gate_status = 'pass',
                    imported_problem_id = 'dmath-ch06-prob-999'
                WHERE candidate_id = 'dmath-ch06-cand-001'
                """
            )
            conn.commit()
            findings = validate_pool.run_candidate_gates(
                conn,
                "dmath-ch06-",
                {"dmath-ch06-kp-001"},
                set(),
            )
        finally:
            conn.close()

        self.assertIn(
            "imported_problem_id references missing problem",
            "\n".join(item["message"] for item in findings),
        )


if __name__ == "__main__":
    unittest.main()
