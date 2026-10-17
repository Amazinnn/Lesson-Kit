import sqlite3
import pytest
from tests.workbench.test_schema_migration import pool_schema


def fixture(fk, broken=False, missing=False):
    conn = sqlite3.connect(':memory:')
    conn.executescript('''
        CREATE TABLE problems(problem_id TEXT PRIMARY KEY);
        INSERT INTO problems VALUES ('p1');
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL REFERENCES problems(problem_id),
            status TEXT CHECK(status IN ('new', 'wrong', 'stuck', 'reviewing', 'mastered')),
            extra TEXT NOT NULL DEFAULT 'retained');
        INSERT INTO problem_attempts VALUES (7, 'p1', 'stuck', 'original');
        INSERT INTO problem_attempts VALUES (50, 'p1', 'wrong', 'deleted');
        DELETE FROM problem_attempts WHERE id=50;
        CREATE TABLE child(id INTEGER PRIMARY KEY, attempt_id REFERENCES problem_attempts(id), note TEXT);
        INSERT INTO child VALUES (3, 7, 'draft');
        CREATE TABLE second_child(id INTEGER PRIMARY KEY, attempt_id REFERENCES problem_attempts(id));
        INSERT INTO second_child VALUES (4, 7);
        CREATE TABLE grandchild(id INTEGER REFERENCES child(id));
        INSERT INTO grandchild VALUES (3);
        CREATE INDEX custom_attempt_index ON problem_attempts(extra);
        CREATE INDEX custom_child_index ON child(note);
        CREATE TABLE audit(note TEXT);
        CREATE TRIGGER child_update AFTER UPDATE ON child BEGIN INSERT INTO audit VALUES (new.note); END;
        CREATE VIEW attempts_view AS SELECT extra FROM problem_attempts;
    ''')
    if broken:
        conn.execute('ALTER TABLE problem_attempts RENAME TO problem_attempts_widening_old')
        conn.execute("CREATE TABLE problem_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, problem_id TEXT NOT NULL REFERENCES problems(problem_id), status TEXT CHECK(status IN ('new', 'answered', 'wrong', 'stuck', 'reviewing', 'mastered')), extra TEXT NOT NULL DEFAULT 'retained')")
        conn.execute('INSERT INTO problem_attempts SELECT * FROM problem_attempts_widening_old')
        conn.execute('DROP TABLE problem_attempts_widening_old')
        conn.execute("UPDATE sqlite_sequence SET seq=50 WHERE name='problem_attempts'")
    if missing:
        conn.execute('DELETE FROM problem_attempts')
    conn.commit()
    conn.execute(f'PRAGMA foreign_keys={fk}')
    return conn


@pytest.mark.parametrize('fk', [0, 1])
@pytest.mark.parametrize('broken', [False, True])
def test_preserves_attempts_inbound_rows_and_schema(fk, broken):
    conn = fixture(fk, broken)
    before = {t: conn.execute(f'SELECT * FROM {t}').fetchall()
              for t in ('problem_attempts', 'child', 'second_child', 'grandchild', 'audit')}
    objects = conn.execute("SELECT name, sql FROM sqlite_master WHERE type IN ('index','trigger') AND sql IS NOT NULL ORDER BY name").fetchall()
    pool_schema._widen_problem_attempts_status_check(conn)
    for table, rows in before.items():
        assert conn.execute(f'SELECT * FROM {table}').fetchall() == rows
    assert conn.execute("SELECT name, sql FROM sqlite_master WHERE type IN ('index','trigger') AND sql IS NOT NULL ORDER BY name").fetchall() == objects
    for table in ('child', 'second_child'):
        assert conn.execute(f'PRAGMA foreign_key_list({table})').fetchone()[2] == 'problem_attempts'
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == fk
    assert not conn.in_transaction
    snapshot = list(conn.iterdump())
    assert pool_schema._widen_problem_attempts_status_check(conn) == []
    assert list(conn.iterdump()) == snapshot
    conn.execute("INSERT INTO problem_attempts(problem_id, status) VALUES ('p1', 'answered')")
    assert conn.execute('SELECT max(id) FROM problem_attempts').fetchone()[0] == 51
    conn.close()


def test_missing_parent_is_reported_without_discarding_child():
    conn = fixture(1, broken=True, missing=True)
    with pytest.warns(RuntimeWarning, match='child.*7'):
        pool_schema._widen_problem_attempts_status_check(conn)
    assert conn.execute('SELECT * FROM problem_attempts').fetchall() == []
    assert conn.execute('SELECT * FROM child').fetchall() == [(3, 7, 'draft')]
    assert len(conn.execute('PRAGMA foreign_key_check').fetchall()) == 2


