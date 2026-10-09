"""Agent-recorded practice attempts: manifests, atomic apply, guarded correction.

An attempt manifest is caller-supplied JSON. Every item is validated before any
row changes; one bad item leaves the whole pool untouched. Rated items reuse the
existing 1-5 feedback rules inside the same transaction, ungraded items stay
plain attempts, and an idempotent request id makes a retried CLI call return the
first result instead of recording twice.
"""

import hashlib
import json
from datetime import date

from workbench.data import active_practice
from workbench.domain import feedback as feedback_rules
from workbench.domain import learning_state
from workbench.domain import schedule as schedule_rules


UNGRADED_STATUS = "new"
ANSWERED_STATUS = "answered"
MANIFEST_FIELDS = {"request_id", "items"}
ITEM_FIELDS = {"problem_id", "answer_text", "note", "rating"}
CORRECTION_FIELDS = {"request_id", "answer_text", "note", "rating"}
MAX_REQUEST_ID = 200
MIGRATION_COMMAND = "python pool/scripts/migrate-progress.py --db {}"


class ManifestError(ValueError):
    """A rejected manifest; ``items`` carries one itemized reason per bad item."""

    def __init__(self, message, items=None):
        super().__init__(message)
        self.items = items or []


class RequestConflict(ValueError):
    """A browser retry id already belongs to a different write."""


# -- manifest reading ---------------------------------------------------------

def check(pool, manifest):
    """Validate a manifest and preview its effects without writing anything."""
    _require_schema(pool)
    request_id, raw_items = _manifest(manifest)
    items = _validate(pool, raw_items)
    batch = _batch_fingerprint("apply", items)
    stored = _operations(pool, request_id)
    if stored:
        _require_same_batch(request_id, stored, batch)
        return {
            "request_id": request_id, "valid": True, "writes": 0, "replay": True,
            "counts": _counts([json.loads(row["result"]) for row in stored]),
            "items": [json.loads(row["result"]) for row in stored],
        }
    previews = [_preview(pool, item) for item in items]
    return {
        "request_id": request_id, "valid": True, "writes": 0, "replay": False,
        "counts": _counts(previews), "items": previews,
    }


def _preview(pool, item):
    rating = item["rating"]
    problem_id = item["problem_id"]
    targets = _targets(pool, problem_id)
    projected = None
    if rating is not None:
        state = pool.schedule_get("problem", problem_id) or schedule_rules.default_state(
            "problem", problem_id
        )
        projected = schedule_rules.after_result(state, rating, date.today())["due_at"]
    return {
        "problem_id": problem_id,
        "rating": rating,
        "graded": rating is not None,
        "status": UNGRADED_STATUS if rating is None
        else feedback_rules.RATING_PROGRESS[rating],
        "answer_chars": len(item["answer_text"]),
        "note_chars": len(item["note"]),
        "signal_targets": targets,
        "projected_due_at": projected,
    }


def _manifest(manifest):
    if not isinstance(manifest, dict):
        raise ManifestError("manifest must be a JSON object")
    extra = sorted(set(manifest) - MANIFEST_FIELDS)
    if extra:
        raise ManifestError(
            f"manifest has unsupported field: {extra[0]} — a manifest carries only "
            "request_id and items"
        )
    request_id = _request_id(manifest.get("request_id"))
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ManifestError("manifest requires a non-empty items list")
    return request_id, items


def _request_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(
            "manifest requires a non-empty request_id string (a caller-stable "
            "idempotency key, e.g. conv-001-turn-004-record)"
        )
    if len(value) > MAX_REQUEST_ID:
        raise ManifestError(
            f"request_id must be at most {MAX_REQUEST_ID} characters"
        )
    return value


def _validate(pool, raw_items):
    """Normalize every item or report each bad one; reads only."""
    items = []
    errors = []
    seen = set()
    for index, raw in enumerate(raw_items):
        item, error = _normalize_item(pool, raw, seen)
        if error:
            errors.append({
                "index": index,
                "problem_id": raw.get("problem_id") if isinstance(raw, dict) else None,
                "error": error,
            })
            continue
        seen.add(item["problem_id"])
        item["index"] = index
        items.append(item)
    if errors:
        first = errors[0]
        raise ManifestError(
            f"item {first['index']}: {first['error']}", items=errors)
    return items


