"""Agent context reads the same durable learning state the UI uses."""

import sys
import unittest

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class CurrentLearningContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.server import api
        self.workspace = {
            "name": "dmath",
            "path": str(self.fixture.ws),
            "db": "pool/dmath.db",
            "active_course": "dmath",
            "active_chapter": "ch06",
        }
        self.pool = api._pool_for(self.workspace)

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_practice_context_prefers_durable_progress_and_keeps_visible_filters(self):
        from workbench.data import active_practice
        from workbench.server import context

        active_practice.create(self.pool, {
            "source_kind": "quick",
            "kp_ids": ["dmath-ch06-kp-001"],
            "practice_mode": "exam",
            "rating_mode": "immediate",
            "items": [
                {"item_type": "problem", "item_id": "dmath-ch06-prob-001"},
            ],
        })

        built = context.build(self.pool, self.workspace, {
            "page_type": "practice",
            "route": "/w/dmath/practice",
            "problem_id": "dmath-ch06-prob-001",
            "progress": {"seen": 999},
            "selected_kp_ids": ["dmath-ch06-kp-001"],
            "practice_selection": {
                "kp_ids": ["dmath-ch06-kp-001"],
                "practice_mode": "exam",
                "count": 10,
                "filters": {
                    "source_kinds": ["final"],
                    "exam_years": ["2024"],
                    "docs": ["题库/final.md"],
                    "picked_problem_ids": ["dmath-ch06-prob-001"],
                },
            },
        })

        self.assertEqual(built["current"]["progress"]["total"], 1)
        self.assertNotIn("seen", built["current"]["progress"])
        self.assertEqual(
            built["current"]["active_practice"]["items"][0]["item_id"],
            "dmath-ch06-prob-001",
        )
        self.assertEqual(
            built["current"]["selection"]["filters"]["source_kinds"], ["final"])
        self.assertEqual(
            built["selection"]["kp_ids"], ["dmath-ch06-kp-001"])

    def test_saved_paper_context_reads_managed_paper_not_dom_text(self):
        from workbench.data import practice_sets
        from workbench.server import context

        saved = practice_sets.create_saved(
            self.pool, "计数热身卷", ["dmath-ch06-prob-001"])

        built = context.build(self.pool, self.workspace, {
            "page_type": "practice-sets",
            "practice_set_id": saved["practice_set_id"],
        })

        self.assertEqual(
            built["current"]["practice_sets"][0]["practice_set_id"], "ps-001")
        self.assertEqual(built["current"]["selected"]["title"], "计数热身卷")
        self.assertEqual(
            built["current"]["selected"]["problems"][0]["problem_id"],
            "dmath-ch06-prob-001",
        )

    def test_records_context_contains_recent_durable_attempts(self):
        from workbench.data import attempts
        from workbench.server import context

        attempts.record_result(
            self.pool, "dmath-ch06-prob-001", "stuck",
            note="不会从哪一步开始")

        built = context.build(self.pool, self.workspace, {
            "page_type": "records",
            "records_problem_id": "dmath-ch06-prob-001",
        })

        self.assertEqual(built["current"]["count"], 1)
        self.assertEqual(
            built["current"]["records"][0]["problem_id"],
            "dmath-ch06-prob-001",
        )
        self.assertEqual(built["current"]["records"][0]["status"], "stuck")

    def test_kps_context_resolves_only_selected_existing_knowledge_points(self):
        from workbench.server import context

        built = context.build(self.pool, self.workspace, {
            "page_type": "kps",
            "selected_kp_ids": [
                "dmath-ch06-kp-001", "missing", "dmath-ch06-kp-001",
            ],
        })

        self.assertEqual(
            [kp["kp_id"] for kp in built["current"]["selected_knowledge_points"]],
            ["dmath-ch06-kp-001"],
        )


if __name__ == "__main__":
    unittest.main()
