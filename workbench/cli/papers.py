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
    parser.add_argument("action", choices=["save", "list", "get", "preview", "update", "delete"])
    parser.add_argument('paper_id', nargs='?', help='explicit existing ps-NNN target')
    parser.add_argument("--input", help="practice-set manifest JSON")
    parser.add_argument('--confirmation', help='JSON file containing the current preview confirmation')
    return parser


def main(argv=None, prog="lesson-kit papers"):
    args = build_parser(prog).parse_args(argv)
    return run(args)


def run(args):
    # Reuse the super-CLI workspace resolver and Pool; this extension only
    # checks the manifest and delegates persistence to the Data writer.
    from workbench.cli import main as cli

    workspace = cli._workspace(args.name)
    db_path = Path(workspace["path"]) / workspace["db"]
    pool = None
    try:
        if not db_path.is_file():
            raise FileNotFoundError(f"pool database not found: {db_path}")
        pool = cli._pool(workspace)
        if args.action == 'list':
            print(json.dumps({'practice_sets': practice_sets.list_saved(pool)}, ensure_ascii=False, indent=2))
            return 0
        if args.action != 'save' and not args.paper_id:
            raise ValueError('an explicit existing paper_id is required')
        if args.action in {'get', 'delete'}:
            result = (practice_sets.get_saved(pool, args.paper_id) if args.action == 'get'
                      else practice_sets.delete_saved(pool, args.paper_id))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not args.input:
            raise ValueError('--input is required')
        manifest = practice_sets.read(args.input)
        if args.action != 'save':
            if manifest.get('course', pool.course) != pool.course:
                raise ValueError('manifest course does not match workspace')
            fields = dict(title=manifest.get('title'), request=manifest.get('request'),
                          description=manifest.get('description'))
            if 'items' in manifest:
                fields['problem_ids'] = [item['problem_id'] for item in manifest['items']]
            if args.action == 'preview':
                result = practice_sets.preview_update(pool, args.paper_id, **fields)
            else:
                confirmation = practice_sets.read(args.confirmation) if args.confirmation else None
                if confirmation and 'confirmation' in confirmation:
                    confirmation = confirmation['confirmation']
                result = practice_sets.update_saved(pool, args.paper_id, confirmation=confirmation, **fields)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        saved = practice_sets.save_manifest(pool, manifest)
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
