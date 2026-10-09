"""Knowledge-point practice experience: optional summary, links, and revision safety."""

import json
import sqlite3
import unittest
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture
from workbench.cli import entry as cli_entry
from workbench.data import experience
from workbench.data.pool import Pool
from workbench.server import context, experience_api, experience_page
from workbench.server.api import ApiError


class PracticeExperienceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.pool = Pool(
            root=self.fixture.ws,
            db_path=self.fixture.db_path,
            course="dmath",
            chapter="ch06",
        )
        self.kp_id = "dmath-ch06-kp-001"
        self.other_kp_id = "dmath-ch06-kp-002"
        self.problem_id = "dmath-ch06-prob-901"
        self.foreign_problem_id = "dmath-ch06-prob-902"
        conn = sqlite3.connect(self.fixture.db_path)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_points (kp_id, knowledge_item) VALUES (?, ?)",
                (self.other_kp_id, "Other concept"),
            )
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type,"
                " source_kind, origin_kind, display_title) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.problem_id, json.dumps([self.kp_id]), "Representative problem",
                 "calculation", "textbook", "source_problem", "典型状态转移题"),
            )
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type,"
                " source_kind, origin_kind) VALUES (?, ?, ?, ?, ?, ?)",
                (self.foreign_problem_id, json.dumps([self.other_kp_id]), "Foreign problem",
                 "calculation", "textbook", "source_problem"),
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_absent_experience_is_not_materialized_by_read(self):
        self.assertIsNone(experience.get(self.pool, self.kp_id))
        count = self.pool.connect().execute(
            "SELECT COUNT(*) FROM kp_experiences WHERE kp_id=?", (self.kp_id,)
        ).fetchone()[0]
        self.assertEqual(count, 0)
        panel = experience_page._panel(self.pool, "fixture", self.kp_id)
        self.assertIn("暂无经验总结", panel)
        self.assertIn("新增经验", panel)

    def test_create_and_read_preserve_ordered_representative_problems(self):
        created = experience.create(
            self.pool, self.kp_id, "先识别状态，再决定遍历方向。",
            [self.problem_id], updated_by="user")

        self.assertEqual(created["revision"], 1)
        self.assertEqual(created["updated_by"], "user")
        self.assertEqual(created["problem_ids"], [self.problem_id])
        self.assertEqual(experience.get(self.pool, self.kp_id), created)
        panel = experience_page._panel(self.pool, "fixture", self.kp_id)
        self.assertIn("先识别状态", panel)
        self.assertIn("典型状态转移题", panel)

    def test_update_requires_the_current_revision(self):
        experience.create(
            self.pool, self.kp_id, "旧经验", [self.problem_id], updated_by="user")
        updated = experience.update(
            self.pool, self.kp_id, 1, "新经验", [], updated_by="agent")
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["content"], "新经验")
        self.assertEqual(updated["problem_ids"], [])

        with self.assertRaises(experience.RevisionConflict):
            experience.update(
                self.pool, self.kp_id, 1, "过期覆盖", [self.problem_id],
                updated_by="user")
        self.assertEqual(experience.get(self.pool, self.kp_id)["content"], "新经验")

    def test_invalid_problem_link_rolls_back_the_whole_update(self):
        before = experience.create(
            self.pool, self.kp_id, "稳定内容", [self.problem_id], updated_by="user")

        with self.assertRaisesRegex(ValueError, "not linked to knowledge point"):
            experience.update(
                self.pool, self.kp_id, before["revision"], "不应写入",
                [self.foreign_problem_id], updated_by="agent")

        after = experience.get(self.pool, self.kp_id)
        self.assertEqual(after["content"], "稳定内容")
        self.assertEqual(after["revision"], 1)
        self.assertEqual(after["problem_ids"], [self.problem_id])

    def test_problem_membership_change_removes_an_invalid_reference(self):
        experience.create(
            self.pool, self.kp_id, "经验", [self.problem_id], updated_by="user")
        conn = self.pool.connect()
        with conn:
            conn.execute(
                "UPDATE problems SET kp_ids=? WHERE problem_id=?",
                (json.dumps([self.other_kp_id]), self.problem_id),
            )
        self.assertEqual(experience.get(self.pool, self.kp_id)["problem_ids"], [])

    def test_deleting_a_problem_removes_only_its_experience_reference(self):
        experience.create(
            self.pool, self.kp_id, "经验仍应保留", [self.problem_id], updated_by="user")
        conn = self.pool.connect()
        with conn:
            conn.execute("DELETE FROM problems WHERE problem_id=?", (self.problem_id,))

        current = experience.get(self.pool, self.kp_id)
        self.assertIsNotNone(current)
        self.assertEqual(current["content"], "经验仍应保留")
        self.assertEqual(current["problem_ids"], [])

    def test_deleting_a_knowledge_point_removes_its_experience(self):
        experience.create(
            self.pool, self.other_kp_id, "会随知识点一起消失", [self.foreign_problem_id],
            updated_by="user")
        conn = self.pool.connect()
        with conn:
            conn.execute("DELETE FROM knowledge_points WHERE kp_id=?", (self.other_kp_id,))

        self.assertIsNone(experience.get(self.pool, self.other_kp_id))
        link_count = conn.execute(
            "SELECT COUNT(*) FROM kp_experience_problems WHERE kp_id=?",
            (self.other_kp_id,),
        ).fetchone()[0]
        self.assertEqual(link_count, 0)

    def test_delete_is_revision_guarded_and_removes_links(self):
        created = experience.create(
            self.pool, self.kp_id, "可删除经验", [self.problem_id], updated_by="user")
        with self.assertRaises(experience.RevisionConflict):
            experience.delete(self.pool, self.kp_id, created["revision"] + 1)

        deleted = experience.delete(self.pool, self.kp_id, created["revision"])
        self.assertEqual(deleted, {"kp_id": self.kp_id, "deleted": True})
        self.assertIsNone(experience.get(self.pool, self.kp_id))
        links = self.pool.connect().execute(
            "SELECT COUNT(*) FROM kp_experience_problems WHERE kp_id=?", (self.kp_id,)
        ).fetchone()[0]
        self.assertEqual(links, 0)

    def test_create_refuses_blank_content_instead_of_storing_an_empty_row(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            experience.create(self.pool, self.kp_id, "   ", [], updated_by="user")
        self.assertIsNone(experience.get(self.pool, self.kp_id))

    def test_http_adapter_reports_revision_conflict_as_409(self):
        experience.create(
            self.pool, self.kp_id, "第一版", [self.problem_id], updated_by="user")
        experience.update(
            self.pool, self.kp_id, 1, "第二版", [self.problem_id], updated_by="agent")

        with self.assertRaises(ApiError) as caught:
            experience_api.update(
                self.pool, {}, {"kp_id": self.kp_id},
                {"expected_revision": 1, "content": "旧客户端覆盖", "problem_ids": []},
            )
        self.assertEqual(caught.exception.status, 409)

    def test_agent_context_reads_the_same_experience_and_problem_title(self):
        experience.create(
            self.pool, self.kp_id, "**倒序**可以避免本轮污染。",
            [self.problem_id], updated_by="agent")

        item = context._experience_context(self.pool, self.kp_id)

        self.assertEqual(item["revision"], 1)
        self.assertEqual(item["updated_by"], "agent")
        self.assertEqual(item["problems"][0]["title"], "典型状态转移题")

    def test_installed_cli_dispatches_lesson_kit_experience_without_touching_legacy_parser(self):
        with mock.patch("workbench.cli.experience.main", return_value=7) as run:
            result = cli_entry.lesson_kit_main([
                "experience", "fixture", "get", self.kp_id,
            ])
        self.assertEqual(result, 7)
        run.assert_called_once_with(
            ["fixture", "get", self.kp_id], prog="lesson-kit experience")

    def test_non_experience_cli_commands_still_delegate_to_the_existing_super_cli(self):
        with mock.patch("workbench.cli.main.lesson_kit_main", return_value=3) as run:
            result = cli_entry.lesson_kit_main(["ls", "--json"])
        self.assertEqual(result, 3)
        run.assert_called_once_with(["ls", "--json"])


if __name__ == "__main__":
    unittest.main()
