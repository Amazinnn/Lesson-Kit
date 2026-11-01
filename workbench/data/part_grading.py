"""Atomic append-only grading revisions; never changes Attempts or learning state."""

import json

TABLES = ("part_attempt_context", "part_grading_revisions", "part_grading_jobs")
MIGRATION_HINT = "python pool/scripts/migrate-progress.py --db <池路径>"


class SchemaMissing(ValueError):
    """This pool never received the additive part-grading migration."""


def missing_schema(conn):
    """Every additive migration piece this pool lacks; empty when fully ready.

    ``problems.parts`` is the authoring column: grading storage does not need it,
    so ``has_schema`` stays tables-only while diagnostics still report the gap.
    """
    names = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    missing = [table for table in TABLES if table not in names]
    columns = {row[1] for row in conn.execute("PRAGMA table_info(problems)")}
    if "parts" not in columns:
        missing.append("problems.parts")
    return missing


def _ready_tables(pool):
    cached = getattr(pool, "_part_grading_tables", None)
    if cached is None:
        cached = {row[0] for row in pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        pool._part_grading_tables = cached
    return cached


def has_revisions(pool):
    """The revisions table alone — what the append-only store needs."""
    return "part_grading_revisions" in _ready_tables(pool)


def has_schema(pool):
    """Whether this pool has the full additive grading storage (per-request cache)."""
    return all(table in _ready_tables(pool) for table in TABLES)


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
    if not has_revisions(pool):
        return None
    return _decode(pool.connect().execute(
        'SELECT * FROM part_grading_revisions WHERE attempt_id=? ORDER BY revision DESC LIMIT 1',
        (attempt_id,)).fetchone())


def list_revisions(pool, attempt_id):
    if not has_revisions(pool):
        return []
    return [_decode(row) for row in pool.connect().execute(
        'SELECT * FROM part_grading_revisions WHERE attempt_id=? ORDER BY revision', (attempt_id,))]


def mutate(pool, *, attempt_id, problem_id, part_id, content_revision,
           expected_revision, operation_id, payload=None, withdraw=False, validate,
           actual_content_revision=None):
    if type(attempt_id) is not int or attempt_id <= 0:
        raise ValueError('invalid Attempt identity')
    if not isinstance(problem_id, str) or not problem_id.strip():
        raise ValueError('invalid problem identity')
    if part_id is not None and (not isinstance(part_id, str) or not part_id.strip()):
        raise ValueError('invalid part identity')
    if content_revision is not None and (type(content_revision) is not int or content_revision < 1):
        raise ValueError('invalid content revision')
    if type(withdraw) is not bool:
        raise ValueError('withdraw must be boolean')
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
        if actual_content_revision is not None:
            actual = actual_content_revision(conn, problem_id)
            if type(actual) is not int or actual != content_revision:
                raise ValueError('stale content revision')
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
