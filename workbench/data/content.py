"""Transactional access to Agent-managed current content."""

import json
import re

from workbench.domain import micro_quiz


TABLES = {
    "kp": ("knowledge_points", "kp_id"),
    "problem": ("problems", "problem_id"),
    "relation": ("knowledge_relations", "relation_id"),
}

PREFIXES = {
    "kp": "kp",
    "problem": "prob",
    "relation": "rel",
}

JSON_FIELDS = {"kp_ids", "related_kp_ids", "options_json", "source_evidence_json",
               "practice_modes", "micro_quiz"}
SOURCE_KINDS = {"textbook", "quiz", "midterm", "final", "makeup", "other"}
ORIGIN_KINDS = {"source_problem", "adapted_problem", "generated_grounded"}
EXAM_YEAR_LIMIT = 20
EXAM_YEAR = re.compile(r"\d{4}")

EDITABLE_FIELDS = {
    "kp": {
        "knowledge_item", "graph_label", "source_location", "knowledge_type",
        "related_kp_ids", "importance", "learning_action", "body", "difficulty",
        "fragile",
    },
    "problem": {
        "kp_ids", "problem_text", "solution", "problem_type", "source_kind",
        "origin_kind", "display_title", "topic_label", "display_summary",
        "figure_paths", "exam_year",
    },
    "relation": {
        "source_kp_id", "target_kp_id", "relation_type", "direction", "strength",
    },
}


def exam_year_error(value):
    """None when an exam year is acceptable; otherwise the reason.

    The field is optional, so empty means "unknown year". A present value starts
    with its four-digit study year (`2023`, `2023-2024秋冬`) — that prefix is
    what the pull filter matches — and stays short enough to read in a table.
    """
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return "exam_year must be a string"
    text = value.strip()
    if not text or not EXAM_YEAR.match(text) or len(text) > EXAM_YEAR_LIMIT:
        return ("exam_year must start with a four-digit year "
                f"(e.g. 2023 or 2023-2024秋冬) and be at most {EXAM_YEAR_LIMIT} characters")
    return None


def normalize_exam_year(value):
    """The stored form of an exam year; raises with the reason when invalid."""
    reason = exam_year_error(value)
    if reason:
        raise ValueError(reason)
    return value.strip() if isinstance(value, str) and value.strip() else None


