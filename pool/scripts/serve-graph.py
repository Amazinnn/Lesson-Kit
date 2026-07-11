#!/usr/bin/env python3
"""Serve an editable local knowledge graph for a lesson-kit pool."""

import argparse
import importlib.util
import json
import mimetypes
import sqlite3
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Sequence
from urllib.parse import parse_qs, unquote, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FRONTEND_DIST = REPO_ROOT / "frontend" / "editable-graph" / "dist"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pool_schema import PROBLEM_STATES, ensure_learning_state_schema, table_exists  # noqa: E402
from learner_signals import upsert_learner_signal  # noqa: E402


RENDER_SPEC = importlib.util.spec_from_file_location(
    "render_graph_html",
    SCRIPT_DIR / "render-graph-html.py",
)
render_graph_html = importlib.util.module_from_spec(RENDER_SPEC)
assert RENDER_SPEC.loader is not None
sys.modules["render_graph_html"] = render_graph_html
RENDER_SPEC.loader.exec_module(render_graph_html)

FOCUS_SPEC = importlib.util.spec_from_file_location(
    "query_focus_map",
    SCRIPT_DIR / "query-focus-map.py",
)
query_focus_map = importlib.util.module_from_spec(FOCUS_SPEC)
assert FOCUS_SPEC.loader is not None
sys.modules["query_focus_map"] = query_focus_map
FOCUS_SPEC.loader.exec_module(query_focus_map)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve a localhost editable lesson-kit knowledge graph.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument("--course", required=True, help="Course prefix, e.g. dmath.")
    parser.add_argument("--chapter", required=True, help="Chapter code, e.g. ch06.")
    parser.add_argument("--course-name", required=True, help="Human-readable course name.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port. Defaults to 8765.")
    parser.add_argument(
        "--signals",
        default=None,
        help="Optional signal-map JSON file used by /api/focus-map.",
    )
    return parser.parse_args(argv)


def scoped_kp_id(course: str, chapter: str, kp_id: str) -> bool:
    return kp_id.startswith(f"{course}-{chapter}-kp-")


def scoped_problem_id(course: str, chapter: str, problem_id: str) -> bool:
    return problem_id.startswith(f"{course}-{chapter}-prob-")


def load_graph(db_path: Path, course: str, chapter: str, course_name: str) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        graph = render_graph_html.build_graph_data(conn, course, chapter, course_name)
    finally:
        conn.close()
    graph["meta"]["editable"] = True
    return graph


def load_focus_map(
    db_path: Path,
    course: str,
    chapter: str,
    seed_ids: Sequence[str],
    target_id: Optional[str],
    depth: int,
    max_nodes: int,
    directed: bool,
    signals_path: Optional[Path] = None,
) -> Dict[str, Any]:
    if not seed_ids:
        raise ValueError("at least one seed is required")
    signals = query_focus_map.load_signal_map(str(signals_path)) if signals_path else None
    conn = sqlite3.connect(db_path)
    try:
        packet = query_focus_map.build_focus_map(
            conn,
            course=course,
            chapter=chapter,
            seed_ids=seed_ids,
            target_id=target_id,
            depth=depth,
            max_nodes=max_nodes,
            signals=signals,
            directed=directed,
        )
    finally:
        conn.close()
    packet["meta"]["editable"] = True
    return packet


def query_int(values: Dict[str, list[str]], key: str, default: int, minimum: int, maximum: int) -> int:
    raw = values.get(key, [str(default)])[-1]
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def query_bool(values: Dict[str, list[str]], key: str, default: bool = False) -> bool:
    if key not in values:
        return default
    raw = str(values.get(key, [""])[-1]).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def query_seeds(values: Dict[str, list[str]]) -> list[str]:
    seed_ids: list[str] = []
    for raw in values.get("seed", []):
        for item in str(raw).split(","):
            item = item.strip()
            if item and item not in seed_ids:
                seed_ids.append(item)
    return seed_ids


