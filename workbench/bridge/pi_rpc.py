"""One hidden Pi RPC process per conversation, retired after 30 idle minutes.

Pi 0.85.1 speaks strict LF JSONL on stdin/stdout in `--mode rpc`: commands carry
an `id` and answer with a correlated `{"type": "response"}` record, while agent
events stream asynchronously. This module owns only that transport; the turn
logic in `conversations` keeps owning what a turn means.
"""

import json
import queue
import subprocess
import threading
import time

from workbench.bridge import conversation_providers


IDLE_SECONDS = conversation_providers.IDLE_SECONDS
REAP_INTERVAL_SECONDS = 60
HANDSHAKE_SECONDS = 60
PROMPT_ACCEPT_SECONDS = 30
STOP_GRACE_SECONDS = 2
# How long an aborted turn may take to settle before terminate/kill.
ABORT_SETTLE_SECONDS = 8
# The in-flight tool budget. It stays below IDLE_SECONDS by construction, so a
# stuck turn fails by its own budget before its process is recycled under it.
TOOL_SECONDS = conversation_providers.TOOL_SECONDS


class PiRpcError(RuntimeError):
    """The RPC process could not serve the request."""


class PiRpcClosed(PiRpcError):
    """The RPC process exited (or its stdout ended)."""


class PiRpcTimeout(PiRpcError):
    """No usable record arrived in time."""


class PiRpcRejected(PiRpcError):
    """The prompt was refused before acceptance: nothing ran, a retry is safe."""


