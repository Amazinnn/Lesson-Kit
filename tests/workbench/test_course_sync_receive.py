"""Receiving a course exchange package into a second installation."""

import base64
from contextlib import contextmanager
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
    CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT, figure_paths TEXT,
                                   related_kp_ids TEXT);
    CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, kp_ids TEXT,
                           figure_paths TEXT, deleted_at TEXT, difficulty TEXT,
                           difficulty_knowledge_breadth TEXT, difficulty_reasoning_depth TEXT,
                           difficulty_transfer_distance TEXT,
                           difficulty_construction_openness TEXT, difficulty_model TEXT);
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
    CREATE TABLE paper_state (
        paper_id TEXT PRIMARY KEY, generation INTEGER NOT NULL DEFAULT 1,
        checkpoint_json TEXT, pending_json TEXT, pending_delete INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE problem_revisions (
        problem_id TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE flash_cards (card_id TEXT PRIMARY KEY, kp_id TEXT);
    CREATE TABLE questions (q_id TEXT PRIMARY KEY, kp_id TEXT);
    CREATE TABLE question_progress (id INTEGER PRIMARY KEY AUTOINCREMENT, q_id TEXT, note TEXT);
    CREATE TABLE kp_progress (kp_id TEXT PRIMARY KEY, state TEXT);
    CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY,
                                      source_kp_id TEXT, target_kp_id TEXT);
    CREATE TABLE learner_signals (id INTEGER PRIMARY KEY, target_id TEXT);
    CREATE TABLE feedback_events (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT,
                                  item_id TEXT, note TEXT);
    CREATE TABLE review_schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT,
                                  item_id TEXT);
    CREATE TABLE learning_current_state (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT,
                                         item_id TEXT);
    CREATE TABLE practice_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, source_kind TEXT,
                                source_ref TEXT, source_label TEXT, kp_ids_json TEXT DEFAULT '[]',
                                practice_mode TEXT, rating_mode TEXT, items_json TEXT DEFAULT '[]',
                                status TEXT, started_at TEXT, finished_at TEXT,
                                reveal_timing TEXT);
    CREATE TABLE part_grading_jobs (attempt_id INTEGER PRIMARY KEY, execution_id INTEGER NOT NULL,
                                    status TEXT NOT NULL DEFAULT 'pending', error TEXT,
                                    conversation_id TEXT, turn_id TEXT, updated_at TEXT);
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
    connection.execute("INSERT INTO knowledge_points (kp_id, body, figure_paths)"
                       " VALUES (?,?,?)", ("math-kp-1", "公式 $x$", None))
    connection.execute("INSERT INTO problems (problem_id, problem_text, kp_ids, figure_paths)"
                       " VALUES (?,?,?,?)",
                       ("math-prob-1", "原题", '["math-kp-1"]', '["math/ch01/a.png"]'))
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


def running_paper(left, draft="草稿", generation=1):
    connection = left.connect()
    connection.execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    connection.execute(
        "INSERT INTO active_practice (singleton, source_kind, source_ref, source_label,"
        " kp_ids_json, practice_mode, rating_mode, cursor, started_at, updated_at,"
        " execution_id, paper_generation, reveal_timing)"
        " VALUES (1,'paper','ps-001','期中练习卷','[\"math-kp-1\"]','exam','immediate',0,"
        "'2026-11-07 10:00:00','2026-11-07 10:00:00',1,?,'per_item')", (generation,))
    connection.execute(
        "INSERT INTO active_practice_items (position, item_type, item_id, state, attempt_id,"
        " content_revision, draft_json, draft_sequence) VALUES (0,'problem','math-prob-1',"
        "'pending',1,3,?,2)", (json.dumps({"answer": draft}, ensure_ascii=False),))
    left.commit()


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

    # The paper file the execution belongs to is part of the same package.
    (left.root / ".lessonkit/practice-sets/ps-001.json").write_text(
        '{"title":"期中练习卷"}\n', encoding="utf-8")
    assert export_course(left, workspace(left), tmp_path / "bundle")["status"] == "success"

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "success", result["failed"]
    assert rows(right, "knowledge_points")[0]["kp_id"] == "math-kp-1"


