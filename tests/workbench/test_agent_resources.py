import json
from pathlib import Path

import pytest

from workbench import agent_resources as resources


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('LESSONKIT_WB_HOME', str(tmp_path / 'home'))
    return tmp_path


def test_global_instructions_are_shared_and_clearable(home):
    assert resources.snapshot()['instructions'] == ''
    resources.save_instructions('主动记录成熟经验')
    assert resources.snapshot()['instructions'] == '主动记录成熟经验'
    resources.save_instructions('')
    assert resources.snapshot()['instructions'] == ''


def test_package_copy_metadata_replacement_and_delete(home):
    source = home / 'original'
    source.mkdir()
    raw = b'---\nname: example\ndescription: >\n  Study methods\n  and examples\n---\n# Example\nBody\n'
    (source / 'SKILL.md').write_bytes(raw)
    (source / 'references').mkdir()
    (source / 'references' / 'notes.md').write_text('reference', encoding='utf-8')
    item = resources.import_skill(str(source))
    assert item['description'] == 'Study methods and examples'
    assert Path(item['entry']).read_bytes() == raw
    assert (Path(item['entry']).parent / 'references/notes.md').exists()
    with pytest.raises(ValueError, match='replace'):
        resources.import_skill(str(source))
    (source / 'SKILL.md').write_text('---\nname: example\ndescription: Changed\n---\nNew', encoding='utf-8')
    resources.import_skill(str(source), replace=True)
    assert resources.detail('example')['body'].endswith('New')
    resources.set_enabled('example', False)
    assert not any(x['id'] == 'example' for x in resources.enabled())
    resources.delete_skill('example')
    assert source.exists()
    assert not any(x['id'] == 'example' for x in resources.snapshot()['skills'])


def test_plain_markdown_and_builtin_protection(home):
    source = home / 'plain.md'
    source.write_text('# Human title\n\nUseful purpose.\n', encoding='utf-8')
    item = resources.import_skill(str(source))
    assert item['name'] == 'Human title'
    assert item['description'] == 'Useful purpose.'
    builtin = next(x for x in resources.snapshot()['skills'] if x['builtin'])
    with pytest.raises(ValueError):
        resources.delete_skill(builtin['id'])
    resources.set_enabled(builtin['id'], False)
    assert builtin['id'] not in [x['id'] for x in resources.enabled()]


def test_failed_import_retains_config_and_source(home):
    source = home / 'bad'
    source.mkdir()
    with pytest.raises(ValueError):
        resources.import_skill(str(source))
    assert source.is_dir()
    assert len(resources.snapshot()['skills']) == 1


def test_recent_exchange_filter_and_prompt(home):
    from workbench.bridge.conversations import _prompt, _continuity
    folder = home / 'conversation'
    folder.mkdir()
    exchanges = [
        {'turn_id': 'turn-001', 'user': '讲势能法', 'assistant': '可以整理闪卡并保存，需要吗？'},
        {'turn_id': 'turn-002', 'user': '好', 'assistant': 'Saved'},
        {'turn_id': 'turn-004', 'user': 'future', 'assistant': 'future'},
    ]
    (folder / 'transcript.jsonl').write_text('\n'.join(json.dumps(x) for x in exchanges), encoding='utf-8')
    for x in exchanges:
        (folder / (x['turn_id'] + '.json')).write_text(json.dumps({'status': 'done'}), encoding='utf-8')
    recent = _continuity(folder, 'turn-003')
    assert len(recent) == 2 and recent[-1]['user'] == '好'
    text = _prompt('继续', {'continuity': recent, 'agent_resources': resources.snapshot()})
    assert '对话承接' in text and '持续授权' in text
    assert '可以整理闪卡' in text and 'future' not in text


def test_running_turn_keeps_retired_files_until_release(home):
    source = home / 'retain.md'
    source.write_text('# Retain\n\nUseful description.', encoding='utf-8')
    item = resources.import_skill(str(source))
    with resources.acquire():
        resources.delete_skill(item['id'])
        assert Path(item['entry']).exists()
    assert not Path(item['entry']).exists()


def test_provider_discovery_uses_native_only_when_compatible(home):
    from workbench.bridge.conversation_providers import build_command
    source = home / 'plain.md'
    source.write_text('# Plain\n\nPurpose.', encoding='utf-8')
    item = resources.import_skill(str(source))
    managed = resources.snapshot()
    command = build_command({'name': 'pi', 'command': 'pi', 'managed_resources': managed}, 'session-1')
    assert item['entry'] not in command  # plain Markdown remains available through the prompt catalog
    assert command[-2:] == ['--session', 'session-1']
    resources.set_enabled(resources.BUILTIN_ID, False)
    command = build_command({'name': 'pi', 'command': 'pi', 'managed_resources': resources.snapshot()})
    assert '--skill' not in command


def test_management_api_validates_and_persists(home):
    from workbench.server import agent_resources_api as api
    from workbench.server.api import ApiError
    assert api.update(None, {}, {}, {'instructions': 'Global'})['instructions'] == 'Global'
    with pytest.raises(ApiError):
        api.update(None, {}, {}, {'instructions': 1})
    with pytest.raises(ApiError):
        api.enable(None, {}, {'skill_id': resources.BUILTIN_ID}, {'enabled': 'false'})
    with pytest.raises(ApiError):
        api.delete(None, {}, {'skill_id': resources.BUILTIN_ID}, None)


def test_failed_replacement_keeps_previous_bytes_and_generation(home, monkeypatch):
    source = home / 'stable.md'
    source.write_text('# Stable\n\nOriginal instructions.', encoding='utf-8')
    item = resources.import_skill(str(source))
    original = Path(item['entry']).read_bytes()
    generation = resources.snapshot()['generation']
    source.write_text('# Stable\n\nNew instructions.', encoding='utf-8')
    def fail_copy(*args, **kwargs):
        raise OSError('copy interrupted')
    monkeypatch.setattr(resources.shutil, 'copy2', fail_copy)
    with pytest.raises(OSError, match='interrupted'):
        resources.import_skill(str(source), replace=True)
    assert resources.snapshot()['generation'] == generation
    assert Path(resources.detail(item['id'])['entry']).read_bytes() == original


def test_retirement_refuses_outside_managed_root(home):
    outside = home / 'original'
    outside.mkdir()
    (outside / 'keep.txt').write_text('keep', encoding='utf-8')
    with pytest.raises(ValueError, match='inside'):
        resources._retire(outside)
    assert (outside / 'keep.txt').exists()
