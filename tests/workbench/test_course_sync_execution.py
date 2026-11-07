"""Exercise portable drafts through the existing Paper and draft writers."""

import shutil
import sqlite3

import pytest

from tests.workbench.fixtures import build_fixture_db
from workbench.data import active_practice, course_sync, paper_progress, practice_sets
from workbench.data.pool import Pool
from workbench.domain.course_sync import plan_exchange


@pytest.fixture
def execution(tmp_path, monkeypatch):
    monkeypatch.setenv('LESSONKIT_WB_HOME', str(tmp_path / 'registry-a'))
    root = tmp_path / 'course-a'
    root.mkdir()
    database = root / 'course.db'
    connection = sqlite3.connect(database)
    try:
        build_fixture_db(connection)
        connection.execute("INSERT INTO problems (problem_id,kp_ids,problem_text,solution,problem_type,source_kind) "
                           "VALUES (?,?,?,?,?,?)", ('dmath-ch06-prob-002', '["dmath-ch06-kp-001"]',
                                                  '第二题', '$x=2$', 'calculation', 'textbook'))
        connection.commit()
    finally:
        connection.close()
    pool = Pool(root, database, 'dmath', 'ch06')
    paper = practice_sets.create_saved(pool, '共同试卷', ['dmath-ch06-prob-001', 'dmath-ch06-prob-002'])
    current = active_practice.start_saved(pool, paper['practice_set_id'],
                                          practice_mode='problem', rating_mode='self', reveal_timing='on_submit')
    yield pool, paper, current
    pool.close()


def test_different_question_edits_do_not_conflict_across_device_exports(execution, tmp_path, monkeypatch):
    pool, paper, current = execution
    course_sync.export_course(pool, {}, tmp_path / 'initial')
    initial = course_sync.read_exchange(tmp_path / 'initial')
    pool.close()
    other_root = tmp_path / 'course-b'
    shutil.copytree(pool.root, other_root)
    other = Pool(other_root, other_root / 'course.db', 'dmath', 'ch06')
    try:
        active_practice.save_draft(pool, current['execution_id'], 0,
                                   {'answer': '设备 A 的原文\n$x=1$', 'reference_viewed': True})
        course_sync.export_course(pool, {}, tmp_path / 'a')
        monkeypatch.setenv('LESSONKIT_WB_HOME', str(tmp_path / 'registry-b'))
        active_practice.save_draft(other, current['execution_id'], 1, {'answer': '设备 B 的原文'})
        course_sync.export_course(other, {}, tmp_path / 'b')
    finally:
        other.close()
    local = course_sync.read_exchange(tmp_path / 'a')['assets']
    incoming = course_sync.read_exchange(tmp_path / 'b')['assets']
    plan = plan_exchange(initial['assets'], local, incoming)
    assert plan['conflicts'] == []
    assert plan['errors'] == []
    assert len(plan['changes']) == 1
    assert len(plan['outgoing']) == 1
    assert plan['changes'][0]['asset']['content']['draft']['answer'] == '设备 B 的原文'
    assert plan['outgoing'][0]['asset']['content']['draft']['answer'] == '设备 A 的原文\n$x=1$'
    assert plan['outgoing'][0]['asset']['content']['draft']['reference_viewed'] is True


def test_clear_generation_explicitly_tombstones_old_execution(execution, tmp_path):
    pool, paper, current = execution
    active_practice.save_draft(pool, current['execution_id'], 0, {'answer': '待清除草稿'})
    course_sync.export_course(pool, {}, tmp_path / 'before')
    with pool.transaction():
        paper_progress.reset(pool, paper['practice_set_id'])
    course_sync.export_course(pool, {}, tmp_path / 'after')
    package = course_sync.read_exchange(tmp_path / 'after')
    executions = [asset for asset in package['assets'].values()
                  if asset['kind'] in {'execution', 'execution_item'}]
    assert len(executions) == 3
    assert all(asset['deleted'] is True for asset in executions)


def test_parked_and_selected_papers_share_the_execution_projection(execution, tmp_path):
    pool, first, current = execution
    active_practice.save_draft(pool, current['execution_id'], 0, {'answer': '暂停后仍保留'})
    second = practice_sets.create_saved(pool, '第二卷', ['dmath-ch06-prob-002'])
    active_practice.start_saved(pool, second['practice_set_id'], practice_mode='problem', rating_mode='self')
    course_sync.export_course(pool, {}, tmp_path / 'bundle')
    assets = course_sync.read_exchange(tmp_path / 'bundle')['assets'].values()
    headers = [asset for asset in assets if asset['kind'] == 'execution']
    assert len(headers) == 2
    assert sum(asset['presentation']['selected'] for asset in headers) == 1
    assert not any(asset['kind'] == 'row' and asset['content']['table'] in
                   {'active_practice', 'active_practice_items'} for asset in assets)
    first_item = next(asset for asset in assets if asset['kind'] == 'execution_item'
                      and asset['content']['paper_id'] == first['practice_set_id']
                      and asset['content']['position'] == 0)
    assert first_item['content']['draft']['answer'] == '暂停后仍保留'
