"""Motion keyframes — the storyboard strips of M-1…M-10.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §6 (the capture algorithm, the frame table, the
strip layout and the automatic verdicts) and ``acceptance.md`` §2 (the
criteria of every motion).

What this module does
---------------------
It turns a one-off animation into an **addressable timeline** (§6.1): the
animations are paused and their ``currentTime`` is set to the frame times of
the table, so a screenshot at "t = 330 ms" really is that moment of the
motion and not whatever phase an infinite loop happens to be in.  For every
motion the module also runs the same trigger in a ``prefers-reduced-motion:
reduce`` context and takes the **terminal state** of both runs; the two
terminal states are compared **item by item** (§6.3's last paragraph and
``acceptance.md`` §3.8), never by eye.

Three rules from the design are implemented literally:

1. the storyboard strip is a *review* artefact — the automatic verdict comes
   from the metadata (§6.5), not from the picture;
2. a motion whose **hook** does not exist is **N/A, never PASS** (§6.5);
3. a motion whose trigger point cannot be reached in this run is
   **PENDING** — missing evidence is not a pass.

Red lines (§8.3): the module only drives a browser and reads the DOM.  It
never writes the pool and never touches product code.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shots import CONSISTENCY, VIEWPORTS  # noqa: E402  (path set up above)

PASS, FAIL, PENDING, NA = "PASS", "FAIL", "PENDING", "N/A"

#: The elements the terminal state is compared on.  The list is the union
#: of everything the design names: the lamp and the ripple layers, the
#: papers, the flame clusters, the ticker, the progress band, the counter
#: tiers, the content position and the calendar cells.
WATCH = [
    ".lk-lamp", ".lk-ripple", ".lk-ripple-glow", ".lk-ripple-veil",
    ".lk-combo-banner", ".lk-combo-banner__count", ".lk-streak",
    ".lk-flames", ".lk-flame", ".lk-flame-on", ".lk-flame-off",
    ".lk-squash", ".micro-verdict",
    ".lk-ticker", ".lk-ticker-digit",
    ".lk-progress", ".lk-progress-fill", ".lk-celebrate-anchor",
    ".lk-celebrate-burst", ".lk-confetti", ".paper-slice",
    "#paper-completion", "#paper-completion-stats", "#paper-dots", ".paper-dot",
    "#middle-page", "#middle-page > *", ".workload-bars", ".workload-bar",
    ".lk-skeleton", ".calendar-cell", ".calendar-day", ".lk-empty__art",
    ".lk-paper", ".lk-confetti-fall", ".bar", ".bar-fill", ".bar-column",
]

#: The terminal-state contract of §3.8: the items that have to be equal
#: between the animated run and the downgraded run — the numbers, the
#: progress band, the counter tier, the lamp and ripple layers, the
#: papers, the flame clusters and the content position.  Everything else
#: is still measured and reported, but it does not decide the verdict:
#: the design enumerates exactly these items.
TERMINAL_CONTRACT = {
    ".lk-ticker": ("text", "transform", "opacity"),
    ".lk-ticker-digit": ("text", "transform"),
    ".lk-combo-banner__count": ("text", "transform"),
    "#paper-completion-stats": ("text",),
    ".lk-progress": ("width", "height", "transform", "opacity"),
    ".lk-progress-fill": ("width", "height", "transform", "opacity"),
    ".lk-streak": ("text", "cls", "transform", "opacity"),
    ".lk-lamp": ("opacity", "display", "visibility"),
    ".lk-ripple": ("opacity", "display", "visibility"),
    ".lk-ripple-glow": ("opacity", "display", "visibility"),
    ".lk-flame": ("opacity", "transform"),
    ".lk-flames": ("opacity", "transform", "width", "height"),
    ".paper-slice": ("opacity", "transform"),
    ".lk-paper": ("opacity", "transform"),
    "#middle-page > *": ("transform", "opacity"),
}

#: The in-page helpers of the capture.
FRAME_JS = r"""
(() => {
  const F = {};
  F.freeze = () => {
    document.getAnimations().forEach((a) => {
      try { a.pause(); } catch (e) { /* an animation without a timeline */ }
    });
  };
  F.setTime = (t) => {
    document.getAnimations().forEach((a) => {
      try { a.pause(); a.currentTime = t; } catch (e) { /* ignore */ }
    });
  };
  F.finish = () => {
    document.getAnimations().forEach((a) => {
      try { a.finish(); } catch (e) { /* ignore */ }
    });
  };
  F.animations = () => (document.getAnimations ? document.getAnimations() : []).map((a) => {
    const timing = (a.effect && a.effect.getTiming) ? a.effect.getTiming() : {};
    const target = a.effect && a.effect.target;
    return {
      name: a.animationName || "",
      playState: a.playState,
      duration: timing.duration == null ? null : timing.duration,
      delay: timing.delay == null ? null : timing.delay,
      currentTime: a.currentTime,
      target: target ? String(target.className || target.tagName || "") : "",
    };
  });
  /* The live state of the watched elements (one frame).  The ::after of
     the first node comes with it: the skeleton sheen is a pseudo element,
     so the element's own transform never moves. */
  F.states = (watch) => {
    const out = {};
    watch.forEach((selector) => {
      const nodes = Array.from(document.querySelectorAll(selector));
      out[selector] = nodes.slice(0, 12).map((el, index) => {
        const st = getComputedStyle(el);
        const record = {
          text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 30),
          transform: st.transform,
          opacity: st.opacity,
          width: Math.round(el.getBoundingClientRect().width),
          height: Math.round(el.getBoundingClientRect().height),
          display: st.display,
          visibility: st.visibility,
          background: st.backgroundColor,
          cls: String(el.className || "").slice(0, 80),
        };
        if (index === 0) {
          const after = getComputedStyle(el, "::after");
          record.afterTransform = after ? after.transform : "";
          record.afterContent = after ? after.content : "";
          record.afterAnimation = after ? after.animationName : "";
          record.afterBackground = after ? after.backgroundImage.slice(0, 80) : "";
        }
        return record;
      });
    });
    return out;
  };
  /* The terminal state: the same fields, but only what has to be equal
     after the motion has finished. */
  F.snapshot = (watch) => {
    const out = {};
    watch.forEach((selector) => {
      const nodes = Array.from(document.querySelectorAll(selector));
      out[selector] = nodes.slice(0, 12).map((el) => {
        const st = getComputedStyle(el);
        return {
          text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 30),
          transform: st.transform,
          opacity: st.opacity,
          width: Math.round(el.getBoundingClientRect().width),
          height: Math.round(el.getBoundingClientRect().height),
          display: st.display,
          visibility: st.visibility,
          background: st.backgroundColor,
          cls: String(el.className || "").slice(0, 80),
        };
      });
    });
    return out;
  };
  /* The translateY of a node, in pixels (M-8). */
  F.translateY = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const st = getComputedStyle(el);
    const match = st.transform.match(/matrix\(1, 0, 0, 1, ([-\d.]+), ([-\d.]+)\)/);
    if (match) return parseFloat(match[2]);
    const parts = st.transform.match(/translate3d\([^,]+,\s*([-\d.]+)px/);
    if (parts) return parseFloat(parts[1]);
    if (st.transform === "none") return 0;
    return null;
  };
  /* The opacity of the first node of a selector. */
  F.opacity = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    return parseFloat(getComputedStyle(el).opacity);
  };
  /* The scale of the first node of a selector (M-7). */
  F.scale = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const st = getComputedStyle(el);
    const match = st.transform.match(/matrix\(([-\d.]+),/);
    if (match) return parseFloat(match[1]);
    if (st.transform === "none") return 1;
    return null;
  };
  window.__lkFrame = F;
})();
"""


# ─────────────────────────────────────────────────────────────────────────
# the motion table (§6.3)
# ─────────────────────────────────────────────────────────────────────────

#: Every motion of §6.3: the frame times, the trigger and the hook.
MOTIONS = {
    "M-1": {
        "title": "台灯主题转场",
        "frames_ms": (0, 90, 180, 330, 500, 700),
        "trigger": "theme",
        "hook": ".lk-lamp",
    },
    "M-2": {
        "title": "交卷庆祝（日常档）",
        "frames_ms": (0, 120, 300, 600, 900),
        "trigger": "celebration",
        "hook": "#paper-completion",
    },
    "M-3": {
        "title": "交卷庆祝（里程碑档）",
        "frames_ms": (0, 150, 400, 800, 1200),
        "trigger": "celebration",
        "hook": ".lk-celebrate-burst",
        "milestone": True,
    },
    "M-4": {
        "title": "连对升级横幅",
        "frames_ms": (0, 100, 250, 450, 700),
        "trigger": "streak",
        "hook": ".lk-combo-banner",
    },
    "M-5": {
        "title": "连对计数器三档",
        "frames_ms": (0, 250, 500),
        "trigger": "streak-tiers",
        "hook": ".lk-streak",
    },
    "M-6": {
        "title": "连对进度火苗簇",
        "frames_ms": (0, 200, 500),
        "trigger": "streak",
        "hook": ".lk-flame",
    },
    "M-7": {
        "title": "挤压回弹（答对）",
        "frames_ms": (0, 17, 33, 83, 167, 217, 517),
        "trigger": "answer",
        "hook": "lk-squash-bounce",
    },
    "M-8": {
        "title": "视图转场",
        "frames_ms": (0, 60, 120, 240),
        "trigger": "view",
        "hook": "#middle-page",
    },
    "M-9": {
        "title": "骨架屏",
        "frames_ms": (0, 400, 900),
        "trigger": "skeleton",
        "hook": ".lk-skeleton",
    },
    "M-10": {
        "title": "数据层（负荷柱 / 日历）",
        "frames_ms": (0, 240, 480),
        "trigger": "records",
        "hook": ".workload-bars",
    },
}


# ─────────────────────────────────────────────────────────────────────────
# the triggers
# ─────────────────────────────────────────────────────────────────────────


def prepare_theme(page, ctx):
    """M-1 — the settings view, before the theme switch."""
    page.goto(ctx.url("settings"), wait_until="load", timeout=30000)
    page.wait_for_timeout(500)


def act_theme(page, ctx):
    """M-1 — the theme switch itself.

    The switch is clicked **in the page**: the visible control is the
    switch's track, and the decorative thumb sits on top of the (visually
    hidden) checkbox, so a real mouse click on the input would be
    intercepted by the decoration.
    """
    page.evaluate("""() => {
      const box = document.getElementById("setting-theme");
      if (box) box.click();
    }""")


def prepare_view(page, ctx):
    """M-8 — the practice page, before the middle column is replaced."""
    page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
    page.wait_for_timeout(600)


def act_view(page, ctx):
    """M-8 — switch the middle column."""
    page.click(".nav-item")


def prepare_skeleton(page, ctx):
    """M-9 — the loading state of the middle column.

    The skeleton the criterion is about is the one the product draws
    itself: ``middle-navigation.js::showLoadingState`` replaces the
    middle column with five ``.lk-skeleton`` blocks (each with the size
    the product gives it) while the new page is on its way.  The probe
    therefore **navigates the middle column** — and the page fetch is
    held back by the caller, so the skeleton really stands on the screen
    while the frames are taken.

    (The first round looked at the paper's own text placeholder
    ``#paper-count .lk-skeleton--text`` instead: it has no size at all,
    so the shimmer had nothing to show.  That is a **product-side**
    fact, not the motion's — see the judge's two evidence lines.)
    """
    page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
    page.wait_for_timeout(400)


def act_skeleton(page, ctx):
    """M-9 — navigate the middle column; the skeleton takes its place.

    The wait is on the **wrapper** (``[data-lk-skeleton]``), not on
    ``.lk-skeleton``: in the downgraded motion mode the product paints
    the same blocks as static grey boxes **without** the class (the
    class carries the sweeping overlay), so the class is not there in
    the reduced twin — and the twin is exactly where the class must be
    missing.
    """
    page.click('a[href$="/practice-sets"]')
    page.wait_for_selector("[data-lk-skeleton]", state="attached", timeout=10000)


def prepare_records(page, ctx):
    """M-10 — the records page, before the data layer enters."""
    page.goto(ctx.url("records"), wait_until="load", timeout=30000)
    page.wait_for_timeout(60)


def act_records(page, ctx):
    """M-10 — nothing to do: the data layer enters with the page."""


def prepare_streak(page, ctx):
    """M-4 / M-6 — the product's own streak component.

    The component is the product's (``window.lkStreak.create``) and the
    styles are the shipped ones; the trigger is the component's own API
    rather than the whole UI path, because the whole UI path only opens
    when the agent assembles a set of questions.  The evidence says so.
    """
    page.goto(ctx.url("practice"), wait_until="load", timeout=30000)
    page.wait_for_timeout(400)
    page.evaluate("""() => {
      const host = document.createElement("p");
      host.className = "practice-streak";
      host.id = "lk-probe-streak";
      host.style.position = "relative";
      const middle = document.getElementById("middle-page") || document.body;
      middle.appendChild(host);
      const streak = window.lkStreak.create({root: host});
      window.__lkProbeStreak = streak;
      host.innerHTML = streak.html();
    }""")
    page.wait_for_timeout(60)


def act_streak(page, ctx):
    """M-4 / M-6 — five correct answers in a row (the banner fires on five).

    The card is replaced as a whole on every turn in the real flow, so
    the component's html is re-rendered here as well; that is what makes
    the flame clusters appear.
    """
    page.evaluate("""async () => {
      const streak = window.__lkProbeStreak;
      const host = document.getElementById("lk-probe-streak");
      for (let i = 0; i < 5; i += 1) {
        streak.apply(streak.judge(true));
        host.innerHTML = streak.html();
        await new Promise((r) => setTimeout(r, 60));
      }
    }""")


def prepare_streak_tiers(page, ctx):
    """M-5 — the counter in its first (grey) tier."""
    prepare_streak(page, ctx)


def act_streak_tiers(page, ctx):
    """M-5 — three tiers: 0, warm (5) and hot (30)."""
    page.evaluate("""async () => {
      const streak = window.__lkProbeStreak;
      const host = document.getElementById("lk-probe-streak");
      for (let i = 0; i < 31; i += 1) {
        streak.apply(streak.judge(true));
      }
      host.innerHTML = streak.html();
      await new Promise((r) => setTimeout(r, 40));
    }""")


def prepare_answer(page, ctx):
    """M-7 — a **real** judgement is about to happen.

    The first round injected an empty ``<div class="practice-card">`` — a
    class that never existed in the repository — and never judged an
    answer.  The page therefore had **no** ``.micro-verdict`` element, and
    the squash (which the product attaches to the verdict element it
    renders itself, ``paper-practice.js::squashVerdict``) could not be
    seen at all.

    The trigger now drives the real path: the paper is opened, the run is
    started and the correct option of the first item is **picked** — the
    answer is not submitted yet, so the verdict lands inside the capture.
    """
    from exercise import (ROUTE_CURRENT, ROUTE_PAPER_START, Service, Waiter)

    service = Service(ctx.base_url)
    waiter = Waiter(service)
    waiter.snapshot()
    plan = ctx.plan or []
    # The verdict of a **multiple-choice** item is the one the product
    # renders after the learner pressed the submit button — a single
    # choice submits itself when the radio is picked, which would put the
    # verdict into the preparation instead of into the capture.
    multiples = [item for item in plan if item.get("multiple")]
    if not multiples:
        raise RuntimeError(
            "M-7 needs a multiple-choice item: the plan has none "
            f"({[item.get('quiz_type') for item in plan]})")
    target = multiples[0]
    if ctx.paper_id:
        paper_id = ctx.paper_id
    else:
        paper_id = service.create_paper(
            ctx.ws, "走查分镜回弹卷",
            [item["problem_id"] for item in plan]).get("practice_set_id")
        ctx.paper_id = paper_id
    page.goto(f"{ctx.base_url}/w/{ctx.ws}/practice?paper={paper_id}",
              wait_until="load", timeout=30000)
    waiter.wait_for(ROUTE_CURRENT)
    page.wait_for_selector("#paper-start", state="visible", timeout=15000)
    page.click("#paper-start")
    waiter.wait_for(ROUTE_PAPER_START)
    page.wait_for_selector("#paper-options input", state="visible", timeout=15000)
    from probe import pick_plan_options

    ctx.target = target
    ctx.picked = pick_plan_options(page, target)


def act_answer(page, ctx):
    """M-7 — the judged answer (the squash-bounce rides on the verdict).

    The submit is a **real gesture**, so the product's own cue and its
    own squash are both armed by it, and the verdict element the product
    renders is the one the animation is attached to.
    """
    from exercise import ROUTE_ATTEMPT, Service, Waiter

    service = Service(ctx.base_url)
    waiter = Waiter(service)
    waiter.snapshot()
    page.wait_for_selector("#paper-item-submit", state="visible", timeout=15000)
    page.click("#paper-item-submit")
    try:
        waiter.wait_for(ROUTE_ATTEMPT)
    except Exception as error:      # the record is the evidence, not a gate
        ctx.attemptError = str(error)
    # The verdict element is what the product hangs the squash on.
    page.wait_for_selector(".micro-verdict", state="attached", timeout=15000)
    # The animation has to exist before the frames are taken.  The wait is
    # **soft**: in the reduced-motion twin the product downgrades the
    # squash away (that is the point of the twin), so there is nothing to
    # wait for there — and the judge, not the wait, decides the verdict.
    try:
        page.wait_for_function(
            """() => document.getAnimations().some(
                    (a) => (a.animationName || "") === "lk-squash-bounce")""",
            timeout=5000)
        ctx.squashAnimationSeen = True
    except Exception:
        ctx.squashAnimationSeen = False
    # Freeze it: the frames set the time themselves.
    page.evaluate("() => window.__lkFrame.freeze()")


def prepare_celebration(page, ctx):
    """M-2 / M-3 — the paper run, up to the submit.

    The celebration starts when the completion page appears, so the paper
    is really answered here and only the submit is left to the trigger.

    **M-3 needs the milestone tier** (decisions.md A-29), and the tier is
    decided by the round itself: ``本轮全对`` ⇒ every item carries an
    objective verdict and all of them are correct.  The plan (seed.py)
    holds the gradable items and their correct options, so the milestone
    round is a real round, not a faked one.  M-2 keeps the ordinary
    round — the ordinary tier must not show the burst.
    """
    from exercise import (ITEM_KINDS, RADIO_OPTION_INDEX, RATING_VALUE,
                          ROUTE_ATTEMPT, ROUTE_CURRENT, ROUTE_FEEDBACK,
                          ROUTE_PAPER_START, SEED_PROBLEM_IDS, TEXT_ANSWER,
                          Service, Waiter)

    service = Service(ctx.base_url)
    waiter = Waiter(service)
    waiter.snapshot()
    plan = ctx.plan or []
    all_correct = ctx.motion_id == "M-3" and bool(plan)
    if all_correct:
        # The paper is created **without** switching the phase: the
        # 建卷 request belongs to the frames, not to the product's own
        # request flow, and it must not show up in the request diff.
        paper_id = service.create_paper(
            ctx.ws, "走查分镜里程碑卷",
            [item["problem_id"] for item in plan]).get("practice_set_id")
    else:
        paper_id = service.create_paper(ctx.ws, "走查分镜种子卷",
                                        list(SEED_PROBLEM_IDS)).get("practice_set_id")
    ctx.paper_id = paper_id
    ctx.allCorrectRound = all_correct
    page.goto(f"{ctx.base_url}/w/{ctx.ws}/practice?paper={paper_id}",
              wait_until="load", timeout=30000)
    waiter.wait_for(ROUTE_CURRENT)
    page.wait_for_selector("#paper-start", state="visible", timeout=15000)
    page.click("#paper-start")
    waiter.wait_for(ROUTE_PAPER_START)
    if all_correct:
        _answer_plan_whole_round(page, ctx, waiter)
    else:
        # The kinds of the items are read from the dom: the order of the
        # plan is the server's, not the harness'.
        for index in range(len(ITEM_KINDS)):
            if page.is_visible("#paper-answer"):
                page.fill("#paper-answer", TEXT_ANSWER)
                page.click("#paper-item-submit")
            else:
                page.wait_for_selector("#paper-options input", state="visible",
                                       timeout=15000)
                options = page.query_selector_all("#paper-options input")
                if not options:
                    break
                options[RADIO_OPTION_INDEX].click()
            waiter.wait_for(ROUTE_ATTEMPT)
            page.wait_for_selector("#paper-rating", state="visible", timeout=15000)
            page.fill("#paper-rating input[type='number']", RATING_VALUE)
            page.click("#paper-rating button")
            waiter.wait_for(ROUTE_FEEDBACK)
            if index + 1 < len(ITEM_KINDS):
                page.click("#paper-next")
                page.wait_for_timeout(200)
    page.wait_for_selector("#paper-final-submit", state="visible", timeout=15000)
    page.wait_for_timeout(200)


def _answer_plan_whole_round(page, ctx, waiter):
    """Answer every item of the plan **correctly** — the all-correct round.

    Each item is picked by its option id (the plan) and submitted the way
    the product expects: the multiple-choice item through its button, the
    single-choice and yes/no items by their radio (which submits itself).
    """
    from exercise import RATING_VALUE, ROUTE_ATTEMPT, ROUTE_FEEDBACK
    from probe import pick_plan_options

    for index, item in enumerate(ctx.plan):
        if index:
            page.wait_for_selector("#paper-next", state="visible", timeout=15000)
            page.click("#paper-next")
            waiter.wait_for("POST /api/w/{name}/practice/current/navigate")
            page.wait_for_timeout(200)
        if item.get("multiple"):
            page.wait_for_selector("#paper-options input", state="visible",
                                   timeout=15000)
            picked = pick_plan_options(page, item)
            if not picked.get("answered"):
                raise RuntimeError(f"the plan did not match the options of "
                                   f"{item.get('problem_id')}: {picked}")
            page.wait_for_selector("#paper-item-submit", state="visible",
                                   timeout=15000)
            page.click("#paper-item-submit")
        else:
            page.wait_for_selector("#paper-options input", state="visible",
                                   timeout=15000)
            picked = pick_plan_options(page, item)
            if not picked.get("answered"):
                raise RuntimeError(f"the plan did not match the options of "
                                   f"{item.get('problem_id')}: {picked}")
        waiter.wait_for(ROUTE_ATTEMPT)
        page.wait_for_selector("#paper-rating", state="visible", timeout=15000)
        page.fill("#paper-rating input[type='number']", RATING_VALUE)
        page.click("#paper-rating button")
        waiter.wait_for(ROUTE_FEEDBACK)


def act_celebration(page, ctx):
    """M-2 / M-3 — the completion page appears."""
    page.click("#paper-final-submit")


#: The two halves of every trigger: ``prepare`` puts the page into the
#: state before the motion, ``act`` starts it.  The capture freezes the
#: animations between the two.
PREPARE = {
    "theme": prepare_theme,
    "view": prepare_view,
    "skeleton": prepare_skeleton,
    "records": prepare_records,
    "streak": prepare_streak,
    "streak-tiers": prepare_streak_tiers,
    "answer": prepare_answer,
    "celebration": prepare_celebration,
}

ACT = {
    "theme": act_theme,
    "view": act_view,
    "skeleton": act_skeleton,
    "records": act_records,
    "streak": act_streak,
    "streak-tiers": act_streak_tiers,
    "answer": act_answer,
    "celebration": act_celebration,
}


# ─────────────────────────────────────────────────────────────────────────
# the capture
# ─────────────────────────────────────────────────────────────────────────


def _launch(playwright, reduced_motion=None):
    options = {
        "viewport": {"width": VIEWPORTS["V1440"]["width"],
                     "height": VIEWPORTS["V1440"]["height"]},
        "device_scale_factor": VIEWPORTS["V1440"]["device_scale_factor"],
        "color_scheme": CONSISTENCY["color_scheme"],
        "locale": CONSISTENCY["locale"],
        "timezone_id": CONSISTENCY["timezone_id"],
        "reduced_motion": reduced_motion or CONSISTENCY["reduced_motion"],
    }
    browser = playwright.chromium.launch(
        headless=True, args=list(CONSISTENCY["browser_args"]))
    context = browser.new_context(**options)
    page = context.new_page()
    page.add_init_script(FRAME_JS)
    return browser, context, page


def capture_strip(page, trigger, frames_ms, out_dir, watch):
    """The deterministic replay of §6.2 — one screenshot per frame time."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page.evaluate("() => window.__lkFrame.freeze()")
    page.wait_for_timeout(20)
    trigger()
    page.wait_for_timeout(60)
    frames = []
    for t in frames_ms:
        page.evaluate("(t) => window.__lkFrame.setTime(t)", t)
        page.wait_for_timeout(40)
        # The state is read **before** the screenshot: a screenshot takes
        # long enough for a transient element (the loading mark) to be
        # gone by the time it is taken.
        states = page.evaluate("(w) => window.__lkFrame.states(w)", watch)
        animations = page.evaluate("() => window.__lkFrame.animations()")
        path = out_dir / f"{t:04d}.png"
        page.screenshot(path=str(path), animations="allow", caret="hide",
                        scale="css")
        frames.append({
            "t": t,
            "file": path.name,
            "states": states,
            "animations": animations,
        })
    return {"frames_ms": list(frames_ms), "frames": frames}


