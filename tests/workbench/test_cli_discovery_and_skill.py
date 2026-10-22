"""Installed CLI discovery and the bundled Lesson Kit Pi skill."""

import os
import subprocess
import sys
import unittest
from importlib import resources
from pathlib import Path

from workbench import surface
from workbench.bridge import conversation_providers
from workbench.cli import entry, main
from tests.workbench.fixtures import WorkspaceFixture


ROOT = Path(__file__).resolve().parents[2]
SKILL_NAME = "source-bounded-learning-drill"


class CliDiscoveryTests(unittest.TestCase):
    def test_command_names_come_from_the_real_parser(self):
        self.assertEqual(set(main.command_names()), set(surface.COMMANDS))
        self.assertEqual(entry.command_names(), main.command_names())

    def test_all_entry_forms_show_real_extension_help(self):
        env = {**os.environ, "PYTHONUTF8": "1"}
        for module in ("workbench.cli.main", "workbench.cli.entry"):
            for tail, expected in (
                (["--help"], ("evidence", "experience", "mirror", "papers")),
                (["papers", "--help"], ("save", "list", "get", "--input")),
                (["mirror", "--help"], ("figures", "check")),
                (["mirror", "dmath", "check", "--help"], ("--repo", "--entity")),
                (["ingest", "dmath", "bundle", "--help"],
                 ("--selection", "--student-out", "--apply")),
            ):
                with self.subTest(module=module, tail=tail):
                    run = subprocess.run(
                        [sys.executable, "-m", module, *tail], cwd=ROOT,
                        env=env, capture_output=True, text=True,
                    )
                    self.assertEqual(run.returncode, 0, run.stderr)
                    for word in expected:
                        self.assertIn(word, run.stdout)

    def test_extension_arguments_are_validated_by_unified_parser(self):
        parser = main.build_parser()
        self.assertEqual(parser.parse_args(["papers", "dmath", "save", "--input", "x"]).input, "x")
        self.assertEqual(parser.parse_args(["ingest", "dmath", "bundle", "--input", "x"]).input, "x")
        with self.assertRaises(SystemExit) as raised:
            parser.parse_args(["papers", "dmath", "save", "--invented"])
        self.assertEqual(raised.exception.code, 2)

    def test_papers_save_list_and_get_reach_the_same_data_from_both_entry_forms(self):
        import contextlib
        import io
        import json

        for run in (entry.lesson_kit_main, main.main):
            fixture = WorkspaceFixture()
            try:
                manifest = Path(fixture.tmp.name) / "plan.json"
                manifest.write_text(json.dumps({
                    "kind": "practice-set", "title": "Known", "course": "dmath",
                    "request": {}, "items": [
                        {"problem_id": "dmath-ch06-prob-001", "reason": "scope"},
                    ],
                }), encoding="utf-8")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = run(["papers", "dmath", "save", "--input", str(manifest)])
                self.assertEqual(code, 0, out.getvalue())
                receipt = json.loads(out.getvalue())
                self.assertEqual(receipt["title"], "Known")
                paper_id = receipt["practice_set_id"]
                for action in (["list"], ["get", paper_id]):
                    with self.subTest(run=run.__module__, action=action):
                        out = io.StringIO()
                        with contextlib.redirect_stdout(out):
                            code = run(["papers", "dmath", *action])
                        self.assertEqual(code, 0)
                        self.assertIn(paper_id, out.getvalue())
                        json.loads(out.getvalue())
            finally:
                fixture.cleanup()


class BundledSkillTests(unittest.TestCase):
    def test_bundled_teaching_resources_are_readable(self):
        packaged = resources.files("workbench").joinpath("resources", "skills", SKILL_NAME)
        for name in ("SKILL.md", "TERMINOLOGY.md"):
            with self.subTest(name=name):
                content = packaged.joinpath(name).read_text(encoding="utf-8")
                self.assertGreater(len(content), 200)
                self.assertIn("Lesson Kit", content)

    def test_pi_receives_one_bundled_skill_in_print_and_rpc(self):
        expected = str(resources.files("workbench").joinpath("resources", "skills", SKILL_NAME))
        old = str(Path.home() / ".lessonkit-workbench" / "skills" / SKILL_NAME)
        for mode in ("print", "rpc"):
            for args in (
                [],
                ["--model", "custom", "--skill", old, "--skill", expected,
                 "--skill", "C:/another-skill"],
            ):
                with self.subTest(mode=mode, args=args):
                    provider = {"name": "pi", "command": "pi", "args": args,
                                "model": "test-model"}
                    before = list(args)
                    command = conversation_providers.build_command(provider, mode=mode)
                    self.assertEqual(provider["args"], before)
                    skills = [command[i + 1] for i, arg in enumerate(command[:-1])
                              if arg == "--skill"]
                    self.assertEqual(skills.count(expected), 1)
                    self.assertNotIn(old, skills)
                    if "C:/another-skill" in args:
                        self.assertIn("C:/another-skill", skills)
                        self.assertIn("custom", command)
                    self.assertEqual(command[command.index("--mode") + 1],
                                     "rpc" if mode == "rpc" else "json")


if __name__ == "__main__":
    unittest.main()
