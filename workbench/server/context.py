"""Rebuild bounded Agent context from browser identifiers and Pool data."""

from workbench.data import active_practice, experience, practice_sets, queries


# Focused practice drafts ride along with one turn only. They are learner input,
# never pool facts, and are bounded so a pasted essay cannot flood the prompt.
DRAFT_ANSWER_CHARS = 2000
DRAFT_NOTE_CHARS = 500
DRAFT_CHOICES = 20
DRAFT_CHOICE_CHARS = 200
DRAFT_IMAGES = 12
DRAFT_IMAGE_CHARS = 300
SELECTED_KPS = 30
ACTIVE_ITEMS = 30
PRACTICE_SETS = 20
RECORDS = 20


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
        "selection": _selected_scope(pool, payload.get("selected_kp_ids", [])),
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
    elif page_type == "practice-sets":
        _practice_sets(pool, payload, result)
    elif page_type == "records":
        _records(pool, payload, result)
    elif page_type == "kps":
        result["current"] = {"selected_knowledge_points": result["selection"]["knowledge_points"]}
    return result


def _next_free_ids(pool, prefix):
    return pool.next_free_content_ids(prefix)


def _practice(pool, payload, result):
    problem_id = payload.get("problem_id")
    result["anchor"]["problem_id"] = problem_id
    try:
        active = active_practice.current(pool, resolve=False)
    except active_practice.ActivePracticeError:
        active = None
    active_summary = _active_summary(active)
    result["current"] = {
        "practice_mode": (
            active.get("practice_mode") if active else payload.get("practice_mode")
        ),
        "progress": (
            active_summary.get("progress") if active_summary
            else payload.get("progress") or {}
        ),
        "active_practice": active_summary,
        "selection": _practice_selection(payload.get("practice_selection")),
    }
    problem = pool.problem(problem_id) if problem_id else None
    if problem:
        result["current"]["problem"] = problem
        result["current"]["knowledge_points"] = [
            pool.kp(kp_id) for kp_id in problem["kp_ids"] if pool.kp(kp_id)
        ]
        result["current"]["submitted_attempts"] = pool.attempts(problem_id)[-10:]
        result["current"]["schedule"] = pool.schedule_get("problem", problem_id)
        result["current"]["state"] = pool.current_state("problem", problem_id)
    if payload.get("include_draft") is True:
        result["current"]["draft"] = _draft(payload)


def _active_summary(active):
    if not active:
        return None
    items = active.get("items") or []
    return {
        "source_kind": active.get("source_kind"),
        "source_ref": active.get("source_ref"),
        "kp_ids": list(active.get("kp_ids") or [])[:SELECTED_KPS],
        "practice_mode": active.get("practice_mode"),
        "rating_mode": active.get("rating_mode"),
        "cursor": active.get("cursor"),
        "progress": dict(active.get("progress") or {}),
        "items": [
            {
                "position": item.get("position"),
                "item_type": item.get("item_type"),
                "item_id": item.get("item_id"),
                "state": item.get("state"),
            }
            for item in items[:ACTIVE_ITEMS]
        ],
        "items_truncated": len(items) > ACTIVE_ITEMS,
    }



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


def _experience_context(pool, kp_id):
    record = experience.get(pool, kp_id)
    if record is None:
        return None
    return {
        **record,
        "problems": [
            _problem_summary(problem)
            for problem_id in record["problem_ids"]
            if (problem := pool.problem(problem_id)) is not None
        ],
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
    detail["practice_experience"] = _experience_context(pool, kp_id)
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
        selected_context["practice_experience"] = _experience_context(pool, selected)
        result["current"]["selected"] = selected_context


def _practice_selection(value):
    if not isinstance(value, dict):
        return {}
    filters = value.get("filters")
    if not isinstance(filters, dict):
        filters = {}
    count = value.get("count")
    if isinstance(count, bool) or not isinstance(count, int):
        count = None
    return {
        "kp_ids": [
            item for item in (value.get("kp_ids") or [])[:SELECTED_KPS]
            if isinstance(item, str)
        ],
        "practice_mode": (
            value.get("practice_mode")
            if isinstance(value.get("practice_mode"), str) else ""
        ),
        "count": count,
        "filters": {
            key: [
                item for item in values[:ACTIVE_ITEMS]
                if isinstance(item, str)
            ] if isinstance(values := filters.get(key), list) else []
            for key in (
                "source_kinds", "exam_years", "docs", "picked_problem_ids"
            )
        },
    }


def _selected_scope(pool, kp_ids):
    if not isinstance(kp_ids, list):
        kp_ids = []
    selected = []
    seen = set()
    for kp_id in kp_ids:
        if not isinstance(kp_id, str) or kp_id in seen:
            continue
        kp = pool.kp(kp_id)
        if kp is None:
            continue
        selected.append(kp)
        seen.add(kp_id)
        if len(selected) == SELECTED_KPS:
            break
    return {
        "kp_ids": [kp["kp_id"] for kp in selected],
        "knowledge_points": selected,
        "truncated": len(kp_ids) > len(selected),
    }


def _problem_summary(problem):
    return {
        "problem_id": problem.get("problem_id"),
        "title": problem.get("display_title") or (problem.get("problem_text") or "")[:80],
        "kp_ids": list(problem.get("kp_ids") or []),
        "source_kind": problem.get("source_kind"),
        "source_evidence": problem.get("source_evidence"),
        "difficulty": problem.get("difficulty"),
    }


def _practice_sets(pool, payload, result):
    records = practice_sets.list_saved(pool)
    result["current"] = {
        "practice_sets": [
            {
                "practice_set_id": record["practice_set_id"],
                "title": record["title"],
                "count": record["count"],
                "problems": [
                    _problem_summary(pool.problem(item["problem_id"]))
                    for item in record["plan"]["items"][:ACTIVE_ITEMS]
                    if pool.problem(item["problem_id"])
                ],
                "items_truncated": len(record["plan"]["items"]) > ACTIVE_ITEMS,
            }
            for record in records[:PRACTICE_SETS]
        ],
        "truncated": len(records) > PRACTICE_SETS,
    }
    practice_set_id = payload.get("practice_set_id")
    if isinstance(practice_set_id, str) and practice_set_id:
        try:
            record = practice_sets.get_saved(pool, practice_set_id)
        except (FileNotFoundError, ValueError):
            return
        result["anchor"]["practice_set_id"] = practice_set_id
        result["current"]["selected"] = {
            "practice_set_id": practice_set_id,
            "title": record["title"],
            "request": record["plan"].get("request") or {},
            "problems": [
                pool.problem(item["problem_id"])
                for item in record["plan"]["items"][:ACTIVE_ITEMS]
                if pool.problem(item["problem_id"])
            ],
            "items_truncated": len(record["plan"]["items"]) > ACTIVE_ITEMS,
        }


def _records(pool, payload, result):
    problem_id = payload.get("records_problem_id")
    if not isinstance(problem_id, str) or not problem_id:
        problem_id = None
    overview = queries.records_overview(pool, limit=RECORDS, problem_id=problem_id)
    result["anchor"]["problem_id"] = problem_id
    result["current"] = {
        "records": overview["records"],
        "count": overview["count"],
        "limit": RECORDS,
    }


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