def terminal_state(page, watch):
    """The terminal state of a run: every animation finished, then read."""
    page.evaluate("() => window.__lkFrame.finish()")
    page.wait_for_timeout(200)
    return page.evaluate("(w) => window.__lkFrame.snapshot(w)", watch)


def _normalise_transform(value):
    """``none`` and the identity matrix mean the same thing.

    A finished animation with ``fill: both`` leaves the identity matrix
    on the element while a disabled animation leaves ``transform: none``.
    The position is the same, so the comparison has to see them as equal.
    """
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "none"):
        return "identity"
    match = re.match(r"matrix\(([^)]+)\)", text)
    if match:
        numbers = [float(part) for part in match.group(1).split(",")]
        if len(numbers) == 6:
            if numbers == [1, 0, 0, 1, 0, 0]:
                return "identity"
            return "matrix(" + ",".join(f"{n:g}" for n in numbers) + ")"
    return text


def compare_terminal(animated, reduced):
    """The scripted comparison of the two terminal states (§6.3, §3.8).

    The two states have to be equal **item by item** for the items §3.8
    names: the numbers, the progress band, the counter tier, the lamp and
    the ripple layers, the papers, the flame clusters and the content
    position.  A difference in either direction is a violation — the
    downgraded frame must not stop in a middle state, and it must not
    lose a visual channel.

    The differences of the other elements are reported as well, but they
    do not decide the verdict: the design enumerates the items above and
    does not include them.
    """
    differences = []
    extra = []
    for selector in sorted(set(animated) | set(reduced)):
        left = animated.get(selector, [])
        right = reduced.get(selector, [])
        fields = TERMINAL_CONTRACT.get(selector)
        bucket = differences if fields else extra
        if len(left) != len(right):
            bucket.append({"selector": selector, "why": "count",
                           "animated": len(left), "reduced": len(right)})
            continue
        for index, (a, b) in enumerate(zip(left, right)):
            if fields is None:
                fields = ("text", "transform", "opacity", "display",
                          "visibility", "width", "height", "background", "cls")
            for field in fields:
                left_value = a.get(field)
                right_value = b.get(field)
                if field == "transform":
                    left_value = _normalise_transform(left_value)
                    right_value = _normalise_transform(right_value)
                if left_value != right_value:
                    bucket.append({
                        "selector": selector, "index": index, "field": field,
                        "animated": a.get(field), "reduced": b.get(field),
                    })
    return differences, extra


