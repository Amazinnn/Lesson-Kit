"""Problem pull engine (pure rules over a Pool)."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import random

from workbench.domain import weak as weak_rules

PRACTICE_MODES = {"exam", "micro", "yes_no"}
DRIVERS = ("weak", "due", "wrong")
WRONG_STATUSES = {"wrong", "stuck"}


def select(pool, kp_ids, n, mode="weak", source_kind=None, origin_kind=None,
           source_group=None, exclude_ids=None, seed=None, include_ids=None,
           difficulty_min=None, difficulty_max=None, difficulty_dimensions=None,
           difficulty_strategy=None, exam_year=None, explicit_ids=None,
           drivers=None, with_reasons=False, coverage=False, today=None):
    """Pull durable problems and report gaps.

    Never fabricates content: whatever cannot be filled is listed in
    ``shortage``. The pull engine reads formal problems only. ``include_ids`` optionally
    restricts the result to those identifiers within the requested scope.

    Composition adds three optional inputs on top of the session filters:

    ``explicit_ids``
        Named problems (recall cards the learner wants included) are always in
        the result and are never filtered out or capped away.
    ``drivers``
        Learner evidence — ``weak`` knowledge points, ``due`` problems, and
        ``wrong`` problems (progress or latest attempt) — selects within the
        candidate universe instead of widening it.
    ``exam_year``
        Prefix match on the recorded source year, so ``2023`` finds
        ``2023-2024秋冬``.

    ``with_reasons`` annotates every returned problem with why it was selected
    (``explicit``, ``wrong``, ``due``, ``weak``, or ``scope``); the reason order is
    the precedence order, strongest first. ``coverage`` orders the candidates so
    each knowledge point contributes one problem before any repeats — before the
    ``n`` cap, which is what makes a set composed across chapters span them.

    Note: ``mode="weak"`` is an *ordering* (most requested knowledge points
    first) and is unrelated to the ``weak`` driver, which is the weakness score
    from `domain.weak`.
    """
    exclude_ids = set(exclude_ids or {})
    include_ids = set(include_ids or [])
    explicit_ids = {item for item in (explicit_ids or {}) if item}
    driver_names = set(drivers or ())
    practice_mode = mode if mode in PRACTICE_MODES else None
    order_mode = "weak" if practice_mode else mode
    today = today or date.today()
    conditional = bool(source_kind or origin_kind or source_group or exam_year) or (
        difficulty_min is not None or difficulty_max is not None
        or bool(difficulty_dimensions)
    )

    if kp_ids or driver_names or conditional or not explicit_ids:
        if order_mode == "all":
            problems = pool.problems_all()
            if source_kind:
                problems = [p for p in problems if p["source_kind"] == source_kind]
        else:
            problems = pool.problems_for_kps(kp_ids, source_kind)
        if order_mode == "weak":
            problems = sorted(
                problems,
                key=lambda p: (-_hit_count(p, kp_ids), p["problem_id"]),
            )
        elif order_mode == "random":
            random.Random(seed).shuffle(problems)
    else:
        problems = []

    if practice_mode:
        problems = [p for p in problems if _eligible_for_mode(p, practice_mode)]
    if origin_kind:
        problems = [p for p in problems if p.get("origin_kind") == origin_kind]
    if source_group:
        problems = [p for p in problems if _source_group(p) == source_group]
    if exam_year:
        problems = [p for p in problems if _matches_exam_year(p, exam_year)]
    if difficulty_min is not None or difficulty_max is not None or difficulty_dimensions:
        problems = [
            p for p in problems
            if _matches_difficulty(
                p, difficulty_min, difficulty_max, difficulty_dimensions or {}
            )
        ]
    matched = _driver_matches(pool, driver_names, today)
    if driver_names:
        selected_by_evidence = set().union(*matched.values())
        problems = [p for p in problems if p["problem_id"] in selected_by_evidence]
    if include_ids:
        problems = [p for p in problems if p["problem_id"] in include_ids]
    problems = [p for p in problems if p["problem_id"] not in exclude_ids]
    if difficulty_strategy == "balanced":
        problems = _balanced(problems)
    if coverage:
        problems = coverage_first(problems)

    shortage = []
    if order_mode != "all":
        for kp_id in kp_ids:
            durable = sum(1 for p in problems if kp_id in p["kp_ids"])
            if durable < n:
                shortage.append(kp_id)

    selected = problems[:n]
    chosen = {p["problem_id"] for p in selected}
    for problem_id in sorted(explicit_ids - chosen):
        problem = pool.problem(problem_id)
        if problem is not None:
            selected.append(problem)
            chosen.add(problem_id)
    if with_reasons:
        for problem in selected:
            problem["reason"] = _reason(problem["problem_id"], explicit_ids, matched)
    return {
        "problems": selected,
        "shortage": shortage,
    }


def _reason(problem_id, explicit_ids, matched):
    if problem_id in explicit_ids:
        return "explicit"
    for driver in DRIVERS:
        if problem_id in matched.get(driver, ()):
            return driver
    return "scope"


def _driver_matches(pool, driver_names, today):
    """Problem ids each driver selects; empty sets when no driver was asked for."""
    matches = {driver: set() for driver in DRIVERS}
    if "wrong" in driver_names:
        matches["wrong"] = {
            row["problem_id"] for row in pool.problem_progress_rows()
            if row.get("status") in WRONG_STATUSES
        } | {
            problem_id for problem_id, status in pool.latest_attempt_statuses().items()
            if status in WRONG_STATUSES
        }
    if "due" in driver_names:
        matches["due"] = _due_problem_ids(pool, today)
    if "weak" in driver_names:
        ranked = weak_rules.score_all(
            pool.kps(pool.scope_prefix()), pool.signals(), pool.schedule_rows(),
            pool.relations(), set(), today,
        )
        weak_kp_ids = weak_rules.weak_kp_ids(ranked)
        matches["weak"] = {
            problem["problem_id"] for problem in pool.problems_for_kps(weak_kp_ids)
        } if weak_kp_ids else set()
    return matches


def _due_problem_ids(pool, today):
    """Problem schedule rows already due (the same day rule the due list uses)."""
    due = set()
    for row in pool.schedule_rows():
        if row.get("item_type") != "problem" or not row.get("due_at"):
            continue
        if str(row["due_at"])[:10] <= today.isoformat():
            due.add(row["item_id"])
    return due


def _matches_exam_year(item, exam_year):
    stored = item.get("exam_year")
    return isinstance(stored, str) and stored.startswith(exam_year)


def coverage_first(problems):
    """Order a composed set so every knowledge point appears before any repeats.

    The problem-set view has always documented this policy ("select at least one
    problem for each available core knowledge point before adding extra problems
    for already covered ones, preserving source order when coverage allows it").
    Composing across chapters needs it: session ordering alone would hand back
    whichever chapter happens to cover the most knowledge points.
    """
    ordered = []
    seen = set()
    # The covering pass runs in source order, so a printed set reads by id rather
    # than by whatever order the session wanted.
    for problem in sorted(problems, key=lambda item: item["problem_id"]):
        fresh = [kp_id for kp_id in problem.get("kp_ids") or [] if kp_id not in seen]
        if not fresh:
            continue
        ordered.append(problem)
        seen.update(fresh)
    covered = {problem["problem_id"] for problem in ordered}
    return ordered + [p for p in problems if p["problem_id"] not in covered]


def _hit_count(item, kp_ids):
    return sum(1 for kp_id in kp_ids if kp_id in item["kp_ids"])


def _eligible_for_mode(item, mode):
    """Unmarked durable content is exam-only; other modes are explicit."""
    declared = item.get("practice_modes", item.get("practice_mode"))
    if isinstance(declared, str):
        declared = [declared]
    declared = set(declared or [])
    return mode in declared if declared else mode == "exam"


def _source_group(item):
    if item.get("origin_kind") == "generated_grounded":
        return "ai_generated"
    source = item.get("source_kind")
    if source == "textbook":
        return "textbook"
    if source in {"quiz", "midterm", "final", "makeup"}:
        return "exam"
    return "other"


def _matches_difficulty(item, minimum, maximum, dimension_ranges):
    total = item.get("difficulty")
    if total is None:
        return False
    if minimum is not None and total < minimum:
        return False
    if maximum is not None and total > maximum:
        return False
    for dimension, bounds in dimension_ranges.items():
        value = item.get("difficulty_" + dimension)
        low, high = bounds
        if value is None or (low is not None and value < low) or (
            high is not None and value > high
        ):
            return False
    return True


def _balanced(problems):
    buckets = {band: [] for band in range(1, 6)}
    unrated = []
    for problem in problems:
        value = problem.get("difficulty")
        if value is None:
            unrated.append(problem)
            continue
        band = int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        buckets[band].append(problem)
    ordered = []
    while any(buckets.values()):
        for band in (3, 2, 4, 1, 5):
            if buckets[band]:
                ordered.append(buckets[band].pop(0))
    return ordered + unrated