def _normalize_item(pool, raw, seen):
    if not isinstance(raw, dict):
        return None, "item must be a JSON object"
    extra = sorted(set(raw) - ITEM_FIELDS)
    if extra:
        return None, (
            f"unsupported field: {extra[0]} — an attempt item carries only "
            "problem_id, answer_text, note, and rating (no image, path, exam "
            "mark, or grader field)"
        )
    problem_id = raw.get("problem_id")
    if not isinstance(problem_id, str) or not problem_id.strip():
        return None, "problem_id is required"
    problem_id = problem_id.strip()
    if problem_id in seen:
        return None, f"duplicate problem in this manifest: {problem_id}"
    if pool.problem(problem_id) is None:
        return None, f"unknown problem: {problem_id}"
    answer_text, error = _text(raw, "answer_text")
    if error:
        return None, error
    note, error = _text(raw, "note")
    if error:
        return None, error
    if not answer_text.strip() and not note.strip():
        return None, "answer_text or note must be non-empty"
    rating = raw.get("rating")
    if rating is not None and (
        isinstance(rating, bool) or not isinstance(rating, int)
        or rating not in range(1, 6)
    ):
        return None, "rating must be an integer from 1 to 5"
    return {
        "problem_id": problem_id, "answer_text": answer_text,
        "note": note, "rating": rating,
    }, None


def _text(raw, field):
    value = raw.get(field)
    if value is None:
        return "", None
    if not isinstance(value, str):
        return None, f"{field} must be a string"
    return value, None


# -- recording ----------------------------------------------------------------

def apply(pool, manifest):
    """Commit every named attempt and its permitted learning effects at once."""
    _require_schema(pool)
    request_id, raw_items = _manifest(manifest)
    with pool.transaction():
        # Validated again under the write transaction: a pool that changed since
        # check must not half-apply.
        items = _validate(pool, raw_items)
        batch = _batch_fingerprint("apply", items)
        replay = _replay(pool, request_id, batch)
        if replay is not None:
            return replay
        results = [
            _record(pool, request_id, "apply", item, batch) for item in items
        ]
        return _envelope(request_id, results)


def correct(pool, attempt_id, payload):
    """Replace one Agent-recorded attempt and recompute only its own effects."""
    _require_schema(pool)
    if not isinstance(payload, dict):
        raise ManifestError("correction must be a JSON object")
    extra = sorted(set(payload) - CORRECTION_FIELDS)
    if extra:
        raise ManifestError(
            f"correction has unsupported field: {extra[0]} — a correction carries "
            "only request_id, answer_text, note, and rating"
        )
    request_id = _request_id(payload.get("request_id"))
    with pool.transaction():
        attempt = pool.attempt(attempt_id)
        if attempt is None:
            raise ManifestError(f"unknown attempt: {attempt_id}")
        item, error = _normalize_item(
            pool,
            {"problem_id": attempt["problem_id"],
             "answer_text": payload.get("answer_text"),
             "note": payload.get("note"),
             "rating": payload.get("rating")},
            set(),
        )
        if error:
            raise ManifestError(f"correction: {error}")
        item["index"] = 0
        batch = _batch_fingerprint("correct", [item], attempt_id)
        replay = _replay(pool, request_id, batch)
        if replay is not None:
            return replay
        operation = linked_operation(pool, attempt_id)
        if operation is None:
            raise ManifestError(
                f"attempt {attempt_id} has no Agent recording to correct — it was "
                "recorded elsewhere, so record a fresh attempt instead"
            )
        conflict = correction_conflict(pool, attempt, operation)
        if conflict:
            raise ManifestError(conflict)
        pre_state = json.loads(operation["pre_state"])
        pool.connect().execute(
            "DELETE FROM feedback_events WHERE attempt_id=?", (attempt_id,)
        )
        _restore(pool, pre_state)
        pool.connect().execute(
            "UPDATE problem_attempts SET status=?, note=?, answer_text=? WHERE id=?",
            (_status(item["rating"]), item["note"] or None,
             item["answer_text"] or None, attempt_id),
        )
        result, post_state = _effects(pool, item, attempt_id, pre_state)
        result["corrected"] = True
        _insert_operation(pool, request_id, "correct", item, attempt_id, batch,
                          pre_state, post_state, result)
        return _envelope(request_id, [result])


