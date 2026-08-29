"""Rebuild bounded Agent context from browser identifiers and SQLite."""

from workbench.data import queries


def build(pool, workspace, payload):
    page_type = payload.get("page_type") or "unknown"
    anchor = {
        "route": payload.get("route") or "",
        "page_type": page_type,
    }
    result = {
        "workspace": {
            "name": workspace["name"],
            "course": workspace.get("active_course", ""),
            "chapter": workspace.get("active_chapter", ""),
        },
        "anchor": anchor,
        "current": {},
        "recent_objects": _recent(pool, payload.get("recent_objects", [])),
        "knowledge_point_ids": [kp["kp_id"] for kp in pool.kps(
            f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
        )],
        "practice_intent": bool(payload.get("practice_intent")),
        "goal_intent": bool(payload.get("goal_intent")),
        "check_intent": bool(payload.get("check_intent")),
    }
    if page_type == "practice":
        _practice(pool, payload, result)
    elif page_type == "kp":
        _kp(pool, payload.get("kp_id"), result)
    elif page_type == "graph":
        _graph(pool, payload, result)
    return result


def _practice(pool, payload, result):
    problem_id = payload.get("problem_id")
    result["anchor"]["problem_id"] = problem_id
    result["current"] = {
        "practice_mode": payload.get("practice_mode"),
        "progress": payload.get("progress") or {},
    }
    problem = pool.problem(problem_id) if problem_id else None
    if problem:
        result["current"]["problem"] = problem
        result["current"]["knowledge_points"] = [
            pool.kp(kp_id) for kp_id in problem["kp_ids"] if pool.kp(kp_id)
        ]
        result["current"]["submitted_attempts"] = pool.attempts(problem_id)
        result["current"]["schedule"] = pool.schedule_get("problem", problem_id)
        result["current"]["state"] = pool.current_state("problem", problem_id)
    if payload.get("include_draft") is True:
        result["current"]["draft"] = {
            "answer": payload.get("draft_answer") or "",
            "note": payload.get("draft_note") or "",
        }


def _kp(pool, kp_id, result):
    result["anchor"]["kp_id"] = kp_id
    detail = queries.kp_detail(pool, kp_id)
    relations = [
        relation for relation in pool.relations()
        if kp_id in (relation["source_kp_id"], relation["target_kp_id"])
    ]
    neighbour_ids = {
        relation["target_kp_id"] if relation["source_kp_id"] == kp_id
        else relation["source_kp_id"]
        for relation in relations
    }
    detail["relations"] = relations
    detail["neighbours"] = [pool.kp(item) for item in sorted(neighbour_ids) if pool.kp(item)]
    result["current"] = detail


def _graph(pool, payload, result):
    selected = payload.get("selected_kp_id")
    result["anchor"]["selected_kp_id"] = selected
    graph_filter = payload.get("graph_filter") or {}
    result["current"] = {
        "filter": {
            "query": graph_filter.get("query") or "",
            "state": graph_filter.get("state") or "",
        },
        "relation_summary": pool.relations(),
    }
    if selected and pool.kp(selected):
        selected_context = {"kp": pool.kp(selected)}
        selected_context.update({
            key: value for key, value in queries.kp_detail(pool, selected).items()
            if key != "kp"
        })
        result["current"]["selected"] = selected_context


def _recent(pool, objects):
    recent = []
    seen = set()
    for item in objects:
        if not isinstance(item, dict):
            continue
        entity = item.get("type")
        object_id = item.get("id")
        key = (entity, object_id)
        if key in seen or entity not in ("kp", "problem"):
            continue
        value = pool.kp(object_id) if entity == "kp" else pool.problem(object_id)
        if value is None:
            continue
        recent.append({"type": entity, "id": object_id, "value": value})
        seen.add(key)
        if len(recent) == 3:
            break
    return recent
