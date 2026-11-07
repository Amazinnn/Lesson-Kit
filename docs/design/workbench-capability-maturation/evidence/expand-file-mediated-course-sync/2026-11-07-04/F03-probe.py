"""F03 bounded probe: file lifecycle across an export -> receive -> re-export chain.

Temporary courses only; LESSONKIT_WB_HOME points at a throwaway directory.
Run from the repo root: python tmp/agent-runs/F03-probe.py
"""

import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / 'pyproject.toml').is_file())
os.environ["LESSONKIT_WB_HOME"] = tempfile.mkdtemp(prefix="f03-registry-")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "workbench"))

from test_course_sync_receive import make_course  # noqa: E402
from workbench.data.course_sync import (  # noqa: E402
    apply_exchange,
    export_course,
    inspect_exchange,
)

TEMP = Path(tempfile.mkdtemp(prefix="f03-courses-"))
RAW_REL = "attachments/raw.bin"


def ws(pool):
    return {"name": pool.course, "path": str(pool.root),
            "db": pool.db_path.name, "active_course": pool.course}


def publish(pool, bundle):
    return export_course(pool, ws(pool), Path(bundle))


def receive(target, bundle, choices=None):
    inspected = inspect_exchange(target, ws(target), Path(bundle))
    return inspected, apply_exchange(target, ws(target), inspected, choices)


def manifest(bundle):
    return json.loads((Path(bundle) / "manifest.json").read_text(encoding="utf-8"))


def asset_ids(bundle):
    return [item["identity"] for item in manifest(bundle)["assets"]]


def deleted_assets(bundle):
    out = []
    for item in manifest(bundle)["assets"]:
        try:
            envelope = json.loads((Path(bundle) / item["path"]).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if envelope.get("deleted"):
            out.append(item["identity"])
    return out


def forge_tombstone(bundle, match, kind):
    descriptor = next(item for item in manifest(bundle)["assets"] if match(item["identity"]))
    path = Path(bundle) / descriptor["path"]
    if kind == "file":
        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["deleted"] = True
    else:
        envelope = {"kind": "row", "deleted": True}
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return descriptor["identity"]


def counts(pool):
    connection = pool.connect()
    tables = ("knowledge_points", "problems", "problem_attempts", "practice_runs")
    return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in tables}


def seed(pool, practice=False):
    connection = pool.connect()
    connection.execute("INSERT INTO knowledge_points (kp_id, body, figure_paths)"
                       " VALUES (?,?,?)", ("kp-1", "公式 $x$", None))
    connection.execute("INSERT INTO problems (problem_id, problem_text, kp_ids, figure_paths)"
                       " VALUES (?,?,?,?)", ("prob-1", "原题", '["kp-1"]', None))
    connection.execute("INSERT INTO problem_attempts VALUES (1,'prob-1','answer-1')")
    if practice:
        connection.execute(
            "INSERT INTO practice_runs (source_kind, source_ref, source_label, kp_ids_json,"
            " practice_mode, rating_mode, items_json, status)"
            " VALUES ('kp','kp-1','KP 练习','[\"kp-1\"]','review','auto','[]','finished')")
    connection.commit()


def declare_attachment(pool):
    target = pool.root / RAW_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"RAW\x00ATTACH")
    config = pool.root / ".lessonkit/course-sync/config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"managed_paths": [RAW_REL]}), encoding="utf-8")


def error_text(exc):
    return f"{type(exc).__name__}: {exc}"


results = {"probe": "F03", "workspace": str(ROOT), "temp_courses": str(TEMP),
           "raw_relative_path": RAW_REL, "probes": {}}


def probe_1():
    a, b, c = (make_course(TEMP / name) for name in ("p1a", "p1b", "p1c"))
    seed(a)
    declare_attachment(a)
    exported = publish(a, TEMP / "p1-b1")
    b_received = receive(b, TEMP / "p1-b1")[1]
    b_exported = publish(b, TEMP / "p1-b2")
    c_received = receive(c, TEMP / "p1-b2")[1]
    return {
        "a_export_status": exported.get("status"),
        "a_package_has_attachment": "file/" + RAW_REL in asset_ids(TEMP / "p1-b1"),
        "b_receive_status": b_received.get("status"),
        "b_file_landed": (b.root / RAW_REL).is_file(),
        "b_file_bytes": (b.root / RAW_REL).read_bytes().hex()
        if (b.root / RAW_REL).is_file() else None,
        "b_has_device_config": (b.root / ".lessonkit/course-sync/config.json").is_file(),
        "b_export_status": b_exported.get("status"),
        "b_package_has_attachment": "file/" + RAW_REL in asset_ids(TEMP / "p1-b2"),
        "c_receive_status": c_received.get("status"),
        "c_file_landed": (c.root / RAW_REL).is_file(),
    }


