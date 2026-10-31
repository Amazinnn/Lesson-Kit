"""Atomic append-only grading revisions; never changes Attempts or learning state."""

import json


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS part_grading_revisions (
        attempt_id INTEGER NOT NULL, revision INTEGER NOT NULL,
        operation_id TEXT NOT NULL UNIQUE, request_json TEXT NOT NULL,
        payload_json TEXT, withdrawn INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY(attempt_id, revision))''')


def _decode(row):
    if row is None:
        return None
    value = dict(row)
    value['payload'] = json.loads(value.pop('payload_json')) if value['payload_json'] else None
    value.pop('request_json')
    value['withdrawn'] = bool(value['withdrawn'])
    return value


def get(pool, attempt_id):
    return _decode(pool.connect().execute(
        'SELECT * FROM part_grading_revisions WHERE attempt_id=? ORDER BY revision DESC LIMIT 1',
        (attempt_id,)).fetchone())


def list_revisions(pool, attempt_id):
    return [_decode(row) for row in pool.connect().execute(
        'SELECT * FROM part_grading_revisions WHERE attempt_id=? ORDER BY revision', (attempt_id,))]


def mutate(pool, *, attempt_id, problem_id, part_id, content_revision,
           expected_revision, operation_id, payload=None, withdraw=False, validate):
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise ValueError('operation identity required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid expected revision')
    if withdraw and payload is not None:
        raise ValueError('withdrawal cannot carry grading')
    checked = None if withdraw else validate(payload)
    request = json.dumps([attempt_id, problem_id, part_id, content_revision,
                          expected_revision, checked, withdraw], sort_keys=True)
    with pool.transaction(immediate=True):
        conn = pool.connect()
        previous = conn.execute('SELECT * FROM part_grading_revisions WHERE operation_id=?',
                                (operation_id,)).fetchone()
        if previous:
            if previous['request_json'] != request:
                raise ValueError('operation identity conflict')
            return _decode(previous)
        attempt = conn.execute('SELECT * FROM problem_attempts WHERE id=?', (attempt_id,)).fetchone()
        if attempt is None or any(attempt[key] != value for key, value in (
                ('problem_id', problem_id), ('part_id', part_id), ('content_revision', content_revision))):
            raise ValueError('Attempt target mismatch')
        current = get(pool, attempt_id)
        if (current['revision'] if current else 0) != expected_revision:
            raise ValueError('stale grading revision')
        if withdraw and (not current or current['withdrawn']):
            raise ValueError('no current grading')
        conn.execute('INSERT INTO part_grading_revisions '
                     '(attempt_id,revision,operation_id,request_json,payload_json,withdrawn) VALUES (?,?,?,?,?,?)',
                     (attempt_id, expected_revision + 1, operation_id, request,
                      json.dumps(checked) if checked is not None else None, int(withdraw)))
        return get(pool, attempt_id)
