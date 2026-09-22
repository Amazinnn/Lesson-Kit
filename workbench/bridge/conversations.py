"""Provider-locked native conversations with a minimal successful mirror."""

import json
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from workbench import ingest
from workbench.bridge import conversation_providers, pi_rpc
from workbench.data.pool import Pool


class ConversationConflict(Exception):
    pass


class InvalidIdentifier(ValueError):
    """A client-supplied conversation or turn id that is not a plain generated name."""


_LOCK = threading.RLock()
# One hidden `pi --mode rpc` process per conversation, retired after 30 idle minutes.
PI_RPC = pi_rpc.REGISTRY
_PROCESSES = {}
_ACTIVE_TURNS = set()
_CANCEL_REQUESTS = set()
_TIMEOUTS = set()
STOP_GRACE_SECONDS = 1
CONVERSATION_ID = re.compile(r"conv-\d+")
TURN_ID = re.compile(r"turn-\d+")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _require_id(value, pattern, kind):
    """Refuse an id that could address anything outside this workspace's jobs dir."""
    if isinstance(value, str) and pattern.fullmatch(value):
        return value
    raise InvalidIdentifier(f"invalid {kind} id: {value!r}")


def _conversation_dir(pool, conversation_id):
    _require_id(conversation_id, CONVERSATION_ID, "conversation")
    return pool.jobs_dir() / conversation_id


def _conversation_file(pool, conversation_id):
    return _conversation_dir(pool, conversation_id) / "conversation.json"


def _turn_file(pool, conversation_id, turn_id):
    _require_id(turn_id, TURN_ID, "turn")
    return _conversation_dir(pool, conversation_id) / f"{turn_id}.json"


def _events_file(pool, conversation_id, turn_id):
    _require_id(turn_id, TURN_ID, "turn")
    return _conversation_dir(pool, conversation_id) / f"{turn_id}.events.jsonl"


def _read_json(path):
    with _LOCK:
        return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    with _LOCK:
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
    with _LOCK:
        lines = transcript.read_text(encoding="utf-8").splitlines() if transcript.is_file() else []
    for line in lines:
        exchange = json.loads(line)
        assistant = {"role": "assistant", "content": exchange["assistant"]}
        if exchange.get("action"):
            assistant["action"] = exchange["action"]
        if exchange.get("activities"):
            assistant["activities"] = exchange["activities"]
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
    process = PI_RPC.discard(str(folder))
    if process is not None:
        process.close()
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
    with _LOCK:
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    rows = [json.loads(line) for line in lines]
    return [row for row in rows if row["sequence"] > after]


def _append_event(path, kind, **fields):
    with _LOCK:
        existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        event = {"sequence": len(existing) + 1, "kind": kind, **fields}
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _coalesced_activities(path):
    """Collapse updates for one provider activity into one durable plan row."""
    rows = {}
    order = []
    with _LOCK:
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    for line in lines:
        event = json.loads(line)
        if event.get("kind") != "activity":
            continue
        activity_id = event.get("activity_id") or f"activity-{event['sequence']}"
        if activity_id not in rows:
            order.append(activity_id)
            rows[activity_id] = {"activity_id": activity_id}
        rows[activity_id].update({
            key: value for key, value in event.items()
            if key not in {"kind", "sequence"}
        })
    return [rows[activity_id] for activity_id in order]


_COUNT_LABELS = {
    "knowledge_points": "知识点",
    "problems": "题目",
    "flash_cards": "闪卡",
    "figures": "图片",
}


