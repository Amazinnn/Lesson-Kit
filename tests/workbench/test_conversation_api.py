"""Internal HTTP API for provider-native conversations."""

import json
import sqlite3
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


FAKE_PI_TURN = r'''import json, sys
prompt = sys.stdin.read()
print(json.dumps({"type":"session","version":3,"id":"pi-native-1","cwd":"."}), flush=True)
print(json.dumps({"type":"agent_start"}), flush=True)
print(json.dumps({"type":"turn_start"}), flush=True)
print(json.dumps({"type":"message_update","assistantMessageEvent":{"type":"text_delta","contentIndex":0,"delta":"Pi 的"}}), flush=True)
print(json.dumps({"type":"message_update","assistantMessageEvent":{"type":"text_delta","contentIndex":0,"delta":"回答"}}), flush=True)
print(json.dumps({"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"Pi 的回答"}],"stopReason":"stop"}}), flush=True)
print(json.dumps({"type":"agent_end","messages":[{"role":"assistant","content":[{"type":"text","text":"Pi 的回答"}]}]}), flush=True)
print(json.dumps({"type":"agent_settled"}), flush=True)
'''


FAKE_PI_ERROR_TURN = r'''import json, sys
prompt = sys.stdin.read()
print(json.dumps({"type":"session","version":3,"id":"pi-native-2","cwd":"."}), flush=True)
print(json.dumps({"type":"message_end","message":{"role":"assistant","content":[],"stopReason":"error","errorMessage":"401 invalid api key"}}), flush=True)
print(json.dumps({"type":"agent_end","messages":[],"willRetry":False}), flush=True)
'''


