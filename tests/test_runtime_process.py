"""Isolated real supervisor/worker checks; never writes to the primary checkout."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def wait_for(callback, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = callback()
            if result:
                return result
        except (OSError, ValueError):
            pass
        time.sleep(.1)
    raise AssertionError('runtime condition timed out')


def test_real_reload_invalid_edit_assets_and_stop(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    for name in ('workbench', 'pool', 'pipeline'):
        shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns('__pycache__'))
    app_path = source / 'workbench/server/app.py'
    fixture_code = app_path.read_text(encoding='utf-8').replace(
        '    def _dispatch_admitted(self, method):',
        '    def _dispatch_admitted(self, method):\n'
        '        if self.path == "/fixture/busy":\n'
        '            with conversations._LOCK: conversations._ACTIVE_TURNS.add("fixture-owner")\n'
        '            return self._send_json(200, {"ok": True})\n'
        '        if self.path == "/fixture/idle":\n'
        '            with conversations._LOCK: conversations._ACTIVE_TURNS.discard("fixture-owner")\n'
        '            return self._send_json(200, {"ok": True})')
    app_path.write_text(fixture_code, encoding='utf-8')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update(PYTHONPATH=str(source), LESSONKIT_WB_HOME=str(tmp_path / 'registry'), PYTHONDONTWRITEBYTECODE='1')
    log = (tmp_path / 'runtime.log').open('w')
    process = subprocess.Popen([sys.executable, '-B', '-m', 'workbench.cli.main', 'serve',
        '--port', str(port), '--project-root', str(source)], cwd=source, env=env, stdout=log, stderr=log)
    def metadata():
        with urlopen(f'http://127.0.0.1:{port}/api/runtime', timeout=2) as response:
            return json.load(response)
    try:
        original = wait_for(metadata)
        assert Path(original['source_root']) == source.resolve()
        assert original['supervisor_pid'] == process.pid
        bad = source / 'workbench' / 'broken_preview.py'
        with urlopen(f'http://127.0.0.1:{port}/fixture/busy') as response:
            response.read()
        bad.write_text('valid = True')
        wait_for(lambda: metadata().get('pending') == 'busy')
        assert metadata()['worker_pid'] == original['worker_pid']
        with urlopen(f'http://127.0.0.1:{port}/fixture/idle') as response:
            response.read()
        original = wait_for(lambda: (m if (m := metadata())['generation'] > original['generation'] else None))
        bad.write_text('def broken(:')
        wait_for(lambda: metadata().get('error'))
        assert metadata()['worker_pid'] == original['worker_pid']
        bad.write_text('raise RuntimeError("preflight must import modules it loads")\n')
        # A valid unrelated module is syntax-checked but deliberately not imported.
        updated = wait_for(lambda: (m if (m := metadata())['generation'] > original['generation'] else None))
        assert updated['worker_pid'] != original['worker_pid']
        asset = source / 'workbench/server/static/runtime-fixture.txt'
        asset.write_text('changed')
        wait_for(lambda: metadata()['assets_generation'] > updated['assets_generation'])
        assert metadata()['worker_pid'] == updated['worker_pid']
        from workbench.cli.runtime import request
        state = json.loads((tmp_path / 'registry/daemon.json').read_text())
        assert request(port, '/prepare-reload', state['token'])['ready']
        request(port, '/shutdown', state['token'])
        assert process.wait(timeout=15) == 0
    finally:
        if process.poll() is None:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                process.terminate()
            process.wait()
        log.close()
