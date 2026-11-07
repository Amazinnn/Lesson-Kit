"""Three-way exchange decisions stay pure and distinguish absence from deletion."""

import copy

from workbench.domain.course_sync import plan_exchange


def asset(value, dependencies=None, deleted=False):
    return {"kind": "test", "content": value, "depends_on": dependencies or [],
            "deleted": deleted}


def test_three_way_decisions_and_inputs_are_preserved():
    scenarios = [
        ({}, {}, {"a": asset(1)}, ["a"], [], []),
        ({}, {"a": asset(1)}, {}, [], ["a"], []),
        ({"a": asset(1)}, {"a": asset(1)}, {"a": asset(2)}, ["a"], [], []),
        ({"a": asset(1)}, {"a": asset(2)}, {"a": asset(1)}, [], ["a"], []),
        ({"a": asset(1)}, {"a": asset(2)}, {"a": asset(2)}, [], [], []),
        ({"a": asset(1)}, {"a": asset(2)}, {"a": asset(3)}, [], [], ["a"]),
        ({"a": asset(1)}, {"a": asset(2)}, {"a": asset(None, deleted=True)}, [], [], ["a"]),
    ]
    for base, local, incoming, changes, outgoing, conflicts in scenarios:
        snapshot = copy.deepcopy((base, local, incoming))
        result = plan_exchange(base, local, incoming)
        assert [item["identity"] for item in result["changes"]] == changes
        assert [item["identity"] for item in result["outgoing"]] == outgoing
        assert [item["identity"] for item in result["conflicts"]] == conflicts
        assert (base, local, incoming) == snapshot


def test_missing_tracked_file_does_not_delete_or_overwrite():
    for local, incoming in [({}, {"a": asset(2)}), ({"a": asset(2)}, {})]:
        result = plan_exchange({"a": asset(1)}, local, incoming)
        assert not result["changes"] and not result["outgoing"]
        assert result["errors"][0]["code"] == "missing_asset"


def test_explicit_deletion_and_transport_metadata():
    before = asset("original")
    after = asset("original") | {"revision": 8, "export_id": "different"}
    assert plan_exchange({"a": before}, {"a": before}, {"a": after})["unchanged"] == ["a"]
    result = plan_exchange({"a": before}, {"a": before}, {"a": asset(None, deleted=True)})
    assert result["changes"][0]["action"] == "delete"


def test_histories_and_question_drafts_merge_independently():
    base = {"draft/1": asset("a"), "draft/2": asset("b")}
    local = base | {"draft/1": asset("changed a"), "attempt/device-a/1": asset("answer a")}
    incoming = base | {"draft/2": asset("changed b"), "attempt/device-b/1": asset("answer b")}
    result = plan_exchange(base, local, incoming)
    assert not result["conflicts"] and not result["errors"]
    assert [x["identity"] for x in result["changes"]] == ["attempt/device-b/1", "draft/2"]
    assert [x["identity"] for x in result["outgoing"]] == ["attempt/device-a/1", "draft/1"]


def test_invalid_dependencies_block_transitive_dependents_only():
    incoming = {"a": asset(1, ["missing"]), "b": asset(2, ["a"]), "ok": asset(3)}
    result = plan_exchange({}, {}, incoming)
    assert [x["identity"] for x in result["changes"]] == ["ok"]
    assert {x["identity"] for x in result["errors"]} == {"a", "b"}


def test_dependency_conflict_blocks_dependent_mutation():
    result = plan_exchange({"a": asset(0)}, {"a": asset(1)},
                           {"a": asset(2), "b": asset(3, ["a"])})
    assert [x["identity"] for x in result["conflicts"]] == ["a"]
    assert not result["changes"]
    assert result["errors"][0]["identity"] == "b"


def test_valid_dependency_cycle_is_retained_as_one_connected_group():
    incoming = {"a": asset(1, ["b"]), "b": asset(2, ["a"])}
    result = plan_exchange({}, {}, incoming)
    assert len(result["changes"]) == 2 and not result["errors"]


def test_deletion_of_a_referenced_asset_is_blocked():
    base = {"a": asset(1), "b": asset(2, ["a"])}
    result = plan_exchange(base, base, base | {"a": asset(None, deleted=True)})
    assert not result["changes"]
    assert result["errors"]


def test_json_boolean_is_distinct_from_integer_and_bad_envelopes_are_isolated():
    result = plan_exchange({}, {"a": asset(True)}, {"a": asset(1), "bad": {"content": 2}})
    assert result["conflicts"][0]["identity"] == "a"
    assert result["errors"][0]["identity"] == "bad"
