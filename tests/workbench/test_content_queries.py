"""Typed knowledge queries and de-duplicated associated problems."""

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
    conn = p.connect()
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body, knowledge_type)"
        " VALUES (?, ?, ?, ?)",
        ('dmath-ch07-kp-001', 'Induction', 'step case', 'method-model'))
    conn.execute(
        "INSERT INTO problems (problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
        " VALUES (?, ?, ?, 'solution', 'calculation', 'textbook')",
        ('dmath-ch06-prob-002', '["dmath-ch06-kp-001"]', 'question 2'))
    conn.execute(
        "INSERT INTO problems (problem_id,kp_ids,problem_text,solution,problem_type,source_kind)"
        " VALUES (?, ?, ?, 'solution', 'calculation', 'textbook')",
        ('dmath-ch06-prob-003', '["dmath-ch06-kp-001","dmath-ch07-kp-001"]', 'question 3'))
    conn.execute(
        "INSERT INTO kp_experiences (kp_id, content, revision, updated_by)"
        " VALUES (?, ?, 1, 'user')", ('dmath-ch06-kp-001', '只在经验里出现的词 鸽巢'))
    p.commit()
    yield p
    p.close()
    fixture.cleanup()


def test_a_keyword_only_in_experience_finds_the_point_once(pool):
    hits = content.knowledge_query(pool, text='鸽巢')

    assert [item['kp_id'] for item in hits] == ['dmath-ch06-kp-001']


def test_type_and_chapter_narrow_the_same_query(pool):
    assert [item['kp_id'] for item in content.knowledge_query(pool, types=['method-model'])] \
        == ['dmath-ch07-kp-001']
    assert [item['kp_id'] for item in
            content.knowledge_query(pool, types=['method-model'], chapter='ch06')] == []
    assert [item['kp_id'] for item in
            content.knowledge_query(pool, chapter='ch07', text='induction')] \
        == ['dmath-ch07-kp-001']


def test_bulk_read_carries_content_and_classification(pool):
    for item in content.knowledge_query(pool):
        assert item['knowledge_type']
        assert 'knowledge_item' in item


def test_chapter_filter_uses_current_ownership_after_a_move(pool):
    connection = pool.connect()
    if 'chapter' not in {row[1] for row in connection.execute('PRAGMA table_info(knowledge_points)')}:
        connection.execute('ALTER TABLE knowledge_points ADD COLUMN chapter TEXT')
    connection.execute("UPDATE knowledge_points SET chapter='ch08' WHERE kp_id='dmath-ch07-kp-001'")
    pool.commit()
    assert [item['kp_id'] for item in content.knowledge_query(pool, chapter='ch08')] == ['dmath-ch07-kp-001']
    assert content.knowledge_query(pool, chapter='ch07') == []


def test_a_problem_with_two_matching_associations_appears_once(pool):
    problems = content.related_problems(
        pool, ['dmath-ch06-kp-001', 'dmath-ch07-kp-001'])
    ids = [item['problem_id'] for item in problems]

    assert ids == sorted(set(ids))
    assert ids == ['dmath-ch06-prob-001', 'dmath-ch06-prob-002', 'dmath-ch06-prob-003']


def test_related_problems_skips_archived_ones(pool):
    pool.connect().execute(
        "UPDATE problems SET deleted_at='2026-11-08' WHERE problem_id='dmath-ch06-prob-002'")
    pool.commit()

    ids = [item['problem_id'] for item in
           content.related_problems(pool, ['dmath-ch06-kp-001'])]
    assert 'dmath-ch06-prob-002' not in ids


def test_cli_search_narrows_knowledge_points(pool, capsys):
    from workbench.cli import main as cli_main

    code = cli_main.main(["data", "dmath", "search", "kp", "induction",
                          "--knowledge-type", "method-model", "--chapter", "ch07", "--json"])
    printed = capsys.readouterr().out

    assert code == 0
    assert 'dmath-ch07-kp-001' in printed
    assert 'dmath-ch06-kp-001' not in printed


def test_cli_related_lists_each_problem_once(pool, capsys):
    from workbench.cli import main as cli_main

    code = cli_main.main(["data", "dmath", "related", "problem",
                          "dmath-ch06-kp-001,dmath-ch07-kp-001", "--json"])
    printed = capsys.readouterr().out

    assert code == 0
    assert printed.count('dmath-ch06-prob-003') == 1


def test_a_chapter_move_keeps_the_id_and_every_reference(pool):
    conn = pool.connect()
    conn.execute(
        "INSERT INTO knowledge_relations (relation_id, source_kp_id, target_kp_id,"
        " relation_type, direction, strength) VALUES"
        " ('rel-001','dmath-ch06-kp-001','dmath-ch07-kp-001','prerequisite','forward','strong')")
    conn.execute(
        "INSERT INTO kp_experiences (kp_id, content, revision, updated_by)"
        " VALUES ('dmath-ch07-kp-001','经验正文',1,'user')")
    pool.commit()

    result = content.move_kp(pool, 'dmath-ch07-kp-001', 'ch09')

    assert result["moved"] is True and result["previous"] == "ch07"
    assert content.get(pool, "kp", "dmath-ch07-kp-001")["chapter"] == "ch09"
    assert pool.connect().execute(
        "SELECT COUNT(*) FROM knowledge_relations").fetchone()[0] == 1
    assert pool.connect().execute(
        "SELECT content FROM kp_experiences WHERE kp_id=?", ("dmath-ch07-kp-001",)
    ).fetchone()[0] == "经验正文"
    assert [item["kp_id"] for item in content.knowledge_query(pool, chapter="ch09")] \
        == ["dmath-ch07-kp-001"]
    assert [item["kp_id"] for item in content.knowledge_query(pool, chapter="ch07")] == []
    # A chapter exists only while content carries it, and the move took the only row.
    assert "ch09" in pool.chapters() and "ch07" not in pool.chapters()


def test_the_active_lens_reads_a_moved_point_in_its_new_chapter(pool):
    content.move_kp(pool, 'dmath-ch07-kp-001', 'ch06')
    moved = Pool(pool.root, pool.db_path, "dmath", "ch06")

    ids = [item["kp_id"] for item in moved.kps(moved.scope_prefix())]
    old_lens = Pool(pool.root, pool.db_path, "dmath", "ch07")

    assert 'dmath-ch07-kp-001' in ids
    assert [item["kp_id"] for item in old_lens.kps(old_lens.scope_prefix())] == []
    moved.close()
    old_lens.close()


def test_a_new_knowledge_point_gets_its_chapter_column(pool):
    created = content.create(pool, "kp", {"knowledge_item": "New", "knowledge_type":
                                          "concept-property", "importance": "core"})

    assert created["chapter"] == "ch06"
