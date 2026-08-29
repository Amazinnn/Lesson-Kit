"""HTTP API tests (TDD, red first)."""

import json
import sqlite3
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

from tests.workbench.fixtures import WorkspaceFixture


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        sys_path_setup = self  # keep import local inside fixture
        from workbench.server import app
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def post(self, path, payload):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def post_error(self, path, payload):
        with self.assertRaises(HTTPError) as ctx:
            self.post(path, payload)
        return ctx.exception.code, json.loads(ctx.exception.read().decode("utf-8"))

    def get_html(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, resp.read().decode("utf-8")

    def test_hub_workspaces(self):
        status, data = self.get("/api/hub/workspaces")
        self.assertEqual(status, 200)
        self.assertEqual(data[0]["name"], "dmath")

    def test_weak_endpoint(self):
        status, data = self.get("/api/w/dmath/weak")
        self.assertEqual(status, 200)
        self.assertEqual(data[0]["kp_id"], "dmath-ch06-kp-001")

    def test_pull_endpoint(self):
        status, data = self.post("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "weak",
        })
        self.assertEqual(status, 200)
        self.assertEqual(
            [p["problem_id"] for p in data["problems"]],
            ["dmath-ch06-prob-001"],
        )
        self.assertEqual(data["shortage"], ["dmath-ch06-kp-001"])

    def test_practice_endpoint(self):
        status, data = self.post("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-001", "result": "wrong",
            "answer_text": "my answer",
        })
        self.assertEqual(status, 200)
        self.assertIn("due_at", data)

    def test_practice_correct_records_reviewing_attempt(self):
        status, data = self.post("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-001", "result": "correct",
        })
        self.assertEqual(status, 200)
        self.assertIn("due_at", data)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            attempts = conn.execute(
                "SELECT status FROM problem_attempts WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchall()
            progress = conn.execute(
                "SELECT status FROM problem_progress WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual([row[0] for row in attempts], ["reviewing"])
        self.assertEqual(progress[0], "reviewing")

    def test_practice_skip_records_nothing(self):
        status, data = self.post("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-001", "result": "skip",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["recorded"], False)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            attempts = conn.execute(
                "SELECT COUNT(*) FROM problem_attempts"
            ).fetchone()[0]
            progress = conn.execute(
                "SELECT COUNT(*) FROM problem_progress"
            ).fetchone()[0]
            schedule = conn.execute(
                "SELECT COUNT(*) FROM review_schedule"
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(attempts, 0)
        self.assertEqual(progress, 0)
        self.assertEqual(schedule, 0)

    def test_practice_rejects_unknown_problem_without_writing(self):
        status, data = self.post_error("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-999", "result": "wrong",
        })
        self.assertEqual(status, 404)
        self.assertIn("unknown problem", data["error"])
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM problem_attempts").fetchone()[0], 0)
        finally:
            conn.close()

    def test_practice_rejects_invalid_result_without_writing(self):
        status, _ = self.post_error("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-001", "result": "perfect",
        })
        self.assertEqual(status, 400)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM problem_attempts").fetchone()[0], 0)
        finally:
            conn.close()

    def test_feedback_endpoint(self):
        status, data = self.post("/api/w/dmath/feedback", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-001", "rating": 2,
        })
        self.assertEqual(status, 200)
        self.assertGreater(len(data), 0)

    def test_feedback_rejects_unknown_item_and_invalid_rating(self):
        status, _ = self.post_error("/api/w/dmath/feedback", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-999", "rating": 2,
        })
        self.assertEqual(status, 404)
        status, _ = self.post_error("/api/w/dmath/feedback", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-001", "rating": 7,
        })
        self.assertEqual(status, 400)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0], 0)
        finally:
            conn.close()

    def test_pull_rejects_empty_unknown_and_malformed_scope(self):
        for payload, expected in (
            ({"kp_ids": [], "n": 1, "mode": "exam"}, 400),
            ({"kp_ids": ["dmath-ch06-kp-999"], "n": 1, "mode": "exam"}, 404),
            ({"kp_ids": ["dmath-ch06-kp-001"], "n": 0, "mode": "exam"}, 400),
            ({"kp_ids": ["dmath-ch06-kp-001"], "n": 1, "mode": "mystery"}, 400),
        ):
            status, _ = self.post_error("/api/w/dmath/pull", payload)
            self.assertEqual(status, expected)

    def test_learning_write_endpoints_require_json_objects(self):
        for path in ("/practice", "/feedback", "/pull"):
            status, _ = self.post_error(f"/api/w/dmath{path}", [])
            self.assertEqual(status, 400)

    def test_problem_detail_endpoint(self):
        status, data = self.get("/api/w/dmath/problem/dmath-ch06-prob-001")
        self.assertEqual(status, 200)
        self.assertEqual(data["problem"]["problem_id"], "dmath-ch06-prob-001")

    def test_kp_detail_endpoint(self):
        status, data = self.get("/api/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertEqual(data["kp"]["kp_id"], "dmath-ch06-kp-001")

    def test_graph_model_reads_live_workspace_data(self):
        status, data = self.get("/api/w/dmath/graph/model")
        self.assertEqual(status, 200)
        self.assertEqual(data["nodes"][0]["id"], "dmath-ch06-kp-001")
        self.assertEqual(data["nodes"][0]["title"], "Counting")
        self.assertIsNone(data["nodes"][0]["state"])

    def test_graph_state_overwrites_without_feedback_history(self):
        status, data = self.post("/api/w/dmath/graph/state", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-001",
            "state": "mastered",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["state"], "mastered")
        _, graph = self.get("/api/w/dmath/graph/model")
        self.assertEqual(graph["nodes"][0]["state"], "mastered")
        _, detail = self.get("/api/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(detail["schedule"]["last_rating"], 5)
        self.assertEqual(detail["signals"], [])

    def test_graph_kp_save_overwrites_content_without_learning_events(self):
        try:
            status, data = self.post("/api/w/dmath/graph/kp", {
                "kp_id": "dmath-ch06-kp-001", "body": "新的正文", "fragile": "易混概念",
            })
        except HTTPError as exc:
            self.fail(f"graph content save endpoint missing: {exc.code}")
        self.assertEqual(status, 200)
        self.assertEqual(data["body"], "新的正文")
        _, graph = self.get("/api/w/dmath/graph/model")
        self.assertEqual(graph["nodes"][0]["body"], "新的正文")
        self.assertEqual(graph["nodes"][0]["fragile"], "易混概念")
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM learner_signals").fetchone()[0], 0)
        finally:
            conn.close()

    def test_kp_detail_exposes_related_problem_current_state(self):
        self.post("/api/w/dmath/graph/state", {
            "item_type": "problem", "item_id": "dmath-ch06-prob-001", "state": "review",
        })
        _, detail = self.get("/api/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(detail["problems"][0]["current_state"]["state"], "review")

    def test_figure_missing_returns_404(self):
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}"
                "/api/w/dmath/figures/dmath/ch06/nope.png"
            )
        self.assertEqual(ctx.exception.code, 404)

    def test_figure_served(self):
        figure_dir = self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06"
        figure_dir.mkdir(parents=True)
        (figure_dir / "dmath-ch06-kp-001-fig-001.png").write_bytes(b"\x89PNG")
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}"
            "/api/w/dmath/figures/dmath/ch06/dmath-ch06-kp-001-fig-001.png"
        ) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b"\x89PNG")

    def test_hub_page(self):
        status, html = self.get_html("/")
        self.assertIn("dmath", html)

    def test_workspace_page(self):
        status, html = self.get_html("/w/dmath/")
        self.assertIn("准备练习", html)

    def test_neutral_knowledge_points_are_not_labeled_as_weak(self):
        from workbench.server.pages import _left_column
        html = _left_column(
            {"name": "dmath"}, [{"name": "dmath"}],
            [{"kp_id": "kp-1", "knowledge_item": "中性知识点", "score": 0.2, "reasons": []}],
            "practice",
        )
        self.assertIn("本章知识点", html)
        self.assertNotIn("优先回看", html)


    def _seed_schedule(self, item_type, item_id, due_iso, direction=""):
        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO review_schedule (item_type, item_id, direction,"
            " state, repetitions, ease, interval_days, due_at, last_rating,"
            " last_reviewed_at) VALUES (?, ?, ?, 'review', 1, 2.5, 2, ?, 3, ?)",
            (item_type, item_id, direction, due_iso, due_iso),
        )
        conn.commit()
        conn.close()

    def test_due_includes_direction_and_limit(self):
        import datetime
        today = datetime.date.today().isoformat()
        self._seed_schedule("kp", "dmath-ch06-kp-001", today)
        self._seed_schedule("kp", "dmath-ch06-kp-001", today, direction="reverse")
        status, data = self.get("/api/w/dmath/due")
        self.assertEqual(status, 200)
        directions = {(i["item_id"], i["direction"]) for i in data}
        self.assertIn(("dmath-ch06-kp-001", "reverse"), directions)
        status, data = self.get("/api/w/dmath/due?limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 1)

    def test_pull_include_ids_restricts_scope(self):
        status, data = self.post("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "weak",
            "include_ids": ["dmath-ch06-prob-001"],
        })
        self.assertEqual(status, 200)
        self.assertEqual(
            [p["problem_id"] for p in data["problems"]], ["dmath-ch06-prob-001"])

    def test_pull_include_ids_with_all_mode_rejected(self):
        status, data = self.post_error("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 5, "mode": "all",
            "include_ids": ["dmath-ch06-prob-001"],
        })
        self.assertEqual(status, 400)

    def test_feedback_direction_targets_schedule_row(self):
        import datetime
        today = datetime.date.today().isoformat()
        self._seed_schedule("kp", "dmath-ch06-kp-001", today)
        self._seed_schedule("kp", "dmath-ch06-kp-001", today, direction="reverse")
        status, _ = self.post("/api/w/dmath/feedback", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-001",
            "rating": 5, "direction": "reverse",
        })
        self.assertEqual(status, 200)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            rows = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT direction, due_at FROM review_schedule"
                    " WHERE item_type='kp' AND item_id='dmath-ch06-kp-001'"
                )
            }
        finally:
            conn.close()
        self.assertEqual(rows[""], today)
        self.assertNotEqual(rows["reverse"], today)


    def test_calendar_view_buckets_days_and_goals(self):
        import datetime
        from pathlib import Path
        today = datetime.date.today()
        self._seed_schedule("kp", "dmath-ch06-kp-001", today.isoformat())
        self._seed_schedule("kp", "dmath-ch06-kp-001",
                            (today + datetime.timedelta(days=3)).isoformat(),
                            direction="reverse")
        self._seed_schedule("kp", "dmath-ch06-kp-002",
                            (today - datetime.timedelta(days=1)).isoformat())
        goals_path = Path(self.fixture.ws) / ".lessonkit" / "goals.json"
        goals_path.parent.mkdir(parents=True, exist_ok=True)
        goals_path.write_text(json.dumps([
            {"id": "goal-001", "kind": "stage", "title": "G1",
             "deadline": (today + datetime.timedelta(days=5)).isoformat()},
        ]), encoding="utf-8")
        status, data = self.get("/api/w/dmath/calendar")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["days"]), 14)
        by_date = {day["date"]: day for day in data["days"]}
        self.assertEqual(by_date[today.isoformat()]["count"], 1)
        self.assertEqual(by_date[today.isoformat()]["overdue"], 1)
        self.assertEqual(
            by_date[(today + datetime.timedelta(days=3)).isoformat()]["count"], 1)
        self.assertEqual(data["goals"][0]["title"], "G1")


if __name__ == "__main__":
    unittest.main()
