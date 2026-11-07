"""Confirmed course learning preferences: one explicit workspace file.

The browser record `wb_settings_<workspace>` stays the interaction mirror. This
store is what a course exchange bundle carries, so only explicit, already
confirmed, non-sensitive learning values live here (`DATA_MODEL.md`
"Confirmed course learning preferences").
"""

import json
import os
import tempfile
import threading
from pathlib import Path


_LOCK = threading.Lock()

FILE_NAME = "course-preferences.json"

#: Boolean learning fields, each stored as a real JSON boolean.
BOOLEAN_FIELDS = ("showRating", "showSource")

#: Learning fields whose value is one of a closed set.
CHOICE_FIELDS = {
    "submissionGranularity": ("per_part", "whole_problem"),
    "revealTiming": ("per_item", "on_submit"),
}

FIELDS = BOOLEAN_FIELDS + tuple(CHOICE_FIELDS)


class CorruptPreferences(ValueError):
    """The stored projection cannot be read, so nothing may be written over it."""


def path(root):
    return Path(root) / ".lessonkit" / FILE_NAME


def load_preferences(root, course):
    """The confirmed values of `course`; no file means no projection yet."""
    stored = _read(root)
    if stored is None or stored[0] != _course(course):
        return {}
    return dict(stored[1])


def save_preferences(root, course, values):
    """Persist the explicit values of `course`; omitted fields keep their value."""
    if not isinstance(values, dict):
        raise ValueError("course preferences must be a JSON object")
    updates = _validate(values)
    if not updates:
        raise ValueError("no learning preference values to save")
    course = _course(course)
    with _LOCK:
        stored = _read(root)
        if stored is not None and stored[0] != course:
            raise ValueError(
                f"{FILE_NAME} already belongs to course {stored[0]!r}")
        merged = {**(stored[1] if stored else {}), **updates}
        _write(root, course, merged)
    return merged


def _course(course):
    value = str(course or "").strip()
    if not value:
        raise ValueError("a course identity is required")
    return value


def _validate(values):
    """Known learning fields only: appearance, credentials and Provider settings are refused."""
    unknown = sorted(set(values) - set(FIELDS))
    if unknown:
        raise ValueError("not learning preferences: " + ", ".join(unknown))
    checked = {}
    for key, value in values.items():
        if key in BOOLEAN_FIELDS:
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be true or false")
        elif value not in CHOICE_FIELDS[key]:
            raise ValueError(
                f"{key} must be one of {', '.join(CHOICE_FIELDS[key])}")
        checked[key] = value
    return checked


def _read(root):
    """The stored course identity and values, or None when nothing was saved."""
    stored_path = path(root)
    if not stored_path.is_file():
        return None
    try:
        stored = json.loads(stored_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CorruptPreferences(f"{FILE_NAME} is unreadable: {exc}") from exc
    if not isinstance(stored, dict):
        raise CorruptPreferences(f"{FILE_NAME} must hold a JSON object")
    course = stored.get("course")
    values = stored.get("values")
    if not isinstance(course, str) or not course.strip():
        raise CorruptPreferences(f"{FILE_NAME} records no course identity")
    if not isinstance(values, dict):
        raise CorruptPreferences(f"{FILE_NAME} records no values object")
    try:
        return course, _validate(values)
    except ValueError as exc:
        raise CorruptPreferences(f"{FILE_NAME} is invalid: {exc}") from exc


def _write(root, course, values):
    target = path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(
        {"course": course, "values": values}, ensure_ascii=False, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=target.parent,
            prefix=f".{target.name}.", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        _publish(temporary, target)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _publish(temporary, target):
    """One replacement step, so an interrupted write leaves the old file whole."""
    temporary.replace(target)
