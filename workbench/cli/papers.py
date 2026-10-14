"""Save an exported practice manifest as one reusable paper."""

import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from workbench.data import practice_sets


def build_parser(prog="lesson-kit papers"):
    parser = argparse.ArgumentParser(
        prog=prog,
        description="save a practice manifest as a reusable Workbench paper",
    )
    parser.add_argument("name", help="registered Lesson Kit workspace")
    parser.add_argument("action", choices=["save"])
    parser.add_argument("--input", required=True, help="practice-set manifest JSON")
    return parser


def main(argv=None, prog="lesson-kit papers"):
    # Reuse the super-CLI workspace resolver and Pool; this extension only
    # checks the manifest and delegates persistence to the Data writer.
    from workbench.cli import main as cli

    args = build_parser(prog).parse_args(argv)
    workspace = cli._workspace(args.name)
    db_path = Path(workspace["path"]) / workspace["db"]
    pool = None
    try:
        if not db_path.is_file():
            raise FileNotFoundError(f"pool database not found: {db_path}")
        pool = cli._pool(workspace)
        saved = practice_sets.save_manifest(pool, practice_sets.read(args.input))
        print(json.dumps({
            "practice_set_id": saved["practice_set_id"],
            "title": saved["title"],
            "count": saved["count"],
            "url": f"/w/{quote(args.name, safe='')}/practice-sets",
        }, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        if pool is not None:
            pool.close()


if __name__ == "__main__":
    raise SystemExit(main(prog="lesson-kit papers"))
