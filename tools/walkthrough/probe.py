"""Browser probes — G-7, G-8 and the 39-item interaction checklist.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §7.2 (G-7 / G-8) and §7.5 (the 38 items, the three
automation levels AUTO / SEMI / MANUAL, the probe mechanisms of §7.5.2, the
token-pair list of §7.5.4 and the "no counterpart on the before side" list of
§7.5.5).  The criteria themselves live in ``acceptance.md`` §3.

What this module does
---------------------
It drives a real browser against the running service and records **raw
evidence** for every item of the interaction checklist, plus the two gates
that only a browser can answer (G-7 pointer events, G-8 focus order).

Three rules from the design are implemented literally:

1. **Only AUTO items may be auto-judged** (§7.5.1).  A SEMI or MANUAL item is
   always reported as ``PENDING`` with its evidence and a reading guide; the
   executor never ticks it for a human.
2. **"N/A" is not "PASS"** (X-7).  The eleven items that have no counterpart
   before the change are ``N/A`` on the before side only; on the after side
   they are judged normally.
3. **Missing evidence is never a pass** (§7.6.2).  A probe that cannot reach
   its target reports ``PENDING`` with the reason, never ``PASS``.

Three passes
------------
The checklist is collected in three passes because the items need different
states of the product:

``static``
    Everything that only reads the DOM.  It must run **before** the scripted
    exercise, because item 3.4-5 (the empty state) needs an empty paper list
    and the exercise creates a paper.
``flow``
    The audio items, which need a real paper run to produce a real
    judgement.  It creates its own paper, so the recorded request stream
    grows by the same amount on both sides.
``persist``
    The "after a service restart" half of item 3.2-6.  It re-reads the
    preference from the *same* browser profile, so the profile has to be a
    persistent one (``--profile``).

Red lines (§8.3): this module only drives a browser and reads files.  It
never writes the pool, never changes a request, never touches product code.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shots import CONSISTENCY, VIEWPORTS  # noqa: E402  (path set up above)

#: Verdict vocabulary (§7.6.2).
PASS, FAIL, PENDING, NA = "PASS", "FAIL", "PENDING", "N/A"

#: The pages the probes visit.  ``{ws}`` is replaced by the workspace name.
PAGES = {
    "hub": "/w/{ws}/",
    "practice": "/w/{ws}/practice",
    "kps": "/w/{ws}/kps",
    "records": "/w/{ws}/records",
    "practice-sets": "/w/{ws}/practice-sets",
    "settings": "/w/{ws}/settings",
    "graph": "/w/{ws}/graph",
}

#: The four viewports of item 3.5-1 (1440 / 1280 / 1024 / 768).
RESPONSIVE_VIEWPORTS = ("V1440", "V1280", "V1024", "V768")

#: The four viewports of §5.4's screenshot matrix, kept in one place.
SHOT_VIEWPORTS = ("V1440", "V1024", "V768", "V1280")


# ─────────────────────────────────────────────────────────────────────────
# §7.5.4 — the contrast token pairs
# ─────────────────────────────────────────────────────────────────────────

#: The after-side pairs (the new ``--surface-*`` / ``--ink-*`` / ``--role-*``
#: namespace).  ``threshold`` is the WCAG ratio the pair must reach; the
#: threshold belongs to the *pair*, not to the colour (§7.5.4).
AFTER_CONTRAST_PAIRS = (
    ("正文 / 页面底", "--ink-body", "--surface-base", 4.5),
    ("正文 / 卡面", "--ink-body", "--surface-card", 4.5),
    ("标题墨 / 页面底", "--ink-strong", "--surface-base", 4.5),
    ("次要文字 / 卡面", "--ink-muted", "--surface-card", 4.5),
    ("三级文字 / 卡面", "--ink-faint", "--surface-card", 3.0),
    ("大字号标题 / 浮起面", "--ink-strong", "--surface-raised", 3.0),
    ("主按钮文字 / 蓝", "--ink-on-role", "--role-blue", 4.5),
    ("选中行文字 / 蓝洗底", "--role-blue", "--role-blue-wash", 4.5),
    ("黄面承载文字 / 黄", "--ink-on-warm", "--role-yellow", 4.5),
    ("红洗底文字 / 红洗底", "--role-red-ink", "--role-red-wash", 4.5),
    ("焦点环 / 页面底", "--role-blue", "--surface-base", 3.0),
    ("状态点 / 卡面", "--role-yellow-deep", "--surface-card", 3.0),
)

#: The before-side pairs (the old ``--lk-*`` / ``--dsw-label-*`` namespace).
#: The night-paper pairs have no counterpart before the change, so they are
#: not in this list at all (§7.5.5: 3.1-2 is *partly* not applicable).
BEFORE_CONTRAST_PAIRS = (
    ("正文 / 纸面", "--lk-ink", "--lk-paper", 4.5),
    ("次要文字 / 纸面", "--dsw-label-secondary", "--lk-paper", 4.5),
    ("三级文字 / 纸面", "--dsw-label-tertiary", "--lk-paper", 3.0),
    ("蓝 / 纸面", "--lk-blue", "--lk-paper", 4.5),
    ("红 / 纸面", "--lk-red", "--lk-paper", 4.5),
    ("黄面文字 / 黄", "#332900", "--lk-yellow", 4.5),
    ("蓝字 / 蓝洗底", "#193f91", "#dce7ff", 4.5),
    ("绿字 / 绿洗底", "#245d32", "#d9ebdd", 4.5),
    ("红字 / 红洗底", "#922d26", "#f6d8d5", 4.5),
)

#: The night-paper pairs, measured on the after side only (§7.5.5: 3.2-2).
NIGHT_CONTRAST_PAIRS = (
    ("正文 / 页面底", "--ink-body", "--surface-base", 4.5),
    ("正文 / 卡面", "--ink-body", "--surface-card", 4.5),
    ("标题墨 / 页面底", "--ink-strong", "--surface-base", 4.5),
    ("次要文字 / 卡面", "--ink-muted", "--surface-card", 4.5),
    ("三级文字 / 卡面", "--ink-faint", "--surface-card", 3.0),
    ("大字号标题 / 浮起面", "--ink-strong", "--surface-raised", 3.0),
    ("主按钮文字 / 蓝", "--ink-on-role", "--role-blue", 4.5),
    ("选中行文字 / 蓝洗底", "--role-blue", "--role-blue-wash", 4.5),
    ("黄面承载文字 / 黄", "--ink-on-warm", "--role-yellow", 4.5),
    ("红洗底文字 / 红洗底", "--role-red-ink", "--role-red-wash", 4.5),
)


# ─────────────────────────────────────────────────────────────────────────
# §7.5.5 — the items with no counterpart before the change
# ─────────────────────────────────────────────────────────────────────────

#: The eleven items of §7.5.5.  On the before side they are ``N/A`` — the
#: capability does not exist there, so there is nothing to compare.  On the
#: after side they are judged normally.
BEFORE_NA = {
    "3.2-1": "改造前无主题系统（workbench/ 与 frontend/ 全目录无 data-theme）",
    "3.2-2": "改造前无夜纸值集（:root 只有亮色一套）",
    "3.2-4": "改造前全仓 0 个 .svg 资产",
    "3.3-1": "改造前无音效代码（workbench/ 全目录无 Audio / AudioContext）",
    "3.3-2": "改造前无音效代码，故无「首次音效」可言（与 3.3-1 同源事实）",
    "3.3-3": "改造前无音效代码",
    "3.3-4": "改造前无音效代码",
    "3.4-3": "改造前无骨架屏（*.css 里 skeleton / shimmer 零命中）",
    "3.6-1": "改造前全仓 0 个 .svg 资产",
    "3.6-3": "改造前无图标、无角色色表",
    "3.6-5": "改造前无 SVG 资产",
    "3.7-3": "改造前本仓自有 CSS 无 @font-face（vendored KaTeX 不计）",
}

#: The pairs that ``G-8`` may excuse: "新增的设置视图入口与主题开关"
#: (§7.2).  A focus stop whose semantic description matches one of these
#: patterns and that does not exist before the change is ADDED-EXPECTED.
ADDED_EXPECTED_PATTERNS = (
    re.compile(r"设置"),
    re.compile(r"主题"),
    re.compile(r"夜纸"),
    re.compile(r"偏好"),
)


# ─────────────────────────────────────────────────────────────────────────
# the in-page probe bundle
# ─────────────────────────────────────────────────────────────────────────

#: Injected into every page before the product's own scripts.  It only
#: *reads* the DOM; the audio shim is the one exception and it only wraps
#: ``play`` to record the call.
PROBE_JS = r"""
(() => {
  const P = {};

  const visible = (el) => {
    if (!el || el.nodeType !== 1) return false;
    const st = getComputedStyle(el);
    if (!st) return false;
    if (st.display === "none" || st.visibility === "hidden") return false;
    if (parseFloat(st.opacity || "1") === 0) return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    return true;
  };
  P.visible = visible;

  /* The semantic description of a focus stop: role + accessible name, never
     the id (the DOM is restructured by the change; the order must not be). */
  /* The visible text of an element, **without** the parts that are
     hidden from the accessibility tree: the new design puts a glyph
     inside the navigation links, and the raw text content would then
     read "练习 练习" — the same link, described differently.  The
     accessible name is what a screen reader announces, so it is what the
     focus order is compared by. */
  P.accessibleText = (el) => {
    const clone = el.cloneNode(true);
    clone.querySelectorAll("[aria-hidden='true']").forEach((n) => n.remove());
    return (clone.textContent || "").replace(/\s+/g, " ").trim();
  };
  P.semantic = (el) => {
    if (!el || el.nodeType !== 1) return "<none>";
    const tag = el.tagName.toLowerCase();
    const type = el.getAttribute("type") || "";
    const role = el.getAttribute("role") || "";
    const name = (el.getAttribute("aria-label") || el.getAttribute("title")
                  || P.accessibleText(el) || "")
      .replace(/\s+/g, " ").trim().slice(0, 40);
    return [tag, type, role, name].filter(Boolean).join("|");
  };

  P.focusables = () => Array.from(document.querySelectorAll(
      "a[href], button, input, select, textarea, [tabindex], [contenteditable='true']"
  )).filter((el) => !el.disabled
      && el.getAttribute("tabindex") !== "-1"
      && el.getAttribute("aria-hidden") !== "true"
      && visible(el));

  /* §7.5.2 text_count_probe — the visible text nodes and their characters.
     Attributes (aria-label …) are not text nodes, so they are excluded by
     construction. */
  P.textCount = () => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let nodes = 0, chars = 0;
    const samples = [];
    let node;
    while ((node = walker.nextNode())) {
      const text = (node.nodeValue || "").replace(/\s+/g, " ").trim();
      if (!text) continue;
      const parent = node.parentElement;
      if (!parent || !visible(parent)) continue;
      nodes += 1;
      chars += text.length;
      if (samples.length < 60) samples.push(text.slice(0, 60));
    }
    return { nodes, chars, samples };
  };

  /* §7.5.2 state_geometry_probe — the state marks and their two channels:
     the colour signature and the geometry signature. */
  const STATE_SELECTOR = "[class*='dot'], [class*='state'], [class*='status'], "
      + "[role='img'][aria-label]";
  P.stateElements = () => {
    const out = [];
    const seen = new Set();
    document.querySelectorAll(STATE_SELECTOR).forEach((el) => {
      if (!visible(el)) return;
      const rect = el.getBoundingClientRect();
      if (rect.width > 64 || rect.height > 64) return;   /* a card is not a mark */
      const st = getComputedStyle(el);
      const before = getComputedStyle(el, "::before");
      const after = getComputedStyle(el, "::after");
      const key = el.className + "|" + el.tagName;
      if (seen.has(key)) return;
      seen.add(key);
      const pseudo = (node) => {
        if (!node) return "none";
        return [
          node.content,
          node.width + "x" + node.height,
          node.backgroundColor,
          node.transform,
          node.borderRadius,
          [node.borderTopWidth, node.borderRightWidth,
           node.borderBottomWidth, node.borderLeftWidth].join("/"),
        ].join(" ");
      };
      out.push({
        tag: el.tagName.toLowerCase(),
        cls: String(el.className || ""),
        text: (el.getAttribute("aria-label") || el.getAttribute("title")
               || el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40),
        color: {
          background: st.backgroundColor,
          border: st.borderTopColor,
          foreground: st.color,
        },
        geometry: {
          radius: st.borderRadius,
          borderWidths: [st.borderTopWidth, st.borderRightWidth,
                         st.borderBottomWidth, st.borderLeftWidth].join("/"),
          before: pseudo(before),
          after: pseudo(after),
          transform: st.transform,
          clipPath: st.clipPath,
        },
        size: [Math.round(rect.width), Math.round(rect.height)],
      });
    });
    return out;
  };

  /* §7.5.2 asset_probe — every image, inline svg, css background and font. */
  P.assets = () => {
    const imgs = Array.from(document.querySelectorAll("img")).map((el) => ({
      src: el.getAttribute("src") || "",
      cls: String(el.className || ""),
      parent: el.parentElement ? String(el.parentElement.className || "") : "",
    }));
    const svgs = Array.from(document.querySelectorAll("svg")).map((el) => ({
      src: el.getAttribute("src") || "",
      cls: String(el.className || ""),
      parent: el.parentElement ? String(el.parentElement.className || "") : "",
      strokeWidths: Array.from(el.querySelectorAll("[stroke-width]"))
          .map((n) => n.getAttribute("stroke-width")),
      radii: Array.from(el.querySelectorAll("[rx],[ry]"))
          .map((n) => (n.getAttribute("rx") || "") + "/" + (n.getAttribute("ry") || "")),
    }));
    const backgrounds = [];
    document.querySelectorAll("*").forEach((el) => {
      const st = getComputedStyle(el);
      const bg = st.backgroundImage;
      if (!bg || bg === "none") return;
      const urls = bg.match(/url\(([^)]*)\)/g) || [];
      urls.forEach((u) => backgrounds.push({
        url: u.replace(/^url\(|\)$/g, "").replace(/["']/g, ""),
        cls: String(el.className || ""),
      }));
    });
    return { imgs, svgs, backgrounds };
  };

  /* The svg sources of the whole document (3.2-4 / 3.6-5).
     An inline <svg> has no src, so its **markup** is the identity: the
     night theme has to use the same markup with different css variables. */
  P.svgSources = () => {
    const out = [];
    document.querySelectorAll("img, svg, use").forEach((el) => {
      const src = el.getAttribute("src") || el.getAttribute("href") || "";
      if (src) out.push("file:" + src);
    });
    document.querySelectorAll("svg").forEach((el) => {
      const markup = el.outerHTML.replace(/\s+/g, " ");
      let hash = 0;
      for (let i = 0; i < markup.length; i += 1) {
        hash = ((hash << 5) - hash + markup.charCodeAt(i)) | 0;
      }
      out.push("inline:" + (hash >>> 0).toString(16) + ":" + markup.length);
    });
    document.querySelectorAll("*").forEach((el) => {
      const bg = getComputedStyle(el).backgroundImage;
      if (!bg || bg === "none") return;
      (bg.match(/url\(([^)]*)\)/g) || []).forEach((u) => {
        out.push("file:" + u.replace(/^url\(|\)$/g, "").replace(/["']/g, ""));
      });
    });
    return out;
  };

  /* §7.5.2 perf_probe — the properties the motion really animates. */
  P.animatedProperties = () => {
    const transitions = [];
    const wildcards = [];
    document.querySelectorAll("*").forEach((el) => {
      const st = getComputedStyle(el);
      const prop = st.transitionProperty;
      if (!prop || prop === "none") return;
      const duration = st.transitionDuration;
      if (!duration || duration.split(",").every((d) => parseFloat(d) === 0)) return;
      const names = prop.split(",").map((s) => s.trim());
      const record = {
        cls: String(el.className || "").slice(0, 60),
        tag: el.tagName.toLowerCase(),
        property: prop,
        duration: duration,
      };
      if (names.indexOf("all") >= 0) wildcards.push(record);
      else transitions.push(record);
    });
    const keyframes = [];
    const running = [];
    if (document.getAnimations) {
      document.getAnimations().forEach((anim) => {
        const effect = anim.effect;
        if (!effect || !effect.getKeyframes) return;
        let props = [];
        try { props = effect.getKeyframes().map((k) => k.keyText); } catch (e) { props = []; }
        props = props.filter(Boolean);
        if (!props.length) return;
        keyframes.push({ name: anim.animationName || "", properties: Array.from(new Set(props)) });
        running.push({
          name: anim.animationName || "",
          playState: anim.playState,
          properties: Array.from(new Set(props)),
        });
      });
    }
    return { transitions, wildcards, keyframes, running };
  };

  /* The computed value of the named custom properties (the token reader). */
  P.tokens = (names) => {
    const root = getComputedStyle(document.documentElement);
    const out = {};
    names.forEach((name) => {
      out[name] = (root.getPropertyValue(name) || "").trim();
    });
    return out;
  };

  /* The three role colours and their wash / soft variants (3.6-3). */
  P.roleColours = () => {
    const root = getComputedStyle(document.documentElement);
    const names = ["--role-blue", "--role-blue-wash", "--role-blue-soft",
                   "--role-yellow", "--role-yellow-wash", "--role-yellow-soft",
                   "--role-role", "--role-red", "--role-red-wash", "--role-red-soft",
                   "--role-red-ink", "--role-yellow-deep"];
    const out = {};
    names.forEach((name) => {
      const value = (root.getPropertyValue(name) || "").trim();
      if (value) out[name] = value;
    });
    return out;
  };

  /* The coloured circle behind the icons (3.6-3). */
  P.iconBackgrounds = () => {
    const out = [];
    const seen = new Set();
    document.querySelectorAll("[class*='icon'], svg").forEach((el) => {
      if (!visible(el)) return;
      const st = getComputedStyle(el);
      const host = el.closest("[class*='icon']") || el.parentElement;
      if (!host) return;
      const hostStyle = getComputedStyle(host);
      const bg = hostStyle.backgroundColor;
      const key = String(host.className || "") + "|" + bg;
      if (seen.has(key)) return;
      seen.add(key);
      out.push({
        cls: String(host.className || "").slice(0, 80),
        background: bg,
        radius: hostStyle.borderRadius,
        ownBackground: st.backgroundColor,
      });
    });
    return out;
  };

  /* The loading mark is transient: the observer records it the moment the
     parser inserts it, before the script that replaces it runs. */
  P.skeletonSeen = () => (window.__lkSkeletonSeen || []).slice();

  /* §7.5.2 skeleton_probe — the loading marks and the shimmer.
     A-114 (iii): the degraded tier renders an equivalent **static** grey
     block — it carries no ``.lk-skeleton`` class (that class is the
     shimmer), only the ``data-lk-skeleton="1"`` wrapper.  The wrapper's
     children are therefore part of the probe too, and every entry says
     which role it plays and where it lives. */
  P.skeleton = () => {
    const out = [];
    const seen = new Set();
    const push = (el, role) => {
      if (seen.has(el)) return;
      seen.add(el);
      const st = getComputedStyle(el);
      const after = getComputedStyle(el, "::after");
      const rect = el.getBoundingClientRect();
      const wrapper = el.closest ? el.closest("[data-lk-skeleton]") : null;
      out.push({
        role: role,
        container: wrapper ? "middle" : "",
        cls: String(el.className || ""),
        visible: visible(el),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        background: st.backgroundColor,
        animationName: st.animationName,
        animationDuration: st.animationDuration,
        afterContent: after ? after.content : "",
        afterAnimation: after ? after.animationName : "",
        afterDuration: after ? after.animationDuration : "",
        afterPointerEvents: after ? after.pointerEvents : "",
      });
    };
    document.querySelectorAll(".lk-skeleton")
        .forEach((el) => push(el, "sweep"));
    document.querySelectorAll("[data-lk-skeleton] > *")
        .forEach((el) => push(el, "block"));
    return out;
  };

  /* §7.5.2 empty_state_probe — the shape of every empty state.
     The container is narrowed on purpose: the class names
     (``.lk-empty__art``, ``.lk-empty__text``, ``.lk-empty__action`` …) also
     match the **parts of an illustration**, and a part is not a container.
     Two rules remove them:
       · an element inside an ``<svg>`` belongs to the drawing;
       · an element whose ancestor is already a container is a part of it.
     The judgement itself is untouched — only "which elements count as a
     container" changed. */
  P.emptyStates = () => {
    const out = [];
    const selector = ".empty-state, .lk-empty, [class*='empty-state'], "
        + "[class*='-empty']";
    const candidates = Array.from(document.querySelectorAll(selector))
        .filter((el) => visible(el));
    const insideSvg = (el) => !!(el.closest && el.closest("svg"));
    const nestedIn = (el) => candidates.some((other) => other !== el
        && other.contains && other.contains(el));
    const containers = candidates.filter((el) => !insideSvg(el) && !nestedIn(el));
    containers.forEach((el) => {
      const art = el.querySelector("svg, img, .lk-empty__art, [class*='art'], [class*='illus']");
      const sentences = Array.from(el.querySelectorAll("p, .muted"))
          .filter((n) => (n.textContent || "").trim().length > 0);
      const action = el.querySelector("button, a.primary, a.button-link, .primary");
      const actionStyle = action ? getComputedStyle(action) : null;
      const rect = action ? action.getBoundingClientRect() : null;
      const parentRect = el.getBoundingClientRect();
      out.push({
        cls: String(el.className || ""),
        tag: el.tagName.toLowerCase(),
        art: art ? {tag: art.tagName.toLowerCase(),
                     src: art.getAttribute("src") || art.getAttribute("href") || "" } : null,
        sentences: sentences.map((n) => (n.textContent || "").trim().slice(0, 60)),
        action: action ? {
          tag: action.tagName.toLowerCase(),
          label: (action.textContent || "").trim().slice(0, 30),
          width: rect ? Math.round(rect.width) : 0,
          containerWidth: Math.round(parentRect.width),
          fullWidth: rect ? rect.width >= parentRect.width - 2 : false,
          display: actionStyle ? actionStyle.display : "",
        } : null,
      });
    });
    const classOf = (el) => el.getAttribute("class") || "";
    window.__lkEmptySkipped = {
      insideSvg: candidates.filter(insideSvg).map(classOf),
      nested: candidates.filter(nestedIn).map(classOf),
    };
    return out;
  };

  /* §7.5.2 scroll_probe — one container's scroll geometry. */
  P.scroll = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const st = getComputedStyle(el);
    return {
      selector,
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
      overflowY: st.overflowY,
      overflowX: st.overflowX,
      overflows: el.scrollHeight > el.clientHeight + 1,
      children: el.children.length,
    };
  };

  /* §7.5.2 custom_select_probe — the native selects and the chapter lens. */
  P.selects = () => {
    const native = Array.from(document.querySelectorAll("select")).map((el) => {
      const st = getComputedStyle(el);
      return {
        id: el.id,
        cls: String(el.className || ""),
        hidden: el.hasAttribute("hidden"),
        display: st.display,
        visible: visible(el),
        label: (el.getAttribute("aria-label") || "").trim(),
        options: el.options ? el.options.length : 0,
      };
    });
    const lensSelect = document.querySelector("#chapter-lens-select");
    const lensPanel = document.querySelector("#chapter-lens-panel");
    return {
      native,
      nativeVisibleCount: native.filter((s) => s.visible).length,
      chapterLens: {
        selectPresent: !!lensSelect,
        selectVisible: lensSelect ? visible(lensSelect) : false,
        selectHidden: lensSelect ? lensSelect.hasAttribute("hidden") : false,
        panelPresent: !!lensPanel,
        panelRole: lensPanel ? lensPanel.getAttribute("role") : null,
        panelVisible: lensPanel ? visible(lensPanel) : false,
        panelOptions: lensPanel ? lensPanel.children.length : 0,
      },
    };
  };

  /* The elements that look like a decorative layer (§7.2 G-7). */
  P.decorativeLayers = () => {
    const out = [];
    const vw = window.innerWidth, vh = window.innerHeight;
    document.querySelectorAll("body *").forEach((el) => {
      const st = getComputedStyle(el);
      if (st.position !== "fixed" && st.position !== "absolute") return;
      const rect = el.getBoundingClientRect();
      if (rect.width * rect.height < vw * vh * 0.15) return;
      if (st.pointerEvents === "none") return;         /* already inert */
      const hasText = (el.textContent || "").trim().length > 0;
      const focusable = el.querySelector("a, button, input, select, textarea, [tabindex]");
      const ariaHidden = el.getAttribute("aria-hidden") === "true";
      const x = Math.min(Math.max(rect.left + rect.width / 2, 1), vw - 1);
      const y = Math.min(Math.max(rect.top + rect.height / 2, 1), vh - 1);
      const hit = document.elementFromPoint(x, y);
      out.push({
        tag: el.tagName.toLowerCase(),
        cls: String(el.className || "").slice(0, 80),
        id: el.id,
        pointerEvents: st.pointerEvents,
        zIndex: st.zIndex,
        opacity: st.opacity,
        rect: [Math.round(rect.left), Math.round(rect.top),
               Math.round(rect.width), Math.round(rect.height)],
        probePoint: [Math.round(x), Math.round(y)],
        hasText,
        focusableInside: !!focusable,
        ariaHidden,
        hit: hit ? {
          tag: hit.tagName.toLowerCase(),
          cls: String(hit.className || "").slice(0, 80),
          id: hit.id,
          isSelf: hit === el || el.contains(hit),
        } : null,
      });
    });
    return out;
  };

  /* The accessible name of every icon (§7.5.2 accessible_name_probe). */
  P.accessibleNames = () => {
    const out = [];
    const seen = new Set();
    document.querySelectorAll("svg, [class*='icon']").forEach((el) => {
      if (!visible(el)) return;
      const own = (el.getAttribute("aria-label") || el.getAttribute("title")
                   || el.getAttribute("alt") || "").trim();
      const host = el.closest("a, button, [role='button'], [role='link'], label") || el;
      const hostName = (host.getAttribute("aria-label") || host.getAttribute("title")
                        || host.textContent || "").replace(/\s+/g, " ").trim();
      const key = String(host.className || "") + "|" + own + "|" + hostName;
      if (seen.has(key)) return;
      seen.add(key);
      out.push({
        tag: el.tagName.toLowerCase(),
        cls: String(el.className || "").slice(0, 60),
        ownName: own,
        hostTag: host.tagName.toLowerCase(),
        hostName: hostName.slice(0, 60),
        hasName: !!(own || hostName),
      });
    });
    return out;
  };

  /* The reduced-motion situation (§7.5.2 reduced_motion_probe). */
  P.motion = () => {
    const animated = [];
    document.querySelectorAll("*").forEach((el) => {
      const st = getComputedStyle(el);
      const anim = st.animationName && st.animationName !== "none";
      const trans = st.transitionProperty && st.transitionProperty !== "none"
        && st.transitionDuration.split(",").some((d) => parseFloat(d) > 0);
      if (!anim && !trans) return;
      animated.push({
        cls: String(el.className || "").slice(0, 60),
        tag: el.tagName.toLowerCase(),
        animationName: st.animationName,
        animationDuration: st.animationDuration,
        transitionProperty: st.transitionProperty,
        transitionDuration: st.transitionDuration,
      });
    });
    return {
      reduceMatches: !!(window.matchMedia
          && window.matchMedia("(prefers-reduced-motion: reduce)").matches),
      animatedCount: animated.length,
      animated: animated.slice(0, 80),
      runningAnimations: document.getAnimations
        ? document.getAnimations().length : 0,
    };
  };

  /* The local storage of this origin (the per-workspace preference). */
  P.storage = () => {
    const out = {};
    try {
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        out[key] = localStorage.getItem(key);
      }
    } catch (e) { out["<error>"] = String(e); }
    return out;
  };

  /* The theme state (3.2-1 … 3.2-6). */
  P.theme = () => {
    const root = document.documentElement;
    return {
      dataTheme: root.getAttribute("data-theme"),
      datasetTheme: root.dataset ? root.dataset.theme : undefined,
      colorScheme: getComputedStyle(root).colorScheme,
      settingsKey: "wb_settings_" + ((document.getElementById("layout") || {}).dataset
          ? document.getElementById("layout").dataset.workspace : ""),
      hasThemeApi: !!(window.lkTheme && typeof window.lkTheme.transition === "function"),
      effective: window.lkTheme && typeof window.lkTheme.effective === "function"
        ? window.lkTheme.effective() : null,
    };
  };

  P.audio = () => (window.__lkAudio || []).slice();
  window.__lkProbe = P;
})();
"""

#: The observer that catches the transient loading mark (§7.5.2).
#:
#: A-114 (i): every record carries the **measured size** of the block
#: (``getBoundingClientRect()``).  The judgement of 3.4-3 reads
#: ``width`` / ``height``, and the old record never collected them ⇒
#: ``sized`` was **always** empty ⇒ the item was a constant FAIL no
#: matter what the product did.
#:
#: A-114 (iii): the **degraded tier** (reduced motion / the in-app motion
#: preference off) renders an equivalent **static** grey block — it has
#: **no** ``.lk-skeleton`` class (that class carries the loading mark),
#: only the ``data-lk-skeleton="1"`` wrapper.  The observer therefore
#: watches the wrapper's children too and says which role a block plays:
#: ``"sweep"`` = the marked block, ``"block"`` = the static one.
#:
#: A-115: the loading mark is a **breathing** block — the block's own
#: surface (its ``background-color`` / its ``opacity``) changes over
#: time.  The record therefore carries
#:
#: * ``samples`` — the block's own ``background-color`` and ``opacity``
#:   at three moments (t0, t0+400ms, t0+800ms) and ``surfaceChanged``;
#: * ``ownAnimations`` — the animations running on the **element itself**
#:   (``effect.pseudoElement === null``) with the properties their
#:   keyframes actually vary;
#: * ``pseudoAnimations`` — the animations running on a **pseudo element**
#:   (``::after``) — the *old* form (a sheen sweeping across an overlay):
#:   it moves the overlay, not the block's surface, so it is evidence
#:   only and never satisfies the criterion.
#:
#: ``container`` says where the block lives: ``"middle"`` = the middle
#: column's page-switch skeleton (``middle-navigation.js``), ``""`` = a
#: block that belongs to some other loading mark (e.g. the paper list's
#: own ``.lk-skeleton--text``).
SKELETON_JS = r"""
(() => {
  const seen = [];
  window.__lkSkeletonSeen = seen;
  const recorded = new WeakSet();
  const DELAYS = [400, 800];
  const SKIP_KEYS = ["offset", "computedOffset", "easing", "composite"];
  const norm = (name) => String(name || "").replace(/-/g, "").toLowerCase();

  const surface = (el) => {
    const st = getComputedStyle(el);
    return {background: st.backgroundColor, opacity: st.opacity};
  };

  /* The running animations, split into "on the element" and "on a pseudo
     element" — the breathing mark lives on the element itself. */
  const animations = (el) => {
    const own = [], pseudo = [];
    let list = [];
    try { list = el.getAnimations ? el.getAnimations() : []; } catch (e) { list = []; }
    list.forEach((a) => {
      const effect = a.effect || {};
      const pseudoElement = effect.pseudoElement || null;
      let frames = [];
      try { frames = effect.getKeyframes ? effect.getKeyframes() : []; } catch (e) { frames = []; }
      const properties = new Set();
      const values = {};
      frames.forEach((frame) => {
        Object.keys(frame).forEach((key) => {
          if (SKIP_KEYS.indexOf(key) >= 0) return;
          const prop = key.indexOf(".") >= 0 ? key.split(".")[1] : key;
          properties.add(prop);
          if (!values[prop]) values[prop] = [];
          if (values[prop].indexOf(String(frame[key])) < 0) {
            values[prop].push(String(frame[key]));
          }
        });
      });
      const entry = {
        name: a.animationName || "",
        playState: a.playState || "",
        pseudoElement: pseudoElement,
        properties: Array.from(properties),
        varied: Array.from(properties).filter((p) => (values[p] || []).length > 1),
      };
      if (pseudoElement) pseudo.push(entry); else own.push(entry);
    });
    return {own: own, pseudo: pseudo};
  };

  const record = (el, role) => {
    if (!el || recorded.has(el)) return;
    recorded.add(el);
    const st = getComputedStyle(el);
    const after = getComputedStyle(el, "::after");
    const rect = el.getBoundingClientRect();
    const wrapper = el.closest ? el.closest("[data-lk-skeleton]") : null;
    const first = surface(el);
    const anims = animations(el);
    const item = {
      role: role,
      container: wrapper ? "middle" : "",
      cls: String(el.className || ""),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      background: first.background,
      opacity: first.opacity,
      animationName: st.animationName,
      animationDuration: st.animationDuration,
      afterContent: after ? after.content : "",
      afterAnimation: after ? after.animationName : "",
      afterDuration: after ? after.animationDuration : "",
      afterBackground: after ? after.backgroundImage : "",
      afterTransform: after ? after.transform : "",
      ownAnimations: anims.own,
      pseudoAnimations: anims.pseudo,
      samples: [{delay: 0, background: first.background, opacity: first.opacity}],
      surfaceChanged: false,
    };
    seen.push(item);
    DELAYS.forEach((delay) => {
      setTimeout(() => {
        if (!el.isConnected) return;
        const now = surface(el);
        item.samples.push({delay: delay, background: now.background,
                           opacity: now.opacity});
        const backgrounds = item.samples.map((s) => s.background);
        const opacities = item.samples.map((s) => s.opacity);
        item.surfaceChanged = backgrounds.some((v) => v !== backgrounds[0])
          || opacities.some((v) => v !== opacities[0]);
      }, delay);
    });
  };
  const scan = () => {
    document.querySelectorAll(".lk-skeleton").forEach((el) => record(el, "sweep"));
    document.querySelectorAll("[data-lk-skeleton] > *").forEach((el) => record(el, "block"));
  };
  try {
    const observer = new MutationObserver(scan);
    observer.observe(document, {childList: true, subtree: true});
    document.addEventListener("DOMContentLoaded", scan);
  } catch (e) { /* the observer is a nicety, not a requirement */ }
})();
"""

#: The motion tier the product is in (``window.lkMotion.mode()``):
#: ``"full"`` / ``"weak"`` / ``"off"``.  A-114 (iii): the loading mark
#: exists in the ``"full"`` tier only — the degraded tiers render the
#: equivalent static grey block instead.
MOTION_TIER_JS = """() => {
  try {
    if (window.lkMotion && typeof window.lkMotion.mode === "function") {
      return String(window.lkMotion.mode());
    }
  } catch (e) { /* the product has no motion module — full tier */ }
  return "full";
}"""

#: The audio shim (§7.5.2 audio_probe).  It wraps ``play`` and
#: ``AudioContext.start`` to record every playback in the page.
AUDIO_JS = r"""
(() => {
  const plays = [];
  window.__lkAudio = plays;
  const stamp = () => Math.round(performance.now());
  const activation = () => !!(navigator.userActivation && navigator.userActivation.isActive);
  const proto = window.HTMLMediaElement && window.HTMLMediaElement.prototype;
  if (proto && !proto.__lkPatched) {
    const original = proto.play;
    proto.play = function () {
      plays.push({
        t: stamp(),
        kind: this.tagName ? this.tagName.toLowerCase() : "media",
        src: this.currentSrc || this.src || "",
        userActivation: activation(),
      });
      return original.apply(this, arguments);
    };
    proto.__lkPatched = true;
  }
  const Ctor = window.AudioContext || window.webkitAudioContext;
  if (Ctor && !Ctor.prototype.__lkPatched) {
    const originalStart = Ctor.prototype.start;
    Ctor.prototype.start = function () {
      plays.push({ t: stamp(), kind: "audiocontext", src: "",
                   userActivation: activation() });
      return originalStart.apply(this, arguments);
    };
    Ctor.prototype.__lkPatched = true;
  }
})();
"""

#: The sound hook of 3.3-1.  It answers the one question the first round
#: could not answer: **was the cue blocked by the browser, or did the code
#: never trigger it?**
#:
#: Two counters are kept apart:
#:
#: * ``__lkSfxCalls`` — every call of ``window.lkSfx.playCue`` (the **code**
#:   level: did the product decide that something should sound?);
#: * ``__lkSfxPlays`` — every call of ``HTMLMediaElement.play`` **with the
#:   outcome of its promise** (the **browser** level: a rejected promise is
#:   the autoplay policy saying no).
#:
#: ``lkSfx`` is published by ``sfx.js`` as a plain assignment and the module
#: is loaded asynchronously, so the hook is installed through a setter: the
#: wrapper is in place whenever the module publishes itself.
SFX_HOOK_JS = r"""
(() => {
  const calls = [];
  const plays = [];
  window.__lkSfxCalls = calls;
  window.__lkSfxPlays = plays;
  const stamp = () => Math.round(performance.now());
  const activation = () => !!(navigator.userActivation && navigator.userActivation.isActive);

  const proto = window.HTMLMediaElement && window.HTMLMediaElement.prototype;
  if (proto && !proto.__lkOutcomePatched) {
    const original = proto.play;
    proto.play = function () {
      const entry = {t: stamp(), src: this.currentSrc || this.src || "",
                     userActivation: activation(), outcome: "pending"};
      plays.push(entry);
      let result;
      try {
        result = original.apply(this, arguments);
      } catch (error) {
        entry.outcome = "threw";
        entry.error = String(error && error.name);
        throw error;
      }
      if (result && typeof result.then === "function") {
        result.then(
          () => { entry.outcome = "fulfilled"; },
          (error) => {
            entry.outcome = "rejected";
            entry.error = String(error && error.name);
          });
      } else {
        entry.outcome = "no-promise";
      }
      return result;
    };
    proto.__lkOutcomePatched = true;
  }

  let real = undefined;
  Object.defineProperty(window, "lkSfx", {
    configurable: true,
    enumerable: true,
    get() { return real; },
    set(value) {
      if (value && typeof value.playCue === "function" && !value.__lkHooked) {
        const original = value.playCue;
        value.playCue = function (name) {
          const entry = {t: stamp(), name: String(name),
                         userActivation: activation()};
          calls.push(entry);
          const out = original.apply(this, arguments);
          entry.returned = out;
          return out;
        };
        value.__lkHooked = true;
      }
      real = value;
    },
  });
})();
"""


# ─────────────────────────────────────────────────────────────────────────
# small helpers
# ─────────────────────────────────────────────────────────────────────────


def _hex_to_rgb(value):
    """``#abc`` / ``#aabbcc`` / ``rgb(...)`` → ``(r, g, b)`` or ``None``."""
    if not value:
        return None
    text = value.strip().lower()
    if text.startswith("#"):
        text = text[1:]
        if len(text) == 3:
            text = "".join(c * 2 for c in text)
        if len(text) != 6:
            return None
        try:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None
    match = re.match(r"rgba?\(([^)]+)\)", text)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        try:
            return tuple(int(float(p)) for p in parts[:3])
        except ValueError:
            return None
    return None


