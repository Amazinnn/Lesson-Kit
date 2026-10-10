"""JSON API handlers. Each handler gets (pool, workspace, params, body)."""

import json
import threading
from datetime import date, datetime
from pathlib import Path

from workbench import ingest
from workbench.bridge import conversation_providers, conversations, pi_rpc
from workbench.data import active_practice, attempts as attempts_data, goals, practice_sets, queries
from workbench.domain import (
    cards as card_rules, difficulty as difficulty_rules, feedback, learning_state, planning, pull,
    schedule as schedule_rules, signals as signal_rules, weak,
)
from workbench.server import context as agent_context

ORIGIN_KINDS = {"source_problem", "adapted_problem", "generated_grounded"}


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _query_int(params, name, default, *, minimum=0, maximum=None):
    raw = params.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(400, f"{name} must be an integer") from exc
    if value < minimum or maximum is not None and value > maximum:
        bounds = f"at least {minimum}" if maximum is None else f"from {minimum} to {maximum}"
        raise ApiError(400, f"{name} must be {bounds}")
    return value


def hub_workspaces(pool, workspace, params, body):
    from workbench import registry
    results = []
    for ws in registry.list_workspaces():
        entry = {"name": ws["name"], "path": ws["path"]}
        try:
            ws_pool = _pool_for(ws)
        except ValueError as exc:
            results.append({**entry, "error": str(exc)})
            continue
        try:
            entry["stats"] = queries.hub_stats(ws_pool)
        except Exception as exc:  # one broken pool must not blank the whole hub
            entry["error"] = str(exc)
        finally:
            ws_pool.close()
        results.append(entry)
    return results


def _pool_for(workspace):
    from workbench.data import pool as pool_mod
    root = Path(workspace["path"])
    return pool_mod.Pool(
        root=root,
        db_path=root / workspace["db"],
        course=workspace.get("active_course", ""),
        chapter=workspace.get("active_chapter", ""),
    )


def set_chapter_lens(pool, workspace, params, body):
    """The top-bar chapter switch: the human writer of the one active-chapter value.

    Empty chapter means the whole course. `lesson-kit use` writes the same value.
    """
    from workbench import registry
    chapter = body.get("chapter", "")
    if not isinstance(chapter, str):
        raise ApiError(400, "chapter must be a string or empty")
    try:
        registry.update_active(
            workspace["name"], workspace.get("active_course", ""), chapter)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"chapter": chapter, "chapters": pool.chapters()}


def weak_list(pool, workspace, params, body):
    prefix = pool.scope_prefix()
    limit = _query_int(params, "limit", 20, maximum=1000)
    return weak.score_all(
        pool.kps(prefix), pool.signals(), pool.schedule_rows(),
        pool.relations(), set(), date.today(),
    )[:limit]


def due_list(pool, workspace, params, body):
    limit = _query_int(params, "limit", 100, maximum=1000)
    return queries.due_list(pool)[:limit]


def calendar_view(pool, workspace, params, body):
    return queries.calendar_view(pool, workspace)


def daily_plan(pool, workspace, params, body):
    path = _plan_path(workspace)
    if path.is_file():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if (saved.get("plan_version") == 1
                    and saved.get("plan_date") == date.today().isoformat()):
                return saved
        except (OSError, ValueError, AttributeError):
            pass
    plan = planning.build_baseline_plan(
        queries.planning_facts(pool, workspace), now=datetime.now()
    )
    plan.update({"plan_version": 1, "plan_date": date.today().isoformat()})
    _persist_plan(path, plan)
    return plan


def daily_plan_recalculate(pool, workspace, params, body):
    baseline = planning.build_baseline_plan(
        queries.planning_facts(pool, workspace), now=datetime.now()
    )
    plan = planning.apply_adjustment(baseline, (body or {}).get("adjustment"))
    plan.update({"plan_version": 1, "plan_date": date.today().isoformat()})
    _persist_plan(_plan_path(workspace), plan)
    return {"plan": plan, "status": "已更新今日计划"}


