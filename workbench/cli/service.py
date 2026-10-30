"""Background workbench service: pid state, detached start, stop, liveness."""

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from workbench import registry


STATE_FILE = "daemon.json"
LOG_FILE = "daemon.log"
START_TIMEOUT_S = 20.0
STOP_TIMEOUT_S = 10.0


def repo_root():
    return Path(__file__).resolve().parents[2]


def state_path():
    return registry.base_dir() / STATE_FILE


def log_path():
    return registry.base_dir() / LOG_FILE


def read_state():
    path = state_path()
    if not path.is_file():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return state if isinstance(state, dict) else {}


def write_state(state):
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_state():
    try:
        state_path().unlink()
    except FileNotFoundError:
        pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def process_alive(pid):
    """Liveness probe that never signals the process.

    os.kill(pid, 0) is NOT usable on Windows: it maps to TerminateProcess, so
    probing would kill the very process being probed.
    """
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        return _windows_exit_code(pid) == _STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


_STILL_ACTIVE = 259


def _windows_exit_code(pid):
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return None
        return code.value
    finally:
        kernel32.CloseHandle(handle)


def process_image(pid):
    """Executable path of a process, or "" when it cannot be determined."""
    if not process_alive(pid):
        return ""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)
            ):
                return ""
            return buffer.value
        finally:
            kernel32.CloseHandle(handle)
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.split(b"\0")[0].decode("utf-8", "replace")


def _looks_like_python(image):
    if not image:
        return False
    name = Path(image).name.lower()
    return name.startswith("python") or name.startswith("py")


def port_answers(port, host="127.0.0.1", timeout=0.5):
    if not isinstance(port, int):
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def running_state():
    """Verify listener identity; a live recycled PID is not a service."""
    from workbench.cli.runtime import request
    state = read_state()
    if not process_alive(state.get("pid")):
        return {}
    if not state.get("source_root") or not state.get("token"):
        image = process_image(state.get("pid"))
        if image and not _looks_like_python(image) and not port_answers(state.get("port")):
            clear_state()
            return {}
        raise RuntimeError("legacy service identity unverified; stop it in its original terminal")
    try:
        observed = request(state["port"])
    except (OSError, ValueError) as exc:
        raise RuntimeError("recorded service identity cannot be verified") from exc
    if any(observed.get(k) != state.get(k) for k in ("supervisor_pid", "source_root", "worker_pid")):
        raise RuntimeError("recorded service does not match the live runtime identity")
    return dict(state, **observed)


def _detach_kwargs():
    if os.name == "nt":
        return {"creationflags": 0x00000008 | 0x08000000}  # DETACHED_PROCESS | NO_WINDOW
    return {"start_new_session": True}


def start(port=3081, project_root=None, reload_enabled=True):
    from workbench.cli import runtime, runtime_source
    root = runtime_source.project_root(project_root)
    state = running_state()
    if state:
        if Path(state["source_root"]) != root or state["port"] != port or state["reload_enabled"] != reload_enabled:
            raise RuntimeError("running service source/port/reload differs; stop it safely before switching")
        return {"started": False, "already_running": True, "pid": state.get("pid"),
                "port": state.get("port"), "log": str(log_path())}
    if port_answers(port):
        raise RuntimeError(f"port {port} already answers but is not a recorded service")
    clear_state()
    log = log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "ab") as stream:
        process = subprocess.Popen(
            [sys.executable, "-B", "-m", "workbench.cli.main", "serve", "--port", str(port),
             "--project-root", str(root)] + ([] if reload_enabled else ["--no-reload"]),
            cwd=str(root), env=runtime.child_env(root),
            stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
            **_detach_kwargs(),
        )
    deadline = time.time() + START_TIMEOUT_S
    while time.time() < deadline:
        if port_answers(port) and read_state().get("pid") == process.pid:
            break
        if process.poll() is not None:
            raise RuntimeError(
                f"service exited with code {process.returncode}; see {log}"
            )
        time.sleep(0.2)
    else:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            process.terminate()
        raise RuntimeError(f"service did not answer on port {port}; see {log}")
    state = read_state()
    return {"started": True, "already_running": False, "pid": state["pid"],
            "port": state["port"], "log": str(log)}


def stop():
    from workbench.cli.runtime import request
    state = running_state()
    if not state:
        clear_state()
        return {"stopped": False, "was_running": False, "log": str(log_path())}
    if not request(state["port"], "/prepare-reload", state["token"])["ready"]:
        raise RuntimeError("Agent work or queued/approval work is active; stop deferred")
    request(state["port"], "/shutdown", state["token"])
    deadline = time.monotonic() + STOP_TIMEOUT_S
    while time.monotonic() < deadline and process_alive(state["pid"]):
        time.sleep(.1)
    if process_alive(state["pid"]):
        raise RuntimeError("runtime is draining existing requests; stop remains pending")
    clear_state()
    return {"stopped": True, "was_running": True, "pid": state["pid"], "log": str(log_path())}


def _terminate(pid, port):
    _signal(pid, terminate=True)
    deadline = time.time() + STOP_TIMEOUT_S
    while time.time() < deadline:
        if not process_alive(pid):
            return
        time.sleep(0.2)
    _signal(pid, terminate=False)


def _signal(pid, terminate):
    if os.name == "nt":
        import ctypes

        PROCESS_TERMINATE = 0x0001
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            try:
                kernel32.TerminateProcess(handle, 0)
            finally:
                kernel32.CloseHandle(handle)
        return
    import signal

    os.kill(pid, signal.SIGTERM if terminate else signal.SIGKILL)


def status():
    state = running_state()
    if not state:
        return {"running": False, "log": str(log_path())}
    return {**{k: v for k, v in state.items() if k != "token"}, "running": True, "pid": state.get("pid"), "port": state.get("port"),
            "started_at": state.get("started_at"), "log": str(log_path())}


def workbench_url(port=3081, name=None):
    if name:
        return f"http://127.0.0.1:{port}/w/{name}/"
    return f"http://127.0.0.1:{port}/"
