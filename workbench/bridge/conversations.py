"""Provider-locked native conversations with a minimal successful mirror."""

import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from workbench.bridge import conversation_providers


class ConversationConflict(Exception):
    pass


_LOCK = threading.Lock()
_PROCESSES = {}
_CANCEL_REQUESTS = set()
_TIMEOUTS = set()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _conversation_dir(pool, conversation_id):
    return pool.jobs_dir() / conversation_id


def _conversation_file(pool, conversation_id):
    return _conversation_dir(pool, conversation_id) / "conversation.json"


def _turn_file(pool, conversation_id, turn_id):
    return _conversation_dir(pool, conversation_id) / f"{turn_id}.json"


def _events_file(pool, conversation_id, turn_id):
    return _conversation_dir(pool, conversation_id) / f"{turn_id}.events.jsonl"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    temporary = path.with_name(path.name + f".{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _next_number(paths, prefix):
    numbers = []
    for path in paths:
        suffix = path.stem[len(prefix):]
        if path.stem.startswith(prefix) and suffix.isdigit():
            numbers.append(int(suffix))
    return max(numbers, default=0) + 1


def create(pool, provider_name):
    conversation_providers.get(provider_name)
    jobs_dir = pool.jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        number = _next_number(jobs_dir.glob("conv-*"), "conv-")
        conversation_id = f"conv-{number:03d}"
        folder = jobs_dir / conversation_id
        folder.mkdir()
        now = _now()
        record = {
            "conversation_id": conversation_id,
            "provider": provider_name,
            "provider_session_id": None,
            "status": "idle",
            "current_turn_id": None,
            "created_at": now,
            "updated_at": now,
        }
        _write_json(folder / "conversation.json", record)
    return record


def list_sessions(pool, limit=10):
    records = []
    jobs_dir = pool.jobs_dir()
    if not jobs_dir.is_dir():
        return records
    for path in jobs_dir.glob("conv-*/conversation.json"):
        records.append(_read_json(path))
    records.sort(key=lambda item: item["updated_at"], reverse=True)
    return records[:limit]


def get(pool, conversation_id):
    record = _read_json(_conversation_file(pool, conversation_id))
    messages = []
    transcript = _conversation_dir(pool, conversation_id) / "transcript.jsonl"
    if transcript.is_file():
        for line in transcript.read_text(encoding="utf-8").splitlines():
            exchange = json.loads(line)
            messages.extend([
                {"role": "user", "content": exchange["user"]},
                {"role": "assistant", "content": exchange["assistant"]},
            ])
    record["messages"] = messages
    return record


def get_turn(pool, conversation_id, turn_id):
    return _read_json(_turn_file(pool, conversation_id, turn_id))


def events(pool, conversation_id, turn_id, after=0):
    path = _events_file(pool, conversation_id, turn_id)
    if not path.is_file():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["sequence"] > after
    ]


def _append_event(path, kind, **fields):
    existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    event = {"sequence": len(existing) + 1, "kind": kind, **fields}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _prompt(message, context):
    return (
        "你是 Lesson Kit 的外部 AI 教师。普通问答只读取上下文；只有学生明确要求修改内容或提交学习结论时，"
        "才可使用 wb data 写命令。回答末尾如有写入，用简洁中文列出对象、动作和可访问路径，不展示命令、SQL 或工具日志。\n\n"
        "服务端重建的当前上下文：\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n\n学生消息：\n"
        + message
    )


