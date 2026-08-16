"""JSON API handlers. Each handler gets (pool, workspace, params, body)."""

import json
from datetime import date
from pathlib import Path

from workbench.bridge import runner
from workbench.data import queries
from workbench.domain import feedback, pull, schedule as schedule_rules, weak


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


def ai_run(pool, workspace, params, body):
    operation = params["operation"]
    if operation not in ("explain", "diagnose"):
        raise ApiError(400, "unknown operation")
    job_id = runner.run_ai_task(
        pool, Path(workspace["path"]), operation, body.get("problem_id"),
        provider_name=body.get("provider"), note=body.get("note"),
        user_answer=body.get("user_answer"), stuck_step=body.get("stuck_step"),
    )
    return {"job_id": job_id}


def ai_status(pool, workspace, params, body):
    from workbench.bridge import jobs
    return jobs.status(pool.jobs_dir(), params["job_id"])


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
