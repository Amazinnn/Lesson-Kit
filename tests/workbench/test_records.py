"""Records stay behind one small data/view boundary."""

import sys
import unittest

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class RecordsBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.server import api
        self.pool = api._pool_for({
            "path": str(self.fixture.ws),
            "db": "pool/dmath.db",
            "active_course": "dmath",
            "active_chapter": "ch06",
        })

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_legacy_query_alias_and_records_renderer_share_the_new_boundary(self):
        from workbench.data import queries, records
        from workbench.server import records as records_view

        self.assertIs(queries.records_overview, records.overview)
        self.pool.insert_attempt(
            "dmath-ch06-prob-001", "answered", answer_text="my answer",
            verdict=True, choices=["A"],
        )

        overview = records.overview(self.pool)
        self.assertEqual(overview["count"], 1)
        self.assertEqual(overview["records"][0]["answer_text"], "my answer")

        rendered = records_view.content("dmath", overview)
        self.assertIn("my answer", rendered)
        self.assertIn("record-verdict-ok", rendered)


if __name__ == "__main__":
    unittest.main()
