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
_ACTIVE_TURNS = set()
_CANCEL_REQUESTS = set()
_TIMEOUTS = set()
STOP_GRACE_SECONDS = 1


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
        record = _recover_interrupted(pool, _read_json(path))
        record.setdefault("title", "")
        record.setdefault("title_source", "unset")
        records.append(record)
    records.sort(key=lambda item: item["updated_at"], reverse=True)
    return records if limit is None else records[:limit]


def get(pool, conversation_id):
    record = _recover_interrupted(
        pool, _read_json(_conversation_file(pool, conversation_id))
    )
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
    record = _recover_interrupted(
        pool, _read_json(folder / "conversation.json")
    )
    with _LOCK:
        record = _read_json(folder / "conversation.json")
        if record.get("status") == "running":
            raise ConversationConflict("conversation has a running turn")
        shutil.rmtree(folder)
    return {"conversation_id": conversation_id, "deleted": True}


def get_turn(pool, conversation_id, turn_id):
    _recover_interrupted(
        pool, _read_json(_conversation_file(pool, conversation_id))
    )
    return _read_json(_turn_file(pool, conversation_id, turn_id))


def _recover_interrupted(pool, record):
    """Turn a persisted running state with no live worker into an honest failure."""
    if record.get("status") != "running" or not record.get("current_turn_id"):
        return record
    turn_id = record["current_turn_id"]
    key = (str(_conversation_dir(pool, record["conversation_id"])), turn_id)
    with _LOCK:
        if key in _ACTIVE_TURNS:
            return record
        current = _read_json(_conversation_file(pool, record["conversation_id"]))
        if current.get("status") != "running" or current.get("current_turn_id") != turn_id:
            return current
        error = "workbench restarted while the provider turn was running"
        turn_path = _turn_file(pool, record["conversation_id"], turn_id)
        if turn_path.is_file():
            turn = _read_json(turn_path)
            turn.update({"status": "failed", "error": error, "updated_at": _now()})
            _write_json(turn_path, turn)
            _append_event(
                _events_file(pool, record["conversation_id"], turn_id),
                "error", text=error,
            )
        current.update({"status": "idle", "current_turn_id": None, "updated_at": _now()})
        _write_json(_conversation_file(pool, record["conversation_id"]), current)
        return current


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
        "\"title\":\"…\",\"kind\":\"stage|long_term\",\"start_date\":\"YYYY-MM-DD或空\","
        "\"deadline\":\"YYYY-MM-DD或空\","
        "\"description\":\"…\"} ``` 代填目标字段（仅此意图可附，普通问答不得代填）。"
        "仅当学生明确要求出题、补池或给某知识点加内容时，才可在回答末尾附出题入库区块；\n"
        "对话内出题一律用 lessonkit-action 区块，禁止直接运行 wb ingest 或写数据库。\n"
        "manifest 规则：kind 为 flash-card-patch 或 micro-quiz-patch。\n"
        "闪卡 item 字段：card_id/kp_id/front/back/source_evidence，可选 topic_label。\n"
        "微题 item 字段：problem_id/kp_id/stem/quiz_type/options/answer_key/error_reason/source_evidence，\n"
        "可选 topic_label/display_title/display_summary。\n"
        "id 形如 <course>-<chapter>-fc-NNN 或 -mq-NNN（NNN 为三位数字；与池内已有 id\n"
        "重复会被拒收，收到拒收原因后改用其他编号重试）；kp_id 必须取自下方上下文的\n"
        "knowledge_point_ids；新内容 id 从下方上下文 next_free_ids 起顺延（它给出每类\n"
        "实体的下一个空闲编号）。\n"
        "长度与取值：front≤100 字、back≤300 字、stem≤200 字、options 为 2–6 个互不相同的\n"
        "字符串且 answer_key 必须是其中之一（yes_no 用默认 是/否 对）、quiz_type 仅\n"
        "yes_no/single_choice/multiple_choice、topic_label≤40 字、display_title≤80 字、\n"
        "display_summary≤200 字；数学乘号一律用 ×；source_evidence 必填（如\n"
        "\"textbook ch06 §3.1\"）；一次产出 3–6 条。\n"
        "闪卡 item 示例：{\"card_id\":\"dmath-ch06-fc-901\",\"kp_id\":\"dmath-ch06-kp-001\",\n"
        "\"front\":\"乘法规则针对的是什么情形？\",\"back\":\"一个过程可分解为先后的两个任务，各自都有若干种做法——分步计数用乘法。\",\n"
        "\"source_evidence\":\"textbook ch06 product rule\",\"topic_label\":\"计数原理\"}\n"
        "微题 item 示例：{\"problem_id\":\"dmath-ch06-mq-901\",\"kp_id\":\"dmath-ch06-kp-001\",\n"
        "\"stem\":\"自然数 1 是质数吗？\",\"quiz_type\":\"yes_no\",\"answer_key\":\"否\",\n"
        "\"error_reason\":\"1 只有 1 个正因数，不算质数。\",\"source_evidence\":\"Rosen 6th, §3.1 定义\",\n"
        "\"topic_label\":\"计数原理\"}\n"
        "若上下文含 last_check_outcome：成功则不要重复提交相同内容；被拒收则按逐条原因\n"
        "修正后重新提交完整区块。\n\n"
        "服务端重建的当前上下文：\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n\n学生消息：\n"
        + message
    )


