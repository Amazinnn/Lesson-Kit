"""Per-Paper checkpoints, readable revisions and recoverable file publication."""

import json
import sqlite3

from workbench.domain.answering_content import signature


def available(conn):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE name='paper_state'").fetchone() is not None


def revision(conn, problem_id):
    row = conn.execute('SELECT revision FROM problem_revisions WHERE problem_id=?',
                       (problem_id,)).fetchone()
    return row[0] if row else 1


def changed(conn, before, after):
    if not available(conn) or signature(before) == signature(after):
        return
    previous_factory = conn.row_factory
    try:
        conn.row_factory = sqlite3.Row
        _changed(conn, before)
    finally:
        conn.row_factory = previous_factory


def _changed(conn, before):
    problem_id = before['problem_id']
    conn.execute('INSERT INTO problem_revisions(problem_id, revision) VALUES (?, 2) '
                 'ON CONFLICT(problem_id) DO UPDATE SET revision=revision+1', (problem_id,))
    reconcile_active(conn)
    for row in conn.execute('SELECT paper_id,checkpoint_json FROM paper_state WHERE checkpoint_json IS NOT NULL').fetchall():
        record = json.loads(row['checkpoint_json'])
        altered = False
        for item in record['items']:
            if item['item_id'] == problem_id and item['item_type'] == 'problem':
                item.update(state='pending', attempt_id=None, draft={}, draft_sequence=0,
                            content_revision=revision(conn, problem_id))
                record['cursor'] = min(record['cursor'], item['position'])
                altered = True
        if altered:
            conn.execute('UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?',
                         (json.dumps(record, ensure_ascii=False), row['paper_id']))


def update_question(conn, sql, parameters):
    """Execute an existing single-question UPDATE (identity is its last parameter)."""
    if not available(conn):
        return conn.execute(sql, parameters)
    def read():
        cursor = conn.execute('SELECT * FROM problems WHERE problem_id=?', (parameters[-1],))
        row = cursor.fetchone()
        return dict(zip([column[0] for column in cursor.description], row)) if row else None
    before = read()
    if before and before.get('deleted_at'):
        raise ValueError('cannot edit deleted question: ' + parameters[-1])
    result = conn.execute(sql, parameters)
    after = read()
    if before and after:
        changed(conn, before, after)
    return result


def reconcile_active(conn):
    for item in conn.execute('SELECT position,item_id,content_revision FROM active_practice_items '
                             "WHERE item_type='problem'").fetchall():
        current = revision(conn, item['item_id'])
        if current != item['content_revision']:
            conn.execute("UPDATE active_practice_items SET state='pending',attempt_id=NULL,"
                         'draft_json=NULL,draft_sequence=0,content_revision=? WHERE position=?',
                         (current, item['position']))
            conn.execute('UPDATE active_practice SET cursor=MIN(cursor, ?) WHERE singleton=1',
                         (item['position'],))


def state(conn, paper_id):
    row = conn.execute('SELECT * FROM paper_state WHERE paper_id=?', (paper_id,)).fetchone()
    return dict(row) if row else dict(paper_id=paper_id, generation=1, checkpoint_json=None,
                                     pending_json=None, pending_delete=0)


def ensure_state(conn, paper_id):
    if not available(conn):
        database = conn.execute('PRAGMA database_list').fetchone()[2]
        raise ValueError('pool requires Paper progress migration: run python pool/scripts/migrate-progress.py --db ' + database)
    conn.execute('INSERT OR IGNORE INTO paper_state(paper_id) VALUES (?)', (paper_id,))
    return state(conn, paper_id)


def park(pool, record):
    """A saved Paper pauses; temporary executions retain the old explicit replace rule."""
    paper_id = record.get('source_ref')
    if not paper_id or not paper_id.startswith('ps-'):
        return False
    from workbench.data import practice_sets
    from workbench.data.active_practice import ActivePracticeConflict
    if not practice_sets._saved_path(pool, paper_id).is_file():
        return False
    paper = practice_sets.get_saved(pool, paper_id)
    status = paper['continuation']
    if not status or not status['available']:
        raise ActivePracticeConflict((status or {}).get('reason') or '试卷执行进度无法验证，不能暂停。')
    ensure_state(pool.connect(), paper_id)
    pool.connect().execute('UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?',
                           (json.dumps(record, ensure_ascii=False), paper_id))
    return True


