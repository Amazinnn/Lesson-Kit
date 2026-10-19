"""Pure answer normalization and optional objective grading for Paper submit."""

from workbench.domain import micro_quiz


def grade_answer(problem, answer_text, choices):
    """Return a verdict only when the problem carries a usable objective key."""
    quiz = (problem or {}).get('micro_quiz') or {}
    if not micro_quiz.has_answer_key(quiz):
        return None
    if quiz.get('quiz_type') == 'multiple_choice':
        submitted = choices
    else:
        submitted = choices[0] if choices else answer_text
    return micro_quiz.check_answer(problem, submitted)
