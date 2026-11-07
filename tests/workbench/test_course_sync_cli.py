"""The course-sync CLI: receipts, exit codes, Git orchestration, scheduled task."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from workbench.cli import course_sync


SCHEMA = """
    CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT, figure_paths TEXT);
    CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, kp_ids TEXT,
                           figure_paths TEXT, deleted_at TEXT);
    CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY, problem_id TEXT, answer_text TEXT);
"""


def git(cwd, *args, check=True):
    completed = subprocess.run(
        ["git", *args], cwd=str(cwd), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and completed.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {completed.stderr}")
    return completed


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    root.mkdir()
    (root / "pool").mkdir()
    database = root / "pool/course.db"
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO knowledge_points VALUES ('math-kp-1','公式 $x$',NULL)")
    connection.execute("INSERT INTO problems VALUES "
                       "('math-prob-1','原题','[\"math-kp-1\"]',NULL,NULL)")
    connection.execute("INSERT INTO problem_attempts VALUES (1,'math-prob-1','原始答案')")
    connection.commit()
    connection.close()
    from workbench import registry
    registry.register(name="math", path=root, db="pool/course.db",
                      course="math", chapter="")
    return root


def cli(*argv):
    return course_sync.main(list(argv), prog="lesson-kit course-sync")


def test_export_then_check_then_receive_reports_a_receipt(
        workspace, tmp_path, capsys):
    bundle = tmp_path / "bundle"
    assert cli("math", "export", "--to", str(bundle), "--json-output") == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["status"] == "success"

    assert cli("math", "check", "--from", str(bundle), "--json-output") == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "success"
    assert checked["changes"] == []
    assert checked["unchanged"] > 0

    receipt = workspace / ".lessonkit/course-sync/last-receipt.json"
    assert json.loads(receipt.read_text(encoding="utf-8"))["exit_code"] == 0

    assert cli("math", "receive", "--from", str(bundle), "--json-output") == 0
    received = json.loads(capsys.readouterr().out)
    assert received["operation"].startswith("receive-")
    assert received["remote"] is None


def test_missing_input_is_an_input_error(workspace, capsys):
    assert cli("math", "export") == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    assert cli("missing", "status") == 2
    assert "unknown workspace" in capsys.readouterr().out
    assert cli("math", "receive", "--from", str(workspace / "nowhere")) == 2


def test_status_reports_state_media_and_the_latest_receipt(workspace, tmp_path, capsys):
    cli("math", "export", "--to", str(tmp_path / "bundle"))
    capsys.readouterr()
    assert cli("math", "status") == 0
    state = json.loads(capsys.readouterr().out)
    assert state["course"]["id"] == "math"
    assert state["state"]["base_size"] > 0
    assert state["last_receipt"]["status"] == "success"


def _repo(tmp_path):
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    git(tmp_path, "init", "-b", "main", str(repo))
    git(repo, "config", "user.name", "Sync Test")
    git(repo, "config", "user.email", "sync@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "README.md").write_text("# course\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")
    git(repo, "push", "-u", "origin", "main")
    return repo


def test_sync_publishes_a_first_package_and_reports_the_remote(
        workspace, tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda title, message: True)

    assert cli("math", "sync", "--repo", str(repo), "--path", "sync",
               "--json-output") == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "success", receipt
    assert receipt["remote"]["status"] == "published"
    assert (repo / "sync/manifest.json").is_file()
    assert "receive" not in receipt["local"]

    published = git(repo, "log", "--oneline", "-1")
    assert "exchange course files" in published.stdout

    assert cli("math", "sync", "--repo", str(repo), "--path", "sync",
               "--json-output") == 0
    again = json.loads(capsys.readouterr().out)
    assert again["remote"]["status"] == "unchanged", again
    assert again["local"]["export"]["written"] == 0
    assert again["local"]["export"]["manifest_changed"] is False
    assert again["local"]["receive"]["applied"] == []


def test_sync_receives_what_the_other_installation_published(
        workspace, tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda title, message: True)
    cli("math", "sync", "--repo", str(repo), "--path", "sync")
    capsys.readouterr()

    # Another installation publishes a change through the same package path.
    other = tmp_path / "other"
    other.mkdir()
    (other / "pool").mkdir()
    connection = sqlite3.connect(other / "pool/course.db")
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()
    from workbench import registry
    registry.register(name="other", path=other, db="pool/course.db",
                      course="math", chapter="")
    cli("other", "receive", "--from", str(repo / "sync"))
    capsys.readouterr()
    connection = sqlite3.connect(other / "pool/course.db")
    connection.execute("UPDATE knowledge_points SET body='另一位安装改的正文'")
    connection.commit()
    connection.close()
    assert cli("other", "sync", "--repo", str(repo), "--path", "sync",
               "--json-output") == 0
    outer = json.loads(capsys.readouterr().out)
    assert outer["remote"]["status"] in {"published", "unchanged"}, outer

    code = cli("math", "sync", "--repo", str(repo), "--path", "sync", "--json-output")
    receipt = json.loads(capsys.readouterr().out)
    assert code == 0, receipt
    assert any("knowledge_points" in identity
               for identity in receipt["local"]["receive"]["applied"])
    connection = sqlite3.connect(workspace / "pool/course.db")
    body = connection.execute("SELECT body FROM knowledge_points").fetchone()[0]
    connection.close()
    assert body == "另一位安装改的正文"


def test_a_genuine_conflict_returns_3_and_notifies_once(
        workspace, tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    seen = []
    monkeypatch.setattr(course_sync, "_toast",
                        lambda title, message: seen.append(message) or True)
    cli("math", "sync", "--repo", str(repo), "--path", "sync")
    capsys.readouterr()

    other = tmp_path / "other"
    other.mkdir()
    (other / "pool").mkdir()
    connection = sqlite3.connect(other / "pool/course.db")
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()
    from workbench import registry
    registry.register(name="other", path=other, db="pool/course.db",
                      course="math", chapter="")
    cli("other", "receive", "--from", str(repo / "sync"))
    capsys.readouterr()

    connection = sqlite3.connect(workspace / "pool/course.db")
    connection.execute("UPDATE knowledge_points SET body='本地版本'")
    connection.commit()
    connection.close()
    connection = sqlite3.connect(other / "pool/course.db")
    connection.execute("UPDATE knowledge_points SET body='对方版本'")
    connection.commit()
    connection.close()
    cli("other", "sync", "--repo", str(repo), "--path", "sync")
    capsys.readouterr()

    code = cli("math", "receive", "--from", str(repo / "sync"), "--json-output")
    receipt = json.loads(capsys.readouterr().out)
    assert code == 3, receipt
    assert receipt["status"] == "conflict"
    assert len(seen) == 1

    # The same unresolved conflict is not announced twice.
    assert cli("math", "receive", "--from", str(repo / "sync")) == 3
    capsys.readouterr()
    assert len(seen) == 1

    assert cli("math", "receive", "--from", str(repo / "sync"),
               "--keep", "incoming") == 0
    capsys.readouterr()
    connection = sqlite3.connect(workspace / "pool/course.db")
    body = connection.execute("SELECT body FROM knowledge_points").fetchone()[0]
    connection.close()
    assert body == "对方版本"


def test_a_rejected_push_reports_local_completion_without_remote_success(
        workspace, tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda title, message: True)
    git(tmp_path, "--git-dir", str(tmp_path / "remote.git"), "config",
        "receive.denyCurrentBranch", "ignore")
    # A pre-receive hook rejects the publication.
    (tmp_path / "remote.git/hooks").mkdir(exist_ok=True)
    hook = tmp_path / "remote.git/hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)

    code = cli("math", "sync", "--repo", str(repo), "--path", "sync", "--json-output")
    receipt = json.loads(capsys.readouterr().out)

    assert code == 4, receipt
    assert receipt["status"] == "partial"
    assert receipt["remote"]["status"] == "failed"
    assert receipt["local"]["export"]["status"] == "success"
    assert (repo / "sync/manifest.json").is_file()


def test_schedule_install_records_media_and_registers_one_task(
        workspace, tmp_path, capsys, monkeypatch):
    calls = []

    class Completed:
        returncode = 0
        stdout = b"SUCCESS"
        stderr = b""

    def fake_run(args, **kwargs):
        calls.append(args)
        return Completed()

    monkeypatch.setattr(course_sync.subprocess, "run", fake_run)
    code = cli("math", "schedule", "install", "--repo", str(tmp_path / "repo"),
               "--path", "sync")
    receipt = json.loads(capsys.readouterr().out)

    assert code == 0
    assert receipt["action"] == "install"
    config = json.loads((workspace / ".lessonkit/course-sync/config.json")
                        .read_text(encoding="utf-8"))
    assert config["media"]["repo"] == str(tmp_path / "repo")
    assert config["media"]["package"] == "sync"
    assert calls[0][:4] == ["schtasks", "/TN", course_sync.TASK_NAME, "/Create"]
    assert "--all-configured" in " ".join(calls[0])

    assert cli("math", "schedule", "disable") == 0
    assert "/DISABLE" in calls[-1]
    assert cli("math", "schedule", "remove") == 0
    assert "/Delete" in calls[-1]


def test_all_configured_aggregates_each_course_exit_code(
        workspace, tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda title, message: True)
    cli("math", "schedule", "install", "--repo", str(repo), "--path", "sync")
    capsys.readouterr()
    from workbench import registry
    idle = tmp_path / "idle-course"
    (idle / "pool").mkdir(parents=True)
    connection = sqlite3.connect(idle / "pool/course.db")
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()
    registry.register(name="idle", path=idle, db="pool/course.db",
                      course="idle", chapter="")

    code = cli("--all-configured", "sync", "--json-output")
    receipt = json.loads(capsys.readouterr().out)

    assert code == 0, receipt
    assert receipt["courses"] == {"math": 0}


@pytest.mark.parametrize("conflict", [False, True])
def test_sync_never_publishes_an_unaccepted_incoming_package(workspace, tmp_path, monkeypatch, capsys, conflict):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(course_sync.git_sync, "inspect_repository", lambda *a: {
        "repo": str(repo), "branch_checked_out": True})
    monkeypatch.setattr(course_sync.git_sync, "fetch_remote", lambda *a: {"commit": "remote-tip"})
    monkeypatch.setattr(course_sync, "_materialize", lambda *a: tmp_path / "incoming")
    monkeypatch.setattr(course_sync.exchange, "inspect_exchange", lambda *a: {"errors": []})
    monkeypatch.setattr(course_sync.exchange, "apply_exchange", lambda *a: {
        "status": "conflict" if conflict else "partial", "applied": [], "kept": [],
        "failed": [] if conflict else [{"identity": "bad", "code": "apply_failed"}],
        "conflicts": [{"identity": "contested"}] if conflict else []})
    def refuse_publication(*a):
        pytest.fail("an unresolved package must not be exported or published")
    monkeypatch.setattr(course_sync.exchange, "export_course", refuse_publication)
    monkeypatch.setattr(course_sync.git_sync, "publish", refuse_publication)
    monkeypatch.setattr(course_sync, "_toast", lambda *a: True)
    assert cli("math", "sync", "--repo", str(repo), "--path", "sync", "--json-output") == (3 if conflict else 4)
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["remote"]["status"] == "not_published"


def test_git_fetch_failure_keeps_a_transport_receipt(workspace, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(course_sync.git_sync, "inspect_repository", lambda *a: {
        "repo": str(tmp_path), "branch_checked_out": True})
    def offline(*a):
        raise RuntimeError("remote is offline")
    monkeypatch.setattr(course_sync.git_sync, "fetch_remote", offline)
    assert cli("math", "sync", "--repo", str(tmp_path), "--path", "sync", "--json-output") == 4
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "partial"
    assert "offline" in str(receipt["errors"])
    stored = json.loads((workspace / ".lessonkit/course-sync/last-receipt.json").read_text(encoding="utf-8"))
    assert stored["exit_code"] == 4


def test_notice_rearms_after_resolution(workspace, monkeypatch):
    from types import SimpleNamespace
    pool = SimpleNamespace(root=workspace, course="math")
    shown = []
    monkeypatch.setattr(course_sync, "_toast", lambda *a: shown.append(a) or True)
    course_sync._notice(pool, {"conflicts": ["same"]})
    course_sync._notice(pool, {"conflicts": []})
    course_sync._notice(pool, {"conflicts": ["same"]})
    assert len(shown) == 2


def test_toast_passes_text_as_data(monkeypatch):
    calls = []
    def capture(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(course_sync.subprocess, "run", capture)
    monkeypatch.setattr(course_sync.sys, "platform", "win32")
    assert course_sync._toast("标题 ' $x", "正文 ; $y")
    command, kwargs = calls[0]
    assert "标题 ' $x" not in command
    assert kwargs["env"]["LK_TOAST_TITLE"] == "标题 ' $x"
    assert kwargs["env"]["LK_TOAST_MESSAGE"] == "正文 ; $y"
    assert kwargs["timeout"] > 0


def test_sync_tracks_readable_files_and_removes_old_envelopes(workspace, tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda *a: True)
    (workspace / ".lessonkit/learning").mkdir(parents=True)
    (workspace / ".lessonkit/learning/summary.md").write_text("summary", encoding="utf-8")
    assert cli("math", "sync", "--repo", str(repo), "--path", "sync") == 0
    capsys.readouterr()
    assert git(repo, "status", "--porcelain").stdout == ""
    connection = sqlite3.connect(workspace / "pool/course.db")
    connection.execute("UPDATE knowledge_points SET body='changed'")
    connection.commit()
    connection.close()
    assert cli("math", "sync", "--repo", str(repo), "--path", "sync") == 0
    capsys.readouterr()
    assert git(repo, "status", "--porcelain").stdout == ""
    tracked = git(repo, "ls-files", "sync/files").stdout
    assert "summary.md" in tracked


def test_sync_receives_tutor_edits_from_readable_git_files(workspace, tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    monkeypatch.setattr(course_sync, "_toast", lambda *a: True)
    learning = workspace / ".lessonkit/learning/summary.md"
    learning.parent.mkdir(parents=True)
    learning.write_text("before", encoding="utf-8")
    assert cli("math", "sync", "--repo", str(repo), "--path", "sync") == 0
    capsys.readouterr()
    other = tmp_path / "tutor"
    git(tmp_path, "clone", str(tmp_path / "remote.git"), str(other))
    git(other, "config", "user.name", "Tutor Test")
    git(other, "config", "user.email", "tutor@example.com")
    git(other, "config", "commit.gpgsign", "false")
    (other / "sync/files/.lessonkit/learning/summary.md").write_text("Tutor update", encoding="utf-8")
    git(other, "add", "--", "sync/files/.lessonkit/learning/summary.md")
    git(other, "commit", "-m", "Tutor update")
    git(other, "push", "origin", "main")
    code = cli("math", "sync", "--repo", str(repo), "--path", "sync", "--json-output")
    receipt = json.loads(capsys.readouterr().out)
    assert code == 0, receipt
    assert learning.read_text(encoding="utf-8") == "Tutor update"