def start_turn(pool, workspace, conversation_id, message, context):
    folder = _conversation_dir(pool, conversation_id)
    conversation_path = folder / "conversation.json"
    with _LOCK:
        conversation = _read_json(conversation_path)
        if conversation["status"] == "running":
            raise ConversationConflict("conversation already has a running turn")
        turn_number = _next_number(folder.glob("turn-*.json"), "turn-")
        turn_id = f"turn-{turn_number:03d}"
        now = _now()
        turn = {
            "turn_id": turn_id,
            "status": "running",
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        _write_json(folder / f"{turn_id}.json", turn)
        conversation.update({"status": "running", "current_turn_id": turn_id, "updated_at": now})
        _write_json(conversation_path, conversation)
        key = (str(folder), turn_id)
        _CANCEL_REQUESTS.discard(key)
        _TIMEOUTS.discard(key)
        thread = threading.Thread(
            target=_run_turn,
            args=(pool.root, pool.jobs_dir(), workspace, conversation_id, turn_id, message, context),
            daemon=True,
        )
        thread.start()
    return turn


def _run_turn(root, jobs_dir, workspace, conversation_id, turn_id, message, context):
    folder = jobs_dir / conversation_id
    conversation_path = folder / "conversation.json"
    turn_path = folder / f"{turn_id}.json"
    event_path = folder / f"{turn_id}.events.jsonl"
    key = (str(folder), turn_id)
    conversation = _read_json(conversation_path)
    try:
        provider = conversation_providers.get(conversation["provider"])
        command = conversation_providers.build_command(
            provider, conversation.get("provider_session_id")
        )
    except (KeyError, OSError, ValueError) as exc:
        _append_event(event_path, "error", text=f"provider unavailable: {exc}")
        _finish(folder, conversation_id, turn_id, "failed", f"provider unavailable: {exc}")
        return
    _append_event(event_path, "phase", label="provider.started")
    if key in _CANCEL_REQUESTS:
        _finish(folder, conversation_id, turn_id, "cancelled", "cancelled")
        return
    try:
        process = subprocess.Popen(
            command,
            cwd=str(workspace["path"]),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        _append_event(event_path, "error", text=f"provider launch failed: {exc}")
        _finish(folder, conversation_id, turn_id, "failed", f"provider launch failed: {exc}")
        return
    with _LOCK:
        _PROCESSES[key] = process

    def timeout_process():
        with _LOCK:
            if process.poll() is None:
                _TIMEOUTS.add(key)
                process.terminate()

    timer = threading.Timer(provider.get("timeout_s", 300), timeout_process)
    timer.start()
    text_parts = []
    result_text = ""
    try:
        process.stdin.write(_prompt(message, context))
        process.stdin.close()
        for line in process.stdout:
            try:
                normalized = conversation_providers.normalize_event(
                    conversation["provider"], json.loads(line)
                )
            except json.JSONDecodeError:
                _append_event(event_path, "phase", label="provider.output")
                continue
            provider_session_id = normalized.pop("provider_session_id", None)
            if provider_session_id:
                conversation = _read_json(conversation_path)
                conversation["provider_session_id"] = provider_session_id
                conversation["updated_at"] = _now()
                _write_json(conversation_path, conversation)
            kind = normalized.pop("kind")
            _append_event(event_path, kind, **normalized)
            if kind == "text":
                text_parts.append(normalized.get("text", ""))
            elif kind == "result":
                result_text = normalized.get("text", "")
        return_code = process.wait()
    finally:
        timer.cancel()
        with _LOCK:
            _PROCESSES.pop(key, None)

    if key in _CANCEL_REQUESTS:
        _finish(folder, conversation_id, turn_id, "cancelled", "cancelled")
        return
    if key in _TIMEOUTS:
        _finish(folder, conversation_id, turn_id, "failed", "provider timed out")
        return
    if return_code != 0:
        _finish(folder, conversation_id, turn_id, "failed", f"provider exit code {return_code}")
        return
    answer = result_text or "".join(text_parts)
    if not answer:
        _finish(folder, conversation_id, turn_id, "failed", "provider returned no assistant text")
        return

    conversation = _read_json(conversation_path)
    exchange = {
        "turn_id": turn_id,
        "user": message,
        "assistant": answer,
        "context_anchor": context.get("anchor", {}),
        "provider_session_id": conversation.get("provider_session_id"),
        "change_summary": [],
        "completed_at": _now(),
    }
    with (folder / "transcript.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(exchange, ensure_ascii=False) + "\n")
    _append_event(event_path, "done")
    _finish(folder, conversation_id, turn_id, "done", None)


def _finish(folder, conversation_id, turn_id, status, error):
    now = _now()
    conversation_path = folder / "conversation.json"
    conversation = _read_json(conversation_path)
    conversation.update({"status": "idle", "current_turn_id": None, "updated_at": now})
    _write_json(conversation_path, conversation)
    turn_path = folder / f"{turn_id}.json"
    turn = _read_json(turn_path)
    turn.update({"status": status, "error": error, "updated_at": now})
    _write_json(turn_path, turn)


def cancel(pool, conversation_id):
    conversation = _read_json(_conversation_file(pool, conversation_id))
    if conversation["status"] != "running":
        raise ConversationConflict("conversation has no running turn")
    key = (str(_conversation_dir(pool, conversation_id)), conversation["current_turn_id"])
    with _LOCK:
        _CANCEL_REQUESTS.add(key)
        process = _PROCESSES.get(key)
        if process is not None and process.poll() is None:
            process.terminate()
    return {"conversation_id": conversation_id, "turn_id": conversation["current_turn_id"], "status": "cancelling"}
