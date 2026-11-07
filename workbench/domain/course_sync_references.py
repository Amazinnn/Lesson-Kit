"""Typed stored references inside exchange JSON columns.

A course exchange moves rows between installations whose integer identities
differ, so a stored reference travels as the portable stable row identity and
comes back as the receiving installation's own integer. Only the paths where a
writer really stores such an identity are rewritten: learner answers, notes,
choices, part definitions, and grading payloads keep their bytes even when they
happen to contain a key named like a reference.

One helper serves both directions. ``resolve(target_table, value)`` maps the
local integer to the exchange identity while exporting, and the exchange
identity back to a local integer while importing; recording the dependency is
the caller's business, so this module stays pure and touches no store.

The declared paths, by writer:

- ``practice_runs.items_json`` / ``paper_state.checkpoint_json``:
  ``execution_id``, item-level ``attempt_id``, and
  ``draft.parts.<part_id>.attempt_id`` (``active_practice._archive``,
  ``paper_progress.park``, ``paper_progress.bind_attempts``).
- ``attempt_operations.result``: ``attempt_id``, ``paper.execution_id``,
  ``paper.run_id``, ``paper.previous_states.<problem_id>.attempt_id``
  (``attempts._effects``, ``paper_progress.bind_attempts``).
- ``practice_request_operations.payload``: ``execution_id``, ``attempt_id``,
  ``context.execution_id``, ``practice_context.execution_id``, and
  ``drafts[].practice_context.execution_id`` (``attempts`` browser payloads,
  ``part_practice.submit``, ``active_practice.mark_stuck_draft``,
  ``active_practice.submit``).
- ``practice_request_operations.result``: ``attempt_id``, ``attempt_ids``,
  ``execution_id``, ``run_id``, and the cached ``practice`` projection
  (``part_practice.submit``, ``active_practice.mark_stuck_draft``,
  ``active_practice.submit``, ``attempts._save_browser_operation``).
- ``part_grading_revisions.request_json``: element 0 only (``part_grading.mutate``).
"""

import json

#: ``json.dumps``' own spelling, which two readers compare byte for byte.
DEFAULT = {"sort_keys": True}
#: Kinds whose payload ``attempts`` re-serializes; the others stay compact.
RE_DUMPED_KINDS = {"attempt", "feedback"}
#: The exchange spelling of every other remapped JSON column.
COMPACT = {"sort_keys": True, "ensure_ascii": False, "separators": (",", ":")}


def convert_json(table, field, value, resolve):
    """Rewrite the declared references of one stored JSON value."""
    return CONVERTERS[(table, field)](value, resolve)


def convert_draft(draft, resolve):
    """Rewrite the machine attempt links of one part draft and nothing else."""
    if not isinstance(draft, dict):
        return draft
    parts = draft.get("parts")
    if not isinstance(parts, dict):
        return draft
    return {**draft, "parts": {
        part_id: ({**part, "attempt_id": resolve("problem_attempts", part["attempt_id"])}
                  if isinstance(part, dict) and part.get("attempt_id") is not None else part)
        for part_id, part in parts.items()}}


def serialize_json(table, field, value):
    """Render a converted value in the exact spelling its reader compares."""
    if (table, field) == ("part_grading_revisions", "request_json"):
        # part_grading.mutate re-derives this request and compares the raw string.
        return json.dumps(value, **DEFAULT)
    if (table, field) == ("practice_request_operations", "payload"):
        # attempts._browser_replay compares this payload byte for byte.
        return json.dumps(value, **(DEFAULT if _re_dumped(value) else COMPACT))
    return json.dumps(value, **COMPACT)


def _re_dumped(payload):
    """``attempts`` re-serializes these payloads without the compact separators."""
    if not isinstance(payload, dict):
        return False
    return "edit_existing" in payload or (
        payload.get("kind") in RE_DUMPED_KINDS and "practice_context" in payload)


def _items(value, resolve):
    return [_item(item, resolve) for item in value] if isinstance(value, list) else value


def _item(item, resolve):
    converted = dict(item)
    attempt_id = converted.get("attempt_id")
    if attempt_id is not None:
        converted["attempt_id"] = resolve("problem_attempts", attempt_id)
    if "draft" in converted:
        converted["draft"] = convert_draft(converted["draft"], resolve)
    return converted


def _checkpoint(record, resolve):
    converted = dict(record)
    execution_id = converted.get("execution_id")
    if execution_id is not None:
        converted["execution_id"] = resolve("practice_execution_ids", execution_id)
    if "items" in converted:
        converted["items"] = _items(converted["items"], resolve)
    return converted