def reset(pool, paper_id):
    conn = pool.connect()
    ensure_state(conn, paper_id)
    conn.execute('UPDATE paper_state SET generation=generation+1,checkpoint_json=NULL '
                 'WHERE paper_id=?', (paper_id,))
    active = conn.execute('SELECT source_ref FROM active_practice WHERE singleton=1').fetchone()
    if active and active[0] == paper_id:
        from workbench.data.active_practice import _delete
        _delete(pool)


def reconcile_membership(pool, paper_id, problem_ids, reason="membership"):
    """Rewrite one Paper's execution by question identity, keeping survivors.

    A membership or order edit no longer throws the unfinished run away: every
    surviving question keeps its state, attempt link, draft and sequence, an added
    or replaced identity starts pending, and a removed item moves into the retained
    history instead of disappearing with the run.
    """
    from workbench.data import active_practice
    from workbench.data.pool import ensure_paper_lifecycle_schema
    conn = pool.connect()
    ensure_state(conn, paper_id)
    ensure_paper_lifecycle_schema(conn)
    wanted = [str(problem_id) for problem_id in problem_ids]
    record = _live_or_parked(pool, paper_id)
    if record is None:
        return {"preserved": 0, "added": len(wanted), "removed": 0, "execution_id": None}
    live = record.get("source_ref") == paper_id and active_practice.current(pool, resolve=False)
    live = bool(live and live.get("execution_id") == record.get("execution_id"))
    generation = state(conn, paper_id)["generation"] + 1
    old_items = [item for item in record.get("items") or []
                 if item.get("item_type") == "problem"]
    known = {item["item_id"]: item for item in old_items}
    kept = [problem_id for problem_id in wanted if problem_id in known]
    added = [problem_id for problem_id in wanted if problem_id not in known]
    removed = [item for item in old_items if item["item_id"] not in set(wanted)]
    cursor = _reconciled_cursor(old_items, wanted, int(record.get("cursor") or 0))
    items = []
    for position, problem_id in enumerate(wanted):
        source = known.get(problem_id)
        if source is None:
            items.append({"position": position, "item_type": "problem", "item_id": problem_id,
                          "direction": "", "state": "pending", "attempt_id": None,
                          "content_revision": revision(conn, problem_id),
                          "draft": {}, "draft_sequence": 0})
            continue
        items.append({**source, "position": position})
    for item in removed:
        _retire_item(conn, paper_id, item, reason)
    record = {**record, "items": items, "cursor": cursor, "paper_generation": generation}
    conn.execute('UPDATE paper_state SET generation=? WHERE paper_id=?', (generation, paper_id))
    if items:
        if live:
            active_practice._delete(pool)
            active_practice._restore(pool, record)
        else:
            conn.execute('UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?',
                         (json.dumps(record, ensure_ascii=False), paper_id))
    else:
        # Nothing survives, so there is no unfinished run to keep; every removed
        # item is already in the retained history.
        if live:
            active_practice._delete(pool)
        conn.execute('UPDATE paper_state SET checkpoint_json=NULL WHERE paper_id=?', (paper_id,))
    return {"preserved": len(kept), "added": len(added), "removed": len(removed),
            "execution_id": record.get("execution_id")}


def _live_or_parked(pool, paper_id):
    from workbench.data import active_practice
    active = active_practice.current(pool, resolve=False)
    if active and active.get("source_ref") == paper_id:
        return active
    parked = state(pool.connect(), paper_id)["checkpoint_json"]
    return json.loads(parked) if parked else None


def _reconciled_cursor(old_items, wanted, cursor):
    """Keep the cursor on its question; otherwise the next, then previous survivor."""
    if not wanted:
        return 0
    position = max(0, min(cursor, len(old_items) - 1)) if old_items else 0
    anchor = old_items[position]["item_id"] if old_items else None
    if anchor in wanted:
        return wanted.index(anchor)
    for item in old_items[position + 1:]:
        if item["item_id"] in wanted:
            return wanted.index(item["item_id"])
    for item in reversed(old_items[:position]):
        if item["item_id"] in wanted:
            return wanted.index(item["item_id"])
    return 0