@pytest.mark.parametrize('fk', [0, 1])
def test_does_not_commit_callers_transaction(fk):
    conn = fixture(fk)
    conn.execute("INSERT INTO audit VALUES ('uncommitted')")
    if fk:
        with pytest.raises(sqlite3.OperationalError, match='no active transaction'):
            pool_schema._widen_problem_attempts_status_check(conn)
    else:
        pool_schema._widen_problem_attempts_status_check(conn)
    assert conn.in_transaction
    conn.rollback()
    assert conn.execute('SELECT * FROM audit').fetchall() == []
    assert 'answered' not in conn.execute("SELECT sql FROM sqlite_master WHERE name='problem_attempts'").fetchone()[0]
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == fk

@pytest.mark.parametrize('fk', [0, 1])
def test_rebuild_failure_restores_schema_rows_and_settings(fk):
    conn = fixture(fk)
    before = list(conn.iterdump())
    conn.execute('PRAGMA legacy_alter_table=ON')
    conn.set_authorizer(lambda action, *args: sqlite3.SQLITE_DENY
                        if action == sqlite3.SQLITE_DROP_TABLE else sqlite3.SQLITE_OK)
    with pytest.raises(sqlite3.DatabaseError, match='authorized'):
        pool_schema._widen_problem_attempts_status_check(conn)
    conn.set_authorizer(None)
    assert list(conn.iterdump()) == before
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == fk
    assert conn.execute('PRAGMA legacy_alter_table').fetchone()[0] == 1
    assert not conn.in_transaction


def test_unconstrained_legacy_status_needs_no_rebuild():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE problem_attempts(id INTEGER PRIMARY KEY, status TEXT)')
    before = list(conn.iterdump())
    assert pool_schema._widen_problem_attempts_status_check(conn) == []
    assert list(conn.iterdump()) == before


def test_public_ensure_repairs_existing_child_and_survives_reopen(tmp_path):
    from tests.workbench.test_schema_migration import build_old_schema_db
    path = tmp_path / 'isolated.db'
    conn = sqlite3.connect(path)
    build_old_schema_db(conn)
    pool_schema.ensure_workbench_schema(conn)
    conn.commit()
    conn.execute('CREATE TABLE preserved_child(id INTEGER PRIMARY KEY, attempt_id REFERENCES problem_attempts_widening_old(id))')
    conn.execute('INSERT INTO preserved_child VALUES (1, 1)')
    conn.commit()
    attempts = conn.execute('SELECT * FROM problem_attempts').fetchall()
    changes = pool_schema.ensure_workbench_schema(conn)
    assert 'preserved_child.attempt_foreign_key' in changes
    conn.commit()
    conn.close()
    conn = sqlite3.connect(path)
    assert conn.execute('SELECT * FROM problem_attempts').fetchall() == attempts
    assert conn.execute('SELECT * FROM preserved_child').fetchall() == [(1, 1)]
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    assert pool_schema.ensure_workbench_schema(conn) == []
    conn.close()

def test_reference_repair_does_not_rewrite_literal_defaults():
    conn = fixture(0, broken=True)
    conn.execute("ALTER TABLE child ADD COLUMN guidance TEXT DEFAULT 'REFERENCES problem_attempts_widening_old'")
    before = conn.execute('PRAGMA table_info(child)').fetchall()
    pool_schema._widen_problem_attempts_status_check(conn)
    assert conn.execute('PRAGMA table_info(child)').fetchall() == before

def test_existing_migration_command_repairs_an_isolated_pool(tmp_path):
    import subprocess
    import sys
    from tests.workbench.test_schema_migration import build_old_schema_db, REPO_ROOT
    path = tmp_path / 'command-copy.db'
    conn = sqlite3.connect(path)
    build_old_schema_db(conn)
    pool_schema.ensure_workbench_schema(conn)
    conn.execute('CREATE TABLE saved_checkpoint(attempt_id REFERENCES problem_attempts_widening_old(id))')
    conn.execute('INSERT INTO saved_checkpoint VALUES (1)')
    conn.commit()
    before = conn.execute('SELECT * FROM problem_attempts').fetchall()
    conn.close()
    result = subprocess.run([sys.executable, str(REPO_ROOT / 'pool/scripts/migrate-progress.py'),
                             '--db', str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'saved_checkpoint.attempt_foreign_key' in result.stdout
    conn = sqlite3.connect(path)
    assert conn.execute('SELECT * FROM problem_attempts').fetchall() == before
    assert conn.execute('SELECT * FROM saved_checkpoint').fetchall() == [(1,)]
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    conn.close()
