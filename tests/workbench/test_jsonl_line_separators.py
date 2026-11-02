"""JSONL readers must split on "\\n" only.

`str.splitlines()` also breaks on U+2028 / U+2029 / U+0085, which are legal
inside a JSON string; a tool output carrying one used to cut a valid event or
transcript record in half and surface as "Unterminated string" whenever the
conversation was read.
"""

import json

from workbench.bridge import conversations
from workbench.data.pool import Pool

SEPARATORS = "前\u2028中\u2029后\x85末"


def test_json_lines_keeps_unicode_line_separators_inside_the_record(tmp_path):
    path = tmp_path / "x.jsonl"
    path.write_text(
        json.dumps({"a": SEPARATORS}, ensure_ascii=False) + "\n"
        + json.dumps({"b": 1}) + "\n",
        encoding="utf-8")
    lines = conversations._json_lines(path)
    assert len(lines) == 2
    assert json.loads(lines[0])["a"] == SEPARATORS


def test_events_read_survives_unicode_line_separators(tmp_path):
    pool = Pool(tmp_path, tmp_path / "pool.db", "test", "ch01")
    folder = pool.jobs_dir() / "conv-001"
    folder.mkdir(parents=True)
    (folder / "turn-001.events.jsonl").write_text(
        json.dumps({"sequence": 1, "kind": "text", "text": SEPARATORS},
                   ensure_ascii=False) + "\n",
        encoding="utf-8")
    try:
        rows = conversations.events(pool, "conv-001", "turn-001")
    finally:
        pool.close()
    assert rows[0]["text"] == SEPARATORS