def _prompt(message, context):
    workspace = context.get("workspace") or {}
    course = workspace.get("course") or "<course>"
    chapter = workspace.get("chapter") or "ch01"
    staged_dir = context.get("staged_manifest_dir") or f".lessonkit/jobs/<对话目录>"
    return (
        "你是 Lesson Kit 的外部 AI 教师。普通问答只读取上下文；只有学生明确要求修改内容或提交学习结论时，"
        "才可使用 lesson-kit data 写命令（等价写法 python -m workbench.cli.main data）。"
        "回答末尾如有写入，用简洁中文列出对象、动作和可访问路径，不展示命令、SQL 或工具日志。"
        "若学生明确要求选择或安排练习范围，可在回答末尾附一个 lessonkit-action JSON 区块；"
        "普通问答不要附带动作。格式为 ```lessonkit-action {\"type\":\"replace_practice_selection\","
        "\"kp_ids\":[\"知识点ID\"]} ```。"
        "若学生从目标表单发起一句话求助，可附 ```lessonkit-action {\"type\":\"prefill_goal_form\","
        "\"title\":\"…\",\"kind\":\"stage|long_term\",\"start_date\":\"YYYY-MM-DD或空\","
        "\"deadline\":\"YYYY-MM-DD或空\","
        "\"description\":\"…\"} ``` 代填目标字段（仅此意图可附，普通问答不得代填）。\n"
        "学生要求新增学习内容时，一律用 lessonkit-action 区块提交 content-bundle 清单；"
        "对话内出题禁止直接运行 lesson-kit ingest 或写数据库。合法的纯新增动作会自动执行、不弹确认；"
        "修改、删除、回滚和难度评级仍然只按学生的明确指令执行。\n"
        "content-bundle 契约：\n"
        "1) 清单可以很大：先把完整清单原样写进 " + staged_dir + " 下的一个 .json 文件（随对话保留），"
        "区块里只写 {\"type\":\"content-bundle\",\"staged_manifest\":\"<文件名>\"}；小清单也可以在区块里内联 manifest。\n"
        "2) 清单字段是 knowledge_points / problems / flash_cards 三个列表，可以只给其中一个，"
        "条数没有上限；一个清单就是一个批次。\n"
        "3) 每项都要有本清单内唯一的 key；题目 kp_ids、闪卡 kp_id、图片引用一律用 key 互相引用。"
        "内容 id 由服务端按当前课程与章顺序分配，不要自己编号，也不要复用池内已有 id。\n"
        "4) 知识点字段：knowledge_item（必填）、knowledge_type、importance、source_location、body、"
        "graph_label、related_kp_ids、fragile。\n"
        "5) 题目字段：problem_text（必填）、problem_type（calculation/proof/modeling/explanation/"
        "experiment/design/application/counterexample/other，必填）、kp_ids、source_kind、origin_kind、"
        "source_evidence（必填，例如 \"textbook 第12章 习题12-5\"）、source_answer、solution、"
        "solution_origin、topic_label/display_title/display_summary、"
        "figures（形如 [{\"key\":\"f1\",\"source_path\":\"任意本机路径\"}]）。\n"
        "6) 教材原题必须保留原题文字、数值、选项、作答形式与 problem_type，origin_kind 写 source_problem，"
        "不要为了套用现有流程把计算题、证明题改造成选择题；只有原题本身就是客观小题、"
        "或学生明确要求改编时，才写 quiz_type/options/answer_key/error_reason 变成微题"
        "（微题 subtype 仅 yes_no/single_choice/multiple_choice，改编用 origin_kind=adapted_problem）。"
        "自己生成的判断/选择题用 generated_grounded。OCR 错字可以对照原页纠正，其余不得润色改写。\n"
        "7) 图片在 problem_text 里用 ![](figure:f1) 引用，figures 给出源文件路径；服务端按原始字节复制到"
        ".lessonkit/figures/{course}/{chapter}/，不裁剪、不转换。声明了却没被引用、或缺必需图片的题目，"
        "会让整批零写入。\n"
        "8) 教材短答案放 source_answer，详细解析才放 solution；AI 按需生成的解析 solution_origin 写 generated，"
        "教材原有解析写 source。\n"
        "9) 闪卡字段：kp_id/front（≤100 字）/back（≤300 字）/source_evidence（必填），可选 topic_label；"
        "directions 只能是 [\"forward\"]（默认，单向）或 [\"forward\",\"reverse\"]（双向）。\n"
        "10) 出题入库不得携带任何难度字段，也不得自动建议或排队评级；只有学生明确要求给指定题目评级时，"
        "才可另行调用 lesson-kit difficulty 先 check 再 apply。\n"
        "11) 长度与取值：stem≤200 字、options 为 2–6 个互不相同的字符串且 answer_key 必须是其中之一"
        "（yes_no 用默认 是/否 对）、topic_label≤40 字、display_title≤80 字、display_summary≤200 字；"
        "数学乘号一律用 ×；正文可以带标题、列表、引用、代码、链接、图片、$数学$ 与 GFM 表格。\n"
        "服务端整批预检：任何一条不合法就整批零写入并逐条给出原因；请按原因修正完整清单后重新提交，"
        "不要擅自删掉不合格的条目，也不要向学生声称已写入。若上下文含 last_check_outcome："
        "成功则不要重复提交相同内容；被拒收则按逐条原因修正后重新提交完整区块。\n\n"
        "服务端重建的当前上下文：\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n\n学生消息：\n"
        + message
    )


