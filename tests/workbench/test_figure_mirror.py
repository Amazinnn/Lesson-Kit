"""Version-controlled binary figure projection and legacy workspace compatibility."""

import json
import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import figure_mirror
from workbench.data import pool as pool_mod


class FigureMirrorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.ws = self.fixture.ws
        self.repo = Path(self.fixture.tmp.name) / "content-repo"
        self.pool = pool_mod.Pool(
            root=self.ws,
            db_path=self.fixture.db_path,
            course="dmath",
            chapter="ch06",
        )
        self.logical = "dmath/ch06/dmath-ch06-prob-001/fig-001.png"
        self._set_paths([self.logical])

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def _set_paths(self, paths):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE problems SET figure_paths=? WHERE problem_id='dmath-ch06-prob-001'",
                (json.dumps(paths),),
            )
            conn.commit()
        finally:
            conn.close()

    def _canonical(self, logical=None):
        return self.ws / "figures" / (logical or self.logical)

    def _legacy(self, logical=None):
        return self.ws / ".lessonkit" / "figures" / (logical or self.logical)

    def _repo(self, logical=None):
        return self.repo / "figures" / (logical or self.logical)

    @staticmethod
    def _write(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def test_push_imports_a_legacy_runtime_figure(self):
        self._write(self._legacy(), b"legacy-bytes")

        report = figure_mirror.sync(self.pool, self.repo, "push")

        self.assertTrue(report["valid"])
        self.assertEqual(report["applied"], 1)
        self.assertEqual(self._repo().read_bytes(), b"legacy-bytes")
        self.assertEqual(report["items"][0]["source"], "legacy_workspace")

    def test_push_prefers_the_new_top_level_workspace_figure(self):
        self._write(self._legacy(), b"old-runtime-copy")
        self._write(self._canonical(), b"edited-canonical-copy")

        report = figure_mirror.sync(self.pool, self.repo, "push")

        self.assertTrue(report["valid"])
        self.assertEqual(self._repo().read_bytes(), b"edited-canonical-copy")
        self.assertEqual(report["items"][0]["source"], "workspace")

    def test_pull_updates_canonical_and_legacy_compatibility_copies(self):
        self._write(self._repo(), b"github-edited-bytes")
        self._write(self._legacy(), b"old-local-bytes")

        report = figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertTrue(report["valid"])
        self.assertEqual(report["applied"], 1)
        self.assertEqual(self._canonical().read_bytes(), b"github-edited-bytes")
        self.assertEqual(self._legacy().read_bytes(), b"github-edited-bytes")

    def test_check_is_read_only_and_reports_differences(self):
        self._write(self._canonical(), b"local")
        self._write(self._repo(), b"repository")

        report = figure_mirror.sync(self.pool, self.repo, "check")

        self.assertTrue(report["valid"])
        self.assertEqual(report["items"][0]["status"], "different")
        self.assertEqual(self._canonical().read_bytes(), b"local")
        self.assertEqual(self._repo().read_bytes(), b"repository")

    def test_dry_run_writes_nothing(self):
        self._write(self._legacy(), b"legacy-bytes")

        report = figure_mirror.sync(self.pool, self.repo, "push", dry_run=True)

        self.assertTrue(report["valid"])
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["items"][0]["status"], "create")
        self.assertFalse(self._repo().exists())

    def test_one_missing_source_blocks_the_whole_push_before_writes(self):
        missing = "dmath/ch06/dmath-ch06-prob-001/fig-002.png"
        self._set_paths([self.logical, missing])
        self._write(self._canonical(), b"new-first")
        self._write(self._repo(), b"old-first")

        report = figure_mirror.sync(self.pool, self.repo, "push")

        self.assertFalse(report["valid"])
        self.assertEqual(self._repo().read_bytes(), b"old-first")
        statuses = {item["logical"]: item["status"] for item in report["items"]}
        self.assertEqual(statuses[self.logical], "update")
        self.assertEqual(statuses[missing], "invalid")

    def test_foreign_course_and_traversal_paths_are_invalid(self):
        for logical in (
            "other/ch06/fig.png",
            "dmath/ch06/../escape.png",
            "dmath\\ch06\\escape.png",
        ):
            with self.subTest(logical=logical):
                self._set_paths([logical])
                report = figure_mirror.plan(self.pool, self.repo, "check")
                self.assertFalse(report["valid"])
                self.assertEqual(report["items"][0]["status"], "invalid")

    def test_shared_logical_figure_is_copied_once_and_keeps_all_owners(self):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE knowledge_points SET figure_paths=? "
                "WHERE kp_id='dmath-ch06-kp-001'",
                (json.dumps([self.logical]),),
            )
            conn.commit()
        finally:
            conn.close()
        self._write(self._legacy(), b"shared")

        report = figure_mirror.sync(self.pool, self.repo, "push")

        self.assertEqual(len(report["items"]), 1)
        owners = {(item["owner_type"], item["owner_id"])
                  for item in report["items"][0]["owners"]}
        self.assertEqual(owners, {
            ("kp", "dmath-ch06-kp-001"),
            ("problem", "dmath-ch06-prob-001"),
        })
        self.assertEqual(self._repo().read_bytes(), b"shared")


if __name__ == "__main__":
    unittest.main()
