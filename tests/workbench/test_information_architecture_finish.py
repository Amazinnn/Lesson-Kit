"""Red tests for the final information architecture contract."""

import json
import threading
import unittest
import urllib.request

from tests.workbench.fixtures import WorkspaceFixture


class InformationArchitectureFinishTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server import app
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def fetch(self, path):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.server.server_address[1]}{path}"
        ) as response:
            return response.read().decode("utf-8")

    def test_agent_column_starts_as_history_list_without_daily_console(self):
        body = self.fetch("/w/dmath/kps")
        self.assertIn("ai-session-list", body)
        self.assertIn("ai-new-session", body)
        self.assertNotIn("id='ai-daily'", body)
        self.assertNotIn("id='ai-provider'", body)
        self.assertNotIn("id='ai-session'", body)

    def test_graph_detail_is_dashboard_not_duplicate_editor(self):
        body = self.fetch("/w/dmath/graph")
        self.assertIn("学习看板", body)
        self.assertIn("打开知识点", body)
        self.assertNotIn("id='graph-body'", body)
        self.assertNotIn("id='graph-fragile'", body)
        self.assertNotIn("graph-problem-save", body)

    def test_markdown_contract_is_present_in_client(self):
        body = self.fetch("/static/workbench.js")
        self.assertIn("<h2>", body)
        self.assertIn("<blockquote>", body)
        self.assertIn("<pre>", body)


if __name__ == "__main__":
    unittest.main()
