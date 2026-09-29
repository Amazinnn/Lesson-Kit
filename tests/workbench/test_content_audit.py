"""The content hygiene audit reports findings and leaves the workspace intact."""

import contextlib
import hashlib
import io
import json
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture, open_db
from workbench.data.content_audit import CHECKS, audit
from workbench.data.pool import Pool


class ContentAuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.ws = self.fixture.ws
        self.db = self.fixture.db_path
        self.pool = Pool(self.ws, self.db, "dmath", "ch06")

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def insert_problem(self, problem_id, text, **fields):
        values = {
            "problem_id": problem_id,
            "kp_ids": '[]',
            "problem_text": text,
            "problem_type": "calculation",
            "source_kind": "textbook",
            "origin_kind": "source_problem",
            **fields,
        }
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        with open_db(self.db) as conn:
            conn.execute(
                f"INSERT INTO problems ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )

    def test_reports_each_named_finding_and_performs_no_writes(self):
        self.insert_problem(
            "dmath-ch06-prob-002", "P1!", display_title="duplicate",
        )
        self.insert_problem(
            "dmath-ch06-prob-003", "Given that the field strength equals x", 
            display_title="fragment A",
        )
        self.insert_problem(
            "dmath-ch06-prob-004",
            "Given that the field strength equals x, compute the potential.",
            display_title="fragment B",
        )
        self.insert_problem(
            "dmath-ch06-mq-001", "判断题：电场是矢量。", micro_quiz=json.dumps(
                {"quiz_type": "yes_no"}, ensure_ascii=False),
            practice_modes=None,
        )
        self.insert_problem(
            "dmath-ch06-prob-005", "Find the point shown ![diagram](dmath/ch06/missing.png)",
            display_title=None, figure_paths=json.dumps(["dmath/ch06/missing.png"]),
        )
        figure_root = self.ws / ".lessonkit" / "figures" / "dmath" / "ch06"
        figure_root.mkdir(parents=True)
        (figure_root / "orphan.png").write_bytes(b"orphan")

        before_hash = hashlib.sha256(self.db.read_bytes()).hexdigest()
        before_counts = {}
        with open_db(self.db) as conn:
            for table in ("problems", "knowledge_points", "ingest_batches"):
                before_counts[table] = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

        result = audit(self.pool)
        checks = {finding["check"] for finding in result["findings"]}
        self.assertEqual(set(CHECKS), checks)
        duplicate = next(item for item in result["findings"]
                         if item["check"] == "duplicates")
        self.assertEqual(duplicate["problem_ids"], [
            "dmath-ch06-prob-001", "dmath-ch06-prob-002",
        ])
        self.assertTrue(any("prefix/suffix" in item["detail"]
                            for item in result["findings"]
                            if item["check"] == "fragments"))
        self.assertTrue(any(item["problem_ids"] == ["dmath-ch06-mq-001"]
                            for item in result["findings"]
                            if item["check"] == "unmarked-objective"))
        self.assertTrue(any(item["problem_ids"] == ["dmath-ch06-prob-001"]
                            for item in result["findings"]
                            if item["check"] == "untitled"))
        self.assertTrue(any("missing.png" in item["detail"]
                            for item in result["findings"]
                            if item["check"] == "figures"))
        self.assertTrue(any("orphan.png" in item["detail"]
                            for item in result["findings"]
                            if item["check"] == "orphan-figures"))

        with open_db(self.db) as conn:
            after_counts = {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in before_counts
            }
        self.assertEqual(after_counts, before_counts)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before_hash)

    def test_check_selection_and_cli_exit_codes(self):
        from workbench.cli import main as cli
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            clean_code = cli.main(["data", "dmath", "audit", "--check", "figures"])
        self.assertEqual(clean_code, 0)
        self.assertIn("content audit: clean", output.getvalue())

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            finding_code = cli.main(["data", "dmath", "audit", "--check", "untitled", "--json"])
        self.assertEqual(finding_code, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["checks"], ["untitled"])
        self.assertEqual(report["findings"][0]["problem_ids"], ["dmath-ch06-prob-001"])


if __name__ == "__main__":
    unittest.main()