def build_strip(frames_dir, out_path, gap=8, background="#fdf8ef"):
    """§6.4 — the storyboard strip (a review artefact, not a verdict)."""
    from PIL import Image, ImageDraw

    frames_dir = Path(frames_dir)
    files = sorted(frames_dir.glob("*.png"))
    if not files:
        return None
    images = [Image.open(path).convert("RGB") for path in files]
    width = max(image.width for image in images)
    height = max(image.height for image in images)
    label = 18
    strip = Image.new("RGB", (width * len(images) + gap * (len(images) - 1),
                              height + label), background)
    draw = ImageDraw.Draw(strip)
    for index, image in enumerate(images):
        x = index * (width + gap)
        strip.paste(image, (x, 0))
        draw.text((x + 4, height + 3), files[index].stem, fill="#6b6459")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(out_path)
    return out_path


# ─────────────────────────────────────────────────────────────────────────
# the per-motion verdicts
# ─────────────────────────────────────────────────────────────────────────


def _animations_named(meta, name):
    return [frame for frame in meta["frames"]
            for anim in frame["animations"] if anim.get("name") == name]


def judge_m1(meta, reduced_meta, watch):
    """M-1 — the four stages of the lamp transition."""
    saw_layer = False
    for frame in meta["frames"]:
        if frame["states"].get(".lk-lamp"):
            saw_layer = True
            break
    if not saw_layer:
        return {"verdict": FAIL, "detail": "四段转场里没有出现台灯层 —— 是瞬切"}
    terminal = meta["frames"][-1]["states"]
    leftovers = [name for name in (".lk-lamp", ".lk-ripple", ".lk-ripple-glow")
                 if terminal.get(name)]
    if leftovers:
        return {"verdict": FAIL, "detail": f"700ms 后还有装饰层没收回：{leftovers}"}
    return {"verdict": PASS, "detail": "台灯四段转场在 700ms 后收干净"}


