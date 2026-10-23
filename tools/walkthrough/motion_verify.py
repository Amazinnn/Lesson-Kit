"""Supplementary motion verification — the items ``frames.py`` does not cover.

Why this module exists
-----------------------
``tools/walkthrough/frames.py`` covers M-1…M-10.  Three things are still
missing, and this module measures them **without touching product code and
without changing any existing harness module**:

1. **M-11** (连对断裂负反馈) — no entry in ``frames.py`` at all.
2. **M-12** (动效偏好与系统 reduced-motion 的分级降级) — ``frames.py`` only
   takes the *reduced twin* (system reduce + preference unset).  The four
   combinations of A-2 need four runs.
3. **M-9** (骨架屏) — ``frames.py``'s judge still measures the **old**
   criterion (「微光扫过」, A-115 已作废).  A-117 §1 定稿 the new criterion
   (「灰块**自身表面**随时间变化」), so M-9 has to be measured again.

Two more things are measured here because ``frames.py``'s watch list cannot
see them, although they are part of the acceptance criteria:

* **M-2 / M-3** — the number rolling is a **rAF text writer**, not a CSS
  animation, so ``frames.py``'s ``setTime`` cannot address it; and the
  progress band's fill element is ``.lk-progress__fill`` (two underscores),
  while ``frames.py`` watches ``.lk-progress-fill`` (one).
* **M-4 / M-6** — ``frames.py``'s streak trigger calls ``streak.apply()``
  **before** the card is re-rendered, while **both product flows**
  (``paper-practice.js:1141`` and ``practice-flow.js:1697``) re-render
  **first** and apply afterwards.  The order matters: ``showBanner()`` adds
  ``is-on`` to the banner element that exists at that moment, and a later
  re-render wipes it again ⇒ the banner stays invisible (opacity 0) in
  ``frames.py``'s capture.  This module drives the **product's own order**
  and says so in its evidence.

Red lines: this module drives a browser and reads the DOM.  It never writes
the pool and never touches product code.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import frames as F  # noqa: E402  (path set up above)

PASS, FAIL, PENDING, NA = "PASS", "FAIL", "PENDING", "N/A"


# ─────────────────────────────────────────────────────────────────────────
# the helpers
# ─────────────────────────────────────────────────────────────────────────


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


def pref_js(ws, pref):
    """Write (or clear) the ``motion`` preference of the open workspace.

    ``None`` ⇒ the field is **absent** (偏好未设).  ``True`` / ``False`` ⇒
    the explicit pick.  The record is the product's own
    ``wb_settings_<workspace>`` (workbench.js: ``SETTINGS_KEY``).
    """
    literal = "null" if pref is None else ("true" if pref else "false")
    return """
