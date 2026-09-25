"""Practice set composition and export: selection, manifest, render, check (TDD)."""

import contextlib
import importlib.util
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TODAY = date.today()


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("practice_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script("practice_create_tables", Path("pipeline/scripts/create-tables.py"))

PROBLEMS = (
    # (problem_id, kp_ids, source_kind, exam_year, solution)
    ("dmath-ch12-prob-001", ["dmath-ch12-kp-001"], "textbook", "2023-2024秋冬", "解答一"),
    ("dmath-ch12-prob-002", ["dmath-ch12-kp-002"], "final", "2023-2024秋冬", "解答二"),
    ("dmath-ch12-prob-003", ["dmath-ch12-kp-002"], "textbook", None, None),
    ("dmath-ch13-prob-001", ["dmath-ch13-kp-001"], "final", "2024-2025秋冬", "解答四"),
)


class PracticeSetTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "course"
        (self.ws / "pool").mkdir(parents=True)
        self.db_path = self.ws / "pool" / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        for kp_id in ("dmath-ch12-kp-001", "dmath-ch12-kp-002", "dmath-ch13-kp-001"):
            conn.execute(
                "INSERT INTO knowledge_points "
                "(kp_id, knowledge_item, knowledge_type, importance) VALUES (?, ?, ?, ?)",
                (kp_id, kp_id, "concept-property", "core"),
            )
        for problem_id, kp_ids, source_kind, exam_year, solution in PROBLEMS:
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
                " problem_type, source_kind, origin_kind, exam_year) VALUES (?,?,?,?,?,?,?,?)",
                (problem_id, json.dumps(kp_ids), f"第 {problem_id[-3:]} 题的题干", solution,
                 "calculation", source_kind, "source_problem", exam_year),
            )
        conn.commit()
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from cli import main as cli_mod
        from registry import register

        self.cli = cli_mod
        self.registry = sys.modules["registry"]
        register(str(self.ws), name="course", course="dmath", chapter="ch12")

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    # -- helpers ----------------------------------------------------------

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def json_cli(self, *args):
        code, output = self.run_cli(*args)
        return code, json.loads(output)

    def pool(self):
        from workbench.data import pool as pool_mod
        from workbench import registry

        workspace = registry.get_workspace("course")
        return pool_mod.Pool(
            root=Path(workspace["path"]),
            db_path=Path(workspace["path"]) / workspace["db"],
            course=workspace["active_course"], chapter=workspace["active_chapter"],
        )

    def seed_evidence(self):
        """One wrong problem, one wrong latest attempt, one due row, one signal."""
        pool = self.pool()
        try:
            pool.upsert_problem_progress("dmath-ch12-prob-002", "wrong")
            pool.insert_attempt("dmath-ch13-prob-001", "wrong", "卡在第二问")
            pool.schedule_upsert({
                "item_type": "problem", "item_id": "dmath-ch12-prob-001", "direction": "",
                "state": "review", "repetitions": 1, "ease": 2.5, "interval_days": 1.0,
                "due_at": (TODAY - timedelta(days=2)).isoformat(),
                "last_rating": 3, "last_reviewed_at": (TODAY - timedelta(days=3)).isoformat(),
            })
            pool.upsert_signal("node", "dmath-ch12-kp-002", "confusion", "high", 2, "混淆")
        finally:
            pool.close()

    def learning_rows(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            tables = ("problem_attempts", "feedback_events", "learner_signals",
                      "problem_progress", "learning_current_state", "review_schedule")
            return {table: [dict(r) for r in conn.execute(
                f"SELECT * FROM {table} ORDER BY 1")] for table in tables}
        finally:
            conn.close()

    def problem_ids(self, result):
        return [item["problem_id"] if isinstance(item, dict) else item
                for item in result["problems"]]

    def reasons(self, result):
        return {item["problem_id"]: item["reason"] for item in result["problems"]}


class SelectionTests(PracticeSetTestCase):
    def test_scope_and_conditional_filters_select_inside_the_scope(self):
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002",
            "--source-kind", "textbook", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-003"])
        self.assertEqual(self.reasons(result), {"dmath-ch12-prob-003": "scope"})

    def test_rows_come_back_whole_and_ids_stay_available(self):
        code, rows = self.json_cli("pull", "course", "--kp", "dmath-ch12-kp-001")
        self.assertEqual(code, 0)
        self.assertEqual(rows["problems"][0]["problem_id"], "dmath-ch12-prob-001")
        self.assertEqual(rows["problems"][0]["problem_text"], "第 001 题的题干")
        self.assertEqual(rows["problems"][0]["reason"], "scope")

        code, ids = self.json_cli("pull", "course", "--kp", "dmath-ch12-kp-001", "--ids")
        self.assertEqual(ids["problems"], ["dmath-ch12-prob-001"])

    def test_explicit_problem_survives_filters_and_the_cap(self):
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-001", "--source-kind", "final",
            "--n", "1", "--problem", "dmath-ch12-prob-001")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-001"])
        self.assertEqual(self.reasons(result), {"dmath-ch12-prob-001": "explicit"})

    def test_exam_year_filters_by_prefix(self):
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002", "--exam-year", "2023", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-002"])

    def test_wrong_driver_uses_progress_and_the_latest_attempt(self):
        self.seed_evidence()
        code, result = self.json_cli("pull", "course", "--wrong", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-002"])
        self.assertEqual(self.reasons(result), {"dmath-ch12-prob-002": "wrong"})

        self.run_cli("use", "dmath", "")
        code, whole = self.json_cli("pull", "course", "--wrong", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(self.problem_ids(whole)),
                         ["dmath-ch12-prob-002", "dmath-ch13-prob-001"])

    def test_due_driver_selects_problems_already_due(self):
        self.seed_evidence()
        code, result = self.json_cli("pull", "course", "--due", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-001"])
        self.assertEqual(self.reasons(result), {"dmath-ch12-prob-001": "due"})

    def test_weak_driver_selects_problems_of_weak_knowledge_points(self):
        self.seed_evidence()
        code, result = self.json_cli(
            "pull", "course", "--weak", "--kp", "dmath-ch12-kp-002", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(self.problem_ids(result)),
                         ["dmath-ch12-prob-002", "dmath-ch12-prob-003"])
        self.assertEqual(set(self.reasons(result).values()), {"weak"})

    def test_drivers_union_but_respect_the_scope(self):
        self.seed_evidence()
        code, result = self.json_cli("pull", "course", "--due", "--wrong", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(self.problem_ids(result)),
                         ["dmath-ch12-prob-001", "dmath-ch12-prob-002"])

    def test_include_filter_restricts_the_selection(self):
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002",
            "--include", "dmath-ch12-prob-003", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(result), ["dmath-ch12-prob-003"])

    def test_shortage_stays_honest(self):
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-001", "--n", "5")
        self.assertEqual(code, 0)
        self.assertEqual(result["shortage"], ["dmath-ch12-kp-001"])

    def test_unmigrated_pool_explains_the_exam_year_migration(self):
        old = Path(self.tmp.name) / "legacy"
        (old / "pool").mkdir(parents=True)
        conn = sqlite3.connect(old / "pool" / "dmath.db")
        conn.executescript(create_tables.SCHEMA_SQL)
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type,"
            " source_kind) VALUES (?, ?, ?, ?, ?)",
            ("dmath-ch12-prob-001", "[]", "text", "calculation", "textbook"))
        conn.commit()
        conn.close()
        self.registry.register(str(old), name="legacy", course="dmath", chapter="ch12")
        code, result = self.json_cli(
            "pull", "legacy", "--kp", "dmath-ch12-kp-001", "--exam-year", "2023")
        self.assertEqual(code, 2)
        self.assertIn("migrate-progress.py --db pool/dmath.db", result["error"])

    def test_selection_writes_nothing(self):
        self.seed_evidence()
        before = self.learning_rows()
        self.json_cli("pull", "course", "--wrong", "--due", "--weak", "--n", "5")
        self.assertEqual(self.learning_rows(), before)


