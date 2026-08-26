"""Pure, read-only mastery v0 evidence evaluation."""

VERSION = "v0"
CATEGORIES = (
    "evidence_insufficient", "needs_work", "due_review", "recently_stable",
)


def evaluate(snapshot, today):
    """Classify the plain evidence rows supplied by the data projection."""
    problems = [_evaluate_problem(problem, today) for problem in snapshot["problems"]]
    problem_by_id = {item["id"]: item for item in problems}
    knowledge_points = [
        _evaluate_kp(kp, snapshot["problems"], problem_by_id,
                     snapshot.get("candidates", ()), today)
        for kp in snapshot["kps"]
    ]
    return {
        "version": VERSION,
        "problems": problems,
        "knowledge_points": knowledge_points,
    }


def _evaluate_problem(problem, today):
    evidence = _evidence(problem.get("attempts", ()), problem.get("feedback", ()), problem["id"])
    latest = _latest(evidence)
    positive = _matching(evidence, "positive")
    if latest and latest["polarity"] == "negative":
        return _result(problem["id"], "problem", "needs_work", [latest])
    if _is_due(problem.get("schedule"), today):
        return _result(problem["id"], "problem", "due_review", [_due_reason(problem)])
    if _is_stable(positive):
        return _result(problem["id"], "problem", "recently_stable", positive)
    return _result(problem["id"], "problem", "evidence_insufficient", [_insufficient_reason()])


def _evaluate_kp(kp, all_problems, problem_by_id, candidates, today):
    linked = [problem for problem in all_problems if kp["id"] in problem["kp_ids"]]
    if not linked:
        return _result(kp["id"], "kp", "evidence_insufficient", [_zero_problem_reason()])

    formal_negative = [
        problem_by_id[problem["id"]]["reasons"][0]
        for problem in linked
        if problem_by_id[problem["id"]]["category"] == "needs_work"
    ]
    candidate_evidence = []
    for candidate in candidates:
        if kp["id"] in candidate["kp_ids"]:
            evidence = _evidence(candidate.get("attempts", ()), (), candidate["id"])
            latest = _latest(evidence)
            if latest:
                candidate_evidence.append(latest)
    direct_evidence = _evidence((), kp.get("feedback", ()), kp["id"])
    direct_latest = _latest(direct_evidence)
    candidate_negative = _matching(candidate_evidence, "negative")
    direct_negative = [direct_latest] if direct_latest and direct_latest["polarity"] == "negative" else []
    negative = _latest(formal_negative + candidate_negative + direct_negative)
    if negative:
        return _result(kp["id"], "kp", "needs_work", [negative])
    if _is_due(kp.get("schedule"), today):
        return _result(kp["id"], "kp", "due_review", [_due_reason(kp)])

    formal_positive = {
        problem["id"]: _matching(
            _evidence(problem.get("attempts", ()), problem.get("feedback", ()), problem["id"]),
            "positive",
        )
        for problem in linked
    }
    direct_positive = _matching(direct_evidence, "positive")
    candidate_positive = _matching(candidate_evidence, "positive")
    formal_items = [item for items in formal_positive.values() for item in items]
    positive = formal_items + candidate_positive
    if len(linked) == 1:
        if (formal_items and direct_positive
                and _distinct_dates(formal_items + direct_positive) >= 2):
            return _result(kp["id"], "kp", "recently_stable", positive + direct_positive)
    elif (sum(bool(items) for items in formal_positive.values()) >= 2
          and _distinct_dates(positive) >= 2):
        return _result(kp["id"], "kp", "recently_stable", positive)
    return _result(kp["id"], "kp", "evidence_insufficient", [_insufficient_reason()])


def _evidence(attempts, feedback, item_id=None):
    items = []
    for attempt in attempts:
        status = attempt.get("status")
        if attempt.get("is_correct") == 1 or status == "mastered":
            label = "correct" if attempt.get("is_correct") == 1 else status
            items.append(_reason(attempt, "positive", "strong", f"自动结果 {label}", item_id))
        elif attempt.get("is_correct") == 0 or status in ("wrong", "stuck"):
            label = "wrong" if attempt.get("is_correct") == 0 else status
            items.append(_reason(attempt, "negative", "strong", f"自动结果 {label}", item_id))
    for event in feedback:
        rating = event.get("rating")
        if rating in (1, 2):
            items.append(_reason(event, "negative", "medium", f"自评 {rating}", item_id))
        elif rating in (4, 5):
            items.append(_reason(event, "positive", "medium", f"自评 {rating}", item_id, True))
    return items


def _reason(row, polarity, strength, evidence, item_id=None, self_rating=False):
    return {
        "item_id": item_id or row.get("item_id") or row.get("problem_id") or row.get("candidate_id"),
        "date": _date(row.get("created_at")),
        "polarity": polarity,
        "strength": strength,
        "evidence": evidence,
        "self_rating": self_rating,
    }


def _matching(items, polarity):
    return [item for item in items if item["polarity"] == polarity]


def _latest(items):
    return max(items, key=lambda item: item["date"] or "") if items else None


def _is_stable(positive):
    return (
        _distinct_dates(positive) >= 2 and any(item["strength"] == "strong" for item in positive)
    ) or (
        sum(item["self_rating"] for item in positive) >= 3 and _distinct_dates(positive) >= 2
    )


def _distinct_dates(items):
    return len({_day(item["date"]) for item in items if item["date"]})


def _is_due(schedule, today):
    due_at = (schedule or {}).get("due_at")
    return bool(due_at and _day(due_at) and _day(due_at) <= today.isoformat())


def _date(value):
    return value or None


def _day(value):
    return value[:10] if value else None


def _result(item_id, entity, category, reasons):
    explanations = {
        "evidence_insufficient": "证据不足：尚无足以判断学习状态的有效证据。",
        "needs_work": "需要巩固：存在决定性的负面学习证据。",
        "due_review": "应当复习：当前复习计划已经到期。",
        "recently_stable": "近期稳定：跨日期的正向学习证据满足 v0 阈值。",
    }
    return {
        "entity": entity,
        "id": item_id,
        "category": category,
        "explanation": explanations[category],
        "reasons": reasons,
    }


def _due_reason(item):
    return {
        "item_id": item["id"], "date": _date(item["schedule"]["due_at"]),
        "polarity": "due", "strength": "schedule", "evidence": "复习计划到期",
        "self_rating": False,
    }


def _insufficient_reason():
    return {
        "item_id": None, "date": None, "polarity": "neutral", "strength": "none",
        "evidence": "有效学习证据不足", "self_rating": False,
    }


def _zero_problem_reason():
    return {
        "item_id": None, "date": None, "polarity": "neutral", "strength": "none",
        "evidence": "没有关联的正式题目", "self_rating": False,
    }
