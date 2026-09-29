"""Practice manifests: the input that pins one practice set, and its preview.

A manifest is an input, not a stored practice — it records which problems the
caller asked for and why, so the same command can print the same set again.
Reading or checking one writes nothing.
"""

import json
import re
from datetime import datetime, timezone
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

# -- managed reusable practice sets -------------------------------------------

SAVED_ID = re.compile(r"^ps-(\d+)$")


def _saved_dir(pool):
    return Path(pool.root) / ".lessonkit" / "practice-sets"


def _saved_path(pool, practice_set_id):
    if not isinstance(practice_set_id, str) or not SAVED_ID.fullmatch(practice_set_id):
        raise ValueError("invalid practice_set_id")
    return _saved_dir(pool) / f"{practice_set_id}.json"


def _timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _next_saved_id(pool):
    # practice_runs keeps the source_ref of deleted papers forever, so the
    # scan must include it: reusing a freed id would merge two different
    # papers into one run-history group.
    maximum = 0
    folder = _saved_dir(pool)
    if folder.is_dir():
        for path in folder.glob("ps-*.json"):
            match = SAVED_ID.fullmatch(path.stem)
            if match:
                maximum = max(maximum, int(match.group(1)))
    if "practice_runs" in {
        row[0] for row in pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'")
    }:
        for (ref,) in pool.connect().execute(
            "SELECT DISTINCT source_ref FROM practice_runs WHERE source_ref IS NOT NULL"
        ):
            match = SAVED_ID.fullmatch(ref or "")
            if match:
                maximum = max(maximum, int(match.group(1)))
    return f"ps-{maximum + 1:03d}"


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _saved_record(pool, practice_set_id, plan, created_at, updated_at):
    checked, errors = _validated(pool, plan)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "practice_set_id": practice_set_id,
        "title": checked.get("title") or "练习",
        "created_at": created_at,
        "updated_at": updated_at,
        "count": len(checked["items"]),
        "plan": checked,
    }


def list_saved(pool):
    """List reusable papers without creating any learning evidence."""
    folder = _saved_dir(pool)
    if not folder.is_dir():
        return []
    records = []
    for path in sorted(folder.glob("ps-*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = _saved_record(
                pool, raw["practice_set_id"], raw["plan"],
                raw["created_at"], raw["updated_at"])
        except (KeyError, ValueError, OSError, json.JSONDecodeError):
            continue
        records.append(record)
    return records


def get_saved(pool, practice_set_id):
    path = _saved_path(pool, practice_set_id)
    if not path.is_file():
        raise FileNotFoundError(f"unknown practice set: {practice_set_id}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _saved_record(
        pool, raw["practice_set_id"], raw["plan"],
        raw["created_at"], raw["updated_at"])


def _plan_from_ids(pool, title, problem_ids, request=None):
    if not isinstance(problem_ids, list) or not problem_ids:
        raise ValueError("problem_ids must be a non-empty string list")
    if not all(isinstance(problem_id, str) and problem_id for problem_id in problem_ids):
        raise ValueError("problem_ids must be a non-empty string list")
    if len(set(problem_ids)) != len(problem_ids):
        raise ValueError("problem_ids must not contain duplicates")
    problems = []
    for problem_id in problem_ids:
        problem = pool.problem(problem_id)
        if problem is None:
            raise ValueError(f"unknown problem: {problem_id}")
        problems.append({**problem, "reason": "manual"})
    plan = build(title or "练习", problems, request=request)
    plan["course"] = pool.course
    return plan


def create_saved(pool, title, problem_ids, request=None):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")
    if request is not None and not isinstance(request, dict):
        raise ValueError("request must be an object")
    practice_set_id = _next_saved_id(pool)
    now = _timestamp()
    record = {
        "practice_set_id": practice_set_id,
        "created_at": now,
        "updated_at": now,
        "plan": _plan_from_ids(pool, title.strip(), problem_ids, request=request),
    }
    _atomic_json(_saved_path(pool, practice_set_id), record)
    return get_saved(pool, practice_set_id)


def update_saved(pool, practice_set_id, *, title=None, problem_ids=None, request=None):
    current = get_saved(pool, practice_set_id)
    plan = current["plan"]
    next_title = plan.get("title") or "练习"
    if title is not None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        next_title = title.strip()
    if request is not None and not isinstance(request, dict):
        raise ValueError("request must be an object")
    if problem_ids is None:
        problem_ids = [item["problem_id"] for item in plan["items"]]
    next_plan = _plan_from_ids(
        pool, next_title, problem_ids,
        request=plan.get("request") if request is None else request)
    raw = {
        "practice_set_id": practice_set_id,
        "created_at": current["created_at"],
        "updated_at": _timestamp(),
        "plan": next_plan,
    }
    _atomic_json(_saved_path(pool, practice_set_id), raw)
    return get_saved(pool, practice_set_id)


def delete_saved(pool, practice_set_id):
    current = get_saved(pool, practice_set_id)
    _saved_path(pool, practice_set_id).unlink()
    return {"deleted": True, "practice_set_id": practice_set_id, "title": current["title"]}


def render_saved(pool, practice_set_id):
    record = get_saved(pool, practice_set_id)
    rendered = render(pool, record["plan"])
    return {"practice_set_id": practice_set_id, **rendered}

