"""Receiving a course exchange package into a second installation."""

import base64
import json
import sqlite3

import pytest

from workbench.data.course_sync import (
    apply_exchange,
    export_course,
    inspect_exchange,
    read_exchange,
)
from workbench.data.pool import Pool

SCHEMA = """
    CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT, figure_paths TEXT);
    CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, kp_ids TEXT,
                           figure_paths TEXT, deleted_at TEXT);
    CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY, problem_id TEXT, answer_text TEXT);
    CREATE TABLE practice_execution_ids (id INTEGER PRIMARY KEY AUTOINCREMENT);
    CREATE TABLE active_practice (
        singleton INTEGER PRIMARY KEY, source_kind TEXT, source_ref TEXT, source_label TEXT,
        kp_ids_json TEXT DEFAULT '[]', practice_mode TEXT, rating_mode TEXT,
        cursor INTEGER DEFAULT 0, started_at TEXT, updated_at TEXT,
        execution_id INTEGER DEFAULT 0, paper_generation INTEGER DEFAULT 1,
        reveal_timing TEXT);
    CREATE TABLE active_practice_items (
        position INTEGER PRIMARY KEY, item_type TEXT, item_id TEXT, direction TEXT DEFAULT '',
        state TEXT DEFAULT 'pending', attempt_id INTEGER, content_revision INTEGER DEFAULT 1,
        draft_json TEXT, draft_sequence INTEGER DEFAULT 0);
"""


def make_course(root, course="math"):
    root.mkdir(parents=True, exist_ok=True)
    database = root / "course.db"
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()
    return Pool(root, database, course, "")


