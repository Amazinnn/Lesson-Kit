"""Focused, bounded practice context for Agent turns."""

import unittest

from tests.workbench.fixtures import WorkspaceFixture


class AgentPracticeContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def _start_six_problem_practice(self):
        from workbench.data import active_practice

        ids = [f"dmath-ch06-prob-{number:03d}" for number in range(1, 7)]
        self.pool.connect().executemany(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    problem_id,
                    '["dmath-ch06-kp-001"]',
                    f"Problem {number}",
                    f"Solution {number}",
                    "calculation",
                    "textbook",
                )
                for number, problem_id in enumerate(ids[1:], start=2)
            ],
        )
        self.pool.commit()
        active_practice.create(self.pool, {
            "source_kind": "quick",
            "source_label": "Context test",
            "kp_ids": ["dmath-ch06-kp-001"],
            "practice_mode": "immediate",
            "rating_mode": "off",
            "items": [
                {"item_type": "problem", "item_id": problem_id}
                for problem_id in ids
            ],
        })
        for position, problem_id in enumerate(ids[:-1]):
            is_last = position == len(ids) - 2
            attempt_id = self.pool.insert_attempt(
                problem_id,
                "wrong" if is_last else "mastered",
                answer_text=f"learner answer {position + 1}",
                verdict=0 if is_last else 1,
                choices=[],
            )
            active_practice.mark(
                self.pool, position, "answered", attempt_id=attempt_id
            )
        return ids

    def _context(self, problem_id, message):
        from workbench.server import context

        return context.build(self.pool, self.workspace, {
            "route": "/w/dmath/practice",
            "page_type": "practice",
            "problem_id": problem_id,
            "message": message,
        })

    def test_previous_reference_becomes_focus_with_full_settled_evidence(self):
        ids = self._start_six_problem_practice()

        result = self._context(ids[-1], "上一题为什么又错了？")

        self.assertEqual(result["anchor"]["problem_id"], ids[-1])
        self.assertEqual(result["focus"], {
            "type": "problem",
            "problem_ids": [ids[-2]],
            "basis": "user_previous_reference",
        })
        items = result["working_set"]["items"]
        self.assertEqual(
            [item["relation"] for item in items],
            ["previous_4", "previous_3", "previous_2", "previous_1", "current"],
        )
        # The oldest settled problem falls outside the four-problem bound.
        self.assertEqual(
            [item["problem"]["problem_id"] for item in items],
            ids[1:],
        )
        previous = items[-2]
        self.assertEqual(previous["problem"]["problem_text"], "Problem 5")
        self.assertEqual(previous["attempt"]["answer_text"], "learner answer 5")
        self.assertEqual(previous["attempt"]["status"], "wrong")
        self.assertEqual(previous["attempt"]["verdict"], 0)

    def test_recent_reference_focuses_the_bounded_previous_problem_group(self):
        ids = self._start_six_problem_practice()

        result = self._context(ids[-1], "前几题我是不是都用了同一种方法？")

        self.assertEqual(result["focus"], {
            "type": "problem",
            "problem_ids": ids[1:-1],
            "basis": "user_recent_reference",
        })
        self.assertEqual(result["working_set"]["kind"], "practice")

    def test_current_page_remains_default_focus_when_message_has_no_reference(self):
        ids = self._start_six_problem_practice()

        result = self._context(ids[-1], "这题为什么这样做？")

        self.assertEqual(result["focus"], {
            "type": "problem",
            "problem_ids": [ids[-1]],
            "basis": "page_anchor",
        })

    def test_building_working_context_is_read_only(self):
        ids = self._start_six_problem_practice()
        before = len(self.pool.attempts(ids[-2]))

        self._context(ids[-1], "上一道题的作答结果是什么？")

        self.assertEqual(len(self.pool.attempts(ids[-2])), before)
        active = self.pool.connect().execute(
            "SELECT cursor FROM active_practice WHERE singleton=1"
        ).fetchone()
        self.assertEqual(active["cursor"], 5)


if __name__ == "__main__":
    unittest.main()
