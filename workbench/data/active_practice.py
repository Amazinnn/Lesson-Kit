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
        item['draft'] = json.loads(item.pop('draft_json', None) or '{}')
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
                                       rating_mode=normalized['rating_mode'], replace=replace)
        if _row(pool) is not None:
            if not replace:
                raise ActivePracticeConflict("an unfinished practice already exists")
            previous = current(pool, resolve=False)
            if not paper_progress.park(pool, previous):
                _archive(pool, previous, "abandoned")
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
        " rating_mode, items_json, status, started_at, execution_id, paper_generation) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
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
        ),
    )


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


def clear(pool):
    _require_schema(pool, writing=True)
    before = current(pool)
    if before is None:
        return {"cleared": False, "practice": None}
    with pool.transaction(immediate=True):
        _archive(pool, before, "abandoned")
        _delete(pool)
    return {"cleared": True, "practice": before}


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
            "UPDATE active_practice_items SET state=?, attempt_id=?,draft_json=NULL WHERE position=?",
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


def _restore(pool, record):
    """Restore the existing singleton representation without new learning effects."""
    pool.connect().execute(
        'INSERT INTO active_practice(singleton,source_kind,source_ref,source_label,kp_ids_json,'
        'practice_mode,rating_mode,cursor,started_at,updated_at,execution_id,paper_generation) '
        'VALUES (1,?,?,?,?,?,?,?,?,?,?,?)',
        (record['source_kind'], record.get('source_ref'), record.get('source_label'),
         json.dumps(record['kp_ids'], ensure_ascii=False), record['practice_mode'],
         record['rating_mode'], record['cursor'], record['started_at'], record['updated_at'],
         record['execution_id'], record['paper_generation']))
    for item in record['items']:
        pool.connect().execute(
            'INSERT INTO active_practice_items(position,item_type,item_id,direction,state,'
            'attempt_id,content_revision,draft_json,draft_sequence) VALUES (?,?,?,?,?,?,?,?,?)',
            (item['position'], item['item_type'], item['item_id'], item.get('direction') or '',
             item['state'], item.get('attempt_id'), item.get('content_revision', 1),
             json.dumps(item.get('draft') or {}, ensure_ascii=False), item.get('draft_sequence', 0)))


def start_saved(pool, paper_id, *, practice_mode='exam', rating_mode='immediate', replace=False):
    from workbench.data import practice_sets
    _require_schema(pool)
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
        continuation = paper['continuation']
        if continuation and not continuation['available']:
            raise ActivePracticeConflict(continuation['reason'])
        existing = current(pool, resolve=False)
        if existing and existing.get('source_ref') == paper_id:
            if ids != [item['item_id'] for item in existing['items']]:
                raise ActivePracticeConflict('legacy Paper execution does not match its container; explicit repair is required')
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
            _restore(pool, record)
            pool.connect().execute('UPDATE paper_state SET checkpoint_json=NULL WHERE paper_id=?', (paper_id,))
        else:
            return create(pool, dict(source_ref=paper_id, source_label=paper['title'],
                                     kp_ids=list(dict.fromkeys(kp for q in ids for kp in pool.problem(q)['kp_ids'])),
                                     practice_mode=practice_mode, rating_mode=rating_mode,
                                     items=[dict(item_type='problem',item_id=q) for q in ids]))
    return current(pool)


def submission_context(practice, position):
    item = practice['items'][position]
    return dict(execution_id=practice['execution_id'], paper_id=practice.get('source_ref'),
                paper_generation=practice['paper_generation'], item_id=item['item_id'],
                content_revision=item['content_revision'], position=position)


def save_draft(pool, execution_id, position, draft, *, context=None, sequence=None):
    if not isinstance(draft, dict) or set(draft)-{'answer','choices'}:
        raise ActivePracticeError('draft must contain answer/choices only')
    if not isinstance(draft.get('answer', ''), str) or not isinstance(draft.get('choices', []), list) \
            or not all(isinstance(item, str) for item in draft.get('choices', [])):
        raise ActivePracticeError('invalid answer/choice draft')
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
        if sequence is None:
            sequence = item['draft_sequence'] + 1
        if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 9007199254740991:
            raise ActivePracticeError('invalid draft sequence')
        if sequence < item['draft_sequence'] or (sequence == item['draft_sequence'] and draft != item['draft']):
            raise ActivePracticeConflict('stale draft: a newer draft has already been saved')
        pool.connect().execute('UPDATE active_practice_items SET draft_json=?,draft_sequence=? WHERE position=?',
                               (json.dumps(draft, ensure_ascii=False), sequence, position))
    return {'saved': True}
