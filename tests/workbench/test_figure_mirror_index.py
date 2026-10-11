"""Derived Git figure index keeps hash-named assets discoverable by owner id."""

import json
import sqlite3
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


if __name__ == "__main__":
    unittest.main()
