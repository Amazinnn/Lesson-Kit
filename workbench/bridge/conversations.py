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
from workbench.bridge import conversation_actions, conversation_providers, pi_rpc
from workbench.data import practice_sets
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
# A print-mode turn is failed for silence, not for duration: any output line
# resets the clock, and while a command or tool runs the longer tool budget
# applies so a slow command is never cut off mid-run.
DEFAULT_IDLE_SECONDS = conversation_providers.DEFAULT_IDLE_SECONDS
DEFAULT_TOOL_SECONDS = pi_rpc.TOOL_SECONDS
BUSY_ACTIVITY_STATUSES = {"running"}
# A command or tool in flight is the one thing allowed to be silent for long.
BUSY_ACTIVITY_TYPES = {"command", "tool"}
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


def create(pool, provider_name, title="", model=None, entry=None):
    conversation_providers.get(provider_name)
    target = _resolve_target(provider_name, model=model, entry=entry)
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
            "provider": target["provider"],
            "model": target["model"],
            "model_entry": target.get("entry"),
            "model_args": target.get("args", []),
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
    transcript_by_turn = {}
    transcript_without_turn = []
    transcript = _conversation_dir(pool, conversation_id) / "transcript.jsonl"
    with _LOCK:
        lines = transcript.read_text(encoding="utf-8").splitlines() if transcript.is_file() else []
    for line in lines:
        exchange = json.loads(line)
        turn_id = exchange.get("turn_id")
        if turn_id:
            transcript_by_turn[turn_id] = exchange
        else:
            transcript_without_turn.append(exchange)

    turns = []
    folder = _conversation_dir(pool, conversation_id)
    for path in folder.glob("turn-*.json"):
        try:
            turn = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        turns.append((turn.get("turn_id") or path.stem, turn))
    turns.sort(key=lambda item: int(item[0][5:]) if TURN_ID.fullmatch(item[0]) else 0)

    messages = []
    # Exchanges without turn ids predate durable turn artifacts. Show them
    # before all new turn projections so a later accepted turn cannot reorder
    # that legacy history to the bottom.
    for exchange in transcript_without_turn:
        assistant = {"role": "assistant", "content": exchange["assistant"]}
        for key in ("actions", "action", "activities"):
            if exchange.get(key):
                assistant[key] = exchange[key]
        messages.extend([
            {"role": "user", "content": exchange["user"]},
            assistant,
        ])
    for turn_id, turn in turns:
        exchange = transcript_by_turn.pop(turn_id, None)
        if exchange is not None:
            user = {
                "role": "user", "content": exchange["user"], "turn_id": turn_id,
                "status": "done",
            }
            if turn.get("submission_id"):
                user["submission_id"] = turn["submission_id"]
            messages.append(user)
            assistant = {"role": "assistant", "content": exchange["assistant"],
                         "turn_id": turn_id}
            for key in ("actions", "action", "activities"):
                if exchange.get(key):
                    assistant[key] = exchange[key]
            messages.append(assistant)
            continue
        accepted_message = turn.get("message")
        # Old incomplete turn artifacts did not persist user input. Do not
        # invent a message for them.
        if not isinstance(accepted_message, str):
            continue
        user = {
            "role": "user", "content": accepted_message, "turn_id": turn_id,
            "status": turn.get("status", "failed"),
        }
        if turn.get("submission_id"):
            user["submission_id"] = turn["submission_id"]
        if turn.get("error"):
            user["error"] = conversation_providers._pi_safe_text(
                turn["error"], conversation_providers._PI_SUMMARY_LIMIT,
            )
        messages.append(user)
        activities = _coalesced_activities(
            _events_file(pool, conversation_id, turn_id),
        )
        partial = turn.get("partial_output")
        if activities or (isinstance(partial, str) and partial):
            assistant = {"role": "assistant", "turn_id": turn_id,
                         "status": turn.get("status", "failed")}
            if activities:
                assistant["activities"] = activities
            if isinstance(partial, str) and partial:
                assistant.update({"content": partial, "partial": True})
            messages.append(assistant)

    for turn_id, exchange in sorted(
        transcript_by_turn.items(),
        key=lambda item: int(item[0][5:]) if TURN_ID.fullmatch(item[0]) else 0,
    ):
        assistant = {"role": "assistant", "content": exchange["assistant"],
                     "turn_id": turn_id}
        for key in ("actions", "action", "activities"):
            if exchange.get(key):
                assistant[key] = exchange[key]
        messages.extend([
            {"role": "user", "content": exchange["user"], "turn_id": turn_id},
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


def _resolve_target(provider_name, model=None, entry=None):
    if entry is not None:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("model entry must be a non-empty string")
        return conversation_providers.resolve_target(provider_name, entry_name=entry)
    if model is not None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        match = next(
            (item for item in conversation_providers.discover_entries()
             if item["provider"] == provider_name and item["name"] == model),
            None,
        )
        if match:
            return {
                "provider": provider_name,
                "model": match.get("model"),
                "args": list(match.get("args", [])),
                "entry": match["name"],
            }
        if len(model.split()) > 1:
            raise ValueError("unknown model entry — a raw model id must be one token")
    return conversation_providers.resolve_target(provider_name, model=model)


def _pi_model_parts(model):
    if not isinstance(model, str) or "/" not in model:
        return None
    provider, model_id = model.split("/", 1)
    return (provider, model_id) if provider and model_id else None


def set_model(pool, conversation_id, model, provider=None, entry=None):
    """Switch models inside one immutable Agent harness.

    A conversation is permanently bound to the harness chosen at creation.
    Same-Pi switches use Pi's live RPC set_model when possible; Codex and Claude
    keep their native session id and receive the new --model on the next turn.
    """
    path = _conversation_file(pool, conversation_id)
    with _LOCK:
        record = _recover_interrupted(pool, _read_json(path))
        if record["status"] == "running":
            raise ConversationConflict("conversation has a running turn")
        harness = record["provider"]
        if provider is not None and provider != harness:
            raise ConversationConflict(
                "conversation harness cannot be changed; create a new conversation")
        if model is None and entry is None:
            target = _resolve_target(harness, model=None)
        else:
            target = _resolve_target(harness, model=model, entry=entry)
        folder = _conversation_dir(pool, conversation_id)
        target_changed = (
            record.get("model") != target.get("model")
            or list(record.get("model_args") or []) != list(target.get("args", []))
        )
        if harness == "pi" and target_changed:
            process = PI_RPC.active().get(str(folder))
            if process is not None:
                parts = _pi_model_parts(target.get("model"))
                if parts:
                    try:
                        process.set_model(*parts)
                    except pi_rpc.PiRpcError:
                        stale = PI_RPC.discard(str(folder), process)
                        if stale is not None:
                            stale.close()
                else:
                    stale = PI_RPC.discard(str(folder), process)
                    if stale is not None:
                        stale.close()
        record.update({
            "model": target.get("model"),
            "model_entry": target.get("entry"),
            "model_args": list(target.get("args", [])),
            "updated_at": _now(),
        })
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
    return _turn_response(_read_json(_turn_file(pool, conversation_id, turn_id)))


def _get_turn_record(pool, conversation_id, turn_id):
    _recover_interrupted(
        pool, _read_json(_conversation_file(pool, conversation_id))
    )
    return _read_json(_turn_file(pool, conversation_id, turn_id))


def _turn_response(turn):
    """Keep captured prompt context and client payload out of public turn reads."""
    return {
        key: value for key, value in turn.items()
        if key in {
            "turn_id", "status", "error", "created_at", "updated_at",
            "partial_output", "action", "actions", "submission_id", "retry_of",
        }
    }


def find_submission(pool, conversation_id, message, submission_id, submitted_fields):
    """Return an accepted turn for an idempotent retry, or raise on changed input."""
    if submission_id is None:
        return None
    if not isinstance(submission_id, str) or not submission_id.strip():
        raise ValueError("submission_id must be a non-empty string")
    folder = _conversation_dir(pool, conversation_id)
    with _LOCK:
        for path in folder.glob("turn-*.json"):
            prior = _read_json(path)
            if prior.get("submission_id") != submission_id.strip():
                continue
            if prior.get("message") != message \
                    or prior.get("submitted_fields", {}) != submitted_fields:
                raise ConversationConflict("submission_id was already used with different input")
            return _turn_response(prior)
    return None


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
        transcript = _conversation_dir(pool, record["conversation_id"]) / "transcript.jsonl"
        with _LOCK:
            transcript_lines = transcript.read_text(encoding="utf-8").splitlines() \
                if transcript.is_file() else []
        completed = False
        for line in transcript_lines:
            try:
                if json.loads(line).get("turn_id") == turn_id:
                    completed = True
                    break
            except json.JSONDecodeError:
                continue
        error = None if completed else "workbench restarted while the provider turn was running"
        turn_path = _turn_file(pool, record["conversation_id"], turn_id)
        if turn_path.is_file():
            turn = _read_json(turn_path)
            turn.update({
                "status": "done" if completed else "failed",
                "error": error, "updated_at": _now(),
            })
            if not completed:
                partial_output = _partial_output_from_events(
                    _events_file(pool, record["conversation_id"], turn_id),
                )
                if partial_output:
                    turn["partial_output"] = conversation_providers._pi_safe_text(
                        partial_output, conversation_providers._PI_OUTPUT_LIMIT,
                    )
            _write_json(turn_path, turn)
            if error:
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
    if kind == "error" and fields.get("text"):
        fields["text"] = conversation_providers._pi_safe_text(
            fields["text"], conversation_providers._PI_SUMMARY_LIMIT,
        )
    elif kind == "activity":
        for field, limit in (("detail", conversation_providers._PI_DETAIL_LIMIT),
                             ("output", conversation_providers._PI_OUTPUT_LIMIT),
                             ("summary", conversation_providers._PI_SUMMARY_LIMIT)):
            if fields.get(field):
                fields[field] = conversation_providers._pi_safe_text(fields[field], limit)
        impact = fields.get("impact")
        if isinstance(impact, dict) and impact.get("summary"):
            impact = dict(impact)
            impact["summary"] = conversation_providers._pi_safe_text(
                impact["summary"], conversation_providers._PI_SUMMARY_LIMIT,
            )
            fields["impact"] = impact
    with _LOCK:
        existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        event = {"sequence": len(existing) + 1, "kind": kind, **fields}
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _partial_output_from_events(path):
    """Rebuild only assistant text already streamed for an interrupted turn."""
    with _LOCK:
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    text_parts = []
    result_text = ""
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("kind") == "text":
            text_parts.append(event.get("text", ""))
        elif event.get("kind") == "result":
            result_text = event.get("text", "")
    return result_text or "".join(text_parts)


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
    "keyless": "未录答案键",
    "difficulty_cleared": "评级清空",
}



class _TurnWatchdog:
    """Fail a print-mode turn that stops making progress.

    The budget measures silence: ``touch`` on every output line and ``observe``
    on every normalized activity, so a turn that keeps working is never cut off
    for taking long. A command or tool in flight swaps in the longer budget;
    everything else — including the turn-level progress activity, which is
    "running" for the whole turn — stays on the idle budget.
    """

    TICK_SECONDS = 0.1

    def __init__(self, process, idle_seconds, tool_seconds, on_timeout):
        self.process = process
        self.idle_seconds = idle_seconds
        self.tool_seconds = tool_seconds
        self.on_timeout = on_timeout
        self._busy = set()
        self._last = time.monotonic()
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)

    def start(self):
        self._thread.start()

    def cancel(self):
        self._stopped.set()

    def touch(self):
        """One line of provider output is progress."""
        self._last = time.monotonic()

    def observe(self, normalized):
        """Track which commands and tools are in flight, and count this as progress."""
        self._last = time.monotonic()
        if normalized.get("kind") != "activity":
            return
        if normalized.get("activity_type") not in BUSY_ACTIVITY_TYPES:
            return
        activity_id = normalized.get("activity_id")
        if activity_id is None:
            return
        if normalized.get("status") in BUSY_ACTIVITY_STATUSES:
            self._busy.add(activity_id)
        else:
            self._busy.discard(activity_id)

    def _watch(self):
        while not self._stopped.wait(self.TICK_SECONDS):
            if self.process.poll() is not None:
                return
            budget = self.tool_seconds if self._busy else self.idle_seconds
            if time.monotonic() - self._last > budget:
                self.on_timeout()
                return


