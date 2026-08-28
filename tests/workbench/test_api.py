"""HTTP API tests (TDD, red first)."""

import json
import sqlite3
import threading
import time
import unittest
import urllib.request
from urllib.error import HTTPError
from unittest import mock

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

    def test_feedback_endpoint(self):
        status, data = self.post("/api/w/dmath/feedback", {
            "item_type": "kp", "item_id": "dmath-ch06-kp-001", "rating": 2,
        })
        self.assertEqual(status, 200)
        self.assertGreater(len(data), 0)

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

    def test_ai_explain_without_provider_fails_gracefully(self):
        status, data = self.post("/api/w/dmath/ai/explain", {
            "problem_id": "dmath-ch06-prob-001",
        })
        self.assertEqual(status, 200)
        job_id = data["job_id"]
        self.assertTrue(job_id.startswith("job-"))
        state = None
        for _ in range(50):  # task runs on a worker thread now — let it settle
            try:
                _, data = self.get(f"/api/w/dmath/ai/jobs/{job_id}")
                state = data["state"]
            except HTTPError:
                pass  # job record may not be visible yet
            if state in ("done", "failed"):
                break
            time.sleep(0.05)
        self.assertEqual(state, "failed")

    @mock.patch("workbench.server.api.runner.run_ai_task")
    @mock.patch("workbench.server.api.runner.create_ai_task", return_value="job-042")
    def test_ai_explain_returns_the_reserved_job_id(self, create_task, run_task):
        status, data = self.post("/api/w/dmath/ai/explain", {
            "problem_id": "dmath-ch06-prob-001",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["job_id"], "job-042")
        create_task.assert_called_once()
        deadline = time.time() + 1
        while not run_task.called and time.time() < deadline:
            time.sleep(0.01)
        self.assertEqual(run_task.call_args.kwargs["job_id"], "job-042")

    def test_ai_explain_unknown_problem_404(self):
        with self.assertRaises(HTTPError) as ctx:
            self.post("/api/w/dmath/ai/explain", {
                "problem_id": "dmath-ch06-prob-999",
            })
        self.assertEqual(ctx.exception.code, 404)

    def test_hub_page(self):
        status, html = self.get_html("/")
        self.assertIn("dmath", html)

    def test_workspace_page(self):
        status, html = self.get_html("/w/dmath/")
        self.assertIn("弱项", html)

    def test_neutral_knowledge_points_are_not_labeled_as_weak(self):
        from workbench.server.pages import _left_column
        html = _left_column(
            {"name": "dmath"}, [{"name": "dmath"}],
            [{"kp_id": "kp-1", "knowledge_item": "中性知识点", "score": 0.2, "reasons": []}],
            "practice",
        )
        self.assertIn("本章知识点", html)
        self.assertNotIn("优先回看", html)


if __name__ == "__main__":
    unittest.main()
