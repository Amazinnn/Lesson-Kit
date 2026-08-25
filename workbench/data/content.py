"""Transactional access to Agent-managed current content."""

import json


TABLES = {
    "kp": ("knowledge_points", "kp_id"),
    "problem": ("problems", "problem_id"),
    "candidate": ("candidate_problems", "candidate_id"),
    "relation": ("knowledge_relations", "relation_id"),
}

PREFIXES = {
    "kp": "kp",
    "problem": "prob",
    "candidate": "cand",
    "relation": "rel",
}

JSON_FIELDS = {"kp_ids", "related_kp_ids", "options_json", "source_evidence_json"}

EDITABLE_FIELDS = {
    "kp": {
        "knowledge_item", "graph_label", "source_location", "knowledge_type",
        "related_kp_ids", "importance", "learning_action", "body", "difficulty",
        "fragile",
    },
    "problem": {
        "kp_ids", "problem_text", "solution", "problem_type", "source_kind",
        "display_title", "topic_label", "display_summary", "figure_paths",
    },
    "candidate": {"display_title", "topic_label", "display_summary"},
    "relation": {
        "source_kp_id", "target_kp_id", "relation_type", "direction", "strength",
    },
}


def _entity(entity):
    try:
        return TABLES[entity]
    except KeyError as exc:
        raise ValueError(f"unknown entity: {entity}") from exc


def _row(row):
    if row is None:
        return None
    item = dict(row)
    for field in JSON_FIELDS & item.keys():
        value = item[field]
        if isinstance(value, str) and value:
            item[field] = json.loads(value)
    return item


def get(pool, entity, object_id):
    table, id_column = _entity(entity)
    row = pool.connect().execute(
        f"SELECT * FROM {table} WHERE {id_column}=?", (object_id,)
    ).fetchone()
    return _row(row)


def list_items(pool, entity):
    table, id_column = _entity(entity)
    rows = pool.connect().execute(
        f"SELECT * FROM {table} ORDER BY {id_column}"
    ).fetchall()
    return [_row(row) for row in rows]


def search(pool, entity, query):
    needle = query.casefold()
    return [
        item for item in list_items(pool, entity)
        if needle in json.dumps(item, ensure_ascii=False).casefold()
    ]


def history(pool, entity, object_id):
    conn = pool.connect()
    if entity == "problem":
        return {
            "attempts": _rows(conn, "problem_attempts", "problem_id", object_id, "id"),
            "feedback": _item_rows(conn, "feedback_events", "problem", object_id, "id"),
            "schedule": _item_rows(conn, "review_schedule", "problem", object_id, "direction"),
            "state": _item_rows(conn, "learning_current_state", "problem", object_id, "updated_at"),
            "progress": _rows(conn, "problem_progress", "problem_id", object_id, "problem_id"),
            "signals": _rows(conn, "learner_signals", "target_id", object_id, "signal_id"),
        }
    if entity == "kp":
        return {
            "feedback": _item_rows(conn, "feedback_events", "kp", object_id, "id"),
            "schedule": _item_rows(conn, "review_schedule", "kp", object_id, "direction"),
            "state": _item_rows(conn, "learning_current_state", "kp", object_id, "updated_at"),
            "signals": _rows(conn, "learner_signals", "target_id", object_id, "signal_id"),
        }
    if entity == "candidate":
        return {
            "attempts": _rows(conn, "candidate_attempts", "candidate_id", object_id, "id")
        }
    if entity == "relation":
        return {
            "signals": _rows(conn, "learner_signals", "target_id", object_id, "signal_id")
        }
    _entity(entity)


def _rows(conn, table, column, value, order):
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE {column}=? ORDER BY {order}", (value,)
    ).fetchall()
    return [dict(row) for row in rows]


def _item_rows(conn, table, item_type, item_id, order):
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE item_type=? AND item_id=? ORDER BY {order}",
        (item_type, item_id),
    ).fetchall()
    return [dict(row) for row in rows]


