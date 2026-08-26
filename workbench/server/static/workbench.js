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
  var AI_CONVERSATION_KEY = "wb_ai_conversation_" + WS;
  var AI_RECENT_KEY = "wb_ai_recent_" + WS;
  var selectedGraphKpId = null;

  /* ---------- helpers ---------- */

  function api(path, options) {
    return fetch("/api/w/" + WS + path, options).then(function (resp) {
      if (!resp.ok) throw new Error(resp.status);
      return resp.json();
    });
  }

  function post(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  function store(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
  }

  function load(key, fallback) {
    var raw = sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  }

  function renderMath(root) {
    var spans = (root || document).querySelectorAll(".math");
    if (!spans.length || !window.katex) return;
    spans.forEach(function (span) {
      try {
        katex.render(span.textContent, span, { throwOnError: false });
      } catch (e) { /* keep raw text */ }
    });
  }

  function escapeHtml(text) {
    return String(text == null ? "" : text).replace(/[&<>\"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[ch];
    });
  }

  function richInline(text) {
    var tokens = [];
    function token(html) {
      var key = "\u0000" + tokens.length + "\u0000";
      tokens.push(html);
      return key;
    }
    var value = escapeHtml(text == null ? "" : String(text));
    value = value.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function (_, alt, src) {
      if (!/^\/(?:api\/w\/|static\/)|^[\w./-]+$/.test(src)) return alt;
      return token("<img alt='" + alt + "' src='" + src.replace(/'/g, "&#39;") + "'>");
    });
    value = value.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, function (_, id, label) {
      var cleanId = id.trim();
      if (!/^[\w-]+$/.test(cleanId)) return label || cleanId;
      return token("<a href='/w/" + encodeURIComponent(WS) + "/kp/" + encodeURIComponent(cleanId)
        + "'>" + (label || cleanId) + "</a>");
    });
    value = value.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, function (_, label, href) {
      return token("<a href='" + href.replace(/'/g, "&#39;")
        + "' target='_blank' rel='noopener noreferrer'>" + label + "</a>");
    });
    value = value.replace(/`([^`\n]+)`/g, function (_, code) {
      return token("<code>" + code + "</code>");
    });
    value = value.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    value = value.replace(/__([^_\n]+)__/g, "<strong>$1</strong>");
    value = value.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
    value = value.replace(/_([^_\n]+)_/g, "<em>$1</em>");
    value = value.replace(/\$\$([\s\S]+?)\$\$/g, function (_, math) {
      return token("<span class='math display'>" + math + "</span>");
    });
    value = value.replace(/\$([^$\n]+)\$/g, function (_, math) {
      return token("<span class='math'>" + math + "</span>");
    });
    return value.replace(/\u0000(\d+)\u0000/g, function (_, index) { return tokens[Number(index)]; });
  }

  function richText(text) {
    var lines = String(text == null ? "" : text).replace(/\r\n?/g, "\n").split("\n");
    var out = [], paragraph = [], listType = null, inCode = false, codeLang = "", codeLines = [];
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
    lines.forEach(function (line) {
      var fence = line.match(/^\s*```\s*([\w-]*)\s*$/);
      if (fence) {
        flushParagraph(); closeList();
        if (inCode) flushCode();
        inCode = !inCode; codeLang = inCode ? fence[1] : "";
        return;
      }
      if (inCode) { codeLines.push(line); return; }
      var heading = line.match(/^\s*(#{1,3})\s+(.+?)\s*#*\s*$/);
      if (heading) {
        flushParagraph(); closeList();
        out.push("<h" + heading[1].length + ">" + richInline(heading[2]) + "</h" + heading[1].length + ">");
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
    return out.join("");
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

  /* ---------- native knowledge graph ---------- */

  var graphCanvas = document.getElementById("graph-canvas");
  if (graphCanvas) {
    var graphSearch = document.getElementById("graph-search");
    var graphFilter = document.getElementById("graph-state-filter");
    var graphDetail = document.getElementById("graph-detail-panel");
    var graphDetailTab = document.getElementById("graph-detail-tab");
    var teacherTab = document.getElementById("ai-teacher-tab");
    var teacherPanel = document.getElementById("ai-teacher-panel");
    var graphData = { nodes: [], edges: [] };
    var graphSimulation = null;
    var graphFrame = null;
    var graphStage = null;
    var graphNodeElements = new Map();
    var graphEdgeElements = [];
    var graphView = { x: 0, y: 0, scale: 1 };
    var graphAutoFit = true;
    var draggedNode = null;
    var panStart = null;
    var reducedGraphMotion = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function stateLabel(state) {
      return {
        needs_work: "待攻克", review: "待复习", mastered: "已掌握",
      }[state] || "未标注";
    }

    function relationStrengthLabel(strength) {
      return { low: "弱", medium: "中", high: "强" }[strength] || "暂无";
    }

    function showGraphPanel(detailOpen) {
      if (graphDetail) graphDetail.classList.toggle("hidden", !detailOpen);
      if (teacherPanel) teacherPanel.classList.toggle("hidden", detailOpen);
      if (graphDetailTab) {
        graphDetailTab.classList.toggle("active", detailOpen);
        graphDetailTab.setAttribute("aria-selected", detailOpen ? "true" : "false");
      }
      if (teacherTab) {
        teacherTab.classList.toggle("active", !detailOpen);
        teacherTab.setAttribute("aria-selected", detailOpen ? "false" : "true");
      }
    }

    function renderGraphDetail(node) {
      if (!graphDetail) return;
      selectedGraphKpId = node.id;
      recordRecent("kp", node.id);
      var neighborCount = graphData.edges.filter(function (edge) {
        return edge.source === node.id || edge.target === node.id;
      }).length;
      var strongest = graphData.edges.filter(function (edge) {
        return edge.source === node.id || edge.target === node.id;
      }).reduce(function (best, edge) {
        var rank = { low: 0, medium: 1, high: 2 };
        return !best || rank[edge.strength] > rank[best.strength] ? edge : best;
      }, null);
      graphDetail.innerHTML = "<p class='side-label'>学习看板</p><h2>"
        + escapeHtml(node.title) + "</h2>"
        + "<div class='graph-dashboard-metrics' aria-label='知识点指标'>"
        + "<div><span>当前状态</span><strong>" + escapeHtml(stateLabel(node.state)) + "</strong></div>"
        + "<div><span>关联题目</span><strong>" + escapeHtml(node.problem_count || 0) + " 道</strong></div>"
        + "<div><span>相邻知识点</span><strong>" + neighborCount + " 个</strong></div>"
        + "<div><span>主要关系</span><strong>" + escapeHtml(strongest ? relationStrengthLabel(strongest.strength) : "暂无") + "</strong></div>"
        + "<div><span>学习信号</span><strong id='graph-signal-summary'>读取中</strong></div>"
        + "<div><span>下次复习</span><strong id='graph-schedule-summary'>读取中</strong></div>"
        + "</div><p class='graph-dashboard-note muted'>状态和关联规模来自当前工作区的正式题池。</p>"
        + "<label for='graph-state'>更新学习状态</label>";
      var state = document.createElement("select");
      state.id = "graph-state";
      state.innerHTML = "<option value='needs_work'>待攻克</option>"
        + "<option value='review'>待复习</option><option value='mastered'>已掌握</option>";
      state.value = node.state || "review";
      var save = document.createElement("button");
      save.id = "graph-state-save";
      save.className = "primary sm";
      save.textContent = "保存状态";
      save.addEventListener("click", function () {
        post("/graph/state", {
          item_type: "kp", item_id: node.id, state: state.value,
        }).then(function (data) {
          node.state = data.state;
          renderGraph();
          renderGraphDetail(node);
        });
      });
      graphDetail.appendChild(state);
      graphDetail.appendChild(save);
      var link = document.createElement("a");
      link.id = "graph-open-kp";
      link.className = "graph-dashboard-link";
      link.href = "/w/" + encodeURIComponent(WS) + "/kp/" + encodeURIComponent(node.id);
      link.textContent = "打开知识点";
      graphDetail.appendChild(link);
      api("/kp/" + encodeURIComponent(node.id)).then(function (detail) {
        if (selectedGraphKpId !== node.id) return;
        var signal = (detail.signals || []).map(function (item) {
          return item.signal_type + " · " + item.weight;
        }).join("、") || "暂无信号";
        var schedule = detail.schedule && detail.schedule.due_at
          ? "" + detail.schedule.due_at : "未排期";
        var signalEl = document.getElementById("graph-signal-summary");
        var scheduleEl = document.getElementById("graph-schedule-summary");
        if (signalEl) signalEl.textContent = signal;
        if (scheduleEl) scheduleEl.textContent = schedule;
      }).catch(function () {
        if (selectedGraphKpId !== node.id) return;
        var signalEl = document.getElementById("graph-signal-summary");
        var scheduleEl = document.getElementById("graph-schedule-summary");
        if (signalEl) signalEl.textContent = "暂不可用";
        if (scheduleEl) scheduleEl.textContent = "暂不可用";
      });
      showGraphPanel(true);
    }

    function renderGraph() {
      var search = (graphSearch && graphSearch.value || "").trim().toLowerCase();
      var state = graphFilter && graphFilter.value;
      var nodes = graphData.nodes.filter(function (node) {
        return (!search || (node.title + " " + node.id).toLowerCase().includes(search))
          && (!state || node.state === state);
      });
      var visibleIds = new Set(nodes.map(function (node) { return node.id; }));
      var edges = graphData.edges.filter(function (edge) {
        return visibleIds.has(edge.source) && visibleIds.has(edge.target);
      });
      if (graphFrame !== null) cancelAnimationFrame(graphFrame);
      graphFrame = null;
      var stage = document.createElement("div");
      stage.className = "graph-stage";
      graphStage = stage;
      graphNodeElements = new Map();
      graphEdgeElements = [];
      graphSimulation = GraphPhysics.createSimulation(
        nodes, edges, graphCanvas.clientWidth, graphCanvas.clientHeight,
      );
      graphAutoFit = true;
      graphSimulation.edges.forEach(function (edge) {
        var link = document.createElement("span");
        link.className = "graph-edge";
        stage.appendChild(link);
        graphEdgeElements.push({ element: link, edge: edge });
      });
      graphSimulation.nodes.forEach(function (node) {
        var button = document.createElement("button");
        button.className = "graph-node " + (node.state || "unmarked");
        button.dataset.kpId = node.id;
        button.style.width = (node.radius * 2) + "px";
        button.style.height = (node.radius * 2) + "px";
        button.setAttribute("aria-label", node.title + "，" + stateLabel(node.state)
          + "，关联 " + (node.problem_count || 0) + " 道题");
        button.title = node.title + " · " + stateLabel(node.state)
          + " · " + (node.problem_count || 0) + " 道题";
        button.addEventListener("click", function () { renderGraphDetail(node); });
        button.addEventListener("pointerdown", function (event) {
          if (event.stopPropagation) event.stopPropagation();
          draggedNode = node;
          graphAutoFit = false;
          node.fx = node.x;
          node.fy = node.y;
          if (button.setPointerCapture && event.pointerId !== undefined) {
            button.setPointerCapture(event.pointerId);
          }
          GraphPhysics.reheat(graphSimulation);
          runGraphSimulation();
        });
        stage.appendChild(button);
        var label = document.createElement("span");
        label.className = "graph-node-label";
        label.textContent = node.title;
        stage.appendChild(label);
        graphNodeElements.set(node.id, { node: button, label: label });
      });
      if (!nodes.length) {
        var empty = document.createElement("p");
        empty.className = "muted graph-empty";
        empty.textContent = "没有符合条件的知识点。";
        stage.appendChild(empty);
      }
      graphCanvas.replaceChildren(stage);
      applyGraphView();
      if (reducedGraphMotion) {
        GraphPhysics.settle(graphSimulation, 1600);
        drawGraph();
        fitGraph();
      } else {
        runGraphSimulation();
      }
    }

    function drawGraph() {
      graphEdgeElements.forEach(function (entry) {
        var source = entry.edge.sourceNode;
        var target = entry.edge.targetNode;
        var dx = target.x - source.x;
        var dy = target.y - source.y;
        entry.element.style.left = source.x + "px";
        entry.element.style.top = source.y + "px";
        entry.element.style.width = Math.hypot(dx, dy) + "px";
        entry.element.style.transform = "rotate(" + Math.atan2(dy, dx) + "rad)";
      });
      if (!graphSimulation) return;
      graphSimulation.nodes.forEach(function (node) {
        var elements = graphNodeElements.get(node.id);
        if (!elements) return;
        elements.node.style.left = node.x + "px";
        elements.node.style.top = node.y + "px";
        elements.label.style.left = node.x + "px";
        elements.label.style.top = (node.y + node.radius + 6) + "px";
      });
    }

    function runGraphSimulation() {
      if (!graphSimulation || reducedGraphMotion || graphFrame !== null) return;
      function frame() {
        graphFrame = null;
        var stable = GraphPhysics.tick(graphSimulation);
        drawGraph();
        if (!stable) graphFrame = requestAnimationFrame(frame);
        else if (graphAutoFit) fitGraph();
      }
      graphFrame = requestAnimationFrame(frame);
    }

    function applyGraphView() {
      if (!graphStage) return;
      graphStage.style.transform = "translate(" + graphView.x + "px," + graphView.y
        + "px) scale(" + graphView.scale + ")";
    }

    function setGraphScale(scale) {
      graphAutoFit = false;
      graphView.scale = Math.max(0.4, Math.min(2.5, scale));
      applyGraphView();
    }

    function fitGraph() {
      if (!graphSimulation || !graphSimulation.nodes.length) return;
      var xs = graphSimulation.nodes.map(function (node) { return node.x; });
      var ys = graphSimulation.nodes.map(function (node) { return node.y; });
      var minX = Math.min.apply(null, xs) - 48;
      var maxX = Math.max.apply(null, xs) + 48;
      var minY = Math.min.apply(null, ys) - 48;
      var maxY = Math.max.apply(null, ys) + 68;
      graphView.scale = Math.max(0.4, Math.min(1, Math.min(
        graphCanvas.clientWidth / Math.max(1, maxX - minX),
        graphCanvas.clientHeight / Math.max(1, maxY - minY),
      )));
      graphView.x = (graphCanvas.clientWidth - (minX + maxX) * graphView.scale) / 2;
      graphView.y = (graphCanvas.clientHeight - (minY + maxY) * graphView.scale) / 2;
      graphAutoFit = false;
      applyGraphView();
    }

    if (graphSearch) graphSearch.addEventListener("input", renderGraph);
    if (graphFilter) graphFilter.addEventListener("change", renderGraph);
    var zoomIn = document.getElementById("graph-zoom-in");
    var zoomOut = document.getElementById("graph-zoom-out");
    var graphFit = document.getElementById("graph-fit");
    if (zoomIn) zoomIn.addEventListener("click", function () {
      setGraphScale(graphView.scale + 0.1);
    });
    if (zoomOut) zoomOut.addEventListener("click", function () {
      setGraphScale(graphView.scale - 0.1);
    });
    if (graphFit) graphFit.addEventListener("click", fitGraph);
    graphCanvas.addEventListener("wheel", function (event) {
      if (event.preventDefault) event.preventDefault();
      setGraphScale(graphView.scale * (event.deltaY > 0 ? 0.9 : 1.1));
    });
    graphCanvas.addEventListener("pointerdown", function (event) {
      graphAutoFit = false;
      panStart = { x: event.clientX, y: event.clientY, viewX: graphView.x, viewY: graphView.y };
    });
    graphCanvas.addEventListener("pointermove", function (event) {
      if (draggedNode) {
        var rect = graphCanvas.getBoundingClientRect();
        draggedNode.fx = (event.clientX - rect.left - graphView.x) / graphView.scale;
        draggedNode.fy = (event.clientY - rect.top - graphView.y) / graphView.scale;
        GraphPhysics.reheat(graphSimulation);
        runGraphSimulation();
      } else if (panStart) {
        graphView.x = panStart.viewX + event.clientX - panStart.x;
        graphView.y = panStart.viewY + event.clientY - panStart.y;
        applyGraphView();
      }
    });
    graphCanvas.addEventListener("pointerup", function () {
      if (draggedNode) {
        draggedNode.fx = null;
        draggedNode.fy = null;
        GraphPhysics.reheat(graphSimulation);
        runGraphSimulation();
      }
      draggedNode = null;
      panStart = null;
    });
    window.addEventListener("resize", renderGraph);
    if (graphDetailTab) graphDetailTab.addEventListener("click", function () { showGraphPanel(true); });
    if (teacherTab) teacherTab.addEventListener("click", function () { showGraphPanel(false); });
    showGraphPanel(true);
    api("/graph/model").then(function (model) {
      graphData = model;
      renderGraph();
    }).catch(function () {
      graphCanvas.textContent = "图谱暂时无法读取。";
    });
  }

  /* ---------- practice session ---------- */

  var stream = document.getElementById("stream");
  var composer = document.getElementById("composer");
  var answerBox = document.getElementById("answer-box");
  var submitAnswer = document.getElementById("answer-submit");
  var showAnswer = document.getElementById("show-answer");
  var noTime = document.getElementById("no-time");
  var startPractice = document.getElementById("start-practice");
  var currentProblem = load(CURRENT_KEY, null);
  var similarRound = sessionStorage.getItem(SIMILAR_KEY) === "1";

  function session() {
    return load(SESSION_KEY, []);
  }

  function currentKps() {
    return load(KPS_KEY, []);
  }

  function setCurrent(problem) {
    currentProblem = problem || null;
    store(CURRENT_KEY, currentProblem);
    if (currentProblem) recordRecent("problem", currentProblem.problem_id);
  }

  function updateSession(problemId, values) {
    var list = session();
    list.forEach(function (item) {
      if (item.problem_id === problemId) Object.assign(item, values);
    });
    store(SESSION_KEY, list);
  }

  if (stream) {
    var modeImmediate = document.getElementById("practice-mode-immediate");
    var modeBatch = document.getElementById("practice-mode-batch");
    var actions = document.getElementById("composer-actions");
    var feedbackArea = document.getElementById("feedback-area");
    var ratingInput = document.getElementById("rating-input");
    var feedbackNote = document.getElementById("feedback-note");
    var saveRating = document.getElementById("save-rating");
    var sessionEntry = document.getElementById("session-end-entry");
    var startArea = document.getElementById("start-area");

    function selectedMode() {
      if (modeImmediate && modeImmediate.checked) return "immediate";
      if (modeBatch && modeBatch.checked) return "batch";
      return "";
    }

    function showComposer(show) {
      if (composer) composer.classList.toggle("hidden", !show);
      if (sessionEntry) sessionEntry.classList.toggle("hidden", !show);
    }

    function renderQuestion(problem) {
      stream.innerHTML = "<article class='practice-question-card card'>"
        + "<p class='context-line'>题目 · " + escapeHtml(problem.problem_id) + "</p>"
        + "<div class='problem-text rich-text'>" + richText(problem.problem_text) + "</div></article>";
      renderMath(stream);
    }

    function finishExhausted() {
      var mode = sessionStorage.getItem(MODE_KEY);
      stream.innerHTML = similarRound
        ? "<p class='muted'>暂无更多同类题。</p>"
        : "<p class='muted'>本轮相关题目已练完。</p>";
      similarRound = false;
      sessionStorage.removeItem(SIMILAR_KEY);
      setCurrent(null);
      showComposer(false);
      if (mode === "batch") window.location = "session-end";
      else {
        sessionStorage.removeItem(MODE_KEY);
        modeImmediate.checked = false;
        modeBatch.checked = false;
        startPractice.disabled = true;
        if (startArea) startArea.classList.remove("hidden");
      }
    }

    function loadNext() {
      var kps = currentKps();
      var exclude = session().map(function (item) { return item.problem_id; });
      api("/pull", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kp_ids: kps, n: 1, mode: "weak", exclude_ids: exclude }),
      }).then(function (result) {
        if (!result.problems.length) {
          finishExhausted();
          return;
        }
        var problem = result.problems[0];
        var seen = session();
        seen.push({ problem_id: problem.problem_id, answer_text: "", state: "active" });
        store(SESSION_KEY, seen);
        setCurrent(problem);
        renderQuestion(problem);
        answerBox.value = "";
        answerBox.disabled = false;
        submitAnswer.classList.remove("hidden");
        actions.classList.add("hidden");
        feedbackArea.classList.add("hidden");
        ratingInput.value = "";
        feedbackNote.value = "";
        showComposer(true);
        answerBox.focus();
      });
    }

    function startSession() {
      var mode = selectedMode();
      if (!mode) return;
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.setItem(MODE_KEY, mode);
      api("/weak?limit=200").then(function (items) {
        store(KPS_KEY, items.map(function (item) { return item.kp_id; }));
        if (startArea) startArea.classList.add("hidden");
        loadNext();
      });
    }

    function bindMode(mode) {
      if (mode) mode.addEventListener("change", function () {
        startPractice.disabled = !selectedMode();
      });
    }

    bindMode(modeImmediate);
    bindMode(modeBatch);
    if (startPractice) {
      startPractice.disabled = !selectedMode();
      startPractice.addEventListener("click", startSession);
    }

    if (submitAnswer) submitAnswer.addEventListener("click", function () {
      if (!currentProblem) return;
      var answer = answerBox.value.trim();
      currentProblem.answer_text = answer;
      setCurrent(currentProblem);
      updateSession(currentProblem.problem_id, { answer_text: answer });
      if (sessionStorage.getItem(MODE_KEY) === "batch") {
        updateSession(currentProblem.problem_id, { state: "unrated" });
        setCurrent(null);
        loadNext();
        return;
      }
      answerBox.disabled = true;
      submitAnswer.classList.add("hidden");
      actions.classList.remove("hidden");
    });

    if (showAnswer) showAnswer.addEventListener("click", function () {
      if (!currentProblem) return;
      api("/problem/" + currentProblem.problem_id).then(function (detail) {
        var solution = detail.problem.solution || "（本题无解析，请基于自身作答自评）";
        stream.innerHTML += "<section class='practice-solution'><p class='section-kicker'>解析</p>"
          + "<div class='rich-text'>" + richText(solution) + "</div></section>";
        renderMath(stream);
        showAnswer.classList.add("hidden");
        feedbackArea.classList.remove("hidden");
      });
    });

    if (saveRating) saveRating.addEventListener("click", function () {
      var rating = parseInt(ratingInput.value, 10);
      if (!currentProblem || rating < 1 || rating > 5) return;
      post("/feedback", {
        item_type: "problem", item_id: currentProblem.problem_id,
        rating: rating, note: feedbackNote.value.trim(),
      }).then(function () {
        updateSession(currentProblem.problem_id, { state: "rated" });
        setCurrent(null);
        loadNext();
      });
    });

    if (noTime) noTime.addEventListener("click", function () {
      if (!currentProblem) return;
      updateSession(currentProblem.problem_id, { state: "skipped" });
      setCurrent(null);
      loadNext();
    });

    var gotoBtn = document.getElementById("goto-session-end");
    if (gotoBtn) gotoBtn.addEventListener("click", function () {
      if (currentProblem) updateSession(currentProblem.problem_id, { state: "skipped" });
      setCurrent(null);
      showComposer(false);
      if (sessionStorage.getItem(MODE_KEY) === "batch") {
        window.location = "session-end";
      } else {
        sessionStorage.removeItem(MODE_KEY);
        stream.innerHTML = "<p class='muted'>本轮练习已提前结束。</p>";
        if (startArea) startArea.classList.remove("hidden");
      }
    });
  }

  /* ---------- session-end ---------- */

  var pending = document.getElementById("pending-ratings");
  if (pending) {
    var unrated = session().filter(function (item) { return item.state === "unrated"; });
    if (!unrated.length) {
      pending.innerHTML = "<p>没有待评的题。</p>";
    } else {
      var remaining = unrated.length;
      unrated.forEach(function (item) {
        api("/problem/" + item.problem_id).then(function (detail) {
          var problem = detail.problem;
          var card = document.createElement("article");
          card.className = "pending-rating-card card";
          card.dataset.pid = item.problem_id;
          card.innerHTML = "<p class='context-line'>题目 · " + escapeHtml(item.problem_id) + "</p>"
          + "<div class='problem-text rich-text'>" + richText(problem.problem_text) + "</div>"
          + "<p class='section-kicker'>我的作答</p><div class='rich-text'>" + richText(item.answer_text || "（未作答）") + "</div>"
          + "<p class='section-kicker'>解析</p><div class='rich-text'>" + richText(problem.solution || "（本题无解析）") + "</div>";
          var rating = document.createElement("input");
          rating.id = "end-rating";
          rating.type = "number";
          rating.min = "1";
          rating.max = "5";
          rating.placeholder = "输入 1–5";
          var note = document.createElement("textarea");
          note.id = "end-note";
          note.placeholder = "可选备注";
          var save = document.createElement("button");
          save.id = "end-save";
          save.className = "primary sm";
          save.textContent = "保存评分";
          save.addEventListener("click", function () {
            var value = parseInt(rating.value, 10);
            if (value < 1 || value > 5) return;
            post("/feedback", {
              item_type: "problem", item_id: item.problem_id,
              rating: value, note: note.value.trim(),
            }).then(function () {
              updateSession(item.problem_id, { state: "rated" });
              card.remove();
              remaining -= 1;
              if (!remaining) pending.innerHTML = "<p>全部评完 ✓</p>";
            });
          });
          card.appendChild(rating);
          card.appendChild(note);
          card.appendChild(save);
          pending.appendChild(card);
          renderMath(card);
        });
      });
    }
    var similar = document.getElementById("practice-similar");
    if (similar) similar.addEventListener("click", function () {
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(MODE_KEY);
      api("/weak?limit=200").then(function (items) {
        store(KPS_KEY, items.map(function (item) { return item.kp_id; }));
        sessionStorage.setItem(SIMILAR_KEY, "1");
        window.location = "practice";
      });
    });
  }

  /* ---------- AI column ---------- */

  var messages = document.getElementById("ai-messages");
  var aiInput = document.getElementById("ai-input");
  var aiSend = document.getElementById("ai-send");
  var aiStop = document.getElementById("ai-stop");
  var aiStatus = document.getElementById("ai-status");
  var aiDraft = document.getElementById("ai-include-draft");
  var aiConversation = load(AI_CONVERSATION_KEY, "");
  var aiTurn = null;
  var aiPollTimer = null;
  var aiPollSequence = 0;
  var aiStreamingMessage = null;

  function aiAddMarkdown(text, cls) {
    aiAdd(richText(text || ""), cls);
  }

  function aiAdd(html, cls) {
    var div = document.createElement("div");
    div.className = "msg " + (cls || "ai");
    div.innerHTML = "<div class='rich-text'>" + html + "</div>";
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    renderMath(div);
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
    aiStreamingMessage.innerHTML = "<div class='rich-text'>"
      + richText(aiStreamingMessage.content) + "</div>";
    messages.scrollTop = messages.scrollHeight;
    renderMath(aiStreamingMessage);
  }

  function aiSetStatus(text) {
    if (aiStatus) aiStatus.textContent = text || "";
  }

  function aiSetRunning(running) {
    if (aiSend) aiSend.disabled = running || !aiConversation;
    if (aiStop) aiStop.classList.toggle("hidden", !running);
    if (aiInput) aiInput.disabled = running;
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
    messages.innerHTML = "";
    aiStreamingMessage = null;
    (record.messages || []).forEach(function (message) {
      aiAddMarkdown(message.content || "", message.role === "user" ? "user" : "ai");
    });
    aiSetRunning(record.status === "running");
    aiSetStatus(record.status === "running" ? "Agent 正在处理…" : "");
    if (record.status === "running" && record.current_turn_id) {
      aiTurn = record.current_turn_id;
      aiPollConversationTurn();
    }
  }

  function aiLoadConversation(conversationId) {
    if (!conversationId) return Promise.resolve();
    aiConversation = conversationId;
    store(AI_CONVERSATION_KEY, conversationId);
    return api("/ai/sessions/" + encodeURIComponent(conversationId)).then(function (record) {
      aiRenderConversation(record);
    });
  }

  function aiContextBody(message) {
    var body = {
      message: message,
      route: window.location.pathname || "",
      page_type: layout.dataset.page || "unknown",
      recent_objects: load(AI_RECENT_KEY, []),
    };
    if (layout.dataset.objectType) body.object_type = layout.dataset.objectType;
    if (layout.dataset.objectId) body.object_id = layout.dataset.objectId;
    if (layout.dataset.page === "kp") body.kp_id = layout.dataset.objectId;
    if (layout.dataset.page === "practice" && currentProblem) {
      body.problem_id = currentProblem.problem_id;
      body.practice_mode = sessionStorage.getItem(MODE_KEY) || "";
      body.progress = { seen: session().length };
      if (aiDraft && aiDraft.checked) {
        body.include_draft = true;
        body.draft_answer = answerBox ? answerBox.value : (currentProblem.answer_text || "");
        body.draft_note = feedbackNote ? feedbackNote.value : "";
      }
    }
    if (layout.dataset.page === "graph") {
      body.selected_kp_id = selectedGraphKpId;
      body.graph_filter = {
        query: (document.getElementById("graph-search") || {}).value || "",
        state: (document.getElementById("graph-state-filter") || {}).value || "",
      };
    }
    return body;
  }

  function aiAppendEvents(data) {
    (data.events || []).forEach(function (event) {
      aiPollSequence = Math.max(aiPollSequence, event.sequence || 0);
      if (event.kind === "text") aiAppendAssistantText(event.text || "");
      else if (event.kind === "error") aiSetStatus(event.text || "Agent 返回错误");
      else if (event.kind === "phase" && event.label !== "provider.started") aiSetStatus(event.label || "");
    });
    if (!data.turn) return;
    if (data.turn.status === "done") {
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("");
      aiLoadConversation(aiConversation);
      if (typeof aiRefreshSessionList === "function") aiRefreshSessionList();
    } else if (data.turn.status === "failed") {
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("Agent 失败：" + (data.turn.error || "未知错误"));
    } else if (data.turn.status === "cancelled") {
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("本轮已停止。");
    }
  }

  function aiPollConversationTurn() {
    if (!aiConversation || !aiTurn) return;
    if (aiPollTimer) clearTimeout(aiPollTimer);
    api("/ai/sessions/" + encodeURIComponent(aiConversation) + "/turns/"
      + encodeURIComponent(aiTurn) + "?after=" + aiPollSequence).then(function (data) {
      aiAppendEvents(data);
      if (data.turn && (data.turn.status === "running" || data.turn.status === "queued")) {
        aiPollTimer = setTimeout(aiPollConversationTurn, 350);
      }
    }).catch(function () {
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("无法读取 Agent 进度。");
    });
  }

  function aiSendMessage() {
    var message = aiInput ? aiInput.value.trim() : "";
    if (!message || !aiConversation || aiTurn) return;
    aiStreamingMessage = null;
    aiAddMarkdown(message, "user");
    aiInput.value = "";
    aiSetRunning(true);
    aiSetStatus("正在发送…");
    post("/ai/sessions/" + encodeURIComponent(aiConversation) + "/turns", aiContextBody(message))
      .then(function (turn) {
        aiTurn = turn.turn_id;
        aiPollSequence = 0;
        aiPollConversationTurn();
      }).catch(function (err) {
        aiSetRunning(false);
        aiSetStatus("发送失败：" + (err.message || "未知错误"));
      });
  }

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
  var aiSessionList = document.getElementById("ai-session-list");
  var aiSessionEmpty = document.getElementById("ai-session-empty");
  var aiNewSession = document.getElementById("ai-new-session");
  var aiProviderPicker = document.getElementById("ai-provider-picker");
  var aiProviderOptions = document.getElementById("ai-provider-options");
  var aiChatView = document.getElementById("ai-chat-view");
  var aiSessionBack = document.getElementById("ai-session-back");
  var aiSessionRecords = [];
  var aiProviders = [];

  if (aiSessionBack) {
    aiSessionBack.setAttribute("aria-label", "返回对话列表");
    aiSessionBack.title = "返回对话列表";
  }

  function aiSetView(view) {
    if (!aiSessionListView || !aiProviderPicker || !aiChatView) return;
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

  function aiShowProviderPicker() {
    if (!aiProviderOptions) return;
    aiSetView("picker");
    aiProviderOptions.innerHTML = "";
    aiProviders.forEach(function (provider) {
      var button = document.createElement("button");
      button.className = "outline sm ai-provider-option";
      button.type = "button";
      button.dataset.provider = provider.name;
      button.textContent = provider.name + (provider.model ? " · " + provider.model : "");
      button.addEventListener("click", function () { aiCreateSession(provider.name); });
      aiProviderOptions.appendChild(button);
    });
    if (!aiProviders.length) aiSetStatus("未发现可用 Agent CLI。");
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

  function aiCreateSession(provider) {
    post("/ai/sessions", { provider: provider }).then(function (record) {
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
    aiTurn = null;
    aiConversation = "";
    sessionStorage.removeItem(AI_CONVERSATION_KEY);
    aiSetView("list");
    aiRefreshSessionList();
  });
  if (aiSessionList) {
    aiSetView("list");
    Promise.all([
      api("/ai/providers").then(function (items) { aiProviders = items || []; }),
      aiRefreshSessionList(),
    ]).catch(function () { aiSetStatus("Agent 服务暂不可用。"); });
  }
  if (layout.dataset.objectType && layout.dataset.objectId) {
    aiRecordRecent(layout.dataset.objectType, layout.dataset.objectId);
  }

  /* ---------- page init ---------- */

  var middleRoot = document.getElementById("middle");
  if (middleRoot) {
    renderMath(middleRoot);
    middleRoot.querySelectorAll("img").forEach(function (img) {
      img.addEventListener("error", function () {
        var alt = img.getAttribute("alt") || "图";
        img.outerHTML = "<span class='fig-missing'>（图缺失：" + escapeHtml(alt) + "）</span>";
      });
    });
  }

  function fitAiColumn() {
    if (window.innerWidth < 1024) layout.setAttribute("data-ai-collapsed", "1");
    else layout.removeAttribute("data-ai-collapsed");
  }
  fitAiColumn();
  window.addEventListener("resize", fitAiColumn);

})();
