"""One optional reusable practice-experience summary per knowledge point."""


class RevisionConflict(ValueError):
    """The caller edited a revision that is no longer current."""


def get(pool, kp_id):
    row = pool.connect().execute(
        "SELECT kp_id, content, revision, updated_by, created_at, updated_at "
        "FROM kp_experiences WHERE kp_id=?",
        (kp_id,),
    ).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["problem_ids"] = [
        linked[0] for linked in pool.connect().execute(
            "SELECT problem_id FROM kp_experience_problems WHERE kp_id=? "
            "ORDER BY position, problem_id",
            (kp_id,),
        )
    ]
    return item


def create(pool, kp_id, content, problem_ids=None, updated_by="user"):
    with pool.transaction(immediate=True):
        text, ids = _validate(pool, kp_id, content, problem_ids, updated_by)
        if get(pool, kp_id) is not None:
            raise RevisionConflict(f"experience already exists for {kp_id}")
        pool.connect().execute(
            "INSERT INTO kp_experiences (kp_id, content, revision, updated_by) "
            "VALUES (?, ?, 1, ?)",
            (kp_id, text, updated_by),
        )
        _replace_links(pool, kp_id, ids)
    return get(pool, kp_id)


def update(pool, kp_id, expected_revision, content, problem_ids, updated_by="user"):
    """Replace one summary against the revision the editor previously read."""
    revision = _revision(expected_revision)
    with pool.transaction(immediate=True):
        text, ids = _validate(pool, kp_id, content, problem_ids, updated_by)
        current = get(pool, kp_id)
        if current is None:
            raise KeyError(kp_id)
        if current["revision"] != revision:
            raise RevisionConflict(
                f"experience revision changed: expected {revision}, current {current['revision']}"
            )
        pool.connect().execute(
            "UPDATE kp_experiences SET content=?, revision=revision+1, "
            "updated_by=?, updated_at=datetime('now') WHERE kp_id=?",
            (text, updated_by, kp_id),
        )
        _replace_links(pool, kp_id, ids)
    return get(pool, kp_id)


def delete(pool, kp_id, expected_revision):
    revision = _revision(expected_revision)
    with pool.transaction(immediate=True):
        current = get(pool, kp_id)
        if current is None:
            raise KeyError(kp_id)
        if current["revision"] != revision:
            raise RevisionConflict(
                f"experience revision changed: expected {revision}, current {current['revision']}"
            )
        pool.connect().execute(
            "DELETE FROM kp_experience_problems WHERE kp_id=?", (kp_id,)
        )
        pool.connect().execute("DELETE FROM kp_experiences WHERE kp_id=?", (kp_id,))
    return {"kp_id": kp_id, "deleted": True}


def _validate(pool, kp_id, content, problem_ids, updated_by):
    if pool.kp(kp_id) is None:
        raise KeyError(kp_id)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("experience content must be non-empty")
    if updated_by not in {"user", "agent"}:
        raise ValueError("updated_by must be user or agent")
    if problem_ids is None:
        problem_ids = []
    if not isinstance(problem_ids, list) or not all(
        isinstance(problem_id, str) and problem_id for problem_id in problem_ids
    ):
        raise ValueError("problem_ids must be a string list")
    ids = list(dict.fromkeys(problem_ids))
    for problem_id in ids:
        problem = pool.problem(problem_id)
        if problem is None:
            raise ValueError(f"unknown problem: {problem_id}")
        if kp_id not in problem["kp_ids"]:
            raise ValueError(
                f"problem {problem_id} is not linked to knowledge point {kp_id}"
            )
    return content.strip(), ids


def _revision(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("expected_revision must be a positive integer")
    return value


def _replace_links(pool, kp_id, problem_ids):
    conn = pool.connect()
    conn.execute("DELETE FROM kp_experience_problems WHERE kp_id=?", (kp_id,))
    conn.executemany(
        "INSERT INTO kp_experience_problems (kp_id, problem_id, position) "
        "VALUES (?, ?, ?)",
        [(kp_id, problem_id, position) for position, problem_id in enumerate(problem_ids)],
    )
