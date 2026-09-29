"""Discover supported Agent CLIs and normalize their stable JSONL output."""

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from workbench import registry


SUPPORTED = ("codex", "claude", "pi")

# Turn budgets measure silence, not total time: IDLE_SECONDS is how long a turn
# may produce nothing at all before it is declared stuck, and TOOL_SECONDS is
# the longer budget that applies while a tool call is in flight, because a slow
# command printing nothing for minutes is normal rather than stalled.
#
# A tool budget must stay under IDLE_SECONDS: that is also the RPC process idle
# window, after which the reaper closes the process out from under its turn.
IDLE_SECONDS = 30 * 60
TOOL_SECONDS = 20 * 60
DEFAULT_IDLE_SECONDS = 300


def hidden_launch_kwargs():
    """Never flash a console window for a provider child on Windows.

    Every provider process — the persistent Pi RPC one and each print-mode run —
    goes through this, so "no visible console" is one rule, not a per-call hope.
    """
    if os.name == "nt":
        # The constant is Windows-only, like the branch that reads it.
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


_PI_DETAIL_LIMIT = 500
_PI_OUTPUT_LIMIT = 4000
_PI_SUMMARY_LIMIT = 240
_PI_FAILURE_FALLBACK = "执行失败，未返回诊断信息"
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([a-z0-9_]*(?:api[_-]?key|token|password|secret)[a-z0-9_]*)\b"
    r"(\s*(?:=|:)\s*|\s+)([^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_SHELL_SEGMENT = re.compile(r"&&|\|\||[;\n]")


def _budgets(name, override):
    """Effective turn budgets, kept inside what this provider can honor."""
    idle = max(1, int(override.get("timeout_s", DEFAULT_IDLE_SECONDS)))
    tool = max(idle, int(override.get("tool_timeout_s", TOOL_SECONDS)))
    if name == "pi":
        # The reaper closes a Pi RPC process after IDLE_SECONDS of quiet, so a
        # tool budget up there would let the process die mid-turn instead of the
        # turn failing by its own budget.
        tool = min(tool, IDLE_SECONDS - 60)
    return idle, tool


def discover():
    overrides = registry.load_bridges().get("providers", {})
    found = []
    for name in SUPPORTED:
        override = overrides.get(name, {})
        command = override.get("command") or shutil.which(name)
        if not command:
            continue
        idle, tool = _budgets(name, override)
        found.append({
            "name": name,
            "command": command,
            "args": list(override.get("args", [])),
            "model": override.get("model"),
            "timeout_s": idle,
            "tool_timeout_s": tool,
        })
    return found


def get(name):
    for provider in discover():
        if provider["name"] == name:
            return provider
    raise KeyError(f"provider unavailable: {name}")


CLAUDE_MODELS = (
    ("claude-fable-5", "Fable 5"),
    ("claude-opus-5", "Opus 5"),
    ("claude-opus-4-8", "Opus 4.8"),
    ("claude-opus-4-7", "Opus 4.7"),
    ("claude-opus-4-6", "Opus 4.6"),
    ("claude-opus-4-5-20251101", "Opus 4.5"),
    ("claude-sonnet-5", "Sonnet 5"),
    ("claude-sonnet-4-6", "Sonnet 4.6"),
    ("claude-sonnet-4-5-20250929", "Sonnet 4.5"),
    ("claude-haiku-4-5-20251001", "Haiku 4.5"),
)
MODEL_DISCOVERY_TIMEOUT = 8


def _configured_entries(provider_name, base):
    entries = []
    for model in registry.load_models():
        if model.get("provider") != provider_name:
            continue
        name = model.get("name")
        model_id = model.get("model")
        if not isinstance(name, str) or not name:
            continue
        entry = {
            **base,
            "name": name,
            "provider": provider_name,
            "model": model_id or base.get("model"),
            "source": "configured",
            "entry": name,
        }
        if isinstance(model.get("args"), list):
            entry["args"] = list(model["args"])
        entries.append(entry)
    return entries


def _normalize_codex_models(items):
    models = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        visibility = str(item.get("visibility") or "").lower()
        if item.get("hidden") is True or visibility == "hide":
            continue
        model_id = item.get("model") or item.get("slug") or item.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        display = (
            item.get("displayName") or item.get("display_name")
            or item.get("name") or model_id
        )
        models.append({
            "name": str(display),
            "model": model_id,
            "source": "runtime",
            "entry": None,
        })
    return models