def _prompt(message, context):
    """Small always-on map; detailed operational contracts are loaded on demand."""
    workspace = context.get("workspace") or {}
    workspace_name = workspace.get("name") or "<工作区名>"
    staged_dir = context.get("staged_manifest_dir") or ".lessonkit/jobs/<对话目录>"
    contract_cli = "python -m workbench.bridge.agent_contracts"
    return (
        "你是 Lesson Kit 的外部 AI 教师。当前页面只是上下文锚点，不是不可推翻的焦点："
        "context.focus 若存在，优先围绕 focus 回答；context.working_set 是当前学习活动的少量近期工作记忆。"
        "如果学生的问题明显跨出当前上下文，你可以且应该主动读取 Lesson Kit 数据，不必先征求读取许可。"
        "查询范围随问题扩大：当前对象→近期工作集→相关知识点/题目→历史作答与练习→章节/课程。\n"
        "凡是判断学生‘以前/最近/经常/薄弱/进步如何’，必须先依据实际学习记录。"
        "面向学生给出少量、直接支撑结论且可理解的证据（题目内容/主题、具体作答表现、练习时间或场景）；"
        "不要把数据库主键、哈希、内部文件名或实现路径当成主要证据。先概括，再给 1–3 个代表例子；"
        "证据不足时降低结论强度或明确说查不到。\n"
        "普通问答只读取上下文和数据；只有学生明确要求修改内容或提交学习结论时，"
        "才可使用 lesson-kit data 写命令。读取可以主动，写入必须有明确用户意图。"
        "参数不确定时先查 `lesson-kit <命令> --help`，不要猜。"
        "工作区参数紧跟命令，例如 `lesson-kit data " + workspace_name
        + " create kp --input <清单文件>`。每条 Lesson Kit 命令单独执行；不要接管道，"
        "不要用 `|| true` 或命令串掩盖退出码。输出太长可 `lesson-kit … > out.txt` 后读取；"
        "需要确认退出码时检查 `echo $?`。只有真实成功才能宣称成功，不要谎报成功。\n"
        "详细操作规则按需读取，而不是每轮重复背诵：`" + contract_cli + " list`。"
        "可用主题：commands（命令/退出码）、attempts（记录/更正作答）、practice（组卷/选题/保存试卷）、"
        "actions（前端动作）、content（新增/修改学习内容）。执行对应专门动作前先读取相应主题；"
        "普通教学问答无需读取无关契约。\n"
        "若学生明确要求选择或安排练习范围，可在回答末尾附一个 lessonkit-action JSON 区块；"
        "普通问答不要附带动作。格式为 ```lessonkit-action {\"type\":\"replace_practice_selection\","
        "\"kp_ids\":[\"知识点ID\"]} ```。"
        "若学生从目标表单发起一句话求助，可附 ```lessonkit-action {\"type\":\"prefill_goal_form\","
        "\"title\":\"…\",\"kind\":\"stage|long_term\",\"start_date\":\"YYYY-MM-DD或空\","
        "\"deadline\":\"YYYY-MM-DD或空\",\"description\":\"…\"} ``` 代填目标字段"
        "（仅此意图可附，普通问答不得代填）。\n"
        "content-bundle 契约（v2，详细版按需读取 `" + contract_cli + " content`）："
        "学生要求新增学习内容时禁止直接运行 lesson-kit ingest；使用 content-bundle。"
        "大清单写入当前 staged_manifest_dir=" + staged_dir + "，动作只引用 staged_manifest。"
        "最小地图：knowledge_points / problems / flash_cards，条数没有上限；"
        "一份清单可以跨任意多章，缺少单项或清单章号会点名拒收且不回退当前章，服务端按章各记一个批次；"
        "同一回复里的 content-bundle 区块都会被依次应用，不要只导一章就停下来。"
        "6) 题目字段：problem_text、problem_type（machine enum: calculation/proof/modeling/explanation/experiment/design/application/counterexample/other; 中文释义仅作说明：proof = 证明题）、kp_ids、source_kind、"
        "origin_kind、source_evidence、source_answer、solution、solution_origin、display_title、"
        "display_summary、figures；图片引用形如 figure:f1。"
        "7) 练习题型三选一：普通题、yes_no、single_choice/multiple_choice；"
        "客观题即使题源没有正确答案也照样入库，可暂缺 answer_key。"
        "来源语义包含 source_problem、adapted_problem、generated_grounded。"
        "11) 闪卡字段：kp_id/front/back/source_evidence，可选 topic_label；directions 表示单/双向。"
        "12) 出题入库不携带难度字段；只有学生明确要求评级时才用 lesson-kit difficulty。"
        "数学乘号一律用 ×。学生明确要求修改已有题目时使用 problem-patch 原地修改，不要删了重导。"
        "服务端整份清单预检；失败零写入并按原因修正。若 context 中有 last_check_outcome，"
        "按其结果避免重复提交或修正后再提交。\n\n"
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
    actions = exchange.get("actions")
    if isinstance(actions, list) and actions:
        return _content_outcome(actions)
    action = exchange.get("action")
    if not isinstance(action, dict):
        return None
    if action.get("type") == "check_ingest" and "manifest" in action:
        return _content_outcome([action])
    return _notice_outcome(action)


def _content_outcome(actions):
    """What the agent must know about the content actions it just emitted."""
    applied = []
    failures = []
    invalid = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        result = action.get("result")
        if isinstance(result, dict) and (result.get("batches") or result.get("batch_id")):
            applied.append(result)
        elif action.get("error"):
            # A manifest that failed the gate is correctable; a block that never
            # became a manifest is not.
            (failures if "manifest" in action else invalid).append(str(action["error"]))
    lines = []
    for result in applied:
        summary = "、".join(
            f"{_COUNT_LABELS.get(key, key)} {value}"
            for key, value in (result.get("counts") or {}).items() if value
        )
        lines.append(
            f"上一轮内容动作已成功入库：{_batch_label(result)}"
            f"（{result.get('kind')}，{summary or '无新增'}）。不要重复提交相同内容；"
            "若学生要求的内容还有未导入的章，直接继续提交剩余部分，不要让学生再说一次「继续」。"
        )
    if failures:
        lines.append(
            "上一轮内容动作被门禁拒收（零写入），逐条原因：\n"
            + "\n".join(failures)
            + "\n请修正清单后重新提交完整的 lessonkit-action 区块。"
        )
    if invalid:
        lines.append(
            f"上一轮内容动作区块无效：{invalid[0]}。请重新提交符合契约的完整区块。"
        )
    if not lines:
        return None
    return "\n".join(lines)


def _notice_outcome(action):
    if action.get("ignored"):
        return (
            f"上一轮回复附带了 lessonkit-action 区块，但未被接受（{action['ignored']}），"
            "未写入任何内容。不要向学生声称已写入；只有收到批次确认才算成功。"
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


def start_turn(pool, workspace, conversation_id, message, context, *,
               submission_id=None, submitted_fields=None, retry_of=None):
    folder = _conversation_dir(pool, conversation_id)
    conversation_path = folder / "conversation.json"
    _recover_interrupted(pool, _read_json(conversation_path))
    with _LOCK:
        conversation = _read_json(conversation_path)
        fields = submitted_fields if isinstance(submitted_fields, dict) else {}
        if retry_of is not None and submission_id is None:
            raise ValueError("submission_id is required for an explicit retry")
        prior = find_submission(pool, conversation_id, message, submission_id, fields)
        if prior:
            return prior
        if submission_id is not None:
            submission_id = submission_id.strip()
        if conversation["status"] == "running":
            raise ConversationConflict("conversation already has a running turn")
        retry_context = None
        if retry_of is not None:
            retry_id = _require_id(retry_of, TURN_ID, "turn")
            retry_path = _turn_file(pool, conversation_id, retry_id)
            if not retry_path.is_file():
                raise ConversationConflict("retry source turn does not exist")
            previous = _read_json(retry_path)
            if previous.get("status") not in {"failed", "cancelled"} \
                    or previous.get("message") != message:
                raise ConversationConflict("only the same accepted failed turn can be retried")
            if fields != previous.get("submitted_fields", {}):
                raise ConversationConflict("retry input must match the original accepted message")
            retry_context = previous.get("context")
        turn_number = _next_number(folder.glob("turn-*.json"), "turn-")
        turn_id = f"turn-{turn_number:03d}"
        now = _now()
        turn_context = dict(retry_context if retry_context is not None else context)
        last_check_outcome = _last_check_outcome(folder)
        if last_check_outcome:
            turn_context["last_check_outcome"] = last_check_outcome
        turn = {
            "turn_id": turn_id,
            "status": "running",
            "error": None,
            "message": message,
            "context": turn_context,
            "created_at": now,
            "updated_at": now,
        }
        if submission_id is not None:
            turn["submission_id"] = submission_id
            turn["submitted_fields"] = fields
        if retry_of is not None:
            turn["retry_of"] = retry_of
        _write_json(folder / f"{turn_id}.json", turn)
        conversation.update({"status": "running", "current_turn_id": turn_id, "updated_at": now})
        _write_json(conversation_path, conversation)
        key = (str(folder), turn_id)
        _ACTIVE_TURNS.add(key)
        _CANCEL_REQUESTS.discard(key)
        _TIMEOUTS.discard(key)
        thread = threading.Thread(
            target=_run_turn_safely,
            args=(
                pool.root, pool.jobs_dir(), workspace, conversation_id, turn_id,
                message, turn_context,
            ),
            daemon=True,
        )
        try:
            thread.start()
        except Exception as exc:
            _finish(
                folder, conversation_id, turn_id, "failed",
                f"provider launch failed: {exc}",
            )
            turn = _read_json(_turn_file(pool, conversation_id, turn_id))
    return _turn_response(turn)


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
            _finish(
                folder, conversation_id, turn_id, "failed", f"provider turn failed: {exc}",
                partial_output=_partial_output_from_events(
                    folder / f"{turn_id}.events.jsonl",
                ),
            )


def _run_turn(root, jobs_dir, workspace, conversation_id, turn_id, message, context):
    folder = jobs_dir / conversation_id
    conversation_path = folder / "conversation.json"
    turn_path = folder / f"{turn_id}.json"
    event_path = folder / f"{turn_id}.events.jsonl"
    key = (str(folder), turn_id)
    conversation = _read_json(conversation_path)
    try:
        provider = conversation_providers.get(conversation["provider"])
        provider = {
            **provider,
            "model": conversation.get("model"),
            "args": list(conversation.get("model_args") or provider.get("args", [])),
        }
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

    # The budget measures silence, not total time: a provider that keeps
    # printing stays alive however long it works, and a command running quietly
    # gets the longer tool budget instead of being cut off mid-flight.
    watchdog = _TurnWatchdog(
        process,
        idle_seconds=provider.get("timeout_s", DEFAULT_IDLE_SECONDS),
        tool_seconds=provider.get("tool_timeout_s", DEFAULT_TOOL_SECONDS),
        on_timeout=timeout_process,
    )
    watchdog.start()
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
            watchdog.touch()
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
                conversation["provider"], data, event_path, conversation_path, state,
                watchdog=watchdog)
        return_code = process.wait()
    finally:
        watchdog.cancel()
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
        _finish(
            folder, conversation_id, turn_id, "cancelled", "cancelled",
            partial_output=result_text or "".join(text_parts),
        )
        return
    if key in _TIMEOUTS:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed", label="Agent 处理超时",
            )
        _finish(folder, conversation_id, turn_id, "failed", "provider timed out",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
        return
    if return_code != 0:
        if not pi_messages:
            _append_event(
                event_path, "activity", activity_id="provider-turn",
                activity_type="progress", status="failed", label="Agent 处理失败",
            )
        _finish(folder, conversation_id, turn_id, "failed", f"provider exit code {return_code}",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
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
                error_text or "provider returned no assistant text",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
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


def _apply_record(provider_name, data, event_path, conversation_path, state,
                  watchdog=None):
    """Normalize one provider record into durable events and running totals."""
    normalized = conversation_providers.normalize_event(provider_name, data)
    if normalized is None:
        return
    if watchdog is not None:
        watchdog.observe(normalized)
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


def _apply_content_action(action, root, workspace, conversation_id, turn_id,
                          event_path, activity_id, index=0):
    """Apply one content action and record its batches on the action itself."""
    _append_event(
        event_path, "activity", activity_id=activity_id,
        activity_type="tool", status="running", label="校验并写入学习内容",
    )
    action_pool = Pool(
        root=root,
        db_path=root / workspace["db"],
        course=workspace.get("active_course", ""),
        chapter=workspace.get("active_chapter", ""),
    )
    # Every action of a turn needs its own recovery copy: the ingest layer
    # refuses to clobber an existing one, which is what makes a later action in
    # the same turn fail if they share a name.
    suffix = f"-{index + 1}" if index else ""
    backup = action_pool.db_path.with_name(
        action_pool.db_path.name
        + f".{conversation_id}-{turn_id}-ingest-backup{suffix}")
    try:
        applied = ingest.apply_batch(
            action_pool.db_path, action["manifest"],
            source="bridge", backup_path=backup,
            course=action_pool.course)
        action["result"] = {
            key: applied[key]
            for key in ("batch_id", "kind", "counts", "origins", "batches",
                        "backup_path", "applied", "typesetting")
            if key in applied
        }
        action["result"]["workspace"] = workspace["name"]
        _append_event(
            event_path, "activity", activity_id=activity_id,
            activity_type="tool", status="done", label="学习内容已入库",
            output=_batch_label(applied),
            impact={"status": "known", "summary": _batch_label(applied)},
        )
    except Exception as exc:
        action["error"] = str(exc)
        _append_event(
            event_path, "activity", activity_id=activity_id,
            activity_type="tool", status="failed", label="学习内容未入库",
            output=str(exc),
        )
    finally:
        action_pool.close()


def _batch_label(applied):
    """One chapter reads as its batch id; several name their chapters."""
    batches = applied.get("batches") or []
    if len(batches) <= 1:
        return f"批次 {applied.get('batch_id')}"
    return "批次 " + "、".join(
        f"{batch['batch_id']}（{batch.get('chapter') or '?'}）" for batch in batches
    )

def _verified_paper_artifact(notice, root, workspace, event_path):
    """Show an Artifact only for a managed Paper that actually exists.

    The contract asks the model to emit this action only after a successful
    `lesson-kit papers ... save` receipt, so an unknown id means the claim is
    wrong. The managed record is the only source for identity, title and count.
    """
    record = None
    pool = None
    try:
        pool = Pool(
            root=root,
            db_path=root / workspace["db"],
            course=workspace.get("active_course", ""),
            chapter=workspace.get("active_chapter", ""),
        )
        record = practice_sets.get_saved(pool, notice["practice_set_id"])
    except (FileNotFoundError, KeyError, ValueError, OSError):
        record = None
    finally:
        if pool is not None:
            pool.close()
    if record is None:
        _append_event(
            event_path, "activity", activity_id="paper-artifact",
            activity_type="tool", status="failed",
            label=f"未找到已保存试卷 {notice.get('practice_set_id')}，不显示工件",
        )
        return None
    return {
        "type": "paper_artifact",
        "practice_set_id": record["practice_set_id"],
        "title": str(record.get("title") or record["practice_set_id"])[:120],
        "summary": str(notice.get("summary") or "")[:300],
        "item_count": record.get("count"),
    }


def _store_answer(folder, conversation_path, turn_path, event_path, root, workspace,
                  conversation_id, turn_id, message, context, answer,
                  pi_messages=False):
    """Store one finished answer: actions, ingestion, mirror, done event."""
    answer, content_actions, notice = _extract_action(answer, context, folder)
    if notice is not None and notice.get("type") == "paper_artifact":
        notice = _verified_paper_artifact(notice, root, workspace, event_path)
    if not pi_messages:
        _append_event(
            event_path, "activity", activity_id="answer",
            activity_type="answer", status="done", label="回答已生成",
        )
    for index, action in enumerate(content_actions):
        activity_id = "check-ingest" if index == 0 else f"check-ingest-{index + 1}"
        if isinstance(action.get("manifest"), dict):
            _apply_content_action(
                action, root, workspace, conversation_id, turn_id, event_path,
                activity_id, index,
            )

    conversation = _read_json(conversation_path)
    turn = _read_json(turn_path)
    if content_actions:
        turn["actions"] = content_actions
    if notice is not None:
        turn["action"] = notice
    elif len(content_actions) == 1:
        turn["action"] = content_actions[0]
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
    if content_actions:
        exchange["actions"] = content_actions
    if "action" in turn:
        exchange["action"] = turn["action"]
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
        try:
            process = PI_RPC.launch_with_retry(
                str(folder), provider, workspace["path"],
                conversation.get("provider_session_id"),
            )
        except pi_rpc.PiRpcError as exc:
            if not conversation.get("provider_session_id"):
                raise
            # A resumed session can refuse a different model after an in-chat
            # switch: drop the native session once and start fresh — the local
            # mirror keeps the whole history either way.
            conversation = _read_json(conversation_path)
            conversation["provider_session_id"] = None
            conversation["updated_at"] = _now()
            _write_json(conversation_path, conversation)
            _append_event(
                event_path, "activity", activity_id="model-switch",
                activity_type="progress", status="done",
                label="切换模型后无法续接原会话，已开启新会话（本地历史不受影响）",
            )
            process = PI_RPC.launch_with_retry(
                str(folder), provider, workspace["path"], None,
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
        for record in process.stream(
            provider.get("timeout_s", DEFAULT_IDLE_SECONDS),
            provider.get("tool_timeout_s", DEFAULT_TOOL_SECONDS),
        ):
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
        _finish(folder, conversation_id, turn_id, "cancelled", "cancelled",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
        return
    if key in _TIMEOUTS:
        _finish(folder, conversation_id, turn_id, "failed", "provider timed out",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
        return
    answer = state["result_text"] or "".join(state["text_parts"])
    if not answer:
        _finish(folder, conversation_id, turn_id, "failed",
                state["error_text"] or "provider returned no assistant text",
                partial_output=state["result_text"] or "".join(state["text_parts"]))
        return
    _store_answer(
        folder, conversation_path, turn_path, event_path, root, workspace,
        conversation_id, turn_id, message, context, answer, pi_messages=pi_messages,
    )


_extract_action = conversation_actions.extract_action


def _finish(folder, conversation_id, turn_id, status, error, partial_output=None):
    now = _now()
    key = (str(folder), turn_id)
    with _LOCK:
        conversation_path = folder / "conversation.json"
        conversation = _read_json(conversation_path)
        conversation.update({"status": "idle", "current_turn_id": None, "updated_at": now})
        _write_json(conversation_path, conversation)
        turn_path = folder / f"{turn_id}.json"
        turn = _read_json(turn_path)
        turn.update({
            "status": status,
            "error": conversation_providers._pi_safe_text(
                error, conversation_providers._PI_SUMMARY_LIMIT,
            ) if error else None,
            "updated_at": now,
        })
        if status in {"failed", "cancelled"} and partial_output:
            turn["partial_output"] = conversation_providers._pi_safe_text(
                partial_output, conversation_providers._PI_OUTPUT_LIMIT,
            )
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
