"""UI shell route tests (TDD, red first)."""

import json
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

from tests.workbench.fixtures import WorkspaceFixture


class UiRouteTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server import app
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def fetch(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, resp.read().decode("utf-8")

    def test_static_asset_served(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn("column", body)

    def test_static_path_traversal_blocked(self):
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/static/../pool/dmath.db"
            )
        self.assertEqual(ctx.exception.code, 404)

    def test_practice_page_renders_shell(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("left-column", body)
        self.assertIn("ai-column", body)

    def test_kp_page_renders(self):
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertIn("dmath-ch06-kp-001", body)

    def test_session_end_page_renders(self):
        status, body = self.fetch("/w/dmath/session-end")
        self.assertEqual(status, 200)
        self.assertIn("rating", body)

    def test_explain_result_endpoint(self):
        explain_dir = (self.fixture.ws / ".lessonkit" / "explain"
                       / "dmath" / "ch06")
        explain_dir.mkdir(parents=True)
        (explain_dir / "dmath-ch06-prob-001.md").write_text(
            "# Explain\n\n## 结论\n\nok\n", encoding="utf-8"
        )
        status, data = self.fetch_json(
            "/api/w/dmath/explain/dmath-ch06-prob-001"
        )
        self.assertEqual(status, 200)
        self.assertIn("## 结论", data["markdown"])

    def test_explain_result_missing_404(self):
        from urllib.error import HTTPError
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}"
                "/api/w/dmath/explain/dmath-ch06-prob-999"
            )
        self.assertEqual(ctx.exception.code, 404)

    def fetch_json(self, path):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}{path}"
        ) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
