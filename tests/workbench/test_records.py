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
        from workbench.data import active_practice, queries, records
        from workbench.server import records as records_view

        self.assertIs(queries.records_overview, records.overview)
        self.pool.insert_attempt(
            "dmath-ch06-prob-001", "answered", answer_text="my answer",
            verdict=False, choices=["A"],
        )
        active_practice.create(self.pool, {
            "source_kind": "quick",
            "kp_ids": ["dmath-ch06-kp-001"],
            "practice_mode": "exam",
            "rating_mode": "immediate",
            "items": [{"item_type": "problem", "item_id": "dmath-ch06-prob-001"}],
        })
        active_practice.mark(self.pool, 0, "stuck")

        overview = records.overview(self.pool)
        self.assertEqual(overview["count"], 1)
        self.assertEqual(overview["summary"]["attempts"], 1)
        self.assertEqual(sum(day["attempts"] for day in overview["trend"]), 1)
        self.assertEqual(overview["runs"][0]["status"], "completed")
        self.assertEqual(overview["records"][0]["answer_text"], "my answer")

        rendered = records_view.content("dmath", overview)
        self.assertIn("练习 / 试卷", rendered)
        self.assertIn("最近 14 天", rendered)
        self.assertIn("record-verdict-bad", rendered)
        wrong = records_view.content("dmath", overview, view="wrong")
        self.assertIn("my answer", wrong)


if __name__ == "__main__":
    unittest.main()
