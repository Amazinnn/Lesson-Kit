"""Per-part submissions within the existing durable Paper execution."""

import copy
import json

from workbench.data import active_practice, attempts, paper_progress, part_grading
from workbench.domain import problem_parts


def definitions(pool, item):
    if item['item_type'] != 'problem':
        return []
    snapshot = (item.get('draft') or {}).get('part_definitions')
    return snapshot if snapshot is not None else problem_parts.definitions(
        item.get('payload') or pool.problem(item['item_id']) or {})


def _target(pool, execution_id, position, context):
    if not isinstance(context, dict):
        raise active_practice.ActivePracticeConflict('stale practice page: reload before changing a part')
    practice = active_practice.current(pool, resolve=False)
    if not practice or practice['execution_id'] != execution_id:
        raise active_practice.ActivePracticeConflict('stale practice execution')
    if type(position) is not int or not 0 <= position < len(practice['items']):
        raise active_practice.ActivePracticeError('unknown part position')
    item = practice['items'][position]
    paper_progress.guard(pool, context,
                         item['item_id'], position)
    parts = definitions(pool, item)
    if not parts:
        raise active_practice.ActivePracticeError('this item has no subjective or mixed parts')
    return practice, item, parts


def _write(pool, item, draft):
    pool.connect().execute('UPDATE active_practice_items SET draft_json=?,draft_sequence=draft_sequence+1 '
                           'WHERE position=?', (json.dumps(draft, ensure_ascii=False), item['position']))


def save_draft(pool, execution_id, position, part_id, fields, *, context=None, sequence=None):
    if not isinstance(fields, dict) or set(fields) - {'answer', 'choices', 'stuck', 'reference_viewed'}:
        raise active_practice.ActivePracticeError('invalid part draft fields')
    if not isinstance(fields.get('answer', ''), str) or not isinstance(fields.get('choices', []), list) \
            or not all(isinstance(x, str) for x in fields.get('choices', [])):
        raise active_practice.ActivePracticeError('invalid part answer')
    if any(type(fields[key]) is not bool for key in ('stuck', 'reference_viewed') if key in fields):
        raise active_practice.ActivePracticeError('part flags must be boolean')
    with pool.transaction(immediate=True):
        practice, item, parts = _target(pool, execution_id, position, context)
        part = next((p for p in parts if p['id'] == part_id), None)
        if part is None:
            raise active_practice.ActivePracticeError('unknown part id')
        draft = copy.deepcopy(item.get('draft') or {})
        draft.setdefault('part_definitions', parts)
        values = draft.setdefault('parts', {})
        previous = values.get(part_id, {})
        if previous.get('attempt_id') or item['state'] != 'pending':
            raise active_practice.ActivePracticeConflict('cannot edit a submitted part')
        new = {**previous, **fields}
        if part['type'] in problem_parts.OBJECTIVE:
            options = ['是', '否'] if part['type'] == 'yes_no' else part['options']
            choices = new.get('choices', [])
            if len(choices) != len(set(choices)) or any(x not in options for x in choices) \
                    or (part['type'] != 'multiple_choice' and len(choices) > 1):
                raise active_practice.ActivePracticeError('invalid part choices')
        new['reference_viewed'] = bool(previous.get('reference_viewed') or new.get('reference_viewed') or new.get('stuck'))
        changed = any(new.get(k) != previous.get(k) for k in ('answer', 'choices'))
        if changed and (new.get('answer', '').strip() or new.get('choices')) and not fields.get('stuck'):
            new['stuck'] = False
        old_sequence = previous.get('sequence', 0)
        sequence = old_sequence + 1 if sequence is None else sequence
        if type(sequence) is not int or not 0 <= sequence <= 9007199254740991:
            raise active_practice.ActivePracticeError('invalid part draft sequence')
        if sequence < old_sequence or (sequence == old_sequence and any(
                new.get(k) != previous.get(k) for k in fields)):
            raise active_practice.ActivePracticeConflict('stale part draft')
        new['sequence'] = sequence
        values[part_id] = new
        _write(pool, item, draft)
    return {'saved': True, 'sequence': sequence}


def _submit_item(pool, practice, item, parts, part_id=None):
    draft = copy.deepcopy(item.get('draft') or {})
    draft.setdefault('part_definitions', parts)
    values = draft.setdefault('parts', {})
    selected = [p for p in parts if part_id is None or p['id'] == part_id]
    if not selected:
        raise active_practice.ActivePracticeError('unknown part id')
    ids = []
    for part in selected:
        saved = values.setdefault(part['id'], {})
        if saved.get('attempt_id'):
            ids.append(saved['attempt_id'])
            continue
        # Carry a legacy unstructured draft into its virtual whole part once.
        if part['id'] == 'whole' and len(parts) == 1:
            for key in ('answer', 'choices', 'stuck', 'reference_viewed'):
                if key not in saved and key in draft:
                    saved[key] = draft[key]
        answer = saved.get('answer', '')
        choices = saved.get('choices') or []
        stuck = bool(saved.get('stuck')) or not (answer.strip() or choices)
        objective = part['type'] in problem_parts.OBJECTIVE
        verdict = problem_parts.objective_grade(part, choices) if objective and not stuck else None
        attempt_id = pool.insert_attempt(item['item_id'], 'stuck' if stuck else 'answered',
                                         answer_text=answer, verdict=None if verdict is None else int(verdict),
                                         choices=choices)
        if part_grading.has_schema(pool):
            pool.connect().execute('UPDATE problem_attempts SET part_id=?,content_revision=? WHERE id=?',
                                   (part['id'], item['content_revision'], attempt_id))
            pool.connect().execute('INSERT INTO part_attempt_context(attempt_id,execution_id,part_json) VALUES (?,?,?)',
                                   (attempt_id, practice['execution_id'], json.dumps(part, ensure_ascii=False)))
        saved.update(attempt_id=attempt_id, stuck=stuck,
                     reference_viewed=bool(saved.get('reference_viewed') or stuck))
        if part_grading.has_schema(pool) and not objective:
            pool.connect().execute('INSERT INTO part_grading_jobs(attempt_id,execution_id) VALUES (?,?)',
                                   (attempt_id, practice['execution_id']))
        ids.append(attempt_id)
    _write(pool, item, draft)
    if all(values.get(p['id'], {}).get('attempt_id') for p in parts):
        # Parent has progress only; its verdict is never inferred from children.
        state = 'stuck' if all(values[p['id']].get('stuck') for p in parts) else 'answered'
        pool.connect().execute('UPDATE active_practice_items SET state=?,attempt_id=? WHERE position=?',
                               (state, values[parts[-1]['id']]['attempt_id'], item['position']))
    return ids


