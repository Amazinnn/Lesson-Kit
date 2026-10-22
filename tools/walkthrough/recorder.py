"""Request-sequence recorder and verdict report for the workbench visual walkthrough.

Specification (the only source of truth for this file):
``openspec/changes/workbench-visual-language-v2/design-notes/walkthrough-harness.md``

  §2    capture — in-process, at ``app.WorkbenchHandler._dispatch``; never an
         external proxy, never a change to the product
  §2.4  canonicalisation — route template, payload key set, payload shape,
         value whitelist, read/write split
  §2.6  diff algorithm (``difflib``) and the evidence files
  §7    verdicts (PASS / FAIL / PENDING / BLOCKED) and the report

Red lines honoured here (§8.3): the recorder only *reads* the request stream
and writes evidence files.  It never touches the pool, never changes a
response, and every hook swallows its own exceptions so a broken recorder can
never break a request (§2.1).
"""

import argparse
import difflib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

RECORD_FORMAT_VERSION = 1

# ── §2.4(d) value whitelist ───────────────────────────────────────────────
# Enumerated fields whose *values* take part in the diff.  Their key sets
# already participate via §2.4(c); these are the values that are stable across
# runs and therefore meaningful when compared.
VALUE_WHITELIST = (
    "practice_mode",
    "rating_mode",
    "reveal_timing",
    "stuck",
    "edit_existing",
    "item_type",
    "verdict",
)

# ── §2.4(a) id-shaped path segments ───────────────────────────────────────
_ID_SEGMENT_PATTERNS = (
    re.compile(r"^ps-\d+$"),
    re.compile(r"^\d+$"),
    re.compile(r"^kp-[\w-]+-\d+$"),
    re.compile(r"^conv-[\w-]+$"),
    re.compile(r"^run-\d+$"),
    re.compile(r"^goal-\d+$"),
    re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I),
    re.compile(r"^[0-9a-f]{16,}$", re.I),
)


class RecorderError(RuntimeError):
    """Raised when the recorder cannot be installed (never silently ignored)."""


# ─────────────────────────────────────────────────────────────────────────
# byte capture (§2.3 tee reader)
# ─────────────────────────────────────────────────────────────────────────


class _ByteSink:
    """Collects the bytes the business code reads out of the request body."""

    def __init__(self):
        self._chunks = []

    def write(self, data):
        if data:
            self._chunks.append(bytes(data))

    def bytes(self):
        return b"".join(self._chunks)


class _TeeReader:
    """Wraps ``rfile`` so a read is returned unchanged *and* copied to a sink.

    ``_dispatch`` reads the body exactly once (``self.rfile.read(length)``), so
    wrapping the reader hands the business code the same bytes while letting
    the recorder see the payload without reading the stream twice.
    """

    def __init__(self, source, sink):
        self._source = source
        self._sink = sink

    def read(self, size=-1):
        data = self._source.read(size)
        self._sink.write(data)
        return data

    def readline(self, *args):
        data = self._source.readline(*args)
        self._sink.write(data)
        return data

    def readinto(self, buffer):
        n = self._source.readinto(buffer)
        if n:
            self._sink.write(memoryview(buffer)[:n])
        return n

    def __getattr__(self, name):
        return getattr(self._source, name)


# ─────────────────────────────────────────────────────────────────────────
# canonicalisation (§2.4)
# ─────────────────────────────────────────────────────────────────────────


def normalize_path(path):
    """Replace id-shaped path segments with ``{id}`` (§2.4(a))."""
    parts = []
    for segment in path.split("/"):
        if any(p.match(segment) for p in _ID_SEGMENT_PATTERNS):
            parts.append("{id}")
        else:
            parts.append(segment)
    return "/".join(parts)


def route_template(routes, method, path):
    """Return the route template for ``method``/``path``.

    Mirrors ``app.WorkbenchHandler._match_route`` (§2.4(a)) but returns the
    *pattern* instead of the handler: the route table is the frozen API
    surface, so a changed template is an API change.

    ``routes`` is ``app.ROUTES`` — a list of ``(method, pattern, handler)``.
    """
    segments = [unquote(s) for s in path.split("/") if s]
    for rmethod, pattern, _handler in routes:
        if rmethod != method:
            continue
        pattern_segments = [s for s in pattern.split("/") if s]
        if len(segments) != len(pattern_segments):
            continue
        for pseg, seg in zip(pattern_segments, segments):
            if pseg.startswith("{") and pseg.endswith("}"):
                continue
            if pseg != seg:
                break
        else:
            return f"{method} {pattern}"
    return f"<UNMATCHED> {normalize_path(path)}"


