"""The explicit successful-batch undo is retired; its history stays readable."""

import sqlite3

import pytest

from tests.workbench.fixtures import WorkspaceFixture
from workbench import ingest


@pytest.fixture
def workspace():
    fixture = WorkspaceFixture()
    yield fixture
    fixture.cleanup()


def test_ingest_rollback_is_no_longer_a_command(workspace):
    from workbench.cli import main as cli_main

    parser = cli_main.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["ingest", "rollback", "--batch", "batch-001"])


def test_a_historical_rollback_stays_readable(workspace):
    conn = sqlite3.connect(workspace.db_path)
    conn.execute(
        "INSERT INTO ingest_batches (batch_id, kind, manifest_path, counts_json,"
        " backup_path, applied_at, rolled_back_at)"
        " VALUES ('batch-old','content-patch','history/old.json','{\"problems\": 2}',"
        " 'history/old.db','2026-10-01 10:00:00','2026-10-02 11:00:00')")
    conn.commit()
    conn.close()

    batches = ingest.list_batches(workspace.db_path)

    assert [batch["batch_id"] for batch in batches] == ["batch-old"]
    assert batches[0]["rolled_back_at"] == "2026-10-02 11:00:00"
