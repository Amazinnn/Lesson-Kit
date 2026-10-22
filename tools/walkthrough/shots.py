"""Screenshot collector for the workbench visual walkthrough.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §5 (paired screenshots) and §5.7 (the graph gate).

Two commands:

``capture``
    Take the S-1…S-12 screenshots of one side (before / after) against a
    running service, with every consistency variable of §5.2 pinned, and
    write ``index.json`` next to the PNG files.

``diff``
    Compare the two sides pixel by pixel and write the per-item verdicts
    (``diff/shots/<id>.json``), the side-by-side images and the delta
    images.

Two *separate* pixel-diff functions live here on purpose (§8.1 R-31):

* :func:`pixel_diff_for_shots` — the S-1…S-12 verdict, with the
  anti-aliasing tolerance band of §5.4.
* :func:`pixel_diff_for_g5` — the graph gate, which is a *negative*
  assertion: ``ae == 0`` or FAIL, no tolerance band at all (§5.7).

The G-5 *capture* protocol is deliberately **not** implemented here: it has
its own freeze procedure in ``design-notes/graph-isolation.md`` §6.3–§6.8 and
must not be reinvented (§5.7, W-17).
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover - reported, not fatal
    Image = None
    ImageChops = None

# ── §5.1 viewport table ──────────────────────────────────────────────────
VIEWPORTS = {
    "V1440": {"width": 1440, "height": 900, "device_scale_factor": 1},
    "V1024": {"width": 1024, "height": 800, "device_scale_factor": 1},
    "V768": {"width": 768, "height": 900, "device_scale_factor": 1},
    "V1280": {"width": 1280, "height": 900, "device_scale_factor": 1},
}

# ── §5.2 the pinned consistency variables ────────────────────────────────
CONSISTENCY = {
    "device_scale_factor": 1,
    "color_scheme": "light",
    "reduced_motion": "no-preference",
    "locale": "zh-CN",
    "timezone_id": "Asia/Shanghai",
    "browser_args": ["--force-color-profile=srgb", "--disable-lcd-text"],
    "font_gate": "document.fonts.ready + document.fonts.status === 'loaded'",
    "scroll_gate": "anchor element scrollIntoView({block:'start'})",
    "animation_gate": "no running finite animation at capture time",
}

# ── §5.6 the capture list ───────────────────────────────────────────────
# ``requires`` marks entries that need a collector this delivery does not
# have yet (the scripted exercise, an empty workspace, a second seed); they
# are reported as skipped, never as a pass.
SHOT_SPECS = [
    {"id": "S-1", "slug": "hub", "path": "/", "viewport": "V1440", "variant": "1440",
     "anchor": ".workspace-card", "focus": "最近使用置顶区、卡片信息层级"},
    {"id": "S-2", "slug": "practice", "path": "/w/{ws}/practice", "viewport": "V1440",
     "variant": "1440", "anchor": "#paper-setup", "focus": "顶栏三段式、题面纸、题号导航"},
    {"id": "S-3", "slug": "practice", "path": "/w/{ws}/practice", "viewport": "V1440",
     "variant": "in-progress", "anchor": "#paper-work",
     "focus": "题面独立纸、24px 题号、解析同级纸",
     "requires": "脚本化练习（exercise.py）——本交付未包含"},
    {"id": "S-4", "slug": "kps", "path": "/w/{ws}/kps", "viewport": "V1440", "variant": "1440",
     "anchor": "#middle-page", "focus": "分组卡片、彩色圆点状态"},
    {"id": "S-5", "slug": "kp-detail", "path": "/w/{ws}/kp", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page", "focus": "衬线阅读面 + 单侧结构线",
     "resolve": "first_kp_link"},
    {"id": "S-6", "slug": "records-overview", "path": "/w/{ws}/records", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page", "focus": "仪表盘卡片、热力日历"},
    {"id": "S-7", "slug": "records-detail", "path": "/w/{ws}/records", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page",
     "focus": "圆角卡片流（不得出现表格）", "resolve": "first_problem_link"},
    {"id": "S-8", "slug": "practice-sets", "path": "/w/{ws}/practice-sets", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page", "focus": "卡片网格、状态圆点、无 5px 黄带"},
    {"id": "S-9", "slug": "settings", "path": "/w/{ws}/settings", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page", "focus": "主题 / 阅读字面 / 动效 / 声音"},
    {"id": "S-10", "slug": "night", "path": "/", "viewport": "V1440", "variant": "dark",
     "color_scheme": "dark", "anchor": ".workspace-card",
     "focus": "夜纸值集、圆底降饱和提亮、插画反相"},
    {"id": "S-11", "slug": "narrow", "path": "/", "viewport": "V768", "variant": "768",
     "anchor": ".workspace-card", "focus": "三栏折叠、右栏抽屉"},
    {"id": "S-11", "slug": "narrow", "path": "/", "viewport": "V1024", "variant": "1024",
     "anchor": ".workspace-card", "focus": "三栏折叠、右栏抽屉"},
    {"id": "S-12", "slug": "empty", "path": "/w/{ws}/practice-sets", "viewport": "V1440",
     "variant": "1440", "anchor": "#middle-page", "focus": "插画 + 一句 + 满宽主按钮",
     "requires": "空工作区种子（第二份 seed）——本交付未包含"},
]

# ── §5.4 the tolerance band for the S series ────────────────────────────
SHOT_AA_TOLERANCE = 0.005


# ─────────────────────────────────────────────────────────────────────────
# in-page probes (§5.2)
# ─────────────────────────────────────────────────────────────────────────

_JS_ANCHOR = """
(selector) => {
  if (!selector) return {found: true, top: null, scrollY: window.scrollY};
  const el = document.querySelector(selector);
  if (!el) return {found: false, top: null, scrollY: window.scrollY};
  el.scrollIntoView({block: 'start'});
  const rect = el.getBoundingClientRect();
  return {found: true, top: Math.round(rect.top * 100) / 100, scrollY: Math.round(window.scrollY)};
}
"""

_JS_RUNNING_ANIMATIONS = """
() => {
  const anims = (document.getAnimations) ? document.getAnimations() : [];
  const running = [];
  for (const a of anims) {
    const timing = (a.effect && a.effect.getTiming) ? a.effect.getTiming() : {};
    const infinite = timing.iterations === Infinity;
    if (a.playState === 'running' && !infinite) {
      running.push({
        name: a.animationName || (a.constructor && a.constructor.name) || '?',
        duration: timing.duration,
      });
    }
  }
  return running;
}
"""

_JS_FONTS = """
() => ({
  status: document.fonts ? document.fonts.status : 'unsupported',
  families: document.fonts ? Array.from(document.fonts).map(f => f.family) : [],
})
"""


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ─────────────────────────────────────────────────────────────────────────
# capture
# ─────────────────────────────────────────────────────────────────────────


def _new_context(browser, viewport, color_scheme, reduced_motion):
    return browser.new_context(
        viewport={"width": viewport["width"], "height": viewport["height"]},
        device_scale_factor=viewport["device_scale_factor"],
        color_scheme=color_scheme,
        reduced_motion=reduced_motion,
        locale=CONSISTENCY["locale"],
        timezone_id=CONSISTENCY["timezone_id"],
    )


def _goto(page, url):
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        page.goto(url, wait_until="load", timeout=30000)


def _resolve_target(page, spec, base_url, ws):
    """Resolve the concrete URL of a spec entry (``{ws}`` and the resolvers).

    The resolver runs *before* the path is substituted, because a spec entry
    such as ``/w/{ws}/kp`` still needs a concrete id that only the page can
    supply.
    """
    resolver = spec.get("resolve")
    if resolver == "first_kp_link":
        _goto(page, base_url + f"/w/{ws}/kps")
        href = page.evaluate(
            "() => { const a = document.querySelector('a[href*=\"/kp/\"]');"
            " return a ? a.getAttribute('href') : null; }")
        if not href:
            return None, "找不到知识点链接（kps 页没有 a[href*='/kp/']）"
        return base_url + href, None
    if resolver == "first_problem_link":
        _goto(page, base_url + f"/w/{ws}/records?view=attempts")
        problem_id = page.evaluate(
            "() => { const a = document.querySelector('a[href*=\"problem=\"]');"
            " if (!a) return null;"
            " const m = a.getAttribute('href').match(/[?&]problem=([^&]+)/);"
            " return m ? decodeURIComponent(m[1]) : null; }")
        if not problem_id:
            return None, "记录页里找不到作答明细（没有带 problem= 的链接）"
        return (f"{base_url}/w/{ws}/records?view=attempts&problem={problem_id}", None)
    path = spec["path"].format(ws=ws)
    return base_url + path, None


def _settle_animations(page, timeout_ms=2000):
    """Wait until no *finite* animation is running, then report the state.

    `networkidle` says nothing about CSS animations: a view transition
    animates `#middle-page > *` in from `opacity: 0` for 240ms, so a shot
    taken right after networkidle catches a blank middle column.  Waiting
    here keeps the screenshot honest (and the comparison fair).
    """
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    running = []
    while True:
        running = page.evaluate(_JS_RUNNING_ANIMATIONS)
        if not running:
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(0.05)
    return {"running": running, "settled": not running}

def capture(base_url, ws, out_dir, only=None, seed=None):
    """Take the screenshots of one side and write ``index.json``."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shots = []
    skipped = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=list(CONSISTENCY["browser_args"]))
        try:
            for spec in SHOT_SPECS:
                if only and spec["id"] not in only:
                    continue
                if spec.get("requires"):
                    skipped.append({"id": spec["id"], "slug": spec["slug"],
                                    "variant": spec["variant"],
                                    "reason": spec["requires"]})
                    continue
                viewport = VIEWPORTS[spec["viewport"]]
                color_scheme = spec.get("color_scheme", CONSISTENCY["color_scheme"])
                context = _new_context(browser, viewport, color_scheme,
                                       CONSISTENCY["reduced_motion"])
                page = context.new_page()
                try:
                    url, reason = _resolve_target(page, spec, base_url, ws)
                    if url is None:
                        skipped.append({"id": spec["id"], "slug": spec["slug"],
                                        "variant": spec["variant"], "reason": reason})
                        continue
                    _goto(page, url)
                    anchor = page.evaluate(_JS_ANCHOR, spec.get("anchor"))
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    fonts = page.evaluate(_JS_FONTS)
                    # Settle before shooting: a view transition animates
                    # `#middle-page > *` in from `opacity: 0`, and networkidle
                    # does not wait for it — screenshotting straight after
                    # networkidle catches a **blank middle column** and the
                    # comparison then blames the CSS for a tool race.
                    settled = _settle_animations(page, timeout_ms=2000)
                    running = settled["running"]
                    name = f"{spec['id']}-{spec['slug']}-{spec['variant']}"
                    path = out_dir / f"{name}.png"
                    page.screenshot(path=str(path))
                    shots.append({
                        "id": spec["id"],
                        "slug": spec["slug"],
                        "variant": spec["variant"],
                        "file": path.name,
                        "url": url,
                        "focus": spec.get("focus", ""),
                        "viewport": viewport,
                        "color_scheme": color_scheme,
                        "reduced_motion": CONSISTENCY["reduced_motion"],
                        "anchor": spec.get("anchor"),
                        "anchor_found": anchor["found"],
                        "anchor_top": anchor["top"],
                        "scroll_y": anchor["scrollY"],
                        "running_animations": running,
                        "fonts_status": fonts["status"],
                        "sha256": sha256_file(path),
                        "bytes": path.stat().st_size,
                    })
                finally:
                    context.close()
        finally:
            browser.close()

    index = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "base_url": base_url,
        "workspace": ws,
        "consistency": CONSISTENCY,
        "seed": seed or {},
        "shots": shots,
        "skipped": skipped,
    }
    (out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


# ─────────────────────────────────────────────────────────────────────────
# pixel diff (§5.4 and §5.7)
# ─────────────────────────────────────────────────────────────────────────


def _load_rgb(path):
    if Image is None:
        raise RuntimeError("PIL is not available; cannot compare pixels")
    return Image.open(path).convert("RGB")


def _difference_stats(before_path, after_path):
    """Return ``(ae, ratio, bbox, size_mismatch)`` for two images."""
    before = _load_rgb(before_path)
    after = _load_rgb(after_path)
    if before.size != after.size:
        return None, None, None, (before.size, after.size)
    diff = ImageChops.difference(before, after)
    bbox = diff.getbbox()
    gray = diff.convert("L")
    histogram = gray.histogram()
    ae = sum(histogram[1:])
    total = before.size[0] * before.size[1]
    return ae, (ae / total if total else 0.0), bbox, None


def pixel_diff_for_shots(before_path, after_path):
    """The S-1…S-12 verdict (§5.4).

    ``ratio == 0`` -> identical.  ``0 < ratio <= 0.005`` -> only anti-aliasing
    differences, a human has to look.  ``ratio > 0.005`` -> FAIL.
    """
    ae, ratio, bbox, mismatch = _difference_stats(before_path, after_path)
    if mismatch is not None:
        return {
            "ae": None, "ratio": None, "bbox": None,
            "verdict": "FAIL",
            "detail": f"图像尺寸不同：before {mismatch[0]} vs after {mismatch[1]}",
            "size_mismatch": True,
        }
    if ae == 0:
        verdict, detail = "PASS", "完全一致"
    elif ratio <= SHOT_AA_TOLERANCE:
        verdict = "PENDING"
        detail = f"仅抗锯齿/字体渲染差异（ratio={ratio:.6f} ≤ {SHOT_AA_TOLERANCE}），需人工判读"
    else:
        verdict = "FAIL"
        detail = f"差异超出容差带（ratio={ratio:.6f} > {SHOT_AA_TOLERANCE}），bbox={bbox}"
    return {
        "ae": ae, "ratio": ratio, "bbox": list(bbox) if bbox else None,
        "verdict": verdict, "detail": detail, "size_mismatch": False,
    }


def pixel_diff_for_g5(before_path, after_path):
    """The G-5 verdict (§5.7).

    The graph gate is a *negative* assertion: the change must not have
    touched the graph page at all.  So the verdict is ``ae == 0`` -> PASS,
    anything else -> FAIL.  **No tolerance band** — that is §5.4's band and
    it must never leak in here (§8.1 R-31).
    """
    ae, ratio, bbox, mismatch = _difference_stats(before_path, after_path)
    if mismatch is not None:
        return {
            "ae": None, "ratio": None, "bbox": None, "verdict": "FAIL",
            "detail": f"图像尺寸不同：before {mismatch[0]} vs after {mismatch[1]}",
        }
    verdict = "PASS" if ae == 0 else "FAIL"
    return {
        "ae": ae, "ratio": ratio, "bbox": list(bbox) if bbox else None,
        "verdict": verdict,
        "detail": ("ae = 0，改造未误伤图谱" if ae == 0
                   else f"ae = {ae} ≠ 0，改造误伤了图谱（bbox={bbox}）"),
    }


def write_side_by_side(before_path, after_path, out_path, gap=2):
    """Before on the left, after on the right, a 2px separator between."""
    before = _load_rgb(before_path)
    after = _load_rgb(after_path)
    width = max(before.size[0], after.size[0])
    height = max(before.size[1], after.size[1])
    canvas = Image.new("RGB", (width * 2 + gap, height), (255, 255, 255))
    canvas.paste(before, (0, 0))
    canvas.paste(after, (width + gap, 0))
    canvas.save(out_path)
    return out_path


def write_delta(before_path, after_path, out_path):
    """Differing pixels in red, the rest greyed out."""
    before = _load_rgb(before_path)
    after = _load_rgb(after_path)
    if before.size != after.size:
        raise ValueError(f"size mismatch: {before.size} vs {after.size}")
    diff = ImageChops.difference(before, after)
    mask = diff.convert("L").point(lambda value: 255 if value else 0)
    grey = before.convert("L").convert("RGB")
    delta = Image.composite(Image.new("RGB", before.size, (220, 40, 40)), grey, mask)
    delta.save(out_path)
    return out_path


def diff_sides(before_dir, after_dir, out_dir):
    """Compare the two sides and write the per-item verdicts."""
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    before_index = _read_json(before_dir / "index.json") or {"shots": []}
    after_index = _read_json(after_dir / "index.json") or {"shots": []}
    before_shots = {s["file"]: s for s in before_index.get("shots", [])}
    after_shots = {s["file"]: s for s in after_index.get("shots", [])}

    results = []
    for name in sorted(set(before_shots) | set(after_shots)):
        before = before_shots.get(name)
        after = after_shots.get(name)
        entry = {
            "file": name,
            "id": (before or after)["id"],
            "slug": (before or after)["slug"],
            "variant": (before or after)["variant"],
        }
        if before is None:
            entry.update({"verdict": "N/A", "ae": None, "ratio": None,
                          "detail": "改造前没有这张图（该条目在改造前不存在）"})
        elif after is None:
            entry.update({"verdict": "N/A", "ae": None, "ratio": None,
                          "detail": "改造后没有这张图"})
        else:
            before_path = before_dir / name
            after_path = after_dir / name
            if not before_path.is_file() or not after_path.is_file():
                entry.update({"verdict": "BLOCKED", "ae": None, "ratio": None,
                              "detail": "PNG 文件缺失"})
            else:
                outcome = pixel_diff_for_shots(before_path, after_path)
                entry.update(outcome)
                entry["pair"] = f"diff/shots/{name}"
                try:
                    write_side_by_side(before_path, after_path, out_dir / name)
                    write_delta(before_path, after_path,
                                out_dir / name.replace(".png", "-delta.png"))
                    entry["pair_image"] = f"diff/shots/{name}"
                    entry["delta_image"] = f"diff/shots/{name.replace('.png', '-delta.png')}"
                except Exception as exc:
                    entry["pair_error"] = str(exc)
        (out_dir / name.replace(".png", ".json")).write_text(
            json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(entry)

    summary = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tolerance": SHOT_AA_TOLERANCE,
        "results": results,
    }
    (out_dir / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────────────────────
# command line
# ─────────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Capture and compare the walkthrough screenshots.")
    sub = parser.add_subparsers(dest="command", required=True)

    capture_parser = sub.add_parser("capture", help="take the screenshots of one side")
    capture_parser.add_argument("--base-url", required=True,
                                help="e.g. http://127.0.0.1:3191")
    capture_parser.add_argument("--ws", required=True, help="workspace name")
    capture_parser.add_argument("--out", required=True, help="output directory (shots/)")
    capture_parser.add_argument("--only", nargs="*", default=None,
                                help="only these shot ids (S-1 S-2 ...)")
    capture_parser.add_argument("--seed", default=None,
                                help="JSON describing the data state, stored in index.json")

    diff_parser = sub.add_parser("diff", help="compare the two sides pixel by pixel")
    diff_parser.add_argument("--before", required=True, help="before shots directory")
    diff_parser.add_argument("--after", required=True, help="after shots directory")
    diff_parser.add_argument("--out", required=True, help="diff output directory")

    args = parser.parse_args(argv)

    if args.command == "capture":
        seed = json.loads(args.seed) if args.seed else None
        index = capture(args.base_url, args.ws, args.out, args.only, seed)
        print(json.dumps({
            "shots": len(index["shots"]),
            "skipped": len(index["skipped"]),
            "files": [s["file"] for s in index["shots"]],
            "skipped_detail": index["skipped"],
        }, ensure_ascii=False, indent=2))
        return 0

    summary = diff_sides(args.before, args.after, args.out)
    print(json.dumps({
        "compared": len(summary["results"]),
        "results": [{"id": r["id"], "variant": r["variant"],
                     "verdict": r["verdict"], "ae": r.get("ae"),
                     "ratio": r.get("ratio")} for r in summary["results"]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
