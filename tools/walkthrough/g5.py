"""G-5 — the graph page must not be damaged by the change.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
graph-isolation.md`` §6.3–§6.8 (the nine-step freeze protocol, the wait
predicates, the comparison and the three scopes) and
``acceptance.md`` §0 G-5 (a negative assertion: the difference must be 0).

The two settled calibres
------------------------
**A-49 — the baseline is a git worktree.**  The "before" side is the commit
``cf9d596d`` (the parent of the branch's first product commit
``16d3ff89``), checked out with ``git worktree``.  The screenshots under
``tmp/frontend-audit/`` are **not** used: their viewport and device pixel
ratio are not controlled, so they are not admitted into the pixel
judgement.

**A-48 / A-65 — the three scopes run side by side.**  G-5 is judged as
R-2 + R-3, and R-1 becomes "identical except the left column and the top
bar":

``R-1``
    the whole page, **excluding** the left column (``x < 280``) and the top
    bar (``y < 52``); the difference pixels have to be 0.
``R-2``
    the crop rectangle of ``.graph-workspace``; pixel-identical, **no mask**.
``R-3``
    the canvas rectangle plus one pure-colour sample per column.  The left
    sample is fixed **inside the left column's paper area (top)**, where the
    ground is ``--surface-sunken`` on both sides, so "the shell ground did
    not change" can be shown honestly.  **The sample coordinates are written
    into the artefact** and the before side is sampled at exactly those
    coordinates, so they cannot drift with the content.

The report has to say, in as many words:

    左栏纸面以下的底色由 ``--surface-sunken`` 变为 ``--surface-base``
    —— 属 15.3 的既定改造，非图谱误伤

and that note must **not** turn R-3 into a FAIL: inside the paper the
sample is the same on both sides.

The verdict follows §7.6.2: all three scopes at 0 ⇒ PASS, all three above
0 ⇒ FAIL, a disagreement between the scopes ⇒ PENDING.  **PENDING is not a
pass.**
"""

import argparse
import json
import sys
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shots import CONSISTENCY, VIEWPORTS  # noqa: E402  (path set up above)

PASS, FAIL, PENDING = "PASS", "FAIL", "PENDING"

#: The region of R-1 that is excluded (A-48).
R1_EXCLUDE_LEFT = 280
R1_EXCLUDE_TOP = 52

#: The note the report has to carry (A-65).
LEFT_COLUMN_NOTE = ("左栏纸面以下的底色由 `--surface-sunken` 变为 `--surface-base`"
                    " —— 属 15.3 的既定改造，非图谱误伤")