def test_an_active_execution_is_rebuilt_with_its_drafts(pair, tmp_path):
    left, right = pair
    running_paper(left)
    assert export_course(left, workspace(left), tmp_path / "bundle")["status"] == "success"

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "success", result["failed"]
    active = rows(right, "active_practice")
    assert len(active) == 1
    assert active[0]["source_ref"] == "ps-001"
    assert json.loads(active[0]["kp_ids_json"]) == ["math-kp-1"]
    assert active[0]["reveal_timing"] == "per_item"
    items = rows(right, "active_practice_items")
    assert [(row["position"], row["item_id"], row["state"]) for row in items] == [
        (0, "math-prob-1", "pending")]
    assert json.loads(items[0]["draft_json"]) == {"answer": "草稿"}
    assert items[0]["draft_sequence"] == 2
    assert items[0]["content_revision"] == 3
    assert items[0]["attempt_id"] == 1


def test_a_draft_changed_on_one_side_travels_without_a_conflict(pair, tmp_path):
    left, right = pair
    running_paper(left)
    export_course(left, workspace(left), tmp_path / "bundle")
    receive(right, tmp_path / "bundle")

    right.connect().execute(
        "UPDATE active_practice_items SET draft_json=?, draft_sequence=3 WHERE position=0",
        (json.dumps({"answer": "右边的草稿"}, ensure_ascii=False),))
    right.commit()
    export_course(right, workspace(right), tmp_path / "bundle")

    inspected, result = receive(left, tmp_path / "bundle")
    assert inspected["conflicts"] == []
    assert result["status"] == "success", result["failed"]
    assert json.loads(rows(left, "active_practice_items")[0]["draft_json"]) == {
        "answer": "右边的草稿"}


def test_a_parked_checkpoint_is_rebuilt_for_its_paper(pair, tmp_path):
    left, right = pair
    record = {
        "source_kind": "paper", "source_ref": "ps-001", "source_label": "期中练习卷",
        "kp_ids": ["math-kp-1"], "practice_mode": "exam", "rating_mode": "immediate",
        "cursor": 0, "started_at": "2026-11-07 10:00:00", "updated_at": "2026-11-07 10:05:00",
        "execution_id": 1, "paper_generation": 2, "reveal_timing": "on_submit",
        "items": [{"position": 0, "item_type": "problem", "item_id": "math-prob-1",
                   "direction": "", "state": "answered", "attempt_id": 1,
                   "content_revision": 3, "draft": {"answer": "暂停的草稿"},
                   "draft_sequence": 4}],
        "progress": {"completed": 1, "remaining": 0, "total": 1},
    }
    connection = left.connect()
    connection.execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    connection.execute("INSERT INTO paper_state VALUES ('ps-001', 2, ?, NULL, 0)",
                       (json.dumps(record, ensure_ascii=False),))
    left.commit()
    (left.root / ".lessonkit/practice-sets/ps-001.json").write_text(
        '{"title":"期中练习卷"}\n', encoding="utf-8")
    export_course(left, workspace(left), tmp_path / "bundle")

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "success", result["failed"]
    state = rows(right, "paper_state")[0]
    assert state["paper_id"] == "ps-001"
    assert state["generation"] == 2
    parked = json.loads(state["checkpoint_json"])
    assert parked["execution_id"] == 1
    assert parked["items"][0]["draft"] == {"answer": "暂停的草稿"}
    assert parked["items"][0]["draft_sequence"] == 4
    assert parked["cursor"] == 0
    assert rows(right, "active_practice") == []


