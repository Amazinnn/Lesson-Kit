"""Bridge provider execution tests (TDD, red first)."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


providers = load_script("wb_providers", Path("workbench/bridge/providers.py"))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        self.log = self.workspace / "stdout.log"

    def tearDown(self):
        self.tmp.cleanup()

    def write_script(self, name, body):
        path = self.workspace / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_run_success(self):
        script = self.write_script(
            "ok.py", "import sys\nsys.stdout.write('hello')\n"
        )
        code = providers.run_provider(
            {"command": "python", "args": [str(script)], "timeout_s": 30},
            self.workspace,
            self.log,
        )
        self.assertEqual(code, 0)
        self.assertIn("hello", self.log.read_text(encoding="utf-8"))

    def test_run_failure_returns_nonzero(self):
        script = self.write_script("fail.py", "import sys\nsys.exit(3)\n")
        code = providers.run_provider(
            {"command": "python", "args": [str(script)], "timeout_s": 30},
            self.workspace,
            self.log,
        )
        self.assertEqual(code, 3)

    def test_run_timeout_returns_timeout_marker(self):
        script = self.write_script(
            "sleepy.py", "import time\ntime.sleep(5)\n"
        )
        code = providers.run_provider(
            {"command": "python", "args": [str(script)], "timeout_s": 1},
            self.workspace,
            self.log,
        )
        self.assertEqual(code, "timeout")


if __name__ == "__main__":
    unittest.main()
