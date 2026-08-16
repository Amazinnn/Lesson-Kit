"""View queries: hub stats, due list, detail pages, figures."""

from datetime import date


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


def due_list(pool):
    today = date.today()
    items = []
    for row in pool.schedule_rows():
        if not _is_due(row, today):
            continue
        label = _item_label(pool, row["item_type"], row["item_id"])
        items.append({
            "item_type": row["item_type"],
            "item_id": row["item_id"],
            "due_at": row["due_at"],
            "interval_days": row["interval_days"],
            "ease": row["ease"],
            "last_rating": row["last_rating"],
            "label": label,
        })
    return items


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
    return {
        "kp": kp,
        "signals": signals,
        "problems": problems,
        "schedule": pool.schedule_get("kp", kp_id),
    }


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
