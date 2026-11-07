"""Typed stored references inside exchange JSON columns.

Pure helpers: no pool, no database, no files. Every case names the writer that
produced the JSON so the converted spelling still satisfies the real reader.
"""

import copy
import json

import pytest

from workbench.data import attempts
from workbench.data.course_sync import REFERENCE_JSON_FIELDS
from workbench.domain import course_sync_references as references


protected_draft = {
    "stuck": False,
    "reference_viewed": True,
    "answer": "我的草稿 attempt_id: 7",
    "choices": ["A", "B"],
    "sequence": 4,
    "part_definitions": [
        {"id": "whole", "type": "subjective", "answer_key": "x=2",
         "reference_answer": "由勾股定理得 $x=2$"},
    ],
    "parts": {
        "whole": {"answer": "x=2", "choices": [], "stuck": False,
                  "reference_viewed": True, "sequence": 2, "attempt_id": 9},
    },
}

items = [
    {
        "position": 0,
        "item_type": "problem",
        "item_id": "dmath-ch06-prob-001",
        "direction": "",
        "state": "answered",
        "attempt_id": 7,
        "content_revision": 3,
        "draft": copy.deepcopy(protected_draft),
        "draft_sequence": 5,
    },
    {
        "position": 1,
        "item_type": "problem",
        "item_id": "dmath-ch06-prob-002",
        "direction": "",
        "state": "pending",
        "attempt_id": None,
        "content_revision": 1,
        "draft": {},
        "draft_sequence": 0,
    },
]

checkpoint = {
    "source_kind": "paper",
    "source_ref": "ps-001",
    "source_label": "第一卷",
    "kp_ids": ["dmath-ch06-kp-001"],
    "practice_mode": "problem",
    "rating_mode": "self",
    "started_at": "2026-10-11 08:00:00",
    "cursor": 1,
    "reveal_timing": "on_submit",
    "execution_id": 3,
    "paper_generation": 4,
    "items": copy.deepcopy(items),
}

attempt_result = {
    "problem_id": "dmath-ch06-prob-001",
    "attempt_id": 12,
    "status": "mastered",
    "rating": 5,
    "graded": True,
    "note_recorded": True,
    "due_at": None,
    "changes": [{"text": "signal kp: high", "attempt_id": 999}],
    "paper_id": "ps-001",
    "paper_position": 2,
    "paper_action": "import",
    "paper": {
        "paper_id": "ps-001",
        "mode": "active",
        "execution_id": 3,
        "reveal_timing": "on_submit",
        "positions": {"dmath-ch06-prob-001": 2},
        "actions": {"dmath-ch06-prob-001": "import"},
        "progress": {"total": 3, "completed": 1},
        "completed": False,
        "run_id": 5,
        "rebound": ["dmath-ch06-prob-001"],
        "previous_states": {
            "dmath-ch06-prob-001": {"state": "pending", "attempt_id": 11},
            "dmath-ch06-prob-002": {"state": "answered", "attempt_id": None},
        },
    },
}

snapshot = {
    "problem_id": "dmath-ch06-prob-001",
    "targets": ["dmath-ch06-kp-001"],
    "rows": {
        "problem_progress": [
            {"problem_id": "dmath-ch06-prob-001", "status": "wrong",
             "note": "上次 attempt_id 12 的错因：符号", "updated_at": "2026-10-11 08:00:00"},
        ],
        "learner_signals": [
            {"signal_id": "sig-1", "target_type": "node", "target_id": "k1",
             "signal_type": "weak_node", "weight": "high", "evidence_count": 2,
             "attempt_id": 12, "note": "attempt_id: 12 是老师记的"},
        ],
    },
}

part_submit_payload = {
    "kind": "part-submit",
    "execution_id": 3,
    "position": 1,
    "part_id": "b",
    "context": {"execution_id": 3, "paper_id": "ps-001", "paper_generation": 2,
                "item_id": "dmath-ch06-prob-001", "content_revision": 3, "position": 1},
}

