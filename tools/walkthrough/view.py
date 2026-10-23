"""每波交付的**视觉板** —— before/after 对照截图 + 像素差 + 锚点。

用法（仓库根）::

    # ① 抓一侧（当前工作树）
    python tools/walkthrough/view.py capture \
        --base-url http://127.0.0.1:3322 --ws walk --out tmp/view/wave1-after

    # ② 出板（两份对照）
    python tools/walkthrough/view.py board \
        --before tmp/view/wave1-before --after tmp/view/wave1-after \
        --out tmp/view/wave1-board.html

为什么要有这个工具：每一波改的是**看得见的东西**（列宽、内边距、标题字号、
抽屉形态），而报告里的数字（280/740/420）没人能从文字里"看见"。
⇒ 每波结束都要给所有者**一张能打开的图**：左边是改前，右边是改后，
每行标出这一眼到底在看什么，外加一个**像素差百分比**当客观量。

**锚点必须写进板子**：所有者看到的是"哪一版"，必须可查
（沿用 `tmp/frontend-audit/layout-board/` 的做法：HEAD + CSS sha256 + 抓取时刻）。

⚠️ 抓图必须满足（沿用 `shots.py` §5.2 的一致性变量）：
   DSF=1 / srgb / 字体已加载 / 动画已停 / 视口高度固定 —— 否则两张图不可比。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

# ── 视口一致性（与 tools/walkthrough/shots.py 的 CONSISTENCY 对齐）────────
BROWSER_ARGS = ["--force-color-profile=srgb", "--disable-lcd-text"]
LOCALE = "zh-CN"
TIMEZONE = "Asia/Shanghai"
HEIGHT = 900

# ── 默认视图集 ────────────────────────────────────────────────────────────
# caption 要写成「一眼能看懂在看什么」，不是内部术语。
VIEWS = [
    {"id": "practice-1440", "page": "practice", "w": 1440, "theme": "paper",
     "caption": "练习页 · 1440（A 档：三栏 280 / 740 / 420）"},
    {"id": "practice-in-progress", "page": "practice", "w": 1440, "theme": "paper",
     "start_practice": True, "query": "?paper=ps-002",
     "caption": "练习页 · 1440 · 进行中（样板图 shell.html 对应的那一态）"},
    {"id": "practice-1280", "page": "practice", "w": 1280, "theme": "paper",
     "caption": "练习页 · 1280（B 档：收窄到 248 / 652 / 380）"},
    {"id": "practice-1024", "page": "practice", "w": 1024, "theme": "paper",
     "caption": "练习页 · 1024（C 档：右栏出栅格，中栏拿到 792）"},
    {"id": "practice-768", "page": "practice", "w": 768, "theme": "paper",
     "caption": "练习页 · 768（D 档：单栏 + 双抽屉）"},
    {"id": "kps-1440", "page": "kps", "w": 1440, "theme": "paper",
     "caption": "知识点列表 · 1440"},
    {"id": "records-1440", "page": "records", "w": 1440, "theme": "paper",
     "caption": "记录中心 · 1440"},
    {"id": "hub-1440", "page": "hub", "w": 1440, "theme": "paper",
     "caption": "工作台首页 · 1440"},
    {"id": "practice-1440-night", "page": "practice", "w": 1440, "theme": "night",
     "caption": "练习页 · 1440 · 夜纸（夜纸值集不变）"},
]

PAGES = {
    "hub": "/w/{ws}/",
    "practice": "/w/{ws}/practice",
    "kps": "/w/{ws}/kps",
    "records": "/w/{ws}/records",
    "practice-sets": "/w/{ws}/practice-sets",
    "settings": "/w/{ws}/settings",
}

# ── 抓图前的三道闸门（照 tools/walkthrough/shots.py 的 CONSISTENCY）────────
# ⚠️ **动画闸门是必须的，不是锦上添花**：`networkidle` 对 CSS 动画一无所知，
# 而视图转场会把 `#middle-page > *` 从 `opacity: 0` 动画进来（240ms）——
# 刚过 networkidle 就截图 ⇒ **拍到一片空白的中栏**（本工具第一版就踩了：
# 1440 的「改后」图整列内容是空的，而产品其实正常）。
# ⇒ 必须等到**没有正在跑的有限动画**再拍，否则两张图不可比。
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


def _settle_animations(page, timeout_ms=3000):
    """等到没有正在跑的**有限**动画，再截图。"""
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


def _anchor(repo_root):
    """抓图时刻的版本锚点 —— 板子顶部要显示它。"""
    root = pathlib.Path(repo_root)
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(root), text=True).strip()
    except Exception:
        head = "?"
    css = root / "workbench" / "server" / "static" / "workbench.css"
    data = css.read_bytes() if css.is_file() else b""
    dirty = False
    try:
        diff = subprocess.check_output(
            ["git", "status", "--porcelain", "--",
             "workbench/server/static/workbench.css",
             "workbench/server/static/workbench.js",
             "workbench/server/static/agent-ui.css"],
            cwd=str(root), text=True)
        dirty = bool(diff.strip())
    except Exception:
        pass
    return {
        "head": head,
        "css_bytes": len(data),
        "css_sha256": hashlib.sha256(data).hexdigest()[:16],
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        # ⚠️ 抓"改前"那一侧时通常是把旧版文件 checkout 出来的 ⇒ 工作树与 HEAD 不一致。
        #    这时 **HEAD 不代表图里的版本**，CSS 的 sha256 才是。
        "tree_dirty": dirty,
    }


def capture(args):
    from playwright.sync_api import sync_playwright

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    views = [v for v in VIEWS if not args.only or v["id"] in args.only]
    manifest = {"anchor": _anchor(args.repo_root), "ws": args.ws,
                "base_url": args.base_url, "views": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=BROWSER_ARGS)
        try:
            for view in views:
                context = browser.new_context(
                    viewport={"width": view["w"], "height": HEIGHT},
                    device_scale_factor=1,
                    color_scheme="light",
                    reduced_motion="no-preference",
                    locale=LOCALE,
                    timezone_id=TIMEZONE,
                )
                # 主题走产品的偏好存储（`wb_settings_<ws>` 的 theme 键），
                # 不用 prefers-color-scheme —— 产品认的是显式偏好。
                context.add_init_script(
                    "try { window.localStorage.setItem(%r, JSON.stringify({theme: %r}));"
                    " } catch (e) {}" % ("wb_settings_" + args.ws, view["theme"])
                )
                page = context.new_page()
                url = args.base_url.rstrip("/") + PAGES[view["page"]].format(ws=args.ws) + view.get("query", "")
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    # 「进行中」那一态要点开练习（产品里没有直达链接）
                    if view.get("start_practice"):
                        try:
                            page.wait_for_selector("#paper-start", state="visible", timeout=15000)
                            page.click("#paper-start")
                            page.wait_for_timeout(1200)
                        except Exception as exc:
                            print(f"  ! {view['id']} 起练习失败：{exc}")
                    # 字体没加载完就截图 ⇒ 两张图不可比
                    try:
                        page.evaluate("() => document.fonts.ready")
                    except Exception:
                        pass
                    # ⚠️ 动画闸门：视图转场把 `#middle-page > *` 从 opacity:0 动画进来，
                    #    刚过 networkidle 拍 ⇒ 中栏一片空白（第一版的 bug）。
                    settle = _settle_animations(page)
                    try:
                        page.wait_for_timeout(250)
                    except Exception:
                        pass
                    # ⚠️ 空白中栏守卫：内容为空时**大声报出来**，不要让一张空图混进板子。
                    middle_text = page.evaluate(
                        """() => {
                            const el = document.querySelector('#middle-page');
                            if (!el) return -1;
                            const t = (el.innerText || '').trim();
                            return t.length;
                        }"""
                    )
                    path = out / (view["id"] + ".png")
                    page.screenshot(path=str(path), full_page=False)
                    manifest["views"].append({
                        "id": view["id"], "caption": view["caption"],
                        "file": path.name, "width": view["w"], "theme": view["theme"],
                        "page": view["page"],
                        "settled": settle["settled"],
                        "running_at_shot": settle["running"],
                        "middle_text_chars": middle_text,
                    })
                    if not settle["settled"]:
                        print(f"  ! {view['id']:23} 截图时仍有动画在跑："
                              f"{[a.get('name') for a in settle['running']]}")
                    if middle_text <= 0:
                        print(f"  ! {view['id']:23} **中栏是空的**（0 个字符）——"
                              f"这张图不能进板子")
                    print(f"  captured {view['id']:24} {view['w']}x{HEIGHT} {view['theme']}")
                finally:
                    context.close()
        finally:
            browser.close()

    (out / "index.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written:", out / "index.json")
    return 0


def _pixel_delta(before_png, after_png):
    """两张图的像素差百分比（Pillow）。尺寸不同 ⇒ 返回 None。"""
    try:
        from PIL import Image, ImageChops
    except Exception:
        return None
    try:
        a = Image.open(before_png).convert("RGB")
        b = Image.open(after_png).convert("RGB")
    except Exception:
        return None
    if a.size != b.size:
        return None
    diff = ImageChops.difference(a, b).convert("L")
    changed = sum(1 for px in diff.getdata() if px > 8)
    return round(100.0 * changed / (a.size[0] * a.size[1]), 3)


def capture_static(args):
    """拍一张**静态 HTML**（样板图这类）—— 不需要起服务，走 file://。"""
    from playwright.sync_api import sync_playwright

    src = pathlib.Path(args.file).resolve()
    if not src.is_file():
        print("找不到文件:", src)
        return 1
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=BROWSER_ARGS)
        try:
            context = browser.new_context(
                viewport={"width": args.width, "height": args.height},
                device_scale_factor=1, color_scheme="light",
                reduced_motion="no-preference", locale=LOCALE, timezone_id=TIMEZONE,
            )
            page = context.new_page()
            page.goto(src.as_uri(), wait_until="load", timeout=30000)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            _settle_animations(page)
            page.wait_for_timeout(250)
            page.screenshot(path=str(out), full_page=False)
            print("captured:", out)
        finally:
            browser.close()
    return 0