def _shape_of(value):
    """Payload shape of one value: ``scalar`` / ``[]`` / ``{}`` / ``[]{}``."""
    if isinstance(value, dict):
        return "{}"
    if isinstance(value, list):
        if value and all(isinstance(v, dict) for v in value):
            return "[]{}"
        return "[]"
    return "scalar"


def canonical_payload_shape(body):
    """Return ``(shape_by_key, subkeys_by_key)`` for a JSON object body.

    ``subkeys`` carries the union of the sub-keys of every object array, so a
    change inside ``drafts[]`` is still visible even though the values do not
    take part in the diff (§2.4(c)).
    """
    if not isinstance(body, dict):
        return {}, {}
    shape = {key: _shape_of(value) for key, value in sorted(body.items())}
    subkeys = {}
    for key, value in body.items():
        if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
            keys = sorted({sub for item in value for sub in item})
            if keys:
                subkeys[key] = keys
    return shape, subkeys


def whitelist_values(body, whitelist=VALUE_WHITELIST):
    """Collect whitelisted enum values from anywhere in the payload."""
    found = {}

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{path}.{key}" if path else key
                if key in whitelist and not isinstance(value, (dict, list)):
                    found[here] = value
                else:
                    walk(value, here)
        elif isinstance(node, list):
            for item in node:
                walk(item, f"{path}[]")

    walk(body, "")
    return dict(sorted(found.items()))


def canonical_signature(record):
    """The canonical form of one request (§2.4 / §2.6)."""
    body = record.get("body")
    shape, subkeys = canonical_payload_shape(body)
    return {
        "method": record["method"],
        "route": record["route"],
        "keys": list(record.get("body_keys") or []),
        "shape": shape,
        "subkeys": subkeys,
        "vals": whitelist_values(body) if body else {},
    }


def signature_text(signature):
    """One-line rendering of a canonical signature (§2.6)."""
    return (
        f"{signature['method']} {signature['route']} "
        f"| keys={signature['keys']} "
        f"| shape={signature['shape']} "
        f"| vals={signature['vals']}"
    )


def is_write(record):
    """§2.4(e): a write request is a mutating method on an ``/api/`` path."""
    return (
        record["method"] in {"POST", "PATCH", "PUT", "DELETE"}
        and record["raw_path"].startswith("/api/")
    )


def is_api_read(record):
    return record["method"] == "GET" and record["raw_path"].startswith("/api/")


# ─────────────────────────────────────────────────────────────────────────
# the recorder itself (§2.2)
# ─────────────────────────────────────────────────────────────────────────


class Recorder:
    """Append-only JSONL recorder of the requests the service handled."""

    def __init__(self, out_path, phase="measure", group="exercise", keep_body=False):
        self.out_path = Path(out_path)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.phase = phase
        self.group = group
        self.keep_body = keep_body
        self._lock = threading.Lock()
        self._seq = 0
        self._start = time.monotonic()
        self._handle = self.out_path.open("w", encoding="utf-8")
        self._local = threading.local()

    # -- control surface (used by the launcher and by exercise scripts) ----
    def set_phase(self, phase, group=None):
        with self._lock:
            self.phase = phase
            if group is not None:
                self.group = group

    def events(self):
        """The records written so far (in-memory view of the file)."""
        with self._lock:
            self._handle.flush()
        return load_events(self.out_path)

    def close(self):
        with self._lock:
            if not self._handle.closed:
                self._handle.flush()
                self._handle.close()

    # -- internals --------------------------------------------------------
    def _next_seq(self):
        with self._lock:
            self._seq += 1
            return self._seq

    def emit(self, record):
        """Write one record; never raises (a broken recorder must not break a
        response — §2.1)."""
        try:
            with self._lock:
                self._handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                self._handle.flush()
        except Exception as exc:  # pragma: no cover - defensive only
            print(f"[walkthrough] recorder write failed: {exc}", file=sys.stderr)


