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


def test_existing_card_item_is_not_reported_as_unavailable(pool, monkeypatch):
    paper_id = paper(pool, 'A', [Q, R])
    start(pool, paper_id)
    monkeypatch.setattr(pool, 'card', lambda card_id: {'card_id': card_id})
    pool.connect().execute(
        "UPDATE active_practice_items SET item_type='card',item_id='card-existing' WHERE position=0")
    pool.commit()

    status = practice_sets.get_saved(pool, paper_id)['continuation']

    assert status['unavailable_item_ids'] == []
    assert status['available'] is False
    assert '名单或顺序' in status['reason']


def test_parked_paper_readiness_reports_unparkable_active_paper(pool):
    target = paper(pool, 'Target', [Q, R])
    active_id = paper(pool, 'Active', [Q, R])
    start(pool, target)
    active_practice.mark(pool, 0, 'stuck')
    start(pool, active_id)
    pool.connect().execute('UPDATE active_practice_items SET item_id=? WHERE position=0',
                           ('legacy-missing-question',))
    pool.commit()

    target_status = practice_sets.get_saved(pool, target)
    current_before = active_practice.current(pool)

    assert target_status['continuation']['available'] is True
    assert target_status['progress'] == {'total': 2, 'completed': 1}
    assert target_status['can_start'] is False
    assert '当前活动试卷' in target_status['start_block_reason']
    with pytest.raises(active_practice.ActivePracticeConflict, match='当前活动试卷'):
        start(pool, target)
    assert active_practice.current(pool)['source_ref'] == active_id
    assert active_practice.current(pool)['execution_id'] == current_before['execution_id']


def test_active_resume_readiness_includes_saved_container_validation(pool):
    paper_id = paper(pool, 'A', [Q, R])
    start(pool, paper_id)
    path = practice_sets._saved_path(pool, paper_id)
    plan = __import__('json').loads(path.read_text(encoding='utf-8'))
    plan['plan']['unsupported_field'] = 'stale contract'
    path.write_text(__import__('json').dumps(plan), encoding='utf-8')

    saved = practice_sets.get_saved(pool, paper_id)
    current = active_practice.current(pool)

    assert saved['validation_errors']
    assert saved['continuation']['available'] is False
    assert '内容校验失败' in saved['continuation']['reason']
    assert saved['progress'] is None
    assert current['continuation'] == saved['continuation']
    with pytest.raises(active_practice.ActivePracticeError, match='unsupported manifest field'):
        start(pool, paper_id)


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


def test_explicit_reveal_timing_navigation_and_pause_restore_independent_state(pool):
    a = paper(pool, 'A', [Q, R])
    started = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    assert started['reveal_timing'] == 'on_submit'
    context = active_practice.submission_context(started, 1)
    marked = api.practice_stuck(pool, {}, {}, {
        'execution_id': started['execution_id'], 'position': 1,
        'request_id': 'draft-stuck-1', 'practice_context': context,
    })['practice']
    assert marked['items'][1]['state'] == 'pending'
    assert marked['items'][1]['attempt_id'] is None
    assert marked['items'][1]['draft']['reference_viewed'] is True
    replay = api.practice_stuck(pool, {}, {}, {
        'execution_id': started['execution_id'], 'position': 1,
        'request_id': 'draft-stuck-1', 'practice_context': context,
    })
    assert replay['replay'] is True
    navigated = api.practice_navigate(pool, {}, {}, {
        'execution_id': started['execution_id'], 'position': 1,
        'practice_context': context,
    })['practice']
    assert navigated['cursor'] == 1
    assert navigated['items'][1]['state'] == 'pending'
    assert pool.attempts(R) == []

    api.practice_draft(pool, {}, {}, {
        'execution_id': started['execution_id'], 'position': 1,
        'practice_context': context, 'sequence': 2,
        'draft': {'answer': 'new answer', 'choices': [], 'stuck': False,
                  'reference_viewed': False},
    })
    updated = active_practice.current(pool)['items'][1]['draft']
    assert updated == {'answer': 'new answer', 'choices': [], 'stuck': False,
                       'reference_viewed': True}

    with pytest.raises(api.ApiError) as stale_pause:
        api.active_practice_delete(pool, {}, {}, {
            'execution_id': started['execution_id'] + 1,
            'practice_context': context,
        })
    assert stale_pause.value.status == 409
    assert active_practice.current(pool)['execution_id'] == started['execution_id']

    paused = api.active_practice_delete(pool, {}, {}, {
        'execution_id': started['execution_id'], 'practice_context': context,
    })
    assert paused['paused'] is True
    assert active_practice.current(pool) is None
    continuation = practice_sets.get_saved(pool, a)['continuation']['execution']
    assert continuation['execution_id'] == started['execution_id']
    assert continuation['reveal_timing'] == 'on_submit'
    resumed = active_practice.start_saved(pool, a, reveal_timing='per_item')
    assert resumed['execution_id'] == started['execution_id']
    assert resumed['reveal_timing'] == 'on_submit'
    assert resumed['cursor'] == 1
    assert resumed['items'][1]['draft']['answer'] == 'new answer'
    assert resumed['items'][1]['draft']['reference_viewed'] is True