class PiRpcProcess:
    """A long-lived `pi --mode rpc` child for exactly one conversation."""

    def __init__(self, provider, workspace, session_id=None, clock=time.monotonic):
        self.provider = provider
        self.workspace = str(workspace)
        self.session_id = session_id
        self._clock = clock
        self._process = None
        self._inbox = queue.Queue()
        self._reader = None
        self._requests = 0
        self._last_used = clock()
        self.noise = []
        self.pid = None
        self.started_processes = 0

    # -- lifecycle --------------------------------------------------------

    def start(self):
        """Launch and hand shake. Raises PiRpcError without leaving a child behind."""
        command = conversation_providers.build_command(
            self.provider, self.session_id, mode="rpc")
        try:
            self._process = subprocess.Popen(
                command,
                cwd=self.workspace,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **conversation_providers.hidden_launch_kwargs(),
            )
        except OSError as exc:
            raise PiRpcError(f"rpc launch failed: {exc}") from exc
        self.started_processes += 1
        self.pid = self._process.pid
        self._inbox = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        state = self.request({"type": "get_state"}, HANDSHAKE_SECONDS)
        session_id = state.get("sessionId") if isinstance(state, dict) else None
        if isinstance(session_id, str) and session_id:
            self.session_id = session_id
        self._last_used = self._clock()
        return self

    def close(self):
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=STOP_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    @property
    def alive(self):
        return self._process is not None and self._process.poll() is None

    def idle_seconds(self):
        return self._clock() - self._last_used

    def touch(self):
        self._last_used = self._clock()

    # -- transport --------------------------------------------------------

    def _pump(self):
        """Read strict LF-framed records; one JSON object per line."""
        stream = self._process.stdout
        buffer = bytearray()
        while True:
            try:
                chunk = stream.read1(65536) if hasattr(stream, "read1") else stream.read(4096)
            except (OSError, ValueError):
                break
            if not chunk:
                break
            buffer.extend(chunk)
            while True:
                index = buffer.find(b"\n")
                if index < 0:
                    break
                line = bytes(buffer[:index])
                del buffer[: index + 1]
                if line.endswith(b"\r"):
                    line = line[:-1]
                if not line.strip():
                    continue
                self._inbox.put(line.decode("utf-8", "replace"))
        self._inbox.put(None)

    def _next_record(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PiRpcTimeout("no record arrived in time")
            try:
                raw = self._inbox.get(timeout=remaining)
            except queue.Empty:
                raise PiRpcTimeout("no record arrived in time") from None
            if raw is None:
                raise PiRpcClosed("rpc process ended")
            try:
                return json.loads(raw)
            except ValueError:
                # Not protocol: keep it for diagnostics and read on.
                self.noise.append(raw[:500])
                self.noise = self.noise[-5:]

    def _send(self, payload):
        process = self._process
        if process is None or process.poll() is not None:
            raise PiRpcClosed("rpc process is not running")
        try:
            process.stdin.write(
                (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise PiRpcClosed(f"rpc write failed: {exc}") from exc

    def request(self, payload, timeout):
        """Send one command and return its response `data` (empty when absent)."""
        self._requests += 1
        request_id = f"lk-{self._requests}"
        envelope = {**payload, "id": request_id}
        self._send(envelope)
        while True:
            record = self._next_record(timeout)
            if record.get("type") != "response" or record.get("id") != request_id:
                self._stash(record)
                continue
            if not record.get("success"):
                raise PiRpcError(str(record.get("error") or "rpc command failed"))
            data = record.get("data")
            self._last_used = self._clock()
            return data if isinstance(data, dict) else {}

    def _stash(self, record):
        """Events that arrive before a response must not be lost."""
        self._pending = getattr(self, "_pending", None) or []
        if record.get("type") in {"agent_start", "turn_start", "message_start",
                                  "message_update", "tool_execution_start",
                                  "tool_execution_update", "tool_execution_end",
                                  "message_end", "turn_end", "agent_end",
                                  "agent_settled", "queue_update",
                                  "compaction_start", "compaction_end",
                                  "auto_retry_start", "auto_retry_end"}:
            self._pending.append(record)

    def take_pending(self):
        pending = getattr(self, "_pending", None) or []
        self._pending = []
        return pending

    def prompt(self, message):
        """Accept one prompt; returns after acceptance, not completion."""
        try:
            self.request({"type": "prompt", "message": message}, PROMPT_ACCEPT_SECONDS)
        except PiRpcError as exc:
            raise PiRpcRejected(str(exc)) from exc

    def stream(self, timeout, tool_timeout=None):
        """Yield agent events until the run settles or the process ends.

        The budget measures silence, not total time: every record resets it, so a
        turn that keeps working is never cut off for taking long. While a tool
        call is in flight the longer ``tool_timeout`` applies instead, because a
        slow command is exactly the case that prints nothing for minutes.
        """
        tool_timeout = timeout if tool_timeout is None else tool_timeout
        live_tools = set()
        pending = list(self.take_pending())
        while pending:
            record = pending.pop(0)
            _track_tools(live_tools, record)
            yield record
            if record.get("type") == "agent_settled":
                return
        while True:
            record = self._next_record(tool_timeout if live_tools else timeout)
            self._last_used = self._clock()
            _track_tools(live_tools, record)
            if record.get("type") == "response":
                self._stash(record)
                continue
            yield record
            if record.get("type") == "agent_settled":
                return

    def abort(self):
        """Send RPC abort; True when the command went out.

        The turn thread is the only consumer of the event stream, so a waiting
        `abort` response would race it. The caller decides the terminate/kill
        fallback from whether the run actually settled.
        """
        self._requests += 1
        try:
            self._send({"id": f"lk-{self._requests}", "type": "abort"})
        except PiRpcError:
            return False
        return True


def _track_tools(live_tools, record):
    """Remember which tool calls are in flight, so a slow one keeps its budget."""
    record_type = record.get("type")
    if record_type == "tool_execution_start":
        tool_id = record.get("toolCallId") or record.get("id") or "tool"
        live_tools.add(tool_id)
    elif record_type == "tool_execution_end":
        tool_id = record.get("toolCallId") or record.get("id") or "tool"
        live_tools.discard(tool_id)
    elif record_type in {"turn_end", "agent_end", "agent_settled"}:
        live_tools.clear()


class PiRpcRegistry:
    """Conversation-keyed RPC processes with idle expiry and one restart."""

    def __init__(self, idle_seconds=IDLE_SECONDS, clock=time.monotonic):
        self._lock = threading.RLock()
        self._processes = {}
        self._idle_seconds = idle_seconds
        self._clock = clock
        self._reaper = None

    def process(self, key, provider, workspace, session_id=None):
        """The conversation's live process, launching it when needed."""
        with self._lock:
            current = self._processes.get(key)
            if current is not None and current.alive:
                current.touch()
                return current
            if current is not None:
                current.close()
            process = PiRpcProcess(provider, workspace, session_id, clock=self._clock)
            try:
                process.start()
            except PiRpcError:
                process.close()
                raise
            self._processes[key] = process
            self._ensure_reaper()
            return process

    def launch_with_retry(self, key, provider, workspace, session_id=None):
        """One launch/handshake failure before prompt acceptance restarts once."""
        try:
            return self.process(key, provider, workspace, session_id)
        except PiRpcError:
            return self.process(key, provider, workspace, session_id)

    def discard(self, key, process=None):
        """Forget a conversation's process (it crashed, or the conversation went away)."""
        with self._lock:
            current = self._processes.get(key)
            if current is None:
                return None
            if process is not None and current is not process:
                return None
            del self._processes[key]
            return current

    def close_all(self):
        with self._lock:
            processes = list(self._processes.values())
            self._processes.clear()
        for process in processes:
            process.close()
        return len(processes)

    def expire_idle(self, now=None):
        """Close every process idle past the window (or already dead)."""
        now = self._clock() if now is None else now
        with self._lock:
            expired = [
                process for process in self._processes.values()
                if not process.alive or process.idle_seconds() >= self._idle_seconds
            ]
            for process in expired:
                for key, item in list(self._processes.items()):
                    if item is process:
                        del self._processes[key]
        for process in expired:
            process.close()
        return expired

    def active(self):
        with self._lock:
            return {key: item for key, item in self._processes.items()}

    def _ensure_reaper(self):
        if self._reaper is not None and self._reaper.is_alive():
            return
        self._reaper = threading.Thread(target=self._reap_forever, daemon=True)
        self._reaper.start()

    def _reap_forever(self):
        while True:
            time.sleep(min(REAP_INTERVAL_SECONDS, max(1, self._idle_seconds / 10)))
            self.expire_idle()
            with self._lock:
                if not self._processes:
                    self._reaper = None
                    return


REGISTRY = PiRpcRegistry()
