"""File-mediated course exchange: one configured CLI for files, Git and the hourly task.

The receipt is the only thing callers parse: a top-level `status`
(`success` / `partial` / `conflict` / `failed`), the course origin, the unit
counts, the operation identity, and per-unit outcomes. Exit codes follow the
receipt: 0 complete success, 2 input or format error, 3 a genuine conflict needs
a side, 4 partial completion or transport failure — with 2 winning over 3 over 4.
"""

import argparse
import json
import os
import subprocess
import sqlite3
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from workbench import registry
from workbench.bridge import git_sync
from workbench.data import course_sync as exchange
from workbench.data import tutor_handoff

TASK_NAME = "LessonKit Course Sync"
TASK_COMMAND = "--all-configured sync"
RECEIPT = "last-receipt.json"
NOTICE = "last-notice.json"


def build_parser(prog="lesson-kit course-sync"):
    parser = argparse.ArgumentParser(
        prog=prog,
        description="exchange a whole course through files, Git and an hourly task",
    )
    parser.add_argument("name", nargs="?", help="registered Lesson Kit workspace")
    parser.add_argument("action", choices=[
        "export", "receive", "check", "sync", "status", "schedule"])
    parser.add_argument("schedule_action", nargs="?",
                        choices=["install", "enable", "disable", "remove"])
    parser.add_argument("--to", help="package directory to write (export)")
    parser.add_argument("--from", dest="source", help="package directory to read")
    parser.add_argument("--keep", choices=["local", "incoming"],
                        help="side to take for every genuine conflict")
    parser.add_argument("--choices", help="JSON file with per-identity conflict sides")
    parser.add_argument("--associate", action="store_true",
                        help="accept a package from another course lineage")
    parser.add_argument("--repo", help="Git repository holding the package")
    parser.add_argument("--branch", help="branch the exchange package travels on")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--path", help="package directory inside the repository")
    parser.add_argument("--message", help="commit message for a publication")
    parser.add_argument("--package", help="remember this package directory as the media")
    parser.add_argument("--all-configured", action="store_true",
                        help="every registered course with configured media")
    parser.add_argument("--json-output", action="store_true",
                        help="print the receipt without the human summary")
    return parser


def main(argv=None, prog="lesson-kit course-sync"):
    args = build_parser(prog).parse_args(argv)
    return run(args)


def run(args):
    try:
        if args.action == "schedule":
            return _schedule(args)
        if args.all_configured:
            return _run_every_course(args)
        if not args.name:
            raise ValueError("a workspace name or --all-configured is required")
        pool, workspace = _open(args.name)
        try:
            return _dispatch(args, pool, workspace)
        finally:
            pool.close()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "errors": [str(exc)]}, ensure_ascii=False))
        return 2


class _InputError(ValueError):
    """The request itself is unusable; nothing was written."""


def _open(name):
    from workbench.cli import main as cli

    try:
        workspace = cli._workspace(name)
    except SystemExit as exc:  # the shared resolver prints the readable refusal
        raise _InputError(str(exc) or f"unknown workspace: {name}") from exc
    pool = cli._pool(workspace)
    return pool, workspace


def _dispatch(args, pool, workspace, media=None, emit=True):
    if args.action == "export":
        return _export(args, pool, workspace, emit=emit)
    if args.action in {"check", "receive"}:
        return _receive(args, pool, workspace, dry_run=args.action == "check", emit=emit)
    if args.action == "status":
        return _status(pool, workspace)
    return _sync(args, pool, workspace, media or _media(pool.root), emit=emit)


def _export(args, pool, workspace, emit=True):
    destination = _required(args.to, "--to")
    result = exchange.export_course(pool, workspace, destination)
    tutor_handoff.write(pool, destination)
    return _finish(args, pool, {"status": result["status"]}, _exit_code(result["status"]),
                   emit=emit)


