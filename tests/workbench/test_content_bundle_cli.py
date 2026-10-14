"""Installed CLI path for Git-reviewed content-bundle manifests."""

import contextlib
import io
import json
import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture
from workbench.cli import entry


class ContentBundleCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.db_path = self.fixture.db_path
        self.tmp = Path(self.fixture.tmp.name)

    def tearDown(self):
        self.fixture.cleanup()

    def count(self, table):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()

    def write_manifest(self, payload, name="bundle.json"):
        path = self.tmp / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def run_entry(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = entry.lesson_kit_main(list(args))
        return code, json.loads(output.getvalue())

    def bundle(self):
        return {
            "kind": "content-bundle",
            "chapter": "ch06",
            "knowledge_points": [
                {
                    "key": "new-kp",
                    "knowledge_item": "Git reviewed concept",
                    "body": "The reviewed source closes this concept.",
                }
            ],
        }

    def problem_bundle(self):
        payload = self.bundle()
        payload["problems"] = [
            {
                "key": "new-problem",
                "kp_ids": ["new-kp"],
                "problem_text": "Explain the Git reviewed concept.",
                "solution": "It enters through governed ingest.",
                "problem_type": "explanation",
                "source_kind": "original",
                "origin_kind": "generated_ungrounded",
                "solution_origin": "generated",
            }
        ]
        return payload

    def selection(self):
        return {
            "kind": "practice-set-selection",
            "chapter": "ch06",
            "title": "Reviewed set",
            "total_points": 10,
            "items": [{"problem_key": "new-problem", "points": 10}],
        }

    def test_check_is_read_only_and_plans_canonical_identity(self):
        path = self.write_manifest(self.bundle())
        before = (self.count("knowledge_points"), self.count("ingest_batches"))

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(path)
        )

        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["knowledge_points"][0]["kp_id"], "dmath-ch06-kp-002")
        self.assertEqual(
            (self.count("knowledge_points"), self.count("ingest_batches")), before
        )
        self.assertFalse(Path(str(self.db_path) + ".ingest-backup").exists())

    def test_apply_reuses_governed_batch_and_backup(self):
        path = self.write_manifest(self.bundle())
        backup = self.tmp / "reviewed-bundle-backup.db"

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(path),
            "--apply", "--backup", str(backup),
        )

        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "content-bundle")
        self.assertEqual(result["counts"]["knowledge_points"], 1)
        self.assertEqual(self.count("knowledge_points"), 2)
        self.assertEqual(self.count("ingest_batches"), 1)
        self.assertTrue(backup.is_file())

    def test_git_authored_bundle_cannot_supply_canonical_id(self):
        payload = self.bundle()
        payload["knowledge_points"][0]["kp_id"] = "dmath-ch06-kp-999"
        path = self.write_manifest(payload)
        before = (self.count("knowledge_points"), self.count("ingest_batches"))

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(path), "--apply"
        )

        self.assertEqual(code, 2)
        self.assertFalse(result["ok"])
        self.assertIn("kp_id is not allowed", result["errors"][0])
        self.assertEqual(
            (self.count("knowledge_points"), self.count("ingest_batches")), before
        )

    def test_selection_check_resolves_local_key_without_writes(self):
        bundle = self.write_manifest(self.problem_bundle())
        selection = self.write_manifest(self.selection(), "selection.json")
        before = (self.count("problems"), self.count("ingest_batches"))

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(bundle),
            "--selection", str(selection),
        )

        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["selection"][0]["problem_key"], "new-problem")
        self.assertTrue(result["selection"][0]["problem_id"].startswith("dmath-ch06-prob-"))
        self.assertEqual((self.count("problems"), self.count("ingest_batches")), before)

    def test_selection_apply_renders_through_existing_practice_set(self):
        bundle = self.write_manifest(self.problem_bundle())
        selection = self.write_manifest(self.selection(), "selection.json")
        student = self.tmp / "student.md"
        solutions = self.tmp / "solutions.md"

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(bundle), "--apply",
            "--selection", str(selection),
            "--student-out", str(student), "--solutions-out", str(solutions),
        )

        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["selection"]["total_points"], 10)
        self.assertEqual(len(result["selection"]["items"]), 1)
        problem_id = result["selection"]["items"][0]["problem_id"]
        self.assertTrue(problem_id.startswith("dmath-ch06-prob-"))
        self.assertIn("Explain the Git reviewed concept.", student.read_text(encoding="utf-8"))
        self.assertNotIn(problem_id, student.read_text(encoding="utf-8"))
        self.assertIn("It enters through governed ingest.", solutions.read_text(encoding="utf-8"))

    def test_selection_rejects_unknown_local_key(self):
        bundle = self.write_manifest(self.problem_bundle())
        payload = self.selection()
        payload["items"][0]["problem_key"] = "missing"
        selection = self.write_manifest(payload, "selection.json")

        code, result = self.run_entry(
            "ingest", "dmath", "bundle", "--input", str(bundle),
            "--selection", str(selection),
        )

        self.assertEqual(code, 2)
        self.assertFalse(result["ok"])
        self.assertIn("unknown problem_key", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