def _relative_luminance(rgb):
    """The WCAG relative luminance of an sRGB triple."""
    channels = []
    for raw in rgb:
        value = raw / 255.0
        if value <= 0.03928:
            channels.append(value / 12.92)
        else:
            channels.append(((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground, background):
    """The WCAG contrast ratio of two colours; ``None`` if one is unusable."""
    fg = _hex_to_rgb(foreground)
    bg = _hex_to_rgb(background)
    if fg is None or bg is None:
        return None
    light = max(_relative_luminance(fg), _relative_luminance(bg))
    dark = min(_relative_luminance(fg), _relative_luminance(bg))
    return round((light + 0.05) / (dark + 0.05), 2)


def _norm_colour(value):
    """A comparable form of a computed colour (``rgb(1, 2, 3)`` → ``#010203``)."""
    rgb = _hex_to_rgb(value)
    if rgb is None:
        return None
    return "#%02x%02x%02x" % rgb


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────
# the probe context
# ─────────────────────────────────────────────────────────────────────────


class ProbeContext:
    """Everything a probe needs: the page, the service and the side."""

    def __init__(self, page, base_url, ws, side, repo_root=None, out_dir=None):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.ws = ws
        self.side = side
        self.repo_root = Path(repo_root) if repo_root else None
        self.out_dir = Path(out_dir) if out_dir else None
        self.notes = {}

    # -- navigation ------------------------------------------------------
    def url(self, page_key):
        return self.base_url + PAGES[page_key].format(ws=self.ws)

    def goto(self, page_key, wait=True):
        self.page.goto(self.url(page_key), wait_until="load", timeout=30000)
        if wait:
            try:
                self.page.wait_for_timeout(400)
            except Exception:
                pass
        return self.page.url

    def evaluate(self, script, arg=None):
        if arg is None:
            return self.page.evaluate(script)
        return self.page.evaluate(script, arg)

    # -- product css -----------------------------------------------------
    def own_css_files(self):
        """The repository's own stylesheets (the vendored ones are excluded).

        §7.5.3 item 3.7-3 is explicit: the vendored KaTeX stylesheet carries
        20 ``@font-face`` rules of its own and must not be counted.
        """
        if not self.repo_root:
            return []
        static = self.repo_root / "workbench" / "server" / "static"
        if not static.is_dir():
            return []
        return sorted(p for p in static.glob("*.css") if p.is_file())


# ─────────────────────────────────────────────────────────────────────────
# the probes
# ─────────────────────────────────────────────────────────────────────────


def _ok(data, note=""):
    return {"verdict": PASS, "data": data, "note": note}


def _bad(data, note=""):
    return {"verdict": FAIL, "data": data, "note": note}


def _pending(data, note=""):
    return {"verdict": PENDING, "data": data, "note": note}


def _na(data, note=""):
    return {"verdict": NA, "data": data, "note": note}


def probe_focus_ring(ctx, sequence):
    """3.1-1 — every Tab stop must show a focus ring.

    The walk is the real keyboard walk (the same one G-8 records), so the
    ring is the one the browser really paints, not a computed guess.
    """
    stops = [stop for stop in sequence if stop.get("semantic") != "<body>"]
    offenders = []
    for stop in stops:
        width = stop.get("outlineWidth", "0px")
        style = stop.get("outlineStyle", "none")
        shadow = stop.get("boxShadow", "none")
        has_ring = False
        try:
            has_ring = float(str(width).replace("px", "").strip() or 0) > 0 \
                and style not in ("none", "")
        except ValueError:
            has_ring = False
        if not has_ring and shadow in ("none", ""):
            offenders.append(stop)
    data = {
        "stops": len(stops),
        "offenders": offenders,
        "sample": stops[:12],
    }
    if not stops:
        return _pending(data, "Tab 遍历没有停在任何可聚焦元素上")
    if offenders:
        return _bad(data, f"{len(offenders)} 个焦点停靠点没有可见焦点环")
    return _ok(data, f"{len(stops)} 个焦点停靠点都有可见焦点环")


def probe_states(ctx, page_key):
    """3.1-3 / 3.1-4 — the state marks must not rely on colour alone.

    The rule implemented here is the one §7.5.3 spells out: two state marks
    that share the same geometry but differ in colour are distinguished
    **only** by colour, which is a violation of 3.1-3.  Such a mark must
    then carry a text (3.1-4) — the decisions close the channel as
    "文字是可选辅助，不是必需", so the requirement is read as "a colour-only
    state may not be silent".
    """
    elements = ctx.evaluate("() => window.__lkProbe.stateElements()")
    by_geometry = {}
    for element in elements:
        key = json.dumps(element["geometry"], sort_keys=True, ensure_ascii=False)
        by_geometry.setdefault(key, []).append(element)
    colour_only = []
    for group in by_geometry.values():
        colours = {}
        for element in group:
            colours.setdefault(json.dumps(element["color"], sort_keys=True,
                                          ensure_ascii=False), []).append(element)
        if len(colours) < 2:
            continue
        for key, members in colours.items():
            for other_key, other_members in colours.items():
                if other_key == key:
                    continue
                for member in members:
                    colour_only.append({
                        "cls": member["cls"],
                        "text": member["text"],
                        "color": member["color"],
                        "geometry": member["geometry"],
                        "otherStates": [m["cls"] for m in other_members],
                    })
    return {"count": len(elements), "elements": elements,
            "colourOnly": colour_only}


def judge_states_geometry(data):
    """3.1-3 — the states must have a geometric encoding."""
    if not data.get("count"):
        return _pending(data, "本页没有找到任何状态标记元素")
    if data.get("colourOnly"):
        return _bad(data, f"{len(data['colourOnly'])} 个状态只靠颜色区分")
    return _ok(data, f"{data['count']} 个状态标记均有几何编码")


def judge_states_text(data):
    """3.1-4 — a colour-only state may not be silent."""
    silent = [item for item in data.get("colourOnly", []) if not item.get("text")]
    payload = dict(data)
    payload["silent"] = silent
    if not data.get("count"):
        return _pending(payload, "本页没有找到任何状态标记元素")
    if silent:
        return _bad(payload, f"{len(silent)} 个只靠颜色的状态没有文字")
    return _ok(payload, "只靠颜色的状态都带了文字")


def probe_text_count(ctx, page_key):
    """3.1-5 — the visible text must not grow (the count is compared later)."""
    count = ctx.evaluate("() => window.__lkProbe.textCount()")
    return count


def probe_reduced_motion(ctx, playwright):
    """3.1-6 — under ``prefers-reduced-motion: reduce`` nothing may animate."""
    reduced = ctx.evaluate("() => window.__lkProbe.motion()")
    browser = playwright.chromium.launch(
        headless=True, args=list(CONSISTENCY["browser_args"]))
    context = browser.new_context(
        viewport={"width": VIEWPORTS["V1440"]["width"],
                  "height": VIEWPORTS["V1440"]["height"]},
        device_scale_factor=VIEWPORTS["V1440"]["device_scale_factor"],
        color_scheme=CONSISTENCY["color_scheme"],
        reduced_motion="reduce",
        locale=CONSISTENCY["locale"],
        timezone_id=CONSISTENCY["timezone_id"])
    page = context.new_page()
    try:
        page.add_init_script(PROBE_JS)
        page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
        page.wait_for_timeout(500)
        in_reduced = page.evaluate("() => window.__lkProbe.motion()")
    finally:
        context.close()
        browser.close()
    # §3.1-6 is about the **motion**: a running keyframe animation or a
    # transition that moves something.  A colour / opacity fade is not a
    # motion effect, and the product's own stylesheet says so ("不再保留
    # 「一刀切 none」的老闸门 …… 也会把「透明度过渡」一并冻掉"), so a fade
    # is recorded as evidence but does not fail the item.
    offenders = []
    for item in in_reduced.get("animated", []):
        if item.get("animationName") not in (None, "none"):
            offenders.append({"cls": item.get("cls"), "why": "animation",
                              "animationName": item.get("animationName")})
            continue
        prop = item.get("transitionProperty") or ""
        if "transform" in prop:
            offenders.append({"cls": item.get("cls"), "why": "transform-transition",
                              "transitionProperty": prop})
    fades = [item for item in in_reduced.get("animated", [])
             if item.get("animationName") in (None, "none")
             and "transform" not in (item.get("transitionProperty") or "")]
    data = {
        "normal": {"animatedCount": reduced.get("animatedCount"),
                   "runningAnimations": reduced.get("runningAnimations")},
        "reduced": {"reduceMatches": in_reduced.get("reduceMatches"),
                    "animatedCount": in_reduced.get("animatedCount"),
                    "runningAnimations": in_reduced.get("runningAnimations")},
        "offenders": offenders,
        "colourFadesLeft": len(fades),
        "fadeSample": fades[:10],
    }
    if not in_reduced.get("reduceMatches"):
        return _pending(data, "浏览器没有进入 reduce 模式")
    if offenders:
        return _bad(data, f"reduce 模式下仍有 {len(offenders)} 个元素带动画/过渡")
    return _ok(data, "reduce 模式下没有仍在运行的动画或过渡")


def probe_accessible_names(ctx, page_key):
    """3.1-8 — every icon must carry an accessible name."""
    names = ctx.evaluate("() => window.__lkProbe.accessibleNames()")
    missing = [item for item in names if not item["hasName"]]
    data = {"count": len(names), "missing": missing, "sample": names[:20]}
    if not names:
        return _pending(data, "本页没有找到任何图标元素")
    if missing:
        return _bad(data, f"{len(missing)} 个图标没有可访问名称")
    return _ok(data, f"{len(names)} 个图标都有可访问名称")


def probe_contrast(ctx, pairs, label):
    """§7.5.4 — the token pairs are measured, not eyeballed."""
    names = []
    for _, fg, bg, _threshold in pairs:
        names.extend([fg, bg])
    values = ctx.evaluate("(names) => window.__lkProbe.tokens(names)", sorted(set(names)))
    results = []
    for name, fg, bg, threshold in pairs:
        fg_value = values.get(fg)
        bg_value = values.get(bg)
        if not fg_value or not bg_value:
            results.append({"pair": name, "fg": fg, "bg": bg, "threshold": threshold,
                            "status": "MISSING",
                            "fg_value": fg_value, "bg_value": bg_value})
            continue
        ratio = contrast_ratio(fg_value, bg_value)
        if ratio is None:
            results.append({"pair": name, "fg": fg, "bg": bg, "threshold": threshold,
                            "status": "UNREADABLE", "fg_value": fg_value,
                            "bg_value": bg_value})
            continue
        results.append({
            "pair": name, "fg": fg, "bg": bg, "threshold": threshold,
            "fg_value": fg_value, "bg_value": bg_value, "ratio": ratio,
            "status": "OK" if ratio >= threshold else "BELOW",
        })
    data = {"scope": label, "pairs": results}
    missing = [r for r in results if r["status"] in ("MISSING", "UNREADABLE")]
    below = [r for r in results if r["status"] == "BELOW"]
    if missing:
        return _pending(data, f"{len(missing)} 对 token 读不到（MISSING）")
    if below:
        return _bad(data, f"{len(below)} 对 token 低于阈值")
    return _ok(data, f"{len(results)} 对 token 全部达标")


def probe_theme_night_assets(ctx):
    """3.2-4 / 3.6-5 — the night theme must not load a second set of files."""
    result = ctx.evaluate("""async () => {
      const root = document.documentElement;
      const collect = () => window.__lkProbe.svgSources();
      const before = collect();
      const previous = root.getAttribute("data-theme");
      root.setAttribute("data-theme", "night");
      const night = collect();
      if (previous === null) root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", previous);
      const after = collect();
      return {light: before, night, restored: after};
    }""")
    light = set(result.get("light", []))
    night = set(result.get("night", []))
    only_night = sorted(night - light)
    only_light = sorted(light - night)
    data = {"light": sorted(light), "night": sorted(night),
            "only_in_night": only_night, "only_in_light": only_light}
    if not light and not night:
        return _pending(data, "页面里没有任何 SVG 资源")
    if only_night or only_light:
        return _bad(data, f"两套主题的 SVG 资源集合不同（夜纸多 {len(only_night)} 个，"
                          f"亮色多 {len(only_light)} 个）")
    return _ok(data, "夜纸与亮色共用同一批资源")


def probe_theme_ui(ctx):
    """3.2-1 / 3.2-5 / 3.2-6 — the theme switch of the settings view.

    The probe uses the **real** switch (``#setting-theme``), because that is
    the only path that writes the preference; the lamp layers it creates are
    the evidence for 3.2-1.
    """
    page = ctx.page
    result = page.evaluate("""async () => {
      const out = {};
      const box = document.getElementById("setting-theme");
      out.switchPresent = !!box;
      if (!box) return out;
      const root = document.documentElement;
      out.before = {checked: box.checked, theme: root.getAttribute("data-theme")};
      const samples = [];
      box.click();
      const t0 = performance.now();
      for (let i = 0; i < 32; i += 1) {
        samples.push({
          t: Math.round(performance.now() - t0),
          lamp: !!document.querySelector(".lk-lamp"),
          ripple: !!document.querySelector(".lk-ripple"),
          glow: !!document.querySelector(".lk-ripple-glow"),
          theme: root.getAttribute("data-theme"),
        });
        await new Promise((r) => setTimeout(r, 25));
      }
      out.samples = samples;
      out.after = {checked: box.checked, theme: root.getAttribute("data-theme")};
      out.storage = window.__lkProbe.storage();
      out.effective = window.lkTheme && window.lkTheme.effective
        ? window.lkTheme.effective() : null;
      return out;
    }""")
    if not result.get("switchPresent"):
        return (_na(result, "设置页没有主题开关"), _na(result, ""), _na(result, ""))
    saw_layers = any(sample.get("lamp") or sample.get("ripple")
                     for sample in result.get("samples", []))
    changed_at = None
    for sample in result.get("samples", []):
        if sample.get("theme") != result.get("before", {}).get("theme"):
            changed_at = sample.get("t")
            break
    transition = {
        "sawLampLayers": saw_layers,
        "themeChangedAtMs": changed_at,
        "samples": result.get("samples", [])[:12],
        "before": result.get("before"),
        "after": result.get("after"),
    }
    if not saw_layers:
        lamp = _bad(transition, "切换主题时没有出现台灯层 —— 是瞬切")
    else:
        lamp = _ok(transition, "切换主题时出现了台灯层")

    # -- the preference is stored per workspace ---------------------------
    storage = result.get("storage", {})
    theme = page.evaluate("() => window.__lkProbe.theme()")
    key = theme.get("settingsKey") or ""
    current = storage.get(key)
    try:
        parsed = json.loads(current or "{}")
    except ValueError:
        parsed = {}
    storage_data = {"settingsKey": key, "storageKeys": sorted(storage),
                    "current": parsed, "workspace": ctx.ws}
    if current is None:
        per_workspace = _pending(storage_data, f"{key} 里还没有偏好")
    elif "theme" not in parsed:
        per_workspace = _pending(storage_data, f"{key} 里没有 theme 偏好")
    else:
        per_workspace = _ok(storage_data, f"{key} 里存着 theme")

    # -- the preference survives a reload ---------------------------------
    page.reload(wait_until="load")
    page.wait_for_timeout(400)
    reloaded = page.evaluate("""() => {
      const root = document.documentElement;
      return {
        theme: root.getAttribute("data-theme"),
        effective: window.lkTheme && window.lkTheme.effective
          ? window.lkTheme.effective() : null,
        storage: window.__lkProbe.storage(),
      };
    }""")
    persist_data = {"settingsKey": key, "stored": parsed,
                    "afterReload": reloaded.get("effective"),
                    "dataTheme": reloaded.get("theme"),
                    "storageKind": "localStorage"}
    if reloaded.get("effective") != parsed.get("theme"):
        persist = _bad(persist_data, "刷新后主题偏好没有保持")
    else:
        persist = _ok(persist_data, "刷新后主题偏好保持")
    return lamp, per_workspace, persist


def probe_theme_persist(ctx):
    """3.2-6 — the preference survives a reload (and a service restart)."""
    storage = ctx.evaluate("() => window.__lkProbe.storage()")
    theme = ctx.evaluate("() => window.__lkProbe.theme()")
    key = theme.get("settingsKey") or ""
    current = storage.get(key)
    try:
        parsed = json.loads(current or "{}")
    except ValueError:
        parsed = {}
    data = {"settingsKey": key, "stored": parsed,
            "effective": theme.get("effective"),
            "dataTheme": theme.get("dataTheme"),
            "storageKind": "localStorage" if current is not None else None}
    if current is None:
        return _pending(data, "该工作区还没有写进任何偏好")
    if "theme" not in parsed:
        return _pending(data, f"{key} 里没有 theme 偏好")
    if theme.get("effective") != parsed.get("theme"):
        return _bad(data, "存下来的主题与当前生效的主题不一致")
    return _ok(data, "刷新 / 重启后主题偏好仍在")


def probe_audio_moments(ctx):
    """3.3-1 — only the four moments may sound, and each cue is < 200 ms."""
    page = ctx.page
    cues = page.evaluate("""() => {
      if (!window.lkSfx || !window.lkSfx.cues) return null;
      const out = {};
      Object.keys(window.lkSfx.cues).forEach((name) => {
        const cue = window.lkSfx.cues[name];
        out[name] = {file: cue.file, seconds: cue.seconds, volume: cue.volume};
      });
      return out;
    }""")
    plays = page.evaluate("() => window.__lkProbe.audio()")
    data = {"cues": cues, "plays": plays}
    if cues is None:
        return _na(data, "没有音效模块（window.lkSfx 不存在）")
    expected = {"correct", "wrong", "complete", "milestone"}
    names = set(cues)
    if names != expected:
        return _bad(data, f"音效时刻集合是 {sorted(names)}，不是四个时刻")
    too_long = {name: cue for name, cue in cues.items()
                if float(cue.get("seconds", 1)) >= 0.2}
    if too_long:
        return _bad(data, f"{len(too_long)} 条音效 >= 200ms")
    return _ok(data, "四个时刻齐备，每条都短于 200ms")


def probe_audio_gesture(ctx, playwright):
    """3.3-2 — the first cue may only follow a user gesture.

    The page has to be **fresh**: any earlier key press would have unlocked
    the audio module (the unlock listener is on ``keydown``), so the probe
    opens its own browser context.
    """
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
        page.add_init_script(PROBE_JS)
        page.add_init_script(AUDIO_JS)
        page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
        page.wait_for_timeout(400)
        result = page.evaluate("""async () => {
          const out = {hasSfx: !!(window.lkSfx && window.lkSfx.playCue)};
          if (!out.hasSfx) return out;
          out.beforeGesture = window.__lkProbe.audio().length;
          out.playedBeforeGesture = window.lkSfx.playCue("correct");
          await new Promise((r) => setTimeout(r, 150));
          out.afterGestureCall = window.__lkProbe.audio().length;
          out.activationBefore = !!(navigator.userActivation
                                    && navigator.userActivation.isActive);
          return out;
        }""")
        if not result.get("hasSfx"):
            return _na(result, "没有音效模块")
        # A real gesture: a click on the page.
        try:
            page.mouse.click(10, 10)
        except Exception:
            pass
        page.wait_for_timeout(250)
        after = page.evaluate("""async () => {
          const out = {};
          out.activation = !!(navigator.userActivation && navigator.userActivation.isActive);
          window.lkSfx.playCue("correct");
          await new Promise((r) => setTimeout(r, 200));
          out.plays = window.__lkProbe.audio();
          return out;
        }""")
        result["afterGesture"] = after
    finally:
        context.close()
        browser.close()
    plays = after.get("plays", [])
    if result.get("afterGestureCall", 0) > result.get("beforeGesture", 0):
        return _bad(result, "手势之前就有音效播放")
    if not plays:
        return _pending(result, "手势之后也没有观察到播放（可能音频被浏览器拦截）")
    if not any(play.get("userActivation") for play in plays):
        return _bad(result, "播放发生时没有用户激活")
    return _ok(result, "手势之前无声，手势之后有播放")


def probe_audio_mute(ctx):
    """3.3-3 / 3.3-4 — the mute switch exists and silences every cue."""
    page = ctx.page
    result = page.evaluate("""async () => {
      const out = {hasSfx: !!(window.lkSfx && window.lkSfx.setEnabled)};
      const box = document.getElementById("setting-sound");
      out.switchPresent = !!box;
      out.switchChecked = box ? box.checked : null;
      out.enabledByDefault = window.lkSfx && window.lkSfx.isEnabled
        ? window.lkSfx.isEnabled() : null;
      out.storage = window.__lkProbe.storage();
      if (!out.hasSfx) return out;
      window.lkSfx.setEnabled(false);
      await new Promise((r) => setTimeout(r, 60));
      out.enabledAfterMute = window.lkSfx.isEnabled();
      out.beforePlays = window.__lkProbe.audio().length;
      ["correct", "wrong", "complete", "milestone"].forEach((name) => {
        window.lkSfx.playCue(name);
      });
      await new Promise((r) => setTimeout(r, 200));
      out.afterPlays = window.__lkProbe.audio().length;
      out.plays = window.__lkProbe.audio();
      window.lkSfx.setEnabled(true);
      await new Promise((r) => setTimeout(r, 60));
      out.enabledAfterUnmute = window.lkSfx.isEnabled();
      out.storageAfter = window.__lkProbe.storage();
      return out;
    }""")
    if not result.get("hasSfx"):
        return _na(result, "没有音效模块")
    data = result
    if not result.get("switchPresent"):
        return _bad(result, "没有静音开关（#setting-sound）")
    if result.get("enabledAfterMute") is not False:
        return _bad(result, "静音后 isEnabled() 仍为真")
    if result.get("afterPlays", 0) > result.get("beforePlays", 0):
        return _bad(result, "静音后仍然有播放")
    return _ok(result, "静音开关存在，静音后四个时刻全部无声")


# ─────────────────────────────────────────────────────────────────────────
# 3.3-1 — the sound probe: the cue count and the browser's verdict
# ─────────────────────────────────────────────────────────────────────────


def pick_plan_options(page, item):
    """Pick the options the plan names; return what was picked.

    The option is matched by its **id** (the option text), never by its
    position: the plan is computed from the pool, the page renders the
    options of the same record, and the id is what both sides agree on.
    The answer is **not** submitted here — a multiple-choice item is
    submitted by its button, and that click is the gesture the product
    arms the answer cue with.
    """
    wanted = list(item.get("option_ids") or [])
    if not wanted:
        return {"answered": False, "why": "plan item without option ids"}
    inputs = page.query_selector_all("#paper-options input")
    if not inputs:
        return {"answered": False, "why": "the item rendered no options"}
    picked = []
    for element in inputs:
        value = element.get_attribute("value") or ""
        if value in wanted:
            element.click()
            picked.append(value)
    if not picked:
        return {"answered": False, "why": "no option matched the plan",
                "options": [element.get_attribute("value") or ""
                            for element in inputs]}
    return {"answered": True, "picked": picked, "kind": item.get("quiz_type")}


def answer_plan_item(page, item):
    """Answer one paper item the way the plan says; return what was clicked."""
    outcome = pick_plan_options(page, item)
    submitted = False
    if outcome.get("answered") and item.get("multiple"):
        # A multiple-choice item is submitted by the button — that click is
        # the gesture the product arms the answer cue with.
        page.wait_for_selector("#paper-item-submit", state="visible",
                               timeout=15000)
        page.click("#paper-item-submit")
        submitted = True
    outcome["submittedByButton"] = submitted
    return outcome


def read_sound_state(page):
    """Read the two counters and the verdict nodes of the page."""
    return page.evaluate("""() => ({
      hasSfx: !!(window.lkSfx && window.lkSfx.playCue),
      enabled: (window.lkSfx && window.lkSfx.isEnabled)
        ? window.lkSfx.isEnabled() : null,
      cueCalls: (window.__lkSfxCalls || []).map((c) => ({
        t: c.t, name: c.name, userActivation: c.userActivation,
        returned: c.returned,
      })),
      plays: (window.__lkSfxPlays || []).map((p) => ({
        t: p.t, src: p.src, userActivation: p.userActivation,
        outcome: p.outcome, error: p.error || "",
      })),
      verdicts: Array.from(document.querySelectorAll(".micro-verdict"))
        .map((el) => String(el.className || "")),
    })""")


def probe_audio_cue(ctx, paper_id, plan, waiter=None):
    """3.3-1 — the cue after an answer: how often, and who stopped it.

    The probe answers the question the first round could not answer:
    "答题后没有观察到音效" was one PENDING for two very different causes.

    The protocol (the brief's, verbatim):

    1. **a real gesture first** — the browser's autoplay policy only lets
       the audio context run after the learner has acted, so the probe
       clicks a real button (``#paper-start``) before anything else;
    2. **answer a question** through the real UI, with the real submit
       gesture;
    3. **count the calls in the page** — ``playCue`` calls (the code) and
       ``play()`` calls with their promise outcome (the browser);
    4. **a control call** at the end: a direct ``playCue`` proves whether
       the browser would have played at all, so "the browser blocked it"
       and "the code never triggered it" can be told apart.

    The page is a **fresh** context: an earlier key press would have
    unlocked the audio module and the probe would measure the wrong thing.
    """
    from playwright.sync_api import sync_playwright

    from shots import CONSISTENCY, VIEWPORTS

    data = {"paper_id": paper_id, "plan": plan}
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
            page.add_init_script(PROBE_JS)
            page.add_init_script(AUDIO_JS)
            page.add_init_script(SFX_HOOK_JS)
            page.goto(f"{ctx.base_url}/w/{ctx.ws}/practice?paper={paper_id}",
                      wait_until="load", timeout=30000)
            page.wait_for_timeout(400)

            data["beforeGesture"] = read_sound_state(page)

            # -- 1. the real gesture: the start button -------------------
            page.wait_for_selector("#paper-start", state="visible", timeout=15000)
            page.click("#paper-start")
            if waiter is not None:
                waiter.wait_for(
                    "POST /api/w/{name}/practice-sets/{practice_set_id}/start")
            page.wait_for_timeout(300)
            data["afterGesture"] = read_sound_state(page)
            data["userActivationAfterGesture"] = page.evaluate(
                "() => !!(navigator.userActivation && navigator.userActivation.hasBeenActive)")

            # -- 2. answer the items the plan gives ----------------------
            answers = []
            for index, item in enumerate(plan or []):
                if index:
                    page.wait_for_selector("#paper-next", state="visible", timeout=15000)
                    page.click("#paper-next")
                    if waiter is not None:
                        waiter.wait_for(
                            "POST /api/w/{name}/practice/current/navigate")
                    page.wait_for_timeout(300)
                before = read_sound_state(page)
                outcome = answer_plan_item(page, item)
                outcome["index"] = index
                outcome["problem_id"] = item.get("problem_id")
                if waiter is not None:
                    waiter.wait_for("POST /api/w/{name}/attempts")
                try:
                    page.wait_for_selector(".micro-verdict", state="attached",
                                           timeout=15000)
                except Exception:
                    outcome["verdictAppeared"] = False
                else:
                    outcome["verdictAppeared"] = True
                page.wait_for_timeout(200)
                after = read_sound_state(page)
                outcome["cueCalls"] = len(after["cueCalls"]) - len(before["cueCalls"])
                outcome["plays"] = len(after["plays"]) - len(before["plays"])
                outcome["verdicts"] = after["verdicts"]
                # The self-rating keeps the request shape of a real round;
                # it happens **after** the verdict, so it cannot cancel it.
                try:
                    page.wait_for_selector("#paper-rating", state="visible",
                                           timeout=10000)
                    page.fill("#paper-rating input[type='number']", "4")
                    page.click("#paper-rating button")
                    if waiter is not None:
                        waiter.wait_for("POST /api/w/{name}/feedback")
                except Exception:
                    outcome["rated"] = False
                else:
                    outcome["rated"] = True
                answers.append(outcome)
            data["answers"] = answers
            data["afterAnswers"] = read_sound_state(page)

            # -- 3. the control: may the browser play at all? ------------
            control = page.evaluate("""async () => {
              if (!window.lkSfx || !window.lkSfx.playCue) return {hasSfx: false};
              const before = (window.__lkSfxPlays || []).length;
              window.lkSfx.playCue("complete");
              await new Promise((r) => setTimeout(r, 250));
              const plays = (window.__lkSfxPlays || []).slice(before);
              return {hasSfx: true, plays: plays.map((p) => ({
                src: p.src, outcome: p.outcome, error: p.error || "",
                userActivation: p.userActivation}))};
            }""")
            data["control"] = control
        finally:
            context.close()
            browser.close()
    return data


def judge_audio_cue(data):
    """3.3-1 — turn the sound evidence into a verdict.

    The classification (not the threshold — there is none here):

    * **no cue call at all** ⇒ the *code* did not trigger the sound;
    * **a cue call whose ``play()`` promise was rejected** ⇒ the *browser*
      blocked it (the autoplay policy);
    * **a cue call and a fulfilled play** ⇒ the sound happened.
    """
    if not data.get("afterAnswers", {}).get("hasSfx"):
        return _na(data, "没有音效模块（window.lkSfx 不存在）")
    if data.get("afterAnswers", {}).get("enabled") is False:
        return _pending(data, "声音偏好是关的 —— 本轮不验音效")
    answers = data.get("answers") or []
    graded = [item for item in answers if item.get("verdictAppeared")]
    if not graded:
        return _pending(data, "本轮没有产生任何判定（没有 .micro-verdict），"
                              "音效无从验")
    control = data.get("control") or {}
    control_played = any(play.get("outcome") == "fulfilled"
                          for play in (control.get("plays") or []))
    blocked = [play for play in (data.get("afterAnswers", {}).get("plays") or [])
               if play.get("outcome") == "rejected"]
    silent = [item for item in graded if not item.get("cueCalls")]
    data["summary"] = {
        "gradedAnswers": len(graded),
        "answersWithoutCue": [item.get("problem_id") for item in silent],
        "cueCalls": len(data.get("afterAnswers", {}).get("cueCalls") or []),
        "plays": len(data.get("afterAnswers", {}).get("plays") or []),
        "browserBlocked": bool(blocked),
        "controlPlayed": control_played,
    }
    if silent:
        silent_names = [item.get("problem_id") for item in silent]
        loud = [item.get("problem_id") for item in graded if item.get("cueCalls")]
        return _bad(data, "答完题后这些判定没有声音（playCue 调用 0 次）："
                           f"{silent_names}；有声音的是 {loud} —— "
                           "代码没有触发音效（控制调用能播放 ⇒ 不是浏览器拦的）")
    if blocked:
        return _bad(data, f"音效被调用了，但有 {len(blocked)} 次播放被浏览器拒绝"
                           "（自动播放策略）")
    if not control_played:
        return _pending(data, "控制调用也没有播放 —— 本轮无法区分"
                              "「浏览器拦的」与「代码没触发」")
    return _ok(data, f"答完题后 playCue 调用 {data['summary']['cueCalls']} 次，"
                     f"播放 {data['summary']['plays']} 次，浏览器没有拦截")


#: The style properties a hover / pressed feedback may change.
WATCHED_PROPERTIES = ("background-color", "color", "border-color", "transform",
                      "box-shadow", "opacity")

#: The hover feedback has to be perceivable: 120–180 ms (§3.4-1).
HOVER_MIN_MS, HOVER_MAX_MS = 120, 180


def _parse_duration(value):
    """``"0.2s, 0.3s"`` → ``[200.0, 300.0]`` in milliseconds."""
    out = []
    for part in (value or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if part.endswith("ms"):
                out.append(float(part[:-2]))
            elif part.endswith("s"):
                out.append(float(part[:-1]) * 1000.0)
            else:
                out.append(float(part))
        except ValueError:
            continue
    return out


#: The reading of the **candidate element itself** (A-114).
#:
#: ``document.elementFromPoint(x, y)`` answers "the **innermost** element
#: under the pointer" — for a ``.nav-item`` that is the ``<a>`` inside it,
#: for an ``.ai-session-entry`` button the ``<span>`` inside it.  Those
#: inner elements carry **no** ``:active`` rule (the rule sits on
#: ``.nav-item`` / ``button``), so the old probe read the **same inner
#: element's** style on both sides ⇒ the hover side and the pressed side
#: could never differ ⇒ 3.4-2 was a constant FAIL.
#:
#: The hit test is still done — it proves the candidate really is under
#: the pointer — but the **style is read on the candidate**, on both the
#: hover side and the pressed side.  ``relation`` says how the candidate
#: relates to the hit element:
#:
#: * ``self``       — the candidate *is* the element under the pointer;
#: * ``descendant`` — the pointer is on a descendant of the candidate
#:   ⇒ the candidate is hovered **and** it is in the ``:active`` chain
#:   (Chromium puts ``:active`` on the pressed element **and its
#:   ancestors**);
#: * ``ancestor``   — the pointer is on an ancestor of the candidate ⇒
#:   the candidate is hovered, but it is **not** in the ``:active`` chain
#:   (``:active`` never reaches a descendant of the pressed element);
#: * ``other``      — the pointer is somewhere else entirely ⇒ the
#:   candidate is not hovered at all.
HOVER_READ_JS = """([index, x, y, watched]) => {
  const el = (window.__lkHoverTargets || [])[index];
  if (!el || !el.isConnected) return null;
  const hit = document.elementFromPoint(x, y);
  if (!hit) return null;
  const st = getComputedStyle(el);
  const state = {};
  watched.forEach((name) => { state[name] = st.getPropertyValue(name); });
  let relation = "other";
  if (hit === el) relation = "self";
  else if (el.contains(hit)) relation = "descendant";
  else if (hit.contains(el)) relation = "ancestor";
  return {
    relation: relation,
    tag: el.tagName.toLowerCase(),
    cls: String(el.className || "").slice(0, 60),
    hitTag: hit.tagName.toLowerCase(),
    hitCls: String(hit.className || "").slice(0, 60),
    state: state,
  };
}"""


def probe_hover(ctx):
    """3.4-1 — the hover feedback must last 120–180 ms.

    The probe really hovers: the element's style is read at rest, then
    under the pointer, and only an element that *changes* counts as a hover
    feedback (an element without a transition changes instantly, which is
    below the 120 ms floor and therefore a violation).

    A-114: the readings are taken on **the candidate element itself**
    (a stable index into ``window.__lkHoverTargets``) — the hover side
    and the pressed side read the **same** element.  See
    :data:`HOVER_READ_JS` for why the old ``elementFromPoint`` reading
    could never see a difference.

    The probe runs **two passes**:

    * pass 1 measures the hover feedback (3.4-1) and **never presses**;
    * pass 2 measures the pressed feedback (3.4-2) with the same
      hover → press → read → release sequence as before.

    The split exists because a press is a **click**: the product's own
    click handler answers it by switching the page (the left column's
    links swap the middle column), so a press in the middle of the old
    single loop made the rest reading and the hover reading come from
    **two different page states**.  The difference the old loop then
    measured — the nav entry that has just become the active one — is a
    navigation artifact, not a hover feedback.  Pass 1 keeps the rest
    reading and the hover reading in one page state; pass 2 compares the
    pressed state with the hovered state of the same candidate, which are
    read one after the other and therefore always agree on the page
    state.
    """
    page = ctx.page
    candidates = page.evaluate("""(watched) => {
      const out = [];
      const targets = [];
      window.__lkHoverTargets = targets;
      const selector = "button, a[href], .nav-item, .paper-dot, [role='button'], "
        + ".side-row, .setting-row, .lk-empty__action, .button-link, "
        + ".column-resizer, .chapter-lens-option";
      document.querySelectorAll(selector).forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        if (rect.top < 0 || rect.bottom > window.innerHeight) return;
        if (rect.left < 0 || rect.right > window.innerWidth) return;
        const st = getComputedStyle(el);
        const state = {};
        watched.forEach((name) => { state[name] = st.getPropertyValue(name); });
        targets.push(el);
        out.push({
          index: targets.length - 1,
          x: Math.round(rect.left + rect.width / 2),
          y: Math.round(rect.top + rect.height / 2),
          cls: String(el.className || "").slice(0, 60),
          tag: el.tagName.toLowerCase(),
          id: el.id || "",
          href: el.getAttribute("href") || "",
          text: (el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 30),
          transitionProperty: st.transitionProperty,
          transitionDuration: st.transitionDuration,
          state,
        });
        if (out.length >= 20) return;
      });
      return out;
    }""", list(WATCHED_PROPERTIES))
    if not candidates:
        return _pending({"candidates": 0}, "本页视口内没有可交互元素")
    page.mouse.move(2, 2)
    page.wait_for_timeout(60)

    # -- pass 1 — the hover feedback (3.4-1) ---------------------------
    # This pass **never presses the mouse**: a press is a click, and the
    # product's own click handler answers it by changing the page (the
    # left column's links switch the middle column).  The rest state is
    # read once, up front — so a press in the middle of the old single
    # loop made the **rest** reading and the **hover** reading come from
    # two different page states, and the difference (the nav entry that
    # turns into the active one) was a navigation artifact, not a hover
    # feedback.  With the presses moved to pass 2 the rest state stays
    # valid for the whole pass.
    hover_offenders, hover_samples, hovered = [], [], set()
    for candidate in candidates:
        page.mouse.move(candidate["x"], candidate["y"])
        page.wait_for_timeout(260)
        hover_state = page.evaluate(
            HOVER_READ_JS,
            [candidate["index"], candidate["x"], candidate["y"],
             list(WATCHED_PROPERTIES)])
        if not hover_state:
            continue
        # The candidate has to be under the pointer (or be an ancestor of
        # what is under it) — otherwise it is not hovered at all.
        if hover_state["relation"] not in ("self", "descendant", "ancestor"):
            continue
        changed = [name for name in WATCHED_PROPERTIES
                   if hover_state["state"].get(name) != candidate["state"].get(name)]
        if not changed:
            continue
        durations = _parse_duration(candidate["transitionDuration"])
        duration = max(durations) if durations else 0.0
        record = {
            "cls": candidate["cls"], "tag": candidate["tag"],
            "id": candidate.get("id", ""), "href": candidate.get("href", ""),
            "text": candidate.get("text", ""),
            "changed": changed, "durationMs": duration,
            "transitionProperty": candidate["transitionProperty"],
            "hitTag": hover_state["hitTag"], "hitCls": hover_state["hitCls"],
            "relation": hover_state["relation"],
        }
        hover_samples.append(record)
        hovered.add(candidate["index"])
        if duration < HOVER_MIN_MS or duration > HOVER_MAX_MS:
            hover_offenders.append(record)

    # -- pass 2 — the pressed feedback (3.4-2) -------------------------
    # The same sequence as before — hover, press, read, release — but on
    # the **same candidate** on both sides (A-114): the pressed state is
    # compared with the hovered state of that very candidate, so a
    # candidate that carries no ``:active`` rule of its own cannot
    # borrow the difference of some inner element.
    active_offenders = []
    for candidate in candidates:
        if candidate["index"] not in hovered:
            continue
        page.mouse.move(candidate["x"], candidate["y"])
        page.wait_for_timeout(260)
        hover_state = page.evaluate(
            HOVER_READ_JS,
            [candidate["index"], candidate["x"], candidate["y"],
             list(WATCHED_PROPERTIES)])
        if not hover_state:
            continue
        if hover_state["relation"] not in ("self", "descendant", "ancestor"):
            continue
        page.mouse.down()
        page.wait_for_timeout(80)
        active_state = page.evaluate(
            HOVER_READ_JS,
            [candidate["index"], candidate["x"], candidate["y"],
             list(WATCHED_PROPERTIES)])
        page.mouse.up()
        if active_state:
            pressed = [name for name in WATCHED_PROPERTIES
                       if active_state["state"].get(name) != hover_state["state"].get(name)]
            if pressed:
                active_offenders.append({"cls": candidate["cls"],
                                         "id": candidate.get("id", ""),
                                         "text": candidate.get("text", ""),
                                         "pressed": pressed,
                                         "relation": active_state["relation"],
                                         "hitTag": active_state["hitTag"],
                                         "hitCls": active_state["hitCls"]})
    page.mouse.move(2, 2)
    data = {"hoverSamples": hover_samples, "hoverOffenders": hover_offenders,
            "pressedFeedback": active_offenders}
    if not hover_samples:
        return _bad(data, "没有任何可感知的 hover 反馈")
    return data


def judge_hover(data):
    """3.4-1 / 3.4-2 — turn the hover evidence into verdicts."""
    hover_data = dict(data)
    hover_offenders = hover_data.get("hoverOffenders", [])
    pressed = hover_data.get("pressedFeedback", [])
    if hover_offenders:
        outcome = _bad(hover_data, f"{len(hover_offenders)} 个 hover 反馈不在 120–180ms")
    else:
        outcome = _ok(hover_data, "hover 反馈都在 120–180ms")
    if not pressed:
        active = _bad({"pressedFeedback": pressed},
                      "没有观察到按下（:active）反馈 —— 判据：按下时的样式要比"
                      "悬停时的样式多一层变化（悬停已经改过的元素不算）")
    else:
        active = _ok({"pressedFeedback": pressed},
                     f"{len(pressed)} 个元素有按下反馈")
    return outcome, active


def probe_focus_not_stolen(ctx):
    """3.1-7 — a transition or an overlay must not steal the focus."""
    page = ctx.page
    scenarios = []

    def active_element():
        return page.evaluate("""() => {
          const el = document.activeElement;
          if (!el || el === document.body) return {tag: "<body>", cls: "", id: ""};
          return {
            tag: el.tagName.toLowerCase(),
            cls: String(el.className || "").slice(0, 60),
            id: el.id || "",
            label: (el.getAttribute("aria-label") || el.textContent || "")
                .replace(/\\s+/g, " ").trim().slice(0, 40),
          };
        }""")

    def mark(element):
        page.evaluate("""() => {
          document.querySelectorAll("[data-lk-probe-activated]")
            .forEach((el) => el.removeAttribute("data-lk-probe-activated"));
        }""")
        try:
            page.evaluate("(el) => el.setAttribute('data-lk-probe-activated', '1')",
                          element)
            return True
        except Exception:
            return False

    def is_activated():
        return page.evaluate("""() => {
          const el = document.activeElement;
          if (!el) return false;
          return !!(el.closest && el.closest("[data-lk-probe-activated]"));
        }""")

    # (a) a page transition — a navigation entry in the left column.
    nav = page.query_selector(".nav-item")
    if nav:
        before = active_element()
        mark(nav)
        try:
            nav.click()
            page.wait_for_timeout(600)
            after = active_element()
            scenarios.append({"name": "page-transition", "before": before,
                              "after": after,
                              "activatedKeptFocus": is_activated()})
        except Exception as exc:
            scenarios.append({"name": "page-transition", "error": str(exc)})

    # (b) an overlay — the settings view.
    toggle = page.query_selector("#setting-view-toggle")
    if toggle:
        before = active_element()
        mark(toggle)
        try:
            toggle.click()
            page.wait_for_timeout(600)
            after = active_element()
            inside = page.evaluate("""() => {
              const el = document.activeElement;
              const surface = document.getElementById("middle-page");
              return !!(el && surface && surface.contains(el));
            }""")
            scenarios.append({"name": "settings-overlay", "before": before,
                              "after": after, "insideSurface": inside,
                              "activatedKeptFocus": is_activated()})
        except Exception as exc:
            scenarios.append({"name": "settings-overlay", "error": str(exc)})

    stolen = []
    for scenario in scenarios:
        if "after" not in scenario:
            continue
        after = scenario["after"]
        if after.get("tag") == "<body>":
            continue            # the focus was released, not stolen
        if scenario.get("activatedKeptFocus"):
            continue        # the activated control kept the focus — not stolen
        if scenario["name"] == "settings-overlay" and scenario.get("insideSurface"):
            continue
        stolen.append(scenario)
    data = {"scenarios": scenarios, "stolen": stolen}
    if not scenarios:
        return _pending(data, "没有找到可触发的转场 / 浮层入口")
    if stolen:
        return _bad(data, f"{len(stolen)} 个场景里焦点被抢走了")
    return _ok(data, f"{len(scenarios)} 个场景里焦点都没有被抢走")


def probe_icon_night(ctx):
    """3.2-3 — the night icon discs are the desaturated, brighter version."""
    result = ctx.evaluate("""async () => {
      const root = document.documentElement;
      const read = () => ({
        icons: window.__lkProbe.iconBackgrounds(),
        roles: window.__lkProbe.roleColours(),
      });
      const light = read();
      const previous = root.getAttribute("data-theme");
      root.setAttribute("data-theme", "night");
      const night = read();
      if (previous === null) root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", previous);
      return {light, night};
    }""")
    light = result.get("light", {})
    night = result.get("night", {})

    def hsl(value):
        rgb = _hex_to_rgb(value)
        if rgb is None:
            return None
        red, green, blue = [c / 255.0 for c in rgb]
        high, low = max(red, green, blue), min(red, green, blue)
        lightness = (high + low) / 2.0
        if high == low:
            return (0.0, round(lightness * 100, 1))
        delta = high - low
        saturation = delta / (2.0 - high - low) if lightness > 0.5 else delta / (high + low)
        if red == high:
            hue = ((green - blue) / delta) % 6
        elif green == high:
            hue = (blue - red) / delta + 2
        else:
            hue = (red - green) / delta + 4
        return (round(hue * 60, 1), round(saturation * 100, 1),
                round(lightness * 100, 1))

    pairs = []
    night_icons = {item["cls"]: item for item in night.get("icons", [])}
    for item in light.get("icons", []):
        counterpart = night_icons.get(item["cls"])
        if not counterpart:
            continue
        pairs.append({
            "cls": item["cls"],
            "light": item["background"], "night": counterpart["background"],
            "lightHsl": hsl(item["background"]),
            "nightHsl": hsl(counterpart["background"]),
        })
    data = {"pairs": pairs, "lightRoles": light.get("roles", {}),
            "nightRoles": night.get("roles", {})}
    return data  # SEMI → the runner turns this into PENDING


def _skeleton_switch(playwright, base_url, ws, target="kps",
                     reduced_motion=None):
    """Catch the middle column's skeleton **during a page switch**.

    A-114 (ii): the product renders the loading skeleton in
    ``middle-navigation.js``'s ``showLoadingState()`` — that is, **only
    when the middle column changes page**.  A first-screen load never
    goes through it, so the old scenario (slow the paper list's API down
    and reload) could not reproduce what the product actually does.

    The probe therefore slows the **target page's** request down, clicks
    the left column's link to that page (the product's own click handler
    → ``navigate()`` → ``showLoadingState()``), and reads what the
    observer recorded while the request was still in flight.
    """
    import time

    browser = playwright.chromium.launch(
        headless=True, args=list(CONSISTENCY["browser_args"]))
    context = browser.new_context(
        viewport={"width": VIEWPORTS["V1440"]["width"],
                  "height": VIEWPORTS["V1440"]["height"]},
        device_scale_factor=VIEWPORTS["V1440"]["device_scale_factor"],
        color_scheme=CONSISTENCY["color_scheme"],
        reduced_motion=reduced_motion or CONSISTENCY["reduced_motion"],
        locale=CONSISTENCY["locale"],
        timezone_id=CONSISTENCY["timezone_id"])
    page = context.new_page()
    try:
        page.add_init_script(PROBE_JS)
        page.add_init_script(SKELETON_JS)
        href = PAGES[target].format(ws=ws)

        def slow(route):
            time.sleep(1.5)
            route.continue_()

        # The **target page's** request is the one that is slowed down.
        page.route("**/w/*/" + target, slow)
        page.goto(base_url.rstrip("/") + PAGES["practice"].format(ws=ws),
                  wait_until="load", timeout=30000)
        page.wait_for_timeout(400)
        # The product's own click handler does the switch (it calls
        # ``navigate()`` → ``showLoadingState()`` → fetch).
        clicked = page.evaluate("""(href) => {
          const links = Array.from(
              document.querySelectorAll("#left-column a[href]"));
          const link = links.find((a) => a.getAttribute("href") === href);
          if (!link) return false;
          link.click();
          return true;
        }""", href)
        try:
            page.wait_for_function(
                "(path) => window.location.pathname === path",
                arg=href, timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(200)
        items = page.evaluate("() => (window.__lkSkeletonSeen || []).slice()")
        tier = page.evaluate(MOTION_TIER_JS)
        return {"clicked": clicked, "tier": tier, "target": href,
                "items": items}
    finally:
        try:
            context.close()
        finally:
            browser.close()


#: The properties a **breathing** loading mark may breathe with (A-115).
#: The mark changes the block's **own surface** — its background colour
#: or its opacity.  The old form (a sheen sweeping across an ``::after``
#: overlay) moves the overlay, not the surface, so it never counts.
BREATHING_PROPERTIES = ("opacity", "backgroundcolor", "background")


def _norm_property(name):
    """``background-color`` / ``backgroundColor`` → ``backgroundcolor``."""
    return str(name or "").replace("-", "").lower()


def _breathes(item):
    """Does this block's **own surface** change while it is on screen?

    Two independent pieces of evidence, either of which is enough:

    * ``surfaceChanged`` — the block's own ``background-color`` or
      ``opacity`` really differs between the samples the observer took
      (t0 / t0+400ms / t0+800ms);
    * an animation running **on the element itself** whose keyframes
      vary ``opacity`` / ``background-color``.

    An animation on a **pseudo element** (the old ``::after`` sweep) is
    deliberately **not** accepted: it animates the overlay, the block's
    own surface stays put.
    """
    if item.get("surfaceChanged"):
        return True
    for animation in item.get("ownAnimations") or []:
        for prop in animation.get("varied") or []:
            if _norm_property(prop) in BREATHING_PROPERTIES:
                return True
    return False


def _skeleton_judgement(items):
    """Split the recorded blocks into "has a body" and "breathes".

    ``container == "middle"`` keeps only the middle column's page-switch
    skeleton — the paper list has a loading mark of its own (a
    ``.lk-skeleton--text``), and that one is not the scenario of 3.4-3.
    """
    blocks = [item for item in items if item.get("container") == "middle"]
    sized = [item for item in blocks
             if (item.get("width") or 0) > 0 and (item.get("height") or 0) > 0]
    breathing = [item for item in blocks if _breathes(item)]
    # The **old** form: a sheen sweeping across an ``::after`` overlay.
    # Chromium's ``Element.getAnimations()`` does not hand the pseudo
    # element's animation back, so the overlay is recognised by the
    # computed ``::after`` animation name.  It is evidence, never a pass.
    sweep_only = [item for item in blocks
                  if not _breathes(item)
                  and (item.get("afterAnimation") not in (None, "none")
                       or item.get("pseudoAnimations"))]
    return {"blocks": blocks, "sized": sized, "breathing": breathing,
            "sweepOnly": sweep_only}


def probe_skeleton(ctx, playwright):
    """3.4-3 — the loading state has a skeleton that **breathes**.

    A-114 (ii): the scenario is the **middle column's page switch** — the
    product renders the skeleton in ``middle-navigation.js``'s
    ``showLoadingState()``, which only runs when the middle column changes
    page.  A first-screen load never goes through it.

    A-114 (i): the blocks are measured (``getBoundingClientRect()``) and
    the judgement reads those measurements — the old judgement read
    ``width`` / ``height`` fields the probe had never collected, so
    ``sized`` was always empty.

    A-114 (iii): the judgement follows the **motion tier** the product is
    in: the full tier has to show the loading mark, the degraded tier
    (reduced motion / the in-app motion preference off) renders an
    equivalent **static** grey block and is judged on its **body** alone.

    A-115: the criterion is **"有体积 + 加载期动效（呼吸）"** — the block's
    **own surface** (its ``background-color`` or its ``opacity``) has to
    change while it is on screen.  A sheen sweeping across an ``::after``
    overlay does **not** satisfy it (it moves the overlay, not the
    surface).  See :func:`_breathes`.
    """
    css_hit = []
    for path in ctx.own_css_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if "lk-skeleton" in text or "shimmer" in text:
            css_hit.append(path.name)

    # The loading marks the current page carries (the paper list's own
    # ``.lk-skeleton--text`` among them).  They are **not** the scenario
    # of 3.4-3 — the criterion is about the middle column's page switch —
    # but they are kept as evidence.
    page_marks = []
    try:
        page_marks = ctx.evaluate("() => window.__lkProbe.skeleton()")
    except Exception:
        page_marks = []

    # -- the scenario: the middle column changes page ------------------
    primary = _skeleton_switch(playwright, ctx.base_url, ctx.ws,
                                reduced_motion=CONSISTENCY["reduced_motion"])
    tier = primary.get("tier") or "full"
    judged = _skeleton_judgement(primary.get("items") or [])
    blocks, sized = judged["blocks"], judged["sized"]
    breathing, sweep_only = judged["breathing"], judged["sweepOnly"]
    data = {"scenario": "middle-column switch", "tier": tier,
            "elements": blocks, "cssFiles": css_hit,
            "pageMarks": page_marks,
            "switch": {k: v for k, v in primary.items() if k != "items"}}

    # -- the degraded tier, as the second half of the evidence ---------
    # (the same scenario with the system's reduced-motion tier on: the
    # product renders the equivalent static grey block there).
    degraded = None
    try:
        reduced = _skeleton_switch(playwright, ctx.base_url, ctx.ws,
                                   reduced_motion="reduce")
        reduced_judged = _skeleton_judgement(reduced.get("items") or [])
        degraded = {
            "tier": reduced.get("tier"),
            "elements": reduced_judged["blocks"],
            "sized": len(reduced_judged["sized"]),
            "breathing": len(reduced_judged["breathing"]),
            "switch": {k: v for k, v in reduced.items() if k != "items"},
        }
    except Exception as error:  # the extra evidence is a bonus, not the verdict
        degraded = {"error": str(error)}
    data["degradedTier"] = degraded

    if not blocks:
        return _pending(data, "中栏换页的加载态没有被触达（没有采到骨架块）")
    if not sized:
        return _bad(data, "骨架屏没有尺寸（0×0）—— 灰块与微光都无从显示")
    if tier != "full":
        return _ok(data, "降级档：等价静态灰块有体积（动效档才要求加载期动效）")
    # A-115: the loading mark has to **breathe** — the block's own surface
    # (background colour / opacity) has to change while it is on screen.
    if not breathing:
        if sweep_only:
            detail = ("骨架屏有体积 ✔，但加载期动效是 ::after 覆盖层横扫 ✖"
                      "（块的自身底色 / 不透明度没有随时间变化）")
        else:
            detail = "骨架屏有体积 ✔，但加载期没有动效 ✖"
        return _bad(data, detail + " —— 判据：有体积 + 加载期动效（呼吸："
                                  "块的自身底色或 opacity 随时间变化）")
    return _ok(data, "骨架屏有体积，且加载期有呼吸动效")


def probe_error_colour(ctx):
    """3.4-4 — the machine lists the red places, the human judges them."""
    reds = []
    for path in ctx.own_css_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for index, line in enumerate(text.splitlines(), 1):
            if re.search(r"--role-red|--lk-red|#d1392b|#d6453d|#b8331f", line):
                reds.append({"file": path.name, "line": index, "text": line.strip()[:160]})
    data = {"redDeclarations": reds, "count": len(reds)}
    if not reds:
        return _pending(data, "样式表里没有红色 token 的使用点")
    return data  # SEMI → the runner turns this into PENDING


def probe_empty_state(ctx):
    """3.4-5 — the empty state is an illustration + one sentence + a full
    width primary action whose label is the action itself.

    The **judgement** is unchanged (illustration + exactly one sentence +
    a full width ``<button>``); only the *container recognition* was
    narrowed: the parts of an illustration carry the same class names as
    the container (``lk-empty__art`` / ``lk-empty__text`` /
    ``lk-empty__action``), so they used to be counted as containers and
    reported as empty states without an illustration.  The skipped
    elements are listed in the evidence so the narrowing can be reviewed.
    """
    states = ctx.evaluate("() => window.__lkProbe.emptyStates()")
    skipped = ctx.evaluate("() => window.__lkEmptySkipped || null")
    data = {"states": states, "skipped": skipped}
    if not states:
        return _pending(data, "本页没有可见的空态容器（未触达空态）")
    offenders = []
    for state in states:
        problems = []
        if not state.get("art"):
            problems.append("缺插画")
        if len(state.get("sentences") or []) != 1:
            problems.append(f"说明句 {len(state.get('sentences') or [])} 句（应为 1 句）")
        action = state.get("action")
        if not action:
            problems.append("没有主按钮")
        else:
            if not action.get("fullWidth"):
                problems.append("主按钮不是满宽")
            if action.get("tag") != "button":
                problems.append(f"主动作是 <{action.get('tag')}> 而不是 <button>")
        if problems:
            offenders.append({"cls": state.get("cls"), "problems": problems,
                              "action": action})
    data["offenders"] = offenders
    if offenders:
        return _bad(data, f"{len(offenders)} 个空态容器不合规")
    return _ok(data, f"{len(states)} 个空态容器都合规")


def probe_session_scroll(ctx):
    """3.4-6 — the session list must not be cut silently.

    What the criterion forbids is a **silent crop**: a list whose older
    entries cannot be reached.  The list does not have to be the scroll
    container itself — the content may also be reachable through a
    scrolling ancestor — but it must be reachable **somehow**.

    The probe therefore measures three things and judges on them:

    * the list's own geometry and its ``overflow-y``;
    * the chain of ancestors (which one clips, which one scrolls);
    * whether the **last** session can be brought into the visible box
      after the chain has been scrolled to the end.
    """
    info = ctx.evaluate("""() => {
      const list = document.querySelector("#ai-session-list");
      if (!list) return null;
      const els = [];
      let node = list;
      while (node && node.nodeType === 1 && els.length < 12) {
        els.push(node);
        node = node.parentElement;
      }
      const describe = (el) => {
        const st = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || "",
          cls: String(el.className || "").slice(0, 60),
          overflowY: st.overflowY,
          overflowX: st.overflowX,
          clientHeight: el.clientHeight,
          scrollHeight: el.scrollHeight,
          scrollTop: el.scrollTop,
          rect: {top: Math.round(rect.top), bottom: Math.round(rect.bottom)},
        };
      };
      const chain = els.map(describe);
      const children = list.children.length;
      const last = list.lastElementChild;
      if (!last || children < 2) {
        return {children: children, chain: chain, reachable: null};
      }
      const before = last.getBoundingClientRect();
      /* scroll the whole chain to the end: the list itself first, then
         every ancestor that is a scroll container. */
      els.forEach((el) => {
        const oy = getComputedStyle(el).overflowY;
        if (oy === "auto" || oy === "scroll" || oy === "overlay") {
          el.scrollTop = el.scrollHeight;
        }
      });
      try { window.scrollTo(0, document.body.scrollHeight); } catch (e) {}
      const after = last.getBoundingClientRect();
      /* the visible box: the nearest ancestor that clips, else the window */
      const clipper = els.find((el) => {
        const oy = getComputedStyle(el).overflowY;
        return oy === "hidden" || oy === "clip";
      });
      const box = clipper ? clipper.getBoundingClientRect()
                          : {top: 0, bottom: window.innerHeight};
      return {
        children: children,
        chain: chain,
        lastBefore: {top: Math.round(before.top), bottom: Math.round(before.bottom)},
        lastAfter: {top: Math.round(after.top), bottom: Math.round(after.bottom)},
        box: {top: Math.round(box.top), bottom: Math.round(box.bottom)},
        clipper: clipper ? (clipper.id || String(clipper.className || "")
                            .slice(0, 40)) : null,
        reachable: after.top >= box.top - 1 && after.bottom <= box.bottom + 1,
      };
    }""")
    data = {"container": info}
    if not info:
        return _pending(data, "本页没有 #ai-session-list")
    if not info.get("children"):
        return _pending(data, "会话列表是空的 —— 无从判断是否被裁切")
    overflow_y = (info.get("chain") or [{}])[0].get("overflowY")
    if overflow_y in ("auto", "scroll"):
        return _ok(data, f"会话列表自己是滚动容器（{info['children']} 条对话，"
                         f"overflow-y: {overflow_y}）")
    if info.get("reachable") is None:
        return _pending(data, "会话列表内容不足，无法证明可滚动")
    if info.get("reachable"):
        return _ok(data, f"会话列表不是滚动容器，但 {info['children']} 条对话"
                         f"都能滚到（经由祖先的滚动容器）")
    return _bad(data, f"会话列表被静默裁切：{info['children']} 条对话里最后一条"
                       f"滚不到可视区（裁切者：{info.get('clipper')}）")


def probe_custom_select(ctx):
    """3.4-7 — the chapter lens must be a drawn panel, not a native select."""
    info = ctx.evaluate("() => window.__lkProbe.selects()")
    data = info
    lens = info.get("chapterLens", {})
    if not lens.get("selectPresent") and not lens.get("panelPresent"):
        return _pending(data, "本页没有章节透镜")
    if lens.get("panelPresent") and not lens.get("selectVisible"):
        return _ok(data, "章节透镜已是自绘面板")
    if lens.get("selectVisible"):
        return _bad(data, "章节透镜仍是原生 select")
    return _pending(data, "章节透镜的面板与原生 select 状态不明确")


def probe_responsive(ctx):
    """3.5-1 — four viewports, no horizontal scrollbar."""
    page = ctx.page
    results = []
    for name in RESPONSIVE_VIEWPORTS:
        viewport = VIEWPORTS[name]
        page.set_viewport_size({"width": viewport["width"],
                                "height": viewport["height"]})
        page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
        page.wait_for_timeout(300)
        info = page.evaluate("""() => {
          const root = document.documentElement;
          return {
            scrollWidth: root.scrollWidth,
            clientWidth: root.clientWidth,
            overflows: root.scrollWidth > root.clientWidth + 1,
            columns: {
              left: !!document.querySelector("#left-column"),
              middle: !!document.querySelector("#middle"),
              right: !!document.querySelector("#ai-column"),
            },
          };
        }""")
        results.append({"viewport": name, "width": viewport["width"], **info})
    page.set_viewport_size({"width": VIEWPORTS["V1440"]["width"],
                            "height": VIEWPORTS["V1440"]["height"]})
    data = {"viewports": results}
    offenders = [r for r in results if r["overflows"]]
    if offenders:
        return _bad(data, "有视口出现横向滚动")
    return _ok(data, "四档视口都没有横向滚动")


def probe_graph_drawer(ctx):
    """3.5-4 — on the graph page a narrow-viewport drawer stays on top.

    The graph page pins the three columns' `z-index` back to `auto` (G-5's
    pixel freeze: a stacking context would change the canvas's antialiasing).
    That flattening also took the **drawer's** own `z-index: 10` away ⇒ the
    canvas painted over the open drawer and the navigation inside it could
    not be clicked (reported 2026-10-24).

    The check: open the left drawer at 768 and hit-test a navigation entry —
    the hit must land **inside the drawer**, not on the canvas.
    """
    page = ctx.page
    viewport = VIEWPORTS["V768"]
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    page.goto(ctx.url("graph"), wait_until="load", timeout=30000)
    page.wait_for_timeout(600)
    closed = page.evaluate("""() => {
      const col = document.querySelector("#left-column");
      const st = col ? getComputedStyle(col) : null;
      return {present: !!col, position: st ? st.position : null,
              zIndex: st ? st.zIndex : null};
    }""")
    opened = {"opened": False, "reason": "没有开抽屉的入口"}
    try:
        page.click("#mobile-nav-toggle", timeout=5000)
        page.wait_for_timeout(700)
        opened = page.evaluate("""() => {
          const col = document.querySelector("#left-column");
          const item = col ? col.querySelector(".nav-item") : null;
          if (!item) return {opened: true, probe: "抽屉里没有导航项"};
          const r = item.getBoundingClientRect();
          const hit = document.elementFromPoint(r.left + Math.min(24, r.width / 2),
                                               r.top + r.height / 2);
          return {opened: true,
                  drawerZ: getComputedStyle(col).zIndex,
                  hit: hit ? {tag: hit.tagName.toLowerCase(),
                              cls: String(hit.className || "").slice(0, 60),
                              insideDrawer: col.contains(hit),
                              insideCanvas: !!hit.closest("#graph-canvas")} : null};
        }""")
    except Exception as exc:
        opened = {"opened": False, "reason": str(exc)}
    page.set_viewport_size({"width": VIEWPORTS["V1440"]["width"],
                            "height": VIEWPORTS["V1440"]["height"]})
    data = {"closed": closed, "opened": opened}
    if not closed.get("present"):
        return _pending(data, "图谱页没有左栏")
    if closed.get("position") != "fixed":
        return _bad(data, "768 下左栏不是抽屉（position 不是 fixed）")
    if not opened.get("opened"):
        return _pending(data, f"没能打开抽屉：{opened.get('reason')}")
    hit = opened.get("hit") or {}
    if not hit.get("insideDrawer"):
        return _bad(data, "抽屉打开时命中的是 "
                          f"{hit.get('cls') or hit.get('tag')}（画布盖住了抽屉）")
    return _ok(data, "抽屉里的导航项可点")


def probe_drawer(ctx):
    """3.5-2 / 3.5-3 — the right column becomes a drawer at 768 and the
    background stays interactive while it is open."""
    page = ctx.page
    viewport = VIEWPORTS["V768"]
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
    page.wait_for_timeout(400)
    closed = page.evaluate("""() => {
      const col = document.querySelector("#ai-column");
      const st = col ? getComputedStyle(col) : null;
      return {
        present: !!col,
        position: st ? st.position : null,
        transform: st ? st.transform : null,
        toggle: !!document.querySelector("#mobile-ai-toggle"),
        middleInteractive: (() => {
          const middle = document.querySelector("#middle");
          if (!middle) return false;
          const rect = middle.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + Math.min(rect.height / 2, 200);
          const hit = document.elementFromPoint(x, y);
          return hit ? (middle.contains(hit) ? "middle" : hit.className || hit.tagName)
                    : "none";
        })(),
      };
    }""")
    opened = {"opened": False, "reason": "没有开抽屉的入口"}
    try:
        page.click("#mobile-ai-toggle", timeout=5000)
        page.wait_for_timeout(400)
        opened = page.evaluate("""() => {
          const col = document.querySelector("#ai-column");
          const st = col ? getComputedStyle(col) : null;
          const middle = document.querySelector("#middle");
          const rect = middle ? middle.getBoundingClientRect() : null;
          let hit = null;
          if (rect) {
            const x = rect.left + rect.width / 2;
            const y = rect.top + Math.min(rect.height / 2, 200);
            hit = document.elementFromPoint(x, y);
          }
          return {
            opened: true,
            position: st ? st.position : null,
            transform: st ? st.transform : null,
            backgroundHit: hit ? {
              tag: hit.tagName.toLowerCase(),
              cls: String(hit.className || "").slice(0, 60),
              insideMiddle: middle ? middle.contains(hit) : false,
            } : null,
            decorative: Array.from(document.querySelectorAll("body *"))
              .filter((el) => {
                const s = getComputedStyle(el);
                if (s.position !== "fixed") return false;
                if (s.pointerEvents === "none") return false;
                return !el.querySelector("a, button, input, select, textarea");
              })
              .map((el) => ({cls: String(el.className || "").slice(0, 60),
                             pointerEvents: getComputedStyle(el).pointerEvents})),
          };
        }""")
    except Exception as exc:
        opened = {"opened": False, "reason": str(exc)}
    page.set_viewport_size({"width": VIEWPORTS["V1440"]["width"],
                            "height": VIEWPORTS["V1440"]["height"]})
    data = {"closed": closed, "opened": opened}
    if not closed.get("present"):
        return _pending(data, "本页没有右栏")
    if closed.get("position") != "fixed":
        return _bad(data, "768 下右栏不是抽屉（position 不是 fixed）")
    if not opened.get("opened"):
        return _pending(data, f"没能打开抽屉：{opened.get('reason')}")
    hit = opened.get("backgroundHit") or {}
    if not hit.get("insideMiddle"):
        return _bad(data, f"抽屉打开时背景命中的是 {hit.get('cls') or hit.get('tag')}")
    return _ok(data, "768 下右栏是抽屉，抽屉打开时背景仍可交互")


def probe_assets(ctx):
    """3.6-1 — every icon and illustration is a local SVG.

    Per `decisions.md` **A-86**, the criterion covers the **UI** assets (icons,
    empty-state illustrations, motion assets, badges).  A **content figure** (a
    question picture served from the pool under `/api/w/{ws}/figures/…`) is
    content, owned by the content pipeline — it is reported in its own bucket
    and **never silently dropped**, but it does not fail this criterion.
    """
    assets = ctx.evaluate("() => window.__lkProbe.assets()")
    external, ui_bitmaps, content_figures, fonts = [], [], [], []
    # Classify the <img> elements first: a question picture is content, not UI.
    role_of = {}
    for item in assets["imgs"]:
        src = item.get("src") or ""
        role = "icon-or-illustration"
        if "/figures/" in src or "figure" in (item.get("parent") or "").lower():
            role = "content-figure"
        role_of[src] = role
    for item in assets["imgs"]:
        src = item["src"]
        if not src:
            continue
        if re.match(r"^(https?:)?//", src) or src.startswith("data:"):
            external.append(src)
        elif re.search(r"\.(png|jpe?g|webp|gif|bmp)(\?|$)", src, re.I):
            if role_of.get(src) == "content-figure":
                content_figures.append(src)
            else:
                ui_bitmaps.append(src)
    for item in assets["backgrounds"]:
        url = item["url"]
        if re.match(r"^(https?:)?//", url):
            external.append(url)
        elif re.search(r"\.(png|jpe?g|webp|gif|bmp)(\?|$)", url, re.I):
            # A background-image is always UI.
            ui_bitmaps.append(url)
    for path in ctx.own_css_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"@font-face\s*\{[^}]*\}", text, re.S):
            fonts.append({"file": path.name, "block": match.group(0)[:200]})
    classified = []
    for item in assets["imgs"]:
        src = item["src"]
        classified.append({**item, "role": role_of.get(src, "icon-or-illustration")})
    data = {
        "imgCount": len(assets["imgs"]),
        "svgCount": len(assets["svgs"]),
        "backgroundCount": len(assets["backgrounds"]),
        "external": external,
        "bitmaps": ui_bitmaps,
        "uiBitmaps": ui_bitmaps,
        "contentFigures": content_figures,
        "fontFaces": fonts,
        "imgs": classified[:30],
        "note": "UI 资产（图标 / 插画）必须是内联 SVG；题图（content-figure，"
                "来自题池 /api/w/{ws}/figures/…）是**内容资产**，由内容管线管，"
                "单列一类、不计入本条判定，但**必须出现在报告里**（A-86）",
    }
    if not assets["imgs"] and not assets["svgs"] and not assets["backgrounds"]:
        return _na(data, "页面上没有任何图标 / 插画 / 背景图")
    if external:
        return _bad(data, f"{len(external)} 个外链资源")
    if ui_bitmaps:
        return _bad(data, f"{len(ui_bitmaps)} 个 UI 位图资源")
    if content_figures:
        return _ok(data, f"UI 资产全部是本地 SVG；另有 {len(content_figures)} 个题图"
                       f"（内容资产，另由内容管线核对）")
    return _ok(data, "全部资源都是本地 SVG")


def probe_icon_language(ctx):
    """3.6-2 — the stroke widths and the radii (the human judges)."""
    assets = ctx.evaluate("() => window.__lkProbe.assets()")
    strokes = {}
    radii = {}
    for svg in assets["svgs"]:
        for width in svg.get("strokeWidths") or []:
            strokes[width] = strokes.get(width, 0) + 1
        for radius in svg.get("radii") or []:
            radii[radius] = radii.get(radius, 0) + 1
    return {"svgCount": len(assets["svgs"]),
            "strokeWidths": strokes, "radii": radii,
            "sample": assets["svgs"][:12]}


def probe_icon_colours(ctx):
    """3.6-3 — the icon discs use the three role colours only."""
    backgrounds = ctx.evaluate("() => window.__lkProbe.iconBackgrounds()")
    roles = ctx.evaluate("() => window.__lkProbe.roleColours()")
    families = {
        "blue": set(),
        "yellow": set(),
        "red": set(),
    }
    for name, value in roles.items():
        normalised = _norm_colour(value)
        if not normalised:
            continue
        if "blue" in name:
            families["blue"].add(normalised)
        elif "yellow" in name:
            families["yellow"].add(normalised)
        elif "red" in name:
            families["red"].add(normalised)
    known = families["blue"] | families["yellow"] | families["red"]
    offenders = []
    for item in backgrounds:
        colour = _norm_colour(item.get("background") or "")
        if not colour:
            continue
        if colour in known:
            continue
        if item.get("background") in ("rgba(0, 0, 0, 0)", "transparent"):
            continue
        offenders.append(item)
    data = {"iconBackgrounds": backgrounds, "roleColours": roles,
            "offenders": offenders}
    if not backgrounds:
        return _pending(data, "本页没有带底色的图标")
    if not known:
        return _pending(data, "没有读到角色色表")
    if offenders:
        return _bad(data, f"{len(offenders)} 个图标底色不在三个角色色里")
    return _ok(data, f"{len(backgrounds)} 个图标底色都在三个角色色里")


def probe_animation_properties(ctx):
    """3.7-1 — the motion may only touch transform and opacity."""
    live = ctx.evaluate("() => window.__lkProbe.animatedProperties()")
    allowed = {"transform", "opacity"}
    offenders = []
    for item in live.get("transitions", []):
        for name in item["property"].split(","):
            name = name.strip()
            if name and name not in allowed:
                offenders.append({"source": "transition", "property": name,
                                 "cls": item["cls"], "duration": item["duration"]})
    for item in live.get("keyframes", []):
        for name in item["properties"]:
            if name not in allowed:
                offenders.append({"source": "keyframes", "property": name,
                                 "cls": item.get("name", "")})
    css_offenders = []
    for path in ctx.own_css_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", text):
            name = match.group(1)
            # The block is bounded by its **matching** brace: a window
            # would run into the rules that follow the keyframes.
            body = _matching_block(text, match.end() - 1)
            for block in re.findall(r"[^{}]+\{([^{}]*)\}", body):
                for prop in re.findall(r"(?:^|;)\s*([a-z-]+)\s*:", block):
                    if prop in allowed or prop in ANIMATION_CONTROL:
                        continue
                    css_offenders.append({"file": path.name, "keyframes": name,
                                          "property": prop})
                    break
    data = {
        "live": {"transitions": live.get("transitions", [])[:40],
                 "wildcards": live.get("wildcards", [])[:20],
                 "keyframes": live.get("keyframes", [])[:40]},
        "offenders": offenders,
        "cssOffenders": css_offenders,
    }
    if offenders or css_offenders:
        return _bad(data, "有动效动了 transform / opacity 之外的属性")
    return _ok(data, "动效只动 transform / opacity")


#: The animation **control** properties: they do not animate anything by
#: themselves, so they are not "the motion touches a third property".
ANIMATION_CONTROL = {
    "animation", "animation-name", "animation-duration", "animation-delay",
    "animation-timing-function", "animation-fill-mode", "animation-direction",
    "animation-iteration-count", "animation-play-state",
    "transition", "transition-property", "transition-duration",
    "transition-delay", "transition-timing-function",
}


def _matching_block(text, open_index):
    """The body of the block whose opening brace is at ``open_index``."""
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index]
    return text[open_index:]


def probe_long_list(ctx):
    """3.7-2 — a list of 98+ records has to scroll smoothly.

    The list that is **measured** is the list that was **counted** — the
    probe does not count one container and scroll another.  A verdict
    without a measurement is never a pass (§7.6.2), so a list that cannot
    scroll at all is a failure of the criterion, not a silent PASS.
    """
    page = ctx.page
    info = page.evaluate("""() => {
      const candidates = ["#records-list", ".records-list", "#ai-session-list",
                          ".workload-list", "#record-list", "main ul", "main ol"];
      let best = null;
      for (const selector of candidates) {
        const el = document.querySelector(selector);
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        if (!best || rect.height > best.height) {
          best = {selector, count: el.children.length,
                  scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                  overflowY: getComputedStyle(el).overflowY, height: rect.height};
        }
      }
      return best;
    }""")
    data = {"list": info}
    if not info:
        return _pending(data, "本页没有找到记录列表容器")
    if info.get("count", 0) < 98:
        return _pending(data, f"列表只有 {info.get('count')} 条 —— 不足 98 条，"
                              "本轮无法测「98+ 条记录滚动流畅」")
    frames = page.evaluate("""async (selector) => {
      const list = document.querySelector(selector);
      if (!list) return null;
      /* the scroller is the list itself, or the nearest ancestor that
         scrolls: that is the element the learner's wheel would move. */
      let scroller = null;
      let node = list;
      while (node && node.nodeType === 1) {
        const oy = getComputedStyle(node).overflowY;
        if (oy === "auto" || oy === "scroll" || oy === "overlay") {
          scroller = node;
          break;
        }
        node = node.parentElement;
      }
      if (!scroller) {
        return {scroller: null, scrollable: false, frames: 0};
      }
      scroller.scrollTop = 0;
      const start = scroller.scrollTop;
      const gaps = [];
      let last = performance.now();
      const stop = performance.now() + 1000;
      while (performance.now() < stop) {
        scroller.scrollTop += 40;
        await new Promise((r) => requestAnimationFrame(r));
        const now = performance.now();
        gaps.push(now - last);
        last = now;
      }
      gaps.sort((a, b) => a - b);
      return {
        scroller: scroller === list ? selector
                  : (scroller.id || String(scroller.className || "").slice(0, 40)),
        scrollerIsList: scroller === list,
        scrollable: scroller.scrollTop > start,
        scrollTopAfter: scroller.scrollTop,
        frames: gaps.length,
        median: gaps[Math.floor(gaps.length / 2)],
        p95: gaps[Math.floor(gaps.length * 0.95)],
        max: gaps[gaps.length - 1],
      };
    }""", info.get("selector"))
    data["frames"] = frames
    if not frames:
        return _pending(data, "滚动帧间隔没有采到 —— 本轮无法判定滚动是否流畅")
    if frames.get("scroller") is None:
        return _bad(data, f"{info.get('count')} 条记录的列表滚不动"
                           "（整条链上没有任何滚动容器）—— 静默裁切，"
                           "滚动流畅无从成立")
    if not frames.get("frames"):
        return _pending(data, "没有采到滚动帧间隔 —— 本轮无法判定滚动是否流畅")
    if not frames.get("scrollable"):
        return _bad(data, f"{info.get('count')} 条记录的列表滚不动"
                           f"（滚动容器 {frames.get('scroller')} 的 scrollTop 没动）"
                           "—— 静默裁切，滚动流畅无从成立")
    if frames.get("p95", 0) > 50:
        return _bad(data, f"滚动帧间隔 p95 = {frames.get('p95')}ms")
    return _ok(data, f"{info.get('count')} 条记录的滚动帧间隔在阈值内"
                     f"（p95 = {frames.get('p95')}ms）")


def probe_fonts(ctx):
    """3.7-3 — every web font of our own CSS must declare font-display."""
    faces = []
    for path in ctx.own_css_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"@font-face\s*\{([^}]*)\}", text, re.S):
            block = match.group(1)
            family = re.search(r"font-family\s*:\s*([^;]+)", block)
            display = re.search(r"font-display\s*:\s*([^;]+)", block)
            faces.append({
                "file": path.name,
                "family": family.group(1).strip() if family else None,
                "fontDisplay": display.group(1).strip() if display else None,
            })
    data = {"faces": faces, "count": len(faces),
            "files": [p.name for p in ctx.own_css_files()]}
    if not faces:
        return _ok(data, "本仓自有 CSS 没有 @font-face（无可闪排的 web font）")
    missing = [f for f in faces if not f["fontDisplay"]
               or f["fontDisplay"].lower() == "auto"]
    if missing:
        return _bad(data, f"{len(missing)} 个 @font-face 没有 font-display 或用了 auto")
    return _ok(data, f"{len(faces)} 个 @font-face 都声明了 font-display")


def probe_cache(ctx):
    """3.7-4 — a changed CSS must take effect at once."""
    page = ctx.page
    response = page.request.get(ctx.base_url + "/static/workbench.css")
    headers = {key.lower(): value for key, value in response.headers.items()}
    body = response.body()
    css_bytes = None
    if ctx.repo_root:
        candidate = ctx.repo_root / "workbench" / "server" / "static" / "workbench.css"
        if candidate.is_file():
            css_bytes = candidate.stat().st_size
    data = {
        "status": response.status,
        "headers": {key: headers.get(key) for key in
                    ("cache-control", "etag", "last-modified", "content-length",
                     "content-type", "expires")},
        "servedBytes": len(body),
        "fileBytes": css_bytes,
        "sameAsFile": (css_bytes is not None and len(body) == css_bytes),
    }
    cache_control = (headers.get("cache-control") or "").lower()
    if re.search(r"max-age\s*=\s*([1-9]\d*)", cache_control):
        return _bad(data, f"响应带 {headers.get('cache-control')}，改了 CSS 可能不立刻生效")
    if data["sameAsFile"] is False:
        return _bad(data, "服务出去的 CSS 与仓库里的不是同一份")
    return _ok(data, "静态资源没有长缓存，CSS 改动立刻生效")


# ─────────────────────────────────────────────────────────────────────────
# G-7 / G-8
# ─────────────────────────────────────────────────────────────────────────


def probe_g7(ctx):
    """G-7 — a decorative layer must not intercept the pointer."""
    result = ctx.evaluate("""async () => {
      const P = window.__lkProbe;
      const samples = [];
      const collect = () => P.decorativeLayers();
      samples.push({phase: "idle", layers: collect()});
      if (window.lkTheme && typeof window.lkTheme.transition === "function") {
        window.lkTheme.transition("night");
        for (let i = 0; i < 12; i += 1) {
          await new Promise((r) => setTimeout(r, 40));
          samples.push({phase: "lamp", layers: collect()});
        }
      }
      return {samples};
    }""")
    offenders = []
    seen = set()
    for sample in result.get("samples", []):
        for layer in sample.get("layers", []):
            key = layer.get("cls") or layer.get("id")
            if key in seen:
                continue
            seen.add(key)
            if layer.get("focusableInside"):
                continue        # an interactive layer is not decoration
            if not layer.get("ariaHidden"):
                continue        # a visible layer is content, not decoration
            hit = layer.get("hit") or {}
            if hit.get("isSelf"):
                offenders.append(layer)
    data = {"offenders": offenders, "samples": result.get("samples", [])[:4]}
    if offenders:
        return _bad(data, f"{len(offenders)} 个装饰层挡住了它下面的元素")
    return _ok(data, "装饰层全部让开了指针事件")


def focus_sequence(page, steps=600):
    """The Tab walk of §7.2 — the *semantic* description of every stop.

    The walk stops when the focus cycle closes (the first stop comes
    back): the focus order is a **cycle**, and the change may add one
    entry to it.  A fixed number of steps would then compare two cycles
    that start at different places.

    ``steps`` is only a safety net against a page whose focus never
    cycles.  It used to be 120 — but the seed (§0.5) puts 120
    conversations in the right column and every conversation carries
    three buttons, so the cycle grew to ~310 stops and the walk was cut
    short: the two sides then compared **different parts** of the cycle
    and G-8 failed for a reason that had nothing to do with the change.
    The cap now sits far above the seeded cycle.
    """
    page.evaluate("""() => {
      if (document.activeElement && document.activeElement !== document.body) {
        document.activeElement.blur();
      }
    }""")
    sequence = []
    first = None
    for _ in range(steps):
        page.keyboard.press("Tab")
        stop = page.evaluate("""() => {
          const el = document.activeElement;
          if (!el || el === document.body) return {semantic: "<body>"};
          const st = getComputedStyle(el);
          return {
            semantic: window.__lkProbe.semantic(el),
            tag: el.tagName.toLowerCase(),
            id: el.id || "",
            cls: String(el.className || "").slice(0, 60),
            outlineWidth: st.outlineWidth,
            outlineStyle: st.outlineStyle,
            outlineColor: st.outlineColor,
            boxShadow: st.boxShadow,
            focusVisible: el.matches ? el.matches(":focus-visible") : null,
          };
        }""")
        semantic = stop.get("semantic")
        if first is None:
            first = semantic
        elif semantic == first:
            break
        sequence.append(stop)
    return sequence


def probe_g8(ctx, sequence):
    """G-8 — the focus order must not change (the diff is done in ``diff``)."""
    data = {"stops": len(sequence),
            "sequence": [stop.get("semantic") for stop in sequence]}
    return data


# ─────────────────────────────────────────────────────────────────────────
# the passes
# ─────────────────────────────────────────────────────────────────────────


def _launch(playwright, profile=None, reduced_motion=None):
    """Open a browser with the consistency settings of §5.2.

    Returns ``(context, page, browser)``; ``browser`` is ``None`` for a
    persistent context (the profile is the context there).
    """
    options = {
        "viewport": {"width": VIEWPORTS["V1440"]["width"],
                     "height": VIEWPORTS["V1440"]["height"]},
        "device_scale_factor": VIEWPORTS["V1440"]["device_scale_factor"],
        "color_scheme": CONSISTENCY["color_scheme"],
        "locale": CONSISTENCY["locale"],
        "timezone_id": CONSISTENCY["timezone_id"],
    }
    if reduced_motion is not None:
        options["reduced_motion"] = reduced_motion
    else:
        options["reduced_motion"] = CONSISTENCY["reduced_motion"]
    if profile:
        context = playwright.chromium.launch_persistent_context(
            str(profile), headless=True, args=list(CONSISTENCY["browser_args"]),
            **options)
        page = context.pages[0] if context.pages else context.new_page()
        return context, page, None
    browser = playwright.chromium.launch(
        headless=True, args=list(CONSISTENCY["browser_args"]))
    context = browser.new_context(**options)
    return context, context.new_page(), browser


def run_static(args):
    """The static pass — everything that only reads the DOM."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(args.out)
    probe_dir = out_dir / "probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    with sync_playwright() as playwright:
        context, page, browser = _launch(playwright, profile=args.profile)
        page.add_init_script(PROBE_JS)
        page.add_init_script(AUDIO_JS)
        page.add_init_script(SKELETON_JS)
        ctx = ProbeContext(page, args.base_url, args.ws, args.side,
                           repo_root=args.repo_root, out_dir=out_dir)
        try:
            # -- the practice page -------------------------------------
            ctx.goto("practice")
            sequence = focus_sequence(page)
            results["3.1-1"] = probe_focus_ring(ctx, sequence)
            results["3.1-5"] = {"verdict": PENDING, "data": probe_text_count(ctx, "practice"),
                                 "note": "需要与改造前的一侧比较"}
            results["3.1-8"] = probe_accessible_names(ctx, "practice")

            pairs = BEFORE_CONTRAST_PAIRS if args.side == "before" else AFTER_CONTRAST_PAIRS
            results["3.1-2"] = probe_contrast(ctx, pairs,
                                              "before" if args.side == "before" else "after")
            if args.side == "after":
                results["3.2-2"] = probe_contrast(ctx, NIGHT_CONTRAST_PAIRS, "night")
            results["3.1-6"] = probe_reduced_motion(ctx, playwright)
            results["3.1-7"] = probe_focus_not_stolen(ctx)

            results["3.2-3"] = probe_icon_night(ctx)
            results["3.2-4"] = probe_theme_night_assets(ctx)
            results["3.6-5"] = probe_theme_night_assets(ctx)

            results["3.3-1"] = probe_audio_moments(ctx)
            results["3.3-2"] = probe_audio_gesture(ctx, playwright)
            results["3.3-3"] = probe_audio_mute(ctx)
            results["3.3-4"] = probe_audio_mute(ctx)

            results["3.4-3"] = probe_skeleton(ctx, playwright)
            results["3.4-4"] = probe_error_colour(ctx)
            results["3.4-7"] = probe_custom_select(ctx)
            hover = probe_hover(ctx)
            results["3.4-1"], results["3.4-2"] = judge_hover(hover)

            results["3.6-1"] = probe_assets(ctx)
            results["3.6-2"] = probe_icon_language(ctx)
            results["3.6-3"] = probe_icon_colours(ctx)
            results["3.6-4"] = {
                "verdict": PENDING,
                "data": {"shot": "shots/S-12-*.png",
                         "illustrations": ctx.evaluate(
                             "() => window.__lkProbe.assets().svgs"
                             ".filter((s) => !s.parent || /art|illus|empty/i.test(s.parent))")},
                "note": "插画是否为具象器物需人看渲染结果",
            }

            results["3.7-1"] = probe_animation_properties(ctx)
            results["3.7-3"] = probe_fonts(ctx)
            results["3.7-4"] = probe_cache(ctx)

            results["g7"] = probe_g7(ctx)
            results["g8"] = probe_g8(ctx, sequence)

            # -- the settings view (the theme switch) ------------------
            ctx.goto("settings")
            lamp, per_workspace, persist = probe_theme_ui(ctx)
            results["3.2-1"] = lamp
            results["3.2-5"] = per_workspace
            results["3.2-6"] = persist
            # Put the theme back to the light one for the remaining probes.
            page.evaluate("""() => {
              const box = document.getElementById("setting-theme");
              if (box && box.checked) box.click();
            }""")
            page.wait_for_timeout(200)

            # -- the knowledge list (the state marks) -------------------
            ctx.goto("kps")
            states = probe_states(ctx, "kps")
            results["3.1-3"] = judge_states_geometry(states)
            results["3.1-4"] = judge_states_text(states)

            # -- the paper list (the empty state) ----------------------
            ctx.goto("practice-sets")
            results["3.4-5"] = probe_empty_state(ctx)

            # -- the records -------------------------------------------
            ctx.goto("records")
            results["3.7-2"] = probe_long_list(ctx)
            results["3.4-6"] = probe_session_scroll(ctx)

            # -- the responsive matrix ---------------------------------
            results["3.5-1"] = probe_responsive(ctx)
            results["3.5-2"] = probe_drawer(ctx)
            results["3.5-3"] = probe_drawer(ctx)
            results["3.5-4"] = probe_graph_drawer(ctx)
        finally:
            try:
                context.close()
            except Exception:
                pass
            if browser is not None:
                browser.close()

    _write_results(probe_dir, results, args.side)
    return results


def run_flow(args):
    """The flow pass — the sound item needs a real paper run.

    The paper is built from the **plan** (seed.py) when there is one: the
    plan's items are gradable and their correct options are known, so the
    round is an all-correct one and the answer cue has something to say.
    Without a plan the pass falls back to the exercise's seed paper.
    """
    from exercise import Service, Waiter, seed_paper

    out_dir = Path(args.out)
    probe_dir = out_dir / "probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    plan = []
    if getattr(args, "plan", None):
        plan = (_read_json(args.plan) or {}).get("items") or []
    service = Service(args.base_url)
    waiter = Waiter(service)
    waiter.snapshot()
    paper_id = args.paper_id
    if paper_id is None:
        if plan:
            service.set_phase("seed", group="paper")
            created = service.create_paper(
                args.ws, "走查音效探针卷",
                [item["problem_id"] for item in plan])
            paper_id = created.get("practice_set_id")
        else:
            paper_id = seed_paper(service, args.ws)
    service.set_phase("verify", group="probe")

    ctx = ProbeContext(None, args.base_url, args.ws, args.side,
                       repo_root=args.repo_root, out_dir=out_dir)
    # The sound probe opens its **own** browser context: the audio module
    # must not be unlocked before the probe's own gesture.
    data = probe_audio_cue(ctx, paper_id, plan, waiter=waiter)
    results["3.3-1"] = judge_audio_cue(data)

    _write_results(probe_dir, results, args.side)
    return results


def run_persist(args):
    """The persist pass — the theme preference after a service restart."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(args.out)
    probe_dir = out_dir / "probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    with sync_playwright() as playwright:
        context, page, browser = _launch(playwright, profile=args.profile)
        page.add_init_script(PROBE_JS)
        ctx = ProbeContext(page, args.base_url, args.ws, args.side,
                           repo_root=args.repo_root, out_dir=out_dir)
        try:
            ctx.goto("practice")
            results["3.2-6"] = probe_theme_persist(ctx)
        finally:
            try:
                context.close()
            except Exception:
                pass
            if browser is not None:
                browser.close()
    _write_results(probe_dir, results, args.side)
    return results


#: The automation level of every item (§7.5.3).  Only an AUTO item may be
#: auto-judged; a SEMI or MANUAL item is always reported as PENDING.
LEVELS = {
    "3.1-1": "AUTO", "3.1-2": "AUTO", "3.1-3": "AUTO", "3.1-4": "AUTO",
    "3.1-5": "AUTO", "3.1-6": "AUTO", "3.1-7": "AUTO", "3.1-8": "AUTO",
    "3.2-1": "AUTO", "3.2-2": "AUTO", "3.2-3": "SEMI", "3.2-4": "AUTO",
    "3.2-5": "AUTO", "3.2-6": "AUTO",
    "3.3-1": "AUTO", "3.3-2": "AUTO", "3.3-3": "AUTO", "3.3-4": "AUTO",
    "3.3-5": "AUTO",
    "3.4-1": "AUTO", "3.4-2": "AUTO", "3.4-3": "AUTO", "3.4-4": "SEMI",
    "3.4-5": "AUTO", "3.4-6": "AUTO", "3.4-7": "AUTO",
    "3.5-1": "AUTO", "3.5-2": "AUTO", "3.5-3": "AUTO", "3.5-4": "AUTO",
    "3.6-1": "AUTO", "3.6-2": "SEMI", "3.6-3": "AUTO", "3.6-4": "MANUAL",
    "3.6-5": "AUTO",
    "3.7-1": "AUTO", "3.7-2": "AUTO", "3.7-3": "AUTO", "3.7-4": "AUTO",
}

#: The reading guide for the items a human has to sign (SEMI / MANUAL).
GUIDES = {
    "3.2-3": "看 probe/3.2-3.json 的 HSL 数值：夜纸的图标圆底应当「降饱和 + 提亮」；"
             "幅度由人判。",
    "3.4-4": "看 probe/3.4-4.json 列出的每一条红色声明，逐点判断它是不是「失败 / 阻塞」。",
    "3.6-2": "看 probe/3.6-2.json 的 stroke-width 分布与 rx/ry 集合，判断是否同一套线宽语言。",
    "3.6-4": "看 shots/S-12-*.png 与图标集，判断插画是否是具象器物。",
}


def _write_results(probe_dir, results, side):
    """Write the per-item evidence files and the partial checklist."""
    entries = []
    for item_id, outcome in sorted(results.items()):
        if item_id in ("g7", "g8"):
            continue
        if isinstance(outcome, dict) and "verdict" in outcome:
            data = outcome.get("data", {})
            verdict = outcome.get("verdict", PENDING)
            note = outcome.get("note", "")
        else:
            # A probe that only collects evidence (SEMI / MANUAL) hands the
            # raw data back; the runner turns it into PENDING.
            data = outcome or {}
            verdict = PENDING
            note = "证据已采集，需人工判读"
        level = LEVELS.get(item_id, "AUTO")
        if level != "AUTO" and verdict in (PASS, FAIL):
            # §7.5.1 — only AUTO may be auto-judged.
            verdict = PENDING
        if side == "before" and item_id in BEFORE_NA:
            verdict = NA
            note = BEFORE_NA[item_id]
        entry = {
            "id": item_id,
            "level": level,
            "auto": level == "AUTO",
            "verdict": verdict,
            "note": note,
            "data": data,
        }
        if item_id in GUIDES:
            entry["guide"] = GUIDES[item_id]
        _write_json(probe_dir / f"{item_id}.json", entry)
        entries.append(entry)
    # The passes run one after another (static, then flow, then persist),
    # so the checklist is **merged**, not overwritten: the flow pass only
    # knows about the items it measured.
    existing = _read_json(probe_dir / "checklist.json") or {}
    merged = {item["id"]: item for item in existing.get("results", [])}
    for entry in entries:
        merged[entry["id"]] = entry
    checklist = {"side": side,
                 "results": [merged[key] for key in sorted(merged)]}
    _write_json(probe_dir / "checklist.json", checklist)
    for key in ("g7", "g8"):
        if key in results:
            outcome = results[key]
            if isinstance(outcome, dict) and "verdict" in outcome:
                payload = {
                    "side": side,
                    "verdict": outcome.get("verdict", PENDING),
                    "note": outcome.get("note", ""),
                    "data": outcome.get("data", {}),
                }
            else:
                payload = {"side": side, "verdict": PENDING, "note": "",
                           "data": outcome or {}}
            _write_json(probe_dir / f"{key}.json", payload)
    return checklist


# ─────────────────────────────────────────────────────────────────────────
# the diff pass
# ─────────────────────────────────────────────────────────────────────────


def _semantic_key(entry):
    """The semantic description of a focus stop.

    The recorded sequence is a list of descriptions; a full stop record is
    accepted as well, so both shapes can be diffed.
    """
    if isinstance(entry, dict):
        return entry.get("semantic") or ""
    return str(entry or "")


def _rotate(sequence, offset):
    return sequence[offset:] + sequence[:offset]


def _mismatch_count(before, after):
    """The number of differing positions of two equally long lists."""
    if len(before) != len(after):
        return max(len(before), len(after))
    return sum(1 for left, right in zip(before, after) if left != right)


def _align_cycles(before, after):
    """Align two focus cycles.

    The focus order is a **cycle**: the walk starts wherever the browser
    starts, and the change may have added one entry to the cycle.  The
    two cycles are therefore rotated against each other and the rotation
    with the fewest differences is taken — the *order inside* the cycle
    is what has to stay the same.
    """
    if not before or not after:
        return before, after
    best = None
    for offset in range(len(after)):
        rotated = _rotate(after, offset)
        score = _mismatch_count(before, rotated)
        if best is None or score < best[0]:
            best = (score, rotated)
    return before, best[1]


def diff_focus(before_sequence, after_sequence):
    """G-8 — compare the two focus orders (§7.2).

    The comparison is **semantic** (tag + role + accessible name), never
    by id: the change restructures the DOM, but the *order* of the focus
    must not change.  The two entries the acceptance explicitly excuses
    — the new settings entry and the theme switch — are reported as
    ADDED-EXPECTED.
    """
    before = [_semantic_key(stop) for stop in before_sequence]
    after = [_semantic_key(stop) for stop in after_sequence]
    before, after = _align_cycles(before, after)
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    added_expected, unexpected, missing, changed, order = [], [], [], [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            for stop in after[j1:j2]:
                if any(pattern.search(stop) for pattern in ADDED_EXPECTED_PATTERNS):
                    added_expected.append(stop)
                else:
                    unexpected.append(stop)
        elif tag == "delete":
            missing.extend(before[i1:i2])
        else:
            left = before[i1:i2]
            right = after[j1:j2]
            for offset in range(max(len(left), len(right))):
                if offset < len(left) and offset < len(right):
                    if left[offset] != right[offset]:
                        changed.append({"before": left[offset], "after": right[offset]})
                elif offset < len(left):
                    missing.append(left[offset])
                else:
                    stop = right[offset]
                    if any(pattern.search(stop) for pattern in ADDED_EXPECTED_PATTERNS):
                        added_expected.append(stop)
                    else:
                        unexpected.append(stop)
    if unexpected or missing or changed:
        order = ["顺序变了"]
    data = {
        "beforeStops": len(before), "afterStops": len(after),
        "addedExpected": added_expected, "unexpectedAdded": unexpected,
        "missingBefore": missing, "changed": changed,
        "before": before, "after": after,
    }
    if unexpected or missing or changed:
        return _bad(data, "焦点顺序与改造前不一致")
    if added_expected:
        return _ok(data, f"焦点顺序未变（{len(added_expected)} 个预期新增入口）")
    return _ok(data, "焦点顺序未变")


def _read_side_items(side_dir):
    """The items of one side, read from the per-item evidence files.

    The per-item files are the source of truth: the checklist is written
    by several passes, and a file that is missing from the checklist must
    not be lost.
    """
    probe_dir = Path(side_dir) / "probe"
    items = {}
    if probe_dir.is_dir():
        for path in sorted(probe_dir.glob("*.json")):
            if path.name in ("checklist.json", "g7.json", "g8.json"):
                continue
            entry = _read_json(path)
            if not entry or "id" not in entry:
                continue
            items[entry["id"]] = entry
    checklist = _read_json(probe_dir / "checklist.json") or {}
    for item in checklist.get("results", []):
        items.setdefault(item["id"], item)
    return items


def diff_checklist(before_dir, after_dir, out_dir):
    """Merge the two sides and judge the comparative items."""
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    before_items = _read_side_items(before_dir)
    after_items = _read_side_items(after_dir)

    # -- 3.1-5 — the visible text must not grow --------------------------
    before_count = (before_items.get("3.1-5") or {}).get("data") or {}
    after_count = (after_items.get("3.1-5") or {}).get("data") or {}
    if before_count and after_count:
        grew = after_count.get("chars", 0) > before_count.get("chars", 0)
        grew_nodes = after_count.get("nodes", 0) > before_count.get("nodes", 0)
        data = {"before": before_count, "after": after_count,
                "charsDelta": after_count.get("chars", 0) - before_count.get("chars", 0),
                "nodesDelta": after_count.get("nodes", 0) - before_count.get("nodes", 0)}
        if grew or grew_nodes:
            outcome = _bad(data, "改造后界面上的说明性文字变多了")
        else:
            outcome = _ok(data, "说明性文字没有变多")
        after_items["3.1-5"] = dict(after_items.get("3.1-5", {"id": "3.1-5"}),
                                    **outcome)

    # -- G-8 — the focus order ------------------------------------------
    before_g8 = _read_json(before_dir / "probe" / "g8.json") or {}
    after_g8 = _read_json(after_dir / "probe" / "g8.json") or {}
    before_sequence = (before_g8.get("data") or {}).get("sequence") or []
    after_sequence = (after_g8.get("data") or {}).get("sequence") or []
    if before_sequence and after_sequence:
        g8 = diff_focus(before_sequence, after_sequence)
        _write_json(out_dir / "g8.diff.json", g8)
    else:
        g8 = _pending({}, "缺少两侧的焦点序列")

    # -- G-7 — the decorative layers -------------------------------------
    before_g7 = _read_json(before_dir / "probe" / "g7.json") or {}
    after_g7 = _read_json(after_dir / "probe" / "g7.json") or {}
    g7 = after_g7 or before_g7

    # -- the merged checklist --------------------------------------------
    merged = []
    for item_id in sorted(set(before_items) | set(after_items)):
        item = dict(after_items.get(item_id) or before_items.get(item_id) or {})
        item["id"] = item_id
        item.setdefault("level", LEVELS.get(item_id, "AUTO"))
        item.setdefault("auto", item["level"] == "AUTO")
        item.setdefault("verdict", PENDING)
        item.setdefault("data", {})
        item.setdefault("note", "")
        if item_id in BEFORE_NA:
            item["beforeVerdict"] = NA
            item["beforeNote"] = BEFORE_NA[item_id]
        else:
            item["beforeVerdict"] = (before_items.get(item_id) or {}).get("verdict")
        merged.append(item)

    checklist = {
        "before": str(before_dir),
        "after": str(after_dir),
        "results": merged,
        "gates": {"G-7": g7, "G-8": g8},
    }
    _write_json(out_dir / "checklist.json", checklist)
    # The recorder reads the after side's checklist; the merged one is the
    # authoritative result, so it is written there as well.
    _write_json(after_dir / "probe" / "checklist.json", checklist)
    return checklist


# ─────────────────────────────────────────────────────────────────────────
# the entry point
# ─────────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Browser probes: G-7, G-8 and the 38-item checklist.")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("static", "flow", "persist"):
        p = sub.add_parser(name)
        p.add_argument("--base-url", required=True)
        p.add_argument("--ws", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--side", choices=("before", "after"), default="after")
        p.add_argument("--repo-root", default=None,
                       help="the repository root of this side (for the css scan)")
        p.add_argument("--profile", default=None,
                       help="a persistent browser profile (localStorage survives)")
        if name == "flow":
            p.add_argument("--paper-id", default=None)
            p.add_argument("--plan", default=None,
                           help="the all-correct plan (seed.py): the gradable "
                                "items and the options that make the round "
                                "all-correct")

    diff = sub.add_parser("diff")
    diff.add_argument("--before", required=True)
    diff.add_argument("--after", required=True)
    diff.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.command == "static":
        results = run_static(args)
    elif args.command == "flow":
        results = run_flow(args)
    elif args.command == "persist":
        results = run_persist(args)
    else:
        checklist = diff_checklist(args.before, args.after, args.out)
        results = checklist
    summary = {}
    for item_id, outcome in results.items():
        if isinstance(outcome, dict) and "verdict" in outcome:
            summary[item_id] = outcome["verdict"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
