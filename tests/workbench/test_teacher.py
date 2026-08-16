"""Teacher instruction rendering tests (TDD, red first)."""

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


teacher = load_script("wb_teacher", Path("workbench/bridge/teacher.py"))


EXPLAIN_CONTEXT = {
    "problem_text": "Count the pairs (a, b) with a < b from {1..5}.",
    "solution": "By the product rule: 5 choose 2 = 10.",
    "kp_ids": ["dmath-ch06-kp-001"],
    "learner_note": "I do not see why order matters.",
    "weak_signals": [{"kp_id": "dmath-ch06-kp-001", "signal_type": "weak_node", "note": "confused"}],
    "recent_attempts": [{"result": "wrong", "note": "stuck"}],
}


class TeacherTests(unittest.TestCase):
    def test_explain_instruction_contains_conduct_rules(self):
        text = teacher.render("explain", EXPLAIN_CONTEXT, "out.md").lower()
        self.assertIn("what the learner already knows", text)
        self.assertIn("never guess", text)
        self.assertIn("cite the source", text)
        self.assertIn("comprehension", text)

    def test_explain_instruction_contains_context(self):
        text = teacher.render("explain", EXPLAIN_CONTEXT, "out.md")
        self.assertIn("Count the pairs", text)
        self.assertIn("dmath-ch06-kp-001", text)
        self.assertIn("I do not see why order matters", text)
        self.assertIn("out.md", text)

    def test_diagnose_instruction_is_locate_first(self):
        context = dict(EXPLAIN_CONTEXT, user_answer="My design: I summed both sets.")
        text = teacher.render("diagnose", context, "out.md").lower()
        self.assertIn("locate", text)
        self.assertIn("hint", text)
        self.assertIn("not the full solution", text)
        self.assertIn("my design: i summed both sets.", text)
        self.assertNotIn("give the full solution", text)


if __name__ == "__main__":
    unittest.main()
