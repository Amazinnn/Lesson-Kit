/* Paper practice motion: visual state only; the Paper controller owns all facts. */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.PixelPracticeMotion = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
  function mix(a, b, amount) { return a.map(function (value, i) { return Math.round(value + (b[i] - value) * amount); }); }
  function color(ratio) {
    var stops = [[226, 118, 44], [246, 202, 62], [132, 200, 233]];
    var point = clamp(ratio, 0, 1) * 2;
    var index = Math.min(1, Math.floor(point));
    return mix(stops[index], stops[index + 1], point - index);
  }
  function density(x, time, ratio) {
    var phase = ((x - time * (.065 + .095 * ratio)) % 112 + 112) % 112;
    var distance = Math.min(phase, 112 - phase);
    return 1 - distance / 56;
  }
  function tone(ratio, amount) {
    var level = clamp(Math.round(amount * 7), 0, 7);
    return mix(color(ratio), [255, 242, 218], level / 7 * (.38 + .28 * ratio));
  }
  function completed(statuses, onSubmit) {
    return statuses.filter(function (status) { return status !== "unanswered" && (onSubmit || status !== "filled"); }).length;
  }
  function phase(age, reduced) {
    if (reduced) return { enter: 1, dock: 1, summary: 1 };
    return {
      enter: clamp(age / 420, 0, 1),
      dock: clamp((age - 950) / 1050, 0, 1),
      summary: clamp((age - 1900) / 500, 0, 1),
    };
  }
  function mount(options) {
    var root = options.root, work = options.work, completion = options.completion;
    var question = options.question, answers = options.options;
    var stage = document.createElement("section");
    stage.className = "paper-pixel-progress";
    stage.setAttribute("aria-label", "试卷完成度");
    stage.innerHTML = "<div class='paper-pixel-progress__heading'><span>✦ 星焰航迹</span><strong></strong></div>"
      + "<div class='paper-pixel-progress__bar' role='progressbar' aria-label='试卷完成度' aria-valuemin='0' aria-valuemax='100'><div class='paper-pixel-progress__cells'></div><i class='paper-pixel-progress__cap' aria-hidden='true'></i></div>"
      + "<small>从容起步，每一步都算数。</small>";
    work.insertBefore(stage, work.firstChild);
    var heading = stage.querySelector("strong"), bar = stage.querySelector("[role=progressbar]");
    var field = stage.querySelector(".paper-pixel-progress__cells"), cap = stage.querySelector(".paper-pixel-progress__cap");
    var banner = document.createElement("div");
    banner.className = "paper-pixel-combo";
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");
    banner.hidden = true;
    banner.innerHTML = "<b class='paper-pixel-combo__number'></b><span class='paper-pixel-combo__word'><img src='/static/combo-word.svg' alt='combo'></span><span class='paper-pixel-combo__brush' aria-hidden='true'>✎</span>";
    root.appendChild(banner);
    var confetti = document.createElement("div");
    confetti.className = "paper-pixel-confetti";
    confetti.setAttribute("aria-hidden", "true");
    root.appendChild(confetti);
    var cells = [], state = { count: 0, total: 0, ratio: 0, chargeAt: -1e9 }, frame = 0, timer = 0, disposed = false;
    var mode = function () { return window.lkMotion && typeof window.lkMotion.mode === "function" ? window.lkMotion.mode() : "full"; };
    function quiet() { return mode() === "off" || mode() === "weak" || document.hidden; }
    var motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    var observer = new MutationObserver(function () { if (!frame) frame = requestAnimationFrame(draw); });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-motion"] });
    motionQuery.addEventListener("change", visibility);
    function buildCells() {
      var width = Math.max(112, Math.floor(bar.clientWidth || 560));
      var columns = Math.ceil(width / 8);
      if (cells.length === columns * 3) return;
      field.replaceChildren(); cells = [];
      for (var row = 0; row < 3; row += 1) for (var col = 0; col < columns; col += 1) {
        var cell = document.createElement("i");
        cell.className = "paper-pixel-progress__cell";
        cell.style.left = col * 8 + "px"; cell.style.top = row * 8 + "px";
        field.appendChild(cell); cells.push({ node: cell, x: col * 8 });
      }
    }
    function draw(now) {
      frame = 0;
      if (disposed || document.hidden || stage.hidden || !stage.isConnected) return;
      buildCells();
      var width = bar.clientWidth || 560, end = width * state.ratio;
      var charging = now - state.chargeAt < 2200;
      cells.forEach(function (cell) {
        var active = cell.x < end;
        cell.node.style.visibility = active ? "visible" : "hidden";
        if (!active) return;
        var wave = density(cell.x, now, state.ratio);
        var base = tone(state.ratio, wave);
        if (charging) base = mix(base, [255, 203, 108], density(cell.x, now * 1.22 + 180, state.ratio) * .65);
        cell.node.style.backgroundColor = "rgb(" + base.join(",") + ")";
      });
      cap.style.left = clamp(end - 16, 0, width - 16) + "px";
      cap.style.backgroundColor = quiet() ? "#e4e0d5" : "rgb(" + mix([209, 209, 202], [255, 255, 255], density(end, now, state.ratio)).join(",") + ")";
      if (!quiet()) frame = requestAnimationFrame(draw);
    }
    function update(facts) {
      var statuses = facts.statuses || [];
      state.total = statuses.length;
      state.count = completed(statuses, facts.mode === "on_submit");
      state.ratio = state.total ? state.count / state.total : 0;
      heading.textContent = state.count + " / " + state.total + " 已完成";
      bar.setAttribute("aria-valuenow", String(Math.round(state.ratio * 100)));
      bar.setAttribute("aria-valuetext", "已完成 " + state.count + " / " + state.total);
      stage.querySelector("small").textContent = state.ratio >= 1 ? "这一程，已抵达 ✦" : state.ratio >= .85 ? "终点就在眼前，星焰正在蓄力 ✦" : state.ratio >= .45 ? "星焰渐盛，再向前一点。" : "从容起步，每一步都算数。";
      stage.hidden = !!facts.archived && !facts.reviewing;
      if (!stage.hidden && !frame) frame = requestAnimationFrame(draw);
    }
    function answer() {
      if (quiet()) return;
      var nodes = [question].concat(Array.prototype.slice.call(answers.children || []));
      nodes.forEach(function (node, index) {
        if (node && node.animate) node.animate([
          { transform: "translateY(0)" }, { transform: "translateY(-5px)" },
          { transform: "translateY(0)" }, { transform: "translateY(-4px)" }, { transform: "translateY(0)" },
        ], { duration: 620, delay: index * 12, easing: "ease-out" });
      });
    }
    function combo(number) {
      if (quiet()) return;
      state.chargeAt = performance.now();
      banner.querySelector("b").textContent = String(number);
      banner.hidden = false;
      banner.classList.remove("is-on"); void banner.offsetWidth; banner.classList.add("is-on");
      clearTimeout(timer);
      timer = setTimeout(function () { banner.hidden = true; banner.classList.remove("is-on"); }, 2400);
      if (!frame) frame = requestAnimationFrame(draw);
    }
    function complete() {
      if (disposed || quiet()) return;
      completion.classList.remove("paper-pixel-complete"); void completion.offsetWidth;
      completion.classList.add("paper-pixel-complete");
      var results = completion.querySelector("#paper-links");
      if (results) { results.classList.remove("paper-pixel-results-enter"); void results.offsetWidth; results.classList.add("paper-pixel-results-enter"); }
      confetti.replaceChildren();
      var colors = ["#2b62e8", "#f5c518", "#d1392b", "#f08b2c", "#75c9ef", "#aa65b5"];
      for (var i = 0; i < 64; i += 1) {
        var piece = document.createElement("i");
        piece.style.setProperty("--x", (i % 2 ? 95 : 5) + "%");
        piece.style.setProperty("--dx", ((i % 2 ? -1 : 1) * (40 + (i % 13) * 17)) + "px");
        piece.style.setProperty("--dy", (-220 - (i % 9) * 22) + "px");
        piece.style.setProperty("--delay", (i % 4) * 135 + "ms");
        piece.style.backgroundColor = colors[i % colors.length];
        confetti.appendChild(piece);
      }
      clearTimeout(timer);
      timer = setTimeout(function () { confetti.replaceChildren(); }, 3000);
    }
    function dispose() {
      disposed = true; clearTimeout(timer); cancelAnimationFrame(frame);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("resize", resize);
      motionQuery.removeEventListener("change", visibility);
      observer.disconnect();
      stage.remove(); banner.remove(); confetti.remove();
      root.dataset.pixelMotion = "";
    }
    function visibility() { if (!document.hidden && !frame) frame = requestAnimationFrame(draw); }
    function resize() { buildCells(); if (!frame) frame = requestAnimationFrame(draw); }
    root.dataset.pixelMotion = "true";
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("resize", resize);
    return { update: update, answer: answer, combo: combo, complete: complete, dispose: dispose };
  }
  return { color: color, density: density, tone: tone, completed: completed, phase: phase, mount: mount };
}));