def test_an_imported_question_edit_clears_difficulty_and_local_drafts(pair, tmp_path):
    left, right = pair
    publish(left, tmp_path / "bundle")
    receive(right, tmp_path / "bundle")
    connection = right.connect()
    connection.execute("UPDATE problems SET difficulty='hard', difficulty_model='m1'")
    connection.execute("INSERT OR REPLACE INTO problem_revisions VALUES ('math-prob-1', 4)")
    connection.execute(
        "INSERT INTO active_practice_items (position, item_type, item_id, state, draft_json)"
        " VALUES (0,'problem','math-prob-1','pending','{\"answer\":\"本机草稿\"}')")
    connection.execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    connection.execute("INSERT INTO active_practice (singleton, source_kind, source_ref,"
                       " practice_mode, rating_mode, execution_id)"
                       " VALUES (1,'paper','ps-001','exam','immediate',1)")
    right.commit()

    left.connect().execute("UPDATE problems SET problem_text='改了题面'")
    left.commit()
    publish(left, tmp_path / "bundle")

    # A local difficulty rating and a remote question edit are two changes to
    # one row, so the row needs a side before the writer clears that rating.
    inspected, blocked = receive(right, tmp_path / "bundle")
    assert blocked["status"] == "conflict", blocked
    assert [item["identity"] for item in inspected["conflicts"]] == ['row/problems/["math-prob-1"]']
    _inspected, result = receive(right, tmp_path / "bundle", {"side": "incoming"})

    assert result["status"] == "success", result["failed"]
    problem = rows(right, "problems")[0]
    assert problem["problem_text"] == "改了题面"
    assert problem["difficulty"] is None and problem["difficulty_model"] is None
    item = rows(right, "active_practice_items")[0]
    assert item["state"] == "pending"
    assert item["attempt_id"] is None
    assert item["draft_json"] is None
    assert item["content_revision"] == 5


def test_an_imported_deletion_keeps_the_writer_side_effects(pair, tmp_path):
    left, right = pair
    connection = right.connect()
    connection.execute("INSERT INTO flash_cards VALUES ('card-1','math-kp-1')")
    connection.execute("INSERT INTO questions VALUES ('q-1','math-kp-1')")
    connection.execute("INSERT INTO question_progress (q_id, note) VALUES ('q-1','')")
    connection.execute("INSERT INTO kp_progress VALUES ('math-kp-1','learned')")
    connection.execute("INSERT INTO knowledge_relations VALUES ('r-1','math-kp-1','math-kp-2')")
    connection.execute("INSERT INTO learner_signals VALUES (1,'card-1')")
    right.commit()
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
    for table in ("flash_cards", "questions", "question_progress", "kp_progress",
                  "knowledge_relations"):
        assert rows(right, table) == [], table
    assert rows(right, "learner_signals") == []


def test_a_waiting_grading_job_is_not_dispatched_by_an_import(pair, tmp_path):
    left, right = pair
    left.connect().execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    left.connect().execute("INSERT INTO part_grading_jobs (attempt_id, execution_id, status)"
                           " VALUES (1, 1, 'pending')")
    left.commit()
    publish(left, tmp_path / "bundle")

    _inspected, result = receive(right, tmp_path / "bundle")

    assert result["status"] == "partial"
    refused = {item["identity"]: item["message"] for item in result["failed"]}
    assert any("grading job" in message for message in refused.values())
    assert rows(right, "part_grading_jobs") == []

    left.connect().execute("UPDATE part_grading_jobs SET status='failed', error='timeout'")
    left.commit()
    publish(left, tmp_path / "bundle")
    _inspected, settled = receive(right, tmp_path / "bundle")
    assert settled["status"] == "success", settled["failed"]
    assert rows(right, "part_grading_jobs")[0]["status"] == "failed"


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


def test_commit_failure_does_not_acknowledge_an_incoming_edit(pair, tmp_path, monkeypatch):
    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    left.connect().execute("UPDATE knowledge_points SET body='after'")
    left.commit()
    publish(left, bundle)
    actual = right.transaction
    failed = False

    @contextmanager
    def fail_once(*args, **kwargs):
        nonlocal failed
        with actual(*args, **kwargs):
            yield
            if not failed and rows(right, "knowledge_points")[0]["body"] == "after":
                failed = True
                raise sqlite3.OperationalError("injected before SQLite commit")

    monkeypatch.setattr(right, "transaction", fail_once)
    _inspection, result = receive(right, bundle)
    assert result["status"] == "partial"
    assert rows(right, "knowledge_points")[0]["body"] != "after"
    retry = inspect_exchange(right, workspace(right), bundle)
    assert len(retry["plan"]["changes"]) == 1
    assert retry["plan"]["outgoing"] == []
    assert receive(right, bundle)[1]["status"] == "success"
    assert rows(right, "knowledge_points")[0]["body"] == "after"


