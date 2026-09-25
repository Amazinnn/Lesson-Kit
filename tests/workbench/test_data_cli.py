"""JSON data CLI contracts for external Agent providers."""

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


pool_schema = load_script("data_cli_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script("data_cli_create_tables", Path("pipeline/scripts/create-tables.py"))


class DataCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "course"
        (self.ws / "pool").mkdir(parents=True)
        self.db_path = self.ws / "pool" / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        conn.execute(
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, knowledge_type, importance) VALUES (?, ?, ?, ?)",
            ("dmath-ch06-kp-001", "乘法规则", "concept-property", "core"),
        )
        conn.execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "dmath-ch06-prob-001",
                '["dmath-ch06-kp-001"]',
                "Original problem",
                "Original solution",
                "calculation",
                "textbook",
            ),
        )
        conn.commit()
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from cli import main as cli_mod
        from registry import register

        self.cli = cli_mod
        register(str(self.ws), name="course", course="dmath", chapter="ch06")

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    def write_json(self, name, value):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        payload = json.loads(out.getvalue())
        return code, payload

    def test_read_commands_return_json_without_writes(self):
        conn = sqlite3.connect(self.db_path)
        before = conn.execute("SELECT total_changes()").fetchone()[0]
        conn.close()

        code, item = self.run_cli(
            "data", "course", "get", "kp", "dmath-ch06-kp-001"
        )
        self.assertEqual(code, 0)
        self.assertEqual(item["knowledge_item"], "乘法规则")
        self.assertEqual(self.run_cli("data", "course", "list", "kp")[1][0]["kp_id"], "dmath-ch06-kp-001")
        self.assertEqual(self.run_cli("data", "course", "search", "kp", "乘法")[1][0]["kp_id"], "dmath-ch06-kp-001")
        self.assertEqual(self.run_cli("data", "course", "history", "problem", "dmath-ch06-prob-001")[1]["attempts"], [])

        conn = sqlite3.connect(self.db_path)
        after = conn.execute("SELECT total_changes()").fetchone()[0]
        conn.close()
        self.assertEqual(after, before)

    def test_ingest_batches_returns_json_envelope(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO ingest_batches (batch_id, kind, manifest_path, counts_json,"
            " backup_path, applied_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("batch-001", "flash-card-patch", "batch-001.json",
             '{"flash_cards": 3}', "backup.db", "2026-08-30 10:00:00"),
        )
        conn.commit()
        conn.close()

        code, result = self.run_cli("ingest", "course", "batches")

        self.assertEqual(code, 0)
        self.assertEqual(result, {
            "artifact": None,
            "result": {"batches": [{
                "batch_id": "batch-001", "kind": "flash-card-patch",
                "counts": {"flash_cards": 3},
                "applied_at": "2026-08-30 10:00:00",
                "rolled_back_at": None, "backup_path": "backup.db",
            }]},
        })

    def test_create_update_delete_and_state_use_explicit_commands(self):
        create_path = self.write_json(
            "kp.json",
            {
                "knowledge_item": "减法规则",
                "knowledge_type": "concept-property",
                "importance": "core",
                "body": "两集合重叠时使用。",
            },
        )
        code, created = self.run_cli(
            "data", "course", "create", "kp", "--input", str(create_path)
        )
        self.assertEqual(code, 0)
        self.assertEqual(created["kp_id"], "dmath-ch06-kp-002")

        update_path = self.write_json("kp-update.json", {"body": "更新后的正文"})
        code, updated = self.run_cli(
            "data", "course", "update", "kp", created["kp_id"],
            "--input", str(update_path),
        )
        self.assertEqual(code, 0)
        self.assertEqual(updated["body"], "更新后的正文")

        code, state = self.run_cli(
            "data", "course", "state", "problem", "dmath-ch06-prob-001", "mastered"
        )
        self.assertEqual(code, 0)
        self.assertEqual(state["state"], "mastered")
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0], 0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM learner_signals").fetchone()[0], 0)
        conn.close()

        code, deleted = self.run_cli(
            "data", "course", "delete", "kp", created["kp_id"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(deleted["action"], "deleted")

    def test_formal_problem_can_be_created_directly(self):
        path = self.write_json("problem.json", {
            "kp_ids": ["dmath-ch06-kp-001"],
            "problem_text": "How many ordered pairs can be formed?",
            "solution": "Use the product rule.",
            "problem_type": "calculation",
            "source_kind": "textbook",
            "origin_kind": "source_problem",
        })
        code, created = self.run_cli(
            "data", "course", "create", "problem", "--input", str(path)
        )
        self.assertEqual(code, 0)
        self.assertEqual(created["problem_id"], "dmath-ch06-prob-002")
        self.assertEqual(created["kp_ids"], ["dmath-ch06-kp-001"])

    def test_problem_create_requires_both_provenance_axes(self):
        path = self.write_json("problem-missing-origin.json", {
            "kp_ids": ["dmath-ch06-kp-001"],
            "problem_text": "Generated check",
            "solution": "Answer",
            "problem_type": "calculation",
            "source_kind": "textbook",
        })
        code, result = self.run_cli(
            "data", "course", "create", "problem", "--input", str(path)
        )
        self.assertEqual(code, 2)
        self.assertIn("origin_kind is required", result["error"])

    def micro_item(self, payload):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type, "
            "source_kind, origin_kind, practice_modes, micro_quiz) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-mq-001", '["dmath-ch06-kp-001"]', "1 是质数吗？", "other",
             "textbook", "generated_grounded", '["yes_no"]',
             json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
        conn.close()

    def stored_quiz(self):
        conn = sqlite3.connect(self.db_path)
        try:
            raw = conn.execute(
                "SELECT micro_quiz FROM problems WHERE problem_id='dmath-ch06-mq-001'"
            ).fetchone()[0]
        finally:
            conn.close()
        return json.loads(raw)

    def test_an_answer_key_can_be_filled_in_and_cleared(self):
        self.micro_item({"quiz_type": "yes_no", "answer_key": None,
                         "source_evidence": "教材 §3.1"})
        filled = self.write_json("key.json", {"answer_key": "否"})
        code, updated = self.run_cli(
            "data", "course", "update", "problem", "dmath-ch06-mq-001",
            "--input", str(filled),
        )
        self.assertEqual(code, 0)
        self.assertEqual(updated["micro_quiz"]["answer_key"], "否")

        cleared = self.write_json("clear.json", {"answer_key": ""})
        code, _ = self.run_cli(
            "data", "course", "update", "problem", "dmath-ch06-mq-001",
            "--input", str(cleared),
        )
        self.assertEqual(code, 0)
        self.assertIsNone(self.stored_quiz()["answer_key"])

    def test_a_key_must_fit_the_items_own_quiz_type(self):
        self.micro_item({"quiz_type": "single_choice", "options": ["甲", "乙"],
                         "answer_key": None, "source_evidence": "教材 §3.1"})
        before = self.stored_quiz()
        wrong = self.write_json("wrong-key.json", {"answer_key": "丙"})

        code, result = self.run_cli(
            "data", "course", "update", "problem", "dmath-ch06-mq-001",
            "--input", str(wrong),
        )

        self.assertEqual(code, 2)
        self.assertIn("answer_key must be one of the options", result["error"])
        self.assertEqual(self.stored_quiz(), before)

    def test_an_answer_key_needs_an_objective_item(self):
        path = self.write_json("not-micro.json", {"answer_key": "是"})
        code, result = self.run_cli(
            "data", "course", "update", "problem", "dmath-ch06-prob-001",
            "--input", str(path),
        )
        self.assertEqual(code, 2)
        self.assertIn("判断/小测", result["error"])


if __name__ == "__main__":
    unittest.main()
