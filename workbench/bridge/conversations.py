"""Provider-locked native conversations with a minimal successful mirror."""

import json
import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from workbench import ingest
from workbench.bridge import conversation_providers
from workbench.data.pool import Pool


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


def create(pool, provider_name, title=""):
    conversation_providers.get(provider_name)
    jobs_dir = pool.jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        number = _next_number(jobs_dir.glob("conv-*"), "conv-")
        conversation_id = f"conv-{number:03d}"
        folder = jobs_dir / conversation_id
        folder.mkdir()
        now = _now()
        title = title.strip() if isinstance(title, str) else ""
        record = {
            "conversation_id": conversation_id,
            "provider": provider_name,
            "title": title,
            "title_source": "user" if title else "unset",
            "provider_session_id": None,
            "status": "idle",
            "current_turn_id": None,
            "created_at": now,
            "updated_at": now,
        }
        _write_json(folder / "conversation.json", record)
    return record


def list_sessions(pool, limit=None):
    records = []
    jobs_dir = pool.jobs_dir()
    if not jobs_dir.is_dir():
        return records
    for path in jobs_dir.glob("conv-*/conversation.json"):
        record = _read_json(path)
        record.setdefault("title", "")
        record.setdefault("title_source", "unset")
        records.append(record)
    records.sort(key=lambda item: item["updated_at"], reverse=True)
    return records if limit is None else records[:limit]


def get(pool, conversation_id):
    record = _read_json(_conversation_file(pool, conversation_id))
    record.setdefault("title", "")
    record.setdefault("title_source", "unset")
    messages = []
    transcript = _conversation_dir(pool, conversation_id) / "transcript.jsonl"
    if transcript.is_file():
        for line in transcript.read_text(encoding="utf-8").splitlines():
            exchange = json.loads(line)
            assistant = {"role": "assistant", "content": exchange["assistant"]}
            if exchange.get("action"):
                assistant["action"] = exchange["action"]
            messages.extend([
                {"role": "user", "content": exchange["user"]},
                assistant,
            ])
    record["messages"] = messages
    return record


def rename(pool, conversation_id, title):
    """Set a user-owned title on the local mirror."""
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    title = title.strip()
    if not title:
        raise ValueError("title is required")
    path = _conversation_file(pool, conversation_id)
    with _LOCK:
        record = _read_json(path)
        record.update({"title": title, "title_source": "user", "updated_at": _now()})
        _write_json(path, record)
    return record


