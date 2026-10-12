"""Derived Git figure index keeps hash-named assets discoverable by owner id."""

import json
import os
import sqlite3
import subprocess
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import figure_mirror
from workbench.data import pool as pool_mod


class FigureMirrorIndexTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.repo = Path(self.fixture.tmp.name) / "content-repo"
        self.pool = pool_mod.Pool(
            root=self.fixture.ws,
            db_path=self.fixture.db_path,
            course="dmath",
            chapter="ch06",
        )
        self.logical = "dmath/ch06/deadbeef.png"
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE problems SET figure_paths=? WHERE problem_id='dmath-ch06-prob-001'",
                (json.dumps([self.logical]),),
            )
            conn.commit()
        finally:
            conn.close()
        source = self.fixture.ws / ".lessonkit" / "figures" / self.logical
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"png-bytes")

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def _set_all_paths(self, paths):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            encoded = json.dumps(paths)
            conn.execute("UPDATE problems SET figure_paths=?", (encoded,))
            conn.execute("UPDATE knowledge_points SET figure_paths=?", (encoded,))
            conn.commit()
        finally:
            conn.close()

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

    def test_push_writes_owner_searchable_index(self):
        report = figure_mirror.sync(self.pool, self.repo, "push")

        index_path = self.repo / "figures" / "dmath" / "_index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(report["index"]["status"], "applied")
        self.assertEqual(index["schema_version"], 1)
        self.assertEqual(index["course_id"], "dmath")
        self.assertEqual(index["figures"], [{
            "logical_path": self.logical,
            "owners": [{
                "owner_type": "problem",
                "owner_id": "dmath-ch06-prob-001",
            }],
        }])

    def test_check_reports_a_stale_index_without_rewriting_it(self):
        figure_mirror.sync(self.pool, self.repo, "push")
        index_path = self.repo / "figures" / "dmath" / "_index.json"
        index_path.write_text("{}\n", encoding="utf-8")

        report = figure_mirror.sync(self.pool, self.repo, "check")

        self.assertEqual(report["index"]["status"], "different")
        self.assertEqual(index_path.read_text(encoding="utf-8"), "{}\n")

    def test_empty_push_rejects_an_index_root_outside_the_checkout(self):
        self._set_all_paths([])
        self.assertEqual(figure_mirror.references(self.pool), [])
        outside_course = Path(self.fixture.tmp.name) / "outside-index-course"
        self._redirect_directory(
            self.repo / "figures" / "dmath", outside_course
        )
        outside_index = outside_course / "_index.json"
        outside_index.write_text("keep\n", encoding="utf-8")

        with self.assertRaises(figure_mirror.FigureMirrorError):
            figure_mirror.sync(self.pool, self.repo, "push")

        self.assertEqual(outside_index.read_text(encoding="utf-8"), "keep\n")

    def test_empty_or_unmanaged_databases_are_not_valid_empty_figure_pools(self):
        empty_db = self.fixture.ws / "pool" / "empty.db"
        empty_db.touch()
        unmanaged_db = self.fixture.ws / "pool" / "unmanaged.db"
        conn = sqlite3.connect(unmanaged_db)
        try:
            conn.execute("CREATE TABLE unrelated (value TEXT)")
            conn.commit()
        finally:
            conn.close()

        for db_path in (empty_db, unmanaged_db):
            with self.subTest(db_path=db_path):
                pool = pool_mod.Pool(
                    root=self.fixture.ws,
                    db_path=db_path,
                    course="dmath",
                    chapter="ch06",
                )
                try:
                    report = figure_mirror.plan(pool, self.repo, "check")
                finally:
                    pool.close()

                self.assertFalse(report["valid"])
                self.assertEqual(report["items"][0]["status"], "invalid")

    def test_old_pool_without_figure_paths_columns_has_no_references(self):
        old_db = self.fixture.ws / "pool" / "pre-figure-paths.db"
        conn = sqlite3.connect(old_db)
        try:
            conn.execute("CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE problems (problem_id TEXT PRIMARY KEY)")
            conn.commit()
        finally:
            conn.close()
        pool = pool_mod.Pool(
            root=self.fixture.ws,
            db_path=old_db,
            course="dmath",
            chapter="ch06",
        )
        try:
            report = figure_mirror.plan(pool, self.repo, "check")
        finally:
            pool.close()

        self.assertTrue(report["valid"])
        self.assertEqual(report["items"], [])


if __name__ == "__main__":
    unittest.main()
