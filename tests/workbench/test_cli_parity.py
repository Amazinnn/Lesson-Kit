"""Every learning action the page can do is reachable from the CLI, with the same
validation and the same transaction boundary (TDD, red first)."""

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
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("parity_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script("parity_create_tables", Path("pipeline/scripts/create-tables.py"))


class CliParityTests(unittest.TestCase):
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
            "INSERT INTO knowledge_points (kp_id, knowledge_item, knowledge_type,"
            " importance) VALUES (?, ?, ?, ?)",
            ("dmath-ch06-kp-001", "乘法规则", "concept-property", "core"))
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
            " problem_type, source_kind, origin_kind) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "P1", "S1",
             "calculation", "textbook", "source_problem"))
        conn.execute(
            "INSERT INTO flash_cards (card_id, kp_id, front, back, source_evidence,"
            " directions) VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-fc-001", "dmath-ch06-kp-001", "正面", "背面", "教材",
             '["forward", "reverse"]'))
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

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def rows(self, table, where="", params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute(
                f"SELECT * FROM {table} {where} ORDER BY 1", params)]
        finally:
            conn.close()

    # -- practice ---------------------------------------------------------

    def test_an_unknown_problem_is_refused_before_any_write(self):
        code, output = self.run_cli("practice", "course", "--problem",
                                    "dmath-ch06-prob-999", "--result", "correct")
        self.assertEqual(code, 2)
        self.assertIn("unknown problem: dmath-ch06-prob-999", output)
        for table in ("problem_attempts", "problem_progress", "review_schedule"):
            self.assertEqual(self.rows(table), [], table)

    def test_a_failed_write_leaves_no_partial_record(self):
        from workbench.cli import main as cli_mod
        from workbench.data import pool as pool_mod

        real_progress = pool_mod.Pool.upsert_problem_progress

        def explode(self, *args, **kwargs):
            raise sqlite3.OperationalError("disk full")

        with mock.patch.object(pool_mod.Pool, "upsert_problem_progress", explode):
            code, output = self.run_cli("practice", "course", "--problem",
                                        "dmath-ch06-prob-001", "--result", "correct",
                                        "--note", "第一次")
        self.assertEqual(code, 2)
        self.assertIn("disk full", output)
        # The attempt was written first; the transaction must have taken it back.
        self.assertEqual(self.rows("problem_attempts"), [])
        self.assertEqual(self.rows("review_schedule"), [])
        self.assertTrue(real_progress)

        code, _ = self.run_cli("practice", "course", "--problem",
                               "dmath-ch06-prob-001", "--result", "correct")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.rows("problem_attempts")), 1)
        self.assertEqual(self.rows("problem_progress")[0]["status"], "reviewing")

    def test_skip_still_records_nothing(self):
        code, output = self.run_cli("practice", "course", "--problem",
                                    "dmath-ch06-prob-001", "--result", "skip")
        self.assertEqual(code, 0)
        self.assertIn("no learning record", output)
        self.assertEqual(self.rows("problem_attempts"), [])

    # -- feedback ---------------------------------------------------------

    def test_a_card_can_be_rated_in_a_direction_from_the_cli(self):
        code, output = self.run_cli(
            "feedback", "course", "--item", "card", "--id", "dmath-ch06-fc-001",
            "--rating", "4", "--direction", "reverse", "--note", "反向不熟")
        self.assertEqual(code, 0)
        self.assertIn("event logged", output)
        rows = {row["direction"]: row for row in self.rows("review_schedule")}
        self.assertEqual(list(rows), ["reverse"])
        self.assertEqual(rows["reverse"]["last_rating"], 4)

    def test_an_unknown_item_and_a_bad_direction_are_refused(self):
        code, output = self.run_cli("feedback", "course", "--item", "kp",
                                    "--id", "dmath-ch06-kp-999", "--rating", "3")
        self.assertEqual(code, 2)
        self.assertIn("unknown kp: dmath-ch06-kp-999", output)
        self.assertEqual(self.rows("feedback_events"), [])

        code, output = self.run_cli(
            "feedback", "course", "--item", "card", "--id", "dmath-ch06-fc-001",
            "--rating", "3", "--direction", "sideways")
        self.assertEqual(code, 2)
        self.assertIn("direction is not available", output)
        self.assertEqual(self.rows("feedback_events"), [])

    def test_feedback_needs_a_rating_or_a_note(self):
        code, output = self.run_cli("feedback", "course", "--item", "problem",
                                    "--id", "dmath-ch06-prob-001", "--note", "  ")
        self.assertEqual(code, 2)
        self.assertIn("rating or note is required", output)
        self.assertEqual(self.rows("feedback_events"), [])

    # -- goals ------------------------------------------------------------

    def test_a_cli_goal_write_drops_the_cached_plan(self):
        plan = self.ws / ".lessonkit" / "plan.json"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text('{"plan_version": 1, "plan_date": "2000-01-01"}', encoding="utf-8")

        code, _ = self.run_cli("goals", "course", "add", "--title", "期末复习")
        self.assertEqual(code, 0)
        self.assertFalse(plan.exists(), "a goal change must make the cached plan stale")

    def test_listing_goals_touches_no_plan(self):
        plan = self.ws / ".lessonkit" / "plan.json"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text('{"plan_version": 1}', encoding="utf-8")
        code, _ = self.run_cli("goals", "course", "list")
        self.assertEqual(code, 0)
        self.assertTrue(plan.exists())

    # -- read commands ----------------------------------------------------

    def test_read_commands_offer_json_and_keep_their_text_default(self):
        code, text = self.run_cli("weak", "course")
        self.assertEqual(code, 0)
        self.assertIn("dmath-ch06-kp-001", text)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(text)

        code, output = self.run_cli("weak", "course", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)[0]["kp_id"], "dmath-ch06-kp-001")

        code, output = self.run_cli("due", "course", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), [])

        code, output = self.run_cli("ls", "--json")
        self.assertEqual(code, 0)
        listed = json.loads(output)
        self.assertEqual(listed[0]["name"], "course")
        self.assertEqual(listed[0]["problems"], 1)

        code, text = self.run_cli("ls")
        self.assertEqual(code, 0)
        self.assertIn("course", text)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(text)

    # -- dead surfaces ----------------------------------------------------

    def test_removed_arguments_are_gone_not_silently_ignored(self):
        parser = self.cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["ingest", "course", "render", "problem-set",
                               "--input", "a", "--output", "b"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["ingest", "course", "gate", "kp",
                               "--solutions", "a", "--audit", "b", "--output", "c"])
        parser.parse_args(["ingest", "course", "render", "--input", "a", "--output", "b"])
        parser.parse_args(["ingest", "course", "gate", "problem",
                           "--solutions", "a", "--audit", "b", "--output", "c"])


if __name__ == "__main__":
    unittest.main()