def delete(pool, conversation_id):
    """Delete only an idle Lesson Kit mirror; provider sessions are untouched."""
    folder = _conversation_dir(pool, conversation_id)
    with _LOCK:
        record = _read_json(folder / "conversation.json")
        if record.get("status") == "running":
            raise ConversationConflict("conversation has a running turn")
        shutil.rmtree(folder)
    return {"conversation_id": conversation_id, "deleted": True}


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
        "才可使用 wb data 写命令。回答末尾如有写入，用简洁中文列出对象、动作和可访问路径，不展示命令、SQL 或工具日志。"
        "若学生明确要求选择或安排练习范围，可在回答末尾附一个 lessonkit-action JSON 区块；"
        "普通问答不要附带动作。格式为 ```lessonkit-action {\"type\":\"replace_practice_selection\","
        "\"kp_ids\":[\"知识点ID\"]} ```。"
        "若学生从目标表单发起一句话求助，可附 ```lessonkit-action {\"type\":\"prefill_goal_form\","
        "\"title\":\"…\",\"kind\":\"stage|long_term\",\"deadline\":\"YYYY-MM-DD或空\","
        "\"description\":\"…\"} ``` 代填目标字段（仅此意图可附，普通问答不得代填）。"
        "仅当学生明确要求出题、补池或给某知识点加内容时，可在回答末尾附 "
        "```lessonkit-action {\"type\":\"check_ingest\",\"manifest\":{"
        "\"kind\":\"flash-card-patch\",\"items\":[…]}} ```。kind 只能是 "
        "flash-card-patch 或 micro-quiz-patch；闪卡 items 必须包含 "
        "card_id/kp_id/front/back/source_evidence；微题 items 必须包含 "
        "problem_id/kp_id/stem/quiz_type/options/answer_key/error_reason/source_evidence。\n\n"
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
            provider_title = normalized.pop("title", None)
            if provider_session_id:
                conversation = _read_json(conversation_path)
                conversation["provider_session_id"] = provider_session_id
                conversation["updated_at"] = _now()
                _write_json(conversation_path, conversation)
            provider_title = str(provider_title).strip() if provider_title else ""
            if provider_title:
                conversation = _read_json(conversation_path)
                if conversation.get("title_source", "unset") == "unset":
                    conversation.update({
                        "title": provider_title,
                        "title_source": "agent",
                        "updated_at": _now(),
                    })
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

    answer, action = _extract_action(answer, context)
    if action and action["type"] == "check_ingest" and "manifest" in action:
        action_pool = Pool(
            root=root,
            db_path=root / workspace["db"],
            course=workspace.get("active_course", ""),
            chapter=workspace.get("active_chapter", ""),
        )
        try:
            applied = ingest.apply_batch(action_pool.db_path, action["manifest"], source="bridge")
            action["result"] = {
                key: applied[key]
                for key in ("batch_id", "kind", "counts", "backup_path", "applied")
            }
        except ValueError as exc:
            action["error"] = str(exc)
        finally:
            action_pool.close()

    conversation = _read_json(conversation_path)
    turn = _read_json(turn_path)
    if action:
        turn["action"] = action
        _write_json(turn_path, turn)
    exchange = {
        "turn_id": turn_id,
        "user": message,
        "assistant": answer,
        "context_anchor": context.get("anchor", {}),
        "provider_session_id": conversation.get("provider_session_id"),
        "change_summary": [],
        "completed_at": _now(),
    }
    if action:
        exchange["action"] = action
    with (folder / "transcript.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(exchange, ensure_ascii=False) + "\n")
    _append_event(event_path, "done")
    _finish(folder, conversation_id, turn_id, "done", None)


_GOAL_KINDS = {"stage", "long_term"}


def _extract_action(answer, context):
    match = re.search(r"```lessonkit-action\s*([\s\S]*?)```", answer, re.IGNORECASE)
    if not match:
        return answer, None
    try:
        raw = json.loads(match.group(1).strip())
    except (TypeError, ValueError):
        if context.get("check_intent"):
            cleaned = (answer[:match.start()] + answer[match.end():]).strip()
            return cleaned, {
                "type": "check_ingest",
                "error": "action block is not valid JSON",
            }
        return answer, None
    action = None
    if raw.get("type") == "replace_practice_selection" and context.get("practice_intent"):
        allowed = set(context.get("knowledge_point_ids") or [])
        ids = []
        for item in raw.get("kp_ids") or []:
            if item in allowed and item not in ids:
                ids.append(item)
        if ids:
            action = {"type": raw["type"], "kp_ids": ids}
    elif raw.get("type") == "prefill_goal_form" and context.get("goal_intent"):
        action = _clean_goal_form_action(raw)
    elif raw.get("type") == "check_ingest" and context.get("check_intent"):
        manifest = raw.get("manifest")
        if not isinstance(manifest, dict):
            action = {"type": "check_ingest", "error": "manifest must be an object"}
        elif manifest.get("kind") not in {"flash-card-patch", "micro-quiz-patch"}:
            action = {
                "type": "check_ingest",
                "error": "manifest kind must be flash-card-patch or micro-quiz-patch",
            }
        elif not isinstance(manifest.get("items"), list) or not manifest["items"]:
            action = {
                "type": "check_ingest",
                "error": "manifest items must be a non-empty list",
            }
        else:
            action = {"type": "check_ingest", "manifest": manifest}
    if action is None:
        return answer, None
    cleaned = (answer[:match.start()] + answer[match.end():]).strip()
    return cleaned, action


def _clean_goal_form_action(raw):
    title = str(raw.get("title") or "").strip()[:120]
    if not title:
        return None
    kind = raw.get("kind") if raw.get("kind") in _GOAL_KINDS else "stage"
    deadline = str(raw.get("deadline") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline):
        deadline = ""
    description = str(raw.get("description") or "").strip()[:500]
    return {
        "type": "prefill_goal_form",
        "title": title,
        "kind": kind,
        "deadline": deadline,
        "description": description,
    }


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
