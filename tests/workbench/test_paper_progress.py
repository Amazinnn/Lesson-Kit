"""Saved Paper independence, update boundaries and historical preservation."""

import pytest

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import active_practice, practice_sets, content, attempts
from workbench.server import api


@pytest.fixture
def pool():
    fixture = WorkspaceFixture()
    p = api._pool_for(dict(path=str(fixture.ws), db='pool/dmath.db',
                          active_course='dmath', active_chapter='ch06'))
    for index in (2, 3):
        p.connect().execute(
            "INSERT INTO problems(problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
            " VALUES (?, ?, ?, 'solution', 'calculation', 'textbook')",
            (f'dmath-ch06-prob-00{index}', '["dmath-ch06-kp-001"]', f'question {index}'))
    p.commit()
    yield p
    p.close()
    fixture.cleanup()


Q = 'dmath-ch06-prob-001'
R = 'dmath-ch06-prob-002'


def paper(pool, title, ids):
    return practice_sets.create_saved(pool, title, ids)['practice_set_id']


def start(pool, paper_id):
    return active_practice.start_saved(pool, paper_id, rating_mode='off')


def evidence(pool):
    return {t: [tuple(r) for r in pool.connect().execute('SELECT * FROM '+t)]
            for t in ('problem_attempts','problem_progress','feedback_events',
                      'review_schedule','learning_current_state','learner_signals')}


def test_switch_keeps_both_progress_drafts_and_rating_preference(pool):
    a = paper(pool, 'A', [Q, R]); b = paper(pool, 'B', [Q, R])
    first = start(pool, a)
    active_practice.mark(pool, 0, 'stuck')
    active_practice.save_draft(pool, first['execution_id'], 1,
                               dict(answer='unfinished', choices=[]))
    before = evidence(pool)
    start(pool, b)
    resumed = active_practice.start_saved(pool, a, rating_mode='batch')
    assert resumed['execution_id'] == first['execution_id']
    assert resumed['cursor'] == 1
    assert resumed['rating_mode'] == 'off'
    assert resumed['items'][0]['state'] == 'stuck'
    assert resumed['items'][1]['draft']['answer'] == 'unfinished'
    assert evidence(pool) == before
    assert pool.connect().execute('SELECT COUNT(*) FROM practice_runs').fetchone()[0] == 0
    assert practice_sets.get_saved(pool, a)['continuation']['available'] is True
    assert practice_sets.get_saved(pool, a)['progress'] == {'total': 2, 'completed': 1}


def test_saved_read_does_not_attach_count_mismatched_execution(pool):
    paper_id = paper(pool, 'A', [Q, R])
    active = start(pool, paper_id)
    active_practice.mark(pool, 0, 'stuck')
    pool.connect().execute(
        "INSERT INTO active_practice_items(position,item_type,item_id,direction,state,"
        "attempt_id,content_revision,draft_json,draft_sequence) "
        "VALUES (2,'problem',?,'','pending',NULL,1,'{}',0)", ('dmath-ch06-prob-003',))
    pool.commit()

    saved = practice_sets.get_saved(pool, paper_id)
    current = active_practice.current(pool)

    assert saved['count'] == 2
    assert saved['progress'] is None
    assert saved['continuation']['available'] is False
    assert '名单或顺序' in saved['continuation']['reason']
    assert saved['continuation']['execution']['progress'] == {'total': 3, 'completed': 1}
    assert current['continuation'] == saved['continuation']
    assert current['execution_id'] == active['execution_id']
    before_items = [tuple(row) for row in pool.connect().execute(
        'SELECT * FROM active_practice_items ORDER BY position')]
    before_evidence = evidence(pool)
    with pytest.raises(active_practice.ActivePracticeConflict, match='名单或顺序'):
        start(pool, paper_id)
    assert [tuple(row) for row in pool.connect().execute(
        'SELECT * FROM active_practice_items ORDER BY position')] == before_items
    assert evidence(pool) == before_evidence


