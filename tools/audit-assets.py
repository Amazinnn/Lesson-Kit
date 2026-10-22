"""Audit the static SVG assets against `design-notes/asset-spec.md`.

This is the acceptance gate for the asset work: the spec already carries a
measured size table (§3.12) and says "画完后请用浏览器的 getBBox() 复核，偏差 > 2 u
即说明画偏了".  Nobody ran that check, so the assets drifted.

Usage:
    python tools/audit-assets.py            # human-readable table
    python tools/audit-assets.py --json     # machine-readable
    python tools/audit-assets.py --strict   # exit 1 when any check fails

Exit codes: 0 = all pass, 1 = at least one check failed (with --strict),
2 = the audit itself could not run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "workbench" / "server" / "static" / "assets"

# --- the authority: asset-spec.md §3.12 (插画尺寸实测表) ---------------------
# asset -> (x_min, x_max, y_min, y_max)  [u]
SPEC_SIZE = {
    "empty-vase":         (78, 158, 36, 166),
    "empty-fruit-basket": (74, 166, 85, 167),
    "empty-canvas":       (70, 170, 48, 166),
    "empty-cup":          (74, 164, 88, 167),
    "empty-books":        (60, 180, 114, 166),
    "empty-pen":          (59.5, 171, 121, 166),
    "empty-pencil-cup":   (92, 146, 44, 166),
    "empty-globe":        (84, 156, 52, 166),
    "empty-inkwell":      (89, 162, 69, 166),
    "empty-compass":      (88, 154, 43, 166),
}
TOLERANCE_U = 2.0          # §3.12: 偏差 > 2 u 即说明画偏了
VIEWBOX = {"icon": "0 0 48 48", "empty": "0 0 240 200", "lamp": "0 0 240 240"}
STROKE_LADDER = {1.5, 2, 3}   # §1.2: 主 3u / 次 2u / 细 1.5u，不得出现第四档
BASELINE_Y = 168              # §3.0: 桌面横线统一落在 y = 168
BASELINE_LEN = (144, 168)     # 画幅宽的 60%–70%
DESKTOP_LINE_COLOR = "8%"     # 中性 8%–10%

_MEASURE_JS = """
() => {
  const svg = document.querySelector('svg');
  const out = {viewBox: svg.getAttribute('viewBox'),
               rootWidth: svg.getAttribute('width'),
               rootHeight: svg.getAttribute('height'),
               linecap: null, linejoin: null, clipPaths: 0, filters: 0,
               strokes: [], fillOpacity: [], strokeOpacity: [],
               groups: [], bbox: null, baseline: null, highlight: 0,
               washFills: 0, shadowOpacities: []};
  const all = svg.querySelectorAll('*');
  for (const el of all) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'clippath') out.clipPaths++;
    if (tag.startsWith('fe')) out.filters++;
    if (el.hasAttribute('filter')) out.filters++;
    if (el.hasAttribute('fill-opacity')) out.fillOpacity.push(el.getAttribute('fill-opacity'));
    if (el.hasAttribute('stroke-opacity')) out.strokeOpacity.push(el.getAttribute('stroke-opacity'));
    if (el.classList && el.classList.contains('asset-empty__shadow')) {
      out.groups.push('shadow');
      const o = el.getAttribute('opacity');
      if (o) out.shadowOpacities.push(parseFloat(o));
    }
    if (el.classList && el.classList.contains('asset-empty__wash')) out.groups.push('wash');
    if (el.classList && el.classList.contains('asset-empty__line')) out.groups.push('line');
    if (el.classList && el.classList.contains('asset-empty__highlight')) out.groups.push('highlight');
    const sw = el.getAttribute('stroke-width');
    if (sw !== null && sw !== '') out.strokes.push(parseFloat(sw));
    const f = el.getAttribute('fill');
    if (f && (f.indexOf('--asset-wash') >= 0 || f.indexOf('color-mix') >= 0)) out.washFills++;
  }
  // resolved linecap / linejoin (inherit from the outermost <g>)
  const g = svg.querySelector('g');
  if (g) { out.linecap = g.getAttribute('stroke-linecap'); out.linejoin = g.getAttribute('stroke-linejoin'); }
  // the object bbox, excluding the desktop baseline + contact shadow group
  // 延伸元素（蒸汽 / 花枝）按 asset-spec §3.0 必须带 asset-empty__extension ⇒ 排除
  const body = svg.querySelector('.asset-empty__line, .asset-empty__wash');
  let box = null;
  if (body) {
    for (const el of body.ownerSVGElement.querySelectorAll('.asset-empty__line *, .asset-empty__wash *')) {
      if (el.closest('.asset-empty__extension')) continue;
      let b;
      try { b = el.getBBox(); } catch (e) { continue; }
      if (!b || (b.width === 0 && b.height === 0)) continue;
      box = box ? {x: Math.min(box.x, b.x), y: Math.min(box.y, b.y),
                   x2: Math.max(box.x2, b.x + b.width), y2: Math.max(box.y2, b.y + b.height)} : {x: b.x, y: b.y, x2: b.x + b.width, y2: b.y + b.height};
    }
  }
  out.bbox = box;
  // the desktop baseline: a near-horizontal stroked path inside the shadow group
  const sg = svg.querySelector('.asset-empty__shadow');
  if (sg) {
    for (const p of sg.querySelectorAll('path')) {
      const d = p.getAttribute('d') || '';
      const m = d.match(/M\\s*([\\d.]+)\\s+([\\d.]+)\\s+L\\s*([\\d.]+)\\s+([\\d.]+)/);
      if (m && Math.abs(parseFloat(m[2]) - parseFloat(m[4])) < 1.5) {
        const y = parseFloat(m[2]);
        if (Math.abs(y - 168) < 1.5) {
          out.baseline = {y: y, x1: parseFloat(m[1]), x2: parseFloat(m[3])};
        }
      }
    }
  }
  out.highlight = svg.querySelectorAll('.asset-empty__highlight path, .asset-empty__highlight ellipse').length;
  return out;
}
"""


def _check(results, asset, name, ok, expected, actual, note=""):
    results.append({"asset": asset, "check": name, "ok": bool(ok),
                    "expected": expected, "actual": actual, "note": note})


async def _measure_all():
    from playwright.async_api import async_playwright
    files = sorted(ASSETS.glob("*/*.svg"))
    data = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        for f in files:
            raw = f.read_text(encoding="utf-8")
            raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
            await page.set_content(
                f"<!doctype html><meta charset=utf-8>"
                f"<style>svg{{--asset-paper:#fffdf7;--asset-ink:#2a2620}}</style>{raw}")
            await page.wait_for_timeout(30)
            key = f"{f.parent.name}/{f.stem}"
            data[key] = await page.evaluate(_MEASURE_JS)
        await browser.close()
    return data


def audit(data):
    results = []
    for key, m in sorted(data.items()):
        kind = "icon" if key.startswith("icons/") else ("lamp" if key.startswith("motion/") else "empty")
        # --- technical (§1.1 §1.2 §1.3 §1.12 §5.2) ---
        _check(results, key, "viewBox", m["viewBox"] == VIEWBOX[kind], VIEWBOX[kind], m["viewBox"])
        _check(results, key, "根上无 width/height",
               not m["rootWidth"] and not m["rootHeight"], "无", f"{m['rootWidth']}/{m['rootHeight']}")
        _check(results, key, "无 SVG filter", m["filters"] == 0, 0, m["filters"], "§1.5 禁止 filter")
        _check(results, key, "无 fill/stroke-opacity", not m["fillOpacity"] and not m["strokeOpacity"],
               0, f"{m['fillOpacity']}/{m['strokeOpacity']}", "§1.5 淡彩用预混色，不用 alpha")
        if kind == "empty":
            _check(results, key, "端点/连接 round",
                   m["linecap"] == "round" and m["linejoin"] == "round",
                   "round/round", f"{m['linecap']}/{m['linejoin']}", "§1.3")
            bad = sorted({s for s in m["strokes"] if s not in STROKE_LADDER})
            _check(results, key, "线宽在 3:2:1.5 阶梯内", not bad,
                   sorted(STROKE_LADDER), bad or sorted(set(m["strokes"])), "§1.2 不得出现第四档")
            _check(results, key, "线宽档数 ≤ 3", len(set(m["strokes"])) <= 3, "≤3", len(set(m["strokes"])))
            for grp in ("wash", "line", "highlight", "shadow"):
                _check(results, key, f"含 {grp} 组", grp in m["groups"], "有", m["groups"], "§1.8 语义组")
            _check(results, key, "桌面横线 y=168", m["baseline"] is not None, "y=168",
                   m["baseline"] and m["baseline"]["y"])
            if m["baseline"]:
                ln = abs(m["baseline"]["x2"] - m["baseline"]["x1"])
                _check(results, key, "横线长度 144–168u",
                       BASELINE_LEN[0] <= ln <= BASELINE_LEN[1], f"{BASELINE_LEN[0]}–{BASELINE_LEN[1]}",
                       round(ln, 1), "§3.0 画幅宽的 60%–70%")
            _check(results, key, "高光 ≤ 2 处", m["highlight"] <= 2, "≤2", m["highlight"], "§3.0")
            _check(results, key, "阴影不透明度 ≤ 12%",
                   all(o <= 0.12 for o in m["shadowOpacities"]), "≤0.12",
                   m["shadowOpacities"], "§3.0")
        # --- size / safe area (§1.1 §3.0 §3.12) ---
        if key.split("/")[-1] in SPEC_SIZE and m["bbox"]:
            exp = SPEC_SIZE[key.split("/")[-1]]
            meas = (m["bbox"]["x"], m["bbox"]["x2"], m["bbox"]["y"], m["bbox"]["y2"])
            dev = [round(meas[i] - exp[i], 1) for i in range(4)]
            worst = max(abs(d) for d in dev)
            _check(results, key, "外接框贴住 §3.12 实测表（±2u）", worst <= TOLERANCE_U,
                   f"偏差 ≤{TOLERANCE_U}u", f"最大偏差 {worst}u {dev}", "§3.12")
            longest = max(meas[1] - meas[0], meas[3] - meas[2])
            _check(results, key, "最长边 60–125u", 60 <= longest <= 125, "60–125", round(longest, 1))
            _check(results, key, "器物高 ≤ 132u", (meas[3] - meas[2]) <= 132, "≤132",
                   round(meas[3] - meas[2], 1))
            _check(results, key, "左右留白 ≥ 40u",
                   meas[0] >= 40 and (240 - meas[1]) >= 40, "≥40",
                   f"左 {round(meas[0], 1)} 右 {round(240 - meas[1], 1)}")
            _check(results, key, "压线 165–168u", 165 <= meas[3] <= 168, "165–168", round(meas[3], 1))
            _check(results, key, "水平偏移 ≤ 6u",
                   abs((meas[0] + meas[1]) / 2 - 120) <= 6, "≤6",
                   round(abs((meas[0] + meas[1]) / 2 - 120), 1))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    try:
        data = asyncio.run(_measure_all())
    except Exception as exc:                      # pragma: no cover
        print(f"audit could not run: {exc}", file=sys.stderr)
        return 2
    results = audit(data)
    fails = [r for r in results if not r["ok"]]
    if args.json:
        print(json.dumps({"results": results, "failed": len(fails)}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if not r["ok"]:
                print(f"  ✗ {r['asset']:<34} {r['check']:<28} 期望 {r['expected']} / 实得 {r['actual']} {r['note']}")
        print(f"\n{len(results) - len(fails)}/{len(results)} 项通过，{len(fails)} 项不通过")
    return 1 if (args.strict and fails) else 0


if __name__ == "__main__":
    raise SystemExit(main())
