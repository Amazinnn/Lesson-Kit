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
        CREATE TABLE candidate_problems (
            candidate_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            status TEXT NOT NULL,
            structure_gate_status TEXT NOT NULL DEFAULT 'pending',
            audit_gate_status TEXT NOT NULL DEFAULT 'pending'
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


FAKE_PROVIDER = """\
import os
result = \"\"\"# Explain

## 结论

The product rule counts ordered pairs.

## 逐步拆解

Step one then step two.

## 易错点

Independence is required.

## 回源指向

Rosen, Discrete Mathematics, section 6.1.
\"\"\"
with open(os.environ["LESSONKIT_OUTPUT_PATH"], "w", encoding="utf-8") as f:
    f.write(result)
"""


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
        self.assertIn("dmath-ch06-prob-001", out)
        self.assertIn("shortage", out)

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

    def test_ai_explain_without_provider_fails_gracefully(self):
        code, out = self.run_cli("ai", "dmath", "explain",
                                 "dmath-ch06-prob-001")
        self.assertEqual(code, 0)
        self.assertIn("job-", out)
        self.assertIn("no provider", out)

    def test_ai_explain_with_provider_completes(self):
        provider_script = Path(self.tmp.name) / "fake_provider.py"
        provider_script.write_text(FAKE_PROVIDER, encoding="utf-8")
        from registry import add_bridge
        add_bridge("fake", "python", args=[str(provider_script)])
        code, out = self.run_cli("ai", "dmath", "explain",
                                 "dmath-ch06-prob-001", "--provider", "fake")
        self.assertEqual(code, 0)
        self.assertIn("done", out)
        explain_file = self.ws / ".lessonkit" / "explain" / "dmath" / "ch06" \
            / "dmath-ch06-prob-001.md"
        self.assertTrue(explain_file.is_file())

    def test_ai_status_reports_failed(self):
        code, out = self.run_cli("ai", "dmath", "explain",
                                 "dmath-ch06-prob-001")
        job_id = out.strip().split(":")[0]
        code, out = self.run_cli("ai", "dmath", "status", job_id)
        self.assertIn("failed", out)


if __name__ == "__main__":
    unittest.main()
