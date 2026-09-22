"""A fake `pi --mode rpc` speaking the real strict-LF JSONL protocol.

Modes (a positional argument) drive the failure shapes the bridge must survive,
and the script appends to a log file (the next positional argument) so a test
can prove what was delivered. Abort is handled while a turn sleeps, the way the
real agent's event loop answers it.
"""

import json
import os
import sys
import threading
import time


_KNOWN_FLAGS = {"--mode", "--print", "--model", "--session", "--session-dir"}


def _positional_arguments(argv):
    """Skip real pi flags and their values, so the bridge's own argv is honoured."""
    rest = []
    index = 0
    while index < len(argv):
        if argv[index] in _KNOWN_FLAGS:
            index += 2
            continue
        rest.append(argv[index])
        index += 1
    return rest


ARGV = sys.argv[1:]
POSITIONAL = _positional_arguments(ARGV)
MODE = POSITIONAL[0] if POSITIONAL else "normal"
LOG = POSITIONAL[1] if len(POSITIONAL) > 1 else ""
SESSION = "pi-rpc-session-1"

_OUT = threading.Lock()
_STATE = {"prompt_count": 0, "aborted": False}
USAGE = {"input": 10, "output": 2, "cacheRead": 0, "cacheWrite": 0,
         "totalTokens": 12, "cost": {"input": 0, "output": 0, "total": 0}}


def log(entry):
    if not LOG:
        return
    with open(LOG, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def emit(payload):
    with _OUT:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def respond(request_id, command, success=True, data=None, error=None):
    payload = {"id": request_id, "type": "response", "command": command, "success": success}
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    emit(payload)


def read_commands():
    """Strict LF framing: strip only a trailing CR, never split on U+2028."""
    while True:
        chunk = sys.stdin.readline()
        if not chunk:
            return
        line = chunk[:-1] if chunk.endswith("\n") else chunk
        if line.endswith("\r"):
            line = line[:-1]
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except ValueError:
            respond(None, "parse", success=False, error="Failed to parse command")


def run_turn(count, request_id):
    _STATE["aborted"] = False
    answer = "第 %d 轮回答" % count
    log({"event": "turn", "pid": os.getpid(), "count": count})
    emit({"type": "agent_start"})
    emit({"type": "turn_start"})
    if MODE == "crash-after-accept":
        # A real crash takes the whole process down, not just this thread.
        log({"event": "crash", "pid": os.getpid()})
        sys.stdout.flush()
        os._exit(7)
    emit({"type": "message_start", "message": {"role": "assistant", "content": []}})
    if MODE == "error":
        # The provider rejects the key: the process keeps running, the turn failed.
        emit({"type": "message_end", "message": {
            "role": "assistant", "stopReason": "error",
            "errorMessage": "401 invalid api key", "content": []}})
        emit({"type": "turn_end"})
        emit({"type": "agent_settled"})
        return
    emit({"type": "message_update",
          "assistantMessageEvent": {"type": "text_start", "contentIndex": 0}})
    if MODE == "slow":
        deadline = time.time() + 30
        while time.time() < deadline and not _STATE["aborted"]:
            time.sleep(0.05)
        if _STATE["aborted"]:
            return
    emit({"type": "message_update",
          "assistantMessageEvent": {"type": "text_delta", "delta": "收到"}})
    emit({"type": "message_update",
          "assistantMessageEvent": {"type": "toolcall_start", "id": "call_1",
                                    "toolName": "read"}})
    emit({"type": "tool_execution_start", "toolCallId": "call_1",
          "toolName": "read", "args": {"path": "TASK.md"}})
    emit({"type": "tool_execution_end", "toolCallId": "call_1",
          "toolName": "read", "isError": False,
          "result": {"content": [{"type": "text", "text": "文件内容"}], "details": {}}})
    emit({"type": "message_update",
          "assistantMessageEvent": {"type": "text_delta", "delta": answer}})
    emit({"type": "message_end", "message": {
        "role": "assistant", "stopReason": "stop",
        "content": [{"type": "text", "text": answer}], "usage": USAGE}})
    emit({"type": "turn_end"})
    emit({"type": "agent_end", "messages": [
        {"role": "assistant", "stopReason": "stop",
         "content": [{"type": "text", "text": answer}]}]})
    emit({"type": "agent_settled"})


log({"event": "start", "pid": os.getpid(), "argv": ARGV})

for command in read_commands():
    kind = command.get("type")
    request_id = command.get("id")
    if kind == "get_state":
        if MODE == "handshake-fail" and not os.environ.get("LK_FAKE_HANDSHAKE_DONE"):
            log({"event": "handshake-failed", "pid": os.getpid()})
            respond(request_id, "get_state", success=False, error="no model configured")
            continue
        log({"event": "handshake", "pid": os.getpid()})
        respond(request_id, "get_state", data={
            "sessionId": SESSION, "isStreaming": False,
            "messageCount": _STATE["prompt_count"],
        })
    elif kind == "prompt":
        _STATE["prompt_count"] += 1
        count = _STATE["prompt_count"]
        log({"event": "prompt", "pid": os.getpid(), "text": command.get("message")})
        if MODE == "reject" and count == 1:
            respond(request_id, "prompt", success=False, error="prompt rejected")
            continue
        respond(request_id, "prompt", success=True)
        threading.Thread(target=run_turn, args=(count, request_id), daemon=True).start()
    elif kind == "abort":
        log({"event": "abort", "pid": os.getpid()})
        _STATE["aborted"] = True
        respond(request_id, "abort", data={})
        emit({"type": "message_end", "message": {
            "role": "assistant", "stopReason": "aborted", "content": []}})
        emit({"type": "turn_end"})
        emit({"type": "agent_settled"})
    elif kind == "set_session_name":
        respond(request_id, kind, data={})
    else:
        respond(request_id, str(kind), success=False, error="unsupported command")
