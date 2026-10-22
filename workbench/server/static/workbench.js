/* workbench — DSH-styled client logic (vanilla JS, no build) */

(function () {
  "use strict";

  var layout = document.getElementById("layout");
  if (!layout) return;
  var WS = layout.dataset.workspace;

  var SESSION_KEY = "wb_session_" + WS;
  var KPS_KEY = "wb_kps_" + WS;
  var CURRENT_KEY = "wb_current_" + WS;
  var SIMILAR_KEY = "wb_similar_round_" + WS;
  var MODE_KEY = "wb_practice_mode_" + WS;
  var RATING_MODE_KEY = "wb_practice_rating_mode_" + WS;
  var FLASH_DIRECTION_KEY = "wb_flash_direction_" + WS;
  var SELECTION_KEY = "wb_agent_scope_" + WS;
  var AI_CONVERSATION_KEY = "wb_ai_conversation_" + WS;
  var AI_LIVE_ARTIFACT_KEY = "wb_ai_live_artifact_" + WS;
  var AI_RECENT_KEY = "wb_ai_recent_" + WS;
  var selectedGraphKpId = null;
  var practiceRuntime = null;
  var middlePageGeneration = 0;
  var currentProblem = function () { return null; };
  var session = function () { return []; };
  var visiblePracticeImages = function () { return []; };
  var draftAnswer = function () { return ""; };
  var draftNote = function () { return ""; };
  var practiceSelectionContext = function () { return {}; };
  var currentGraphContext = function () { return null; };

  function navigateMiddle(target) {
    if (window.WorkbenchNavigation) return window.WorkbenchNavigation.navigate(target);
    window.location = target;
  }

  function refreshMiddle() {
    if (window.WorkbenchNavigation) return window.WorkbenchNavigation.refresh();
    if (window.location && typeof window.location.reload === "function") window.location.reload();
  }

  function selectedKpIds() {
    var ids = load(SELECTION_KEY, []);
    return Array.from(new Set((Array.isArray(ids) ? ids : []).filter(Boolean)));
  }

  function saveSelectedKpIds(ids) {
    var unique = Array.from(new Set((ids || []).filter(Boolean)));
    store(SELECTION_KEY, unique);
    if (window.AgentUISurfaces) window.AgentUISurfaces.renderContext();
    return unique;
  }

  function bindChapterLens() {
    var lens = document.getElementById("chapter-lens");
    var toggle = document.getElementById("chapter-lens-switch");
    var select = document.getElementById("chapter-lens-select");
    if (!lens || !toggle || !select) return;
    function applyChapter(chapter) {
      post("/chapter", { chapter: chapter }).then(function () {
        refreshMiddle();
      }, function (error) {
        window.alert("章节切换失败：" + error.message);
        window.location.reload();
      });
    }
    toggle.addEventListener("change", function () {
      applyChapter(toggle.checked ? select.value : "");
    });
    select.addEventListener("change", function () {
      applyChapter(select.value);
    });

    /* ---- 15.4 自绘章节面板 ----------------------------------------------
       面板是**选章器**：开合 / Esc 关闭 / 点外部关闭 / 关闭后焦点归位到开关 /
       打开时焦点进面板 / `aria-expanded` 同步 / 键盘可达
       （↑↓ 移动、Enter·Space 选中、Home·End 首尾）。
       ⚠️ 选中一项走的是 `#chapter-lens-select` 已在用的那条 `applyChapter`
       路径 —— 同一个端点、同一个载荷键 `{chapter}`，**不新增请求**。
       ⚠️ 面板内**只有章节名**：不显示每章计数 / 统计 / 选择理由
       （`openspec/specs/workbench-ui/spec.md`「Chapter switch in the top bar」）。
       原生 `<select>` 保留作无 JS 兜底（不删、不改），它的 `value` 仍承载
       当前章 id —— 面板选章时同步写回，两条路径共用同一个载体。 */
    var panel = document.getElementById("chapter-lens-panel");
    if (!panel) return;
    var options = Array.from(panel.querySelectorAll(".chapter-lens-option"));
    toggle.setAttribute("aria-expanded", "false");

    function panelOpen() { return !panel.hidden; }

    function markChapter(chapter) {
      options.forEach(function (option) {
        if (chapter && option.getAttribute("data-chapter") === chapter) {
          option.setAttribute("aria-selected", "true");
        } else {
          option.removeAttribute("aria-selected");
        }
      });
    }

    function openPanel() {
      if (panelOpen()) return;
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      var target = null;
      for (var i = 0; i < options.length; i++) {
        if (options[i].getAttribute("aria-selected") === "true") { target = options[i]; break; }
      }
      if (!target) target = options[0];
      if (target) target.focus();
    }

    function closePanel(restoreFocus) {
      if (!panelOpen()) return;
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      if (restoreFocus) toggle.focus();
    }

    function chooseChapter(option) {
      var chapter = option.getAttribute("data-chapter");
      if (!chapter) return;
      markChapter(chapter);
      select.value = chapter;            /* 原生 select 继续承载当前章 id */
      closePanel(true);
      applyChapter(chapter);             /* 既有的章节切换路径，不新增请求 */
    }

    function moveFocus(key) {
      if (!options.length) return;
      var index = -1;
      for (var i = 0; i < options.length; i++) {
        if (options[i] === document.activeElement) { index = i; break; }
      }
      if (index < 0) index = 0;
      var next = index;
      if (key === "ArrowDown") next = Math.min(index + 1, options.length - 1);
      else if (key === "ArrowUp") next = Math.max(index - 1, 0);
      else if (key === "Home") next = 0;
      else if (key === "End") next = options.length - 1;
      options[next].focus();
    }

    /* 开关是面板的触发器：点它开面板。开关本身的透镜语义（勾上 = 恰好一章）
       一字未动 —— 勾选/取消仍走上面的 `change` → `applyChapter`。 */
    toggle.addEventListener("click", function () {
      markChapter(toggle.checked ? select.value : "");
      openPanel();
    });

    options.forEach(function (option) {
      option.addEventListener("click", function () { chooseChapter(option); });
    });

    panel.addEventListener("keydown", function (event) {
      var key = event.key;
      if (key === "Escape" || key === "Esc") {
        event.preventDefault();
        closePanel(true);
        return;
      }
      if (key === "ArrowDown" || key === "ArrowUp" || key === "Home" || key === "End") {
        event.preventDefault();
        moveFocus(key);
        return;
      }
      if (key === "Enter" || key === " " || key === "Spacebar") {
        event.preventDefault();
        var option = event.target && event.target.closest
          ? event.target.closest(".chapter-lens-option") : null;
        if (option) chooseChapter(option);
      }
    });

    /* 点面板外关闭。焦点归位只做在**焦点会丢**的情形：用户点的是别的控件，
       焦点就该留在那儿；点的是不可聚焦的地方（焦点会掉回 body），才还回开关。
       （`layout-spec.md` §2.3 只要求 `Esc` 关闭并把焦点还给 chip。） */
    document.addEventListener("click", function (event) {
      if (!panelOpen()) return;
      if (event.target && lens.contains(event.target)) return;
      closePanel(false);
      if (!document.activeElement || document.activeElement === document.body) toggle.focus();
    });

    /* 焦点走到透镜之外的另一个控件（Tab 走人）时，面板跟着收起；
       焦点掉到 body（点空白处）时不在这里收 —— 由上面的点外部关闭接手。 */
    lens.addEventListener("focusout", function (event) {
      if (!panelOpen()) return;
      var next = event.relatedTarget;
      if (!next || lens.contains(next)) return;
      closePanel(false);
    });
  }

  bindChapterLens();

  function mountSelectionPage() { bindKnowledgeSort(); }

  function bindKnowledgeSort() {
    var list = document.getElementById("knowledge-list");
    if (!list && document.querySelector) list = document.querySelector(".knowledge-list");
    var sort = document.getElementById("knowledge-sort");
    var direction = document.getElementById("knowledge-sort-direction");
    if (!list || !sort) return;
    var descending = false;
    function apply() {
      // 18.1: a row sits one level down inside its group card, so the rows are
      // collected across the groups. After sorting, every row goes back into
      // the group it belongs to — the group headers are never touched, and a
      // row never migrates to another group (its chapter is the row's own).
      var rows = Array.from(list.querySelectorAll(".knowledge-row"));
      var field = sort.value || "source";
      rows.sort(function (a, b) {
        var av = field === "source" ? Number(a.dataset.kpOrder || 0)
          : field === "problem_count" ? Number(a.dataset.kpProblemCount || 0)
            : String(a.dataset["kp" + field.charAt(0).toUpperCase() + field.slice(1)] || "").toLowerCase();
        var bv = field === "source" ? Number(b.dataset.kpOrder || 0)
          : field === "problem_count" ? Number(b.dataset.kpProblemCount || 0)
            : String(b.dataset["kp" + field.charAt(0).toUpperCase() + field.slice(1)] || "").toLowerCase();
        var result = typeof av === "number" && typeof bv === "number" ? av - bv : av.localeCompare(bv);
        if (!result) result = Number(a.dataset.kpOrder || 0) - Number(b.dataset.kpOrder || 0);
        return descending ? -result : result;
      });
      var homes = rows.map(function (row) { return row.parentNode; });
      rows.forEach(function (row, index) { homes[index].appendChild(row); });
      if (direction) direction.textContent = descending ? "↓" : "↑";
    }
    sort.addEventListener("change", apply);
    if (direction) direction.addEventListener("click", function () { descending = !descending; apply(); });
    apply();
  }

  /* ---------- helpers ---------- */

  function api(path, options) {
    return fetch("/api/w/" + WS + path, options).then(function (resp) {
      return resp.json().catch(function () { return {}; }).then(function (data) {
        if (!resp.ok) {
          var error = new Error(data.error || resp.status);
          error.status = resp.status;
          throw error;
        }
        return data;
      });
    });
  }

  function post(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  function patch(path, body) {
    return api(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  function del(path, body) {
    return api(path, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  function store(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
  }

  function load(key, fallback) {
    var raw = sessionStorage.getItem(key);
    if (!raw) return fallback;
    try {
      return JSON.parse(raw);
    } catch (error) {
      sessionStorage.removeItem(key);
      return fallback;
    }
  }

  // Preferences outlive the tab; every other client state is session-scoped.
  var SETTINGS_KEY = "wb_settings_" + WS;

  function loadSetting(key, fallback) {
    var raw = null;
    try { raw = window.localStorage.getItem(SETTINGS_KEY); } catch (error) { return fallback; }
    if (!raw) return fallback;
    try {
      var value = JSON.parse(raw)[key];
      return value === undefined ? fallback : value;
    } catch (error) {
      return fallback;
    }
  }

  function saveSetting(key, value) {
    var data = {};
    try { data = JSON.parse(window.localStorage.getItem(SETTINGS_KEY) || "{}") || {}; }
    catch (error) { data = {}; }
    data[key] = value;
    try { window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(data)); } catch (error) {}
  }

  function showRatingEnabled() {
    return loadSetting("showRating", true) !== false;
  }

  /* The sound preference is one field of the same record (`sound`, boolean,
     on by default — decisions.md A-38).  sfx.js reads the very same field, so
     the two never disagree; before the module is there the record itself is
     the answer. */
  function soundEnabled() {
    if (window.lkSfx && typeof window.lkSfx.isEnabled === "function") {
      return window.lkSfx.isEnabled();
    }
    return loadSetting("sound", true) !== false;
  }

  /* ---------- appearance preferences ----------
   * Theme, reading face, motion and sound are browser preferences of the
   * open workspace: they live in the same `wb_settings_<workspace>` record
   * as the two behaviour preferences and they never leave the browser
   * (design.md D-9).  An explicit pick wins over the system; without one
   * the system decides (A-11 for the theme, A-2 for the motion).
   */

  /* The system preferences are read through one live MediaQueryList each, so
     the helpers stay cheap and always see the current system value. */
  var darkQuery = null;
  var motionQuery = null;

  function prefersDarkScheme() {
    if (!window.matchMedia) return false;
    if (!darkQuery) darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
    return !!darkQuery.matches;
  }

  function prefersReducedMotion() {
    if (!window.matchMedia) return false;
    if (!motionQuery) motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    return !!motionQuery.matches;
  }

  function storedTheme() {
    var value = loadSetting("theme", null);
    return value === "night" || value === "paper" ? value : null;
  }

  function effectiveTheme() {
    var stored = storedTheme();
    if (stored) return stored;
    return prefersDarkScheme() ? "night" : "paper";
  }

  function applyTheme(theme) {
    var root = document.documentElement;
    if (!root) return;
    root.dataset.theme = theme === "night" ? "night" : "";
    root.style.colorScheme = theme === "night" ? "dark" : "light";
  }

  function storedReadingFace() {
    var value = loadSetting("readingFace", null);
    return value === "serif" || value === "sans" ? value : null;
  }

  function effectiveReadingFace() {
    return storedReadingFace() || "serif";
  }

  function applyReadingFace(face) {
    var root = document.documentElement;
    if (!root) return;
    root.dataset.face = face === "sans" ? "sans" : "serif";
    /* The reading face is a type family, so it is carried by the reading
       token; the attribute is the hook for the reading layer's own rules. */
    if (face === "sans") root.style.setProperty("--font-read", "var(--font-ui)");
    else root.style.removeProperty("--font-read");
  }

  function storedMotion() {
    var value = loadSetting("motion", null);
    return value === true || value === false ? value : null;
  }

  /* The motion tier in force: "full", "weak" (the system's reduced tier) or
     "off".  An explicit choice wins over the system setting (A-2). */
  function motionMode() {
    var stored = storedMotion();
    if (stored === false) return "off";
    if (stored === true) return "full";
    return prefersReducedMotion() ? "weak" : "full";
  }

  function applyMotion() {
    var root = document.documentElement;
    if (!root) return;
    var stored = storedMotion();
    /* Without a stored choice the stylesheet's own reduced-motion query
       decides; the attribute only carries an explicit choice. */
    if (stored === true) root.dataset.motion = "on";
    else if (stored === false) root.dataset.motion = "off";
    else root.removeAttribute("data-motion");
  }

  window.lkMotion = {
    mode: motionMode,
    isFull: function () { return motionMode() === "full"; },
    isWeak: function () { return motionMode() === "weak"; },
    isOff: function () { return motionMode() === "off"; },
    apply: applyMotion,
  };

  /* ---------- motion orchestration (tasks.md 8.4 / 8.7 / 8.8 · design.md D-7) ----------
     The stylesheet owns every keyframe; this side switches classes, writes the
     values of the counters that already exist and drives the timelines.  Three
     rules hold everywhere below:

       · an animated element's static style **is** its final style — the start
         state (opacity 0 / offset / scale) lives inside the @keyframes only
         (decisions.md A-2 derived rule / tasks.md 8.9);
       · no new request, no new learning fact, no change to the request
         sequence — the celebration starts only after the response that ends
         the round has arrived;
       · the motion tier is read from one place (`window.lkMotion.mode()`),
         never from a second `matchMedia` of its own.  The four combinations
         of A-2 hold: system reduce + unset ⇒ weak, system reduce + explicit
         on ⇒ full (the learner's explicit choice wins), system allows +
         unset ⇒ full, system allows + explicit off ⇒ straight cut.

     The shared ticker below is the **only** ticker in the product: the streak
     counter of group 17 calls this one instead of writing a second copy
     (tasks.md 17.1).  */

  var TICKER_DURATION_MS = 240;   /* motion-spec §2.1 item 8: 240 ms per digit */
  var TICKER_STAGGER_MS = 40;     /* per-digit stagger */
  var FLAME_STAGGER_MS = 80;      /* motion-spec §3.6: 80 ms between clusters */

  function tickerFrame() {
    return window.requestAnimationFrame
      ? function (fn) { return window.requestAnimationFrame(fn); }
      : function (fn) { return window.setTimeout(fn, 16); };
  }

  /* ① the shared ticker (tasks.md 8.4 ① / 17.1): vanilla rAF, writes
     `textContent` only — it creates no node and binds no listener. */
  function tickerSet(el, value, options) {
    if (!el) return false;
    var settings = options || {};
    var target = Number(value);
    if (!isFinite(target)) {
      el.textContent = String(value == null ? "" : value);
      return false;
    }
    var from = Number(settings.from);
    if (!isFinite(from)) from = 0;
    var duration = settings.duration == null ? TICKER_DURATION_MS : Number(settings.duration);
    var delay = settings.delay == null ? 0 : Number(settings.delay);
    /* A downgraded tier lands on the final value directly: the figure has to
       be readable, and a moving figure is not readable while it moves. */
    if (motionMode() !== "full" || !isFinite(duration) || duration <= 0) {
      el.textContent = String(target);
      return true;
    }
    var started = null;
    var request = tickerFrame();
    function step(now) {
      if (started === null) started = now;
      var elapsed = now - started - delay;
      if (elapsed < 0) { request(step); return; }
      var progress = Math.min(1, elapsed / duration);
      var eased = 1 - Math.pow(1 - progress, 3);   /* the "out" curve */
      el.textContent = String(Math.round(from + (target - from) * eased));
      if (progress < 1) { request(step); return; }
      el.textContent = String(target);
    }
    request(step);
    return true;
  }

  window.lkTicker = {
    set: tickerSet,
    isFull: function () { return motionMode() === "full"; },
  };

  /* ② the flame clusters (tasks.md 8.4 ② / 17.8): the class only — the
     ignition is a CSS keyframe, the clusters stagger by 80 ms. */
  function setFlames(root, litCount) {
    if (!root || !root.querySelectorAll) return 0;
    var flames = root.querySelectorAll(".lk-flame");
    var lit = Number(litCount) || 0;
    Array.prototype.forEach.call(flames, function (flame, index) {
      var on = index < lit;
      flame.classList.toggle("is-lit", on);
      /* The stagger is a delay, not a start state: the start state stays
         inside the keyframes. */
      flame.style.animationDelay = on ? (index * FLAME_STAGGER_MS) + "ms" : "";
    });
    return flames.length;
  }

  window.lkFlame = { set: setFlames };

  /* ③ the progress band (tasks.md 8.4 ③ / 17.4): the static style is already
     the final one (scaleX 1); `is-filled` replays the growth keyframe. */
  function fillProgressBand(root) {
    if (!root || !root.querySelectorAll) return 0;
    var bands = root.querySelectorAll(".lk-progress");
    Array.prototype.forEach.call(bands, function (band) {
      /* The markup carries `is-filled` so that the band's static style is its
         final style; the growth is replayed here, when the completion surface
         appears — without it the keyframe would have run while the section
         was still hidden. */
      band.classList.remove("is-filled");
      void band.offsetWidth;          /* let the removal land before the replay */
      band.classList.add("is-filled");
    });
    return bands.length;
  }

  window.lkProgress = { fill: fillProgressBand };

  /* ④ the streak state machine (decisions.md A-58): the **one** implementation
     of the streak feedback — count / three tiers / growth / break / reset /
     banner / flames.  `practice-flow.js` and `paper-practice.js` used to carry
     a copy each; that is the "one component in two shapes" disease (F-1) with
     two instances of it.

     This API owns the state machine only.  **The verdict source stays in the
     flow** — the quick-practice flow reads the micro-quiz verdict, the Paper
     flow reads the `verdict` of the submit payload — so this side only turns
     a verdict into feedback; the verdict semantics do not move.

     The thresholds are the ones both flows already used, item by item:
     TIER_HOT 30 · FLAME_CAP 10 · STAGGER 80 ms · STEP 40 ms ·
     BANNER_EVERY 5 · BREAK_OVER 4.  */
  var STREAK_TIER_HOT = 30;         /* the third tier starts here */
  var STREAK_FLAME_CAP = 10;        /* at most ten flame clusters */
  var STREAK_FLAME_STAGGER_MS = 80; /* per-cluster ignition delay */
  var STREAK_FLAME_STEP_MS = 40;    /* per-cluster extinguish delay */
  var STREAK_BANNER_EVERY = 5;      /* the banner fires on every multiple of five */
  var STREAK_BREAK_OVER = 4;        /* a break above four must be shown plainly */

  function streakTierOf(count) {
    if (count <= 0) return 0;
    return count >= STREAK_TIER_HOT ? 2 : 1;
  }

  function streakCreate(options) {
    var settings = options || {};
    var host = settings.root;
    var count = 0;

    /* The card is replaced as a whole on every render, so the parts are
       looked up by class at the moment they are needed — never cached. */
    function part(selector) {
      var element = typeof host === "function" ? host() : host;
      if (!element || typeof element.querySelector !== "function") return null;
      return element.querySelector(selector);
    }

    function setNumber(value, from) {
      var ticker = part(".lk-ticker");
      if (!ticker) return;
      if (window.lkTicker && typeof window.lkTicker.set === "function") {
        try {
          window.lkTicker.set(ticker, value, { from: from == null ? value : from });
          return;
        } catch (error) {
          /* The shared ticker is absent — the figure still has to be right. */
        }
      }
      ticker.textContent = String(value);
    }

    function showBanner(bannerCount) {
      var banner = part(".lk-combo-banner");
      if (!banner) return;
      var number = banner.querySelector ? banner.querySelector(".lk-combo-banner__count") : null;
      if (number) number.textContent = String(bannerCount);
      /* The tier difference is carried by this one semantic class only. */
      banner.classList.toggle("is-large", bannerCount >= STREAK_BANNER_EVERY * 2);
      banner.classList.add("is-on");
    }

    function html() {
      var slots = Math.min(count, STREAK_FLAME_CAP);
      var flames = "";
      for (var i = 0; i < slots; i += 1) {
        flames += "<span class='lk-flame is-lit' style='animation-delay:"
          + (i * STREAK_FLAME_STAGGER_MS) + "ms'>"
          + "<span class='lk-flame-off'></span><span class='lk-flame-on'></span></span>";
      }
      var tier = streakTierOf(count);
      return "<span class='lk-streak"
        + (tier === 2 ? " is-hot" : tier === 1 ? " is-warm" : "")
        + "' data-lk-streak-tier='" + tier + "'>"
        + "<span class='lk-flames' aria-hidden='true'>" + flames + "</span>"
        + "<span class='lk-ticker' data-value='" + count + "' aria-label='连对 "
        + count + "'>" + count + "</span></span>"
        /* one banner: 5 in a row / 10 in a row … share the same DOM and the same
           animation, the figure is the parameter */
        + "<span class='lk-combo-banner' aria-hidden='true'>"
        + "<span class='lk-combo-banner__count'>" + count + "</span></span>";
    }

    function growStreak(before) {
      setNumber(count, before);
      if (count > 0 && count % STREAK_BANNER_EVERY === 0) showBanner(count);
    }

    function breakStreak(before, loud) {
      var flames = part(".lk-flames");
      var lit = count;
      /* cluster by cluster: from the newest one, 40 ms apart (the extinguish is
         a pure opacity transition) */
      for (var remaining = lit - 1; remaining >= 0; remaining -= 1) {
        (function (left) {
          setTimeout(function () {
            if (flames && window.lkFlame && typeof window.lkFlame.set === "function") {
              window.lkFlame.set(flames, left);
            }
          }, (lit - 1 - left) * STREAK_FLAME_STEP_MS);
        })(remaining);
      }
      count = 0;
      setNumber(0, before);
      if (!loud) return;
      /* a break above four must be shown plainly: one horizontal shake of
         ≤4 px / 160 ms, never a screen-wide shake */
      var counter = part(".lk-streak");
      if (!counter) return;
      counter.classList.add("lk-error-nudge");
      counter.style.animation = "lk-error-nudge 160ms var(--ease-standard) both";
    }

    /* the verdict fork: right → count + 1; wrong above four → shown plainly and
       zeroed; any other wrong answer → zeroed.  The verdict semantics do not
       move — the flow decides what a verdict is, this side only reacts to it. */
    function judge(verdict) {
      if (verdict !== true && verdict !== false) return null;
      var before = count;
      var breaking = false;
      if (verdict === true) {
        count += 1;
      } else if (count > STREAK_BREAK_OVER) {
        /* on a break the count stays for a moment, so the flames can go out
           one by one before it returns to zero */
        breaking = true;
      } else {
        count = 0;
      }
      return { before: before, breaking: breaking, correct: verdict === true };
    }

    function apply(landed) {
      if (!landed) return;
      if (landed.breaking) breakStreak(landed.before, true);
      else if (landed.correct) growStreak(landed.before);
      else setNumber(0, landed.before);
    }

    return {
      count: function () { return count; },
      reset: function () { count = 0; },
      html: html,
      judge: judge,
      apply: apply,
    };
  }

  window.lkStreak = { create: streakCreate };

  /* ---------- the lamp transition (tasks.md 8.7 / 12.5 · motion-spec §4) ----------
     Four stages: lean out (140 ms) → light up (140–220 ms) → the ripple
     spreads (140–590 ms) → the skin is swapped (590 ms) → retract and clear
     (590–700 ms).

     The ripple carries the **target** theme's ground colour and it is written
     at the *start* of the transition — one frame later and the old colour
     flashes for a frame (tasks.md 12.5).  The ripple is a ground layer: it
     reads `--surface-base` (the page ground), never a card token that changes
     with the theme (decisions.md A-1).  All three layers are decoration:
     `pointer-events: none`, and the ripple stays below the content.  */

  var LAMP_SWAP_MS = 590;
  var LAMP_CLEAN_MS = 700;
  var lampAsset = null;
  var lampRun = null;

  function lampAssetText() {
    if (!lampAsset) {
      lampAsset = fetch("/static/assets/motion/lamp.svg")
        .then(function (response) { return response.ok ? response.text() : ""; })
        .catch(function () { return ""; });
    }
    return lampAsset;
  }

  /* The ground colour of a theme: `--surface-base` is one name with two value
     sets, so the target theme is set for a moment and read back — inside the
     same task, so nothing flashes (motion-spec §4.2). */
  function themeBase(theme) {
    var root = document.documentElement;
    if (!root || !window.getComputedStyle) return "";
    var previous = root.getAttribute("data-theme");
    root.setAttribute("data-theme", theme === "night" ? "night" : "");
    var value = window.getComputedStyle(root).getPropertyValue("--surface-base").trim();
    if (previous === null) root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", previous);
    return value;
  }

  function runLampTransition(nextTheme) {
    /* A second switch while the first is still running replaces it: the
       pending swap of the older run must not land after the newer one. */
    if (lampRun) lampRun.cancel();
    lampRun = null;
    /* The downgraded tiers never build the three layers: the theme is simply
       swapped (motion-spec §4.6). */
    if (motionMode() !== "full") {
      applyTheme(nextTheme);
      return;
    }
    var ripple = document.createElement("div");
    ripple.className = "lk-ripple";
    var glow = document.createElement("div");
    glow.className = "lk-ripple-glow";
    var lamp = document.createElement("div");
    lamp.className = "lk-lamp";
    /* The target ground colour goes in at the start of the transition.  The
       stylesheet reads `--ripple-base`; that name is written on the layer that
       reads it — the layer is removed at the end of the transition, so the
       value never outlives it and cannot go stale on a later theme change. */
    var base = themeBase(nextTheme);
    ripple.style.setProperty("--ripple-base", base);
    document.body.appendChild(ripple);
    document.body.appendChild(glow);
    document.body.appendChild(lamp);
    lampAssetText().then(function (svg) {
      if (svg && lamp.parentNode) lamp.innerHTML = svg;
    });
    /* ① lean out, ② light up, ③ ripple — the stylesheet carries the delays,
       so the classes go on at once. */
    lamp.classList.add("is-out", "is-lit");
    ripple.classList.add("is-on", "is-clear");
    glow.classList.add("is-on", "is-clear");
    var swapTimer = null;
    var cleanTimer = null;
    function removeLayers() {
      [ripple, glow, lamp].forEach(function (layer) {
        if (layer.parentNode) layer.parentNode.removeChild(layer);
      });
    }
    var run = {
      cancel: function () {
        if (swapTimer) window.clearTimeout(swapTimer);
        if (cleanTimer) window.clearTimeout(cleanTimer);
        removeLayers();
      },
    };
    lampRun = run;
    /* ④ skin swap: the ripple has covered the ground colour by now. */
    swapTimer = window.setTimeout(function () {
      applyTheme(nextTheme);
    }, LAMP_SWAP_MS);
    /* ⑤⑥ retract and clear — the terminal state is clean. */
    cleanTimer = window.setTimeout(function () {
      removeLayers();
      if (lampRun === run) lampRun = null;
    }, LAMP_CLEAN_MS);
  }

  window.lkTheme = {
    effective: effectiveTheme,
    apply: applyTheme,
    transition: runLampTransition,
  };

  /* ---------- the two-tier celebration (tasks.md 8.8 / 17.4 / 17.6) ----------
     A-29: the milestone tier has exactly **two** conditions — the round
     finished fully correct, or it completes a chapter for the first time.
     No proxy measure (such as "better than last time") may stand in for
     them: its comparison scope does not exist in the contract.  The ordinary
     tier never mounts the burst or the paper flutter.  */

  var celebrationArmedAt = 0;
  var celebrationFacts = null;

  /* The two-condition judgment — the single place that decides the tier. */
  function isMilestoneRound(facts) {
    if (!facts) return false;
    if (facts.chapterFirstCompletion === true) return true;
    var total = Number(facts.total);
    var correct = Number(facts.correct);
    if (!isFinite(total) || !isFinite(correct)) return false;
    return total > 0 && correct >= total;
  }

  /* The facts of the round are read from the completion surface itself: the
     server writes `data-lk-total` / `data-lk-correct` / `data-lk-chapter-first`
     on it.  A module that holds the round may hand the facts over instead
     (`window.lkCelebrate.setFacts`).  Without facts the round stays in the
     ordinary tier — the burst and the paper flutter are milestone only. */
  function completionFacts(surface) {
    var facts = celebrationFacts;
    if (surface && surface.dataset) {
      var data = surface.dataset;
      if (data.lkTotal != null || data.lkCorrect != null) {
        facts = {
          total: Number(data.lkTotal) || 0,
          correct: Number(data.lkCorrect) || 0,
          chapterFirstCompletion: data.lkChapterFirst === "true",
        };
      } else if (data.lkChapterFirst === "true") {
        facts = { total: 0, correct: 0, chapterFirstCompletion: true };
      }
    }
    return facts || null;
  }

  /* The figures of the completion surface roll up to their values: a bare
     number, or a slot that names its value in `data-lk-value` /
     `data-lk-count`.  A slot that carries anything else (a unit, a label) is
     left alone — its text is never rewritten. */
  function rollCompletionFigures(surface) {
    if (!surface || !surface.querySelectorAll) return 0;
    var figures = surface.querySelectorAll("[data-lk-value], [data-lk-count], .lk-ticker");
    var rolled = 0;
    Array.prototype.forEach.call(figures, function (figure, index) {
      var declared = figure.getAttribute("data-lk-value");
      if (declared == null) declared = figure.getAttribute("data-lk-count");
      var text = String(figure.textContent == null ? "" : figure.textContent).trim();
      var target;
      if (declared != null) target = Number(declared);
      else if (/^\d+$/.test(text)) target = Number(text);
      else return;
      if (!isFinite(target)) return;
      rolled += 1;
      tickerSet(figure, target, { from: 0, delay: index * TICKER_STAGGER_MS });
    });
    return rolled;
  }

  /* The milestone anchor: the place the burst and the paper flutter hang in.
     It is a decoration layer — it never sits over the primary action. */
  function celebrationAnchor(surface) {
    if (!surface || !surface.querySelector) return null;
    return surface.querySelector("[data-lk-celebrate-anchor]")
      || surface.querySelector(".lk-celebrate-anchor")
      || surface.querySelector("#paper-milestone-anchor")
      || surface.querySelector(".lk-milestone-anchor")
      || surface.querySelector("#paper-completion-stats")
      || surface;
  }

  /* The burst and the paper flutter are created here and nowhere else: the
     ordinary tier never has them in the document at all (tasks.md 8.8).

     The paper flutter is drawn the way the group-9 illustrations are drawn
     (assets/empty/*.svg): a pale wash plus an ink line, round caps and
     joins, stroke widths 1.5 / 2, the same asset tokens.  Three small shapes
     — a thin strip, a round chip and a triangle — take turns.  No bitmap, no
     sprite, no image sequence; the shapes are inline SVG strings, so the
     gradient rule of the authority table (gradients only inside a drawing)
     holds by construction: there is no gradient at all here. */
  var CONFETTI_SPOTS = [
    [8, 12], [18, 26], [28, 8], [38, 30], [47, 14], [56, 26],
    [65, 8], [74, 22], [83, 12], [91, 28], [14, 40], [60, 38],
  ];

  var CONFETTI_STRIP = "M 10.4 4.6 C 11.7 4 13.3 4 14.6 4.7 "
    + "C 14.2 10 13.6 15 13.2 19.5 C 12.1 19.9 11 19.9 10 19.4 "
    + "C 10.5 14.8 10.9 9.8 10.4 4.6 Z";
  var CONFETTI_CHIP = "M 19.2 12 C 19.2 15.7 16 18.6 12 18.6 "
    + "C 8 18.6 4.8 15.7 4.8 12 C 4.8 8.3 8 5.4 12 5.4 "
    + "C 16 5.4 19.2 8.3 19.2 12 Z";
  var CONFETTI_TRIANGLE = "M 12.4 4.2 C 14 7.6 16.4 11.4 18.4 15.2 "
    + "C 18.8 16 18.6 16.8 17.8 17 L 6.6 17.4 C 5.8 17.4 5.4 16.6 5.9 15.8 "
    + "C 8 12 10.2 8 12.4 4.2 Z";

  function confettiShape(kind) {
    var wash = kind === 1
      ? "color-mix(in oklab, var(--asset-ground-blue, #2b62e8) 16%, var(--asset-paper, #fffdf7))"
      : "color-mix(in oklab, var(--asset-ground-yellow, #f5c518) 16%, var(--asset-paper, #fffdf7))";
    var path = kind === 0 ? CONFETTI_STRIP : kind === 1 ? CONFETTI_CHIP : CONFETTI_TRIANGLE;
    var width = kind === 0 ? "1.5" : "2";
    return "<svg viewBox='0 0 24 24' class='asset asset-confetti' "
      + "xmlns='http://www.w3.org/2000/svg' aria-hidden='true' focusable='false'>"
      + "<g stroke-linecap='round' stroke-linejoin='round'>"
      + "<g class='asset-confetti__wash'><path d='" + path + "' fill='" + wash + "'/></g>"
      + "<g class='asset-confetti__line' fill='none' stroke='var(--asset-ink, #2a2620)'>"
      + "<path d='" + path + "' stroke-width='" + width + "'/></g>"
      + "</g></svg>";
  }

  function mountMilestoneBurst(surface) {
    var anchor = celebrationAnchor(surface);
    if (!anchor) return null;
    /* The burst is positioned absolutely, so the anchor needs a positioning
       context.  This is layout, not an animation start state. */
    if (window.getComputedStyle && window.getComputedStyle(anchor).position === "static") {
      anchor.style.position = "relative";
    }
    var burst = document.createElement("div");
    /* The geometric burst is a **ring** that spreads and fades: the
       stylesheet draws it as a 2px outline with a fully round radius
       (`.lk-celebrate-burst`), and the keyframe scales it out while the
       opacity goes up and down again — a ring, never a filled block
       (tasks.md 17.7). */
    burst.className = "lk-celebrate-burst";
    /* A-38: the burst carries the cue hook.  A-53: the hook marks the burst
       only — the milestone sound itself is driven by the tier decision (see
       `celebrateCompletion`), so it lands in the downgraded tier too, where
       no burst is drawn at all. */
    burst.setAttribute("data-lk-cue", "milestone");
    anchor.appendChild(burst);
    return { burst: burst, pieces: [], anchor: anchor };
  }

  function mountConfetti(mounted) {
    if (!mounted || !mounted.anchor) return;
    CONFETTI_SPOTS.forEach(function (spot, index) {
      var piece = document.createElement("div");
      piece.className = "lk-confetti";
      /* The stylesheet's chip is a plain colour block; the shape and its size
         are the drawing's, so the block is emptied here — the placement and
         the fall animation still come from the stylesheet.  These are static
         declarations, not animation start states. */
      piece.style.background = "none";
      piece.style.width = "16px";
      piece.style.height = "16px";
      piece.style.left = spot[0] + "%";
      piece.style.top = spot[1] + "%";
      piece.innerHTML = confettiShape(index % 3);
      mounted.anchor.appendChild(piece);
      mounted.pieces.push(piece);
    });
  }

  function clearMilestone(mounted) {
    if (!mounted) return;
    if (mounted.burst && mounted.burst.parentNode) mounted.burst.parentNode.removeChild(mounted.burst);
    mounted.pieces.forEach(function (piece) {
      if (piece.parentNode) piece.parentNode.removeChild(piece);
    });
    mounted.pieces = [];
  }

  /* The celebration itself: the ordinary tier rolls the figures and fills the
     progress band; the milestone tier adds the burst (400 ms — the same beat
     as the milestone cue) and the paper flutter (800 ms). */
  function celebrateCompletion(surface) {
    var target = surface || document.getElementById("paper-completion");
    if (!target) return;
    var milestone = isMilestoneRound(completionFacts(target));
    window.setTimeout(function () {
      rollCompletionFigures(target);
      fillProgressBand(target);
    }, 150);
    if (!milestone) return;
    /* A-53: the milestone cue rides on the **tier decision**, not on the
       burst element.  The burst is decoration, and a downgraded tier draws
       no burst at all — the sound is a channel of its own, so the downgraded
       tier still sounds (the ordinary tier never reaches this line). */
    window.setTimeout(function () {
      if (window.lkSfx && typeof window.lkSfx.playCue === "function") {
        window.lkSfx.playCue("milestone");
      }
    }, 400);
    /* A downgraded tier does not draw the burst or the paper flutter at all
       (motion-spec §7.2 row 14). */
    if (motionMode() !== "full") return;
    var mounted = null;
    /* The burst goes up at 400 ms — the same beat as the milestone cue
       (tasks.md 10.6). */
    window.setTimeout(function () {
      mounted = mountMilestoneBurst(target);
    }, 400);
    /* The paper flutter starts at 700 ms, so that the 800 ms frame of the
       storyboard catches it at its peak; it falls for `--dur-ceremony`
       (700 ms) and is cleared afterwards, which leaves a clean end state. */
    window.setTimeout(function () {
      mountConfetti(mounted);
    }, 700);
    window.setTimeout(function () {
      clearMilestone(mounted);
    }, 1600);
  }

  window.lkCelebrate = {
    isMilestone: isMilestoneRound,
    setFacts: function (facts) { celebrationFacts = facts || null; },
    play: celebrateCompletion,
  };

  function renderMath(root) {
    var spans = (root || document).querySelectorAll(".math");
    if (!spans.length || !window.katex) return;
    spans.forEach(function (span) {
      try {
        // A `$$` block is emitted with the `display` class, so read the layout
        // mode off it: without this KaTeX lays `$$` out inline and rejects
        // `\tag`, which only exists in display equations.
        katex.render(span.textContent, span, {
          displayMode: span.classList.contains("display"),
          throwOnError: false,
        });
      } catch (e) { /* keep raw text */ }
    });
  }

  function escapeHtml(text) {
    // `'` maps to `&#x27;` to match the server's `html.escape`, so both
    // renderers emit byte-identical HTML for the same input.
    return String(text == null ? "" : text).replace(/[&<>\"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#x27;" }[ch];
    });
  }

  /* Placeholder delimiters are private-use code points, which course text
     can never contain, so body text cannot forge a token and break rendering. */
  var DISPLAY_MARKS = ["\ue000", "\ue001", "\ue002", "\ue003", "\ue004"];
  var INLINE_MARKS = ["\ue010", "\ue011", "\ue012", "\ue013", "\ue014"];
  var DISPLAY_BLOCK_RE = /\$\$([\s\S]*?)\$\$/g;
  var FENCE_LINE_RE = /^\s*```\s*([\w-]*)\s*$/;
  var MATH_RE = /\$\$([\s\S]+?)\$\$|\$([^$\n]+)\$/g;
  // Emphasis must not fire on a delimiter LaTeX escaped (\\_, \*, \\_\\_),
  // so every delimiter carries a lookaround that also rejects a preceding
  // backslash. The triple-star form is matched first, otherwise the double-star
  // rule would split it and nest the tags across each other
  var STRONG_EM_RE = /(?<![\\*])\*\*\*(?!\*)(.+?)(?<![\\*])\*\*\*(?!\*)/g;
  var STRONG_STAR_RE = /(?<![\\*])\*\*(?!\*)(.+?)(?<![\\*])\*\*(?!\*)/g;
  var STRONG_UNDERSCORE_RE = /(?<![A-Za-z0-9_\\])__(.+?)__(?![A-Za-z0-9_\\])/g;
  var EM_STAR_RE = /(?<![\\*])\*(?!\*)([^*\n]+?)\*(?![\\*])/g;
  var EM_UNDERSCORE_RE = /(?<![A-Za-z0-9_\\])_([^_\n]+)_(?![A-Za-z0-9_\\])/g;
  var CODE_RE = /`([^`\n]+)`/g;

  function pickMark(text, marks) {
    for (var i = 0; i < marks.length; i += 1) {
      if (text.indexOf(marks[i]) === -1) return marks[i];
    }
    return marks[0];
  }

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function restoreTokens(text, mark, tokens) {
    if (!tokens.length) return text;
    var pattern = new RegExp(escapeRegExp(mark) + "(\\d+)" + escapeRegExp(mark), "g");
    return text.replace(pattern, function (whole, index) {
      var at = Number(index);
      return at < tokens.length ? tokens[at] : whole;
    });
  }

  function displaySpan(expr) {
    return "<span class='math display'>" + escapeHtml(expr) + "</span>";
  }

  function mathSpan(display, expr) {
    // The delimiters own the surrounding newlines; KaTeX wants the body.
    if (display != null) return displaySpan(expr.replace(/^\n+|\n+$/g, ""));
    return "<span class='math'>" + escapeHtml(expr) + "</span>";
  }

  function stashDisplayBlocks(text) {
    /* Pull whole display-math blocks out before the line loop runs: richInline
       is called one line at a time, so a $$…$$ block whose delimiters own their
       own lines could never match there. Each block collapses to a one-line
       placeholder richInline cannot touch, restored after the loop. */
    var mark = pickMark(text, DISPLAY_MARKS);
    var spans = [];
    function replace(chunk) {
      var blocks = new RegExp([
        CODE_RE.source, "!\\[[^\\]]*\\]\\([^)]+\\)",
        "\\[\\[([^\\]|]+)(?:\\|([^\\]]+))?\\]\\]",
        "\\[[^\\]]+\\]\\(https?://[^\\s)]+\\)", DISPLAY_BLOCK_RE.source,
      ].join("|"), "g");
      return chunk.replace(blocks, function (whole) {
        if (whole.slice(0, 2) !== "$$") return whole;
        spans.push(displaySpan(whole.slice(2, -2).replace(/^\n+|\n+$/g, "")));
        return mark + (spans.length - 1) + mark;
      });
    }
    var out = [], buffer = [], inCode = false;
    String(text).split("\n").forEach(function (line) {
      if (FENCE_LINE_RE.test(line)) {
        if (buffer.length) { out.push(replace(buffer.join("\n"))); buffer = []; }
        out.push(line);
        inCode = !inCode;
      } else if (inCode) {
        out.push(line);
      } else {
        buffer.push(line);
      }
    });
    if (buffer.length) out.push(replace(buffer.join("\n")));
    return { text: out.join("\n"), spans: spans, mark: mark };
  }

  function richInline(text) {
    /* Escape each fragment exactly once, in this order (order matters).
       Math and <sup>/<sub> are stashed BEFORE the remaining text is escaped,
       so no Markdown rule below can ever see LaTeX source, and each stashed
       fragment is escaped exactly once. */
    var tokens = [];
    var mark = pickMark(text == null ? "" : String(text), INLINE_MARKS);
    function token(html) {
      html = restoreTokens(html, mark, tokens);
      tokens.push(html);
      return mark + (tokens.length - 1) + mark;
    }
    var source = text == null ? "" : String(text);
    var protectedInline = new RegExp([
      CODE_RE.source, MATH_RE.source, "!\\[[^\\]]*\\]\\([^)]+\\)",
      "\\[\\[([^\\]|]+)(?:\\|([^\\]]+))?\\]\\]", "\\[[^\\]]+\\]\\(https?://[^\\s)]+\\)",
    ].join("|"), "g");
    source = source.replace(protectedInline, function (whole) {
      if (whole.charAt(0) === "`") return token("<code>" + escapeHtml(whole.slice(1, -1)) + "</code>");
      if (whole.charAt(0) === "$") {
        var math = whole.match(new RegExp(MATH_RE.source));
        return token(mathSpan(math[1], math[1] != null ? math[1] : math[2]));
      }
      if (whole.indexOf("![") === 0) {
        var image = whole.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
        var src = image[2], resolved;
        if (/^\/(?:api\/w\/|static\/)/.test(src)) resolved = src;
        else if (/^[\w./-]+$/.test(src)) {
          resolved = "/api/w/" + encodeURIComponent(WS) + "/figures/" + src.replace(/^\//, "");
        } else return token(escapeHtml(image[1]));
        return token("<img alt='" + escapeHtml(image[1]) + "' src='" + escapeHtml(resolved) + "'>");
      }
      if (whole.indexOf("[[") === 0) {
        var wiki = whole.match(/^\[\[([^\]|]+)(?:\|([^\]]+))?\]\]$/);
        var id = wiki[1].trim(), label = richInline(wiki[2] || id);
        if (!/^[\w-]+$/.test(id)) return token(label);
        return token("<a href='/w/" + encodeURIComponent(WS) + "/kp/" + encodeURIComponent(id) + "'>" + label + "</a>");
      }
      var link = whole.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
      return token("<a href='" + escapeHtml(link[2]) + "' target='_blank' rel='noopener noreferrer'>"
        + richInline(link[1]) + "</a>");
    });
    source = source.replace(/<(sup|sub)>([^<>]+)<\/\1>/g, function (_, tag, content) {
      return token("<" + tag + ">" + escapeHtml(content) + "</" + tag + ">");
    });
    var value = escapeHtml(source);
    value = value.replace(STRONG_EM_RE, "<strong><em>$1</em></strong>");
    value = value.replace(STRONG_STAR_RE, "<strong>$1</strong>");
    value = value.replace(STRONG_UNDERSCORE_RE, "<strong>$1</strong>");
    value = value.replace(EM_STAR_RE, "<em>$1</em>");
    value = value.replace(EM_UNDERSCORE_RE, "<em>$1</em>");
    // A LaTeX-escaped underscore outside math is a fill-in blank, so render the
    // underscore the author meant. Safe here: every math fragment is already
    // stashed out of this text.
    value = value.replace(/\\_/g, "_");
    return restoreTokens(value, mark, tokens);
  }

  var TABLE_DELIMITER_CELL = /^:?-{1,}:?$/;
  var THEMATIC_BREAK = /^\s*(?:\*(?:\s*\*){2,}|-(?:\s*-){2,}|_(?:\s*_){2,})\s*$/;

  function tableCells(line) {
    var value = String(line).trim();
    if (value.charAt(0) === "|") value = value.slice(1);
    if (value.charAt(value.length - 1) === "|") value = value.slice(0, -1);
    return value.split("|").map(function (cell) { return cell.trim(); });
  }

  function tableStart(lines, position) {
    if (position + 1 >= lines.length || lines[position].indexOf("|") === -1) return false;
    var header = tableCells(lines[position]);
    if (header.length < 2) return false;
    var delimiter = tableCells(lines[position + 1]);
    if (delimiter.length !== header.length) return false;
    return delimiter.every(function (cell) { return TABLE_DELIMITER_CELL.test(cell); });
  }

  function tableHtml(lines, position) {
    var header = tableCells(lines[position]);
    var rows = [];
    var cursor = position + 2;
    while (cursor < lines.length && lines[cursor].trim()
      && lines[cursor].indexOf("|") !== -1) {
      rows.push(tableCells(lines[cursor]));
      cursor += 1;
    }
    var head = header.map(function (cell) {
      return "<th>" + richInline(cell) + "</th>";
    }).join("");
    var body = rows.map(function (row) {
      return "<tr>" + row.map(function (cell) {
        return "<td>" + richInline(cell) + "</td>";
      }).join("") + "</tr>";
    }).join("");
    return {
      html: "<div class='rich-table-wrap'><table><thead><tr>" + head
        + "</tr></thead><tbody>" + body + "</tbody></table></div>",
      next: cursor - 1,
    };
  }

  function richText(text) {
    var display = stashDisplayBlocks(String(text == null ? "" : text).replace(/\r\n?/g, "\n"));
    var lines = display.text.split("\n");
    var out = [], paragraph = [], listType = null, inCode = false, codeLang = "", codeLines = [];
    var skipUntil = -1;
    function closeList() {
      if (listType) out.push("</" + listType + ">");
      listType = null;
    }
    function flushParagraph() {
      if (!paragraph.length) return;
      out.push("<p>" + paragraph.map(richInline).join("<br>") + "</p>");
      paragraph = [];
    }
    function flushCode() {
      var cls = codeLang ? " class='language-" + codeLang.replace(/[^\w-]/g, "") + "'" : "";
      out.push("<pre><code" + cls + ">" + escapeHtml(codeLines.join("\n")) + "</code></pre>");
      codeLines = []; codeLang = "";
    }
    lines.forEach(function (line, position) {
      if (position <= skipUntil) return;
      var fence = line.match(/^\s*```\s*([\w-]*)\s*$/);
      if (fence) {
        flushParagraph(); closeList();
        if (inCode) flushCode();
        inCode = !inCode; codeLang = inCode ? fence[1] : "";
        return;
      }
      if (inCode) { codeLines.push(line); return; }
      if (tableStart(lines, position)) {
        flushParagraph(); closeList();
        var table = tableHtml(lines, position);
        out.push(table.html);
        skipUntil = table.next;
        return;
      }
      if (THEMATIC_BREAK.test(line)) {
        flushParagraph(); closeList();
        out.push("<hr>");
        return;
      }
      var heading = line.match(/^\s*(#{1,3})\s+(.+?)\s*#*\s*$/);
      if (heading) {
        flushParagraph(); closeList();
        // Body headings start at h2: h1 belongs to the page title, so the
        // body never competes with the shell (design.md D-6). The server
        // uses the same rule, and tests/test_markdown_render_parity.py holds
        // the two renderers to it character for character.
        var level = heading[1].length + 1;
        out.push("<h" + level + ">" + richInline(heading[2]) + "</h" + level + ">");
        return;
      }
      var unordered = line.match(/^\s*[-*+]\s+(.+)$/);
      var ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (unordered || ordered) {
        flushParagraph();
        var wanted = ordered ? "ol" : "ul";
        if (listType && listType !== wanted) closeList();
        if (!listType) { listType = wanted; out.push("<" + listType + ">"); }
        out.push("<li>" + richInline((ordered || unordered)[1]) + "</li>");
        return;
      }
      if (/^\s*>\s?/.test(line)) {
        flushParagraph(); closeList();
        out.push("<blockquote>" + richInline(line.replace(/^\s*>\s?/, "")) + "</blockquote>");
        return;
      }
      if (!line.trim()) { flushParagraph(); closeList(); return; }
      closeList(); paragraph.push(line);
    });
    if (inCode) flushCode();
    flushParagraph(); closeList();
    return restoreTokens(out.join(""), display.mark, display.spans);
  }

  function recordRecent(type, id) {
    if (!type || !id) return;
    var recent = load(AI_RECENT_KEY, []).filter(function (item) {
      return !(item.type === type && item.id === id);
    });
    recent.unshift({ type: type, id: id });
    store(AI_RECENT_KEY, recent.slice(0, 3));
  }

  if (layout.dataset.objectType && layout.dataset.objectId) {
    recordRecent(layout.dataset.objectType, layout.dataset.objectId);
  }

  /* ---------- workspace switch ---------- */

  var selector = document.getElementById("workspace-select");
  if (selector) {
    selector.addEventListener("change", function () {
      window.location = "/w/" + selector.value + "/practice";
    });
  }

  /* ---------- learner settings ---------- */

  var showRatingBox = document.getElementById("setting-show-rating");
  if (showRatingBox) {
    showRatingBox.checked = showRatingEnabled();
    showRatingBox.addEventListener("change", function () {
      saveSetting("showRating", showRatingBox.checked);
    });
  }

  var runningSendSetting = document.getElementById("setting-running-send");
  if (runningSendSetting) {
    runningSendSetting.value = loadSetting("runningSendAction", "queue");
    runningSendSetting.addEventListener("change", function () {
      var action = runningSendSetting.value === "interrupt" ? "interrupt" : "queue";
      runningSendSetting.value = action;
      saveSetting("runningSendAction", action);
    });
  }

  /* ---------- the settings view ---------- */

  /* The settings view is a middle-column page of the same workspace, so it
     travels the same navigation path as the other views and the Agent rail
     stays mounted across the switch (design.md D-9).  The left control opens
     it and closes it again; closing returns to the view it replaced. */
  var settingsReturnUrl = null;

  function settingsViewOpen() {
    return layout.dataset.page === "settings";
  }

  function openSettingsView() {
    settingsReturnUrl = window.location.href;
    navigateMiddle("/w/" + WS + "/settings");
  }

  function closeSettingsView() {
    navigateMiddle(settingsReturnUrl || ("/w/" + WS + "/practice"));
  }

  function renderSettingsToggle() {
    var toggle = document.getElementById("setting-view-toggle");
    if (!toggle) return;
    var open = settingsViewOpen();
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.classList.toggle("active", open);
  }

  function bindSettingsViewToggle() {
    var toggle = document.getElementById("setting-view-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function (event) {
      event.preventDefault();
      if (settingsViewOpen()) closeSettingsView();
      else openSettingsView();
    });
  }

  function renderAppearanceValues() {
    var theme = effectiveTheme();
    var themeBox = document.getElementById("setting-theme");
    var themeValue = document.getElementById("setting-theme-value");
    if (themeBox) themeBox.checked = theme === "night";
    if (themeValue) themeValue.textContent = theme === "night" ? "夜纸" : "暖纸";

    var face = effectiveReadingFace();
    var faceValue = document.getElementById("setting-face-value");
    if (faceValue) faceValue.textContent = face === "sans" ? "无衬线" : "衬线";
    Array.prototype.forEach.call(
      document.querySelectorAll("input[name='setting-face']"),
      function (input) { input.checked = input.value === face; }
    );

    var mode = motionMode();
    var motionBox = document.getElementById("setting-motion");
    var motionValue = document.getElementById("setting-motion-value");
    if (motionBox) motionBox.checked = mode === "full";
    if (motionValue) {
      motionValue.textContent = mode === "full" ? "完整" : (mode === "weak" ? "弱动效" : "直切");
    }

    var soundBox = document.getElementById("setting-sound");
    var soundValue = document.getElementById("setting-sound-value");
    var soundOn = soundEnabled();
    if (soundBox) soundBox.checked = soundOn;
    if (soundValue) soundValue.textContent = soundOn ? "开" : "关";
  }

  function mountSettingsView() {
    var themeBox = document.getElementById("setting-theme");
    var motionBox = document.getElementById("setting-motion");
    var soundBox = document.getElementById("setting-sound");
    var closeButton = document.getElementById("settings-close");

    if (themeBox) {
      themeBox.addEventListener("change", function () {
        var theme = themeBox.checked ? "night" : "paper";
        saveSetting("theme", theme);
        /* The theme change is carried by the lamp transition (tasks.md 8.7);
           the preference is stored first, so the theme is the same whether
           the transition plays or the tier is downgraded. */
        runLampTransition(theme);
        renderAppearanceValues();
      });
    }
    Array.prototype.forEach.call(
      document.querySelectorAll("input[name='setting-face']"),
      function (input) {
        input.addEventListener("change", function () {
          if (!input.checked) return;
          saveSetting("readingFace", input.value);
          applyReadingFace(input.value);
          renderAppearanceValues();
        });
      }
    );
    if (motionBox) {
      motionBox.addEventListener("change", function () {
        saveSetting("motion", motionBox.checked);
        applyMotion();
        renderAppearanceValues();
      });
    }
    if (soundBox) {
      soundBox.addEventListener("change", function () {
        if (window.lkSfx) window.lkSfx.setEnabled(soundBox.checked);
        else saveSetting("sound", soundBox.checked);
        renderAppearanceValues();
      });
    }
    if (closeButton) {
      closeButton.addEventListener("click", function () { closeSettingsView(); });
    }
    renderAppearanceValues();
  }

  bindSettingsViewToggle();
  applyTheme(effectiveTheme());
  applyReadingFace(effectiveReadingFace());
  applyMotion();

  /* ---------- key feedback cues ----------
   * Four contract events carry a cue: an answer judged correct, an answer
   * judged wrong, a finished round and a milestone (openspec
   * changes/workbench-visual-language-v2, spec requirement "Key feedback
   * audio cues").  Nothing else may sound.
   *
   * The cues themselves live in sfx.js.  The shell's script list belongs to
   * pages.py, so the module is pulled in here and the triggers are wired only
   * once it is there.  A cue may only follow a judgment the learner just
   * caused, so each trigger is armed by the gesture it belongs to — the
   * submit, or the pick that judges on the spot, by mouse or by keyboard
   * (A-102) — and disarmed as soon as it fires; re-rendering an old answer
   * stays silent.
   *
   * A-53: the milestone cue is not wired here — it rides on the tier
   * decision in `celebrateCompletion`, so the downgraded tier sounds too.
   */

  var CUE_ARM_WINDOW_MS = 10000;
  var VERDICT_SELECTOR = ".micro-verdict";
  var verdictArmedAt = 0;
  var completionArmedAt = 0;

  function ancestorWithId(node, id) {
    var current = node;
    while (current && current.nodeType === 1) {
      if (current.id === id) return current;
      current = current.parentNode;
    }
    return null;
  }

  /* The other gesture that carries a verdict: a choice that judges on the
     spot.  In the paper flow a single-choice / yes-no item is judged the
     moment its option is picked, so that pick is the gesture the verdict
     belongs to — it has to arm the cue exactly like the submit button does,
     or the sound lands apart from the bounce (decisions.md A-102).
     Only the paper flow judges on selection: the practice flow judges at its
     own submit button, and a multiple-choice item is judged at the paper's
     submit button too.  Only the input itself counts: while an answered
     paper is read back the options are disabled, so they cannot be picked,
     and a read-back never sounds. */
  function judgesOnSelection(node) {
    if (!node || node.nodeType !== 1) return false;
    if (node.tagName !== "INPUT" || node.type !== "radio") return false;
    if (!node.hasAttribute || !node.hasAttribute("data-paper-choice")) return false;
    return !!ancestorWithId(node, "paper-options");
  }

  /* The keyboard reaches the same choice without a click: the arrow keys
     move the selection inside a radio group, and the browser reports that
     as a change — some engines also report a click for it, some do not.  So
     the change arms the cue as well, on the same one-shot arm: a mouse pick
     arrives as a click *and* a change, both write the same value, and the
     cue still fires exactly once. */
  layout.addEventListener("change", function (event) {
    var target = event.target;
    if (!target) return;
    if (!judgesOnSelection(target)) return;
    verdictArmedAt = Date.now();
  }, true);

  /* The click gate hangs off the layout element, the root of the workbench
     shell: every control that can judge an answer lives inside it. */
  layout.addEventListener("click", function (event) {
    var target = event.target;
    if (!target) return;
    /* A cue belongs to the judgment or the completion caused by the learner's
       most recent interaction: the gesture that judges (a submit, or a pick
       that judges on the spot) arms it, any other click cancels it, so
       re-reading an old answer stays silent. */
    if (ancestorWithId(target, "answer-submit")
        || ancestorWithId(target, "paper-item-submit")
        || judgesOnSelection(target)) {
      verdictArmedAt = Date.now();
    } else {
      verdictArmedAt = 0;
    }
    if (ancestorWithId(target, "paper-final-submit")) {
      completionArmedAt = Date.now();
      /* The celebration rides on the same gesture: it belongs to the round
         that this submit ends, not to every later look at the completion
         surface (tasks.md 8.8: the celebration waits for the response). */
      celebrationArmedAt = Date.now();
    } else {
      completionArmedAt = 0;
      celebrationArmedAt = 0;
    }
  }, true);

  function cueArmed(armedAt) {
    return Date.now() - armedAt < CUE_ARM_WINDOW_MS;
  }

  function cueVerdict(node) {
    if (!cueArmed(verdictArmedAt)) return;
    var classes = node.classList;
    if (!classes) return;
    var ok = classes.contains("ok");
    if (!ok && !classes.contains("bad")) return;
    verdictArmedAt = 0;
    if (ok) {
      window.lkSfx.playCue("correct");
    } else {
      window.lkSfx.playCue("wrong");
    }
  }

  function cueInspect(node) {
    if (!node || node.nodeType !== 1) return;
    var verdicts = [];
    if (node.matches && node.matches(VERDICT_SELECTOR)) verdicts.push(node);
    if (node.querySelectorAll) {
      verdicts = verdicts.concat(Array.prototype.slice.call(
        node.querySelectorAll(VERDICT_SELECTOR)));
    }
    verdicts.forEach(cueVerdict);
  }

  function wireKeyFeedbackCues() {
    if (!window.lkSfx || typeof window.lkSfx.playCue !== "function") return;

    var middlePage = document.getElementById("middle-page");
    if (middlePage && window.MutationObserver) {
      var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
          Array.prototype.slice.call(mutation.addedNodes).forEach(cueInspect);
        });
      });
      observer.observe(middlePage, { childList: true, subtree: true });
    }

    var completion = document.getElementById("paper-completion");
    if (completion && window.MutationObserver) {
      var wasVisible = !completion.hidden
        && !(completion.classList && completion.classList.contains("hidden"));
      var completionObserver = new MutationObserver(function () {
        var visible = !completion.hidden
          && !(completion.classList && completion.classList.contains("hidden"));
        if (visible && !wasVisible && cueArmed(completionArmedAt)) {
          completionArmedAt = 0;
          window.lkSfx.playCue("complete");
        }
        wasVisible = visible;
      });
      completionObserver.observe(completion, {
        attributes: true,
        attributeFilter: ["class", "hidden"],
      });
    }
  }

  function loadSfxModule() {
    return new Promise(function (resolve) {
      var script = document.createElement("script");
      script.src = "/static/sfx.js";
      script.async = false;
      script.onload = function () { resolve(true); };
      script.onerror = function () { resolve(false); };
      /* A script inserted into the document runs wherever it is placed, and
         the layout element is the one element every page of the shell has. */
      layout.appendChild(script);
    });
  }

  loadSfxModule().then(function (loaded) {
    if (!loaded) return;
    wireKeyFeedbackCues();
  });

  var mobileNavToggle = document.getElementById("mobile-nav-toggle");
  var mobileAiToggle = document.getElementById("mobile-ai-toggle");
  function toggleDrawer(name) {
    var open = !layout.classList.contains(name);
    layout.classList.toggle("left-drawer-open", name === "left-drawer-open" && open);
    layout.classList.toggle("ai-drawer-open", name === "ai-drawer-open" && open);
    if (mobileNavToggle) mobileNavToggle.setAttribute(
      "aria-expanded", layout.classList.contains("left-drawer-open") ? "true" : "false"
    );
    if (mobileAiToggle) mobileAiToggle.setAttribute(
      "aria-expanded", layout.classList.contains("ai-drawer-open") ? "true" : "false"
    );
  }
  if (mobileNavToggle) mobileNavToggle.addEventListener("click", function () {
    toggleDrawer("left-drawer-open");
  });
  if (mobileAiToggle) mobileAiToggle.addEventListener("click", function () {
    toggleDrawer("ai-drawer-open");
  });

  function mountGraphPage() {
  /* ---------- native knowledge graph (implementation blueprint port) ---------- */

  var graphCanvas = document.getElementById("graph-canvas");
  if (!graphCanvas) return null;
  var graphDisposed = false;
  var graphResizeObserver = null;
  var graphResizeHandler = null;
  if (graphCanvas) {
    var graphSearch = document.getElementById("graph-search");
    var graphViews = document.getElementById("graph-views");
    var graphFocusBtn = document.getElementById("graph-focus");
    var graphFitBtn = document.getElementById("graph-fit");
    var graphFilters = document.getElementById("graph-filters");
    var graphGravity = document.getElementById("graph-gravity");
    var graphGravityValue = document.getElementById("graph-gravity-value");
    var graphStrongGap = document.getElementById("graph-strong-gap");
    var graphMediumGap = document.getElementById("graph-medium-gap");
    var graphWeakGap = document.getElementById("graph-weak-gap");
    var graphSolverState = document.getElementById("graph-solver-state");
    var graphSolverText = document.getElementById("graph-solver-text");
    var graphReadabilityState = document.getElementById("graph-readability-state");
    var graphStage = document.getElementById("graph-stage");
    var graphEdges = document.getElementById("graph-edges");
    var graphTide = document.getElementById("graph-tide");
    var graphToast = document.getElementById("graph-toast");
    var graphToastTimer = null;
    var graphToastPersistent = false;
    var graphZoomIn = document.getElementById("graph-zoom-in");
    var graphZoomOut = document.getElementById("graph-zoom-out");
    var graphZoomReset = document.getElementById("graph-reset");
    var graphDetail = document.getElementById("graph-detail-panel");
    var graphControls = document.getElementById("graph-controls");
    var graphControlsToggle = document.getElementById("graph-controls-toggle");
    var graphEdgeBudgetEl = null;

    // The control card starts folded — the server renders it that way, so there is no flash
    // — and this only has to keep the button and the card in step.
    if (graphControls && graphControlsToggle) {
      graphControlsToggle.addEventListener("click", function () {
        var collapsed = graphControls.dataset.collapsed !== "true";
        graphControls.dataset.collapsed = collapsed ? "true" : "false";
        graphControlsToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      });
    }

    var STATE_LABEL = { work: "重点练习", review: "可以复习", mastered: "已掌握", new: "未标记" };
    var STATE_SHORT = { work: "练", review: "复", mastered: "熟", new: "新" };
    var STATE_PILL = {
      work: { bg: "var(--redSoft)", fg: "var(--red)" },
      review: { bg: "var(--yellowSoft)", fg: "#8c6b00" },
      mastered: { bg: "var(--blueSoft)", fg: "var(--blue)" },
      new: { bg: "#f3f4f6", fg: "#747983" },
    };
    var REL_NAME = { prereq: "先修", related: "相关", contrast: "对比", apply: "应用" };
    var REL_CLS = { prereq: "blue", related: "", contrast: "red", apply: "yellow" };
    var PROJECTION_TEXT = {
      structure: "关系", problem_count: "题目", importance: "重要性", state: "关注度",
    };

    function mapGraphState(state) {
      if (!state) return "new";
      if (state === "needs_work") return "work";
      return state;
    }

    function mapEdgeType(edge) {
      if (edge.id && String(edge.id).indexOf("legacy:") === 0) return "legacy";
      return ({
        prerequisite: "prereq",
        applies_to: "apply",
        contrasts: "contrast",
        related: "related",
      })[edge.relation_type] || "related";
    }

    function mapStrength(strength) {
      return strength === "high" ? 1.875 : strength === "medium" ? 1.25 : .75;
    }

    // Relation-type visibility, driven by the legend buttons. Co-occurrence
    // ("legacy") edges are auto-derived rather than authored, so a pool that
    // also has explicit relations starts with them hidden; the legend item
    // brings them back.
    var graphHiddenEdgeTypes = {};
    /* Relation display budget. A whole-course lens can carry several hundred
     * relations (习概: 192 points, 728 relations), and drawing them all is a
     * hairball nobody can read. Each knowledge point keeps its single strongest
     * relation, then the remaining slots go by weight, so low-weight links drop
     * out of both the picture and the layout instead of papering over it.
     *
     * The ratio is edges per point, and since sum(degree) = 2E it is also half the
     * average degree. At 0.5 every point showed on average one relation, which
     * measured as 24 of dmath's 35 relations — a third of the authored graph was
     * invisible. 1.5 shows all of dmath's 35 and still caps 习概 at 288 of 728. */
    var GRAPH_EDGE_BUDGET_RATIO = 1.5;

    function graphEdgeWeight(edge) {
      var typeWeight = edge.type === "prereq" ? 1
        : edge.type === "apply" ? .95
          : edge.type === "contrast" ? .85
            : edge.type === "legacy" ? .25
              : .6;                      // authored "related"
      var strengthWeight = edge.strength >= 1.875 ? 1 : edge.strength >= 1.25 ? .8 : .6;
      // A co-occurrence link that gathers many shared problems is closer to a
      // real relation than one that shares a single problem.
      return typeWeight * strengthWeight + Math.min(.25, edge.sharedProblems / 200);
    }

    function graphSelectDisplayEdges(edges, nodeCount) {
      var budget = Math.max(24, Math.round(nodeCount * GRAPH_EDGE_BUDGET_RATIO));
      var ranked = edges.map(function (edge) { return { edge: edge, score: graphEdgeWeight(edge) }; })
        .sort(function (a, b) {
          return b.score - a.score || String(a.edge.id).localeCompare(String(b.edge.id));
        });
      var kept = new Set();
      var bestPerNode = new Map();
      ranked.forEach(function (item) {
        [item.edge.s, item.edge.t].forEach(function (id) {
          var best = bestPerNode.get(id);
          if (!best || best.score < item.score) bestPerNode.set(id, item);
        });
      });
      bestPerNode.forEach(function (item) { kept.add(item); });
      for (var i = 0; i < ranked.length && kept.size < budget; i += 1) kept.add(ranked[i]);
      var hiddenIds = new Set();
      ranked.forEach(function (item) {
        if (!kept.has(item)) hiddenIds.add(item.edge.id);
      });
      return { hiddenIds: hiddenIds, budget: budget, shown: kept.size };
    }

    var graphEdgeTotals = { total: 0, shown: 0 };

    function graphEdgeBudgetText() {
      if (!graphEdgeTotals.total) return "—";
      return graphEdgeTotals.shown + " / " + graphEdgeTotals.total;
    }

    function graphApplyEdgeVisibility() {
      if (!sim) return;
      var enabled = sim.edges.filter(function (edge) {
        return !graphHiddenEdgeTypes[edge.type];
      });
      var selection = graphSelectDisplayEdges(enabled, sim.nodes.length);
      sim.setEdgeVisibility({ types: graphHiddenEdgeTypes, ids: selection.hiddenIds });
      graphEdgeTotals = { total: sim.edges.length, shown: selection.shown };
      if (graphEdgeBudgetEl) {
        graphEdgeBudgetEl.textContent = graphEdgeBudgetText();
        graphEdgeBudgetEl.title = "整门课按权重取舍关系：每个知识点至少保留最强的一条，隐含共现排在最末。"
          + "当前显示 " + selection.shown + " 条，共 " + sim.edges.length + " 条（预算 " + selection.budget + "，隐式类型不计入）。";
      }
      var trimmed = sim.edges.length - selection.shown;
      if (trimmed > 0 && !graphEdgeBudget.told) {
        graphEdgeBudget.told = true;
        graphToastShow("关系较多：按权重显示 " + selection.shown + " / " + sim.edges.length + " 条，低权重关系不参与显示与布局");
      }
    }

    var graphEdgeBudget = { told: false };
    var graphEdgeBudgetEl = null;

    var graphNodeData = [];   // physics nodes
    var graphEdgeData = [];   // physics edges
    var graphEdgeEls = [];    // {edge, path}
    var graphEls = new Map(); // id -> {wrap, node, label, meta, value, satellite}
    var sim = null;
    currentGraphContext = function () {
      return sim && sim.graph ? { selectedKpId: selectedGraphKpId, filters: sim.graph.filters } : null;
    };
    var graphPhysicsAvailable = typeof GraphPhysics !== "undefined"
      && GraphPhysics && GraphPhysics.workerBacked === true;
    var graphView = { scale: .7, panX: 52, panY: -18, userMoved: false };
    var graphPathScaled = 1;
    var graphLastPaintedScale = 0;
    var graphRenderDirty = true;
    var graphFrameHandle = null;
    var graphAutoFitInFrame = false;
    // Smoothed milliseconds for one whole graph frame, paint included. Decides whether the next
    // frame paints — see the note in graphFrame. Null until the first frame has been measured.
    var graphFrameCostMs = null;

    function nowMs() {
      return typeof performance !== "undefined" && performance.now ? performance.now() : Date.now();
    }

    function graphSolver(solving) {
      if (!graphSolverState) return;
      graphSolverState.classList.toggle("solving", !!solving);
      if (graphSolverText) graphSolverText.textContent = solving ? "约束求解中" : "已收敛";
    }

    function graphLegendItems() {
      var legend = document.getElementById("graph-legend");
      if (!legend) return [];
      var found = legend.querySelectorAll ? legend.querySelectorAll(".legend-item") : [];
      if (found && found.length) return Array.prototype.slice.call(found);
      var children = legend.children ? Array.prototype.slice.call(legend.children) : [];
      return children.filter(function (child) {
        return typeof child.className === "string"
          && child.className.split(/\s+/).indexOf("legend-item") >= 0;
      });
    }

    function graphSyncLegend() {
      graphLegendItems().forEach(function (item) {
        var hidden = !!graphHiddenEdgeTypes[item.dataset.edgeType];
        item.classList.toggle("off", hidden);
        item.setAttribute("aria-pressed", hidden ? "false" : "true");
      });
    }

    function graphToastShow(text, persistent) {
      if (!graphToast || (graphToastPersistent && !persistent)) return;
      if (graphToastTimer !== null) clearTimeout(graphToastTimer);
      graphToast.textContent = text;
      graphToast.classList.add("show");
      graphToastPersistent = !!persistent;
      if (graphToastPersistent) return;
      graphToastTimer = setTimeout(function () {
        graphToastTimer = null;
        graphToast.classList.remove("show");
      }, 1300);
    }

    function graphFailureShow(message) {
      graphSolver(false);
      if (graphSolverText) graphSolverText.textContent = "计算已停止";
      graphToastShow(message || "图谱计算失败，布局已停止。刷新页面后可重试。", true);
      graphRenderDirty = false;
    }

    function graphUpdateGapLegend() {
      if (!sim) return;
      // The legend has to describe the guides the current view actually uses:
      // structure guides follow gravity only (band wrapping, not inflation,
      // absorbs pressure), while the metric views keep the inflation escape
      // hatch from the blueprint.
      var inflation = sim.graph.view === "structure" ? 1 : sim.graph.layoutInflation;
      var spread = GraphPhysics.spreadFactor(sim.graph.gravity) * inflation;
      if (graphStrongGap) graphStrongGap.textContent = Math.round(GraphPhysics.baseGapForStrength(1.875) * spread) + "px";
      if (graphMediumGap) graphMediumGap.textContent = Math.round(GraphPhysics.baseGapForStrength(1.25) * spread) + "px";
      if (graphWeakGap) graphWeakGap.textContent = Math.round(GraphPhysics.baseGapForStrength(.75) * spread) + "px";
      if (graphReadabilityState) {
        graphReadabilityState.textContent = "硬下限 · " + inflation.toFixed(2) + "×";
      }
    }

    function graphStageSize(nodes, levels, gravity) {
      // The stage must cover the guide grid exactly; both come from the same
      // physics helper so they cannot drift apart.
      return GraphPhysics.structureStageSize(nodes, levels, gravity);
    }

    /* The graph shows the shortest name a title can be cut down to: up to the first
     * punctuation that is not a comma, so "广义鸽巢原理 (Generalized Pigeonhole
     * Principle)" reads as "广义鸽巢原理" and "摊还分析：聚合分析法 (Aggregate Method)"
     * reads as "摊还分析". Measured on the two real pools this takes 53% off dmath's
     * total label width and 39% off c02's, which matters beyond legibility: label width
     * is what sets how close two points may sit, so it is also what decides how small
     * the whole graph has to be and therefore how far Fit zooms out.
     *
     * The comma is exempt because "r-组合计数公式 C(n,r) = n!/(r!(n-r)!)" would
     * otherwise be cut inside a formula.
     *
     * Cutting does not always leave distinct names. Measured: dmath keeps 31 distinct
     * labels out of 31, but c02 collapses three groups — three different amortised-
     * analysis methods all become "摊还分析". Same-named points on a graph are a
     * correctness problem, not a cosmetic one, so any group that would collide is
     * extended to the next punctuation instead ("摊还分析：聚合分析法" and so on), and
     * falls back to the full title if that still collides. Six of c02's 86 points are
     * affected; dmath has none.
     *
     * This is view-layer only. The knowledge point's own text is never changed and
     * nothing is written back. */
    var GRAPH_TITLE_STOP = /[。！？；：、（）【】《》“”‘’…—·!?;:()\[\]{}<>"']/;

    function graphTitleCut(title, stops) {
      var text = String(title || "");
      var seen = 0;
      for (var i = 0; i < text.length; i += 1) {
        if (!GRAPH_TITLE_STOP.test(text[i])) continue;
        seen += 1;
        if (seen > stops) return text.slice(0, i);
      }
      return text;
    }

    function graphShortTitles(nodes) {
      var out = new Map();
      nodes.forEach(function (node) { out.set(node.id, graphTitleCut(node.title, 0)); });
      // Any name more than one point would share gets one more stop, so the group is
      // told apart without dragging every other label longer.
      var best = graphTitleCut;
      for (var stops = 0; ; stops += 1) {
        var byLabel = new Map();
        nodes.forEach(function (node) {
          var label = out.get(node.id);
          if (!byLabel.has(label)) byLabel.set(label, []);
          byLabel.get(label).push(node);
        });
        var clashing = [];
        byLabel.forEach(function (group) { if (group.length > 1) clashing.push(group); });
        if (!clashing.length) break;
        var extended = false;
        clashing.forEach(function (group) {
          group.forEach(function (node) {
            var label = best(node.title, stops + 1);
            if (label === out.get(node.id)) label = String(node.title || node.id);
            if (label !== out.get(node.id)) extended = true;
            out.set(node.id, label);
          });
        });
        if (!extended) {
          clashing.forEach(function (group) {
            group.forEach(function (node) { out.set(node.id, String(node.title || node.id) + " · " + node.id); });
          });
          break;
        }
      }
      return out;
    }

    function graphBuild(model) {
      if (!graphPhysicsAvailable) {
        graphFailureShow("图谱计算无法启动：浏览器不支持 Worker，或图谱资源加载失败。请刷新页面，或使用支持 Worker 的浏览器。");
        return;
      }
      var shortTitles = graphShortTitles(model.nodes || []);
      graphNodeData = (model.nodes || []).map(function (node) {
        return {
          id: node.id,
          title: node.title || node.id,
          shortTitle: shortTitles.get(node.id) || node.title || node.id,
          state: mapGraphState(node.state),
          kind: node.importance === "supplementary" ? "support" : "core",
          importance: node.importance === "supplementary" ? .55 : 1,
          problems: Number(node.problem_count) || 0,
        };
      });
      graphEdgeData = (model.edges || []).map(function (edge) {
        return {
          id: edge.id,
          s: edge.source,
          t: edge.target,
          type: mapEdgeType(edge),
          strength: mapStrength(edge.strength),
          direction: edge.direction,
          sharedProblems: Number(edge.shared_problem_count) || 0,
        };
      });
      var ids = new Set(graphNodeData.map(function (node) { return node.id; }));
      graphEdgeData = graphEdgeData.filter(function (edge) {
        return ids.has(edge.s) && ids.has(edge.t) && edge.s !== edge.t;
      });
      var levels = GraphPhysics.hierarchyLevels(graphNodeData, graphEdgeData);
      var size = graphStageSize(graphNodeData, levels, graphGravity ? Number(graphGravity.value) : 30);
      graphHiddenEdgeTypes = {};
      var hasSemanticEdge = graphEdgeData.some(function (edge) { return edge.type !== "legacy"; });
      var hasLegacyEdge = graphEdgeData.some(function (edge) { return edge.type === "legacy"; });
      if (hasSemanticEdge && hasLegacyEdge) graphHiddenEdgeTypes.legacy = true;
      sim = GraphPhysics.create(graphNodeData, graphEdgeData, {
        stageWidth: size.width,
        stageHeight: size.height,
        view: "structure",
        gravity: graphGravity ? Number(graphGravity.value) : 30,
        hiddenEdgeTypes: graphHiddenEdgeTypes,
      });
      if (sim.failed) {
        graphFailureShow(sim.error);
        return;
      }
      // The fit follows the window, not the canvas — see graphWatchWindowSize.
      graphWatchWindowSize();
      graphEdgeBudget = { told: false };
      graphEdgeBudgetEl = graphEdgeBudgetEl || document.getElementById("graph-edge-budget");
      graphApplyEdgeVisibility();
      graphSyncLegend();
      graphNodeData = sim.nodes;
      graphEdgeData = sim.edges;
      graphStage.style.width = sim.state.stageWidth + "px";
      graphStage.style.height = sim.state.stageHeight + "px";
      graphEdges.setAttribute("width", String(sim.state.stageWidth));
      graphEdges.setAttribute("height", String(sim.state.stageHeight));
      graphEdges.setAttribute("viewBox", "0 0 " + sim.state.stageWidth + " " + sim.state.stageHeight);
      graphCreateSvg();
      graphCreateNodes();
      graphApplyVisibility();
      graphUpdateGapLegend();
      graphApplyView();
      sim.reheat(1, true);
      graphSolver(true);
      graphEnsureLoop();
    }

    function graphCreateSvg() {
      graphEdges.innerHTML =
        "<defs>"
        + "<marker id='graph-arrow-blue' viewBox='0 0 8 8' refX='7' refY='4' markerWidth='6' markerHeight='6' orient='auto'>"
        + "<path d='M0 0 L8 4 L0 8Z' fill='#2457c5' opacity='.75'></path></marker>"
        + "<marker id='graph-arrow-yellow' viewBox='0 0 8 8' refX='7' refY='4' markerWidth='6' markerHeight='6' orient='auto'>"
        + "<path d='M0 0 L8 4 L0 8Z' fill='#c3a128' opacity='.72'></path></marker>"
        + "</defs>";
      // Weak relationships first: SVG paints in document order, so appending ascending by
      // strength is what puts strong evidence on top. Same rule as the WebGL pass — this
      // is the fallback layer, and it should not disagree with the primary one about which
      // relationship wins when two overlap.
      graphEdgeEls = sim.edges.slice().sort(function (x, y) {
        var d = (Number(x.strength) || 0) - (Number(y.strength) || 0);
        if (d) return d;
        return String(x.id) < String(y.id) ? -1 : String(x.id) > String(y.id) ? 1 : 0;
      }).map(function (edge) {
        var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "graph-edge " + edge.type);
        if (edge.id !== undefined && path.dataset) path.dataset.edgeId = String(edge.id);
        if (edge.type === "prereq" && edge.direction !== "symmetric") {
          path.setAttribute("marker-end", "url(#graph-arrow-blue)");
        }
        if (edge.type === "apply" && edge.direction !== "symmetric") {
          path.setAttribute("marker-end", "url(#graph-arrow-yellow)");
        }
        graphEdges.appendChild(path);
        return { edge: edge, path: path };
      });
    }

    function graphCreateNodes() {
      if (graphEls.size) {
        graphEls.forEach(function (elements) {
          elements.wrap.remove();
          elements.select.remove();
        });
        graphEls = new Map();
      }
      var selected = selectedKpIds();
      sim.nodes.forEach(function (node) {
        var wrap = document.createElement("div");
        wrap.className = "node-wrap " + node.kind + " state-" + node.state;
        wrap.dataset.kpId = node.id;
        var button = document.createElement("button");
        button.type = "button";
        button.className = "node";
        button.setAttribute("aria-label", node.title);
        var metric = document.createElement("span");
        metric.className = "metric-track";
        var ring = document.createElement("span");
        ring.className = "status-ring";
        var face = document.createElement("span");
        face.className = "node-face";
        var value = document.createElement("span");
        value.className = "node-value";
        var unit = document.createElement("span");
        unit.className = "node-unit";
        face.appendChild(value);
        face.appendChild(unit);
        var satellite = document.createElement("span");
        satellite.className = "node-satellite";
        button.appendChild(metric);
        button.appendChild(ring);
        button.appendChild(face);
        button.appendChild(satellite);
        var label = document.createElement("div");
        label.className = "label";
        label.textContent = node.shortTitle || node.title;
        // Hover still has to give the whole title: the graph is showing an abbreviation.
        label.title = node.title;
        button.title = node.title;
        var meta = document.createElement("div");
        meta.className = "meta";
        wrap.appendChild(button);
        wrap.appendChild(label);
        wrap.appendChild(meta);
        var pressAt = null;
        button.addEventListener("click", function (event) {
          if (event.stopPropagation) event.stopPropagation();
          // A drag is not a click. With pointer capture the browser still fires click
          // when the press and the release both land on the button, however far the
          // pointer travelled in between, so moving a node used to open its panel.
          var travelled = pressAt
            ? Math.hypot(event.clientX - pressAt.x, event.clientY - pressAt.y)
            : 0;
          pressAt = null;
          if (travelled > 4) return;
          graphSelect(node.id, true);
        });
        button.addEventListener("mouseenter", function () {
          sim.graph.hover = node.id;
          graphMarkDirty();
        });
        button.addEventListener("mouseleave", function () {
          if (sim.graph.hover === node.id) sim.graph.hover = null;
          graphMarkDirty();
        });
        button.addEventListener("pointerdown", function (event) {
          if (event.stopPropagation) event.stopPropagation();
          sim.graph.drag = { id: node.id, pointerId: event.pointerId };
          pressAt = { x: event.clientX, y: event.clientY };
          wrap.classList.add("dragging");
          if (button.setPointerCapture && event.pointerId !== undefined) {
            button.setPointerCapture(event.pointerId);
          }
          sim.reheat(.55, false);
          graphSolver(true);
          graphEnsureLoop();
        });
        button.addEventListener("dblclick", function (event) {
          if (event.stopPropagation) event.stopPropagation();
          node.anchorX = null;
          node.anchorY = null;
          sim.reheat(.8, true);
          graphSolver(true);
          graphEnsureLoop();
          graphToastShow("已释放固定位置");
        });
        graphStage.appendChild(wrap);
        graphEls.set(node.id, {
          node: node, wrap: wrap, button: button, label: label, meta: meta,
          value: value, unit: unit,
        });
        graphUpdateNodeAppearance(node);
      });
      graphSyncScope();
    }

    function graphProjectionDisplay(node) {
      var score = sim.scoreFor(node);
      if (sim.graph.view === "structure") return [String(sim.state.degreeCount.get(node.id) || 0), ""];
      if (sim.graph.view === "problem_count") return [String(node.problems), ""];
      if (sim.graph.view === "importance") return [String(Math.round(node.importance * 100)), "%"];
      return [STATE_SHORT[node.state], ""];
    }

    function graphUpdateNodeAppearance(node) {
      var elements = graphEls.get(node.id);
      if (!elements) return;
      var score = sim.scoreFor(node);
      elements.button.style.setProperty("--metric-angle", (Math.max(.06, score) * 302) + "deg");
      var display = graphProjectionDisplay(node);
      if (elements.value) elements.value.textContent = display[0];
      if (elements.unit) elements.unit.textContent = display[1];
      if (elements.meta) {
        elements.meta.textContent = STATE_LABEL[node.state] + " · "
          + PROJECTION_TEXT[sim.graph.view] + " " + display[0] + display[1];
      }
    }

    function graphSyncScope() {}

    function graphApplyVisibility() {
      var filters = sim.graph.filters;
      var focus = sim.graph.selected
        ? sim.neighbors(sim.graph.selected)
        : { one: new Set(), two: new Set() };
      sim.nodes.forEach(function (node) {
        var allowed = filters.size === 0 || filters.has(node.state);
        node.visible = allowed;
        var weight = 1;
        if (sim.graph.selected) {
          weight = node.id === sim.graph.selected ? 1
            : focus.one.has(node.id) ? .92
              : focus.two.has(node.id) ? .48 : .12;
        }
        node.focusWeight = weight;
        node.targetOpacity = allowed ? weight : 0;
        var elements = graphEls.get(node.id);
        if (elements) {
          elements.wrap.classList.toggle("selected", node.id === sim.graph.selected);
          elements.wrap.classList.toggle("dim", weight < .5);
          elements.wrap.classList.toggle("filtered", !allowed);
        }
      });
    }

    function graphApplyView() {
      if (!sim) return;
      graphStage.style.transform = "translate(" + graphView.panX + "px," + graphView.panY + "px) scale(" + graphView.scale + ")";
      // Camera movement never reheats the solver. Zoom uses the light
      // stroke/label pass; fixed-scale translation invalidates the parked
      // renderer so viewport culling follows the camera.
      if (graphView.scale !== graphLastPaintedScale) {
        graphPaintViewport();
      } else if (!graphAutoFitInFrame) {
        // Translation changes renderer viewport culling even at fixed zoom.
        graphRenderRelations();
      }
    }

    function graphPaintViewport() {
      if (!sim) return;
      graphLastPaintedScale = graphView.scale;
      graphPathScaled = 1 / Math.max(.2, graphView.scale || 1);
      graphEdgeEls.forEach(function (item) {
        if (item.path.style && item.path.style.display === "none") return;
        var style = sim.edgeStyle(item.edge);
        item.path.style.strokeWidth = (style.width * graphPathScaled) + "px";
        if (item.edge.type === "contrast") {
          item.path.style.strokeDasharray = (6 * graphPathScaled) + " " + (5 * graphPathScaled);
        } else if (item.edge.type === "legacy") {
          item.path.style.strokeDasharray = (2 * graphPathScaled) + " " + (6 * graphPathScaled);
        }
      });
      graphPaintNodes();
      graphNotePaint("viewport");
      if (!graphAutoFitInFrame) graphRenderRelations();
    }

    function graphRenderRelations() {
      if (!sim || !sim.renderer) return;
      if (graphTideState.reduced && !sim.graph.settled) return;
      sim.renderer.render();
    }

    function graphNotePaint(kind) {
      if (graphStage.dataset) graphStage.dataset.lastPaint = kind;
    }

    /* The learning dashboard is closed until a point is chosen, because until then it has
     * nothing to show and it costs the canvas a whole column. Folding it changes the canvas
     * width and the resize watcher re-fits from that — the panel's own job is only to
     * change the layout, not to reach in and re-zoom the graph itself.
     * The state is deliberately not remembered: every visit starts from the canvas. */
    function graphSetDashboard(open) {
      var workspace = document.getElementById("graph-workspace");
      if (!workspace) return;
      var next = open ? "open" : "collapsed";
      if (workspace.dataset.dashboard === next) return;
      workspace.dataset.dashboard = next;
    }

    function graphSelect(id, centerIt) {
      sim.graph.selected = id;
      selectedGraphKpId = id;
      recordRecent("kp", id);
      graphSetDashboard(Boolean(id));
      graphApplyVisibility();
      graphRenderDetail(sim.byId.get(id));
      if (centerIt) graphCenterOn(sim.byId.get(id), true);
      graphMarkDirty();
    }

    function graphCenterOn(node, zoom) {
      if (!node) return;
      if (zoom) graphView.scale = Math.max(graphView.scale, .78);
      graphView.panX = graphCanvas.clientWidth / 2 - node.x * graphView.scale;
      graphView.panY = graphCanvas.clientHeight / 2 - node.y * graphView.scale;
      graphView.userMoved = true;
      graphApplyView();
    }

    /* Fit once after the first settle, and when the WINDOW changes size — not when the canvas
     * changes size.
     *
     * That distinction is the whole point. The dashboard is a column of the graph grid, so
     * opening it narrows the canvas, and re-fitting there re-zoomed the entire picture on every
     * selection: the learner picks a point to read about it and the view jumps to a new zoom,
     * sliding the very point they were looking at. Selecting a point is a change of subject,
     * not a change of viewport, and it should not move the camera.
     *
     * A window resize is a different thing. The space genuinely changed and nobody wants a graph
     * left cropped because the browser got narrower, so that one still re-fits.
     *
     * The fit button still fits on demand, and the first settle still fits once — the initial
     * view is not affected by this. */
    function graphWatchWindowSize() {
      if (typeof window === "undefined" || !window.addEventListener) return;
      window.addEventListener("resize", function () {
        if (!sim) return;
        graphFit();
        graphMarkDirty();
      });
    }

    function graphFit() {
      if (!sim) return;
      var active = sim.nodes.filter(function (node) { return node.visible && node.opacity > .02; });
      if (!active.length) return;
      var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      active.forEach(function (node) {
        var fp = GraphPhysics.footprint(node);
        minX = Math.min(minX, node.x - fp.left - 18);
        maxX = Math.max(maxX, node.x + fp.right + 18);
        minY = Math.min(minY, node.y - fp.top - 18);
        maxY = Math.max(maxY, node.y + fp.bottom + 18);
      });
      var width = maxX - minX + 90;
      var height = maxY - minY + 100;
      // The floor used to be .38, sized for the old layouts, which the row grid held
      // near 1100px — a 1200px viewport never came close to it. A free force field
      // finds its own extent and can be several times that, so .38 stopped being a
      // readability floor and started cropping the graph. Fit should fit.
      graphView.scale = Math.max(.1, Math.min(1.05,
        (graphCanvas.clientWidth - 36) / width,
        (graphCanvas.clientHeight - 36) / height));
      graphView.panX = graphCanvas.clientWidth / 2 - (minX + maxX) / 2 * graphView.scale;
      graphView.panY = graphCanvas.clientHeight / 2 - (minY + maxY) / 2 * graphView.scale;
      graphApplyView();
    }

    function graphRenderDetail(node) {
      if (!graphDetail) return;
      if (!node) {
        graphSetDashboard(false);
        graphDetail.innerHTML =
          "<p class='side-label'>学习看板</p><h2>选择一个节点</h2>"
          + "<p class='muted'>点击图中的知识点，查看掌握状态、关联题数与关系强度。</p>";
        return;
      }
      var pill = STATE_PILL[node.state] || STATE_PILL.new;
      var relations = sim.edges.filter(function (edge) {
        return edge.s === node.id || edge.t === node.id;
      });
      var rows = relations.slice(0, 7).map(function (edge) {
        var other = sim.byId.get(edge.s === node.id ? edge.t : edge.s);
        var score = GraphPhysics.strength01(edge.strength);
        var strength = score > .72 ? "强" : score > .28 ? "中" : "弱";
        return "<div class='rel-item'>"
          + "<span class='rel-tag " + (REL_CLS[edge.type] || "") + "'>"
          + (REL_NAME[edge.type] || "相关") + "</span>"
          + "<span>" + escapeHtml(other ? other.title : "") + " · " + strength + "</span></div>";
      }).join("");
      var member = selectedKpIds().indexOf(node.id) >= 0;
      graphDetail.innerHTML =
        "<div class='eyebrow'>Knowledge Point</div>"
        + "<h3 id='graph-detail-title'>" + escapeHtml(node.title) + "</h3>"
        + "<div class='id'>" + escapeHtml(node.id) + "</div>"
        + "<div class='state-pill' style='background:" + pill.bg + ";color:" + pill.fg + "'>"
        + (STATE_LABEL[node.state] || "未标记") + "</div>"
        + "<section class='section'><div class='section-title'>学习概况</div>"
        + "<div class='metric-row'>"
        + "<div class='metric'><b>" + node.problems + "</b><span>关联题目</span></div>"
        + "<div class='metric'><b>" + relations.length + "</b><span>直接关系</span></div>"
        + "</div></section>"
        + "<section class='section'><div class='section-title'>直接关系</div>"
        + "<div class='rel-list'>" + (rows || "<p class='muted'>还没有直接关系。</p>") + "</div></section>"
        + "<section class='section'><div class='section-title'>说明</div>"
        + "<div class='note'>布局在可读性硬下限之上同时压低点密度与线密度：节点从局部过密区域轻微疏散；"
        + "连线不再都从同一圆心出发，而是分配不同的出口 port 与 lane。</div></section>"
        + "<div class='detail-actions'>"
        + "<a class='ghost' href='/w/" + encodeURIComponent(WS) + "/kps?kp=" + encodeURIComponent(node.id)
        + "'>打开知识点</a>"
        + "</div>";
    }

    /* A point's label appears once the point is big enough on screen to hold it.
     *
     * That is how the reference behaves: its renderer draws a node's text when the node's
     * drawn radius clears a threshold, so a big point earns its label at a lower zoom than a
     * small one, and zooming out drops the small ones first. The old rule here was a single
     * global cutoff (scale > .60), which meant every point's label appeared at the same moment
     * no matter how big the point was — size and legibility had nothing to do with each other.
     *
     * 14px is calibrated against the old behaviour rather than picked: the median point is 52px
     * across, which used to appear at .60 and now appears at 14/26 = .538 — near enough the
     * same. What changes is the spread around it. The largest point (80px across) earns its
     * label at .35; the smallest (20px across) waits for 1.4, which the zoom controls can reach
     * but only near their top end.
     *
     * Read against node.size — the animated value — rather than targetSize, so the threshold
     * tracks the circle actually on screen. */
    var LABEL_MIN_RADIUS_PX = 14;

    function labelScaleThreshold(node) {
      return LABEL_MIN_RADIUS_PX / Math.max(1, node.size / 2);
    }

    function graphPaintNodes() {
      if (!sim) return;
      var focus = sim.graph.selected ? sim.neighbors(sim.graph.selected) : null;
      sim.nodes.forEach(function (node) {
        var elements = graphEls.get(node.id);
        if (!elements) return;
        var sizeDelta = node.targetSize - node.size;
        node.size += sizeDelta * .14;
        var opacityDelta = node.targetOpacity - node.opacity;
        node.opacity += opacityDelta * .18;
        elements.wrap.style.left = node.x + "px";
        elements.wrap.style.top = node.y + "px";
        elements.wrap.style.opacity = node.opacity.toFixed(3);
        elements.wrap.style.setProperty("--size", node.size + "px");
        var focused = sim.graph.selected
          && (node.id === sim.graph.selected || focus.one.has(node.id));
        // The selected point always shows its label: it is the one the learner just picked,
        // and answering "what did I click" must not depend on the zoom.
        //
        // Its neighbours do NOT get a pass. They are held to the same size rule as everything
        // else, which is the whole point of the rule — a large neighbour earns its label at
        // this zoom and a small one waits until the learner zooms in. They are still marked as
        // related, but through weight rather than by overriding legibility: a heavier label
        // than the rest, still subject to the same threshold.
        var labelVisible = node.id === sim.graph.selected
          || sim.graph.hover === node.id
          || graphView.scale >= labelScaleThreshold(node);
        var labelWeight = focused && node.id !== sim.graph.selected ? .7 : 1;
        elements.label.style.opacity = (labelVisible ? node.opacity * labelWeight : 0).toFixed(3);
        elements.meta.style.opacity = ((graphView.scale > .84 || node.id === sim.graph.selected ? .9 : 0) * node.opacity).toFixed(3);
      });
    }

    function graphRenderFrame() {
      if (!sim) return;
      graphPaintNodes();
      var activeEdges = sim.visibleEdges();
      var visibleSet = new Set(activeEdges);
      sim.computePortSlots(activeEdges);
      // Vector-effect cannot rescue strokes from an ancestor CSS transform, so
      // the render keeps line weight and dash rhythm constant on screen by
      // pre-dividing them by the zoom. Without this a fit view of a wide graph
      // draws 0.4px lines and the relations simply vanish.
      graphPathScaled = 1 / Math.max(.2, graphView.scale || 1);
      graphLastPaintedScale = graphView.scale;
      graphEdgeEls.forEach(function (item) {
        var edge = item.edge;
        if (!visibleSet.has(edge)) {
          // A relation hidden by type or by the weight budget is not a layout
          // constraint either, so it must not leave a stale path painted on the
          // canvas; it comes back the moment the legend or the budget allows.
          item.path.style.display = "none";
          return;
        }
        item.path.style.display = "";
        var a = sim.byId.get(edge.s);
        var b = sim.byId.get(edge.t);
        var style = sim.edgeStyle(edge);
        var edgeFocus = 1;
        if (sim.graph.selected) {
          edgeFocus = (edge.s === sim.graph.selected || edge.t === sim.graph.selected) ? 1
            : (a.focusWeight >= .48 && b.focusWeight >= .48) ? .38 : .07;
        }
        var opacity = Math.min(a.opacity, b.opacity) * edgeFocus * style.baseOpacity;
        item.path.setAttribute("d", sim.edgePath(edge));
        item.path.style.opacity = opacity.toFixed(3);
        item.path.style.strokeWidth = (style.width * graphPathScaled) + "px";
        if (edge.type === "contrast") {
          item.path.style.strokeDasharray = (6 * graphPathScaled) + " " + (5 * graphPathScaled);
        } else if (edge.type === "legacy") {
          item.path.style.strokeDasharray = (2 * graphPathScaled) + " " + (6 * graphPathScaled);
        } else {
          item.path.style.strokeDasharray = "";
        }
      });
      graphNotePaint("full");
      graphRenderRelations();
    }

    function graphFrame() {
      graphFrameHandle = null;
      if (!sim || graphDisposed) return;
      if (sim.failed) {
        graphFailureShow(sim.error);
        return;
      }
      var frameStarted = nowMs();
      var wasSolving = sim.graph.alpha > 0;
      // One physics step per frame is plenty for a normal pool; a couple of
      // hundred nodes get a few steps per frame so the settle finishes in a
      // sensible wall-clock time instead of a minute of near-static frames.
      var steps = sim.nodes.length > 120 ? 3 : 1;
      while (steps > 0 && sim.graph.alpha > 0) {
        sim.tick();
        steps -= 1;
        if (sim.failed) {
          graphFailureShow(sim.error);
          return;
        }
      }
      // Exactly one fit, after the first settle.
      //
      // The flag is armed by create() alone, so a reheat from a control cannot arm it. That is
      // the whole difference between "the view finds the graph once it has stopped moving" and
      // "the view jumps every time you touch the spacing control": the first is what the build
      // needs, the second was the bug — measured, one slide left the camera at 0.211 having
      // started at 0.313, and the picture also re-centred.
      //
      // Fitting on the seat instead of on the settled layout is not an option either: measured
      // that way the graph overflowed the canvas at 112% of its width at load.
      if (sim.graph.settled && sim.graph.autoFitAfterSettle && !graphView.userMoved) {
        sim.graph.autoFitAfterSettle = false;
        graphAutoFitInFrame = true;
        graphFit();
        graphAutoFitInFrame = false;
      }
      if (wasSolving !== (sim.graph.alpha > 0)) {
        graphSolver(sim.graph.alpha > 0);
        graphUpdateGapLegend();
      } else if (wasSolving) {
        graphUpdateGapLegend();
      }
      // Paint every frame, unless the previous frames were running long.
      //
      // This used to be a fixed stride by point count: skip every eighth frame above 120 points,
      // every twelfth above 300. Two things were wrong with that. It was written when the
      // physics ran on this thread and a skipped paint bought more solve per second — the
      // physics is in a worker now, so a skipped paint buys nothing, it only makes the picture
      // older. And a point count is a bad proxy for cost: it cannot tell an expensive graph from
      // a cheap one, so the threshold that protects a slow renderer makes a fast one stutter.
      //
      // Measured on 习概 (192 points): the browser ran at 59.7 frames a second while positions
      // changed every 137ms — 8.2 frames, the stride exactly. The learner's words were "it
      // settles quickly but there is no smooth slide, it just jumps".
      //
      // The cost is a smoothed measurement of how long a whole frame takes, paint included, so
      // the loop settles at whatever rate the machine can actually sustain: a fast renderer
      // never skips, a slow one skips only as often as it must.
      var solving = sim.graph.alpha > 0;
      // 20ms against a 60fps budget of 16.7ms: a machine that is comfortably keeping up never
      // trips it, and one that is not starts skipping rather than falling further behind. The
      // threshold sits above one frame on purpose — sitting exactly on the budget would make the
      // loop oscillate across it, painting and skipping in alternation.
      //
      // Only while solving. An idle graph has nothing to gain from a skipped paint and everything
      // to lose: the frame after a solve has to show the final layout, and skipping there would
      // leave the loop alive with nothing drawn.
      var overBudget = solving && graphFrameCostMs !== null && graphFrameCostMs > 20;
      var paintNow = !overBudget && !(graphTideState.reduced && solving);
      if (!paintNow) graphRenderDirty = true;
      if (paintNow) {
        graphRenderFrame();
        graphRenderDirty = false;
      }
      graphTideSurge(solving ? .06 : 0);
      // Feed the smoothed frame cost that decides whether the next frame paints. The cost
      // includes the paint itself, so a renderer that cannot keep up raises it, which skips the
      // next paint, which lowers it again — the loop settles where the paint just fits.
      var frameCost = nowMs() - frameStarted;
      graphFrameCostMs = graphFrameCostMs === null
        ? frameCost
        : graphFrameCostMs * .82 + frameCost * .18;
      // keep animating only while the solver runs or a frame was requested;
      // interactions call graphEnsureLoop() again when they change something
      if (solving || graphRenderDirty) graphEnsureLoop();
    }

    function graphEnsureLoop() {
      if (graphDisposed || !graphPhysicsAvailable || (sim && sim.failed)) return;
      if (graphFrameHandle === null) graphFrameHandle = requestAnimationFrame(graphFrame);
    }

    /* Anything that changes what the canvas should show marks it dirty through
     * here. Setting the flag alone is not enough: the loop parks itself once the
     * solver settles, and a parked loop would only repaint on the next
     * unrelated interaction (selection, hover and zoom all hit this). */
    function graphMarkDirty() {
      graphRenderDirty = true;
      graphEnsureLoop();
    }

    /* ---- ambient layer: paper-styled chroma tide, lower-left -> upper-right ---- */

    var graphTideState = { boost: 0, live: false, frame: null, reduced: false };
    var graphTideCtx = null;
    var graphTideSize = { w: 0, h: 0 };
    var graphTideRibbons = [
      { offset: -240, amp: 16, wave: 170, laneGap: 34, lanes: 2, step: 34, speed: 32, dotBase: 2.2, dotAmp: 4.0, alpha: .10, color: [195, 161, 40], phase: .3 },
      { offset: -130, amp: 19, wave: 210, laneGap: 37, lanes: 3, step: 36, speed: 38, dotBase: 2.3, dotAmp: 4.8, alpha: .12, color: [36, 87, 197], phase: 1.2 },
      { offset: 0, amp: 22, wave: 235, laneGap: 40, lanes: 4, step: 39, speed: 44, dotBase: 2.7, dotAmp: 5.8, alpha: .115, color: [214, 69, 61], phase: 2.5 },
      { offset: 135, amp: 19, wave: 205, laneGap: 37, lanes: 3, step: 36, speed: 36, dotBase: 2.3, dotAmp: 4.8, alpha: .12, color: [36, 87, 197], phase: 3.8 },
      { offset: 245, amp: 16, wave: 175, laneGap: 33, lanes: 2, step: 33, speed: 29, dotBase: 2.1, dotAmp: 3.9, alpha: .10, color: [195, 161, 40], phase: 5.1 },
    ];

    function graphTideHash(value) {
      var x = (value | 0) + 0x6D2B79F5;
      x = Math.imul(x ^ (x >>> 15), x | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    }

    function graphTideSurge(amount) {
      graphTideState.boost = Math.max(graphTideState.boost, amount);
    }

    function graphTideResize() {
      if (!graphTide || !graphTideCtx) return;
      var rect = graphCanvas.getBoundingClientRect();
      var w = Math.max(1, Math.round(rect.width));
      var h = Math.max(1, Math.round(rect.height));
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      graphTide.width = Math.round(w * dpr);
      graphTide.height = Math.round(h * dpr);
      graphTide.style.width = w + "px";
      graphTide.style.height = h + "px";
      graphTideCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      graphTideSize = { w: w, h: h };
    }

    function graphTideNodeMask(x, y, w, h) {
      var mask = 1;
      if (!sim) return mask;
      for (var i = 0; i < sim.nodes.length; i += 1) {
        var node = sim.nodes[i];
        if (!node.visible || node.opacity < .06) continue;
        var sx = graphView.panX + node.x * graphView.scale;
        var sy = graphView.panY + node.y * graphView.scale;
        var core = Math.max(48, node.size * graphView.scale * .84) + 18;
        var fade = core + 92;
        var dist = Math.hypot(x - sx, y - sy);
        if (dist <= core) return .02;
        if (dist < fade) mask = Math.min(mask, .02 + .98 * (dist - core) / (fade - core));
      }
      return mask;
    }

    function graphTideEdgeMask(x, y, w, h) {
      var ex = Math.min(1, x / 108, (w - x) / 108);
      var ey = Math.min(1, y / 84, (h - y) / 84);
      return Math.max(0, Math.min(1, Math.min(ex, ey)));
    }

    function graphTideDraw(t) {
      var ctx = graphTideCtx;
      var w = graphTideSize.w;
      var h = graphTideSize.h;
      if (!ctx || !w || !h) return;
      ctx.clearRect(0, 0, w, h);
      var SQ = Math.sqrt(.5);
      var DIR = { x: SQ, y: -SQ };
      var NRM = { x: SQ, y: SQ };
      var TAU = Math.PI * 2;
      var boost = graphTideState.boost;
      var center = { x: w * .5, y: h * .56 };

      graphTideRibbons.forEach(function (ribbon, bandIndex) {
        var diag = Math.hypot(w, h);
        var travel = t * ribbon.speed * (1 + boost * 1.55);
        var span = diag + 320;
        var cols = Math.ceil(span / ribbon.step) + 8;
        for (var lane = 0; lane < ribbon.lanes; lane += 1) {
          var laneOffset = ribbon.offset + (lane - (ribbon.lanes - 1) / 2) * ribbon.laneGap;
          var alongPhase = lane * .58 + bandIndex * .77;
          for (var i = -4; i < cols; i += 1) {
            var seed = bandIndex * 100000 + lane * 10000 + i;
            var u = -span / 2 + i * ribbon.step + (travel % (ribbon.step * 3));
            var wave = Math.sin((u / ribbon.wave) * TAU + ribbon.phase + alongPhase + t * .9) * ribbon.amp;
            var cross = laneOffset + wave;
            var x = center.x + DIR.x * u + NRM.x * cross;
            var y = center.y + DIR.y * u + NRM.y * cross;
            if (x < -34 || x > w + 34 || y < -34 || y > h + 34) continue;
            var local = Math.sin((u / (ribbon.wave * .72)) * TAU + ribbon.phase * 1.35 + t * 1.65 + lane * .45) * .5 + .5;
            var pulse = Math.sin(t * 1.35 + lane * .82 + i * .13 + ribbon.phase) * .5 + .5;
            var radius = (ribbon.dotBase + ribbon.dotAmp * (.24 + .76 * local))
              * (.87 + .22 * pulse) * (1 + boost * .38);
            var mask = graphTideNodeMask(x, y) * graphTideEdgeMask(x, y, w, h);
            if (mask < .018) continue;
            var jitterX = (graphTideHash(seed + 11) - .5) * 1.7;
            var jitterY = (graphTideHash(seed + 17) - .5) * 1.9;
            var alpha = ribbon.alpha * mask * (.74 + .34 * graphTideHash(seed + 29)) * (1 + boost * .16);
            ctx.beginPath();
            ctx.fillStyle = "rgba(" + ribbon.color[0] + "," + ribbon.color[1] + "," + ribbon.color[2] + "," + alpha.toFixed(4) + ")";
            ctx.arc(x + jitterX, y + jitterY, radius, 0, TAU);
            ctx.fill();
            if (radius > 5.15) {
              ctx.beginPath();
              ctx.fillStyle = "rgba(" + ribbon.color[0] + "," + ribbon.color[1] + "," + ribbon.color[2] + "," + (alpha * .11).toFixed(4) + ")";
              ctx.arc(x + jitterX, y + jitterY, radius * 1.7, 0, TAU);
              ctx.fill();
            }
          }
        }
      });

      var dustCount = Math.max(18, Math.round((w * h) / 21000));
      var palette = [[36, 87, 197], [195, 161, 40], [214, 69, 61]];
      for (var d = 0; d < dustCount; d += 1) {
        var dustSeed = 700000 + d;
        var dx = (graphTideHash(dustSeed) * w + t * 5 * (graphTideHash(dustSeed + 1) - .5) + w) % w;
        var dy = (graphTideHash(dustSeed + 2) * h + t * 3 * (graphTideHash(dustSeed + 3) - .5) + h) % h;
        var dustMask = graphTideNodeMask(dx, dy) * graphTideEdgeMask(dx, dy, w, h);
        if (dustMask < .03) continue;
        var color = palette[Math.floor(graphTideHash(dustSeed + 4) * palette.length)];
        var dustR = .8 + graphTideHash(dustSeed + 5) * 1.6;
        var dustA = (.018 + graphTideHash(dustSeed + 6) * .018) * (1 + boost * .08) * dustMask;
        ctx.beginPath();
        ctx.fillStyle = "rgba(" + color[0] + "," + color[1] + "," + color[2] + "," + dustA.toFixed(4) + ")";
        ctx.arc(dx, dy, dustR, 0, TAU);
        ctx.fill();
      }

      var markAlpha = .03 * (1 + boost * .35);
      var marks = [
        [w * .18, h * .82, 18, 0, "36,87,197"],
        [w * .49, h * .50, 0, 16, "214,69,61"],
        [w * .82, h * .18, 14, 0, "195,161,40"],
      ];
      for (var m = 0; m < marks.length; m += 1) {
        var mark = marks[m];
        var wobble = Math.sin(t * .32 + m * 1.7) * 1.8;
        var markMask = graphTideNodeMask(mark[0], mark[1]);
        ctx.strokeStyle = "rgba(" + mark[4] + "," + (markAlpha * markMask).toFixed(4) + ")";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(mark[0] - mark[2] / 2, mark[1] - mark[3] / 2 + wobble);
        ctx.lineTo(mark[0] + mark[2] / 2, mark[1] + mark[3] / 2 + wobble);
        ctx.stroke();
      }
      graphTideState.boost *= graphTideState.reduced ? 0 : .968;
      if (graphTideState.boost < .008) graphTideState.boost = 0;
    }

    function graphTideFrame(now) {
      graphTideState.frame = null;
      if (!graphTideState.live) return;
      // While a large pool solves, the ambient canvas would double the paint
      // bill of every frame for no information; it resumes on settle.
      var solvingLarge = sim && sim.nodes.length > 120 && sim.graph.alpha > 0;
      if (!solvingLarge) graphTideDraw(graphTideState.reduced ? 0 : now / 1000);
      if (!graphTideState.reduced) graphTideState.frame = requestAnimationFrame(graphTideFrame);
    }

    function graphStartTide() {
      graphTideState.reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
      if (!graphTide || graphTideState.live) return;
      graphTideCtx = graphTide.getContext && graphTide.getContext("2d", { alpha: true });
      if (!graphTideCtx) return;
      graphTideState.live = true;
      if (typeof ResizeObserver === "function") {
        graphResizeObserver = new ResizeObserver(function () {
          graphTideResize();
          graphMarkDirty();
          graphEnsureLoop();
        });
        graphResizeObserver.observe(graphCanvas);
      }
      graphResizeHandler = function () {
        graphTideResize();
        graphMarkDirty();
        graphEnsureLoop();
      };
      window.addEventListener("resize", graphResizeHandler);
      graphTideResize();
      if (graphTideState.reduced) graphTideFrame(0);
      else graphTideState.frame = requestAnimationFrame(graphTideFrame);
    }

    /* ---- interactions ---- */

    function graphPointerToStage(event) {
      var rect = graphCanvas.getBoundingClientRect();
      return {
        x: (event.clientX - rect.left - graphView.panX) / graphView.scale,
        y: (event.clientY - rect.top - graphView.panY) / graphView.scale,
      };
    }

    var graphPanDrag = null;
    var graphCanvasPress = null;

    graphCanvas.addEventListener("pointerdown", function (event) {
      if (event.target.closest && event.target.closest(".node-wrap, .controls, .zoom, .legend")) return;
      graphCanvasPress = { x: event.clientX, y: event.clientY };
      graphPanDrag = {
        x: event.clientX, y: event.clientY,
        panX: graphView.panX, panY: graphView.panY,
      };
      graphView.userMoved = true;
      if (graphCanvas.setPointerCapture && event.pointerId !== undefined) {
        graphCanvas.setPointerCapture(event.pointerId);
      }
    });

    graphCanvas.addEventListener("pointermove", function (event) {
      if (!sim) return;
      if (sim.graph.drag) {
        var dragged = sim.byId.get(sim.graph.drag.id);
        var point = graphPointerToStage(event);
        dragged.x = point.x;
        dragged.y = point.y;
        dragged.vx = 0;
        dragged.vy = 0;
        dragged.anchorX = point.x;
        dragged.anchorY = point.y;
        // No reheat per move. pointermove runs at 60-120Hz, and reheat() bumps
        // controlRevision, which makes the Worker drop every snapshot older than it
        // (graph-physics.js:299) — so reheating here froze the rest of the graph for
        // the whole drag. The coordinates already reach the Worker through the step
        // controls (controlsFor carries x/y and the anchor marks the node as dragged),
        // so the only thing a move needs is to wake a solver that has gone to sleep.
        if (sim.graph.alpha <= 0) sim.reheat(.34, false);
        graphSolver(true);
        graphEnsureLoop();
        return;
      }
      if (graphPanDrag) {
        graphView.panX = graphPanDrag.panX + event.clientX - graphPanDrag.x;
        graphView.panY = graphPanDrag.panY + event.clientY - graphPanDrag.y;
        graphApplyView();
      }
    });

    graphCanvas.addEventListener("pointerup", function () {
      if (sim && sim.graph.drag) {
        var node = sim.byId.get(sim.graph.drag.id);
        var elements = graphEls.get(node.id);
        if (elements) elements.wrap.classList.remove("dragging");
        node.anchorX = node.x;
        node.anchorY = node.y;
        sim.reheat(.52, false);
        graphSolver(true);
        graphEnsureLoop();
      }
      sim && (sim.graph.drag = null);
      graphPanDrag = null;
    });

    graphCanvas.addEventListener("click", function (event) {
      if (!sim) return;
      if (event.target !== graphCanvas && event.target !== graphStage) {
        // A node button, a control, the legend or the zoom buttons. Not our business — but the
        // press record is cleared so it cannot leak into a later click on empty space and
        // suppress it with a stale travel distance.
        graphCanvasPress = null;
        return;
      }
      // A click always follows a drag, because the browser synthesises one when the press and
      // the release land on the same element — so panning the canvas used to clear the
      // selection every time. The learner nudged the view to read something and lost the point
      // they had opened; "drag" is not "click on empty space". The node buttons already had this
      // travel test (graphNodePress); the canvas itself did not.
      if (graphCanvasPress) {
        var travelled = Math.hypot(event.clientX - graphCanvasPress.x, event.clientY - graphCanvasPress.y);
        graphCanvasPress = null;
        if (travelled > 4) return;
      }
      sim.graph.selected = null;
      selectedGraphKpId = null;
      graphApplyVisibility();
      graphRenderDetail(null);
      graphMarkDirty();
    });

    graphCanvas.addEventListener("wheel", function (event) {
      event.preventDefault();
      var old = graphView.scale;
      graphView.scale = Math.max(.38, Math.min(1.6, graphView.scale * (event.deltaY > 0 ? .92 : 1.08)));
      var rect = graphCanvas.getBoundingClientRect();
      var mx = event.clientX - rect.left;
      var my = event.clientY - rect.top;
      graphView.panX = mx - (mx - graphView.panX) * (graphView.scale / old);
      graphView.panY = my - (my - graphView.panY) * (graphView.scale / old);
      graphView.userMoved = true;
      graphApplyView();
    }, { passive: false });

    if (graphViews) {
      graphViews.addEventListener("click", function (event) {
        var view = event.target.dataset ? event.target.dataset.view : null;
        if (!view || !sim) return;
        graphViews.querySelectorAll("button").forEach(function (button) {
          button.classList.toggle("active", button.dataset.view === view);
        });
        sim.setView(view);
        sim.updateProjection();
        sim.nodes.forEach(graphUpdateNodeAppearance);
        graphSolver(true);
        graphEnsureLoop();
        graphTideSurge(.95);
      });
    }

    var graphLegend = document.getElementById("graph-legend");
    if (graphLegend) {
      graphLegend.addEventListener("click", function (event) {
        var item = event.target && event.target.closest
          ? event.target.closest(".legend-item")
          : event.target;
        if (!item || !sim || !item.dataset) return;
        var type = item.dataset.edgeType;
        if (!type) return;
        if (graphHiddenEdgeTypes[type]) delete graphHiddenEdgeTypes[type];
        else graphHiddenEdgeTypes[type] = true;
        graphSyncLegend();
        graphApplyEdgeVisibility();
        var labels = { prereq: "先修", related: "相关", apply: "应用", contrast: "对比", legacy: "隐含关联" };
        graphToastShow((graphHiddenEdgeTypes[type] ? "已隐藏" : "已显示") + (labels[type] || type));
        graphView.userMoved = false;
        graphSolver(true);
        graphEnsureLoop();
        graphTideSurge(.45);
      });
    }

    if (graphFilters) {
      graphFilters.addEventListener("click", function (event) {
        var key = event.target.dataset ? event.target.dataset.filter : null;
        if (!key || !sim) return;
        if (key === "all") sim.graph.filters.clear();
        else if (sim.graph.filters.has(key)) sim.graph.filters.delete(key);
        else sim.graph.filters.add(key);
        graphFilters.querySelectorAll(".chip").forEach(function (chip) {
          chip.classList.toggle("active", chip.dataset.filter === "all"
            ? sim.graph.filters.size === 0
            : sim.graph.filters.has(chip.dataset.filter));
        });
        graphApplyVisibility();
        if (sim.graph.selected && !sim.byId.get(sim.graph.selected).visible) {
          sim.graph.selected = null;
          selectedGraphKpId = null;
          graphApplyVisibility();
          graphRenderDetail(null);
        }
        graphView.userMoved = false;
        sim.reheat(.88, true);
        graphSolver(true);
        graphEnsureLoop();
        graphTideSurge(.45);
      });
    }

    if (graphGravity) {
      graphGravity.addEventListener("input", function () {
        if (!sim) return;
        graphGravityValue.textContent = graphGravity.value;
        sim.graph.gravity = GraphPhysics.clamp(Number(graphGravity.value) || 0, 0, 100);
        graphView.userMoved = false;
        sim.reheat(.62, true);
        graphSolver(true);
        graphEnsureLoop();
      });
    }

    if (graphSearch) {
      graphSearch.addEventListener("input", function () {
        if (!sim) return;
        var query = graphSearch.value.trim().toLowerCase();
        if (!query) return;
        var hit = sim.nodes.find(function (node) {
          return node.title.toLowerCase().indexOf(query) >= 0
            || String(node.id).toLowerCase().indexOf(query) >= 0;
        });
        if (!hit) return;
        if (sim.graph.filters.size && !sim.graph.filters.has(hit.state)) {
          sim.graph.filters.clear();
          if (graphFilters) {
            graphFilters.querySelectorAll(".chip").forEach(function (chip) {
              chip.classList.toggle("active", chip.dataset.filter === "all");
            });
          }
          graphApplyVisibility();
        }
        graphSelect(hit.id, true);
      });
    }

    if (graphFocusBtn) {
      graphFocusBtn.addEventListener("click", function () {
        if (sim && sim.graph.selected) graphCenterOn(sim.byId.get(sim.graph.selected), true);
      });
    }
    if (graphFitBtn) {
      graphFitBtn.addEventListener("click", function () {
        graphView.userMoved = false;
        graphFit();
      });
    }
    if (graphZoomIn) {
      graphZoomIn.addEventListener("click", function () {
        graphView.scale = Math.min(1.6, graphView.scale + .09);
        graphView.userMoved = true;
        graphApplyView();
      });
    }
    if (graphZoomOut) {
      graphZoomOut.addEventListener("click", function () {
        graphView.scale = Math.max(.38, graphView.scale - .09);
        graphView.userMoved = true;
        graphApplyView();
      });
    }
    if (graphZoomReset) {
      graphZoomReset.addEventListener("click", function () {
        graphView.scale = 1;
        graphView.panX = 0;
        graphView.panY = 0;
        graphView.userMoved = true;
        graphApplyView();
      });
    }

    if (!graphPhysicsAvailable) {
      if (typeof GraphPhysics !== "undefined") GraphPhysics = undefined;
      graphFailureShow("图谱计算无法启动：浏览器不支持 Worker，或图谱资源加载失败。请刷新页面，或使用支持 Worker 的浏览器。");
    } else {
      graphStartTide();
      api("/graph/model").then(function (model) {
        if (graphDisposed) return;
        graphBuild(model);
        graphStartTide();
        graphEnsureLoop();
      }).catch(function (error) {
        if (graphDisposed) return;
        if (typeof console !== "undefined" && console.error) {
          console.error("graph: model render failed", error && error.stack ? error.stack : error);
        }
        if (graphCanvas) graphCanvas.textContent = "图谱暂时无法读取。";
      });
    }
  }

  return function disposeGraphPage() {
    graphDisposed = true;
    if (graphFrameHandle !== null && window.cancelAnimationFrame) {
      window.cancelAnimationFrame(graphFrameHandle);
    }
    if (graphTideState.frame !== null && window.cancelAnimationFrame) {
      window.cancelAnimationFrame(graphTideState.frame);
    }
    graphTideState.live = false;
    if (graphResizeObserver) graphResizeObserver.disconnect();
    if (graphResizeHandler) window.removeEventListener("resize", graphResizeHandler);
    if (graphToastTimer !== null) clearTimeout(graphToastTimer);
    if (sim && typeof sim.dispose === "function") sim.dispose();
    currentGraphContext = function () { return null; };
    selectedGraphKpId = null;
  };
  }

  function mountPracticeViews() {
  var pageGeneration = middlePageGeneration;
  function routeIsCurrent() { return pageGeneration === middlePageGeneration; }
  /* ---------- practice flow ---------- */

  practiceRuntime = PracticeFlow.start({
    api: api,
    post: post,
    patch: patch,
    store: store,
    load: load,
    showRatingEnabled: showRatingEnabled,
    renderMath: renderMath,
    escapeHtml: escapeHtml,
    richText: richText,
    navigate: navigateMiddle,
    selectedKpIds: selectedKpIds,
    saveSelectedKpIds: saveSelectedKpIds,
    recordRecent: recordRecent,
  });
  currentProblem = practiceRuntime.currentProblem;
  session = practiceRuntime.session;
  visiblePracticeImages = practiceRuntime.visiblePracticeImages;
  draftAnswer = practiceRuntime.draftAnswer;
  draftNote = practiceRuntime.draftNote;
  practiceSelectionContext = practiceRuntime.selectionContext
    || function () { return {}; };

  /* ---------- saved papers ---------- */

  var practiceSetList = document.getElementById("practice-set-list");
  var paperOpenKey = "wb_paper_open_" + WS;

  // A card folds away its problem list, and the fold survives the reload that
  // every edit does — otherwise moving one item shut the paper being edited.
  function restorePaperFolds() {
    var open = load(paperOpenKey, {});
    Array.prototype.forEach.call(
      practiceSetList.querySelectorAll(".practice-set-card"),
      function (card) {
        var body = card.querySelector(".practice-set-card-body");
        if (!body) return;
        if (open[card.dataset.practiceSetId]) body.open = true;
        body.addEventListener("toggle", function (event) {
          if (event.target !== body) return;
          var state = load(paperOpenKey, {});
          state[card.dataset.practiceSetId] = body.open;
          store(paperOpenKey, state);
        });
      });
  }

  function practiceSetStatus(card, message) {
    if (!routeIsCurrent()) return;
    var status = card.querySelector(".practice-set-status");
    if (!status) return;
    status.textContent = message || "";
    status.classList.toggle("hidden", !message);
  }

  function reloadPage() {
    if (routeIsCurrent()) refreshMiddle();
  }

  function downloadPaper(title, suffix, text) {
    if (typeof Blob === "undefined" || !window.URL || !window.URL.createObjectURL) return;
    var blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    var url = window.URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = (title || "practice-set").replace(/[\\/:*?"<>|]+/g, "-") + suffix;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  if (practiceSetList) {
    restorePaperFolds();
    practiceSetList.addEventListener("click", function (event) {
      var card = event.target.closest && event.target.closest(".practice-set-card");
      if (!card) return;
      var practiceSetId = card.dataset.practiceSetId;
      layout.dataset.practiceSetId = practiceSetId;
      var button = event.target.closest && event.target.closest("button");
      if (!button) return;
      // The card head is a <summary>: a control click must not also fold the paper.
      event.preventDefault();
      var encoded = encodeURIComponent(practiceSetId);

      if (button.hasAttribute("data-set-start")) {
        navigateMiddle("/w/" + encodeURIComponent(WS) + "/practice?paper=" + encoded);
        return;
      }

      if (button.hasAttribute("data-set-rename")) {
        var heading = card.querySelector("h2");
        var title = window.prompt
          ? window.prompt("试卷名称", heading ? heading.textContent : "")
          : null;
        if (!title || !title.trim()) return;
        patch("/practice-sets/" + encoded, { title: title.trim() })
          .then(reloadPage)
          .catch(function (error) { if (routeIsCurrent()) practiceSetStatus(card, error.message); });
        return;
      }

      if (button.hasAttribute("data-set-delete")) {
        if (window.confirm && !window.confirm("删除这张试卷？做题记录不会被删除。")) return;
        api("/practice-sets/" + encoded, { method: "DELETE" })
          .then(reloadPage)
          .catch(function (error) { if (routeIsCurrent()) practiceSetStatus(card, error.message); });
        return;
      }

      if (button.hasAttribute("data-set-export")) {
        api("/practice-sets/" + encoded + "/render").then(function (rendered) {
          if (!routeIsCurrent()) return;
          var heading = card.querySelector("h2");
          var title = heading ? heading.textContent : practiceSetId;
          downloadPaper(title, "-problem-set.md", rendered.practice_set || "");
          downloadPaper(title, "-solutions.md", rendered.solutions || "");
        }).catch(function (error) { if (routeIsCurrent()) practiceSetStatus(card, error.message); });
        return;
      }

    });
  }

  var recordsCenter = document.querySelector(".records-center");
  if (recordsCenter) {
    recordsCenter.addEventListener("click", function (event) {
      var view = event.target.closest && event.target.closest("[data-run-view]");
      if (view) {
        navigateMiddle("/w/" + encodeURIComponent(WS) + "/practice?run=" + encodeURIComponent(view.dataset.runView));
        return;
      }
      var button = event.target.closest && event.target.closest("[data-run-replay]");
      if (!button) return;
      var runId = encodeURIComponent(button.dataset.runReplay);
      button.disabled = true;
      post("/practice/runs/" + runId + "/replay", {}).then(function () {
        if (routeIsCurrent()) navigateMiddle("/w/" + encodeURIComponent(WS) + "/practice");
      }).catch(function (error) {
        if (!routeIsCurrent()) return;
        button.disabled = false;
        if (error.message === "an unfinished practice already exists"
            && window.confirm
            && window.confirm("当前还有一轮练习没有完成。重新开始会清除旧进度，继续吗？")) {
          button.disabled = true;
          post("/practice/runs/" + runId + "/replay", { replace: true }).then(function () {
            if (routeIsCurrent()) navigateMiddle("/w/" + encodeURIComponent(WS) + "/practice");
          }).catch(function (retryError) {
            if (!routeIsCurrent()) return;
            button.disabled = false;
            if (window.alert) window.alert(retryError.message || "无法重新开始");
          });
        } else if (window.alert) {
          window.alert(error.message || "无法重新开始");
        }
      });
    });
  }

  /* ---------- goals ---------- */

  var recalculatePlan = document.getElementById("recalculate-plan");
  if (recalculatePlan) {
    recalculatePlan.addEventListener("click", function () {
      recalculatePlan.disabled = true;
      post("/plan/recalculate", {}).then(function () {
        if (!routeIsCurrent()) return;
        recalculatePlan.disabled = false;
        refreshMiddle();
      }).catch(function () { if (routeIsCurrent()) recalculatePlan.disabled = false; });
    });
  }

  var goalForm = document.getElementById("goal-form");
  if (goalForm) {
    var goalIdField = document.getElementById("goal-id");
    var goalSubmit = document.getElementById("goal-submit");
    var goalCancel = document.getElementById("goal-cancel");
    var goalSummary = document.getElementById("goal-editor-summary");
    var goalNl = document.getElementById("goal-nl");
    var goalAssistSend = document.getElementById("goal-assist-send");

    function goalStatus(text) {
      if (!routeIsCurrent()) return;
      var status = document.getElementById("goal-form-status");
      if (status) status.textContent = text || "";
    }

    function resetGoalForm() {
      if (goalIdField) goalIdField.value = "";
      if (goalCancel) goalCancel.classList.add("hidden");
      if (goalSubmit) goalSubmit.textContent = "保存目标";
      if (goalSummary) goalSummary.textContent = "添加目标";
      goalForm.reset();
      goalStatus("");
    }

    function loadGoalIntoForm(card) {
      if (goalIdField) goalIdField.value = card.dataset.goalId || "";
      document.getElementById("goal-title").value = card.dataset.goalTitle || "";
      var kind = document.getElementById("goal-kind");
      if (kind) kind.value = card.dataset.goalKind || "stage";
      var startDate = document.getElementById("goal-start-date");
      if (startDate) startDate.value = card.dataset.goalStartDate || "";
      var deadline = document.getElementById("goal-deadline");
      if (deadline) deadline.value = card.dataset.goalDeadline || "";
      document.getElementById("goal-description").value = card.dataset.goalDescription || "";
      if (goalCancel) goalCancel.classList.remove("hidden");
      if (goalSubmit) goalSubmit.textContent = "保存修改";
      if (goalSummary) goalSummary.textContent = "修改目标";
      if (goalForm.parentElement && goalForm.parentElement.open === false) {
        goalForm.parentElement.open = true;
      }
      goalStatus("");
    }

    var goalCardsBox = document.getElementById("goal-cards");
    Array.prototype.forEach.call(goalCardsBox ? goalCardsBox.querySelectorAll(".goal-card") : [], function (card) {
      var edit = card.querySelector("[data-goal-edit]");
      if (edit) edit.addEventListener("click", function () { loadGoalIntoForm(card); });
      var remove = card.querySelector("[data-goal-delete]");
      if (remove) remove.addEventListener("click", function () {
        var id = card.dataset.goalId;
        if (!id || (window.confirm && !window.confirm("删除这个目标？"))) return;
        api("/goals/" + encodeURIComponent(id), { method: "DELETE" })
          .then(function () { if (routeIsCurrent()) refreshMiddle(); })
          .catch(function (error) { goalStatus("删除失败：" + (error.message || "未知错误")); });
      });
    });

    if (goalCancel) goalCancel.addEventListener("click", resetGoalForm);

    goalForm.addEventListener("submit", function (event) {
      if (event.preventDefault) event.preventDefault();
      var title = document.getElementById("goal-title");
      var kind = document.getElementById("goal-kind");
      var startDate = document.getElementById("goal-start-date");
      var deadline = document.getElementById("goal-deadline");
      var description = document.getElementById("goal-description");
      if (!title || !title.value.trim()) {
        goalStatus("请填写目标名称。");
        return;
      }
      if (startDate && deadline && startDate.value && deadline.value
          && startDate.value > deadline.value) {
        goalStatus("开始日期不能晚于截止日期。");
        return;
      }
      var payload = {
        title: title.value.trim(),
        kind: kind ? kind.value : "stage",
        start_date: startDate ? startDate.value : "",
        deadline: deadline ? deadline.value : "",
        description: description ? description.value.trim() : "",
      };
      var editing = goalIdField && goalIdField.value;
      var request = editing
        ? api("/goals/" + encodeURIComponent(goalIdField.value), {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          })
        : post("/goals", payload);
      request.then(function () {
        if (routeIsCurrent()) refreshMiddle();
      }).catch(function (error) {
        goalStatus("保存失败：" + (error.message || "未知错误"));
      });
    });

    function sendGoalAssist() {
      var text = goalNl ? goalNl.value.trim() : "";
      if (!text) {
        goalStatus("先用一句话写下你的目标。");
        return;
      }
      if (!(aiProviders || []).length) {
        goalStatus("暂无可用 Agent。请先配置一个提供方。");
        return;
      }
      if (aiSendPending) {
        goalStatus("Agent 请求仍在提交，请稍候。");
        return;
      }
      if (!aiConversation) {
        if (typeof aiShowProviderPicker === "function") aiShowProviderPicker();
        goalStatus("请先在右侧选择 Agent，再点一次「让 Agent 代填」。");
        return;
      }
      var body = aiContextBody(text);
      body.goal_intent = true;
      goalStatus("已发给 Agent，等待代填…");
      aiPostTurn(body)
        .catch(function (error) {
          goalStatus("发送失败：" + (error.message || "未知错误"));
        });
    }
    if (goalAssistSend) goalAssistSend.addEventListener("click", sendGoalAssist);
  }
  }

  /* ---------- AI column ---------- */

  var messages = document.getElementById("ai-messages");
  var aiInput = document.getElementById("ai-input");
  var aiSend = document.getElementById("ai-send");
  var aiStop = document.getElementById("ai-stop");
  var aiStatus = document.getElementById("ai-status");
  var aiConversation = load(AI_CONVERSATION_KEY, "");
  var aiSurfaceConversation = "";
  var aiConversationSequence = 0;
  var aiConversationLoadSequence = 0;
  var aiTurn = null;
  var aiSendPending = false;
  var aiProgressReadFailed = false;
  var aiLiveArtifactId = "";
  var aiPollTimer = null;
  var aiQueuePollTimer = null;
  var aiQueueEditingTurn = "";
  var aiQueueEdit = null;
  var aiQueueSnapshot = null;
  var aiQueueRenderedSignature = "";
  var aiQueueDragTurn = "";
  var aiQueueDragContext = null;
  var aiQueueFocusTurnId = "";
  var aiQueueFocusControl = null;
  var aiPollSequence = 0;
  var aiStreamingMessage = null;
  var aiExecutionPlan = null;
  var aiCurrentProvider = "";
  var aiPiActivities = {};
  var aiCurrentSubmissionId = "";
  var aiRecoveryContainer = null;
  var aiOutboxRenderedSignature = "";
  var aiRenderedDoneTurns = {};
  var aiHistoryReconciling = false;
  var aiCurrentPaperApproval = null;
  var aiPaperApprovalOwner = null;
  var aiPaperApprovalNotice = null;
  var aiPaperApprovalUnknownKey = "";
  var aiPaperApprovalInFlight = {};
  var aiPaperProposalCards = {};
  var AI_OUTBOX_PREFIX = "wb_ai_message_outbox_" + WS + "_";

  function aiPreviewRoute() {
    var location = window.location || {};
    return (location.pathname || "") + (location.search || "") + (location.hash || "");
  }

  function aiClearLiveArtifact() {
    sessionStorage.removeItem(AI_LIVE_ARTIFACT_KEY);
  }

  function aiForgetLiveArtifact() {
    aiLiveArtifactId = "";
    aiClearLiveArtifact();
  }

  function aiGetLiveArtifact(conversationId) {
    var marker = load(AI_LIVE_ARTIFACT_KEY, null);
    if (!marker) return null;
    if (!conversationId || marker.conversation_id !== conversationId
        || !marker.practice_set_id || marker.route !== aiPreviewRoute()) {
      aiForgetLiveArtifact();
      return null;
    }
    aiLiveArtifactId = marker.practice_set_id;
    return marker;
  }

  function aiSaveLiveArtifact(action) {
    if (!aiConversation || !action || !action.practice_set_id) return;
    aiLiveArtifactId = action.practice_set_id;
    store(AI_LIVE_ARTIFACT_KEY, {
      conversation_id: aiConversation,
      practice_set_id: action.practice_set_id,
      route: aiPreviewRoute(),
    });
  }

  function aiHasLiveArtifact(conversationId, practiceSetId) {
    var marker = aiGetLiveArtifact(conversationId);
    return !!(marker && marker.practice_set_id === practiceSetId);
  }

  if (aiConversation) aiGetLiveArtifact(aiConversation);
  else aiForgetLiveArtifact();

  function aiResetConversationRuntime(preserveLiveArtifactConversationId) {
    aiConversationSequence += 1;
    if (preserveLiveArtifactConversationId) {
      aiGetLiveArtifact(preserveLiveArtifactConversationId);
    } else {
      aiForgetLiveArtifact();
    }
    aiTurn = null;
    aiSendPending = false;
    aiProgressReadFailed = false;
    aiPollSequence = 0;
    if (aiPollTimer) clearTimeout(aiPollTimer);
    if (aiQueuePollTimer) clearTimeout(aiQueuePollTimer);
    aiPollTimer = null;
    aiQueuePollTimer = null;
    aiQueueEditingTurn = "";
    aiQueueEdit = null;
    aiQueueSnapshot = null;
    aiQueueRenderedSignature = "";
    aiQueueDragTurn = "";
    aiQueueDragContext = null;
    aiQueueFocusTurnId = "";
    aiQueueFocusControl = null;
    aiStreamingMessage = null;
    aiExecutionPlan = null;
    aiCurrentProvider = "";
    aiPiActivities = {};
    aiCurrentSubmissionId = "";
    aiRecoveryContainer = null;
    aiOutboxRenderedSignature = "";
    aiRenderedDoneTurns = {};
    aiHistoryReconciling = false;
    aiCurrentPaperApproval = null;
    aiPaperApprovalOwner = null;
    aiPaperApprovalNotice = null;
    aiPaperApprovalUnknownKey = "";
    aiPaperProposalCards = {};
    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.resetTurn) {
      AgentUISurfaces.resetTurn();
    }
    aiSetStatus("");
  }

  if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.setCollapseHandler) {
    AgentUISurfaces.setCollapseHandler(aiClearLiveArtifact);
  }
  if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.setArtifactPreviewHandler) {
    AgentUISurfaces.setArtifactPreviewHandler(function (action) {
      if (action && action.practice_set_id === aiLiveArtifactId) aiSaveLiveArtifact(action);
    });
  }

  function aiOutboxKey(conversationId) {
    return AI_OUTBOX_PREFIX + conversationId;
  }

  function aiReadOutbox(conversationId) {
    try {
      return JSON.parse(window.localStorage.getItem(aiOutboxKey(conversationId)) || "{}") || {};
    } catch (error) {
      return {};
    }
  }

  function aiWriteOutbox(conversationId, records) {
    try {
      if (Object.keys(records).length) {
        window.localStorage.setItem(aiOutboxKey(conversationId), JSON.stringify(records));
      } else {
        window.localStorage.removeItem(aiOutboxKey(conversationId));
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  function aiSaveOutbox(item) {
    var records = aiReadOutbox(item.conversation_id);
    records[item.submission_id] = item;
    return aiWriteOutbox(item.conversation_id, records);
  }

  function aiUpdateOutbox(conversationId, submissionId, update) {
    if (!submissionId) return;
    var records = aiReadOutbox(conversationId);
    if (!records[submissionId]) return;
    records[submissionId] = Object.assign({}, records[submissionId], update);
    aiWriteOutbox(conversationId, records);
  }

  function aiRemoveOutbox(conversationId, submissionId) {
    if (!submissionId) return;
    var records = aiReadOutbox(conversationId);
    delete records[submissionId];
    aiWriteOutbox(conversationId, records);
  }

  function aiNewSubmissionId() {
    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
  }

  function aiPrepareSubmission(body, existing) {
    var request = Object.assign({}, body || {});
    request.submission_id = request.submission_id || aiNewSubmissionId();
    var item = existing || {
      conversation_id: aiConversation,
      submission_id: request.submission_id,
      body: request,
      status: "sending",
      created_at: Date.now(),
    };
    item.body = request;
    item.status = "sending";
    return aiSaveOutbox(item) ? item : null;
  }

  function aiOutboxAction(item, label, callback, action) {
    var button = document.createElement("button");
    button.className = "outline sm";
    button.type = "button";
    button.textContent = label;
    if (action) button.dataset.action = action;
    var turnId = item.dataset && item.dataset.turnId;
    if (turnId) {
      button.dataset.turnId = turnId;
      button.addEventListener("focus", function () {
        aiQueueFocusControl = { turn_id: turnId, action: action };
      });
      button.addEventListener("blur", function () {
        if (aiQueueFocusControl && aiQueueFocusControl.turn_id === turnId
            && aiQueueFocusControl.action === action) aiQueueFocusControl = null;
      });
      if (item.queueControls) item.queueControls[action] = button;
    }
    button.addEventListener("click", callback);
    item.appendChild(button);
    return button;
  }

  function aiSyncOutboxWithHistory(record) {
    var conversationId = record.conversation_id || aiConversation;
    var outbox = aiReadOutbox(conversationId);
    var changed = false;
    Object.keys(outbox).forEach(function (submissionId) {
      var item = outbox[submissionId];
      var accepted = (record.messages || []).find(function (message) {
        return message.role === "user" && message.submission_id === submissionId;
      });
      if (accepted) {
        if (accepted.status === "done") {
          delete outbox[submissionId];
        } else if (accepted.status === "failed" || accepted.status === "cancelled") {
          item.status = "failed";
          item.turn_id = accepted.turn_id;
          item.error = accepted.error || "Agent 未能完成";
          if (typeof accepted.content === "string" && item.body) {
            item.body.message = accepted.content;
          }
          outbox[submissionId] = item;
        } else if (accepted.status === "running" || accepted.status === "queued"
                   || accepted.status === "waiting_for_stop") {
          item.status = "accepted";
          item.turn_id = accepted.turn_id;
          if (typeof accepted.content === "string" && item.body) {
            item.body.message = accepted.content;
          }
          outbox[submissionId] = item;
        }
        changed = true;
      } else if (item.status === "sending") {
        item.status = "unknown";
        outbox[submissionId] = item;
        changed = true;
      }
    });
    if (changed) aiWriteOutbox(conversationId, outbox);
    if (record.status === "running" && record.current_turn_id) {
      Object.keys(outbox).some(function (submissionId) {
        if (outbox[submissionId].turn_id === record.current_turn_id) {
          aiCurrentSubmissionId = submissionId;
          return true;
        }
        return false;
      });
    }
    return outbox;
  }

  function aiPendingMessages(record) {
    var pending = (record.messages || []).filter(function (message) {
      return message.role === "user"
        && message.status === "queued";
    });
    if (Array.isArray(record.queue_order)) {
      var positions = {};
      record.queue_order.forEach(function (turnId, index) {
        positions[String(turnId)] = index;
      });
      pending.sort(function (left, right) {
        var leftPosition = positions[String(left.turn_id)];
        var rightPosition = positions[String(right.turn_id)];
        if (leftPosition === undefined) return rightPosition === undefined ? 0 : 1;
        if (rightPosition === undefined) return -1;
        return leftPosition - rightPosition;
      });
    }
    return pending;
  }

  function aiWaitingForStopMessages(record) {
    return (record.messages || []).filter(function (message) {
      return message.role === "user" && message.status === "waiting_for_stop";
    });
  }

  function aiQueueRenderKey(snapshot) {
    return JSON.stringify([
      snapshot.workspace,
      snapshot.conversation_id,
      snapshot.sequence,
      snapshot.items,
      snapshot.approval_pending,
      aiQueueEditingTurn,
      aiQueueEdit && [aiQueueEdit.turn_id, aiQueueEdit.revision, aiQueueEdit.text],
    ]);
  }

  function aiCaptureConversationMutation(conversationId) {
    return {
      workspace: WS,
      conversation_id: conversationId || aiConversation,
      sequence: aiConversationSequence,
    };
  }

  function aiCaptureQueueMutation(message) {
    var context = aiCaptureConversationMutation(aiConversation);
    context.turn_id = message.turn_id;
    context.revision = message.queue_revision || 1;
    context.expected_order = aiQueueSnapshot ? aiQueueSnapshot.order.slice() : [];
    return context;
  }

  function aiMutationIsCurrent(context) {
    return !!context && context.workspace === WS
      && context.conversation_id === aiConversation
      && context.sequence === aiConversationSequence;
  }

  function aiRefreshQueueForMutation(context) {
    return aiMutationIsCurrent(context) ? aiRefreshQueue() : Promise.resolve(null);
  }

  function aiPaperApprovalDecisionKey(conversationId, approval) {
    return JSON.stringify([WS, conversationId, approval.turn_id, approval.practice_set_id,
      approval.revision]);
  }

  function aiPaperApprovalProposalKey(conversationId, approval) {
    return JSON.stringify([WS, conversationId, approval.turn_id, approval.practice_set_id]);
  }

  function aiPaperText(host, tag, className, value) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    host.appendChild(node);
    return node;
  }

  function aiPaperOrder(host, label, ids) {
    if (!Array.isArray(ids)) return;
    aiPaperText(host, "p", "ai-paper-approval-order-label", label);
    var list = document.createElement("ol");
    list.className = "ai-paper-approval-order";
    ids.forEach(function (id) {
      aiPaperText(list, "li", "", String(id));
    });
    host.appendChild(list);
  }

  function aiPaperApprovalDetails(host, approval, fallbackProposedIds) {
    var paperId = approval.practice_set_id || "";
    var title = approval.title || paperId;
    aiPaperText(host, "p", "ai-paper-approval-paper", "Paper：" + title
      + (paperId && title !== paperId ? "（" + paperId + "）" : ""));
    var added = Array.isArray(approval.added_problem_ids) ? approval.added_problem_ids : [];
    var removed = Array.isArray(approval.removed_problem_ids) ? approval.removed_problem_ids : [];
    var changes = [];
    if (added.length) changes.push("加入 " + added.join("、"));
    if (removed.length) changes.push("移除 " + removed.join("、"));
    if (approval.order_changed) changes.push("调整题目顺序");
    if (!changes.length) changes.push("成员与顺序未变化");
    aiPaperText(host, "p", "ai-paper-approval-change", changes.join("；"));
    if (Array.isArray(approval.current_problem_ids)) {
      aiPaperOrder(host, "当前顺序", approval.current_problem_ids);
    }
    var proposedIds = Array.isArray(approval.proposed_problem_ids)
      ? approval.proposed_problem_ids : fallbackProposedIds;
    aiPaperOrder(host, "更新后顺序", proposedIds);
    if (approval.resets_progress) {
      aiPaperText(host, "p", "ai-paper-approval-impact",
        "将清除这张试卷未完成练习中的进度（当前已完成 "
          + Number(approval.completed_items || 0) + " 项）和草稿 "
          + Number(approval.draft_items || 0) + " 份；历史作答与评分保留。");
    } else if (approval.status !== "invalid") {
      aiPaperText(host, "p", "ai-paper-approval-impact",
        "不会清除未完成进度或草稿；历史作答与评分保留。");
    }
  }

  function aiPaperActionStatus(approval) {
    if (!approval) return "提议已记录";
    if (approval.status === "approved") return "已批准";
    if (approval.status === "cancelled") return "已取消";
    if (approval.status === "invalid") return "无法应用";
    return "等待确认";
  }

  function aiRenderPaperProposalHistory(action, turnId) {
    if (!action || action.type !== "paper_update_proposal" || !messages) return;
    var approval = action.paper_approval || {};
    var id = String(turnId || approval.turn_id || action.turn_id
      || action.practice_set_id || "proposal");
    var card = aiPaperProposalCards[id];
    if (!card) {
      card = document.createElement("article");
      card.className = "msg ai ai-paper-proposal-history";
      aiPaperProposalCards[id] = card;
      messages.appendChild(card);
    }
    card.innerHTML = "";
    aiPaperText(card, "strong", "ai-paper-approval-history-title",
      "Agent 提议更新试卷 · " + (approval.title || action.practice_set_id || "现有试卷"));
    aiPaperText(card, "p", "ai-paper-approval-history-status", aiPaperActionStatus(approval));
    if (approval.status === "invalid") {
      aiPaperText(card, "p", "ai-paper-approval-impact",
        "这个提议无法应用：" + (approval.error || "请检查目标试卷或题目。"));
      if (Array.isArray(action.problem_ids)) aiPaperOrder(card, "提议顺序", action.problem_ids);
      return;
    }
    aiPaperApprovalDetails(card, Object.assign({}, approval, {
      practice_set_id: action.practice_set_id || approval.practice_set_id,
    }), action.problem_ids);
  }

  function aiUpdatePaperProposalHistory(record) {
    (record.messages || []).forEach(function (message) {
      if (message.role !== "assistant") return;
      (message.actions || []).forEach(function (action) {
        aiRenderPaperProposalHistory(action, message.turn_id);
      });
      aiRenderPaperProposalHistory(message.action, message.turn_id);
    });
  }

  function aiSetPaperApprovalOwner(record) {
    if (!record || (record.conversation_id && record.conversation_id !== aiConversation)) return;
    var approval = record.pending_paper_approval;
    if (approval && approval.conversation_id === aiConversation) {
      aiPaperApprovalOwner = {
        conversation_id: approval.conversation_id, turn_id: approval.turn_id,
        practice_set_id: approval.practice_set_id, revision: approval.revision,
      };
      return;
    }
    for (var i = (record.messages || []).length - 1; i >= 0; i -= 1) {
      var message = record.messages[i];
      if (message.role !== "assistant") continue;
      var actions = (message.actions || []).concat(message.action ? [message.action] : []);
      for (var j = actions.length - 1; j >= 0; j -= 1) {
        var action = actions[j];
        var projection = action && action.paper_approval;
        if (!action || action.type !== "paper_update_proposal" || !projection) continue;
        aiPaperApprovalOwner = {
          conversation_id: record.conversation_id || aiConversation,
          turn_id: projection.turn_id || message.turn_id,
          practice_set_id: action.practice_set_id || projection.practice_set_id,
          revision: projection.revision,
        };
        return;
      }
    }
    aiPaperApprovalOwner = null;
  }

  function aiRenderPaperApproval(approval) {
    var panel = document.getElementById("ai-paper-approval");
    var status = document.getElementById("ai-paper-approval-status");
    var details = document.getElementById("ai-paper-approval-details");
    var approve = document.getElementById("ai-paper-approval-approve");
    var cancel = document.getElementById("ai-paper-approval-cancel");
    if (!panel) return;
    var current = approval && approval.status === "pending"
      && approval.conversation_id === aiConversation ? approval : null;
    aiCurrentPaperApproval = current;
    panel.classList.toggle("hidden", !current);
    if (details) details.innerHTML = "";
    if (!current) {
      if (status) status.textContent = "";
      if (approve) approve.disabled = false;
      if (cancel) cancel.disabled = false;
      aiPaperApprovalNotice = null;
      aiPaperApprovalUnknownKey = "";
      return;
    }
    var proposalKey = aiPaperApprovalProposalKey(aiConversation, current);
    var decisionKey = aiPaperApprovalDecisionKey(aiConversation, current);
    var inFlight = !!aiPaperApprovalInFlight[proposalKey];
    var unknown = aiPaperApprovalUnknownKey === decisionKey;
    var notice = aiPaperApprovalNotice;
    if (notice && (notice.conversation_id !== aiConversation
        || notice.turn_id !== current.turn_id
        || notice.practice_set_id !== current.practice_set_id
        || notice.revision !== current.revision)) {
      aiPaperApprovalNotice = null;
      notice = null;
    }
    if (status) status.textContent = notice ? notice.text
      : "确认前不会修改试卷；批准或取消后，队列仍需手动继续。";
    if (details) aiPaperApprovalDetails(details, current);
    if (approve) approve.disabled = inFlight || unknown;
    if (cancel) cancel.disabled = inFlight || unknown;
  }

  function aiPaperApprovalDecisionOwnerMatches(context, revision) {
    var owner = aiPaperApprovalOwner;
    return context.workspace === WS && context.conversation_id === aiConversation
      && context.sequence === aiConversationSequence && owner
      && owner.conversation_id === context.conversation_id
      && owner.turn_id === context.turn_id
      && owner.practice_set_id === context.practice_set_id
      && (owner.revision === context.revision
        || owner.revision === (revision === undefined ? context.revision : revision));
  }

  function aiDecidePaperApproval(decision) {
    var approval = aiCurrentPaperApproval;
    var conversationId = aiConversation;
    if (!approval || approval.status !== "pending" || !conversationId) return;
    var context = {
      workspace: WS, conversation_id: conversationId,
      turn_id: approval.turn_id, practice_set_id: approval.practice_set_id,
      revision: approval.revision, sequence: aiConversationSequence,
    };
    var proposalKey = aiPaperApprovalProposalKey(conversationId, approval);
    var decisionKey = aiPaperApprovalDecisionKey(conversationId, approval);
    if (aiPaperApprovalInFlight[proposalKey] || aiPaperApprovalUnknownKey === decisionKey) return;
    aiPaperApprovalInFlight[proposalKey] = decisionKey;
    aiPaperApprovalNotice = {
      conversation_id: conversationId, turn_id: approval.turn_id,
      practice_set_id: approval.practice_set_id, revision: approval.revision,
      text: decision === "approve" ? "正在提交批准并核对最新状态…" : "正在取消并核对最新状态…",
    };
    aiRenderPaperApproval(approval);
    var responseApproval = null;
    var requestFailed = false;
    post("/ai/sessions/" + encodeURIComponent(conversationId) + "/paper-approval", {
      turn_id: approval.turn_id, expected_revision: approval.revision, decision: decision,
    }).then(function (result) {
      responseApproval = result.approval || null;
      var responseRevision = responseApproval && responseApproval.revision;
      var responseMatches = result.conversation_id === context.conversation_id
        && result.turn_id === context.turn_id && responseApproval
        && responseApproval.conversation_id === context.conversation_id
        && responseApproval.turn_id === context.turn_id
        && responseApproval.practice_set_id === context.practice_set_id;
      if (!responseMatches || !aiPaperApprovalDecisionOwnerMatches(context, responseRevision)) {
        return null;
      }
      if (result.stale && responseApproval) {
        aiPaperApprovalOwner = {
          conversation_id: responseApproval.conversation_id,
          turn_id: responseApproval.turn_id,
          practice_set_id: responseApproval.practice_set_id,
          revision: responseApproval.revision,
        };
        aiPaperApprovalNotice = {
          conversation_id: conversationId, turn_id: approval.turn_id,
          practice_set_id: approval.practice_set_id, revision: responseApproval.revision,
          text: "试卷或练习进度已变化。请核对下面的最新影响，再次点击「"
            + (decision === "approve" ? "批准更新" : "取消更新") + "」。",
        };
        aiRenderPaperApproval(responseApproval);
      } else {
        aiPaperApprovalNotice = null;
      }
      return result;
    }, function () {
      requestFailed = true;
      if (aiPaperApprovalDecisionOwnerMatches(context)) {
        aiPaperApprovalNotice = {
          conversation_id: conversationId, turn_id: approval.turn_id,
          practice_set_id: approval.practice_set_id, revision: approval.revision,
          text: "正在重新读取试卷状态；在核对完成前不会再次提交。",
        };
      }
      return null;
    }).then(function () {
      if (!aiPaperApprovalDecisionOwnerMatches(context,
          responseApproval && responseApproval.revision || context.revision)) return null;
      return aiRefreshQueue().then(function (record) {
        if (context.sequence !== aiConversationSequence || conversationId !== aiConversation) return null;
        if (!record) {
          var unresolved = aiCurrentPaperApproval || approval;
          var unresolvedKey = aiPaperApprovalDecisionKey(conversationId, unresolved);
          aiPaperApprovalUnknownKey = unresolvedKey;
          aiPaperApprovalNotice = {
            conversation_id: conversationId, turn_id: unresolved.turn_id,
            practice_set_id: unresolved.practice_set_id, revision: unresolved.revision,
            text: "无法确认这次操作的结果。请刷新页面重新读取状态后再操作。",
          };
          aiRenderPaperApproval(aiCurrentPaperApproval);
          return null;
        }
        var current = record.pending_paper_approval;
        if (requestFailed && current && current.turn_id === approval.turn_id
            && current.practice_set_id === approval.practice_set_id
            && current.revision === approval.revision) {
          aiPaperApprovalNotice = {
            conversation_id: conversationId, turn_id: approval.turn_id,
            practice_set_id: approval.practice_set_id, revision: approval.revision,
            text: "上次操作未能确认；当前试卷仍待确认。请核对影响后重试。",
          };
        }
        return record;
      });
    }).finally(function () {
      if (aiPaperApprovalInFlight[proposalKey] === decisionKey) {
        delete aiPaperApprovalInFlight[proposalKey];
      }
      if (context.sequence === aiConversationSequence && conversationId === aiConversation) {
        aiRenderPaperApproval(aiCurrentPaperApproval);
      }
    });
  }

  function aiRenderPendingQueue(record) {
    var panel = document.getElementById("ai-pending-queue");
    var list = document.getElementById("ai-pending-list");
    var status = document.getElementById("ai-queue-status");
    var handoffStatus = document.getElementById("ai-handoff-status");
    var continueButton = document.getElementById("ai-queue-continue");
    if (!panel || !list) return;
    var pending = aiPendingMessages(record);
    var waitingForStop = aiWaitingForStopMessages(record);
    var paused = record.queue_paused === true;
    var approvalPending = record.pending_paper_approval
      && record.pending_paper_approval.status === "pending"
      && record.pending_paper_approval.conversation_id === aiConversation;
    aiQueueSnapshot = {
      workspace: WS,
      conversation_id: record.conversation_id || aiConversation,
      sequence: aiConversationSequence,
      approval_pending: !!approvalPending,
      order: pending.map(function (message) { return message.turn_id; }),
      items: pending.map(function (message) {
        return [message.turn_id, message.content || "", message.queue_revision || 1];
      }),
    };
    panel.classList.toggle("hidden", !pending.length);
    if (handoffStatus) {
      handoffStatus.textContent = waitingForStop.length
        ? "正在等待当前回复停止，随后发送。" : "";
      handoffStatus.classList.toggle("hidden", !waitingForStop.length);
    }
    if (continueButton) {
      continueButton.classList.toggle("hidden", !paused || !pending.length
        || record.status === "running" || !!approvalPending);
    }
    if (status) {
      status.textContent = approvalPending
        ? "试卷更新待确认；批准或取消后，仍需手动继续队列。"
        : paused
        ? "队列已暂停；继续后会按顺序发送。"
        : pending.length ? "当前回复结束后按顺序发送；列表中的消息尚未开始。" : "";
    }
    if (aiQueueEditingTurn && !pending.some(function (message) {
      return message.turn_id === aiQueueEditingTurn;
    })) {
      var lostEditTurn = aiQueueEditingTurn;
      aiQueueEditingTurn = "";
      if (aiQueueEdit && aiQueueEdit.turn_id === lostEditTurn) {
        aiQueueEdit.recoverable = true;
        aiSetStatus("该排队消息已开始或离开队列；未保存的编辑草稿保留在恢复摘要中。");
        aiRenderOutbox();
      } else {
        aiQueueEdit = null;
      }
    }
    var renderSignature = aiQueueRenderKey(aiQueueSnapshot);
    if (renderSignature === aiQueueRenderedSignature && list.children.length === pending.length) {
      return;
    }
    aiQueueRenderedSignature = renderSignature;
    var focusedControl = aiQueueFocusControl;
    list.innerHTML = "";
    pending.forEach(function (message) {
      var card = document.createElement("article");
      card.className = "ai-pending-message";
      card.dataset.turnId = message.turn_id;
      card.setAttribute("data-turn-id", message.turn_id);
      card.queueControls = { handle: null, editor: null };
      var context = aiCaptureQueueMutation(message);
      var handle = document.createElement("button");
      handle.className = "ai-pending-handle";
      handle.type = "button";
      handle.textContent = "↕";
      handle.setAttribute("aria-label", "调整消息顺序；使用上、下方向键移动");
      handle.setAttribute("draggable", "true");
      handle.draggable = true;
      handle.dataset.turnId = message.turn_id;
      handle.addEventListener("focus", function () {
        aiQueueFocusControl = { turn_id: message.turn_id, action: "handle" };
      });
      handle.addEventListener("blur", function () {
        if (aiQueueFocusControl && aiQueueFocusControl.turn_id === message.turn_id
            && aiQueueFocusControl.action === "handle") aiQueueFocusControl = null;
      });
      handle.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
        if (event.preventDefault) event.preventDefault();
        var order = context.expected_order.slice();
        var index = order.indexOf(message.turn_id);
        var next = index + (event.key === "ArrowUp" ? -1 : 1);
        if (index < 0 || next < 0 || next >= order.length) return;
        order.splice(index, 1);
        order.splice(next, 0, message.turn_id);
        aiReorderPendingMessages(context, order);
      });
      handle.addEventListener("dragstart", function (event) {
        aiQueueDragTurn = message.turn_id;
        aiQueueDragContext = context;
        if (event.dataTransfer && event.dataTransfer.setData) {
          event.dataTransfer.setData("text/plain", message.turn_id);
          event.dataTransfer.effectAllowed = "move";
        }
      });
      handle.addEventListener("dragend", function () {
        aiQueueDragTurn = "";
        aiQueueDragContext = null;
      });
      card.addEventListener("dragover", function (event) {
        if (event.preventDefault) event.preventDefault();
      });
      card.addEventListener("drop", function (event) {
        if (event.preventDefault) event.preventDefault();
        var draggedTurn = event.dataTransfer && event.dataTransfer.getData
          ? event.dataTransfer.getData("text/plain") : aiQueueDragTurn;
        var dragContext = aiQueueDragContext || context;
        var order = dragContext.expected_order.slice();
        var from = order.indexOf(draggedTurn);
        var to = order.indexOf(message.turn_id);
        if (from < 0 || to < 0 || from === to) return;
        order.splice(from, 1);
        order.splice(to, 0, draggedTurn);
        aiReorderPendingMessages(dragContext, order);
        aiQueueDragTurn = "";
        aiQueueDragContext = null;
      });
      card.appendChild(handle);
      card.queueControls.handle = handle;
      if (message.turn_id === aiQueueEditingTurn) {
        card.className += " is-editing";
        aiEditPendingMessage(message, aiQueueEdit || context, card);
      } else {
        var content = document.createElement("p");
        content.className = "ai-pending-content";
        content.textContent = message.content || "";
        content.title = message.content || "";
        card.appendChild(content);
        var actions = document.createElement("div");
        actions.className = "ai-pending-actions";
        actions.dataset.turnId = message.turn_id;
        actions.queueControls = card.queueControls;
        aiOutboxAction(actions, "立即发送", function () {
          if (!aiMutationIsCurrent(context)) return;
          if (approvalPending) {
            aiSetStatus("试卷更新待确认；请先处理审批，再立即发送。");
            return;
          }
          post("/ai/sessions/" + encodeURIComponent(context.conversation_id) + "/turns/"
            + encodeURIComponent(context.turn_id) + "/interrupt", {
              expected_revision: context.revision,
            }).then(function (turn) {
              if (!aiMutationIsCurrent(context)) return null;
              aiSetStatus(turn.status === "waiting_for_stop"
                ? "消息已提升，等待当前回复停止。" : "消息已提升为立即发送。");
              return aiRefreshQueueForMutation(context);
            }).catch(function (error) {
              if (!aiMutationIsCurrent(context)) return;
              aiSetStatus(error.status === 409
                ? "消息状态已变化；已刷新队列，请确认后重试。"
                : "立即发送失败：" + (error.message || "未知错误"));
              aiRefreshQueueForMutation(context);
            });
        }, "send-now");
        aiOutboxAction(actions, "编辑", function () {
          if (!aiMutationIsCurrent(context)) return;
          if (aiQueueEdit && aiQueueEdit.recoverable) {
            aiSetStatus("请先从恢复摘要处理未保存的排队编辑草稿，再编辑其他排队消息。");
            return;
          }
          aiQueueEditingTurn = message.turn_id;
          aiQueueEdit = Object.assign({}, context, { text: message.content || "" });
          aiQueueFocusControl = { turn_id: message.turn_id, action: "editor" };
          aiRenderPendingQueue(record);
        }, "edit");
        aiOutboxAction(actions, "移出队列", function () {
          if (!aiMutationIsCurrent(context)) return;
          del("/ai/sessions/" + encodeURIComponent(context.conversation_id) + "/turns/"
            + encodeURIComponent(context.turn_id), { expected_revision: context.revision })
            .then(function () {
              if (!aiMutationIsCurrent(context)) return null;
              aiSetStatus("消息已移出队列；接受记录保留为已取消。");
              return aiRefreshQueueForMutation(context);
            }).catch(function (error) {
              if (!aiMutationIsCurrent(context)) return;
              aiSetStatus(error.status === 409
                ? "消息已变化；已刷新队列，请再试一次。"
                : "移出队列失败：" + (error.message || "未知错误"));
              aiRefreshQueueForMutation(context);
            });
        }, "remove");
        card.appendChild(actions);
      }
      list.appendChild(card);
      if (aiQueueFocusTurnId === message.turn_id && handle.focus) {
        handle.focus();
        aiQueueFocusTurnId = "";
      } else if (focusedControl && focusedControl.turn_id === message.turn_id) {
        var focusTarget = card.queueControls[focusedControl.action];
        if (!focusTarget && (focusedControl.action === "save"
            || focusedControl.action === "cancel")) {
          focusTarget = card.queueControls.edit;
        }
        if (focusTarget && focusTarget.focus) focusTarget.focus();
      }
    });
  }

  function aiReorderPendingMessages(context, turnIds) {
    if (!aiMutationIsCurrent(context)) return;
    aiQueueFocusTurnId = context.turn_id;
    post("/ai/sessions/" + encodeURIComponent(context.conversation_id) + "/queue/reorder", {
      expected_order: context.expected_order.slice(), turn_ids: turnIds.slice(),
    }).then(function () {
      if (!aiMutationIsCurrent(context)) return null;
      return aiRefreshQueueForMutation(context);
    }).catch(function (error) {
      if (!aiMutationIsCurrent(context)) return;
      aiQueueFocusTurnId = "";
      aiSetStatus(error.status === 409
        ? "队列已变化；当前显示服务器确认的顺序。"
        : "调整队列顺序失败：" + (error.message || "未知错误"));
      return aiRefreshQueueForMutation(context);
    });
  }

  function aiRefreshQueue() {
    if (!aiConversation) return Promise.resolve(null);
    var conversationId = aiConversation;
    var sequence = aiConversationSequence;
    return api("/ai/sessions/" + encodeURIComponent(conversationId)).then(function (record) {
      if (sequence !== aiConversationSequence || conversationId !== aiConversation) return null;
      aiSetPaperApprovalOwner(record);
      aiUpdatePaperProposalHistory(record);
      aiRenderPaperApproval(record.pending_paper_approval);
      aiSyncOutboxWithHistory(record);
      aiRenderOutbox();
      aiRenderPendingQueue(record);
      var completedNotRendered = (record.messages || []).some(function (message) {
        return message.role === "user" && message.status === "done" && message.turn_id
          && !aiRenderedDoneTurns[message.turn_id];
      });
      if (completedNotRendered && !aiHistoryReconciling) {
        aiHistoryReconciling = true;
        return aiLoadConversation(conversationId).then(function (loaded) {
          if (!loaded) aiHistoryReconciling = false;
          return loaded;
        });
      }
      if (record.status === "running" && record.current_turn_id
          && record.current_turn_id !== aiTurn) {
        return aiLoadConversation(conversationId);
      }
      var pending = aiPendingMessages(record);
      if (aiQueuePollTimer) clearTimeout(aiQueuePollTimer);
      aiQueuePollTimer = null;
      var waitingForStop = aiWaitingForStopMessages(record).length > 0;
      var queuedCanRun = !record.queue_paused
        && pending.some(function (message) { return message.status === "queued"; });
      if (waitingForStop || queuedCanRun) {
        aiQueuePollTimer = setTimeout(function () {
          if (sequence === aiConversationSequence && conversationId === aiConversation) {
            aiRefreshQueue();
          }
        }, 350);
      }
      return record;
    }).catch(function () { return null; });
  }

  function aiEditPendingMessage(message, context, card) {
    var textarea = document.createElement("textarea");
    textarea.className = "ai-pending-editor";
    textarea.dataset.turnId = message.turn_id;
    textarea.addEventListener("focus", function () {
      aiQueueFocusControl = { turn_id: message.turn_id, action: "editor" };
    });
    textarea.addEventListener("blur", function () {
      if (aiQueueFocusControl && aiQueueFocusControl.turn_id === message.turn_id
          && aiQueueFocusControl.action === "editor") aiQueueFocusControl = null;
    });
    var edit = aiQueueEdit && aiQueueEdit.turn_id === message.turn_id
      ? aiQueueEdit : context;
    textarea.value = edit.text || "";
    textarea.addEventListener("input", function () {
      if (!aiMutationIsCurrent(edit) || !aiQueueEdit
          || aiQueueEdit.turn_id !== message.turn_id) return;
      aiQueueEdit.text = textarea.value;
      aiQueueRenderedSignature = aiQueueRenderKey(aiQueueSnapshot);
      if (typeof textarea.selectionStart === "number") {
        aiQueueEdit.selectionStart = textarea.selectionStart;
        aiQueueEdit.selectionEnd = textarea.selectionEnd;
      }
    });
    var actions = document.createElement("div");
    actions.className = "ai-pending-actions";
    actions.dataset.turnId = message.turn_id;
    actions.queueControls = card.queueControls;
    aiOutboxAction(actions, "保存", function () {
      if (!aiMutationIsCurrent(edit)) return;
      if (!textarea.value.trim()) {
        aiSetStatus("消息不能为空。");
        return;
      }
      var submittedText = textarea.value;
      edit.text = submittedText;
      patch("/ai/sessions/" + encodeURIComponent(edit.conversation_id) + "/turns/"
        + encodeURIComponent(edit.turn_id), {
          message: submittedText, expected_revision: edit.revision,
        }).then(function (saved) {
          if (!aiMutationIsCurrent(edit)) return null;
          if (aiQueueEdit === edit) {
            if (edit.text === submittedText) {
              aiQueueEditingTurn = "";
              aiQueueEdit = null;
            } else {
              edit.revision = saved.queue_revision;
            }
          }
          return aiRefreshQueueForMutation(edit);
        }).catch(function (error) {
          if (!aiMutationIsCurrent(edit) || aiQueueEdit !== edit) return;
          aiSetStatus(error.status === 409
            ? "消息已开始执行或被修改；草稿仍保留，请复制后取消或重新读取。"
            : "编辑队列消息失败：" + (error.message || "未知错误"));
          aiRefreshQueueForMutation(edit);
        });
    }, "save");
    aiOutboxAction(actions, "取消", function () {
      if (!aiMutationIsCurrent(edit)) return;
      aiQueueEditingTurn = "";
      aiQueueEdit = null;
      aiRefreshQueueForMutation(edit);
    }, "cancel");
    card.appendChild(textarea);
    card.queueControls.editor = textarea;
    card.appendChild(actions);
    if (typeof edit.selectionStart === "number" && textarea.setSelectionRange) {
      textarea.setSelectionRange(edit.selectionStart, edit.selectionEnd);
    }
  }

  function aiRenderOutbox() {
    if (!messages || !aiConversation) return;
    var records = aiReadOutbox(aiConversation);
    var items = Object.keys(records).map(function (key) { return records[key]; })
      .sort(function (a, b) { return (a.created_at || 0) - (b.created_at || 0); });
    var actionable = items.filter(function (item) {
      return item.status === "unknown" || item.status === "rejected";
    });
    var queueEditRecovery = aiQueueEdit && aiQueueEdit.recoverable ? aiQueueEdit : null;
    var renderSignature = JSON.stringify([WS, aiConversation, aiConversationSequence, actionable,
      queueEditRecovery && [queueEditRecovery.turn_id, queueEditRecovery.revision,
        queueEditRecovery.text]]);
    if (!actionable.length && !queueEditRecovery) {
      if (renderSignature !== aiOutboxRenderedSignature && aiRecoveryContainer) {
        aiRecoveryContainer.innerHTML = "";
        aiRecoveryContainer.classList.add("hidden");
      }
      aiOutboxRenderedSignature = renderSignature;
      return;
    }
    if (renderSignature === aiOutboxRenderedSignature && aiRecoveryContainer) return;
    aiOutboxRenderedSignature = renderSignature;
    var wasOpen = aiRecoveryContainer && aiRecoveryContainer.open === true;
    if (!aiRecoveryContainer) {
      aiRecoveryContainer = document.createElement("details");
      aiRecoveryContainer.className = "ai-send-recoveries";
      aiRecoveryContainer.setAttribute("aria-label", "未完成的消息发送");
      messages.appendChild(aiRecoveryContainer);
    } else {
      aiRecoveryContainer.innerHTML = "";
    }
    aiRecoveryContainer.classList.remove("hidden");
    aiRecoveryContainer.open = wasOpen;
    var summary = document.createElement("summary");
    summary.textContent = "需要处理的消息（" + (actionable.length + (queueEditRecovery ? 1 : 0)) + "）";
    aiRecoveryContainer.appendChild(summary);
    var recoveryList = document.createElement("div");
    recoveryList.className = "ai-send-recovery-list";
    aiRecoveryContainer.appendChild(recoveryList);
    actionable.forEach(function (record) {
      var card = document.createElement("div");
      card.className = "ai-send-recovery";
      var label = document.createElement("p");
      if (record.status === "unknown") {
        label.textContent = "发送状态未知。可用同一消息编号核对，避免重复执行。";
      } else if (record.status === "rejected") {
        label.textContent = "这条消息被服务端拒绝；原文仍保存在本机。";
      } else {
        label.textContent = "Agent 未完成这条消息；可以明确重试一次。";
      }
      card.appendChild(label);
      var savedMessage = document.createElement("p");
      savedMessage.textContent = (record.body && record.body.message) || "";
      card.appendChild(savedMessage);
      var context = aiCaptureConversationMutation(record.conversation_id || aiConversation);
      if (record.status === "unknown") {
        aiOutboxAction(card, "核对发送状态", function () {
          if (!aiMutationIsCurrent(context)) return;
          aiRetryOutbox(record, false, context);
        }, "reconcile");
      } else if (record.status === "rejected") {
        aiOutboxAction(card, "恢复原文", function () {
          if (!aiMutationIsCurrent(context)) return;
          if (!aiInput || aiInput.value.trim()) {
            aiSetStatus("输入框已有草稿；为保护草稿，未覆盖它。请先清空输入框再恢复。没有执行整轮重试。");
            return;
          }
          aiInput.value = record.body.message || "";
          aiInput.focus();
          aiSetStatus("已恢复原文，请编辑后重新发送。");
        }, "restore");
      }
      recoveryList.appendChild(card);
    });
    if (queueEditRecovery) {
      var edit = queueEditRecovery;
      var editContext = aiCaptureConversationMutation(edit.conversation_id || aiConversation);
      var editCard = document.createElement("div");
      editCard.className = "ai-send-recovery";
      editCard.dataset.turnId = edit.turn_id;
      var editLabel = document.createElement("p");
      editLabel.textContent = "这条排队消息已开始或离开队列；未保存的编辑文本仍可手动恢复。";
      editCard.appendChild(editLabel);
      var editText = document.createElement("p");
      editText.textContent = edit.text || "";
      editCard.appendChild(editText);
      aiOutboxAction(editCard, "恢复编辑草稿", function () {
        if (!aiMutationIsCurrent(editContext) || !aiQueueEdit
            || aiQueueEdit.turn_id !== edit.turn_id || !aiQueueEdit.recoverable) return;
        if (!aiInput || aiInput.value.trim()) {
          aiSetStatus("输入框已有草稿；为保护草稿，未覆盖它。请先清空输入框再恢复。");
          return;
        }
        aiInput.value = edit.text || "";
        aiQueueEdit = null;
        aiQueueEditingTurn = "";
        aiInput.focus();
        aiSetStatus("已恢复未保存的排队编辑文本，请检查后决定是否发送。");
        aiRenderOutbox();
      }, "restore-queue-edit");
      recoveryList.appendChild(editCard);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  function aiRetryOutbox(item, newAttempt, context) {
    context = context || aiCaptureConversationMutation(item.conversation_id || aiConversation);
    if (!aiMutationIsCurrent(context) || aiSendPending) return;
    var body = Object.assign({}, item.body || {});
    if (newAttempt) {
      body.submission_id = aiNewSubmissionId();
      body.retry_of = item.turn_id;
      delete body.queue_action;
    }
    var submission = aiPrepareSubmission(body, newAttempt ? null : item);
    if (!submission) {
      aiSetStatus("无法在本机保存发送记录；原文仍保留在恢复卡片中，请复制后再试。");
      return;
    }
    aiSetRunning(Boolean(aiTurn));
    aiSetStatus(newAttempt ? "正在重试…" : "正在核对发送状态…");
    aiPostTurn(submission.body, submission, !newAttempt).catch(function (error) {
      if (!aiMutationIsCurrent(context)) return;
      aiSetRunning(Boolean(aiTurn));
      aiSetStatus("发送未确认：" + (error.message || "未知错误"));
      aiRenderOutbox();
    });
  }

  function aiPostTurn(body, existingOutbox, preserveQueueAction) {
    if (!aiConversation || aiSendPending) {
      return Promise.reject(new Error("一条消息正在发送中"));
    }
    var requestBody = Object.assign({}, body || {});
    if (!preserveQueueAction) {
      var sendAction = document.getElementById("ai-send-action");
      var selectedAction = sendAction ? sendAction.value : "default";
      requestBody.queue_action = selectedAction === "queue" || selectedAction === "interrupt"
        ? selectedAction : loadSetting("runningSendAction", "queue");
    }
    var submission = aiPrepareSubmission(requestBody, existingOutbox);
    if (!submission) {
      return Promise.reject(new Error("无法在本机保存发送记录；输入尚未发送"));
    }
    requestBody = submission.body;
    var conversationId = aiConversation;
    var sequence = aiConversationSequence;
    var workspace = WS;
    aiSendPending = true;
    aiSetRunning(Boolean(aiTurn));
    return post("/ai/sessions/" + encodeURIComponent(conversationId) + "/turns", requestBody)
      .then(function (turn) {
        aiUpdateOutbox(conversationId, requestBody.submission_id, {
          status: "accepted", turn_id: turn.turn_id,
        });
        if (workspace !== WS || sequence !== aiConversationSequence
            || conversationId !== aiConversation) return null;
        aiSendPending = false;
        if (!turn.status || turn.status === "running") {
          if (aiTurn !== turn.turn_id) {
            if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.resetTurn) {
              AgentUISurfaces.resetTurn();
            }
            aiForgetLiveArtifact();
            aiStreamingMessage = null;
            aiExecutionPlan = null;
            aiPiActivities = {};
            aiAddMarkdown(requestBody.message || "", "user");
            aiTurn = turn.turn_id;
            aiCurrentSubmissionId = requestBody.submission_id;
            aiPollSequence = 0;
            aiPollConversationTurn();
          }
          aiSetRunning(true);
          aiRefreshQueue();
        } else {
          aiSetRunning(Boolean(aiTurn));
          aiSetStatus(turn.status === "waiting_for_stop"
            ? "已接受，等待当前任务确认停止。" : "已加入队列，当前任务结束后执行。");
          aiRefreshQueue();
        }
        return turn;
      }, function (error) {
        var rejected = error.status >= 400 && error.status < 500;
        aiUpdateOutbox(conversationId, requestBody.submission_id, {
          status: rejected ? "rejected" : "unknown", error: error.message,
        });
        if (conversationId === aiConversation) aiRenderOutbox();
        if (workspace !== WS || sequence !== aiConversationSequence
            || conversationId !== aiConversation) return null;
        aiSendPending = false;
        aiSetRunning(Boolean(aiTurn));
        throw error;
      });
  }

  function aiAddMarkdown(text, cls) {
    return aiAdd(richText(text || ""), cls);
  }

  function aiAdd(html, cls) {
    var div = document.createElement("div");
    div.className = "msg " + (cls || "ai");
    div.innerHTML = "<div class='wb-reading'>" + html + "</div>";
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    renderMath(div);
    return div;
  }

  function aiAppendAssistantText(text) {
    if (!messages || !text) return;
    if (!aiStreamingMessage) {
      aiStreamingMessage = document.createElement("div");
      aiStreamingMessage.className = "msg ai";
      messages.appendChild(aiStreamingMessage);
      aiStreamingMessage.content = "";
    }
    aiStreamingMessage.content += text;
    aiStreamingMessage.innerHTML = "<div class='wb-reading'>"
      + richText(aiStreamingMessage.content) + "</div>";
    messages.scrollTop = messages.scrollHeight;
    renderMath(aiStreamingMessage);
  }

  function aiActivityState(status) {
    if (status === "done") return "已完成";
    if (status === "failed" || status === "error") return "失败";
    return "进行中";
  }

  function aiActivityStatus(status) {
    if (status === "done") return "done";
    if (status === "failed" || status === "error") return "failed";
    return "running";
  }

  function aiUpdateActivitySemantics(parts, activity) {
    var summary = activity.summary || "";
    if (parts.summary) {
      parts.summary.textContent = String(summary);
      parts.summary.classList.toggle("hidden", !summary);
    }
    if (parts.impact) {
      var evidence = activity.impact;
      if (evidence && evidence.status === "known" && evidence.summary) {
        parts.impact.textContent = "已知影响：" + String(evidence.summary);
      } else if (["tool", "command", "file", "file-read", "file-write", "lesson-kit", "search"]
          .indexOf(activity.activity_type) !== -1) {
        parts.impact.textContent = "影响未知";
      } else {
        parts.impact.textContent = "";
      }
      parts.impact.classList.toggle("hidden", !parts.impact.textContent);
    }
  }

  function aiCreateExecutionPlan() {
    if (!messages) return null;
    var plan = document.createElement("section");
    plan.className = "ai-plan";
    plan.setAttribute("aria-label", "执行计划");
    var title = document.createElement("div");
    title.className = "ai-plan-title";
    title.textContent = "执行计划";
    var list = document.createElement("ol");
    list.className = "ai-plan-list";
    plan.appendChild(title);
    plan.appendChild(list);
    messages.appendChild(plan);
    aiExecutionPlan = { element: plan, list: list, rows: {} };
    return aiExecutionPlan;
  }

  function aiUpsertActivity(activity, plan) {
    if (!activity) return;
    plan = plan || aiExecutionPlan || aiCreateExecutionPlan();
    if (!plan) return;
    var id = String(activity.activity_id || "activity-" + Object.keys(plan.rows).length);
    var row = plan.rows[id];
    if (!row) {
      row = document.createElement("li");
      var marker = document.createElement("span");
      marker.className = "ai-plan-marker";
      marker.setAttribute("aria-hidden", "true");
      var body = document.createElement("div");
      body.className = "ai-plan-body";
      var heading = document.createElement("div");
      heading.className = "ai-plan-heading";
      var label = document.createElement("strong");
      label.className = "ai-plan-label";
      var state = document.createElement("span");
      state.className = "ai-plan-state";
      heading.appendChild(label);
      heading.appendChild(state);
      var detail = document.createElement("div");
      detail.className = "ai-plan-detail hidden";
      var summary = document.createElement("div");
      summary.className = "ai-plan-summary hidden";
      var impact = document.createElement("div");
      impact.className = "ai-plan-impact hidden";
      body.appendChild(heading);
      body.appendChild(detail);
      body.appendChild(summary);
      body.appendChild(impact);
      row.appendChild(marker);
      row.appendChild(body);
      row.activityParts = {
        label: label, state: state, detail: detail, summary: summary,
        impact: impact, body: body,
      };
      plan.rows[id] = row;
      plan.list.appendChild(row);
    }
    var status = aiActivityStatus(activity.status);
    row.className = "ai-plan-step is-" + status;
    if (activity.label != null || !row.activityParts.label.textContent) {
      row.activityParts.label.textContent = activity.label || "执行步骤";
    }
    row.activityParts.state.textContent = aiActivityState(status);
    if (activity.detail != null) row.activityParts.detail.textContent = activity.detail || "";
    row.activityParts.detail.classList.toggle("hidden", !row.activityParts.detail.textContent);
    aiUpdateActivitySemantics(row.activityParts, activity);
    if (activity.output != null && String(activity.output).length) {
      if (!row.activityParts.output) {
        var disclosure = document.createElement("details");
        disclosure.className = "ai-plan-output";
        var summary = document.createElement("summary");
        summary.textContent = "查看输出";
        var output = document.createElement("pre");
        disclosure.appendChild(summary);
        disclosure.appendChild(output);
        row.activityParts.body.appendChild(disclosure);
        row.activityParts.output = output;
      }
      row.activityParts.output.textContent = String(activity.output);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  function aiRenderExecutionPlan(activities) {
    if (!activities || !activities.length) return;
    var plan = aiCreateExecutionPlan();
    activities.forEach(function (activity) { aiUpsertActivity(activity, plan); });
  }

  function aiUpsertPiActivity(activity) {
    if (!messages || !activity) return;
    var id = String(activity.activity_id || "activity-" + Object.keys(aiPiActivities).length);
    var row = aiPiActivities[id];
    if (!row) {
      aiStreamingMessage = null;
      row = document.createElement("div");
      var body = document.createElement("div");
      body.className = "ai-plan-body";
      var heading = document.createElement("div");
      heading.className = "ai-plan-heading";
      var label = document.createElement("strong");
      label.className = "ai-plan-label";
      var state = document.createElement("span");
      state.className = "ai-plan-state";
      heading.appendChild(label);
      heading.appendChild(state);
      var detail = document.createElement("div");
      detail.className = "ai-plan-detail hidden";
      var summary = document.createElement("div");
      summary.className = "ai-plan-summary hidden";
      var impact = document.createElement("div");
      impact.className = "ai-plan-impact hidden";
      body.appendChild(heading);
      body.appendChild(detail);
      body.appendChild(summary);
      body.appendChild(impact);
      row.appendChild(body);
      row.activityParts = {
        label: label, state: state, detail: detail, summary: summary, impact: impact, body: body,
        disclosure: null, output: null,
      };
      aiPiActivities[id] = row;
      messages.appendChild(row);
    }
    var status = aiActivityStatus(activity.status);
    row.className = "msg ai-activity is-" + status;
    if (activity.label != null || !row.activityParts.label.textContent) {
      row.activityParts.label.textContent = activity.label || "调用工具";
    }
    row.activityParts.state.textContent = aiActivityState(status);
    if (activity.detail != null) row.activityParts.detail.textContent = activity.detail || "";
    row.activityParts.detail.classList.toggle("hidden", !row.activityParts.detail.textContent);
    // Provider summaries and explicit write evidence remain visible; output stays folded.
    aiUpdateActivitySemantics(row.activityParts, activity);
    if (activity.output != null && String(activity.output).length) {
      if (!row.activityParts.output) {
        var disclosure = document.createElement("details");
        disclosure.className = "ai-plan-output";
        var summary = document.createElement("summary");
        summary.textContent = "查看输出";
        var output = document.createElement("pre");
        disclosure.appendChild(summary);
        disclosure.appendChild(output);
        row.activityParts.body.appendChild(disclosure);
        row.activityParts.disclosure = disclosure;
        row.activityParts.output = output;
      }
      row.activityParts.output.textContent = String(activity.output);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  function aiHandleActivity(activity) {
    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.activity) {
      AgentUISurfaces.activity(activity);
    }
    if (aiCurrentProvider === "pi") aiUpsertPiActivity(activity);
    else aiUpsertActivity(activity);
  }

  function aiRenderActivities(activities) {
    if (!activities || !activities.length) return;
    if (aiCurrentProvider === "pi") {
      activities.forEach(aiUpsertPiActivity);
    } else {
      aiRenderExecutionPlan(activities);
    }
  }

  function aiSetStatus(text) {
    if (aiStatus) aiStatus.textContent = text || "";
  }

  function aiSetRunning(running) {
    if (aiSend) aiSend.disabled = aiSendPending || !aiConversation;
    if (aiStop) aiStop.classList.toggle("hidden", !running);
    // Each submission is gated independently; an active provider does not
    // prevent another accepted message from joining the durable queue.
    if (aiInput) aiInput.disabled = false;
    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.setRunning) {
      AgentUISurfaces.setRunning(running);
    }
  }

  function aiApplyAction(action) {
    if (!action) return;
    if (action.type === "paper_artifact") {
      aiLiveArtifactId = action.practice_set_id || "";
      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {
        var previewAllowed = AgentUISurfaces.state && !AgentUISurfaces.state.userCollapsed;
        if (AgentUISurfaces.artifact(action) && previewAllowed) aiSaveLiveArtifact(action);
        else aiClearLiveArtifact();
      }
      return;
    }
    if (action.type === "replace_practice_selection") {
      if (!Array.isArray(action.kp_ids) || !action.kp_ids.length) return;
      saveSelectedKpIds(action.kp_ids);
      aiSetStatus("练习范围已更新");
      return;
    }
    if (action.type === "check_ingest") {
      aiApplyCheckAction(action);
      return;
    }
    if (action.type === "prefill_goal_form") {
      var map = {
        "goal-title": action.title, "goal-kind": action.kind,
        "goal-start-date": action.start_date, "goal-deadline": action.deadline,
        "goal-description": action.description,
      };
      Object.keys(map).forEach(function (id) {
        var field = document.getElementById(id);
        if (field && map[id]) field.value = map[id];
      });
      var editor = document.querySelector(".goal-editor");
      if (editor && editor.open === false) editor.open = true;
      var goalNotice = document.getElementById("goal-form-status");
      if (goalNotice) goalNotice.textContent = "Agent 已代填目标字段，确认后保存。";
    }
  }

  var ASSET_LABELS = [
    ["knowledge_points", "知识点"],
    ["problems", "题目"],
    ["flash_cards", "闪卡"],
    ["figures", "图片"],
    ["keyless", "未录答案键"],
  ];

  function aiAssetSummary(counts) {
    return ASSET_LABELS.filter(function (pair) {
      return counts[pair[0]];
    }).map(function (pair) {
      return pair[1] + " " + counts[pair[0]];
    }).join("、");
  }

  function aiResultDetail(result) {
    var counts = result.counts || {};
    var origins = result.origins || {};
    var lines = ["批次 " + (result.batch_id || "?") + " · " + (result.kind || "?")];
    var assets = aiAssetSummary(counts);
    if (assets) lines.push(assets);
    var originKeys = Object.keys(origins);
    if (originKeys.length) {
      lines.push("来源 " + originKeys.map(function (key) {
        return key + " " + origins[key];
      }).join(" · "));
    }
    if (result.workspace) lines.push("工作区 " + result.workspace);
    if (result.backup_path) {
      lines.push("备份 " + String(result.backup_path).split(/[\\/]/).pop());
    }
    return lines.join("\n");
  }

  function aiBatchState(batchId) {
    return api("/ingest/batches").then(function (items) {
      var rows = items || [];
      for (var index = 0; index < rows.length; index += 1) {
        if (rows[index].batch_id === batchId) return rows[index];
      }
      return null;
    }).catch(function () { return null; });
  }

  function aiMarkRolledBack(card, batchId) {
    if (!card) return;
    var row = aiBatchRow(card, batchId);
    if (row) {
      var label = row.children[0];
      if (label) label.textContent = "批次 " + batchId + " 已整批回滚";
      (row.children || []).slice().forEach(function (child) {
        if (child.className === "check-card-rollback") child.remove();
      });
      return;
    }
    var title = card.querySelector(".check-card-title");
    var detail = card.querySelector(".check-card-detail");
    var assets = detail && detail.dataset ? detail.dataset.assets : "";
    if (title) title.textContent = "Check 入库已回滚";
    if (detail) {
      detail.textContent = "批次 " + batchId + " 已整批回滚"
        + (assets ? "（撤销 " + assets + "）" : "") + "，池中不再包含该批内容。";
    }
    var button = card.querySelector(".check-card-rollback");
    if (button) button.remove();
  }

  function aiBatchRow(card, batchId) {
    var body = (card.children || [])[0];
    var rows = (body && body.children) || [];
    for (var index = 0; index < rows.length; index += 1) {
      var row = rows[index];
      if (row.dataset && row.dataset.batchId === batchId) return row;
    }
    return null;
  }

  function aiApplyCheckAction(action) {
    if (action.error) {
      aiAddCheckCard("入库未执行", "校验未通过：" + action.error, null);
      return;
    }
    var result = action.result;
    if (!result) return;
    var batches = Array.isArray(result.batches) ? result.batches : [];
    if (batches.length > 1) {
      // One bundle that spanned chapters: every recorded batch gets its own row
      // and its own rollback.
      var card = aiAddMultiBatchCard(result, batches);
      batches.forEach(function (batch) {
        aiBatchState(batch.batch_id).then(function (state) {
          if (state && state.rolled_back_at) aiMarkRolledBack(card, batch.batch_id);
        });
      });
      return;
    }
    if (!result.batch_id) return;
    var single = aiAddCheckCard("入库完成", aiResultDetail(result), result.batch_id);
    var line = single ? single.querySelector(".check-card-detail") : null;
    if (line) line.dataset.assets = aiAssetSummary(result.counts || {});
    // A reopened card shows the batch's current state, not the state at the time
    // it ran: an already rolled-back batch offers no second rollback.
    aiBatchState(result.batch_id).then(function (batch) {
      if (batch && batch.rolled_back_at) aiMarkRolledBack(single, result.batch_id);
    });
  }

  function aiAddMultiBatchCard(result, batches) {
    var card = aiAddCheckCard("入库完成", aiMultiBatchDetail(result, batches), null);
    if (!card) return null;
    var body = card.children[0];
    batches.forEach(function (batch) {
      var row = document.createElement("div");
      row.className = "check-card-batch";
      row.dataset.batchId = batch.batch_id;
      var label = document.createElement("div");
      label.className = "check-card-batch-label";
      label.textContent = aiBatchLabel(batch);
      row.appendChild(label);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "check-card-rollback";
      button.textContent = "整批回滚";
      button.addEventListener("click", function () {
        aiRollbackBatch(batch.batch_id, button);
      });
      row.appendChild(button);
      body.appendChild(row);
    });
    return card;
  }

  function aiBatchLabel(batch) {
    var parts = ["批次 " + batch.batch_id];
    if (batch.chapter) parts.push(batch.chapter);
    var assets = aiAssetSummary(batch.counts || {});
    if (assets) parts.push(assets);
    return parts.join(" · ");
  }

  function aiMultiBatchDetail(result, batches) {
    var chapters = batches.map(function (batch) { return batch.chapter; })
      .filter(function (chapter) { return !!chapter; });
    var totals = {};
    batches.forEach(function (batch) {
      Object.keys(batch.counts || {}).forEach(function (key) {
        totals[key] = (totals[key] || 0) + batch.counts[key];
      });
    });
    var lines = ["共 " + batches.length + " 个批次"
      + (chapters.length ? " · " + chapters.join("、") : "")
      + " · " + (result.kind || "?")];
    var assets = aiAssetSummary(totals);
    if (assets) lines.push(assets);
    if (result.workspace) lines.push("工作区 " + result.workspace);
    if (result.backup_path) {
      lines.push("备份 " + String(result.backup_path).split(/[\\/]/).pop());
    }
    return lines.join("\\n");
  }

  function aiAddCheckCard(title, detail, batchId) {
    if (!messages) return null;
    var div = document.createElement("div");
    div.className = "msg ai check-card";
    var body = document.createElement("div");
    body.className = "check-card-body";
    var heading = document.createElement("div");
    heading.className = "check-card-title";
    heading.textContent = title;
    body.appendChild(heading);
    var text = document.createElement("div");
    text.className = "check-card-detail";
    text.textContent = detail;
    body.appendChild(text);
    if (batchId) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "check-card-rollback";
      button.textContent = "整批回滚";
      button.addEventListener("click", function () { aiRollbackBatch(batchId, button); });
      body.appendChild(button);
    }
    div.appendChild(body);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function aiRollbackBatch(batchId, button) {
    function executeRollback() {
      button.disabled = true;
      api("/ingest/rollback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batch_id: batchId }),
      }).then(function (result) {
        var card = button.closest(".check-card");
        if (card) {
          var detail = card.querySelector(".check-card-detail");
          if (detail) {
            detail.textContent = "批次 " + batchId + " 已整批回滚（撤销 "
              + (result && result.deleted != null ? result.deleted : "?") + " 行）。";
          }
        }
        button.remove();
        aiSetStatus("批次已回滚");
      }).catch(function (err) {
        button.disabled = false;
        aiSetStatus("回滚失败：" + (err && err.message ? err.message : "未知错误"));
      });
    }

    var approval = {
      title: "整批回滚 " + batchId,
      reason: "内容变更不可撤销，需要你确认。",
      impact: "这批内容会从池中删除。",
      approveLabel: "确认回滚",
    };
    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.confirm
        && AgentUISurfaces.confirm(approval, executeRollback)) {
      return;
    }
    if (window.confirm && !window.confirm("整批回滚 " + batchId + "？这批内容会从池中删除。")) return;
    executeRollback();
  }

  function aiRecordRecent(type, id) {
    if (!type || !id) return;
    var recent = load(AI_RECENT_KEY, []).filter(function (item) {
      return !(item.type === type && item.id === id);
    });
    recent.unshift({ type: type, id: id });
    store(AI_RECENT_KEY, recent.slice(0, 3));
  }

  function aiRenderConversation(record) {
    if (!messages) return;
    if (aiChatView) aiSetView("chat");
    aiTurn = null;
    aiCurrentSubmissionId = "";
    aiRenderedDoneTurns = {};
    aiHistoryReconciling = false;
    aiPaperProposalCards = {};
    messages.innerHTML = "";
    aiRecoveryContainer = null;
    aiOutboxRenderedSignature = "";
    var conversationId = record.conversation_id || aiConversation;
    aiSyncOutboxWithHistory(record);
    var outboxRecords = aiReadOutbox(conversationId);
    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.resetConversation) {
      AgentUISurfaces.resetConversation();
    }
    aiCurrentProvider = record.provider || "";
    aiSetPaperApprovalOwner(record);
    aiSyncModelSwitch(record);
    aiStreamingMessage = null;
    aiExecutionPlan = null;
    aiPiActivities = {};
    (record.messages || []).forEach(function (message) {
      if (message.role === "user") {
        if (message.status === "queued" || message.status === "waiting_for_stop") return;
        if (message.status === "done" && message.turn_id) {
          aiRenderedDoneTurns[message.turn_id] = true;
        }
        var userMessage = aiAddMarkdown(message.content || "", "user");
        if (message.status === "failed" || message.status === "cancelled") {
          var statusText = message.status === "cancelled" ? "本轮已停止。" : "本轮未完成。";
          if (message.error) statusText += " " + message.error;
          var status = document.createElement("p");
          status.className = "ai-turn-inline-status";
          status.textContent = statusText;
          userMessage.appendChild(status);
          var recovery = message.submission_id && outboxRecords[message.submission_id];
          if (recovery && recovery.status === "failed") {
            var retryContext = aiCaptureConversationMutation(conversationId);
            var retryButton = aiOutboxAction(userMessage, "基于此消息重试", function () {
              if (!aiMutationIsCurrent(retryContext)) return;
              aiRetryOutbox(recovery, true, retryContext);
            }, "retry-failed");
            retryButton.className += " ai-inline-retry";
          }
        }
      } else {
        aiPiActivities = {};
        aiRenderActivities(message.activities || []);
        var restoredText = message.content || "";
        if (message.partial && restoredText) {
          restoredText = "部分回答（本轮未完成）\n\n" + restoredText;
        }
        if (restoredText) aiAddMarkdown(restoredText, "ai");
        // Restore durable presentational results only. Mutable actions such as
        // practice selection and goal prefills are never replayed from history.
        var actions = message.actions || [];
        actions.forEach(function (restored) {
          if (!restored) return;
          if (restored.type === "check_ingest") aiApplyCheckAction(restored);
          else if (restored.type === "paper_update_proposal") {
            aiRenderPaperProposalHistory(restored, message.turn_id);
          }
          else if (restored.type === "paper_artifact"
              && typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {
            AgentUISurfaces.artifact(restored, { restore: true });
          }
        });
        if (message.action && message.action.type === "paper_artifact"
            && typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {
          var livePreview = aiHasLiveArtifact(
            record.conversation_id || aiConversation, message.action.practice_set_id);
          AgentUISurfaces.artifact(message.action, { restore: !livePreview });
        } else if (!actions.length && message.action && message.action.type === "check_ingest") {
          aiApplyCheckAction(message.action);
        } else if (message.action && message.action.type === "paper_update_proposal") {
          aiRenderPaperProposalHistory(message.action, message.turn_id);
        }
        aiExecutionPlan = null;
      }
    });
    aiRenderOutbox();
    aiRenderPaperApproval(record.pending_paper_approval);
    aiRenderPendingQueue(record);
    aiSetRunning(record.status === "running");
    aiSetStatus(record.status === "running" ? "Agent 正在处理…" : "");
    if (record.status === "running" && record.current_turn_id) {
      aiTurn = record.current_turn_id;
      aiPollConversationTurn();
    }
    if (aiPendingMessages(record).length || aiWaitingForStopMessages(record).length) {
      aiRefreshQueue();
    }
  }

  function aiLoadConversation(conversationId) {
    if (!conversationId) return Promise.resolve(null);
    if (aiSurfaceConversation !== conversationId) {
      var initialRestore = !aiSurfaceConversation && aiConversation === conversationId;
      aiResetConversationRuntime(initialRestore ? conversationId : "");
      aiSurfaceConversation = conversationId;
    }
    aiConversation = conversationId;
    store(AI_CONVERSATION_KEY, conversationId);
    var sequence = aiConversationSequence;
    var loadSequence = ++aiConversationLoadSequence;
    return api("/ai/sessions/" + encodeURIComponent(conversationId)).then(function (record) {
      if (sequence !== aiConversationSequence
          || loadSequence !== aiConversationLoadSequence
          || aiConversation !== conversationId) return null;
      aiRenderConversation(record);
      return record;
    }, function (error) {
      if (sequence !== aiConversationSequence
          || loadSequence !== aiConversationLoadSequence
          || aiConversation !== conversationId) return null;
      if (error.status === 404) {
        aiConversation = "";
        aiSurfaceConversation = "";
        sessionStorage.removeItem(AI_CONVERSATION_KEY);
        aiResetConversationRuntime();
        aiSetRunning(false);
        aiSetView("list");
        return null;
      }
      aiSetView("chat");
      aiSetRunning(false);
      if (aiSend) aiSend.disabled = true;
      aiSetStatus("读取对话失败：" + (error.message || "未知错误") + "。刷新页面可重试。");
      return null;
    });
  }

  function aiTargetValue(entry) {
    return JSON.stringify([
      entry.model || "",
      entry.entry || "",
    ]);
  }

  function aiSyncModelSwitch(record) {
    // A conversation is permanently bound to its Agent harness. The selector
    // therefore contains only models enumerated by that harness.
    var select = document.getElementById("ai-model-switch");
    if (!select || !record) return;
    select.innerHTML = "";
    var matched = false;
    var models = aiProviders.filter(function (entry) {
      return (entry.provider || "") === (record.provider || "");
    });
    models.forEach(function (entry) {
      var option = document.createElement("option");
      option.value = aiTargetValue(entry);
      option.textContent = entry.name;
      var sameModel = (record.model || "") === (entry.model || "");
      var sameEntry = !record.model_entry || !entry.entry || record.model_entry === entry.entry;
      if (sameModel && sameEntry) {
        option.selected = true;
        matched = true;
      }
      select.appendChild(option);
    });
    if (!matched && record.provider) {
      var current = document.createElement("option");
      current.value = JSON.stringify([record.model || "", record.model_entry || ""]);
      current.textContent = record.model_entry || record.model || (record.provider + " 默认");
      current.selected = true;
      select.insertBefore(current, select.firstChild);
    }
    select.classList.toggle("hidden", !select.children.length);
  }


  var aiModelSwitch = document.getElementById("ai-model-switch");
  if (aiModelSwitch) {
    aiModelSwitch.addEventListener("change", function () {
      if (!aiConversation) return;
      var failure = "";
      aiSetStatus("切换模型中…");
      var target;
      try {
        target = JSON.parse(aiModelSwitch.value || "[]");
      } catch (error) {
        target = [];
      }
      patch("/ai/sessions/" + encodeURIComponent(aiConversation), {
        model: target[0] || null,
        entry: target[1] || null,
      })
        .catch(function (err) { failure = err.message || "未知错误"; })
        .then(function () {
          // The reload repaints the header, so the notice is set after it.
          return aiLoadConversation(aiConversation);
        })
        .then(function (record) {
          if (!record) return null;
          aiSetStatus(failure ? "无法切换模型：" + failure
                              : "模型已切换，下一轮生效。");
          return record;
        });
    });
  }

  function aiContextBody(message) {
    // No keyword gate: a valid append-only content action carries its own
    // authority, so the learner's wording no longer decides whether one runs.
    var body = {
      message: message,
      route: window.location.pathname || "",
      page_type: layout.dataset.page || "unknown",
      recent_objects: load(AI_RECENT_KEY, []),
      practice_intent: /练习|做题|刷题|复习题/.test(message),
      selected_kp_ids: selectedKpIds(),
    };
    if (layout.dataset.objectType) body.object_type = layout.dataset.objectType;
    if (layout.dataset.objectId) body.object_id = layout.dataset.objectId;
    if (layout.dataset.page === "kp") body.kp_id = layout.dataset.objectId;
    if (layout.dataset.page === "practice" && currentProblem()) {
      var active = currentProblem();
      body.problem_id = active.id;
      body.practice_mode = sessionStorage.getItem(MODE_KEY) || "";
      body.progress = { seen: session().length };
      // Opted-in fields are bounded and captured only in this turn snapshot;
      // they never become learning records or a later turn's draft.
      body.include_draft = true;
      body.draft_answer = draftAnswer();
      body.draft_note = draftNote();
      body.draft_choices = (active.choices || []).slice();
      body.draft_images = visiblePracticeImages();
      body.practice_selection = practiceSelectionContext();
    } else if (layout.dataset.page === "practice") {
      body.practice_selection = practiceSelectionContext();
    }
    if (layout.dataset.page === "practice-sets" && layout.dataset.practiceSetId) {
      body.practice_set_id = layout.dataset.practiceSetId;
    }
    if (layout.dataset.page === "records") {
      try {
        body.records_problem_id = new URLSearchParams(window.location.search || "")
          .get("problem") || "";
      } catch (_) {
        body.records_problem_id = "";
      }
    }
    if (layout.dataset.page === "graph") {
      var graphContext = currentGraphContext();
      body.selected_kp_id = graphContext ? graphContext.selectedKpId : null;
      var activeGraphFilters = graphContext ? graphContext.filters : null;
      body.graph_filter = {
        query: (document.getElementById("graph-search") || {}).value || "",
        states: ["needs_work", "review", "mastered", "null"].filter(function (state) {
          if (!activeGraphFilters) return false;
          var key = state === "needs_work" ? "work" : state === "null" ? "new" : state;
          return activeGraphFilters.has(key);
        }),
      };
    }
    return body;
  }

  function aiAppendEvents(data) {
    (data.events || []).forEach(function (event) {
      aiPollSequence = Math.max(aiPollSequence, event.sequence || 0);
      if (event.kind === "text") aiAppendAssistantText(event.text || "");
      else if (event.kind === "activity") aiHandleActivity(event);
      else if (event.kind === "error") {
        var eventError = event.text || "Agent 返回错误";
        aiSetStatus(eventError);
        if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {
          AgentUISurfaces.failure(eventError);
        }
      }
    });
    if (!data.turn) return;
    if (data.turn.status === "done") {
      aiRemoveOutbox(aiConversation, aiCurrentSubmissionId);
      aiCurrentSubmissionId = "";
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("");
      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.finishTurn) {
        AgentUISurfaces.finishTurn();
      }
      aiApplyAction(data.turn.action);
      aiLoadConversation(aiConversation);
      if (typeof aiRefreshSessionList === "function") aiRefreshSessionList();
    } else if (data.turn.status === "failed") {
      aiUpdateOutbox(aiConversation, aiCurrentSubmissionId, {
        status: "failed", turn_id: data.turn.turn_id || aiTurn,
        error: data.turn.error || "Agent 未能完成",
      });
      aiCurrentSubmissionId = "";
      aiTurn = null;
      aiSetRunning(false);
      var turnError = "Agent 失败：" + (data.turn.error || "未知错误");
      aiSetStatus(turnError);
      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {
        AgentUISurfaces.failure(turnError);
      }
      aiLoadConversation(aiConversation);
    } else if (data.turn.status === "cancelled") {
      aiUpdateOutbox(aiConversation, aiCurrentSubmissionId, {
        status: "failed", turn_id: data.turn.turn_id || aiTurn,
        error: "本轮已取消",
      });
      aiCurrentSubmissionId = "";
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("本轮已停止。");
      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.finishTurn) {
        AgentUISurfaces.finishTurn();
      }
      aiLoadConversation(aiConversation);
    }
  }

  function aiPollConversationTurn() {
    if (!aiConversation || !aiTurn) return;
    if (aiPollTimer) clearTimeout(aiPollTimer);
    var conversationId = aiConversation;
    var turnId = aiTurn;
    var sequence = aiConversationSequence;
    var after = aiPollSequence;
    function isCurrentTurn() {
      return sequence === aiConversationSequence
        && conversationId === aiConversation && turnId === aiTurn;
    }
    function scheduleNextPoll() {
      aiPollTimer = setTimeout(function () {
        if (isCurrentTurn()) aiPollConversationTurn();
      }, 350);
    }
    api("/ai/sessions/" + encodeURIComponent(conversationId) + "/turns/"
      + encodeURIComponent(turnId) + "?after=" + after).then(function (data) {
      if (!isCurrentTurn()) return;
      if (aiProgressReadFailed) {
        aiProgressReadFailed = false;
        aiSetStatus("Agent 正在处理…");
      }
      aiAppendEvents(data);
      if (data.turn && data.turn.status === "running") {
        scheduleNextPoll();
      }
    }).catch(function () {
      if (!isCurrentTurn()) return;
      aiProgressReadFailed = true;
      aiSetStatus("无法读取 Agent 进度，当前轮次状态暂时未知。请检查连接或重新打开此对话。");
      scheduleNextPoll();
    });
  }

  function aiSendMessage() {
    var message = aiInput ? aiInput.value.trim() : "";
    if (!message || !aiConversation || aiSendPending) return;
    var submission = aiPrepareSubmission(aiContextBody(message));
    if (!submission) {
      aiSetStatus("无法在本机保存发送记录；消息仍留在输入框中，没有发送。");
      return;
    }
    aiSetRunning(Boolean(aiTurn));
    aiSetStatus("正在发送…");
    var request = aiPostTurn(submission.body, submission);
    aiInput.value = "";
    request.catch(function (err) {
      aiSetRunning(Boolean(aiTurn));
      var sendError = "发送失败：" + (err.message || "未知错误");
      aiSetStatus(sendError);
      aiRenderOutbox();
      if (!aiTurn && typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {
        AgentUISurfaces.failure(sendError);
      }
    });
  }

  var aiQueueContinue = document.getElementById("ai-queue-continue");
  if (aiQueueContinue) aiQueueContinue.addEventListener("click", function () {
    if (!aiConversation || aiTurn || aiSendPending
        || (aiCurrentPaperApproval && aiCurrentPaperApproval.status === "pending")) return;
    var context = aiCaptureConversationMutation(aiConversation);
    aiQueueContinue.disabled = true;
    post("/ai/sessions/" + encodeURIComponent(context.conversation_id) + "/queue/continue", {})
      .then(function () {
        if (!aiMutationIsCurrent(context)) return null;
        aiSetStatus("正在继续队列…");
        return aiRefreshQueueForMutation(context);
      }).catch(function (error) {
        if (!aiMutationIsCurrent(context)) return null;
        aiSetStatus(error.status === 409
          ? "当前任务尚未结束，暂时无法继续队列。"
          : "继续队列失败：" + (error.message || "未知错误"));
        return aiRefreshQueueForMutation(context);
      }).finally(function () { aiQueueContinue.disabled = false; });
  });

  var aiPaperApprovalApprove = document.getElementById("ai-paper-approval-approve");
  var aiPaperApprovalCancel = document.getElementById("ai-paper-approval-cancel");
  if (aiPaperApprovalApprove) aiPaperApprovalApprove.addEventListener("click", function () {
    aiDecidePaperApproval("approve");
  });
  if (aiPaperApprovalCancel) aiPaperApprovalCancel.addEventListener("click", function () {
    aiDecidePaperApproval("cancel");
  });

  if (aiSend) aiSend.addEventListener("click", aiSendMessage);
  if (aiInput) aiInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      if (event.preventDefault) event.preventDefault();
      aiSendMessage();
    }
  });
  if (aiStop) aiStop.addEventListener("click", function () {
    if (!aiConversation || !aiTurn) return;
    post("/ai/sessions/" + encodeURIComponent(aiConversation) + "/cancel", {})
      .then(function () { aiSetStatus("正在停止…"); })
      .catch(function () { aiSetStatus("停止请求失败。"); });
  });
  /* ---------- compact Agent session IA ---------- */

  var aiSessionListView = document.getElementById("ai-session-list-view");
  var aiSessionControls = document.getElementById("ai-session-controls");
  var aiSessionList = document.getElementById("ai-session-list");
  var aiSessionEmpty = document.getElementById("ai-session-empty");
  var aiNewSession = document.getElementById("ai-new-session");
  var aiProviderPicker = document.getElementById("ai-provider-picker");
  var aiProviderOptions = document.getElementById("ai-provider-options");
  var aiChatView = document.getElementById("ai-chat-view");
  var aiSessionBack = document.getElementById("ai-session-back");
  var aiSessionRecords = [];
  var aiProviders = [];
  var aiProviderLoadError = "";

  if (aiSessionBack) {
    aiSessionBack.setAttribute("aria-label", "返回对话列表");
    aiSessionBack.title = "返回对话列表";
  }

  function aiSetView(view) {
    if (!aiSessionListView || !aiProviderPicker || !aiChatView) return;
    if (aiSessionControls) aiSessionControls.classList.toggle("hidden", view === "chat");
    aiSessionListView.classList.toggle("hidden", view !== "list");
    aiProviderPicker.classList.toggle("hidden", view !== "picker");
    aiChatView.classList.toggle("hidden", view !== "chat");
  }

  function aiSessionLabel(record) {
    return record.title || "未命名对话";
  }

  function aiRenderSessionList(items) {
    if (!aiSessionList) return;
    aiSessionRecords = items || [];
    aiSessionList.innerHTML = "";
    aiSessionRecords.forEach(function (record) {
      var row = document.createElement("div");
      row.className = "ai-session-item";
      row.setAttribute("role", "listitem");
      row.dataset.conversationId = record.conversation_id;
      var button = document.createElement("button");
      button.className = "ai-session-entry";
      button.type = "button";
      button.setAttribute("aria-label", aiSessionLabel(record));
      var title = document.createElement("strong");
      title.className = "ai-session-entry-title";
      title.textContent = aiSessionLabel(record);
      var meta = document.createElement("span");
      meta.className = "ai-session-entry-meta";
      var updated = record.updated_at ? String(record.updated_at).slice(0, 10) : "";
      meta.textContent = (record.provider || "Agent")
        + (updated ? " · " + updated : "")
        + (record.status === "running" ? " · 运行中" : "");
      button.appendChild(title);
      button.appendChild(meta);
      button.addEventListener("click", function () { aiLoadConversation(record.conversation_id); });
      row.appendChild(button);
      var actions = document.createElement("div");
      actions.className = "ai-session-actions";
      var rename = document.createElement("button");
      rename.type = "button";
      rename.className = "ghost sm icon-only";
      rename.textContent = "✎";
      rename.title = "重命名对话";
      rename.setAttribute("aria-label", "重命名对话");
      rename.addEventListener("click", function (event) {
        if (event && event.stopPropagation) event.stopPropagation();
        var next = window.prompt ? window.prompt("会话名称", aiSessionLabel(record)) : "";
        next = String(next || "").trim();
        if (!next) return;
        api("/ai/sessions/" + encodeURIComponent(record.conversation_id), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: next }),
        }).then(aiRefreshSessionList).catch(function (err) {
          aiSetStatus("无法重命名：" + (err.message || "未知错误"));
        });
      });
      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "ghost sm icon-only";
      remove.textContent = "×";
      remove.title = "删除本地会话";
      remove.setAttribute("aria-label", "删除本地会话");
      remove.addEventListener("click", function (event) {
        if (event && event.stopPropagation) event.stopPropagation();
        if (window.confirm && !window.confirm("删除这个本地会话？")) return;
        api("/ai/sessions/" + encodeURIComponent(record.conversation_id), { method: "DELETE" })
          .then(aiRefreshSessionList).catch(function (err) {
            aiSetStatus(err.message === "409" ? "会话运行中，暂时不能删除。" : "无法删除会话。");
          });
      });
      actions.appendChild(rename);
      actions.appendChild(remove);
      row.appendChild(actions);
      aiSessionList.appendChild(row);
    });
    if (aiSessionEmpty) aiSessionEmpty.classList.toggle("hidden", aiSessionRecords.length > 0);
  }

  function aiRenderProviderPicker() {
    if (!aiProviderOptions) return;
    aiProviderOptions.innerHTML = "";
    aiProviders.forEach(function (entry) {
      var button = document.createElement("button");
      button.className = "outline sm ai-provider-option";
      button.type = "button";
      button.dataset.provider = entry.provider || entry.name;
      button.dataset.model = entry.model || "";
      button.dataset.entry = entry.entry || "";
      // The display name is the entry's own — the harness and model id stay
      // out of the label.
      button.textContent = (entry.provider || "") + " · " + entry.name;
      button.addEventListener("click", function () {
        aiCreateSession(entry.provider || entry.name, entry.model || "", entry.entry || "");
      });
      aiProviderOptions.appendChild(button);
    });
    if (aiProviderLoadError) {
      aiProviderOptions.innerHTML = "<p class='inline-error'>Agent 服务暂不可用。请稍后重试。</p>";
    } else if (!aiProviders.length) {
      aiProviderOptions.innerHTML = "<p class='inline-error'>暂无可用 Agent。请先配置一个提供方。</p>";
    }
  }

  function aiShowProviderPicker() {
    if (!aiProviderOptions) return;
    aiConversationLoadSequence += 1;
    aiSetView("picker");
    // Show the last known catalog immediately; then refresh it without leaving
    // the picker blank while runtime discovery is in flight.
    aiRenderProviderPicker();
    aiRefreshProviders().then(aiRenderProviderPicker);
  }

  function aiRefreshProviders() {
    return api("/ai/providers").then(function (items) {
      aiProviders = items || [];
      aiProviderLoadError = "";
      return aiProviders;
    }).catch(function () {
      aiProviders = [];
      aiProviderLoadError = "Agent 服务暂不可用。";
      return [];
    });
  }

  function aiRefreshSessionList() {
    return api("/ai/sessions").then(function (items) {
      aiRenderSessionList(items);
      return items;
    }).catch(function () {
      aiSetStatus("无法读取历史对话。");
      aiRenderSessionList([]);
      return [];
    });
  }

  function aiCreateSession(provider, model, entry) {
    var payload = { provider: provider };
    if (model) payload.model = model;
    if (entry) payload.entry = entry;
    post("/ai/sessions", payload).then(function (record) {
      aiConversation = record.conversation_id;
      store(AI_CONVERSATION_KEY, aiConversation);
      aiSetView("chat");
      return aiLoadConversation(aiConversation);
    }).then(aiRefreshSessionList).catch(function (err) {
      aiSetStatus("无法新建对话：" + (err.message || "未知错误"));
    });
  }

  if (aiNewSession) aiNewSession.addEventListener("click", aiShowProviderPicker);
  if (aiSessionBack) aiSessionBack.addEventListener("click", function () {
    aiResetConversationRuntime();
    aiSurfaceConversation = "";
    aiConversation = "";
    sessionStorage.removeItem(AI_CONVERSATION_KEY);
    aiSetView("list");
    aiRefreshSessionList();
  });
  if (aiSessionList) {
    aiSetView("list");
    var startupLoadSequence = aiConversationLoadSequence;
    var providerRequest = aiRefreshProviders().then(function () {
      if (aiProviderLoadError && aiSessionEmpty) {
        aiSessionEmpty.textContent = aiProviderLoadError;
        aiSessionEmpty.classList.remove("hidden");
      }
    });
    Promise.all([
      providerRequest,
      aiRefreshSessionList(),
    ]).then(function () {
      if (startupLoadSequence !== aiConversationLoadSequence) return null;
      // The Agent rail is independent of the middle view: reopening a page
      // restores the conversation the learner left open instead of the list.
      if (!aiConversation) return null;
      return aiLoadConversation(aiConversation);
    });
  }
  if (layout.dataset.objectType && layout.dataset.objectId) {
    aiRecordRecent(layout.dataset.objectType, layout.dataset.objectId);
  }

  /* ---------- page init ---------- */

  function mountMiddlePageRender() {
  var middleRoot = document.getElementById("middle-page");
  if (middleRoot) {
    renderMath(middleRoot);
    middleRoot.querySelectorAll("img").forEach(function (img) {
      img.addEventListener("error", function () {
        var alt = img.getAttribute("alt") || "图";
        img.outerHTML = "<span class='fig-missing'>（图缺失：" + escapeHtml(alt) + "）</span>";
      });
    });
  }

  mountCompletionCelebration();
  }

  /* The celebration is armed by the final submit and fires when the response
   * has arrived and the completion surface shows up (tasks.md 8.8: the
   * celebration waits for the response, the request sequence is unchanged).
   * The observer is bound per mount because the surface is rebuilt with the
   * middle page. */
  function mountCompletionCelebration() {
    var surface = document.getElementById("paper-completion");
    if (!surface || !window.MutationObserver) return;
    var wasVisible = !surface.hidden
      && !(surface.classList && surface.classList.contains("hidden"));
    var observer = new MutationObserver(function () {
      var visible = !surface.hidden
        && !(surface.classList && surface.classList.contains("hidden"));
      if (visible && !wasVisible && cueArmed(celebrationArmedAt)) {
        celebrationArmedAt = 0;
        celebrateCompletion(surface);
      }
      wasVisible = visible;
    });
    observer.observe(surface, { attributes: true, attributeFilter: ["class", "hidden"] });
  }

  function fitAiColumn() {
    if (!layout) return;
    if (window.innerWidth < 1024) layout.setAttribute("data-ai-collapsed", "1");
    else layout.removeAttribute("data-ai-collapsed");
  }

  /* ---------- three-column geometry (design.md D-10 / tasks.md 13.2 / 13.3) ----------
     The stylesheet owns the grid template (`#layout` reads --wb-col-left and
     --wb-col-right, which forward to the authoritative --shell-col-* pair);
     this side writes the two values only.  The old inline
     `grid-template-columns` overrode the stylesheet on every paint, so the CSS
     rule was dead code and the two files each carried their own numbers. */

  var COLUMN_MIN = { left: 200, right: 360 };
  var leftWidth = 280;
  var rightWidth = 420;
  var middleMinWidth = 420;
  var columnCeilings = null;

  /* The clamp ceilings are CSS constants (--shell-col-left-max /
     --shell-col-right-max), so they are read from the stylesheet instead of
     being written twice (layout-spec.md §1.2 rule 3).  The floors have no
     token and stay here; the middle column's 420px floor stays a constant
     because this side is the one that maintains the invariant
     (layout-spec.md §1.3). */
  function columnBounds() {
    if (columnCeilings) return columnCeilings;
    var fallback = { left: 480, right: 560 };
    if (window.getComputedStyle) {
      var style = window.getComputedStyle(layout);
      var left = parseFloat(style.getPropertyValue("--shell-col-left-max"));
      var right = parseFloat(style.getPropertyValue("--shell-col-right-max"));
      fallback.left = left > 0 ? left : fallback.left;
      fallback.right = right > 0 ? right : fallback.right;
    }
    columnCeilings = fallback;
    return columnCeilings;
  }

  function applyColumnWidths() {
    if (!layout || !layout.style) return;
    if (window.innerWidth < 1024) {
      layout.style.removeProperty("--wb-col-left");
      layout.style.removeProperty("--wb-col-right");
      return;
    }
    var bounds = columnBounds();
    var available = (layout.clientWidth || window.innerWidth) - middleMinWidth;
    leftWidth = Math.max(COLUMN_MIN.left, Math.min(bounds.left, Math.min(leftWidth, available - rightWidth)));
    rightWidth = Math.max(COLUMN_MIN.right, Math.min(bounds.right, Math.min(rightWidth, available - leftWidth)));
    /* The stylesheet's write point for these two values (workbench.css
       `#layout`): it forwards them to the authoritative --shell-col-* pair. */
    layout.style.setProperty("--wb-col-left", leftWidth + "px");
    layout.style.setProperty("--wb-col-right", rightWidth + "px");
  }

  function bindColumnResizer(id, side, min, max) {
    var handle = document.getElementById(id);
    var layout = document.getElementById("layout");
    if (!handle || !layout || window.innerWidth < 1024) return;
    var dragging = false;
    handle.addEventListener("pointerdown", function (event) {
      dragging = true;
      layout.classList.add("is-resizing");
      if (handle.setPointerCapture) handle.setPointerCapture(event.pointerId);
      document.body.style.cursor = "col-resize";
      event.preventDefault();
    });
    handle.addEventListener("pointermove", function (event) {
      if (!dragging) return;
      var rect = layout.getBoundingClientRect();
      var width = side === "left" ? event.clientX - rect.left : rect.right - event.clientX;
      var available = (layout.clientWidth || window.innerWidth) - middleMinWidth;
      var cap = side === "left" ? available - rightWidth : available - leftWidth;
      width = Math.max(min, Math.min(max, Math.min(width, cap)));
      if (side === "left") leftWidth = width;
      else rightWidth = width;
      applyColumnWidths();
    });
    function stop() { if (!dragging) return; dragging = false; document.body.style.cursor = ""; layout.classList.remove("is-resizing"); }
    handle.addEventListener("pointerup", stop);
    handle.addEventListener("pointercancel", stop);
  }
  bindColumnResizer("left-resizer", "left", COLUMN_MIN.left, columnBounds().left);
  bindColumnResizer("right-resizer", "right", COLUMN_MIN.right, columnBounds().right);
  fitAiColumn();
  applyColumnWidths();
  window.addEventListener("resize", function () { fitAiColumn(); applyColumnWidths(); });

  function mountTimeView() {
  /* ---------- time view (calendar + workload) ---------- */

  var timeView = document.getElementById("time-view");
  var timeViewDisposed = false;
  if (!timeView) return null;
  if (timeView) {
    var timeViewContent = document.getElementById("time-view-content");
    var calendarGrid = document.getElementById("calendar-grid");
    var calendarMonthLabel = document.getElementById("calendar-month-label");
    var workloadBars = document.getElementById("workload-bars");
    var workloadTotal = document.getElementById("workload-total");
    var workloadPeak = document.getElementById("workload-peak");
    var workloadOverdue = document.getElementById("workload-overdue");
    var workloadPrefill = document.getElementById("workload-prefill");
    var timeViewEmpty = document.getElementById("time-view-empty");
    var WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];

    function isoDate(date) {
      var month = String(date.getMonth() + 1).padStart(2, "0");
      var day = String(date.getDate()).padStart(2, "0");
      return date.getFullYear() + "-" + month + "-" + day;
    }

    function renderMonthGrid(goals) {
      var today = new Date();
      var year = today.getFullYear();
      var month = today.getMonth();
      var first = new Date(year, month, 1);
      var last = new Date(year, month + 1, 0);
      var daysInMonth = last.getDate();
      var lead = (first.getDay() + 6) % 7; /* Monday-first */
      var weekCount = Math.ceil((lead + daysInMonth) / 7);
      var periods = [];
      var offGrid = [];
      if (calendarMonthLabel) {
        calendarMonthLabel.textContent = year + "年" + (month + 1) + "月";
      }

      function plainDate(value) {
        if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value.slice(0, 10))) {
          return null;
        }
        var parts = value.slice(0, 10).split("-").map(Number);
        return new Date(parts[0], parts[1] - 1, parts[2]);
      }

      function dayNumber(value) {
        return Date.UTC(value.getFullYear(), value.getMonth(), value.getDate()) / 86400000;
      }

      goals.forEach(function (goal) {
        var end = plainDate(goal.deadline);
        var start = plainDate(goal.start_date) || end;
        if (start && end && start <= end && end >= first && start <= last) {
          periods.push({ goal: goal, start: start, end: end });
          return;
        }
        offGrid.push(goal);
      });
      if (offGrid.length) {
        var offLine = offGrid.map(function (goal) {
          return escapeHtml(goal.title || "未命名目标")
            + (goal.deadline ? "（" + escapeHtml(goal.deadline.slice(0, 10)) + "）" : "");
        }).join("、");
        calendarGrid.insertAdjacentHTML("afterend",
          "<p class='muted time-off-note'>本月之外或未设截止日期：" + offLine + " 个。</p>");
      }
      periods.sort(function (a, b) {
        return a.start - b.start || b.end - a.end
          || String(a.goal.id || "").localeCompare(String(b.goal.id || ""));
      });
      var periodLaneEnds = [];
      periods.forEach(function (period) {
        var startDay = dayNumber(period.start);
        var lane = periodLaneEnds.findIndex(function (occupiedUntil) {
          return occupiedUntil < startDay;
        });
        if (lane < 0) lane = periodLaneEnds.length;
        period.lane = lane;
        periodLaneEnds[lane] = dayNumber(period.end);
      });

      var html = "<div class='calendar-weekdays'>" + WEEKDAYS.map(function (label) {
        return "<div class='calendar-head'>" + label + "</div>";
      }).join("") + "</div>";
      for (var week = 0; week < weekCount; week += 1) {
        var weekStart = new Date(year, month, 1 - lead + week * 7);
        var weekEnd = new Date(year, month, 7 - lead + week * 7);
        var segments = [];
        periods.forEach(function (period) {
          var segmentStart = period.start > weekStart ? period.start : weekStart;
          var segmentEnd = period.end < weekEnd ? period.end : weekEnd;
          if (segmentStart > segmentEnd) return;
          var startColumn = dayNumber(segmentStart) - dayNumber(weekStart) + 1;
          var endColumn = dayNumber(segmentEnd) - dayNumber(weekStart) + 1;
          segments.push({
            period: period, startColumn: startColumn, endColumn: endColumn, lane: period.lane,
            begins: segmentStart.getTime() === period.start.getTime(),
            ends: segmentEnd.getTime() === period.end.getTime(),
          });
        });

        var cells = "";
        for (var column = 0; column < 7; column += 1) {
          var cellDate = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate() + column);
          var inMonth = cellDate.getMonth() === month;
          var isToday = isoDate(cellDate) === isoDate(today);
          cells += "<div class='calendar-cell" + (!inMonth ? " blank" : "")
            + (isToday ? " today" : "") + "'>"
            + (inMonth ? "<span class='calendar-day'>" + cellDate.getDate() + "</span>" : "")
            + "</div>";
        }
        var lanes = segments.map(function (segment) {
          var goal = segment.period.goal;
          var title = escapeHtml(goal.title || "未命名目标");
          var kind = goal.kind === "long_term" ? " long-term" : " stage";
          var overdue = segment.period.end < new Date(today.getFullYear(), today.getMonth(), today.getDate())
            ? " overdue" : "";
          var edges = (segment.begins ? " segment-start" : "") + (segment.ends ? " segment-end" : "");
          if (!segment.ends) edges += " segment-continuing";
          var span = segment.endColumn - segment.startColumn + 1;
          var range = isoDate(segment.period.start) + " 至 " + isoDate(segment.period.end);
          var labelHere = !segment.period.labelShown
            && (span > 1 || segment.ends || week === weekCount - 1);
          var label = labelHere ? "<span class='calendar-goal-label'>" + title + "</span>" : "";
          if (labelHere) segment.period.labelShown = true;
          return "<span class='calendar-goal" + kind + overdue + edges + "'"
            + " style='grid-column:" + segment.startColumn + " / span " + span
            + ";grid-row:" + (segment.lane + 1) + "' title='" + title + " · " + range
            + "' aria-label='" + title + "，" + range + "'>" + label + "</span>";
        }).join("");
        var laneCount = segments.reduce(function (highest, segment) {
          return Math.max(highest, segment.lane + 1);
        }, 0);
        html += "<div class='calendar-week' style='--calendar-lanes:" + laneCount + "'>"
          + "<div class='calendar-week-days'>" + cells + "</div>"
          + "<div class='calendar-lane-layer'>" + lanes + "</div></div>";
      }
      calendarGrid.innerHTML = html;
    }

    function renderBars(days) {
      var max = 0;
      var total = 0;
      days.forEach(function (day) {
        max = Math.max(max, day.count);
        total += day.count;
      });
      var nonzero = days.filter(function (day) { return day.count > 0; });
      var average = nonzero.length
        ? nonzero.reduce(function (sum, day) { return sum + day.count; }, 0) / nonzero.length
        : 0;
      var heavyThreshold = average * 2;
      var peakDay = days.find(function (day) { return day.count === max && max > 0; });
      var overdue = days.length ? Number(days[0].overdue || 0) : 0;
      if (workloadTotal) workloadTotal.textContent = "共 " + total + " 项";
      if (workloadPeak) {
        workloadPeak.textContent = peakDay
          ? "峰值 " + peakDay.date.slice(5).replace("-", ".") + " · " + peakDay.count + " 项"
          : "峰值 —";
      }
      if (workloadOverdue) workloadOverdue.textContent = "逾期 " + overdue + " 项";
      var bars = days.map(function (day) {
        var height = max ? Math.round((day.count / max) * 132) : 0;
        var heavy = day.count >= heavyThreshold && day.count > 0;
        var peak = day === peakDay;
        var label = day.date.slice(8);
        var state = (peak ? " peak" : "") + (heavy ? " heavy" : "");
        var stateLabel = (peak ? "，峰值" : "") + (heavy ? "，任务偏重" : "");
        return "<div class='bar-col" + state + "' role='listitem' data-bar-date='" + day.date
          + "' aria-label='" + day.date + "，" + day.count + " 项" + stateLabel + "'>"
          + "<div class='bar-plot'>"
          + (day.count ? "<span class='bar-value' style='bottom:" + (height + 5) + "px'>" + day.count + "</span>" : "")
          + (day.count ? "<div class='bar-fill' style='height:" + height + "px'></div>" : "")
          + (heavy ? "<span class='bar-heavy-flag' style='bottom:" + Math.max(height - 3, 0) + "px' aria-hidden='true'></span>" : "")
          + "</div><span class='bar-date'>" + label + "</span></div>";
      }).join("");
      workloadBars.innerHTML = bars
        + (nonzero.length ? "" : "<p class='muted workload-empty'>未来 14 天暂无到期复习项</p>");
      var heavyDays = days.filter(function (day) {
        return day.count >= heavyThreshold && day.count > 0;
      });
      if (heavyDays.length) {
        workloadPrefill.classList.remove("hidden");
        var busiest = heavyDays.reduce(function (a, b) { return b.count > a.count ? b : a; });
        workloadPrefill.dataset.busiestCount = String(busiest.count);
      }
    }

    api("/calendar").then(function (data) {
      if (timeViewDisposed) return;
      var goals = data.goals || [];
      var days = data.days || [];
      var hasWorkload = days.some(function (day) { return day.count > 0; });
      if (!goals.length && !hasWorkload) {
        timeView.classList.remove("hidden");
        if (timeViewContent) timeViewContent.classList.add("hidden");
        timeViewEmpty.classList.remove("hidden");
        return;
      }
      timeView.classList.remove("hidden");
      if (timeViewContent) timeViewContent.classList.remove("hidden");
      renderMonthGrid(goals);
      renderBars(days);
      if (!goals.length) {
        calendarGrid.insertAdjacentHTML("afterend",
          "<p class='muted'>暂无带截止日期的目标</p>");
      }
    }).catch(function () { /* the time view stays hidden on failure */ });

    if (workloadPrefill) {
      workloadPrefill.addEventListener("click", function () {
        var input = document.getElementById("ai-input");
        if (!input) return;
        var count = workloadPrefill.dataset.busiestCount || "较多";
        input.value = "最近几天任务偏重（最多的一天 " + count + " 项），帮我重排一下。";
        input.focus();
      });
    }
  }

  return function disposeTimeView() { timeViewDisposed = true; };
  }

  var middlePageMounted = false;
  var graphPageDispose = null;
  var timeViewDispose = null;

  function disposeMiddlePage() {
    if (!middlePageMounted) return;
    middlePageGeneration += 1;
    if (practiceRuntime && practiceRuntime.dispose) practiceRuntime.dispose();
    if (graphPageDispose) graphPageDispose();
    if (timeViewDispose) timeViewDispose();
    graphPageDispose = null;
    timeViewDispose = null;
    practiceRuntime = null;
    currentProblem = function () { return null; };
    session = function () { return []; };
    visiblePracticeImages = function () { return []; };
    draftAnswer = function () { return ""; };
    draftNote = function () { return ""; };
    practiceSelectionContext = function () { return {}; };
    currentGraphContext = function () { return null; };
    middlePageMounted = false;
  }

  function mountMiddlePage() {
    disposeMiddlePage();
    mountSelectionPage();
    graphPageDispose = mountGraphPage();
    mountPracticeViews();
    mountMiddlePageRender();
    timeViewDispose = mountTimeView();
    mountSettingsView();
    renderSettingsToggle();
    if (layout.dataset.objectType && layout.dataset.objectId) {
      recordRecent(layout.dataset.objectType, layout.dataset.objectId);
      aiRecordRecent(layout.dataset.objectType, layout.dataset.objectId);
    }
    middlePageMounted = true;
  }

  window.WorkbenchMiddlePage = { mount: mountMiddlePage, dispose: disposeMiddlePage };
  mountMiddlePage();

})();
