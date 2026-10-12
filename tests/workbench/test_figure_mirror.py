"""Version-controlled binary figure projection and legacy workspace compatibility."""

import json
import os
import sqlite3
import subprocess
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

    def _redirect_directory(self, link, target):
        target.mkdir(parents=True, exist_ok=True)
        link.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            quote = lambda path: "'" + str(path).replace("'", "''") + "'"
            command = (
                f"New-Item -ItemType Junction -Path {quote(link)} "
                f"-Target {quote(target)} | Out-Null"
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            link.symlink_to(target, target_is_directory=True)

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

    def test_pull_refuses_changed_bytes_at_a_legacy_hash_identity(self):
        logical = (
            "dmath/ch06/ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad.png"
        )
        self._set_paths([logical])
        canonical, legacy, repository = (
            self._canonical(logical), self._legacy(logical), self._repo(logical)
        )
        self._write(canonical, b"abc")
        self._write(legacy, b"abc")
        self._write(repository, b"edited-repository-bytes")

        report = figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertFalse(report["valid"])
        self.assertEqual(report["items"][0]["status"], "conflict")
        self.assertEqual(canonical.read_bytes(), b"abc")
        self.assertEqual(legacy.read_bytes(), b"abc")
        self.assertEqual(repository.read_bytes(), b"edited-repository-bytes")

    def test_pull_refuses_a_legacy_hash_without_a_workspace_baseline(self):
        logical = (
            "dmath/ch06/ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad.png"
        )
        self._set_paths([logical])
        repository = self._repo(logical)
        self._write(repository, b"repo-only-bytes")

        report = figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertFalse(report["valid"])
        self.assertEqual(report["items"][0]["status"], "conflict")
        self.assertFalse(self._canonical(logical).exists())
        self.assertFalse(self._legacy(logical).exists())
        self.assertEqual(repository.read_bytes(), b"repo-only-bytes")

    def test_a_workspace_hash_copy_can_seed_and_restore_matching_repository_bytes(self):
        logical = (
            "dmath/ch06/ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad.png"
        )
        self._set_paths([logical])
        canonical, legacy, repository = (
            self._canonical(logical), self._legacy(logical), self._repo(logical)
        )
        self._write(canonical, b"abc")

        pushed = figure_mirror.sync(self.pool, self.repo, "push")
        pulled = figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertTrue(pushed["valid"])
        self.assertEqual(repository.read_bytes(), b"abc")
        self.assertTrue(pulled["valid"])
        self.assertEqual(canonical.read_bytes(), b"abc")
        self.assertEqual(legacy.read_bytes(), b"abc")

    def test_push_refuses_changed_bytes_at_a_legacy_hash_identity(self):
        logical = (
            "dmath/ch06/ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad.png"
        )
        self._set_paths([logical])
        canonical, legacy, repository = (
            self._canonical(logical), self._legacy(logical), self._repo(logical)
        )
        self._write(canonical, b"edited-workspace-bytes")
        self._write(legacy, b"edited-workspace-bytes")
        self._write(repository, b"abc")

        report = figure_mirror.sync(self.pool, self.repo, "push")

        self.assertFalse(report["valid"])
        self.assertEqual(report["items"][0]["status"], "conflict")
        self.assertEqual(canonical.read_bytes(), b"edited-workspace-bytes")
        self.assertEqual(legacy.read_bytes(), b"edited-workspace-bytes")
        self.assertEqual(repository.read_bytes(), b"abc")

    def test_top_level_figure_root_cannot_redirect_outside_workspace(self):
        outside = Path(self.fixture.tmp.name) / "outside-top-level"
        self._redirect_directory(self.ws / "figures", outside)
        self._write(self._repo(), b"repository-bytes")

        with self.assertRaises(figure_mirror.FigureMirrorError):
            figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertFalse((outside / self.logical).exists())

    def test_legacy_figure_root_cannot_redirect_outside_workspace(self):
        outside = Path(self.fixture.tmp.name) / "outside-legacy"
        self._redirect_directory(self.ws / ".lessonkit" / "figures", outside)
        self._write(self._repo(), b"repository-bytes")

        with self.assertRaises(figure_mirror.FigureMirrorError):
            figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertFalse((outside / self.logical).exists())
        self.assertFalse(self._canonical().exists())

    def test_repository_figure_root_cannot_redirect_outside_checkout(self):
        outside = Path(self.fixture.tmp.name) / "outside-repository"
        self._redirect_directory(self.repo / "figures", outside)
        self._write(outside / self.logical, b"repository-bytes")

        with self.assertRaises(figure_mirror.FigureMirrorError):
            figure_mirror.sync(self.pool, self.repo, "pull")

        self.assertFalse(self._canonical().exists())
        self.assertFalse(self._legacy().exists())

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
