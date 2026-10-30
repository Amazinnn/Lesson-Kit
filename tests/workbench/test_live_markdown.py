from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_live_editor_is_local_and_uses_source_state():
    source = (ROOT / "workbench/frontend/live-editor.js").read_text(encoding="utf-8")
    assert "EditorState.create" in source
    assert "Decoration.replace" in source
    assert "MutationObserver" in source
    assert "isComposing" in source
    assert "window.LessonKitMarkdown" in source
    assert "getMarkdown" not in source

def test_every_shell_loads_standalone_editor():
    source = (ROOT / "workbench/server/pages.py").read_text(encoding="utf-8")
    assert "/static/live-editor.js" in source