#: The in-page helpers: the quiescence signature and the geometry.
GRAPH_JS = r"""
(() => {
  const G = {};
  G.signature = () => {
    const stage = document.getElementById("graph-stage");
    if (!stage) return "";
    const parts = [];
    stage.querySelectorAll(".node-wrap").forEach((w) => {
      const label = w.querySelector(".label");
      const meta = w.querySelector(".meta");
      parts.push([
        w.dataset.kpId,
        w.style.left, w.style.top,
        w.style.getPropertyValue("--size"),
        w.style.opacity,
        label ? label.style.opacity : "",
        meta ? meta.style.opacity : "",
      ].join("|"));
    });
    parts.push("stage:" + stage.style.transform);
    return parts.join(";");
  };
  G.solving = () => {
    const state = document.querySelector("#graph-solver-state");
    return !!(state && state.classList.contains("solving"));
  };
  G.assertions = () => {
    const canvas = document.getElementById("graph-canvas");
    const tide = document.getElementById("graph-tide");
    const layout = document.getElementById("layout");
    const left = document.getElementById("left-column");
    const right = document.getElementById("ai-column");
    const workspace = document.querySelector(".graph-workspace");
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top),
              Math.round(r.width), Math.round(r.height)];
    };
    /* The colours have to be compared as rgb, not as strings: the token
       is written as a hex, the computed style as rgb(). */
    const rgb = (value) => {
      const match = String(value || "").match(
        /rgba?\(([^)]+)\)/);
      if (match) {
        const parts = match[1].split(",").map((p) => parseFloat(p));
        return parts.length >= 3 ? parts.slice(0, 3).join(",") : null;
      }
      const hex = String(value || "").trim();
      if (/^#[0-9a-f]{6}$/i.test(hex)) {
        return [parseInt(hex.slice(1, 3), 16),
                parseInt(hex.slice(3, 5), 16),
                parseInt(hex.slice(5, 7), 16)].join(",");
      }
      if (/^#[0-9a-f]{3}$/i.test(hex)) {
        return [0, 1, 2].map((i) => parseInt(hex[1 + i] + hex[1 + i], 16))
          .join(",");
      }
      return null;
    };
    const paper = (container) => {
      /* The "paper" of a column: the biggest descendant whose ground is
         the sunken surface.  Its top area is where the sample goes. */
      if (!container) return null;
      const root = getComputedStyle(document.documentElement);
      const sunken = rgb(root.getPropertyValue("--surface-sunken"));
      let best = null;
      let fallback = null;
      container.querySelectorAll("*").forEach((el) => {
        const st = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        if (r.width < 40 || r.height < 40) return;
        const area = r.width * r.height;
        const colour = rgb(st.backgroundColor);
        if (!colour || st.backgroundColor === "rgba(0, 0, 0, 0)") {
          if (!fallback || area > fallback.area) {
            fallback = {el, area, rect: [r.left, r.top, r.width, r.height],
                        colour: st.backgroundColor};
          }
          return;
        }
        if (sunken && colour === sunken) {
          if (!best || area > best.area) {
            best = {el, area, rect: [r.left, r.top, r.width, r.height],
                    colour: st.backgroundColor};
          }
        } else if (!fallback || area > fallback.area) {
          fallback = {el, area, rect: [r.left, r.top, r.width, r.height],
                      colour: st.backgroundColor};
        }
      });
      const chosen = best || fallback;
      if (!chosen) return null;
      return {
        rect: [Math.round(chosen.rect[0]), Math.round(chosen.rect[1]),
               Math.round(chosen.rect[2]), Math.round(chosen.rect[3])],
        cls: String(chosen.el.className || "").slice(0, 80),
        colour: chosen.colour,
        sunkenToken: sunken,
        rule: best ? "surface-sunken" : "largest-opaque-ground",
      };
    };
    return {
      scrollX: window.scrollX,
      scrollY: window.scrollY,
      solving: G.solving(),
      rendererActive: !!(canvas && canvas.classList.contains("graph-renderer-active")),
      tideOpacity: tide ? getComputedStyle(tide).opacity : null,
      gridColumns: layout ? getComputedStyle(layout).gridTemplateColumns : null,
      workspace: rect(workspace),
      canvas: rect(canvas),
      left: rect(left),
      right: rect(right),
      leftPaper: paper(left),
      rightPaper: paper(right),
      viewport: [window.innerWidth, window.innerHeight],
      dpr: window.devicePixelRatio,
    };
  };
  G.hit = (x, y) => {
    const el = document.elementFromPoint(x, y);
    if (!el) return null;
    const st = getComputedStyle(el);
    return {
      tag: el.tagName.toLowerCase(),
      cls: String(el.className || "").slice(0, 80),
      id: el.id || "",
      background: st.backgroundColor,
    };
  };
  window.__lkGraph = G;
})();
"""


# ─────────────────────────────────────────────────────────────────────────
# the nine steps of §6.5
# ─────────────────────────────────────────────────────────────────────────


