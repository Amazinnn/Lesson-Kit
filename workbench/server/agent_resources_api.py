"""Thin settings API over user-level Agent resources."""

from workbench import agent_resources
from workbench.server.api import ApiError


def _call(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except KeyError as exc:
        raise ApiError(404, 'Skill not found') from exc
    except (ValueError, OSError) as exc:
        raise ApiError(400, str(exc)) from exc


def get(pool, workspace, params, body):
    return _call(agent_resources.snapshot)


def update(pool, workspace, params, body):
    if not isinstance(body, dict) or set(body) != {'instructions'}:
        raise ApiError(400, 'Expected instructions')
    return _call(agent_resources.save_instructions, body['instructions'])


def create(pool, workspace, params, body):
    if not isinstance(body, dict) or not set(body) <= {'source_path', 'replace'}:
        raise ApiError(400, 'Expected source_path and optional replace')
    return _call(agent_resources.import_skill, body.get('source_path'), replace=body.get('replace', False))


def detail(pool, workspace, params, body):
    return _call(agent_resources.detail, params['skill_id'])


def enable(pool, workspace, params, body):
    if not isinstance(body, dict) or set(body) != {'enabled'}:
        raise ApiError(400, 'Expected enabled')
    return _call(agent_resources.set_enabled, params['skill_id'], body['enabled'])


def delete(pool, workspace, params, body):
    return _call(agent_resources.delete_skill, params['skill_id'])
