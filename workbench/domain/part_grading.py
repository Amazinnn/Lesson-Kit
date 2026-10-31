"""Pure validation and learner disclosure for independent grading dimensions."""

import json


def validate(payload, *, answering_type=None, learner_response=None):
    if not isinstance(payload, dict):
        raise ValueError('grading must be an object')
    allowed = {'answer_conclusion', 'process_conclusion', 'extracted_answer',
               'reference_answer', 'reference_reasoning', 'reference_origin', 'feedback'}
    if set(payload) - allowed:
        raise ValueError('unknown grading fields')
    for key in allowed - {'answer_conclusion', 'process_conclusion'}:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError('grading text must be a string')
    if not payload:
        raise ValueError('empty grading')
    if not ({'answer_conclusion', 'process_conclusion'} & set(payload)):
        raise ValueError('grading requires an applicable conclusion')
    if answering_type == 'proof' and ({'answer_conclusion', 'extracted_answer'} & set(payload)):
        raise ValueError('proof grading uses process only')
    if payload.get('answer_conclusion') == 'unprovided' and payload.get('extracted_answer'):
        raise ValueError('unprovided answer cannot have extraction')
    if learner_response is not None and not learner_response.strip() and payload.get('extracted_answer'):
        raise ValueError('blank learner response cannot have extraction')
    if 'needs_confirmation' in (payload.get('answer_conclusion'), payload.get('process_conclusion')) and not payload.get('feedback', '').strip():
        raise ValueError('needs confirmation requires an explanation')
    if payload.get('reference_origin') == 'agent_derived' and not payload.get('reference_reasoning', '').strip():
        raise ValueError('Agent-derived reference requires reasoning')
    if (payload.get('reference_answer') or payload.get('reference_reasoning')) and not payload.get('reference_origin'):
        raise ValueError('reference requires provenance')
    for key in ('answer_conclusion', 'process_conclusion'):
        choices = {'correct', 'wrong', 'needs_confirmation', 'unprovided'}
        if key == 'process_conclusion':
            choices.add('partially_correct')
        if key in payload and (not isinstance(payload[key], str) or payload[key] not in choices):
            raise ValueError('invalid conclusion')
    for key in allowed - {'answer_conclusion', 'process_conclusion'}:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError('grading text must be a string')
    if 'reference_origin' in payload and payload['reference_origin'] not in {'source', 'agent_derived'}:
        raise ValueError('invalid reference origin')
    return json.loads(json.dumps(payload))


def reveal(result, disclosed=False):
    """No grading/reference information is disclosed before learner reveal."""
    return result if disclosed else None
