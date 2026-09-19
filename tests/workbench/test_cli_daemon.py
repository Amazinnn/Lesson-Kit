"""Background service lifecycle and the lesson-kit CLI entry point."""

import contextlib
import io
import os
import unittest
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

    def test_both_entry_points_keep_their_own_program_name(self):
        self.assertEqual(self.cli.build_parser().prog, "wb")
        self.assertEqual(self.cli.build_parser("lesson-kit").prog, "lesson-kit")
        self.assertTrue(callable(self.cli.lesson_kit_main))


if __name__ == "__main__":
    unittest.main()
