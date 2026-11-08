"""FLOW-03: fix a wrong edit by direct correction, with learning records intact."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.workbench.fixtures import WorkspaceFixture  # noqa: E402
from workbench.data import content  # noqa: E402
from workbench.data.pool import Pool  # noqa: E402


def main():
    fixture = WorkspaceFixture()
    try:
        pool = Pool(fixture.ws, fixture.db_path, "dmath", "ch06")
        conn = sqlite3.connect(fixture.db_path)
        conn.execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text)"
            " VALUES ('dmath-ch06-prob-001', 'wrong', '我原来的作答')")
        conn.commit()
        conn.close()

        # The wrong edit, made the same way any edit is made.
        content.update(pool, "problem", "dmath-ch06-prob-001",
                       {"display_title": "错的标题"})
        # The correction: another direct edit, same identity, no deletion.
        content.update(pool, "problem", "dmath-ch06-prob-001",
                       {"display_title": "正确的标题"})

        row = content.get(pool, "problem", "dmath-ch06-prob-001")
        conn = sqlite3.connect(fixture.db_path)
        attempts = conn.execute(
            "SELECT COUNT(*), MIN(answer_text) FROM problem_attempts WHERE problem_id=?",
            ("dmath-ch06-prob-001",)).fetchone()
        conn.close()
        result = {
            "flow": "FLOW-03 direct correction",
            "problem_id": row["problem_id"],
            "display_title": row["display_title"],
            "identity_unchanged": row["problem_id"] == "dmath-ch06-prob-001",
            "attempts": attempts[0],
            "original_answer_kept": attempts[1] == "我原来的作答",
            "undo_entry_removed": not hasattr(__import__("workbench.ingest", fromlist=["x"]),
                                              "rollback_batch"),
        }
        print(json.dumps(result, ensure_ascii=False))
        pool.close()
    finally:
        fixture.cleanup()


if __name__ == "__main__":
    main()
