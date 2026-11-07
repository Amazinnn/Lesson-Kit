"""Knowledge points get independent chapter ownership, backfilled from the id."""

import sqlite3
from pathlib import Path

from tests.workbench.fixtures import load_script

pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))


def _call(connection):
    return pool_schema.ensure_knowledge_chapter_schema(connection)


def _pool_with(rows):
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY, body TEXT)")
    connection.executemany("INSERT INTO knowledge_points (kp_id, body) VALUES (?, ?)", rows)
    return connection


def test_backfills_the_initial_chapter_from_the_id():
    connection = _pool_with([
        ("dmath-ch06-kp-001", "a"),
        ("dmath-ch11-kp-007", "b"),
    ])

    changes = _call(connection)

    assert {row[0] for row in connection.execute(
        "SELECT chapter FROM knowledge_points ORDER BY kp_id")} == {"ch06", "ch11"}
    assert "knowledge_points.chapter" in changes


def test_a_multi_segment_chapter_keeps_its_whole_segment():
    """The repository elsewhere reads the whole segment between course and -kp-."""
    connection = _pool_with([("dmath-source-ch03-kp-001", "a")])

    _call(connection)

    assert connection.execute("SELECT chapter FROM knowledge_points").fetchone()[0] \
        == "source-ch03"


def test_an_id_without_a_chapter_segment_is_left_null():
    connection = _pool_with([("dmath-kp-001", "a"), ("legacy-kp-001", "b")])

    _call(connection)

    assert [row[0] for row in connection.execute(
        "SELECT chapter FROM knowledge_points")] == [None, None]


def test_rerunning_keeps_an_explicit_assignment():
    connection = _pool_with([("dmath-ch06-kp-001", "a")])
    _call(connection)
    connection.execute("UPDATE knowledge_points SET chapter='ch07' WHERE kp_id='dmath-ch06-kp-001'")

    _call(connection)

    assert connection.execute("SELECT chapter FROM knowledge_points").fetchone()[0] == "ch07"