def test_same_count_with_different_order_is_not_continuable(pool):
    paper_id = paper(pool, 'A', [Q, R])
    start(pool, paper_id)
    conn = pool.connect()
    conn.execute('UPDATE active_practice_items SET item_id=? WHERE position=0', ('dmath-ch06-prob-003',))
    conn.execute('UPDATE active_practice_items SET item_id=? WHERE position=1', (Q,))
    conn.execute('UPDATE active_practice_items SET item_id=? WHERE position=0', (R,))
    pool.commit()

    saved = practice_sets.get_saved(pool, paper_id)

    assert saved['count'] == saved['continuation']['execution']['progress']['total'] == 2
    assert saved['progress'] is None
    assert '名单或顺序' in saved['continuation']['reason']
    with pytest.raises(active_practice.ActivePracticeConflict, match='名单或顺序'):
        start(pool, paper_id)


def test_same_count_with_changed_available_id_is_not_continuable(pool):
    paper_id = paper(pool, 'A', [Q, R])
    start(pool, paper_id)
    pool.connect().execute('UPDATE active_practice_items SET item_id=? WHERE position=0',
                           ('dmath-ch06-prob-003',))
    pool.commit()

    saved = practice_sets.get_saved(pool, paper_id)
    current = active_practice.current(pool)

    assert saved['count'] == saved['continuation']['execution']['progress']['total'] == 2
    assert saved['continuation']['unavailable_item_ids'] == []
    assert saved['continuation']['available'] is False
    assert current['continuation'] == saved['continuation']
    assert saved['progress'] is None
    with pytest.raises(active_practice.ActivePracticeConflict, match='名单或顺序'):
        start(pool, paper_id)


def test_unavailable_execution_item_is_reported_without_repairing_history(pool):
    paper_id = paper(pool, 'A', [Q, R])
    active = start(pool, paper_id)
    active_practice.mark(pool, 0, 'stuck')
    before = [tuple(row) for row in pool.connect().execute(
        'SELECT * FROM active_practice_items ORDER BY position')]

    pool.connect().execute('DELETE FROM problems WHERE problem_id=?', (Q,))
    pool.commit()

    saved = practice_sets.get_saved(pool, paper_id)
    current = active_practice.current(pool)
    assert saved['continuation']['available'] is False
    assert saved['continuation']['unavailable_item_ids'] == [Q]
    assert '不可用题目' in saved['continuation']['reason']
    assert saved['progress'] is None
    assert current['continuation'] == saved['continuation']
    with pytest.raises(active_practice.ActivePracticeError, match='题目不可用'):
        start(pool, paper_id)
    assert [tuple(row) for row in pool.connect().execute(
        'SELECT * FROM active_practice_items ORDER BY position')] == before
    assert current['execution_id'] == active['execution_id']


def test_active_execution_generation_and_content_revision_are_revalidated(pool):
    paper_id = paper(pool, 'A', [Q, R])
    start(pool, paper_id)
    assert practice_sets.get_saved(pool, paper_id)['continuation']['available'] is True

    pool.connect().execute('UPDATE paper_state SET generation=generation+1 WHERE paper_id=?', (paper_id,))
    pool.commit()
    status = practice_sets.get_saved(pool, paper_id)['continuation']
    assert status['available'] is False
    assert '结构版本' in status['reason']
    with pytest.raises(active_practice.ActivePracticeConflict, match='结构版本'):
        start(pool, paper_id)

    pool.connect().execute('UPDATE paper_state SET generation=generation-1 WHERE paper_id=?', (paper_id,))
    pool.connect().execute('INSERT INTO problem_revisions(problem_id,revision) VALUES (?,2) '
                           'ON CONFLICT(problem_id) DO UPDATE SET revision=2', (Q,))
    pool.commit()
    status = practice_sets.get_saved(pool, paper_id)['continuation']
    assert status['available'] is False
    assert '作答内容已变化' in status['reason']
    with pytest.raises(active_practice.ActivePracticeConflict, match='作答内容已变化'):
        start(pool, paper_id)


