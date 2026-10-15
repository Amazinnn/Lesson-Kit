from pathlib import Path

saved_path = Path("tests/workbench/test_saved_practice_sets.py")
saved = saved_path.read_text(encoding="utf-8")
old = '        self.assertEqual(started["source_kind"], "practice_set")\n'
new = '        self.assertEqual(started["source_kind"], "paper")\n'
if saved.count(old) != 1:
    raise SystemExit(f"saved-paper legacy expectation count={saved.count(old)}")
saved_path.write_text(saved.replace(old, new, 1), encoding="utf-8")

ui_path = Path("tests/workbench/test_ui_routes.py")
ui = ui_path.read_text(encoding="utf-8")
replacements = {
    '        self.assertIn("临时练习", runs)\n': '        self.assertIn("临时试卷", runs)\n',
    '        self.assertEqual(payload["source_kind"], "quick")\n': '        self.assertEqual(payload["source_kind"], "paper")\n',
}
for old, new in replacements.items():
    if ui.count(old) != 1:
        raise SystemExit(f"UI legacy expectation {old.strip()!r} count={ui.count(old)}")
    ui = ui.replace(old, new, 1)
ui_path.write_text(ui, encoding="utf-8")

Path(".github/workflows/one-shot-paper-source-test-expectations.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-paper-source-test-expectations.py").unlink()
