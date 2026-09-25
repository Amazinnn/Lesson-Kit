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
        "figure_paths", "exam_year", "source_evidence", "source_answer",
        "solution_origin", "practice_modes", "micro_quiz",
    },
    "relation": {
        "source_kp_id", "target_kp_id", "relation_type", "direction", "strength",
    },
}

# The four content axes: changing one clears the whole difficulty rating group.
CONTENT_AXES = {"kp_ids", "problem_text", "solution", "problem_type"}
DIFFICULTY_COLUMNS = (
    "difficulty", "difficulty_knowledge_breadth", "difficulty_reasoning_depth",
    "difficulty_transfer_distance", "difficulty_construction_openness",
    "difficulty_model",
)
# What an in-place problem patch may carry; `answer_key` is the shape-only sugar
# for the item's own payload (see `plan_problem_patch`).
PROBLEM_PATCH_FIELDS = frozenset(EDITABLE_FIELDS["problem"]) | {"answer_key"}


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
    if entity == "problem":
        return _update_problem(pool, object_id, data)
    fields = [field for field in EDITABLE_FIELDS[entity] if field in data]
    if not fields:
        return get(pool, entity, object_id)
    assignments = [f"{field}=?" for field in fields]
    values = [_db_value(field, data[field]) for field in fields]
    columns = {row[1] for row in pool.connect().execute(f"PRAGMA table_info({table})")}
    if "updated_at" in columns:
        assignments.append("updated_at=datetime('now')")
    conn = pool.connect()
    with conn:
        cursor = conn.execute(
            f"UPDATE {table} SET {', '.join(assignments)} WHERE {id_column}=?",
            (*values, object_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(object_id)
    return get(pool, entity, object_id)


def _update_problem(pool, problem_id, data):
    """Apply one in-place problem patch through the shared plan."""
    plan = plan_problem_update(pool, problem_id, data)
    if plan["errors"]:
        raise ValueError("; ".join(plan["errors"]))
    fields = plan["fields"]
    if not fields:
        return get(pool, "problem", problem_id)
    columns = {row[1] for row in pool.connect().execute("PRAGMA table_info(problems)")}
    assignments = [f"{field}=?" for field in fields]
    values = [_db_value(field, value) for field, value in fields.items()]
    if plan["clear_difficulty"]:
        assignments.extend(
            f"{field}=NULL" for field in DIFFICULTY_COLUMNS if field in columns)
    if "updated_at" in columns:
        assignments.append("updated_at=datetime('now')")
    conn = pool.connect()
    with conn:
        cursor = conn.execute(
            f"UPDATE problems SET {', '.join(assignments)} WHERE problem_id=?",
            (*values, problem_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(problem_id)
    return get(pool, "problem", problem_id)


def plan_problem_update(pool, problem_id, data):
    """Plan one in-place patch for a problem that must already exist here."""
    row = pool.problem(problem_id)
    if row is None:
        return {"errors": [f"unknown problem: {problem_id}"], "fields": {},
                "clear_difficulty": False, "row": None}
    return plan_problem_patch(row, data, course=pool.course)


def decode_problem(row):
    """Decode one `problems` row into the shape a patch plan expects."""
    item = dict(row)
    item["kp_ids"] = json.loads(item.get("kp_ids") or "[]")
    for field in ("practice_modes", "micro_quiz"):
        raw = item.get(field)
        if isinstance(raw, str):
            item[field] = json.loads(raw) if raw else None
    return item


def plan_problem_patch(row, data, course=""):
    """Validate one in-place problem patch and return what to write.

    One authority for both entry points — `data update problem` and the bulk
    `problem-patch` gate — so a converted row can never be one the ingestion
    contract would refuse. `row` is the decoded current row (`kp_ids`,
    `practice_modes`, and `micro_quiz` already parsed).

    - an unknown field is an error, never a silent drop;
    - the id must belong to this workspace's course and never changes;
    - difficulty stays a separate command;
    - `practice_modes` follows the payload unless it is declared (`[]`/null is
      exam-only), and a micro/yes-no marking without a payload is refused;
    - the resulting row is checked against the micro-quiz contract for the parts
      this patch touches (payload shape, one knowledge point, stem bound, mode
      marking). Fields the patch does not touch are left as they are, so legacy
      rows stay patchable without re-validating their old content.

    Returns ``{"errors", "fields", "clear_difficulty", "row"}``; `fields` is
    empty when nothing would change.
    """
    if not isinstance(data, dict):
        return {"errors": ["a problem patch must be a JSON object"], "fields": {},
                "clear_difficulty": False, "row": row}
    errors = []
    if "problem_id" in data:
        errors.append("a patch cannot change problem_id — it is the row's identity")
    unsupported = sorted(set(data) - PROBLEM_PATCH_FIELDS - {"problem_id"})
    if unsupported:
        difficulty = [name for name in unsupported
                      if name.startswith("difficulty")]
        if difficulty:
            errors.append(
                "difficulty is rated separately with `lesson-kit difficulty`")
        rest = [name for name in unsupported if not name.startswith("difficulty")]
        if rest:
            errors.append(
                f"unsupported field(s) {rest} — writable fields: "
                + ", ".join(sorted(PROBLEM_PATCH_FIELDS)))
    problem_id = (row or {}).get("problem_id", "")
    if course and isinstance(problem_id, str) and problem_id \
            and not problem_id.startswith(f"{course}-"):
        errors.append(
            f"{problem_id}: id must start with {course}- (this workspace's course)")
    if errors:
        return {"errors": errors, "fields": {}, "clear_difficulty": False,
                "row": row}

    fields = {name: data[name] for name in data
              if name in PROBLEM_PATCH_FIELDS and name != "answer_key"}
    # A whole-payload write gets the full contract; the `answer_key` sugar only
    # checks the key's shape, so an existing row keeps its other payload fields.
    explicit_payload = "micro_quiz" in data
    if "exam_year" in fields:
        reason = exam_year_error(fields["exam_year"])
        if reason:
            errors.append(reason)
        else:
            fields["exam_year"] = normalize_exam_year(fields["exam_year"])

    if "answer_key" in data:
        errors.extend(_answer_key_errors(row, fields, data["answer_key"]))

    if "micro_quiz" in fields:
        payload = fields["micro_quiz"]
        if payload is None:
            # Clearing the payload puts the item back in 综合题; the mode follows
            # unless the caller declares one.
            fields.pop("practice_modes", None)
            fields["practice_modes"] = None
            fields["micro_quiz"] = None
        elif not isinstance(payload, dict) or not payload.get("quiz_type"):
            errors.append(
                "micro_quiz needs quiz_type (yes_no / single_choice / "
                "multiple_choice), or null to clear it back to 综合题")
        else:
            carried = fields.get("source_evidence") or row.get("source_evidence")
            if not str(payload.get("source_evidence") or "").strip() \
                    and str(carried or "").strip():
                # The row already carries its provenance (or this patch supplies
                # it); a payload write need not repeat it.
                payload = {**payload, "source_evidence": carried}
                fields["micro_quiz"] = payload
            if "practice_modes" not in fields:
                fields["practice_modes"] = micro_quiz.practice_modes_for(
                    payload["quiz_type"])
    elif "practice_modes" in fields:
        declared = fields["practice_modes"]
        modes = [] if declared is None else (
            declared if isinstance(declared, list) else [declared])
        existing = row.get("micro_quiz")
        outside = sorted({mode for mode in modes if mode != "exam"})
        if outside and not (isinstance(existing, dict) and existing.get("quiz_type")):
            errors.append(
                f"practice_modes {outside} need a micro_quiz payload — send "
                "quiz_type and options to make this a 判断/小测 item, or leave "
                "practice_modes unset for 综合题")
        fields["practice_modes"] = [mode for mode in modes if mode != "exam"] or None

    if errors:
        return {"errors": errors, "fields": {}, "clear_difficulty": False,
                "row": row}

    prospective = {**row, **fields}
    payload = prospective.get("micro_quiz")
    if isinstance(payload, dict) and payload.get("quiz_type"):
        if explicit_payload:
            errors.extend(micro_quiz.validate_payload(payload["quiz_type"], payload))
        if explicit_payload or "kp_ids" in fields:
            kp_ids = prospective.get("kp_ids")
            if not isinstance(kp_ids, list) or len(kp_ids) != 1:
                errors.append("a micro quiz maps to exactly one knowledge point")
        if "problem_text" in fields:
            stem = prospective.get("problem_text")
            if not isinstance(stem, str) or not stem.strip():
                errors.append("problem_text is required")
            elif len(stem) > micro_quiz.MAX_STEM_CHARS:
                errors.append(
                    f"problem_text exceeds {micro_quiz.MAX_STEM_CHARS} characters; "
                    "long content belongs to the exam mode")
        modes = prospective.get("practice_modes")
        if not isinstance(modes, list) or not modes:
            errors.append("practice_modes marking is required for a micro quiz")
        else:
            allowed = micro_quiz.practice_modes_for(payload["quiz_type"])
            if not set(modes) <= set(allowed):
                errors.append(
                    f"practice_modes for {payload['quiz_type']} must be within "
                    f"{sorted(allowed)}")
    return {
        "errors": errors,
        "fields": {} if errors else fields,
        "clear_difficulty": bool(CONTENT_AXES & set(fields)),
        "row": row,
    }


def _answer_key_errors(row, fields, answer_key):
    """Fold an `answer_key` patch into the item's payload; only its shape is checked.

    Filling a key in later must not force an error reason the learner may not
    have, so this is the shape-only rule while a whole-payload write gets the
    full contract.
    """
    payload = fields.get("micro_quiz", row.get("micro_quiz"))
    if not isinstance(payload, dict) or not payload.get("quiz_type"):
        return [
            "answer_key needs a 判断/小测 item: set micro_quiz (quiz_type and "
            "options) first, or send the whole micro_quiz payload"
        ]
    cleared = answer_key in (None, "")
    if cleared:
        fields["micro_quiz"] = {**payload, "answer_key": None}
        return []
    errors = micro_quiz.validate_answer_key(
        payload["quiz_type"], payload.get("options"), answer_key)
    if not errors:
        fields["micro_quiz"] = {**payload, "answer_key": answer_key}
    return errors


def _db_value(field, value):
    if value is None:
        return None
    if field in JSON_FIELDS and not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return value


def delete(pool, entity, object_id):
    _entity(entity)
    table, id_column = _entity(entity)
    conn = pool.connect()
    with conn:
        exists = conn.execute(
            f"SELECT 1 FROM {table} WHERE {id_column}=?", (object_id,)
        ).fetchone()
        if exists is None:
            raise KeyError(object_id)
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
