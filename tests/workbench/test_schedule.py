"""SM-2 variant scheduling tests (TDD, red first)."""

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


schedule = load_script("wb_schedule", Path("workbench/domain/schedule.py"))


def new_state(repetitions=0, ease=2.5, interval_days=0.0, state="learning"):
    return {
        "item_type": "problem",
        "item_id": "p1",
        "direction": "",
        "state": state,
        "repetitions": repetitions,
        "ease": ease,
        "interval_days": interval_days,
        "due_at": None,
        "last_rating": None,
        "last_reviewed_at": None,
    }


NOW = date(2026, 8, 16)


class ScheduleTests(unittest.TestCase):
    def test_first_correct_schedules_one_day(self):
        result = schedule.after_result(new_state(), "correct", NOW)
        self.assertEqual(result["repetitions"], 1)
        self.assertEqual(result["interval_days"], 1.0)
        self.assertEqual(result["due_at"], "2026-08-17")
        self.assertEqual(result["state"], "review")
        self.assertEqual(result["ease"], 2.6)

    def test_second_correct_schedules_six_days(self):
        state = new_state(repetitions=1, ease=2.6, interval_days=1.0)
        result = schedule.after_result(state, "correct", NOW)
        self.assertEqual(result["repetitions"], 2)
        self.assertEqual(result["interval_days"], 6.0)

    def test_third_correct_multiplies_by_ease(self):
        state = new_state(repetitions=2, ease=2.7, interval_days=6.0)
        result = schedule.after_result(state, "correct", NOW)
        self.assertEqual(result["interval_days"], 16.0)
        self.assertEqual(result["due_at"], "2026-09-01")

    def test_wrong_resets_to_relearning(self):
        state = new_state(repetitions=3, ease=2.6, interval_days=16.0)
        result = schedule.after_result(state, "wrong", NOW)
        self.assertEqual(result["state"], "relearning")
        self.assertEqual(result["repetitions"], 0)
        self.assertEqual(result["interval_days"], 0.0)
        self.assertEqual(result["due_at"], "2026-08-16")
        self.assertEqual(result["ease"], 2.4)

    def test_stuck_counts_as_wrong(self):
        result = schedule.after_result(new_state(), "stuck", NOW)
        self.assertEqual(result["state"], "relearning")

    def test_skip_leaves_schedule_unchanged(self):
        state = new_state(repetitions=2, ease=2.6, interval_days=6.0)
        result = schedule.after_result(state, "skip", NOW)
        self.assertEqual(result, state)

    def test_rating_five_grows_interval(self):
        state = new_state(repetitions=1, ease=2.5, interval_days=1.0)
        result = schedule.after_result(state, 5, NOW)
        self.assertEqual(result["repetitions"], 2)
        self.assertEqual(result["last_rating"], 5)

    def test_rating_one_resets(self):
        state = new_state(repetitions=2, ease=2.6, interval_days=6.0)
        result = schedule.after_result(state, 1, NOW)
        self.assertEqual(result["state"], "relearning")
        self.assertEqual(result["repetitions"], 0)

    def test_ease_floor(self):
        state = new_state(repetitions=5, ease=1.4, interval_days=8.0)
        result = schedule.after_result(state, "wrong", NOW)
        self.assertEqual(result["ease"], 1.3)


if __name__ == "__main__":
    unittest.main()