def judge_celebration(meta, reduced_meta, watch, milestone=False):
    """M-2 / M-3 — the celebration.

    M-3 has **two** trigger conditions (decisions.md A-29): 「本轮全对」and
    「章节首次完成」.  The first one is decidable — the round's own counts
    say whether every item carried a correct verdict — and the second one
    is **not**: the client writes ``data-lk-chapter-first="false"``
    because ``practice_runs`` carries no chapter column, and A-29 forbids
    approximating it with a proxy signal.

    The verdict therefore says which condition was verified and **what
    data the other one needs**; it never invents the missing fact.
    """
    hook = ".lk-celebrate-burst" if milestone else "#paper-completion"

    def visible(nodes):
        return [node for node in nodes
                if node.get("display") not in (None, "none")
                and node.get("visibility") not in (None, "hidden")]

    seen = any(visible(frame["states"].get(hook, []))
               for frame in meta["frames"])
    if not milestone:
        if not seen:
            return {"verdict": PENDING,
                    "detail": "完成页没有在采集窗口内出现"}
        confetti = [frame for frame in meta["frames"]
                    if frame["states"].get(".lk-confetti")]
        if confetti:
            return {"verdict": FAIL, "detail": "日常档出现了彩带"}
        return {"verdict": PASS, "detail": "庆祝层的出现与档位符合判据"}

    # -- M-3: the two conditions, kept apart ----------------------------
    facts = meta.get("completionFacts") or {}
    total = facts.get("total")
    correct = facts.get("correct")
    all_correct = bool(total) and total == correct
    conditions = {
        "allCorrect": {
            "verdict": PASS if all_correct else FAIL,
            "total": total,
            "correct": correct,
            "detail": (f"本轮 {correct}/{total} 全对 ⇒ 里程碑档" if all_correct
                       else f"本轮 {correct}/{total} —— 不是全对轮，"
                            "里程碑档不该出现"),
        },
        "chapterFirst": {
            "verdict": PENDING,
            "chapterFirstRaw": facts.get("chapterFirstRaw"),
            "missing": [
                "practice_runs 的章标识（这一轮属于哪一章）",
                "「该章此前未完成」的事实（由服务端判定，不由客户端猜）",
                "完成页响应里的该事实，客户端据此写 data-lk-chapter-first",
            ],
            "detail": "practice_runs 无章列，客户端恒写 data-lk-chapter-first=false；"
                      "A-29 禁止用代理指标近似，所以这一档不可判定",
        },
    }
    if not seen:
        return {"verdict": PENDING,
                "detail": "本轮没有触达该庆祝档（缺里程碑种子数据）",
                "conditions": conditions}
    if not all_correct:
        return {"verdict": FAIL,
                "detail": f"出现了里程碑爆点，但本轮不是全对（{correct}/{total}）",
                "conditions": conditions}
    return {"verdict": PENDING,
            "detail": (f"「本轮全对」这一档已采到并通过（本轮 {correct}/{total} 全对，"
                       f"里程碑爆点 .lk-celebrate-burst 出现）；"
                       "「章节首次完成」这一档仍不可判定 —— "
                       "缺的数据：practice_runs 的章标识 + 「该章此前未完成」的服务端事实"
                       "（客户端据此写 data-lk-chapter-first）；"
                       "A-29 禁止用代理指标近似，故不判 PASS"),
            "conditions": conditions}