def _attempt_result(result, resolve):
    converted = dict(result)
    attempt_id = converted.get("attempt_id")
    if attempt_id is not None:
        converted["attempt_id"] = resolve("problem_attempts", attempt_id)
    if isinstance(converted.get("paper"), dict):
        converted["paper"] = _attempt_paper(converted["paper"], resolve)
    return converted


def _attempt_paper(paper, resolve):
    converted = dict(paper)
    for field, table in (("execution_id", "practice_execution_ids"),
                         ("run_id", "practice_runs")):
        if converted.get(field) is not None:
            converted[field] = resolve(table, converted[field])
    states = converted.get("previous_states")
    if isinstance(states, dict):
        converted["previous_states"] = {
            problem_id: _previous_state(state, resolve) for problem_id, state in states.items()}
    return converted


def _previous_state(state, resolve):
    if not isinstance(state, dict):
        return None if state is None else resolve("problem_attempts", state)
    if state.get("attempt_id") is None:
        return state
    return {**state, "attempt_id": resolve("problem_attempts", state["attempt_id"])}


def _snapshot(value, resolve):
    """Effect snapshots carry no reference, so they travel verbatim.

    ``attempts._snapshot`` serializes rows of problem_progress,
    learning_current_state, review_schedule, and learner_signals only, and none
    of those tables declares an identity column (``pool_schema.py``: 270-280,
    762-776, 629-642, 385-410). An ``attempt_id`` appearing in one of their rows
    is therefore note text, not a reference.
    """
    return value


def _payload(payload, resolve):
    converted = dict(payload)
    execution_id = converted.get("execution_id")
    if execution_id is not None:
        converted["execution_id"] = resolve("practice_execution_ids", execution_id)
    attempt_id = converted.get("attempt_id")
    if attempt_id is not None:
        converted["attempt_id"] = resolve("problem_attempts", attempt_id)
    for field in ("context", "practice_context"):
        if isinstance(converted.get(field), dict):
            converted[field] = _context(converted[field], resolve)
    drafts = converted.get("drafts")
    if isinstance(drafts, list):
        converted["drafts"] = [
            {**entry, "practice_context": _context(entry["practice_context"], resolve)}
            if isinstance(entry, dict) and isinstance(entry.get("practice_context"), dict)
            else entry
            for entry in drafts]
    return converted


def _context(context, resolve):
    if context.get("execution_id") is None:
        return context
    return {**context, "execution_id": resolve("practice_execution_ids",
                                               context["execution_id"])}


def _browser_result(result, resolve):
    if not isinstance(result, dict):
        # A feedback write caches the learner-facing sentences it produced.
        return result
    converted = dict(result)
    for field, table in (("attempt_id", "problem_attempts"),
                         ("execution_id", "practice_execution_ids"),
                         ("run_id", "practice_runs")):
        if converted.get(field) is not None:
            converted[field] = resolve(table, converted[field])
    ids = converted.get("attempt_ids")
    if isinstance(ids, list):
        converted["attempt_ids"] = [
            value if value is None else resolve("problem_attempts", value) for value in ids]
    if isinstance(converted.get("practice"), dict):
        # mark caches {completed, replay, practice: record}; mark_stuck_draft
        # caches the record itself — both are the shape a checkpoint holds.
        converted["practice"] = _practice_mark(converted["practice"], resolve)
    return converted


def _practice_mark(value, resolve):
    converted = _checkpoint(value, resolve)
    if isinstance(converted.get("practice"), dict):
        converted["practice"] = _checkpoint(converted["practice"], resolve)
    return converted


def _grading_request(request, resolve):
    """Element 0 is the attempt; element 5 is the agent's own grading payload."""
    if not isinstance(request, list) or not request or request[0] is None:
        return request
    converted = list(request)
    converted[0] = resolve("problem_attempts", converted[0])
    return converted


def _opaque(value, resolve):
    return value


CONVERTERS = {
    ("practice_runs", "items_json"): _items,
    ("paper_state", "checkpoint_json"): _checkpoint,
    ("attempt_operations", "result"): _attempt_result,
    ("attempt_operations", "pre_state"): _snapshot,
    ("attempt_operations", "post_state"): _snapshot,
    ("practice_request_operations", "payload"): _payload,
    ("practice_request_operations", "result"): _browser_result,
    ("part_grading_revisions", "request_json"): _grading_request,
    ("part_grading_revisions", "payload_json"): _opaque,
}