(() => {
  try {
    var key = "wb_settings_%s";
    var data = {};
    try { data = JSON.parse(window.localStorage.getItem(key) || "{}") || {}; }
    catch (error) { data = {}; }
    if (%s === null) delete data.motion;
    else data.motion = %s;
    window.localStorage.setItem(key, JSON.stringify(data));
  } catch (error) { /* a locked store must not break the page */ }
})();
""" % (ws, literal, literal)


def launch(playwright, reduced_motion=None, pref=None, ws=None):
    """A browser with the consistency variables of §5.2 pinned."""
    browser, context, page = F._launch(playwright, reduced_motion=reduced_motion)
    if ws is not None and pref is not None:
        page.add_init_script(pref_js(ws, pref))
    return browser, context, page


def ctx_of(base_url, ws, plan=None, motion_id=None, paper_id=None):
    return F._Context(base_url, ws, paper_id, plan=plan, motion_id=motion_id)


def matrix_scale(value):
    """The **X** scale of a computed ``transform`` (1 when there is none)."""
    match = re.match(r"matrix\(([-\d.]+),", str(value or ""))
    if match:
        return float(match.group(1))
    return 1.0


def matrix_scale_y(value):
    """The **Y** scale of a computed ``transform`` (1 when there is none).

    The load bars grow in **Y** (``scaleY(0→1)``, ``transform-origin: bottom``)
    ⇒ the X component of their matrix stays 1 and says nothing about them.
    """
    match = re.match(r"matrix\(\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),",
                     str(value or ""))
    if match:
        return float(match.group(4))
    return 1.0


def translate_x(value):
    """The X translation of a computed ``transform`` (0 when there is none)."""
    match = re.match(r"matrix\(1, 0, 0, 1, ([-\d.]+),", str(value or ""))
    if match:
        return float(match.group(1))
    return 0.0


# ─────────────────────────────────────────────────────────────────────────
# M-9 — the skeleton, measured against A-115 / A-117
# ─────────────────────────────────────────────────────────────────────────

#: What has to be read off one skeleton block.
#:
#: ⚠️ The **downgraded tier** paints the same blocks **without** the class
#: ``.lk-skeleton`` (middle-navigation.js::skeletonBlock: 「降级档：不用
#: ``.lk-skeleton`` … 改用等价的静态灰块」).  The selector therefore asks for
#: the wrapper's children as well — otherwise the twin would be measured as
#: "no skeleton at all".
SKELETON_JS = r"""
() => {
  const nodes = Array.from(document.querySelectorAll(
      "[data-lk-skeleton] > div, .lk-skeleton"));
  return nodes.slice(0, 12).map((el) => {
    const st = getComputedStyle(el);
    const after = getComputedStyle(el, "::after");
    const rect = el.getBoundingClientRect();
    return {
      cls: String(el.className || ""),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      opacity: st.opacity,
      background: st.backgroundColor,
      backgroundImage: st.backgroundImage.slice(0, 90),
      animationName: st.animationName,
      transform: st.transform,
      afterAnimation: after ? after.animationName : "none",
      afterBackground: after ? after.backgroundImage.slice(0, 90) : "none",
      afterTransform: after ? after.transform : "none",
      hasAfterContent: after ? after.content !== "none" : false,
    };
  });
}
"""


def run_m9(playwright, base_url, ws, out_dir):
    """M-9 — the breathing skeleton, in the animated tier and in the twin."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-9"
    frames_dir.mkdir(parents=True, exist_ok=True)
    times = (0, 200, 400, 600, 800, 900)

    def one_run(reduced):
        browser, context, page = launch(playwright, reduced_motion=reduced)
        held = []

        def hold(route):
            held.append(route)

        try:
            page.route("**/w/*/practice-sets", hold)
            ctx = ctx_of(base_url, ws)
            F.prepare_skeleton(page, ctx)
            F.act_skeleton(page, ctx)
            samples = []
            for t in times:
                page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
                page.wait_for_timeout(40)
                blocks = page.evaluate(SKELETON_JS)
                name = f"{t:04d}.png"
                page.screenshot(path=str(frames_dir / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, "blocks": blocks})
            # the terminal state of the twin: every animation finished
            page.evaluate("() => window.__lkFrame.finish()")
            page.wait_for_timeout(200)
            terminal = page.evaluate(SKELETON_JS)
            return {"samples": samples, "terminal": terminal}
        finally:
            for route in held:
                try:
                    route.continue_()
                except Exception:
                    pass
            context.close()
            browser.close()

    animated = one_run(None)
    reduced = one_run("reduce")

    # ---- the judge (A-117 §1, verbatim) --------------------------------
    first = animated["samples"][0]["blocks"]
    if not first:
        return {"id": "M-9", "verdict": PENDING,
                "detail": "没有采到骨架块", "animated": animated, "reduced": reduced}
    has_box = all(b["width"] > 0 and b["height"] > 0 for b in first)
    surfaces = []
    for sample in animated["samples"]:
        for block in sample["blocks"]:
            surfaces.append((sample["t"], block["background"], block["opacity"]))
    bg_values = {value for _, value, _ in surfaces}
    op_values = {value for _, _, value in surfaces}
    own_animation = sorted({block["animationName"] for sample in animated["samples"]
                            for block in sample["blocks"]})
    sweep = sorted({block["afterAnimation"] for sample in animated["samples"]
                    for block in sample["blocks"]})
    gradients = sorted({block["backgroundImage"] for sample in animated["samples"]
                        for block in sample["blocks"]})
    after_gradients = sorted({block["afterBackground"] for sample in animated["samples"]
                              for block in sample["blocks"]})

    changes = len(bg_values) >= 2 or len(op_values) >= 2
    own_keyframe = any(name and name != "none" for name in own_animation)
    surface_changed = changes or own_keyframe
    no_sweep = all(name in ("none", None, "") for name in sweep)
    no_gradient = all(g in ("none", "") for g in gradients) and \
        all(g in ("none", "") for g in after_gradients)

    reduced_blocks = reduced["terminal"]
    reduced_has_box = bool(reduced_blocks) and all(
        b["width"] > 0 and b["height"] > 0 for b in reduced_blocks)
    reduced_static = bool(reduced_blocks) and all(
        (b["animationName"] in ("none", "")) for b in reduced_blocks)
    reduced_opacity = sorted({b["opacity"] for b in reduced_blocks})

    checks = {
        "有体积（width>0 且 height>0）": has_box,
        "块自身表面随时间变化（底色或 opacity）": surface_changed,
        "无横扫（::after 无动画）": no_sweep,
        "无表面渐变（无 background-image）": no_gradient,
        "降级档是等价静态灰块且有体积": reduced_has_box and reduced_static,
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("灰块整体明暗呼吸 ✔（自身 opacity " + " → ".join(
        sorted({v for _, _, v in surfaces}, key=float)) + "）· 无横扫 ✔ · 无表面渐变 ✔"
        if verdict == PASS else
        "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    strip = F.build_strip(frames_dir, out_dir / "M-9-strip.png")
    return {
        "id": "M-9",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-9（按 decisions.md A-115 / A-117 定稿口径）",
        "checks": checks,
        "evidence": {
            "sizes": sorted({(b["width"], b["height"]) for sample in animated["samples"]
                             for b in sample["blocks"]}),
            "backgroundValues": sorted(bg_values),
            "opacityValues": sorted(op_values, key=float),
            "ownAnimationNames": own_animation,
            "afterAnimationNames": sweep,
            "ownBackgroundImages": gradients,
            "afterBackgroundImages": after_gradients,
            "reducedTierOpacity": reduced_opacity,
            "reducedTierBlocks": len(reduced_blocks),
            "reducedTierUsesClassLkSkeleton": sorted({
                b["cls"] for b in reduced_blocks}),
        },
        "animated": animated,
        "reduced": reduced,
        "strip": str(strip.name) if strip else None,
    }


# ─────────────────────────────────────────────────────────────────────────
# M-1 — the lamp: four stages + the card outline
# ─────────────────────────────────────────────────────────────────────────

#: The lamp's **cleanup** timer (workbench.js: ``LAMP_CLEAN_MS = 700``) removes
#: the three decoration layers from the DOM.  A screenshot of a 1440×900 page
#: takes longer than 700 ms, so the layers would be gone before the storyboard
#: is taken — the storyboard would then show an empty page at every frame
#: except the first.  The capture therefore **defers that one timer**; the CSS
#: animations themselves are untouched (they are addressed by ``setTime``),
#: and the "700 ms 后终态干净" clause is measured in a **separate run without
#: the deferral** (see :func:`run_m1`).
DEFER_CLEANUP_JS = r"""
(() => {
  if (window.__lkOriginalSetTimeout) return;
  window.__lkOriginalSetTimeout = window.setTimeout.bind(window);
  window.setTimeout = function (fn, delay) {
    const args = Array.prototype.slice.call(arguments, 2);
    let value = Number(delay) || 0;
    if (value >= 640 && value <= 760) value = 60000;   // the lamp cleanup
    return window.__lkOriginalSetTimeout(fn, value, ...args);
  };
})();
"""

LAMP_JS = r"""
() => {
  const pick = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      present: true,
      opacity: st.opacity,
      transform: st.transform,
      display: st.display,
      zIndex: st.zIndex,
      background: st.backgroundColor,
      backgroundImage: st.backgroundImage.slice(0, 90),
      pointerEvents: st.pointerEvents,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      animationName: st.animationName,
      cls: String(el.className || ""),
    };
  };
  /* the card that the ripple must **not** flatten */
  const card = document.querySelector("#middle-page .card, #middle-page .lk-card, .lk-card");
  let cardState = null;
  if (card) {
    const st = getComputedStyle(card);
    const rect = card.getBoundingClientRect();
    /* The **geometry** of the shadow, without its colours: the theme swap
       (590 ms) legitimately changes the card's colours, but the outline's
       shape must not change — 「只有底色在变」. */
    const shadowGeometry = st.boxShadow.replace(/rgba?\([^)]*\)/g, "C")
      .replace(/#[0-9a-f]+/gi, "C");
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    cardState = {
      cls: String(card.className || "").slice(0, 60),
      borderTopWidth: st.borderTopWidth,
      borderRadius: st.borderRadius,
      boxShadowGeometry: shadowGeometry,
      filter: st.filter,
      opacity: st.opacity,
      zIndex: st.zIndex,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      coveredBy: hit ? (hit.tagName + "." + String(hit.className || "").slice(0, 40)) : null,
      hitIsCard: !!(hit && (hit === card || card.contains(hit) || hit.contains(card))),
    };
  }
  return {
    theme: document.documentElement.getAttribute("data-theme"),
    lamp: pick(".lk-lamp"),
    lampGlow: pick(".lk-lamp__glow"),
    ripple: pick(".lk-ripple"),
    glow: pick(".lk-ripple-glow"),
    card: cardState,
    cardCount: document.querySelectorAll("#middle-page .card, #middle-page .lk-card").length,
  };
}
"""


def run_m1(playwright, base_url, ws, out_dir):
    """M-1 — the four stages of the lamp transition and the card outline."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-1"
    frames_dir.mkdir(parents=True, exist_ok=True)
    card_dir = out_dir / "M-1-cards"
    card_dir.mkdir(parents=True, exist_ok=True)
    times = (0, 90, 180, 330, 500, 700)

    def one_run(reduced, page_key="settings", defer_cleanup=True):
        browser, context, page = launch(playwright, reduced_motion=reduced)
        try:
            ctx = ctx_of(base_url, ws)
            if page_key == "settings":
                F.prepare_theme(page, ctx)
            else:
                # The **card** measurement needs real cards on the screen, so
                # the transition is started from the practice page — with the
                # product's own entry point (``window.lkTheme.transition``),
                # the very function the settings switch calls.
                F.prepare_view(page, ctx)
            if defer_cleanup:
                page.evaluate(DEFER_CLEANUP_JS)
            page.evaluate("() => window.__lkFrame.freeze()")
            if page_key == "settings":
                F.act_theme(page, ctx)
            else:
                page.evaluate("""() => {
                  window.lkTheme.transition("night");
                }""")
            page.wait_for_timeout(60)
            samples = []
            for t in times:
                page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
                page.wait_for_timeout(40)
                state = page.evaluate(LAMP_JS)
                name = f"{t:04d}.png"
                directory = frames_dir if page_key == "settings" else card_dir
                page.screenshot(path=str(directory / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, **state})
            return {"samples": samples}
        finally:
            context.close()
            browser.close()

    def terminal_run():
        """The same transition **without** the deferral: after 700 ms the
        three decoration layers must be gone from the document."""
        browser, context, page = launch(playwright)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_theme(page, ctx)
            F.act_theme(page, ctx)
            page.wait_for_timeout(1200)
            state = page.evaluate("""() => ({
              lamp: document.querySelectorAll(".lk-lamp").length,
              ripple: document.querySelectorAll(".lk-ripple").length,
              glow: document.querySelectorAll(".lk-ripple-glow").length,
              theme: document.documentElement.getAttribute("data-theme"),
            })""")
            return state
        finally:
            context.close()
            browser.close()

    animated = one_run(None)
    reduced = one_run("reduce")
    cards_run = one_run(None, "cards")
    terminal = terminal_run()

    stages = []
    for sample in animated["samples"]:
        lamp = sample.get("lamp") or {}
        ripple = sample.get("ripple") or {}
        glow = sample.get("glow") or {}
        lamp_glow = sample.get("lampGlow") or {}
        stages.append({
            "t": sample["t"],
            "lampPresent": bool(lamp.get("present")),
            "lampOpacity": lamp.get("opacity"),
            "lampTransform": lamp.get("transform"),
            "lampClass": lamp.get("cls"),
            "lampAnimation": lamp.get("animationName"),
            "lampGlowOpacity": lamp_glow.get("opacity"),
            "lampGlowAnimation": lamp_glow.get("animationName"),
            "rippleOpacity": ripple.get("opacity"),
            "rippleTransform": ripple.get("transform"),
            "rippleZIndex": ripple.get("zIndex"),
            "glowOpacity": glow.get("opacity"),
            "glowTransform": glow.get("transform"),
            "theme": sample.get("theme"),
            "card": sample.get("card"),
        })

    # ① 探出 → ② 点亮 → ③ 涟漪扩散 → ④ 收回
    lit = [s for s in stages if s["lampPresent"]
           and float(s["lampOpacity"] or 0) > 0]
    ripple_scale = [matrix_scale(s["rippleTransform"]) for s in stages
                    if s["rippleTransform"]]
    ripple_grew = len(ripple_scale) >= 2 and max(ripple_scale) > min(ripple_scale)
    themes = [s["theme"] for s in stages]
    swapped = any(themes[index] != themes[0] for index in range(len(themes)))
    ripple_below = all((s["rippleZIndex"] or "0") in ("0", "auto") for s in stages
                        if s["rippleTransform"] is not None)
    cleaned = not stages[-1]["lampPresent"] and not stages[-1]["rippleTransform"]
    lamp_anim = sorted({s["lampAnimation"] for s in stages if s["lampAnimation"]})
    lamp_glow_anim = sorted({s["lampGlowAnimation"] for s in stages
                             if s["lampGlowAnimation"]})
    lamp_glow_lit = [s for s in stages
                     if s["lampGlowOpacity"] is not None
                     and float(s["lampGlowOpacity"] or 0) > 0]
    # ④ 收回 — the lamp has to **retract** (the design's 590–700 ms stage).
    # The keyframes exist (``@keyframes lk-lamp-retract`` + ``.lk-lamp.is-in``)
    # ⇒ the measurement is: at the last frame the lamp is either gone from
    # the document or visibly retracting (its opacity below 1 / its
    # animation is the retract).
    last = stages[-1]
    retract_seen = (
        "lk-lamp-retract" in (last["lampAnimation"] or "")
        or (last["lampOpacity"] is not None
            and float(last["lampOpacity"]) < 0.999))
    lamp_gone_at_end = not last["lampPresent"]
    clean_terminal = (terminal.get("lamp") == 0 and terminal.get("ripple") == 0
                      and terminal.get("glow") == 0)

    # -- the card outline, measured on a page that really has cards -------
    card_samples = cards_run["samples"]
    card_states = [s["card"] for s in card_samples if s["card"]]
    outline_fields = ("borderTopWidth", "borderRadius", "boxShadowGeometry",
                      "filter", "opacity", "zIndex", "width", "height")
    # The **theme swap** (590 ms) legitimately changes the card's own tokens
    # (the shadow of the night paper is a different token).  The criterion is
    # about the **ripple** flattening the card, so the comparison is split at
    # the swap: before the swap the outline must be untouched, after it the
    # only allowed change is the theme's own shadow token.
    themes = [s.get("theme") for s in card_samples]
    swap_index = next((index for index, theme in enumerate(themes)
                       if theme != themes[0]), len(themes))
    outline_changed = False
    outline_detail = []
    post_swap_detail = []
    if card_states:
        first_card = card_states[0]
        for index, card in enumerate(card_states):
            changed = {field: [first_card[field], card[field]]
                       for field in outline_fields
                       if card[field] != first_card[field]}
            if not changed:
                continue
            if index < swap_index:
                outline_changed = True
                outline_detail.append({"index": index, "changed": changed})
            else:
                post_swap_detail.append({"index": index, "changed": changed})
    card_present = bool(card_states)
    card_ripple_ran = any(
        (s.get("ripple") or {}).get("transform") for s in card_samples)
    card_not_covered = all(s["card"].get("hitIsCard") for s in card_samples
                            if s.get("card"))

    checks = {
        "① 探出：灯层出现且不透明度 > 0": bool(lit),
        "② 点亮：灯罩的暖光层有自己的点亮动画": any(
            "light-up" in name for name in lamp_glow_anim) and bool(lamp_glow_lit),
        "③ 涟漪扩散：涟漪层的 scale 随时间变大": ripple_grew,
        "④ 收回：灯层在 590–700ms 之间有收回动画": retract_seen,
        "700ms 后终态干净（三层已从 DOM 移除）": clean_terminal,
        "转场中主题已切换（皮肤在转体内换）": swapped,
        "涟漪期间卡片轮廓未被压平": card_present and card_ripple_ran
        and not outline_changed,
        "涟漪期间卡片没有被盖住（命中测试仍是卡片）": card_not_covered,
        "涟漪层在内容层之下（z-index = base）": ripple_below,
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("四段齐备（探出 → 点亮 → 涟漪扩散 → 收回）· 卡片轮廓全程不变"
              if verdict == PASS else
              "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    strip = F.build_strip(frames_dir, out_dir / "M-1-strip.png")
    card_strip = F.build_strip(card_dir, out_dir / "M-1-cards-strip.png")
    return {
        "id": "M-1",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-1",
        "checks": checks,
        "stages": stages,
        "cardMeasurement": {
            "cardCountOnPage": card_samples[0].get("cardCount") if card_samples else 0,
            "cardClass": card_states[0]["cls"] if card_states else None,
            "outlineChanged": outline_changed,
            "outlineChanges": outline_detail,
            "themeSwapFrameIndex": swap_index,
            "changesAfterTheThemeSwap": post_swap_detail,
            "cardPerFrame": [
                {"t": s["t"], "borderTopWidth": (s["card"] or {}).get("borderTopWidth"),
                 "borderRadius": (s["card"] or {}).get("borderRadius"),
                 "boxShadowGeometry": (s["card"] or {}).get("boxShadowGeometry"),
                 "opacity": (s["card"] or {}).get("opacity"),
                 "width": (s["card"] or {}).get("width"),
                 "height": (s["card"] or {}).get("height"),
                 "coveredBy": (s["card"] or {}).get("coveredBy"),
                 "hitIsCard": (s["card"] or {}).get("hitIsCard"),
                 "rippleScale": matrix_scale((s.get("ripple") or {}).get("transform"))}
                for s in card_samples],
            "rippleRanOnThisPage": card_ripple_ran,
        },
        "animated": animated,
        "reduced": reduced,
        "cardsRun": cards_run,
        "terminalAfter700ms": terminal,
        "strip": str(strip.name) if strip else None,
        "cardsStrip": str(card_strip.name) if card_strip else None,
    }


# ─────────────────────────────────────────────────────────────────────────
# M-2 / M-3 — the celebration: number rolling, progress band, the CTA
# ─────────────────────────────────────────────────────────────────────────

CELEBRATION_JS = r"""
() => {
  const list = (selector) => Array.from(document.querySelectorAll(selector)).slice(0, 12);
  const figures = list(".lk-stat__value, [data-lk-value]").map((el) => ({
    value: el.getAttribute("data-lk-value"),
    text: (el.textContent || "").trim(),
  }));
  const fills = list(".lk-progress__fill, .lk-progress-fill").map((el) => {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      cls: String(el.className || ""),
      transform: st.transform,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      animationName: st.animationName,
      opacity: st.opacity,
    };
  });
  const bands = list(".lk-progress").map((el) => {
    const st = getComputedStyle(el);
    return {cls: String(el.className || ""),
            width: Math.round(el.getBoundingClientRect().width),
            height: Math.round(el.getBoundingClientRect().height),
            animationName: st.animationName};
  });
  const burst = list(".lk-celebrate-burst").map((el) => {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {opacity: st.opacity, transform: st.transform, zIndex: st.zIndex,
            pointerEvents: st.pointerEvents,
            width: Math.round(rect.width), height: Math.round(rect.height),
            rect: {x: Math.round(rect.left), y: Math.round(rect.top),
                   w: Math.round(rect.width), h: Math.round(rect.height)}};
  });
  const confetti = list(".lk-confetti").map((el) => {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {opacity: st.opacity, transform: st.transform, zIndex: st.zIndex,
            pointerEvents: st.pointerEvents,
            width: Math.round(rect.width), height: Math.round(rect.height),
            rect: {x: Math.round(rect.left), y: Math.round(rect.top),
                   w: Math.round(rect.width), h: Math.round(rect.height)}};
  });
  /* the primary action of the completion surface */
  const cta = document.querySelector("#paper-completion button, #paper-completion .primary,"
      + " #paper-completion .btn-primary, #paper-completion a[href]");
  let ctaState = null;
  if (cta) {
    const st = getComputedStyle(cta);
    const rect = cta.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    /* how many visible decoration pieces overlap the CTA's box */
    const overlaps = burst.concat(confetti).filter((piece) => {
      if (parseFloat(piece.opacity || "0") <= 0.01) return false;
      return !(piece.rect.x + piece.rect.w < rect.left
               || piece.rect.x > rect.right
               || piece.rect.y + piece.rect.h < rect.top
               || piece.rect.y > rect.bottom);
    }).length;
    ctaState = {
      text: (cta.textContent || "").trim().slice(0, 20),
      cls: String(cta.className || ""),
      zIndex: st.zIndex,
      pointerEvents: st.pointerEvents,
      width: Math.round(rect.width), height: Math.round(rect.height),
      hitIsCta: !!(hit && (hit === cta || cta.contains(hit) || hit.contains(cta))),
      hitTag: hit ? (hit.tagName + "." + String(hit.className || "").slice(0, 40)) : null,
      visibleDecorationsOverlapping: overlaps,
    };
  }
  return {
    theme: document.documentElement.getAttribute("data-theme"),
    figures: figures,
    fills: fills,
    bands: bands,
    burst: burst,
    confetti: confetti,
    confettiCount: confetti.length,
    burstCount: burst.length,
    cta: ctaState,
    stats: (document.getElementById("paper-completion-stats") || {}).textContent || "",
  };
}
"""


def poll_figures(page, milliseconds=700):
    """Watch the completion figures while the ticker rolls them.

    The number rolling is a **rAF text writer** (``window.lkTicker.set``), not
    a CSS animation — ``frames.py``'s ``setTime`` cannot address it.  The
    proof that it *rolls* is therefore that the text goes through intermediate
    values, and that is what this poll records.
    """
    samples = []
    elapsed = 0
    step = 16
    while elapsed <= milliseconds:
        values = page.evaluate("""() => Array.from(
            document.querySelectorAll(".lk-stat__value, [data-lk-value]")
          ).slice(0, 8).map((el) => ({
            target: el.getAttribute("data-lk-value"),
            text: (el.textContent || "").trim(),
          }))""")
        samples.append({"t": elapsed, "values": values})
        page.wait_for_timeout(step)
        elapsed += step
    return samples


def run_celebration(playwright, base_url, ws, out_dir, motion_id, plan):
    """M-2 (ordinary tier) / M-3 (milestone tier) — the extra measurements."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / motion_id
    frames_dir.mkdir(parents=True, exist_ok=True)
    times = F.MOTIONS[motion_id]["frames_ms"]

    def one_run(reduced):
        browser, context, page = launch(playwright, reduced_motion=reduced)
        try:
            ctx = ctx_of(base_url, ws, plan=plan, motion_id=motion_id)
            F.prepare_celebration(page, ctx)
            if not reduced:
                page.evaluate("() => window.__lkFrame.freeze()")
            F.act_celebration(page, ctx)
            page.wait_for_selector("#paper-completion", state="attached",
                                   timeout=20000)
            roll = poll_figures(page, 500)
            samples = []
            for t in times:
                page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
                page.wait_for_timeout(40)
                state = page.evaluate(CELEBRATION_JS)
                name = f"{t:04d}.png"
                page.screenshot(path=str(frames_dir / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, **state})
            page.evaluate("() => window.__lkFrame.finish()")
            page.wait_for_timeout(200)
            terminal = page.evaluate(CELEBRATION_JS)
            return {"samples": samples, "terminal": terminal, "roll": roll}
        finally:
            context.close()
            browser.close()

    animated = one_run(None)
    reduced = one_run("reduce")
    strip = F.build_strip(frames_dir, out_dir / f"{motion_id}-strip.png")

    # -- the number rolling ------------------------------------------------
    roll = animated["roll"]
    intermediate = 0
    for sample in roll:
        for value in sample["values"]:
            text = value["text"]
            target = value["target"]
            if target and text != target and text.isdigit():
                intermediate += 1
    # -- the progress band --------------------------------------------------
    fills = [f for sample in animated["samples"] for f in sample["fills"]]
    fill_scales = [matrix_scale(f["transform"]) for f in fills]
    terminal_fill = [matrix_scale(f["transform"]) for f in animated["terminal"]["fills"]]
    reduced_fill = [matrix_scale(f["transform"]) for f in reduced["terminal"]["fills"]]
    band_grew = bool(fill_scales) and min(fill_scales) < 0.999
    band_full = bool(terminal_fill) and all(abs(v - 1.0) < 0.01 for v in terminal_fill)
    band_same = (len(terminal_fill) == len(reduced_fill)) and all(
        abs(a - b) < 0.01 for a, b in zip(terminal_fill, reduced_fill))
    # -- the confetti / the CTA --------------------------------------------
    confetti_frames = [s["confettiCount"] for s in animated["samples"]]
    burst_frames = [s["burstCount"] for s in animated["samples"]]
    cta_samples = [s["cta"] for s in animated["samples"] if s.get("cta")]
    cta_hit = all(c.get("hitIsCta") for c in cta_samples) if cta_samples else None
    cta_overlaps = [c.get("visibleDecorationsOverlapping") for c in cta_samples]
    decoration_pointer_events = sorted({
        c.get("pointerEvents") for s in animated["samples"]
        for c in (s["burst"] + s["confetti"]) if c.get("pointerEvents")})

    return {
        "id": motion_id,
        "animated": animated,
        "reduced": reduced,
        "strip": str(strip.name) if strip else None,
        "derived": {
            "intermediateFigureValues": intermediate,
            "figureRollSamples": len(roll),
            "progressFillScales": fill_scales,
            "progressFillTerminalAnimated": terminal_fill,
            "progressFillTerminalReduced": reduced_fill,
            "bandGrewFromZero": band_grew,
            "bandFullAtTerminal": band_full,
            "bandTerminalEqualInBothTiers": band_same,
            "confettiPerFrame": confetti_frames,
            "burstPerFrame": burst_frames,
            "ctaPerFrame": cta_samples,
            "ctaHitTestPassed": cta_hit,
            "ctaVisibleDecorationsOverlappingPerFrame": cta_overlaps,
            "decorationPointerEvents": decoration_pointer_events,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
# M-4 / M-6 — the streak, driven in the **product's own order**
# ─────────────────────────────────────────────────────────────────────────

STREAK_STATE_JS = r"""
() => {
  const counter = document.querySelector("#lk-probe-streak .lk-streak");
  const banner = document.querySelector("#lk-probe-streak .lk-combo-banner");
  const count = document.querySelector("#lk-probe-streak .lk-combo-banner__count");
  const ticker = document.querySelector("#lk-probe-streak .lk-ticker");
  const flames = Array.from(document.querySelectorAll("#lk-probe-streak .lk-flame")).map((el) => {
    const on = el.querySelector(".lk-flame-on");
    const st = getComputedStyle(el);
    const onStyle = on ? getComputedStyle(on) : null;
    return {
      lit: el.classList.contains("is-lit"),
      opacity: st.opacity,
      transform: st.transform,
      onOpacity: onStyle ? onStyle.opacity : null,
      delay: el.style.animationDelay || "",
    };
  });
  /* the ancestors of the counter: a screen-wide shake would move them.
     The walk starts **above** the counter — the counter itself is the thing
     that is allowed to move (by ≤4px). */
  const ancestors = [];
  let node = counter ? counter.parentElement : null;
  while (node && node !== document.documentElement) {
    const st = getComputedStyle(node);
    const m = st.transform.match(/matrix\(1, 0, 0, 1, ([-\d.]+),/);
    ancestors.push({
      tag: node.tagName.toLowerCase(),
      cls: String(node.className || "").slice(0, 40),
      shift: m ? Math.round(parseFloat(m[1]) * 100) / 100 : 0,
    });
    node = node.parentElement;
  }
  const bodyStyle = getComputedStyle(document.body);
  const htmlStyle = getComputedStyle(document.documentElement);
  const bodyM = bodyStyle.transform.match(/matrix\(1, 0, 0, 1, ([-\d.]+),/);
  const htmlM = htmlStyle.transform.match(/matrix\(1, 0, 0, 1, ([-\d.]+),/);
  return {
    counterClass: counter ? String(counter.className || "") : null,
    counterAnimation: counter ? getComputedStyle(counter).animationName : null,
    counterTransform: counter ? getComputedStyle(counter).transform : null,
    counterShift: counter ? (function () {
      const m = getComputedStyle(counter).transform.match(/matrix\(1, 0, 0, 1, ([-\d.]+),/);
      return m ? Math.round(parseFloat(m[1]) * 100) / 100 : 0;
    })() : null,
    counterTier: counter ? counter.getAttribute("data-lk-streak-tier") : null,
    ancestors: ancestors,
    bodyShift: bodyM ? Math.round(parseFloat(bodyM[1]) * 100) / 100 : 0,
    htmlShift: htmlM ? Math.round(parseFloat(htmlM[1]) * 100) / 100 : 0,
    tickerText: ticker ? (ticker.textContent || "").trim() : null,
    bannerClass: banner ? String(banner.className || "") : null,
    bannerOpacity: banner ? getComputedStyle(banner).opacity : null,
    bannerAnimation: banner ? getComputedStyle(banner).animationName : null,
    bannerCount: banner ? banner.querySelectorAll(".lk-combo-banner__count").length : 0,
    bannerText: count ? (count.textContent || "").trim() : null,
    bannerCountText: banner ? (banner.textContent || "").trim() : null,
    flames: flames,
    litFlames: flames.filter((f) => f.lit).length,
  };
}
"""


def streak_html_js(count):
    """The product's own call order: **render first, apply afterwards**.

    ``paper-practice.js:1141`` and ``practice-flow.js:1697`` both do
    ``renderCurrent()`` → ``streak.apply(streakLanded)``.  ``frames.py``'s
    trigger does the opposite, which wipes the ``is-on`` class that
    ``showBanner()`` has just added.
    """
    return """
(async (count) => {
  const streak = window.__lkProbeStreak;
  const host = document.getElementById("lk-probe-streak");
  for (let i = 0; i < count; i += 1) {
    const landed = streak.judge(true);
    host.innerHTML = streak.html();
    streak.apply(landed);
    await new Promise((r) => setTimeout(r, 60));
  }
})(%d)
""" % count


def run_streak_motions(playwright, base_url, ws, out_dir):
    """M-4 (the banner) and M-6 (the flame clusters), product order."""
    out_dir = Path(out_dir)
    results = {}

    for motion_id, times, count in (("M-4", (0, 100, 250, 450, 700), 5),
                                     ("M-4-10", (0, 100, 250, 450, 700), 10),
                                     ("M-6", (0, 200, 500), 5)):
        frames_dir = out_dir / motion_id
        frames_dir.mkdir(parents=True, exist_ok=True)
        browser, context, page = launch(playwright)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_streak(page, ctx)
            page.evaluate(streak_html_js(count))
            page.wait_for_timeout(200)
            page.evaluate("() => window.__lkFrame.freeze()")
            samples = []
            for t in times:
                page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
                page.wait_for_timeout(40)
                state = page.evaluate(STREAK_STATE_JS)
                name = f"{t:04d}.png"
                page.screenshot(path=str(frames_dir / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, **state})
            page.evaluate("() => window.__lkFrame.finish()")
            page.wait_for_timeout(300)
            terminal = page.evaluate(STREAK_STATE_JS)
            strip = F.build_strip(frames_dir, out_dir / f"{motion_id}-strip.png")
            results[motion_id] = {
                "count": count,
                "samples": samples,
                "terminal": terminal,
                "strip": str(strip.name) if strip else None,
            }
        finally:
            context.close()
            browser.close()

    # ---- M-4 ------------------------------------------------------------
    m4 = results["M-4"]
    m4b = results["M-4-10"]
    on_frames = [s for s in m4["samples"] if s["bannerClass"] and "is-on" in s["bannerClass"]]
    visible = [s for s in m4["samples"]
               if s["bannerOpacity"] is not None and float(s["bannerOpacity"]) > 0]
    single = all(s["bannerCount"] == 1 for s in m4["samples"])
    parameterized = (m4["terminal"]["bannerText"] == "5"
                     and m4b["terminal"]["bannerText"] == "10")
    left = [s for s in m4["samples"] if float(s["bannerOpacity"] or 0) == 0
            and s["t"] > 0]
    m4_checks = {
        "横幅出现（is-on 且不透明度 > 0）": bool(on_frames) and bool(visible),
        "横幅只有一份": single,
        "数字是参数化输入的结果（5 / 10）": parameterized,
        "退场（末帧不透明度回到 0）": bool(left),
    }
    m4_verdict = PASS if all(m4_checks.values()) else FAIL

    # ---- M-6 ------------------------------------------------------------
    m6 = results["M-6"]
    lit = [s["litFlames"] for s in m6["samples"]]
    # The ignition animates the **cluster** (``.lk-flame``), not the yellow
    # layer (``.lk-flame-on`` carries the static opacity rule).
    opacities = sorted({f["opacity"] for s in m6["samples"] for f in s["flames"]
                         if f["opacity"] is not None}, key=float)
    per_frame_opacity = [[f["opacity"] for f in s["flames"]] for s in m6["samples"]]
    delays = sorted({f["delay"] for s in m6["samples"] for f in s["flames"]
                     if f["delay"]})
    m6_checks = {
        "火苗簇存在（5 簇）": any(s["litFlames"] == 5 for s in m6["samples"]),
        "火苗逐簇点亮（同一帧内各簇透明度不同）":
            any(len(set(frame)) > 1 for frame in per_frame_opacity),
        "错峰写在 animation-delay 上（80ms 一档）": any(
            "80ms" in d for d in delays),
    }
    m6_verdict = PASS if all(m6_checks.values()) else FAIL

    return {
        "M-4": {
            "id": "M-4", "verdict": m4_verdict,
            "detail": ("横幅出现 → 数字替换 → 退场，且横幅只有一份、数字是参数"
                       if m4_verdict == PASS else
                       "；".join(n for n, ok in m4_checks.items() if not ok) + " 不成立"),
            "criterion": "acceptance.md §2 M-4",
            "checks": m4_checks,
            "evidence": {
                "bannerOpacityPerFrame": [s["bannerOpacity"] for s in m4["samples"]],
                "bannerClassPerFrame": [s["bannerClass"] for s in m4["samples"]],
                "bannerText5": m4["terminal"]["bannerText"],
                "bannerText10": m4b["terminal"]["bannerText"],
                "bannerElementsPerFrame": [s["bannerCount"] for s in m4["samples"]],
                "note": "驱动顺序 = 产品自身的顺序（先重绘、后 apply）",
            },
            "detail_raw": results,
        },
        "M-6": {
            "id": "M-6", "verdict": m6_verdict,
            "detail": ("火苗逐簇点亮（80ms 错峰）"
                       if m6_verdict == PASS else
                       "；".join(n for n, ok in m6_checks.items() if not ok) + " 不成立"),
            "criterion": "acceptance.md §2 M-6",
            "checks": m6_checks,
            "evidence": {
                "litFlamesPerFrame": lit,
                "flameClusterOpacities": opacities,
                "flameClusterOpacitiesPerFrame": per_frame_opacity,
                "animationDelays": delays,
            },
            "detail_raw": results,
        },
    }


def seed_recent_days(pool_path, days=13):
    """Put one attempt on each of the last ``days`` days of the **copy**.

    Why: the load bars of the records page are the **last 14 days**; the
    seed module writes its rows with fixed timestamps in 2026-03, so in this
    run only one of the fourteen days carries data ⇒ the **stagger** of the
    bars (one column per day, 24 ms apart) cannot be observed.  This writes
    one extra attempt per day into the **isolated copy** only — the same
    thing ``seed.py`` does, with the same table shape, and never into the
    real pool.

    Returns the list of the days it touched.
    """
    import datetime
    import sqlite3

    path = Path(pool_path).resolve()
    connection = sqlite3.connect(str(path), timeout=30.0)
    try:
        problems = connection.execute(
            "SELECT problem_id FROM problems "
            "WHERE deleted_at IS NULL ORDER BY problem_id").fetchall()
        if not problems:
            return []
        today = datetime.date.today()
        touched = []
        for offset in range(days, 0, -1):
            day = today - datetime.timedelta(days=offset)
            stamp = f"{day.isoformat()} 09:15:00"
            cursor = connection.execute(
                "INSERT INTO problem_attempts "
                "(problem_id, status, note, answer_text, verdict, choices, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (problems[offset % len(problems)][0], "answered", None,
                 "6500", 1, None, stamp))
            connection.execute(
                "INSERT INTO feedback_events "
                "(item_type, item_id, rating, note, created_at, attempt_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("problem", problems[offset % len(problems)][0], 4, None,
                 stamp, cursor.lastrowid))
            touched.append(day.isoformat())
        connection.commit()
        return touched
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────────────────────
# M-5 — the three tiers of the streak counter
# ─────────────────────────────────────────────────────────────────────────

TIER_STATE_JS = r"""
() => {
  const counter = document.querySelector("#lk-probe-streak .lk-streak");
  if (!counter) return null;
  const st = getComputedStyle(counter);
  const before = getComputedStyle(counter, "::before");
  const flames = Array.from(counter.querySelectorAll(".lk-flame-on"))
    .map((el) => getComputedStyle(el));
  return {
    cls: String(counter.className || ""),
    tier: counter.getAttribute("data-lk-streak-tier"),
    text: (counter.textContent || "").trim(),
    color: st.color,
    background: st.backgroundColor,
    backgroundImage: st.backgroundImage.slice(0, 160),
    paddingLeft: st.paddingLeft,
    paddingRight: st.paddingRight,
    beforeContent: before.content,
    beforeBackground: before.backgroundColor,
    beforeBackgroundImage: before.backgroundImage.slice(0, 160),
    beforeHeight: before.height,
    beforeWidth: before.width,
    flameColour: flames.length ? flames[0].backgroundColor : null,
    flameImage: flames.length ? flames[0].backgroundImage.slice(0, 160) : null,
    flameCount: flames.length,
  };
}
"""


def run_m5(playwright, base_url, ws, out_dir):
    """M-5 — the counter in its three tiers (grey / yellow / yellow→blue)."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-5"
    frames_dir.mkdir(parents=True, exist_ok=True)
    tiers = []
    for count in (0, 5, 31):
        browser, context, page = launch(playwright)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_streak(page, ctx)
            page.evaluate(streak_html_js(count))
            page.wait_for_timeout(400)
            state = page.evaluate(TIER_STATE_JS)
            if state:
                state["count"] = count
                tiers.append(state)
                page.screenshot(path=str(frames_dir / f"{count:02d}.png"),
                                caret="hide", scale="css")
        finally:
            context.close()
            browser.close()
    classes = {tier["cls"] for tier in tiers}
    backgrounds = {tier["background"] for tier in tiers}
    gradients = {tier["backgroundImage"] for tier in tiers}
    bars = {tier["beforeBackground"] for tier in tiers}
    bar_images = {tier["beforeBackgroundImage"] for tier in tiers}
    flame_colours = {tier["flameColour"] for tier in tiers}
    flame_images = {tier["flameImage"] for tier in tiers}
    paddings = {tier["paddingLeft"] for tier in tiers}
    # the tier must not be carried by the text: the **geometry/colour**
    # channels have to differ between the three tiers
    colour_channels = len(bars) + len(bar_images) + len(flame_colours)         + len(flame_images)
    hot = next((tier for tier in tiers if tier["cls"].endswith("is-hot")), None)
    hot_is_gradient = bool(hot) and (
        "gradient" in (hot["beforeBackgroundImage"] or "")
        or "gradient" in (hot["flameImage"] or ""))
    checks = {
        "三档采到": len(tiers) == 3,
        "三档的类名不同": len(classes) == 3,
        "档位色（色条 / 火苗）逐档不同": colour_channels >= 3,
        "高档是渐变（黄→蓝）": hot_is_gradient,
        "不靠文字（文字之外还有颜色与几何通道）":
            len(classes) == 3
            and (len(bars) >= 2 or len(bar_images) >= 2
                 or len(flame_colours) >= 2 or len(flame_images) >= 2
                 or len(paddings) >= 2),
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("三档靠颜色 / 几何区分（灰 → 黄 → 黄蓝渐变），不靠文字"
              if verdict == PASS else
              "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    return {
        "id": "M-5",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-5",
        "checks": checks,
        "tiers": tiers,
        "framesDir": str(frames_dir),
    }


# ─────────────────────────────────────────────────────────────────────────
# M-10 — the data layer: the load bars and the activity heat map
# ─────────────────────────────────────────────────────────────────────────

DATA_JS = r"""
() => {
  const bars = Array.from(
    document.querySelectorAll(".workload-bars .bar-fill")).map((el) => {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const col = el.closest(".bar-col");
    return {
      animationName: st.animationName,
      animationDelay: st.animationDelay,
      transform: st.transform,
      height: Math.round(rect.height),
      width: Math.round(rect.width),
      inlineHeight: el.style.height || null,
      inlineDelay: el.style.animationDelay || null,
      barDate: col && col.dataset ? col.dataset.barDate || null : null,
    };
  });
  const cells = Array.from(
    document.querySelectorAll(".record-activity-day")).map((el) => {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const match = String(el.className || "").match(/level-(\d)/);
    return {
      cls: String(el.className || "").slice(0, 40),
      level: match ? match[1] : null,
      height: Math.round(rect.height),
      background: st.backgroundColor,
      animationName: st.animationName,
      transform: st.transform,
      inlineHeight: el.style.height || null,
    };
  });
  return {
    bars: bars,
    cells: cells,
    barCount: bars.length,
    cellCount: cells.length,
    levelCounts: cells.reduce((acc, cell) => {
      acc[cell.level] = (acc[cell.level] || 0) + 1;
      return acc;
    }, {}),
    heightsByLevel: cells.reduce((acc, cell) => {
      const key = cell.level;
      if (!acc[key]) acc[key] = [];
      if (!acc[key].includes(cell.height)) acc[key].push(cell.height);
      return acc;
    }, {}),
    coloursByLevel: cells.reduce((acc, cell) => {
      const key = cell.level;
      if (!acc[key]) acc[key] = [];
      if (!acc[key].includes(cell.background)) acc[key].push(cell.background);
      return acc;
    }, {}),
  };
}
"""


def run_m10(playwright, base_url, ws, out_dir):
    """M-10 — the load bars grow (staggered) and the heat map encodes twice."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-10"
    frames_dir.mkdir(parents=True, exist_ok=True)
    times = (0, 120, 240, 480)

    def one_run(reduced):
        browser, context, page = launch(playwright, reduced_motion=reduced)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_records(page, ctx)
            samples = []
            for t in times:
                page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
                page.wait_for_timeout(40)
                state = page.evaluate(DATA_JS)
                name = f"{t:04d}.png"
                page.screenshot(path=str(frames_dir / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, **state})
            page.evaluate("() => window.__lkFrame.finish()")
            page.wait_for_timeout(200)
            terminal = page.evaluate(DATA_JS)
            return {"samples": samples, "terminal": terminal}
        finally:
            context.close()
            browser.close()

    animated = one_run(None)
    reduced = one_run("reduce")

    # -- the load bars ----------------------------------------------------
    first = animated["samples"][0]["bars"]
    scales_per_frame = [[matrix_scale_y(bar["transform"]) for bar in sample["bars"]]
                        for sample in animated["samples"]]
    grew = bool(scales_per_frame[0]) and min(scales_per_frame[0]) < 0.05
    # the **terminal** state (every animation finished) must be full: the
    # 24 ms stagger pushes the last column's end past the last frame time.
    terminal_scales = [matrix_scale_y(bar["transform"])
                       for bar in animated["terminal"]["bars"]]
    full = bool(terminal_scales) and all(
        abs(scale - 1.0) < 0.01 for scale in terminal_scales)
    delays = sorted({bar["inlineDelay"] for bar in first if bar["inlineDelay"]})
    staggered = len(delays) >= 2
    # the stagger must be *visible*: at an intermediate frame the columns are
    # at different heights
    mid = scales_per_frame[1] if len(scales_per_frame) > 1 else []
    stagger_visible = len(set(mid)) >= 2
    terminal_bars = animated["terminal"]["bars"]
    reduced_bars = reduced["terminal"]["bars"]
    bars_terminal_equal = (
        len(terminal_bars) == len(reduced_bars)
        and all(abs(matrix_scale_y(a["transform"]) - matrix_scale_y(b["transform"])) < 0.01
                and a["height"] == b["height"]
                for a, b in zip(terminal_bars, reduced_bars)))

    # -- the heat map -----------------------------------------------------
    cells = animated["terminal"]["cells"]
    levels = sorted({cell["level"] for cell in cells if cell["level"] is not None})
    colours = animated["terminal"]["coloursByLevel"]
    heights = animated["terminal"]["heightsByLevel"]
    colour_encoded = len({tuple(v) for v in colours.values()}) >= 2
    height_encoded = len({tuple(sorted(v)) for v in heights.values()}) >= 2
    cell_animations = sorted({cell["animationName"] for cell in cells
                               if cell["animationName"]})
    cells_move = any(
        abs(matrix_scale(cell["transform"]) - 1.0) > 0.001
        for sample in animated["samples"] for cell in sample["cells"])
    cell_height_over_time = len({
        (sample["t"], cell["height"]) for sample in animated["samples"]
        for cell in sample["cells"]}) > len(cells)
    terminal_cells = animated["terminal"]["cells"]
    reduced_cells = reduced["terminal"]["cells"]
    cells_terminal_equal = (
        len(terminal_cells) == len(reduced_cells)
        and all(a["height"] == b["height"]
                and a["background"] == b["background"]
                for a, b in zip(terminal_cells, reduced_cells)))

    checks = {
        "负荷柱从 0 生长": grew,
        "负荷柱终态满格（scaleY 1）": full,
        "逐柱错峰（行内 animation-delay 多个取值）": staggered,
        "错峰可见（同一帧内各柱高度不同）": stagger_visible,
        "日历格颜色按强度编码（多档不同底色）": colour_encoded,
        "日历格高度按强度编码（多档不同高度）": height_encoded,
        "日历格按强度扩散（格子自身有生长动画）":
            bool(cell_animations) and (cells_move or cell_height_over_time),
        "负荷柱终态两档一致": bars_terminal_equal,
        "日历格终态两档一致": cells_terminal_equal,
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("负荷柱从 0 生长并逐柱错峰 24ms；日历格颜色 + 高度双编码"
              if verdict == PASS else
              "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    strip = F.build_strip(frames_dir, out_dir / "M-10-strip.png")
    return {
        "id": "M-10",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-10",
        "checks": checks,
        "evidence": {
            "barCount": animated["terminal"]["barCount"],
            "barScalesPerFrame": scales_per_frame,
            "barInlineDelays": delays,
            "cellCount": animated["terminal"]["cellCount"],
            "levelCounts": animated["terminal"]["levelCounts"],
            "coloursByLevel": colours,
            "heightsByLevel": heights,
            "cellAnimationNames": cell_animations,
            "cellsMoveDuringTheCapture": cells_move,
            "cellHeightChangesOverTime": cell_height_over_time,
        },
        "animated": animated,
        "reduced": reduced,
        "strip": str(strip.name) if strip else None,
    }


# ─────────────────────────────────────────────────────────────────────────
# M-11 — the break of a streak (the negative feedback)
# ─────────────────────────────────────────────────────────────────────────


def run_m11(playwright, base_url, ws, out_dir):
    """M-11 — a streak of five breaks: the negative feedback must not be silent."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-11"
    frames_dir.mkdir(parents=True, exist_ok=True)
    times = (0, 80, 200, 400)

    def one_run(reduced, mode):
        """``mode`` = ``frames`` (the storyboard) or ``dense`` (the poll)."""
        browser, context, page = launch(playwright, reduced_motion=reduced)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_streak(page, ctx)
            # five correct answers in a row (product order: render, then apply)
            page.evaluate(streak_html_js(5))
            page.wait_for_timeout(400)
            before = page.evaluate(STREAK_STATE_JS)
            break_js = page.evaluate("""() => {
              const streak = window.__lkProbeStreak;
              const host = document.getElementById("lk-probe-streak");
              const landed = streak.judge(false);
              host.innerHTML = streak.html();
              streak.apply(landed);
            }""")
            if mode == "dense":
                # A **dense** poll of the two things that move on timers
                # (the flame extinguish, 40 ms apart) and on the clock
                # (the nudge): the four storyboard frames are too coarse.
                dense = []
                for index in range(30):
                    page.wait_for_timeout(10)
                    dense.append(page.evaluate(STREAK_STATE_JS))
                return {"before": before, "dense": dense}
            samples = []
            elapsed = 0
            for t in times:
                wait = max(0, t - elapsed)
                page.wait_for_timeout(wait)
                elapsed = t
                state = page.evaluate(STREAK_STATE_JS)
                name = f"{t:04d}.png"
                page.screenshot(path=str(frames_dir / name),
                                animations="allow", caret="hide", scale="css")
                samples.append({"t": t, "file": name, **state})
            page.wait_for_timeout(600)
            terminal = page.evaluate(STREAK_STATE_JS)
            return {"before": before, "samples": samples, "terminal": terminal}
        finally:
            context.close()
            browser.close()

    animated = one_run(None, "frames")
    reduced = one_run("reduce", "frames")
    dense = one_run(None, "dense")

    samples = animated["samples"]
    terminal = animated["terminal"]
    # ① the negative feedback is there at all
    nudged = any("lk-error-nudge" in (s["counterClass"] or "") for s in samples)
    anim_name = next((s["counterAnimation"] for s in samples
                      if s.get("counterAnimation") not in (None, "none")), None)
    # ② the shake stays inside ±4 px and never becomes a screen shake
    swings = [abs(s["counterShift"] or 0) for s in samples]
    dense_shifts = [abs(s["counterShift"] or 0) for s in dense["dense"]]
    worst_counter = max(swings + dense_shifts) if swings else 0
    ancestor_shifts = [abs(a["shift"]) for s in samples for a in s["ancestors"]]
    ancestor_shifts += [abs(a["shift"]) for s in dense["dense"] for a in s["ancestors"]]
    worst_ancestor = max(ancestor_shifts) if ancestor_shifts else 0
    worst_page = max([abs(s["bodyShift"] or 0) for s in samples]
                     + [abs(s["htmlShift"] or 0) for s in samples]
                     + [abs(s["bodyShift"] or 0) for s in dense["dense"]]
                     + [abs(s["htmlShift"] or 0) for s in dense["dense"]])
    # ③ the counter goes back to zero
    zeroed = (terminal.get("tickerText") == "0")
    # ④ the flames go out cluster by cluster
    lit_per_frame = [s["litFlames"] for s in samples]
    dense_lit = [s["litFlames"] for s in dense["dense"]]
    extinguish_staggered = len(set(lit_per_frame + dense_lit)) >= 3
    flames_out = all(not f["lit"] for f in terminal["flames"])
    # ⑤ the negative feedback must not be carried by the banner
    banner_on_during_break = any("is-on" in (s["bannerClass"] or "") for s in samples)

    checks = {
        "答错时出现明确的负反馈（计数器摆动 lk-error-nudge）": nudged,
        "摆动幅度 ≤4px": worst_counter <= 4.01,
        "不做屏幕级震动（祖先层与 body/html 不位移）":
            worst_ancestor <= 0.01 and worst_page <= 0.01,
        "计数器归零": zeroed,
        "火苗簇逐簇熄灭（熄灭过程有错峰）": extinguish_staggered,
        "终态火苗全灭": flames_out,
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("负反馈 = 计数器水平摆动（≤4px）+ 火苗逐簇熄灭 + 计数器归零"
              if verdict == PASS else
              "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    strip = F.build_strip(frames_dir, out_dir / "M-11-strip.png")
    return {
        "id": "M-11",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-11",
        "checks": checks,
        "evidence": {
            "animationName": anim_name,
            "counterShifts": [s["counterShift"] for s in samples],
            "worstCounterShiftPx": worst_counter,
            "worstAncestorShiftPx": worst_ancestor,
            "worstPageShiftPx": worst_page,
            "litFlamesPerFrame": lit_per_frame,
            "litFlamesDensePoll": dense_lit,
            "counterShiftsDensePoll": [s["counterShift"] for s in dense["dense"]],
            "tickerTextDensePoll": [s["tickerText"] for s in dense["dense"]],
            "tickerTextPerFrame": [s["tickerText"] for s in samples],
            "tierPerFrame": [s["counterTier"] for s in samples],
            "bannerClassPerFrame": [s["bannerClass"] for s in samples],
            "bannerCarriesTheNegativeFeedback": banner_on_during_break,
            "beforeCount": animated["before"]["tickerText"],
            "terminalTicker": terminal.get("tickerText"),
            "terminalTier": terminal.get("tickerTier"),
            "terminalTierAttribute": terminal.get("counterTier"),
        },
        "animated": animated,
        "reduced": reduced,
        "strip": str(strip.name) if strip else None,
    }


# ─────────────────────────────────────────────────────────────────────────
# M-12 — the four combinations of the motion tier
# ─────────────────────────────────────────────────────────────────────────

#: (label, system reduced-motion, explicit preference)
COMBINATIONS = [
    ("system-reduce + pref-unset", "reduce", None),
    ("system-reduce + pref-on", "reduce", True),
    ("system-allow + pref-unset", "no-preference", None),
    ("system-allow + pref-off", "no-preference", False),
]

TIER_JS = r"""
() => {
  const counter = document.querySelector("#lk-probe-streak .lk-streak");
  const ticker = document.querySelector("#lk-probe-streak .lk-ticker");
  const banner = document.querySelector("#lk-probe-streak .lk-combo-banner");
  const flames = Array.from(document.querySelectorAll("#lk-probe-streak .lk-flame"));
  return {
    mode: window.lkMotion ? window.lkMotion.mode() : null,
    dataMotion: document.documentElement.getAttribute("data-motion"),
    tier: counter ? counter.getAttribute("data-lk-streak-tier") : null,
    counterClass: counter ? String(counter.className || "") : null,
    counterText: ticker ? (ticker.textContent || "").trim() : null,
    litFlames: flames.filter((f) => f.classList.contains("is-lit")).length,
    flameCount: flames.length,
    bannerOn: banner ? banner.classList.contains("is-on") : null,
    bannerOpacity: banner ? getComputedStyle(banner).opacity : null,
    bannerText: banner ? (banner.textContent || "").trim() : null,
    lampExists: !!document.querySelector(".lk-lamp"),
    runningAnimations: Array.from(new Set(document.getAnimations().map(
      (a) => a.animationName || "").filter((name) => name && name !== "none"))),
  };
}
"""


def run_m12(playwright, base_url, ws, out_dir):
    """M-12 — the four combinations of A-2, compared with the full tier."""
    out_dir = Path(out_dir)
    frames_dir = out_dir / "M-12"
    frames_dir.mkdir(parents=True, exist_ok=True)

    def one_run(system, pref, label):
        browser, context, page = launch(playwright, reduced_motion=system,
                                        pref=pref, ws=ws)
        try:
            ctx = ctx_of(base_url, ws)
            F.prepare_streak(page, ctx)
            page.evaluate(streak_html_js(5))
            page.wait_for_timeout(900)
            tier = page.evaluate(TIER_JS)
            name = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") + ".png"
            page.screenshot(path=str(frames_dir / name), caret="hide", scale="css")
            # the theme switch: the lamp layers are the loudest signal of the tier
            page.goto(ctx.url("settings"), wait_until="load", timeout=30000)
            page.wait_for_timeout(500)
            page.evaluate("""() => {
              const box = document.getElementById("setting-theme");
              if (box && !box.checked) box.click();
            }""")
            page.wait_for_timeout(200)
            lamp = page.evaluate("""() => ({
              lamp: !!document.querySelector(".lk-lamp"),
              ripple: !!document.querySelector(".lk-ripple"),
              mode: window.lkMotion ? window.lkMotion.mode() : null,
            })""")
            return {"label": label, "system": system, "pref": pref,
                    "tier": tier, "lamp": lamp, "frame": name}
        finally:
            context.close()
            browser.close()

    results = []
    for label, system, pref in COMBINATIONS:
        results.append(one_run(system, pref, label))

    baseline = next(r for r in results
                    if r["label"] == "system-allow + pref-unset")
    expected_mode = {
        "system-reduce + pref-unset": "weak",
        "system-reduce + pref-on": "full",
        "system-allow + pref-unset": "full",
        "system-allow + pref-off": "off",
    }
    #: The items §2's通用判据 enumerates for the terminal-state comparison:
    #: 数字 · 进度带 · 计数器档位 · 灯与涟漪层 · 纸片 · 火苗簇 · 内容位置.
    #: The banner's **opacity** is not in that list — but motion-spec §7.2
    #: row 18 requires the banner to disappear after the hold in the
    #: downgraded tiers too, so it is checked separately.
    terminal_fields = ("tier", "counterText", "litFlames", "flameCount",
                       "bannerOn", "bannerText")

    rows = []
    for result in results:
        tier = result["tier"]
        base = baseline["tier"]
        diffs = []
        for field in terminal_fields:
            if tier.get(field) != base.get(field):
                diffs.append({"field": field, "combination": tier.get(field),
                              "baseline": base.get(field)})
        mode_ok = tier.get("mode") == expected_mode[result["label"]]
        lamp_ok = result["lamp"].get("lamp") == (expected_mode[result["label"]] == "full")
        rows.append({
            "label": result["label"],
            "systemReducedMotion": result["system"],
            "preference": "unset" if result["pref"] is None
                          else ("on" if result["pref"] else "off"),
            "expectedMode": expected_mode[result["label"]],
            "actualMode": tier.get("mode"),
            "dataMotionAttribute": tier.get("dataMotion"),
            "lampLayersCreated": result["lamp"].get("lamp"),
            "runningAnimations": tier.get("runningAnimations"),
            "terminal": {field: tier.get(field) for field in terminal_fields},
            "bannerOpacityAtTerminal": tier.get("bannerOpacity"),
            "terminalDifferencesVsFullTier": diffs,
            "modeMatchesExpectation": mode_ok,
            "lampMatchesTier": lamp_ok,
            "frame": result["frame"],
        })

    consistent = all(not row["terminalDifferencesVsFullTier"] for row in rows)
    modes_ok = all(row["modeMatchesExpectation"] for row in rows)
    lamps_ok = all(row["lampMatchesTier"] for row in rows)
    explicit_on = next(row for row in rows
                       if row["label"] == "system-reduce + pref-on")
    explicit_off = next(row for row in rows
                        if row["label"] == "system-allow + pref-off")
    #: The banner must have left in **every** tier (motion-spec §7.2 row 18:
    #: 「横幅直接以终态出现并在 hold 后直接消失」).
    banner_left = {row["label"]: row["bannerOpacityAtTerminal"] for row in rows}
    banner_leaves_everywhere = all(
        value is not None and float(value) == 0 for value in banner_left.values())
    checks = {
        "四种组合的终态与「动效开启」逐项一致（数字/档位/火苗/横幅内容）": consistent,
        "四种组合的档位与 A-2 的分级一致": modes_ok,
        "显式「开」恢复完整动效（台灯层被创建）": lamps_ok
        and explicit_on["lampLayersCreated"] is True,
        "显式「关」全部直切（台灯层不创建）":
            explicit_off["lampLayersCreated"] is False,
        "横幅在四种组合下都退场（hold 后不透明度 = 0）": banner_leaves_everywhere,
    }
    verdict = PASS if all(checks.values()) else FAIL
    detail = ("四种组合的终态（计数器 / 档位 / 火苗 / 横幅）与动效开启时逐项一致；"
              "显式选择优先于系统设置"
              if verdict == PASS else
              "；".join(name for name, ok in checks.items() if not ok) + " 不成立")
    return {
        "id": "M-12",
        "verdict": verdict,
        "detail": detail,
        "criterion": "acceptance.md §2 M-12",
        "checks": checks,
        "rows": rows,
        "bannerOpacityAtTerminalPerCombination": banner_left,
        "framesDir": str(frames_dir),
    }


# ─────────────────────────────────────────────────────────────────────────
# the reduced-motion twins — one pair per motion
# ─────────────────────────────────────────────────────────────────────────

#: The trigger of every motion that has a **visual** terminal state.
#: ``frames.py``'s triggers are reused as they are; the streak ones use the
#: product's own call order (render → apply).
TRIGGERS = {
    "M-1": "theme",
    "M-2": "celebration",
    "M-3": "celebration",
    "M-4": "streak",
    "M-5": "streak-tiers",
    "M-6": "streak",
    "M-7": "answer",
    "M-8": "view",
    "M-9": "skeleton",
    "M-10": "records",
}


def _trigger(page, ctx, trigger, motion_id, plan):
    """Run one trigger and leave the page in its terminal state."""
    if trigger in ("streak", "streak-tiers"):
        F.prepare_streak(page, ctx)
        count = 31 if trigger == "streak-tiers" else 5
        page.evaluate(streak_html_js(count))
        page.wait_for_timeout(900)
        return
    if trigger == "celebration":
        F.prepare_celebration(page, ctx)
        F.act_celebration(page, ctx)
        page.wait_for_selector("#paper-completion", state="attached", timeout=20000)
        page.wait_for_timeout(1200)
        return
    prepare = F.PREPARE[trigger]
    act = F.ACT[trigger]
    prepare(page, ctx)
    act(page, ctx)
    page.wait_for_timeout(1200)


def run_twins(playwright, base_url, ws, out_dir, plan):
    """One **animated / reduced** pair of terminal frames per motion.

    ``frames.py`` records the reduced twin as **data** (the DOM state), not as
    pictures.  The deliverable asks for the picture as well, so the pair is
    captured here: the same trigger, the same moment (the terminal state), in
    the two tiers.
    """
    out_dir = Path(out_dir)
    pairs_dir = out_dir / "twins"
    pairs_dir.mkdir(parents=True, exist_ok=True)
    watch = F.WATCH
    rows = []

    for motion_id, trigger in TRIGGERS.items():
        row = {"id": motion_id, "trigger": trigger}
        states = {}
        for tier, reduced in (("animated", None), ("reduced", "reduce")):
            browser, context, page = launch(playwright, reduced_motion=reduced)
            held = []

            def hold(route):
                held.append(route)

            try:
                if motion_id == "M-9":
                    page.route("**/w/*/practice-sets", hold)
                ctx = ctx_of(base_url, ws, plan=plan, motion_id=motion_id)
                _trigger(page, ctx, trigger, motion_id, plan)
                page.evaluate("() => window.__lkFrame.finish()")
                page.wait_for_timeout(300)
                path = pairs_dir / f"{motion_id}-{tier}.png"
                page.screenshot(path=str(path), caret="hide", scale="css")
                states[tier] = page.evaluate(
                    "(w) => window.__lkFrame.snapshot(w)", watch)
                row[f"{tier}File"] = path.name
            finally:
                for route in held:
                    try:
                        route.continue_()
                    except Exception:
                        pass
                context.close()
                browser.close()
        differences, extra = F.compare_terminal(states["animated"], states["reduced"])
        row["terminalDifferences"] = differences
        row["terminalExtraDifferences"] = extra
        row["terminalEqual"] = not differences
        rows.append(row)
    return {
        "rows": rows,
        "pairsDir": str(pairs_dir),
        "contract": sorted(F.TERMINAL_CONTRACT),
    }


# ─────────────────────────────────────────────────────────────────────────
# the CLI
# ─────────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Supplementary motion verification (M-1…M-6, M-9…M-12).")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--ws", required=True)
    parser.add_argument("--out", required=True, help="the output directory")
    parser.add_argument("--only", default=None,
                        help="a comma separated list: M-1,M-2,M-3,M-4,M-6,M-9,M-10,M-11,M-12")
    parser.add_argument("--plan", default=None,
                        help="the all-correct plan (seed.py)")
    parser.add_argument("--pool", default=None,
                        help="the isolated pool copy (used by --seed-days)")
    parser.add_argument("--seed-days", type=int, default=0,
                        help="write one attempt on each of the last N days into "
                             "the isolated pool copy (makes the load bars' "
                             "stagger observable)")
    args = parser.parse_args(argv)

    from playwright.sync_api import sync_playwright

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = ([m.strip() for m in args.only.split(",")] if args.only
              else ["M-1", "M-2", "M-3", "M-4", "M-5", "M-6", "M-9", "M-10", "M-11", "M-12", "twins"])
    plan = []
    if args.plan:
        plan = (F._read_json(args.plan) or {}).get("items") or []
    if args.seed_days:
        if not args.pool:
            raise SystemExit("--seed-days needs --pool (the isolated copy)")
        touched = seed_recent_days(args.pool, args.seed_days)
        print(json.dumps({"seededDays": touched}, ensure_ascii=False))

    summary = {}
    with sync_playwright() as playwright:
        if "M-1" in wanted:
            result = run_m1(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-1-extra.json", result)
            summary["M-1"] = result["verdict"]
        for motion_id in ("M-2", "M-3"):
            if motion_id in wanted:
                result = run_celebration(playwright, args.base_url, args.ws, out_dir,
                                         motion_id, plan)
                write_json(out_dir / f"{motion_id}-extra.json", result)
                summary[motion_id] = "captured"
        if "M-4" in wanted or "M-6" in wanted:
            results = run_streak_motions(playwright, args.base_url, args.ws, out_dir)
            for key, result in results.items():
                write_json(out_dir / f"{key}-extra.json", result)
                if key in summary:
                    summary[key] = result["verdict"]
        if "M-9" in wanted:
            result = run_m9(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-9-extra.json", result)
            summary["M-9"] = result["verdict"]
        if "M-5" in wanted:
            result = run_m5(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-5-extra.json", result)
            summary["M-5"] = result["verdict"]
        if "M-10" in wanted:
            result = run_m10(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-10-extra.json", result)
            summary["M-10"] = result["verdict"]
        if "M-11" in wanted:
            result = run_m11(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-11-extra.json", result)
            summary["M-11"] = result["verdict"]
        if "M-12" in wanted:
            result = run_m12(playwright, args.base_url, args.ws, out_dir)
            write_json(out_dir / "M-12-extra.json", result)
            summary["M-12"] = result["verdict"]
        if "twins" in wanted:
            result = run_twins(playwright, args.base_url, args.ws, out_dir, plan)
            write_json(out_dir / "twins.json", result)
            summary["twins"] = {
                row["id"]: ("EQUAL" if row["terminalEqual"] else "DIFF")
                for row in result["rows"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
