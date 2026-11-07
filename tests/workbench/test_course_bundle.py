"""Grouped JSON transport keeps physical file counts bounded and isolates groups."""

import copy
import json
from pathlib import Path

import pytest

from workbench.data.course_bundle import _size, load, pack
from workbench.data.course_sync import _read_json, _relative

SMALL_LIMIT = 512
GROUP_MEMBERS = 256
GROUP_BYTES = 8 * 1024 * 1024


def envelope(number, text=""):
    return {"kind": "row", "content": {"number": number, "text": text}, "depends_on": []}


def large_assets():
    return {f"row/{number:04d}": envelope(number) for number in range(SMALL_LIMIT + 1)}


def publish(root, result):
    for relative, value in result["files"].items():
        path = _relative(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def read(root, result, read_json=_read_json):
    return load(root, result["descriptors"], result["format_version"], _relative, read_json)


def counting(read_json=_read_json):
    """Count physical reads so tests can assert one read per file."""
    calls = []

    def track(path):
        calls.append(Path(path))
        return read_json(path)

    return calls, track


def test_small_package_keeps_one_envelope_per_physical_file(tmp_path):
    assets = {"row/a": envelope(1), "row/b": envelope(2), "note/存在": envelope(3, "汉字")}
    snapshot = copy.deepcopy(assets)
    result = pack(assets, "export-small")
    assert assets == snapshot
    assert result["format_version"] == 1
    assert result["written"] == 3 and result["reused"] == 0
    assert [item["identity"] for item in result["descriptors"]] == sorted(assets)
    assert all("member" not in item for item in result["descriptors"])
    assert {item["path"] for item in result["descriptors"]} == set(result["files"])
    assert set(result["files"]) == {f"export-small/assets/{number:06d}.json"
                                    for number in (1, 2, 3)}
    publish(tmp_path, result)
    calls, track = counting()
    loaded, errors = read(tmp_path, result, track)
    assert loaded == assets and errors == []
    assert len(calls) == 3
    assert {path.relative_to(tmp_path).as_posix()
            for path in tmp_path.rglob("*") if path.is_file()} == set(result["files"])


def test_unchanged_small_package_reuses_its_descriptors(tmp_path):
    assets = {"row/a": envelope(1), "row/b": envelope(2)}
    first = pack(assets, "export-one")
    again = pack(assets, "export-two",
                 previous_manifest={"format_version": 1, "assets": first["descriptors"]},
                 previous_assets=assets)
    assert again["format_version"] == 1
    assert again["files"] == {} and again["written"] == 0 and again["reused"] == 2
    assert again["descriptors"] == first["descriptors"]


def test_large_package_groups_assets_into_bounded_files(tmp_path):
    assets = large_assets()
    result = pack(assets, "export-large")
    assert len(assets) > SMALL_LIMIT
    assert result["format_version"] == 2
    assert len(result["files"]) == 3
    assert all(set(group) == {"assets"} for group in result["files"].values())
    assert all(len(group["assets"]) <= GROUP_MEMBERS for group in result["files"].values())
    assert sorted(identity for group in result["files"].values()
                  for identity in group["assets"]) == sorted(assets)
    homes = {item["identity"]: item["path"] for item in result["descriptors"]}
    assert all(item["member"] == item["identity"] for item in result["descriptors"])
    assert all(homes[identity] in result["files"] for identity in assets)
    assert all(result["files"][homes[identity]]["assets"][identity] == assets[identity]
               for identity in assets)
    assert len(set(homes.values())) == len(result["files"]) == 3
    publish(tmp_path, result)
    calls, track = counting()
    loaded, errors = read(tmp_path, result, track)
    assert errors == [] and loaded == assets and len(calls) == len(result["files"])


def test_group_payload_stays_within_the_byte_target():
    assets = large_assets()
    assets["row/0000"]["content"]["text"] = "x" * (5 * 1024 * 1024)
    assets["row/0001"]["content"]["text"] = "x" * (5 * 1024 * 1024)
    result = pack(assets, "export-target")
    sizes = {path: len(json.dumps(group, ensure_ascii=False).encode("utf-8"))
             for path, group in result["files"].items()}
    assert max(sizes.values()) <= GROUP_BYTES
    homes = {identity: path for path, group in result["files"].items()
             for identity in group["assets"] if identity in {"row/0000", "row/0001"}}
    assert homes["row/0000"] != homes["row/0001"]
    assert len(result["files"]) == 3


def test_group_size_is_measured_in_utf8_bytes_and_keeps_a_huge_envelope_whole():
    assets = large_assets()
    assets["row/0000"]["content"]["text"] = "汉" * (3 * 1024 * 1024)
    result = pack(assets, "export-utf8")
    sizes = [len(json.dumps(group, ensure_ascii=False).encode("utf-8"))
             for group in result["files"].values()]
    assert sorted(len(group["assets"]) for group in result["files"].values()) == [1, 256, 256]
    assert sum(size > GROUP_BYTES for size in sizes) == 1
    assert result["files"][min(result["files"])]["assets"].keys() == {"row/0000"}


def test_unchanged_large_package_reuses_every_descriptor():
    assets = large_assets()
    first = pack(assets, "export-one")
    again = pack(assets, "export-two",
                 previous_manifest={"format_version": 2, "assets": first["descriptors"]},
                 previous_assets=assets)
    assert again["format_version"] == 2
    assert again["files"] == {}
    assert again["written"] == 0 and again["reused"] == len(assets)
    assert again["descriptors"] == first["descriptors"]
    assert {item["path"] for item in again["descriptors"]} == set(first["files"])


def test_changed_large_package_writes_a_fresh_generation():
    assets = large_assets()
    first = pack(assets, "export-one")
    changed = dict(assets)
    changed["row/0007"] = envelope(7, "changed")
    again = pack(changed, "export-two",
                 previous_manifest={"format_version": 2, "assets": first["descriptors"]},
                 previous_assets=assets)
    assert again["format_version"] == 2
    assert again["written"] == len(assets) and again["reused"] == 0
    assert all(path.startswith("export-two/") for path in again["files"])
    assert set(again["files"]) == {item["path"] for item in again["descriptors"]}


def test_missing_and_corrupt_groups_isolate_only_their_assets(tmp_path):
    assets = large_assets()
    result = pack(assets, "export-groups")
    publish(tmp_path, result)
    missing, corrupt, healthy = sorted(result["files"])
    _relative(tmp_path, missing).unlink()
    _relative(tmp_path, corrupt).write_text("{not json", encoding="utf-8")
    loaded, errors = read(tmp_path, result)
    assert set(loaded) == set(result["files"][healthy]["assets"])
    assert {error["identity"] for error in errors} == (
        set(result["files"][missing]["assets"]) | set(result["files"][corrupt]["assets"]))
    codes = {error["identity"]: error["code"] for error in errors}
    assert {codes[identity] for identity in result["files"][missing]["assets"]} == {"missing_asset"}
    assert {codes[identity] for identity in result["files"][corrupt]["assets"]} == {"invalid_asset"}


def test_load_reads_each_physical_file_once(tmp_path):
    assets = {"row/a": envelope(1), "row/b": envelope(2)}
    small = pack(assets, "export-small")
    publish(tmp_path, small)
    calls, track = counting()
    loaded, errors = read(tmp_path, small, track)
    assert not errors and loaded == assets and len(calls) == 2
    grouped = pack(large_assets(), "export-groups")
    publish(tmp_path, grouped)
    calls, track = counting()
    loaded, errors = read(tmp_path, grouped, track)
    assert not errors and len(calls) == len(grouped["files"]) == 3


def test_duplicate_and_aliased_descriptors_are_rejected(tmp_path):
    def reject(descriptors, version):
        with pytest.raises(ValueError):
            load(tmp_path, descriptors, version, _relative, _read_json)

    reject([{"identity": "a", "kind": "row", "path": "gen/1.json"},
            {"identity": "a", "kind": "row", "path": "gen/2.json"}], 1)
    reject([{"identity": "a", "kind": "row", "path": "gen/1.json"},
            {"identity": "b", "kind": "row", "path": "gen/1.json"}], 1)
    reject([{"identity": "a", "kind": "row", "path": "gen/Shared.json"},
            {"identity": "b", "kind": "row", "path": "gen/shared.json"}], 1)
    reject([{"identity": "a", "kind": "row", "path": "gen/g.json", "member": "b"}], 2)
    reject([{"identity": "a", "kind": "row", "path": "gen/g.json", "member": "a"},
            {"identity": "b", "kind": "row", "path": "gen/G.json", "member": "b"}], 2)
    reject([{"identity": "", "kind": "row", "path": "gen/1.json"}], 1)
    reject(["not a descriptor"], 1)


def test_unsafe_paths_are_rejected_as_a_malformed_manifest(tmp_path):
    for path in ("../outside.json", "gen\\outside.json", "/absolute.json", "C:/absolute.json"):
        with pytest.raises(ValueError):
            load(tmp_path, [{"identity": "a", "kind": "row", "path": path}], 1,
                 _relative, _read_json)


def test_unexpected_group_members_are_rejected_instead_of_dropped(tmp_path):
    assets = large_assets()
    result = pack(assets, "export-groups")
    publish(tmp_path, result)
    target = min(result["files"])
    path = _relative(tmp_path, target)
    group = json.loads(path.read_text(encoding="utf-8"))
    group["assets"]["row/9999"] = envelope(9999)
    path.write_text(json.dumps(group, ensure_ascii=False), encoding="utf-8")
    loaded, errors = read(tmp_path, result)
    declared = set(result["files"][target]["assets"])
    assert set(loaded) == set(assets) - declared
    assert {error["identity"] for error in errors} == declared
    assert {error["code"] for error in errors} == {"invalid_asset"}
    assert "row/9999" not in loaded


def test_group_schema_and_declared_membership_are_enforced(tmp_path):
    assets = {"row/a": envelope(1), "row/b": envelope(2), "row/c": envelope(3)}
    descriptors = [{"identity": identity, "kind": "row", "path": "gen/g.json", "member": identity}
                   for identity in sorted(assets)]
    target = _relative(tmp_path, "gen/g.json")
    target.parent.mkdir()
    for content in ({"assets": assets, "extra": 1}, {"members": assets}, ["assets"]):
        target.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        loaded, errors = load(tmp_path, descriptors, 2, _relative, _read_json)
        assert not loaded
        assert [error["code"] for error in errors] == ["invalid_asset"] * 3
    target.write_text(json.dumps({"assets": {key: value for key, value in assets.items()
                                             if key != "row/b"}}, ensure_ascii=False),
                      encoding="utf-8")
    loaded, errors = load(tmp_path, descriptors, 2, _relative, _read_json)
    assert not loaded and {error["identity"] for error in errors} == set(assets)


def test_version1_remains_readable_at_any_size(tmp_path):
    assets = large_assets()
    descriptors = []
    for number, identity in enumerate(sorted(assets), 1):
        relative = f"gen/assets/{number:06d}.json"
        target = _relative(tmp_path, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(assets[identity], ensure_ascii=False), encoding="utf-8")
        descriptors.append({"identity": identity, "kind": "row", "path": relative,
                            "depends_on": []})
    calls, track = counting()
    loaded, errors = load(tmp_path, descriptors, 1, _relative, track)
    assert not errors and loaded == assets and len(calls) == len(assets)


def test_unknown_format_versions_and_descriptor_shapes_are_rejected(tmp_path):
    for version in (0, 3, "2", None, True):
        with pytest.raises(ValueError):
            load(tmp_path, [], version, _relative, _read_json)
    with pytest.raises(ValueError):
        load(tmp_path, {"a": 1}, 1, _relative, _read_json)


def test_a_changed_small_envelope_gets_a_new_path_and_loads_the_new_projection(tmp_path):
    """A regression that reused a v1 path for a changed envelope would ship stale bytes."""
    assets = {"row/a": envelope(1), "row/b": envelope(2), "row/c": envelope(3)}
    first = pack(assets, "export-one")
    publish(tmp_path, first)
    changed = dict(assets)
    changed["row/b"] = envelope(2, "changed")
    again = pack(changed, "export-two",
                 previous_manifest={"format_version": 1, "assets": first["descriptors"]},
                 previous_assets=assets)
    assert again["written"] == 1 and again["reused"] == 2
    new_paths = {item["identity"]: item["path"] for item in again["descriptors"]}
    stale = {item["identity"]: item["path"] for item in first["descriptors"]}
    assert new_paths["row/b"] != stale["row/b"]
    assert new_paths["row/a"] == stale["row/a"] and new_paths["row/c"] == stale["row/c"]
    publish(tmp_path, again)
    loaded, errors = read(tmp_path, again)
    assert errors == []
    assert loaded == changed


def test_a_mixed_generation_reads_the_new_projection(tmp_path):
    """Reused old paths and fresh paths must load together as the committed image."""
    assets = {f"row/{number}": envelope(number) for number in range(4)}
    first = pack(assets, "export-one")
    publish(tmp_path, first)
    changed = dict(assets)
    changed["row/1"] = envelope(1, "第二版")
    again = pack(changed, "export-two",
                 previous_manifest={"format_version": 1, "assets": first["descriptors"]},
                 previous_assets=assets)
    publish(tmp_path, again)
    loaded, errors = read(tmp_path, again)
    assert errors == []
    assert loaded == changed
    assert loaded["row/1"]["content"]["text"] == "第二版"


def test_the_byte_target_boundary_is_inclusive_and_exact():
    """Exactly GROUP_BYTES keeps two members; one more byte splits them."""
    assets = large_assets()
    base = _size({"assets": {}})
    first, second = "row/0000", "row/0001"
    natural = _size(first) + 2 + _size(envelope(0)) + 2 + _size(second) + 2 + _size(envelope(1))
    slack = GROUP_BYTES - base - natural
    assert slack >= 0
    padded = dict(assets)
    padded[first] = envelope(0, "x" * slack)
    result = pack(padded, "export-exact")
    (path, payload), = [(name, value) for name, value in result["files"].items()
                        if first in value["assets"]]
    assert len(payload["assets"]) == 2
    assert _size(payload) == GROUP_BYTES

    bigger = dict(padded)
    bigger[first] = envelope(0, "x" * (slack + 1))
    split = pack(bigger, "export-split")
    (path, payload), = [(name, value) for name, value in split["files"].items()
                        if first in value["assets"]]
    assert len(payload["assets"]) == 1