def _retire_item(conn, paper_id, item, reason):
    sequence = conn.execute(
        'SELECT COALESCE(MAX(sequence), 0) + 1 FROM retired_paper_items WHERE paper_id=?',
        (paper_id,)).fetchone()[0]
    conn.execute(
        'INSERT INTO retired_paper_items (paper_id, sequence, problem_id, position, state,'
        ' attempt_id, content_revision, draft_json, draft_sequence, reason)'
        ' VALUES (?,?,?,?,?,?,?,?,?,?)',
        (paper_id, sequence, item["item_id"], item.get("position", 0), item.get("state", "pending"),
         item.get("attempt_id"), item.get("content_revision"),
         json.dumps(item.get("draft") or {}, ensure_ascii=False),
         item.get("draft_sequence", 0), reason))


def queue_file(pool, paper_id, record):
    conn = pool.connect()
    ensure_state(conn, paper_id)
    conn.execute('UPDATE paper_state SET pending_json=?,pending_delete=? WHERE paper_id=?',
                 (json.dumps(record, ensure_ascii=False) if record is not None else None,
                  int(record is None), paper_id))


def flush_files(pool):
    from workbench.data import practice_sets
    if not available(pool.connect()):
        return
    if pool._transaction_depth > 1:
        return  # Never publish a file intent from an uncommitted enclosing mutation.
    with pool.transaction(immediate=True):
        rows = pool.connect().execute('SELECT * FROM paper_state '
                                       'WHERE pending_json IS NOT NULL OR pending_delete=1').fetchall()
        for row in rows:
            path = practice_sets._saved_path(pool, row['paper_id'])
            if row['pending_delete']:
                path.unlink(missing_ok=True)
            else:
                practice_sets._atomic_json(path, json.loads(row['pending_json']))
            pool.connect().execute('UPDATE paper_state SET pending_json=NULL,pending_delete=0 '
                                    'WHERE paper_id=?', (row['paper_id'],))


def guard(pool, context, problem_id=None, position=None, *, feedback=False,
          attempt_id=None):
    from workbench.data.active_practice import ActivePracticeConflict
    if not available(pool.connect()) or not isinstance(context, dict):
        raise ActivePracticeConflict('stale practice page: refresh before submitting')
    conn = pool.connect()
    active = conn.execute('SELECT * FROM active_practice WHERE singleton=1').fetchone()
    execution = context.get('execution_id')
    record = dict(active) if active and active['execution_id'] == execution else None
    active_execution = record is not None
    if feedback and record is None:
        archived = conn.execute('SELECT * FROM practice_runs WHERE execution_id=?', (execution,)).fetchone()
        if archived:
            record = dict(archived)
        else:
            for row in conn.execute('SELECT checkpoint_json FROM paper_state WHERE checkpoint_json IS NOT NULL'):
                parked = json.loads(row[0])
                if parked['execution_id'] == execution:
                    record = parked
                    break
    paper_id = record.get('source_ref') if record else None
    if (record is None or context.get('paper_id') != paper_id
            or record['paper_generation'] != context.get('paper_generation')
            or (paper_id and state(conn, paper_id)['generation'] != context.get('paper_generation'))):
        raise ActivePracticeConflict('stale practice execution: reload the current Paper')
    if problem_id and (context.get('item_id') != problem_id
                       or revision(conn, problem_id) != context.get('content_revision')):
        raise ActivePracticeConflict('stale answering content: reload the corrected question')
    if position is not None:
        item = conn.execute('SELECT item_id,content_revision FROM active_practice_items WHERE position=?', (position,)).fetchone()
        if not item or item[0] != context.get('item_id'):
            raise ActivePracticeConflict('stale Paper position: reload the current Paper')
        if item[1] != context.get('content_revision'):
            raise ActivePracticeConflict('stale answering content: reload the corrected question')
    if attempt_id is not None:
        target_position = context.get('position')
        if isinstance(target_position, bool) or not isinstance(target_position, int):
            raise ActivePracticeConflict('stale rating target: reload the current Paper')
        if active_execution:
            target = conn.execute(
                'SELECT item_type,item_id,attempt_id FROM active_practice_items WHERE position=?',
                (target_position,)).fetchone()
            matches = bool(target and target['item_type'] == 'problem'
                           and target['item_id'] == problem_id
                           and target['attempt_id'] == attempt_id)
        else:
            items = record.get('items')
            if items is None:
                items = json.loads(record.get('items_json') or '[]')
            target = next((item for item in items
                           if item.get('position') == target_position), None)
            matches = bool(target and target.get('item_type') == 'problem'
                           and target.get('item_id') == problem_id
                           and target.get('attempt_id') == attempt_id)
        if not matches:
            raise ActivePracticeConflict(
                'stale rating target: attempt is not part of this Paper run')


