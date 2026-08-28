"""View queries: hub stats, due list, detail pages, figures, graph data."""

from datetime import date, timedelta
import json
import sqlite3
from pathlib import Path


def hub_stats(pool):
    due = sum(1 for r in pool.schedule_rows() if _is_due(r, date.today()))
    prefix = f"{pool.course}-{pool.chapter}"
    return {
        "kps": len(pool.kps(prefix)),
        "problems": len(pool.problems_all()),
        "candidates": len(pool.gate_passed_candidates()),
        "signals": len(pool.signals()),
        "due": due,
    }


def planning_facts(pool, workspace):
    """Collect read-only facts for the Domain planner."""
    prefix = f"{pool.course}-{pool.chapter}"
    problems = pool.problems_all()
    progress = {}
    conn = pool.connect()
    try:
        rows = conn.execute(
            "SELECT problem_id, status FROM problem_progress"
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    for row in rows:
        progress.setdefault(row["problem_id"], {})["status"] = row["status"]
    totals = {}
    for problem in problems:
        for kp_id in problem.get("kp_ids") or []:
            totals[kp_id] = totals.get(kp_id, 0) + 1
    completed = {}
    for problem in problems:
        if progress.get(problem["problem_id"], {}).get("status") in {"correct", "reviewing"}:
            for kp_id in problem.get("kp_ids") or []:
                completed[kp_id] = completed.get(kp_id, 0) + 1
    progress_by_kp = {
        kp_id: {"total": total, "completed": completed.get(kp_id, 0)}
        for kp_id, total in totals.items()
    }
    goals = workspace.get("goals") or []
    goals_path = Path(workspace["path"]) / ".lessonkit" / "goals.json"
    if not goals and goals_path.is_file():
        try:
            goals = json.loads(goals_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            goals = []
    return {
        "course": pool.course,
        "chapter": pool.chapter,
        "goals": goals,
        "kps": pool.kps(prefix),
        "problems": problems,
        "progress": progress_by_kp,
        "signals": pool.signals(),
        "schedule": pool.schedule_rows(),
    }


def due_list(pool):
    today = date.today()
    items = []
    for row in pool.schedule_rows():
        if not _is_due(row, today):
            continue
        items.append(_due_item(row, pool, today))
    return items


def review_overview(pool, upcoming_days=7):
    """Due rows plus the next ``upcoming_days`` days, and a count of the rest."""
    today = date.today()
    items = []
    later_count = 0
    for row in pool.schedule_rows():
        try:
            days = (date.fromisoformat(str(row["due_at"])[:10]) - today).days
        except ValueError:
            days = 0
        if days <= upcoming_days:
            items.append(_due_item(row, pool, today))
        else:
            later_count += 1
    return {"items": items, "later_count": later_count}


def _due_item(row, pool, today):
    label = _item_label(pool, row["item_type"], row["item_id"])
    return {
        "item_type": row["item_type"],
        "item_id": row["item_id"],
        "direction": row.get("direction") or "",
        "due_at": row["due_at"],
        "interval_days": row["interval_days"],
        "ease": row["ease"],
        "last_rating": row["last_rating"],
        "label": label,
    }


def problem_detail(pool, problem_id):
    return {
        "problem": pool.problem(problem_id),
        "attempts": pool.attempts(problem_id),
        "schedule": pool.schedule_get("problem", problem_id),
    }


def kp_detail(pool, kp_id):
    kp = pool.kp(kp_id)
    signals = [s for s in pool.signals() if s["target_id"] == kp_id]
    problems = [p for p in pool.problems_all() if kp_id in p["kp_ids"]]
    for problem in problems:
        problem["current_state"] = pool.current_state("problem", problem["problem_id"])
    return {
        "kp": kp,
        "signals": signals,
        "problems": problems,
        "schedule": pool.schedule_get("kp", kp_id),
        "current_state": pool.current_state("kp", kp_id),
    }


def graph_model(pool, signal_weights=None):
    """Compose the graph view. signal_weights maps kp_id -> strongest weight;
    the caller aggregates signals via the Domain layer (Data imports no Domain)."""
    prefix = f"{pool.course}-{pool.chapter}"
    kps = pool.kps(prefix)
    ids = {kp["kp_id"] for kp in kps}
    current = {
        (row["item_type"], row["item_id"]): row["state"]
        for row in pool.current_states()
    }
    signals = signal_weights or {}
    problems = pool.problems_all()
    problem_count = {kp_id: 0 for kp_id in ids}
    problem_kps = []
    for problem in problems:
        kp_ids = {kp_id for kp_id in problem["kp_ids"] if kp_id in ids}
        problem_kps.append(kp_ids)
        for kp_id in kp_ids:
            problem_count[kp_id] += 1
    nodes = [
        {
            "id": kp["kp_id"],
            "title": kp.get("knowledge_item") or kp["kp_id"],
            "body": kp.get("body") or "",
            "fragile": kp.get("fragile") or "",
            "problem_count": problem_count[kp["kp_id"]],
            "importance": kp.get("importance") or "supplementary",
            "state": current.get(
                ("kp", kp["kp_id"]), _signal_state(signals.get(kp["kp_id"]))
            ),
        }
        for kp in kps
    ]
    edges = {}
    for relation in pool.relations():
        source = relation["source_kp_id"]
        target = relation["target_kp_id"]
        if source in ids and target in ids:
            _merge_graph_edge(
                edges, source, target, relation["relation_type"],
                relation.get("strength") or "medium",
            )
    for kp in kps:
        for related in json.loads(kp.get("related_kp_ids") or "[]"):
            if related in ids:
                _merge_graph_edge(edges, kp["kp_id"], related, "related", "medium")
    for edge in edges.values():
        shared = sum(
            1 for kp_ids in problem_kps
            if edge["source"] in kp_ids and edge["target"] in kp_ids
        )
        edge["shared_problem_count"] = shared
        coefficient = {"low": 0.75, "medium": 1.0, "high": 1.25}[edge["strength"]]
        edge["attraction"] = coefficient * min(1.5, 1 + shared * 0.1)
    return {"nodes": nodes, "edges": list(edges.values())}


def _merge_graph_edge(edges, source, target, relation_type, strength):
    if source == target:
        return
    source, target = sorted((source, target))
    key = (source, target)
    strength = strength if strength in {"low", "medium", "high"} else "medium"
    rank = {"low": 0, "medium": 1, "high": 2}
    current = edges.get(key)
    if current is None:
        edges[key] = {
            "source": source, "target": target,
            "relation_type": relation_type, "strength": strength,
        }
    elif rank[strength] > rank[current["strength"]]:
        current["strength"] = strength
        current["relation_type"] = relation_type


def figures_list(pool):
    figure_dir = pool.figures_dir()
    if not figure_dir.is_dir():
        return []
    prefix = f"{pool.course}/{pool.chapter}/"
    return sorted(
        prefix + name
        for name in (p.name for p in figure_dir.iterdir())
        if name.endswith((".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"))
    )


def _is_due(row, today):
    due_at = row.get("due_at")
    if not due_at:
        return False
    try:
        due_date = date.fromisoformat(due_at[:10])
    except ValueError:
        return False
    return due_date <= today


def _signal_state(weight):
    if weight == "high":
        return "needs_work"
    if weight:
        return "review"
    return None


def _item_label(pool, item_type, item_id):
    if item_type == "problem":
        problem = pool.problem(item_id)
        if problem:
            return problem["problem_text"][:40]
    else:
        kp = pool.kp(item_id)
        if kp:
            return kp["knowledge_item"]
    return item_id


def calendar_view(pool, workspace):
    """Read-only time view: goals plus a 14-day due histogram (today..+13)."""
    from workbench.data import goals as goals_data

    today = date.today()
    buckets = {}
    for offset in range(14):
        day = (today + timedelta(days=offset)).isoformat()
        buckets[day] = {"date": day, "count": 0, "overdue": 0}
    overdue = 0
    for row in pool.schedule_rows():
        key = str(row["due_at"])[:10]
        if key in buckets:
            buckets[key]["count"] += 1
        elif key < today.isoformat():
            overdue += 1
    days = list(buckets.values())
    if days:
        days[0]["overdue"] = overdue
    return {
        "goals": goals_data.list_goals(workspace["path"]),
        "days": days,
    }
