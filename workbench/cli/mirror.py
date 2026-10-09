"""Installed CLI extension for the checked-out JSON content repository."""

import argparse
import json

from workbench.cli import main as cli_main
from workbench.data import content_mirror


def build_parser(prog="lesson-kit mirror"):
    parser = argparse.ArgumentParser(
        prog=prog,
        description="synchronize governed authored content with a local JSON repository checkout",
    )
    parser.add_argument("workspace")
    sub = parser.add_subparsers(dest="action", required=True)

    action = sub.add_parser("init", help="bootstrap repository JSON from the current pool")
    action.add_argument("--repo", required=True)
    action.add_argument("--entity")
    action.add_argument("--dry-run", action="store_true")

    for name, help_text in (
        ("check", "validate and classify repository entities without writing"),
        ("status", "show per-entity synchronization direction without writing"),
    ):
        action = sub.add_parser(name, help=help_text)
        action.add_argument("--repo", required=True)
        action.add_argument("--entity")

    action = sub.add_parser("sync", help="synchronize independent entities")
    action.add_argument("--repo", required=True)
    action.add_argument("--entity")
    action.add_argument("--dry-run", action="store_true")
    return parser


def _exit_code(report):
    bad = {"invalid", "conflict"}
    return 2 if any(item.get("status") in bad for item in report["items"]) \
        or any(item.get("status") == "invalid" for item in report["delete_requests"]) else 0


def main(argv=None, prog="lesson-kit mirror"):
    args = build_parser(prog).parse_args(argv)
    workspace = cli_main._workspace(args.workspace)
    pool = cli_main._pool(workspace)
    try:
        if args.action == "init":
            report = content_mirror.init(
                pool, args.repo, entity_id=args.entity, dry_run=args.dry_run
            )
            if args.dry_run:
                report["dry_run"] = True
        elif args.action in {"check", "status"}:
            report = content_mirror.plan(pool, args.repo, entity_id=args.entity)
        else:
            report = content_mirror.sync(
                pool, args.repo, entity_id=args.entity, dry_run=args.dry_run
            )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return _exit_code(report)
    except (content_mirror.MirrorError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    finally:
        pool.close()


if __name__ == "__main__":
    raise SystemExit(main())
