"""Read-only environment self-check for the workbench (lesson-kit doctor)."""

import json
import sqlite3
from pathlib import Path

from workbench import registry
from workbench.bridge import conversation_providers
from workbench.cli import service


def run_checks():
    """Return the full check list; every entry is (name, ok, detail)."""
    checks = []
    checks.append(_check_registry())
    workspace_checks, workspaces = _check_workspaces()
    checks.extend(workspace_checks)
    checks.append(_check_providers())
    checks.append(_check_service(workspaces))
    checks.extend(_check_workspace_files(workspaces))
    return checks


def _check_registry():
    try:
        workspaces = registry.list_workspaces()
        return ("registry readable", True,
                f"{registry.base_dir() / 'workspaces.json'} ({len(workspaces)} workspaces)")
    except (OSError, json.JSONDecodeError) as exc:
        return ("registry readable", False, str(exc))


def _check_workspaces():
    checks = []
    workspaces = []
    try:
        workspaces = registry.list_workspaces()
    except (OSError, json.JSONDecodeError):
        return checks, workspaces
    for workspace in workspaces:
        name = workspace.get("name", "?")
        db_rel = workspace.get("db") or ""
        db_path = Path(workspace.get("path", "")) / db_rel
        if not db_rel or not db_path.is_file():
            checks.append((f"workspace {name}: pool database", False, str(db_path)))
            continue
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT COUNT(*) FROM knowledge_points")
            conn.close()
            checks.append((f"workspace {name}: pool database", True, str(db_path)))
        except sqlite3.Error as exc:
            checks.append((f"workspace {name}: pool database", False, str(exc)))
    return checks, workspaces


def _check_providers():
    try:
        providers = conversation_providers.discover()
    except (OSError, json.JSONDecodeError) as exc:
        return ("agent providers", False, str(exc))
    if not providers:
        return ("agent providers", True, "none discovered (non-AI workbench still works)")
    missing = [p for p in providers if not Path(p["command"]).is_file()]
    detail = "; ".join(f"{p['name']} -> {p['command']}" for p in providers)
    if missing:
        names = ", ".join(p["name"] for p in missing)
        return ("agent providers", False, f"missing executable for {names}: {detail}")
    return ("agent providers", True, detail)


def _check_service(workspaces):
    state = service.running_state()
    if not state:
        return ("background service", True, "not running (start with: lesson-kit daemon start)")
    port = state.get("port")
    if not service.port_answers(port):
        return ("background service", False,
                f"pid {state.get('pid')} recorded on port {port} but the port does not answer")
    return ("background service", True,
            f"running: pid {state.get('pid')} on port {port}")


def _check_workspace_files(workspaces):
    checks = []
    for workspace in workspaces:
        name = workspace.get("name", "?")
        root = Path(workspace.get("path", ""))
        for file_name, parser in (("goals.json", json.loads), ("plan.json", json.loads)):
            path = root / ".lessonkit" / file_name
            if not path.exists():
                continue
            try:
                parser(path.read_text(encoding="utf-8"))
                checks.append((f"workspace {name}: {file_name}", True, str(path)))
            except (OSError, ValueError) as exc:
                checks.append((f"workspace {name}: {file_name}", False, str(exc)))
    return checks


def format_report(checks):
    lines = []
    for name, ok, detail in checks:
        marker = "ok  " if ok else "FAIL"
        lines.append(f"[{marker}] {name}: {detail}")
    return lines


def all_passed(checks):
    return all(ok for _, ok, _ in checks)