def exam_year_column_error(pool):
    """None when this pool can hold or filter exam years; else the migrate hint."""
    columns = {str(row[1]) for row in pool.connect().execute("PRAGMA table_info(problems)")}
    if "exam_year" in columns:
        return None
    try:
        db = pool.db_path.relative_to(pool.root).as_posix()
    except ValueError:
        db = pool.db_path
    return (
        "this pool has no exam_year column yet — run: "
        f"python pool/scripts/migrate-progress.py --db {db}"
    )



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
    scope = pool.scope_prefix()
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
    table, id_column = _entity(entity)
    if entity == "problem":
        if data.get("source_kind") not in SOURCE_KINDS:
            raise ValueError("source_kind is required and must be valid")
        if data.get("origin_kind") not in ORIGIN_KINDS:
            raise ValueError("origin_kind is required and must be valid")
        reason = exam_year_error(data.get("exam_year"))
        if reason:
            raise ValueError(reason)
        if "exam_year" in data:
            data = {**data, "exam_year": normalize_exam_year(data["exam_year"])}
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
    if entity == "problem" and "exam_year" in data:
        reason = exam_year_error(data["exam_year"])
        if reason:
            raise ValueError(reason)
        data = {**data, "exam_year": normalize_exam_year(data["exam_year"])}
    special = {}
    if entity == "problem" and "answer_key" in data:
        special["micro_quiz"] = _patched_micro_quiz(pool, object_id, data["answer_key"])
    fields = [field for field in EDITABLE_FIELDS[entity] if field in data]
    if not fields and not special:
        return get(pool, entity, object_id)
    assignments = [f"{field}=?" for field in fields]
    values = [_db_value(field, data[field]) for field in fields]
    columns = {row[1] for row in pool.connect().execute(f"PRAGMA table_info({table})")}
    if entity == "problem" and {"kp_ids", "problem_text", "solution", "problem_type"} & set(fields):
        assignments.extend(
            f"{field}=NULL" for field in (
                "difficulty", "difficulty_knowledge_breadth",
                "difficulty_reasoning_depth", "difficulty_transfer_distance",
                "difficulty_construction_openness", "difficulty_model",
            ) if field in columns
        )
    if "updated_at" in columns:
        assignments.append("updated_at=datetime('now')")
    assignments.extend(f"{field}=?" for field in special)
    values.extend(special.values())
    conn = pool.connect()
    with conn:
        cursor = conn.execute(
            f"UPDATE {table} SET {', '.join(assignments)} WHERE {id_column}=?",
            (*values, object_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(object_id)
    return get(pool, entity, object_id)


def _patched_micro_quiz(pool, problem_id, answer_key):
    """Fold a supplied answer key into the item's own micro-quiz payload.

    Only the key's shape is checked, against that item's quiz type, so filling a
    key in later never forces an error reason the learner may not have. An empty
    value clears the key and the item is practised ungraded again.
    """
    row = pool.connect().execute(
        "SELECT micro_quiz FROM problems WHERE problem_id=?", (problem_id,)
    ).fetchone()
    if row is None:
        raise KeyError(problem_id)
    raw = row[0]
    payload = None
    if isinstance(raw, str) and raw.strip():
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = None
    if not isinstance(payload, dict) or not payload.get("quiz_type"):
        raise ValueError(
            f"{problem_id} is not a 判断/小测 item: an answer key belongs to an "
            "objective item imported with quiz_type/options"
        )
    cleared = answer_key in (None, "")
    candidate = {**payload, "answer_key": None if cleared else answer_key}
    if not cleared:
        errors = micro_quiz.validate_answer_key(
            payload["quiz_type"], payload.get("options"), answer_key)
        if errors:
            raise ValueError("; ".join(errors))
    return json.dumps(candidate, ensure_ascii=False)


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
        elif entity == "kp":
            _delete_kp(conn, object_id)
        else:
            conn.execute(
                "DELETE FROM knowledge_relations WHERE relation_id=?", (object_id,)
            )


def _delete_problem(conn, problem_id):
    conn.execute("DELETE FROM problem_progress WHERE problem_id=?", (problem_id,))
    conn.execute("DELETE FROM problem_attempts WHERE problem_id=?", (problem_id,))
    _delete_learning_rows(conn, "problem", problem_id)
    conn.execute("DELETE FROM learner_signals WHERE target_id=?", (problem_id,))
    conn.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))

def _delete_learning_rows(conn, item_type, item_id):
    for table in ("feedback_events", "review_schedule", "learning_current_state"):
        conn.execute(
            f"DELETE FROM {table} WHERE item_type=? AND item_id=?",
            (item_type, item_id),
        )


def _delete_kp(conn, kp_id):
    card_ids = [
        row[0] for row in conn.execute(
            "SELECT card_id FROM flash_cards WHERE kp_id=?", (kp_id,)
        )
    ]
    for card_id in card_ids:
        _delete_learning_rows(conn, "card", card_id)
        conn.execute("DELETE FROM learner_signals WHERE target_id=?", (card_id,))
    conn.execute("DELETE FROM flash_cards WHERE kp_id=?", (kp_id,))

    question_ids = [
        row[0] for row in conn.execute(
            "SELECT q_id FROM questions WHERE kp_id=?", (kp_id,)
        )
    ]
    for question_id in question_ids:
        conn.execute("DELETE FROM question_progress WHERE q_id=?", (question_id,))
    conn.execute("DELETE FROM questions WHERE kp_id=?", (kp_id,))
    conn.execute("DELETE FROM kp_progress WHERE kp_id=?", (kp_id,))

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

    rows = conn.execute("SELECT problem_id, kp_ids FROM problems").fetchall()
    for row in rows:
        kp_ids = json.loads(row[1] or "[]")
        if kp_id not in kp_ids:
            continue
        remaining = [item for item in kp_ids if item != kp_id]
        if remaining:
            conn.execute(
                "UPDATE problems SET kp_ids=?, difficulty=NULL, "
                "difficulty_knowledge_breadth=NULL, difficulty_reasoning_depth=NULL, "
                "difficulty_transfer_distance=NULL, "
                "difficulty_construction_openness=NULL, difficulty_model=NULL "
                "WHERE problem_id=?",
                (json.dumps(remaining, ensure_ascii=False), row[0]),
            )
        else:
            _delete_problem(conn, row[0])

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
