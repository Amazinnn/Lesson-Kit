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
        self.assertEqual(len(overview["activity"]), 84)
        self.assertEqual(sum(day["attempts"] for day in overview["activity"]), 1)

    def test_attempt_views_admit_truncation_at_the_load_limit(self):
        from workbench.data import records
        from workbench.server import records as records_view

        self.pool.insert_attempt("dmath-ch06-prob-001", "answered")
        overview = records.overview(self.pool)

        capped = records_view.content(
            "dmath", overview, view="attempts", limit=1)
        self.assertIn("已载入最近 1 条", capped)
        self.assertIn("更早的记录未显示", capped)
        wrong_capped = records_view.content(
            "dmath", overview, view="wrong", limit=1)
        self.assertIn("已载入最近 1 条", wrong_capped)

        roomy = records_view.content(
            "dmath", overview, view="attempts", limit=50)
        self.assertNotIn("更早的记录未显示", roomy)


    def test_same_practice_set_keeps_each_completed_result_separate(self):
        from workbench.data import records
        from workbench.server import records as records_view

        self.pool.insert_attempt(
            "dmath-ch06-prob-001", "answered", answer_text="first",
            verdict=True, choices=["A"],
        )
        first_attempt = self.pool.connect().execute(
            "SELECT id FROM problem_attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()["id"]
        self.pool.connect().execute(
            "INSERT INTO feedback_events "
            "(item_type, item_id, rating, attempt_id) VALUES ('problem', ?, 4, ?)",
            ("dmath-ch06-prob-001", first_attempt),
        )
        self.pool.connect().execute(
            "INSERT INTO practice_runs "
            "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            "rating_mode, items_json, status, started_at, finished_at) "
            "VALUES ('practice_set', 'ps-001', '第一章试卷', '[]', 'exam', "
            "'immediate', ?, 'completed', '2026-09-20 10:00:00', '2026-09-20 10:20:00')",
            ('[{"item_type":"problem","item_id":"dmath-ch06-prob-001",'
             '"direction":"","state":"answered","attempt_id":%d}]' % first_attempt,),
        )

        self.pool.insert_attempt(
            "dmath-ch06-prob-001", "answered", answer_text="second",
            verdict=False, choices=["B"],
        )
        second_attempt = self.pool.connect().execute(
            "SELECT id FROM problem_attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()["id"]
        self.pool.connect().execute(
            "INSERT INTO feedback_events "
            "(item_type, item_id, rating, attempt_id) VALUES ('problem', ?, 2, ?)",
            ("dmath-ch06-prob-001", second_attempt),
        )
        self.pool.connect().execute(
            "INSERT INTO practice_runs "
            "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            "rating_mode, items_json, status, started_at, finished_at) "
            "VALUES ('practice_set', 'ps-001', '第一章试卷', '[]', 'exam', "
            "'immediate', ?, 'completed', '2026-09-29 10:00:00', '2026-09-29 10:20:00')",
            ('[{"item_type":"problem","item_id":"another-problem",'
             '"direction":"","state":"stuck","attempt_id":%d}]' % second_attempt,),
        )

        overview = records.overview(self.pool)
        paper = overview["practice_sets"][0]
        self.assertEqual(paper["source_ref"], "ps-001")
        self.assertEqual(paper["count"], 2)
        self.assertTrue(paper["content_changed"])
        self.assertEqual(paper["runs"][0]["accuracy"], 0.0)
        self.assertEqual(paper["runs"][0]["average_rating"], 2.0)

        rendered = records_view.content("dmath", overview, view="runs")
        self.assertIn("第一章试卷", rendered)
        self.assertIn("题目或顺序曾变化", rendered)

    def test_unchanged_paper_runs_merge_without_the_warning(self):
        from workbench.data import records
        from workbench.server import records as records_view

        for label, started in (("旧的一轮", "2026-09-20 10:00:00"),
                               ("新的一轮", "2026-09-29 10:00:00")):
            self.pool.insert_attempt(
                "dmath-ch06-prob-001", "answered", answer_text=label,
                verdict=True, choices=["A"])
            attempt = self.pool.connect().execute(
                "SELECT id FROM problem_attempts ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
            items_json = ('[{"item_type":"problem","item_id":"dmath-ch06-prob-001",'
                          '"direction":"","state":"answered","attempt_id":%d}]' % attempt)
            self.pool.connect().execute(
                "INSERT INTO practice_runs "
                "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
                "rating_mode, items_json, status, started_at, finished_at) "
                "VALUES ('practice_set', 'ps-001', '第一章试卷', '[]', 'exam', "
                "'immediate', ?, 'completed', ?, ?)",
                (items_json, started, started))

        overview = records.overview(self.pool)
        paper = overview["practice_sets"][0]
        self.assertEqual(paper["count"], 2)
        self.assertFalse(paper["content_changed"])
        self.assertEqual(paper["runs"][0]["accuracy"], 1.0)

        rendered = records_view.content("dmath", overview, view="runs")
        self.assertNotIn("题目或顺序曾变化", rendered)

    def test_freed_paper_ids_are_not_reused_after_the_paper_is_deleted(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "会删掉的卷子", ["dmath-ch06-prob-001"])
        old_id = saved["practice_set_id"]
        self.pool.connect().execute(
            "INSERT INTO practice_runs "
            "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            "rating_mode, items_json, status, started_at, finished_at) "
            "VALUES ('practice_set', ?, '旧卷', '[]', 'exam', 'immediate', "
            "'[]', 'completed', '2026-09-20 10:00:00', '2026-09-20 10:20:00')",
            (old_id,),
        )
        practice_sets.delete_saved(self.pool, old_id)

        recreated = practice_sets.create_saved(
            self.pool, "重建的卷子", ["dmath-ch06-prob-001"])
        self.assertNotEqual(recreated["practice_set_id"], old_id)
        self.assertEqual(recreated["practice_set_id"], "ps-002")


if __name__ == "__main__":
    unittest.main()

    def test_late_utc_attempts_land_on_the_local_date(self):
        """created_at is stored UTC; 16:30 UTC is next morning for UTC+8."""
        from datetime import datetime, timedelta, timezone
        from workbench.data import records

        self.pool.insert_attempt("dmath-ch06-prob-001", "answered")
        stamped = (datetime.now(timezone.utc) - timedelta(days=1)
                   ).replace(hour=16, minute=30, second=0, microsecond=0)
        self.pool.connect().execute(
            "UPDATE problem_attempts SET created_at=? "
            "WHERE id=(SELECT MAX(id) FROM problem_attempts)",
            (stamped.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        self.pool.commit()

        overview = records.overview(self.pool)
        local_day = stamped.astimezone().date().isoformat()
        self.assertEqual(
            sum(day["attempts"] for day in overview["trend"]
                if day["date"] == local_day), 1)
        self.assertEqual(
            sum(day["attempts"] for day in overview["activity"]
                if day["date"] == local_day), 1)
        self.assertEqual(overview["runs"][0]["status"], "completed")
        self.assertEqual(overview["records"][0]["answer_text"], "my answer")

        rendered = records_view.content("dmath", overview)
        self.assertIn("练习 / 试卷", rendered)
        self.assertIn("最近 14 天", rendered)
        self.assertIn("作答日历", rendered)
        self.assertIn("record-verdict-bad", rendered)
        wrong = records_view.content("dmath", overview, view="wrong")
        self.assertIn("my answer", wrong)
        self.assertIn("再做一次", rendered)
        wrong = records_view.content("dmath", overview, view="wrong")
        self.assertIn("my answer", wrong)


if __name__ == "__main__":
    unittest.main()
