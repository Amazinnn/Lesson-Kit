"""UI shell route tests (TDD, red first)."""

import json
import sqlite3
import threading
import unittest
import urllib.request
from urllib.error import HTTPError
from urllib.parse import quote

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

    def post_json(self, path, body):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def request_json(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=data,
            headers={"Content-Type": "application/json"}, method=method,
        )
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_static_asset_served(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn("--dsw-brand-primary", body)
        self.assertIn(".scope-tray-list {", body)
        self.assertIn("overscroll-behavior: contain;", body)

    def test_css_defines_hidden_rule(self):
        # regression: .hidden was missing, breaking the practice visibility choreography
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn(".hidden { display: none !important; }", body)
        self.assertIn("#ai-messages {", body)
        self.assertIn("overflow-y: auto;", body)
        self.assertIn(".ai-plan-step {", body)
        self.assertIn("overflow-wrap: anywhere;", body)
        self.assertIn("column-resizer", body)
        self.assertIn(".flash-card-stage.is-revealed", body)
        self.assertIn("@keyframes flash-answer-reveal", body)
        self.assertIn("@media (prefers-reduced-motion: reduce)", body)

    def test_css_keeps_primary_text_complete_and_contains_wide_content(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn(".page-header h1,", body)
        self.assertIn(".rich-text :not(pre) > code", body)
        self.assertIn(".rich-text table {", body)
        staged_rule = body.split(".staged-title {", 1)[1].split("}", 1)[0]
        suggestion_rule = body.split(".suggestion-title {", 1)[1].split("}", 1)[0]
        self.assertIn("overflow-wrap: anywhere", staged_rule)
        self.assertNotIn("text-overflow: ellipsis", staged_rule)
        self.assertIn("overflow-wrap: anywhere", suggestion_rule)
    def test_css_exposes_the_soft_mondrian_visual_roles(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        self.assertIn("--lk-paper: #fffdf7", body)
        self.assertIn("--lk-blue: #2457c5", body)
        self.assertIn("--lk-yellow: #f2c94c", body)
        self.assertIn("--lk-red: #d6453d", body)
        self.assertIn("#topbar .brand::before", body)
        self.assertIn(".page-header::after", body)
        self.assertIn("inset 4px 0 0 var(--lk-blue)", body)
    def test_css_makes_learning_content_the_primary_surface(self):
        status, body = self.fetch("/static/workbench.css")
        self.assertEqual(status, 200)
        knowledge = body.split(".knowledge-body {", 1)[1].split("}", 1)[0]
        question = body.split(".practice-question-card {", 1)[1].split("}", 1)[0]
        solution = body.split(".practice-solution {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 17px", knowledge)
        self.assertIn("border-left: 4px", knowledge)
        self.assertIn("font-size: 17px", question)
        self.assertIn("box-shadow: none", question)
        self.assertIn("color: var(--dsw-label-secondary)", solution)

    def test_practice_page_session_controls_live_outside_the_answer_card(self):
        # Session controls must not be nested in the answer card, where a state
        # transition could make them unreachable.
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("id='session-end-entry'", body)
        self.assertIn("id='goto-session-end'", body)

    def test_practice_page_requires_an_explicit_content_mode(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("id='practice-mode-exam'", body)
        self.assertIn("id='practice-mode-micro'", body)
        self.assertIn("id='practice-mode-flash_card'", body)
        self.assertIn("id='practice-mode-yes_no'", body)
        self.assertIn("id='flash-direction-choice'", body)
        self.assertIn("id='flash-direction-forward'", body)
        self.assertIn("id='flash-direction-reverse'", body)
        self.assertIn("checked> 正向 · 概念先行", body)
        self.assertNotIn("flash-direction-mixed", body)
        self.assertNotIn("card-direction-switch", body)
        self.assertIn("> 小测<", body)
        self.assertIn("> 闪卡<", body)
        self.assertIn("id='practice-rating-immediate'", body)
        self.assertIn("id='practice-rating-batch'", body)
        self.assertIn("id='start-practice' class='primary' disabled", body)

    def test_practice_page_uses_compact_direct_rating_input(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn(
            "id='rating-input' type='number' min='1' max='5' step='1'",
            body,
        )
        self.assertIn("placeholder='自评 1–5'", body)
        self.assertIn(
            "class='visually-hidden' for='rating-input'", body
        )
        self.assertIn("class='feedback-note-row'", body)
        self.assertIn(
            "id='save-rating' class='primary sm'>记录并下一题", body
        )
        self.assertNotIn("class='rate'", body)

    def test_practice_page_uses_explicit_scope_and_single_content_modes(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("id='staged-list'", body)
        self.assertIn("id='staged-empty'", body)
        for mode in ("exam", "micro", "flash_card", "yes_no"):
            self.assertIn(f"id='practice-mode-{mode}'", body)
        self.assertIn("id='practice-columns'", body)
        self.assertIn("id='practice-rating-immediate'", body)
        self.assertIn("id='practice-rating-batch'", body)

    def test_session_end_page_mentions_cards(self):
        status, body = self.fetch("/w/dmath/session-end")
        self.assertEqual(status, 200)
        self.assertIn("题目与闪卡", body)

    def test_workspace_pages_expose_one_shared_selection_tray(self):
        for path in (
            "/w/dmath/practice", "/w/dmath/kps", "/w/dmath/graph",
            "/w/dmath/kp/dmath-ch06-kp-001", "/w/dmath/session-end",
        ):
            status, body = self.fetch(path)
            self.assertEqual(status, 200)
            self.assertIn("id='scope-tray-toggle'", body)
            self.assertIn("aria-controls='scope-tray-panel'", body)
            self.assertIn("id='scope-tray-panel'", body)
            self.assertIn("id='scope-tray-list'", body)
            self.assertIn("id='scope-tray-collapse'", body)
            self.assertIn("id='scope-tray-practice'", body)
            self.assertIn("dmath-ch06-kp-001", body)
        for path in ("/w/dmath/kps", "/w/dmath/graph"):
            body = self.fetch(path)[1]
            self.assertIn("data-kp-selection", body)
            self.assertNotIn("id='practice-selected'", body)

    def test_plan_keeps_goal_cards_and_dissolves_the_queue_into_suggestions(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("class='goal-cards'", body)
        self.assertNotIn("plan-queue-item", body)
        self.assertNotIn("data-queue-kp-ids", body)
        self.assertNotIn("data-practice-path='", body)
        self.assertIn("id='recalculate-plan'", body)

    def test_practice_page_shows_staged_list_and_suggestions(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("id='daily-plan'", body)
        self.assertIn("学习安排", body)
        self.assertIn("id='staged-practice'", body)
        self.assertIn("id='suggestions-toggle'", body)
        self.assertIn("id='suggestion-list'", body)
        self.assertIn("id='suggestions-empty'", body)
        self.assertNotIn("逐题", body)
        self.assertNotIn("data-practice-path='", body)

    def test_daily_plan_api_is_available_without_agent(self):
        status, payload = self.fetch_json("/api/w/dmath/plan")
        self.assertEqual(status, 200)
        self.assertIn("queue", payload)
        self.assertTrue(payload["queue"])

    def test_goal_api_crud_is_explicit(self):
        status, payload = self.request_json("POST", "/api/w/dmath/goals", {
            "title": "完成 ch06 复习", "kind": "stage",
            "deadline": "2026-09-10", "description": "覆盖核心概念",
        })
        self.assertEqual(status, 200)
        goal_id = payload["goal"]["id"]
        status, listed = self.fetch_json("/api/w/dmath/goals")
        self.assertEqual(status, 200)
        self.assertEqual(listed[0]["id"], goal_id)
        status, updated = self.request_json("PATCH", f"/api/w/dmath/goals/{goal_id}", {"title": "完成复习"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["goal"]["title"], "完成复习")
        status, deleted = self.request_json("DELETE", f"/api/w/dmath/goals/{goal_id}")
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])

    def test_graph_page_uses_native_canvas_not_artifact_iframe(self):
        graph = (self.fixture.ws / "output" / "dmath" / "ch06"
                 / "ch06-graph.html")
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><body>graph</body></html>", encoding="utf-8")
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("id='graph-canvas'", body)
        self.assertIn("id='graph-detail-tab'", body)
        self.assertIn("id='ai-teacher-tab'", body)
        self.assertIn("<script src='/static/graph-physics.js'></script>", body)
        self.assertNotIn("<iframe", body)

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
        self.assertIn("id='left-resizer'", body)
        self.assertIn("id='right-resizer'", body)
        self.assertIn("ai-column", body)
        self.assertIn("topbar", body)
        self.assertIn("<a class='brand' href='/'>lesson-kit</a>", body)
        self.assertNotIn("ai-identity", body)

    def test_ai_column_is_free_conversation_not_task_shortcuts(self):
        for path in ("/w/dmath/practice", "/w/dmath/kps", "/w/dmath/graph"):
            status, body = self.fetch(path)
            self.assertEqual(status, 200)
            self.assertIn("id='ai-session-list'", body)
            self.assertIn("id='ai-new-session'", body)
            self.assertIn("id='ai-provider-picker'", body)
            self.assertIn("id='ai-session-back'", body)
            self.assertNotIn("id='ai-session-delete'", body)
            self.assertNotIn("id='ai-session-rename'", body)
            self.assertNotIn("id='ai-context'", body)
            self.assertNotIn("id='ai-provider'", body)
            self.assertNotIn("id='ai-session'", body)
            self.assertNotIn("id='ai-daily'", body)
        self.assertIn("id='ai-messages'", body)
        self.assertIn("id='ai-input'", body)
        self.assertIn("id='ai-send'", body)
        self.assertIn("id='ai-stop'", body)

    def test_chat_never_offers_a_draft_attachment_setting(self):
        _, practice = self.fetch("/w/dmath/practice")
        _, kps = self.fetch("/w/dmath/kps")
        self.assertNotIn("id='ai-include-draft'", practice)
        self.assertNotIn("id='ai-include-draft'", kps)

    def test_shell_exposes_compact_mobile_drawer_controls(self):
        _, body = self.fetch("/w/dmath/practice")
        self.assertIn("id='mobile-nav-toggle'", body)
        self.assertIn("id='mobile-ai-toggle'", body)
        self.assertIn("aria-controls='left-column'", body)
        self.assertIn("aria-controls='ai-column'", body)

    def test_compact_breakpoint_keeps_the_agent_drawer_entry(self):
        _, css = self.fetch("/static/workbench.css")
        self.assertIn("@media (max-width: 1023px)", css)
        self.assertIn(".mobile-drawer-controls { display: flex; }", css)

    def test_kp_with_an_unscheduled_review_row_stays_neutral(self):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "DELETE FROM learner_signals WHERE target_id=?",
                ("dmath-ch06-kp-001",),
            )
            conn.execute(
                "INSERT INTO review_schedule (item_type, item_id) VALUES (?, ?)",
                ("kp", "dmath-ch06-kp-001"),
            )
            conn.commit()
        finally:
            conn.close()
        _, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertNotIn("重点练习", body)
        self.assertNotIn("可以复习", body)

    def test_kp_page_has_one_scoped_practice_handoff_and_no_raw_study_parameters(self):
        _, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertIn("id='practice-kp'", body)
        self.assertIn("data-practice-kp-id='dmath-ch06-kp-001'", body)
        self.assertNotIn("<h3>信号</h3>", body)
        self.assertNotIn("<h3>调度</h3>", body)
        self.assertNotIn("reps=", body)

    def test_pages_have_editorial_landmarks(self):
        for path in ("/w/dmath/practice", "/w/dmath/kps", "/w/dmath/graph",
                     "/w/dmath/session-end"):
            status, body = self.fetch(path)
            self.assertEqual(status, 200)
            self.assertIn("class='page-header'", body)
            self.assertIn("class='context-line'", body)

    def test_workspace_switch_target_keeps_original_pool_records(self):
        self.fixture.add_workspace("algebra")
        self.post_json("/api/w/dmath/practice", {
            "problem_id": "dmath-ch06-prob-001", "result": "wrong",
        })
        self.post_json("/api/w/dmath/feedback", {
            "item_type": "problem", "item_id": "dmath-ch06-prob-001",
            "rating": 3, "note": "needs review",
        })
        status, body = self.fetch("/w/algebra/practice")
        self.assertEqual(status, 200)
        self.assertIn("data-workspace='algebra'", body)
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM problem_attempts").fetchone()[0], 1
            )
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0], 1
            )
            self.assertGreater(
                conn.execute("SELECT COUNT(*) FROM learner_signals").fetchone()[0], 0
            )
        finally:
            conn.close()

    def test_hub_page_chinese(self):
        status, body = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("<h1>学习工作台</h1>", body)

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
        self.assertIn(">Counting</a>", body)
        self.assertIn("本章知识点", body)
        self.assertIn("id='knowledge-sort'", body)
        self.assertIn("id='knowledge-sort-direction'", body)
        self.assertIn("data-kp-problem-count=", body)

    def test_kp_page_renders(self):
        full_text = "<sup>∗</sup>*两类代表*<b>原始 HTML</b>" + "的组合计数条件。" * 38
        summary = "分析两类代表选择中的乘法计数与顺序条件。"
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE problems SET problem_text=?, display_title=?, topic_label=?, "
                "display_summary=? WHERE problem_id=?",
                (
                    full_text, "两类代表选择", "乘法规则", summary,
                    "dmath-ch06-prob-001",
                ),
            )
            conn.commit()
        finally:
            conn.close()
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertIn("两类代表选择", body)
        self.assertIn("乘法规则", body)
        self.assertIn("dmath-ch06-kp-001", body)
        self.assertNotIn(summary, body)
        self.assertNotIn("problem-summary", body)
        self.assertNotIn("linked-problem-detail", body)
        self.assertIn("class='problem-topic'", body)
        self.assertNotIn("class='problem-topic' open", body)
        self.assertIn("两类代表", body)
        self.assertNotIn("…", body)
        self.assertNotIn("...", body)
        self.assertNotIn("dmath-ch06-prob-001", body)
        self.assertIn("<sup>∗</sup>", body)
        self.assertIn("&lt;b&gt;原始 HTML&lt;/b&gt;", body)
        self.assertIn("<em>", body)

    def test_linked_problem_shows_its_source_evidence(self):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE problems SET source_evidence=?, source_answer=?, "
                "solution_origin=? WHERE problem_id=?",
                ("教材 第12章 习题12-5", "答案：E = λ/(2πε₀x)", "source",
                 "dmath-ch06-prob-001"),
            )
            conn.commit()
        finally:
            conn.close()
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertIn("linked-problem-source", body)
        self.assertIn("教材 第12章 习题12-5", body)

    def test_linked_problem_without_source_evidence_shows_no_source_line(self):
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertNotIn("linked-problem-source", body)

    def test_short_linked_problem_does_not_manufacture_a_summary(self):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "UPDATE problems SET problem_text=?, display_title=?, topic_label=?, "
                "display_summary=? WHERE problem_id=?",
                (
                    "完整短题题干。", "短题标题", "基础计数", "不应显示的摘要。",
                    "dmath-ch06-prob-001",
                ),
            )
            conn.commit()
        finally:
            conn.close()
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        self.assertIn("短题标题", body)
        self.assertIn("完整短题题干。", body)
        self.assertNotIn("不应显示的摘要。", body)

    def test_wiki_link_points_to_a_reachable_knowledge_point(self):
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "INSERT INTO knowledge_points "
                "(kp_id, knowledge_item, body, knowledge_type, importance) "
                "VALUES (?, ?, ?, ?, ?)",
                ("dmath-ch06-kp-002", "Permutations", "", "concept-property", "core"),
            )
            conn.execute(
                "UPDATE knowledge_points SET body = ? WHERE kp_id = ?",
                ("See [[dmath-ch06-kp-002]]", "dmath-ch06-kp-001"),
            )
            conn.commit()
        finally:
            conn.close()
        status, body = self.fetch("/w/dmath/kp/dmath-ch06-kp-001")
        self.assertEqual(status, 200)
        target = "/w/dmath/kp/dmath-ch06-kp-002"
        self.assertIn(f"href='{target}'", body)
        status, target_body = self.fetch(target)
        self.assertEqual(status, 200)
        self.assertIn("Permutations", target_body)

    def test_session_end_page_renders(self):
        status, body = self.fetch("/w/dmath/session-end")
        self.assertEqual(status, 200)
        self.assertIn("pending-ratings", body)

    def test_graph_page_with_artifact(self):
        graph = (self.fixture.ws / "output" / "dmath" / "ch06"
                 / "ch06-graph.html")
        graph.parent.mkdir(parents=True)
        graph.write_text("<html><body>graph</body></html>", encoding="utf-8")
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("id='graph-canvas'", body)
        status, data = self.fetch_json("/api/w/dmath/graph/model")
        self.assertEqual(status, 200)
        self.assertIn("nodes", data)

    def test_graph_page_without_artifact_still_reads_workspace_data(self):
        status, body = self.fetch("/w/dmath/graph")
        self.assertEqual(status, 200)
        self.assertIn("id='graph-canvas'", body)
        status, data = self.fetch_json("/api/w/dmath/graph/model")
        self.assertEqual(status, 200)
        self.assertEqual(data["nodes"][0]["title"], "Counting")
        self.assertIn("id='graph-projection'", body)
        self.assertIn("id='graph-projection-hint'", body)
        self.assertIn("id='graph-state-filter'", body)
        self.assertIn("id='graph-filter-needs_work'", body)
        self.assertIn("id='graph-filter-review'", body)
        self.assertIn("id='graph-filter-mastered'", body)
        self.assertIn("id='graph-filter-null'", body)

    def test_goal_lifecycle_controls_render(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/w/dmath/goals",
            data=json.dumps({"title": "期末掌握计数", "kind": "stage"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn("id='goal-cards'", body)
        self.assertIn("data-goal-edit", body)
        self.assertIn("data-goal-delete", body)
        self.assertIn("data-goal-id='goal-001'", body)
        self.assertIn("期末掌握计数", body)
        self.assertIn("id='goal-start-date'", body)
        self.assertIn("id='goal-nl'", body)
        self.assertIn("id='goal-assist-send'", body)

    def test_left_nav_returns_to_three_pages(self):
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        self.assertIn(">练习<", body)
        self.assertIn(">知识点<", body)
        self.assertIn(">知识图谱<", body)
        self.assertNotIn(">复习<", body)

    def seed_schedule(self, item_type, item_id, days_offset, direction=""):
        import datetime
        conn = sqlite3.connect(self.fixture.db_path)
        due = (datetime.date.today() + datetime.timedelta(days=days_offset)).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO review_schedule (item_type, item_id, direction,"
            " state, repetitions, ease, interval_days, due_at, last_rating,"
            " last_reviewed_at) VALUES (?, ?, ?, 'review', 1, 2.5, 2, ?, 3, ?)",
            (item_type, item_id, direction, due, due),
        )
        conn.commit()
        conn.close()

    def test_practice_page_suggestions_carry_one_phrase_and_hide_scheduler_parameters(self):
        self.seed_schedule("kp", "dmath-ch06-kp-001", -2)
        self.seed_schedule("kp", "dmath-ch06-kp-002", 0)
        self.seed_schedule("kp", "dmath-ch06-kp-003", 3, direction="reverse")
        self.seed_schedule("problem", "dmath-ch06-prob-001", 0)
        self.seed_schedule("kp", "dmath-ch06-kp-004", 10)
        status, body = self.fetch("/w/dmath/practice")
        self.assertEqual(status, 200)
        # the due problem row is folded into its knowledge point; kp-001 keeps
        # its overdue phrase and kp-002 its due-today phrase; future rows stay out
        self.assertIn("id='suggestions-toggle'", body)
        self.assertIn("拖了 2 天", body)
        self.assertIn("今天到期", body)
        self.assertNotIn("3 天后", body)
        self.assertNotIn("badge", body)
        self.assertNotIn("data-include-id", body)
        self.assertNotIn("ease", body)
        self.assertNotIn("interval_days", body)
        self.assertNotIn("repetitions", body)

    def test_suggestion_rows_mapping(self):
        import datetime
        from workbench.server import pages
        today = datetime.date.today()

        def due(days):
            return (today + datetime.timedelta(days=days)).isoformat()

        plan_queue = [
            {"kp_ids": ["kp-1"], "title": "数列极限", "reason": "覆盖仍低"},
            {"kp_ids": ["kp-9"], "title": "未到期项", "reason": "覆盖仍低"},
        ]
        due_items = [
            {"item_type": "kp", "item_id": "kp-1", "due_at": due(-3), "label": "数列极限"},
            {"item_type": "kp", "item_id": "kp-2", "due_at": due(0), "label": "导数定义"},
            {"item_type": "kp", "item_id": "kp-8", "due_at": due(5), "label": "未来项"},
            {"item_type": "problem", "item_id": "prob-1", "due_at": due(-1), "label": "题目"},
        ]
        rows = pages.suggestion_rows(
            plan_queue, due_items,
            problem_kps={"prob-1": ["kp-2"]},
            kp_titles={"kp-1": "数列极限", "kp-2": "导数定义", "kp-9": "未到期项"},
            today=today,
        )
        # due phrases win over plan phrases; overdue first, one row per point
        self.assertEqual(
            rows,
            [
                {"kp_id": "kp-1", "title": "数列极限", "reason": "拖了 3 天"},
                {"kp_id": "kp-2", "title": "导数定义", "reason": "拖了 1 天"},
                {"kp_id": "kp-9", "title": "未到期项", "reason": "覆盖仍低"},
            ],
        )

    def test_suggestion_rows_capped_at_twenty(self):
        import datetime
        from workbench.server import pages
        today = datetime.date.today()
        due_items = [
            {"item_type": "kp", "item_id": f"kp-{i:02d}",
             "due_at": (today - datetime.timedelta(days=1)).isoformat(),
             "label": f"知识点 {i:02d}"}
            for i in range(1, 26)
        ]
        rows = pages.suggestion_rows([], due_items, today=today)
        self.assertEqual(len(rows), 25)
        staged = pages._staged_practice_html("ws", rows)
        self.assertIn("还有 5 条", staged)
        self.assertEqual(staged.count("suggestion-row"), 20)

    def test_review_page_is_gone(self):
        status, body = self.fetch("/w/dmath/review")
        self.assertEqual(status, 200)
        # unknown pages fall back to the practice shell: no review surface remains
        self.assertIn("data-page='practice'", body)
        self.assertNotIn("id='review-content'", body)
        self.assertNotIn("id='card-session'", body)
        self.assertNotIn("id='start-card-review'", body)
        self.assertNotIn("id='start-card-review'", self.fetch("/w/dmath/practice")[1])

    def test_encoded_workspace_names_resolve_on_pages_and_api(self):
        self.fixture.add_workspace("大学物理")
        encoded = quote("大学物理")

        status, body = self.fetch(f"/w/{encoded}/practice")

        self.assertEqual(status, 200)
        self.assertIn("大学物理", body)
        status, payload = self.fetch_json(f"/api/w/{encoded}/weak")
        self.assertEqual(status, 200)
        self.assertIsInstance(payload, list)

    def test_topbar_shows_the_name_and_chapter_not_the_machine_course(self):
        self.fixture.add_workspace("大学物理", course="c01", chapter="ch06")

        status, body = self.fetch(f"/w/{quote('大学物理')}/practice")

        self.assertEqual(status, 200)
        meta = body.split("<span class='meta'>", 1)[1].split("</span>", 1)[0]
        self.assertIn("大学物理", meta)
        self.assertNotIn("c01", meta)
        self.assertNotIn("ch06", meta)

    def test_the_chapter_lens_controls_the_lens_not_the_name(self):
        _, body = self.fetch("/w/dmath/practice")

        self.assertIn("id='chapter-lens'", body)
        self.assertIn("id='chapter-lens-switch' checked", body)
        self.assertIn("<option value='ch06' selected>ch06</option>", body)

    def test_the_whole_course_lens_leaves_the_switch_off(self):
        self.fixture.add_workspace("second", chapter="")

        _, body = self.fetch("/w/second/practice")

        self.assertIn("id='chapter-lens-switch'>", body)
        self.assertIn("id='chapter-lens-select' aria-label='选择章节' hidden", body)

    def test_switching_the_lens_writes_the_registry_value(self):
        from workbench import registry

        status, payload = self.post_json("/api/w/dmath/chapter", {"chapter": "ch06"})

        self.assertEqual(status, 200)
        self.assertEqual(payload["chapter"], "ch06")
        self.assertEqual(payload["chapters"], ["ch06"])
        self.assertEqual(registry.get_workspace("dmath")["active_chapter"], "ch06")

        status, payload = self.post_json("/api/w/dmath/chapter", {"chapter": ""})

        self.assertEqual(payload["chapter"], "")
        self.assertEqual(registry.get_workspace("dmath")["active_chapter"], "")

    def test_the_lens_endpoint_refuses_a_value_that_is_not_an_identifier(self):
        from workbench import registry

        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/w/dmath/chapter",
            data=json.dumps({"chapter": "第7章"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urllib.request.urlopen(request)

        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(registry.get_workspace("dmath")["active_chapter"], "ch06")

    def _seed_second_chapter(self):
        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
            " knowledge_type, importance) VALUES (?, ?, ?, ?, ?)",
            ("dmath-ch07-kp-001", "递归", "", "concept-property", "core"),
        )
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
            " problem_type, source_kind) VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch07-prob-001", '["dmath-ch07-kp-001"]', "P7", "S7",
             "calculation", "textbook"),
        )
        conn.commit()
        conn.close()

    def test_chapters_come_from_content_and_the_hub_stays_course_wide(self):
        self._seed_second_chapter()

        status, payload = self.post_json("/api/w/dmath/chapter", {"chapter": "ch07"})

        self.assertEqual(status, 200)
        self.assertEqual(payload["chapters"], ["ch06", "ch07"])
        _, body = self.fetch("/w/dmath/practice")
        self.assertIn("<option value='ch06'>ch06</option>", body)
        self.assertIn("<option value='ch07' selected>ch07</option>", body)

        stats = self.fetch_json("/api/hub/workspaces")[1][0]["stats"]
        self.assertEqual(stats["kps"], 2)
        self.assertEqual(stats["problems"], 2)

    def test_views_follow_the_lens(self):
        self._seed_second_chapter()
        self.post_json("/api/w/dmath/chapter", {"chapter": "ch07"})

        _, body = self.fetch("/w/dmath/kps")

        self.assertIn("dmath-ch07-kp-001", body)
        self.assertNotIn("dmath-ch06-kp-001", body)

    def test_practice_still_draws_from_a_selection_that_spans_chapters(self):
        self._seed_second_chapter()
        self.post_json("/api/w/dmath/chapter", {"chapter": "ch07"})

        status, payload = self.post_json("/api/w/dmath/pull", {
            "kp_ids": ["dmath-ch06-kp-001", "dmath-ch07-kp-001"],
            "n": 5, "mode": "all",
        })

        self.assertEqual(status, 200)
        self.assertEqual(
            {problem["problem_id"] for problem in payload["problems"]},
            {"dmath-ch06-prob-001", "dmath-ch07-prob-001"},
        )

    def test_unknown_workspace_names_fail_cleanly(self):
        missing = quote("没有这个区")

        with self.assertRaises(HTTPError) as page_error:
            self.fetch(f"/w/{missing}/practice")
        self.assertEqual(page_error.exception.code, 404)
        with self.assertRaises(HTTPError) as api_error:
            self.fetch_json(f"/api/w/{missing}/weak")
        self.assertEqual(api_error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
