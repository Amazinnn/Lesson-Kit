from pathlib import Path
import pytest
from workbench.cli import runtime_source

def test_installed_worktree_is_served_and_explicit_override_wins(tmp_path):
    main=tmp_path/'main'; linked=tmp_path/'preview'
    (main/'.git/worktrees/preview').mkdir(parents=True)
    (main/'workbench/cli').mkdir(parents=True)
    (linked/'workbench/cli').mkdir(parents=True)
    (linked/'.git').write_text('gitdir: '+str(main/'.git/worktrees/preview'))
    (main/'.git/worktrees/preview/commondir').write_text('../..')
    assert runtime_source.project_root(installed=linked)==linked.resolve()
    assert runtime_source.project_root(linked,installed=main)==linked.resolve()

def test_explicit_path_must_be_a_lesson_kit_source(tmp_path):
    (tmp_path/'workbench/cli').mkdir(parents=True)
    with pytest.raises(ValueError): runtime_source.project_root(tmp_path/'missing',installed=tmp_path)

def test_default_source_is_the_imported_package_checkout():
    assert runtime_source.project_root()==Path(runtime_source.__file__).resolve().parents[2]

def test_snapshot_detects_edit_delete_rollback_and_ignores_runtime_data(tmp_path):
    code=tmp_path/'workbench/cli/x.py';code.parent.mkdir(parents=True);code.write_text('a')
    assets=tmp_path/'workbench/server/static/x.js';assets.parent.mkdir(parents=True);assets.write_text('a')
    first=runtime_source.snapshot(tmp_path)
    code.write_text('ab'); assert runtime_source.changed_kind(first,runtime_source.snapshot(tmp_path))=='python'
    code.unlink(); assert runtime_source.changed_kind(first,runtime_source.snapshot(tmp_path))=='python'
    code.write_text('a'); restored=runtime_source.snapshot(tmp_path)
    assets.write_text('ab');assert runtime_source.changed_kind(restored,runtime_source.snapshot(tmp_path))=='assets'
    before=runtime_source.snapshot(tmp_path)
    ignored=tmp_path/'workbench/__pycache__/x.py';ignored.parent.mkdir();ignored.write_text('bad')
    assert runtime_source.snapshot(tmp_path)==before

def test_invalid_source_detected_without_executing(tmp_path):
    p=tmp_path/'workbench/x.py';p.parent.mkdir();p.write_text('if :')
    assert runtime_source.syntax_error(tmp_path)
    p.write_text('raise RuntimeError("must not execute")')
    assert runtime_source.syntax_error(tmp_path) is None
