"""Discover supported Agent CLIs and normalize their stable JSONL output."""

import json
import shutil

from workbench import registry


SUPPORTED = ("codex", "claude")


def discover():
    overrides = registry.load_bridges().get("providers", {})
    found = []
    for name in SUPPORTED:
        command = shutil.which(name)
        if not command:
            continue
        override = overrides.get(name, {})
        found.append({
            "name": name,
            "command": command,
            "args": list(override.get("args", [])),
            "model": override.get("model"),
            "timeout_s": int(override.get("timeout_s", 300)),
        })
    return found


def get(name):
    for provider in discover():
        if provider["name"] == name:
            return provider
    raise KeyError(f"provider unavailable: {name}")


def build_command(provider, session_id=None):
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


def normalize_event(provider_name, data):
    event_type = data.get("type", "")
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