class ManifestTests(PracticeSetTestCase):
    def compose(self, name="plan.json", *extra):
        path = Path(self.tmp.name) / name
        code, output = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002", "--n", "5",
            "--plan", str(path), *extra)
        self.assertEqual(code, 0)
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_records_the_selection_and_replays_it(self):
        path, plan = self.compose()
        self.assertEqual(plan["kind"], "practice-set")
        self.assertEqual(plan["course"], "dmath")
        self.assertEqual([item["problem_id"] for item in plan["items"]],
                         ["dmath-ch12-prob-002", "dmath-ch12-prob-003"])
        self.assertEqual(plan["request"]["n"], 5)
        before = self.learning_rows()

        code, replayed = self.json_cli("pull", "course", "--input", str(path))
        self.assertEqual(code, 0)
        self.assertEqual(self.problem_ids(replayed),
                         ["dmath-ch12-prob-002", "dmath-ch12-prob-003"])
        self.assertEqual(self.learning_rows(), before)

    def test_unknown_and_duplicate_problems_are_refused(self):
        for payload, message in (
            ({"kind": "practice-set", "title": "t", "items": [
                {"problem_id": "dmath-ch12-prob-999", "reason": "scope"}]},
             "unknown problem dmath-ch12-prob-999"),
            ({"kind": "practice-set", "title": "t", "items": [
                {"problem_id": "dmath-ch12-prob-001"},
                {"problem_id": "dmath-ch12-prob-001"}]},
             "duplicate problem dmath-ch12-prob-001"),
            ({"kind": "content-bundle", "items": []}, "expected a practice-set manifest"),
            ({"kind": "practice-set", "title": "t", "items": [], "extra": 1},
             "unsupported manifest field: extra"),
        ):
            with self.subTest(message=message):
                path = Path(self.tmp.name) / "bad.json"
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                before = self.learning_rows()
                code, result = self.json_cli("pull", "course", "--input", str(path))
                self.assertEqual(code, 2)
                self.assertIn(message, result["error"])
                self.assertEqual(self.learning_rows(), before)

    def test_input_and_selection_flags_are_alternatives(self):
        path, _ = self.compose()
        code, result = self.json_cli(
            "pull", "course", "--input", str(path), "--kp", "dmath-ch12-kp-001")
        self.assertEqual(code, 2)
        self.assertIn("not both", result["error"])