def test_committed_history_survives_sidecar_failure_without_duplicates(pair, tmp_path, monkeypatch):
    from workbench.data import course_sync

    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    left.connect().execute("INSERT INTO problem_attempts VALUES(2,'math-prob-1','new answer')")
    left.commit()
    publish(left, bundle)
    original = course_sync._atomic_json

    def fail_copy(path, value):
        if path == right.root / ".lessonkit/course-sync/state.json" \
                and len(rows(right, "problem_attempts")) == 2:
            raise OSError("injected after SQLite commit")
        return original(path, value)

    monkeypatch.setattr(course_sync, "_atomic_json", fail_copy)
    with pytest.raises(OSError, match="after SQLite commit"):
        receive(right, bundle)
    assert len(rows(right, "problem_attempts")) == 2
    right.close()
    monkeypatch.setattr(course_sync, "_atomic_json", original)
    inspected, result = receive(right, bundle)
    assert inspected["plan"]["changes"] == []
    assert result["status"] == "success"
    assert len(rows(right, "problem_attempts")) == 2
    export = publish(right, tmp_path / "reply")
    assert "course_sync_checkpoint" not in {table["table"] for table in export["tables"]}


@pytest.mark.parametrize("deleting", [False, True])
def test_file_publication_failure_has_read_only_inspection_and_resumes(pair, tmp_path, monkeypatch, deleting):
    from workbench.data import course_sync

    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    relative = ".lessonkit/practice-sets/ps-001.json"
    target = right.root / relative
    before = target.read_bytes()
    if deleting:
        # A manifest tombstone is an explicit deletion, unlike a missing file.
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        descriptor = next(item for item in manifest["assets"]
                          if item["identity"] == "file/" + relative)
        envelope = bundle / descriptor["path"]
        asset = json.loads(envelope.read_text(encoding="utf-8"))
        asset["deleted"] = True
        envelope.write_text(json.dumps(asset), encoding="utf-8")
    else:
        (left.root / relative).write_text('{"title":"new paper"}', encoding="utf-8")
        publish(left, bundle)
    original = course_sync._write_file

    def fail_publish(root, change):
        raise OSError("injected file publication failure")

    monkeypatch.setattr(course_sync, "_write_file", fail_publish)
    _inspection, failed = receive(right, bundle)
    assert failed["status"] == "partial"
    assert any(item["code"] == "publication_pending" for item in failed["failed"])
    assert target.read_bytes() == before
    right.close()
    inspection = inspect_exchange(right, workspace(right), bundle)
    assert inspection["plan"]["changes"] == []
    assert inspection["plan"]["outgoing"] == []
    assert target.read_bytes() == before  # check cannot publish pending files
    monkeypatch.setattr(course_sync, "_write_file", original)
    assert receive(right, bundle)[1]["status"] == "success"
    if deleting:
        assert not target.exists()
    else:
        assert target.read_bytes() == (left.root / relative).read_bytes()


def test_invalid_file_never_enters_a_committed_checkpoint(pair, tmp_path):
    from workbench.data import course_sync

    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    inspection = inspect_exchange(right, workspace(right), bundle)
    bad = {"identity": "file/.lessonkit/learning/bad.md", "action": "create",
           "asset": {"kind": "file", "content": {"path": ".lessonkit/learning/bad.md",
                     "encoding": "base64", "data": "invalid base64!"}, "depends_on": []}}
    inspection["plan"]["changes"] = [bad]
    result = apply_exchange(right, workspace(right), inspection)
    assert result["status"] == "partial"
    state = course_sync._state(right.root, right.course, read_only=True, pool=right)
    assert bad["identity"] not in state["base"]
    assert not state.get("pending_files")


