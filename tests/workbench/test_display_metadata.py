import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.data import display_metadata


class DisplayMetadataTests(unittest.TestCase):
    def test_tracked_manifest_covers_pool_and_records_topic_audit(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((
            root / "intermediate/dmath/problem_extraction/ch06/02_analysis/"
            "problem-display-metadata.json"
        ).read_text(encoding="utf-8"))
        rows = manifest["problems"]
        self.assertEqual(len(rows), 303)
        self.assertEqual(len({row["problem_id"] for row in rows}), 303)
        summaries = [row for row in rows if row["display_summary"]]
        self.assertEqual(len(summaries), 19)
        self.assertGreaterEqual(len(manifest["audit"]["reviewed_problem_ids"]), 30)
        self.assertEqual(
            set(manifest["audit"]["topic_coverage"]),
            {row["topic_label"] for row in summaries},
        )

    def test_validate_rejects_summary_at_or_below_500_and_ellipsis(self):
        rows = [
            {"problem_id": "p-1", "problem_text": "短题", "display_title": "短题标题",
             "topic_label": "基础计数", "display_summary": "不该存在。"},
            {"problem_id": "p-2", "problem_text": "长" * 501, "display_title": "长题标题",
             "topic_label": "组合计数", "display_summary": "这是截断摘要…"},
        ]
        errors = display_metadata.validate(rows)
        self.assertIn("p-1: summary is only allowed above 500 characters", errors)
        self.assertIn("p-2: summary must not contain an ellipsis", errors)

    def test_validate_requires_complete_display_fields_and_long_summary(self):
        rows = [
            {"problem_id": "p-1", "problem_text": "长" * 501,
             "display_title": "", "topic_label": "", "display_summary": ""},
        ]
        errors = display_metadata.validate(rows)
        self.assertIn("p-1: display title is required", errors)
        self.assertIn("p-1: topic label is required", errors)
        self.assertNotIn("summary is required", " ".join(errors))

    def test_apply_updates_problem_display_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pool.db"
            manifest = Path(tmp) / "metadata.json"
            conn = sqlite3.connect(db)
            conn.execute(
                "CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, "
                "display_title TEXT, topic_label TEXT, display_summary TEXT)"
            )
            conn.execute("INSERT INTO problems VALUES ('p-1', ?, NULL, NULL, NULL)",
                ("长" * 501,))
            conn.commit()
            manifest.write_text(json.dumps({"problems": [{
                "problem_id": "p-1",
                "display_title": "长题标题", "topic_label": "组合计数",
                "display_summary": "概括组合计数题的目标与约束。",
            }]}, ensure_ascii=False), encoding="utf-8")
            try:
                updated = display_metadata.apply(conn, manifest)
                row = conn.execute(
                    "SELECT display_title, topic_label, display_summary FROM problems"
                ).fetchone()
            finally:
                conn.close()
        self.assertEqual(updated, 1)
        self.assertEqual(row, ("长题标题", "组合计数", "概括组合计数题的目标与约束。"))

    def test_apply_rejects_manifest_that_does_not_cover_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pool.db"
            manifest = Path(tmp) / "metadata.json"
            conn = sqlite3.connect(db)
            conn.execute(
                "CREATE TABLE problems (problem_id TEXT PRIMARY KEY, problem_text TEXT, "
                "display_title TEXT, topic_label TEXT, display_summary TEXT)"
            )
            conn.executemany(
                "INSERT INTO problems VALUES (?, ?, NULL, NULL, NULL)",
                [("p-1", "短题一"), ("p-2", "短题二")],
            )
            conn.commit()
            manifest.write_text(json.dumps({"problems": [{
                "problem_id": "p-1", "display_title": "短题标题",
                "topic_label": "基础计数", "display_summary": None,
            }]}, ensure_ascii=False), encoding="utf-8")
            try:
                with self.assertRaisesRegex(
                    ValueError, "manifest must cover every pool problem"
                ):
                    display_metadata.apply(conn, manifest)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
