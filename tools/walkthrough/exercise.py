"""Scripted exercise driver — the request-sequence source for G-1.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §3 (the scripted exercise) and ``acceptance.md`` §0
G-1.

What this module does
---------------------
It drives the **real UI** with a browser, so the requests recorded by
``recorder.py`` are the ones a learner would cause.  §3.1 is explicit: an
HTTP-direct script would make G-1 an empty check, because the request
sequence would be whatever the script hard-coded rather than what the page
sends.  Every wait in here is therefore a wait for the **server-side
record** (``GET /__walkthrough__/events``), never for a browser event
(§3.5).

The step table is §3.2's, applied to the saved-Paper flow:

======  ==========================================  ==============================
step    UI action                                   expected server request
======  ==========================================  ==============================
seed    ``POST /api/w/{name}/practice-sets``        建卷（浏览器无入口，§3.3）
E0      open ``/w/{name}/practice?paper=<id>``     ``GET  .../practice/current``
E1      click ``#paper-start``                      ``POST .../practice-sets/{id}/start``
E2      answer each item                            ``POST .../attempts``
E3      self-rate each item                         ``POST .../feedback``
E4      type into the text item                     ``POST .../practice/draft``
E5      click ``#paper-next``                       ``POST .../practice/current/navigate``
E7      click ``#paper-final-submit``               ``POST .../practice/current/submit``
E8      completion page loads the run               ``GET  .../practice/runs/{id}``
E9      ``#paper-completion`` visible               （无写请求）
======  ==========================================  ==============================

The 建卷 request is recorded under phase ``seed`` and the practice itself
under phase ``measure``; §3.3 wants them in separate diff tables, because
建卷 has no browser path and therefore no regression-detection power.

Red lines (§8.3): this module only *drives* a browser and *reads* the
service.  It never writes the pool, never changes a request, and never
touches product code.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shots import CONSISTENCY, VIEWPORTS  # noqa: E402  (path set up above)

#: The seed paper.  §3.4 pins the item list so both sides drive the same
#: items; the paper id itself is normalised away by the recorder
#: (``ps-NNN`` -> ``{id}``), so only the *content* has to match.
SEED_TITLE = "走查种子卷"
SEED_PROBLEM_IDS = (
    "dmath-ch06-mq-010",    # single choice → POST /attempts with verdict
    "dmath-ch06-prob-001",  # text item     → POST /practice/draft
    "dmath-ch06-mq-001",    # yes/no        → POST /attempts with verdict
)

#: Item kinds, in the same order as ``SEED_PROBLEM_IDS``.
ITEM_KINDS = ("choice", "text", "yesno")

#: Deterministic answers.  The verdict of a graded item is part of the
#: request payload whitelist, so the same option must be picked on both sides.
TEXT_ANSWER = "42"
RADIO_OPTION_INDEX = 0
RATING_VALUE = "4"

#: The routes this driver expects, in order.  The recorder's ``route`` field
#: is the service's own route template prefixed with the method, so these
#: strings are exactly what lands in ``requests.jsonl``.  Used to assert that
#: the run really produced the §3.2 sequence (and that both sides produce it).
ROUTE_PAPER_CREATE = "POST /api/w/{name}/practice-sets"
ROUTE_PAPER_START = "POST /api/w/{name}/practice-sets/{practice_set_id}/start"
ROUTE_ATTEMPT = "POST /api/w/{name}/attempts"
ROUTE_FEEDBACK = "POST /api/w/{name}/feedback"
ROUTE_DRAFT = "POST /api/w/{name}/practice/draft"
ROUTE_NAVIGATE = "POST /api/w/{name}/practice/current/navigate"
ROUTE_SUBMIT = "POST /api/w/{name}/practice/current/submit"
ROUTE_CURRENT = "GET /api/w/{name}/practice/current"
ROUTE_RUN = "GET /api/w/{name}/practice/runs/{run_id}"

#: 建卷 has no browser entry, so its request is recorded under the ``seed``
#: phase and diffed as its own group (§3.3).
EXPECTED_SEED_WRITES = (ROUTE_PAPER_CREATE,)

#: The practice itself, in the order the UI produces it.  Per item: the
#: answer (a radio auto-submits in ``per_item`` mode), then the self-rating,
#: then the move to the next item.  The text item adds one draft write
#: (its ``input`` event queues a draft, §3.4's 350 ms debounce).
EXPECTED_MEASURE_WRITES = (
    ROUTE_PAPER_START,
    ROUTE_ATTEMPT,      # item 1 — single choice
    ROUTE_FEEDBACK,
    ROUTE_NAVIGATE,
    ROUTE_DRAFT,        # item 2 — text
    ROUTE_ATTEMPT,
    ROUTE_FEEDBACK,
    ROUTE_NAVIGATE,
    ROUTE_ATTEMPT,      # item 3 — yes/no
    ROUTE_FEEDBACK,
    ROUTE_SUBMIT,
)

EXPECTED_WRITES = EXPECTED_SEED_WRITES + EXPECTED_MEASURE_WRITES


class ExerciseError(RuntimeError):
    """Raised when the scripted exercise cannot complete as specified."""


# ─────────────────────────────────────────────────────────────────────────
# service access (read-only observation of the recorded request stream)
# ─────────────────────────────────────────────────────────────────────────


class Service:
    """A thin client for the running service and its recorder endpoints."""

    def __init__(self, base_url, timeout=30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path):
        import urllib.error
        import urllib.request

        url = self.base_url + path
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ExerciseError(f"{url} → HTTP {exc.code}") from exc
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise ExerciseError(f"{url} → {exc}") from exc

    def _post(self, path, payload):
        import urllib.error
        import urllib.request

        url = self.base_url + path
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise ExerciseError(f"{url} → HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise ExerciseError(f"{url} → {exc}") from exc

    # -- recorder control surface (not recorded as product traffic) ------
    def set_phase(self, phase, group="exercise"):
        self._post("/__walkthrough__/phase", {"phase": phase, "group": group})

    def events(self):
        return self._get("/__walkthrough__/events").get("events", [])

    # -- product API (used only for 建卷, which has no browser entry) ----
    def create_paper(self, ws, title, problem_ids):
        return self._post(f"/api/w/{ws}/practice-sets",
                          {"title": title, "problem_ids": list(problem_ids)})

    def fetch_due(self, ws):
        return self._get(f"/api/w/{ws}/due")

    def fetch_weak(self, ws):
        return self._get(f"/api/w/{ws}/weak")


class Waiter:
    """Waits for a request to show up in the **server-side** record (§3.5).

    The recorder hands out a monotonic ``seq`` when a request *arrives* and
    appends it to the JSONL when the response is *finished*, so the file
    order is not the arrival order.  Tracking is therefore done on ``seq``,
    never on the list index.
    """

    def __init__(self, service):
        self.service = service
        self.start_seq = 0
        self.cursor = 0

    def snapshot(self):
        events = self.service.events()
        self.start_seq = max((event.get("seq", 0) for event in events), default=0)
        self.cursor = self.start_seq
        return events

    def wait_for(self, route, timeout=30.0):
        """Block until a matching request is recorded; return the event.

        ``route`` is the recorder's own route string, i.e. the service's
        route template prefixed with the method (``POST /api/w/{name}/attempts``).
        """
        deadline = time.monotonic() + timeout
        while True:
            events = self.service.events()
            matches = sorted(
                (event for event in events
                 if event.get("seq", 0) > self.cursor and event.get("route") == route),
                key=lambda event: event.get("seq", 0))
            if matches:
                self.cursor = matches[0].get("seq", self.cursor)
                return matches[0]
            if time.monotonic() > deadline:
                pending = sorted((event.get("route") for event in events
                                  if event.get("seq", 0) > self.cursor),
                                 key=str)
                raise ExerciseError(
                    f"timed out after {timeout:.0f}s waiting for {route}; "
                    f"recorded since the wait started: {pending}")
            time.sleep(0.05)

    def writes_since_start(self, phase=None):
        """The write requests this run produced, in arrival order.

        ``phase`` filters by the recorder's phase tag, so the 建卷 request
        (phase ``seed``) and the practice itself (phase ``measure``) land in
        separate groups (§3.3).
        """
        events = sorted(
            (event for event in self.service.events()
             if event.get("seq", 0) > self.start_seq),
            key=lambda event: event.get("seq", 0))
        return [event.get("route") for event in events
                if event.get("method") in {"POST", "PATCH", "PUT", "DELETE"}
                and event.get("raw_path", "").startswith("/api/")
                and (phase is None or event.get("phase") == phase)]


# ─────────────────────────────────────────────────────────────────────────
# the exercise
# ─────────────────────────────────────────────────────────────────────────


def seed_paper(service, ws):
    """建卷 — the browser has no entry for it, so it goes through the API
    (§3.3).  Both sides run it with identical parameters."""
    service.set_phase("seed", group="paper")
    result = service.create_paper(ws, SEED_TITLE, SEED_PROBLEM_IDS)
    paper_id = result.get("practice_set_id")
    if not paper_id:
        raise ExerciseError(f"建卷 returned no practice_set_id: {result}")
    return paper_id


def _wait_enabled(page, selector, timeout=15000):
    page.wait_for_selector(selector, state="attached", timeout=timeout)
    page.wait_for_function(
        """(sel) => {
             const el = document.querySelector(sel);
             return !!el && !el.disabled && el.offsetParent !== null;
           }""",
        arg=selector, timeout=timeout)


def settle_animations(page, timeout=3000):
    """Wait until no finite animation is running (§5.2's animation gate)."""
    try:
        page.wait_for_function(
            """() => {
                 const anims = document.getAnimations ? document.getAnimations() : [];
                 return anims.every((a) => {
                   const timing = a.effect && a.effect.getTiming ? a.effect.getTiming() : {};
                   if (timing.iterations === Infinity) return true;
                   return a.playState !== 'running';
                 });
               }""",
            timeout=timeout)
    except Exception:
        # A still-running animation is recorded in the shot metadata; the
        # comparison stays valid because both sides take the same shot.
        pass


def run_exercise(base_url, ws, out_dir, paper_id=None):
    """Drive E0…E9 and return the run summary."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    exercise_dir = out_dir / "exercise"
    exercise_dir.mkdir(parents=True, exist_ok=True)

    service = Service(base_url)
    waiter = Waiter(service)
    # The snapshot goes first so the 建卷 request (phase ``seed``) is part of
    # this run's record; the practice itself is tagged ``measure`` (§3.3).
    waiter.snapshot()

    if paper_id is None:
        paper_id = seed_paper(service, ws)
    service.set_phase("measure", group="exercise")

    steps = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=list(CONSISTENCY["browser_args"]))
        context = browser.new_context(
            viewport={"width": VIEWPORTS["V1440"]["width"],
                      "height": VIEWPORTS["V1440"]["height"]},
            device_scale_factor=VIEWPORTS["V1440"]["device_scale_factor"],
            color_scheme=CONSISTENCY["color_scheme"],
            reduced_motion=CONSISTENCY["reduced_motion"],
            locale=CONSISTENCY["locale"],
            timezone_id=CONSISTENCY["timezone_id"])
        page = context.new_page()
        try:
            # E0 ── open the practice page with the seeded paper.
            page.goto(f"{base_url}/w/{ws}/practice?paper={paper_id}",
                      wait_until="load", timeout=30000)
            waiter.wait_for(ROUTE_CURRENT)
            steps.append({"step": "E0", "url": page.url})

            # E1 ── start the run.
            _wait_enabled(page, "#paper-start")
            page.click("#paper-start")
            waiter.wait_for(ROUTE_PAPER_START)
            steps.append({"step": "E1"})

            # E2/E3/E4/E5 ── one turn per item, in the seed paper's order.
            for index, kind in enumerate(ITEM_KINDS):
                if kind == "text":
                    # E4 first: typing is what produces the draft request.
                    page.wait_for_selector("#paper-answer", state="visible", timeout=15000)
                    page.fill("#paper-answer", TEXT_ANSWER)
                    waiter.wait_for(ROUTE_DRAFT)
                    steps.append({"step": "E4", "item": index})
                    page.click("#paper-item-submit")
                else:
                    page.wait_for_selector("#paper-options input", state="visible", timeout=15000)
                    options = page.query_selector_all("#paper-options input")
                    if not options:
                        raise ExerciseError(f"item {index} rendered no options")
                    options[RADIO_OPTION_INDEX].click()
                waiter.wait_for(ROUTE_ATTEMPT)
                steps.append({"step": "E2", "item": index, "kind": kind})

                # The S-3 shot is taken on the first answered item, while the
                # run is still in progress (§5.6 S-3).
                if index == 0:
                    capture_in_progress(page, out_dir)

                # E3 ── self-rate the item.
                page.wait_for_selector("#paper-rating", state="visible", timeout=15000)
                page.fill("#paper-rating input[type='number']", RATING_VALUE)
                page.click("#paper-rating button")
                waiter.wait_for(ROUTE_FEEDBACK)
                steps.append({"step": "E3", "item": index})

                # E5 ── move to the next item (not after the last one).
                if index + 1 < len(ITEM_KINDS):
                    page.click("#paper-next")
                    waiter.wait_for(ROUTE_NAVIGATE)
                    steps.append({"step": "E5", "item": index})

            # E7 ── submit the paper.
            page.click("#paper-final-submit")
            waiter.wait_for(ROUTE_SUBMIT)
            steps.append({"step": "E7"})

            # E8/E9 ── the completion page fetches the run it just created.
            waiter.wait_for(ROUTE_RUN)
            page.wait_for_selector("#paper-completion", state="visible", timeout=20000)
            steps.append({"step": "E9", "paper_id": paper_id})
        finally:
            context.close()
            browser.close()

    # The verify phase is where the learning projection is read (§3.6).
    service.set_phase("verify", group="verify")
    due = service.fetch_due(ws)
    weak = service.fetch_weak(ws)
    (exercise_dir / "due.json").write_text(
        json.dumps(due, ensure_ascii=False, indent=2), encoding="utf-8")
    (exercise_dir / "weak.json").write_text(
        json.dumps(weak, ensure_ascii=False, indent=2), encoding="utf-8")

    measure_writes = waiter.writes_since_start(phase="measure")
    seed_writes = waiter.writes_since_start(phase="seed")
    summary = {
        "paper_id": paper_id,
        "steps": steps,
        "expected_seed_writes": list(EXPECTED_SEED_WRITES),
        "expected_measure_writes": list(EXPECTED_MEASURE_WRITES),
        "observed_seed_writes": seed_writes,
        "observed_measure_writes": measure_writes,
        "seed_sequence_matches": seed_writes == list(EXPECTED_SEED_WRITES),
        "measure_sequence_matches": measure_writes == list(EXPECTED_MEASURE_WRITES),
    }
    (exercise_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def capture_in_progress(page, out_dir):
    """S-3 — the practice page while a run is in progress."""
    shots_dir = Path(out_dir) / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    settle_animations(page)
    target = shots_dir / "S-3-practice-in-progress.png"
    page.screenshot(path=str(target), animations="disabled", caret="hide", scale="css")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Drive the scripted practice exercise against a running service.")
    parser.add_argument("--base-url", required=True,
                        help="e.g. http://127.0.0.1:3191")
    parser.add_argument("--ws", required=True, help="workspace name inside the service")
    parser.add_argument("--out", required=True,
                        help="evidence directory of this side (e.g. <scratch>/evidence/after)")
    parser.add_argument("--paper-id", default=None,
                        help="use an existing paper instead of 建卷 (idempotent re-runs)")
    args = parser.parse_args(argv)

    summary = run_exercise(args.base_url, args.ws, args.out, args.paper_id)
    print(json.dumps({
        "paper_id": summary["paper_id"],
        "steps": len(summary["steps"]),
        "observed_seed_writes": len(summary["observed_seed_writes"]),
        "observed_measure_writes": len(summary["observed_measure_writes"]),
        "seed_sequence_matches": summary["seed_sequence_matches"],
        "measure_sequence_matches": summary["measure_sequence_matches"],
    }, ensure_ascii=False, indent=2))
    return 0 if (summary["seed_sequence_matches"]
                  and summary["measure_sequence_matches"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
