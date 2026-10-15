import http.client
import json
import threading
import unittest

from workbench.server.app import create_server


class RetiredManualProblemIncludeTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post_pull(self, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        raw = json.dumps(payload).encode("utf-8")
        connection.request(
            "POST",
            "/api/w/missing/pull",
            body=raw,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw)),
            },
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, body

    def test_include_ids_is_rejected_as_retired_browser_behavior(self):
        status, body = self.post_pull({
            "kp_ids": ["kp-1"],
            "include_ids": ["problem-1"],
        })

        self.assertEqual(status, 400)
        self.assertIn("include_ids is retired", body["error"])
        self.assertIn("compose a paper", body["error"])

    def test_plain_pull_still_reaches_normal_route(self):
        status, body = self.post_pull({"kp_ids": ["kp-1"]})

        self.assertEqual(status, 404)
        self.assertIn("unknown workspace", body["error"])


class RetiredManualPickerStaticTests(unittest.TestCase):
    def test_browser_bundle_has_no_manual_problem_picker_or_include_state(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        flow = (root / "workbench/server/static/practice-flow.js").read_text(encoding="utf-8")
        workbench = (root / "workbench/server/static/workbench.js").read_text(encoding="utf-8")

        for retired in (
            "wb_practice_include_", "include_ids", "filterState.picked",
            "picked_problem_ids", "data-picked-id", "搜索选题",
        ):
            self.assertNotIn(retired, flow)
        self.assertNotIn("wb_practice_include_", workbench)


if __name__ == "__main__":
    unittest.main()