attempt_payload = {
    "kind": "attempt",
    "problem_id": "dmath-ch06-prob-001",
    "answer_text": "我的作答：$x=2$",
    "verdict": 1,
    "choices": ["A"],
    "practice_position": 1,
    "stuck": False,
    "practice_context": {"execution_id": 3, "paper_id": "ps-001",
                         "paper_generation": 2, "item_id": "dmath-ch06-prob-001",
                         "content_revision": 3, "position": 1},
}

feedback_payload = {
    "kind": "feedback",
    "item_type": "problem",
    "item_id": "dmath-ch06-prob-001",
    "rating": 4,
    "note": "note 里也写了 attempt_id 12",
    "direction": "",
    "attempt_id": 12,
}

edit_payload = {
    "kind": "feedback",
    "item_type": "problem",
    "item_id": "dmath-ch06-prob-001",
    "rating": 4,
    "note": None,
    "direction": "",
    "attempt_id": 12,
    "edit_existing": True,
    "expected_rating": 4,
    "expected_note": None,
}

grading_request = [
    12,
    "dmath-ch06-prob-001",
    "b",
    3,
    0,
    {"score": 2, "comment": "符号写错，思路对", "attempt_id": 12},
    False,
]


def exporter():
    """Local integer -> portable stable reference, recording each dependency."""
    seen = []

    def resolve(table, value):
        assert type(value) is int, value
        seen.append((table, value))
        return f"row/{table}/{value}"

    return resolve, seen


def importer(local_ids):
    """Portable stable reference -> this installation's own integer identity."""
    def resolve(table, value):
        assert isinstance(value, str), value
        assert table in local_ids and value in local_ids[table], value
        return local_ids[table][value]

    return resolve


local_ids = {
    "problem_attempts": {f"row/problem_attempts/{number}": number + 1000
                         for number in (7, 9, 11, 12)},
    "practice_execution_ids": {"row/practice_execution_ids/3": 3003},
    "practice_runs": {"row/practice_runs/5": 5005},
}


# -- practice_runs.items_json / paper_state.checkpoint_json -------------------

def test_items_json_roundtrip_moves_item_and_part_attempts_to_local_ids():
    resolve, seen = exporter()
    portable = references.convert_json("practice_runs", "items_json", items, resolve)
    assert seen == [("problem_attempts", 7), ("problem_attempts", 9)]
    assert portable[0]["attempt_id"] == "row/problem_attempts/7"
    assert portable[0]["draft"]["parts"]["whole"]["attempt_id"] == "row/problem_attempts/9"
    assert portable[1]["attempt_id"] is None
    assert portable[0]["draft"] == {**protected_draft,
                                    "parts": {"whole": {**protected_draft["parts"]["whole"],
                                                        "attempt_id": "row/problem_attempts/9"}}}
    local = references.convert_json(
        "practice_runs", "items_json",
        json.loads(references.serialize_json("practice_runs", "items_json", portable)),
        importer(local_ids))
    assert local[0]["attempt_id"] == 1007
    assert local[0]["draft"]["parts"]["whole"]["attempt_id"] == 1009
    assert local[1]["attempt_id"] is None
    expected = copy.deepcopy(items)
    expected[0]["attempt_id"] = 1007
    expected[0]["draft"]["parts"]["whole"]["attempt_id"] = 1009
    assert local == expected


def test_checkpoint_json_moves_the_execution_and_keeps_presentation_values():
    resolve, seen = exporter()
    portable = references.convert_json(
        "paper_state", "checkpoint_json", checkpoint, resolve)
    assert seen == [("practice_execution_ids", 3),
                    ("problem_attempts", 7), ("problem_attempts", 9)]
    assert portable["execution_id"] == "row/practice_execution_ids/3"
    assert portable["items"][0]["attempt_id"] == "row/problem_attempts/7"
    assert portable["items"][0]["draft"]["parts"]["whole"]["attempt_id"] == \
        "row/problem_attempts/9"
    assert {key: value for key, value in portable.items()
            if key not in {"execution_id", "items"}} == \
        {key: value for key, value in checkpoint.items()
         if key not in {"execution_id", "items"}}
    local = references.convert_json(
        "paper_state", "checkpoint_json",
        json.loads(references.serialize_json("paper_state", "checkpoint_json", portable)),
        importer(local_ids))
    assert local["execution_id"] == 3003
    assert local["items"][0]["attempt_id"] == 1007
    assert local["items"][1]["attempt_id"] is None


