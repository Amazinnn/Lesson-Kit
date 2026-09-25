"""Practice manifests: the input that pins one practice set, and its preview.

A manifest is an input, not a stored practice — it records which problems the
caller asked for and why, so the same command can print the same set again.
Reading or checking one writes nothing.
"""

import json
import re
from pathlib import Path

from workbench.domain import practice_set as render_rules

FIGURE_REFERENCE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

KIND = "practice-set"
FIELDS = {"kind", "title", "course", "request", "shortage", "items"}
ITEM_FIELDS = {"problem_id", "reason"}


def build(title, problems, request=None):
    """One manifest describing the selected problems in order."""
    return {
        "kind": KIND,
        "title": title,
        "request": request or {},
        "items": [
            {"problem_id": problem["problem_id"], "reason": problem.get("reason", "scope")}
            for problem in problems
        ],
    }


def read(path):
    """Load a manifest from a file or from stdin (`-`)."""
    import sys

    text = sys.stdin.read() if str(path) == "-" else Path(path).read_text(encoding="utf-8-sig")
    plan = json.loads(text)
    if not isinstance(plan, dict):
        raise ValueError("a practice manifest must be a JSON object")
    return plan


def write(path, plan):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def resolve(pool, plan):
    """The plan's problems in plan order; raises when the plan cannot be used."""
    plan, errors = _validated(pool, plan)
    if errors:
        raise ValueError("; ".join(errors))
    problems = []
    for item in plan["items"]:
        problem = pool.problem(item["problem_id"])
        problem["reason"] = item.get("reason", "scope")
        problems.append(problem)
    return plan, problems


def _validated(pool, plan):
    errors = []
    if not isinstance(plan, dict) or plan.get("kind") != KIND:
        return {}, [f"expected a {KIND} manifest"]
    extra = sorted(set(plan) - FIELDS)
    if extra:
        errors.append(f"unsupported manifest field: {extra[0]}")
    items = plan.get("items")
    if not isinstance(items, list) or not items:
        return plan, errors + ["manifest requires a non-empty items list"]
    seen = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("problem_id"), str) \
                or not item["problem_id"]:
            errors.append(f"item {index}: problem_id is required")
            continue
        item_extra = sorted(set(item) - ITEM_FIELDS)
        if item_extra:
            errors.append(f"item {index}: unsupported field: {item_extra[0]}")
        if item["problem_id"] in seen:
            errors.append(f"item {index}: duplicate problem {item['problem_id']}")
            continue
        seen.add(item["problem_id"])
        if pool.problem(item["problem_id"]) is None:
            errors.append(f"item {index}: unknown problem {item['problem_id']}")
    return plan, errors


def check(pool, plan):
    """Validate a manifest and preview the render; zero writes."""
    plan, errors = _validated(pool, plan)
    if errors:
        raise ValueError("; ".join(errors))
    _, problems = resolve(pool, plan)
    title = plan.get("title") or "练习"
    student = render_rules.render_practice_set(problems, title)
    leaks = render_rules.leaks(problems, student)
    return {
        "valid": not leaks,
        "writes": 0,
        "title": title,
        "count": len(problems),
        "items": [
            {
                "index": index,
                "problem_id": problem["problem_id"],
                "reason": problem.get("reason", "scope"),
                "has_solution": bool(
                    isinstance(problem.get("solution"), str) and problem["solution"].strip()),
            }
            for index, problem in enumerate(problems, start=1)
        ],
        "missing_solutions": [
            problem["problem_id"] for problem in problems
            if not (isinstance(problem.get("solution"), str) and problem["solution"].strip())
        ],
        "leaks": leaks,
        # The sheets keep the stored relative references; say where the bytes are
        # so a printed copy can carry them.
        "figures": _figures(pool, problems),
    }


def _figures(pool, problems):
    references = sorted({
        reference
        for problem in problems
        for reference in FIGURE_REFERENCE.findall(problem.get("problem_text") or "")
    })
    base = Path(pool.root) / ".lessonkit" / "figures"
    return {"count": len(references), "base": str(base) if references else ""}


def render(pool, plan):
    """The two sheets for a manifest, plus its checked preview."""
    preview = check(pool, plan)
    if preview["leaks"]:
        raise ValueError(
            "the student sheet would leak internal content: "
            + "; ".join(f"item {leak['index']} {leak['token']}" for leak in preview["leaks"])
        )
    _, problems = resolve(pool, plan)
    title = preview["title"]
    return {
        "preview": preview,
        "practice_set": render_rules.render_practice_set(problems, title),
        "solutions": render_rules.render_solutions(problems, title),
    }