def _persist_plan(path, plan):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def goals_list(pool, workspace, params, body):
    return goals.list_goals(workspace["path"])


def goals_create(pool, workspace, params, body):
    try:
        goal = goals.create_goal(workspace["path"], body or {})
        _invalidate_plan(workspace)
        return {"goal": goal}
    except ValueError as exc:
        raise ApiError(400, str(exc))


def goals_update(pool, workspace, params, body):
    try:
        goal = goals.update_goal(workspace["path"], params["goal_id"], body or {})
        _invalidate_plan(workspace)
        return {"goal": goal}
    except ValueError as exc:
        raise ApiError(400, str(exc))


def goals_delete(pool, workspace, params, body):
    result = goals.delete_goal(workspace["path"], params["goal_id"])
    _invalidate_plan(workspace)
    return result


def _plan_path(workspace):
    return goals.plan_path(workspace)


def _invalidate_plan(workspace):
    """Shared with the CLI (`lesson-kit goals`), so both surfaces drop the cache."""
    goals.invalidate_plan(workspace)


def pull_problems(pool, workspace, params, body):
    body = _request_object(body)
    kp_ids = body.get("kp_ids")
    if not isinstance(kp_ids, list) or not kp_ids or not all(
        isinstance(item, str) and item for item in kp_ids
    ):
        raise ApiError(400, "kp_ids must be a non-empty string list")
    unknown = [kp_id for kp_id in kp_ids if pool.kp(kp_id) is None]
    if unknown:
        raise ApiError(404, f"unknown knowledge point: {unknown[0]}")
    n = body.get("n", 5)
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 100:
        raise ApiError(400, "n must be an integer from 1 to 100")
    mode = body.get("mode", "weak")
    if mode not in {"weak", "random", "all", *pull.PRACTICE_MODES}:
        raise ApiError(400, "invalid practice mode")
    exclude_ids = body.get("exclude_ids", [])
    if not isinstance(exclude_ids, list) or not all(
        isinstance(item, str) for item in exclude_ids
    ):
        raise ApiError(400, "exclude_ids must be a string list")
    include_ids = body.get("include_ids", [])
    if not isinstance(include_ids, list) or not all(
        isinstance(item, str) and item for item in include_ids
    ):
        raise ApiError(400, "include_ids must be a non-empty string list")
    if include_ids and mode == "all":
        raise ApiError(400, "include_ids cannot be combined with mode all")
    origin_kinds = body.get("origin_kinds") or []
    if not isinstance(origin_kinds, list) or not all(
        isinstance(item, str) and item for item in origin_kinds
    ):
        raise ApiError(400, "origin_kinds must be a string list")
    if not set(origin_kinds) <= ORIGIN_KINDS:
        raise ApiError(400, "invalid origin_kinds")
    source_group = body.get("source_group")
    if source_group not in {None, "textbook", "exam", "ai_generated", "other"}:
        raise ApiError(400, "invalid source_group")
    difficulty_min = body.get("difficulty_min")
    difficulty_max = body.get("difficulty_max")
    for name, value in (("difficulty_min", difficulty_min), ("difficulty_max", difficulty_max)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 5
        ):
            raise ApiError(400, f"{name} must be a number from 1 to 5")
    if difficulty_min is not None and difficulty_max is not None and difficulty_min > difficulty_max:
        raise ApiError(400, "difficulty_min must not exceed difficulty_max")
    dimension_ranges = body.get("difficulty_dimensions", {})
    if not isinstance(dimension_ranges, dict) or set(dimension_ranges) - set(difficulty_rules.DIMENSIONS):
        raise ApiError(400, "difficulty_dimensions contains an unknown dimension")
    for name, bounds in dimension_ranges.items():
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ApiError(400, f"{name} range must be [min, max]")
        low, high = bounds
        if any(value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5
        ) for value in bounds):
            raise ApiError(400, f"{name} bounds must be integers from 1 to 5")
        if low is not None and high is not None and low > high:
            raise ApiError(400, f"{name} minimum must not exceed maximum")
    difficulty_strategy = body.get("difficulty_strategy")
    if difficulty_strategy not in {None, "balanced"}:
        raise ApiError(400, "invalid difficulty_strategy")
    filters = body.get("filters", {})
    if not isinstance(filters, dict):
        raise ApiError(400, "filters must be an object")
    unknown = set(filters) - {"source_kinds", "exam_years", "docs", "origin_kinds"}
    if unknown:
        raise ApiError(400, f"filters has unknown dimension(s): {sorted(unknown)}")
    def _dimension(name):
        value = filters.get(name)
        if value is None:
            return []
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ApiError(400, f"filters.{name} must be a string list")
        return value
    exam_year_single = body.get("exam_year")
    if exam_year_single is not None and (
        not isinstance(exam_year_single, str) or not exam_year_single
    ):
        raise ApiError(400, "exam_year must be a string")
    filter_origins = _dimension("origin_kinds")
    if filter_origins and not set(filter_origins) <= ORIGIN_KINDS:
        raise ApiError(400, "invalid origin_kinds")
    return pull.select(
        pool, kp_ids, n=n, mode=mode, source_kind=body.get("source_kind"),
        origin_kinds=set(origin_kinds) | set(filter_origins),
        source_group=source_group,
        exclude_ids=set(exclude_ids), include_ids=set(include_ids),
        difficulty_min=difficulty_min, difficulty_max=difficulty_max,
        difficulty_dimensions=dimension_ranges,
        difficulty_strategy=difficulty_strategy,
        exam_year=exam_year_single,
        source_kinds=_dimension("source_kinds"),
        exam_years=_dimension("exam_years"),
        evidence_docs=_dimension("docs"),
    )