def _record(pool, request_id, kind, item, batch):
    """Insert one attempt with its permitted effects and link the two."""
    problem_id = item["problem_id"]
    targets = _targets(pool, problem_id)
    pre_state = _snapshot(pool, problem_id, targets)
    attempt_id = pool.insert_attempt(
        problem_id, _status(item["rating"]), item["note"] or None,
        item["answer_text"] or None,
    )
    result, post_state = _effects(pool, item, attempt_id, pre_state)
    _insert_operation(pool, request_id, kind, item, attempt_id, batch,
                      pre_state, post_state, result)
    return result


def _effects(pool, item, attempt_id, pre_state):
    """Run the existing rating rules for a rated item; nothing for an ungraded one.

    Returns the reported result together with the post-effect projection snapshot
    a later correction compares against.
    """
    problem_id = item["problem_id"]
    rating = item["rating"]
    note = item["note"] or None
    changes = []
    if rating is not None:
        changes = feedback_rules.apply(
            pool, "problem", problem_id, rating=rating, note=note,
            attempt_id=attempt_id,
        )
    schedule = pool.schedule_get("problem", problem_id)
    result = {
        "problem_id": problem_id,
        "attempt_id": attempt_id,
        "status": _status(rating),
        "rating": rating,
        "graded": rating is not None,
        "note_recorded": bool(note),
        "due_at": schedule["due_at"] if rating is not None and schedule else None,
        "changes": changes,
    }
    post_state = _snapshot(pool, problem_id, _targets(pool, problem_id))
    return result, post_state


def _status(rating):
    return UNGRADED_STATUS if rating is None else feedback_rules.RATING_PROGRESS[rating]


def _insert_operation(pool, request_id, kind, item, attempt_id, batch,
                      pre_state, post_state, result):
    pool.connect().execute(
        "INSERT INTO attempt_operations (request_id, problem_id, attempt_id, kind,"
        " rating, fingerprint, batch_fingerprint, result, pre_state, post_state)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (request_id, item["problem_id"], attempt_id, kind, item["rating"],
         _fingerprint({"kind": kind, "attempt_id": attempt_id, **item}),
         batch, json.dumps(result, ensure_ascii=False),
         json.dumps(pre_state, ensure_ascii=False),
         json.dumps(post_state, ensure_ascii=False)),
    )


# -- idempotency and correction guard ----------------------------------------

def _operations(pool, request_id):
    return pool.connect().execute(
        "SELECT * FROM attempt_operations WHERE request_id=? ORDER BY rowid",
        (request_id,),
    ).fetchall()


def linked_operation(pool, attempt_id):
    row = pool.connect().execute(
        "SELECT * FROM attempt_operations WHERE attempt_id=? ORDER BY rowid DESC LIMIT 1",
        (attempt_id,),
    ).fetchone()
    return dict(row) if row else None


def _require_same_batch(request_id, stored, batch):
    if any(row["batch_fingerprint"] != batch for row in stored):
        raise ManifestError(
            f"request_id {request_id!r} was already used for different content — "
            "use a new request_id for a new recording"
        )


def _replay(pool, request_id, batch):
    """The original response when this exact request already ran; else None."""
    stored = _operations(pool, request_id)
    if not stored:
        return None
    _require_same_batch(request_id, stored, batch)
    return _envelope(request_id, [json.loads(row["result"]) for row in stored])


def correction_conflict(pool, attempt, operation):
    """Why this attempt cannot be replaced anymore; None when it still can."""
    problem_id = attempt["problem_id"]
    if _snapshot(pool, problem_id, _targets(pool, problem_id)) != json.loads(
        operation["post_state"]
    ):
        return (
            f"attempt {attempt['id']} cannot be corrected: later learning activity "
            f"changed {problem_id} or its knowledge points — record a fresh attempt "
            "with `lesson-kit attempts <workspace> apply` instead"
        )
    newer = pool.connect().execute(
        "SELECT id FROM problem_attempts WHERE problem_id=? AND id>? ORDER BY id LIMIT 1",
        (problem_id, attempt["id"]),
    ).fetchone()
    if newer:
        return (
            f"attempt {attempt['id']} cannot be corrected: attempt {newer['id']} came "
            f"later for {problem_id} — correct that attempt, or record a fresh one"
        )
    return None


# -- reading ------------------------------------------------------------------