def test_parked_execution_mismatch_stays_visible_and_blocks_resume(pool):
    a = paper(pool, 'A', [Q, R])
    b = paper(pool, 'B', [Q, R])
    start(pool, a)
    start(pool, b)
    checkpoint = practice_sets.get_saved(pool, a)['continuation']
    assert checkpoint['available'] is True
    record = __import__('json').loads(
        pool.connect().execute('SELECT checkpoint_json FROM paper_state WHERE paper_id=?', (a,)).fetchone()[0])
    record['items'][1]['item_id'] = 'dmath-ch06-prob-003'
    pool.connect().execute('UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?',
                           (__import__('json').dumps(record), a))
    pool.commit()

    saved = practice_sets.get_saved(pool, a)
    assert saved['continuation']['available'] is False
    assert saved['progress'] is None
    with pytest.raises(active_practice.ActivePracticeConflict, match='名单或顺序'):
        start(pool, a)
    assert active_practice.current(pool)['source_ref'] == b
    assert practice_sets.get_saved(pool, a)['continuation']['execution']['progress']['total'] == 2


def test_metadata_preserves_progress_structure_requires_confirmed_preview(pool):
    a = paper(pool, 'A', [Q, R]); run = start(pool, a)
    active_practice.mark(pool, 0, 'stuck')
    practice_sets.update_saved(pool, a, title='renamed')
    assert active_practice.current(pool)['execution_id'] == run['execution_id']
    before = evidence(pool)
    preview = practice_sets.preview_update(pool, a, problem_ids=[R, Q])
    assert preview['resets_progress'] and preview['completed_items'] == 1
    with pytest.raises(ValueError, match='confirm'):
        practice_sets.update_saved(pool, a, problem_ids=[R, Q])
    assert active_practice.current(pool)['items'][0]['item_id'] == Q
    practice_sets.update_saved(pool, a, problem_ids=[R, Q], confirmation=preview['confirmation'])
    assert active_practice.current(pool) is None
    assert practice_sets.get_saved(pool, a)['practice_set_id'] == a
    assert evidence(pool) == before


def test_semantic_edit_resets_shared_item_only_and_rejects_old_submit(pool):
    a = paper(pool, 'A', [Q, R, 'dmath-ch06-prob-003']); b = paper(pool, 'B', [Q, R, 'dmath-ch06-prob-003'])
    first = start(pool, a)
    old_token = active_practice.submission_context(first, 0)
    active_practice.mark(pool, 0, 'stuck')
    active_practice.mark(pool, 1, 'stuck')
    # Start an unfinished second execution, preserving historical attempts below.
    start(pool, b)
    active_practice.mark(pool, 0, 'stuck')
    before = evidence(pool)
    content.update(pool, 'problem', Q, dict(problem_text='corrected stem'))
    resumed = start(pool, b)
    assert resumed['items'][0]['state'] == 'pending'
    assert resumed['items'][1]['state'] == 'pending'
    with pytest.raises(ValueError, match='stale'):
        attempts.record_browser_attempt(pool, Q, answer_text='old',
                                        request_id='stale-request', practice_position=0,
                                        practice_context=old_token)
    a_resumed = start(pool, a)
    assert a_resumed['items'][0]['state'] == 'pending'
    assert a_resumed['items'][1]['state'] == 'stuck'
    assert evidence(pool) == before


def test_delete_question_cleans_memberships_but_preserves_history_and_other_progress(pool):
    a = paper(pool, 'A', [Q, R]); b = paper(pool, 'B', [Q, R])
    start(pool, a); active_practice.mark(pool, 0, 'stuck')
    start(pool, b); active_practice.mark(pool, 0, 'stuck')
    attempts.record_browser_attempt(pool, Q, answer_text='historical')
    before = evidence(pool)
    content.delete(pool, 'problem', Q)
    assert pool.problem(Q) is None
    assert evidence(pool) == before
    for pid in (a, b):
        assert [i['problem_id'] for i in practice_sets.get_saved(pool, pid)['plan']['items']] == [R]
        assert start(pool, pid)['items'][0]['item_id'] == R


