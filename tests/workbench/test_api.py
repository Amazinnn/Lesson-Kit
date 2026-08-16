"""HTTP API tests (TDD, red first)."""

import json
import threading
import time
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


if __name__ == "__main__":
    unittest.main()