def board(args):
    before_dir = pathlib.Path(args.before)
    after_dir = pathlib.Path(args.after)
    b_index = json.loads((before_dir / "index.json").read_text(encoding="utf-8"))
    a_index = json.loads((after_dir / "index.json").read_text(encoding="utf-8"))
    b_views = {v["id"]: v for v in b_index["views"]}
    a_views = {v["id"]: v for v in a_index["views"]}

    # 参考列（靶子）：目录里放**与产品视图同名**的 PNG
    reference = {}
    reference_dir = pathlib.Path(args.reference) if args.reference else None
    if reference_dir:
        for vid in a_views:
            candidate = reference_dir / (vid + ".png")
            if candidate.is_file():
                reference[vid] = candidate

    rows = []
    for vid, av in a_views.items():
        bv = b_views.get(vid)
        if not bv:
            continue
        delta = _pixel_delta(before_dir / bv["file"], after_dir / av["file"])
        rows.append({"caption": av["caption"], "id": vid,
                     "before": bv["file"], "after": av["file"], "delta": delta,
                     "reference": reference.get(vid)})

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 图片路径改成相对板子文件的路径，方便整目录拷走
    for row in rows:
        row["before_href"] = os.path.relpath(before_dir / row["before"], out.parent)
        row["after_href"] = os.path.relpath(after_dir / row["after"], out.parent)
        if row["reference"]:
            row["reference_href"] = os.path.relpath(row["reference"], out.parent)

    html = _render(rows, b_index["anchor"], a_index["anchor"], out)
    out.write_text(html, encoding="utf-8")
    print("written:", out)
    for row in rows:
        mark = "—" if row["delta"] is None else f"{row['delta']:.3f}%"
        print(f"  {row['id']:24} 像素差 {mark}"
              + ("  [有靶子]" if row["reference"] else ""))
    return 0