def tombstone_case(tag, rel, retain_content, holder=False):
    a, b = (make_course(TEMP / f"p2{tag}a"), make_course(TEMP / f"p2{tag}b"))
    bundle = TEMP / f"p2{tag}-b1"
    if rel.startswith("attachments"):
        declare_attachment(a)
    else:
        target = a.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"title":"试卷"}', encoding="utf-8")
    seed(a)
    publish(a, bundle)
    first = receive(b, bundle)[1]
    descriptor = next(item for item in manifest(bundle)["assets"]
                      if item["identity"] == "file/" + rel)
    envelope_path = bundle / descriptor["path"]
    if retain_content:
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        envelope["deleted"] = True
        envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    else:
        envelope_path.write_text(json.dumps({"kind": "file", "deleted": True}),
                                 encoding="utf-8")
    inspected = inspect_exchange(b, ws(b), bundle)
    applied = apply_exchange(b, ws(b), inspected)
    exported = publish(b, TEMP / f"p2{tag}-b2")
    record = {
        "path": rel,
        "tombstone_form": "deleted+content" if retain_content else "deleted-only",
        "first_receive": first.get("status"),
        "plan_changes": [item["identity"] for item in inspected["plan"]["changes"]],
        "receive_status": applied.get("status"),
        "receive_failed": [item.get("message") for item in applied.get("failed", [])],
        "file_after_tombstone": (b.root / rel).is_file(),
        "export_status": exported.get("status"),
        "export_mentions_file": "file/" + rel in asset_ids(TEMP / f"p2{tag}-b2"),
        "export_deleted_assets": deleted_assets(TEMP / f"p2{tag}-b2"),
    }
    if holder:
        c = make_course(TEMP / f"p2{tag}c")
        receive(c, bundle)  # C already holds the file before B re-exports
        c_receive = receive(c, TEMP / f"p2{tag}-b2")[1]
        record["holder_file_before"] = (c.root / rel).is_file()
        record["holder_receive_after_b_export"] = c_receive.get("status")
        record["holder_file_after"] = (c.root / rel).is_file()
    return record


def probe_2():
    return {
        "raw_attachment": tombstone_case("raw", RAW_REL, True, holder=True),
        "managed_folder_file": tombstone_case(
            "ps", ".lessonkit/practice-sets/ps-002.json", True),
        "minimal_tombstone": tombstone_case("minimal", RAW_REL, False),
    }


def probe_3():
    a, b = (make_course(TEMP / name) for name in ("p3a", "p3b"))
    seed(a, practice=True)
    publish(a, TEMP / "p3-b0")
    receive(b, TEMP / "p3-b0")
    before = {"a": counts(a), "b": counts(b)}
    identity = forge_tombstone(TEMP / "p3-b0",
                               lambda item: "knowledge_points" in item, "row")
    b_deleted = receive(b, TEMP / "p3-b0")[1]
    after_b = counts(b)
    b_export = publish(b, TEMP / "p3-b1")
    ids = asset_ids(TEMP / "p3-b1")
    round_trip = receive(a, TEMP / "p3-b1")[1]
    return {
        "tombstone_identity": identity,
        "counts_before": before,
        "b_receive_status": b_deleted.get("status"),
        "counts_b_after_delete": after_b,
        "b_export_status": b_export.get("status"),
        "b_export_has_kp_tombstone": any("knowledge_points" in item for item in ids),
        "b_export_deleted_assets": deleted_assets(TEMP / "p3-b1"),
        "b_export_has_attempts": any("problem_attempts" in item for item in ids),
        "b_export_has_practice_runs": any("practice_runs" in item for item in ids),
        "a_round_trip_status": round_trip.get("status"),
        "a_round_trip_failed": [item.get("message") for item in round_trip.get("failed", [])],
        "counts_a_after_round_trip": counts(a),
    }


def probe_3b():
    d = make_course(TEMP / "p3d")
    seed(d)
    first = publish(d, TEMP / "p3d-b0")
    connection = d.connect()
    connection.execute("DELETE FROM knowledge_points")
    connection.commit()
    second = publish(d, TEMP / "p3d-b1")
    ids = asset_ids(TEMP / "p3d-b1")
    return {
        "initial_export": first.get("status"),
        "post_delete_export": second.get("status"),
        "post_delete_has_kp_row": any("knowledge_points" in item for item in ids),
        "post_delete_deleted_assets": deleted_assets(TEMP / "p3d-b1"),
        "post_delete_has_problem": any("problems" in item for item in ids),
    }


for name, function in (("1_attachment_chain", probe_1), ("2_file_tombstone", probe_2),
                       ("3_kp_delete_round_trip", probe_3),
                       ("3b_local_delete_export", probe_3b)):
    try:
        results["probes"][name] = function()
    except Exception as exc:  # fixture failure is itself a finding
        results["probes"][name] = {"probe_error": error_text(exc),
                                   "traceback": traceback.format_exc(limit=3)}

target = ROOT / "tmp/agent-runs/F03-results.json"
target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