def record_result(pool, problem_id, result, note=None, answer_text=None, now=None,
                  practice_position=None):
    """Record one practice result atomically, the way the practice page does.

    Both surfaces call this, so the CLI cannot write a different shape than the
    HTTP handler: the attempt, the progress row, and the schedule move together
    or not at all. ``result`` is the categorical correct/wrong/stuck/skip.
    """
    status = schedule_rules.recorded_status(result)
    if status is None:
        return {"problem_id": problem_id, "result": result, "recorded": False}
    if pool.problem(problem_id) is None:
        raise ValueError(f"unknown problem: {problem_id}")
    with pool.transaction():
        attempt_id = pool.insert_attempt(problem_id, status, note, answer_text)
        pool.upsert_problem_progress(problem_id, status, note)
        state = pool.schedule_get("problem", problem_id) or schedule_rules.default_state(
            "problem", problem_id
        )
        next_state = schedule_rules.after_result(state, result, now or date.today())
        pool.schedule_upsert(next_state)
        practice = None
        if practice_position is not None:
            practice = active_practice.mark(
                pool, practice_position,
                "stuck" if result == "stuck" else "answered",
                attempt_id=attempt_id,
            )
    return {
        "problem_id": problem_id, "result": result, "recorded": True,
        "attempt_id": attempt_id, "status": status, "due_at": next_state["due_at"],
        "practice": practice,
    }


def list_attempts(pool, problem_id):
    """Every attempt of one problem with its Agent linkage and rating."""
    _require_schema(pool)
    if pool.problem(problem_id) is None:
        raise ManifestError(f"unknown problem: {problem_id}")
    attempts = pool.attempts(problem_id)
    latest = attempts[-1]["id"] if attempts else None
    rows = []
    for attempt in attempts:
        operation = linked_operation(pool, attempt["id"])
        event = pool.feedback_event_for_attempt(attempt["id"])
        rating = operation["rating"] if operation else (
            event["rating"] if event else None)
        rows.append({
            **attempt,
            "agent_recorded": operation is not None,
            "request_id": operation["request_id"] if operation else None,
            "rating": rating,
            "graded": rating is not None,
            "latest": attempt["id"] == latest,
        })
    return {"problem_id": problem_id, "count": len(rows), "attempts": rows}


def _round_rating_mode(pool):
    """The active round's rating mode, or None when no round is active."""
    row = pool.connect().execute(
        "SELECT rating_mode FROM active_practice WHERE singleton = 1").fetchone()
    return row[0] if row else None


def record_browser_attempt(pool, problem_id, answer_text=None, verdict=None,
                           choices=None, request_id=None, practice_position=None,
                           stuck=False):
    """Persist one answer the practice page just submitted.

    The attempt row is the learner's durable record; progress, schedule, and
    signals still move only when the session's rating lands, linked back through
    ``attempt_id``. The verdict is the objective grading the browser computed;
    a综合题 answer has none and stores ``answer_text`` alone. A pool that has
    not been migrated yet still gets the row (status ``new``, no verdict) — the
    migration adds the ``answered`` status and the verdict/choices columns.
    """
    if not isinstance(stuck, bool):
        raise ManifestError("stuck must be a boolean")
    if verdict is not None and verdict not in (0, 1):
        raise ManifestError("verdict must be true or false")
    # In a rating-off round the verdict IS the learning conclusion: the machine
    # judged the answer, so the self-question is already answered. Derived
    # state moves progress/current-state/schedule; no rated feedback event is
    # written, so the self-rating stats stay free of synthesized data.
    derive = verdict is not None and _round_rating_mode(pool) == "off"
    if choices is not None and (
            not isinstance(choices, list)
            or not all(isinstance(choice, str) for choice in choices)):
        raise ManifestError("choices must be a list of option texts")
    payload = _browser_payload("attempt", problem_id=problem_id,
                               answer_text=answer_text, verdict=verdict,
                               choices=choices, practice_position=practice_position,
                               stuck=stuck)
    if request_id is not None:
        _require_browser_schema(pool)
    with pool.transaction(immediate=request_id is not None):
        replay = _browser_replay(pool, request_id, payload)
        if replay is not None:
            return replay
        if pool.problem(problem_id) is None:
            raise ManifestError(f"unknown problem: {problem_id}")
        conn = pool.connect()
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='problem_attempts'"
        ).fetchone()
        columns = {row[1] for row in conn.execute("PRAGMA table_info(problem_attempts)")}
        widened = bool(ddl) and "'answered'" in (ddl[0] or "")
        status = "stuck" if stuck else (
            ANSWERED_STATUS if widened else UNGRADED_STATUS)
        attempt_id = pool.insert_attempt(
            problem_id, status, None, answer_text or None,
            verdict if widened and "verdict" in columns else None,
            choices if widened and "choices" in columns else None)
        result = {"attempt_id": attempt_id, "problem_id": problem_id,
                  "recorded": True, "status": status,
                  "verdict_recorded": widened and verdict is not None}
        if stuck:
            pool.upsert_problem_progress(problem_id, "stuck")
            state = pool.schedule_get("problem", problem_id) or schedule_rules.default_state(
                "problem", problem_id)
            next_state = schedule_rules.after_result(state, "stuck", date.today())
            pool.schedule_upsert(next_state)
            result["due_at"] = next_state["due_at"]
        if derive:
            progress_status = feedback_rules.RATING_PROGRESS[5 if verdict else 2]
            pool.upsert_problem_progress(problem_id, progress_status)
            pool.upsert_current_state(
                "problem", problem_id,
                learning_state.for_rating(5 if verdict else 2))
            state = pool.schedule_get("problem", problem_id) or schedule_rules.default_state(
                "problem", problem_id)
            next_state = schedule_rules.after_result(
                state, 5 if verdict else 2, date.today())
            pool.schedule_upsert(next_state)
            result["derived_state"] = progress_status
            for target_id in _targets(pool, problem_id):
                pool.upsert_current_state("kp", target_id, learning_state.for_rating(
                    5 if verdict else 2))
        if practice_position is not None:
            result["practice"] = active_practice.mark(
                pool, practice_position, "stuck" if stuck else "answered",
                attempt_id=attempt_id)
        _save_browser_operation(pool, request_id, payload, result)
    return result