def install(app_module, out_path, phase="measure", group="exercise",
            keep_body=None):
    """Install the in-process request recorder on ``app_module``.

    Two hooks (§2.1, §2.5):

    * ``WorkbenchHandler._dispatch`` — the single entry point of every
      request, so pages, static assets, figures, graph artifacts and 404s are
      all covered, and the payload is visible.
    * ``BaseHTTPRequestHandler.send_response`` (patched onto the handler
      class) — the only choke point all five response paths go through
      (``_send_json`` / ``_send_html`` / ``_send_static`` / ``_send_figure`` /
      ``_send_graph_artifact``), so no status code is missed.
    """
    if keep_body is None:
        keep_body = os.environ.get("WALKTHROUGH_KEEP_BODY") == "1"

    recorder = Recorder(out_path, phase=phase, group=group, keep_body=keep_body)
    handler_class = app_module.WorkbenchHandler
    original_dispatch = handler_class._dispatch
    original_send_response = handler_class.send_response

    def _recording_send_response(self, code, message=None):
        current = getattr(recorder._local, "current", None)
        if current is not None:
            current["status"] = code
        return original_send_response(self, code, message)

    def _recording_dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/__walkthrough__/"):
            return _handle_control(recorder, self, method, path)

        sink = _ByteSink()
        original_rfile = self.rfile
        self.rfile = _TeeReader(original_rfile, sink)
        record = {
            "seq": recorder._next_seq(),
            "t_ms": round((time.monotonic() - recorder._start) * 1000, 3),
            "method": method,
            "raw_path": path,
            "route": route_template(app_module.ROUTES, method, path),
            "query": _canonical_query(parsed.query),
            "body_keys": [],
            "body_shape": {},
            "body_subkeys": {},
            "status": None,
            "phase": recorder.phase,
            "group": recorder.group,
        }
        recorder._local.current = record
        try:
            return original_dispatch(self, method)
        finally:
            self.rfile = original_rfile
            current = recorder._local.current
            recorder._local.current = None
            try:
                _finalize(recorder, record, sink.bytes())
            except Exception as exc:  # pragma: no cover - defensive only
                print(f"[walkthrough] recorder failed: {exc}", file=sys.stderr)

    handler_class._dispatch = _recording_dispatch
    handler_class.send_response = _recording_send_response
    recorder.original_dispatch = original_dispatch
    recorder.original_send_response = original_send_response
    return recorder


def _canonical_query(raw_query):
    """§2.4(b): the query *key set* is kept, the values are dropped."""
    parsed = parse_qs(raw_query)
    return {key: parsed[key][0] for key in sorted(parsed)} if parsed else {}


def _finalize(recorder, record, raw_body):
    """Fill in the payload facts and write the record."""
    body = None
    if raw_body:
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            body = None
    if isinstance(body, dict):
        shape, subkeys = canonical_payload_shape(body)
        record["body_keys"] = sorted(body.keys())
        record["body_shape"] = shape
        record["body_subkeys"] = subkeys
        if recorder.keep_body:
            record["body_raw"] = raw_body.decode("utf-8", "replace")
    recorder.emit(record)


def _handle_control(recorder, handler, method, path):
    """Read-only control surface for the recorder (``/__walkthrough__/``).

    It is handled before the product's own dispatch so it never reaches the
    product router, and it is marked ``control`` so it stays out of the
    canonical request sequence.
    """
    if path == "/__walkthrough__/events" and method == "GET":
        payload = json.dumps({"events": recorder.events()}, ensure_ascii=False)
        data = payload.encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)
        return
    if path == "/__walkthrough__/phase" and method == "POST":
        length = int(handler.headers.get("Content-Length", 0) or 0)
        raw = handler.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
            body = {}
        recorder.set_phase(body.get("phase", "measure"), body.get("group"))
        data = json.dumps({"phase": recorder.phase, "group": recorder.group}).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)
        return
    handler.send_response(404)
    handler.send_header("Content-Length", "0")
    handler.end_headers()


# ─────────────────────────────────────────────────────────────────────────
# reading and diffing (§2.6)
# ─────────────────────────────────────────────────────────────────────────


def load_events(path):
    """Read a JSONL record file; missing file -> empty list."""
    path = Path(path)
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def signature_key(signature):
    """A hashable form of a canonical signature.

    ``difflib.SequenceMatcher`` hashes its elements, so the matcher runs on
    these keys while the reports keep the readable dicts.
    """
    return (
        signature["method"],
        signature["route"],
        tuple(signature["keys"]),
        tuple(sorted((key, value) for key, value in signature["shape"].items())),
        tuple(sorted((key, str(value)) for key, value in signature["vals"].items())),
        tuple(sorted((key, tuple(value)) for key, value in signature["subkeys"].items())),
    )