def selected_saved(pool):
    if not available(pool.connect()):
        return False
    row = pool.connect().execute('SELECT source_ref FROM active_practice WHERE singleton=1').fetchone()
    return bool(row and (row[0] or '').startswith('ps-'))


def saved_attempt(pool, attempt_id):
    """Recognize versioned saved-Paper evidence even after selection/completion."""
    if not available(pool.connect()):
        return False
    conn = pool.connect()
    snapshots = [json.loads(row[0]) for row in conn.execute(
        'SELECT checkpoint_json FROM paper_state WHERE checkpoint_json IS NOT NULL')]
    for row in conn.execute("SELECT items_json FROM practice_runs WHERE execution_id IS NOT NULL "
                            "AND source_ref GLOB 'ps-*'"):
        snapshots.append({'items': json.loads(row[0])})
    return any(item.get('attempt_id') == attempt_id for record in snapshots for item in record['items'])


class BindingError(ValueError):
    """A Paper-bound import cannot proceed without writing anything."""


def _paper_for_binding(pool, paper_id):
    from workbench.data import practice_sets
    if not isinstance(paper_id, str) or not practice_sets.SAVED_ID.fullmatch(paper_id):
        raise BindingError("paper_id must name one saved Paper (ps-NNN)")
    try:
        paper = practice_sets.get_saved(pool, paper_id)
    except FileNotFoundError as exc:
        raise BindingError(f"unknown Paper: {paper_id}") from exc
    if paper["missing_problem_ids"]:
        raise BindingError(
            "Paper references unavailable problems: "
            + ", ".join(paper["missing_problem_ids"]))
    if paper["validation_errors"]:
        raise BindingError(
            "Paper validation failed: " + "; ".join(paper["validation_errors"]))
    return paper


def _binding_target(pool, paper):
    """Where this Paper's execution lives: active row, checkpoint, or nowhere."""
    paper_id = paper["practice_set_id"]
    conn = pool.connect()
    active = conn.execute(
        "SELECT * FROM active_practice WHERE singleton=1").fetchone()
    if active and active["source_ref"] == paper_id:
        previous = conn.row_factory
        try:
            conn.row_factory = sqlite3.Row
            items = [dict(row) for row in conn.execute(
                "SELECT * FROM active_practice_items ORDER BY position")]
        finally:
            conn.row_factory = previous
        if not items:
            raise BindingError("the selected Paper has no execution items")
        _require_continuation(paper, "selected Paper execution")
        return dict(mode="active", record=dict(active), items=items,
                    execution_id=active["execution_id"],
                    reveal_timing=active["reveal_timing"])
    checkpoint = state(conn, paper_id)["checkpoint_json"]
    if checkpoint:
        record = json.loads(checkpoint)
        items = record.get("items") or []
        if not items:
            raise BindingError("the parked Paper has no execution items")
        _require_continuation(paper, "parked Paper execution")
        return dict(mode="parked", record=record, items=items,
                    execution_id=record.get("execution_id"),
                    reveal_timing=record.get("reveal_timing"))
    return dict(mode="new", record=None, items=[], execution_id=None,
                reveal_timing="on_submit")


def _require_continuation(paper, label):
    continuation = paper.get("continuation")
    if continuation and continuation.get("available"):
        return
    reason = (continuation or {}).get("reason") or (
        f"{label} cannot be validated against the current Paper")
    raise BindingError(reason)


def _position_map(items):
    return {
        item["item_id"]: item["position"]
        for item in items
        if item.get("item_type", "problem") == "problem"
    }


def _progress(items):
    answered = sum(1 for item in items if item["state"] == "answered")
    stuck = sum(1 for item in items if item["state"] == "stuck")
    total = len(items)
    return dict(total=total, answered=answered, stuck=stuck,
                completed=answered + stuck, remaining=total - answered - stuck)


def _new_items(pool, paper):
    conn = pool.connect()
    return [
        dict(position=position, item_type="problem",
             item_id=item["problem_id"], direction="", state="pending",
             attempt_id=None, content_revision=revision(conn, item["problem_id"]))
        for position, item in enumerate(paper["plan"]["items"])
    ]