def record_browser_feedback(pool, item_type, item_id, rating=None, note=None,
                            direction="", attempt_id=None, request_id=None):
    """Apply a rating and its retry marker in one serialized transaction."""
    payload = _browser_payload("feedback", item_type=item_type, item_id=item_id,
                               rating=rating, note=note, direction=direction,
                               attempt_id=attempt_id)
    if request_id is not None:
        _require_browser_schema(pool)
    with pool.transaction(immediate=request_id is not None):
        replay = _browser_replay(pool, request_id, payload)
        if replay is not None:
            return replay
        result = feedback_rules.apply(
            pool, item_type, item_id, rating=rating, note=note,
            direction=direction, attempt_id=attempt_id)
        _save_browser_operation(pool, request_id, payload, result)
    return result


def _browser_payload(kind, **fields):
    return json.dumps({"kind": kind, **fields}, sort_keys=True,
                      ensure_ascii=False, separators=(",", ":"))


def _require_browser_schema(pool):
    row = pool.connect().execute(
        "SELECT 1 FROM sqlite_master WHERE type='table'"
        " AND name='practice_request_operations'"
    ).fetchone()
    if row is None:
        db = pool.db_path.relative_to(pool.root)
        raise ManifestError(
            "this pool is not migrated for retry-safe browser practice — run: "
            + MIGRATION_COMMAND.format(db))


def _browser_replay(pool, request_id, payload):
    if request_id is None:
        return None
    row = pool.connect().execute(
        "SELECT payload, result FROM practice_request_operations WHERE request_id=?",
        (request_id,)).fetchone()
    if row is None:
        return None
    if row["payload"] != payload:
        raise RequestConflict(f"request_id {request_id} was already used for another write")
    return json.loads(row["result"])


def _save_browser_operation(pool, request_id, payload, result):
    if request_id is not None:
        pool.connect().execute(
            "INSERT INTO practice_request_operations (request_id, payload, result)"
            " VALUES (?, ?, ?)",
            (request_id, payload, json.dumps(result, ensure_ascii=False,
                                              sort_keys=True)))


def get_attempt(pool, attempt_id):
    """One attempt with its linked recording, event, and correction eligibility."""
    _require_schema(pool)
    attempt = pool.attempt(attempt_id)
    if attempt is None:
        raise ManifestError(f"unknown attempt: {attempt_id}")
    operation = linked_operation(pool, attempt_id)
    conflict = None
    if operation is not None:
        conflict = correction_conflict(pool, attempt, operation)
    row = pool.connect().execute(
        "SELECT * FROM problem_progress WHERE problem_id=?",
        (attempt["problem_id"],),
    ).fetchone()
    return {
        "attempt": attempt,
        "agent_recorded": operation is not None,
        "operation": None if operation is None else {
            "request_id": operation["request_id"],
            "kind": operation["kind"],
            "rating": operation["rating"],
        },
        "feedback_event": pool.feedback_event_for_attempt(attempt_id),
        "problem_progress": dict(row) if row else None,
        "current_state": pool.current_state("problem", attempt["problem_id"]),
        "schedule": pool.schedule_get("problem", attempt["problem_id"]),
        "correctable": operation is not None and conflict is None,
        "correction_conflict": conflict,
    }


