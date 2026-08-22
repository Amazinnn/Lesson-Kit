"""HTTP server: routing, JSON API dispatch, static figure serving, pages."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from workbench import registry
from workbench.domain import weak
from workbench.server import api as api_mod
from workbench.server import pages

FRONTEND_DIST = (
    Path(__file__).resolve().parents[2] / "frontend" / "editable-graph" / "dist"
)
STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
}


def _content_type(suffix):
    return CONTENT_TYPES.get(suffix, "application/octet-stream")

ROUTES = [
    ("GET", "/api/hub/workspaces", api_mod.hub_workspaces),
    ("GET", "/api/w/{name}/weak", api_mod.weak_list),
    ("GET", "/api/w/{name}/due", api_mod.due_list),
    ("POST", "/api/w/{name}/pull", api_mod.pull_problems),
    ("POST", "/api/w/{name}/practice", api_mod.practice),
    ("POST", "/api/w/{name}/feedback", api_mod.feedback_record),
    ("GET", "/api/w/{name}/problem/{problem_id}", api_mod.problem_detail),
    ("GET", "/api/w/{name}/kp/{kp_id}", api_mod.kp_detail),
    ("GET", "/api/w/{name}/graph/model", api_mod.graph_model),
    ("POST", "/api/w/{name}/graph/state", api_mod.graph_state),
    ("POST", "/api/w/{name}/graph/kp", api_mod.graph_kp),
    ("POST", "/api/w/{name}/ai/{operation}", api_mod.ai_run),
    ("GET", "/api/w/{name}/ai/jobs/{job_id}", api_mod.ai_status),
    ("GET", "/api/w/{name}/explain/{problem_id}", api_mod.explain_result),
    ("GET", "/api/w/{name}/graph", api_mod.graph_artifact),
]


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "Workbench/0.1"

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if path == "/":
            self._send_html(200, pages.hub_page(self._hub_data()))
            return
        if path.startswith("/static/"):
            self._send_static(path)
            return
        if path.startswith("/w/"):
            self._send_page(path)
            return
        if path.startswith("/api/w/") and "/figures/" in path:
            self._send_figure(path)
            return
        if path.startswith("/api/w/") and path.endswith("/graph/artifact"):
            self._send_graph_artifact(path)
            return

        handler, params = self._match_route(method, path)
        if handler is None:
            self._send_json(404, {"error": "not found"})
            return

        body = None
        if method == "POST":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw.decode("utf-8")) if raw else {}

        name = params.pop("name", None)
        if name is None:
            self._send_json(200, handler(None, None, query, body))
            return
        workspace = registry.get_workspace(name)
        pool = api_mod._pool_for(workspace)
        try:
            result = handler(pool, workspace, {**query, **params}, body)
        except api_mod.ApiError as exc:
            self._send_json(exc.status, {"error": exc.message})
            return
        except KeyError as exc:
            self._send_json(404, {"error": f"unknown: {exc}"})
            return
        except FileNotFoundError as exc:
            self._send_json(404, {"error": f"unknown: {exc}"})
            return
        finally:
            pool.close()
        self._send_json(200, result)

    def _hub_data(self):
        return api_mod.hub_workspaces(None, None, {}, None)

    def _send_static(self, path):
        relative = path[len("/static/"):]
        if ".." in relative.split("/"):
            self._send_json(404, {"error": "not found"})
            return
        for base in (STATIC_DIR, FRONTEND_DIST):
            target = (base / relative).resolve()
            if not target.is_relative_to(base.resolve()):
                self._send_json(404, {"error": "not found"})
                return
            if target.is_file():
                data = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", _content_type(target.suffix))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        self._send_json(404, {"error": "not found"})

    def _send_page(self, path):
        parts = [s for s in path.split("/") if s]
        # /w/{name}/{practice|kps|kp/{id}|graph|session-end}
        name = parts[1]
        try:
            workspace = registry.get_workspace(name)
        except KeyError:
            self._send_html(404, pages._base("not found", "<h1>not found</h1>"))
            return
        workspaces = registry.list_workspaces()
        pool = api_mod._pool_for(workspace)
        try:
            weak_items = self._weak_items(workspace, pool)
            page = parts[2] if len(parts) > 2 else "practice"
            if page == "kp":
                kp_id = parts[3] if len(parts) > 3 else ""
                html_body = pages.kp_page(workspace, workspaces, weak_items,
                                          pool, kp_id)
            elif page == "kps":
                html_body = pages.kps_page(workspace, workspaces, weak_items, pool)
            elif page == "graph":
                html_body = pages.graph_page(
                    workspace, workspaces, weak_items,
                    self._graph_artifact(workspace).is_file(),
                )
            elif page == "session-end":
                html_body = pages.session_end_page(workspace, workspaces, weak_items)
            else:
                html_body = pages.practice_page(workspace, workspaces, weak_items)
        finally:
            pool.close()
        self._send_html(200, html_body)

    def _weak_items(self, workspace, pool):
        from datetime import date
        prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
        return weak.score_all(
            pool.kps(prefix), pool.signals(), pool.schedule_rows(),
            pool.relations(), set(), date.today(),
        )[:20]

    def _graph_artifact(self, workspace):
        course = workspace.get("active_course", "")
        chapter = workspace.get("active_chapter", "")
        return (Path(workspace["path"]) / "output" / course / chapter
                / f"{chapter}-graph.html")

    def _send_figure(self, path):
        parts = path.split("/")
        # /api/w/{name}/figures/{course}/{chapter}/{file}
        name = parts[3]
        logical = "/".join(parts[5:])
        try:
            workspace = registry.get_workspace(name)
        except KeyError:
            self._send_json(404, {"error": "unknown workspace"})
            return
        pool = api_mod._pool_for(workspace)
        try:
            base = (Path(workspace["path"]) / ".lessonkit" / "figures").resolve()
            target = (base / logical).resolve()
            if not str(target).startswith(str(base)):
                self._send_json(403, {"error": "forbidden"})
                return
            if not target.is_file():
                self._send_json(404, {"error": "figure not found"})
                return
            data = target.read_bytes()
        finally:
            pool.close()
        self.send_response(200)
        self.send_header("Content-Type", _content_type(target.suffix))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_graph_artifact(self, path):
        parts = path.split("/")
        # /api/w/{name}/graph/artifact — raw self-contained graph HTML
        name = parts[3]
        try:
            workspace = registry.get_workspace(name)
        except KeyError:
            self._send_json(404, {"error": "unknown workspace"})
            return
        artifact = self._graph_artifact(workspace)
        if not artifact.is_file():
            self._send_json(404, {"error": "graph artifact missing"})
            return
        data = artifact.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _match_route(self, method, path):
        segments = [s for s in path.split("/") if s]
        for rmethod, pattern, handler in ROUTES:
            if rmethod != method:
                continue
            pattern_segments = [s for s in pattern.split("/") if s]
            if len(segments) != len(pattern_segments):
                continue
            params = {}
            for pseg, seg in zip(pattern_segments, segments):
                if pseg.startswith("{") and pseg.endswith("}"):
                    params[pseg[1:-1]] = seg
                elif pseg != seg:
                    break
            else:
                return handler, params
        return None, None

    def _send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, status, text):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def create_server(host="127.0.0.1", port=3081):
    return ThreadingHTTPServer((host, port), WorkbenchHandler)


def serve(port=3081):
    server = create_server(host="127.0.0.1", port=port)
    print(f"lesson-kit workbench: http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