def _last_check_outcome(folder):
    transcript = folder / "transcript.jsonl"
    try:
        with _LOCK:
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
        batch_id = result.get("batch_id")
        if not batch_id:
            return None
        summary = "、".join(
            f"{_COUNT_LABELS.get(key, key)} {value}"
            for key, value in result["counts"].items() if value
        )
        return (
            f"上一轮内容动作已成功入库：批次 {batch_id}"
            f"（{result.get('kind')}，{summary or '无新增'}）。不要重复提交相同内容。"
        )
    error = action.get("error")
    if not isinstance(error, str):
        return None
    if "manifest" in action:
        return (
            "上一轮内容动作被门禁拒收（零写入），逐条原因：\n"
            f"{error}\n"
            "请修正清单后重新提交完整的 lessonkit-action 区块。"
        )
    return f"上一轮内容动作区块无效：{error}。请重新提交符合契约的完整区块。"


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
        if conversation["provider"] != "pi":
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
    if conversation["provider"] == "pi":
        _run_rpc_turn(
            root, folder, workspace, conversation, conversation_path, event_path,
            turn_path, key, turn_id, message, context, provider,
        )
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
            **conversation_providers.hidden_launch_kwargs(),
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
    provider_output = []
    pi_messages = conversation["provider"] == "pi"
    state = {
        "text_parts": [], "result_text": "", "error_text": "",
        "answer_started": False, "pi_messages": pi_messages,
    }
    try:
        try:
            process.stdin.write(_prompt(message, context))
            process.stdin.close()
        except OSError:
            # A provider that died before reading its prompt (timeout, cancel, or
            # a launch that never came up) is reported by the checks below; a
            # broken pipe must not replace that outcome with a traceback.
            pass
        for line in process.stdout:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                provider_output.append(line.rstrip("\r\n"))
                if not pi_messages:
                    _append_event(
                        event_path, "activity", activity_id="provider-output",
                        activity_type="output", status="running", label="接收 Agent 输出",
                        output="\n".join(provider_output),
                    )
                continue
            _apply_record(
                conversation["provider"], data, event_path, conversation_path, state)
        return_code = process.wait()
    finally:
        timer.cancel()
        with _LOCK:
            _PROCESSES.pop(key, None)
    text_parts = state["text_parts"]
    result_text = state["result_text"]
    error_text = state["error_text"]

    if key in _CANCEL_REQUESTS:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed", label="本轮已停止",
            )
        _finish(folder, conversation_id, turn_id, "cancelled", "cancelled")
        return
    if key in _TIMEOUTS:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed", label="Agent 处理超时",
            )
        _finish(folder, conversation_id, turn_id, "failed", "provider timed out")
        return
    if return_code != 0:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed", label="Agent 处理失败",
            )
        _finish(folder, conversation_id, turn_id, "failed", f"provider exit code {return_code}")
        return
    answer = result_text or "".join(text_parts)
    if not answer:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed",
                label="Agent 处理失败" if error_text else "Agent 未返回回答",
            )
        _finish(folder, conversation_id, turn_id, "failed",
                error_text or "provider returned no assistant text")
        return

    if not pi_messages:
        _append_event(
            event_path, "activity", activity_id="provider-turn",
            activity_type="progress", status="done", label="Agent 处理完成",
        )
        if provider_output:
            _append_event(
                event_path, "activity", activity_id="provider-output",
                activity_type="output", status="done", label="Agent 输出已接收",
                output="\n".join(provider_output),
            )
    _store_answer(
        folder, conversation_path, turn_path, event_path, root, workspace,
        conversation_id, turn_id, message, context, answer,
        pi_messages=pi_messages,
    )


