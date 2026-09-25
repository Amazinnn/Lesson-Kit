"""Rebuild bounded Agent context from browser identifiers and Pool data."""

from workbench.data import queries


# Focused practice drafts ride along with one turn only. They are learner input,
# never pool facts, and are bounded so a pasted essay cannot flood the prompt.
DRAFT_ANSWER_CHARS = 2000
DRAFT_NOTE_CHARS = 500
DRAFT_CHOICES = 20
DRAFT_CHOICE_CHARS = 200
DRAFT_IMAGES = 12
DRAFT_IMAGE_CHARS = 300


def build(pool, workspace, payload):
    page_type = payload.get("page_type") or "unknown"
    anchor = {
        "route": payload.get("route") or "",
        "page_type": page_type,
    }
    prefix = pool.scope_prefix()
    result = {
        "workspace": {
            "name": workspace["name"],
            "course": workspace.get("active_course", ""),
            "chapter": workspace.get("active_chapter", ""),
        },
        "anchor": anchor,
        "current": {},
        "recent_objects": _recent(pool, payload.get("recent_objects", [])),
        "knowledge_point_ids": [kp["kp_id"] for kp in pool.kps(prefix)],
        "practice_intent": bool(payload.get("practice_intent")),
        "goal_intent": bool(payload.get("goal_intent")),
        "check_intent": bool(payload.get("check_intent")),
    }
    conversation_id = payload.get("conversation_id")
    if isinstance(conversation_id, str) and conversation_id:
        # Where a large manifest is staged: relative to the workspace root, the
        # same base the provider's file tools and cwd already use.
        result["staged_manifest_dir"] = f".lessonkit/jobs/{conversation_id}"
    if payload.get("check_intent"):
        result["next_free_ids"] = _next_free_ids(pool, prefix)
    if page_type == "practice":
        _practice(pool, payload, result)
    elif page_type == "kp":
        _kp(pool, payload.get("kp_id"), result)
    elif page_type == "graph":
        _graph(pool, payload, result)
    return result


def _next_free_ids(pool, prefix):
    return pool.next_free_content_ids(prefix)


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
        result["current"]["draft"] = _draft(payload)


def _draft(payload):
    """The focused turn's unsent learner input: bounded, ephemeral, unwritten."""
    answer, cut = _bounded_text(payload.get("draft_answer"), DRAFT_ANSWER_CHARS)
    note, note_cut = _bounded_text(payload.get("draft_note"), DRAFT_NOTE_CHARS)
    choices, choices_cut = _bounded_list(
        payload.get("draft_choices"), DRAFT_CHOICES, DRAFT_CHOICE_CHARS)
    images, images_cut = _bounded_list(
        payload.get("draft_images"), DRAFT_IMAGES, DRAFT_IMAGE_CHARS)
    draft = {"answer": answer, "note": note, "choices": choices, "images": images}
    if cut or note_cut or choices_cut or images_cut:
        draft["truncated"] = True
    return draft


def _bounded_text(value, limit):
    if not isinstance(value, str):
        return "", False
    return value[:limit], len(value) > limit


def _bounded_list(value, count, width):
    if not isinstance(value, list):
        return [], False
    texts = [item[:width] for item in value if isinstance(item, str) and item]
    return texts[:count], len(texts) > count or any(
        len(item) > width for item in value if isinstance(item, str))


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
    states = graph_filter.get("states")
    if not isinstance(states, list):
        states = [graph_filter["state"]] if graph_filter.get("state") else []
    result["current"] = {
        "filter": {
            "query": graph_filter.get("query") or "",
            "state": states[0] if len(states) == 1 else "",
            "states": states,
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