def test_navigate_adopts_legacy_saved_execution_without_resetting_attempts(pool):
    a = paper(pool, 'A', [Q, R])
    legacy = active_practice.start_saved(pool, a)
    first = attempts.record_browser_attempt(
        pool, Q, answer_text='existing answer', request_id='legacy-paper-answer',
        practice_position=0,
        practice_context=active_practice.submission_context(legacy, 0))
    assert first['practice']['completed'] is False

    adopted = api.practice_navigate(pool, {}, {}, {
        'execution_id': legacy['execution_id'], 'position': 1,
        'practice_context': active_practice.submission_context(legacy, 1),
    })['practice']

    assert adopted['execution_id'] == legacy['execution_id']
    assert adopted['reveal_timing'] == 'per_item'
    assert adopted['cursor'] == 1
    assert adopted['items'][0]['state'] == 'answered'
    assert adopted['items'][0]['attempt_id'] == first['attempt_id']
    assert adopted['items'][0]['attempt']['answer_text'] == 'existing answer'
    assert pool.connect().execute(
        'SELECT reveal_timing FROM active_practice WHERE singleton=1').fetchone()[0] == 'per_item'


def test_navigate_adopts_legacy_temporary_problem_run_but_not_cards(pool):
    temporary = active_practice.create(pool, {
        'source_kind': 'quick', 'kp_ids': ['dmath-ch06-kp-001'],
        'practice_mode': 'exam', 'rating_mode': 'off',
        'items': [{'item_type': 'problem', 'item_id': Q},
                  {'item_type': 'problem', 'item_id': R}],
    })
    adopted = active_practice.navigate(
        pool, temporary['execution_id'], 0,
        context=active_practice.submission_context(temporary, 0))['practice']
    assert adopted['source_ref'] is None
    assert adopted['reveal_timing'] == 'per_item'

    card_id = 'legacy-card-for-navigation'
    pool.connect().execute(
        'INSERT INTO flash_cards(card_id,kp_id,front,back,source_evidence,directions) '
        "VALUES (?, 'dmath-ch06-kp-001', 'front', 'back', 'test', '[\"forward\"]')",
        (card_id,))
    pool.commit()
    # Replacing through the legacy execution API archives the first run; this
    # fresh card execution must retain its established NULL-mode semantics.
    card = active_practice.create(pool, {
        'source_kind': 'quick', 'kp_ids': [], 'practice_mode': 'exam',
        'rating_mode': 'off', 'items': [{'item_type': 'card', 'item_id': card_id}],
    }, replace=True)
    navigated = active_practice.navigate(
        pool, card['execution_id'], 0,
        context=active_practice.submission_context(card, 0))['practice']
    assert navigated['reveal_timing'] is None


def test_explicit_start_adopts_active_or_parked_legacy_saved_execution_as_per_item(pool):
    a = paper(pool, 'A', [Q, R])
    legacy = active_practice.start_saved(pool, a)
    attempt = attempts.record_browser_attempt(
        pool, Q, answer_text='old evidence', request_id='start-adopt-answer',
        practice_position=0,
        practice_context=active_practice.submission_context(legacy, 0))

    active = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    assert active['execution_id'] == legacy['execution_id']
    assert active['reveal_timing'] == 'per_item'
    assert active['items'][0]['attempt_id'] == attempt['attempt_id']
    assert len(pool.attempts(Q)) == 1

    paused = active_practice.clear(
        pool, execution_id=active['execution_id'],
        practice_context=active_practice.submission_context(active, 1))
    assert paused['paused'] is True
    restored = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    assert restored['execution_id'] == legacy['execution_id']
    assert restored['reveal_timing'] == 'per_item'
    assert restored['items'][0]['attempt_id'] == attempt['attempt_id']
    assert len(pool.attempts(Q)) == 1


