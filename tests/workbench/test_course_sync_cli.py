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