def test_item_fields_that_only_look_like_references_stay_verbatim():
    """execution_id on an archived item is derived, never a stored reference."""
    resolve, seen = exporter()
    archived = [{"position": 0, "item_type": "problem", "item_id": "p1",
                 "state": "pending", "attempt_id": None, "execution_id": 3,
                 "run_id": 5, "draft": {"answer": "attempt_id: 12", "attempt_id": 12}}]
    assert references.convert_json("practice_runs", "items_json", archived, resolve) == archived
    assert seen == []


# -- attempt_operations.result ------------------------------------------------

def test_attempt_result_moves_only_the_declared_reference_paths():
    resolve, seen = exporter()
    portable = references.convert_json("attempt_operations", "result", attempt_result, resolve)
    assert seen == [("problem_attempts", 12), ("practice_execution_ids", 3),
                    ("practice_runs", 5), ("problem_attempts", 11)]
    assert portable["attempt_id"] == "row/problem_attempts/12"
    assert portable["paper"]["execution_id"] == "row/practice_execution_ids/3"
    assert portable["paper"]["run_id"] == "row/practice_runs/5"
    assert portable["paper"]["previous_states"] == {
        "dmath-ch06-prob-001": {"state": "pending", "attempt_id": "row/problem_attempts/11"},
        "dmath-ch06-prob-002": {"state": "answered", "attempt_id": None},
    }
    assert portable["paper"]["positions"] == {"dmath-ch06-prob-001": 2}
    assert portable["paper"]["progress"] == {"total": 3, "completed": 1}
    assert portable["changes"] == [{"text": "signal kp: high", "attempt_id": 999}]
    local = references.convert_json(
        "attempt_operations", "result",
        json.loads(references.serialize_json("attempt_operations", "result", portable)),
        importer(local_ids))
    assert local["attempt_id"] == 1012
    assert local["paper"]["execution_id"] == 3003
    assert local["paper"]["run_id"] == 5005
    assert local["paper"]["previous_states"]["dmath-ch06-prob-001"]["attempt_id"] == 1011
    assert local["changes"] == [{"text": "signal kp: high", "attempt_id": 999}]


def test_attempt_result_without_paper_or_run_id_is_unchanged():
    resolve, seen = exporter()
    result = {"problem_id": "p1", "attempt_id": 12, "changes": []}
    portable = references.convert_json("attempt_operations", "result", result, resolve)
    assert portable == {"problem_id": "p1", "attempt_id": "row/problem_attempts/12",
                        "changes": []}
    assert seen == [("problem_attempts", 12)]
    no_run = copy.deepcopy(attempt_result)
    no_run["paper"]["run_id"] = None
    portable = references.convert_json("attempt_operations", "result", no_run, exporter()[0])
    assert portable["paper"]["run_id"] is None


# -- attempt_operations.pre_state / post_state --------------------------------

@pytest.mark.parametrize("field", ["pre_state", "post_state"])
def test_effect_snapshots_hold_no_reference_and_travel_verbatim(field):
    """the four snapshotted row sets declare no attempt/execution column."""
    resolve, seen = exporter()
    assert references.convert_json("attempt_operations", field, snapshot, resolve) == snapshot
    assert seen == []


# -- practice_request_operations.payload --------------------------------------

def test_part_submit_payload_moves_the_execution_in_both_positions():
    resolve, seen = exporter()
    portable = references.convert_json(
        "practice_request_operations", "payload", part_submit_payload, resolve)
    assert seen == [("practice_execution_ids", 3), ("practice_execution_ids", 3)]
    assert portable["execution_id"] == "row/practice_execution_ids/3"
    assert portable["context"]["execution_id"] == "row/practice_execution_ids/3"
    assert portable["context"]["paper_id"] == "ps-001"
    assert portable["context"]["item_id"] == "dmath-ch06-prob-001"
    assert portable["position"] == part_submit_payload["position"]
    assert portable["part_id"] == "b"