def test_missing_sidecar_does_not_reset_a_committed_course_lineage(pair, tmp_path):
    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    publish(right, tmp_path / "other")
    (right.root / ".lessonkit/course-sync/state.json").unlink()
    # Make this established course non-empty, independently of the package.
    right.connect().execute("INSERT INTO knowledge_points(kp_id,body) VALUES('own','own')")
    right.commit()
    with pytest.raises(ValueError, match="lineage"):
        receive(right, bundle)


def test_unwritable_file_does_not_block_independent_rows(pair, tmp_path, monkeypatch):
    from workbench.data import course_sync

    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    (left.root / ".lessonkit/practice-sets/ps-001.json").write_text('{"title":"changed"}', encoding="utf-8")
    left.connect().execute("UPDATE knowledge_points SET body='new independent body'")
    left.commit()
    publish(left, bundle)
    def denied(*a):
        raise PermissionError("file denied")
    monkeypatch.setattr(course_sync, "_write_file", denied)
    _inspection, result = receive(right, bundle)
    assert result["status"] == "partial"
    assert rows(right, "knowledge_points")[0]["body"] == "new independent body"
    left.connect().execute("UPDATE knowledge_points SET body='another independent body'")
    left.commit()
    publish(left, bundle)
    _inspection, result = receive(right, bundle)
    assert result["status"] == "partial"
    assert rows(right, "knowledge_points")[0]["body"] == "another independent body"


def test_local_edit_after_inspection_cannot_be_overwritten(pair, tmp_path):
    left, right = pair
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    receive(right, bundle)
    left.connect().execute("UPDATE knowledge_points SET body='peer edit'")
    left.commit()
    publish(left, bundle)
    inspection = inspect_exchange(right, workspace(right), bundle)
    with sqlite3.connect(right.db_path) as concurrent:
        concurrent.execute("UPDATE knowledge_points SET body='new local edit'")
    with pytest.raises(ValueError, match="changed after inspection"):
        apply_exchange(right, workspace(right), inspection)
    assert rows(right, "knowledge_points")[0]["body"] == "new local edit"


def test_pending_file_cannot_be_replaced_before_it_publishes(pair, tmp_path, monkeypatch):
    from workbench.data import course_sync

    left, right = pair
    bundle = tmp_path / "bundle"
    relative = ".lessonkit/practice-sets/ps-001.json"
    publish(left, bundle)
    receive(right, bundle)
    original = course_sync._write_file
    def denied(*a):
        raise PermissionError("denied")
    monkeypatch.setattr(course_sync, "_write_file", denied)
    (left.root / relative).write_text('{"title":"first"}', encoding="utf-8")
    publish(left, bundle)
    assert receive(right, bundle)[1]["status"] == "partial"
    (left.root / relative).write_text('{"title":"second"}', encoding="utf-8")
    publish(left, bundle)
    assert receive(right, bundle)[1]["status"] == "partial"
    state = course_sync._state(right.root, right.course, read_only=True, pool=right)
    assert len(state["pending_files"]) == 1
    assert base64.b64decode(state["pending_files"][0]["asset"]["content"]["data"]) == b'{"title":"first"}'
    monkeypatch.setattr(course_sync, "_write_file", original)
    assert receive(right, bundle)[1]["status"] == "success"
    assert (right.root / relative).read_bytes() == b'{"title":"second"}'


@pytest.mark.parametrize("malformed", [{"paper_id": "ps-001"}, None])
def test_bad_execution_item_does_not_block_independent_content(pair, tmp_path, malformed):
    left, right = pair
    running_paper(left)
    bundle = tmp_path / "bundle"
    publish(left, bundle)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    descriptor = next(item for item in manifest["assets"] if item["kind"] == "execution_item")
    envelope = bundle / descriptor["path"]
    asset = json.loads(envelope.read_text(encoding="utf-8"))
    asset["content"] = malformed
    if malformed is None:
        asset["deleted"] = True
    envelope.write_text(json.dumps(asset), encoding="utf-8")
    inspected, result = receive(right, bundle)
    assert any(error["identity"] == descriptor["identity"] for error in inspected["errors"])
    assert result["status"] == "partial"
    assert rows(right, "knowledge_points")[0]["body"] == rows(left, "knowledge_points")[0]["body"]
    assert rows(right, "active_practice") == []