def _simulated(items, problem_ids):
    wanted = set(problem_ids)
    return [
        dict(item, state="answered") if item["item_id"] in wanted else item
        for item in items
    ]


def _next_cursor(items, current):
    pending = [item["position"] for item in items if item["state"] == "pending"]
    if not pending:
        return current
    return current if current in pending else pending[0]


def _import_draft(item):
    draft = dict(item.get("draft") or {})
    draft.pop("answer", None)
    draft.pop("choices", None)
    draft["stuck"] = False
    return draft


def preview_binding(pool, paper_id, problem_ids):
    """Describe a Paper-bound import without writing anything."""
    if not available(pool.connect()):
        raise BindingError(
            "this pool is not migrated for Paper progress — run the documented migration")
    paper = _paper_for_binding(pool, paper_id)
    target = _binding_target(pool, paper)
    items = _new_items(pool, paper) if target["mode"] == "new" else target["items"]
    positions = _position_map(items)
    missing = [problem_id for problem_id in problem_ids
               if problem_id not in positions]
    if missing:
        raise BindingError(
            "problem is not part of this Paper: " + ", ".join(missing))
    actions = {}
    rows = []
    for problem_id in problem_ids:
        item = items[positions[problem_id]]
        action = ("rebind" if item["state"] != "pending"
                  or item.get("attempt_id") is not None else "import")
        actions[problem_id] = action
        rows.append(dict(problem_id=problem_id, position=item["position"],
                         state=item["state"], attempt_id=item.get("attempt_id"),
                         action=action))
    progress_before = _progress(items)
    progress_after = _progress(_simulated(items, problem_ids))
    reveal = target["reveal_timing"]
    if progress_after["remaining"]:
        completion = "partial"
    elif target["mode"] == "active" and reveal is None:
        completion = "archive"
    elif target["mode"] == "parked":
        completion = "parked"
    else:
        completion = "wait_for_submit"
    return dict(
        paper_id=paper_id, title=paper["title"], mode=target["mode"],
        execution_id=target["execution_id"], reveal_timing=reveal,
        positions={problem_id: positions[problem_id] for problem_id in problem_ids},
        actions=actions, items=rows, progress_before=progress_before,
        progress_after=progress_after,
        would_complete=progress_after["remaining"] == 0,
        completion=completion,
    )


