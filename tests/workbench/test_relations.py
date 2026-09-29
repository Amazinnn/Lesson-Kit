"""Strict relation CRUD and atomic batch contracts."""

import importlib.util
import sqlite3
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


pool_schema = load_script("relation_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script(
    "relation_create_tables", Path("pipeline/scripts/create-tables.py")
)


class RelationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        for number, title in ((1, "极限"), (2, "导数"), (3, "连续")):
            conn.execute(
                "INSERT INTO knowledge_points "
                "(kp_id, knowledge_item, knowledge_type, importance) "
                "VALUES (?, ?, 'concept-property', 'core')",
                (f"dmath-ch06-kp-{number:03d}", title),
            )
        conn.commit()
        conn.close()

        from workbench.data.pool import Pool
        self.pool = Pool(self.tmp.name, self.db_path, "dmath", "ch06")

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def relation(self, source=1, target=2, relation_type="prerequisite",
                 direction="directed", strength="high"):
        return {
            "source_kp_id": f"dmath-ch06-kp-{source:03d}",
            "target_kp_id": f"dmath-ch06-kp-{target:03d}",
            "relation_type": relation_type,
            "direction": direction,
            "strength": strength,
        }

    def test_single_crud_validates_resulting_relation(self):
        from workbench.data import content

        created = content.create(self.pool, "relation", self.relation())
        self.assertEqual(created["relation_id"], "dmath-ch06-rel-001")
        self.assertEqual(created["source_kp_id"], "dmath-ch06-kp-001")
        self.assertEqual(created["target_kp_id"], "dmath-ch06-kp-002")

        updated = content.update(
            self.pool, "relation", created["relation_id"], {"strength": "medium"}
        )
        self.assertEqual(updated["strength"], "medium")

        with self.assertRaisesRegex(ValueError, "cannot point to itself"):
            content.update(
                self.pool, "relation", created["relation_id"],
                {"target_kp_id": "dmath-ch06-kp-001"},
            )
        with self.assertRaisesRegex(ValueError, "unsupported relation field"):
            content.update(
                self.pool, "relation", created["relation_id"], {"confidence": 0.9}
            )

        content.delete(self.pool, "relation", created["relation_id"])
        self.assertIsNone(content.get(self.pool, "relation", created["relation_id"]))

    def test_create_rejects_unknown_endpoints_and_unknown_fields(self):
        from workbench.data import content

        bad = self.relation()
        bad["target_kp_id"] = "dmath-ch06-kp-999"
        with self.assertRaisesRegex(ValueError, "unknown target knowledge point"):
            content.create(self.pool, "relation", bad)

        bad = self.relation()
        bad["relation_kind"] = "prerequisite"
        with self.assertRaisesRegex(ValueError, "unsupported relation field"):
            content.create(self.pool, "relation", bad)

    def test_symmetric_reverse_duplicate_is_rejected_but_directed_reverse_is_not(self):
        from workbench.data import content

        content.create(
            self.pool, "relation",
            self.relation(
                relation_type="contrasts", direction="symmetric", strength="medium"
            ),
        )
        with self.assertRaisesRegex(ValueError, "duplicate relation"):
            content.create(
                self.pool, "relation",
                self.relation(
                    source=2, target=1, relation_type="contrasts",
                    direction="symmetric", strength="medium",
                ),
            )

        content.create(
            self.pool, "relation",
            self.relation(source=2, target=1, relation_type="prerequisite"),
        )
        self.assertEqual(len(content.list_items(self.pool, "relation")), 2)

    def test_batch_check_is_read_only_and_reports_item_errors(self):
        from workbench.data import relations

        result = relations.check(self.pool, {
            "items": [
                {"action": "create", **self.relation()},
                {
                    "action": "create",
                    **self.relation(source=1, target=99, relation_type="applies_to"),
                },
            ]
        })

        self.assertFalse(result["valid"])
        self.assertEqual(result["items"][0]["valid"], True)
        self.assertEqual(result["items"][1]["valid"], False)
        self.assertIn("unknown target knowledge point", result["errors"][0]["message"])
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT COUNT(*) FROM knowledge_relations"
            ).fetchone()[0],
            0,
        )

    def test_batch_apply_is_atomic_when_any_item_is_invalid(self):
        from workbench.data import relations

        result = relations.apply(self.pool, {
            "items": [
                {"action": "create", **self.relation()},
                {
                    "action": "create",
                    **self.relation(source=2, target=2, relation_type="applies_to"),
                },
            ]
        })

        self.assertFalse(result["valid"])
        self.assertFalse(result["applied"])
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT COUNT(*) FROM knowledge_relations"
            ).fetchone()[0],
            0,
        )

    def test_batch_can_create_update_and_delete_in_one_transaction(self):
        from workbench.data import content, relations

        old = content.create(
            self.pool, "relation",
            self.relation(source=2, target=3, relation_type="applies_to",
                          direction="directed", strength="low"),
        )
        keep = content.create(
            self.pool, "relation",
            self.relation(source=3, target=1, relation_type="generalizes",
                          direction="directed", strength="low"),
        )

        result = relations.apply(self.pool, {
            "items": [
                {"action": "delete", "relation_id": old["relation_id"]},
                {
                    "action": "update",
                    "relation_id": keep["relation_id"],
                    "strength": "high",
                },
                {
                    "action": "create",
                    **self.relation(source=1, target=2, relation_type="prerequisite",
                                   direction="directed", strength="high"),
                },
            ]
        })

        self.assertTrue(result["valid"])
        self.assertTrue(result["applied"])
        self.assertEqual(result["counts"], {"create": 1, "update": 1, "delete": 1})
        rows = content.list_items(self.pool, "relation")
        self.assertEqual(len(rows), 2)
        self.assertNotIn(old["relation_id"], {row["relation_id"] for row in rows})
        self.assertEqual(
            content.get(self.pool, "relation", keep["relation_id"])["strength"], "high"
        )
        created_ids = [
            item["relation_id"] for item in result["items"]
            if item["action"] == "create"
        ]
        self.assertEqual(len(created_ids), 1)

    def test_batch_rejects_manifest_internal_conflicts(self):
        from workbench.data import relations

        result = relations.check(self.pool, {
            "items": [
                {
                    "action": "create",
                    **self.relation(
                        relation_type="contrasts", direction="symmetric",
                        strength="medium",
                    ),
                },
                {
                    "action": "create",
                    **self.relation(
                        source=2, target=1, relation_type="contrasts",
                        direction="symmetric", strength="medium",
                    ),
                },
            ]
        })
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 2)
        self.assertTrue(all("duplicate relation" in error["message"]
                            for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
