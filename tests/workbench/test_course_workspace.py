"""Fresh-course bootstrap on a device that has never seen the course."""

import sqlite3

import pytest

from workbench import registry
from workbench.data import course_workspace


def _tables(path):
    connection = sqlite3.connect(path)
    try:
        return {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        connection.close()


def test_bootstrap_creates_the_canonical_pool_and_skeleton(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "device"
    (root / ".lessonkit" / "figures").mkdir(parents=True)
    (root / ".lessonkit" / "figures" / "old-diagram.png").write_bytes(b"png")
    (root / "handout.md").write_text("learner material", encoding="utf-8")

    relative = course_workspace.bootstrap(root, "uphy2")

    assert relative == ".lessonkit/pool/uphy2.db"
    database = root / relative
    assert database.is_file()
    assert {"knowledge_points", "problems", "learning_current_state",
            "flash_cards"} <= _tables(database)
    assert all((root / ".lessonkit" / name).is_dir()
               for name in ("figures", "explain", "jobs"))
    assert (root / ".lessonkit" / "figures" / "old-diagram.png").read_bytes() == b"png"
    assert (root / "handout.md").read_text(encoding="utf-8") == "learner material"
    assert registry.looks_like_workspace(root)
    assert registry.find_pool(root, "uphy2") == relative
    assert not (tmp_path / "registry" / "workspaces.json").exists()


def test_bootstrap_creates_an_absent_root_folder(tmp_path):
    root = tmp_path / "handoff" / "device"

    assert course_workspace.bootstrap(root, "dmath") == ".lessonkit/pool/dmath.db"

    assert (root / ".lessonkit" / "pool" / "dmath.db").is_file()
    assert (root / ".lessonkit" / "jobs").is_dir()


@pytest.mark.parametrize("course", ["", "DMath", "-dmath", "../dmath", "dmath/ch06",
                                   "dmath ch06", "d\u00e4th", None, 7])
def test_bootstrap_rejects_an_invalid_course_before_creating_anything(tmp_path, course):
    root = tmp_path / "device"

    with pytest.raises(ValueError):
        course_workspace.bootstrap(root, course)

    assert not root.exists()


@pytest.mark.parametrize("folder, existing",
                         [(".lessonkit/pool", "uphy2"),
                          (".lessonkit/pool", "dmath"),
                          ("pool", "uphy2")])
def test_bootstrap_never_overwrites_an_existing_pool(tmp_path, folder, existing):
    root = tmp_path / "device"
    pool = root / folder
    pool.mkdir(parents=True)
    database = pool / f"{existing}.db"
    database.write_bytes(b"learner facts")

    with pytest.raises(ValueError) as excinfo:
        course_workspace.bootstrap(root, "uphy2")

    assert "pool database" in str(excinfo.value)
    assert database.read_bytes() == b"learner facts"
    assert [path.name for path in pool.glob("*.db")] == [f"{existing}.db"]
    assert not (root / ".lessonkit" / "figures").exists()


def test_bootstrap_refuses_when_the_canonical_script_is_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(
        course_workspace, "CREATE_TABLES",
        tmp_path / "checkout" / "pipeline" / "scripts" / "create-tables.py")
    root = tmp_path / "device"

    with pytest.raises(RuntimeError) as excinfo:
        course_workspace.bootstrap(root, "uphy2")

    assert "create-tables.py" in str(excinfo.value)
    assert not root.exists()


def test_bootstrap_surfaces_the_creation_failure_without_registering(tmp_path, monkeypatch):
    stub = tmp_path / "create-tables.py"
    stub.write_text("import sys\n"
                    "sys.stderr.write('cannot create schema\\n')\n"
                    "raise SystemExit(3)\n", encoding="utf-8")
    monkeypatch.setattr(course_workspace, "CREATE_TABLES", stub)
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "device"

    with pytest.raises(RuntimeError) as excinfo:
        course_workspace.bootstrap(root, "uphy2")

    message = str(excinfo.value)
    assert "exit 3" in message
    assert "cannot create schema" in message
    assert root.is_dir()
    assert not (root / ".lessonkit" / "pool" / "uphy2.db").exists()
    assert not (root / ".lessonkit" / "figures").exists()
    assert not (tmp_path / "registry" / "workspaces.json").exists()


def test_bootstrap_bounds_the_captured_child_output(tmp_path, monkeypatch):
    stub = tmp_path / "create-tables.py"
    stub.write_text("import sys\n"
                    "sys.stderr.write('x' * 50000)\n"
                    "raise SystemExit(1)\n", encoding="utf-8")
    monkeypatch.setattr(course_workspace, "CREATE_TABLES", stub)

    with pytest.raises(RuntimeError) as excinfo:
        course_workspace.bootstrap(tmp_path / "device", "uphy2")

    assert len(str(excinfo.value)) < 2500
