"""Weakness ordering and cascade boost tests (TDD, red first)."""

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


weak = load_script("wb_weak", Path("workbench/domain/weak.py"))


def sig(target_id, weight="high", evidence=1):
    return {
        "target_type": "node",
        "target_id": target_id,
        "signal_type": "weak_node",
        "weight": weight,
        "evidence_count": evidence,
    }


def kp(kp_id):
    return {"kp_id": kp_id, "knowledge_item": kp_id}


def rel(source, target, rtype="prerequisite", strength="high"):
    return {
        "relation_id": f"r-{source}-{target}",
        "source_kp_id": source,
        "target_kp_id": target,
        "relation_type": rtype,
        "direction": "directed",
        "strength": strength,
    }


NOW = date(2026, 8, 16)


class WeakTests(unittest.TestCase):
    def test_signaled_kp_ranks_first(self):
        kps = [kp("a"), kp("b")]
        signals = [sig("b")]
        scored = weak.score_all(kps, signals, [], [], set(), NOW)
        ranked = [s["kp_id"] for s in scored]
        self.assertEqual(ranked, ["b", "a"])
        self.assertGreater(scored[0]["score"], scored[1]["score"])

    def test_evidence_multiplies_weight(self):
        signals = [sig("b", "medium", 3)]
        scored = weak.score_all([kp("b")], signals, [], [], set(), NOW)
        self.assertGreater(scored[0]["score"], 1.0)

    def test_multiple_signal_types_use_the_strongest_independent_of_order(self):
        high = {**sig("b", "high", 1), "signal_id": "b-sig-confusion",
                "signal_type": "confusion"}
        low = {**sig("b", "low", 9), "signal_id": "b-sig-weak",
               "signal_type": "weak_node"}
        first = weak.score_all([kp("b")], [high, low], [], [], set(), NOW)
        second = weak.score_all([kp("b")], [low, high], [], [], set(), NOW)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["score"], 2.0)

    def test_overdue_boosts_ordering(self):
        kps = [kp("a"), kp("b")]
        signals = [sig("a"), sig("b")]
        schedule = [
            {"item_type": "kp", "item_id": "a", "direction": "", "due_at": "2026-08-10"},
            {"item_type": "kp", "item_id": "b", "direction": "", "due_at": "2026-08-30"},
        ]
        scored = weak.score_all(kps, signals, schedule, [], set(), NOW)
        self.assertEqual(scored[0]["kp_id"], "a")

    def test_any_overdue_direction_boosts_the_knowledge_point(self):
        schedule = [
            {"item_type": "kp", "item_id": "a", "direction": "", "due_at": None},
            {
                "item_type": "kp", "item_id": "a", "direction": "reverse",
                "due_at": "2026-08-10",
            },
            {
                "item_type": "kp", "item_id": "b", "direction": "",
                "due_at": "2026-08-30",
            },
        ]

        scored = weak.score_all(
            [kp("a"), kp("b")], [sig("a"), sig("b")], schedule, [], set(), NOW
        )

        self.assertEqual(scored[0]["kp_id"], "a")
        self.assertGreater(scored[0]["score"], scored[1]["score"])

    def test_session_repeat_penalty(self):
        kps = [kp("a"), kp("b")]
        signals = [sig("a"), sig("b")]
        practiced = {"a"}
        scored = weak.score_all(kps, signals, [], [], practiced, NOW)
        self.assertEqual(scored[0]["kp_id"], "b")

    def test_cascade_boosts_prerequisite(self):
        kps = [kp("base"), kp("hard")]
        signals = [sig("hard")]
        relations = [rel("base", "hard")]
        scored = weak.score_all(kps, signals, [], relations, set(), NOW)
        base = next(s for s in scored if s["kp_id"] == "base")
        self.assertGreater(base["score"], 0.2)
        self.assertTrue(any("hard" in r for r in base["reasons"]))

    def test_cascade_does_not_use_contrasts(self):
        kps = [kp("a"), kp("b")]
        signals = [sig("b")]
        relations = [rel("a", "b", rtype="contrasts")]
        scored = weak.score_all(kps, signals, [], relations, set(), NOW)
        a = next(s for s in scored if s["kp_id"] == "a")
        self.assertEqual(a["score"], 0.2)
        self.assertEqual(a["reasons"], [])

    def test_cascade_respects_strength_and_depth(self):
        kps = [kp("root"), kp("mid"), kp("leaf")]
        signals = [sig("leaf")]
        relations = [
            rel("root", "mid", strength="low"),
            rel("mid", "leaf", strength="high"),
        ]
        scored = weak.score_all(kps, signals, [], relations, set(), NOW)
        root = next(s for s in scored if s["kp_id"] == "root")
        mid = next(s for s in scored if s["kp_id"] == "mid")
        self.assertGreater(mid["score"], root["score"])
        self.assertGreater(root["score"], 0.2)

    def test_review_state_follows_the_contract_rule_not_the_score(self):
        # A signal is the explicit weakness evidence; a due schedule row is
        # the review; everything else stays neutral (GLOSSARY「行动提醒」).
        due = {"item_type": "kp", "item_id": "due-kp", "due_at": "2026-08-16"}
        later = {"item_type": "kp", "item_id": "later-kp", "due_at": "2026-09-01"}
        states = weak.review_states(
            ["weak-kp", "due-kp", "later-kp", "other-kp"],
            [sig("weak-kp")], [due, later], NOW)
        self.assertEqual(states["weak-kp"], "needs_work")
        self.assertEqual(states["due-kp"], "review")
        self.assertEqual(states["later-kp"], "neutral")
        self.assertEqual(states["other-kp"], "neutral")
        self.assertTrue(set(states.values()) <= set(weak.REVIEW_STATES))

    def test_a_due_row_overrides_nothing_but_an_overdue_one_counts(self):
        overdue = {"item_type": "kp", "item_id": "kp-1", "due_at": "2026-08-01"}
        states = weak.review_states(["kp-1"], [], [overdue], NOW)
        self.assertEqual(states["kp-1"], "review")

    def test_the_review_states_are_the_three_contract_words(self):
        self.assertEqual(weak.REVIEW_STATES, ("needs_work", "review", "neutral"))



if __name__ == "__main__":
    unittest.main()