def test_invalid_and_empty_containers_remain_manageable(pool):
    a = paper(pool, 'A', [Q])
    pool.connect().execute('DELETE FROM problems WHERE problem_id=?', (Q,)); pool.commit()
    assert len(practice_sets.list_saved(pool)) == 1
    assert practice_sets.get_saved(pool, a)['missing_problem_ids'] == [Q]
    with pytest.raises(ValueError, match='题目不可用'):
        start(pool, a)
    practice_sets.delete_saved(pool, a)
    assert practice_sets.list_saved(pool) == []


def test_paper_file_publication_failure_recovers_without_losing_progress_rules(pool, monkeypatch):
    a = paper(pool, 'A', [Q, R]); start(pool, a)
    preview = practice_sets.preview_update(pool, a, problem_ids=[R])
    original = practice_sets._atomic_json
    monkeypatch.setattr(practice_sets, '_atomic_json', lambda *args: (_ for _ in ()).throw(OSError('disk full')))
    with pytest.raises(OSError, match='disk full'):
        practice_sets.update_saved(pool, a, problem_ids=[R], confirmation=preview['confirmation'])
    monkeypatch.setattr(practice_sets, '_atomic_json', original)
    assert [i['problem_id'] for i in practice_sets.get_saved(pool, a)['plan']['items']] == [R]
    assert active_practice.current(pool) is None


def test_draft_sequence_and_preview_token_reject_late_writes(pool):
    a = paper(pool, 'A', [Q, R]); run = start(pool, a)
    token = active_practice.submission_context(run, 0)
    preview = practice_sets.preview_update(pool, a, problem_ids=[R, Q])
    active_practice.save_draft(pool, run['execution_id'], 0, {'answer': 'new'}, context=token, sequence=20)
    with pytest.raises(ValueError, match='stale'):
        active_practice.save_draft(pool, run['execution_id'], 0, {'answer': 'old'}, context=token, sequence=19)
    with pytest.raises(ValueError, match='confirm'):
        practice_sets.update_saved(pool, a, problem_ids=[R, Q], confirmation=preview['confirmation'])
    assert active_practice.current(pool)['items'][0]['draft'] == {'answer': 'new'}


def test_metadata_and_noop_preserve_drafts_and_content_revision(pool):
    a = paper(pool, 'A', [Q, R]); run = start(pool, a)
    token = active_practice.submission_context(run, 0)
    active_practice.save_draft(pool, run['execution_id'], 0, {'answer': 'draft'}, context=token)
    before = evidence(pool)
    content.update(pool, 'problem', Q, {'solution': 'updated explanation'})
    practice_sets.update_saved(pool, a, problem_ids=[Q, R], description='notes')
    current = active_practice.current(pool)
    assert current['items'][0]['draft'] == {'answer': 'draft'}
    assert active_practice.submission_context(current, 0) == token
    assert evidence(pool) == before


def test_delete_shared_question_preserves_other_completed_item_and_empty_container(pool):
    from workbench.data import records
    a = paper(pool, 'A', [R, Q, 'dmath-ch06-prob-003']); b = paper(pool, 'B', [Q])
    start(pool, a); active_practice.mark(pool, 0, 'stuck')
    attempts.record_browser_attempt(pool, Q, answer_text='historical')
    before = evidence(pool)
    content.delete(pool, 'problem', Q)
    assert start(pool, a)['items'][0]['state'] == 'stuck'
    assert practice_sets.get_saved(pool, b)['count'] == 0
    with pytest.raises(ValueError, match='empty'):
        start(pool, b)
    assert records.overview(pool)['records'][0]['deleted_content']
    assert evidence(pool) == before


def test_delete_container_keeps_other_paper_and_question_evidence(pool):
    a = paper(pool, 'A', [Q, R]); b = paper(pool, 'B', [Q, R])
    run = start(pool, a); token = active_practice.submission_context(run, 0)
    start(pool, b); active_practice.mark(pool, 0, 'stuck')
    before = evidence(pool)
    practice_sets.delete_saved(pool, a)
    assert active_practice.current(pool)['source_ref'] == b
    assert pool.problem(Q) is not None
    with pytest.raises(ValueError, match='stale'):
        attempts.record_browser_attempt(pool, Q, answer_text='stale', practice_position=0,
                                        practice_context=token, request_id='deleted-container')
    assert evidence(pool) == before


