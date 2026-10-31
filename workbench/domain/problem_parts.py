"""Saved problem-part shapes; no parsing or IO during practice."""

import re

OBJECTIVE = {'yes_no', 'single_choice', 'multiple_choice'}
TYPES = OBJECTIVE | {'calculation', 'proof', 'open_response'}


def validate(parts):
    if parts is None:
        return None
    if not isinstance(parts, list):
        raise ValueError('parts must be a list or null')
    seen = set()
    allowed = {'id', 'prompt', 'type', 'options', 'answer_key', 'reference_answer',
               'reference_reasoning', 'short_answer'}
    for part in parts:
        if not isinstance(part, dict) or set(part) - allowed:
            raise ValueError('invalid part fields')
        identity = part.get('id')
        if not isinstance(identity, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', identity) or identity in seen:
            raise ValueError('part id must be unique and readable')
        seen.add(identity)
        if part.get('type') not in TYPES or not isinstance(part.get('prompt'), str) or not part['prompt'].strip():
            raise ValueError('part needs a supported type and nonempty prompt')
        for key in ('reference_answer', 'reference_reasoning'):
            if key in part and not isinstance(part[key], str):
                raise ValueError('part reference must be text')
        if 'short_answer' in part and type(part['short_answer']) is not bool:
            raise ValueError('short_answer must be boolean')
        if part['type'] == 'proof' and (part.get('short_answer') or part.get('reference_answer')):
            raise ValueError('proof parts use reasoning only')
        if part['type'] in OBJECTIVE:
            options = ['是', '否'] if part['type'] == 'yes_no' else part.get('options')
            if not isinstance(options, list) or len(options) < 2 or not all(isinstance(x, str) and x.strip() for x in options) or len(set(options)) != len(options):
                raise ValueError('objective part requires distinct options')
            key = part.get('answer_key')
            if key is not None:
                keys = key if part['type'] == 'multiple_choice' else [key]
                if not isinstance(keys, list) or not keys or not all(isinstance(x, str) and x in options for x in keys) or len(set(keys)) != len(keys):
                    raise ValueError('part answer key must name its options')
    return parts


def definitions(problem):
    if not problem:
        return []
    if problem.get('parts'):
        return problem['parts']
    if problem.get('micro_quiz'):
        return []  # legacy objective items keep their existing execution path
    kind = problem.get('problem_type')
    kind = kind if kind in {'proof', 'calculation'} else 'open_response'
    return [{'id': 'whole', 'prompt': '', 'type': kind,
             'short_answer': kind != 'proof' and bool(problem.get('source_answer')),
             'reference_answer': '' if kind == 'proof' else problem.get('source_answer') or '',
             'reference_reasoning': problem.get('solution') or ''}]


def has_final(part):
    return part['type'] == 'calculation' or bool(part.get('short_answer'))


def objective_grade(part, choices):
    key = part.get('answer_key')
    if key is None:
        return None
    return set(choices) == set(key if isinstance(key, list) else [key])