def submit(pool, execution_id, position, request_id, *, part_id=None, context=None):
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > attempts.MAX_REQUEST_ID:
        raise active_practice.ActivePracticeError('request_id is required')
    payload = attempts._browser_payload('part-submit', execution_id=execution_id, position=position,
                                        part_id=part_id, context=context)
    with pool.transaction(immediate=True):
        replay = attempts._browser_replay(pool, request_id, payload)
        if replay is not None:
            return {**replay, 'replay': True}
        practice, item, parts = _target(pool, execution_id, position, context)
        ids = _submit_item(pool, practice, item, parts, part_id)
        result = {'attempt_ids': ids, 'replay': False}
        attempts._save_browser_operation(pool, request_id, payload, result)
    return result


def project(pool, practice, *, completed=False):
    """Learner response: never serialize unrevealed child references or grades."""
    if practice is None:
        return None
    result = copy.deepcopy(practice)
    for item in result['items']:
        if 'part_items' in item:
            continue
        parts = definitions(pool, item)
        if not parts:
            continue
        draft = item.get('draft') or {}
        values = draft.get('parts', {})
        children = []
        counts = {'total': len(parts), 'submitted': 0, 'stuck': 0, 'grading': {}, 'answer': {}, 'process': {}}
        for part in parts:
            saved = copy.deepcopy(values.get(part['id'], {}))
            if not values and part['id'] == 'whole':
                saved = {k: draft[k] for k in ('answer', 'choices', 'stuck', 'reference_viewed') if k in draft}
                if item.get('attempt_id'):
                    saved['attempt_id'] = item['attempt_id']
                    saved['answer'] = (item.get('attempt') or {}).get('answer_text') or saved.get('answer', '')
            locked = bool(saved.get('attempt_id'))
            disclosed = completed or bool(saved.get('reference_viewed')) or (
                practice.get('reveal_timing') != 'on_submit' and locked)
            child = {k: copy.deepcopy(v) for k, v in part.items() if k not in {
                'answer_key', 'reference_answer', 'reference_reasoning'}}
            child.update(saved, locked=locked, disclosed=disclosed, grading=None,
                         grading_status='not_requested', objective_verdict=None)
            counts['submitted'] += int(locked)
            counts['stuck'] += int(bool(saved.get('stuck')))
            if locked:
                attempt_id = saved['attempt_id']
                # A pool without the additive migration has no stored grading:
                # report the legacy state instead of reading missing tables.
                if part_grading.has_schema(pool):
                    grade = part_grading.get(pool, attempt_id)
                    job = pool.connect().execute('SELECT status,error FROM part_grading_jobs WHERE attempt_id=?',
                                                  (attempt_id,)).fetchone()
                    child['grading_status'] = job['status'] if job else 'not_requested'
                    if grade:
                        child['grading_status'] = 'withdrawn' if grade['withdrawn'] else 'completed'
                    if disclosed:
                        child['grading'] = grade if grade and not grade['withdrawn'] else None
                        child['grading_error'] = job['error'] if job else None
                        if part['type'] in problem_parts.OBJECTIVE:
                            verdict = pool.attempt(attempt_id).get('verdict')
                            child['objective_verdict'] = bool(verdict) if verdict is not None else None
                    # Hide completion versus withdrawal while results are embargoed.
                    elif child['grading_status'] in {'completed', 'withdrawn'}:
                        child['grading_status'] = 'submitted'
            if disclosed:
                child['reference_answer'] = part.get('reference_answer', part.get('answer_key', ''))
                child['reference_reasoning'] = part.get('reference_reasoning', '')
                payload = (child.get('grading') or {}).get('payload') or {}
                if child['objective_verdict'] is not None:
                    payload = {'answer_conclusion': 'correct' if child['objective_verdict'] else 'wrong'}
                for dimension in ('answer', 'process'):
                    verdict = payload.get(dimension + '_conclusion')
                    if verdict:
                        counts[dimension][verdict] = counts[dimension].get(verdict, 0) + 1
            status = child['grading_status']
            counts['grading'][status] = counts['grading'].get(status, 0) + 1
            children.append(child)
        item['part_items'] = children
        item['part_summary'] = counts
        # The snapshot contains all siblings' solutions: it is never a learner field.
        item['draft'].pop('part_definitions', None)
        if item.get('payload'):
            for key in ('parts', 'solution', 'source_answer', 'micro_quiz'):
                item['payload'].pop(key, None)
        # Do not let the last child's legacy verdict look like the parent verdict.
        if len(parts) != 1 or parts[0]['id'] != 'whole':
            item.pop('attempt', None)
    if any(i.get('part_items') for i in result['items']):
        result.pop('result_counts', None)
    return result