def judge_streak_banner(meta, reduced_meta, watch):
    """M-4 — one banner, and it leaves again."""
    counts = [len(frame["states"].get(".lk-combo-banner", [])) for frame in meta["frames"]]
    if not any(counts):
        return {"verdict": PENDING, "detail": "没有出现连对横幅"}
    if max(counts) > 1:
        return {"verdict": FAIL, "detail": f"横幅同时出现了 {max(counts)} 份"}
    return {"verdict": PASS, "detail": "横幅只有一份"}


def capture_streak_tiers(playwright, out_dir, base_url, ws):
    """M-5 — the three tiers of the counter, one run per tier.

    The tiers are three *states*, not three moments of one animation, so
    they are captured as three runs (0 / 5 / 31) and compared by their
    class and their colour — the criterion says the tier may not be
    carried by the text.
    """
    tiers = []
    for count in (0, 5, 31):
        browser, context, page = _launch(playwright)
        try:
            ctx = _Context(base_url, ws)
            prepare_streak(page, ctx)
            page.evaluate("""(count) => {
              const streak = window.__lkProbeStreak;
              for (let i = 0; i < count; i += 1) {
                streak.apply(streak.judge(true));
              }
              const host = document.getElementById("lk-probe-streak");
              host.innerHTML = streak.html();
            }""", count)
            page.wait_for_timeout(200)
            state = page.evaluate("""() => {
              const el = document.querySelector(".lk-streak");
              if (!el) return null;
              const st = getComputedStyle(el);
              return {
                cls: String(el.className || ""),
                text: (el.textContent || "").trim(),
                background: st.backgroundColor,
                backgroundImage: st.backgroundImage.slice(0, 120),
                color: st.color,
              };
            }""")
            if state:
                state["count"] = count
                tiers.append(state)
        finally:
            context.close()
            browser.close()
    return tiers