def bind_attempts(pool, paper_id, links):
    """Bind imported attempts to a Paper's active, parked, or new progress."""
    if not available(pool.connect()):
        raise BindingError(
            "this pool is not migrated for Paper progress — run the documented migration")
    paper = _paper_for_binding(pool, paper_id)
    target = _binding_target(pool, paper)
    problem_ids = [problem_id for problem_id, _ in links]
    items = _new_items(pool, paper) if target["mode"] == "new" else target["items"]
    positions = _position_map(items)
    missing = [problem_id for problem_id in problem_ids
               if problem_id not in positions]
    if missing:
        raise BindingError(
            "problem is not part of this Paper: " + ", ".join(missing))

    before = {item["item_id"]: item for item in items}
    rebound = [
        problem_id for problem_id in problem_ids
        if before[problem_id]["state"] != "pending"
        or before[problem_id].get("attempt_id") is not None
    ]
    actions = {
        problem_id: "rebind" if problem_id in rebound else "import"
        for problem_id in problem_ids
    }

    if target["mode"] == "active":
        from workbench.data import active_practice
        previous_states = {}
        for problem_id, attempt_id in links:
            previous_states[problem_id] = active_practice.bind_attempt(
                pool, positions[problem_id], attempt_id)
        finish = active_practice.finish_if_complete(pool)
        progress = _progress(_simulated(items, problem_ids))
        return dict(
            paper_id=paper_id, mode="active",
            execution_id=target["execution_id"],
            reveal_timing=target["reveal_timing"],
            positions={problem_id: positions[problem_id] for problem_id in problem_ids},
            actions=actions, progress=progress,
            completed=finish.get("completed", False),
            run_id=finish.get("run_id"), rebound=rebound,
            previous_states=previous_states,
        )

    conn = pool.connect()
    now = conn.execute("SELECT datetime('now')").fetchone()[0]
    if target["mode"] == "parked":
        record = target["record"]
        generation = state(conn, paper_id)["generation"]
        for problem_id, attempt_id in links:
            item = record["items"][positions[problem_id]]
            item["state"] = "answered"
            item["attempt_id"] = attempt_id
            item["content_revision"] = revision(conn, problem_id)
            if record.get("reveal_timing") in {"per_item", "on_submit"}:
                item["draft"] = _import_draft(item)
                item["draft_sequence"] = item.get("draft_sequence", 0) + 1
            else:
                item["draft"] = {}
                item["draft_sequence"] = 0
        record["paper_generation"] = generation
        record["cursor"] = _next_cursor(record["items"], record.get("cursor", 0))
        record["updated_at"] = now
        conn.execute(
            "UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?",
            (json.dumps(record, ensure_ascii=False), paper_id))
        return dict(
            paper_id=paper_id, mode="parked",
            execution_id=record.get("execution_id"),
            reveal_timing=record.get("reveal_timing"),
            positions={problem_id: positions[problem_id] for problem_id in problem_ids},
            actions=actions, progress=_progress(record["items"]),
            completed=False, run_id=None, rebound=rebound,
        )

    execution_id = conn.execute(
        "INSERT INTO practice_execution_ids DEFAULT VALUES").lastrowid
    generation = ensure_state(conn, paper_id)["generation"]
    items = _new_items(pool, paper)
    for problem_id, attempt_id in links:
        item = items[positions[problem_id]]
        item["state"] = "answered"
        item["attempt_id"] = attempt_id
        item["draft"] = {"stuck": False}
        item["draft_sequence"] = 1
    kp_ids = list(dict.fromkeys(
        knowledge_id
        for item in paper["plan"]["items"]
        for knowledge_id in (pool.problem(item["problem_id"]) or {}).get("kp_ids", [])
    ))
    record = dict(
        source_kind="paper", source_ref=paper_id,
        source_label=paper["title"], kp_ids=kp_ids,
        practice_mode="exam", rating_mode="immediate",
        cursor=_next_cursor(items, 0), started_at=now, updated_at=now,
        execution_id=execution_id, paper_generation=generation,
        reveal_timing="on_submit", items=items,
    )
    conn.execute(
        "UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?",
        (json.dumps(record, ensure_ascii=False), paper_id))
    return dict(
        paper_id=paper_id, mode="new", execution_id=execution_id,
        reveal_timing="on_submit",
        positions={problem_id: positions[problem_id] for problem_id in problem_ids},
        actions=actions, progress=_progress(items),
        completed=False, run_id=None, rebound=[],
    )


def attempt_paper(pool, attempt_id):
    """The Paper item currently linked to one attempt, if any."""
    if not available(pool.connect()):
        return None
    conn = pool.connect()
    active = conn.execute(
        "SELECT source_ref FROM active_practice WHERE singleton=1").fetchone()
    if active:
        row = conn.execute(
            "SELECT position,state FROM active_practice_items WHERE attempt_id=?",
            (attempt_id,)).fetchone()
        if row:
            return dict(paper_id=active["source_ref"], position=row["position"],
                        state=row["state"], mode="active")
    for row in conn.execute(
            "SELECT paper_id,checkpoint_json FROM paper_state "
            "WHERE checkpoint_json IS NOT NULL"):
        record = json.loads(row["checkpoint_json"])
        for item in record.get("items") or []:
            if item.get("attempt_id") == attempt_id:
                return dict(paper_id=row["paper_id"], position=item["position"],
                            state=item["state"], mode="parked")
    for row in conn.execute(
            "SELECT source_ref,items_json FROM practice_runs "
            "WHERE items_json IS NOT NULL"):
        for item in json.loads(row["items_json"] or "[]"):
            if item.get("attempt_id") == attempt_id:
                return dict(paper_id=row["source_ref"], position=item["position"],
                            state=item["state"], mode="archived")
    return None