def pull_facets(pool, workspace, params, body):
    """The filter dimensions of this pool, each value with its row count."""
    from workbench.domain import facets

    return facets.pool_facets(pool)


def search_problems(pool, workspace, params, body):
    """A lightweight picker feed for the filter panel's two keyword boxes."""
    return queries.search_problems(
        pool, stem_q=params.get("stem"), source_q=params.get("source"),
    )


def records_overview(pool, workspace, params, body):
    """The practice history feed behind the records page."""
    problem_id = params.get("problem") or None
    limit = _query_int(params, "limit", 100, minimum=1, maximum=500)
    return queries.records_overview(pool, limit=limit, problem_id=problem_id)


def pull_cards(pool, workspace, params, body):
    """Pull flash cards inside the selected scope; due rows first."""
    body = _request_object(body)
    kp_ids = body.get("kp_ids")
    if not isinstance(kp_ids, list) or not kp_ids or not all(
        isinstance(item, str) and item for item in kp_ids
    ):
        raise ApiError(400, "kp_ids must be a non-empty string list")
    unknown = [kp_id for kp_id in kp_ids if pool.kp(kp_id) is None]
    if unknown:
        raise ApiError(404, f"unknown knowledge point: {unknown[0]}")
    exclude_ids = body.get("exclude_ids", [])
    if not isinstance(exclude_ids, list) or not all(
        isinstance(item, str) for item in exclude_ids
    ):
        raise ApiError(400, "exclude_ids must be a string list")
    exclude = set(exclude_ids)
    direction_mode = body.get("direction_mode", "forward")
    if direction_mode not in {"forward", "reverse"}:
        raise ApiError(400, "direction_mode must be forward or reverse")
    exclude_directions = body.get("exclude_directions", [])
    if not isinstance(exclude_directions, list) or not all(
        isinstance(item, str) for item in exclude_directions
    ):
        raise ApiError(400, "exclude_directions must be a string list")
    return {"cards": card_rules.select(
        pool.cards_for_kps(kp_ids), pool.schedule_rows(),
        preference=direction_mode, excluded_ids=exclude,
        excluded_directions=set(exclude_directions), today=date.today().isoformat(),
    )}


def practice_sets_list(pool, workspace, params, body):
    return {"practice_sets": practice_sets.list_saved(pool)}