def test_payload_with_a_null_context_is_still_converted():
    resolve, seen = exporter()
    payload = dict(part_submit_payload, context=None)
    portable = references.convert_json(
        "practice_request_operations", "payload", payload, resolve)
    assert portable["context"] is None
    assert portable["execution_id"] == "row/practice_execution_ids/3"
    assert seen == [("practice_execution_ids", 3)]


def test_attempt_and_feedback_payloads_move_only_machine_references():
    resolve, seen = exporter()
    portable = references.convert_json(
        "practice_request_operations", "payload", attempt_payload, resolve)
    assert portable["practice_context"]["execution_id"] == "row/practice_execution_ids/3"
    assert portable["answer_text"] == attempt_payload["answer_text"]
    assert portable["verdict"] == 1
    assert seen == [("practice_execution_ids", 3)]

    resolve, seen = exporter()
    portable = references.convert_json(
        "practice_request_operations", "payload", feedback_payload, resolve)
    assert portable["attempt_id"] == "row/problem_attempts/12"
    assert portable["note"] == feedback_payload["note"]
    assert seen == [("problem_attempts", 12)]


def test_paper_submit_payload_moves_the_execution_through_its_draft_contexts():
    """active_practice.submit builds every draft's own practice_context."""
    resolve, seen = exporter()
    payload = {
        "kind": "paper-submit",
        "execution_id": 3,
        "drafts": [
            {"position": 0, "sequence": 2, "draft": {"answer": "我的答案"},
             "practice_context": {"execution_id": 3, "paper_id": "ps-001",
                                  "paper_generation": 2, "item_id": "p1",
                                  "content_revision": 3, "position": 0}},
            {"position": 1, "sequence": 1, "draft": {"stuck": True},
             "practice_context": {"execution_id": 3, "paper_id": "ps-001",
                                  "paper_generation": 2, "item_id": "p2",
                                  "content_revision": 1, "position": 1}},
        ],
    }
    portable = references.convert_json(
        "practice_request_operations", "payload", payload, resolve)
    assert seen == [("practice_execution_ids", 3), ("practice_execution_ids", 3),
                    ("practice_execution_ids", 3)]
    assert portable["execution_id"] == "row/practice_execution_ids/3"
    assert [entry["practice_context"]["execution_id"] for entry in portable["drafts"]] == \
        ["row/practice_execution_ids/3"] * 2
    assert [entry["draft"] for entry in portable["drafts"]] == \
        [entry["draft"] for entry in payload["drafts"]]
    assert [entry["sequence"] for entry in portable["drafts"]] == [2, 1]


# -- practice_request_operations.result --------------------------------------

def test_browser_result_moves_attempt_ids_and_keeps_learner_facing_sentences():
    resolve, seen = exporter()
    ids = {"attempt_ids": [21, 22], "replay": False}
    assert references.convert_json(
        "practice_request_operations", "result", ids, resolve) == {
            "attempt_ids": ["row/problem_attempts/21", "row/problem_attempts/22"],
            "replay": False}
    assert seen == [("problem_attempts", 21), ("problem_attempts", 22)]

    resolve, seen = exporter()
    recorded = {"attempt_id": 21, "problem_id": "p1", "recorded": True,
                "status": "stuck", "due_at": "2026-10-12"}
    portable = references.convert_json(
        "practice_request_operations", "result", recorded, resolve)
    assert portable["attempt_id"] == "row/problem_attempts/21"
    assert seen == [("problem_attempts", 21)]

    resolve, seen = exporter()
    changes = ["signal dmath-ch06-kp-001: medium (2x)", "progress problem -> wrong"]
    assert references.convert_json(
        "practice_request_operations", "result", changes, resolve) == changes
    assert seen == []


def test_edited_feedback_result_keeps_the_event_identity_it_cannot_resolve_alone():
    resolve, seen = exporter()
    result = {"edited": True, "attempt_id": 12, "feedback_event_id": 44}
    assert references.convert_json(
        "practice_request_operations", "result", result, resolve) == {
            "edited": True, "attempt_id": "row/problem_attempts/12",
            "feedback_event_id": 44}
    assert seen == [("problem_attempts", 12)]