def next_id(pool, entity):
    table, id_column = _entity(entity)
    scope = f"{pool.course}-{pool.chapter}"
    prefix = f"{scope}-{PREFIXES[entity]}-"
    conn = pool.connect()
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT next_value FROM content_sequences "
            "WHERE scope=? AND entity_type=?",
            (scope, entity),
        ).fetchone()
        if row is None:
            existing = conn.execute(
                f"SELECT {id_column} FROM {table} WHERE {id_column} LIKE ?",
                (prefix + "%",),
            ).fetchall()
            numbers = [
                int(value[0][len(prefix):])
                for value in existing
                if value[0][len(prefix):].isdigit()
            ]
            value = max(numbers, default=0) + 1
            conn.execute(
                "INSERT INTO content_sequences (scope, entity_type, next_value) "
                "VALUES (?, ?, ?)",
                (scope, entity, value + 1),
            )
        else:
            value = row[0]
            conn.execute(
                "UPDATE content_sequences SET next_value=? "
                "WHERE scope=? AND entity_type=?",
                (value + 1, scope, entity),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return f"{prefix}{value:03d}"


def create(pool, entity, data):
    if entity == "problem":
        raise ValueError("formal problems can only be created by candidate promotion")
    if entity == "candidate":
        raise ValueError("candidate creation must use the candidate pipeline")
    table, id_column = _entity(entity)
    object_id = next_id(pool, entity)
    fields = [field for field in EDITABLE_FIELDS[entity] if field in data]
    values = [_db_value(field, data[field]) for field in fields]
    conn = pool.connect()
    with conn:
        conn.execute(
            f"INSERT INTO {table} ({id_column}, {', '.join(fields)}) "
            f"VALUES ({', '.join('?' for _ in range(len(fields) + 1))})",
            (object_id, *values),
        )
    return get(pool, entity, object_id)


def update(pool, entity, object_id, data):
    table, id_column = _entity(entity)
    fields = [field for field in EDITABLE_FIELDS[entity] if field in data]
    if not fields:
        return get(pool, entity, object_id)
    assignments = [f"{field}=?" for field in fields]
    columns = {row[1] for row in pool.connect().execute(f"PRAGMA table_info({table})")}
    if "updated_at" in columns:
        assignments.append("updated_at=datetime('now')")
    values = [_db_value(field, data[field]) for field in fields]
    conn = pool.connect()
    with conn:
        cursor = conn.execute(
            f"UPDATE {table} SET {', '.join(assignments)} WHERE {id_column}=?",
            (*values, object_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(object_id)
    return get(pool, entity, object_id)


def _db_value(field, value):
    if field in JSON_FIELDS and not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return value


def delete(pool, entity, object_id):
    _entity(entity)
    conn = pool.connect()
    with conn:
        if entity == "problem":
            _delete_problem(conn, object_id)
        elif entity == "candidate":
            _delete_candidate(conn, object_id)
        elif entity == "kp":
            _delete_kp(conn, object_id)
        else:
            conn.execute(
                "DELETE FROM knowledge_relations WHERE relation_id=?", (object_id,)
            )


def _delete_problem(conn, problem_id):
    conn.execute(
        "UPDATE candidate_problems SET imported_problem_id=NULL, "
        "status=CASE WHEN status='imported' THEN 'needs_revision' ELSE status END, "
        "structure_gate_status=CASE WHEN status='imported' THEN 'pending' ELSE structure_gate_status END, "
        "audit_gate_status=CASE WHEN status='imported' THEN 'pending' ELSE audit_gate_status END, "
        "gate_report=CASE WHEN status='imported' THEN NULL ELSE gate_report END "
        "WHERE imported_problem_id=?",
        (problem_id,),
    )
    conn.execute("DELETE FROM problem_progress WHERE problem_id=?", (problem_id,))
    conn.execute("DELETE FROM problem_attempts WHERE problem_id=?", (problem_id,))
    _delete_learning_rows(conn, "problem", problem_id)
    conn.execute("DELETE FROM learner_signals WHERE target_id=?", (problem_id,))
    conn.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))


def _delete_candidate(conn, candidate_id):
    conn.execute("DELETE FROM candidate_attempts WHERE candidate_id=?", (candidate_id,))
    conn.execute("DELETE FROM candidate_problems WHERE candidate_id=?", (candidate_id,))


def _delete_learning_rows(conn, item_type, item_id):
    for table in ("feedback_events", "review_schedule", "learning_current_state"):
        conn.execute(
            f"DELETE FROM {table} WHERE item_type=? AND item_id=?",
            (item_type, item_id),
        )


def _delete_kp(conn, kp_id):
    relation_ids = [
        row[0] for row in conn.execute(
            "SELECT relation_id FROM knowledge_relations "
            "WHERE source_kp_id=? OR target_kp_id=?",
            (kp_id, kp_id),
        )
    ]
    for relation_id in relation_ids:
        conn.execute("DELETE FROM learner_signals WHERE target_id=?", (relation_id,))
    conn.execute(
        "DELETE FROM knowledge_relations WHERE source_kp_id=? OR target_kp_id=?",
        (kp_id, kp_id),
    )

    for table, id_column in (("problems", "problem_id"), ("candidate_problems", "candidate_id")):
        rows = conn.execute(f"SELECT {id_column}, kp_ids FROM {table}").fetchall()
        for row in rows:
            kp_ids = json.loads(row[1] or "[]")
            if kp_id not in kp_ids:
                continue
            remaining = [item for item in kp_ids if item != kp_id]
            if remaining:
                conn.execute(
                    f"UPDATE {table} SET kp_ids=? WHERE {id_column}=?",
                    (json.dumps(remaining, ensure_ascii=False), row[0]),
                )
            elif table == "problems":
                _delete_problem(conn, row[0])
            else:
                _delete_candidate(conn, row[0])

    rows = conn.execute(
        "SELECT kp_id, related_kp_ids FROM knowledge_points "
        "WHERE related_kp_ids IS NOT NULL"
    ).fetchall()
    for row in rows:
        related = json.loads(row[1] or "[]")
        if kp_id in related:
            conn.execute(
                "UPDATE knowledge_points SET related_kp_ids=? WHERE kp_id=?",
                (json.dumps([item for item in related if item != kp_id], ensure_ascii=False), row[0]),
            )

    _delete_learning_rows(conn, "kp", kp_id)
    conn.execute("DELETE FROM learner_signals WHERE target_id=?", (kp_id,))
    conn.execute("DELETE FROM knowledge_points WHERE kp_id=?", (kp_id,))
