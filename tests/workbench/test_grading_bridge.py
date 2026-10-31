import json

import pytest

from workbench.bridge import grading
from workbench.data import grading_jobs, part_grading
from workbench.data.pool import Pool


@pytest.fixture
def pool(tmp_path):
    pool = Pool(tmp_path, tmp_path / 'test.db', 'test', 'ch01')
    conn = pool.connect()
    conn.executescript('''CREATE TABLE problem_attempts(id INTEGER PRIMARY KEY,problem_id TEXT,
        part_id TEXT,content_revision INTEGER,answer_text TEXT);
        CREATE TABLE part_attempt_context(attempt_id INTEGER PRIMARY KEY,execution_id INTEGER,part_json TEXT);
        CREATE TABLE problem_revisions(problem_id TEXT PRIMARY KEY,revision INTEGER);
        CREATE TABLE part_grading_jobs(attempt_id INTEGER PRIMARY KEY,execution_id INTEGER,
            status TEXT,error TEXT,conversation_id TEXT,turn_id TEXT,updated_at TEXT);
        INSERT INTO problem_attempts VALUES(1,'p','a',1,'original proof');
        INSERT INTO part_grading_jobs(attempt_id,execution_id,status) VALUES(1,12,'pending');''')
    conn.execute('INSERT INTO part_attempt_context VALUES(1,12,?)', (json.dumps({'id': 'a', 'type': 'proof'}),))
    part_grading.ensure_schema(conn)
    conn.commit()
    yield pool
    pool.close()


def request(**changes):
    result = dict(attempt_id=1,problem_id='p',part_id='a',content_revision=1,
                  expected_revision=0,operation_id='op1',payload={'process_conclusion':'correct'})
    result.update(changes)
    return result


def test_bound_proof_and_current_version(pool):
    with pytest.raises(ValueError, match='process only'):
        grading.apply(pool, request(payload={'answer_conclusion':'correct'}))
    result = grading.apply(pool, request())
    assert result['revision'] == 1
    assert grading_jobs.get(pool, 1)['status'] == 'completed'
    assert grading.apply(pool, request()) == result
    pool.connect().execute("INSERT INTO problem_revisions VALUES('p',2)")
    pool.commit()
    with pytest.raises(ValueError, match='stale content'):
        grading.apply(pool, request(operation_id='op2',expected_revision=1))
    assert len(grading.history(pool, 1)) == 1
    assert grading.get(pool,1)['target']['answer_text'] == 'original proof'


def test_request_independent_and_no_config_preserves_attempt(pool, monkeypatch):
    monkeypatch.setattr(grading.conversation_providers,'discover',lambda: [])
    with pytest.raises(ValueError, match='choose an Agent'):
        grading._request(pool, {'name':'test'}, grading_jobs.get(pool,1))
    assert grading.target(pool,1)['answer_text'] == 'original proof'
    monkeypatch.setattr(grading.conversations,'create',lambda *a,**k: {'conversation_id':'conv-grade'})
    monkeypatch.setattr(grading.conversations,'list_sessions',lambda *a,**k: [{'provider':'fake'}])
    def start(*args,**kwargs):
        assert args[2] == 'conv-grade'
        assert 'original proof' in args[3]
        return {'turn_id':'turn-001'}
    monkeypatch.setattr(grading.conversations,'start_turn',start)
    grading._request(pool, {'name':'test','grading_provider':'fake'},grading_jobs.get(pool,1))
    assert grading_jobs.get(pool,1)['status'] == 'running'


def test_retry_retains_attempt_and_resets_failed_transport(pool):
    grading_jobs.update(pool,1,'failed','offline','conv-old','turn-old')
    job = grading.retry(pool,1)
    assert job['status'] == 'pending' and job['conversation_id'] is None
    assert grading.retry(pool,1) == job
    assert pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0] == 1


