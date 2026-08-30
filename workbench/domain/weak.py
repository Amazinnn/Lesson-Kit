"""Weakness ordering and cascade boosts (pure rules)."""

from datetime import date

from workbench.domain import signals as signal_rules

WEIGHT_SCORE = {"low": 0.5, "medium": 1.0, "high": 2.0}
NO_SIGNAL = 0.2
STRENGTH_FACTOR = {"high": 1.0, "medium": 0.7, "low": 0.4}
CASCADE_TYPES = ("prerequisite", "applies_to", "part_of")
RECENCY_PENALTY = 0.3
DEPTH_DECAY = 0.5


def score_all(kps, signals, schedule_rows, relations, session_practiced, today):
    """Score and rank knowledge points. Never filters — ordering only."""
    signal_by_target = signal_rules.strongest_by_target(signals)
    signal_extra = {
        s["target_id"]: _signal_score(s) - NO_SIGNAL
        for s in signal_by_target.values()
    }
    edges = [r for r in relations if r["relation_type"] in CASCADE_TYPES]

    ranked = []
    for kp in kps:
        kp_id = kp["kp_id"]
        base = _signal_score(
            signal_by_target.get(kp_id)
        )
        boost = _due_boost(schedule_rows, kp_id, today)
        cascade, reasons = _cascade(kp_id, signal_extra, edges)
        score = base * boost + cascade
        if kp_id in session_practiced:
            score *= RECENCY_PENALTY
            reasons.append(f"{kp_id} practiced this session")
        ranked.append({
            "kp_id": kp_id,
            "knowledge_item": kp.get("knowledge_item", kp_id),
            "score": round(score, 3),
            "reasons": reasons,
        })
    ranked.sort(key=lambda item: (-item["score"], item["kp_id"]))
    return ranked


def _signal_score(signal):
    if signal is None:
        return NO_SIGNAL
    base = WEIGHT_SCORE.get(signal.get("weight"), 1.0)
    if signal.get("evidence_count", 1) >= 2:
        base *= 1.5
    return base


def _due_boost(schedule_rows, item_id, today):
    boosts = []
    for row in schedule_rows:
        if row.get("item_type") != "kp" or row.get("item_id") != item_id:
            continue
        due_at = row.get("due_at")
        if not due_at:
            continue
        try:
            due = date.fromisoformat(str(due_at)[:10])
        except ValueError:
            continue
        boosts.append(1.0 + (today - due).days if due <= today else 0.8)
    return max(boosts, default=1.0)


def _cascade(kp_id, signal_extra, edges):
    """Reverse boosts: signaled targets raise their sources, depth <= 2."""
    score = 0.0
    reasons = []
    for edge in edges:
        if edge["source_kp_id"] != kp_id:
            continue
        target = edge["target_kp_id"]
        factor = STRENGTH_FACTOR.get(edge.get("strength"), 0.7)
        weight = signal_extra.get(target, 0.0)
        if weight > 0:
            score += weight * factor
            reasons.append(f"{target} is weak (cascade)")
        for hop in edges:
            if hop["source_kp_id"] != target:
                continue
            weight2 = signal_extra.get(hop["target_kp_id"], 0.0)
            if weight2 > 0:
                factor2 = STRENGTH_FACTOR.get(hop.get("strength"), 0.7)
                score += weight2 * factor2 * DEPTH_DECAY
                reasons.append(
                    f"{hop['target_kp_id']} is weak via {target} (cascade)"
                )
    return score, reasons
