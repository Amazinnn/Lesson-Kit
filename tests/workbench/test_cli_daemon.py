"""Background service lifecycle and the lesson-kit CLI entry point."""

import contextlib
import io
import os
import shutil
import sqlite3
import unittest
from pathlib import Path
from unittest import mock

from tests.workbench.fixtures import WorkspaceFixture


class ServiceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import service

        self.service = service

    def tearDown(self):
        self.fixture.cleanup()

    def test_liveness_probe_rejects_unusable_pids_without_signalling(self):
        self.assertTrue(self.service.process_alive(os.getpid()))
        self.assertFalse(self.service.process_alive(None))
        self.assertFalse(self.service.process_alive(0))
        self.assertFalse(self.service.process_alive(-1))
        self.assertFalse(self.service.process_alive("123"))
        self.assertFalse(self.service.process_alive(999999999))

    def test_process_image_identifies_python_and_rejects_others(self):
        image = self.service.process_image(os.getpid())

        self.assertTrue(image)
        self.assertTrue(self.service._looks_like_python(image))
        self.assertFalse(self.service._looks_like_python("C:/Windows/explorer.exe"))
        self.assertFalse(self.service._looks_like_python(""))

    def test_state_round_trip_and_stale_record(self):
        self.assertEqual(self.service.read_state(), {})

        self.service.write_state({"pid": os.getpid(), "port": 3099})
        self.assertEqual(self.service.running_state()["pid"], os.getpid())

        self.service.write_state({"pid": 999999999, "port": 3099})
        self.assertEqual(self.service.running_state(), {})

        self.service.clear_state()
        self.assertEqual(self.service.read_state(), {})

    def test_status_reports_absence_without_raising(self):
        self.assertFalse(self.service.status()["running"])

    def test_stop_refuses_a_recycled_pid(self):
        self.service.write_state({"pid": os.getpid(), "port": 3099})
        with mock.patch.object(
            self.service, "process_image", return_value="C:/Windows/explorer.exe"
        ), mock.patch.object(self.service, "_signal") as signal:
            with self.assertRaises(RuntimeError) as caught:
                self.service.stop()

        self.assertIn("explorer.exe", str(caught.exception))
        signal.assert_not_called()
        self.assertEqual(self.service.read_state(), {})

    def test_stop_terminates_the_recorded_service(self):
        self.service.write_state({"pid": os.getpid(), "port": 3099})
        with mock.patch.object(
            self.service, "process_image", return_value="C:/Python/python.exe"
        ), mock.patch.object(self.service, "_terminate") as terminate:
            result = self.service.stop()

        terminate.assert_called_once_with(os.getpid(), 3099)
        self.assertTrue(result["stopped"])
        self.assertEqual(self.service.read_state(), {})

    def test_start_reports_a_service_that_dies_immediately(self):
        process = mock.Mock(pid=4242, returncode=3)
        process.poll.return_value = 3
        with mock.patch.object(
            self.service.subprocess, "Popen", return_value=process
        ), mock.patch.object(self.service, "port_answers", return_value=False):
            with self.assertRaises(RuntimeError) as caught:
                self.service.start(port=3099)

        self.assertIn("exited with code 3", str(caught.exception))
        self.assertEqual(self.service.read_state(), {})

    def test_start_requires_the_port_to_answer(self):
        process = mock.Mock(pid=4242, returncode=None)
        process.poll.return_value = None
        with mock.patch.object(
            self.service.subprocess, "Popen", return_value=process
        ), mock.patch.object(
            self.service, "port_answers", return_value=False
        ), mock.patch.object(self.service, "START_TIMEOUT_S", 0.05):
            with self.assertRaises(RuntimeError) as caught:
                self.service.start(port=3099)

        self.assertIn("did not answer", str(caught.exception))
        process.terminate.assert_called_once()
        self.assertEqual(self.service.read_state(), {})

    def test_start_records_the_service_only_once_it_answers(self):
        process = mock.Mock(pid=4242, returncode=None)
        process.poll.return_value = None
        with mock.patch.object(
            self.service.subprocess, "Popen", return_value=process
        ), mock.patch.object(
            self.service, "port_answers", side_effect=[False, True]
        ) as port_answers:
            result = self.service.start(port=3099)

        self.assertTrue(result["started"])
        self.assertEqual(port_answers.call_count, 2)
        self.assertEqual(self.service.read_state(), {
            "pid": 4242, "port": 3099, "started_at": mock.ANY,
        })

    def test_start_refuses_a_port_taken_by_an_unrecorded_process(self):
        with mock.patch.object(
            self.service.subprocess, "Popen"
        ) as popen, mock.patch.object(self.service, "port_answers", return_value=True):
            with self.assertRaises(RuntimeError) as caught:
                self.service.start(port=3099)

        self.assertIn("already answers", str(caught.exception))
        popen.assert_not_called()

    def test_start_is_idempotent_while_the_service_lives(self):
        self.service.write_state({"pid": os.getpid(), "port": 3099})
        with mock.patch.object(self.service.subprocess, "Popen") as popen:
            result = self.service.start(port=3099)

        popen.assert_not_called()
        self.assertTrue(result["already_running"])


class CliSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import main as cli_main

        self.cli = cli_main

    def tearDown(self):
        self.fixture.cleanup()

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def test_parser_accepts_daemon_and_dashboard_commands(self):
        parser = self.cli.build_parser()

        self.assertEqual(parser.parse_args(["daemon", "start", "--port", "3098"]).port, 3098)
        self.assertEqual(parser.parse_args(["daemon", "stop"]).action, "stop")
        self.assertEqual(parser.parse_args(["daemon", "status"]).action, "status")
        self.assertEqual(parser.parse_args(["dashboard"]).port, 3081)

    def test_daemon_status_without_a_service_reports_absence(self):
        code, out = self.run_cli("daemon", "status")

        self.assertEqual(code, 0)
        self.assertIn("not running", out)

    def test_daemon_stop_without_a_service_is_not_an_error(self):
        code, out = self.run_cli("daemon", "stop")

        self.assertEqual(code, 0)
        self.assertIn("not running", out)

    def test_bridge_add_writes_command_and_model(self):
        code, _ = self.run_cli(
            "bridge", "add", "pi", "--command", "C:/npm-global/pi.cmd",
            "--model", "minimax/MiniMax-M2.7",
        )

        self.assertEqual(code, 0)
        from workbench import registry

        entry = registry.load_bridges()["providers"]["pi"]
        self.assertEqual(entry["command"], "C:/npm-global/pi.cmd")
        self.assertEqual(entry["model"], "minimax/MiniMax-M2.7")

    def test_bridge_add_requires_provider_and_command(self):
        with self.assertRaises(SystemExit):
            self.run_cli("bridge", "add")

    def test_bridge_list_reports_the_configured_command_and_its_source(self):
        self.run_cli("bridge", "add", "pi", "--command", "C:/npm-global/pi.cmd")
        with mock.patch(
            "workbench.bridge.conversation_providers.shutil.which", return_value=None
        ):
            code, out = self.run_cli("bridge", "list")

        self.assertEqual(code, 0)
        self.assertIn("pi: C:/npm-global/pi.cmd", out)
        self.assertIn("[config]", out)

    def test_bridge_list_reports_every_supported_provider(self):
        with mock.patch(
            "workbench.bridge.conversation_providers.shutil.which", return_value=None
        ):
            code, out = self.run_cli("bridge", "list")

        self.assertEqual(code, 0)
        for name in ("codex", "claude", "pi"):
            self.assertIn(f"{name}: not found", out)

    def test_one_command_name_for_both_entry_points(self):
        self.assertEqual(self.cli.build_parser().prog, "lesson-kit")
        self.assertEqual(self.cli.build_parser("lesson-kit").prog, "lesson-kit")
        self.assertTrue(callable(self.cli.lesson_kit_main))
        self.assertTrue(callable(self.cli.main))


class BootstrapInitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import main as cli_main

        self.cli = cli_main
        self.empty = Path(self.fixture.tmp.name) / "fresh"
        self.empty.mkdir()
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)
        self.fixture.cleanup()

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def test_init_creates_a_workspace_from_an_empty_folder(self):
        code, out = self.run_cli("init", str(self.empty), "--course", "geo", "--chapter", "ch01")

        self.assertEqual(code, 0)
        self.assertIn("registered workspace", out)
        self.assertTrue((self.empty / "pool" / "geo.db").is_file())
        for name in ("figures", "explain", "jobs"):
            self.assertTrue((self.empty / ".lessonkit" / name).is_dir(), name)
        from workbench import registry

        workspace = registry.get_workspace("fresh")
        self.assertEqual(workspace["active_course"], "geo")
        self.assertEqual(workspace["active_chapter"], "ch01")

        conn = sqlite3.connect(self.empty / "pool" / "geo.db")
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertIn("knowledge_points", tables)
        self.assertIn("flash_cards", tables)
        self.assertNotIn("candidate_problems", tables)

    def test_init_on_an_existing_workspace_never_bootstraps(self):
        code, out = self.run_cli("init", str(self.fixture.ws), "--course", "dmath")

        self.assertEqual(code, 0)
        self.assertFalse((self.fixture.ws / ".lessonkit").exists())
        self.assertFalse((self.fixture.ws / "pool" / "dmath2.db").exists())

    def test_init_defaults_to_the_current_directory(self):
        os.chdir(self.empty)

        code, out = self.run_cli("init", "--course", "geo")

        self.assertEqual(code, 0)
        self.assertTrue((self.empty / "pool" / "geo.db").is_file())
        from workbench import registry

        workspace = registry.get_workspace("fresh")
        self.assertEqual(workspace["path"], str(self.empty))
        self.assertEqual(workspace["active_course"], "geo")

    def test_init_derives_the_course_from_an_ascii_folder_name(self):
        folder = Path(self.fixture.tmp.name) / "Linear Algebra (Spring)"
        folder.mkdir()

        code, out = self.run_cli("init", str(folder))

        self.assertEqual(code, 0)
        self.assertTrue((folder / "pool" / "linear-algebra-spring.db").is_file())

    def test_init_in_the_current_directory_derives_from_its_resolved_name(self):
        folder = Path(self.fixture.tmp.name) / "Graph Theory"
        folder.mkdir()
        os.chdir(folder)

        code, out = self.run_cli("init")

        self.assertEqual(code, 0)
        self.assertTrue((folder / "pool" / "graph-theory.db").is_file())

    def test_init_on_an_existing_pool_takes_the_course_from_the_database(self):
        folder = Path(self.fixture.tmp.name) / "已建好的库"
        (folder / "pool").mkdir(parents=True)
        shutil.copy(self.fixture.db_path, folder / "pool" / "dmath.db")

        code, out = self.run_cli("init", str(folder))

        self.assertEqual(code, 0)
        from workbench import registry

        workspace = registry.get_workspace("已建好的库")
        self.assertEqual(workspace["active_course"], "dmath")

    def test_a_folder_name_without_ascii_gets_the_first_short_code(self):
        folder = Path(self.fixture.tmp.name) / "大学物理"
        folder.mkdir()

        code, out = self.run_cli("init", str(folder))

        self.assertEqual(code, 0)
        self.assertTrue((folder / "pool" / "c01.db").is_file())
        from workbench import registry

        self.assertEqual(registry.get_workspace("大学物理")["active_course"], "c01")

    def test_automatic_short_codes_do_not_repeat_across_workspaces(self):
        first = Path(self.fixture.tmp.name) / "大学物理甲"
        second = Path(self.fixture.tmp.name) / "大学物理乙"

        for folder in (first, second):
            folder.mkdir()
            code, out = self.run_cli("init", str(folder))
            self.assertEqual(code, 0)

        self.assertTrue((first / "pool" / "c01.db").is_file())
        self.assertTrue((second / "pool" / "c02.db").is_file())

    def test_an_explicit_course_must_be_a_lowercase_ascii_slug(self):
        for bad in ("大学物理", "Graph Theory", "Geo"):
            with self.assertRaises(SystemExit) as caught:
                self.run_cli("init", str(self.empty), "--course", bad)

            self.assertIn("not a valid identifier", str(caught.exception))

        self.assertFalse((self.empty / "pool").exists())
        self.assertFalse((self.empty / ".lessonkit").exists())

    def test_use_switches_the_active_course_and_chapter(self):
        code, out = self.run_cli("use", "geo", "ch07")

        self.assertEqual(code, 0)
        from workbench import registry

        workspace = registry.get_workspace("dmath")
        self.assertEqual(workspace["active_course"], "geo")
        self.assertEqual(workspace["active_chapter"], "ch07")

    def test_use_names_an_unknown_workspace_without_changing_state(self):
        with self.assertRaises(KeyError):
            self.run_cli("use", "geo", "ch07", "--workspace", "nope")

        from workbench import registry

        workspace = registry.get_workspace("dmath")
        self.assertEqual(workspace["active_course"], "dmath")

    def test_use_refuses_a_course_that_is_not_an_identifier(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("use", "大学物理", "ch01")

        self.assertIn("not a valid identifier", str(caught.exception))
        from workbench import registry

        self.assertEqual(registry.get_workspace("dmath")["active_course"], "dmath")

    def test_use_refuses_a_chapter_that_is_not_an_identifier(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("use", "geo", "第7章")

        self.assertIn("not a valid identifier", str(caught.exception))
        from workbench import registry

        self.assertEqual(registry.get_workspace("dmath")["active_chapter"], "ch06")

    def test_init_refuses_a_chapter_that_is_not_an_identifier(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("init", str(self.fixture.ws), "--chapter", "ch0 6")

        self.assertIn("not a valid identifier", str(caught.exception))

    def test_init_refuses_a_folder_with_several_pools(self):
        folder = Path(self.fixture.tmp.name) / "two-pools"
        (folder / "pool").mkdir(parents=True)
        shutil.copy(self.fixture.db_path, folder / "pool" / "dmath.db")
        shutil.copy(self.fixture.db_path, folder / "pool" / "dmath-backup.db")

        with self.assertRaises(SystemExit) as caught:
            self.run_cli("init", str(folder))

        self.assertIn("dmath-backup.db", str(caught.exception))

    def test_a_command_with_several_workspaces_names_the_candidates(self):
        self.fixture.add_workspace("second")

        with self.assertRaises(SystemExit) as caught:
            self.run_cli("weak")

        message = str(caught.exception)
        self.assertIn("dmath", message)
        self.assertIn("second", message)
        self.assertIn("lesson-kit weak", message)

        code, out = self.run_cli("weak", "second", "--limit", "1")
        self.assertEqual(code, 0)

    def test_use_with_an_empty_chapter_switches_to_the_whole_course(self):
        code, out = self.run_cli("use", "dmath", "")

        self.assertEqual(code, 0)
        from workbench import registry

        self.assertEqual(registry.get_workspace("dmath")["active_chapter"], "")
        self.assertIn("全课程", out)

    def test_use_requires_an_explicit_workspace_when_ambiguous(self):
        self.fixture.add_workspace("second")
        with self.assertRaises(SystemExit):
            self.run_cli("use", "geo", "ch07")

        code, out = self.run_cli("use", "geo", "ch07", "--workspace", "second")
        self.assertEqual(code, 0)
        from workbench import registry

        self.assertEqual(registry.get_workspace("second")["active_course"], "geo")


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.cli import main as cli_main

        self.cli = cli_main

    def tearDown(self):
        self.fixture.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.cli.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_doctor_passes_on_a_healthy_fixture_and_writes_nothing(self):
        from workbench import registry
        from workbench.cli import doctor

        before = (registry.base_dir() / "workspaces.json").read_text(encoding="utf-8")
        code, out, _ = self.run_cli("doctor")

        self.assertEqual(code, 0)
        self.assertIn("all checks passed", out)
        self.assertIn("pool database", out)
        self.assertEqual(
            (registry.base_dir() / "workspaces.json").read_text(encoding="utf-8"),
            before)
        self.assertTrue(callable(doctor.all_passed))

    def test_doctor_lists_a_missing_database_and_fails(self):
        (self.fixture.ws / "pool" / "dmath.db").unlink()
        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 2)
        self.assertIn("FAIL", out)
        self.assertIn("pool database", out)
        self.assertIn("nothing was changed", err)

    def test_doctor_lists_a_missing_provider_executable(self):
        with mock.patch(
            "workbench.bridge.conversation_providers.discover",
            return_value=[{"name": "pi", "command": "C:/nowhere/pi.cmd",
                           "args": [], "model": None, "timeout_s": 300}],
        ):
            code, out, _ = self.run_cli("doctor")

        self.assertEqual(code, 2)
        self.assertIn("missing executable for pi", out)

    def test_doctor_reports_a_service_that_no_longer_answers(self):
        from workbench.cli import service

        service.write_state({"pid": 999999999, "port": 3099, "started_at": "x"})
        try:
            code, out, _ = self.run_cli("doctor")
        finally:
            service.clear_state()

        self.assertEqual(code, 0)
        self.assertIn("not running", out)


if __name__ == "__main__":
    unittest.main()
