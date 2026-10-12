"""Deterministic, read-only evaluation of Agent-facing retrieval primitives.

The evaluator deliberately does not call an LLM. It measures whether the data
interfaces can surface the facts a provider would need, and how many primitive
reads the scenario requires. Product retrieval changes should improve these
results rather than being justified by intuition alone.
"""

import argparse
import json
from pathlib import Path

from workbench import registry
from workbench.data import content
from workbench.data import pool as pool_mod


KINDS = {"search", "compare", "kp_history"}
ID_FIELDS = {"kp": "kp_id", "problem": "problem_id", "relation": "relation_id"}
ATTEMPT_STATUSES = {"new", "answered", "wrong", "stuck", "reviewing", "mastered"}


def evaluate(pool, manifest):
    """Run a synthetic retrieval manifest without writing workspace state."""
    scenarios = manifest.get("scenarios") if isinstance(manifest, dict) else None
    if not isinstance(scenarios, list):
        raise ValueError("retrieval manifest requires a scenarios list")

    results = []
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise ValueError(f"scenario {index} must be an object")
        kind = scenario.get("kind")
        if kind not in KINDS:
            raise ValueError(f"scenario {index}: unknown kind {kind!r}")
        if kind == "search":
            result = _search(pool, scenario)
        elif kind == "compare":
            result = _compare(pool, scenario)
        else:
            result = _kp_history(pool, scenario)
        result["name"] = scenario.get("name") or f"scenario-{index}"
        result["kind"] = kind
        results.append(result)

    passed = sum(1 for result in results if result["passed"])
    total_expected = sum(result["expected_count"] for result in results)
    total_found = sum(result["found_count"] for result in results)
    return {
        "summary": {
            "scenarios": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "recall": (total_found / total_expected) if total_expected else 1.0,
            "primitive_reads": sum(result["primitive_reads"] for result in results),
        },
        "results": results,
    }


def _search(pool, scenario):
    entity = scenario.get("entity")
    if entity not in ID_FIELDS:
        raise ValueError(f"search scenario has invalid entity {entity!r}")
    query = scenario.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("search scenario requires a non-empty query")
    expected = _expected_ids(scenario)
    rows = content.search(pool, entity, query)
    id_field = ID_FIELDS[entity]
    found = {row[id_field] for row in rows if row.get(id_field)}
    return _result(expected, found, primitive_reads=1,
                   detail={"query": query, "entity": entity})


def _compare(pool, scenario):
    entity = scenario.get("entity", "kp")
    if entity not in ID_FIELDS:
        raise ValueError(f"compare scenario has invalid entity {entity!r}")
    left = scenario.get("left_query")
    right = scenario.get("right_query")
    if not isinstance(left, str) or not left.strip() \
            or not isinstance(right, str) or not right.strip():
        raise ValueError("compare scenario requires left_query and right_query")
    expected = _expected_ids(scenario)
    id_field = ID_FIELDS[entity]
    found = {
        row[id_field]
        for query in (left, right)
        for row in content.search(pool, entity, query)
        if row.get(id_field)
    }
    return _result(expected, found, primitive_reads=2,
                   detail={"left_query": left, "right_query": right, "entity": entity})


def _kp_history(pool, scenario):
    kp_id = scenario.get("kp_id")
    if not isinstance(kp_id, str) or not kp_id:
        raise ValueError("kp_history scenario requires kp_id")
    expected_text = scenario.get("expected_problem_text")
    if not isinstance(expected_text, str) or not expected_text:
        raise ValueError("kp_history scenario requires expected_problem_text")

    history = content.history(pool, "kp", kp_id)
    evidence = _human_problem_evidence(history)
    expected_folded = expected_text.casefold()
    found = {expected_text} if any(
        expected_folded == row["problem_text"].casefold()
        for row in evidence
    ) else set()
    return _result(
        {expected_text}, found, primitive_reads=1,
        detail={
            "kp_id": kp_id,
            "human_evidence_rows": len(evidence),
            "requirement": "one history read should include problem text plus learning evidence",
        },
    )


def _human_problem_evidence(value):
    """Find evidence rows that are understandable without another id lookup.

    The evaluator does not prescribe a production field name. Any nested row
    counts when it contains the problem text plus at least one concrete learner
    outcome field. That lets the product implementation evolve without teaching
    the evaluator its internal schema.
    """
    rows = []
    if isinstance(value, dict):
        problem_text = value.get("problem_text")
        has_outcome = _has_concrete_outcome(value)
        if isinstance(problem_text, str) and problem_text.strip() and has_outcome:
            rows.append(value)
        for child in value.values():
            rows.extend(_human_problem_evidence(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_human_problem_evidence(child))
    return rows


def _has_concrete_outcome(row):
    status = row.get("status")
    if isinstance(status, str) and status in ATTEMPT_STATUSES:
        return True
    if any(isinstance(row.get(key), str) and row[key].strip()
           for key in ("answer_text", "note")):
        return True
    rating = row.get("rating")
    if (isinstance(rating, (int, float)) and not isinstance(rating, bool)
            and 1 <= rating <= 5):
        return True
    verdict = row.get("verdict")
    return isinstance(verdict, bool) or (
        isinstance(verdict, int) and verdict in (0, 1)
    )


def _expected_ids(scenario):
    values = scenario.get("expected_ids")
    if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value for value in values):
        raise ValueError("scenario requires non-empty expected_ids")
    return set(values)


def _result(expected, found, primitive_reads, detail):
    matched = expected & found
    return {
        "passed": matched == expected,
        "expected_count": len(expected),
        "found_count": len(matched),
        "recall": len(matched) / len(expected) if expected else 1.0,
        "primitive_reads": primitive_reads,
        "detail": detail,
    }


def _pool(workspace):
    root = Path(workspace["path"])
    db_path = root / workspace["db"]
    if not db_path.is_file():
        raise FileNotFoundError(f"workspace database is not a regular file: {db_path}")
    return pool_mod.Pool(
        root=root,
        db_path=db_path,
        course=workspace.get("active_course", ""),
        chapter=workspace.get("active_chapter", ""),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="read-only synthetic evaluation of Lesson Kit retrieval primitives")
    parser.add_argument("workspace")
    parser.add_argument("--input", required=True,
                        help="JSON manifest containing retrieval scenarios")
    args = parser.parse_args(argv)

    workspace = registry.get_workspace(args.workspace)
    manifest = json.loads(Path(args.input).read_text(encoding="utf-8"))
    pool = _pool(workspace)
    try:
        report = evaluate(pool, manifest)
    finally:
        pool.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
