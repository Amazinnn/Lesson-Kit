import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lessonkit", REPO_ROOT / "lessonkit.py")
lessonkit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["lessonkit"] = lessonkit
SPEC.loader.exec_module(lessonkit)


class LessonKitRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = lessonkit.main(args, root=self.root)
        return code, output.getvalue()

    def write_file(self, relative_path, text="ok\n"):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_problem_set_artifacts(self):
        files = [
            "intermediate/dmath-ch06/problem-set/01_inputs/view-scope.md",
            "intermediate/dmath-ch06/problem-set/02_analysis/problem-query-result.json",
            "intermediate/dmath-ch06/problem-set/03_plans/selection-plan.md",
            "intermediate/dmath-ch06/problem-set/04_checks/problem-set-check.md",
            "intermediate/dmath-ch06/problem-set/04_checks/solution-sync-check.md",
            "output/dmath/ch06/ch06-problem-set.md",
            "output/dmath/ch06/ch06-solutions.md",
        ]
        for relative in files:
            text = "Result: PASS\n" if "04_checks" in relative else "ok\n"
            self.write_file(relative, text)

    def write_problem_extraction_artifacts(self):
        files = [
            "intermediate/dmath/problem_extraction/ch06/01_inputs/kp-query-result.json",
            "intermediate/dmath/problem_extraction/ch06/01_inputs/full-problem-bank.md",
            "intermediate/dmath/problem_extraction/ch06/02_analysis/problem-insert-manifest.json",
            "intermediate/dmath/problem_extraction/ch06/04_checks/problem-pool-validation-report.md",
        ]
        for relative in files:
            text = "Result: PASS\n  - ERROR:   0\n" if "04_checks" in relative else "ok\n"
            self.write_file(relative, text)

    def write_validate_pool_script(self, return_code, output):
        script = self.root / "pipeline" / "scripts" / "validate-pool.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "import sys\n"
            f"print({output!r})\n"
            f"sys.exit({return_code})\n",
            encoding="utf-8",
        )

    def test_init_writes_runtime_state(self):
        code, output = self.run_cli(
            [
                "init",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--command",
                "extract-problems",
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn("Initialized", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["active_course"], "dmath")
        self.assertEqual(state["active_chapter"], "ch06")
        self.assertEqual(state["active_command"], "extract-problems")
        self.assertEqual(state["phase"], "active")
        self.assertIn(
            "intermediate/dmath/problem_extraction/ch06/01_inputs/full-problem-bank.md",
            state["required_artifacts"],
        )

    def test_guard_missing_artifacts_blocks_and_updates_state(self):
        code, output = self.run_cli(
            [
                "guard",
                "extract-problems",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--apply",
            ]
        )

        self.assertEqual(code, 2)
        self.assertIn("Result: FAIL", output)
        self.assertIn("Missing artifacts", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "blocked")
        self.assertEqual(state["last_gate_status"], "FAIL")
        self.assertIn("intermediate/dmath/problem_extraction/ch06", state["blocked_reason"])

    def test_problem_set_guard_passes_and_updates_state(self):
        self.write_problem_set_artifacts()

        code, output = self.run_cli(
            [
                "guard",
                "problem-set",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--apply",
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn("Result: PASS", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "complete")
        self.assertEqual(state["last_gate_name"], "problem-set")
        self.assertEqual(state["last_gate_status"], "PASS")
        self.assertEqual(state["blocked_reason"], "")

    def test_check_file_fail_marker_blocks(self):
        files = [
            "intermediate/dmath/extraction/ch06/01_inputs/source-scope.md",
            "intermediate/dmath/extraction/ch06/02_analysis/knowledge-points.md",
            "intermediate/dmath/extraction/ch06/02_analysis/knowledge-relationship-analysis.md",
            "intermediate/dmath/extraction/ch06/02_analysis/kp-consolidation-analysis.md",
            "intermediate/dmath/extraction/ch06/02_analysis/coverage-check.md",
            "intermediate/dmath/extraction/ch06/02_analysis/pool-insert-manifest.json",
            "intermediate/dmath/extraction/ch06/04_checks/pool-validation-report.md",
        ]
        for relative in files:
            self.write_file(relative, "ok\n")
        self.write_file(
            "intermediate/dmath/extraction/ch06/02_analysis/coverage-check.md",
            "| Category | Status |\n|---|---|\n| definitions | FAIL |\n",
        )
        self.write_file(
            "intermediate/dmath/extraction/ch06/04_checks/pool-validation-report.md",
            "Result: PASS\n  - ERROR:   0\n",
        )

        code, output = self.run_cli(
            [
                "guard",
                "extract-chapter",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--apply",
            ]
        )

        self.assertEqual(code, 2)
        self.assertIn("Blocking issues", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "blocked")
        self.assertIn("coverage-check.md", state["blocked_reason"])

    def test_zero_error_count_is_not_blocking(self):
        self.assertIsNone(lessonkit.find_blocking_marker("Result: PASS\nERROR: 0\n"))
        self.assertIsNotNone(lessonkit.find_blocking_marker("Result: PASS\nERROR: 2\n"))

    def test_default_guard_does_not_require_db(self):
        self.write_problem_extraction_artifacts()

        code, output = self.run_cli(
            [
                "guard",
                "extract-problems",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn("Result: PASS", output)

    def test_db_guard_blocks_when_db_is_missing(self):
        self.write_problem_extraction_artifacts()

        code, output = self.run_cli(
            [
                "guard",
                "extract-problems",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--db",
                "pool/dmath.db",
                "--apply",
            ]
        )

        self.assertEqual(code, 2)
        self.assertIn("DB not found", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "blocked")
        self.assertIn("DB not found", state["blocked_reason"])

    def test_db_guard_blocks_when_validate_pool_fails(self):
        self.write_problem_extraction_artifacts()
        self.write_file("pool/dmath.db", "")
        self.write_validate_pool_script(2, "=== Pool validation report ===\\nResult: FAIL")

        code, output = self.run_cli(
            [
                "guard",
                "extract-problems",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--db",
                "pool/dmath.db",
                "--apply",
            ]
        )

        self.assertEqual(code, 2)
        self.assertIn("pool validation failed", output)
        self.assertIn("Result: FAIL", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "blocked")
        self.assertIn("Result: FAIL", state["blocked_reason"])

    def test_db_guard_passes_when_validate_pool_passes(self):
        self.write_problem_extraction_artifacts()
        self.write_file("pool/dmath.db", "")
        self.write_validate_pool_script(0, "Result: PASS")

        code, output = self.run_cli(
            [
                "guard",
                "extract-problems",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--db",
                "pool/dmath.db",
                "--apply",
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn("Pool validation passed", output)
        state = lessonkit.read_state(self.root)
        self.assertEqual(state["phase"], "complete")
        self.assertEqual(state["last_gate_status"], "PASS")
        self.assertIn("validate-pool.py --db pool/dmath.db", state["last_gate_report"])

    def test_db_guard_is_not_supported_for_problem_set(self):
        self.write_problem_set_artifacts()

        code, output = self.run_cli(
            [
                "guard",
                "problem-set",
                "--course",
                "dmath",
                "--chapter",
                "ch06",
                "--db",
                "pool/dmath.db",
            ]
        )

        self.assertEqual(code, 1)
        self.assertIn("--db is only supported", output)


if __name__ == "__main__":
    unittest.main()
