"""HTTP adapter for the confirmed course learning preferences file.

Routing only: the course scope, the values and every validation rule belong to
`workbench.data.course_preferences`.
"""

from workbench.data import course_preferences
from workbench.server.api import ApiError


def _course(workspace):
    return workspace.get("active_course") or workspace["name"]


def get(pool, workspace, params, body):
    try:
        values = course_preferences.load_preferences(workspace["path"], _course(workspace))
    except course_preferences.CorruptPreferences as exc:
        raise ApiError(500, str(exc)) from exc
    return {"saved": bool(values), "values": values}


def update(pool, workspace, params, body):
    try:
        values = course_preferences.save_preferences(
            workspace["path"], _course(workspace), body)
    except course_preferences.CorruptPreferences as exc:
        raise ApiError(500, str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"saved": True, "values": values}
