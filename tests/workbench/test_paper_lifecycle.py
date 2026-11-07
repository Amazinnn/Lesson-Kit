"""Membership edits reconcile by question identity instead of resetting the run."""

import pytest

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import active_practice, attempts, paper_progress, practice_sets
from workbench.server import api

DUPLICATE = 'dmath-ch06-prob-001'
KEPT = 'dmath-ch06-prob-002'
THIRD = 'dmath-ch06-prob-003'


@pytest.fixture
def pool():
    fixture = WorkspaceFixture()
    p = api._pool_for(dict(path=str(fixture.ws), db='pool/dmath.db',
                          active_course='dmath', active_chapter='ch06'))
    for index in (2, 3, 4):
        p.connect().execute(
            "INSERT INTO problems(problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
            " VALUES (?, ?, ?, 'solution', 'calculation', 'textbook')",
            (f'dmath-ch06-prob-00{index}', '["dmath-ch06-kp-001"]', f'question {index}'))
    p.commit()
    yield p
    p.close()
    fixture.cleanup()


def saved(pool, title, ids):
    return practice_sets.create_saved(pool, title, ids)['practice_set_id']


def update(pool, paper_id, ids):
    preview = practice_sets.preview_update(pool, paper_id, problem_ids=ids)
    return practice_sets.update_saved(pool, paper_id, problem_ids=ids,
                                      confirmation=preview['confirmation'])


def test_removing_a_duplicate_keeps_every_surviving_state_draft_and_attempt(pool):
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT, THIRD])
    run = active_practice.start_saved(pool, paper_id, rating_mode='off')
    active_practice.mark(pool, 0, 'stuck')
    active_practice.mark(pool, 2, 'stuck')
    active_practice.save_draft(pool, run['execution_id'], 1, {'answer': '未提交草稿'})
    before = [tuple(row) for row in pool.connect().execute(
        'SELECT id, problem_id, status, note FROM problem_attempts ORDER BY id')]

    preview = practice_sets.preview_update(pool, paper_id, problem_ids=[KEPT, THIRD])
    assert preview['preserved_items'] == 2
    assert preview['removed_items'] == 1
    assert preview['resets_progress'] is False
    update(pool, paper_id, [KEPT, THIRD])

    current = active_practice.current(pool)
    assert current['execution_id'] == run['execution_id']
    assert [item['item_id'] for item in current['items']] == [KEPT, THIRD]
    assert [item['position'] for item in current['items']] == [0, 1]
    assert current['items'][0]['draft']['answer'] == '未提交草稿'
    assert current['items'][1]['state'] == 'stuck'
    assert current['items'][1]['attempt_id'] == run['items'][2]['attempt_id']
    assert [tuple(row) for row in pool.connect().execute(
        'SELECT id, problem_id, status, note FROM problem_attempts ORDER BY id')] == before
    retired = pool.connect().execute(
        'SELECT problem_id, position, state, reason FROM retired_paper_items'
        ' WHERE paper_id=? ORDER BY sequence', (paper_id,)).fetchall()
    assert [tuple(row) for row in retired] == [(DUPLICATE, 0, 'stuck', 'membership')]


def test_a_removed_draft_is_retained_and_an_added_question_starts_pending(pool):
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT])
    run = active_practice.start_saved(pool, paper_id, rating_mode='off')
    active_practice.save_draft(pool, run['execution_id'], 0, {'answer': '会被归档的草稿'})

    update(pool, paper_id, [KEPT, THIRD])

    current = active_practice.current(pool)
    assert [item['item_id'] for item in current['items']] == [KEPT, THIRD]
    assert current['items'][0]['state'] == 'pending'
    assert current['items'][1]['state'] == 'pending'
    assert current['items'][1]['attempt_id'] is None
    assert current['items'][1]['draft'] == {}
    retired = pool.connect().execute(
        'SELECT problem_id, draft_json FROM retired_paper_items WHERE paper_id=?',
        (paper_id,)).fetchall()
    assert retired[0][0] == DUPLICATE
    assert '会被归档的草稿' in retired[0][1]