def test_paper_submit_result_moves_the_run_and_the_cached_practice_projection():
    """active_practice.submit caches completion, run, and the whole projection."""
    resolve, seen = exporter()
    result = {"completed": True, "replay": False, "run_id": 5, "execution_id": 3}
    portable = references.convert_json(
        "practice_request_operations", "result", result, resolve)
    assert seen == [("practice_execution_ids", 3), ("practice_runs", 5)]
    assert portable == {"completed": True, "replay": False,
                        "run_id": "row/practice_runs/5",
                        "execution_id": "row/practice_execution_ids/3"}

    resolve, seen = exporter()
    stuck = {"practice": copy.deepcopy(checkpoint)}
    portable = references.convert_json("practice_request_operations", "result", stuck, resolve)
    assert seen == [("practice_execution_ids", 3),
                    ("problem_attempts", 7), ("problem_attempts", 9)]
    assert portable["practice"]["execution_id"] == "row/practice_execution_ids/3"
    assert portable["practice"]["items"][0]["draft"]["parts"]["whole"]["attempt_id"] == \
        "row/problem_attempts/9"
    assert portable["practice"]["cursor"] == checkpoint["cursor"]

    # attempt writes nest one more level: mark() returns {completed, replay, practice}.
    resolve, seen = exporter()
    marked = {"attempt_id": 12, "due_at": "2026-10-15",
              "practice": {"completed": False, "replay": False,
                           "practice": copy.deepcopy(checkpoint)}}
    portable = references.convert_json("practice_request_operations", "result", marked, resolve)
    assert seen == [("problem_attempts", 12), ("practice_execution_ids", 3),
                    ("problem_attempts", 7), ("problem_attempts", 9)]
    assert portable["practice"]["practice"]["execution_id"] == "row/practice_execution_ids/3"
    assert portable["practice"]["practice"]["items"][0]["attempt_id"] == "row/problem_attempts/7"
    assert portable["practice"]["completed"] is False


# -- part_grading_revisions.request_json -------------------------------------

def test_grading_request_moves_element_zero_and_leaves_checked_grading_opaque():
    resolve, seen = exporter()
    portable = references.convert_json(
        "part_grading_revisions", "request_json", grading_request, resolve)
    assert seen == [("problem_attempts", 12)]
    assert portable[0] == "row/problem_attempts/12"
    assert portable[1:] == grading_request[1:]
    assert portable[5] == grading_request[5]

    local = references.convert_json(
        "part_grading_revisions", "request_json",
        json.loads(references.serialize_json(
            "part_grading_revisions", "request_json", portable)),
        importer(local_ids))
    assert local[0] == 1012
    assert local[1:] == grading_request[1:]


def test_grading_request_payload_json_is_opaque():
    resolve, seen = exporter()
    graded = {"score": 2, "comment": "attempt_id 12 是学生的编号", "attempt_id": 12}
    assert references.convert_json(
        "part_grading_revisions", "payload_json", graded, resolve) == graded
    assert seen == []


# -- drafts ------------------------------------------------------------------

def test_convert_draft_moves_only_machine_part_attempts():
    resolve, seen = exporter()
    portable = references.convert_draft(protected_draft, resolve)
    assert seen == [("problem_attempts", 9)]
    assert portable == {**protected_draft,
                        "parts": {"whole": {**protected_draft["parts"]["whole"],
                                            "attempt_id": "row/problem_attempts/9"}}}
    assert portable["answer"] == protected_draft["answer"]
    assert portable["part_definitions"] == protected_draft["part_definitions"]
    assert references.convert_draft({}, resolve) == {}
    assert references.convert_draft({"answer": "attempt_id: 9"}, resolve) == \
        {"answer": "attempt_id: 9"}


# -- reader contracts --------------------------------------------------------

def test_every_reference_field_has_a_conversion():
    for table, fields in REFERENCE_JSON_FIELDS.items():
        for field in fields:
            references.convert_json(table, field, {}, lambda table, value: value)


