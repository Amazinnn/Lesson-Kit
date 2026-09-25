"""Registry and bridge config tests (TDD, red first)."""

import importlib.util
import os
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


registry = load_script("wb_registry", Path("workbench/registry.py"))


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "dmath"
        (self.ws / "pool").mkdir(parents=True)
        (self.ws / "pool" / "dmath.db").write_bytes(b"x")

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    def test_register_valid_folder(self):
        workspace = registry.register(str(self.ws))
        self.assertEqual(workspace["name"], "dmath")
        self.assertEqual(workspace["path"], str(self.ws))

    def test_register_invalid_folder_raises(self):
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        with self.assertRaises(ValueError):
            registry.register(str(empty))

    def test_list_and_get(self):
        registry.register(str(self.ws))
        workspaces = registry.list_workspaces()
        self.assertEqual(len(workspaces), 1)
        self.assertEqual(registry.get_workspace("dmath")["path"], str(self.ws))

    def test_get_missing_raises(self):
        with self.assertRaises(KeyError):
            registry.get_workspace("nope")

    def test_register_twice_updates(self):
        registry.register(str(self.ws))
        registry.register(str(self.ws), course="dmath", chapter="ch06")
        workspace = registry.get_workspace("dmath")
        self.assertEqual(workspace["active_course"], "dmath")
        self.assertEqual(registry.list_workspaces().__len__(), 1)

    def test_a_second_pool_must_be_chosen_explicitly(self):
        (self.ws / "pool" / "dmath-pre-readiness-2026-08-26.db").write_bytes(b"x")

        with self.assertRaises(ValueError) as caught:
            registry.register(str(self.ws))

        message = str(caught.exception)
        self.assertIn("dmath-pre-readiness-2026-08-26.db", message)
        self.assertIn("--course", message)
        self.assertEqual(registry.list_workspaces(), [])

    def test_named_course_picks_its_own_pool_out_of_several(self):
        (self.ws / "pool" / "dmath-pre-readiness-2026-08-26.db").write_bytes(b"x")

        workspace = registry.register(str(self.ws), course="dmath")

        self.assertEqual(workspace["db"], "pool/dmath.db")

    def test_ingest_backups_are_not_pool_candidates(self):
        backup = self.ws / "pool" / "backups"
        backup.mkdir()
        (backup / "batch-001.sqlite").write_bytes(b"x")
        (self.ws / "pool" / "dmath.db.ingest-backup").write_bytes(b"x")
        (self.ws / "pool" / "dmath.db").unlink()

        self.assertEqual(registry.pool_candidates(self.ws), [])
        self.assertEqual(registry.find_pool(self.ws), "")

    def test_a_name_collision_never_replaces_the_other_folder(self):
        registry.register(str(self.ws))
        other = Path(self.tmp.name) / "elsewhere"
        (other / "pool").mkdir(parents=True)
        (other / "pool" / "other.db").write_bytes(b"x")

        with self.assertRaises(ValueError) as caught:
            registry.register(str(other), name="dmath")

        self.assertIn("already registered", str(caught.exception))
        self.assertEqual(registry.get_workspace("dmath")["path"], str(self.ws))

    def test_one_folder_cannot_be_two_workspaces(self):
        registry.register(str(self.ws))

        with self.assertRaises(ValueError) as caught:
            registry.register(str(self.ws), name="alias")

        self.assertIn("already registered", str(caught.exception))
        self.assertEqual([w["name"] for w in registry.list_workspaces()], ["dmath"])

    def test_a_pool_outside_the_folder_is_refused(self):
        outside = Path(self.tmp.name) / "stolen.db"
        outside.write_bytes(b"x")

        with self.assertRaises(ValueError) as caught:
            registry.register(str(self.ws), db="../stolen.db")

        self.assertIn("must live inside the workspace", str(caught.exception))


class BridgeConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    def test_bridges_default_empty(self):
        self.assertEqual(registry.load_bridges(), {"version": 1, "providers": {}})

    def test_add_bridge_provider(self):
        registry.add_bridge("claude", "claude", args=["-p"], timeout_s=300)
        bridges = registry.load_bridges()
        self.assertIn("claude", bridges["providers"])
        self.assertEqual(bridges["providers"]["claude"]["command"], "claude")

    def test_add_bridge_twice_overwrites(self):
        registry.add_bridge("claude", "claude", timeout_s=300)
        registry.add_bridge("claude", "claude-code", timeout_s=600)
        bridges = registry.load_bridges()
        self.assertEqual(bridges["providers"]["claude"]["command"], "claude-code")
        self.assertEqual(len(bridges["providers"]), 1)

    def test_tool_timeout_is_optional(self):
        registry.add_bridge("claude", "claude")
        self.assertNotIn("tool_timeout_s", registry.load_bridges()["providers"]["claude"])

        registry.add_bridge("pi", "pi", tool_timeout_s=900)
        self.assertEqual(
            registry.load_bridges()["providers"]["pi"]["tool_timeout_s"], 900)


if __name__ == "__main__":
    unittest.main()