def update_kp_text(
    db_path: Path,
    course: str,
    chapter: str,
    kp_id: str,
    body: Any,
    fragile: Any,
) -> Dict[str, str]:
    if not scoped_kp_id(course, chapter, kp_id):
        raise ValueError(f"KP is outside the active chapter: {kp_id}")
    if body is not None and not isinstance(body, str):
        raise ValueError("body must be a string or null")
    if fragile is not None and not isinstance(fragile, str):
        raise ValueError("fragile must be a string or null")

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM knowledge_points WHERE kp_id = ?",
            (kp_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"KP not found: {kp_id}")
        clean_fragile = fragile.strip() if isinstance(fragile, str) and fragile.strip() else None
        conn.execute(
            """
            UPDATE knowledge_points
            SET body = ?, fragile = ?, updated_at = datetime('now')
            WHERE kp_id = ?
            """,
            (body, clean_fragile, kp_id),
        )
        conn.commit()
        return {"kp_id": kp_id, "body": body or "", "fragile": clean_fragile or ""}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def record_problem_status(
    db_path: Path,
    course: str,
    chapter: str,
    problem_id: str,
    status: Any,
    note: Any = "",
) -> Dict[str, str]:
    if not scoped_problem_id(course, chapter, problem_id):
        raise ValueError(f"Problem is outside the active chapter: {problem_id}")
    if status not in PROBLEM_STATES:
        raise ValueError(f"invalid status: {status}")
    if note is not None and not isinstance(note, str):
        raise ValueError("note must be a string or null")

    conn = sqlite3.connect(db_path)
    try:
        if not table_exists(conn, "problems"):
            raise ValueError("problems table missing")
        row = conn.execute(
            "SELECT kp_ids FROM problems WHERE problem_id = ?",
            (problem_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"problem not found: {problem_id}")
        ensure_learning_state_schema(conn)
        clean_note = note.strip() if isinstance(note, str) and note.strip() else None
        conn.execute(
            """
            INSERT INTO problem_progress (problem_id, status, note, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(problem_id) DO UPDATE SET
                status = excluded.status,
                note = excluded.note,
                updated_at = datetime('now')
            """,
            (problem_id, status, clean_note),
        )
        conn.execute(
            "INSERT INTO problem_attempts (problem_id, status, note) VALUES (?, ?, ?)",
            (problem_id, status, clean_note),
        )
        if status in {"wrong", "stuck"}:
            try:
                kp_ids = json.loads(row[0] or "[]")
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid kp_ids for problem {problem_id}") from exc
            for kp_id in kp_ids:
                upsert_learner_signal(
                    conn,
                    "node",
                    str(kp_id),
                    "weak_node",
                    note,
                    "problem",
                    problem_id,
                )
        conn.commit()
        return {"problem_id": problem_id, "status": str(status), "note": clean_note or ""}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class GraphHandler(BaseHTTPRequestHandler):
    db_path: Path
    course: str
    chapter: str
    course_name: str
    signals_path: Optional[Path]

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        if not raw.strip():
            return {}
        return json.loads(raw)

    def send_text(self, status: HTTPStatus, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, status: HTTPStatus, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        self.send_text(
            status,
            json.dumps(payload, ensure_ascii=False),
            "application/json; charset=utf-8",
        )

    def send_frontend_file(self, relative: str) -> bool:
        if not FRONTEND_DIST.is_dir():
            return False
        target = (FRONTEND_DIST / relative).resolve()
        try:
            target.relative_to(FRONTEND_DIST.resolve())
        except ValueError:
            return False
        if not target.is_file():
            return False
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_bytes(HTTPStatus.OK, target.read_bytes(), content_type)
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/graph"}:
            if self.send_frontend_file("index.html"):
                return
            graph = load_graph(self.db_path, self.course, self.chapter, self.course_name)
            self.send_text(
                HTTPStatus.OK,
                render_graph_html.render_html(graph, editable=True),
                "text/html; charset=utf-8",
            )
            return
        if parsed.path == "/api/graph":
            graph = load_graph(self.db_path, self.course, self.chapter, self.course_name)
            self.send_json(HTTPStatus.OK, graph)
            return
        if parsed.path == "/api/focus-map":
            try:
                params = parse_qs(parsed.query)
                target_id = (params.get("target", [""])[-1] or "").strip() or None
                packet = load_focus_map(
                    self.db_path,
                    self.course,
                    self.chapter,
                    query_seeds(params),
                    target_id,
                    query_int(params, "depth", 2, 0, 6),
                    query_int(params, "max_nodes", 30, 1, 120),
                    query_bool(params, "directed", False),
                    self.signals_path,
                )
                self.send_json(HTTPStatus.OK, packet)
            except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        if parsed.path.startswith("/assets/"):
            if self.send_frontend_file(parsed.path.removeprefix("/")):
                return
        self.send_text(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/api/kp/"):
                kp_id = unquote(parsed.path.removeprefix("/api/kp/"))
                payload = self.read_json()
                result = update_kp_text(
                    self.db_path,
                    self.course,
                    self.chapter,
                    kp_id,
                    payload.get("body"),
                    payload.get("fragile"),
                )
                self.send_json(HTTPStatus.OK, {"ok": True, **result})
                return
            if parsed.path.startswith("/api/problem/") and parsed.path.endswith("/record"):
                problem_id = unquote(parsed.path.removeprefix("/api/problem/").removesuffix("/record"))
                payload = self.read_json()
                result = record_problem_status(
                    self.db_path,
                    self.course,
                    self.chapter,
                    problem_id,
                    payload.get("status"),
                    payload.get("note", ""),
                )
                self.send_json(HTTPStatus.OK, {"ok": True, **result})
                return
        except (json.JSONDecodeError, ValueError, sqlite3.Error) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self.send_text(HTTPStatus.NOT_FOUND, "not found")


def serve(args: argparse.Namespace) -> None:
    db_path = Path(args.db)
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")
    signals_path = Path(args.signals) if args.signals else None
    if signals_path and not signals_path.is_file():
        raise FileNotFoundError(f"Signal map not found: {signals_path}")
    handler = type(
        "ConfiguredGraphHandler",
        (GraphHandler,),
        {
            "db_path": db_path,
            "course": args.course,
            "chapter": args.chapter,
            "course_name": args.course_name,
            "signals_path": signals_path,
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving editable graph at http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.host not in {"127.0.0.1", "localhost"}:
        print("ERROR: editable graph server must bind to 127.0.0.1 or localhost", file=sys.stderr)
        return 1
    try:
        serve(args)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
