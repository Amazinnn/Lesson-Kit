"""JSON API handlers. Each handler gets (pool, workspace, params, body)."""

import json
import threading
from datetime import date, datetime
from pathlib import Path

from workbench.bridge import conversation_providers, conversations, runner
from workbench.data import goals, queries
from workbench.domain import (
    feedback, learning_state, planning, pull, schedule as schedule_rules, weak,
)
from workbench.server import context as agent_context


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def hub_workspaces(pool, workspace, params, body):
    from workbench import registry
    results = []
    for ws in registry.list_workspaces():
        ws_pool = _pool_for(ws)
        try:
            stats = queries.hub_stats(ws_pool)
        finally:
            ws_pool.close()
        results.append({"name": ws["name"], "path": ws["path"], "stats": stats})
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


def weak_list(pool, workspace, params, body):
    prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
    limit = int(params.get("limit", "20"))
    return weak.score_all(
        pool.kps(prefix), pool.signals(), pool.schedule_rows(),
        pool.relations(), set(), date.today(),
    )[:limit]


def due_list(pool, workspace, params, body):
    return queries.due_list(pool)


def daily_plan(pool, workspace, params, body):
    path = _plan_path(workspace)
    if path.is_file():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved.get("plan_version") == 1:
                return saved
        except (OSError, ValueError, AttributeError):
            pass
    return planning.build_baseline_plan(
        queries.planning_facts(pool, workspace), now=datetime.now()
    )


def daily_plan_recalculate(pool, workspace, params, body):
    baseline = planning.build_baseline_plan(
        queries.planning_facts(pool, workspace), now=datetime.now()
    )
    plan = planning.apply_adjustment(baseline, (body or {}).get("adjustment"))
    plan["plan_version"] = 1
    path = _plan_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"plan": plan, "status": "已更新今日计划"}


def goals_list(pool, workspace, params, body):
    return goals.list_goals(workspace["path"])


def goals_create(pool, workspace, params, body):
    try:
        return {"goal": goals.create_goal(workspace["path"], body or {})}
    except ValueError as exc:
        raise ApiError(400, str(exc))


def goals_update(pool, workspace, params, body):
    try:
        return {"goal": goals.update_goal(workspace["path"], params["goal_id"], body or {})}
    except ValueError as exc:
        raise ApiError(400, str(exc))


def goals_delete(pool, workspace, params, body):
    return goals.delete_goal(workspace["path"], params["goal_id"])


def _plan_path(workspace):
    return Path(workspace["path"]) / ".lessonkit" / "plan.json"


def pull_problems(pool, workspace, params, body):
    return pull.select(
        pool, body.get("kp_ids", []), n=body.get("n", 5),
        mode=body.get("mode", "weak"), source_kind=body.get("source_kind"),
        exclude_ids=set(body.get("exclude_ids", [])),
    )


def practice(pool, workspace, params, body):
    problem_id = body.get("problem_id")
    result = body.get("result")
    if not problem_id or not result:
        raise ApiError(400, "problem_id and result are required")
    pool.insert_attempt(problem_id, result, body.get("note"),
                        body.get("answer_text"))
    status_map = {"correct": "reviewing", "wrong": "wrong", "stuck": "stuck"}
    if result in status_map:
        pool.upsert_problem_progress(problem_id, status_map[result], body.get("note"))
    state = pool.schedule_get("problem", problem_id) or schedule_rules.default_state(
        "problem", problem_id
    )
    next_state = schedule_rules.after_result(state, result, date.today())
    pool.schedule_upsert(next_state)
    return {"problem_id": problem_id, "result": result,
            "due_at": next_state["due_at"]}


def feedback_record(pool, workspace, params, body):
    return feedback.apply(
        pool, body.get("item_type"), body.get("item_id"),
        rating=body.get("rating"), note=body.get("note"),
    )


def problem_detail(pool, workspace, params, body):
    return queries.problem_detail(pool, params["problem_id"])


def kp_detail(pool, workspace, params, body):
    return queries.kp_detail(pool, params["kp_id"])


def graph_model(pool, workspace, params, body):
    return queries.graph_model(pool)


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


def ai_run(pool, workspace, params, body):
    operation = params["operation"]
    if operation not in ("explain", "diagnose"):
        raise ApiError(400, "unknown operation")
    problem_id = body.get("problem_id")
    if problem_id is None or pool.problem(problem_id) is None:
        raise ApiError(404, f"unknown problem: {problem_id}")
    workspace_path = Path(workspace["path"])
    provider_name = body.get("provider")
    note = body.get("note")
    user_answer = body.get("user_answer")
    stuck_step = body.get("stuck_step")
    job_id = runner.create_ai_task(
        pool, operation, problem_id, note=note,
        user_answer=user_answer, stuck_step=stuck_step,
    )

    def _run():
        # Provider runs on its own thread so the HTTP request returns
        # immediately (a provider run may take minutes). The worker opens
        # its own Pool — sqlite connections are not shareable across threads.
        worker_pool = _pool_for(workspace)
        try:
            runner.run_ai_task(
                worker_pool, workspace_path, operation, problem_id,
                provider_name=provider_name, note=note,
                user_answer=user_answer, stuck_step=stuck_step,
                job_id=job_id,
            )
        finally:
            worker_pool.close()

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id}


def ai_status(pool, workspace, params, body):
    from workbench.bridge import jobs
    return jobs.status(pool.jobs_dir(), params["job_id"])


def ai_providers(pool, workspace, params, body):
    return [
        {"name": provider["name"], "model": provider.get("model")}
        for provider in conversation_providers.discover()
    ]


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
        return conversations.create(pool, provider, title or "")
    except KeyError as exc:
        raise ApiError(400, str(exc)) from exc


def ai_session_update(pool, workspace, params, body):
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ApiError(400, "title is required")
    try:
        return conversations.rename(pool, params["conversation_id"], title)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def ai_session_delete(pool, workspace, params, body):
    try:
        return conversations.delete(pool, params["conversation_id"])
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def ai_session_get(pool, workspace, params, body):
    return conversations.get(pool, params["conversation_id"])


def ai_turn_start(pool, workspace, params, body):
    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ApiError(400, "message is required")
    context = agent_context.build(pool, workspace, body)
    try:
        return conversations.start_turn(
            pool, workspace, params["conversation_id"], message.strip(), context
        )
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def ai_turn_events(pool, workspace, params, body):
    turn = conversations.get_turn(
        pool, params["conversation_id"], params["turn_id"]
    )
    return {
        "turn": turn,
        "events": conversations.events(
            pool, params["conversation_id"], params["turn_id"],
            after=int(params.get("after", 0)),
        ),
    }


def ai_turn_cancel(pool, workspace, params, body):
    try:
        return conversations.cancel(pool, params["conversation_id"])
    except conversations.ConversationConflict as exc:
        raise ApiError(409, str(exc)) from exc


def explain_result(pool, workspace, params, body):
    path = pool.explain_dir() / f"{params['problem_id']}.md"
    if not path.is_file():
        raise ApiError(404, "no explain result yet")
    return {
        "problem_id": params["problem_id"],
        "markdown": path.read_text(encoding="utf-8"),
    }


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
