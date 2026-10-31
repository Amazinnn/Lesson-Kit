"""Pure validation and learner disclosure for independent grading dimensions."""

import json


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('grading must be an object')
    allowed = {'answer_conclusion', 'process_conclusion', 'extracted_answer',
               'reference_answer', 'reference_reasoning', 'reference_origin', 'feedback'}
    if set(payload) - allowed:
        raise ValueError('unknown grading fields')
    for key in ('answer_conclusion', 'process_conclusion'):
        choices = {'correct', 'wrong', 'needs_confirmation', 'unprovided'}
        if key == 'process_conclusion':
            choices.add('partially_correct')
        if key in payload and payload[key] not in choices:
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