def _render(rows, b_anchor, a_anchor, out_path):
    def esc(text):
        return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    cards = []
    for row in rows:
        delta = "—" if row["delta"] is None else f"{row['delta']:.3f}%"
        reference_cell = ""
        if row.get("reference"):
            reference_cell = f"""
        <figure><figcaption>靶子 · 样板图基线</figcaption>
          <img src="{esc(row['reference_href'])}" alt="reference {esc(row['id'])}"></figure>"""
        cards.append(f"""
    <section class="row">
      <h2>{esc(row['caption'])}<span class="delta">改前→改后 像素差 {esc(delta)}</span></h2>
      <div class="pair">
        {reference_cell}
        <figure><figcaption>改前</figcaption>
          <img src="{esc(row['before_href'])}" alt="before {esc(row['id'])}"></figure>
        <figure><figcaption>改后</figcaption>
          <img src="{esc(row['after_href'])}" alt="after {esc(row['id'])}"></figure>
      </div>
    </section>""")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>版式视觉板 · before / after</title>
<link rel="icon" href="data:,">
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px 28px 60px;
    background: #fdf8ef; color: #3b3630;
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 14px; line-height: 1.6;
  }}
  header {{ border-bottom: 1px solid #e6dcc4; padding-bottom: 14px; margin-bottom: 22px; }}
  h1 {{ margin: 0 0 8px; font-size: 22px; }}
  .anchors {{ font-size: 12px; color: #6b6459; display: grid; gap: 3px; }}
  .anchors b {{ color: #221f1a; font-weight: 600; }}
  .row {{ margin: 0 0 30px; }}
  .row h2 {{ font-size: 15px; margin: 0 0 8px; font-weight: 600; color: #221f1a;
             display: flex; gap: 12px; align-items: baseline; }}
  .delta {{ font-size: 12px; font-weight: 400; color: #6b6459; }}
  .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  figure {{ margin: 0; }}
  figcaption {{ font-size: 12px; color: #6b6459; margin-bottom: 4px; }}
  img {{ width: 100%; height: auto; display: block; border: 1px solid #e6dcc4;
         border-radius: 8px; background: #fff; }}
  .note {{ font-size: 12px; color: #6b6459; margin-top: 10px; }}
</style>
</head>
<body>
<header>
  <h1>版式视觉板 · 改前 / 改后</h1>
  <div class="anchors">
    <div>改前：<b>HEAD {esc(b_anchor.get('head'))}</b> · CSS {esc(b_anchor.get('css_bytes'))} B · sha256 {esc(b_anchor.get('css_sha256'))} · 抓取于 {esc(b_anchor.get('captured_at'))}{' · <b>工作树与 HEAD 不一致</b>（抓的是旧版文件 ⇒ 以 sha256 为准）' if b_anchor.get('tree_dirty') else ''}</div>
    <div>改后：<b>HEAD {esc(a_anchor.get('head'))}</b> · CSS {esc(a_anchor.get('css_bytes'))} B · sha256 {esc(a_anchor.get('css_sha256'))} · 抓取于 {esc(a_anchor.get('captured_at'))}{' · <b>工作树与 HEAD 不一致</b>' if a_anchor.get('tree_dirty') else ''}</div>
    <div class="note">「像素差」= 两张图逐像素比较后不同像素的占比（容差 8/255）。分母是整幅画面，
      所以几何改动通常只有百分之几 —— 看图比看这个数有用。</div>
  </div>
</header>
{''.join(cards)}
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="每波交付的 before/after 视觉板")
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="抓一侧的截图")
    cap.add_argument("--base-url", required=True)
    cap.add_argument("--ws", required=True)
    cap.add_argument("--out", required=True)
    cap.add_argument("--repo-root", default=".")
    cap.add_argument("--only", nargs="*", default=None)

    static = sub.add_parser("capture-static", help="拍一张静态 HTML（样板图等）")
    static.add_argument("--file", required=True)
    static.add_argument("--out", required=True)
    static.add_argument("--width", type=int, default=1440)
    static.add_argument("--height", type=int, default=900)

    brd = sub.add_parser("board", help="两份对照出板（可加靶子列）")
    brd.add_argument("--before", required=True)
    brd.add_argument("--after", required=True)
    brd.add_argument("--out", required=True)
    brd.add_argument("--reference", default=None,
                     help="靶子截图目录（文件名与产品视图 id 同名）")

    args = parser.parse_args(argv)
    if args.command == "capture":
        return capture(args)
    if args.command == "capture-static":
        return capture_static(args)
    return board(args)


if __name__ == "__main__":
    raise SystemExit(main())
