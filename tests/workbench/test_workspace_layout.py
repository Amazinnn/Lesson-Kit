"""Course layout changes preserve history and remain explicitly opt-in."""

import contextlib
import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from workbench import registry
from workbench.cli import main as cli


@pytest.fixture
def course(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    (root / "pool" / "ingest").mkdir(parents=True)
    database = root / "pool" / "ads.db"
    with sqlite3.connect(database) as conn:
        conn.execute("CREATE TABLE history (body TEXT)")
        conn.execute("INSERT INTO history VALUES ('unchanged pool/reference')")
    conn.close()
    (root / "pool" / "ads.db.ingest-backup").write_bytes(b"backup\x00bytes")
    (root / "pool" / "ingest" / "batch-001.json").write_bytes(b'{"old":"pool/source"}\n')
    (root / "intermediate" / "images").mkdir(parents=True)
    (root / "intermediate" / "images" / "a.png").write_bytes(b"image")
    (root / "sources").mkdir()
    (root / "sources" / "source.md").write_text("original", encoding="utf-8")
    (root / "nested" / "pool").mkdir(parents=True)
    (root / "nested" / "pool" / "copy.db").write_bytes(b"nested")
    registry.register(root, name="ads", course="ads")
    return root


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(list(args))
    return code, out.getvalue()


def test_fresh_init_creates_only_hidden_internal_directories(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "fresh"
    assert run("init", str(root), "--course", "ads")[0] == 0
    assert (root / ".lessonkit" / "pool" / "ads.db").is_file()
    assert registry.get_workspace("fresh")["db"] == ".lessonkit/pool/ads.db"
    assert not (root / "pool").exists()
    assert not (root / "intermediate").exists()


def test_legacy_registration_and_same_course_dual_layout_conflict(course):
    assert registry.find_pool(course, "ads") == "pool/ads.db"
    (course / ".lessonkit" / "pool").mkdir(parents=True)
    (course / ".lessonkit" / "pool" / "ads.db").write_bytes(b"another database")
    with pytest.raises(ValueError, match="several|ambiguous|both"):
        registry.find_pool(course, "ads")


def test_migration_plan_is_read_only_and_apply_preserves_all_history_bytes(course):
    before = {str(p.relative_to(course)): p.read_bytes() for p in course.rglob("*") if p.is_file()}
    registry_before = (registry.base_dir() / "workspaces.json").read_bytes()
    code, output = run("workspace", "ads", "migrate-layout")
    assert code == 0
    plan = json.loads(output)
    assert plan["applied"] is False
    assert len(plan["moves"]) == 2
    assert before == {str(p.relative_to(course)): p.read_bytes() for p in course.rglob("*") if p.is_file()}
    assert (registry.base_dir() / "workspaces.json").read_bytes() == registry_before
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 0, output
    assert json.loads(output)["applied"] is True
    assert registry.get_workspace("ads")["db"] == ".lessonkit/pool/ads.db"
    for relative, content in before.items():
        old = Path(relative)
        new = Path(".lessonkit") / old if old.parts[0] in {"pool", "intermediate"} else old
        assert (course / new).read_bytes() == content
    assert not (course / "pool").exists()
    assert not (course / "intermediate").exists()
    assert run("workspace", "ads", "migrate-layout", "--apply")[0] == 0


def test_migration_collision_refuses_before_any_move(course):
    (course / ".lessonkit" / "intermediate").mkdir(parents=True)
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2
    assert "exists" in output or "collision" in output
    assert (course / "pool" / "ads.db").is_file()
    assert registry.get_workspace("ads")["db"] == "pool/ads.db"


def test_registry_failure_rolls_back_directory_moves(course):
    with patch.object(registry, "save_registry", side_effect=OSError("registry unavailable")):
        code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2, output
    assert (course / "pool" / "ads.db").is_file()
    assert (course / "intermediate" / "images" / "a.png").is_file()
    assert not (course / ".lessonkit" / "pool").exists()
    assert registry.get_workspace("ads")["db"] == "pool/ads.db"


@pytest.mark.parametrize("status", ["running", "queued", "waiting_for_stop"])
def test_active_turn_blocks_apply_but_allows_read_only_preview(course, status):
    jobs = course / ".lessonkit" / "jobs" / "conv-001"
    jobs.mkdir(parents=True)
    (jobs / "turn-001.json").write_text(json.dumps({"status": status}), encoding="utf-8")
    assert run("workspace", "ads", "migrate-layout")[0] == 0
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2 and "active work" in output
    assert (course / "pool" / "ads.db").is_file()


def test_managed_service_blocks_apply(course):
    from workbench.cli import service
    with patch.object(service, "running_state", return_value={"pid": 123}):
        code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2 and "stop" in output
    assert (course / "pool" / "ads.db").is_file()


def test_moved_history_still_rolls_back_and_new_figures_use_workspace_root(tmp_path, monkeypatch):
    from tests.workbench.fixtures import build_fixture_db, open_db
    from workbench import ingest

    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    (root / "pool").mkdir(parents=True)
    database = root / "pool" / "dmath.db"
    with open_db(database) as conn:
        build_fixture_db(conn)
    registry.register(root, name="dmath", course="dmath", chapter="ch06")
    image = root / "source.png"
    image.write_bytes(b"image")
    import hashlib
    logical = "dmath/ch06/" + hashlib.sha256(b"image").hexdigest() + ".png"
    manifest = {"kind": "figure-patch", "course": "dmath", "chapter": "ch06",
                "items": [{"owner_type": "problem", "owner_id": "dmath-ch06-prob-001",
                           "text": f"![]({logical})", "figure_files": [{"source_path": str(image)}]}]}
    source = root / "patch.json"
    source.write_text(json.dumps(manifest), encoding="utf-8")
    applied = ingest.apply_figure_patch(database, source)
    before_db = database.read_bytes()
    assert run("workspace", "dmath", "migrate-layout", "--apply")[0] == 0
    database = root / ".lessonkit" / "pool" / "dmath.db"
    assert database.read_bytes() == before_db
    batch = ingest.list_batches(database)[0]
    assert Path(batch["backup_path"]).is_file()
    assert ingest.rollback_batch(database, applied["batch_id"])["ok"]
    with open_db(database) as conn:
        assert conn.execute("SELECT problem_text FROM problems").fetchone()[0] == "P1"
    applied = ingest.apply_figure_patch(database, source, backup_path=database.with_suffix(".new-backup"))
    assert applied["ok"]
    assert (root / ".lessonkit" / "figures" / logical).is_file()
    assert not (root / ".lessonkit" / ".lessonkit").exists()
    assert (root / ".lessonkit" / "pool" / "ingest" / f'{applied["batch_id"]}.json').is_file()


def test_history_resolver_keeps_external_and_prose_paths_unchanged(course):
    from workbench import workspace_layout
    outside = course.parent / "external" / "pool" / "file.json"
    assert run("workspace", "ads", "migrate-layout", "--apply")[0] == 0
    database = course / ".lessonkit" / "pool" / "ads.db"
    moved = workspace_layout.resolve_history_path(database, course / "pool" / "ingest" / "batch-001.json")
    assert moved == course / ".lessonkit" / "pool" / "ingest" / "batch-001.json"
    assert workspace_layout.resolve_history_path(database, outside) == outside


def test_migration_rebases_only_existing_markdown_link_targets_and_keeps_originals(course):
    source = course / "sources" / "中文 notes.md"
    source.write_text("source bytes", encoding="utf-8")
    history = course / "intermediate" / "history.md"
    original = (
        "prose ../sources/中文%20notes.md stays unchanged\r\n"
        "[source](../sources/中文%20notes.md#section)\r\n"
        "[escaped](../sources/中文\\ notes.md#anchor)\r\n"
        "[angle](<../sources/中文 notes.md#anchor>)\r\n"
        "[image](images/a.png)\r\n"
        "[missing](../sources/missing.md)\r\n"
        "[invalid external](https://[broken)\r\n"
        "[reference]: ../sources/中文%20notes.md#ref\r\n"
        "`[code](../sources/中文%20notes.md)`\r\n"
        "```md\r\n[source](../sources/中文%20notes.md)\r\n```\r\n"
    ).encode("utf-8")
    history.write_bytes(original)
    code, preview = run("workspace", "ads", "migrate-layout")
    assert code == 0 and history.read_bytes() == original
    assert len(json.loads(preview)["link_changes"]) == 1
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 0, output
    moved = course / ".lessonkit" / "intermediate" / "history.md"
    expected = original.replace(b"](../sources/", b"](../../sources/")
    expected = expected.replace(b"](<../sources/", b"](<../../sources/")
    expected = expected.replace(b"]: ../sources/", b"]: ../../sources/")
    expected = expected.replace(b"[missing](../../sources/missing.md)", b"[missing](../sources/missing.md)")
    expected = expected.replace(b"`[code](../../sources/", b"`[code](../sources/")
    expected = expected.replace(b"```md\r\n[source](../../sources/", b"```md\r\n[source](../sources/")
    assert moved.read_bytes() == expected
    report = json.loads(output)
    receipt = json.loads(Path(report["receipt"]).read_text(encoding="utf-8"))
    assert Path(receipt["link_changes"][0]["backup"]).read_bytes() == original
    assert source.read_text(encoding="utf-8") == "source bytes"


def test_registry_failure_also_restores_rebased_markdown_bytes(course):
    original = b"[source](../sources/source.md)\n"
    (course / "intermediate" / "history.md").write_bytes(original)
    with patch.object(registry, "save_registry", side_effect=OSError("registry unavailable")):
        code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2, output
    assert (course / "intermediate" / "history.md").read_bytes() == original
    assert not (course / ".lessonkit" / "layout-migration").exists()


def test_hidden_guard_reads_hidden_artifacts_and_writes_existing_state_area(course):
    import lessonkit

    assert run("workspace", "ads", "migrate-layout", "--apply")[0] == 0
    registry.update_active("ads", "ads", "ch01")
    required, _ = lessonkit.render_paths("extract-problems", "ads", "ch01")
    for relative in required:
        path = course / ".lessonkit" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("PASS", encoding="utf-8")
    code, output = run("guard", "ads", "extract-problems", "--apply")
    assert code == 0, output
    assert (course / ".lessonkit" / "state.yaml").is_file()
    assert not (course / ".lessonkit" / ".lessonkit").exists()
    assert not (course / "intermediate").exists()
    assert lessonkit.render_paths("extract-problems", "ads", "ch01")[0] == required


def test_hidden_graph_artifact_and_generation_hint_do_not_require_root_output(course):
    from workbench.server import api
    assert run("workspace", "ads", "migrate-layout", "--apply")[0] == 0
    workspace = registry.update_active("ads", "ads", "ch01")
    with pytest.raises(api.ApiError) as exc:
        api.graph_artifact(None, workspace, {}, None)
    assert "--out .lessonkit/output/ads/ch01" in str(exc.value)
    path = course / ".lessonkit" / "output" / "ads" / "ch01" / "ch01-graph.html"
    path.parent.mkdir(parents=True)
    path.write_text("hidden graph", encoding="utf-8")
    assert api.graph_artifact(None, workspace, {}, None) == {"html": "hidden graph"}
    assert not (course / "output").exists()


def test_second_directory_move_failure_restores_first_move(course):
    real_rename = Path.rename

    def fail_second(path, target):
        if path == course / "intermediate":
            raise OSError("second directory is busy")
        return real_rename(path, target)

    with patch.object(Path, "rename", fail_second):
        code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2 and "busy" in output
    assert (course / "pool" / "ads.db").is_file()
    assert (course / "intermediate" / "images" / "a.png").is_file()
    assert registry.get_workspace("ads")["db"] == "pool/ads.db"


def test_partial_registry_write_failure_restores_registry_bytes(course):
    path = registry.base_dir() / "workspaces.json"
    before = path.read_bytes()

    def fail_save(data):
        path.write_bytes(b"partial")
        raise OSError("registry write failed")

    with patch.object(registry, "save_registry", fail_save):
        code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2, output
    assert path.read_bytes() == before
    assert (course / "pool" / "ads.db").is_file()


def test_escaping_destination_refuses_before_any_move(course):
    outside = course.parent / "outside"
    outside.mkdir()
    try:
        (course / ".lessonkit").symlink_to(outside, target_is_directory=True)
    except OSError:
        import os
        if os.name != "nt":
            raise
        import _winapi
        _winapi.CreateJunction(str(outside), str(course / ".lessonkit"))
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 2 and "escapes" in output
    assert (course / "pool" / "ads.db").is_file()
    assert list(outside.iterdir()) == []


def test_markdown_cross_area_links_and_hidden_figure_links_remain_valid(course):
    figures = course / ".lessonkit" / "figures"
    figures.mkdir(parents=True)
    (figures / "a.png").write_bytes(b"figure")
    original = b"[batch](../pool/ingest/batch-001.json)\n![figure](../.lessonkit/figures/a.png)\n"
    (course / "intermediate" / "links.md").write_bytes(original)
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 0, output
    moved = course / ".lessonkit" / "intermediate" / "links.md"
    assert moved.read_bytes() == b"[batch](../pool/ingest/batch-001.json)\n![figure](../figures/a.png)\n"


def test_migrated_pool_still_honors_explicit_practice_exports(tmp_path, monkeypatch):
    from tests.workbench.fixtures import build_fixture_db, open_db
    from workbench.data.pool import Pool
    from workbench.data import practice_sets

    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    (root / "pool").mkdir(parents=True)
    database = root / "pool" / "dmath.db"
    with open_db(database) as conn:
        build_fixture_db(conn)
    registry.register(root, name="dmath", course="dmath", chapter="ch06")
    pool = Pool(root, database, "dmath", "ch06")
    try:
        saved = practice_sets.create_saved(pool, "Saved paper", ["dmath-ch06-prob-001"])
    finally:
        pool.close()
    assert run("workspace", "dmath", "migrate-layout", "--apply")[0] == 0
    exported = tmp_path / "learner-export"
    manifest = exported / "plan.json"
    code, output = run("pull", "dmath", "--n", "1", "--plan", str(manifest), "--print", str(exported))
    assert code == 0, output
    assert manifest.is_file()
    assert (exported / "ch06-problem-set.md").is_file()
    pool = cli._pool(registry.get_workspace("dmath"))
    try:
        assert practice_sets.get_saved(pool, saved["practice_set_id"])["title"] == "Saved paper"
    finally:
        pool.close()
    assert not (root / "pool").exists()


@pytest.mark.parametrize("migrate", [False, True])
def test_hidden_provider_result_defaults_inside_hidden_area_and_honors_explicit_output(course, migrate):
    from workbench import ingest
    from workbench.ingest.artifacts import write_artifact

    if migrate:
        assert run("workspace", "ads", "migrate-layout", "--apply")[0] == 0
    source = course.parent / "incoming" / "task.json"
    source.parent.mkdir()
    source.write_text('{"kind":"ingest-task"}', encoding="utf-8")

    def provider(task, output, name, workspace):
        return write_artifact(output, {"kind": "solutions"})

    with patch.object(ingest, "run", side_effect=provider):
        code, output = run("ingest", "ads", "run", str(source), "--provider", "pi")
        assert code == 0, output
        default = Path(json.loads(output)["artifact"])
        assert default.is_relative_to(course / ".lessonkit")
        assert default.is_file()
        hidden_source = course / ".lessonkit" / "intermediate" / "result.json"
        hidden_source.write_text('{"kind":"ingest-task"}', encoding="utf-8")
        code, output = run("ingest", "ads", "run", str(hidden_source), "--provider", "pi")
        assert code == 0, output
        assert json.loads(hidden_source.read_text(encoding="utf-8"))["kind"] == "ingest-task"
        exported = course.parent / "requested-export.json"
        code, output = run("ingest", "ads", "run", str(source), "--provider", "pi", "--output", str(exported))
        assert code == 0, output
        assert exported.is_file()
    assert list(source.parent.iterdir()) == [source]


def test_migration_rebases_balanced_parenthesis_link_destinations(course):
    for name in ("lecture(1).md", "lecture(unit(1)).md"):
        (course / "sources" / name).write_bytes(b"source")
    original = (
        "[ordinary](../sources/lecture(1).md#section)\r\n"
        "[nested](../sources/lecture(unit(1)).md \"read first\")\r\n"
        "[escaped](../sources/lecture\\(1\\).md)\r\n"
        "[angle](<../sources/lecture(unit(1)).md>)\r\n"
        "`[code](../sources/lecture(1).md)`\r\n"
        "```md\r\n[nested](../sources/lecture(unit(1)).md)\r\n```\r\n"
        "prose ../sources/lecture(1).md\r\n"
    ).encode("utf-8")
    history = course / "intermediate" / "parentheses.md"
    history.write_bytes(original)
    code, preview = run("workspace", "ads", "migrate-layout")
    assert code == 0 and history.read_bytes() == original
    targets = json.loads(preview)["link_changes"][0]["targets"]
    assert len(targets) == 4
    code, output = run("workspace", "ads", "migrate-layout", "--apply")
    assert code == 0, output
    expected = original.replace(b"](../sources/", b"](../../sources/")
    expected = expected.replace(b"](<../sources/", b"](<../../sources/")
    expected = expected.replace(b"`[code](../../sources/", b"`[code](../sources/")
    expected = expected.replace(b"```md\r\n[nested](../../sources/", b"```md\r\n[nested](../sources/")
    assert (course / ".lessonkit" / "intermediate" / "parentheses.md").read_bytes() == expected
    assert Path(json.loads(output)["link_changes"][0]["backup"]).read_bytes() == original


@pytest.mark.parametrize("area", ["", ".lessonkit"])
def test_unmigrated_course_guard_reads_existing_or_new_hidden_work_without_local_script(course, area):
    import lessonkit

    registry.update_active("ads", "ads", "ch01")
    required, _ = lessonkit.render_paths("extract-problems", "ads", "ch01")
    for relative in required:
        path = course / area / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("PASS", encoding="utf-8")
    assert not (course / "lessonkit.py").exists()
    code, output = run("guard", "ads", "extract-problems", "--apply")
    assert code == 0, output
    assert registry.get_workspace("ads")["db"] == "pool/ads.db"
    assert (course / ".lessonkit/state.yaml").is_file()


def test_new_hidden_guard_work_cannot_pass_against_stale_legacy_artifacts(course):
    import lessonkit

    registry.update_active("ads", "ads", "ch01")
    required, _ = lessonkit.render_paths("extract-problems", "ads", "ch01")
    for area in ("", ".lessonkit"):
        for relative in required:
            path = course / area / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PASS", encoding="utf-8")
    (course / ".lessonkit" / required[0]).unlink()
    code, output = run("guard", "ads", "extract-problems", "--apply")
    assert code == 2 and "Result: FAIL" in output, output
    assert ".lessonkit/intermediate/" in output


def test_guard_records_hidden_outputs_when_both_hidden_and_legacy_exports_exist(course):
    import lessonkit

    registry.update_active("ads", "ads", "ch01")
    required, outputs = lessonkit.render_paths("problem-set", "ads", "ch01")
    for area in ("", ".lessonkit"):
        for relative in required + outputs:
            path = course / area / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PASS", encoding="utf-8")
    code, output = run("guard", "ads", "problem-set", "--apply")
    assert code == 0, output
    state = lessonkit.read_state(course)
    assert ".lessonkit/" + outputs[0] in state["required_artifacts"]
    assert outputs[0] not in state["required_artifacts"]


@pytest.mark.parametrize("areas", ["legacy", "hidden", "equal", "conflict"])
def test_legacy_image_planning_reads_new_hidden_work_without_silently_switching_content(tmp_path, areas):
    from tests.workbench.fixtures import build_fixture_db, open_db
    from workbench import ingest

    root = tmp_path / "course"
    database = root / "pool/dmath.db"
    database.parent.mkdir(parents=True)
    with open_db(database) as conn:
        build_fixture_db(conn)
        conn.execute("UPDATE problems SET problem_text=? WHERE problem_id=?",
                     ("P1 ![image](images/legacy.png)", "dmath-ch06-prob-001"))
        conn.commit()
    for area in ("", ".lessonkit"):
        if (area == "" and areas == "hidden") or (area and areas == "legacy"):
            continue
        image = root / area / "intermediate/ch06/images/legacy.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"different" if area and areas == "conflict" else b"original")
    before = database.read_bytes()
    result = ingest.build_legacy_figure_manifest(database, root)
    assert database.read_bytes() == before
    if areas == "conflict":
        assert not result["ok"] and any("conflict" in e for e in result["errors"]), result
    else:
        assert result["ok"], result
        image = result["manifests"][0]["items"][0]["figure_files"][0]["source_path"]
        assert Path(image).read_bytes() == b"original"
