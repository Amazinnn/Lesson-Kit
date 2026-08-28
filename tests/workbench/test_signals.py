"""Deterministic current-signal aggregation."""

from workbench.domain.signals import strongest_by_target


def test_strongest_weight_wins_before_evidence_count():
    rows = [
        {"signal_id": "low", "target_type": "node", "target_id": "kp-1",
         "weight": "low", "evidence_count": 99},
        {"signal_id": "high", "target_type": "node", "target_id": "kp-1",
         "weight": "high", "evidence_count": 1},
    ]
    assert strongest_by_target(rows)["kp-1"]["signal_id"] == "high"
    assert strongest_by_target(reversed(rows))["kp-1"]["signal_id"] == "high"


def test_ties_use_evidence_then_stable_identity():
    rows = [
        {"signal_id": "z", "target_id": "kp-1", "weight": "medium", "evidence_count": 2},
        {"signal_id": "b", "target_id": "kp-1", "weight": "medium", "evidence_count": 3},
        {"signal_id": "a", "target_id": "kp-1", "weight": "medium", "evidence_count": 3},
    ]
    assert strongest_by_target(rows)["kp-1"]["signal_id"] == "a"