def practice_sets_create(pool, workspace, params, body):
    body = _request_object(body)
    try:
        return practice_sets.create_saved(
            pool, body.get("title"), body.get("problem_ids"),
            request=body.get("request"))
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_set_get(pool, workspace, params, body):
    try:
        return practice_sets.get_saved(pool, params["practice_set_id"])
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_set_update(pool, workspace, params, body):
    body = _request_object(body)
    allowed = {"title", "problem_ids", "request"}
    extra = set(body) - allowed
    if extra:
        raise ApiError(400, f"unsupported practice-set field: {sorted(extra)[0]}")
    if not body:
        raise ApiError(400, "practice-set update is empty")
    try:
        return practice_sets.update_saved(
            pool, params["practice_set_id"],
            title=body.get("title"),
            problem_ids=body.get("problem_ids"),
            request=body.get("request"))
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_set_delete(pool, workspace, params, body):
    try:
        return practice_sets.delete_saved(pool, params["practice_set_id"])
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_set_render(pool, workspace, params, body):
    try:
        return practice_sets.render_saved(pool, params["practice_set_id"])
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_set_start(pool, workspace, params, body):
    body = _request_object(body)
    replace = body.get("replace", False)
    if not isinstance(replace, bool):
        raise ApiError(400, "replace must be a boolean")
    practice_mode = body.get("practice_mode", "exam")
    rating_mode = body.get("rating_mode", "immediate")
    if practice_mode not in {"exam", "micro", "yes_no"}:
        raise ApiError(400, "practice_mode must be exam, micro, or yes_no")
    if rating_mode not in {"immediate", "batch", "off"}:
        raise ApiError(400, "rating_mode must be immediate, batch, or off")
    try:
        record = practice_sets.get_saved(pool, params["practice_set_id"])
        problem_ids = [item["problem_id"] for item in record["plan"]["items"]]
        kp_ids = []
        for problem_id in problem_ids:
            problem = pool.problem(problem_id)
            for kp_id in (problem or {}).get("kp_ids", []):
                if kp_id not in kp_ids:
                    kp_ids.append(kp_id)
        return active_practice.create(pool, {
            "source_kind": "practice_set",
            "source_ref": record["practice_set_id"],
            "source_label": record["title"],
            "kp_ids": kp_ids,
            "practice_mode": practice_mode,
            "rating_mode": rating_mode,
            "items": [
                {"item_type": "problem", "item_id": problem_id}
                for problem_id in problem_ids
            ],
        }, replace=replace)
    except active_practice.ActivePracticeConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except (active_practice.ActivePracticeError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc


def active_practice_get(pool, workspace, params, body):
    try:
        return {"practice": active_practice.current(pool)}
    except active_practice.ActivePracticeError as exc:
        raise ApiError(400, str(exc)) from exc


def active_practice_create(pool, workspace, params, body):
    body = _request_object(body)
    replace = body.get("replace", False)
    if not isinstance(replace, bool):
        raise ApiError(400, "replace must be a boolean")
    payload = {key: value for key, value in body.items() if key != "replace"}
    try:
        return active_practice.create(pool, payload, replace=replace)
    except active_practice.ActivePracticeConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except active_practice.ActivePracticeError as exc:
        raise ApiError(400, str(exc)) from exc


def active_practice_update(pool, workspace, params, body):
    body = _request_object(body)
    position = body.get("position")
    state = body.get("state")
    attempt_id = body.get("attempt_id")
    try:
        return active_practice.mark(
            pool, position, state, attempt_id=attempt_id)
    except active_practice.ActivePracticeConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except active_practice.ActivePracticeError as exc:
        raise ApiError(400, str(exc)) from exc


def active_practice_delete(pool, workspace, params, body):
    try:
        return active_practice.clear(pool)
    except active_practice.ActivePracticeError as exc:
        raise ApiError(400, str(exc)) from exc


def practice_run_replay(pool, workspace, params, body):
    body = _request_object(body)
    replace = body.get("replace", False)
    if not isinstance(replace, bool):
        raise ApiError(400, "replace must be a boolean")
    try:
        run_id = int(params["run_id"])
        return active_practice.replay(pool, run_id, replace=replace)
    except active_practice.ActivePracticeConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except (active_practice.ActivePracticeError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc


def practice(pool, workspace, params, body):
    body = _request_object(body)
    problem_id = body.get("problem_id")
    result = body.get("result")
    if not problem_id or not result:
        raise ApiError(400, "problem_id and result are required")
    if not isinstance(problem_id, str):
        raise ApiError(400, "problem_id must be a string")
    if pool.problem(problem_id) is None:
        raise ApiError(404, f"unknown problem: {problem_id}")
    if result not in schedule_rules.RESULT_QUALITY:
        raise ApiError(400, "invalid practice result")
    practice_position = body.get("practice_position")
    if practice_position is not None and (
        isinstance(practice_position, bool) or not isinstance(practice_position, int)
        or practice_position < 0
    ):
        raise ApiError(400, "practice_position must be a non-negative integer")
    return attempts_data.record_result(
        pool, problem_id, result, note=body.get("note"),
        answer_text=body.get("answer_text"),
        practice_position=practice_position)


def feedback_record(pool, workspace, params, body):
    body = _request_object(body)
    item_type = body.get("item_type")
    item_id = body.get("item_id")
    rating = body.get("rating")
    note = body.get("note")
    if item_type not in {"kp", "problem", "card"}:
        raise ApiError(400, "item_type must be kp, problem, or card")
    if not isinstance(item_id, str) or not item_id:
        raise ApiError(400, "item_id is required")
    if item_type == "kp":
        item = pool.kp(item_id)
    elif item_type == "card":
        item = pool.card(item_id)
    else:
        item = pool.problem(item_id)
    if item is None:
        raise ApiError(404, f"unknown {item_type}: {item_id}")
    if rating is not None and (
        isinstance(rating, bool) or not isinstance(rating, int) or rating not in range(1, 6)
    ):
        raise ApiError(400, "rating must be an integer from 1 to 5")
    if note is not None and not isinstance(note, str):
        raise ApiError(400, "note must be a string")
    if rating is None and not (note and note.strip()):
        raise ApiError(400, "rating or note is required")
    direction = body.get("direction", "")
    if not isinstance(direction, str):
        raise ApiError(400, "direction must be a string")
    if item_type == "card" and direction not in {"", *item["directions"]}:
        raise ApiError(400, "direction is not available for this card")
    attempt_id = body.get("attempt_id")
    if attempt_id is not None:
        if isinstance(attempt_id, bool) or not isinstance(attempt_id, int):
            raise ApiError(400, "attempt_id must be an integer")
        attempt = pool.attempt(attempt_id)
        if attempt is None or attempt["problem_id"] != item_id:
            raise ApiError(400, "attempt_id does not belong to this item")
    try:
        return attempts_data.record_browser_feedback(
            pool, item_type, item_id, rating=rating, note=note,
            direction=direction, attempt_id=attempt_id,
            request_id=_browser_request_id(body))
    except attempts_data.RequestConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except attempts_data.ManifestError as exc:
        raise ApiError(400, str(exc)) from exc


def attempt_record(pool, workspace, params, body):
    """Persist one answer the practice page just submitted (no rating effects)."""
    body = _request_object(body)
    problem_id = body.get("problem_id")
    if not isinstance(problem_id, str) or not problem_id:
        raise ApiError(400, "problem_id is required")
    answer_text = body.get("answer_text")
    if answer_text is not None and not isinstance(answer_text, str):
        raise ApiError(400, "answer_text must be a string")
    verdict = body.get("verdict")
    if verdict is not None and not isinstance(verdict, bool):
        raise ApiError(400, "verdict must be a boolean")
    choices = body.get("choices")
    if choices is not None and (
            not isinstance(choices, list)
            or not all(isinstance(choice, str) for choice in choices)):
        raise ApiError(400, "choices must be a list of option texts")
    try:
        practice_position = body.get("practice_position")
        if practice_position is not None and (
            isinstance(practice_position, bool)
            or not isinstance(practice_position, int)
            or practice_position < 0
        ):
            raise ApiError(400, "practice_position must be a non-negative integer")
        stuck = body.get("stuck", False)
        if not isinstance(stuck, bool):
            raise ApiError(400, "stuck must be a boolean")
        return attempts_data.record_browser_attempt(
            pool, problem_id, answer_text=answer_text,
            verdict=None if verdict is None else int(verdict), choices=choices,
            request_id=_browser_request_id(body),
            practice_position=practice_position, stuck=stuck)
    except attempts_data.RequestConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except attempts_data.ManifestError as exc:
        raise ApiError(400, str(exc)) from exc


def _browser_request_id(body):
    request_id = body.get("request_id")
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
        or len(request_id) > 200
    ):
        raise ApiError(400, "request_id must be a non-empty string of at most 200 characters")
    return request_id


def _request_object(body):
    if not isinstance(body, dict):
        raise ApiError(400, "request body must be a JSON object")
    return body


def ingest_batches(pool, workspace, params, body):
    """Current state of every batch, so a reopened card can stop offering rollback."""
    return ingest.list_batches(pool.db_path)


def ingest_rollback(pool, workspace, params, body):
    body = _request_object(body)
    batch_id = body.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id:
        raise ApiError(400, "batch_id must be a non-empty string")
    try:
        return ingest.rollback_batch(pool.db_path, batch_id)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def problem_detail(pool, workspace, params, body):
    return queries.problem_detail(pool, params["problem_id"])


def kp_detail(pool, workspace, params, body):
    return queries.kp_detail(pool, params["kp_id"])


def graph_model(pool, workspace, params, body):
    weights = {
        target_id: row["weight"]
        for target_id, row in signal_rules.strongest_by_target(pool.signals()).items()
    }
    return queries.graph_model(pool, weights)


def graph_state(pool, workspace, params, body):
    item_type = body.get("item_type")
    item_id = body.get("item_id")
    state = body.get("state")
    if item_type not in ("kp", "problem") or state not in learning_state.STATE_RATING:
        raise ApiError(400, "invalid graph state")
    item = pool.kp(item_id) if item_type == "kp" else pool.problem(item_id)
    if item is None:
        raise ApiError(404, f"unknown {item_type}: {item_id}")
    schedule_row = learning_state.apply(pool, item_type, item_id, state)
    return {"item_type": item_type, "item_id": item_id, "state": state,
            "due_at": schedule_row["due_at"]}


def graph_kp(pool, workspace, params, body):
    kp_id = body.get("kp_id")
    content = body.get("body")
    fragile = body.get("fragile")
    if not isinstance(kp_id, str) or not isinstance(content, str) or not isinstance(fragile, str):
        raise ApiError(400, "invalid knowledge point content")
    if pool.kp(kp_id) is None:
        raise ApiError(404, f"unknown knowledge point: {kp_id}")
    pool.update_kp_content(kp_id, content, fragile)
    return {"kp_id": kp_id, "body": content, "fragile": fragile}


def ai_providers(pool, workspace, params, body):
    """Return model choices grouped by harness identity in one flat wire catalog."""
    entries = []
    for harness in conversation_providers.discover():
        name = harness["name"]
        runtime_models = []
        if name == "pi":
            try:
                process = pi_rpc.PiRpcProcess(harness, workspace["path"])
                try:
                    process.start()
                    runtime_models = process.available_models()
                finally:
                    process.close()
            except (KeyError, OSError, pi_rpc.PiRpcError):
                runtime_models = []
        for entry in conversation_providers.list_models(
                name, runtime_models=runtime_models):
            entries.append({
                "name": entry["name"],
                "provider": name,
                "model": entry.get("model"),
                "entry": entry.get("entry"),
                "source": entry.get("source", "configured"),
            })
    return entries


def _session_call(func, *args):
    """A refused conversation/turn identifier is a client error, not a server fault."""
    try:
        return func(*args)
    except conversations.InvalidIdentifier as exc:
        raise ApiError(400, str(exc)) from exc


def ai_sessions_list(pool, workspace, params, body):
    return conversations.list_sessions(pool)


def ai_sessions_create(pool, workspace, params, body):
    provider = body.get("provider")
    if not isinstance(provider, str) or not provider:
        raise ApiError(400, "provider is required")
    try:
        title = body.get("title", "")
        if title is not None and not isinstance(title, str):
            raise ApiError(400, "title must be a string")
        model = body.get("model")
        entry = body.get("entry")
        if model is not None and not isinstance(model, str):
            raise ApiError(400, "model must be a string")
        if entry is not None and not isinstance(entry, str):
            raise ApiError(400, "entry must be a string")
        return conversations.create(
            pool, provider, title or "", model=model, entry=entry)
    except (KeyError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc


def ai_session_update(pool, workspace, params, body):
    body = _request_object(body)
    if "provider" in body:
        raise ApiError(
            400, "conversation harness cannot be changed; create a new conversation")
    has_title = "title" in body
    has_target = any(key in body for key in ("model", "entry"))
    title = body.get("title")
    model = body.get("model")
    if model == "":
        model = None
    entry = body.get("entry")
    if not has_title and not has_target:
        raise ApiError(400, "title or model target is required")
    if has_title and title is not None and not isinstance(title, str):
        raise ApiError(400, "title must be a string")
    if model is not None and not isinstance(model, str):
        raise ApiError(400, "model must be a string or null")
    if entry is not None and not isinstance(entry, str):
        raise ApiError(400, "entry must be a string")
    try:
        record = None
        if has_target:
            record = conversations.set_model(
                pool, params["conversation_id"], model, entry=entry)
        if has_title and isinstance(title, str) and title.strip():
            record = conversations.rename(pool, params["conversation_id"], title)
        return record
    except (KeyError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def ai_session_delete(pool, workspace, params, body):
    try:
        return conversations.delete(pool, params["conversation_id"])
    except conversations.InvalidIdentifier as exc:
        raise ApiError(400, str(exc)) from exc
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def ai_session_get(pool, workspace, params, body):
    return _session_call(conversations.get, pool, params["conversation_id"])


def ai_turn_start(pool, workspace, params, body):
    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ApiError(400, "message is required")
    # The conversation owns the staged-manifest directory; the body cannot pick it.
    framed = {**body, "conversation_id": params["conversation_id"]}
    context = agent_context.build(pool, workspace, framed)
    try:
        return conversations.start_turn(
            pool, workspace, params["conversation_id"], message.strip(), context
        )
    except conversations.InvalidIdentifier as exc:
        raise ApiError(400, str(exc)) from exc
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def ai_turn_events(pool, workspace, params, body):
    turn = _session_call(
        conversations.get_turn, pool, params["conversation_id"], params["turn_id"]
    )
    return {
        "turn": turn,
        "events": _session_call(
            conversations.events, pool, params["conversation_id"], params["turn_id"],
            _query_int(params, "after", 0),
        ),
    }


def ai_turn_cancel(pool, workspace, params, body):
    try:
        return conversations.cancel(pool, params["conversation_id"])
    except conversations.InvalidIdentifier as exc:
        raise ApiError(400, str(exc)) from exc
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def graph_artifact(pool, workspace, params, body):
    """Serve the rendered graph HTML, or 404 with a generation hint."""
    course = workspace.get("active_course", "")
    chapter = workspace.get("active_chapter", "")
    path = (Path(workspace["path"]) / "output" / course / chapter
            / f"{chapter}-graph.html")
    if not path.is_file():
        raise ApiError(
            404,
            "graph artifact missing — run: python pool/scripts/render-graph-html.py "
            f"--db {workspace['db']} --course {course} --chapter {chapter} "
            f"--course-name \"...\" --out output/{course}/{chapter}",
        )
    return {"html": path.read_text(encoding="utf-8")}