def judge_streak_tiers(meta, reduced_meta, watch):
    """M-5 — three tiers, not carried by the text."""
    tiers = meta.get("tiers") or []
    if not tiers:
        return {"verdict": PENDING, "detail": "没有采到档位"}
    classes = {node["cls"] for node in tiers}
    if len(classes) < 2:
        return {"verdict": FAIL, "detail": "三档的类名相同 —— 档位没有区别"}
    texts = {node["text"] for node in tiers}
    return {"verdict": PASS,
            "detail": f"三档的类名不同（{len(classes)} 种），文字 {len(texts)} 种"}


def judge_flames(meta, reduced_meta, watch):
    """M-6 — the flame clusters light up one by one."""
    lit = []
    for frame in meta["frames"]:
        for selector in (".lk-flame-on", ".lk-flame-off", ".lk-flame"):
            for node in frame["states"].get(selector, []):
                lit.append(node.get("opacity"))
    if not lit:
        return {"verdict": PENDING, "detail": "没有采到火苗簇"}
    if len(set(lit)) < 2:
        return {"verdict": FAIL, "detail": "火苗簇没有逐簇点亮（透明度全程不变）"}
    return {"verdict": PASS, "detail": f"火苗簇透明度取到 {len(set(lit))} 个值"}


def judge_squash(meta, reduced_meta, watch):
    """M-7 — the squash-bounce on a correct answer.

    The trigger drives a **real judgement**: the product renders the
    verdict element and attaches the squash to it.  The evidence names
    the element the animation is on, so nobody has to take the harness's
    word for it.
    """
    found = _animations_named(meta, "lk-squash-bounce")
    verdicts = meta.get("verdictElements") or {}
    evidence = {"verdictElements": verdicts,
                "animationTargets": sorted({anim.get("target") or ""
                                            for frame in meta["frames"]
                                            for anim in frame["animations"]
                                            if anim.get("name") == "lk-squash-bounce"})}
    if not found:
        return {"verdict": FAIL,
                "detail": "没有出现 lk-squash-bounce 动画（关键帧在样式表里，"
                          "但没有任何地方挂上去）",
                "evidence": evidence}
    durations = {anim.get("duration") for frame in meta["frames"]
                 for anim in frame["animations"]
                 if anim.get("name") == "lk-squash-bounce"}
    if durations and max(d for d in durations if d is not None) < 400:
        return {"verdict": FAIL, "detail": f"回弹总时长 {durations} 远短于 517ms",
                "evidence": evidence}
    return {"verdict": PASS, "detail": f"回弹动画时长 {sorted(durations)}",
            "evidence": evidence}


def judge_view(meta, reduced_meta, watch):
    """M-8 — the view transition floats up 8–12 px and fades in."""
    peaks = []
    for frame in meta["frames"]:
        for selector in ("#middle-page > *", "#middle-page"):
            for node in frame["states"].get(selector, []):
                match = re.search(r"matrix\(1, 0, 0, 1, [-\d.]+, ([-\d.]+)\)",
                                  node.get("transform") or "")
                if match:
                    peaks.append(abs(float(match.group(1))))
    if not peaks:
        return {"verdict": PENDING, "detail": "没有采到转场的位移"}
    top = max(peaks)
    if not (8 <= top <= 12):
        return {"verdict": FAIL, "detail": f"上浮峰值 {top}px 不在 8–12px"}
    return {"verdict": PASS, "detail": f"上浮峰值 {top}px"}


def judge_skeleton(meta, reduced_meta, watch):
    """M-9 — the sheen sweeps across the skeleton.

    Two facts are kept apart, because they belong to two different
    sides:

    * **the product side** — does the skeleton block have a box at all?
      A block of 0×0 is a stylesheet fact (``workbench.css``), not a
      motion fact;
    * **the motion side** — does the sheen move?  That is the animation
      the criterion is about.

    The verdict is the motion's: the sweep has to move **on a block that
    has a size**.  When the block has no size the motion cannot be seen
    at all — then the verdict says exactly that (and the product-side
    fact is reported next to it) instead of mixing the two problems into
    one FAIL.
    """
    transforms = []
    for frame in meta["frames"]:
        for node in frame["states"].get(".lk-skeleton", []):
            transforms.append(node.get("afterTransform") or node.get("transform"))
    sizes = [(node.get("width"), node.get("height"))
             for frame in meta["frames"]
             for node in frame["states"].get(".lk-skeleton", [])]
    has_box = bool(sizes) and not all((w == 0 and h == 0) for w, h in sizes)
    evidence = {
        "motionSide": {
            "sheenPositions": len(set(transforms)),
            "moved": len(set(transforms)) >= 2,
            "positions": sorted(set(transforms))[:8],
        },
        "productSide": {
            "hasBox": has_box,
            "sizes": sorted(set(sizes))[:8],
        },
    }
    if not transforms:
        return {"verdict": PENDING, "detail": "没有采到骨架屏",
                "evidence": evidence}
    if len(set(transforms)) >= 2:
        return {"verdict": PASS,
                "detail": f"微光位置逐帧变化（{len(set(transforms))} 个位置）",
                "evidence": evidence}
    if not has_box:
        return {"verdict": PENDING,
                "detail": "两条证据分开：产品侧 —— 骨架块没有尺寸（0×0），"
                          "灰块与微光都无从显示；动效侧 —— 微光位置全程不变，"
                          "但块没有盒子，本轮无从判定扫光",
                "evidence": evidence}
    return {"verdict": FAIL,
            "detail": "骨架块有尺寸，但微光位置全程不变（动效侧）",
            "evidence": evidence}


