"""Micro-quiz content contract (pure rules)."""

QUIZ_TYPES = ("yes_no", "single_choice", "multiple_choice")
RETIRED_QUIZ_TYPES = ("closest_answer", "short_answer")
OBJECTIVE_TYPES = ("yes_no", "single_choice", "multiple_choice")
YES_NO_OPTIONS = ["是", "否"]
MAX_OPTIONS = 6
MAX_STEM_CHARS = 200

_PRACTICE_MODES = {
    "yes_no": ["yes_no"],
    "single_choice": ["micro"],
    "multiple_choice": ["micro"],
}


def practice_modes_for(quiz_type):
    """Practice modes a quiz type is eligible for (pull marks are explicit)."""
    return list(_PRACTICE_MODES.get(quiz_type, []))


def is_objective(quiz_type):
    return quiz_type in OBJECTIVE_TYPES


def validate_payload(quiz_type, payload):
    """Return a list of contract errors; empty means the payload is valid.

    The stem lives in problem_text and is validated by the caller, which also
    owns the knowledge-point and identity rules.
    """
    errors = []
    if quiz_type in RETIRED_QUIZ_TYPES:
        return [f"retired quiz type: {quiz_type}"]
    if quiz_type not in QUIZ_TYPES:
        return [f"unknown quiz type: {quiz_type}"]
    if not isinstance(payload, dict):
        return ["micro_quiz payload must be an object"]

    options = payload.get("options")
    answer = payload.get("answer_key")
    if not isinstance(payload.get("error_reason"), str) or not payload["error_reason"].strip():
        errors.append("error_reason is required")
    if not isinstance(payload.get("source_evidence"), str) or not payload["source_evidence"].strip():
        errors.append("source_evidence is required")

    if quiz_type == "yes_no":
        if options is not None and options != YES_NO_OPTIONS:
            errors.append("yes_no options must be the default 是/否 pair")
        if answer not in YES_NO_OPTIONS:
            errors.append("yes_no answer_key must be 是 or 否")
    elif quiz_type in ("single_choice", "multiple_choice"):
        if not isinstance(options, list) or not 2 <= len(options) <= MAX_OPTIONS:
            errors.append("choice items need 2-6 options")
        elif len(set(options)) != len(options):
            errors.append("options must be unique")
        if quiz_type == "single_choice":
            if not isinstance(options, list) or answer not in (options or []):
                errors.append("answer_key must be one of the options")
        elif not isinstance(answer, list) or not answer or not isinstance(options, list) \
                or not set(answer) <= set(options):
            errors.append("answer_key must be a non-empty subset of the options")
    else:
        if options:
            errors.append(f"{quiz_type} items take no options")
        if not isinstance(answer, str) or not answer.strip():
            errors.append(f"{quiz_type} answer_key needs a reference answer")
    return errors


def validate_problem_row(row):
    """Validate one problem row carrying micro-quiz content.

    Returns contract errors across identity, stem, marking, and payload.
    """
    errors = []
    quiz_type = (row.get("micro_quiz") or {}).get("quiz_type")
    modes = row.get("practice_modes")
    if not isinstance(row.get("kp_ids"), list) or len(row["kp_ids"]) != 1:
        errors.append("a micro quiz maps to exactly one knowledge point")
    stem = row.get("problem_text")
    if not isinstance(stem, str) or not stem.strip():
        errors.append("stem (problem_text) is required")
    elif len(stem) > MAX_STEM_CHARS:
        errors.append(f"stem exceeds {MAX_STEM_CHARS} characters; "
                      "long content belongs to the exam mode")
    if not isinstance(modes, list) or not modes:
        errors.append("practice_modes marking is required for a micro quiz")
    errors.extend(validate_payload(quiz_type, row.get("micro_quiz")))
    if quiz_type in QUIZ_TYPES and isinstance(modes, list):
        allowed = set(practice_modes_for(quiz_type))
        if not set(modes) <= allowed:
            errors.append(f"practice_modes for {quiz_type} must be within {sorted(allowed)}")
    return errors


def check_answer(item, submitted):
    """Grade an objective submission; non-objective items return None.

    submitted is the option text (yes_no / single_choice) or a list of option
    texts (multiple_choice).
    """
    payload = item.get("micro_quiz") or {}
    quiz_type = payload.get("quiz_type")
    if not is_objective(quiz_type):
        return None
    answer = payload.get("answer_key")
    if quiz_type == "multiple_choice":
        if not isinstance(submitted, list):
            return False
        return sorted(submitted) == sorted(answer)
    return submitted == answer
