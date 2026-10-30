import threading
import time
from workbench.server.runtime import Admission


def test_prepare_waits_for_mutation_and_drains_get():
    gate = Admission()
    assert gate.enter(False)
    assert gate.enter(True)
    prepared = []
    t = threading.Thread(target=lambda: prepared.append(gate.prepare(lambda: True)))
    t.start()
    time.sleep(.05)
    assert not prepared
    assert not gate.enter(True)
    gate.leave(True)
    t.join(1)
    assert prepared == [True]
    assert not gate.enter(False)
    drained = threading.Event()
    t = threading.Thread(target=lambda: (gate.drain(), drained.set()))
    t.start()
    assert not drained.wait(.05)
    gate.leave(False)
    assert drained.wait(1)
    t.join()


def test_busy_reopens_admission():
    gate = Admission()
    assert not gate.prepare(lambda: False)
    assert gate.enter(True)
    gate.leave(True)

def test_http_held_get_drains_before_shutdown():
    from http.server import ThreadingHTTPServer
    from urllib.request import Request, urlopen
    from workbench.server import app
    from workbench.server.runtime import Admission
    import json
    import os
    from unittest.mock import patch
    entered, release = threading.Event(), threading.Event()
    class Handler(app.WorkbenchHandler):
        def _dispatch_admitted(self, method):
            entered.set()
            release.wait(5)
            self._send_json(200, {'completed': True})
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.admission = Admission()
    server.runtime = {"port": server.server_port}
    serving = threading.Thread(target=server.serve_forever)
    serving.start()
    port = server.server_port
    completed = []
    request_thread = threading.Thread(target=lambda: completed.append(json.load(urlopen(f'http://127.0.0.1:{port}/held'))))
    request_thread.start()
    assert entered.wait(2)
    with patch.dict(os.environ, LESSONKIT_RUNTIME_TOKEN='test-owner'), patch.object(app.registry, 'list_workspaces', return_value=[]):
        from workbench.cli.runtime import request
        assert request(port, '/prepare-reload', 'test-owner')['ready']
        request(port, '/shutdown', 'test-owner')
        serving.join(.1)
        assert serving.is_alive()
        release.set()
        request_thread.join(2)
        serving.join(2)
        assert completed == [{'completed': True}]
        assert not serving.is_alive()
    app.conversations.reopen_runtime_admission()
    server.server_close()

def test_bridge_retains_queued_and_approval_ownership(tmp_path):
    import json
    from workbench.bridge import conversations
    folder = tmp_path / 'conv-001'
    folder.mkdir()
    path = folder / 'turn-001.json'
    for turn in ({'status':'queued'},
                 {'status':'done','paper_approval':{'status':'pending'}}):
        path.write_text(json.dumps(turn))
        assert not conversations.prepare_runtime_reload([tmp_path])
    path.write_text(json.dumps({'status':'done'}))
    assert conversations.prepare_runtime_reload([tmp_path])
    conversations.reopen_runtime_admission()

def test_orphaned_running_and_handoff_records_do_not_block_reload(tmp_path):
    """Records left by an older dead service are recovery's business, not live work."""
    import json
    from workbench.bridge import conversations
    folder = tmp_path / 'conv-001'
    folder.mkdir()
    (folder / 'turn-001.json').write_text(json.dumps({'status':'running'}))
    (folder / 'turn-002.json').write_text(json.dumps(
        {'status':'waiting_for_stop','interrupt_target_turn_id':'turn-001'}))
    assert conversations.prepare_runtime_reload([tmp_path])
    conversations.reopen_runtime_admission()

def test_live_turn_owner_blocks_reload(tmp_path):
    import json
    from workbench.bridge import conversations
    folder = tmp_path / 'conv-001'
    folder.mkdir()
    (folder / 'turn-001.json').write_text(json.dumps({'status':'done'}))
    key = (str(folder), 'turn-001')
    conversations._ACTIVE_TURNS.add(key)
    try:
        assert not conversations.prepare_runtime_reload([tmp_path])
    finally:
        conversations._ACTIVE_TURNS.discard(key)
    assert conversations.prepare_runtime_reload([tmp_path])
    conversations.reopen_runtime_admission()