def _receive(args, pool, workspace, dry_run=False, emit=True):
    source = _required(args.source, "--from")
    inspection = exchange.inspect_exchange(pool, workspace, source)
    if dry_run:
        receipt = _inspection_receipt(inspection)
        return _finish(args, pool, receipt, _inspection_exit(inspection), emit=emit)
    choices = _choices(args)
    result = exchange.apply_exchange(pool, workspace, inspection, choices)
    receipt = _receive_receipt(inspection, result)
    _notice(pool, receipt)
    return _finish(args, pool, receipt, _exit_code(receipt["status"]), emit=emit)


def _choices(args):
    if args.choices:
        try:
            body = json.loads(Path(args.choices).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise _InputError(f"cannot read --choices: {exc}") from exc
        if not isinstance(body, dict):
            raise _InputError("--choices must hold a JSON object")
    else:
        body = {}
    if args.keep:
        body = {**body, "side": args.keep}
    if args.associate:
        body = {**body, "associate": True}
    return body


def _inspection_receipt(inspection):
    plan = inspection.get("plan") or {}
    return {"status": _inspection_status(inspection),
            "course": inspection.get("course"),
            "assets": len(inspection.get("incoming") or {}),
            "changes": [item["identity"] for item in plan.get("changes") or []],
            "outgoing": [item["identity"] for item in plan.get("outgoing") or []],
            "conflicts": [item["identity"] for item in plan.get("conflicts") or []],
            "unchanged": len(plan.get("unchanged") or []),
            "errors": inspection.get("errors") or []}


def _remaining_errors(inspection, result):
    pending = {item["identity"] for item in result["failed"] if item["code"] == "publication_pending"}
    return [item for item in inspection.get("errors", [])
            if item.get("code") != "publication_pending" or item.get("identity") in pending]


def _receive_receipt(inspection, result):
    receipt = _inspection_receipt(inspection)
    receipt.update({
        "status": _applied_status(inspection, result),
        "errors": _remaining_errors(inspection, result),
        "conflicts": [item["identity"] for item in result["conflicts"]],
        "operation": "receive-" + str(uuid4()),
        "applied": result["applied"], "kept": result["kept"], "failed": result["failed"],
        "base_size": result["base_size"],
        "local": result["local"], "remote": None,
    })
    return receipt


def _applied_status(inspection, result):
    if result["conflicts"]:
        return "conflict"
    if result["failed"] or _remaining_errors(inspection, result):
        return "partial"
    return "success"


def _inspection_status(inspection):
    plan = inspection.get("plan") or {}
    if plan.get("conflicts"):
        return "conflict"
    if inspection.get("errors"):
        return "partial"
    return "success"


def _inspection_exit(inspection):
    status = _inspection_status(inspection)
    return 3 if status == "conflict" else (4 if status == "partial" else 0)


def _exit_code(status):
    return {"success": 0, "conflict": 3, "partial": 4, "failed": 2}.get(status, 2)


def _status(pool, workspace):
    state = _state(pool)
    receipt = _read_json(pool.root / ".lessonkit/course-sync" / RECEIPT)
    print(json.dumps({
        "course": {"id": pool.course},
        "state": {
            "course_origin": (state or {}).get("course", {}).get("origin"),
            "installation_origin": (state or {}).get("origin"),
            "base_size": len((state or {}).get("base") or {}),
            "initialized": (state or {}).get("initialized", False),
        },
        "media": _media(pool.root),
        "last_receipt": receipt,
    }, ensure_ascii=False, indent=2))
    return 0


def _state(pool):
    path = pool.root / ".lessonkit/course-sync/state.json"
    return _read_json(path)


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _media(root):
    config = _read_json(Path(root) / ".lessonkit/course-sync/config.json") or {}
    media = config.get("media")
    return media if isinstance(media, dict) else {}


def _save_media(root, media):
    path = Path(root) / ".lessonkit/course-sync/config.json"
    config = _read_json(path) or {}
    if not isinstance(config, dict):
        raise _InputError("course sync config is not a JSON object")
    config["media"] = media
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sync(args, pool, workspace, media, emit=True):
    repo = args.repo or media.get("repo")
    package = args.path or media.get("package")
    branch = args.branch or media.get("branch") or "main"
    remote = args.remote or media.get("remote") or "origin"
    if not repo:
        raise _InputError("--repo or a configured media repository is required")
    if not package:
        raise _InputError("--path or a configured package directory is required")
    if Path(package).is_absolute() or ".." in Path(package).parts:
        raise _InputError("the package directory must be a relative path inside the repository")

    repository = git_sync.inspect_repository(repo, branch, remote)
    if not repository["branch_checked_out"]:
        raise _InputError(
            f"branch {branch!r} is not checked out in {repository['repo']}")
    receipt = {"operation": "sync-" + str(uuid4()), "course": {"id": pool.course},
               "repo": repository["repo"], "branch": branch, "package": package,
               "local": {}, "remote": {}, "errors": []}
    try:
        fetched = git_sync.fetch_remote(repository["repo"], branch, remote)
        receipt["fetched_commit"] = fetched["commit"]

        with tempfile.TemporaryDirectory() as staging:
            incoming = _materialize(receipt, repository["repo"], fetched["commit"], package, staging)
            if incoming is not None:
                inspection = exchange.inspect_exchange(pool, workspace, incoming)
                result = exchange.apply_exchange(pool, workspace, inspection, _choices(args))
                receipt["local"]["receive"] = {
                    "status": result["status"], "applied": result["applied"],
                    "kept": result["kept"], "failed": result["failed"],
                    "conflicts": [item["identity"] for item in result["conflicts"]],
                    "errors": _remaining_errors(inspection, result),
                }
                if result["status"] != "success" or _remaining_errors(inspection, result) or receipt["errors"]:
                    receipt["status"] = "conflict" if result["conflicts"] else "partial"
                    receipt["remote"] = {"status": "not_published"}
                    _notice(pool, receipt)
                    return _finish(args, pool, receipt, _sync_exit(receipt), emit=emit)
            git_sync.fast_forward(repository["repo"], branch, fetched["commit"])
            package_dir = Path(repository["repo"]) / package
            previous_paths = (_package_paths(repository["repo"], package)
                              if (package_dir / "manifest.json").is_file() else [])
            exported = exchange.export_course(pool, workspace, package_dir)
            tutor_handoff.write(pool, package_dir)
            receipt["local"]["export"] = {
                "status": exported["status"], "assets": exported["assets"],
                "written": exported["written"], "reused": exported["reused"],
                "manifest_changed": exported["manifest_changed"],
                "cleanup_errors": exported["cleanup_errors"],
            }
        tracked = set(git_sync.tracked_paths(repository["repo"]))
        managed = sorted(set(_package_paths(repository["repo"], package))
                         | (set(previous_paths) & tracked))
        published = git_sync.publish(repository["repo"], branch, managed, remote,
                                     args.message or "chore: exchange course files")
        receipt["remote"] = {"status": published["remote"]["status"],
                             "commit": published["remote"]["commit"],
                             "reason": published["remote"]["reason"],
                             "local_commit": published["local"]["commit"],
                             "changed_paths": published["local"]["changed_paths"]}
        receipt["status"] = _sync_status(receipt)
    except (RuntimeError, OSError, sqlite3.Error) as exc:
        receipt["errors"].append({"code": "exchange_or_transport_failed",
                                  "message": git_sync.sanitize(str(exc))})
        receipt["remote"] = {"status": "failed"}
        receipt["status"] = "partial"
    code = _sync_exit(receipt)
    _notice(pool, receipt)
    return _finish(args, pool, receipt, code, emit=emit)


def _materialize(receipt, repo, commit, package, staging):
    """Copy the remote package into a staging directory, or None when it is new."""
    manifest_path = f"{package}/manifest.json" if package not in {"", "."} else "manifest.json"
    first = git_sync.read_remote_files(repo, commit, [manifest_path])
    if manifest_path in first["missing"]:
        return None
    payload = json.loads(first["files"][manifest_path].decode("utf-8"))
    descriptors = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(descriptors, list):
        raise _InputError("the remote manifest has no asset descriptors")
    prefix = "" if manifest_path == "manifest.json" else package + "/"
    wanted = [manifest_path] + [prefix + item["path"] for item in descriptors
                                if isinstance(item, dict) and isinstance(item.get("path"), str)]
    files = git_sync.read_remote_files(repo, commit, wanted)
    if files["missing"]:
        receipt["errors"].append({"code": "missing_asset",
                                  "message": ", ".join(files["missing"])})
    target = Path(staging)
    for name, data in files["files"].items():
        relative = name[len(prefix):] if prefix else name
        path = exchange._relative(target, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    package_data = exchange.read_exchange(target)
    readable = [prefix + exchange.READABLE_DIR + "/" + asset["content"]["path"]
                for asset in package_data["assets"].values()
                if asset["kind"] == "file" and not asset.get("deleted")]
    if readable:
        copies = git_sync.read_remote_files(repo, commit, readable)
        for name, data in copies["files"].items():
            relative = name[len(prefix):] if prefix else name
            path = exchange._relative(target, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return target


def _package_paths(repo, package):
    manifest = Path(repo) / package / "manifest.json"
    if not manifest.is_file():
        raise _InputError("the exported package has no manifest")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    prefix = "" if package in {"", "."} else package + "/"
    paths = [prefix + "manifest.json", prefix + tutor_handoff.FILE_NAME]
    for item in payload["assets"]:
        paths.append(prefix + item["path"])
        if item["kind"] == "file":
            asset = json.loads((manifest.parent / item["path"]).read_text(encoding="utf-8"))
            if not asset.get("deleted"):
                paths.append(prefix + exchange.READABLE_DIR + "/" + asset["content"]["path"])
    return paths


def _sync_status(receipt):
    receive = receipt["local"].get("receive") or {}
    if receive.get("status") == "conflict":
        return "conflict"
    if receipt["remote"].get("status") != "published" and receipt["remote"].get("status") != "unchanged":
        return "partial"
    if receipt["errors"] or (receive.get("status") or "success") != "success" \
            or receipt["local"]["export"]["status"] != "success":
        return "partial"
    return "success"


def _sync_exit(receipt):
    if receipt["status"] == "conflict":
        return 3
    return 4 if receipt["status"] == "partial" else 0


def _notice(pool, receipt):
    """One short note only for conflicts this course has not reported yet."""
    conflicts = receipt.get("conflicts")
    if not isinstance(conflicts, list):
        conflicts = (receipt.get("local", {}).get("receive") or {}).get("conflicts") or []
    identities = sorted(item for item in conflicts if isinstance(item, str))
    path = pool.root / ".lessonkit/course-sync" / NOTICE
    if not identities:
        path.unlink(missing_ok=True)
        return
    previous = _read_json(path) or {}
    if previous.get("conflicts") == identities and previous.get("notified"):
        return
    shown = _toast(f"{pool.course}: 课程同步有待选侧的差异",
                   f"{len(identities)} 项需要在本地版本与收到的版本之间选一侧")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"conflicts": identities, "notified": shown},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["notification"] = {"notified": shown, "identities": identities}


def _toast(title, message):
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
        " ContentType=WindowsRuntime]|Out-Null;"
        "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$n=$t.GetElementsByTagName('text');$n.Item(0).AppendChild("
        "$t.CreateTextNode($env:LK_TOAST_TITLE))|Out-Null;$n.Item(1).AppendChild("
        "$t.CreateTextNode($env:LK_TOAST_MESSAGE))|Out-Null;"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'Lesson Kit').Show([Windows.UI.Notifications.ToastNotification]::new($t))"
    )
    if sys.platform != "win32":
        return False
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        env=dict(os.environ, LK_TOAST_TITLE=title, LK_TOAST_MESSAGE=message),
        stdin=subprocess.DEVNULL, capture_output=True, check=False, timeout=15,
        **git_sync.hidden_launch_kwargs())
    return completed.returncode == 0


