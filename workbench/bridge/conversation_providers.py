"""Discover supported Agent CLIs and normalize their stable JSONL output."""

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
        result = [command, "exec"]
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


def normalize_event(provider_name, data):
    event_type = data.get("type", "")
    if provider_name == "codex":
        if event_type == "thread.started":
            return {
                "kind": "phase", "label": "thread.started",
                "provider_session_id": data.get("thread_id"),
            }
        if event_type == "item.completed":
            item = data.get("item") or {}
            if item.get("type") == "agent_message":
                return {"kind": "text", "text": str(item.get("text", ""))}
            return {"kind": "phase", "label": f"item.completed:{item.get('type', 'unknown')}"}
        if event_type == "error":
            return {"kind": "error", "text": str(data.get("message", "provider error"))}
        return {"kind": "phase", "label": event_type or "provider.event"}

    if event_type == "system" and data.get("subtype") == "init":
        return {
            "kind": "phase", "label": "session.started",
            "provider_session_id": data.get("session_id"),
        }
    if event_type == "stream_event":
        event = data.get("event") or {}
        delta = event.get("delta") or {}
        if event.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
            return {"kind": "text", "text": str(delta.get("text", ""))}
        return {"kind": "phase", "label": str(event.get("type", "stream_event"))}
    if event_type == "result":
        return {
            "kind": "result", "text": str(data.get("result", "")),
            "provider_session_id": data.get("session_id"),
        }
    return {"kind": "phase", "label": event_type or "provider.event"}
