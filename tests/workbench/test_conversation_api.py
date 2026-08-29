"""Internal HTTP API for provider-native conversations."""

import json
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from urllib.error import HTTPError
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


FAKE_TURN = r'''import json, sys
prompt = sys.stdin.read()
print(json.dumps({"type":"thread.started","thread_id":"api-native"}), flush=True)
print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"API answer"}}), flush=True)
print(json.dumps({"type":"turn.completed"}), flush=True)
'''


class ConversationApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server import app

        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.script = Path(self.fixture.tmp.name) / "api_turn.py"
        self.script.write_text(FAKE_TURN, encoding="utf-8")
        self.provider = {
            "name": "codex", "command": sys.executable, "args": [],
            "model": None, "timeout_s": 3,
        }

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def post(self, path, payload):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def patch(self, path, payload):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def delete(self, path):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", method="DELETE"
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_task_providers_reflect_the_bridge_registry(self):
        status, info = self.get("/api/w/dmath/ai/task-providers")
        self.assertEqual(status, 200)
        self.assertEqual(info, {"available": False, "count": 0})
        from workbench import registry
        registry.add_bridge("codex", sys.executable)
        status, info = self.get("/api/w/dmath/ai/task-providers")
        self.assertEqual(info, {"available": True, "count": 1})

    @mock.patch("workbench.bridge.conversation_providers.discover")
    def test_provider_and_session_endpoints(self, discover):
        discover.return_value = [self.provider]
        status, providers = self.get("/api/w/dmath/ai/providers")
        self.assertEqual(status, 200)
        self.assertEqual(providers, [{"name": "codex", "model": None}])

        with mock.patch("workbench.bridge.conversation_providers.get", return_value=self.provider):
            status, created = self.post("/api/w/dmath/ai/sessions", {"provider": "codex"})
            self.assertEqual(status, 200)
            status, sessions = self.get("/api/w/dmath/ai/sessions")
            self.assertEqual(sessions[0]["conversation_id"], created["conversation_id"])
            status, restored = self.get(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}"
            )
            self.assertEqual(restored["provider"], "codex")
            self.assertEqual(restored["messages"], [])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_session_list_is_unbounded_and_supports_rename_and_delete(self, get_provider):
        get_provider.return_value = self.provider
        created = []
        for _ in range(11):
            _, conversation = self.post("/api/w/dmath/ai/sessions", {"provider": "codex"})
            created.append(conversation)

        _, sessions = self.get("/api/w/dmath/ai/sessions")
        self.assertEqual(len(sessions), 11)
        self.assertTrue(all("title" in item and "title_source" in item for item in sessions))

        conversation_id = created[0]["conversation_id"]
        _, renamed = self.patch(
            f"/api/w/dmath/ai/sessions/{conversation_id}",
            {"title": "我的复习对话"},
        )
        self.assertEqual(renamed["title"], "我的复习对话")
        self.assertEqual(renamed["title_source"], "user")
        status, deleted = self.delete(f"/api/w/dmath/ai/sessions/{conversation_id}")
        self.assertEqual(status, 200)
        self.assertEqual(deleted["conversation_id"], conversation_id)
        _, sessions = self.get("/api/w/dmath/ai/sessions")
        self.assertNotIn(conversation_id, {item["conversation_id"] for item in sessions})

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_turn_endpoint_rebuilds_context_and_returns_events(self, get_provider):
        from workbench.bridge import conversation_providers

        get_provider.return_value = self.provider
        with mock.patch.object(
            conversation_providers, "build_command",
            return_value=[sys.executable, str(self.script)],
        ):
            _, created = self.post("/api/w/dmath/ai/sessions", {"provider": "codex"})
            _, turn = self.post(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}/turns",
                {
                    "message": "Explain the current concept",
                    "route": "/w/dmath/kp/dmath-ch06-kp-001",
                    "page_type": "kp",
                    "kp_id": "dmath-ch06-kp-001",
                    "dom": "must not be forwarded",
                },
            )
            data = None
            for _ in range(100):
                _, data = self.get(
                    f"/api/w/dmath/ai/sessions/{created['conversation_id']}"
                    f"/turns/{turn['turn_id']}?after=0"
                )
                if data["turn"]["status"] not in {"queued", "running"}:
                    break
                time.sleep(0.02)

        self.assertEqual(data["turn"]["status"], "done")
        self.assertEqual([event["sequence"] for event in data["events"]], list(range(1, len(data["events"]) + 1)))
        _, restored = self.get(f"/api/w/dmath/ai/sessions/{created['conversation_id']}")
        self.assertEqual(restored["messages"][-1]["content"], "API answer")
        transcript = self.fixture.ws / ".lessonkit" / "jobs" / created["conversation_id"] / "transcript.jsonl"
        exchange = json.loads(transcript.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(exchange["context_anchor"]["kp_id"], "dmath-ch06-kp-001")
        self.assertNotIn("dom", str(exchange))


if __name__ == "__main__":
    unittest.main()
