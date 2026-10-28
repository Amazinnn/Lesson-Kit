"""User-owned instructions and copied Skill files; no provider-global writes."""

from collections import Counter
from contextlib import contextmanager
from importlib import resources
import json
from pathlib import Path
import re
import shutil
import tempfile
import threading

from workbench import registry

_LOCK = threading.RLock()
_LEASES = Counter()
_RETIRED = set()
BUILTIN_ID = 'source-bounded-learning-drill'


def _load():
    return registry._load_json(registry.base_dir() / 'agent-resources.json',
                               {'generation': 0, 'instructions': '', 'skills': {}, 'builtin_enabled': True})


def _save(config):
    root = registry.base_dir()
    root.mkdir(parents=True, exist_ok=True)
    config['generation'] += 1
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=root, delete=False) as stream:
        json.dump(config, stream, ensure_ascii=False, indent=2)
        staged = Path(stream.name)
    try:
        staged.replace(root / 'agent-resources.json')
    finally:
        staged.unlink(missing_ok=True)


def _metadata(entry):
    text = entry.read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    metadata = {}
    if lines and lines[0].strip() == '---':
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == '---')
        except StopIteration:
            raise ValueError('Skill YAML header must end with ---') from None
        index = 1
        while index < end:
            match = re.match(r'^(name|description):\s*(.*)$', lines[index])
            if match:
                key, value = match.groups()
                if value in ('>', '|', '>-', '|-'):
                    parts = []
                    while index + 1 < end and (not lines[index + 1].strip() or lines[index + 1][:1].isspace()):
                        index += 1
                        parts.append(lines[index].strip())
                    value = ' '.join(parts).strip()
                elif len(value) >= 2 and value[0] == value[-1] and value[0] in '\"\'':
                    value = value[1:-1]
                metadata[key] = value
            index += 1
        lines = lines[end + 1:]
    heading = next((line.lstrip('#').strip() for line in lines if line.startswith('#')), entry.stem)
    prose = next((line.strip() for line in lines if line.strip() and not line.startswith('#')), '')
    name = metadata.get('name') or heading
    description = metadata.get('description') or prose
    if not name.strip() or not description.strip():
        raise ValueError('Skill needs a name/heading and a description/prose paragraph')
    return name, description


def snapshot():
    with _LOCK:
        config = _load()
        entry = Path(str(resources.files('workbench').joinpath('resources', 'skills', BUILTIN_ID, 'SKILL.md')))
        name, description = _metadata(entry)
        builtin = dict(id=BUILTIN_ID, name=name, description=description, entry=str(entry.resolve()),
                       enabled=config['builtin_enabled'], builtin=True)
        return dict(generation=config['generation'], instructions=config['instructions'],
                    skills=[builtin, *config['skills'].values()])


def enabled():
    return [item for item in snapshot()['skills'] if item['enabled']]


def save_instructions(text):
    if not isinstance(text, str):
        raise ValueError('instructions must be text')
    with _LOCK:
        config = _load()
        config['instructions'] = text
        _save(config)
    return snapshot()


def detail(skill_id):
    with _LOCK:
        item = next((x for x in snapshot()['skills'] if x['id'] == skill_id), None)
        if item is None:
            raise KeyError(skill_id)
        return {**item, 'body': Path(item['entry']).read_text(encoding='utf-8-sig')}


def _retire(folder):
    folder = folder.resolve()
    owned = (registry.base_dir() / 'managed-skills').resolve()
    if folder == owned or not folder.is_relative_to(owned):
        raise ValueError('Skill deletion must stay inside the managed directory')
    if _LEASES[str(folder)]:
        _RETIRED.add(str(folder))
    else:
        shutil.rmtree(folder)


def import_skill(source_path, *, replace=False):
    if not isinstance(source_path, str) or not source_path.strip() or not isinstance(replace, bool):
        raise ValueError('source_path and boolean replace are required')
    source = Path(source_path).expanduser()
    if source.is_symlink() or getattr(source, 'is_junction', lambda: False)():
        raise ValueError('Skill symlinks are not supported')
    source = source.resolve()
    owned = (registry.base_dir() / 'managed-skills').resolve()
    builtin_root = Path(str(resources.files('workbench').joinpath('resources', 'skills'))).resolve()
    if source.is_relative_to(owned) or owned.is_relative_to(source) or source.is_relative_to(builtin_root):
        raise ValueError('Import an original source outside managed and built-in Skill directories')
    entry = source / 'SKILL.md' if source.is_dir() else source
    if not entry.is_file() or entry.suffix.lower() != '.md':
        raise ValueError('Expected a Markdown file or a directory containing SKILL.md')
    if source.is_dir() and any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in source.rglob('*')):
        raise ValueError('Skill links are not supported')
    name, description = _metadata(entry)
    skill_id = name if registry.IDENTIFIER.fullmatch(name) else source.stem.lower()
    if not registry.IDENTIFIER.fullmatch(skill_id):
        raise ValueError('Use an ASCII kebab-case filename/directory or YAML name for the Skill id')
    if skill_id == BUILTIN_ID:
        raise ValueError('Cannot replace built-in Skill files')
    with _LOCK:
        config = _load()
        previous = config['skills'].get(skill_id)
        if previous and not replace:
            raise ValueError('Skill already exists; explicitly replace it')
        owned.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix=skill_id + '-', dir=owned))
        try:
            if source.is_dir():
                shutil.copytree(source, folder, dirs_exist_ok=True)
                copied_entry = folder / 'SKILL.md'
            else:
                copied_entry = folder / source.name
                shutil.copy2(source, copied_entry)
            item = dict(id=skill_id, name=name, description=description, entry=str(copied_entry.resolve()),
                        enabled=previous['enabled'] if previous else True, builtin=False, source=str(source),
                        native_pi=bool(registry.IDENTIFIER.fullmatch(name))
                        and entry.read_text(encoding='utf-8-sig').startswith('---')
                        and bool(re.search(r'^name:\s*\S', entry.read_text(encoding='utf-8-sig'), re.M))
                        and bool(re.search(r'^description:\s*\S', entry.read_text(encoding='utf-8-sig'), re.M)))
            config['skills'][skill_id] = item
            _save(config)
        except Exception:
            shutil.rmtree(folder)
            raise
        if previous:
            _retire(Path(previous['entry']).parent)
        return item


def set_enabled(skill_id, value):
    if not isinstance(value, bool):
        raise ValueError('enabled must be boolean')
    with _LOCK:
        config = _load()
        if skill_id == BUILTIN_ID:
            config['builtin_enabled'] = value
        elif skill_id in config['skills']:
            config['skills'][skill_id]['enabled'] = value
        else:
            raise KeyError(skill_id)
        _save(config)
    return snapshot()


def delete_skill(skill_id):
    with _LOCK:
        if skill_id == BUILTIN_ID:
            raise ValueError('Built-in Skills can be disabled, not deleted')
        config = _load()
        item = config['skills'].pop(skill_id)
        _save(config)
        _retire(Path(item['entry']).parent)
    return snapshot()


@contextmanager
def acquire():
    """Keep immutable Skill files available through an accepted running turn."""
    with _LOCK:
        data = snapshot()
        folders = [str(Path(x['entry']).parent) for x in data['skills'] if x['enabled'] and not x['builtin']]
        _LEASES.update(folders)
    try:
        yield data
    finally:
        with _LOCK:
            for folder in folders:
                _LEASES[folder] -= 1
                if not _LEASES[folder] and folder in _RETIRED:
                    shutil.rmtree(folder)
                    _RETIRED.remove(folder)
