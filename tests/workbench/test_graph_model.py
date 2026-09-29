"""Knowledge-graph data must preserve stored relation semantics."""

import importlib.util
import json
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


pool_schema = load_script("graph_model_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script(
    "graph_model_create_tables", Path("pipeline/scripts/create-tables.py")
)


class GraphModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        rows = [
            ("dmath-ch06-kp-001", "A", ["dmath-ch06-kp-002", "dmath-ch06-kp-003"]),
            ("dmath-ch06-kp-002", "B", ["dmath-ch06-kp-001"]),
            ("dmath-ch06-kp-003", "C", []),
        ]
        for kp_id, title, related in rows:
            conn.execute(
                "INSERT INTO knowledge_points "
                "(kp_id, knowledge_item, knowledge_type, importance, related_kp_ids) "
                "VALUES (?, ?, 'concept-property', 'core', ?)",
                (kp_id, title, json.dumps(related)),
            )
        relations = [
            ("dmath-ch06-rel-001", "dmath-ch06-kp-001", "dmath-ch06-kp-002",
             "prerequisite", "directed", "high"),
            ("dmath-ch06-rel-002", "dmath-ch06-kp-001", "dmath-ch06-kp-002",
             "applies_to", "directed", "medium"),
            ("dmath-ch06-rel-003", "dmath-ch06-kp-002", "dmath-ch06-kp-001",
             "prerequisite", "directed", "low"),
        ]
        conn.executemany(
            "INSERT INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            relations,
        )
        conn.commit()
        conn.close()

        from workbench.data.pool import Pool
        self.pool = Pool(self.tmp.name, self.db_path, "dmath", "ch06")

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_formal_relations_keep_id_direction_and_multiple_edges(self):
        from workbench.data import queries

        model = queries.graph_model(self.pool)
        formal = [edge for edge in model["edges"]
                  if not edge["id"].startswith("legacy:")]

        self.assertEqual(len(formal), 3)
        by_id = {edge["id"]: edge for edge in formal}
        self.assertEqual(
            (by_id["dmath-ch06-rel-001"]["source"],
             by_id["dmath-ch06-rel-001"]["target"]),
            ("dmath-ch06-kp-001", "dmath-ch06-kp-002"),
        )
        self.assertEqual(by_id["dmath-ch06-rel-001"]["direction"], "directed")
        self.assertEqual(by_id["dmath-ch06-rel-001"]["relation_type"], "prerequisite")
        self.assertEqual(by_id["dmath-ch06-rel-001"]["strength"], "high")
        self.assertEqual(
            (by_id["dmath-ch06-rel-003"]["source"],
             by_id["dmath-ch06-rel-003"]["target"]),
            ("dmath-ch06-kp-002", "dmath-ch06-kp-001"),
        )
        pair = [
            edge for edge in formal
            if edge["source"] == "dmath-ch06-kp-001"
            and edge["target"] == "dmath-ch06-kp-002"
        ]
        self.assertEqual(
            {edge["relation_type"] for edge in pair},
            {"prerequisite", "applies_to"},
        )

    def test_legacy_related_is_only_a_fallback_for_pairs_without_formal_relations(self):
        from workbench.data import queries

        model = queries.graph_model(self.pool)
        legacy = [edge for edge in model["edges"]
                  if edge["id"].startswith("legacy:")]

        self.assertEqual(len(legacy), 1)
        self.assertEqual(
            {legacy[0]["source"], legacy[0]["target"]},
            {"dmath-ch06-kp-001", "dmath-ch06-kp-003"},
        )
        self.assertEqual(legacy[0]["relation_type"], "related")
        self.assertEqual(legacy[0]["direction"], "symmetric")
        self.assertEqual(legacy[0]["strength"], "low")
        self.assertFalse(any(
            {edge["source"], edge["target"]}
            == {"dmath-ch06-kp-001", "dmath-ch06-kp-002"}
            for edge in legacy
        ))


if __name__ == "__main__":
    unittest.main()
