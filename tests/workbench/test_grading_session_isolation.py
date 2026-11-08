import pytest

from workbench.bridge import conversations, grading
from workbench.server import api
from tests.workbench.test_grading_bridge import pool


def create(pool, monkeypatch, internal):
    monkeypatch.setattr(conversations.conversation_providers, 'get', lambda name: {})
    monkeypatch.setattr(conversations, '_resolve_target', lambda *a, **k:
        {'provider': 'fake', 'model': 'model'})
    return conversations.create(pool, 'fake', internal=internal)


def test_internal_metadata_is_atomic_and_hidden_from_learner_list(pool, monkeypatch):
    internal = create(pool, monkeypatch, True)
    public = create(pool, monkeypatch, False)
    assert conversations.is_internal(pool, internal['conversation_id'])
    assert [x['conversation_id'] for x in api.ai_sessions_list(pool, {}, {}, {})] == [public['conversation_id']]
    assert len(conversations.list_sessions(pool, include_internal=True)) == 2


@pytest.mark.parametrize('handler', [api.ai_session_get, api.ai_session_update, api.ai_session_delete,
    api.ai_turn_start, api.ai_turn_events, api.ai_turn_cancel, api.ai_turn_pending_update,
    api.ai_turn_pending_delete, api.ai_queue_reorder, api.ai_turn_interrupt,
    api.ai_queue_continue])
def test_all_learner_session_operations_refuse_internal_before_body_or_turn_read(pool, monkeypatch, handler):
    internal = create(pool, monkeypatch, True)
    with pytest.raises(api.ApiError) as error:
        handler(pool, {}, {'conversation_id': internal['conversation_id'], 'turn_id': 'turn-001'}, {})
    assert error.value.status == 404
    assert str(error.value) == 'conversation not found'


def test_no_provider_refresh_marks_failure_without_losing_response(pool, monkeypatch):
    monkeypatch.setattr(grading.conversation_providers, 'discover', lambda: [])
    grading._run(pool.root, pool.db_path, pool.course, pool.chapter, {})
    assert grading.get(pool, 1)['job']['status'] == 'failed'
    assert grading.get(pool, 1)['target']['answer_text'] == 'original proof'


def test_preexisting_linked_grading_session_is_also_hidden(pool, monkeypatch):
    old = create(pool, monkeypatch, False)
    pool.connect().execute('UPDATE part_grading_jobs SET conversation_id=?', (old['conversation_id'],))
    pool.commit()
    assert api.ai_sessions_list(pool, {}, {}, {}) == []
    with pytest.raises(api.ApiError):
        api.ai_session_get(pool, {}, {'conversation_id': old['conversation_id']}, {})
