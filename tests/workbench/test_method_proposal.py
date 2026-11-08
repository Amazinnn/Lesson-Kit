"""Practice-derived method proposals: reuse first, governed create, associations."""

import json

import pytest

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import content
from workbench.data.pool import Pool
from workbench.server import api


@pytest.fixture
def pool():
    fixture = WorkspaceFixture()
    p = api._pool_for(dict(path=str(fixture.ws), db='pool/dmath.db',
                          active_course='dmath', active_chapter='ch06'))
    yield p
    p.close()
    fixture.cleanup()


def proposal(**extra):
    base = {
        "knowledge_item": "等差数列求和公式",
        "body": "适用条件：等差数列。\n公式：Sn=n(a1+an)/2。\n步骤：确认公差、代入。",
        "knowledge_type": "formula-calculation",
        "problem_ids": [],
    }
    base.update(extra)
    return base


def test_an_absent_model_is_created_through_the_governed_path(pool):
    result = content.apply_method_proposal(pool, proposal())

    assert result["reused"] is False
    row = content.get(pool, "kp", result["kp_id"])
    assert row["knowledge_type"] == "formula-calculation"
    assert "适用条件" in row["body"]
    assert result["associations_added"] == 0


def test_equivalent_content_reuses_the_existing_identity(pool):
    created = content.apply_method_proposal(pool, proposal())

    again = content.apply_method_proposal(
        pool, proposal(knowledge_item="等差数列 求和公式！", body="换一种写法的正文"))

    assert again["reused"] is True
    assert again["kp_id"] == created["kp_id"]
    assert content.get(pool, "kp", created["kp_id"])["body"].startswith("适用条件")
    assert content.count("kp") if False else len(content.list_items(pool, "kp")) == 2


def test_reuse_extends_the_applicable_problems(pool):
    created = content.apply_method_proposal(pool, proposal())
    conn = pool.connect()
    conn.execute(
        "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
        " problem_type, source_kind)"
        " VALUES ('dmath-ch06-prob-100','[\"dmath-ch06-kp-001\"]','P','S','calculation',"
        " 'textbook')")
    pool.commit()

    again = content.apply_method_proposal(
        pool, proposal(problem_ids=["dmath-ch06-prob-100"]))

    stored = json.loads(conn.execute(
        "SELECT kp_ids FROM problems WHERE problem_id='dmath-ch06-prob-100'"
    ).fetchone()[0])
    assert again["reused"] is True
    assert stored == ["dmath-ch06-kp-001", created["kp_id"]]
    assert again["associations_added"] == 1
    assert again["problems_referenced"] == 1


def test_associations_retain_the_valid_existing_ones(pool):
    created = content.apply_method_proposal(pool, proposal())

    again = content.apply_method_proposal(
        pool, proposal(problem_ids=["dmath-ch06-prob-001"]))
    third = content.apply_method_proposal(
        pool, proposal(problem_ids=["dmath-ch06-prob-001"]))

    stored = content.get(pool, "problem", "dmath-ch06-prob-001")["kp_ids"]
    assert again["associations_added"] == 1
    assert third["associations_added"] == 0
    assert stored == ["dmath-ch06-kp-001", created["kp_id"]]


def test_an_uncertain_classification_is_not_created(pool):
    before = len(content.list_items(pool, "kp"))

    with pytest.raises(ValueError) as caught:
        content.apply_method_proposal(pool, proposal(knowledge_type=None))

    assert "uncertain classification" in str(caught.value)
    assert len(content.list_items(pool, "kp")) == before


def test_a_non_method_type_is_refused(pool):
    with pytest.raises(ValueError) as caught:
        content.apply_method_proposal(
            pool, proposal(knowledge_type="concept-property"))

    assert "reusable method" in str(caught.value)


def test_an_empty_body_is_refused(pool):
    with pytest.raises(ValueError) as caught:
        content.apply_method_proposal(pool, proposal(body="   "))

    assert "body" in str(caught.value)


def test_unknown_problems_refuse_the_whole_proposal(pool):
    before = len(content.list_items(pool, "kp"))

    with pytest.raises(ValueError) as caught:
        content.apply_method_proposal(
            pool, proposal(problem_ids=["dmath-ch06-prob-999"]))

    assert "dmath-ch06-prob-999" in str(caught.value)
    assert len(content.list_items(pool, "kp")) == before


def test_ambiguous_equivalents_demand_a_decision(pool):
    content.create(pool, "kp", {"knowledge_item": "等差求和",
                                "knowledge_type": "method-modeling",
                                "importance": "core"})
    content.create(pool, "kp", {"knowledge_item": "等差 求和",
                                "knowledge_type": "method-modeling",
                                "importance": "core"})

    with pytest.raises(ValueError) as caught:
        content.apply_method_proposal(pool, proposal(
            knowledge_item="等差求和", knowledge_type="method-modeling"))

    assert "several equivalent knowledge points" in str(caught.value)


def test_the_cli_reports_the_proposal_result(pool, capsys):
    from workbench.cli import main as cli_main
    path = pool.root.parent / "method.json"
    path.write_text(json.dumps(proposal(problem_ids=["dmath-ch06-prob-001"])),
                    encoding="utf-8")

    code = cli_main.main(["data", "dmath", "method", "kp", "--input", str(path),
                          "--json"])
    printed = capsys.readouterr().out

    assert code == 0
    assert json.loads(printed)["reused"] is False
    assert json.loads(printed)["associations_added"] == 1