def capture_graph(base_url, ws, out_dir, side):
    """Take the graph screenshot of one side, following §6.5 step by step."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shot = out_dir / f"graph-{side}.png"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=list(CONSISTENCY["browser_args"]))
        # ① a fresh context: no localStorage, no cookies.
        context = browser.new_context(
            viewport={"width": VIEWPORTS["V1440"]["width"],
                      "height": VIEWPORTS["V1440"]["height"]},
            device_scale_factor=VIEWPORTS["V1440"]["device_scale_factor"],
            color_scheme=CONSISTENCY["color_scheme"],
            locale=CONSISTENCY["locale"],
            timezone_id=CONSISTENCY["timezone_id"])
        # ③ the reduced motion has to be set **before** the goto: it is the
        #    necessary condition for the graph to be reproducible at all.
        page = context.new_page()
        page.emulate_media(reduced_motion="reduce")
        page.add_init_script(GRAPH_JS)
        try:
            # ② the graph page.
            page.goto(f"{base_url}/w/{ws}/graph", wait_until="load",
                      timeout=60000)
            # ④ the fonts.
            page.evaluate("() => document.fonts.ready")
            # ⑤ no scroll.
            page.evaluate("() => window.scrollTo(0, 0)")
            # ⑥ the quiescence (the solver state plus a stable signature).
            signature = _wait_for_quiescence(page)
            # ⑦ the assertions.
            assertions = page.evaluate("() => window.__lkGraph.assertions()")
            # ⑧ the screenshot (a viewport screenshot, never fullPage).
            page.screenshot(path=str(shot), animations="disabled", caret="hide",
                            scale="css")
            # ⑨ the reproduction record.
            record = {
                "side": side,
                "shot": shot.name,
                "signature": signature,
                "assertions": assertions,
                "viewport": {"width": VIEWPORTS["V1440"]["width"],
                             "height": VIEWPORTS["V1440"]["height"],
                             "deviceScaleFactor": VIEWPORTS["V1440"]["device_scale_factor"]},
                "browser": browser.version,
                "baseUrl": base_url,
                "workspace": ws,
            }
        finally:
            context.close()
            browser.close()
    (out_dir / f"graph-{side}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def _wait_for_quiescence(page, samples=3, interval_ms=120, timeout_ms=30000):
    """§6.4 — the solver state is reset **and** the signature is stable."""
    import time

    deadline = time.monotonic() + timeout_ms / 1000.0
    last = None
    stable = 0
    while time.monotonic() < deadline:
        signature = page.evaluate("() => window.__lkGraph.signature()")
        solving = page.evaluate("() => window.__lkGraph.solving()")
        if not solving and signature and signature == last:
            stable += 1
            if stable >= samples:
                return signature
        else:
            stable = 0
        last = signature
        page.wait_for_timeout(interval_ms)
    raise RuntimeError("the graph page did not become quiescent in time")


# ─────────────────────────────────────────────────────────────────────────
# the three scopes
# ─────────────────────────────────────────────────────────────────────────


def _load(path):
    from PIL import Image

    return Image.open(path).convert("RGB")


def _diff_pixels(left, right, box=None, mask=None):
    """The number of differing pixels (AE) of two images.

    ``box`` is the crop rectangle (R-2) and ``mask`` a per-pixel mask
    (R-1's excluded areas).  The comparison is done on the raw pixels; no
    tolerance is applied, because the graph scope accepts no mask at all.
    """
    from PIL import ImageChops

    if box:
        left = left.crop(box)
        right = right.crop(box)
    if left.size != right.size:
        return None, {"reason": "the two screenshots have different sizes",
                      "before": list(left.size), "after": list(right.size)}
    diff = ImageChops.difference(left, right)
    bands = diff.split()
    total = 0
    per_band = []
    for band in bands:
        histogram = band.histogram()
        differing = sum(histogram[1:])
        total += differing
        per_band.append(differing)
    if mask is not None:
        # The masked pixels do not count.
        masked = 0
        pixels = diff.load()
        mask_pixels = mask.load()
        width, height = diff.size
        for y in range(height):
            for x in range(width):
                if mask_pixels[x, y]:
                    masked += 1
        total = max(0, total - masked)
    return total, {"perBand": per_band, "size": list(left.size)}


def _mask_for(size, exclude_left=0, exclude_top=0):
    """The mask of the excluded area of R-1 (the left column / the top bar)."""
    from PIL import Image

    width, height = size
    mask = Image.new("L", (width, height), 0)
    pixels = mask.load()
    for y in range(height):
        for x in range(width):
            if x < exclude_left or y < exclude_top:
                pixels[x, y] = 255
    return mask


def _sample(image, point):
    """The RGB of one pixel."""
    x, y = point
    if x < 0 or y < 0 or x >= image.width or y >= image.height:
        return None
    return list(image.getpixel((x, y)))


def build_scopes(before_dir, after_dir):
    """The three scopes of A-48 / A-65, side by side."""
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)
    before_png = before_dir / "graph-before.png"
    after_png = after_dir / "graph-after.png"
    before_json = _read_json(before_dir / "graph-before.json")
    after_json = _read_json(after_dir / "graph-after.json")
    if not (before_png.is_file() and after_png.is_file()):
        return {"error": "the two screenshots are missing"}

    before = _load(before_png)
    after = _load(after_png)

    # -- the sample points (fixed by the artefact, §A-65) -----------------
    # The coordinates come from the **after** side and are written into the
    # artefact; the before side is sampled at exactly the same coordinates.
    samples = []
    left_paper = (after_json or {}).get("assertions", {}).get("leftPaper")
    right_paper = (after_json or {}).get("assertions", {}).get("rightPaper")
    canvas_rect = (after_json or {}).get("assertions", {}).get("canvas")
    if left_paper:
        rect = left_paper["rect"]
        samples.append({"name": "left-column-paper",
                        "point": [rect[0] + 6, rect[1] + 6],
                        "why": "左栏纸面区域内（顶部）：改造前后都是 --surface-sunken"})
    if right_paper:
        rect = right_paper["rect"]
        samples.append({"name": "right-column-paper",
                        "point": [rect[0] + 6, rect[1] + 6],
                        "why": "右栏纸面区域（顶部）"})
    if canvas_rect:
        samples.append({"name": "canvas",
                        "point": [canvas_rect[0] + 6, canvas_rect[1] + 6],
                        "why": "画布矩形内（左上角）"})

    sample_rows = []
    for sample in samples:
        point = sample["point"]
        before_rgb = _sample(before, point)
        after_rgb = _sample(after, point)
        sample_rows.append({
            **sample,
            "before": before_rgb,
            "after": after_rgb,
            "equal": before_rgb == after_rgb,
        })

    # -- R-1: the whole page minus the left column and the top bar -------
    size = before.size
    mask = _mask_for(size, R1_EXCLUDE_LEFT, R1_EXCLUDE_TOP)
    r1_ae, r1_detail = _diff_pixels(before, after, mask=mask)

    # -- R-2: the crop rectangle of .graph-workspace ---------------------
    before_rect = (before_json or {}).get("assertions", {}).get("workspace")
    after_rect = (after_json or {}).get("assertions", {}).get("workspace")
    r2 = {"box": None, "ae": None, "detail": "the workspace rectangle is missing"}
    if before_rect and after_rect:
        if list(before_rect) == list(after_rect):
            box = (before_rect[0], before_rect[1],
                   before_rect[0] + before_rect[2], before_rect[1] + before_rect[3])
            ae, detail = _diff_pixels(before, after, box=box)
            r2 = {"box": list(box), "ae": ae, "detail": detail,
                  "mask": None}
        else:
            r2 = {"box": None, "ae": None,
                  "detail": "the two workspace rectangles differ — the crop "
                            "is not comparable",
                  "before": before_rect, "after": after_rect}

    # -- R-3: the canvas rectangle plus the three samples ----------------
    r3_box = None
    if canvas_rect:
        r3_box = (canvas_rect[0], canvas_rect[1],
                  canvas_rect[0] + canvas_rect[2], canvas_rect[1] + canvas_rect[3])
    canvas_ae, canvas_detail = (None, {})
    if r3_box and before_rect and after_rect:
        if list(before_rect) == list(after_rect):
            canvas_ae, canvas_detail = _diff_pixels(before, after, box=r3_box)
        else:
            canvas_detail = {"reason": "the workspace rectangles differ"}
    sample_equal = all(row["equal"] for row in sample_rows) if sample_rows else None
    r3 = {
        "canvasBox": list(r3_box) if r3_box else None,
        "canvasAe": canvas_ae,
        "canvasDetail": canvas_detail,
        "samples": sample_rows,
        "samplesEqual": sample_equal,
        "note": LEFT_COLUMN_NOTE,
    }

    return {
        "scopes": {
            "R-1": {"ae": r1_ae, "detail": r1_detail,
                    "excluded": {"leftColumnX": R1_EXCLUDE_LEFT,
                                 "topBarY": R1_EXCLUDE_TOP},
                    "mask": "the left column (x < 280) and the top bar (y < 52) "
                            "are excluded (A-48)"},
            "R-2": r2,
            "R-3": {**r3, "ae": r3.get("canvasAe")},
        },
        "meta": {
            "before": {"shot": str(before_png),
                       "assertions": (before_json or {}).get("assertions", {})},
            "after": {"shot": str(after_png),
                      "assertions": (after_json or {}).get("assertions", {})},
            "note": LEFT_COLUMN_NOTE,
        },
    }


def verdict(scopes):
    """§7.6.2 — the verdict of the three scopes.

    ``all == 0`` ⇒ PASS, ``all > 0`` ⇒ FAIL, a disagreement ⇒ PENDING.
    The left column's background change (A-65) must not turn R-3 into a
    FAIL: inside the paper the sample is the same on both sides.
    """
    if scopes.get("error"):
        return {"verdict": PENDING, "detail": scopes["error"], "scopes": scopes}
    parts = scopes.get("scopes", {})
    r1 = parts.get("R-1", {}).get("ae")
    r2 = parts.get("R-2", {}).get("ae")
    r3_ae = parts.get("R-3", {}).get("ae")
    samples_equal = parts.get("R-3", {}).get("samplesEqual")
    values = [value for value in (r1, r2, r3_ae) if value is not None]
    if not values:
        return {"verdict": PENDING, "detail": "the three scopes could not be "
                                              "measured", "scopes": scopes}
    if samples_equal is False:
        return {"verdict": FAIL,
                "detail": "the column samples differ — the shell ground moved",
                "scopes": scopes}
    if all(value == 0 for value in values):
        return {"verdict": PASS,
                "detail": "R-1 / R-2 / R-3 are all 0 — the graph was not damaged",
                "scopes": scopes}
    if all(value > 0 for value in values):
        return {"verdict": FAIL,
                "detail": "R-1 / R-2 / R-3 are all above 0 — the graph changed",
                "scopes": scopes}
    return {"verdict": PENDING,
            "detail": "the scopes disagree — the owner has to decide the "
                      "comparison scope",
            "scopes": scopes}


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="G-5: capture and compare the graph page.")
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture")
    capture.add_argument("--base-url", required=True)
    capture.add_argument("--ws", required=True)
    capture.add_argument("--out", required=True)
    capture.add_argument("--side", choices=("before", "after"), required=True)

    compare = sub.add_parser("compare")
    compare.add_argument("--before", required=True)
    compare.add_argument("--after", required=True)
    compare.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.command == "capture":
        record = capture_graph(args.base_url, args.ws, args.out, args.side)
        print(json.dumps({"side": args.side, "shot": record["shot"],
                          "assertions": record["assertions"]},
                         ensure_ascii=False, indent=2))
        return 0
    scopes = build_scopes(args.before, args.after)
    result = verdict(scopes)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ae.json").write_text(
        json.dumps({**result, **scopes}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    parts = scopes.get("scopes", {})
    print(json.dumps({"verdict": result["verdict"], "detail": result["detail"],
                      "R-1": parts.get("R-1", {}).get("ae"),
                      "R-2": parts.get("R-2", {}).get("ae"),
                      "R-3": parts.get("R-3", {}).get("ae"),
                      "samplesEqual": parts.get("R-3", {}).get("samplesEqual")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
