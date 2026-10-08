"""HTTP adapters for optional knowledge-point practice experience."""

from workbench.data import experience
from workbench.server.api import ApiError


def _record(pool, kp_id):
    record = experience.get(pool, kp_id)
    if record is None:
        return None
    return {
        **record,
        "problems": [
            {
                "problem_id": problem_id,
                "title": problem.get("display_title")
                or (problem.get("problem_text") or "")[:80]
                or problem_id,
            }
            for problem_id in record["problem_ids"]
            if (problem := pool.problem(problem_id)) is not None
        ],
    }


def get(pool, workspace, params, body):
    kp_id = params["kp_id"]
    if pool.kp(kp_id) is None:
        raise ApiError(404, f"unknown knowledge point: {kp_id}")
    return {"experience": _record(pool, kp_id)}


def create(pool, workspace, params, body):
    kp_id = params["kp_id"]
    body = body or {}
    try:
        experience.create(
            pool,
            kp_id,
            body.get("content"),
            body.get("problem_ids", []),
            updated_by="user",
        )
    except experience.RevisionConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"experience": _record(pool, kp_id)}


def update(pool, workspace, params, body):
    kp_id = params["kp_id"]
    body = body or {}
    try:
        experience.update(
            pool,
            kp_id,
            body.get("expected_revision"),
            body.get("content"),
            body.get("problem_ids", []),
            updated_by="user",
        )
    except experience.RevisionConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"experience": _record(pool, kp_id)}


def delete(pool, workspace, params, body):
    kp_id = params["kp_id"]
    try:
        expected_revision = int(params.get("expected_revision", ""))
    except (TypeError, ValueError) as exc:
        raise ApiError(400, "expected_revision must be an integer") from exc
    try:
        return experience.delete(pool, kp_id, expected_revision)
    except experience.RevisionConflict as exc:
        raise ApiError(409, str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
