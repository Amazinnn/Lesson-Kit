"""wb CLI integration tests (TDD, red first)."""

import contextlib
import importlib.util
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))


def build_fixture_db(conn):
    conn.executescript(
        """
        CREATE TABLE knowledge_points (
            kp_id TEXT PRIMARY KEY,
            knowledge_item TEXT NOT NULL,
            knowledge_type TEXT,
            importance TEXT
        );
        CREATE TABLE problems (
            problem_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            problem_type TEXT,
            source_kind TEXT
        );
        CREATE TABLE problem_progress (
            problem_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'new',
            note TEXT,
            updated_at TEXT
        );
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE learner_signals (
            signal_id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            weight TEXT NOT NULL DEFAULT 'medium',
            evidence_count INTEGER NOT NULL DEFAULT 1,
            note TEXT
        );
        CREATE TABLE knowledge_relations (
            relation_id TEXT PRIMARY KEY,
            source_kp_id TEXT NOT NULL,
            target_kp_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            strength TEXT NOT NULL
        );
        """
    )
    pool_schema.ensure_workbench_schema(conn)
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, knowledge_type, importance)"
        " VALUES (?, ?, ?, ?)",
        ("dmath-ch06-kp-001", "Counting", "concept-property", "core"),
    )
    conn.execute(
        "INSERT INTO problems"
        " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "P1", "S1", "calculation", "textbook"),
    )
    conn.commit()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "dmath"
        (self.ws / "pool").mkdir(parents=True)
        self.db_path = self.ws / "pool" / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        build_fixture_db(conn)
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from cli import main as cli_mod
        from registry import register
        self.cli = cli_mod
        register(str(self.ws), course="dmath", chapter="ch06")

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def test_ls_lists_workspace(self):
        code, out = self.run_cli("ls")
        self.assertEqual(code, 0)
        self.assertIn("dmath", out)

    def test_weak_lists_kps(self):
        code, out = self.run_cli("weak", "dmath")
        self.assertEqual(code, 0)
        self.assertIn("dmath-ch06-kp-001", out)

    def test_pull_reports_shortage(self):
        code, out = self.run_cli("pull", "dmath", "--kp", "dmath-ch06-kp-001",
                                 "--n", "5")
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["problems"], ["dmath-ch06-prob-001"])
        self.assertIn("dmath-ch06-kp-001", result["shortage"])
        self.assertNotIn("candidates", result)

    def test_data_parser_excludes_retired_candidate_commands(self):
        parser = self.cli.build_parser()
        for argv in (
            ["data", "dmath", "list", "candidate"],
            ["data", "dmath", "gate", "problem", "p-1"],
            ["data", "dmath", "promote", "problem", "p-1"],
        ):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                parser.parse_args(argv)

    def test_practice_records_attempt(self):
        code, out = self.run_cli("practice", "dmath",
                                 "--problem", "dmath-ch06-prob-001",
                                 "--result", "wrong", "--answer-text", "my text")
        self.assertEqual(code, 0)
        from data import pool as pool_mod
        pool = pool_mod.Pool(root=self.ws, db_path=self.db_path,
                             course="dmath", chapter="ch06")
        attempts = pool.attempts("dmath-ch06-prob-001")
        pool.close()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["answer_text"], "my text")

    def test_practice_correct_records_reviewing_and_skip_records_nothing(self):
        code, out = self.run_cli("practice", "dmath",
                                 "--problem", "dmath-ch06-prob-001",
                                 "--result", "correct")
        self.assertEqual(code, 0)
        code, out = self.run_cli("practice", "dmath",
                                 "--problem", "dmath-ch06-prob-001",
                                 "--result", "skip")
        self.assertEqual(code, 0)
        self.assertIn("no learning record", out)
        from data import pool as pool_mod
        pool = pool_mod.Pool(root=self.ws, db_path=self.db_path,
                             course="dmath", chapter="ch06")
        attempts = pool.attempts("dmath-ch06-prob-001")
        pool.close()
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        progress = conn.execute(
            "SELECT status FROM problem_progress WHERE problem_id = ?",
            ("dmath-ch06-prob-001",),
        ).fetchone()
        conn.close()
        self.assertEqual([a["status"] for a in attempts], ["reviewing"])
        self.assertEqual(progress[0], "reviewing")

    def test_feedback_creates_signal(self):
        code, out = self.run_cli("feedback", "dmath", "--item", "kp",
                                 "--id", "dmath-ch06-kp-001", "--rating", "2")
        self.assertEqual(code, 0)
        self.assertIn("signal", out)

    def test_schedule_shows_state(self):
        self.run_cli("practice", "dmath", "--problem", "dmath-ch06-prob-001",
                     "--result", "correct")
        code, out = self.run_cli("schedule", "dmath", "--item", "problem",
                                 "--id", "dmath-ch06-prob-001")
        self.assertEqual(code, 0)
        self.assertIn("review", out)

    def test_goals_add_list_update_rm(self):
        code, out = self.run_cli("goals", "dmath", "add", "--title", "期末掌握计数",
                                 "--kind", "stage", "--start-date", "2026-09-01",
                                 "--deadline", "2026-09-30",
                                 "--description", "重点鸽巢与组合")
        self.assertEqual(code, 0)
        self.assertIn("期末掌握计数", out)
        self.assertIn("2026-09-01", out)

        code, out = self.run_cli("goals", "dmath", "list")
        self.assertEqual(code, 0)
        self.assertIn("期末掌握计数", out)

        code, out = self.run_cli("goals", "dmath", "update", "goal-001",
                                 "--title", "改后的目标")
        self.assertEqual(code, 0)
        self.assertIn("改后的目标", out)

        code, out = self.run_cli("goals", "dmath", "rm", "goal-001")
        self.assertEqual(code, 0)
        code, out = self.run_cli("goals", "dmath", "list")
        self.assertNotIn("改后的目标", out)

    def test_ingest_parser_exposes_atomic_commands(self):
        parser = self.cli.build_parser()
        prepared = parser.parse_args([
            "ingest", "dmath", "prepare", "problem-solutions",
            "--input", "problems.json", "--output", "job-dir",
        ])
        self.assertEqual(prepared.command, "ingest")
        self.assertEqual(prepared.action, "prepare")
        self.assertEqual(prepared.operation, "problem-solutions")

        run = parser.parse_args([
            "ingest", "dmath", "run", "job-dir", "--provider", "codex",
        ])
        self.assertEqual(run.action, "run")
        self.assertEqual(run.provider, "codex")

        gate = parser.parse_args([
            "ingest", "dmath", "gate", "problem",
            "--solutions", "solutions.json", "--audit", "audit.json",
            "--content-patch", "content.json", "--content-audit", "content-audit.json",
            "--output", "gate.json",
        ])
        self.assertEqual(gate.content_patch, "content.json")
        self.assertEqual(gate.content_audit, "content-audit.json")

        recipe = parser.parse_args([
            "ingest", "dmath", "recipe", "problems",
            "--input", "problems.json", "--output", "recipe-dir", "--apply",
        ])
        self.assertTrue(recipe.apply)

    def test_mastery_experiment_parser_is_explicit_and_read_only(self):
        args = self.cli.build_parser().parse_args([
            "experiment", "dmath", "mastery",
            "--entity", "problem", "--id", "dmath-ch06-prob-001", "--json",
        ])
        self.assertEqual(args.command, "experiment")
        self.assertEqual(args.experiment, "mastery")
        self.assertEqual(args.entity, "problem")
        self.assertTrue(args.json)

    def test_ingest_prepare_routes_to_a_resumable_task_artifact(self):
        source = Path(self.tmp.name) / "source.json"
        source.write_text(json.dumps({
            "items": [{"problem_id": "dmath-ch06-prob-001", "problem_text": "P1"}],
        }), encoding="utf-8")
        output = Path(self.tmp.name) / "job"

        code, out = self.run_cli(
            "ingest", "dmath", "prepare", "problem-solutions",
            "--input", str(source), "--output", str(output),
        )

        self.assertEqual(code, 0)
        task = json.loads((output / "task.json").read_text(encoding="utf-8"))
        self.assertEqual(task["kind"], "ingest-task")
        self.assertEqual(json.loads(out)["artifact"], str(output / "task.json"))

    def test_mastery_experiment_filters_json_without_writing(self):
        conn = sqlite3.connect(self.db_path)
        before = {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in ("knowledge_points", "problems", "problem_attempts",
                          "feedback_events", "review_schedule")
        }
        conn.close()

        code, out = self.run_cli(
            "experiment", "dmath", "mastery", "--entity", "problem",
            "--id", "dmath-ch06-prob-001", "--json",
        )

        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["version"], "v0")
        self.assertEqual([item["id"] for item in result["problems"]],
                         ["dmath-ch06-prob-001"])
        conn = sqlite3.connect(self.db_path)
        after = {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in before
        }
        conn.close()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
