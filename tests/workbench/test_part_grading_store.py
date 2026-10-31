import pytest

from workbench.data.pool import Pool
from workbench.data import part_grading as store
from workbench.domain import part_grading as rules


@pytest.fixture
def pool(tmp_path):
    pool = Pool(tmp_path, tmp_path / 'pool.db', 'test', 'ch01')
    conn = pool.connect()
    conn.execute('CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY, problem_id TEXT, part_id TEXT, content_revision INTEGER, answer_text TEXT, status TEXT)')
    conn.execute("INSERT INTO problem_attempts VALUES (1,'p','a',2,'original response','submitted')")
    store.ensure_schema(conn)
    conn.commit()
    yield pool
    pool.close()


def write(pool, **changes):
    args = dict(attempt_id=1, problem_id='p', part_id='a', content_revision=2,
                expected_revision=0, operation_id='op1',
                payload={'answer_conclusion': 'correct', 'process_conclusion': 'wrong'},
                validate=rules.validate)
    args.update(changes)
    return store.mutate(pool, **args)


def test_revisions_retry_withdraw_and_immutable_attempt(pool):
    before = dict(pool.connect().execute('SELECT * FROM problem_attempts').fetchone())
    first = write(pool)
    assert write(pool) == first
    second = write(pool, operation_id='op2', expected_revision=1,
                   payload={'process_conclusion': 'partially_correct'})
    assert second['revision'] == 2
    withdrawn = write(pool, operation_id='op3', expected_revision=2, withdraw=True, payload=None)
    assert withdrawn['withdrawn'] and withdrawn['payload'] is None
    assert len(store.list_revisions(pool, 1)) == 3
    assert dict(pool.connect().execute('SELECT * FROM problem_attempts').fetchone()) == before
    assert rules.reveal(first) is None
    assert rules.reveal(first, True) == first


def test_conflicts_rollback_without_revision(pool):
    write(pool)
    for args in [dict(operation_id='op2'), dict(payload={'process_conclusion': 'wrong'}),
                 dict(operation_id='op2', expected_revision=1, part_id='other'),
                 dict(operation_id='op2', expected_revision=1,
                      actual_content_revision=lambda conn, problem: 3)]:
        with pytest.raises(ValueError):
            write(pool, **args)
    assert len(store.list_revisions(pool, 1)) == 1


@pytest.mark.parametrize('args', [dict(attempt_id=True), dict(expected_revision=True),
    dict(content_revision=True), dict(part_id=''), dict(problem_id=''), dict(withdraw=1)])
def test_invalid_target_types(pool, args):
    with pytest.raises(ValueError):
        write(pool, **args)
    assert store.get(pool, 1) is None


@pytest.mark.parametrize('payload', [{}, {'overall': 'correct'},
    {'answer_conclusion': []}, {'process_conclusion': 'failed'},
    {'answer_conclusion': 'unprovided', 'extracted_answer': 'invented'}])
def test_invalid_payload_before_write(pool, payload):
    with pytest.raises(ValueError):
        write(pool, payload=payload)
    assert store.list_revisions(pool, 1) == []


def test_proof_process_only():
    assert rules.validate({'process_conclusion': 'correct'}, answering_type='proof')
    for payload in [{'extracted_answer': 'QED'}, {'answer_conclusion': 'correct'}]:
        with pytest.raises(ValueError):
            rules.validate(payload, answering_type='proof')
