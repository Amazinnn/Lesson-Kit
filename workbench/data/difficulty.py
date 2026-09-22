"""Transactional objective-difficulty access."""

from workbench.domain import difficulty as rules


ITEM_FIELDS = {"problem_id", *rules.DIMENSIONS}


def check(pool, manifest):
    """Validate a complete rating manifest and return computed rows."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("items"), list):
        raise ValueError("difficulty manifest requires an items list")
    if not manifest["items"]:
        raise ValueError("difficulty manifest items must not be empty")
    rows = []
    seen = set()
    for item in manifest["items"]:
        if not isinstance(item, dict):
            raise ValueError("difficulty item must be an object")
        extra = set(item) - ITEM_FIELDS
        if extra:
            raise ValueError(f"difficulty item has unsupported field: {sorted(extra)[0]}")
        problem_id = item.get("problem_id")
        if not isinstance(problem_id, str) or not problem_id:
            raise ValueError("difficulty item requires problem_id")
        if problem_id in seen:
            raise ValueError(f"duplicate problem: {problem_id}")
        if pool.problem(problem_id) is None:
            raise ValueError(f"unknown problem: {problem_id}")
        vector = {name: item[name] for name in rules.DIMENSIONS if name in item}
        total = rules.score(vector)
        rows.append({
            "problem_id": problem_id,
            **vector,
            "difficulty": float(total),
            "difficulty_model": rules.MODEL_ID,
        })
        seen.add(problem_id)
    return {"model": rules.MODEL_ID, "items": rows}


def apply(pool, manifest):
    """Overwrite one complete validated rating batch atomically."""
    preview = check(pool, manifest)
    conn = pool.connect()
    conn.execute("BEGIN IMMEDIATE")
    try:
        for item in preview["items"]:
            conn.execute(
                "UPDATE problems SET difficulty=?, "
                "difficulty_knowledge_breadth=?, difficulty_reasoning_depth=?, "
                "difficulty_transfer_distance=?, difficulty_construction_openness=?, "
                "difficulty_model=? WHERE problem_id=?",
                (
                    item["difficulty"], item["knowledge_breadth"],
                    item["reasoning_depth"], item["transfer_distance"],
                    item["construction_openness"], item["difficulty_model"],
                    item["problem_id"],
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {**preview, "updated": len(preview["items"])}