def test_stale_generation_cannot_be_bypassed_by_omitting_paper_id(pool):
    a = paper(pool, 'A', [Q, R]); run = start(pool, a)
    token = active_practice.submission_context(run, 0)
    token['paper_id'] = None
    before = evidence(pool)
    with pytest.raises(ValueError, match='stale'):
        attempts.record_browser_attempt(pool, Q, answer_text='bad token', practice_position=0,
                                        practice_context=token, request_id='bad-token')
    assert evidence(pool) == before


def test_raw_ingest_connection_uses_same_semantic_invalidation(pool):
    import sqlite3
    from workbench.data import paper_progress
    a = paper(pool, 'A', [Q, R]); start(pool, a)
    active_practice.mark(pool, 0, 'stuck')
    before = evidence(pool)
    with sqlite3.connect(pool.db_path) as conn:
        paper_progress.update_question(conn, 'UPDATE problems SET problem_text=? WHERE problem_id=?',
                                       ('corrected by raw ingest connection', Q))
        assert conn.row_factory is None
    conn.close()
    assert active_practice.current(pool)['items'][0]['state'] == 'pending'
    assert evidence(pool) == before


def test_multi_question_delete_failure_rolls_back_paper_files_and_learning_rows(pool):
    from workbench.data import practice_sets
    a = paper(pool, 'A', [Q, R])
    path = practice_sets._saved_path(pool, a)
    file_before = path.read_bytes()
    before = evidence(pool)
    pool.connect().execute("CREATE TRIGGER fail_second_delete BEFORE UPDATE OF deleted_at ON problems "
                           "WHEN OLD.problem_id='dmath-ch06-prob-002' BEGIN SELECT RAISE(ABORT, 'injected'); END")
    pool.commit()
    with pytest.raises(Exception, match='injected'):
        with pool.transaction(immediate=True):
            content._delete_problem(pool.connect(), Q, pool)
            content._delete_problem(pool.connect(), R, pool)
    assert path.read_bytes() == file_before
    assert pool.problem(Q) and pool.problem(R)
    assert evidence(pool) == before


def test_batch_rollback_refuses_current_paper_references_without_learning_rows(pool):
    import sqlite3
    from workbench.ingest import _rollback_blockers
    a = paper(pool, 'A', [Q, R])
    pool.connect().execute('UPDATE problems SET ingest_batch_id=? WHERE problem_id=?', ('batch-999', Q))
    pool.commit()
    conn = sqlite3.connect(pool.db_path)
    try:
        assert any('saved Paper' in item for item in _rollback_blockers(conn, 'batch-999'))
    finally:
        conn.close()
    assert practice_sets.get_saved(pool, a)['count'] == 2


def test_completed_paper_retries_are_idempotent_and_stale_rating_writes_nothing(pool):
    a = paper(pool, 'A', [Q, R]); run = start(pool, a)
    token = active_practice.submission_context(run, 0)
    payload = dict(answer_text='historical', request_id='accepted-before-edit',
                   practice_position=0, practice_context=token)
    first = attempts.record_browser_attempt(pool, Q, **payload)
    active_practice.mark(pool, 1, 'stuck')
    content.update(pool, 'problem', Q, {'problem_text': 'corrected after completion'})
    before = evidence(pool)
    assert attempts.record_browser_attempt(pool, Q, **payload) == first
    with pytest.raises(ValueError, match='stale'):
        attempts.record_browser_feedback(pool, 'problem', Q, rating=3,
                                         attempt_id=first['attempt_id'], practice_context=token,
                                         request_id='late-rating')
    with pytest.raises(ValueError, match='stale'):
        attempts.record_browser_feedback(pool, 'problem', Q, rating=3,
                                         attempt_id=first['attempt_id'], request_id='missing-token-rating')
    assert evidence(pool) == before