@pytest.fixture
def pair(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    left = make_course(tmp_path / "left")
    right = make_course(tmp_path / "right")
    connection = left.connect()
    connection.execute("INSERT INTO knowledge_points VALUES (?,?,?)",
                       ("math-kp-1", "公式 $x$", None))
    connection.execute("INSERT INTO problems VALUES (?,?,?,?,?)",
                       ("math-prob-1", "原题", '["math-kp-1"]', '["math/ch01/a.png"]', None))
    connection.execute("INSERT INTO problem_attempts VALUES (?,?,?)",
                       (1, "math-prob-1", "原始答案\n$x=1$"))
    left.commit()
    (left.root / ".lessonkit/figures/math/ch01").mkdir(parents=True)
    (left.root / ".lessonkit/figures/math/ch01/a.png").write_bytes(b"image\x00\xff")
    (left.root / ".lessonkit/practice-sets").mkdir()
    (left.root / ".lessonkit/practice-sets/ps-001.json").write_text(
        '{"title":"试卷"}\n', encoding="utf-8")
    yield left, right
    left.close()
    right.close()


def workspace(pool):
    return {"name": pool.course, "path": str(pool.root), "db": pool.db_path.name,
            "active_course": pool.course}


def rows(pool, table):
    return [dict(row) for row in pool.connect().execute(f'SELECT * FROM "{table}"')]


def receive(target, bundle, choices=None):
    inspected = inspect_exchange(target, workspace(target), bundle)
    return inspected, apply_exchange(target, workspace(target), inspected, choices)


def publish(pool, bundle):
    return export_course(pool, workspace(pool), bundle)


def test_receive_writes_rows_files_and_original_answers(pair, tmp_path):
    left, right = pair
    assert publish(left, tmp_path / "bundle")["status"] == "success"

    inspected, result = receive(right, tmp_path / "bundle")

    assert inspected["errors"] == []
    assert inspected["plan"]["outgoing"] == []
    assert result["status"] == "success", result["failed"]
    attempts = rows(right, "problem_attempts")
    assert [(row["problem_id"], row["answer_text"]) for row in attempts] == [
        ("math-prob-1", "原始答案\n$x=1$")]
    assert rows(right, "problems")[0]["problem_text"] == "原题"
    assert (right.root / ".lessonkit/figures/math/ch01/a.png").read_bytes() == b"image\x00\xff"
    assert (right.root / ".lessonkit/practice-sets/ps-001.json").is_file()
    assert result["base_size"] >= len(result["applied"])


def test_repeated_receive_creates_no_duplicate_facts(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    receive(right, tmp_path / "bundle")
    before = rows(right, "problem_attempts")

    inspected, result = receive(right, tmp_path / "bundle")

    assert inspected["plan"]["changes"] == []
    assert result["applied"] == []
    assert rows(right, "problem_attempts") == before


def test_one_sided_edits_travel_in_both_directions(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    receive(right, tmp_path / "bundle")

    right.connect().execute("UPDATE problems SET problem_text='右边改题'")
    right.commit()
    publish(right, tmp_path / "bundle")

    left.connect().execute("UPDATE knowledge_points SET body='左边改正文'")
    left.commit()
    _inspected, back = receive(left, tmp_path / "bundle")
    assert back["status"] == "success", back["failed"]
    assert rows(left, "problems")[0]["problem_text"] == "右边改题"
    assert rows(left, "knowledge_points")[0]["body"] == "左边改正文"

    publish(left, tmp_path / "reply")
    _inspected, forward = receive(right, tmp_path / "reply")
    assert forward["status"] == "success", forward["failed"]
    assert rows(right, "knowledge_points")[0]["body"] == "左边改正文"
    assert rows(right, "problems")[0]["problem_text"] == "右边改题"


def test_two_sided_change_needs_a_side_and_applies_a_batch_choice(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    receive(right, tmp_path / "bundle")
    right.connect().execute("UPDATE knowledge_points SET body='右边版本'")
    right.commit()
    left.connect().execute("UPDATE knowledge_points SET body='左边版本'")
    left.commit()
    publish(left, tmp_path / "bundle")

    inspected, blocked = receive(right, tmp_path / "bundle")

    assert [item["identity"] for item in inspected["conflicts"]]
    assert blocked["status"] == "conflict"
    assert blocked["applied"] == []
    assert rows(right, "knowledge_points")[0]["body"] == "右边版本"

    _inspected, resolved = receive(right, tmp_path / "bundle", {"side": "incoming"})
    assert resolved["status"] == "success"
    assert rows(right, "knowledge_points")[0]["body"] == "左边版本"


def test_a_failed_unit_keeps_independent_units_and_retries(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    right.connect().execute(
        "CREATE TRIGGER refuse_kp BEFORE INSERT ON knowledge_points "
        "BEGIN SELECT RAISE(ABORT, 'refused'); END;")
    right.commit()

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "partial"
    failed = {item["identity"] for item in result["failed"]}
    assert any("knowledge_points" in identity for identity in failed)
    assert rows(right, "knowledge_points") == []
    assert [row["problem_id"] for row in rows(right, "problems")] == ["math-prob-1"]

    right.connect().execute("DROP TRIGGER refuse_kp")
    right.commit()
    _inspected, retried = receive(right, tmp_path / "bundle")
    assert retried["status"] == "success", retried["failed"]
    assert rows(right, "knowledge_points")[0]["kp_id"] == "math-kp-1"
    assert [row["id"] for row in rows(right, "problem_attempts")] == [1]


def test_unfinished_executions_are_refused_without_dropping_saved_state(pair, tmp_path):
    left, right = pair
    connection = left.connect()
    connection.execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    connection.execute(
        "INSERT INTO active_practice (singleton, source_kind, source_ref, practice_mode,"
        " rating_mode, execution_id) VALUES (1,'paper','ps-001','exam','immediate',1)")
    connection.execute(
        "INSERT INTO active_practice_items (position, item_type, item_id, draft_json)"
        " VALUES (0,'problem','math-prob-1','{\"answer\":\"草稿\"}')")
    left.commit()
    publish(left, tmp_path / "bundle")

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "partial"
    refused = {item["identity"]: item["code"] for item in result["failed"]}
    executable = {identity for identity in refused if identity.startswith("execution/")}
    assert executable and all(refused[identity] == "unsupported_kind" for identity in executable)
    assert rows(right, "active_practice") == []
    assert rows(right, "active_practice_items") == []
    assert rows(right, "knowledge_points")[0]["kp_id"] == "math-kp-1"


def test_explicit_deletion_removes_the_row_and_a_missing_file_does_not(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    receive(right, tmp_path / "bundle")

    manifest_path = tmp_path / "bundle/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    descriptor = next(item for item in manifest["assets"]
                      if item["kind"] == "row" and "knowledge_points" in item["identity"])
    (tmp_path / "bundle" / descriptor["path"]).write_text(
        json.dumps({"kind": "row", "deleted": True}), encoding="utf-8")

    _inspected, result = receive(right, tmp_path / "bundle")
    assert result["status"] == "success", result["failed"]
    assert rows(right, "knowledge_points") == []

    descriptor = next(item for item in manifest["assets"]
                      if item["kind"] == "file" and item["identity"].endswith("ps-001.json"))
    (tmp_path / "bundle" / descriptor["path"]).unlink()
    inspected = inspect_exchange(right, workspace(right), tmp_path / "bundle")
    assert any(error["code"] == "missing_asset" for error in inspected["errors"])
    assert (right.root / ".lessonkit/practice-sets/ps-001.json").is_file()