def test_grading_request_keeps_the_writer_spelling_that_mutate_compares():
    """part_grading.mutate re-derives and compares request_json byte for byte."""
    converted = list(grading_request)
    converted[0] = "row/problem_attempts/12"
    assert references.serialize_json(
        "part_grading_revisions", "request_json", converted) == \
        json.dumps(converted, sort_keys=True)
    assert references.serialize_json(
        "part_grading_revisions", "request_json", converted) == \
        json.dumps(converted, sort_keys=True, ensure_ascii=True,
                   separators=(", ", ": "))


def test_compact_payload_keeps_the_writer_spelling_that_replay_compares():
    """attempts._browser_replay compares the stored payload string exactly."""
    body = {key: value for key, value in part_submit_payload.items()}
    portable = references.convert_json(
        "practice_request_operations", "payload", body, exporter()[0])
    context = {**part_submit_payload["context"], "execution_id": "row/practice_execution_ids/3"}
    assert references.serialize_json(
        "practice_request_operations", "payload", portable) == \
        attempts._browser_payload("part-submit", execution_id="row/practice_execution_ids/3",
                                  position=1, part_id="b", context=context)


def test_payloads_the_writers_re_dump_keep_the_default_separators():
    """attempts.record_attempt/record_browser_feedback re-dump with json.dumps' own separators."""
    portable = references.convert_json(
        "practice_request_operations", "payload", attempt_payload, exporter()[0])
    compact = attempts._browser_payload(
        "attempt", problem_id="dmath-ch06-prob-001", answer_text="我的作答：$x=2$",
        verdict=1, choices=["A"], practice_position=1, stuck=False)
    context = {**attempt_payload["practice_context"], "execution_id": "row/practice_execution_ids/3"}
    expected = json.dumps(dict(json.loads(compact), practice_context=context), sort_keys=True)
    assert references.serialize_json(
        "practice_request_operations", "payload", portable) == expected

    portable = references.convert_json(
        "practice_request_operations", "payload", edit_payload, exporter()[0])
    compact = attempts._browser_payload(
        "feedback", item_type="problem", item_id="dmath-ch06-prob-001", rating=4,
        note=None, direction="", attempt_id="row/problem_attempts/12")
    expected = json.dumps(dict(json.loads(compact), edit_existing=True,
                               expected_rating=4, expected_note=None), sort_keys=True)
    assert references.serialize_json(
        "practice_request_operations", "payload", portable) == expected


def test_payloads_written_directly_stay_compact_even_with_a_practice_context():
    """active_practice.mark_stuck_draft and submit write one compact payload."""
    payload = {"kind": "stuck-draft", "execution_id": 3, "position": 1,
               "practice_context": copy.deepcopy(attempt_payload["practice_context"])}
    portable = references.convert_json(
        "practice_request_operations", "payload", payload, exporter()[0])
    context = {**payload["practice_context"], "execution_id": "row/practice_execution_ids/3"}
    assert references.serialize_json(
        "practice_request_operations", "payload", portable) == \
        attempts._browser_payload("stuck-draft", execution_id="row/practice_execution_ids/3",
                                  position=1, practice_context=context)
    assert '", "' not in references.serialize_json(
        "practice_request_operations", "payload", portable)


def test_other_remapped_json_uses_compact_sorted_spelling():
    value = {"attempt_id": "row/problem_attempts/7", "note": "中文 attempt_id"}
    assert references.serialize_json("practice_runs", "items_json", value) == \
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert references.serialize_json("attempt_operations", "result", value) == \
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# -- input is never mutated --------------------------------------------------

@pytest.mark.parametrize("table,field,value", [
    ("practice_runs", "items_json", items),
    ("paper_state", "checkpoint_json", checkpoint),
    ("attempt_operations", "result", attempt_result),
    ("attempt_operations", "pre_state", snapshot),
    ("attempt_operations", "post_state", snapshot),
    ("practice_request_operations", "payload", part_submit_payload),
    ("practice_request_operations", "payload", attempt_payload),
    ("practice_request_operations", "result", {"attempt_ids": [21], "replay": False}),
    ("part_grading_revisions", "request_json", grading_request),
    ("part_grading_revisions", "payload_json", grading_request[5]),
])
def test_conversion_leaves_the_source_value_untouched(table, field, value):
    before = copy.deepcopy(value)
    references.convert_json(table, field, value, exporter()[0])
    assert value == before