def _schedule(args):
    """Install or manage the hourly task that runs every configured course."""
    action = args.schedule_action
    if action is None:
        raise _InputError("schedule needs install, enable, disable or remove")
    media = None
    if args.name:
        pool, workspace = _open(args.name)
        try:
            media = _media(pool.root)
            if any((args.package, args.path, args.repo, args.branch)):
                media = {**media, **{key: value for key, value in {
                    "package": args.package or args.path, "repo": args.repo,
                    "branch": args.branch, "remote": args.remote}.items() if value}}
                _save_media(pool.root, media)
            if action == "install" and not media.get("repo") and not media.get("package"):
                raise _InputError("install needs --repo and --path, or saved media")
        finally:
            pool.close()
    command = f'"{sys.executable}" -m workbench.cli.main course-sync {TASK_COMMAND}'
    completed = _schtasks(action, command)
    receipt = {"status": "success" if completed.returncode == 0 else "failed",
               "action": action, "task": TASK_NAME, "command": command,
               "media": media, "output": _text(completed)}
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if completed.returncode == 0 else 4


def _schtasks(action, command):
    if sys.platform != "win32":
        raise _InputError("the hourly task uses the built-in Windows Task Scheduler")
    base = ["schtasks", "/TN", TASK_NAME]
    if action == "install":
        args = base + ["/Create", "/SC", "HOURLY", "/TR", command, "/F"]
    elif action == "remove":
        args = base + ["/Delete", "/F"]
    else:
        args = base + ["/Change", "/ENABLE" if action == "enable" else "/DISABLE"]
    return subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, check=False)