def test_the_cursor_follows_its_question_then_the_next_survivor(pool):
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT, THIRD])
    run = active_practice.start_saved(pool, paper_id, rating_mode='off')
    active_practice.navigate(pool, run['execution_id'], 1,
                             context=active_practice.submission_context(run, 1))

    # The question under the cursor is removed, so the cursor falls to the next
    # surviving old position (THIRD), not back to the start.
    update(pool, paper_id, [DUPLICATE, THIRD])
    current = active_practice.current(pool)
    assert [item['item_id'] for item in current['items']] == [DUPLICATE, THIRD]
    assert current['cursor'] == 1

    # A surviving anchor keeps the cursor on itself.
    update(pool, paper_id, [THIRD, DUPLICATE])
    assert active_practice.current(pool)['cursor'] == 0


def test_removing_every_question_clears_the_run_and_keeps_each_history_row(pool):
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT])
    run = active_practice.start_saved(pool, paper_id, rating_mode='off')
    active_practice.mark(pool, 0, 'stuck')

    update(pool, paper_id, [])

    assert active_practice.current(pool) is None
    retired = pool.connect().execute(
        'SELECT problem_id FROM retired_paper_items WHERE paper_id=? ORDER BY sequence',
        (paper_id,)).fetchall()
    assert [row[0] for row in retired] == [DUPLICATE, KEPT]
    continuation = practice_sets.get_saved(pool, paper_id)['continuation']
    assert continuation is None or continuation['available'] is False
    assert run['execution_id']


def test_a_parked_paper_reconciles_the_same_way(pool):
    first = saved(pool, '卷一', [DUPLICATE, KEPT])
    second = saved(pool, '卷二', [THIRD])
    run = active_practice.start_saved(pool, first, rating_mode='off')
    active_practice.mark(pool, 1, 'stuck')
    active_practice.start_saved(pool, second, rating_mode='off')   # parks the first run

    update(pool, first, [KEPT])

    parked = paper_progress.state(pool.connect(), first)['checkpoint_json']
    record = __import__('json').loads(parked)
    assert [item['item_id'] for item in record['items']] == [KEPT]
    assert record['items'][0]['state'] == 'stuck'
    assert record['paper_generation'] == practice_sets.get_saved(pool, first)['generation']
    assert run['execution_id'] == record['execution_id']


def test_membership_edit_leaves_learning_evidence_untouched(pool):
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT])
    run = active_practice.start_saved(pool, paper_id, rating_mode='immediate')
    attempts.record_browser_attempt(pool, DUPLICATE, answer_text='历史作答')
    tables = ('problem_attempts', 'problem_progress', 'feedback_events',
              'review_schedule', 'learning_current_state', 'learner_signals')
    before = {name: [tuple(row) for row in pool.connect().execute(f'SELECT * FROM {name}')]
              for name in tables}

    update(pool, paper_id, [KEPT])

    after = {name: [tuple(row) for row in pool.connect().execute(f'SELECT * FROM {name}')]
             for name in tables}
    assert after == before
    assert run['execution_id']


def test_restoring_an_archived_question_keeps_it_out_of_its_papers(pool):
    """FS-08: content comes back, the Paper does not silently re-add it."""
    from workbench.data import content
    paper_id = saved(pool, '卷', [DUPLICATE, KEPT])
    run = active_practice.start_saved(pool, paper_id, rating_mode='off')
    content.delete(pool, 'problem', DUPLICATE)
    pool.commit()
    assert pool.problem(DUPLICATE) is None

    restored = content.restore(pool, 'problem', DUPLICATE)

    assert restored['action'] == 'restored'
    assert pool.problem(DUPLICATE) is not None
    assert [item['item_id'] for item in active_practice.current(pool)['items']] == [KEPT]
    assert [item['problem_id'] for item in practice_sets.get_saved(
        pool, paper_id)['plan']['items']] == [KEPT]
    retired = pool.connect().execute(
        'SELECT problem_id, reason FROM retired_paper_items WHERE paper_id=?',
        (paper_id,)).fetchall()
    assert [tuple(row) for row in retired] == [(DUPLICATE, 'deleted')]
    assert content.restore(pool, 'problem', DUPLICATE)['action'] == 'already_current'
    assert run['execution_id']
