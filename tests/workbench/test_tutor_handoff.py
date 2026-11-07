"""The Tutor handoff a course exchange package carries, and its return path."""

import json
import sqlite3

import pytest

from workbench import registry
from workbench.cli import course_sync
from workbench.data import course_sync as exchange
from workbench.data import tutor_handoff
from workbench.data.pool import Pool

SCHEMA = """
    CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT, related_kp_ids TEXT);
    CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, kp_ids TEXT,
                           difficulty TEXT, difficulty_model TEXT, deleted_at TEXT);
    CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY, problem_id TEXT, status TEXT,
                                   note TEXT, answer_text TEXT, verdict INTEGER, choices TEXT,
                                   created_at TEXT);
    CREATE TABLE practice_execution_ids (id INTEGER PRIMARY KEY AUTOINCREMENT);
    CREATE TABLE active_practice (singleton INTEGER PRIMARY KEY, source_kind TEXT,
                                  source_ref TEXT, source_label TEXT, kp_ids_json TEXT,
                                  practice_mode TEXT, rating_mode TEXT, cursor INTEGER,
                                  started_at TEXT, updated_at TEXT, execution_id INTEGER,
                                  paper_generation INTEGER, reveal_timing TEXT);
    CREATE TABLE active_practice_items (position INTEGER PRIMARY KEY, item_type TEXT,
                                        item_id TEXT, state TEXT, draft_json TEXT,
                                        attempt_id INTEGER, content_revision INTEGER);
    CREATE TABLE paper_state (paper_id TEXT PRIMARY KEY, generation INTEGER, checkpoint_json TEXT,
                              pending_json TEXT, pending_delete INTEGER DEFAULT 0);
    CREATE TABLE practice_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, reveal_timing TEXT);
    CREATE TABLE feedback_events (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT,
                                  item_id TEXT, note TEXT, attempt_id INTEGER);
"""


@pytest.fixture
def course(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    (root / ".lessonkit/learning").mkdir(parents=True)
    (root / ".lessonkit/practice-sets").mkdir()
    (root / "pool").mkdir()
    database = root / "pool/pool.db"
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO knowledge_points (kp_id, body) VALUES ('kp-1','正文')")
    connection.execute("INSERT INTO problems (problem_id, problem_text, kp_ids)"
                       " VALUES ('p-1','求 $x$','[\"kp-1\"]')")
    connection.execute(
        "INSERT INTO problem_attempts (id, problem_id, status, note, answer_text, verdict,"
        " choices, created_at) VALUES (1,'p-1','wrong','看错了符号','我的答案 $x=-1$',0,"
        "'[\"A\"]','2026-11-07 09:00:00')")
    connection.execute("INSERT INTO practice_execution_ids DEFAULT VALUES")
    connection.execute(
        "INSERT INTO active_practice VALUES (1,'paper','ps-001','期中卷','[\"kp-1\"]','exam',"
        "'immediate',1,'2026-11-07 09:00:00','2026-11-07 09:10:00',1,1,'on_submit')")
    connection.execute(
        "INSERT INTO active_practice_items VALUES (0,'problem','p-1','answered',"
        "'{\"reference_viewed\":true}',1,3)")
    connection.execute(
        "INSERT INTO active_practice_items VALUES (1,'problem','p-2','pending',NULL,NULL,1)")
    connection.commit()
    connection.close()
    (root / ".lessonkit/goals.json").write_text(json.dumps([
        {"goal_id": "g1", "title": "掌握条件概率", "detail": "能独立完成综合题",
         "status": "active"}], ensure_ascii=False), encoding="utf-8")
    (root / ".lessonkit/learning/misconceptions.md").write_text(
        "# 已纠正的误解\n\n- 把独立当成互斥\n", encoding="utf-8")
    (root / ".lessonkit/practice-sets/ps-001.json").write_text(
        '{"title":"期中卷","plan":{"items":[{"problem_id":"p-1"},{"problem_id":"p-2"}]}}\n',
        encoding="utf-8")
    registry.register(name="math", path=root, db="pool/pool.db",
                      course="math", chapter="")
    pool = Pool(root, database, "math", "")
    yield pool, {"name": "math", "path": str(root), "db": "pool/pool.db",
                 "active_course": "math"}
    pool.close()


def test_the_handoff_carries_answers_reveals_unanswered_items_and_position(course):
    pool, workspace = course
    text = tutor_handoff.build(pool)

    assert "掌握条件概率" in text
    assert "能独立完成综合题" in text
    assert ".lessonkit/learning/misconceptions.md" in text
    assert "把独立当成互斥" not in text, "the index points at the file, it does not copy it"
    assert "`ps-001`" in text
    assert "第 2 题 / 共 2 题" in text
    assert "揭晓时机：on_submit" in text
    assert "已标不会" not in text
    assert "`p-2`" in text, "the unanswered item is named"
    assert "我的答案 $x=-1$" in text, "the original answer stays verbatim"
    assert "客观判定：错" in text
    assert '所选选项：["A"]' in text
    assert text == tutor_handoff.build(pool), "the same facts give the same text"


def test_the_handoff_lands_in_the_package_and_never_in_the_workspace(course, tmp_path):
    pool, workspace = course
    code = course_sync.main(["math", "export", "--to", str(tmp_path / "bundle")],
                            prog="lesson-kit course-sync")

    assert code == 0
    assert (tmp_path / "bundle" / tutor_handoff.FILE_NAME).is_file()
    assert not (pool.root / tutor_handoff.FILE_NAME).exists()
    assert (pool.root / ".lessonkit/learning/misconceptions.md").is_file()


def test_tutor_written_learning_files_are_received(course, tmp_path, capsys):
    pool, workspace = course
    bundle = tmp_path / "bundle"
    course_sync.main(["math", "export", "--to", str(bundle)])
    capsys.readouterr()

    readable = bundle / "files/.lessonkit/learning/misconceptions.md"
    assert readable.is_file(), "the Tutor reads a plain copy, not an envelope"
    readable.write_text("# 已纠正的误解\n\n- 把独立当成互斥（已用文氏图纠正）\n",
                        encoding="utf-8")
    (bundle / "files/.lessonkit/learning/tutor-notes.md").write_text(
        "# Tutor 回写\n\n- 下一步先练互斥与独立的区分\n", encoding="utf-8")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert not any(item["identity"].endswith("tutor-notes.md") for item in manifest["assets"])

    assert course_sync.main(["math", "receive", "--from", str(bundle)]) == 0
    capsys.readouterr()

    assert (pool.root / ".lessonkit/learning/misconceptions.md").read_text(
        encoding="utf-8").endswith("（已用文氏图纠正）\n")


def test_new_tutor_learning_file_is_received_without_hand_editing_manifest(course,tmp_path,capsys):
    pool,workspace=course;bundle=tmp_path/"bundle"
    assert course_sync.main(["math","export","--to",str(bundle)])==0
    capsys.readouterr()
    note=bundle/"files/.lessonkit/learning/new-summary.md"
    note.write_text("# 新总结\n\n原始答案与诊断分开。\n",encoding="utf-8")
    assert course_sync.main(["math","receive","--from",str(bundle)])==0
    target=pool.root/".lessonkit/learning/new-summary.md"
    assert target.is_file(),capsys.readouterr().out
    assert target.read_bytes()==note.read_bytes()
    assert course_sync.main(["math","export","--to",str(tmp_path/"returned")])==0
    assert (tmp_path/"returned/files/.lessonkit/learning/new-summary.md").read_bytes()==note.read_bytes()
