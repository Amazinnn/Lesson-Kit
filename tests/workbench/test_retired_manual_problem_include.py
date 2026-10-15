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


if __name__ == "__main__":
    unittest.main()
