"""Shared test fixtures for workbench tests."""

import importlib.util
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FAKE_PROVIDER = """\
import os
result = \"\"\"# Explain

## 结论

The product rule counts ordered pairs.

## 逐步拆解

Step one then step two.

## 易错点

Independence is required.

## 回源指向

Rosen, Discrete Mathematics, section 6.1.
\"\"\"
with open(os.environ["LESSONKIT_OUTPUT_PATH"], "w", encoding="utf-8") as f:
    f.write(result)
"""


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_fixture_db(conn):
    conn.executescript(
        """
        CREATE TABLE knowledge_points (
            kp_id TEXT PRIMARY KEY,
            knowledge_item TEXT NOT NULL,
            body TEXT,
            knowledge_type TEXT,
            importance TEXT
        );
        CREATE TABLE problems (
            problem_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            problem_type TEXT,
            source_kind TEXT,
            practice_modes TEXT,
            micro_quiz TEXT
        );
        CREATE TABLE problem_progress (
            problem_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'new',
            note TEXT,
            updated_at TEXT
        );
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN (
                'new', 'wrong', 'stuck', 'reviewing', 'mastered'
            )),
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE candidate_problems (
            candidate_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            status TEXT NOT NULL,
            structure_gate_status TEXT NOT NULL DEFAULT 'pending',
            audit_gate_status TEXT NOT NULL DEFAULT 'pending'
        );
        CREATE TABLE learner_signals (
            signal_id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            weight TEXT NOT NULL DEFAULT 'medium',
            evidence_count INTEGER NOT NULL DEFAULT 1,
            note TEXT
        );
        CREATE TABLE knowledge_relations (
            relation_id TEXT PRIMARY KEY,
            source_kp_id TEXT NOT NULL,
            target_kp_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            strength TEXT NOT NULL
        );
        """
    )
    pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))
    pool_schema.ensure_workbench_schema(conn)
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body, knowledge_type, importance)"
        " VALUES (?, ?, ?, ?, ?)",
        ("dmath-ch06-kp-001", "Counting", "", "concept-property", "core"),
    )
    conn.execute(
        "INSERT INTO problems"
        " (problem_id, kp_ids, problem_text, solution, problem_type, source_kind)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "P1", "S1", "calculation", "textbook"),
    )
    conn.commit()


class WorkspaceFixture:
    """Temporary workspace with a fixture pool and a registered entry."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "dmath"
        (self.ws / "pool").mkdir(parents=True)
        self.db_path = self.ws / "pool" / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        build_fixture_db(conn)
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from registry import register
        register(str(self.ws), course="dmath", chapter="ch06")

    def cleanup(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    def add_workspace(self, name, course="dmath", chapter="ch06"):
        """Register another isolated fixture workspace for switching tests."""
        ws = Path(self.tmp.name) / name
        (ws / "pool").mkdir(parents=True)
        conn = sqlite3.connect(ws / "pool" / "dmath.db")
        build_fixture_db(conn)
        conn.close()
        from registry import register
        register(str(ws), course=course, chapter=chapter)
        return ws
