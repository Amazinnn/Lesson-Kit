"""LIFE-SYNC: the Paper item history travels with the course exchange.

A removed question is not just a local row: its retained history must survive a
full round trip, take a fresh local sequence on the other installation, and never
silently replace a different fact that happens to share a number.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from workbench.data import active_practice, course_sync, paper_progress, practice_sets
from workbench.data.pool import Pool, ensure_paper_lifecycle_schema

ROOT = Path(__file__).resolve().parents[2]


def build(name, root, *, seed=True):
    """A real pool from the repository's own schema script."""
    root.mkdir(parents=True, exist_ok=True)
    database = root / "course.db"
    built = subprocess.run(
        [sys.executable, str(ROOT / "pipeline/scripts/create-tables.py"), "--db", str(database)],
        cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(built.stderr)
    pool = Pool(root, database, "dmath", "ch06")
    if not seed:
        return pool
    connection = pool.connect()
    connection.execute(
        "INSERT INTO knowledge_points(kp_id,knowledge_item,knowledge_type,importance,body)"
        " VALUES ('dmath-ch06-kp-001','标题','concept-property','core','正文')")
    for number in range(1, 5):
        connection.execute(
            "INSERT INTO problems(problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
            " VALUES (?,?,?,?,?,?)",
            (f"dmath-ch06-prob-00{number}", '["dmath-ch06-kp-001"]', f"question {number}",
             "$x=1$", "calculation", "textbook"))
    pool.commit()
    return pool


class Device:
    def __init__(self, pool, home):
        self.pool, self.home = pool, home

    def __call__(self):
        os.environ["LESSONKIT_WB_HOME"] = str(self.home)
        return self.pool


@pytest.fixture
def devices(tmp_path):
    left = Device(build("a", tmp_path / "a"), tmp_path / "registry-a")
    right = Device(build("b", tmp_path / "b", seed=False), tmp_path / "registry-b")
    yield left, right
    left.pool.close()
    right.pool.close()


def workspace(pool):
    return {"name": pool.course, "path": str(pool.root), "db": pool.db_path.name,
            "active_course": pool.course}


def round_trip(source, target, bundle, choices=None):
    left = source()
    course_sync.export_course(left, workspace(left), bundle)
    right = target()
    inspection = course_sync.inspect_exchange(right, workspace(right), bundle)
    return inspection, course_sync.apply_exchange(right, workspace(right), inspection, choices)


def retired(pool, paper_id):
    rows = pool.connect().execute(
        'SELECT problem_id, sequence, state, draft_json FROM retired_paper_items'
        ' WHERE paper_id=? ORDER BY sequence', (paper_id,)).fetchall()
    return [tuple(row) for row in rows]


def prepared(pool):
    """One practised Paper plus one duplicate removed, leaving retained history."""
    paper_id = practice_sets.create_saved(pool, "卷", [
        "dmath-ch06-prob-001", "dmath-ch06-prob-002", "dmath-ch06-prob-003"])["practice_set_id"]
    run = active_practice.start_saved(pool, paper_id, rating_mode="off")
    active_practice.mark(pool, 0, "stuck")
    # The draft belongs to the question that is about to be removed.
    active_practice.save_draft(pool, run["execution_id"], 1, {"answer": "保留的草稿"})
    preview = practice_sets.preview_update(pool, paper_id, problem_ids=[
        "dmath-ch06-prob-001", "dmath-ch06-prob-003"])
    practice_sets.update_saved(pool, paper_id, problem_ids=[
        "dmath-ch06-prob-001", "dmath-ch06-prob-003"], confirmation=preview["confirmation"])
    return paper_id, run


def test_retained_history_survives_export_receive_and_the_next_hop(devices, tmp_path):
    left, right = devices
    paper_id, run = prepared(left())
    source_history = retired(left(), paper_id)
    assert [row[0] for row in source_history] == ["dmath-ch06-prob-002"]
    assert "保留的草稿" in source_history[0][3]

    _inspected, result = round_trip(left, right, tmp_path / "hop1")
    assert result["status"] == "success", result["failed"]
    received = retired(right(), paper_id)
    assert [(row[0], row[2]) for row in received] == [("dmath-ch06-prob-002", "pending")]
    assert "保留的草稿" in received[0][3]

    current = active_practice.current(right())
    assert [item["item_id"] for item in current["items"]] == [
        "dmath-ch06-prob-001", "dmath-ch06-prob-003"]
    assert current["items"][0]["state"] == "stuck"
    assert current["items"][1]["state"] == "pending"
    assert run["execution_id"] == current["execution_id"]

    # Third device: the history keeps travelling and stays a single row.
    third = Device(build("c", tmp_path / "c", seed=False), tmp_path / "registry-c")
    try:
        _inspected, forward = round_trip(right, third, tmp_path / "hop2")
        assert forward["status"] == "success", forward["failed"]
        assert [row[0] for row in retired(third(), paper_id)] == ["dmath-ch06-prob-002"]
    finally:
        third.pool.close()


def test_a_received_history_row_takes_a_local_sequence(devices, tmp_path):
    """Two machines numbering their own history must not overwrite each other."""
    left, right = devices
    paper_id, _run = prepared(left())
    connection = right().connect()
    connection.execute(
        "INSERT INTO knowledge_points(kp_id,knowledge_item,knowledge_type,importance,body)"
        " VALUES ('dmath-ch06-kp-001','标题','concept-property','core','正文')")
    for number in (1, 2, 4):
        connection.execute(
            "INSERT INTO problems(problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
            " VALUES (?,?,?,?,?,?)",
            (f"dmath-ch06-prob-00{number}", '["dmath-ch06-kp-001"]', f"local {number}",
             "$x=1$", "calculation", "textbook"))
    right().commit()
    keeper = practice_sets.create_saved(right(), "同号卷", [
        "dmath-ch06-prob-001", "dmath-ch06-prob-002"])["practice_set_id"]
    assert keeper == paper_id, "both installations name their first Paper ps-001"
    ensure_paper_lifecycle_schema(right().connect())
    right().connect().execute(
        "INSERT INTO retired_paper_items (paper_id, sequence, problem_id, position, state,"
        " draft_json) VALUES (?,?,?,?,?,?)",
        (paper_id, 1, "dmath-ch06-prob-004", 9, "pending", json.dumps({"answer": "本地事实"}, ensure_ascii=False)))
    right().commit()

    _inspected, result = round_trip(left, right, tmp_path / "hop1", {"associate": True})

    assert result["status"] == "success", result["failed"]
    rows = retired(right(), paper_id)
    assert [row[0] for row in rows] == ["dmath-ch06-prob-004", "dmath-ch06-prob-002"]
    assert [row[1] for row in rows] == [1, 2]
    assert "本地事实" in rows[0][3]
    assert "保留的草稿" in rows[1][3]


def test_receiving_the_same_history_twice_appends_nothing(devices, tmp_path):
    left, right = devices
    paper_id, _run = prepared(left())
    round_trip(left, right, tmp_path / "hop1")
    before = retired(right(), paper_id)

    _inspected, again = round_trip(left, right, tmp_path / "hop2")

    assert again["applied"] == []
    assert retired(right(), paper_id) == before


def test_a_history_reference_to_a_missing_fact_stays_exportable(devices, tmp_path):
    """A received course may hold an attempt id this machine never had."""
    left, right = devices
    paper_id, _run = prepared(left())
    ensure_paper_lifecycle_schema(right().connect())
    right().connect().execute(
        "INSERT INTO retired_paper_items (paper_id, sequence, problem_id, position, state,"
        " attempt_id, draft_json) VALUES (?,?,?,?,?,?,?)",
        (paper_id, 1, "dmath-ch06-prob-002", 0, "answered", 424242, "{}"))
    right().commit()

    result = course_sync.export_course(right(), workspace(right()), tmp_path / "hop1")

    assert result["status"] == "success"
    dangling = [entry for entry in result["tables"] if entry.get("dangling_history_references")]
    assert dangling and dangling[0]["dangling_history_references"][0]["value"] == 424242
    package = course_sync.read_exchange(tmp_path / "hop1")
    asset = next(asset for asset in package["assets"].values()
                 if asset["kind"] == "row"
                 and asset["content"]["table"] == "retired_paper_items")
    assert asset["content"]["row"]["attempt_id"] is None


def test_an_old_course_without_the_history_table_receives_and_repeats(devices, tmp_path):
    left, right = devices
    paper_id, _run = prepared(left())
    right().connect().execute("DROP TABLE IF EXISTS retired_paper_items")
    right().commit()

    _inspected, first = round_trip(left, right, tmp_path / "hop1")

    assert first["status"] == "success", first["failed"]
    assert [row[0] for row in retired(right(), paper_id)] == ["dmath-ch06-prob-002"]
    _inspected, second = round_trip(left, right, tmp_path / "hop2")
    assert second["applied"] == []
    assert [row[0] for row in retired(right(), paper_id)] == ["dmath-ch06-prob-002"]


def test_a_correction_recorded_elsewhere_replays_its_result(devices, tmp_path):
    """The same request executed on A repeats on B without a false conflict."""
    from workbench.data import attempts
    left, right = devices
    prepared(left())
    recorded = attempts.apply(left(), {
        "request_id": "conv-001-turn-001-record",
        "items": [{"problem_id": "dmath-ch06-prob-003", "answer_text": "第一次的原文",
                   "rating": 3}],
    })
    attempt_id = recorded["items"][0]["attempt_id"]
    correction = {"request_id": "conv-001-turn-002-correct",
                  "answer_text": "更正后的原文", "note": "备注", "rating": 4}
    first = attempts.correct(left(), attempt_id, correction)

    _inspected, result = round_trip(left, right, tmp_path / "hop1")
    assert result["status"] == "success", result["failed"]

    before = [tuple(row) for row in right().connect().execute(
        "SELECT id, problem_id, status, note, answer_text FROM problem_attempts ORDER BY id")]
    replayed = attempts.correct(right(), attempt_id, correction)

    assert replayed["request_id"] == first["request_id"]
    assert replayed["items"] == first["items"]
    assert [tuple(row) for row in right().connect().execute(
        "SELECT id, problem_id, status, note, answer_text FROM problem_attempts ORDER BY id")] == before

    different = dict(correction, answer_text="另一次更正")
    with pytest.raises(attempts.ManifestError, match="different content"):
        attempts.correct(right(), attempt_id, different)


def test_a_cached_display_id_never_blocks_export_or_gets_rebound(devices, tmp_path):
    """A parked snapshot may name a feedback row that no longer exists."""
    left, right = devices
    paper_id = practice_sets.create_saved(left(), "卷", [
        "dmath-ch06-prob-001", "dmath-ch06-prob-002"])["practice_set_id"]
    run = active_practice.start_saved(left(), paper_id, rating_mode="off")
    active_practice.mark(left(), 0, "stuck")
    other = practice_sets.create_saved(left(), "另一卷", ["dmath-ch06-prob-003"])["practice_set_id"]
    active_practice.start_saved(left(), other, rating_mode="off")   # parks the first run

    state = paper_progress.state(left().connect(), paper_id)
    record = json.loads(state["checkpoint_json"])
    record["items"][0]["feedback_event_id"] = 987654
    left().connect().execute(
        "UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?",
        (json.dumps(record, ensure_ascii=False), paper_id))
    left().commit()

    result = course_sync.export_course(left(), workspace(left()), tmp_path / "hop1")

    assert result["status"] == "success"
    package = course_sync.read_exchange(tmp_path / "hop1")
    execution = next(asset for asset in package["assets"].values()
                     if asset["kind"] == "execution" and
                     asset["content"].get("paper_id") == paper_id)
    cached = next(item for item in package["assets"].values()
                  if item["kind"] == "execution_item" and
                  item["content"].get("paper_id") == paper_id)
    assert "feedback_event_id" not in execution["content"]
    # The snapshot keeps the source number as an opaque display value: it is not
    # converted into a reference the target could mistake for a writable local row.
    assert cached["content"].get("feedback_event_id") == 987654

    _inspected, received = round_trip(left, right, tmp_path / "hop2")
    assert received["status"] == "success", received["failed"]


def test_deleting_a_shared_question_propagates_to_the_other_installation(devices, tmp_path):
    """FS-06: the question leaves both Papers and their executions stay writable."""
    from workbench.data import content
    left, right = devices
    paper_id, run = prepared(left())
    first = round_trip(left, right, tmp_path / "hop1")
    assert first[1]["status"] == "success", first[1]["failed"]

    content.delete(left(), "problem", "dmath-ch06-prob-002")
    left().commit()

    _inspected, result = round_trip(left, right, tmp_path / "hop2")

    assert result["status"] == "success", result["failed"]
    current = active_practice.current(right())
    assert "dmath-ch06-prob-002" not in [item["item_id"] for item in current["items"]]
    assert current["execution_id"] == run["execution_id"]


def test_a_deleted_knowledge_point_travels_as_an_explicit_tombstone(devices, tmp_path):
    """GAP-01: deleting a knowledge point must not break the next exchange."""
    from workbench.data import content
    left, right = devices
    first = round_trip(left, right, tmp_path / "hop1")
    assert first[1]["status"] == "success", first[1]["failed"]

    content.delete(left(), "kp", "dmath-ch06-kp-001")

    _inspected, result = round_trip(left, right, tmp_path / "hop2")

    assert result["status"] == "success", result["failed"]
    remaining = right().connect().execute(
        "SELECT COUNT(*) FROM knowledge_points WHERE kp_id=?",
        ("dmath-ch06-kp-001",)).fetchone()[0]
    assert remaining == 0
    assert right().connect().execute(
        "SELECT COUNT(*) FROM knowledge_relations").fetchone()[0] == 0


def test_receiving_a_knowledge_point_tombstone_twice_is_idle(devices, tmp_path):
    from workbench.data import content
    left, right = devices
    round_trip(left, right, tmp_path / "hop1")
    content.delete(left(), "kp", "dmath-ch06-kp-001")
    round_trip(left, right, tmp_path / "hop2")

    inspection = course_sync.inspect_exchange(
        right(), workspace(right()), tmp_path / "hop2")

    assert inspection["plan"]["changes"] == []
    assert inspection["plan"]["outgoing"] == []


def test_a_moved_chapter_survives_the_exchange(devices, tmp_path):
    """WP02 2.3: a move keeps the id and travels with the course."""
    from workbench.data import content
    left, right = devices
    round_trip(left, right, tmp_path / "hop1")

    content.move_kp(left(), "dmath-ch06-kp-001", "ch09")
    round_trip(left, right, tmp_path / "hop2")

    row = right().connect().execute(
        "SELECT chapter FROM knowledge_points WHERE kp_id=?",
        ("dmath-ch06-kp-001",)).fetchone()
    assert row[0] == "ch09"
    assert [item["kp_id"] for item in right().kps("dmath-ch09")] == ["dmath-ch06-kp-001"]
    assert right().kps("dmath-ch06") == []