SLOW_TURN = r'''import json, sys, time
prompt = sys.stdin.read()
time.sleep(1.2)
print(json.dumps({"type":"thread.started","thread_id":"api-slow"}), flush=True)
print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"慢回答"}}), flush=True)
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

    def get_error(self, path):
        with self.assertRaises(HTTPError) as ctx:
            self.get(path)
        return ctx.exception.code, json.loads(ctx.exception.read().decode("utf-8"))

    def post(self, path, payload):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def post_error(self, path, payload):
        with self.assertRaises(HTTPError) as ctx:
            self.post(path, payload)
        return ctx.exception.code, json.loads(ctx.exception.read().decode("utf-8"))

    def patch_error(self, path, payload):
        with self.assertRaises(HTTPError) as ctx:
            self.patch(path, payload)
        return ctx.exception.code, json.loads(ctx.exception.read().decode("utf-8"))

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

    @mock.patch("workbench.bridge.conversation_providers.discover")
    def test_provider_and_session_endpoints(self, discover):
        discover.return_value = [self.provider]
        with mock.patch(
                "workbench.bridge.conversation_providers.list_models",
                return_value=[{
                    **self.provider, "name": "codex 默认", "provider": "codex",
                    "model": None, "entry": None, "source": "default",
                }]):
            status, providers = self.get("/api/w/dmath/ai/providers")
        self.assertEqual(status, 200)
        self.assertEqual(providers, [{
            "name": "codex 默认", "provider": "codex", "model": None,
            "entry": None, "source": "default",
        }])

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

        status, error = self.get_error(
            f"/api/w/dmath/ai/sessions/{created['conversation_id']}"
            f"/turns/{turn['turn_id']}?after=invalid"
        )
        self.assertEqual(status, 400)
        self.assertEqual(error["error"], "after must be an integer")

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_pi_turn_streams_deltas_and_keeps_its_native_session(self, get_provider):
        # Pi answers over its persistent RPC process; the mirror keeps the
        # streamed answer and the native session for resuming.
        from workbench.bridge import conversation_providers, conversations, pi_rpc
        from tests.workbench.test_pi_rpc import FakePiLauncher

        provider = {"name": "pi", "command": sys.executable, "args": [],
                    "model": "minimax/MiniMax-M2.7", "timeout_s": 5}
        get_provider.return_value = provider
        launcher = FakePiLauncher("normal", Path(self.fixture.tmp.name) / "pi.log")
        registry = pi_rpc.PiRpcRegistry(idle_seconds=1800)
        with mock.patch.object(conversation_providers, "build_command", launcher),                 mock.patch.object(conversations, "PI_RPC", registry):
            _, created = self.post("/api/w/dmath/ai/sessions", {"provider": "pi"})
            data = self.run_turn(created["conversation_id"], "解释一下当前知识点")
            registry.close_all()

        self.assertEqual(data["turn"]["status"], "done")
        _, restored = self.get(f"/api/w/dmath/ai/sessions/{created['conversation_id']}")
        self.assertEqual(restored["provider"], "pi")
        self.assertEqual(restored["provider_session_id"], "pi-rpc-session-1")
        self.assertEqual(restored["messages"][-1]["content"], "第 1 轮回答")
        self.assertEqual(launcher.modes, ["rpc"])

    @mock.patch("workbench.bridge.conversation_providers.get")
    def test_pi_stream_error_fails_the_turn_even_though_the_process_succeeds(self, get_provider):
        # A provider-side error arrives in the message stream, not as an exit code.
        from workbench.bridge import conversation_providers, conversations, pi_rpc
        from tests.workbench.test_pi_rpc import FakePiLauncher

        provider = {"name": "pi", "command": sys.executable, "args": [],
                    "model": None, "timeout_s": 5}
        get_provider.return_value = provider
        launcher = FakePiLauncher("error", Path(self.fixture.tmp.name) / "pi.log")
        registry = pi_rpc.PiRpcRegistry(idle_seconds=1800)
        with mock.patch.object(conversation_providers, "build_command", launcher),                 mock.patch.object(conversations, "PI_RPC", registry):
            _, created = self.post("/api/w/dmath/ai/sessions", {"provider": "pi"})
            data = self.run_turn(created["conversation_id"], "解释一下当前知识点")
            registry.close_all()

        self.assertEqual(data["turn"]["status"], "failed")
        self.assertIn("401 invalid api key", data["turn"]["error"])

    def run_turn(self, conversation_id, message):
        _, turn = self.post(
            f"/api/w/dmath/ai/sessions/{conversation_id}/turns",
            {"message": message, "route": "/w/dmath/kp/dmath-ch06-kp-001",
             "page_type": "kp", "kp_id": "dmath-ch06-kp-001"},
        )
        data = None
        for _ in range(100):
            _, data = self.get(
                f"/api/w/dmath/ai/sessions/{conversation_id}/turns/{turn['turn_id']}?after=0"
            )
            if data["turn"]["status"] not in {"queued", "running"}:
                break
            time.sleep(0.02)
        return data

    def test_ingest_rollback_endpoint_returns_result(self):
        result = {
            "ok": True,
            "batch_id": "batch-001",
            "deleted": {"flash_cards": 2},
            "backup_path": "pool/backups/batch-001-rollback.sqlite",
            "accounting": {"flash_cards": 2},
        }
        from workbench.server import api

        with mock.patch.object(
            api.ingest, "rollback_batch", create=True, return_value=result
        ) as rollback_batch:
            status, payload = self.post(
                "/api/w/dmath/ingest/rollback", {"batch_id": "batch-001"}
            )

        self.assertEqual(status, 200)
        self.assertEqual(payload, result)
        self.assertEqual(rollback_batch.call_args.args[1], "batch-001")

    def test_ingest_rollback_endpoint_requires_batch_id(self):
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/w/dmath/ingest/rollback", {})

        self.assertEqual(caught.exception.code, 400)

    def test_ingest_rollback_endpoint_reports_value_error(self):
        from workbench.server import api

        with mock.patch.object(
            api.ingest, "rollback_batch", create=True,
            side_effect=ValueError("unknown ingest batch: batch-999"),
        ):
            with self.assertRaises(HTTPError) as caught:
                self.post(
                    "/api/w/dmath/ingest/rollback", {"batch_id": "batch-999"}
                )

        self.assertEqual(caught.exception.code, 400)
        self.assertEqual(
            json.loads(caught.exception.read().decode("utf-8"))["error"],
            "unknown ingest batch: batch-999",
        )

    # -- records, attempts, filters, and the model switch -----------------

    def seed_evidence(self):
        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "UPDATE problems SET exam_year='2023-2024秋冬', source_evidence=? "
            "WHERE problem_id='dmath-ch06-prob-001'",
            ("题库/midterm·合集A.md 第1题",),
        )
        conn.commit()
        conn.close()

    def test_a_browser_attempt_and_its_rating_form_one_record(self):
        status, submitted = self.post("/api/w/dmath/attempts", {
            "problem_id": "dmath-ch06-prob-001",
            "answer_text": "P1 的作答", "verdict": False, "choices": ["甲"],
        })
        self.assertEqual(status, 200)
        self.assertTrue(submitted["recorded"])

        status, rated = self.post("/api/w/dmath/feedback", {
            "item_type": "problem", "item_id": "dmath-ch06-prob-001",
            "rating": 2, "attempt_id": submitted["attempt_id"],
        })
        self.assertEqual(status, 200)

        status, records = self.get("/api/w/dmath/records")
        self.assertEqual(status, 200)
        self.assertEqual(records["count"], 1)
        row = records["records"][0]
        self.assertEqual(row["verdict"], 0)
        self.assertEqual(row["rating"], 2)
        self.assertEqual(row["choices"], ["甲"])

    def test_an_attempt_for_an_unknown_problem_is_a_client_error(self):
        status, _ = self.post_error("/api/w/dmath/attempts", {
            "problem_id": "dmath-ch06-prob-999", "answer_text": "x",
        })
        self.assertEqual(status, 400)
        status, records = self.get("/api/w/dmath/records")
        self.assertEqual(records["count"], 0)

    def test_browser_write_retries_return_original_result_and_conflict_on_change(self):
        answer = {"request_id": "web-answer-1", "problem_id": "dmath-ch06-prob-001",
                  "answer_text": "原作答", "verdict": False}
        status, first = self.post("/api/w/dmath/attempts", answer)
        self.assertEqual(status, 200)
        status, replay = self.post("/api/w/dmath/attempts", answer)
        self.assertEqual((status, replay), (200, first))
        status, _ = self.post_error("/api/w/dmath/attempts", {
            **answer, "answer_text": "改过的作答"})
        self.assertEqual(status, 409)

        feedback = {"request_id": "web-rating-1", "item_type": "problem",
                    "item_id": answer["problem_id"], "rating": 2,
                    "attempt_id": first["attempt_id"]}
        status, rated = self.post("/api/w/dmath/feedback", feedback)
        self.assertEqual(status, 200)
        status, again = self.post("/api/w/dmath/feedback", feedback)
        self.assertEqual((status, again), (200, rated))
        status, _ = self.post_error("/api/w/dmath/feedback", {**feedback, "rating": 4})
        self.assertEqual(status, 409)
        status, _ = self.post_error("/api/w/dmath/feedback", {
            **feedback, "request_id": answer["request_id"]})
        self.assertEqual(status, 409)
        status, records = self.get("/api/w/dmath/records")
        self.assertEqual((status, records["count"]), (200, 1))
        self.assertEqual(records["records"][0]["rating"], 2)

    def test_the_filter_facets_and_the_search_feed(self):
        self.seed_evidence()
        status, facets = self.get("/api/w/dmath/pull-facets")
        self.assertEqual(status, 200)
        kinds = {item["value"]: item["count"] for item in facets["source_kinds"]}
        self.assertEqual(kinds, {"textbook": 1})
        docs = [item["value"] for item in facets["docs"]]
        self.assertEqual(docs, ["题库/midterm·合集A.md"])

        from urllib.parse import quote
        status, found = self.get("/api/w/dmath/search/problems?q=" + quote("合集a"))
        self.assertEqual(status, 200)
        self.assertEqual([item["problem_id"] for item in found["problems"]],
                         ["dmath-ch06-prob-001"])

    def test_the_pull_api_applies_filter_dimensions_and_exam_year(self):
        self.seed_evidence()
        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "UPDATE problems SET exam_year='2019-2020秋冬', "
            "source_evidence='题库/final·合集B.md 第2题' "
            "WHERE problem_id='dmath-ch06-prob-001'")
        conn.commit()
        conn.close()

        status, result = self.post("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 10, "mode": "all",
            "exam_year": "2023",
        })
        self.assertEqual(status, 200)
        self.assertEqual(result["problems"], [])

        status, result = self.post("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001"], "n": 10, "mode": "all",
            "filters": {"docs": ["合集b"]},
        })
        self.assertEqual(status, 200)
        self.assertEqual([item["problem_id"] for item in result["problems"]],
                         ["dmath-ch06-prob-001"])

    def test_a_running_turn_refuses_a_model_switch(self):
        from workbench.bridge import conversation_providers

        slow = Path(self.fixture.tmp.name) / "slow_turn.py"
        slow.write_text(SLOW_TURN, encoding="utf-8")
        with mock.patch("workbench.bridge.conversation_providers.get",
                        return_value=self.provider), mock.patch.object(
                conversation_providers, "build_command",
                return_value=[sys.executable, str(slow)]):
            _, created = self.post("/api/w/dmath/ai/sessions",
                                   {"provider": "codex", "model": "gpt-test-9"})
            conversation_id = created["conversation_id"]
            _, turn = self.post(
                f"/api/w/dmath/ai/sessions/{conversation_id}/turns",
                {"message": "切换前的这一轮", "page_type": "kps",
                 "route": "/w/dmath/kps"},
            )
            status, error = self.patch_error(
                f"/api/w/dmath/ai/sessions/{conversation_id}",
                {"model": "gpt-test-8"})
            self.assertEqual(status, 409, error)
            self.assertIn("running", error["error"])
            # The refused switch changed nothing.
            _, still = self.get(f"/api/w/dmath/ai/sessions/{conversation_id}")
            self.assertEqual(still["model"], "gpt-test-9")

            for _ in range(150):
                _, data = self.get(
                    f"/api/w/dmath/ai/sessions/{conversation_id}"
                    f"/turns/{turn['turn_id']}?after=0")
                if data["turn"]["status"] not in {"queued", "running"}:
                    break
                time.sleep(0.02)
            self.assertEqual(data["turn"]["status"], "done")

            _, switched = self.patch(
                f"/api/w/dmath/ai/sessions/{conversation_id}",
                {"model": "gpt-test-8"})
            self.assertEqual(switched["model"], "gpt-test-8")
            _, renamed = self.patch(
                f"/api/w/dmath/ai/sessions/{conversation_id}",
                {"title": "换个名字"})
            self.assertEqual(renamed["title"], "换个名字")
            self.assertEqual(renamed["model"], "gpt-test-8")

    def test_the_model_switch_updates_the_conversation_and_refuses_a_running_turn(self):
        with mock.patch("workbench.bridge.conversation_providers.get",
                        return_value=self.provider):
            status, created = self.post("/api/w/dmath/ai/sessions",
                                        {"provider": "codex", "model": "gpt-test-9"})
            self.assertEqual(status, 200)
            self.assertEqual(created["model"], "gpt-test-9")

            status, switched = self.patch(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}",
                {"model": "gpt-test-8"})
            self.assertEqual(status, 200)
            self.assertEqual(switched["model"], "gpt-test-8")

            status, error = self.patch_error(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}",
                {"provider": "claude", "model": "claude-sonnet-5"})
            self.assertEqual(status, 400)
            self.assertIn("harness cannot be changed", error["error"])

            status, cleared = self.patch(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}",
                {"model": ""})
            self.assertEqual(status, 200)
            self.assertIsNone(cleared["model"])

            status, error = self.patch_error(
                f"/api/w/dmath/ai/sessions/{created['conversation_id']}",
                {})
            self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
