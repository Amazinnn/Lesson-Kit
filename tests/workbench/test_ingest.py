"""File-artifact ingestion contracts (TDD: red before implementation)."""

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


try:
    from workbench import ingest
except ImportError:
    ingest = None


DIMENSIONS = (
    "source_consistency", "meaning", "formatting", "knowledge_point_mapping",
    "answer_correctness", "solution_completeness",
)

KP_DIMENSIONS = (
    "source_consistency", "meaning", "formatting", "relationship_mapping",
    "uniqueness", "completeness",
)


def audit_item(source, problem, solution):
    return {
        "source": source, "problem": problem, "solution": solution,
        "decisions": {dimension: "PASS" for dimension in DIMENSIONS},
    }


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, knowledge_item TEXT);
            CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT NOT NULL, solution TEXT);
            CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY, problem_text TEXT);
            CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY, source_kp_id TEXT, target_kp_id TEXT);
            CREATE VIEW problem_view AS SELECT problem_id, problem_text, solution FROM problems;
        """)
        conn.execute("INSERT INTO knowledge_points VALUES ('kp-1', 'Counting')")
        conn.executemany(
            "INSERT INTO problems VALUES (?, ?, ?)",
            [("p-1", "Let x<sup>2</sup> = 1.", "old one"), ("p-2", "Count two choices.", "old two")],
        )
        conn.execute("INSERT INTO candidate_problems VALUES ('c-1', 'Candidate question')")
        conn.execute("INSERT INTO knowledge_relations VALUES ('r-1', 'kp-1', 'kp-1')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def artifact(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def snapshot(self, path=None):
        conn = sqlite3.connect(path or self.db_path)
        try:
            objects = conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE type IN ('table', 'view', 'trigger') ORDER BY type, name"
            ).fetchall()
            rows = {}
            for object_type, name, *_ in objects:
                if object_type == "table":
                    rows[name] = conn.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall()
            return {"objects": objects, "rows": rows}
        finally:
            conn.close()

    def qualified_files(self):
        solutions = self.artifact("solutions.json", {
            "kind": "solutions", "provider": "codex", "provider_session_id": "solution-session",
            "items": [
                {"source": "Let x<sup>2</sup> = 1.", "problem": "p-1", "solution": "x is 1 or -1."},
                {"source": "Count two choices.", "problem": "p-2", "solution": "There are four pairs."},
            ],
        })
        audits = self.artifact("audit.json", {
            "kind": "audit", "provider": "claude", "provider_session_id": "audit-session",
            "items": [
                audit_item("Let x<sup>2</sup> = 1.", "p-1", "x is 1 or -1."),
                audit_item("Count two choices.", "p-2", "There are four pairs."),
            ],
        })
        return solutions, audits

    def test_prepare_writes_resumable_utf8_task_without_provider(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        source = self.artifact("source.json", {"items": [{"problem_id": "p-1", "problem_text": "组合"}]})
        task = self.root / "task.json"

        result = ingest.prepare("problem-solutions", source, task)

        self.assertEqual(result["kind"], "ingest-task")
        self.assertEqual(result["items"], [{"source": "组合", "problem": "p-1"}])
        self.assertEqual(json.loads(task.read_text(encoding="utf-8")), result)

    def test_run_uses_only_explicit_path_provider_and_records_native_session(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        task = self.artifact("task.json", {"kind": "ingest-task", "operation": "problem-solutions", "items": []})
        output = self.root / "solutions.json"
        provider = {"name": "codex", "command": "codex", "args": [], "timeout_s": 30}
        stdout = "\n".join((
            '{"type":"thread.started","thread_id":"native-session"}',
            '{"type":"item.completed","item":{"type":"agent_message","text":"{\\"kind\\":\\"solutions\\",\\"items\\":[]}"}}',
        ))
        with patch("workbench.ingest.conversation_providers.get", return_value=provider) as get_provider, patch(
            "workbench.ingest.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=stdout)
        ):
            result = ingest.run(task, output, "codex", self.root)

        self.assertEqual(result["provider_session_id"], "native-session")
        self.assertEqual(result["provider"], "codex")
        get_provider.assert_called_once_with("codex")
        with self.assertRaises(ValueError):
            ingest.run(task, output, None, self.root)

    def test_gate_binds_plain_fields_to_a_fresh_audit_and_active_pool(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        solutions, audits = self.qualified_files()
        report = self.root / "gate.json"

        result = ingest.gate(self.db_path, solutions, audits, report)

        self.assertTrue(result["ok"])
        self.assertEqual(result["accounting"], {"knowledge_points": 1, "problems": 2, "candidate_problems": 1, "knowledge_relations": 1})
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["kind"], "gate-report")

        stale = self.artifact("stale.json", {**json.loads(audits.read_text(encoding="utf-8")), "items": [
            audit_item("changed source", "p-1", "x is 1 or -1."),
            audit_item("Count two choices.", "p-2", "There are four pairs."),
        ]})
        self.assertFalse(ingest.gate(self.db_path, solutions, stale, self.root / "stale-gate.json")["ok"])
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE problems SET problem_text='changed' WHERE problem_id='p-1'")
        conn.commit()
        conn.close()
        self.assertFalse(ingest.gate(self.db_path, solutions, audits, self.root / "db-gate.json")["ok"])

    def test_gate_accepts_per_item_sessions_from_independent_batches(self):
        solution_items = [
            {"source": "Let x<sup>2</sup> = 1.", "problem": "p-1",
             "solution": "x is 1 or -1.", "provider": "codex",
             "provider_session_id": "solve-batch-01"},
            {"source": "Count two choices.", "problem": "p-2",
             "solution": "There are four pairs.", "provider": "codex",
             "provider_session_id": "solve-batch-02"},
        ]
        audit_items = [
            {**audit_item(item["source"], item["problem"], item["solution"]),
             "provider": "codex", "provider_session_id": "audit-" + item["problem"]}
            for item in solution_items
        ]
        solutions = self.artifact("batch-solutions.json", {
            "kind": "solutions", "items": solution_items,
        })
        audits = self.artifact("batch-audits.json", {"kind": "audit", "items": audit_items})

        result = ingest.gate(self.db_path, solutions, audits, self.root / "batch-gate.json")

        self.assertTrue(result["ok"], result["errors"])
        audit_items[0]["provider_session_id"] = "solve-batch-01"
        same_session = self.artifact("same-session-audits.json", {
            "kind": "audit", "items": audit_items,
        })
        rejected = ingest.gate(
            self.db_path, solutions, same_session, self.root / "same-session-gate.json",
        )
        self.assertFalse(rejected["ok"])

    def test_gate_rejects_solution_markup_ocr_damage_and_unterminated_html(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        for source, solution in (
            ("plain", "in<sub></sub>valid"),
            ("plain", "in<sup>2</sup>valid"),
            ("plain", "x<sub>2</sub>y"),
            ("plain", "<em>unknown</em>"),
            ("plain", "broken <em"),
            ("plain", "x \ufffd y"),
        ):
            with self.subTest(solution=solution):
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE problems SET problem_text=? WHERE problem_id='p-1'", (source,))
                conn.commit()
                conn.close()
                solutions = self.artifact("bad-solutions.json", {"kind": "solutions", "provider": "codex", "provider_session_id": "s1", "items": [{"source": source, "problem": "p-1", "solution": solution}]})
                audits = self.artifact("bad-audit.json", {"kind": "audit", "provider": "claude", "provider_session_id": "s2", "items": [audit_item(source, "p-1", solution)]})
                self.assertFalse(ingest.gate(self.db_path, solutions, audits, self.root / "bad-gate.json")["ok"])

        self.assertEqual(ingest.render_text("x < 3 and <sup>n & m</sup>"), "x &lt; 3 and <sup>n &amp; m</sup>")
        self.assertEqual(
            ingest.render_text("j<i, a_j>a_i, and 0\\le k<n"),
            "j&lt;i, a_j&gt;a_i, and 0\\le k&lt;n",
        )

    def test_render_writes_a_resumable_utf8_artifact(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        source = self.artifact("render-source.json", {
            "kind": "solutions", "items": [
                {"source": "x < 3", "problem": "p-1", "solution": "x<sup>2</sup> & y"},
            ],
        })
        output = self.root / "rendered.json"

        result = ingest.render(source, output)

        self.assertEqual(result["items"][0]["rendered_source"], "x &lt; 3")
        self.assertEqual(result["items"][0]["rendered_solution"], "x<sup>2</sup> &amp; y")
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_recipe_is_file_based_zero_write_and_accounts_all_entity_types(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        source = self.artifact("input.json", {"items": []})
        before = self.snapshot()
        for name in ("knowledge", "problems", "candidates", "views"):
            with self.subTest(recipe=name):
                result = ingest.recipe(name, self.db_path, source, self.root / name)
                self.assertFalse(result["applied"])
                self.assertTrue((self.root / name / "recipe.json").is_file())
        self.assertEqual(self.snapshot(), before)

    def test_apply_revalidates_under_lock_creates_recoverable_copy_and_rolls_back(self):
        self.assertIsNotNone(ingest, "workbench.ingest is required")
        solutions, audits = self.qualified_files()
        gate_path = self.root / "gate.json"
        ingest.gate(self.db_path, solutions, audits, gate_path)
        backup = self.root / "backup.db"

        result = ingest.apply(self.db_path, gate_path, backup)

        self.assertTrue(result["ok"])
        self.assertEqual(self.snapshot(backup)["rows"]["problems"], [("p-1", "Let x<sup>2</sup> = 1.", "old one"), ("p-2", "Count two choices.", "old two")])
        self.assertEqual(self.snapshot()["rows"]["problems"][0][-1], "x is 1 or -1.")

        self.tearDown()
        self.setUp()
        solutions, audits = self.qualified_files()
        gate_path = self.root / "gate.json"
        ingest.gate(self.db_path, solutions, audits, gate_path)
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TRIGGER reject_p2 BEFORE UPDATE ON problems WHEN NEW.problem_id='p-2' BEGIN SELECT RAISE(ABORT, 'stop'); END;")
        conn.commit()
        conn.close()
        before = self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            ingest.apply(self.db_path, gate_path, self.root / "rollback-backup.db")
        self.assertEqual(self.snapshot(), before)


class ContentPatchIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT NOT NULL,
                source_location TEXT,
                knowledge_type TEXT NOT NULL,
                related_kp_ids TEXT,
                importance TEXT NOT NULL,
                learning_action TEXT,
                body TEXT,
                difficulty INTEGER,
                fragile TEXT,
                graph_label TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT
            );
            CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY);
            CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY);
        """)
        conn.executemany(
            "INSERT INTO knowledge_points VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("kp-1", "排列", "Section 1", "concept-property", "[]",
                 "core", None, "排列正文", 2, None, None),
                ("kp-2", "组合", "Section 2", "concept-property", "[]",
                 "core", None, "组合正文", 2, None, None),
            ],
        )
        conn.executemany(
            "INSERT INTO problems VALUES (?, ?, ?, ?)",
            [
                ("p-1", '["kp-1"]', "Problem one", "old one"),
                ("p-2", '["kp-2"]', "Problem two", "old two"),
            ],
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def artifact(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def snapshot(self, path=None):
        conn = sqlite3.connect(path or self.db_path)
        try:
            return {
                "knowledge_points": conn.execute(
                    "SELECT * FROM knowledge_points ORDER BY kp_id"
                ).fetchall(),
                "problems": conn.execute(
                    "SELECT * FROM problems ORDER BY problem_id"
                ).fetchall(),
            }
        finally:
            conn.close()

    def qualified_files(self):
        solution_items = [
            {"source": "Problem one", "problem": "p-1", "solution": "Solution one"},
            {"source": "Problem two", "problem": "p-2", "solution": "Solution two"},
        ]
        solutions = self.artifact("solutions.json", {
            "kind": "solutions", "provider": "codex",
            "provider_session_id": "solution-session", "items": solution_items,
        })
        audits = self.artifact("audit.json", {
            "kind": "audit", "provider": "codex",
            "provider_session_id": "solution-audit-session",
            "items": [audit_item(x["source"], x["problem"], x["solution"])
                      for x in solution_items],
        })
        knowledge_point = {
            "kp_id": "kp-3", "knowledge_item": "位串生成子集",
            "source_location": "Section 3", "knowledge_type": "algorithm-process",
            "related_kp_ids": ["kp-2"], "importance": "supplementary",
            "learning_action": None, "body": "用 $n$ 位串表示子集。",
            "difficulty": 2, "fragile": None, "graph_label": "位串子集",
        }
        mappings = [
            {"problem": "p-1", "kp_ids": ["kp-3"]},
            {"problem": "p-2", "kp_ids": ["kp-1", "kp-2"]},
        ]
        content = self.artifact("content-patch.json", {
            "kind": "knowledge-mapping-patch", "provider": "codex",
            "provider_session_id": "content-session",
            "knowledge_points": [knowledge_point], "mappings": mappings,
        })
        content_audit = self.artifact("content-audit.json", {
            "kind": "knowledge-mapping-audit", "provider": "codex",
            "provider_session_id": "content-audit-session",
            "knowledge_points": [{
                "knowledge_point": knowledge_point,
                "decisions": {dimension: "PASS" for dimension in KP_DIMENSIONS},
                "findings": [],
            }],
            "mappings": [{
                **mapping,
                "source": next(x["source"] for x in solution_items
                               if x["problem"] == mapping["problem"]),
                "solution": next(x["solution"] for x in solution_items
                                 if x["problem"] == mapping["problem"]),
                "decisions": {dimension: "PASS" for dimension in DIMENSIONS},
                "findings": [],
            } for mapping in mappings],
        })
        return solutions, audits, content, content_audit

    def test_gate_binds_new_knowledge_points_and_final_mappings_to_independent_audit(self):
        solutions, audits, content, content_audit = self.qualified_files()
        report_path = self.root / "gate.json"

        report = ingest.gate(
            self.db_path, solutions, audits, report_path, content, content_audit,
        )

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["content_patch"]["kind"], "knowledge-mapping-patch")
        self.assertEqual(report["content_audit"]["kind"], "knowledge-mapping-audit")

        rejected = json.loads(content_audit.read_text(encoding="utf-8"))
        rejected["mappings"][0]["decisions"]["knowledge_point_mapping"] = "FAIL"
        bad_audit = self.artifact("bad-content-audit.json", rejected)
        failed = ingest.gate(
            self.db_path, solutions, audits, self.root / "bad-gate.json",
            content, bad_audit,
        )
        self.assertFalse(failed["ok"])

    def test_apply_uses_one_backup_and_transaction_for_solutions_kps_and_mappings(self):
        solutions, audits, content, content_audit = self.qualified_files()
        gate_path = self.root / "gate.json"
        ingest.gate(
            self.db_path, solutions, audits, gate_path, content, content_audit,
        )
        before = self.snapshot()
        backup = self.root / "backup.db"

        result = ingest.apply(self.db_path, gate_path, backup)

        self.assertTrue(result["ok"])
        self.assertEqual(self.snapshot(backup), before)
        after = self.snapshot()
        self.assertEqual(len(after["knowledge_points"]), 3)
        self.assertEqual(after["problems"][0][1:], ('["kp-3"]', "Problem one", "Solution one"))
        self.assertEqual(
            after["problems"][1][1:],
            ('["kp-1", "kp-2"]', "Problem two", "Solution two"),
        )

        self.tearDown()
        self.setUp()
        solutions, audits, content, content_audit = self.qualified_files()
        gate_path = self.root / "rollback-gate.json"
        ingest.gate(
            self.db_path, solutions, audits, gate_path, content, content_audit,
        )
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TRIGGER reject_mapping BEFORE UPDATE ON problems
            WHEN NEW.problem_id='p-2' BEGIN SELECT RAISE(ABORT, 'stop'); END;
        """)
        conn.commit()
        conn.close()
        before = self.snapshot()

        with self.assertRaises(sqlite3.IntegrityError):
            ingest.apply(self.db_path, gate_path, self.root / "rollback-backup.db")

        self.assertEqual(self.snapshot(), before)

if __name__ == "__main__":
    unittest.main()
