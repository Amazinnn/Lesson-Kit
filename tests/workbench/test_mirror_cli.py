"""CLI contract tests for `lesson-kit mirror`."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from workbench.cli import entry, mirror
from workbench.data import pool as pool_mod
from workbench import registry
from tests.workbench.fixtures import WorkspaceFixture


class MirrorCliTests(unittest.TestCase):
    def test_installed_command_list_includes_mirror(self):
        self.assertIn("mirror", entry.command_names())

    def test_parser_exposes_init_check_status_sync_and_figures(self):
        parser = mirror.build_parser()
        init = parser.parse_args(["course", "init", "--repo", "content"])
        self.assertEqual(init.action, "init")
        self.assertEqual(init.repo, "content")

        check = parser.parse_args(["course", "check", "--repo", "content", "--entity", "c02-ch01-kp-001"])
        self.assertEqual(check.action, "check")
        self.assertEqual(check.entity, "c02-ch01-kp-001")

        status = parser.parse_args(["course", "status", "--repo", "content"])
        self.assertEqual(status.action, "status")

        sync = parser.parse_args(["course", "sync", "--repo", "content", "--dry-run"])
        self.assertEqual(sync.action, "sync")
        self.assertTrue(sync.dry_run)

        figures = parser.parse_args([
            "course", "figures", "--repo", "content",
            "--direction", "pull", "--dry-run",
        ])
        self.assertEqual(figures.action, "figures")
        self.assertEqual(figures.direction, "pull")
        self.assertTrue(figures.dry_run)

    def test_figure_check_refuses_missing_or_non_file_pools_before_connecting(self):
        fixture = WorkspaceFixture()
        self.addCleanup(fixture.cleanup)
        missing_db = fixture.ws / "pool" / "missing.db"
        directory_db = fixture.ws / "pool" / "not-a-database"
        directory_db.mkdir()

        for db_path in (missing_db, directory_db):
            with self.subTest(db_path=db_path):
                registry.register(
                    str(fixture.ws), name="dmath",
                    db=str(db_path.relative_to(fixture.ws)),
                    course="dmath", chapter="ch06",
                )
                output = io.StringIO()
                with patch.object(
                    pool_mod.Pool, "connect",
                    side_effect=AssertionError("figure check must not connect"),
                ):
                    with redirect_stdout(output):
                        code = mirror.main([
                            "dmath", "figures", "--repo",
                            str(Path(fixture.tmp.name) / "content-repo"),
                            "--direction", "check",
                        ])

                self.assertEqual(code, 2)
                report = json.loads(output.getvalue())
                self.assertFalse(report["valid"])
                self.assertEqual(report["items"][0]["status"], "invalid")

        self.assertFalse(missing_db.exists())
        self.assertTrue(directory_db.is_dir())


if __name__ == "__main__":
    unittest.main()