def _last_check_outcome(folder):
    transcript = folder / "transcript.jsonl"
    try:
        exchange = json.loads(transcript.read_text(encoding="utf-8").splitlines()[-1])
    except (OSError, UnicodeError, IndexError, json.JSONDecodeError):
        return None
    if not isinstance(exchange, dict):
        return None
    action = exchange.get("action")
    if not isinstance(action, dict):
        return None
    if action.get("ignored"):
        return (
            f"上一轮回复附带了 lessonkit-action 区块，但未被接受（{action['ignored']}），"
            "未写入任何内容。不要向学生声称已写入；只有收到批次确认才算成功。"
        )
    if action.get("type") != "check_ingest":
        return None
    if "result" in action:
        result = action["result"]
        if not isinstance(result, dict) or not isinstance(result.get("counts"), dict):
            return None
        counts = result["counts"]
        n = counts.get("flash_cards", counts.get("problems", 0))
        try:
            return (
                f"上一轮出题动作已成功入库：批次 {result['batch_id']}"
                f"（{result['kind']}，{n} 条）。不要重复提交相同内容。"
            )
        except KeyError:
            return None
    error = action.get("error")
    if not isinstance(error, str):
        return None
    if "manifest" in action:
        return (
            "上一轮出题动作被门禁拒收（零写入），逐条原因：\n"
            f"{error}\n"
            "请修正 manifest 后重新提交完整的 lessonkit-action 区块。"
        )
    return f"上一轮出题动作区块无效：{error}。请重新提交符合契约的完整区块。"


def start_turn(pool, workspace, conversation_id, message, context):
    folder = _conversation_dir(pool, conversation_id)
    conversation_path = folder / "conversation.json"
    _recover_interrupted(pool, _read_json(conversation_path))
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
        _ACTIVE_TURNS.add(key)
        _CANCEL_REQUESTS.discard(key)
        _TIMEOUTS.discard(key)
        turn_context = dict(context)
        last_check_outcome = _last_check_outcome(folder)
        if last_check_outcome:
            turn_context["last_check_outcome"] = last_check_outcome
        thread = threading.Thread(
            target=_run_turn_safely,
            args=(
                pool.root, pool.jobs_dir(), workspace, conversation_id, turn_id,
                message, turn_context,
            ),
            daemon=True,
        )
        thread.start()
    return turn


def _run_turn_safely(*args):
    jobs_dir, conversation_id, turn_id = args[1], args[3], args[4]
    folder = jobs_dir / conversation_id
    try:
        _run_turn(*args)
    except Exception as exc:
        turn_path = folder / f"{turn_id}.json"
        if turn_path.is_file() and _read_json(turn_path).get("status") == "running":
            _append_event(
                folder / f"{turn_id}.events.jsonl", "error",
                text=f"provider turn failed: {exc}",
            )
            _finish(folder, conversation_id, turn_id, "failed", f"provider turn failed: {exc}")


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
        _stop_process(process)

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
        backup = action_pool.db_path.with_name(
            action_pool.db_path.name
            + f".{conversation_id}-{turn_id}-ingest-backup")
        try:
            applied = ingest.apply_batch(
                action_pool.db_path, action["manifest"],
                source="bridge", backup_path=backup)
            action["result"] = {
                key: applied[key]
                for key in ("batch_id", "kind", "counts", "backup_path", "applied")
            }
        except Exception as exc:
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


