"""The answering/marking content axis, separate from explanation and metadata."""

import json


def signature(problem):
    value = dict(problem or {})
    quiz = value.get('micro_quiz') or {}
    if isinstance(quiz, str):
        quiz = json.loads(quiz)
    modes = value.get('practice_modes') or []
    if isinstance(modes, str):
        modes = json.loads(modes)
    return (value.get('problem_text'), tuple(sorted(modes)),
            json.dumps({key: quiz.get(key) for key in ('quiz_type', 'options', 'answer_key')},
                       ensure_ascii=False, sort_keys=True))