def continuation(pool, paper_id, plan_items, validation_errors=()):
    """Compare saved Paper membership with its active or parked execution."""
    conn = pool.connect()
    if not available(conn):
        return None
    active = conn.execute('SELECT * FROM active_practice WHERE singleton=1').fetchone()
    if active and active['source_ref'] == paper_id:
        record = dict(active)
        record['items'] = [dict(row) for row in conn.execute(
            'SELECT position,item_type,item_id,state,content_revision FROM active_practice_items ORDER BY position')]
    else:
        checkpoint = state(conn, paper_id)['checkpoint_json']
        if not checkpoint:
            return None
        record = json.loads(checkpoint)

    expected = [('problem', item['problem_id']) for item in plan_items
                if isinstance(item, dict) and isinstance(item.get('problem_id'), str)]
    items = record['items']
    actual = [(item.get('item_type'), item.get('item_id')) for item in items]
    unavailable = []
    for item_type, item_id in expected + actual:
        present = (pool.problem(item_id) if item_type == 'problem'
                   else pool.card(item_id) if item_type == 'card' else None)
        if present is None and item_id not in unavailable:
            unavailable.append(item_id)

    progress = dict(total=len(items), completed=sum(item['state'] != 'pending' for item in items))
    reason = None
    if unavailable:
        reason = '当前试卷或旧执行引用了不可用题目，不能继续。'
    elif expected != actual:
        reason = '旧执行的题目名单或顺序与当前试卷不一致，不能继续。'
    elif validation_errors:
        reason = '当前试卷内容校验失败，不能继续：' + '；'.join(validation_errors)
    elif record.get('paper_generation') != state(conn, paper_id)['generation']:
        reason = '旧执行对应的试卷结构版本已过期，不能继续。'
    elif any(item.get('item_type') == 'problem'
             and item.get('content_revision', 1) != revision(conn, item['item_id'])
             for item in items):
        reason = '旧执行引用的题目作答内容已变化，不能继续。'
    return dict(available=reason is None, reason=reason, paper_count=len(plan_items),
                execution=dict(progress=progress, execution_id=record.get('execution_id'),
                               reveal_timing=record.get('reveal_timing')),
                unavailable_item_ids=unavailable)


def start_blocker(pool, paper_id):
    """Return why another saved Paper cannot start because the active one cannot park."""
    conn = pool.connect()
    if not available(conn):
        return None
    active = conn.execute('SELECT source_ref FROM active_practice WHERE singleton=1').fetchone()
    active_id = active['source_ref'] if active else None
    if not isinstance(active_id, str) or not active_id.startswith('ps-') or active_id == paper_id:
        return None
    from workbench.data import practice_sets
    if not practice_sets._saved_path(pool, active_id).is_file():
        return None
    try:
        current = practice_sets.get_saved(pool, active_id)
    except FileNotFoundError:
        return None
    status = current['continuation']
    if status and status['available'] and not current['validation_errors'] and not current['missing_problem_ids']:
        return None
    reason = (status or {}).get('reason') or '当前活动试卷执行状态无法验证。'
    return '当前活动试卷无法暂停，不能开始另一张试卷：' + reason


def remove_question(pool, problem_id):
    """Explicit deletion is the membership-edit exception: keep every other marker."""
    from workbench.data import active_practice, practice_sets
    conn = pool.connect()
    for record in practice_sets.list_saved(pool):
        items = record['plan']['items']
        remaining = [item for item in items if item['problem_id'] != problem_id]
        if len(remaining) == len(items):
            continue
        pid = record['practice_set_id']
        raw = dict(practice_set_id=pid, created_at=record['created_at'],
                   updated_at=practice_sets._timestamp(), plan={**record['plan'], 'items': remaining})
        ensure_state(conn, pid)
        conn.execute('UPDATE paper_state SET generation=generation+1 WHERE paper_id=?', (pid,))
        queue_file(pool, pid, raw)
    # Both active and parked snapshots use the same item-removal rule.
    def cleaned(record):
        old_cursor = record['cursor']
        old = record['items']
        record['items'] = [item for item in old if item['item_id'] != problem_id]
        removed_before = sum(item['item_id'] == problem_id for item in old[:old_cursor])
        record['cursor'] = max(0, min(old_cursor-removed_before, len(record['items'])-1))
        for index, item in enumerate(record['items']):
            item['position'] = index
        pid = record.get('source_ref')
        if pid:
            record['paper_generation'] = state(conn, pid)['generation']
        return record
    for row in conn.execute('SELECT paper_id,checkpoint_json FROM paper_state WHERE checkpoint_json IS NOT NULL').fetchall():
        record = cleaned(json.loads(row['checkpoint_json']))
        conn.execute('UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?',
                     (json.dumps(record, ensure_ascii=False) if record['items'] else None, row['paper_id']))
    active = active_practice.current(pool, resolve=False)
    if active and any(item['item_id'] == problem_id for item in active['items']):
        active_practice._delete(pool)
        active = cleaned(active)
        if active['items']:
            active_practice._restore(pool, active)
