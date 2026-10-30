"""Stable runtime supervisor; all children import the explicitly selected checkout."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import tempfile
from urllib.request import Request, urlopen
from urllib.error import URLError

from workbench.cli import runtime_source, service


def child_env(root):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(root) + os.pathsep + env.get('PYTHONPATH', '')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPYCACHEPREFIX'] = str(Path(tempfile.gettempdir()) / ('lessonkit-runtime-' + secrets.token_hex(8)))
    return env


def request(port, path='', token=None, payload=None):
    data = None if token is None else json.dumps(payload or {}).encode()
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-LessonKit-Runtime'] = token
    with urlopen(Request(f'http://127.0.0.1:{port}/api/runtime{path}', data=data,
                         headers=headers), timeout=None if token else 3) as response:
        return json.load(response)


def preflight(root):
    error = runtime_source.syntax_error(root)
    if error:
        return error
    result = subprocess.run([sys.executable, '-B', '-c',
        'from workbench.server import app; from workbench.cli import main'],
        cwd=root, env=child_env(root), capture_output=True, text=True,
        creationflags=0x08000000 if os.name == 'nt' else 0)
    return result.stderr.strip()[-2000:] if result.returncode else None


def run(port, root, reload_enabled=True):
    root = Path(root).resolve()
    token = secrets.token_urlsafe(24)
    state = dict(source_root=str(root), supervisor_pid=os.getpid(), worker_pid=None,
                 port=port, reload_enabled=reload_enabled, generation=1,
                 assets_generation=1, pending=None, error=None)
    child = None

    def spawn():
        env = child_env(root)
        env.update(LESSONKIT_RUNTIME_WORKER='1', LESSONKIT_RUNTIME_TOKEN=token,
                   LESSONKIT_RUNTIME_STATE=json.dumps(state))
        process = subprocess.Popen([sys.executable, '-B', '-m', 'workbench.cli.main',
            'serve', '--port', str(port), '--project-root', str(root)],
            cwd=root, env=env, creationflags=0x08000000 if os.name == 'nt' else 0)
        deadline = time.monotonic() + 20
        while process.poll() is None and time.monotonic() < deadline:
            try:
                observed = request(port)
                if observed['worker_pid'] == process.pid:
                    state['worker_pid'] = process.pid
                    service.write_state(dict(state, pid=os.getpid(), token=token))
                    return process
            except (URLError, OSError):
                pass
            time.sleep(.1)
        process.terminate()
        process.wait()
        raise RuntimeError('runtime worker failed startup')

    try:
        applied = candidate = runtime_source.snapshot(root)
        child = spawn()
        failed = None
        while child.poll() is None:
            time.sleep(.5)
            if not reload_enabled:
                continue
            current = runtime_source.snapshot(root)
            if current != candidate:
                candidate = current
                continue
            kind = runtime_source.changed_kind(applied, current)
            if not kind or failed == current:
                continue
            state.update(pending=kind, error=None)
            request(port, '/state', token, state)
            if kind == 'python':
                error = preflight(root)
                if error:
                    state.update(pending=None, error=error)
                    request(port, '/state', token, state)
                    failed = current
                    continue
                if runtime_source.snapshot(root) != current:
                    continue
            if not request(port, '/prepare-reload', token)['ready']:
                state['pending'] = 'busy'
                request(port, '/state', token, state)
                continue
            if kind == 'assets':
                state.update(assets_generation=state['assets_generation'] + 1, pending=None)
                request(port, '/state', token, state)
                request(port, '/resume', token)
            else:
                request(port, '/shutdown', token)
                child.wait()  # EVERY admitted handler has completed before listener exits
                state.update(generation=state['generation'] + 1, pending=None)
                child = spawn()
            applied = current
    except KeyboardInterrupt:
        if child and child.poll() is None:
            while not request(port, '/prepare-reload', token)['ready']:
                time.sleep(.5)
            request(port, '/shutdown', token)
            child.wait()
    finally:
        if child and child.poll() is None:
            # Even an orchestration error must not abort admitted learner work.
            while child.poll() is None:
                try:
                    if request(port, '/prepare-reload', token)['ready']:
                        request(port, '/shutdown', token)
                        child.wait()
                        break
                except OSError:
                    pass
                time.sleep(.5)
        if service.read_state().get('pid') == os.getpid():
            service.clear_state()