# -- snapshots ----------------------------------------------------------------

def _targets(pool, problem_id):
    problem = pool.problem(problem_id)
    return list(problem["kp_ids"]) if problem else []


def _snapshot(pool, problem_id, targets):
    """The projections an attempt may touch, canonicalized for exact comparison."""
    conn = pool.connect()
    targets = sorted(targets)
    if targets:
        marks = ",".join("?" for _ in targets)
        state_sql = (
            "SELECT * FROM learning_current_state WHERE"
            f" (item_type='problem' AND item_id=?) OR"
            f" (item_type='kp' AND item_id IN ({marks}))"
        )
        signal_sql = f"SELECT * FROM learner_signals WHERE target_id IN ({marks})"
        signal_rows = conn.execute(signal_sql, targets).fetchall()
    else:
        state_sql = "SELECT * FROM learning_current_state WHERE item_type='problem' AND item_id=?"
        signal_rows = []
    return {
        "problem_id": problem_id,
        "targets": targets,
        "rows": {
            "problem_progress": _rows(conn.execute(
                "SELECT * FROM problem_progress WHERE problem_id=?",
                (problem_id,)).fetchall(), ("problem_id",)),
            "learning_current_state": _rows(
                conn.execute(state_sql, (problem_id, *targets)).fetchall(),
                ("item_type", "item_id")),
            "review_schedule": _rows(conn.execute(
                "SELECT * FROM review_schedule WHERE item_type='problem' AND item_id=?",
                (problem_id,)).fetchall(), ("direction",)),
            "learner_signals": _rows(signal_rows, ("signal_id",)),
        },
    }


def _rows(rows, keys):
    return [dict(row) for row in sorted(rows, key=lambda r: tuple(r[k] for k in keys))]


def _restore(pool, snap):
    """Put the snapshotted projections back exactly, creating and deleting rows."""
    conn = pool.connect()
    problem_id = snap["problem_id"]
    targets = list(snap.get("targets") or [])
    conn.execute("DELETE FROM problem_progress WHERE problem_id=?", (problem_id,))
    conn.execute("DELETE FROM review_schedule WHERE item_type='problem' AND item_id=?",
                 (problem_id,))
    if targets:
        marks = ",".join("?" for _ in targets)
        conn.execute(
            "DELETE FROM learning_current_state WHERE"
            f" (item_type='problem' AND item_id=?) OR"
            f" (item_type='kp' AND item_id IN ({marks}))",
            (problem_id, *targets),
        )
        conn.execute(f"DELETE FROM learner_signals WHERE target_id IN ({marks})", targets)
    else:
        conn.execute(
            "DELETE FROM learning_current_state WHERE item_type='problem' AND item_id=?",
            (problem_id,))
    for table, rows in snap["rows"].items():
        for row in rows:
            columns = ", ".join(row)
            marks = ", ".join("?" for _ in row)
            conn.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({marks})", tuple(row.values())
            )


# -- shared helpers -----------------------------------------------------------

def _envelope(request_id, results):
    return {
        "request_id": request_id,
        "counts": _counts(results),
        "items": results,
    }


def _counts(results):
    graded = sum(1 for item in results if item["graded"])
    return {"attempts": len(results), "graded": graded,
            "ungraded": len(results) - graded}


def _payload(item):
    return {field: item.get(field) for field in
            ("problem_id", "answer_text", "note", "rating")}


def _batch_fingerprint(kind, items, attempt_id=None):
    return _fingerprint({
        "kind": kind,
        "attempt_id": attempt_id,
        "items": [_payload(item) for item in items],
    })


def _fingerprint(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_schema(pool):
    """An unmigrated pool must say so, not fail with a bare SQL error."""
    conn = pool.connect()
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='attempt_operations'"
    ).fetchone()
    columns = [str(item[1]) for item in conn.execute("PRAGMA table_info(feedback_events)")]
    if not row or "attempt_id" not in columns:
        try:
            db = pool.db_path.relative_to(pool.root).as_posix()
        except ValueError:
            db = pool.db_path
        raise ManifestError(
            "this pool is not migrated for Agent attempt records — run: "
            + MIGRATION_COMMAND.format(db)
        )
