"""Durable job state, separate from immutable learner submissions."""

import json


def owns_conversation(pool, conversation_id):
    conn = pool.connect()
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='part_grading_jobs'").fetchone():
        return False
    return conn.execute('SELECT 1 FROM part_grading_jobs WHERE conversation_id=?',
                        (conversation_id,)).fetchone() is not None


def target(pool, attempt_id):
    if type(attempt_id) is not int or attempt_id < 1:
        raise ValueError('invalid Attempt identity')
    row = pool.connect().execute('SELECT a.*,c.part_json,c.execution_id FROM problem_attempts a '
        'JOIN part_attempt_context c ON c.attempt_id=a.id WHERE a.id=?', (attempt_id,)).fetchone()
    if not row:
        raise ValueError('saved part Attempt not found')
    value = dict(row)
    value['part'] = json.loads(value.pop('part_json'))
    return value

def get(pool, attempt_id):
    row = pool.connect().execute('SELECT * FROM part_grading_jobs WHERE attempt_id=?', (attempt_id,)).fetchone()
    return dict(row) if row else None


def update(pool, attempt_id, status, error=None, conversation_id=None, turn_id=None):
    if status not in {'pending', 'running', 'completed', 'failed'}:
        raise ValueError('invalid grading job status')
    with pool.transaction(immediate=True):
        pool.connect().execute('UPDATE part_grading_jobs SET status=?,error=?, '
            'conversation_id=COALESCE(?,conversation_id),turn_id=COALESCE(?,turn_id),'
            "updated_at=datetime('now') WHERE attempt_id=? AND (status!='completed' OR ?='completed')",
            (status, error, conversation_id, turn_id, attempt_id, status))
    return get(pool, attempt_id)


def pending(pool):
    return [dict(row) for row in pool.connect().execute(
        "SELECT * FROM part_grading_jobs WHERE status IN ('pending','running') ORDER BY attempt_id")]


def retry(pool, attempt_id):
    with pool.transaction(immediate=True):
        pool.connect().execute("UPDATE part_grading_jobs SET status='pending',error=NULL,"
            "conversation_id=NULL,turn_id=NULL,updated_at=datetime('now') WHERE attempt_id=? AND status='failed'",
            (attempt_id,))
    return get(pool, attempt_id)
