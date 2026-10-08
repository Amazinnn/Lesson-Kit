"""CLI-facing practice experience operations for explicit Agent mutations."""

import argparse
import json
import sqlite3

from workbench.data import experience


def execute(pool, action, kp_id, *, payload=None, expected_revision=None):
    """Run one explicit Agent operation and return its JSON-ready result."""
    if action == "get":
        return {"experience": experience.get(pool, kp_id)}
    if action == "create":
        payload = _payload(payload)
        return {
            "experience": experience.create(
                pool,
                kp_id,
                payload.get("content"),
                payload.get("problem_ids", []),
                updated_by="agent",
            )
        }
    if action == "update":
        payload = _payload(payload)
        return {
            "experience": experience.update(
                pool,
                kp_id,
                expected_revision,
                payload.get("content"),
                payload.get("problem_ids", []),
                updated_by="agent",
            )
        }
    if action == "delete":
        return experience.delete(pool, kp_id, expected_revision)
    raise ValueError(f"unknown experience action: {action}")


def _payload(value):
    if not isinstance(value, dict):
        raise ValueError("experience create/update requires a JSON object")
    unknown = sorted(set(value) - {"content", "problem_ids"})
    if unknown:
        raise ValueError(f"unsupported experience field(s): {unknown}")
    return value


def build_parser(prog="lesson-kit experience"):
    parser = argparse.ArgumentParser(
        prog=prog,
        description="explicit Agent CRUD for one knowledge point's practice experience",
    )
    parser.add_argument("name", help="registered Lesson Kit workspace")
    parser.add_argument("action", choices=["get", "create", "update", "delete"])
    parser.add_argument("kp_id", help="knowledge point id")
    parser.add_argument(
        "--input",
        help="JSON file (or - for stdin): {\"content\": \"…\", \"problem_ids\": [\"…\"]}",
    )
    parser.add_argument("--expected-revision", type=int)
    return parser


def main(argv=None, prog="lesson-kit experience"):
    # Import the super-CLI helpers lazily so this module stays a thin adapter and
    # does not duplicate workspace resolution or JSON input semantics.
    from workbench.cli import main as cli

    args = build_parser(prog).parse_args(argv)
    workspace = cli._workspace(args.name)
    pool = cli._pool(workspace)
    try:
        if args.action in {"create", "update"}:
            payload = cli._json_input(args.input)
        else:
            payload = None
        if args.action in {"update", "delete"} and args.expected_revision is None:
            raise ValueError(f"experience {args.action} requires --expected-revision")
        result = execute(
            pool,
            args.action,
            args.kp_id,
            payload=payload,
            expected_revision=args.expected_revision,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except experience.RevisionConflict as exc:
        print(json.dumps({"error": str(exc), "conflict": True}, ensure_ascii=False))
        return 2
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


if __name__ == "__main__":
    raise SystemExit(main(prog="lesson-kit-experience"))
