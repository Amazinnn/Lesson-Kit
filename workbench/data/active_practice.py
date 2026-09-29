"""One workspace-local active practice plus a tiny durable run archive.

The active singleton remains execution state. Completed or replaced runs are
snapshotted for the records page; attempts and feedback remain the learning
evidence.
"""

import json


SOURCE_KINDS = {"quick", "practice_set", "agent"}
ITEM_TYPES = {"problem", "card"}
ITEM_STATES = {"pending", "answered", "stuck"}
MIGRATION_COMMAND = "python pool/scripts/migrate-progress.py --db {}"


class ActivePracticeError(ValueError):
    pass


class ActivePracticeConflict(ActivePracticeError):
    pass


def _require_schema(pool):
    names = {
        row[0] for row in pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if {"active_practice", "active_practice_items", "practice_runs"} <= names:
        return
    try:
        db = pool.db_path.relative_to(pool.root).as_posix()
    except ValueError:
        db = str(pool.db_path)
    raise ActivePracticeError(
        "this pool is not migrated for resumable practice — run: "
        + MIGRATION_COMMAND.format(db)
    )


def _json_list(value, name):
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ActivePracticeError(f"{name} must be a string list")
    return list(dict.fromkeys(value))


def _normalize(pool, payload):
    if not isinstance(payload, dict):
        raise ActivePracticeError("active practice must be a JSON object")
    source_kind = payload.get("source_kind", "quick")
    if source_kind not in SOURCE_KINDS:
        raise ActivePracticeError("source_kind must be quick, practice_set, or agent")
    source_ref = payload.get("source_ref")
    if source_ref is not None and (
        not isinstance(source_ref, str) or not source_ref.strip()
    ):
        raise ActivePracticeError("source_ref must be a non-empty string or null")
    source_label = payload.get("source_label")
    if source_label is not None and (
        not isinstance(source_label, str) or not source_label.strip()
    ):
        raise ActivePracticeError("source_label must be a non-empty string or null")
    if source_label is None:
        source_label = (
            f"试卷 {source_ref.strip()}" if source_kind == "practice_set" and source_ref
            else "Agent 练习" if source_kind == "agent"
            else "临时练习"
        )
    practice_mode = payload.get("practice_mode")
    rating_mode = payload.get("rating_mode")
    if not isinstance(practice_mode, str) or not practice_mode:
        raise ActivePracticeError("practice_mode is required")
    if not isinstance(rating_mode, str) or not rating_mode:
        raise ActivePracticeError("rating_mode is required")
    kp_ids = _json_list(payload.get("kp_ids"), "kp_ids")
    unknown_kps = [kp_id for kp_id in kp_ids if pool.kp(kp_id) is None]
    if unknown_kps:
        raise ActivePracticeError(f"unknown knowledge point: {unknown_kps[0]}")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ActivePracticeError("items must be a non-empty list")
    items = []
    seen = set()
    for position, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise ActivePracticeError(f"item {position} must be an object")
        item_type = raw.get("item_type", "problem")
        item_id = raw.get("item_id")
        direction = raw.get("direction") or ""
        if item_type not in ITEM_TYPES:
            raise ActivePracticeError(f"item {position}: invalid item_type")
        if not isinstance(item_id, str) or not item_id:
            raise ActivePracticeError(f"item {position}: item_id is required")
        if not isinstance(direction, str):
            raise ActivePracticeError(f"item {position}: direction must be a string")
        key = (item_type, item_id, direction)
        if key in seen:
            raise ActivePracticeError(f"item {position}: duplicate item {item_id}")
        seen.add(key)
        if item_type == "problem":
            if pool.problem(item_id) is None:
                raise ActivePracticeError(f"item {position}: unknown problem {item_id}")
            direction = ""
        else:
            card = pool.card(item_id)
            if card is None:
                raise ActivePracticeError(f"item {position}: unknown card {item_id}")
            if direction and direction not in card.get("directions", []):
                raise ActivePracticeError(
                    f"item {position}: direction is not available for card {item_id}"
                )
        items.append({
            "position": position,
            "item_type": item_type,
            "item_id": item_id,
            "direction": direction,
        })
    return {
        "source_kind": source_kind,
        "source_ref": source_ref.strip() if isinstance(source_ref, str) else None,
        "source_label": source_label.strip(),
        "kp_ids": kp_ids,
        "practice_mode": practice_mode,
        "rating_mode": rating_mode,
        "items": items,
    }


def _row(pool):
    return pool.connect().execute(
        "SELECT * FROM active_practice WHERE singleton=1"
    ).fetchone()


def current(pool, *, resolve=True):
    _require_schema(pool)
    row = _row(pool)
    if row is None:
        return None
    record = dict(row)
    record["kp_ids"] = json.loads(record.pop("kp_ids_json") or "[]")
    rows = pool.connect().execute(
        "SELECT * FROM active_practice_items ORDER BY position"
    ).fetchall()
    items = []
    answered = stuck = 0
    for raw in rows:
        item = dict(raw)
        if item["state"] == "answered":
            answered += 1
        elif item["state"] == "stuck":
            stuck += 1
        if resolve:
            payload = (
                pool.problem(item["item_id"])
                if item["item_type"] == "problem"
                else pool.card(item["item_id"])
            )
            item["payload"] = payload
            if item["item_type"] == "problem" and item.get("attempt_id"):
                attempt = pool.attempt(item["attempt_id"])
                if attempt is not None:
                    attempt = dict(attempt)
                    choices = attempt.get("choices")
                    if isinstance(choices, str) and choices:
                        try:
                            attempt["choices"] = json.loads(choices)
                        except json.JSONDecodeError:
                            attempt["choices"] = []
                    item["attempt"] = attempt
                    event = pool.feedback_event_for_attempt(item["attempt_id"])
                    if event is not None:
                        item["feedback"] = event
        items.append(item)
    record["items"] = items
    record["progress"] = {
        "completed": answered + stuck,
        "answered": answered,
        "stuck": stuck,
        "remaining": len(items) - answered - stuck,
        "total": len(items),
    }
    return record


def create(pool, payload, *, replace=False):
    _require_schema(pool)
    normalized = _normalize(pool, payload)
    with pool.transaction(immediate=True):
        if _row(pool) is not None:
            if not replace:
                raise ActivePracticeConflict("an unfinished practice already exists")
            _archive(pool, current(pool, resolve=False), "abandoned")
            _delete(pool)
        pool.connect().execute(
            "INSERT INTO active_practice "
            "(singleton, source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            " rating_mode, cursor) VALUES (1, ?, ?, ?, ?, ?, ?, 0)",
            (
                normalized["source_kind"],
                normalized["source_ref"],
                normalized["source_label"],
                json.dumps(normalized["kp_ids"], ensure_ascii=False),
                normalized["practice_mode"],
                normalized["rating_mode"],
            ),
        )
        pool.connect().executemany(
            "INSERT INTO active_practice_items "
            "(position, item_type, item_id, direction, state) "
            "VALUES (?, ?, ?, ?, 'pending')",
            [
                (item["position"], item["item_type"], item["item_id"], item["direction"])
                for item in normalized["items"]
            ],
        )
    return current(pool)