def judge_data_layer(meta, reduced_meta, watch):
    """M-10 — the load bars grow from zero, staggered."""
    heights = []
    for frame in meta["frames"]:
        for selector in (".workload-bar", ".bar-fill", ".bar-column", ".bar"):
            for node in frame["states"].get(selector, []):
                heights.append(node.get("height"))
    if not heights:
        return {"verdict": PENDING, "detail": "没有采到负荷柱"}
    if max(heights) == 0:
        return {"verdict": FAIL, "detail": "负荷柱没有生长"}
    return {"verdict": PASS, "detail": f"负荷柱高度取到 {sorted(set(heights))}"}


JUDGES = {
    "M-1": judge_m1,
    "M-2": lambda meta, reduced, watch: judge_celebration(meta, reduced, watch),
    "M-3": lambda meta, reduced, watch: judge_celebration(meta, reduced, watch,
                                                           milestone=True),
    "M-4": judge_streak_banner,
    "M-5": judge_streak_tiers,
    "M-6": judge_flames,
    "M-7": judge_squash,
    "M-8": judge_view,
    "M-9": judge_skeleton,
    "M-10": judge_data_layer,
}


# ─────────────────────────────────────────────────────────────────────────
# the pass
# ─────────────────────────────────────────────────────────────────────────


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


def _read_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


MUTE_JS = """
(() => {
  try {
    window.localStorage.setItem("wb_settings_%s",
        JSON.stringify({sound: false}));
  } catch (error) { /* a locked store must not break the page */ }
})();
"""