def test_fast_agent_completion_cannot_be_overwritten(pool, monkeypatch):
    monkeypatch.setattr(grading.conversations,'list_sessions',lambda *a,**k: [{'provider':'fake'}])
    monkeypatch.setattr(grading.conversations,'create',lambda *a,**k: {'conversation_id':'conv-grade'})
    def start(*args,**kwargs):
        grading.apply(pool, request())
        return {'turn_id':'turn-001'}
    monkeypatch.setattr(grading.conversations,'start_turn',start)
    grading._request(pool, {'name':'test'}, grading_jobs.get(pool,1))
    assert grading_jobs.get(pool,1)['status'] == 'completed'


def test_recovery_marks_finished_without_grade_failed(pool, monkeypatch):
    grading_jobs.update(pool,1,'running',conversation_id='conv-1',turn_id='turn-1')
    monkeypatch.setattr(grading.conversations,'get',lambda *a: {})
    monkeypatch.setattr(grading.conversations,'get_turn',lambda *a: {'status':'done'})
    grading._run(pool.root,pool.db_path,pool.course,pool.chapter,{'name':'test'})
    assert grading_jobs.get(pool,1)['status'] == 'failed'
    assert grading.target(pool,1)['answer_text'] == 'original proof'


def test_dispatch_starts_only_one_and_waits_for_persistent_running(pool, monkeypatch):
    pool.connect().execute("INSERT INTO part_grading_jobs(attempt_id,execution_id,status) VALUES(2,12,'pending')")
    pool.commit()
    started = []
    def start(pool, workspace, job):
        started.append(job['attempt_id'])
        grading_jobs.update(pool, job['attempt_id'], 'running', conversation_id='conv-1', turn_id='turn-1')
    monkeypatch.setattr(grading,'_request',start)
    grading._run(pool.root,pool.db_path,pool.course,pool.chapter,{})
    assert started == [1]
    recovered = []
    monkeypatch.setattr(grading.conversations,'get',lambda *a: recovered.append(a[1]))
    monkeypatch.setattr(grading.conversations,'get_turn',lambda *a: {'status':'running'})
    grading._run(pool.root,pool.db_path,pool.course,pool.chapter,{})
    assert recovered == ['conv-1'] and started == [1]
    monkeypatch.setattr(grading.conversations,'get_turn',lambda *a: {'status':'failed','error':'orphaned'})
    grading._run(pool.root,pool.db_path,pool.course,pool.chapter,{})
    assert started == [1,2]
    assert grading_jobs.get(pool,1)['error'] == 'orphaned'


@pytest.mark.parametrize('payload', [
    {'feedback':'nothing concluded'},
    {'process_conclusion':'needs_confirmation'},
    {'process_conclusion':'correct','reference_origin':'agent_derived'},
    {'process_conclusion':'correct','reference_answer':'x'},
])
def test_incomplete_academic_payload_is_not_completed(pool, payload):
    with pytest.raises(ValueError):
        grading.apply(pool, request(payload=payload))
    assert grading_jobs.get(pool,1)['status'] == 'pending'


def test_open_response_without_final_answer_and_objective_are_bound(pool):
    pool.connect().execute('UPDATE part_attempt_context SET part_json=?',
                          (json.dumps({'id':'a','type':'open_response','short_answer':False}),))
    pool.commit()
    with pytest.raises(ValueError):
        grading.apply(pool, request(payload={'answer_conclusion':'correct'}))
    pool.connect().execute('UPDATE part_attempt_context SET part_json=?',
                          (json.dumps({'id':'a','type':'yes_no'}),))
    pool.commit()
    with pytest.raises(ValueError, match='objective'):
        grading.apply(pool, request())


def test_blank_calculation_cannot_receive_invented_extraction(pool):
    pool.connect().execute("UPDATE problem_attempts SET answer_text=''")
    pool.connect().execute('UPDATE part_attempt_context SET part_json=?',
                          (json.dumps({'id':'a','type':'calculation'}),))
    pool.commit()
    with pytest.raises(ValueError, match='blank learner'):
        grading.apply(pool, request(payload={'answer_conclusion':'correct','extracted_answer':'42'}))
