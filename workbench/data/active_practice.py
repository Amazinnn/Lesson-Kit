"""One workspace-local active Paper execution plus a tiny durable run archive.

The active singleton remains execution state. Every newly created execution is
normalized to a Paper source before it is stored. Completed or replaced runs
are snapshotted for the records page; attempts and feedback remain the learning
evidence.
"""

import json

from workbench.data import paper_progress


SOURCE_KINDS = {"paper"}
LEGACY_SOURCE_KINDS = {"quick", "practice_set", "agent"}
ITEM_TYPES = {"problem", "card"}
ITEM_STATES = {"pending", "answered", "stuck"}
MIGRATION_COMMAND = "python pool/scripts/migrate-progress.py --db {}"


class ActivePracticeError(ValueError):
    pass


class ActivePracticeConflict(ActivePracticeError):
    pass


def _require_schema(pool, *, writing=False):
    names = {
        row[0] for row in pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    required = {"active_practice", "active_practice_items", "practice_runs"}
    if writing:
        required.add("paper_state")
    if required <= names:
        return
    try:
        db = pool.db_path.relative_to(pool.root).as_posix()
    except ValueError:
        db = str(pool.db_path)
    raise ActivePracticeError(
        "this pool is not migrated for resumable practice — run: "
        + MIGRATION_COMMAND.format(db)
    )


def _has_column(pool, table, column):
    return column in {
        row[1] for row in pool.connect().execute(f'PRAGMA table_info({table})')
    }


def _require_reveal_timing_schema(pool):
    if _has_column(pool, 'active_practice', 'reveal_timing') \
            and _has_column(pool, 'practice_runs', 'reveal_timing'):
        return
    try:
        db = pool.db_path.relative_to(pool.root).as_posix()
    except ValueError:
        db = str(pool.db_path)
    raise ActivePracticeError(
        'this pool is not migrated for Paper answer reveal timing — run: '
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
    requested_source_kind = payload.get("source_kind", "paper")
    if requested_source_kind not in SOURCE_KINDS | LEGACY_SOURCE_KINDS:
        raise ActivePracticeError(
            "source_kind must be paper (legacy quick/practice_set/agent inputs are accepted)"
        )
    # `quick`, `practice_set`, and `agent` were historical execution-source
    # categories. They described how items were assembled, not what was being
    # executed. v1 keeps them as input aliases only so old browser/CLI callers
    # continue to work while every newly persisted run obeys Paper -> Run.
    source_kind = "paper"
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
        if requested_source_kind == "quick":
            source_label = "临时试卷"
        elif requested_source_kind == "agent":
            source_label = "Agent 试卷"
        elif source_ref:
            source_label = f"试卷 {source_ref.strip()}"
        else:
            source_label = "试卷"
    practice_mode = payload.get("practice_mode")
    rating_mode = payload.get("rating_mode")
    reveal_timing = payload.get("reveal_timing")
    if reveal_timing not in (None, "per_item", "on_submit"):
        raise ActivePracticeError("reveal_timing must be per_item or on_submit")
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
    if reveal_timing is not None and any(item["item_type"] != "problem" for item in items):
        raise ActivePracticeError("answer reveal timing applies only to ordinary-problem Papers")
    return {
        "source_kind": source_kind,
        "source_ref": source_ref.strip() if isinstance(source_ref, str) else None,
        "source_label": source_label.strip(),
        "kp_ids": kp_ids,
        "practice_mode": practice_mode,
        "rating_mode": rating_mode,
        "reveal_timing": reveal_timing,
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
        item['draft'] = json.loads(item.pop('draft_json', None) or '{}')
        if record.get('reveal_timing') in {'per_item', 'on_submit'}:
            item['draft'].setdefault('stuck', item['state'] == 'stuck')
            item['draft'].setdefault('reference_viewed', False)
        item['locked'] = item['state'] != 'pending'
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
    if resolve:
        record['unavailable_item_ids'] = [item['item_id'] for item in items if item.get('payload') is None]
    record["progress"] = {
        "completed": answered + stuck,
        "answered": answered,
        "stuck": stuck,
        "remaining": len(items) - answered - stuck,
        "total": len(items),
    }
    source_ref = record.get('source_ref') or ''
    if resolve and source_ref.startswith('ps-') and paper_progress.available(pool.connect()):
        from workbench.data import practice_sets
        try:
            record['continuation'] = practice_sets.get_saved(pool, source_ref)['continuation']
        except FileNotFoundError:
            record['continuation'] = dict(
                available=False, reason='对应的保存试卷已不存在，不能继续。',
                execution=dict(progress={"total": len(items), "completed": answered + stuck}),
                unavailable_item_ids=[])
    return record


def create(pool, payload, *, replace=False):
    _require_schema(pool, writing=True)
    normalized = _normalize(pool, payload)
    if normalized['reveal_timing'] is not None:
        _require_reveal_timing_schema(pool)
    with pool.transaction(immediate=True):
        source = normalized.get('source_ref') or ''
        if source.startswith('ps-'):
            from workbench.data import practice_sets
            path = practice_sets._saved_path(pool, source)
            if path.is_file():
                saved = practice_sets.get_saved(pool, source)
                if [i['problem_id'] for i in saved['plan']['items']] != [i['item_id'] for i in normalized['items']]:
                    raise ActivePracticeConflict('Paper execution does not match its saved container')
                selected = _row(pool)
                parked = paper_progress.state(pool.connect(), source)['checkpoint_json']
                if parked or (selected and selected['source_ref'] == source):
                    return start_saved(pool, source, practice_mode=normalized['practice_mode'],
                                       rating_mode=normalized['rating_mode'],
                                       reveal_timing=normalized['reveal_timing'], replace=replace)
        if _row(pool) is not None:
            if not replace:
                raise ActivePracticeConflict("an unfinished practice already exists")
            previous = current(pool, resolve=False)
            if not paper_progress.park(pool, previous):
                _archive(pool, previous, "abandoned")
            _delete(pool)
        values = (
            normalized["source_kind"], normalized["source_ref"],
            normalized["source_label"], json.dumps(normalized["kp_ids"], ensure_ascii=False),
            normalized["practice_mode"], normalized["rating_mode"],
        )
        if _has_column(pool, 'active_practice', 'reveal_timing'):
            pool.connect().execute(
                "INSERT INTO active_practice "
                "(singleton, source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
                " rating_mode, cursor, reveal_timing) VALUES (1, ?, ?, ?, ?, ?, ?, 0, ?)",
                (*values, normalized["reveal_timing"]),
            )
        else:
            pool.connect().execute(
                "INSERT INTO active_practice "
                "(singleton, source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
                " rating_mode, cursor) VALUES (1, ?, ?, ?, ?, ?, ?, 0)", values,
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
        if paper_progress.available(pool.connect()):
            execution = pool.connect().execute('INSERT INTO practice_execution_ids DEFAULT VALUES').lastrowid
            generation = paper_progress.ensure_state(pool.connect(), normalized['source_ref'])['generation'] if normalized['source_ref'] else 1
            pool.connect().execute('UPDATE active_practice SET execution_id=?,paper_generation=? WHERE singleton=1',
                                   (execution, generation))
            for item in normalized['items']:
                if item['item_type'] == 'problem':
                    pool.connect().execute('UPDATE active_practice_items SET content_revision=? WHERE position=?',
                                           (paper_progress.revision(pool.connect(), item['item_id']), item['position']))
    return current(pool)


def _archive(pool, record, status):
    explicit_mode = record.get('reveal_timing') in {'per_item', 'on_submit'}
    if explicit_mode:
        _require_reveal_timing_schema(pool)
    items = []
    for item in record["items"]:
        archived = {
            "position": item["position"],
            "item_type": item["item_type"],
            "item_id": item["item_id"],
            "direction": item.get("direction") or "",
            "state": item["state"],
            "attempt_id": item.get("attempt_id"),
            "content_revision": item.get("content_revision", 1),
        }
        if record.get('reveal_timing') in {'per_item', 'on_submit'}:
            archived['draft'] = item.get('draft') or {}
            archived['draft_sequence'] = item.get('draft_sequence', 0)
        items.append(archived)
    values = (
            "paper",
            record.get("source_ref"),
            record.get("source_label"),
            json.dumps(record["kp_ids"], ensure_ascii=False),
            record["practice_mode"],
            record["rating_mode"],
            json.dumps(items, ensure_ascii=False),
            status,
            record["started_at"],
            record.get('execution_id'),
            record.get('paper_generation', 1),
    )
    if _has_column(pool, 'practice_runs', 'reveal_timing'):
        cursor = pool.connect().execute(
            "INSERT INTO practice_runs "
            "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            " rating_mode, items_json, status, started_at, execution_id, paper_generation, reveal_timing) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*values, record.get('reveal_timing')),
        )
    else:
        cursor = pool.connect().execute(
            "INSERT INTO practice_runs "
            "(source_kind, source_ref, source_label, kp_ids_json, practice_mode, "
            " rating_mode, items_json, status, started_at, execution_id, paper_generation) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values,
        )
    return cursor.lastrowid


def replay(pool, run_id, *, replace=False):
    """Start the exact Paper items stored by one archived practice run."""
    _require_schema(pool)
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        raise ActivePracticeError("run_id must be a positive integer")
    row = pool.connect().execute(
        "SELECT * FROM practice_runs WHERE id=?", (run_id,)
    ).fetchone()
    if row is None:
        raise ActivePracticeError(f"unknown practice run: {run_id}")
    record = dict(row)
    try:
        items = json.loads(record["items_json"] or "[]")
        kp_ids = json.loads(record["kp_ids_json"] or "[]")
    except json.JSONDecodeError as exc:
        raise ActivePracticeError(f"practice run {run_id} is invalid") from exc
    source_ref = record.get('source_ref')
    if source_ref and source_ref.startswith('ps-'):
        from workbench.data import practice_sets
        path = practice_sets._saved_path(pool, source_ref)
        if path.is_file():
            saved = practice_sets.get_saved(pool, source_ref)
            if [i['problem_id'] for i in saved['plan']['items']] != [i['item_id'] for i in items]:
                source_ref = None  # Historical order is a temporary Paper, not a mutation of today's container.
    return create(pool, {
        # Historical rows may say quick/practice_set/agent. create() accepts
        # those aliases and normalizes the new execution to Paper semantics.
        "source_kind": record["source_kind"],
        "source_ref": source_ref,
        "source_label": record.get("source_label"),
        "kp_ids": kp_ids,
        "practice_mode": record["practice_mode"],
        "rating_mode": record["rating_mode"],
        "reveal_timing": record.get("reveal_timing"),
        "items": [
            {
                "item_type": item.get("item_type"),
                "item_id": item.get("item_id"),
                "direction": item.get("direction") or "",
            }
            for item in items
        ],
    }, replace=replace)


def _delete(pool):
    pool.connect().execute("DELETE FROM active_practice_items")
    pool.connect().execute("DELETE FROM active_practice WHERE singleton=1")


def clear(pool, *, execution_id=None, practice_context=None):
    _require_schema(pool, writing=True)
    before = current(pool)
    if before is None:
        return {"cleared": False, "practice": None}
    with pool.transaction(immediate=True):
        if execution_id is not None or practice_context is not None:
            if execution_id != before.get('execution_id'):
                raise ActivePracticeConflict('stale practice execution: reload the current Paper')
            if not isinstance(practice_context, dict):
                raise ActivePracticeConflict('stale practice page: refresh before pausing')
            paper_progress.guard(pool, practice_context)
            if not paper_progress.park(pool, before):
                raise ActivePracticeConflict('only a saved Paper execution can be paused')
            _delete(pool)
            return {"cleared": True, "paused": True, "practice": before}
        _archive(pool, before, "abandoned")
        _delete(pool)
    return {"cleared": True, "paused": False, "practice": before}


def _adopt_legacy_ordinary(pool, record):
    """Move a problem-only legacy execution into the new navigation lifecycle."""
    if record.get('reveal_timing') is not None or not record.get('items') \
            or any(item['item_type'] != 'problem' for item in record['items']):
        return False
    _require_reveal_timing_schema(pool)
    pool.connect().execute(
        "UPDATE active_practice SET reveal_timing='per_item',updated_at=datetime('now') "
        'WHERE singleton=1')
    record['reveal_timing'] = 'per_item'
    return True


def navigate(pool, execution_id, position, *, context=None):
    """Persist a Paper cursor without changing any answer or item state."""
    _require_schema(pool, writing=True)
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ActivePracticeError('position must be a non-negative integer')
    with pool.transaction(immediate=True):
        active = current(pool, resolve=False)
        if not active or active.get('execution_id') != execution_id:
            raise ActivePracticeConflict('stale practice execution: reload the current Paper')
        if position >= len(active['items']):
            raise ActivePracticeError(f'unknown practice position: {position}')
        item = active['items'][position]
        if not isinstance(context, dict):
            raise ActivePracticeConflict('stale practice page: refresh before navigating')
        paper_progress.guard(pool, context, item['item_id'], position)
        _adopt_legacy_ordinary(pool, active)
        pool.connect().execute(
            "UPDATE active_practice SET cursor=?,updated_at=datetime('now') WHERE singleton=1",
            (position,),
        )
    return {'practice': current(pool)}


def mark_stuck_draft(pool, execution_id, position, *, request_id, context=None):
    """Record a revisable on-submit-mode stuck mark and its disclosure fact."""
    from workbench.data import attempts

    _require_schema(pool, writing=True)
    if not isinstance(request_id, str) or not request_id.strip() \
            or len(request_id) > attempts.MAX_REQUEST_ID:
        raise ActivePracticeError('request_id must be a non-empty string of at most 200 characters')
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ActivePracticeError('position must be a non-negative integer')
    payload = attempts._browser_payload(
        'stuck-draft', execution_id=execution_id, position=position,
        practice_context=context)
    with pool.transaction(immediate=True):
        replay = attempts._browser_replay(pool, request_id, payload)
        if replay is not None:
            replay['replay'] = True
            return replay
        active = current(pool, resolve=False)
        if not active or active.get('execution_id') != execution_id:
            raise ActivePracticeConflict('stale practice execution: reload the current Paper')
        if active.get('reveal_timing') != 'on_submit':
            raise ActivePracticeConflict('revisable stuck marks require on_submit mode')
        if position >= len(active['items']):
            raise ActivePracticeError(f'unknown practice position: {position}')
        item = active['items'][position]
        if context is None:
            raise ActivePracticeConflict('stale practice page: refresh before marking stuck')
        paper_progress.guard(pool, context, item['item_id'], position)
        if item['state'] != 'pending':
            raise ActivePracticeConflict('cannot change the state of a locked item')
        draft = item.get('draft') or {}
        draft['stuck'] = True
        draft['reference_viewed'] = True
        sequence = item.get('draft_sequence', 0) + 1
        pool.connect().execute(
            'UPDATE active_practice_items SET draft_json=?,draft_sequence=? WHERE position=?',
            (json.dumps(draft, ensure_ascii=False), sequence, position),
        )
        result = {'practice': current(pool)}
        attempts._save_browser_operation(pool, request_id, payload, result)
    return result


def mark(pool, position, state, *, attempt_id=None):
    _require_schema(pool, writing=True)
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ActivePracticeError("position must be a non-negative integer")
    if state not in {"answered", "stuck"}:
        raise ActivePracticeError("state must be answered or stuck")
    if attempt_id is not None and (
        isinstance(attempt_id, bool) or not isinstance(attempt_id, int)
    ):
        raise ActivePracticeError("attempt_id must be an integer or null")

    with pool.transaction(immediate=True):
        active_row = _row(pool)
        if active_row is None:
            raise ActivePracticeError("no unfinished practice")
        explicit_mode = dict(active_row).get('reveal_timing') in {'per_item', 'on_submit'}
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

        if explicit_mode:
            metadata = json.loads(item['draft_json'] or '{}')
            metadata['stuck'] = state == 'stuck'
            metadata['reference_viewed'] = True
            pool.connect().execute(
                "UPDATE active_practice_items SET state=?,attempt_id=?,draft_json=? WHERE position=?",
                (state, attempt_id, json.dumps(metadata, ensure_ascii=False), position),
            )
        else:
            pool.connect().execute(
                "UPDATE active_practice_items SET state=?, attempt_id=?,draft_json=NULL WHERE position=?",
                (state, attempt_id, position),
            )
        pending = pool.connect().execute(
            "SELECT position FROM active_practice_items "
            "WHERE state='pending' ORDER BY position"
        ).fetchall()
        if not pending:
            finished = current(pool)
            if explicit_mode:
                pool.connect().execute(
                    "UPDATE active_practice SET cursor=?,updated_at=datetime('now') WHERE singleton=1",
                    (position,),
                )
                return {"completed": False, "replay": False, "practice": current(pool)}
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


def submit(pool, execution_id, request_id, *, grade_answer, drafts=None):
    """Finalize one explicit-mode Paper using saved inputs in one transaction."""
    from workbench.data import attempts

    _require_schema(pool, writing=True)
    if not callable(grade_answer):
        raise ActivePracticeError('grade_answer must be provided by the practice domain')
    if not isinstance(request_id, str) or not request_id.strip() \
            or len(request_id) > attempts.MAX_REQUEST_ID:
        raise ActivePracticeError('request_id must be a non-empty string of at most 200 characters')
    normalized_drafts = []
    if drafts is not None:
        if not isinstance(drafts, list):
            raise ActivePracticeError('drafts must be a list')
        seen = set()
        for entry in drafts:
            if not isinstance(entry, dict):
                raise ActivePracticeError('each final draft must be an object')
            position = entry.get('position')
            if isinstance(position, bool) or not isinstance(position, int) or position < 0:
                raise ActivePracticeError('draft position must be a non-negative integer')
            if position in seen:
                raise ActivePracticeError(f'duplicate final draft position: {position}')
            seen.add(position)
            if not isinstance(entry.get('practice_context'), dict):
                raise ActivePracticeConflict('stale practice page: refresh before submitting')
            normalized_drafts.append({
                'position': position,
                'draft': entry.get('draft'),
                'sequence': entry.get('sequence'),
                'practice_context': entry['practice_context'],
            })
        normalized_drafts.sort(key=lambda entry: entry['position'])
    payload = attempts._browser_payload(
        'paper-submit', execution_id=execution_id, drafts=normalized_drafts)

    with pool.transaction(immediate=True):
        replay = attempts._browser_replay(pool, request_id, payload)
        if replay is not None:
            replay['replay'] = True
            return replay
        active = current(pool, resolve=False)
        if not active or active.get('execution_id') != execution_id:
            raise ActivePracticeConflict('stale practice execution: reload the current Paper')
        if active.get('reveal_timing') not in {'per_item', 'on_submit'}:
            if not _adopt_legacy_ordinary(pool, active):
                raise ActivePracticeConflict('explicit Paper submission is unavailable for this legacy run')

        for entry in normalized_drafts:
            save_draft(pool, execution_id, entry['position'], entry['draft'],
                       context=entry['practice_context'], sequence=entry['sequence'])

        active = current(pool, resolve=False)
        for item in active['items']:
            context = submission_context(active, item['position'])
            paper_progress.guard(pool, context, item['item_id'], item['position'])
            if item['state'] != 'pending':
                continue
            draft = item.get('draft') or {}
            answer_text = draft.get('answer', '')
            choices = draft.get('choices') or []
            if choices and not answer_text:
                answer_text = ', '.join(choices)
            blank = not answer_text.strip() and not choices
            stuck = bool(draft.get('stuck')) or blank
            if stuck:
                answer_text = ''
                choices = []
            verdict = None if stuck else grade_answer(
                pool.problem(item['item_id']), answer_text, choices)
            attempts.record_browser_attempt(
                pool, item['item_id'], answer_text=answer_text,
                verdict=None if verdict is None else int(verdict),
                choices=choices or None, practice_position=item['position'],
                stuck=stuck, practice_context=context)

        finished = current(pool)
        run_id = _archive(pool, finished, 'completed')
        _delete(pool)
        result = {'completed': True, 'replay': False, 'run_id': run_id,
                  'execution_id': execution_id}
        attempts._save_browser_operation(pool, request_id, payload, result)
    return result


def get_run(pool, run_id):
    """Read one completed Paper run with its original inputs and evidence."""
    _require_schema(pool)
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        raise ActivePracticeError('run_id must be a positive integer')
    raw = pool.connect().execute('SELECT * FROM practice_runs WHERE id=?', (run_id,)).fetchone()
    if raw is None:
        raise ActivePracticeError(f'unknown practice run: {run_id}')
    record = dict(raw)
    try:
        record['kp_ids'] = json.loads(record.pop('kp_ids_json') or '[]')
        items = json.loads(record.pop('items_json') or '[]')
    except json.JSONDecodeError as exc:
        raise ActivePracticeError(f'practice run {run_id} is invalid') from exc
    correct = incorrect = ungraded = answered = stuck = 0
    for item in items:
        item['draft'] = item.get('draft') or {}
        if record.get('reveal_timing') in {'per_item', 'on_submit'}:
            item['draft'].setdefault('stuck', item['state'] == 'stuck')
            item['draft'].setdefault('reference_viewed', False)
        item['locked'] = item.get('state') != 'pending'
        if item['state'] == 'answered':
            answered += 1
        elif item['state'] == 'stuck':
            stuck += 1
        item['payload'] = (pool.problem(item['item_id']) if item['item_type'] == 'problem'
                           else pool.card(item['item_id']))
        if item['item_type'] == 'problem' and item.get('attempt_id'):
            attempt = pool.attempt(item['attempt_id'])
            if attempt is not None:
                attempt = dict(attempt)
                choices = attempt.get('choices')
                if isinstance(choices, str) and choices:
                    try:
                        attempt['choices'] = json.loads(choices)
                    except json.JSONDecodeError:
                        attempt['choices'] = []
                item['attempt'] = attempt
                event = pool.feedback_event_for_attempt(item['attempt_id'])
                if event is not None:
                    item['feedback'] = event
                if attempt.get('verdict') == 1:
                    correct += 1
                elif attempt.get('verdict') == 0:
                    incorrect += 1
                elif item['state'] == 'answered':
                    ungraded += 1
    record['items'] = items
    record['unavailable_item_ids'] = [item['item_id'] for item in items
                                      if item.get('payload') is None]
    record['progress'] = {
        'completed': answered + stuck, 'answered': answered, 'stuck': stuck,
        'remaining': len(items) - answered - stuck, 'total': len(items),
    }
    record['result_counts'] = {
        'correct': correct, 'incorrect': incorrect, 'ungraded': ungraded,
        'stuck': stuck, 'total': len(items),
    }
    return record


def _restore(pool, record):
    """Restore the existing singleton representation without new learning effects."""
    values = (record['source_kind'], record.get('source_ref'), record.get('source_label'),
              json.dumps(record['kp_ids'], ensure_ascii=False), record['practice_mode'],
              record['rating_mode'], record['cursor'], record['started_at'], record['updated_at'],
              record['execution_id'], record['paper_generation'])
    if _has_column(pool, 'active_practice', 'reveal_timing'):
        pool.connect().execute(
            'INSERT INTO active_practice(singleton,source_kind,source_ref,source_label,kp_ids_json,'
            'practice_mode,rating_mode,cursor,started_at,updated_at,execution_id,paper_generation,'
            'reveal_timing) VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?)',
            (*values, record.get('reveal_timing')))
    else:
        if record.get('reveal_timing') is not None:
            _require_reveal_timing_schema(pool)
        pool.connect().execute(
            'INSERT INTO active_practice(singleton,source_kind,source_ref,source_label,kp_ids_json,'
            'practice_mode,rating_mode,cursor,started_at,updated_at,execution_id,paper_generation) '
            'VALUES (1,?,?,?,?,?,?,?,?,?,?,?)', values)
    for item in record['items']:
        pool.connect().execute(
            'INSERT INTO active_practice_items(position,item_type,item_id,direction,state,'
            'attempt_id,content_revision,draft_json,draft_sequence) VALUES (?,?,?,?,?,?,?,?,?)',
            (item['position'], item['item_type'], item['item_id'], item.get('direction') or '',
             item['state'], item.get('attempt_id'), item.get('content_revision', 1),
             json.dumps(item.get('draft') or {}, ensure_ascii=False), item.get('draft_sequence', 0)))


def start_saved(pool, paper_id, *, practice_mode='exam', rating_mode='immediate',
                reveal_timing=None, replace=False):
    from workbench.data import practice_sets
    _require_schema(pool)
    if reveal_timing is not None:
        if reveal_timing not in {'per_item', 'on_submit'}:
            raise ActivePracticeError('reveal_timing must be per_item or on_submit')
        _require_reveal_timing_schema(pool)
    if not paper_progress.available(pool.connect()):
        raise ActivePracticeError('migrate the pool for independent Paper progress')
    if pool._transaction_depth == 0:
        paper_progress.flush_files(pool)
    with pool.transaction(immediate=True):
        paper = practice_sets.get_saved(pool, paper_id)
        if paper['missing_problem_ids']:
            raise ActivePracticeError('试卷引用的题目不可用：'+', '.join(paper['missing_problem_ids']))
        ids = [item['problem_id'] for item in paper['plan']['items']]
        if not ids:
            raise ActivePracticeError('empty Paper cannot start')
        if paper['validation_errors']:
            raise ActivePracticeError('; '.join(paper['validation_errors']))
        if paper['start_block_reason']:
            raise ActivePracticeConflict(paper['start_block_reason'])
        continuation = paper['continuation']
        if continuation and not continuation['available']:
            raise ActivePracticeConflict(continuation['reason'])
        existing = current(pool, resolve=False)
        if existing and existing.get('source_ref') == paper_id:
            if ids != [item['item_id'] for item in existing['items']]:
                raise ActivePracticeConflict('legacy Paper execution does not match its container; explicit repair is required')
            if reveal_timing is not None:
                _adopt_legacy_ordinary(pool, existing)
            return current(pool)
        if existing:
            if not paper_progress.park(pool, existing):
                if not replace:
                    raise ActivePracticeConflict('an unfinished temporary practice already exists')
                _archive(pool, existing, 'abandoned')
            _delete(pool)
        state = paper_progress.ensure_state(pool.connect(), paper_id)
        if state['checkpoint_json']:
            record = json.loads(state['checkpoint_json'])
            if not continuation or not continuation['available']:
                raise ActivePracticeConflict((continuation or {}).get('reason') or '试卷执行进度无法验证，不能继续。')
            if reveal_timing is not None and record.get('reveal_timing') is None \
                    and record.get('items') \
                    and all(item['item_type'] == 'problem' for item in record['items']):
                record['reveal_timing'] = 'per_item'
            _restore(pool, record)
            pool.connect().execute('UPDATE paper_state SET checkpoint_json=NULL WHERE paper_id=?', (paper_id,))
        else:
            return create(pool, dict(source_ref=paper_id, source_label=paper['title'],
                                     kp_ids=list(dict.fromkeys(kp for q in ids for kp in pool.problem(q)['kp_ids'])),
                                     practice_mode=practice_mode, rating_mode=rating_mode,
                                     reveal_timing=reveal_timing,
                                     items=[dict(item_type='problem',item_id=q) for q in ids]))
    return current(pool)


def submission_context(practice, position):
    item = practice['items'][position]
    return dict(execution_id=practice['execution_id'], paper_id=practice.get('source_ref'),
                paper_generation=practice['paper_generation'], item_id=item['item_id'],
                content_revision=item['content_revision'], position=position)


def save_draft(pool, execution_id, position, draft, *, context=None, sequence=None):
    fields = {'answer', 'choices', 'stuck', 'reference_viewed'}
    if not isinstance(draft, dict) or set(draft) - fields:
        raise ActivePracticeError('draft must contain answer/choices and optional stuck/reference_viewed flags')
    if not isinstance(draft.get('answer', ''), str) or not isinstance(draft.get('choices', []), list) \
            or not all(isinstance(item, str) for item in draft.get('choices', [])):
        raise ActivePracticeError('invalid answer/choice draft')
    for field in ('stuck', 'reference_viewed'):
        if field in draft and not isinstance(draft[field], bool):
            raise ActivePracticeError(f'draft {field} must be a boolean')
    with pool.transaction(immediate=True):
        active = current(pool, resolve=False)
        if not active or active['execution_id'] != execution_id:
            raise ActivePracticeConflict('stale draft execution')
        if not isinstance(position, int) or isinstance(position, bool) or not 0 <= position < len(active['items']):
            raise ActivePracticeError('unknown draft position')
        item = active['items'][position]
        if context is not None:
            paper_progress.guard(pool, context, item['item_id'], position)
        if item['state'] != 'pending':
            raise ActivePracticeConflict('cannot replace a submitted answer with a draft')
        draft = dict(draft)
        if active.get('reveal_timing') in {'per_item', 'on_submit'}:
            previous = item.get('draft') or {}
            answer_changed = (draft.get('answer', '') != previous.get('answer', '')
                              or draft.get('choices', []) != previous.get('choices', []))
            has_answer = bool(draft.get('answer', '').strip() or draft.get('choices'))
            draft['stuck'] = bool(draft.get('stuck') or previous.get('stuck'))
            if answer_changed and has_answer:
                draft['stuck'] = False
            draft['reference_viewed'] = bool(
                draft.get('reference_viewed', False) or previous.get('reference_viewed', False))
        if sequence is None:
            sequence = item['draft_sequence'] + 1
        if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 9007199254740991:
            raise ActivePracticeError('invalid draft sequence')
        if sequence < item['draft_sequence'] or (sequence == item['draft_sequence'] and draft != item['draft']):
            raise ActivePracticeConflict('stale draft: a newer draft has already been saved')
        pool.connect().execute('UPDATE active_practice_items SET draft_json=?,draft_sequence=? WHERE position=?',
                               (json.dumps(draft, ensure_ascii=False), sequence, position))
    return {'saved': True, 'sequence': sequence}
