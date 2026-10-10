"""CLI contract tests for `lesson-kit mirror`."""

import unittest

from workbench.cli import entry, mirror


class MirrorCliTests(unittest.TestCase):
    def test_installed_command_list_includes_mirror(self):
        self.assertIn("mirror", entry.command_names())

    def test_parser_exposes_init_check_status_and_sync(self):
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


if __name__ == "__main__":
    unittest.main()