def test_on_submit_finalization_records_saved_answers_atomically_and_replays(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    for position, draft in enumerate((
        {'answer': 'response', 'choices': [], 'stuck': False,
         'reference_viewed': False},
        {'answer': '', 'choices': [], 'stuck': True,
         'reference_viewed': True},
    )):
        token = active_practice.submission_context(run, position)
        active_practice.save_draft(pool, run['execution_id'], position, draft,
                                   context=token, sequence=1)

    request = {'execution_id': run['execution_id'], 'request_id': 'paper-submit-1'}
    first = api.practice_submit(pool, {}, {}, request)
    assert first['completed'] is True
    assert first['replay'] is False
    assert isinstance(first['run_id'], int)
    assert active_practice.current(pool) is None
    assert pool.attempts(Q)[-1]['answer_text'] == 'response'
    assert pool.attempts(R)[-1]['status'] == 'stuck'

    replay = api.practice_submit(pool, {}, {}, request)
    assert replay['run_id'] == first['run_id']
    assert replay['replay'] is True
    assert len(pool.attempts(Q)) == 1
    assert len(pool.attempts(R)) == 1

    sheet = api.practice_run_get(pool, {}, {'run_id': str(first['run_id'])}, {})
    assert sheet['execution_id'] == run['execution_id']
    assert sheet['reveal_timing'] == 'on_submit'
    assert [item['item_id'] for item in sheet['items']] == [Q, R]
    assert sheet['items'][0]['attempt']['answer_text'] == 'response'
    assert sheet['items'][1]['state'] == 'stuck'
    assert sheet['items'][1]['draft']['reference_viewed'] is True
    assert sheet['items'][0]['payload']['problem_id'] == Q


def test_on_submit_stuck_wins_over_unchanged_nonblank_draft(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    context = active_practice.submission_context(run, 0)
    active_practice.save_draft(
        pool, run['execution_id'], 0,
        {'answer': 'tentative work', 'choices': []}, context=context, sequence=1)
    marked = api.practice_stuck(pool, {}, {}, {
        'execution_id': run['execution_id'], 'position': 0,
        'request_id': 'stuck-after-draft', 'practice_context': context,
    })['practice']
    assert marked['items'][0]['draft']['answer'] == 'tentative work'
    assert marked['items'][0]['draft']['stuck'] is True
    assert pool.attempts(Q) == []

    completed = api.practice_submit(pool, {}, {}, {
        'execution_id': run['execution_id'], 'request_id': 'stuck-after-draft-final',
        'drafts': [{
            'position': 0,
            'draft': {'answer': 'tentative work', 'choices': [], 'stuck': True,
                      'reference_viewed': True},
            'sequence': 2, 'practice_context': context,
        }],
    })
    sheet = api.practice_run_get(pool, {}, {'run_id': str(completed['run_id'])}, {})
    item = sheet['items'][0]
    assert item['state'] == 'stuck'
    assert item['attempt']['status'] == 'stuck'
    assert item['attempt']['answer_text'] is None
    assert item['attempt']['verdict'] is None
    assert item['draft']['answer'] == 'tentative work'
    assert item['draft']['stuck'] is True


def test_new_nonblank_answer_edit_clears_stuck_and_preserves_reference_viewed(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    context = active_practice.submission_context(run, 0)
    active_practice.save_draft(
        pool, run['execution_id'], 0, {'answer': 'first draft'}, context=context, sequence=1)
    api.practice_stuck(pool, {}, {}, {
        'execution_id': run['execution_id'], 'position': 0,
        'request_id': 'stuck-before-edit', 'practice_context': context,
    })

    saved = api.practice_draft(pool, {}, {}, {
        'execution_id': run['execution_id'], 'position': 0, 'sequence': 3,
        'practice_context': context,
        'draft': {'answer': 'revised answer', 'choices': [], 'stuck': True,
                  'reference_viewed': False},
    })
    current = active_practice.current(pool)
    assert saved['sequence'] == 3
    assert current['items'][0]['draft']['stuck'] is False
    assert current['items'][0]['draft']['reference_viewed'] is True

    completed = api.practice_submit(pool, {}, {}, {
        'execution_id': run['execution_id'], 'request_id': 'edited-answer-final',
    })
    sheet = api.practice_run_get(pool, {}, {'run_id': str(completed['run_id'])}, {})
    assert sheet['items'][0]['state'] == 'answered'
    assert sheet['items'][0]['attempt']['answer_text'] == 'revised answer'


def test_per_item_last_attempt_waits_for_explicit_submit_and_legacy_still_autoarchives(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='per_item')
    for position, problem_id in enumerate((Q, R)):
        result = attempts.record_browser_attempt(
            pool, problem_id, answer_text='response', request_id=f'per-item-{position}',
            practice_position=position,
            practice_context=active_practice.submission_context(run, position))
        assert result['practice']['completed'] is False
    assert active_practice.current(pool)['progress']['remaining'] == 0
    assert pool.connect().execute('SELECT COUNT(*) FROM practice_runs').fetchone()[0] == 0
    completed = api.practice_submit(pool, {}, {}, {
        'execution_id': run['execution_id'], 'request_id': 'per-item-final',
    })
    assert completed['completed'] is True
    assert pool.connect().execute('SELECT COUNT(*) FROM practice_runs').fetchone()[0] == 1

    legacy = active_practice.start_saved(pool, a)
    active_practice.mark(pool, 0, 'stuck')
    active_practice.mark(pool, 1, 'stuck')
    assert active_practice.current(pool) is None
    assert legacy['reveal_timing'] is None


def test_new_navigation_endpoints_are_declared_in_the_interface_surface():
    from workbench.server import app
    from workbench import surface

    expected = {
        ('POST', '/api/w/{name}/practice/current/navigate'),
        ('POST', '/api/w/{name}/practice/current/stuck'),
        ('POST', '/api/w/{name}/practice/current/submit'),
        ('GET', '/api/w/{name}/practice/runs/{run_id}'),
    }
    actual = {(method, path) for method, path, _handler in app.ROUTES}
    assert expected <= actual
    assert expected <= set(surface.ROUTES)


def test_completed_run_read_returns_not_found_for_unknown_archive(pool):
    with pytest.raises(api.ApiError) as missing:
        api.practice_run_get(pool, {}, {'run_id': '99999'}, {})
    assert missing.value.status == 404
    with pytest.raises(api.ApiError) as invalid:
        api.practice_run_get(pool, {}, {'run_id': 'not-an-id'}, {})
    assert invalid.value.status == 400


def test_old_pool_rejects_explicit_mode_with_migration_hint_but_keeps_legacy_runs(pool):
    a = paper(pool, 'A', [Q, R])
    conn = pool.connect()
    conn.execute('ALTER TABLE active_practice DROP COLUMN reveal_timing')
    conn.execute('ALTER TABLE practice_runs DROP COLUMN reveal_timing')
    pool.commit()

    with pytest.raises(active_practice.ActivePracticeError, match='not migrated.*migrate-progress.py'):
        active_practice.start_saved(pool, a, reveal_timing='on_submit')

    legacy = active_practice.start_saved(pool, a)
    assert legacy.get('reveal_timing') is None
    with pytest.raises(active_practice.ActivePracticeError, match='not migrated.*migrate-progress.py'):
        active_practice.navigate(
            pool, legacy['execution_id'], 0,
            context=active_practice.submission_context(legacy, 0))
    active_practice.mark(pool, 0, 'stuck')
    active_practice.mark(pool, 1, 'stuck')
    assert active_practice.current(pool) is None
    assert conn.execute('SELECT status FROM practice_runs').fetchone()[0] == 'completed'


def test_finalization_checks_locked_item_content_revision_before_archiving(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='per_item')
    attempts.record_browser_attempt(
        pool, Q, answer_text='locked answer', request_id='locked-before-final',
        practice_position=0,
        practice_context=active_practice.submission_context(run, 0))
    # Simulate an out-of-band content revision that bypassed the normal
    # reconcile path. Finalization must still validate already-locked items.
    pool.connect().execute(
        'INSERT INTO problem_revisions(problem_id,revision) VALUES (?,2) '
        'ON CONFLICT(problem_id) DO UPDATE SET revision=revision+1', (Q,))
    pool.commit()

    with pytest.raises(api.ApiError, match='stale answering content') as stale:
        api.practice_submit(pool, {}, {}, {
            'execution_id': run['execution_id'], 'request_id': 'final-after-correction',
        })
    assert stale.value.status == 409

    current = active_practice.current(pool)
    assert current['items'][0]['state'] == 'answered'
    assert current['items'][1]['state'] == 'pending'
    assert pool.attempts(R) == []
    assert pool.connect().execute('SELECT COUNT(*) FROM practice_runs').fetchone()[0] == 0


def test_failed_final_attempt_rolls_back_earlier_attempts_and_keeps_drafts(pool):
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    for position, answer in enumerate(('first answer', 'second answer')):
        active_practice.save_draft(
            pool, run['execution_id'], position, {'answer': answer, 'choices': []},
            context=active_practice.submission_context(run, position), sequence=1)
    pool.connect().execute(
        "CREATE TRIGGER reject_second_final BEFORE INSERT ON problem_attempts "
        f"WHEN NEW.problem_id='{R}' BEGIN SELECT RAISE(ABORT,'injected final failure'); END")
    pool.commit()

    with pytest.raises(Exception, match='injected final failure'):
        api.practice_submit(pool, {}, {}, {
            'execution_id': run['execution_id'], 'request_id': 'atomic-final-1',
        })

    current = active_practice.current(pool)
    assert current['items'][0]['state'] == 'pending'
    assert current['items'][0]['draft']['answer'] == 'first answer'
    assert current['items'][1]['draft']['answer'] == 'second answer'
    assert pool.attempts(Q) == []
    assert pool.attempts(R) == []
    assert pool.connect().execute('SELECT COUNT(*) FROM practice_runs').fetchone()[0] == 0


def test_final_submit_grades_only_usable_keys_and_archive_ratings_stay_linked(pool):
    import json

    pool.connect().execute(
        'UPDATE problems SET micro_quiz=?,practice_modes=? WHERE problem_id=?',
        (json.dumps({'quiz_type': 'single_choice', 'options': ['A', 'B'],
                     'answer_key': 'B'}), '["micro"]', Q))
    pool.connect().execute(
        'UPDATE problems SET micro_quiz=?,practice_modes=? WHERE problem_id=?',
        (json.dumps({'quiz_type': 'single_choice', 'options': ['A', 'B']}), '["micro"]', R))
    pool.commit()
    a = paper(pool, 'A', [Q, R])
    run = active_practice.start_saved(pool, a, reveal_timing='on_submit')
    latest_drafts = []
    for position, choices in enumerate((['B'], ['A'])):
        latest_drafts.append({
            'position': position,
            'draft': {'answer': '', 'choices': choices, 'stuck': False,
                      'reference_viewed': False},
            'sequence': 1,
            'practice_context': active_practice.submission_context(run, position),
        })
    submitted = api.practice_submit(pool, {}, {}, {
        'execution_id': run['execution_id'], 'request_id': 'graded-final-1',
        'drafts': latest_drafts,
    })
    sheet = api.practice_run_get(pool, {}, {'run_id': str(submitted['run_id'])}, {})
    assert sheet['items'][0]['attempt']['verdict'] == 1
    assert sheet['items'][1]['attempt']['verdict'] is None
    assert sheet['result_counts'] == {
        'correct': 1, 'incorrect': 0, 'ungraded': 1, 'stuck': 0, 'total': 2,
    }

    token = active_practice.submission_context(sheet, 0)
    attempt_id = sheet['items'][0]['attempt_id']
    attempts.record_browser_feedback(
        pool, 'problem', Q, rating=4, note='first rating', attempt_id=attempt_id,
        request_id='sheet-rating-1', practice_context=token)
    attempts.record_browser_feedback(
        pool, 'problem', Q, rating=5, note='edited rating', attempt_id=attempt_id,
        request_id='sheet-rating-edit', practice_context=token, edit_existing=True,
        expected_rating=4, expected_note='first rating')
    reread = api.practice_run_get(pool, {}, {'run_id': str(submitted['run_id'])}, {})
    assert reread['items'][0]['feedback']['rating'] == 5
    assert pool.connect().execute(
        'SELECT COUNT(*) FROM feedback_events WHERE attempt_id=?', (attempt_id,)
    ).fetchone()[0] == 1


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