def ordered(events):
    """Events in the order the service *received* them.

    The JSONL is written when a request finishes, so concurrent requests land
    in the file out of order.  ``seq`` is the arrival counter, so it — not
    the file order — is the canonical sequence (§2.2).
    """
    return sorted(events, key=lambda event: event.get("seq", 0))


def diff_sequences(before_events, after_events):
    """Diff the canonical write-request sequences of two runs (§2.6).

    Returns a dict with ``added`` / ``removed`` / ``changed`` (the blocking
    L1 layer) and ``read_added`` / ``read_removed`` (the L2 layer that a
    human signs off on).
    """
    before_writes = [canonical_signature(e) for e in ordered(before_events) if is_write(e)]
    after_writes = [canonical_signature(e) for e in ordered(after_events) if is_write(e)]

    matcher = difflib.SequenceMatcher(
        a=[signature_key(s) for s in before_writes],
        b=[signature_key(s) for s in after_writes],
        autojunk=False)
    added, removed, changed = [], [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            added.extend(after_writes[j1:j2])
        elif tag == "delete":
            removed.extend(before_writes[i1:i2])
        else:  # replace — pair the two sides up positionally
            before_part = before_writes[i1:i2]
            after_part = after_writes[j1:j2]
            for offset in range(max(len(before_part), len(after_part))):
                left = before_part[offset] if offset < len(before_part) else None
                right = after_part[offset] if offset < len(after_part) else None
                if left is None:
                    added.append(right)
                elif right is None:
                    removed.append(left)
                elif left["route"] == right["route"] and left["method"] == right["method"]:
                    changed.append({"kind": "payload_changed", "before": left, "after": right})
                else:
                    changed.append({"kind": "renamed_or_replaced", "before": left, "after": right})

    before_reads = [canonical_signature(e) for e in ordered(before_events) if is_api_read(e)]
    after_reads = [canonical_signature(e) for e in ordered(after_events) if is_api_read(e)]
    read_matcher = difflib.SequenceMatcher(
        a=[signature_key(s) for s in before_reads],
        b=[signature_key(s) for s in after_reads],
        autojunk=False)
    read_added, read_removed = [], []
    for tag, i1, i2, j1, j2 in read_matcher.get_opcodes():
        if tag in ("insert", "replace"):
            read_added.extend(after_reads[j1:j2])
        if tag in ("delete", "replace"):
            read_removed.extend(before_reads[i1:i2])

    return {
        "before_count": len(before_writes),
        "after_count": len(after_writes),
        "added": added,
        "removed": removed,
        "changed": changed,
        "read_added": read_added,
        "read_removed": read_removed,
        "before_signatures": before_writes,
        "after_signatures": after_writes,
    }


def requests_diff_verdict(diff):
    """§2.6: one added, removed or changed write request is a FAIL."""
    total = len(diff["added"]) + len(diff["removed"]) + len(diff["changed"])
    if total == 0:
        return "PASS"
    return "FAIL"


# ─────────────────────────────────────────────────────────────────────────
# the report (§7)
# ─────────────────────────────────────────────────────────────────────────

#: Verdict vocabulary (§7.6.2).
PASS, FAIL, PENDING, BLOCKED, NA = "PASS", "FAIL", "PENDING", "BLOCKED", "N/A"

#: Gates whose evidence this executor cannot produce **yet**.  The
#: collector modules (``dbexport`` / ``probe``) are part of the delivery
#: now, so these gates are read from the evidence on disk; a gate whose
#: evidence is missing stays BLOCKED — "cannot be judged" — never PASS.
GATES_WITHOUT_COLLECTOR = {
    "G-2": "needs the persistence export collector (walkthrough-harness.md §4)",
    "G-3": "needs the learning-projection export collector (§4)",
    "G-4": "needs the due/weak export collector (§3.6, §4)",
    "G-6": "needs the pool schema export collector (§4.5)",
    "G-7": "needs the browser probe collector (§7.5.2)",
    "G-8": "needs the focus-sequence probe collector (§7.2)",
}

#: The phase of the requests a **collector** produced on its own (the
#: motion frames).  It is left out of the G-1 diff: the collector only
#: runs on the after side, so its writes would make the two sides differ
#: for a reason that has nothing to do with the product.
COLLECTOR_PHASE = "frames"

#: The gate verdicts the pool export produces (``dbexport.build_gates``).
DB_GATES = ("G-2", "G-3", "G-4", "G-6")


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def _read_jsonl(path):
    return load_events(path)


def _evidence_ref(path, base):
    try:
        return str(Path(path).resolve().relative_to(Path(base).resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def build_report(evidence_dir, out_dir=None, purpose="walkthrough"):
    """Build the verdict report from the evidence on disk.

    Every gate that has no evidence is reported as BLOCKED ("cannot be
    judged"), never as PASS.  The overall verdict therefore only becomes
    PASS / PASS_WITH_PENDING when the evidence for the blocking gates is
    actually present.

    ``purpose`` marks what the report is for.  ``"selfcheck"`` means the two
    sides are the same run (a pipeline check); the report then carries a
    banner so nobody can mistake it for an acceptance result.
    """
    evidence_dir = Path(evidence_dir)
    out_dir = Path(out_dir) if out_dir else evidence_dir / "diff"
    out_dir.mkdir(parents=True, exist_ok=True)

    gates = {}
    shots = {}
    motion = {}
    checklist = {}

    # ── G-1: request sequence (§2.6) ────────────────────────────────────
    before_events = _read_jsonl(evidence_dir / "before" / "requests.jsonl")
    after_events = _read_jsonl(evidence_dir / "after" / "requests.jsonl")
    # The motion frames drive a real paper run; they only run on the after
    # side, so their writes are tagged with their own phase and left out
    # of the request-sequence diff (otherwise the two sides would differ
    # by the collector's own writes).
    before_events = [e for e in before_events if e.get("phase") != COLLECTOR_PHASE]
    after_events = [e for e in after_events if e.get("phase") != COLLECTOR_PHASE]
    if before_events and after_events:
        diff = diff_sequences(before_events, after_events)
        (out_dir / "requests.diff.json").write_text(
            json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "requests.diff.md").write_text(
            render_requests_diff_md(diff), encoding="utf-8")
        verdict = requests_diff_verdict(diff)
        detail = (f"写请求 {diff['before_count']} vs {diff['after_count']} 条；"
                  f"新增 {len(diff['added'])} / 删除 {len(diff['removed'])} / "
                  f"改动 {len(diff['changed'])}")
        gates["G-1"] = {
            "verdict": verdict,
            "auto": True,
            "detail": detail,
            "evidence": ["diff/requests.diff.json", "diff/requests.diff.md"],
            "l2_read_diff": {
                "added": [signature_text(s) for s in diff["read_added"]],
                "removed": [signature_text(s) for s in diff["read_removed"]],
                "note": "GET 差异属 L2 层，需人工签字，不自动判 FAIL（§2.4(e)）",
            },
        }
    else:
        gates["G-1"] = {
            "verdict": BLOCKED,
            "auto": True,
            "detail": "缺少 before/after 两侧的 requests.jsonl，无法判定",
            "evidence": [],
        }

    # ── G-5: graph page untouched (ae == 0, §5.7) ───────────────────────
    ae = _read_json(out_dir / "g5" / "ae.json")
    if ae and ae.get("scopes"):
        gates["G-5"] = _g5_verdict(ae, out_dir)
    else:
        gates["G-5"] = {
            "verdict": BLOCKED,
            "auto": True,
            "detail": ("G-5 需要 graph-isolation.md §6.3–§6.8 的九步冻结协议采集，"
                       "本交付未包含该采集器；且比对口径 R-1/R-2/R-3 尚未裁决（W-15）"),
            "evidence": [],
        }

    # -- G-2 / G-3 / G-4 / G-6: the pool export diff ---------------------
    db_diff = _read_json(out_dir / "db.diff.json")
    if db_diff and db_diff.get("gates"):
        for gate in DB_GATES:
            found = db_diff["gates"].get(gate)
            if not found:
                gates[gate] = {
                    "verdict": BLOCKED,
                    "auto": True,
                    "detail": f"the pool export did not produce {gate}",
                    "evidence": [],
                }
                continue
            gates[gate] = {
                "verdict": found.get("verdict", BLOCKED),
                "auto": True,
                "detail": _db_gate_detail(gate, found),
                "evidence": ["diff/db.diff.json"],
            }
    else:
        for gate in DB_GATES:
            gates[gate] = {
                "verdict": BLOCKED,
                "auto": True,
                "detail": GATES_WITHOUT_COLLECTOR[gate],
                "evidence": [],
            }

    # -- G-7 / G-8: the browser probes -----------------------------------
    checklist_diff = _read_json(out_dir / "checklist.json")
    gate_probes = (checklist_diff or {}).get("gates") or {}
    for gate in ("G-7", "G-8"):
        found = gate_probes.get(gate)
        if not found:
            side_file = _read_json(evidence_dir / "after" / "probe" / f"{gate.lower()}.json")
            found = side_file
        if not found:
            gates[gate] = {
                "verdict": BLOCKED,
                "auto": True,
                "detail": GATES_WITHOUT_COLLECTOR[gate],
                "evidence": [],
            }
            continue
        gates[gate] = {
            "verdict": found.get("verdict", BLOCKED),
            "auto": True,
            "detail": found.get("note", ""),
            "evidence": [f"probe/{gate.lower()}.json"],
        }

    # ── S-1…S-12: paired screenshots (§5.4) ────────────────────────────
    shot_dir = out_dir / "shots"
    if shot_dir.is_dir():
        for path in sorted(shot_dir.glob("*.json")):
            data = _read_json(path)
            if not data or "id" not in data:
                continue
            shots[data["id"]] = {
                "verdict": data.get("verdict", BLOCKED),
                "diff_ratio": data.get("ratio"),
                "diff_ae": data.get("ae"),
                "pair": data.get("pair"),
                "detail": data.get("detail", ""),
                "evidence": [f"diff/shots/{path.name}"],
            }

    # ── M-1…M-10: key frames (§6) ───────────────────────────────────────
    frames_dir = out_dir / "frames"
    if frames_dir.is_dir():
        for path in sorted(frames_dir.glob("*.json")):
            data = _read_json(path)
            if not data or "id" not in data:
                continue
            motion[data["id"]] = {
                "verdict": data.get("verdict", PENDING),
                "detail": data.get("detail", ""),
                "evidence": [f"diff/frames/{path.name}"],
            }

    # ── §3 interaction checklist (38 items, §7.5) ───────────────────────
    # The merged checklist of the diff pass wins: it carries the verdicts
    # of the comparative items (3.1-5) and the before side's verdicts.
    checklist_file = _read_json(out_dir / "checklist.json")
    if not (checklist_file and checklist_file.get("results")):
        checklist_file = _read_json(evidence_dir / "after" / "probe" / "checklist.json")
    if checklist_file and checklist_file.get("results"):
        for item in checklist_file["results"]:
            checklist[item["id"]] = {
                "verdict": item.get("verdict", PENDING),
                "auto": item.get("auto", False),
                "data": item.get("data", {}),
                "evidence": [f"probe/{item['id']}.json"],
            }
    else:
        checklist["*"] = {
            "verdict": BLOCKED,
            "auto": False,
            "detail": "浏览器探针（§7.5.2）尚未实现，38 条交互清单未采集",
            "evidence": [],
        }

    summary = _summarize(gates, shots, motion, checklist)
    report = {
        "schema_version": 1,
        "generated_at": _now(),
        "purpose": purpose,
        "evidence_dir": str(evidence_dir),
        "gates": gates,
        "shots": shots,
        "motion": motion,
        "checklist": checklist,
        "summary": summary,
        "unresolved": _unresolved(gates, shots, motion, checklist),
    }
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(
        render_report_md(report, out_dir), encoding="utf-8")
    return report


def _db_gate_detail(gate, found):
    """One line per gate: what was compared and what came out."""
    if gate == "G-2":
        tables = found.get("tables", {})
        return ("持久化写入比对：" + "、".join(
            f"{table} {verdict}" for table, verdict in tables.items()))
    if gate == "G-3":
        tables = found.get("tables", {})
        return ("学习投影比对：" + "、".join(
            f"{table} {verdict}" for table, verdict in tables.items()))
    if gate == "G-4":
        due = found.get("due", {}).get("verdict")
        weak = found.get("weak", {}).get("verdict")
        return f"到期列表 {due}；薄弱列表 {weak}"
    schema = found.get("schema", {}).get("verdict")
    counts = found.get("row_counts", {}).get("verdict")
    return f"schema 比对 {schema}；行数比对 {counts}"


def _g5_verdict(ae, out_dir):
    """§5.7 / §7.6.2: the graph gate is a negative assertion — ae == 0.

    Three comparison scopes (R-1 / R-2 / R-3) are all run and listed side by
    side; the executor does not pick one (R-32).  PENDING appears only when
    the scopes disagree about the outcome.
    """
    scopes = ae["scopes"]
    values = {name: scope.get("ae") for name, scope in scopes.items()}
    present = [v for v in values.values() if v is not None]
    if not present:
        return {"verdict": BLOCKED, "auto": True,
                "detail": "三口径 AE 未采全", "evidence": ["diff/g5/ae.json"]}
    if all(v == 0 for v in present):
        verdict = PASS
        detail = "三口径 ae 均为 0；本变更未误伤图谱"
    elif all(v > 0 for v in present):
        verdict = FAIL
        detail = "三口径 ae 均大于 0；本变更确实误伤了图谱"
    else:
        verdict = PENDING
        detail = ("口径之间结论不一致（R-1/R-2/R-3 待所有者裁决）；"
                  "无论选哪条口径，目标都是 ae = 0")
    return {
        "verdict": verdict,
        "auto": True,
        "detail": detail,
        "evidence": ["diff/g5/ae.json"],
        "scopes": scopes,
    }


def _summarize(gates, shots, motion, checklist):
    def split(bucket):
        return (
            sorted(k for k, v in bucket.items() if v["verdict"] == FAIL),
            sorted(k for k, v in bucket.items() if v["verdict"] == PENDING),
            sorted(k for k, v in bucket.items() if v["verdict"] == BLOCKED),
        )

    gates_failed, gates_pending, gates_blocked = split(gates)
    shots_failed, shots_pending, shots_blocked = split(shots)
    motion_failed, motion_pending, motion_blocked = split(motion)
    cl_failed, cl_pending, cl_blocked = split(checklist)

    if gates_failed or shots_failed or motion_failed or cl_failed:
        overall = "FAIL"
    elif gates_blocked or cl_blocked:
        overall = "INCOMPLETE"
    elif gates_pending or shots_pending or motion_pending or cl_pending:
        overall = "PASS_WITH_PENDING"
    else:
        overall = "PASS"

    return {
        "overall": overall,
        "gates_failed": gates_failed,
        "gates_pending": gates_pending,
        "gates_blocked": gates_blocked,
        "shots_failed": shots_failed,
        "shots_pending": shots_pending,
        "shots_blocked": shots_blocked,
        "motion_failed": motion_failed,
        "motion_pending": motion_pending,
        "motion_blocked": motion_blocked,
        "checklist_failed": cl_failed,
        "checklist_pending": len(cl_pending),
        "checklist_blocked": cl_blocked,
        "checklist_passed": sum(1 for v in checklist.values() if v["verdict"] == PASS),
    }


def _unresolved(gates, shots, motion, checklist):
    """Every non-PASS item, with the four elements §7.6.4 asks for."""
    items = []
    for bucket, label in ((gates, "G"), (shots, "S"), (motion, "M")):
        for key, value in sorted(bucket.items()):
            if value["verdict"] == PASS:
                continue
            items.append({
                "id": key,
                "verdict": value["verdict"],
                "phenomenon": value.get("detail", ""),
                "impact": "该项未取得可判定证据",
                "repro": "python tools/walkthrough/launch.py --help",
                "suggestion": "补齐对应采集器后重跑",
            })
    for key, value in sorted(checklist.items()):
        if value["verdict"] == PASS:
            continue
        items.append({
            "id": key,
            "verdict": value["verdict"],
            "phenomenon": value.get("detail", ""),
            "impact": "交互清单未采集或未判定",
            "repro": "python tools/walkthrough/launch.py --help",
            "suggestion": "跑浏览器探针后重跑",
        })
    return items


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def render_requests_diff_md(diff):
    """Human-readable unified diff of the two request sequences (§2.6)."""
    lines = ["# 请求序列 diff（G-1）", ""]
    lines.append(f"- before 写请求：{diff['before_count']} 条")
    lines.append(f"- after 写请求：{diff['after_count']} 条")
    lines.append("")
    for title, items in (("新增 added", diff["added"]),
                         ("删除 removed", diff["removed"])):
        lines.append(f"## {title}")
        if not items:
            lines.append("")
            lines.append("（无）")
        else:
            lines.append("")
            for item in items:
                lines.append(f"- `{signature_text(item)}`")
        lines.append("")
    lines.append("## 改动 changed")
    if not diff["changed"]:
        lines.append("")
        lines.append("（无）")
    else:
        lines.append("")
        for item in diff["changed"]:
            lines.append(f"- **{item['kind']}**")
            lines.append(f"  - before: `{signature_text(item['before'])}`")
            lines.append(f"  - after : `{signature_text(item['after'])}`")
    lines.append("")
    lines.append("## L2：GET 差异（需人工签字，不自动判 FAIL）")
    lines.append("")
    if not diff["read_added"] and not diff["read_removed"]:
        lines.append("（无）")
    else:
        for item in diff["read_added"]:
            lines.append(f"- after 多发：`{signature_text(item)}`")
        for item in diff["read_removed"]:
            lines.append(f"- after 少发：`{signature_text(item)}`")
    lines.append("")
    return "\n".join(lines)


def render_report_md(report, out_dir):
    """The human-readable report (§7.1)."""
    summary = report["summary"]
    lines = ["# 走查验收报告 — workbench-visual-language-v2", ""]
    if report.get("purpose") == "selfcheck":
        lines.append("> ⚠️ **自检报告**：两侧证据来自**同一次运行**（流程自检），"
                     "**不是**改造前/改造后对照，**不得**当作验收结论。")
        lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| 结论 | **{summary['overall']}** |")
    lines.append(f"| 生成时间 | {report['generated_at']} |")
    lines.append(f"| 证据目录 | `{report['evidence_dir']}` |")
    lines.append("")
    lines.append("## 0. 底线守卫")
    lines.append("")
    lines.append("| # | 检查项 | 结论 | 证据 | 说明 |")
    lines.append("|---|---|---|---|---|")
    for gate, value in sorted(report["gates"].items()):
        lines.append(f"| {gate} | — | {_mark(value['verdict'])} | "
                     f"{', '.join(value['evidence']) or '—'} | {value.get('detail', '')} |")
    lines.append("")
    lines.append("## 1. 对照截图")
    lines.append("")
    if report["shots"]:
        lines.append("| # | 结论 | 差异率 | 差异像素 | 证据 |")
        lines.append("|---|---|---|---|---|")
        for key, value in sorted(report["shots"].items()):
            ratio = value.get("diff_ratio")
            lines.append(f"| {key} | {_mark(value['verdict'])} | "
                         f"{ratio if ratio is not None else '—'} | "
                         f"{value.get('diff_ae', '—')} | "
                         f"{', '.join(value['evidence']) or '—'} |")
    else:
        lines.append("（未采集）")
    lines.append("")
    lines.append("## 2. 关键帧序列")
    lines.append("")
    if report["motion"]:
        lines.append("| # | 结论 | 证据 | 说明 |")
        lines.append("|---|---|---|---|")
        for key, value in sorted(report["motion"].items()):
            lines.append(f"| {key} | {_mark(value['verdict'])} | "
                         f"{', '.join(value['evidence']) or '—'} | {value.get('detail', '')} |")
    else:
        lines.append("（未采集）")
    lines.append("")
    lines.append("## 3. 交互清单")
    lines.append("")
    if report["checklist"]:
        lines.append("| # | 结论 | 等级 | 证据 |")
        lines.append("|---|---|---|---|")
        for key, value in sorted(report["checklist"].items()):
            lines.append(f"| {key} | {_mark(value['verdict'])} | "
                         f"{'AUTO' if value.get('auto') else '—'} | "
                         f"{', '.join(value['evidence']) or '—'} |")
    else:
        lines.append("（未采集）")
    lines.append("")
    lines.append("## 4. 未过项清单")
    lines.append("")
    if report["unresolved"]:
        lines.append("| # | 结论 | 现象 | 影响 | 复现命令 | 建议 |")
        lines.append("|---|---|---|---|---|---|")
        for item in report["unresolved"]:
            lines.append(f"| {item['id']} | {_mark(item['verdict'])} | "
                         f"{item['phenomenon']} | {item['impact']} | "
                         f"`{item['repro']}` | {item['suggestion']} |")
    else:
        lines.append("（无）")
    lines.append("")
    return "\n".join(lines)


def _mark(verdict):
    return {
        PASS: "✅ PASS",
        FAIL: "❌ FAIL",
        PENDING: "⬜ PENDING",
        BLOCKED: "⬜ BLOCKED",
        NA: "⬜ N/A",
    }.get(verdict, verdict)


def main(argv=None):
    """``python tools/walkthrough/recorder.py --evidence <dir>`` — build the
    report from evidence that is already on disk."""
    parser = argparse.ArgumentParser(
        description="Build the walkthrough verdict report from evidence on disk.")
    parser.add_argument("--evidence", required=True,
                        help="evidence directory (holds before/ and after/)")
    parser.add_argument("--out", default=None,
                        help="output directory (default: <evidence>/diff)")
    parser.add_argument("--purpose", default="walkthrough",
                        choices=("walkthrough", "selfcheck"),
                        help="'selfcheck' marks a pipeline check (both sides are the same run)")
    args = parser.parse_args(argv)
    report = build_report(args.evidence, args.out, args.purpose)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