def _text(completed):
    return (completed.stdout + completed.stderr).decode("utf-8", "replace").strip()


def _run_every_course(args):
    codes, failures = {}, []
    for workspace in registry.list_workspaces():
        pool = None
        try:
            pool, opened = _open(workspace["name"])
            media = _media(pool.root)
            if not media.get("repo") and not media.get("package"):
                continue
            codes[workspace["name"]] = _dispatch(args, pool, opened, media, emit=False)
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
            code = 2 if isinstance(exc, ValueError) else 4
            codes[workspace["name"]] = code
            failures.append({"course": workspace["name"], "error": git_sync.sanitize(str(exc))})
        finally:
            if pool is not None:
                pool.close()
    overall = 2 if 2 in codes.values() else (3 if 3 in codes.values() else (4 if 4 in codes.values() else 0))
    print(json.dumps({"status": _code_status(overall), "courses": codes,
                      "failures": failures}, ensure_ascii=False, indent=2))
    return overall


def _code_status(code):
    return {0: "success", 2: "failed", 3: "conflict", 4: "partial"}.get(code, "failed")


def _finish(args, pool, receipt, code, emit=True):
    """Keep only the latest complete receipt per course; print it or a short summary."""
    path = pool.root / ".lessonkit/course-sync" / RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"exit_code": code, **receipt}, ensure_ascii=False, indent=2)
                    + "\n", encoding="utf-8")
    if not emit:
        return code
    if args.json_output:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    else:
        print(f"{receipt.get('status')}: {_summary(receipt)}")
    return code


def _summary(receipt):
    if receipt.get("changes") is not None:
        return (f"{len(receipt.get('changes') or [])} 项待接收、"
                f"{len(receipt.get('outgoing') or [])} 项待外发、"
                f"{len(receipt.get('conflicts') or [])} 项待选侧")
    if receipt.get("assets") is not None:
        return f"{receipt['assets']} 项资产 → {receipt.get('destination', '')}".strip()
    return receipt.get("operation") or ""


def _required(value, flag):
    if not value:
        raise _InputError(f"{flag} is required")
    return value


if __name__ == "__main__":
    raise SystemExit(main(prog="lesson-kit course-sync"))