def _codex_cache_models():
    home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    path = home / "models_cache.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    return _normalize_codex_models(raw.get("models") if isinstance(raw, dict) else [])


def _codex_app_server_models(provider):
    """Ask Codex's supported app-server model/list endpoint for picker-visible models."""
    requests = [
        {
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "lesson-kit",
                    "title": "Lesson Kit",
                    "version": "0.1",
                }
            },
        },
        {
            "method": "model/list",
            "id": 2,
            "params": {"limit": 100, "cursor": None, "includeHidden": False},
        },
    ]
    try:
        completed = subprocess.run(
            [provider["command"], "app-server"],
            input="\n".join(json.dumps(item) for item in requests) + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            timeout=MODEL_DISCOVERY_TIMEOUT,
            **hidden_launch_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    for line in completed.stdout.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("id") != 2 or not isinstance(record.get("result"), dict):
            continue
        return _normalize_codex_models(record["result"].get("data"))
    return []


def list_models(provider_name, runtime_models=None):
    """Enumerate model choices inside one harness; never return another harness.

    Codex uses its supported app-server model/list RPC (with the local cache as a
    fallback), Claude uses the model catalog documented by Claude Code, and Pi
    accepts the runtime get_available_models result supplied by its RPC caller.
    User-configured model entries are always retained because they may carry
    gateway-specific ids or extra arguments.
    """
    base = get(provider_name)
    entries = _configured_entries(provider_name, base)

    discovered = []
    if provider_name == "codex":
        discovered = _codex_app_server_models(base) or _codex_cache_models()
    elif provider_name == "claude":
        discovered = [
            {"name": name, "model": model_id, "source": "supported", "entry": None}
            for model_id, name in CLAUDE_MODELS
        ]
    elif provider_name == "pi":
        for item in runtime_models or []:
            if not isinstance(item, dict):
                continue
            runtime_provider = item.get("provider")
            model_id = item.get("id")
            if not isinstance(runtime_provider, str) or not runtime_provider:
                continue
            if not isinstance(model_id, str) or not model_id:
                continue
            discovered.append({
                "name": str(item.get("name") or model_id),
                "model": f"{runtime_provider}/{model_id}",
                "source": "runtime",
                "entry": None,
            })

    seen = {
        (entry.get("model"), tuple(entry.get("args", [])))
        for entry in entries
    }
    for item in discovered:
        key = (item.get("model"), ())
        if key in seen:
            continue
        entries.append({**base, "provider": provider_name, **item})
        seen.add(key)

    # The harness default remains a valid reset target even when models were
    # enumerated. Keep it last so concrete choices are more useful in the picker.
    default_key = (base.get("model"), tuple(base.get("args", [])))
    if default_key not in seen:
        entries.append({
            **base,
            "name": f"{provider_name} 默认",
            "provider": provider_name,
            "source": "default",
            "entry": None,
        })
    return entries


def discover_entries():
    """Return configured model targets plus one fallback for uncovered harnesses.

    A configured target must never make another installed harness disappear.
    Each target also carries the exact argv it needs, so selecting a named model
    does not silently lose its per-model flags.
    """
    models = registry.load_models()
    harnesses = {item["name"]: item for item in discover()}
    entries = []
    covered = set()
    for model in models:
        name = model.get("name")
        provider = model.get("provider")
        if not isinstance(name, str) or not name or provider not in harnesses:
            continue
        base = harnesses[provider]
        entry = {
            **base,
            "name": name,
            "provider": provider,
            "model": model.get("model") or base.get("model"),
            "source": "configured",
        }
        if isinstance(model.get("args"), list):
            entry["args"] = list(model["args"])
        entries.append(entry)
        covered.add(provider)
    for provider, base in harnesses.items():
        if provider not in covered:
            entries.append({
                **base,
                "name": provider,
                "provider": provider,
                "source": "default",
            })
    return entries


def get_entry(name, provider=None):
    for entry in discover_entries():
        if entry["name"] == name and (provider is None or entry["provider"] == provider):
            return entry
    raise KeyError(f"model entry unavailable: {name}")


def resolve_target(provider, model=None, entry_name=None):
    """Resolve one conversation target without losing entry-specific arguments."""
    if entry_name:
        entry = get_entry(entry_name, provider)
        return {
            "provider": entry["provider"],
            "model": entry.get("model"),
            "args": list(entry.get("args", [])),
            "entry": entry["name"],
        }
    base = get(provider)
    return {
        "provider": provider,
        "model": model if model is not None else base.get("model"),
        "args": list(base.get("args", [])),
        "entry": None,
    }


def build_command(provider, session_id=None, mode="print"):
    name = provider["name"]
    command = provider["command"]
    args = list(provider.get("args", []))
    model = provider.get("model")
    if name == "codex":
        result = [command, "exec", "--skip-git-repo-check"]
        if session_id:
            result.append("resume")
        result.append("--json")
        if model:
            result.extend(["--model", model])
        result.extend(args)
        if session_id:
            result.append(session_id)
        result.append("-")
        return result
    if name == "pi":
        # `rpc` keeps one process per conversation; `print` is one process per turn.
        result = [command, "--mode", "rpc"] if mode == "rpc" else [
            command, "--print", "--mode", "json"]
        if model:
            result.extend(["--model", model])
        result.extend(args)
        if session_id:
            result.extend(["--session", session_id])
        return result
    result = [
        command, "--print", "--output-format", "stream-json", "--verbose",
        "--include-partial-messages",
    ]
    if model:
        result.extend(["--model", model])
    result.extend(args)
    if session_id:
        result.extend(["--resume", session_id])
    return result


def _text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _activity(activity_id, activity_type, status, label, detail="", output=""):
    event = {
        "kind": "activity",
        "activity_id": str(activity_id),
        "activity_type": activity_type,
        "status": status,
        "label": label,
    }
    if detail:
        event["detail"] = _text(detail)
    if output:
        event["output"] = _text(output)
    return event


def _codex_item_activity(event_type, item):
    item_type = str(item.get("type", "unknown"))
    activity_id = item.get("id") or f"codex-{item_type}"
    failed = item.get("status") == "failed" or item.get("error") not in (None, "")
    if item.get("exit_code") not in (None, 0):
        failed = True
    status = "running" if event_type != "item.completed" else ("failed" if failed else "done")

    if item_type == "reasoning":
        return _activity(activity_id, "reasoning", status, "分析任务")
    if item_type == "command_execution":
        return _activity(
            activity_id, "command", status, "运行命令",
            item.get("command", ""),
            item.get("aggregated_output") or item.get("output") or item.get("error", ""),
        )
    if item_type == "mcp_tool_call":
        tool = item.get("tool") or item.get("name") or "工具"
        server = item.get("server") or item.get("server_name") or ""
        detail = " · ".join(part for part in (server, tool) if part)
        output = item.get("result") or item.get("output") or item.get("error", "")
        return _activity(activity_id, "tool", status, "调用工具", detail, output)
    if item_type == "web_search":
        return _activity(
            activity_id, "search", status, "搜索资料",
            item.get("query") or item.get("text", ""), item.get("result", ""),
        )
    if item_type == "file_change":
        return _activity(
            activity_id, "file", status, "更新文件",
            item.get("changes") or item.get("path", ""), item.get("error", ""),
        )
    return _activity(activity_id, "tool", status, "执行步骤")


def _claude_tool_activity(block, status="running"):
    name = str(block.get("name") or "工具")
    activity_type = "command" if name.lower() in {"bash", "shell", "terminal"} else "tool"
    label = "运行命令" if activity_type == "command" else "调用工具"
    inputs = block.get("input") or {}
    detail = inputs.get("command", "") if isinstance(inputs, dict) else ""
    if not detail:
        detail = name if not inputs else f"{name} · {_text(inputs)}"
    return _activity(block.get("id") or f"claude-{name}", activity_type, status, label, detail)


def _pi_message_text(message):
    parts = []
    for block in (message or {}).get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


def _pi_tool_detail(args):
    if isinstance(args, str):
        return args
    if isinstance(args, dict):
        for field in ("command", "file_path", "path", "pattern", "query", "url"):
            value = args.get(field)
            if isinstance(value, str) and value:
                return value
        return ""
    return ""


def _pi_tool_output(result):
    """Pi returns tool results as {content: [{type, text}], details}, not text."""
    if isinstance(result, dict):
        blocks = result.get("content")
        if isinstance(blocks, list):
            parts = [
                str(block.get("text", "")) for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            text = "".join(parts)
            if text:
                return text
        details = result.get("details")
        return details if details not in (None, "") else ""
    return result if result not in (None, "") else ""


def _pi_safe_text(value, limit):
    text = _text(value)
    text = _BEARER_TOKEN.sub("Bearer [REDACTED]", text)
    text = _SECRET_ASSIGNMENT.sub(
        lambda match: match.group(1) + match.group(2) + "[REDACTED]", text,
    )
    if len(text) > limit:
        text = text[:limit - 1] + "…"
    return text


def _pi_failure_summary(output):
    """The last meaningful line of an already-sanitized failure output.

    Presentation only: the status itself always comes from the provider's own
    failure signal, never from reading the text.
    """
    lines = [line.strip() for line in str(output or "").splitlines() if line.strip()]
    if not lines:
        return _PI_FAILURE_FALLBACK
    summary = lines[-1]
    if len(summary) > _PI_SUMMARY_LIMIT:
        summary = summary[: _PI_SUMMARY_LIMIT - 1] + "…"
    return summary


def _pi_activity_identity(tool_name, detail):
    name = str(tool_name or "工具")
    normalized = name.lower().replace("-", "_")
    if normalized in {"read", "view", "read_file", "view_file"}:
        return "file-read", "读取文件"
    if normalized in {"write", "edit", "apply_patch", "write_file", "edit_file"}:
        return "file-write", "更新文件"
    if normalized in {"grep", "find", "search", "rg"}:
        return "search", "搜索"
    if normalized in {"bash", "shell", "terminal", "command"}:
        if _runs_lesson_kit(detail):
            return "lesson-kit", "操作 Lesson Kit"
        return "command", "运行命令"
    return "tool", f"调用 {name}"


def _runs_lesson_kit(command):
    """Recognize an invoked CLI, not a path or argument containing its name."""
    for segment in _SHELL_SEGMENT.split(command):
        try:
            parts = shlex.split(segment.strip(), posix=False)
        except ValueError:
            parts = segment.split()
        if not parts:
            continue
        parts = [part.strip("\"'") for part in parts]
        executable = re.split(r"[\\/]", parts[0])[-1].lower()
        if executable in {"lesson-kit", "lesson-kit.exe", "lesson-kit.cmd", "lessonkit.py"}:
            return True
        if executable in {"python", "python.exe", "py", "py.exe"}:
            if len(parts) >= 3 and parts[1:3] == ["-m", "workbench.cli.main"]:
                return True
            if len(parts) >= 2 and re.split(r"[\\/]", parts[1])[-1].lower() == "lessonkit.py":
                return True
    return False


def _pi_tool_activity(tool_id, tool_name, status, args=None, result=None):
    detail = _pi_safe_text(_pi_tool_detail(args), _PI_DETAIL_LIMIT)
    output = _pi_safe_text(_pi_tool_output(result), _PI_OUTPUT_LIMIT)
    activity_id = tool_id or "pi-tool"
    if not detail and status != "running":
        event = {"kind": "activity", "activity_id": str(activity_id), "status": status}
        if output:
            event["output"] = output
        if status == "failed":
            event["summary"] = _pi_failure_summary(output)
        return event
    activity_type, label = _pi_activity_identity(tool_name, detail)
    event = _activity(activity_id, activity_type, status, label, detail, output)
    if status == "failed":
        # The reason must be readable without expanding the folded output.
        event["summary"] = _pi_failure_summary(output)
    return event


def _normalize_pi_event(data):
    event_type = data.get("type", "")
    if event_type == "session":
        event = {"kind": "phase", "label": "provider.ready"}
        if data.get("id"):
            event["provider_session_id"] = str(data["id"])
        return event
    if event_type == "turn_start":
        return None
    if event_type == "message_start":
        message = data.get("message") or {}
        if message.get("role") == "assistant":
            return None
        return {"kind": "phase", "label": "provider.working"}
    if event_type == "message_update":
        update = data.get("assistantMessageEvent") or {}
        update_type = update.get("type")
        if update_type == "text_delta":
            return {"kind": "text", "text": str(update.get("delta", ""))}
        if update_type == "thinking_start":
            return None
        if update_type == "thinking_end":
            return None
        if update_type == "toolcall_start":
            return _pi_tool_activity(
                update.get("id"), update.get("toolName"), "running",
            )
        # thinking_delta / text_start / text_end / toolcall_delta carry no
        # learner-facing step at all. Reasoning text must never be surfaced,
        # and Pi emits one such event per token, so they are dropped instead of
        # being written as protocol noise into the durable event log.
        return None
    if event_type == "tool_execution_start":
        return _pi_tool_activity(
            data.get("toolCallId"), data.get("toolName"), "running", data.get("args"),
        )
    if event_type == "tool_execution_update":
        return _pi_tool_activity(
            data.get("toolCallId"), data.get("toolName"), "running",
            data.get("args"), data.get("partialResult"),
        )
    if event_type == "tool_execution_end":
        return _pi_tool_activity(
            data.get("toolCallId"), data.get("toolName"),
            "failed" if data.get("isError") else "done",
            data.get("args"), data.get("result"),
        )
    if event_type == "message_end":
        message = data.get("message") or {}
        if message.get("role") != "assistant":
            return {"kind": "phase", "label": "provider.working"}
        error = str(message.get("errorMessage") or "").strip()
        if error or message.get("stopReason") == "error":
            return {"kind": "error", "text": error or "provider reported an error result"}
        text = _pi_message_text(message)
        if text:
            return {"kind": "result", "text": text}
        return {"kind": "phase", "label": "provider.working"}
    if event_type == "agent_end":
        for message in reversed(data.get("messages") or []):
            if isinstance(message, dict) and message.get("role") == "assistant":
                text = _pi_message_text(message)
                if text:
                    return {"kind": "result", "text": text}
        return {"kind": "phase", "label": "provider.working"}
    return {"kind": "phase", "label": "provider.working"}


def normalize_event(provider_name, data):
    """Normalize one provider event, or return None when it has no meaning here."""
    event_type = data.get("type", "")
    if provider_name == "pi":
        return _normalize_pi_event(data)
    if provider_name == "codex":
        if event_type == "thread.started":
            return {
                "kind": "phase", "label": "provider.ready",
                "provider_session_id": data.get("thread_id"),
            }
        if event_type in {"turn.started", "turn.completed", "turn.failed"}:
            status = "running" if event_type == "turn.started" else (
                "failed" if event_type == "turn.failed" else "done"
            )
            return _activity(
                "provider-turn", "progress", status,
                "Agent 正在处理" if status == "running" else (
                    "Agent 处理失败" if status == "failed" else "Agent 处理完成"
                ),
            )
        if event_type in {"item.started", "item.updated"}:
            return _codex_item_activity(event_type, data.get("item") or {})
        if event_type == "item.completed":
            item = data.get("item") or {}
            if item.get("type") == "agent_message":
                result = {"kind": "text", "text": str(item.get("text", ""))}
                title = item.get("title") or data.get("title")
                if title:
                    result["title"] = str(title)
                return result
            return _codex_item_activity(event_type, item)
        if event_type == "error":
            return {"kind": "error", "text": str(data.get("message", "provider error"))}
        return {"kind": "phase", "label": "provider.working"}

    if event_type == "system" and data.get("subtype") == "init":
        return {
            "kind": "phase", "label": "provider.ready",
            "provider_session_id": data.get("session_id"),
        }
    if event_type == "assistant":
        blocks = (data.get("message") or {}).get("content") or []
        tool = next((item for item in blocks if item.get("type") == "tool_use"), None)
        return _claude_tool_activity(tool) if tool else {"kind": "phase", "label": "provider.working"}
    if event_type == "user":
        blocks = (data.get("message") or {}).get("content") or []
        result = next((item for item in blocks if item.get("type") == "tool_result"), None)
        if result:
            status = "failed" if result.get("is_error") else "done"
            activity = {
                "kind": "activity",
                "activity_id": str(result.get("tool_use_id") or "claude-tool"),
                "status": status,
            }
            if result.get("content") not in (None, ""):
                activity["output"] = _text(result["content"])
            return activity
        return {"kind": "phase", "label": "provider.working"}
    if event_type == "stream_event":
        event = data.get("event") or {}
        delta = event.get("delta") or {}
        if event.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
            return {"kind": "text", "text": str(delta.get("text", ""))}
        block = event.get("content_block") or {}
        if event.get("type") == "content_block_start" and block.get("type") == "tool_use":
            return _claude_tool_activity(block)
        if event.get("type") == "message_start":
            return _activity("provider-turn", "progress", "running", "Agent 正在处理")
        return {"kind": "phase", "label": "provider.working"}
    if event_type == "result":
        result = {
            "kind": "result", "text": str(data.get("result", "")),
            "provider_session_id": data.get("session_id"),
        }
        if data.get("title"):
            result["title"] = str(data["title"])
        return result
    return {"kind": "phase", "label": "provider.working"}
