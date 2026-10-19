"""Pure answer grading used by explicit Paper submission."""

from workbench.domain.practice_submission import grade_answer


def problem(quiz_type, answer_key=None):
    quiz = {'quiz_type': quiz_type}
    if answer_key is not None:
        quiz['answer_key'] = answer_key
    return {'micro_quiz': quiz}


def test_missing_answer_key_stays_ungraded():
    assert grade_answer(problem('single_choice'), '', ['A']) is None
    assert grade_answer({'micro_quiz': {}}, 'response', []) is None


def test_single_choice_uses_selected_option_or_text_answer():
    item = problem('single_choice', 'B')
    assert grade_answer(item, '', ['B']) is True
    assert grade_answer(item, '', ['A']) is False
    assert grade_answer(item, 'B', []) is True


def test_yes_no_uses_selected_option():
    item = problem('yes_no', '是')
    assert grade_answer(item, '', ['是']) is True
    assert grade_answer(item, '', ['否']) is False


def test_multiple_choice_uses_set_normalized_selection():
    item = problem('multiple_choice', ['A', 'C'])
    assert grade_answer(item, '', ['C', 'A']) is True
    assert grade_answer(item, '', ['A']) is False


def test_non_objective_text_answer_has_no_objective_verdict():
    item = problem('text', 'reference')
    assert grade_answer(item, 'my response', []) is None