def _archive(pool, record, status):
    items = [
        {
            "position": item["position"],
            "item_type": item["item_type"],
            "item_id": item["item_id"],
            "direction": item.get("direction") or "",
            "state": item["state"],
            "attempt_id": item.get("attempt_id"),
        }
        for item in record["items"]
    ]
    pool.connect().execute(
        "INSERT INTO practice_runs "
        "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
        " rating_mode, items_json, status, started_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            record["source_kind"],
            record.get("source_ref"),
            record.get("source_label"),
            json.dumps(record["kp_ids"], ensure_ascii=False),
            record["practice_mode"],
            record["rating_mode"],
            json.dumps(items, ensure_ascii=False),
            status,
            record["started_at"],
        ),
    )


def _delete(pool):
    pool.connect().execute("DELETE FROM active_practice_items")
    pool.connect().execute("DELETE FROM active_practice WHERE singleton=1")


def clear(pool):
    _require_schema(pool)
    before = current(pool)
    if before is None:
        return {"cleared": False, "practice": None}
    with pool.transaction(immediate=True):
        _archive(pool, before, "abandoned")
        _delete(pool)
    return {"cleared": True, "practice": before}


def mark(pool, position, state, *, attempt_id=None):
    _require_schema(pool)
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ActivePracticeError("position must be a non-negative integer")
    if state not in {"answered", "stuck"}:
        raise ActivePracticeError("state must be answered or stuck")
    if attempt_id is not None and (
        isinstance(attempt_id, bool) or not isinstance(attempt_id, int)
    ):
        raise ActivePracticeError("attempt_id must be an integer or null")

    with pool.transaction(immediate=True):
        if _row(pool) is None:
            raise ActivePracticeError("no unfinished practice")
        item = pool.connect().execute(
            "SELECT * FROM active_practice_items WHERE position=?", (position,)
        ).fetchone()
        if item is None:
            raise ActivePracticeError(f"unknown practice position: {position}")
        if item["state"] != "pending":
            if item["state"] == state and item["attempt_id"] == attempt_id:
                return {"completed": False, "replay": True, "practice": current(pool)}
            raise ActivePracticeConflict(
                f"practice position {position} is already {item['state']}"
            )
        if attempt_id is not None:
            attempt = pool.attempt(attempt_id)
            if attempt is None:
                raise ActivePracticeError(f"unknown attempt: {attempt_id}")
            if item["item_type"] != "problem" or attempt["problem_id"] != item["item_id"]:
                raise ActivePracticeError("attempt_id does not belong to this practice item")

        pool.connect().execute(
            "UPDATE active_practice_items SET state=?, attempt_id=? WHERE position=?",
            (state, attempt_id, position),
        )
        pending = pool.connect().execute(
            "SELECT position FROM active_practice_items "
            "WHERE state='pending' ORDER BY position"
        ).fetchall()
        if not pending:
            finished = current(pool)
            _archive(pool, finished, "completed")
            _delete(pool)
            return {"completed": True, "replay": False, "practice": finished}

        next_position = next(
            (row["position"] for row in pending if row["position"] > position),
            pending[0]["position"],
        )
        pool.connect().execute(
            "UPDATE active_practice SET cursor=?, updated_at=datetime('now') "
            "WHERE singleton=1",
            (next_position,),
        )
    return {"completed": False, "replay": False, "practice": current(pool)}
