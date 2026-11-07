"""Windows Task Scheduler transport, bound to one explicit source directory."""

import datetime
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from workbench.bridge.git_sync import hidden_launch_kwargs

ARGUMENTS = "-m workbench.cli.main course-sync --all-configured sync"
NAMESPACE = "http://schemas.microsoft.com/windows/2004/02/mit/task"


def definition(source_root, executable=None, user=None):
    """Build native XML; escaping paths is ElementTree's responsibility."""
    ET.register_namespace("", NAMESPACE)
    def child(parent, name, text=None, **attributes):
        item = ET.SubElement(parent, "{" + NAMESPACE + "}" + name, attributes)
        item.text = text
        return item
    task = ET.Element("{" + NAMESPACE + "}Task", {"version": "1.2"})
    triggers = child(task, "Triggers")
    trigger = child(triggers, "TimeTrigger")
    repeat = child(trigger, "Repetition")
    child(repeat, "Interval", "PT1H")
    child(repeat, "StopAtDurationEnd", "false")
    child(trigger, "StartBoundary", (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(timespec="seconds"))
    child(trigger, "Enabled", "true")
    principal = child(child(task, "Principals"), "Principal", id="Author")
    user = user or os.environ.get("USERDOMAIN", "") + "\\" + os.environ.get("USERNAME", "")
    child(principal, "UserId", user.lstrip("\\"))
    child(principal, "LogonType", "InteractiveToken")
    child(principal, "RunLevel", "LeastPrivilege")
    settings = child(task, "Settings")
    child(settings, "MultipleInstancesPolicy", "IgnoreNew")
    child(settings, "DisallowStartIfOnBatteries", "false")
    child(settings, "StopIfGoingOnBatteries", "false")
    child(settings, "StartWhenAvailable", "true")
    child(settings, "ExecutionTimeLimit", "PT1H")
    action = child(child(task, "Actions", Context="Author"), "Exec")
    child(action, "Command", str(executable or sys.executable))
    child(action, "Arguments", ARGUMENTS)
    child(action, "WorkingDirectory", str(Path(source_root).resolve()))
    return ET.tostring(task, encoding="unicode")


def manage(action, name, source_root):
    if sys.platform != "win32":
        raise ValueError("the hourly task uses the built-in Windows Task Scheduler")
    base = ["schtasks", "/TN", name]
    kwargs = dict(stdin=subprocess.DEVNULL, capture_output=True, check=False,
                  timeout=30, **hidden_launch_kwargs())
    if action == "install":
        with tempfile.TemporaryDirectory(prefix="lessonkit-task-") as temporary:
            path = Path(temporary) / "task.xml"
            path.write_text(definition(source_root), encoding="utf-16")
            return subprocess.run(base + ["/Create", "/XML", str(path), "/F"], **kwargs)
    if action not in {"remove", "enable", "disable"}:
        raise ValueError("unknown course-sync task action")
    flags = ["/Delete", "/F"] if action == "remove" else ["/Change", "/ENABLE" if action == "enable" else "/DISABLE"]
    return subprocess.run(base + flags, **kwargs)


def preflight(source_root):
    """Fail rather than install a task that imports a different checkout."""
    root = Path(source_root).resolve()
    result = subprocess.run(
        [sys.executable, "-c", "import pathlib,workbench; print(pathlib.Path(workbench.__file__).resolve().parent.parent)"],
        cwd=root, env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        stdin=subprocess.DEVNULL, capture_output=True, check=False,
        timeout=15, **hidden_launch_kwargs())
    actual = result.stdout.decode("utf-8", "replace").strip()
    if result.returncode or not actual or Path(actual).resolve() != root:
        raise ValueError("scheduled command does not import the selected Lesson Kit source")
    return {"executable": sys.executable, "arguments": ARGUMENTS, "working_directory": str(root)}
