"""Portable projection checks use isolated course data and real files."""

import json
import sqlite3
from pathlib import Path

import pytest

from workbench.data.course_sync import export_course, inspect_exchange, read_exchange, _save_state
from workbench.data.pool import Pool


@pytest.fixture
def course(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONKIT_WB_HOME", str(tmp_path / "registry"))
    root = tmp_path / "course"
    root.mkdir()
    database = root / "course.db"
    conn = sqlite3.connect(database)
    conn.executescript("""
        CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT, figure_paths TEXT);
        CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, kp_ids TEXT,
                               figure_paths TEXT, deleted_at TEXT);
        CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY, problem_id TEXT, answer_text TEXT);
    """)
    conn.execute("INSERT INTO knowledge_points VALUES (?,?,?)", ("math-kp-1", "公式 $x$", None))
    conn.execute("INSERT INTO problems VALUES (?,?,?,?,?)",
                 ("math-prob-1", "原题", '["math-kp-1"]', '["math/ch01/a.png"]', None))
    conn.execute("INSERT INTO problem_attempts VALUES (?,?,?)", (1, "math-prob-1", "原始答案\n$x=1$"))
    conn.commit()
    conn.close()
    (root / ".lessonkit/figures/math/ch01").mkdir(parents=True)
    (root / ".lessonkit/figures/math/ch01/a.png").write_bytes(b"source image bytes\x00\xff")
    (root / ".lessonkit/practice-sets").mkdir()
    (root / ".lessonkit/practice-sets/ps-001.json").write_text('{"title":"试卷"}\n', encoding="utf-8")
    pool = Pool(root, database, "math", "")
    yield pool, {"name": "math", "path": str(root), "db": "course.db", "active_course": "math"}
    pool.close()


def test_export_preserves_all_columns_original_answers_and_bytes(course, tmp_path):
    pool, workspace = course
    result = export_course(pool, workspace, tmp_path / "bundle")
    assert result["status"] == "success"
    package = read_exchange(tmp_path / "bundle")
    rows = [asset["content"]["row"] for asset in package["assets"].values()
            if asset["kind"] == "row" and asset["content"]["table"] == "problem_attempts"]
    assert rows[0]["answer_text"] == "原始答案\n$x=1$"
    assert any(asset["kind"] == "file" for asset in package["assets"].values())
    paths = {asset["content"]["path"]: asset for asset in package["assets"].values()
             if asset["kind"] == "file"}
    import base64
    assert base64.b64decode(paths[".lessonkit/figures/math/ch01/a.png"]["content"]["data"]) == b"source image bytes\x00\xff"
    assert ".lessonkit/practice-sets/ps-001.json" in paths


def test_origin_and_row_identity_survive_repeat_exports(course, tmp_path):
    pool, workspace = course
    export_course(pool, workspace, tmp_path / "one")
    export_course(pool, workspace, tmp_path / "two")
    one, two = (read_exchange(tmp_path / name) for name in ("one", "two"))
    assert one["course"] == two["course"]
    assert one["assets"] == two["assets"]
    assert one["origin"] == two["origin"]


def test_attempt_references_use_record_identity_and_ignore_local_number(course, tmp_path):
    pool, workspace = course
    connection = pool.connect()
    connection.executescript("""
        CREATE TABLE feedback_events (id INTEGER PRIMARY KEY, attempt_id INTEGER, note TEXT);
        CREATE TABLE practice_request_operations (request_id TEXT PRIMARY KEY, payload TEXT, result TEXT);
        CREATE TABLE part_attempt_context (attempt_id INTEGER PRIMARY KEY, part_json TEXT);
    """)
    connection.execute("INSERT INTO feedback_events VALUES (1,1,'保持原文')")
    connection.execute("INSERT INTO practice_request_operations VALUES (?,?,?)",
                       ('request-1', '{"attempt_id": 1}', '{"answer_text":"$x=1$", "attempt_id":1}'))
    connection.execute("INSERT INTO part_attempt_context VALUES (?,?)", (1, '{"title":"原小问"}'))
    pool.commit()
    export_course(pool, workspace, tmp_path / "one")
    first = read_exchange(tmp_path / "one")
    state_path = pool.root / '.lessonkit/course-sync/state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    old_identity = state['row_identities'].pop('problem_attempts/[1]')
    state['row_identities']['problem_attempts/[8]'] = old_identity
    _save_state(pool, state)
    connection.execute('UPDATE problem_attempts SET id=8 WHERE id=1')
    connection.execute('UPDATE feedback_events SET attempt_id=8')
    connection.execute('UPDATE part_attempt_context SET attempt_id=8')
    connection.execute('UPDATE practice_request_operations SET payload=?,result=?',
                       ('{"attempt_id": 8}', '{"answer_text":"$x=1$", "attempt_id":8}'))
    pool.commit()
    export_course(pool, workspace, tmp_path / "two")
    second = read_exchange(tmp_path / "two")
    assert first['assets'] == second['assets']
    attempt = second['assets'][old_identity]['content']['row']
    assert attempt['id'] == old_identity
    assert attempt['answer_text'] == '原始答案\n$x=1$'
    context = next(asset for asset in second['assets'].values()
                   if asset['kind'] == 'row' and asset['content']['table'] == 'part_attempt_context')
    assert context['depends_on'] == [old_identity]


def test_dangling_attempt_reference_is_explicit_export_error(course, tmp_path):
    pool, workspace = course
    pool.connect().executescript('CREATE TABLE feedback_events (id INTEGER PRIMARY KEY, attempt_id INTEGER);'
                               'INSERT INTO feedback_events VALUES (1,999);')
    with pytest.raises(ValueError, match='unresolved course record reference'):
        export_course(pool, workspace, tmp_path / 'bundle')


def test_repeated_export_does_not_acknowledge_one_sided_edits(course, tmp_path):
    pool, workspace = course
    export_course(pool, workspace, tmp_path / 'initial')
    original = read_exchange(tmp_path / 'initial')
    pool.connect().execute("UPDATE knowledge_points SET body='本机修改'")
    pool.commit()
    export_course(pool, workspace, tmp_path / 'second')
    export_course(pool, workspace, tmp_path / 'third')
    package = read_exchange(tmp_path / 'third')
    assert package['base'] == original['assets']
    assert package['assets'] != package['base']


def test_inspection_does_not_initialize_sync_state_or_registry(course, tmp_path, monkeypatch):
    pool, workspace = course
    export_course(pool, workspace, tmp_path / 'bundle')
    import shutil
    shutil.rmtree(pool.root / '.lessonkit/course-sync')
    pool.connect().execute('DROP TABLE course_sync_checkpoint')
    pool.commit()
    registry_home = tmp_path / 'new-registry'
    monkeypatch.setenv('LESSONKIT_WB_HOME', str(registry_home))
    before = {path.relative_to(pool.root): path.read_bytes()
              for path in pool.root.rglob('*') if path.is_file()}
    result = inspect_exchange(pool, workspace, tmp_path / 'bundle')
    after = {path.relative_to(pool.root): path.read_bytes()
             for path in pool.root.rglob('*') if path.is_file()}
    assert before == after
    assert not registry_home.exists()
    assert result['association_required']
    assert result['errors'] == []


def test_inspection_reports_schema_mismatch_without_discarding_other_assets(course, tmp_path):
    pool, workspace = course
    export_course(pool, workspace, tmp_path / 'bundle')
    manifest_path = tmp_path / 'bundle/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    descriptor = next(item for item in manifest['assets'] if 'knowledge_points/' in item['identity'])
    path = tmp_path / 'bundle' / descriptor['path']
    asset = json.loads(path.read_text(encoding='utf-8'))
    asset['content']['row']['unregistered_column'] = 'foreign field'
    path.write_text(json.dumps(asset), encoding='utf-8')
    result = inspect_exchange(pool, workspace, tmp_path / 'bundle')
    assert result['errors'][0]['identity'] == descriptor['identity']
    assert descriptor['identity'] not in result['incoming']
    assert result['incoming']


def test_inspection_reports_a_shared_asset_this_side_never_acknowledged(course, tmp_path):
    """The sender's base cannot vouch for a value this installation never received."""
    pool, workspace = course
    export_course(pool, workspace, tmp_path / 'bundle')
    manifest_path = tmp_path / 'bundle/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    identity = next(key for key in manifest['base'] if 'knowledge_points/' in key)
    manifest['base'][identity]['content']['row']['body'] = '另一个安装的说法'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    state_path = pool.root / '.lessonkit/course-sync/state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state['base'].pop(identity)
    _save_state(pool, state)

    result = inspect_exchange(pool, workspace, tmp_path / 'bundle')

    assert [error['identity'] for error in result['errors']
            if error['code'] == 'baseline_mismatch'] == [identity]


def test_repeat_export_reuses_unchanged_files_and_cleans_replaced_envelopes(course, tmp_path):
    pool, workspace = course
    bundle = tmp_path / 'bundle'
    first = export_course(pool, workspace, bundle)
    before = {path.relative_to(bundle): path.read_bytes() for path in bundle.rglob('*.json')
              if path.name != 'manifest.json'}
    second = export_course(pool, workspace, bundle)
    assert second['written'] == 0
    assert second['reused'] == first['assets']
    assert before == {path.relative_to(bundle): path.read_bytes() for path in bundle.rglob('*.json')
                      if path.name != 'manifest.json'}
    pool.connect().execute("UPDATE knowledge_points SET body='只改一项'")
    pool.commit()
    third = export_course(pool, workspace, bundle)
    assert third['written'] == 1
    assert third['reused'] == first['assets'] - 1
    envelopes = [path for path in bundle.rglob('*.json')
                 if 'files' not in path.relative_to(bundle).parts]
    assert len(envelopes) == first['assets'] + 1
    assert read_exchange(bundle)['errors'] == []
    # The Tutor-readable copy is a view of the same package, not an extra asset.
    assert (bundle / 'files/.lessonkit/practice-sets/ps-001.json').is_file()


def test_unknown_table_is_explicitly_rejected(course, tmp_path):
    pool, workspace = course
    pool.connect().execute("CREATE TABLE unexpected_data (id TEXT)")
    pool.commit()
    with pytest.raises(ValueError, match="unexpected_data"):
        export_course(pool, workspace, tmp_path / "bundle")


def test_missing_referenced_figure_is_not_complete_success(course, tmp_path):
    pool, workspace = course
    (pool.root / ".lessonkit/figures/math/ch01/a.png").unlink()
    with pytest.raises(ValueError, match="figure"):
        export_course(pool, workspace, tmp_path / "bundle")


def test_registered_learning_files_and_original_sources_are_included(course, tmp_path):
    pool, workspace = course
    folder = pool.root / ".lessonkit/course-sync"
    folder.mkdir()
    (pool.root / "source.pdf").write_bytes(b"PDF original")
    (pool.root / "learning.md").write_text("# 误解与续接\n", encoding="utf-8")
    (folder / "config.json").write_text(json.dumps({"managed_paths": ["source.pdf", "learning.md"]}))
    export_course(pool, workspace, tmp_path / "bundle")
    paths = {value["content"]["path"] for value in read_exchange(tmp_path / "bundle")["assets"].values()
             if value["kind"] == "file"}
    assert {"source.pdf", "learning.md"} <= paths


def test_reader_reports_missing_asset_and_rejects_path_escape(course, tmp_path):
    pool, workspace = course
    folder = tmp_path / "bundle"
    export_course(pool, workspace, folder)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    descriptor = manifest["assets"][0]
    (folder / descriptor["path"]).unlink()
    assert read_exchange(folder)["errors"][0]["code"] == "missing_asset"
    descriptor["path"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        read_exchange(folder)


def test_corrupt_goals_and_unconfirmed_pending_paper_are_not_ignored(course, tmp_path):
    pool, workspace = course
    (pool.root / ".lessonkit/goals.json").write_text("broken", encoding="utf-8")
    with pytest.raises(ValueError, match="goals"):
        export_course(pool, workspace, tmp_path / "bundle")


def test_unknown_bundle_version_and_duplicate_identity_are_rejected(course, tmp_path):
    pool, workspace = course
    folder = tmp_path / "bundle"
    export_course(pool, workspace, folder)
    path = folder / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["assets"].append(manifest["assets"][0])
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        read_exchange(folder)
    manifest["format_version"] = 99
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="format_version"):
        read_exchange(folder)


def test_one_invalid_asset_does_not_hide_independent_valid_files(course, tmp_path):
    pool, workspace = course
    folder = tmp_path / "bundle"
    export_course(pool, workspace, folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    (folder / manifest["assets"][0]["path"]).write_text("broken", encoding="utf-8")
    result = read_exchange(folder)
    assert len(result["errors"]) == 1
    assert len(result["assets"]) == len(manifest["assets"]) - 1


def test_windows_git_alias_paths_are_refused(course, tmp_path):
    pool, workspace = course
    folder = pool.root / ".lessonkit/course-sync"
    folder.mkdir()
    for invalid in (".GIT/config", "source/../.git/config", "file.txt "):
        (folder / "config.json").write_text(json.dumps({"managed_paths": [invalid]}))
        with pytest.raises(ValueError, match="path"):
            export_course(pool, workspace, tmp_path / "bundle")


def test_failed_republication_keeps_previous_manifest_and_asset_bytes(course, tmp_path, monkeypatch):
    from workbench.data import course_sync
    pool, workspace = course
    folder = tmp_path / "bundle"
    export_course(pool, workspace, folder)
    original = read_exchange(folder)
    pool.connect().execute("UPDATE problems SET problem_text='changed'")
    pool.commit()
    writer = course_sync._atomic_json

    def interrupted(path, value, **kwargs):
        if Path(path) == folder / "manifest.json":
            raise OSError("interrupted before publishing manifest")
        return writer(path, value, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(course_sync, "_atomic_json", interrupted)
        with pytest.raises(OSError, match="interrupted"):
            export_course(pool, workspace, folder)
    assert read_exchange(folder) == original
    export_course(pool, workspace, folder)
    assert read_exchange(folder)["course"] == original["course"]


def test_standalone_and_installed_checkpoint_schemas_match():
    from pool.scripts.pool_schema import ensure_course_sync_schema as standalone
    from workbench.data.pool import ensure_course_sync_schema as installed

    first, second = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
    try:
        assert standalone(first) == installed(second)
        assert standalone(first) == installed(second) == []
        query = "SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
        assert first.execute(query).fetchall() == second.execute(query).fetchall()
    finally:
        first.close()
        second.close()


def test_export_does_not_keep_readable_copy_of_deleted_file(course,tmp_path):
    import base64
    from workbench.data import course_sync
    pool,workspace=course
    destination=tmp_path/"package";file=destination/"files/.lessonkit/learning/gone.md"
    file.parent.mkdir(parents=True);file.write_bytes(b"old")
    assets={"file/.lessonkit/learning/gone.md":{"kind":"file","content":{"path":".lessonkit/learning/gone.md","encoding":"base64","data":base64.b64encode(b"old").decode()},"deleted":True,"depends_on":[]}}
    assert course_sync._write_readable_files(destination,assets)==[]
    assert not file.exists()


def test_large_export_groups_assets_and_reuses_unchanged_files(course,tmp_path):
    pool,workspace=course
    pool.connect().executemany("INSERT INTO knowledge_points VALUES (?,?,NULL)",
                              [(f"math-extra-{n}","body") for n in range(520)])
    pool.commit();target=tmp_path/"grouped"
    first=export_course(pool,workspace,target)
    manifest=json.loads((target/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["format_version"]==2
    physical={item["path"] for item in manifest["assets"]}
    assert len(physical)<len(manifest["assets"])/100
    assert len(read_exchange(target)["assets"])==first["assets"]
    snapshot={name:(target/name).read_bytes() for name in physical}
    second=export_course(pool,workspace,target)
    assert second["written"]==0
    assert second["manifest_changed"] is False
    assert snapshot=={name:(target/name).read_bytes() for name in physical}


def test_layout_transition_never_overwrites_files_of_published_generation(course,tmp_path,monkeypatch):
    from workbench.data import course_bundle,course_sync
    pool,workspace=course
    pool.connect().executemany("INSERT INTO knowledge_points VALUES (?,?,NULL)",
                              [(f"math-extra-{n}","body") for n in range(520)])
    pool.commit();target=tmp_path/"transition"
    monkeypatch.setattr(course_bundle,"INDIVIDUAL_LIMIT",10000)
    export_course(pool,workspace,target)
    before=read_exchange(target)
    manifest=json.loads((target/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["format_version"]==1
    physical={item["path"] for item in manifest["assets"]}
    snapshot={name:(target/name).read_bytes() for name in physical}
    monkeypatch.setattr(course_bundle,"INDIVIDUAL_LIMIT",512)
    atomic=course_sync._atomic_json
    def interrupt(path,value,**kwargs):
        if Path(path).name=="manifest.json":raise OSError("publication interrupted")
        return atomic(path,value,**kwargs)
    monkeypatch.setattr(course_sync,"_atomic_json",interrupt)
    with pytest.raises(OSError,match="publication interrupted"):
        export_course(pool,workspace,target)
    assert snapshot=={name:(target/name).read_bytes() for name in physical}
    assert read_exchange(target)["assets"]==before["assets"]


def test_a_retired_staging_table_is_skipped_and_reported(course, tmp_path):
    """A legacy pool exports, and the omission is visible rather than silent."""
    pool, workspace = course
    pool.connect().executescript(
        "CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY, body TEXT);"
        "INSERT INTO candidate_problems VALUES ('c-1','旧候选');"
        "CREATE TABLE candidate_attempts (id INTEGER PRIMARY KEY, candidate_id TEXT);"
        "INSERT INTO candidate_attempts VALUES (1,'c-1');")
    pool.commit()

    result = export_course(pool, workspace, tmp_path / 'bundle')
    package = read_exchange(tmp_path / 'bundle')

    assert result['status'] == 'success'
    assert not any('candidate' in identity for identity in package['assets'])
    skipped = [table for table in package['tables'] if table.get('retired_tables')]
    assert skipped and skipped[0]['retired_tables'] == ['candidate_attempts', 'candidate_problems']


def test_a_retired_problem_column_is_dropped_from_the_projection(course, tmp_path):
    """`problems.topic_label` is deleted by DATA_MODEL, so it never travels."""
    pool, workspace = course
    pool.connect().execute("ALTER TABLE problems ADD COLUMN topic_label TEXT")
    pool.connect().execute("UPDATE problems SET topic_label='旧标签'")
    pool.commit()

    export_course(pool, workspace, tmp_path / 'bundle')
    package = read_exchange(tmp_path / 'bundle')

    problem = next(asset for asset in package['assets'].values()
                   if asset['kind'] == 'row' and asset['content']['table'] == 'problems')
    assert 'topic_label' not in problem['content']['row']
    assert problem['content']['row']['problem_text'] == '原题'
    assert any(table.get('retired_columns') == ['topic_label'] for table in package['tables'])
