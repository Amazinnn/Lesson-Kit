"""Read-only Agent-facing learning evidence queries."""

import argparse
import json
import sqlite3
from pathlib import Path

from workbench.data import evidence


def execute(pool, entity, target, *, limit=evidence.DEFAULT_LIMIT):
    if entity == "kp":
        return evidence.for_kp(pool, target, limit=limit)
    raise ValueError(f"unknown evidence entity: {entity}")


def build_parser(prog="lesson-kit evidence"):
    parser = argparse.ArgumentParser(
        prog=prog,
        description="read bounded human-readable learning evidence without writing state",
    )
    parser.add_argument("name", help="registered Lesson Kit workspace")
    parser.add_argument("entity", choices=["kp"])
    parser.add_argument("target", help="knowledge point id")
    parser.add_argument(
        "--limit",
        type=int,
        default=evidence.DEFAULT_LIMIT,
        help=f"recent evidence rows to return (1-{evidence.MAX_LIMIT}, default {evidence.DEFAULT_LIMIT})",
    )
    return parser


def main(argv=None, prog="lesson-kit evidence"):
    args = build_parser(prog).parse_args(argv)
    return run(args)


def run(args):
    from workbench.cli import main as cli

    workspace = cli._workspace(args.name)
    db_path = Path(workspace["path"]) / workspace["db"]
    if not db_path.is_file():
        print(json.dumps({
            "error": f"workspace database is not a regular file: {db_path}"
        }, ensure_ascii=False))
        return 2
    pool = cli._pool(workspace)
    try:
        result = execute(pool, args.entity, args.target, limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


if __name__ == "__main__":
    raise SystemExit(main(prog="lesson-kit-evidence"))
