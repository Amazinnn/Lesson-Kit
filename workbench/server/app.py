"""HTTP server: routing, JSON API dispatch, static figure serving, pages."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from workbench import registry
from workbench.server import api as api_mod
from workbench.server import pages

FRONTEND_DIST = (
    Path(__file__).resolve().parents[2] / "frontend" / "editable-graph" / "dist"
)

ROUTES = [
    ("GET", "/api/hub/workspaces", api_mod.hub_workspaces),
    ("GET", "/api/w/{name}/weak", api_mod.weak_list),
    ("GET", "/api/w/{name}/due", api_mod.due_list),
    ("POST", "/api/w/{name}/pull", api_mod.pull_problems),
    ("POST", "/api/w/{name}/practice", api_mod.practice),
    ("POST", "/api/w/{name}/feedback", api_mod.feedback_record),
    ("GET", "/api/w/{name}/problem/{problem_id}", api_mod.problem_detail),
    ("GET", "/api/w/{name}/kp/{kp_id}", api_mod.kp_detail),
    ("POST", "/api/w/{name}/ai/{operation}", api_mod.ai_run),
    ("GET", "/api/w/{name}/ai/jobs/{job_id}", api_mod.ai_status),
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
        if path.startswith("/w/") and path.endswith("/"):
            self._send_workspace_page(path)
            return
        if path.startswith("/api/w/") and "/figures/" in path:
            self._send_figure(path)
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
        finally:
            pool.close()
        self._send_json(200, result)

    def _hub_data(self):
        return api_mod.hub_workspaces(None, None, {}, None)

    def _send_workspace_page(self, path):
        name = path.split("/")[2]
        try:
            workspace = registry.get_workspace(name)
        except KeyError:
            self._send_html(404, pages._page("not found", "<h1>not found</h1>"))
            return
        pool = api_mod._pool_for(workspace)
        try:
            from datetime import date
            from workbench.domain import weak
            prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
            weak_items = weak.score_all(
                pool.kps(prefix), pool.signals(), pool.schedule_rows(),
                pool.relations(), set(), date.today(),
            )[:20]
            due_items = api_mod.due_list(pool, workspace, {}, None)
        finally:
            pool.close()
        self._send_html(200, pages.workspace_page(workspace, weak_items, due_items))

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
        self.send_header("Content-Type", "image/png")
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