def _apply_record(provider_name, data, event_path, conversation_path, state):
    """Normalize one provider record into durable events and running totals."""
    normalized = conversation_providers.normalize_event(provider_name, data)
    if normalized is None:
        return
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
    if kind in {"text", "result"} and not state["answer_started"] \
            and not state["pi_messages"]:
        _append_event(
            event_path, "activity", activity_id="answer",
            activity_type="answer", status="running", label="组织回答",
        )
        state["answer_started"] = True
    _append_event(event_path, kind, **normalized)
    if kind == "text":
        state["text_parts"].append(normalized.get("text", ""))
    elif kind == "result":
        state["result_text"] = normalized.get("text", "")
    elif kind == "error":
        state["error_text"] = normalized.get("text", "") or state["error_text"]


def _store_answer(folder, conversation_path, turn_path, event_path, root, workspace,
                  conversation_id, turn_id, message, context, answer,
                  pi_messages=False):
    """Store one finished answer: actions, ingestion, mirror, done event."""
    answer, action = _extract_action(answer, context, folder)
    if not pi_messages:
        _append_event(
            event_path, "activity", activity_id="answer",
            activity_type="answer", status="done", label="回答已生成",
        )
    if action and isinstance(action.get("manifest"), dict):
        _append_event(
            event_path, "activity", activity_id="check-ingest",
            activity_type="tool", status="running", label="校验并写入学习内容",
        )
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
                source="bridge", backup_path=backup,
                course=action_pool.course)
            action["result"] = {
                key: applied[key]
                for key in ("batch_id", "kind", "counts", "origins", "backup_path", "applied")
                if key in applied
            }
            action["result"]["workspace"] = workspace["name"]
            _append_event(
                event_path, "activity", activity_id="check-ingest",
                activity_type="tool", status="done", label="学习内容已入库",
                output=f"批次 {applied['batch_id']}",
            )
        except Exception as exc:
            action["error"] = str(exc)
            _append_event(
                event_path, "activity", activity_id="check-ingest",
                activity_type="tool", status="failed", label="学习内容未入库",
                output=str(exc),
            )
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
    activities = _coalesced_activities(event_path)
    if activities:
        exchange["activities"] = activities
    with _LOCK:
        with (folder / "transcript.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(exchange, ensure_ascii=False) + "\n")
    _append_event(event_path, "done")
    _finish(folder, conversation_id, turn_id, "done", None)


def _run_rpc_turn(root, folder, workspace, conversation, conversation_path,
                  event_path, turn_path, key, turn_id, message, context, provider):
    """One turn over the conversation's persistent hidden Pi RPC process."""
    conversation_id = conversation["conversation_id"]
    pi_messages = True
    state = {
        "text_parts": [], "result_text": "", "error_text": "",
        "answer_started": False, "pi_messages": pi_messages,
    }
    try:
        process = PI_RPC.launch_with_retry(
            str(folder), provider, workspace["path"],
            conversation.get("provider_session_id"),
        )
    except pi_rpc.PiRpcError as exc:
        _append_event(event_path, "error", text=f"provider launch failed: {exc}")
        _finish(folder, conversation_id, turn_id, "failed", f"provider launch failed: {exc}")
        return
    with _LOCK:
        _PROCESSES[key] = process
    # RPC mode reports its native session through the handshake, not through an
    # event, so the mirror has to record it here to be able to resume later.
    session_id = getattr(process, "session_id", None)
    if isinstance(session_id, str) and session_id:
        conversation = _read_json(conversation_path)
        if conversation.get("provider_session_id") != session_id:
            conversation["provider_session_id"] = session_id
            conversation["updated_at"] = _now()
            _write_json(conversation_path, conversation)
    accepted = False
    settled = False
    try:
        try:
            process.prompt(_prompt(message, context))
            accepted = True
        except pi_rpc.PiRpcRejected as exc:
            # Rejected before acceptance: nothing ran, so one clean restart is safe.
            PI_RPC.discard(str(folder), process)
            process.close()
            try:
                process = PI_RPC.launch_with_retry(
                    str(folder), provider, workspace["path"],
                    conversation.get("provider_session_id"),
                )
                with _LOCK:
                    _PROCESSES[key] = process
                process.prompt(_prompt(message, context))
                accepted = True
            except (pi_rpc.PiRpcError, OSError) as retry_exc:
                _append_event(event_path, "error", text=f"provider launch failed: {retry_exc}")
                _finish(folder, conversation_id, turn_id, "failed",
                        f"provider launch failed: {retry_exc}")
                return
        except (pi_rpc.PiRpcError, OSError) as exc:
            _append_event(event_path, "error", text=f"provider launch failed: {exc}")
            _finish(folder, conversation_id, turn_id, "failed", f"provider launch failed: {exc}")
            return
        settled = False
        cancel_deadline = None
        for record in process.stream(provider.get("timeout_s", 300)):
            if key in _CANCEL_REQUESTS and cancel_deadline is None:
                # The abort has been sent; give the agent that grace to settle
                # before terminate/kill is used as the fallback.
                cancel_deadline = time.monotonic() + pi_rpc.ABORT_SETTLE_SECONDS
            if record.get("type") == "agent_settled":
                settled = True
            _apply_record("pi", record, event_path, conversation_path, state)
            if cancel_deadline is not None and (
                settled or time.monotonic() > cancel_deadline
            ):
                break
    except pi_rpc.PiRpcTimeout:
        with _LOCK:
            _TIMEOUTS.add(key)
        PI_RPC.discard(str(folder), process)
        process.close()
    except pi_rpc.PiRpcError as exc:
        # The process died after accepting the prompt: tools may already have
        # run, so the turn fails and the prompt is never replayed.
        PI_RPC.discard(str(folder), process)
        process.close()
        _append_event(event_path, "error", text=f"provider turn failed: {exc}")
        _finish(folder, conversation_id, turn_id, "failed", f"provider turn failed: {exc}")
        return
    finally:
        with _LOCK:
            _PROCESSES.pop(key, None)

    if key in _CANCEL_REQUESTS:
        if not settled:
            # The agent did not stop on its own: terminate/kill is the fallback.
            PI_RPC.discard(str(folder), process)
            process.close()
        _finish(folder, conversation_id, turn_id, "cancelled", "cancelled")
        return
    if key in _TIMEOUTS:
        _finish(folder, conversation_id, turn_id, "failed", "provider timed out")
        return
    answer = state["result_text"] or "".join(state["text_parts"])
    if not answer:
        _finish(folder, conversation_id, turn_id, "failed",
                state["error_text"] or "provider returned no assistant text")
        return
    _store_answer(
        folder, conversation_path, turn_path, event_path, root, workspace,
        conversation_id, turn_id, message, context, answer, pi_messages=pi_messages,
    )


_GOAL_KINDS = {"stage", "long_term"}


_ACTION_BLOCK_RE = re.compile(r"```lessonkit-action\s*([\s\S]*?)```", re.IGNORECASE)
CONTENT_ACTION_TYPES = ("check_ingest", "content-bundle")
FLASH_CARD_KIND = "flash-card-patch"
MICRO_QUIZ_KIND = "micro-quiz-patch"
CONTENT_BUNDLE_KIND = "content-bundle"
_MANIFEST_KINDS = {FLASH_CARD_KIND, MICRO_QUIZ_KIND, CONTENT_BUNDLE_KIND}


def _extract_action(answer, context, folder=None):
    """Parse one governed content action, with no keyword gate.

    A syntactically valid append-only action runs on its own: the learner's
    words never decide whether a structured action is honoured. Practice and
    goal actions keep their explicit intents. ``folder`` is the owning
    conversation's jobs directory, the only place a staged manifest may be read
    from.
    """
    blocks = list(_ACTION_BLOCK_RE.finditer(answer))
    if not blocks:
        return answer, None
    applied = None
    invalid_json = False
    matched_intent = False
    recognized = False
    for match in blocks:
        try:
            raw = json.loads(match.group(1).strip())
        except (TypeError, ValueError):
            invalid_json = True
            continue
        if not isinstance(raw, dict):
            continue
        action = None
        raw_type = raw.get("type")
        if raw_type in ("replace_practice_selection", "prefill_goal_form"):
            # Practice and goal actions stay intent-gated: they change what the
            # learner sees, so they are not append-only content.
            recognized = True
            if raw_type == "replace_practice_selection" and context.get("practice_intent"):
                matched_intent = True
                allowed = set(context.get("knowledge_point_ids") or [])
                ids = []
                for item in raw.get("kp_ids") or []:
                    if item in allowed and item not in ids:
                        ids.append(item)
                if ids:
                    action = {"type": raw_type, "kp_ids": ids}
            elif raw_type == "prefill_goal_form" and context.get("goal_intent"):
                matched_intent = True
                # An action without a usable title is discarded entirely (spec).
                action = _clean_goal_form_action(raw)
        elif raw_type in CONTENT_ACTION_TYPES or (
            raw_type is None and raw.get("kind") in _MANIFEST_KINDS
        ):
            # Agents sometimes emit the bare manifest without the action wrapper;
            # both forms are accepted.
            action = _clean_content_action(raw, folder)
        if action is not None:
            applied = action
            break
    cleaned = _ACTION_BLOCK_RE.sub("", answer).strip()
    if applied is not None:
        return cleaned, applied
    if invalid_json:
        return cleaned, {"type": "check_ingest", "error": "action block is not valid JSON"}
    if matched_intent:
        return cleaned, None
    if recognized:
        return cleaned, {"ignored": "no block matched the active intent"}
    if blocks:
        return cleaned, {
            "type": "check_ingest",
            "error": "回复包含 lessonkit-action 区块，但没有区块符合已知动作契约，未写入任何内容",
        }
    return answer, None


def _clean_content_action(raw, folder=None):
    """Resolve one content action, loading its staged manifest when referenced."""
    action = {"type": "check_ingest"}
    reference = raw.get("staged_manifest") or raw.get("manifest_path")
    manifest = raw.get("manifest") if raw.get("type") == "check_ingest" else raw
    if reference is not None:
        action["staged_manifest"] = str(reference)
        if folder is None:
            action["error"] = "staged manifest needs a conversation folder to read from"
            return action
        try:
            manifest = ingest.read_staged_manifest(folder, reference)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            action["error"] = str(exc)
            return action
    error = _manifest_contract_error(manifest)
    if error:
        action["error"] = error
        return action
    action["manifest"] = manifest
    return action


def _manifest_contract_error(manifest):
    """Return why a manifest is not a known governed shape, or "" when it is."""
    if not isinstance(manifest, dict):
        return "manifest must be an object"
    kind = manifest.get("kind")
    if kind in {FLASH_CARD_KIND, MICRO_QUIZ_KIND}:
        if not isinstance(manifest.get("items"), list) or not manifest["items"]:
            return "manifest items must be a non-empty list"
        return ""
    if kind == CONTENT_BUNDLE_KIND:
        for field in ("knowledge_points", "problems", "flash_cards"):
            value = manifest.get(field)
            if isinstance(value, list) and value:
                return ""
        return ("content-bundle requires at least one knowledge point, "
                "problem, or flash card")
    return (f"manifest kind must be {FLASH_CARD_KIND}, {MICRO_QUIZ_KIND}, "
            f"or {CONTENT_BUNDLE_KIND}")


def _clean_check_ingest_action(manifest):
    error = _manifest_contract_error(manifest)
    if error:
        return {"type": "check_ingest", "error": error}
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
    if isinstance(process, pi_rpc.PiRpcProcess):
        # RPC abort first; the turn thread kills only if the run never settles.
        process.abort()
    elif process is not None:
        _stop_process(process)
    return {"conversation_id": conversation_id, "turn_id": conversation["current_turn_id"], "status": "cancelling"}


def shutdown():
    """Close every long-lived provider process (server shutdown, tests)."""
    return PI_RPC.close_all()