class RenderTests(PracticeSetTestCase):
    def rendered(self):
        directory = Path(self.tmp.name) / "out"
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002", "--n", "5",
            "--print", str(directory))
        self.assertEqual(code, 0)
        return directory, result

    def test_student_sheet_has_no_answer_and_no_internal_id(self):
        directory, result = self.rendered()
        student = (directory / "ch12-problem-set.md").read_text(encoding="utf-8")
        self.assertEqual(result["preview"]["count"], 2)
        self.assertEqual(result["printed"], [
            str(directory / "ch12-problem-set.md"),
            str(directory / "ch12-solutions.md"),
        ])
        for token in ("dmath-ch12-prob-002", "dmath-ch12-prob-003",
                      "dmath-ch12-kp-002", "final", "textbook", "解答二"):
            self.assertNotIn(token, student)
        self.assertIn("第 002 题的题干", student)

    def test_both_sheets_number_identically_and_missing_solutions_read_as_pending(self):
        directory, _ = self.rendered()
        student = (directory / "ch12-problem-set.md").read_text(encoding="utf-8")
        solutions = (directory / "ch12-solutions.md").read_text(encoding="utf-8")
        numbers = [line for line in student.splitlines() if line.startswith("### ")]
        self.assertEqual(numbers, ["### 1", "### 2"])
        self.assertEqual([line for line in solutions.splitlines()
                          if line.startswith("### ")], numbers)
        self.assertIn("解答二", solutions)
        self.assertIn("待补", solutions)
        # Each number carries its own problem's text: 1 has the stored solution,
        # 2 the one that is not stored.
        sections = {}
        current = None
        for line in solutions.splitlines():
            if line.startswith("### "):
                current = line
            elif line.strip() and current and current not in sections:
                sections[current] = line.strip()
        self.assertEqual(sections, {"### 1": "解答二", "### 2": "待补"})

    def test_cross_chapter_set_uses_the_chosen_directory_and_base(self):
        self.run_cli("use", "dmath", "")
        directory = Path(self.tmp.name) / "final"
        code, result = self.json_cli(
            "pull", "course", "--n", "9", "--print", str(directory),
            "--base", "review", "--title", "期末复习")
        self.assertEqual(code, 0)
        student = (directory / "review-problem-set.md").read_text(encoding="utf-8")
        self.assertTrue(student.startswith("# 期末复习"))
        self.assertEqual(result["preview"]["count"], 4)

    def test_check_validates_and_writes_nothing(self):
        path, _ = self.compose_plan()
        before = self.learning_rows()
        code, report = self.json_cli("pull", "course", "--input", str(path), "--check")
        self.assertEqual(code, 0)
        self.assertTrue(report["valid"])
        self.assertEqual(report["writes"], 0)
        self.assertEqual(report["count"], 2)
        self.assertEqual(report["missing_solutions"], ["dmath-ch12-prob-003"])
        self.assertEqual(report["leaks"], [])
        self.assertEqual(report["figures"], {"count": 0, "base": ""})
        self.assertEqual(self.learning_rows(), before)

    def test_a_figure_reference_stays_relative_and_names_its_base(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE problems SET problem_text=? WHERE problem_id=?",
            ("看图 ![](dmath/ch12/figure.png) 作答", "dmath-ch12-prob-002"))
        conn.commit()
        conn.close()
        directory = Path(self.tmp.name) / "figures"
        code, result = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002", "--n", "5",
            "--print", str(directory))
        self.assertEqual(code, 0)
        student = (directory / "ch12-problem-set.md").read_text(encoding="utf-8")
        self.assertIn("![](dmath/ch12/figure.png)", student)
        self.assertEqual(result["preview"]["figures"]["count"], 1)
        self.assertTrue(result["preview"]["figures"]["base"].endswith(
            os.path.join(".lessonkit", "figures")))

    def test_check_catches_a_leak_in_a_tampered_manifest(self):
        path, plan = self.compose_plan()
        plan["items"].insert(0, {"problem_id": "dmath-ch12-kp-002", "reason": "scope"})
        path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        code, result = self.json_cli("pull", "course", "--input", str(path))
        self.assertEqual(code, 2)
        self.assertIn("unknown problem dmath-ch12-kp-002", result["error"])

    def compose_plan(self):
        path = Path(self.tmp.name) / "checked.json"
        code, _ = self.json_cli(
            "pull", "course", "--kp", "dmath-ch12-kp-002", "--n", "5", "--plan", str(path))
        self.assertEqual(code, 0)
        return path, json.loads(path.read_text(encoding="utf-8"))


class RenderRuleTests(unittest.TestCase):
    def test_renderer_is_deterministic_and_guards_against_identifier_leaks(self):
        from workbench.domain import practice_set

        problems = [{"problem_id": "dmath-ch06-prob-001", "kp_ids": ["dmath-ch06-kp-001"],
                     "problem_text": "题干", "solution": "解答"}]
        first = practice_set.render_practice_set(problems, "t")
        second = practice_set.render_practice_set(problems, "t")
        self.assertEqual(first, second)
        self.assertEqual(practice_set.leaks(problems, first), [])
        self.assertEqual(
            practice_set.leaks(problems, first + "dmath-ch06-kp-001")[0]["token"],
            "dmath-ch06-kp-001")
        self.assertEqual(practice_set.render_solutions([{}], "t").count("待补"), 1)


if __name__ == "__main__":
    unittest.main()
