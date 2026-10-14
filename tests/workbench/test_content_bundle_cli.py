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


if __name__ == "__main__":
    unittest.main()