_ACTION_BLOCK_RE = re.compile(r"```lessonkit-action\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_action(answer, context):
    blocks = list(_ACTION_BLOCK_RE.finditer(answer))
    if not blocks:
        return answer, None
    applied = None
    invalid_json = False
    matched_intent = False
    for match in blocks:
        try:
            raw = json.loads(match.group(1).strip())
        except (TypeError, ValueError):
            invalid_json = True
            continue
        if not isinstance(raw, dict):
            continue
        action = None
        if raw.get("type") == "replace_practice_selection" and context.get("practice_intent"):
            matched_intent = True
            allowed = set(context.get("knowledge_point_ids") or [])
            ids = []
            for item in raw.get("kp_ids") or []:
                if item in allowed and item not in ids:
                    ids.append(item)
            if ids:
                action = {"type": raw["type"], "kp_ids": ids}
        elif raw.get("type") == "prefill_goal_form" and context.get("goal_intent"):
            matched_intent = True
            # An action without a usable title is discarded entirely (spec).
            action = _clean_goal_form_action(raw)
        elif context.get("check_intent") and (
            raw.get("type") == "check_ingest"
            or ("type" not in raw and raw.get("kind") in {"flash-card-patch", "micro-quiz-patch"})
        ):
            # Agents sometimes emit the bare manifest without the action wrapper;
            # under content-generation intent both forms are accepted.
            matched_intent = True
            manifest = raw.get("manifest") if raw.get("type") == "check_ingest" else raw
            action = _clean_check_ingest_action(manifest)
        if action is not None:
            applied = action
            break
    cleaned = _ACTION_BLOCK_RE.sub("", answer).strip()
    if applied is not None:
        return cleaned, applied
    if invalid_json and context.get("check_intent"):
        return cleaned, {"type": "check_ingest", "error": "action block is not valid JSON"}
    if matched_intent:
        return cleaned, None
    if blocks and context.get("check_intent"):
        return cleaned, {
            "type": "check_ingest",
            "error": "回复包含 lessonkit-action 区块，但没有区块符合本次请求的意图或 manifest 契约，未写入任何内容",
        }
    return cleaned, {"ignored": "no block matched the active intent"}


def _clean_check_ingest_action(manifest):
    if not isinstance(manifest, dict):
        return {"type": "check_ingest", "error": "manifest must be an object"}
    if manifest.get("kind") not in {"flash-card-patch", "micro-quiz-patch"}:
        return {
            "type": "check_ingest",
            "error": "manifest kind must be flash-card-patch or micro-quiz-patch",
        }
    if not isinstance(manifest.get("items"), list) or not manifest["items"]:
        return {"type": "check_ingest", "error": "manifest items must be a non-empty list"}
    return {"type": "check_ingest", "manifest": manifest}


def _clean_goal_form_action(raw):
    title = str(raw.get("title") or "").strip()[:120]
    if not title:
        return None
    kind = raw.get("kind") if raw.get("kind") in _GOAL_KINDS else "stage"
    start_date = str(raw.get("start_date") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_date):
        start_date = ""
    deadline = str(raw.get("deadline") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline):
        deadline = ""
    description = str(raw.get("description") or "").strip()[:500]
    return {
        "type": "prefill_goal_form",
        "title": title,
        "kind": kind,
        "start_date": start_date,
        "deadline": deadline,
        "description": description,
    }


def _finish(folder, conversation_id, turn_id, status, error):
    now = _now()
    key = (str(folder), turn_id)
    with _LOCK:
        conversation_path = folder / "conversation.json"
        conversation = _read_json(conversation_path)
        conversation.update({"status": "idle", "current_turn_id": None, "updated_at": now})
        _write_json(conversation_path, conversation)
        turn_path = folder / f"{turn_id}.json"
        turn = _read_json(turn_path)
        turn.update({"status": status, "error": error, "updated_at": now})
        _write_json(turn_path, turn)
        _ACTIVE_TURNS.discard(key)
        _CANCEL_REQUESTS.discard(key)
        _TIMEOUTS.discard(key)


def _stop_process(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=STOP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def cancel(pool, conversation_id):
    conversation = _recover_interrupted(
        pool, _read_json(_conversation_file(pool, conversation_id))
    )
    if conversation["status"] != "running":
        raise ConversationConflict("conversation has no running turn")
    key = (str(_conversation_dir(pool, conversation_id)), conversation["current_turn_id"])
    with _LOCK:
        _CANCEL_REQUESTS.add(key)
        process = _PROCESSES.get(key)
    if process is not None:
        _stop_process(process)
    return {"conversation_id": conversation_id, "turn_id": conversation["current_turn_id"], "status": "cancelling"}
