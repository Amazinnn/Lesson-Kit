import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POOL_SCRIPT_DIR = REPO_ROOT / "pool" / "scripts"
if str(POOL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(POOL_SCRIPT_DIR))


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))
course_network = load_script("course_network", Path("pool/scripts/course_network.py"))
insert_relations = load_script(
    "insert_knowledge_relations",
    Path("pipeline/scripts/insert-knowledge-relations.py"),
)
query_focus_map = load_script("query_focus_map", Path("pool/scripts/query-focus-map.py"))


class CourseNetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        self.conn = sqlite3.connect(self.db_path)
        self.create_base_tables()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def create_base_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT NOT NULL,
                graph_label TEXT,
                source_location TEXT,
                knowledge_type TEXT,
                related_kp_ids TEXT,
                importance TEXT,
                learning_action TEXT,
                body TEXT,
                difficulty INTEGER,
                fragile TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT,
                problem_type TEXT NOT NULL,
                source_kind TEXT NOT NULL
            );
            CREATE TABLE kp_progress (
                kp_id TEXT PRIMARY KEY,
                mastery_state TEXT
            );
            CREATE TABLE problem_progress (
                problem_id TEXT PRIMARY KEY,
                status TEXT,
                note TEXT,
                updated_at TEXT
            );
            """
        )
        rows = [
            (
                "dmath-ch06-kp-001",
                "乘法规则",
                "乘法规则",
                "Section 6.1",
                "concept-property",
                '["dmath-ch06-kp-002"]',
                "core",
                "practice",
                "Stage choices multiply.",
                1,
                "",
            ),
            (
                "dmath-ch06-kp-002",
                "加法规则",
                "加法规则",
                "Section 6.1",
                "concept-property",
                "[]",
                "core",
                "practice",
                "Disjoint alternatives add.",
                1,
                "",
            ),
            (
                "dmath-ch06-kp-003",
                "二项式定理",
                "二项式",
                "Section 6.4",
                "formula-calculation",
                "[]",
                "core",
                "derive",
                "$$ (x + y)^n = \\sum_k \\binom{n}{k} x^k y^{n-k} $$",
                3,
                "coefficient extraction",
            ),
            (
                "dmath-ch06-kp-004",
                "容斥原理",
                "容斥",
                "Section 6.5",
                "method-modeling",
                "[]",
                "supplementary",
                "compare",
                "Avoid overlap.",
                3,
                "",
            ),
            (
                "dmath-ch06-kp-005",
                "鸽巢原理",
                "鸽巢",
                "Section 6.6",
                "method-modeling",
                "[]",
                "supplementary",
                "prove",
                "Existence by pressure.",
                2,
                "",
            ),
        ]
        self.conn.executemany(
            "INSERT INTO knowledge_points VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        self.conn.executemany(
            "INSERT INTO problems VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    "dmath-ch06-prob-001",
                    '["dmath-ch06-kp-003"]',
                    "Find a coefficient.",
                    "solution must not leak",
                    "calculation",
                    "textbook",
                ),
                (
                    "dmath-ch06-prob-002",
                    '["dmath-ch06-kp-001", "dmath-ch06-kp-002"]',
                    "Count staged alternatives.",
                    "another hidden solution",
                    "calculation",
                    "quiz",
                ),
            ],
        )
        self.conn.execute(
            "INSERT INTO problem_progress VALUES (?, ?, ?, ?)",
            ("dmath-ch06-prob-001", "wrong", "missed coefficient model", "2026-01-01"),
        )
        self.conn.commit()

    def write_manifest(self, relations):
        path = self.root / "relation-insert-manifest.json"
        path.write_text(json.dumps({"relations": relations}, ensure_ascii=False), encoding="utf-8")
        return path

    def test_legacy_related_ids_are_used_when_relation_table_is_absent(self):
        nodes = course_network.fetch_knowledge_nodes(self.conn, "dmath", "ch06")
        relations = course_network.fetch_knowledge_relations(self.conn, nodes)

        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]["source"], "dmath-ch06-kp-001")
        self.assertEqual(relations[0]["target"], "dmath-ch06-kp-002")
        self.assertTrue(relations[0]["fallback"])

    def test_relation_manifest_insert_and_focus_path(self):
        manifest = self.write_manifest(
            [
                {
                    "relation_id": "rel:001-prereq-002",
                    "source_kp_id": "dmath-ch06-kp-001",
                    "target_kp_id": "dmath-ch06-kp-002",
                    "relation_type": "prerequisite",
                    "direction": "directed",
                    "strength": "high",
                },
                {
                    "relation_id": "rel:002-applies-003",
                    "source_kp_id": "dmath-ch06-kp-002",
                    "target_kp_id": "dmath-ch06-kp-003",
                    "relation_type": "applies_to",
                    "direction": "directed",
                    "strength": "medium",
                },
            ]
        )

        inserted, skipped, errors = insert_relations.insert_relations(
            str(self.db_path),
            str(manifest),
            strict=True,
        )
        self.assertEqual((inserted, skipped, errors), (2, 0, []))

        packet = query_focus_map.build_focus_map(
            self.conn,
            course="dmath",
            chapter="ch06",
            seed_ids=["dmath-ch06-kp-001"],
            target_id="dmath-ch06-kp-003",
            depth=1,
            max_nodes=10,
            directed=False,
        )

        self.assertTrue(packet["meta"]["uses_formal_relations"])
        self.assertEqual(packet["paths"][0]["node_ids"], [
            "dmath-ch06-kp-001",
            "dmath-ch06-kp-002",
            "dmath-ch06-kp-003",
        ])
        self.assertIn("path_found", {finding["type"] for finding in packet["findings"]})
        self.assertNotIn("solution must not leak", json.dumps(packet, ensure_ascii=False))
        self.assertNotIn("another hidden solution", json.dumps(packet, ensure_ascii=False))

    def test_symmetric_relations_canonicalize_and_shared_neighbor_is_reported(self):
        manifest = self.write_manifest(
            [
                {
                    "source_kp_id": "dmath-ch06-kp-002",
                    "target_kp_id": "dmath-ch06-kp-001",
                    "relation_type": "variant_of",
                    "direction": "symmetric",
                    "strength": "medium",
                },
                {
                    "source_kp_id": "dmath-ch06-kp-003",
                    "target_kp_id": "dmath-ch06-kp-002",
                    "relation_type": "variant_of",
                    "direction": "symmetric",
                    "strength": "medium",
                },
            ]
        )
        inserted, _skipped, errors = insert_relations.insert_relations(
            str(self.db_path),
            str(manifest),
            strict=True,
        )
        self.assertEqual(inserted, 2)
        self.assertEqual(errors, [])

        rows = self.conn.execute(
            "SELECT source_kp_id, target_kp_id FROM knowledge_relations ORDER BY relation_id"
        ).fetchall()
        self.assertIn(("dmath-ch06-kp-001", "dmath-ch06-kp-002"), rows)
        self.assertIn(("dmath-ch06-kp-002", "dmath-ch06-kp-003"), rows)

        packet = query_focus_map.build_focus_map(
            self.conn,
            course="dmath",
            chapter="ch06",
            seed_ids=["dmath-ch06-kp-001", "dmath-ch06-kp-003"],
            depth=1,
            max_nodes=10,
        )

        shared = [finding for finding in packet["findings"] if finding["type"] == "shared_neighbors"]
        self.assertEqual(shared[0]["items"][0]["node_id"], "dmath-ch06-kp-002")

    def test_signal_nodes_can_enter_cropped_focus_map(self):
        pool_schema.ensure_course_network_schema(self.conn)
        self.conn.commit()
        signals = [
            {
                "signal_id": "sig:005",
                "target_type": "node",
                "target_id": "dmath-ch06-kp-005",
                "signal_type": "weak_node",
                "weight": "high",
                "note": "user wants this surfaced",
                "source": "reflection",
            }
        ]

        packet = query_focus_map.build_focus_map(
            self.conn,
            course="dmath",
            chapter="ch06",
            seed_ids=["dmath-ch06-kp-001"],
            depth=1,
            max_nodes=2,
            signals=signals,
        )

        node_ids = {node["id"] for node in packet["nodes"]}
        self.assertIn("dmath-ch06-kp-001", node_ids)
        self.assertIn("dmath-ch06-kp-005", node_ids)
        self.assertIn("sig:005", {signal["signal_id"] for signal in packet["signals"]})

    def test_focus_map_loads_course_scoped_learner_signals_from_db_by_default(self):
        pool_schema.ensure_workbench_schema(self.conn)
        self.conn.execute(
            """
            INSERT INTO learner_signals (
                signal_id, target_type, target_id, signal_type, weight,
                evidence_count, note, last_practice_kind, last_practice_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "sig:db-default",
                "node",
                "dmath-ch06-kp-005",
                "weak_node",
                "high",
                2,
                "repeated miss",
                "problem",
                "dmath-ch06-prob-007",
            ),
        )
        self.conn.commit()

        packet = query_focus_map.build_focus_map(
            self.conn,
            course="dmath",
            chapter="ch06",
            seed_ids=["dmath-ch06-kp-001"],
            depth=0,
            max_nodes=2,
        )

        self.assertIn("dmath-ch06-kp-005", {node["id"] for node in packet["nodes"]})
        self.assertEqual(packet["signals"][0]["signal_id"], "sig:db-default")
        self.assertEqual(packet["signals"][0]["source"], "problem:dmath-ch06-prob-007")


if __name__ == "__main__":
    unittest.main()