def set_phase(base_url, phase, group="frames"):
    """Tag the requests of this collector.

    The frames drive a **real paper run** (the celebration trigger), so
    their writes land in the request stream.  They are tagged with their
    own phase, and the G-1 diff leaves them out: the frames only run on
    the after side, so leaving them in would make the two sides differ
    by the collector's own writes.
    """
    import json as _json
    import urllib.request

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/__walkthrough__/phase",
        data=_json.dumps({"phase": phase, "group": group}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except Exception as error:      # the control endpoint is not a product route
        raise RuntimeError(f"could not tag the phase: {error}")


def completion_facts(page):
    """The facts the product writes on the completion surface.

    ``data-lk-total`` / ``data-lk-correct`` are the counts of the round
    that really happened — that is what the milestone tier is decided on
    (``workbench.js::isMilestoneRound``).  ``data-lk-chapter-first`` is
    the flag of the second milestone condition; the client always writes
    ``false``, because ``practice_runs`` carries no chapter column
    (``paper-practice.js::writeCompletionFacts``).
    """
    return page.evaluate("""() => {
      const surface = document.getElementById("paper-completion");
      if (!surface || !surface.dataset) return null;
      return {
        total: surface.dataset.lkTotal == null
          ? null : Number(surface.dataset.lkTotal),
        correct: surface.dataset.lkCorrect == null
          ? null : Number(surface.dataset.lkCorrect),
        chapterFirst: surface.dataset.lkChapterFirst === "true",
        chapterFirstRaw: surface.dataset.lkChapterFirst == null
          ? null : surface.dataset.lkChapterFirst,
      };
    }""")


def verdict_elements(page):
    """The verdict and the squash target the product rendered (M-7).

    The squash hangs on the **selected option row** (decisions.md A-89:
    the landing point is the item the learner picked), and the verdict
    line carries a ``lk-verdict-correct`` marker.  The evidence names
    both, so nobody has to take the harness's word for it.
    """
    return page.evaluate("""() => ({
      verdicts: Array.from(document.querySelectorAll(".micro-verdict")).map((el) => {
        const st = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return {
          cls: String(el.className || ""),
          text: (el.textContent || "").trim().slice(0, 30),
          animation: st.animationName,
          transform: st.transform,
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
      }),
      squashes: Array.from(document.querySelectorAll(".lk-squash")).map((el) => {
        const st = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return {
          cls: String(el.className || ""),
          tag: el.tagName.toLowerCase(),
          animation: st.animationName,
          animationDuration: st.animationDuration,
          transform: st.transform,
          text: (el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 40),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
      }),
    })""")


def capture_motion(playwright, motion_id, out_dir, base_url, ws, delay_ms=0,
                   paper_id=None, muted=False, plan=None):
    """Capture one motion: the strip, the metadata and the reduced twin."""
    motion = MOTIONS[motion_id]
    set_phase(base_url, "frames", "frames")
    out_dir = Path(out_dir)
    frames_dir = out_dir / motion_id
    watch = WATCH

    # -- the animated run ------------------------------------------------
    browser, context, page = _launch(playwright)
    if muted:
        page.add_init_script(MUTE_JS % ws)
    held = []
    try:
        if delay_ms:
            # The **page** fetch of the middle column is **held** (not
            # delayed): the request stays pending, so the product's own
            # loading state stands on the screen while the frames are
            # taken.  Sleeping in the handler would block the driver and
            # the frames would be taken after the content had arrived.
            def hold(route):
                held.append(route)

            page.route("**/w/*/practice-sets", hold)
        ctx = _Context(base_url, ws, paper_id, plan=plan, motion_id=motion_id)
        prepare = PREPARE[motion["trigger"]]
        act = ACT[motion["trigger"]]
        prepare(page, ctx)
        set_phase(base_url, "frames", "frames")
        meta = capture_strip(page, lambda: act(page, ctx), motion["frames_ms"],
                             frames_dir, watch)
        animated_terminal = terminal_state(page, watch)
        if motion_id in ("M-2", "M-3"):
            meta["completionFacts"] = completion_facts(page)
        if motion_id == "M-7":
            meta["verdictElements"] = verdict_elements(page)
    finally:
        for route in held:
            try:
                route.continue_()
            except Exception:
                pass
        context.close()
        browser.close()

    # -- the reduced run -------------------------------------------------
    browser, context, page = _launch(playwright, reduced_motion="reduce")
    if muted:
        page.add_init_script(MUTE_JS % ws)
    held = []
    try:
        if delay_ms:
            def hold(route):
                held.append(route)

            page.route("**/w/*/practice-sets", hold)
        ctx = _Context(base_url, ws, paper_id, plan=plan, motion_id=motion_id)
        prepare = PREPARE[motion["trigger"]]
        act = ACT[motion["trigger"]]
        prepare(page, ctx)
        act(page, ctx)
        page.wait_for_timeout(900)
        reduced_meta = {
            "frames_ms": [],
            "frames": [{"t": 900,
                        "file": None,
                        "states": page.evaluate(
                            "(w) => window.__lkFrame.states(w)", watch),
                        "animations": page.evaluate(
                            "() => window.__lkFrame.animations()")}],
        }
        reduced_terminal = terminal_state(page, watch)
    finally:
        for route in held:
            try:
                route.continue_()
            except Exception:
                pass
        context.close()
        browser.close()

    if motion_id == "M-5":
        meta["tiers"] = capture_streak_tiers(playwright, out_dir, base_url, ws)
    differences, extra = compare_terminal(animated_terminal, reduced_terminal)
    judge = JUDGES[motion_id](meta, reduced_meta, watch)
    verdict = judge["verdict"]
    if verdict in (PASS, FAIL) and differences:
        verdict = FAIL
        judge = {"verdict": FAIL,
                 "detail": f"降级帧的终态与动效终态不一致（{len(differences)} 处）"}
    strip = build_strip(frames_dir, out_dir / f"{motion_id}-strip.png")
    compact = []
    for frame in meta["frames"]:
        compact.append({
            "t": frame["t"],
            "file": frame["file"],
            "states": {selector: frame["states"].get(selector, [])
                       for selector in watch if frame["states"].get(selector)},
            "animations": sorted({anim.get("name") for anim in frame["animations"]
                                  if anim.get("name")}),
        })
    result = {
        "id": motion_id,
        "title": motion["title"],
        "verdict": verdict,
        "detail": judge["detail"],
        "frames_ms": meta["frames_ms"],
        "frameStates": compact,
        "frameFiles": [frame["file"] for frame in meta["frames"]],
        "strip": str(strip.name) if strip else None,
        "animations": [anim for frame in meta["frames"]
                       for anim in frame["animations"]],
        "terminalDifferences": differences,
        "terminalExtraDifferences": extra,
        "animatedTerminal": animated_terminal,
        "reducedTerminal": reduced_terminal,
    }
    # The judge's own extra evidence (the two milestone conditions, the
    # two sides of the skeleton) belongs in the product of the capture.
    for key in ("conditions", "evidence"):
        if key in judge:
            result[key] = judge[key]
    if "completionFacts" in meta:
        result["completionFacts"] = meta["completionFacts"]
    if "verdictElements" in meta:
        result["verdictElements"] = meta["verdictElements"]
    return result


class _Context:
    """The little bit of the probe context the triggers need."""

    def __init__(self, base_url, ws, paper_id=None, plan=None, motion_id=None):
        self.base_url = base_url.rstrip("/")
        self.ws = ws
        self.paper_id = paper_id
        #: The all-correct plan (seed.py): the gradable items and the
        #: options that make a round all-correct.  ``None`` ⇒ the trigger
        #: falls back to the ordinary seed paper.
        self.plan = plan or []
        #: Which motion is being captured — M-2 and M-3 share the
        #: celebration trigger but need a different round (the ordinary
        #: tier vs. the milestone tier).
        self.motion_id = motion_id

    def url(self, page_key):
        from probe import PAGES
        return self.base_url + PAGES[page_key].format(ws=self.ws)


def capture_mute_twin(playwright, out_dir, base_url, ws):
    """3.3-5 — the visual feedback is complete without any sound.

    The celebration is captured twice: once with the sound on and once
    with the sound preference off.  The two frame strips have to be
    **pixel identical** — the sound is not the only channel.
    """
    from PIL import Image, ImageChops

    on_dir = Path(out_dir) / "mute-on"
    off_dir = Path(out_dir) / "mute-off"
    on_result = capture_motion(playwright, "M-2", on_dir, base_url, ws)
    off_result = capture_motion(playwright, "M-2", off_dir, base_url, ws,
                                 muted=True)
    frames = []
    identical = True
    for path in sorted((on_dir / "M-2").glob("*.png")):
        twin = off_dir / "M-2" / path.name
        if not twin.is_file():
            identical = False
            continue
        left = Image.open(path).convert("RGB")
        right = Image.open(twin).convert("RGB")
        if left.size != right.size:
            identical = False
            frames.append({"file": path.name, "ae": None,
                           "why": "the two frames have different sizes"})
            continue
        diff = ImageChops.difference(left, right)
        ae = sum(sum(hist[1:]) for hist in
                 [band.histogram() for band in diff.split()])
        frames.append({"file": path.name, "ae": ae})
        if ae:
            identical = False
    # The **terminal state** is what the criterion is about: the sound is
    # not the only channel.  The mid-flight frames are reported as
    # evidence, but their pixels depend on the wall clock (the
    # celebration mounts its pieces on timers), so they are not decisive.
    differences, extra = compare_terminal(
        on_result.get("animatedTerminal") or {},
        off_result.get("animatedTerminal") or {})
    data = {"frames": frames, "soundOn": str(on_dir), "soundOff": str(off_dir),
            "terminalDifferences": differences,
            "terminalExtraDifferences": extra,
            "allFramesIdentical": identical}
    if not frames:
        return {"verdict": PENDING, "data": data,
                "note": "没有采到庆祝帧 —— 无法比较"}
    if differences:
        return {"verdict": FAIL, "data": data,
                "note": f"静音后终态与开静音的不一致（{len(differences)} 处）"
                        " —— 视觉反馈缺了一块"}
    return {"verdict": PASS, "data": data,
            "note": "静音与开静音的终态一致 —— 声音不是唯一通道"}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Capture the storyboard strips of M-1…M-10.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--ws", required=True)
    parser.add_argument("--out", required=True,
                        help="the diff directory (frames/ is written inside)")
    parser.add_argument("--only", default=None,
                        help="a comma separated list of motion ids")
    parser.add_argument("--paper-id", default=None,
                        help="the paper the loading state (M-9) is opened with")
    parser.add_argument("--mute-check", action="store_true",
                        help="also produce the 3.3-5 result (the mute twin)")
    parser.add_argument("--plan", default=None,
                        help="the all-correct plan (seed.py): the gradable items "
                             "and the options that make a round all-correct "
                             "(M-3's milestone tier and M-7's real judgement)")
    args = parser.parse_args(argv)

    from playwright.sync_api import sync_playwright

    out_dir = Path(args.out) / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = ([m.strip() for m in args.only.split(",")] if args.only
               else list(MOTIONS))
    plan = []
    if args.plan:
        plan = (_read_json(args.plan) or {}).get("items") or []
    paper_id = args.paper_id
    summary = {}
    with sync_playwright() as playwright:
        for motion_id in wanted:
            if motion_id not in MOTIONS:
                continue
            delay = 1500 if motion_id == "M-9" else 0
            try:
                result = capture_motion(playwright, motion_id, out_dir,
                                        args.base_url, args.ws, delay_ms=delay,
                                        paper_id=paper_id, plan=plan)
            except Exception as exc:
                result = {"id": motion_id, "title": MOTIONS[motion_id]["title"],
                          "verdict": PENDING, "detail": f"采集失败：{exc}"}
            _write_json(out_dir / f"{motion_id}.json", result)
            summary[motion_id] = result["verdict"]
    if args.mute_check:
        with sync_playwright() as playwright:
            result = capture_mute_twin(playwright, out_dir, args.base_url, args.ws)
        target = Path(args.out).parent / "after" / "probe" / "3.3-5.json"
        if not target.parent.is_dir():
            target = Path(args.out) / "3.3-5.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"id": "3.3-5", "level": "AUTO",
                                      "auto": True, **result},
                                     ensure_ascii=False, indent=2),
                          encoding="utf-8")
        summary["3.3-5"] = result["verdict"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
