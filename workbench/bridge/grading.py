"""Dedicated Agent grading requests; teaching conversations remain independent."""

import json
import threading
from functools import partial

from workbench.bridge import conversations, conversation_providers
from workbench.data import grading_jobs, part_grading, paper_progress
from workbench.data.pool import Pool
from workbench.domain import part_grading as rules

_LOCK = threading.Lock()
_ACTIVE = set()


def target(pool, attempt_id):
    return grading_jobs.target(pool, attempt_id)


def get(pool, attempt_id):
    return {'target': target(pool, attempt_id), 'grading': part_grading.get(pool, attempt_id),
            'job': grading_jobs.get(pool, attempt_id)}


def history(pool, attempt_id):
    target(pool, attempt_id)
    return part_grading.list_revisions(pool, attempt_id)


def apply(pool, request, *, withdraw=False):
    allowed = {'attempt_id', 'problem_id', 'part_id', 'content_revision',
               'expected_revision', 'operation_id', 'payload'}
    if not isinstance(request, dict) or set(request) - allowed:
        raise ValueError('invalid grading request fields')
    saved = target(pool, request.get('attempt_id'))
    with pool.transaction(immediate=True):
        result = part_grading.mutate(pool, **request, withdraw=withdraw,
            validate=partial(rules.validate, answering_type=saved['part']['type']),
            actual_content_revision=paper_progress.revision)
        grading_jobs.update(pool, saved['id'], 'completed')
    return result


def retry(pool, attempt_id):
    target(pool, attempt_id)
    job = grading_jobs.get(pool, attempt_id)
    if not job:
        raise ValueError('grading job not found')
    if job['status'] in {'pending', 'running', 'completed'}:
        return job
    return grading_jobs.retry(pool, attempt_id)


def _request(pool, workspace, job):
    saved = target(pool, job['attempt_id'])
    if paper_progress.revision(pool.connect(), saved['problem_id']) != saved['content_revision']:
        raise ValueError('stale content revision')
    recent = conversations.list_sessions(pool, limit=1)
    provider = recent[0]['provider'] if recent else None
    if not provider:
        providers = conversation_providers.discover()
        if len(providers) != 1:
            raise ValueError('choose an Agent in the existing Agent settings before retrying grading')
        provider = providers[0]['name']
    conversation_id = job.get('conversation_id')
    if not conversation_id:
        conversation_id = conversations.create(pool, provider, title=f"Grading Attempt {saved['id']}")['conversation_id']
        grading_jobs.update(pool, saved['id'], 'pending', conversation_id=conversation_id)
    current = part_grading.get(pool, saved['id'])
    request = {key: saved[key] for key in ('problem_id', 'part_id', 'content_revision')}
    request.update(attempt_id=saved['id'], expected_revision=current['revision'] if current else 0,
                   operation_id=f"grading-attempt-{saved['id']}-revision-{current['revision'] + 1 if current else 1}")
    message = ('Grade only the immutable submitted response below. Load `python -m workbench.bridge.agent_contracts grading`. '
        'Use `lesson-kit grading <workspace> apply --input <file>` with this exact target and a payload. '
        'Do not change Attempts, content, ratings or learning state. Proof uses process only; '
        'missing result is unprovided. Return no fabricated learner extraction.\n' +
        json.dumps({'workspace': workspace.get('name'), 'request': request, 'submission': saved}, ensure_ascii=False))
    turn = conversations.start_turn(pool, workspace, conversation_id, message, {},
        submission_id=request['operation_id'], submitted_fields=request)
    grading_jobs.update(pool, saved['id'], 'running', conversation_id=conversation_id,
                        turn_id=turn['turn_id'])


def _run(root, db_path, course, chapter, workspace):
    pool = Pool(root, db_path, course, chapter)
    key = str(db_path)
    try:
        for job in grading_jobs.pending(pool):
            try:
                if job['status'] == 'running':
                    turn = conversations.get_turn(pool, job['conversation_id'], job['turn_id'])
                    if turn['status'] in {'failed', 'cancelled', 'done'}:
                        grading_jobs.update(pool, job['attempt_id'], 'failed',
                            turn.get('error') or 'Agent finished without applying grading')
                else:
                    _request(pool, workspace, job)
            except (ValueError, KeyError, OSError) as exc:
                grading_jobs.update(pool, job['attempt_id'], 'failed', str(exc))
    finally:
        pool.close()
        with _LOCK:
            _ACTIVE.discard(key)


def dispatch_pending(pool, workspace):
    """Schedule durable jobs without waiting for any external Agent work."""
    key = str(pool.db_path)
    with _LOCK:
        if key in _ACTIVE:
            return
        _ACTIVE.add(key)
    threading.Thread(target=_run, args=(pool.root, pool.db_path, pool.course,
        pool.chapter, dict(workspace)), daemon=True).start()


def reconcile(pool, workspace=None):
    """Poll/recover linked turns asynchronously through the same bounded worker."""
    dispatch_pending(pool, workspace or {})
