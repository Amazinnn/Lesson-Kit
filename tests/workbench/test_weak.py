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

    def test_overdue_boosts_ordering(self):
        kps = [kp("a"), kp("b")]
        signals = [sig("a"), sig("b")]
        schedule = [
            {"item_type": "kp", "item_id": "a", "direction": "", "due_at": "2026-08-10"},
            {"item_type": "kp", "item_id": "b", "direction": "", "due_at": "2026-08-30"},
        ]
        scored = weak.score_all(kps, signals, schedule, [], set(), NOW)
        self.assertEqual(scored[0]["kp_id"], "a")

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


if __name__ == "__main__":
    unittest.main()
