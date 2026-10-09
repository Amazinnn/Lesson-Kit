"""Schema tests for the authored-content mirror ledger."""

import importlib.util
import sqlite3
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "content_mirror_pool_schema", REPO_ROOT / "pool" / "scripts" / "pool_schema.py"
)
pool_schema = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pool_schema)


class ContentMirrorSchemaTests(unittest.TestCase):
    def test_migration_is_additive_idempotent_and_hash_free(self):
        conn = sqlite3.connect(":memory:")
        try:
            first = pool_schema.ensure_content_mirror_schema(conn)
            second = pool_schema.ensure_content_mirror_schema(conn)
            self.assertEqual(first, ["content_mirror_state", "content_mirror_log"])
            self.assertEqual(second, [])
            names = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertIn("content_mirror_state", names)
            self.assertIn("content_mirror_log", names)
            sql = "\n".join(
                row[0] or "" for row in conn.execute(
                    "SELECT sql FROM sqlite_master WHERE name IN "
                    "('content_mirror_state', 'content_mirror_log')"
                )
            ).lower()
            self.assertNotIn("hash", sql)
            self.assertNotIn("fingerprint", sql)
            self.assertNotIn("sha", sql)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
