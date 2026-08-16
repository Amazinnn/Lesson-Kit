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

    def fetch_json(self, path):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}{path}"
        ) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_static_asset_served(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn("--dsw-brand-primary", body)

    def test_css_defines_hidden_rule(self):
        # regression: .hidden was missing, breaking the practice visibility choreography
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn(".hidden { display: none !important; }", body)

    def test_practice_page_session_end_entry_always_visible(self):
        # regression: the session-end entry was inside #composer and became
        # unreachable; it must live outside and stay visible
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("<div id='session-end-entry'>", body)
        self.assertIn("<button id='goto-session-end' class='outline'>", body)
        self.assertNotIn("class='outline hidden'", body)

    def test_graph_page_iframe_points_to_artifact_route(self):
        graph = (self.fixture.ws / "output" / "dmath" / "ch06"
                 / "ch06-graph.html")
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><body>graph</body></html>", encoding="utf-8")
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("/api/w/dmath/graph/artifact", body)
        self.assertNotIn("src='/api/w/dmath/graph'", body)

    def test_graph_artifact_route_serves_raw_html(self):
        graph = (self.fixture.ws / "output" / "dmath" / "ch06"
                 / "ch06-graph.html")
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><body>graph-artifact</body></html>",
                         encoding="utf-8")
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/api/w/dmath/graph/artifact"
        ) as resp:
            body = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "text/html")
        self.assertIn("graph-artifact", body)

    def test_graph_artifact_missing_404(self):
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/api/w/dmath/graph/artifact"
            )
        self.assertEqual(ctx.exception.code, 404)

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
        self.assertIn("topbar", body)
        self.assertIn("<a class='brand' href='/'>lesson-kit</a>", body)
        self.assertIn("ai-collapse", body)

    def test_hub_page_chinese(self):
        status, body = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("<h1>工作台</h1>", body)

    def test_kp_page_has_no_dead_script(self):
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertNotIn("wbKpId", body)

    def test_left_nav_has_three_entries(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn(">练习<", body)
        self.assertIn(">知识点<", body)
        self.assertIn(">知识图谱<", body)

    def test_kps_page_lists_knowledge_points(self):
        status, body = self.fetch("/w/dmath/kps")
        self.assertEqual(status, 200)
        self.assertIn("dmath-ch06-kp-001", body)

    def test_kp_page_renders(self):
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertIn("dmath-ch06-kp-001", body)

    def test_session_end_page_renders(self):
        status, body = self.fetch("/w/dmath/session-end")
        self.assertEqual(status, 200)
        self.assertIn("rating", body)

    def test_graph_page_with_artifact(self):
        graph = (self.fixture.ws / "output" / "dmath" / "ch06"
                 / "ch06-graph.html")
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><body>graph</body></html>", encoding="utf-8")
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("iframe", body)
        status, data = self.fetch_json("/api/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("graph", data["html"])

    def test_graph_page_without_artifact_shows_hint(self):
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("render-graph-html.py", body)
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/api/w/dmath/graph"
            )
        self.assertEqual(ctx.exception.code, 404)

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
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}"
                "/api/w/dmath/explain/dmath-ch06-prob-999"
            )
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
