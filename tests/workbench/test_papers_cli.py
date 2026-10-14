"""Agent paper saving uses the browser's managed reusable-paper store."""

import contextlib
import io
import json
import threading
import unittest
import urllib.request
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture


class PapersCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import main as cli
        from workbench.data import practice_sets
        from workbench.registry import get_workspace
        from workbench.cli.entry import lesson_kit_main

        self.cli = cli
        self.lesson_kit_main = lesson_kit_main
        self.practice_sets = practice_sets
        self.workspace = get_workspace("dmath")
        self.pool = cli._pool(self.workspace)
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-002", '["dmath-ch06-kp-001"]', "P2", "S2",
             "calculation", "textbook"),
        )
        self.pool.commit()
        self.prior = practice_sets.create_saved(
            self.pool, "Existing paper", ["dmath-ch06-prob-001"])

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                code = self.lesson_kit_main(["papers", "dmath", *args])
            except SystemExit as exc:
                code = exc.code
        return code, output.getvalue()

    def write_manifest(self, name, plan):
        path = Path(self.fixture.tmp.name) / name
        if isinstance(plan, bytes):
            path.write_bytes(plan)
        else:
            path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def saved_file_bytes(self):
        folder = self.fixture.ws / ".lessonkit" / "practice-sets"
        return {path.name: path.read_bytes() for path in folder.glob("*.json")}

    def valid_plan(self):
        return {
            "kind": "practice-set",
            "title": "Agent paper",
            "course": "dmath",
            "request": {"source_kinds": ["textbook"], "search_stem": "ordered pairs"},
            "items": [
                {"problem_id": "dmath-ch06-prob-002", "reason": "forced"},
                {"problem_id": "dmath-ch06-prob-001", "reason": "scope"},
            ],
        }

    def test_entry_saves_ordered_manifest_and_browser_lists_it_without_db_writes(self):
        manifest = self.write_manifest("paper.json", self.valid_plan())
        source_before = manifest.read_bytes()
        papers_before = self.saved_file_bytes()
        db_before = self.fixture.db_path.read_bytes()

        code, output = self.run_cli("save", "--input", str(manifest))

        self.assertEqual(code, 0, output)
        receipt = json.loads(output)
        self.assertEqual(receipt, {
            "practice_set_id": "ps-002",
            "title": "Agent paper",
            "count": 2,
            "url": "/w/dmath/practice-sets",
        })
        saved = self.practice_sets.get_saved(self.pool, receipt["practice_set_id"])
        self.assertEqual(
            [item["problem_id"] for item in saved["plan"]["items"]],
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
        )
        self.assertEqual(saved["plan"]["request"], self.valid_plan()["request"])
        self.assertEqual(manifest.read_bytes(), source_before)
        self.assertEqual((self.fixture.ws / ".lessonkit" / "practice-sets" /
                          "ps-001.json").read_bytes(), papers_before["ps-001.json"])

        from workbench.server import app

        server = app.create_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}{receipt['url']}"
            with urllib.request.urlopen(url) as response:
                page = response.read().decode("utf-8")
            self.assertIn("Agent paper", page)
            self.assertIn("data-practice-set-id='ps-002'", page)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(self.fixture.db_path.read_bytes(), db_before)

    def test_invalid_manifests_exit_two_without_db_or_saved_file_changes(self):
        duplicate = self.valid_plan()
        duplicate["items"][1]["problem_id"] = duplicate["items"][0]["problem_id"]
        unknown = self.valid_plan()
        unknown["items"][0]["problem_id"] = "dmath-ch06-prob-999"
        wrong_course = self.valid_plan()
        wrong_course["course"] = "other-course"
        empty_items = self.valid_plan()
        empty_items["items"] = []
        empty_id = self.valid_plan()
        empty_id["items"][0]["problem_id"] = ""
        invalid_title = self.valid_plan()
        invalid_title["title"] = "  "
        invalid_request = self.valid_plan()
        invalid_request["request"] = ["not", "an", "object"]
        cases = [
            ("malformed", b"{"),
            ("unreadable", None),
            ("empty-items", empty_items),
            ("empty-id", empty_id),
            ("duplicate", duplicate),
            ("unknown", unknown),
            ("wrong-course", wrong_course),
            ("invalid-title", invalid_title),
            ("invalid-request", invalid_request),
        ]
        db_before = self.fixture.db_path.read_bytes()
        papers_before = self.saved_file_bytes()

        for name, plan in cases:
            with self.subTest(name=name):
                manifest = (Path(self.fixture.tmp.name) / f"{name}.json"
                            if plan is None else self.write_manifest(f"{name}.json", plan))
                source_before = manifest.read_bytes() if manifest.exists() else None
                code, output = self.run_cli("save", "--input", str(manifest))

                self.assertEqual(code, 2, output)
                self.assertIn("error", json.loads(output))
                if source_before is None:
                    self.assertFalse(manifest.exists())
                else:
                    self.assertEqual(manifest.read_bytes(), source_before)
                self.assertEqual(self.saved_file_bytes(), papers_before)
                self.assertEqual(self.fixture.db_path.read_bytes(), db_before)

    def test_absent_database_is_not_created_by_failed_save(self):
        from workbench.registry import register

        missing = Path(self.fixture.tmp.name) / "absent-workspace"
        (missing / "pool").mkdir(parents=True)
        (missing / "lessonkit.py").touch()
        register(str(missing), name="absent", db="pool/missing.db",
                 course="dmath", chapter="ch06")
        manifest = self.write_manifest("absent.json", self.valid_plan())
        db_path = missing / "pool" / "missing.db"

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                code = self.lesson_kit_main(
                    ["papers", "absent", "save", "--input", str(manifest)])
            except SystemExit as exc:
                code = exc.code

        self.assertEqual(code, 2, output.getvalue())
        self.assertIn("error", json.loads(output.getvalue()))
        self.assertFalse(db_path.exists())
        self.assertFalse((missing / ".lessonkit" / "practice-sets").exists())


if __name__ == "__main__":
    unittest.main()
