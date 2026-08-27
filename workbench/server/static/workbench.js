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
    var source = text == null ? "" : String(text);
    source = source.replace(/<(sup|sub)>([^<>]+)<\/\1>/g, function (_, tag, content) {
      return token("<" + tag + ">" + escapeHtml(content) + "</" + tag + ">");
    });
    var value = escapeHtml(source);
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
    var graphAdjacency = new Map();
    var graphView = { x: 0, y: 0, scale: 1 };
    var graphAutoFit = true;
    var draggedNode = null;
    var panStart = null;
    var reducedGraphMotion = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function actionReminder(node) {
      return node.state === "needs_work" ? "重点练习"
        : node.state === "review" ? "可以复习" : "";
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
      graphDetail.innerHTML = "<p class='side-label'>学习看板</p><h2>"
        + escapeHtml(node.title) + "</h2>"
        + (actionReminder(node) ? "<p class='action-reminder'>"
          + actionReminder(node) + "</p>" : "");
      var link = document.createElement("a");
      link.id = "graph-open-kp";
      link.className = "graph-dashboard-link";
      link.href = "/w/" + encodeURIComponent(WS) + "/kp/" + encodeURIComponent(node.id);
      link.textContent = "打开知识点";
      graphDetail.appendChild(link);
      showGraphPanel(true);
    }

    function clearGraphFocus() {
      graphNodeElements.forEach(function (elements) {
        ["graph-focus-selected", "graph-focus-near", "graph-focus-mid", "graph-focus-far"]
          .forEach(function (name) {
            elements.node.classList.remove(name);
            elements.label.classList.remove(name);
          });
      });
      graphEdgeElements.forEach(function (entry) {
        entry.element.classList.remove("graph-focus-near");
        entry.element.classList.remove("graph-focus-mid");
        entry.element.classList.remove("graph-focus-far");
      });
    }

    function focusGraph(nodeId) {
      clearGraphFocus();
      var distances = new Map([[nodeId, 0]]);
      var pending = [nodeId];
      while (pending.length) {
        var current = pending.shift();
        var distance = distances.get(current);
        if (distance >= 2) continue;
        (graphAdjacency.get(current) || []).forEach(function (neighbor) {
          if (!distances.has(neighbor)) {
            distances.set(neighbor, distance + 1);
            pending.push(neighbor);
          }
        });
      }
      graphNodeElements.forEach(function (elements, id) {
        var distance = distances.get(id);
        var name = distance === 0 ? "graph-focus-selected"
          : distance === 1 ? "graph-focus-near"
            : distance === 2 ? "graph-focus-mid" : "graph-focus-far";
        elements.node.classList.add(name);
        elements.label.classList.add(name);
      });
      graphEdgeElements.forEach(function (entry) {
        var sourceDistance = distances.get(entry.edge.source);
        var targetDistance = distances.get(entry.edge.target);
        var name = sourceDistance <= 1 && targetDistance <= 1 ? "graph-focus-near"
          : sourceDistance !== undefined && targetDistance !== undefined
            ? "graph-focus-mid" : "graph-focus-far";
        entry.element.classList.add(name);
      });
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
      graphAdjacency = new Map(nodes.map(function (node) { return [node.id, []]; }));
      edges.forEach(function (edge) {
        graphAdjacency.get(edge.source).push(edge.target);
        graphAdjacency.get(edge.target).push(edge.source);
      });
      graphSimulation = GraphPhysics.layoutGraph(
        nodes, edges, graphCanvas.clientWidth, graphCanvas.clientHeight,
      );
      graphAutoFit = true;
      var edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      edgeLayer.setAttribute("class", "graph-edge-layer");
      edgeLayer.setAttribute("aria-hidden", "true");
      stage.appendChild(edgeLayer);
      graphSimulation.edges.forEach(function (edge) {
        var link = document.createElementNS("http://www.w3.org/2000/svg", "path");
        link.setAttribute("class", "graph-edge");
        edgeLayer.appendChild(link);
        graphEdgeElements.push({ element: link, edge: edge });
      });
      graphSimulation.nodes.forEach(function (node) {
        var button = document.createElement("button");
        button.className = "graph-node " + (node.state || "unmarked");
        button.dataset.kpId = node.id;
        button.style.width = (node.radius * 2) + "px";
        button.style.height = (node.radius * 2) + "px";
        button.setAttribute("aria-label", node.title);
        button.title = node.title;
        button.addEventListener("click", function () {
          renderGraphDetail(node);
          focusGraph(node.id);
        });
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
      graphEdgeElements.forEach(function (entry, index) {
        var source = entry.edge.sourceNode;
        var target = entry.edge.targetNode;
        var dx = target.x - source.x;
        var dy = target.y - source.y;
        var length = Math.max(1, Math.hypot(dx, dy));
        var bend = Math.min(22, length * 0.08) * (index % 2 ? 1 : -1);
        var controlX = (source.x + target.x) / 2 - dy / length * bend;
        var controlY = (source.y + target.y) / 2 + dx / length * bend;
        entry.element.setAttribute("d", "M " + source.x + " " + source.y
          + " Q " + controlX + " " + controlY + " " + target.x + " " + target.y);
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
    graphCanvas.addEventListener("click", function (event) {
      if (event.target === graphCanvas || event.target === graphStage) clearGraphFocus();
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
  var scopedMatch = String(window.location.search || "").match(/[?&]kp=([^&]+)/);
  var scopedKpId = layout.dataset.practiceKpId || (scopedMatch && decodeURIComponent(scopedMatch[1])) || "";
  var storedKps = load(KPS_KEY, []);
  if (stream && scopedKpId && (storedKps.length !== 1 || storedKps[0] !== scopedKpId)) {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(CURRENT_KEY);
    sessionStorage.removeItem(MODE_KEY);
    store(KPS_KEY, [scopedKpId]);
    currentProblem = null;
  }

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
    var practiceError = document.getElementById("practice-error");
    var retryPractice = document.getElementById("retry-practice");

    function showPracticeError(error, retryable) {
      if (!practiceError) return;
      practiceError.textContent = "请求未完成：" + (error.message || error || "未知错误");
      practiceError.classList.remove("hidden");
      if (retryPractice) retryPractice.classList.toggle("hidden", !retryable);
    }

    function clearPracticeError() {
      if (!practiceError) return;
      practiceError.textContent = "";
      practiceError.classList.add("hidden");
      if (retryPractice) retryPractice.classList.add("hidden");
    }

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
        + "<p class='context-line'>练习题</p><h2>"
        + escapeHtml(problem.display_title || "未命名题目") + "</h2>"
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
      clearPracticeError();
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
      }).catch(function (error) { showPracticeError(error, true); });
    }

    function startSession() {
      var mode = selectedMode();
      if (!mode) return;
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.setItem(MODE_KEY, mode);
      if (scopedKpId) {
        store(KPS_KEY, [scopedKpId]);
        if (startArea) startArea.classList.add("hidden");
        loadNext();
        return;
      }
      api("/weak?limit=200").then(function (items) {
        store(KPS_KEY, items.map(function (item) { return item.kp_id; }));
        if (startArea) startArea.classList.add("hidden");
        loadNext();
      }).catch(showPracticeError);
    }

    function bindMode(mode) {
      if (mode) mode.addEventListener("change", function () {
        startPractice.disabled = !selectedMode();
      });
    }

    bindMode(modeImmediate);
    bindMode(modeBatch);
    var restoredMode = sessionStorage.getItem(MODE_KEY);
    var hasPendingRatings = restoredMode === "batch" && session().some(function (item) {
      return item.state === "unrated";
    });
    if (hasPendingRatings && !currentProblem) {
      window.location = "session-end";
    } else if (restoredMode && currentProblem) {
      if (modeImmediate) modeImmediate.checked = restoredMode === "immediate";
      if (modeBatch) modeBatch.checked = restoredMode === "batch";
      if (startArea) startArea.classList.add("hidden");
      renderQuestion(currentProblem);
      answerBox.value = currentProblem.answer_text || "";
      showComposer(true);
    }
    if (startPractice) {
      startPractice.disabled = !selectedMode();
      startPractice.addEventListener("click", startSession);
    }
    if (retryPractice) retryPractice.addEventListener("click", loadNext);

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
      clearPracticeError();
      api("/problem/" + currentProblem.problem_id).then(function (detail) {
        var solution = detail.problem.solution || "（本题无解析，请基于自身作答自评）";
        stream.innerHTML += "<section class='practice-solution'><p class='section-kicker'>解析</p>"
          + "<div class='rich-text'>" + richText(solution) + "</div></section>";
        renderMath(stream);
        showAnswer.classList.add("hidden");
        feedbackArea.classList.remove("hidden");
      }).catch(showPracticeError);
    });

    if (saveRating) saveRating.addEventListener("click", function () {
      var rating = parseInt(ratingInput.value, 10);
      if (!currentProblem) return;
      if (rating < 1 || rating > 5) {
        showPracticeError("请输入 1-5 的评分");
        return;
      }
      clearPracticeError();
      post("/feedback", {
        item_type: "problem", item_id: currentProblem.problem_id,
        rating: rating, note: feedbackNote.value.trim(),
      }).then(function () {
        updateSession(currentProblem.problem_id, { state: "rated" });
        setCurrent(null);
        loadNext();
      }).catch(showPracticeError);
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
          var title = problem.display_title || "未命名题目";
          card.innerHTML = "<p class='context-line'>练习题</p><h2>" + escapeHtml(title) + "</h2>"
          + "<div class='problem-text rich-text'>" + richText(problem.problem_text) + "</div>"
          + "<p class='section-kicker'>我的作答</p><div class='rich-text'>" + richText(item.answer_text || "（未作答）") + "</div>"
          + "<p class='section-kicker'>解析</p><div class='rich-text'>" + richText(problem.solution || "（本题无解析）") + "</div>";
          var rating = document.createElement("input");
          rating.id = "end-rating-" + item.problem_id;
          rating.type = "number";
          rating.min = "1";
          rating.max = "5";
          rating.placeholder = "输入 1–5";
          var note = document.createElement("textarea");
          note.id = "end-note-" + item.problem_id;
          note.placeholder = "可选备注";
          var save = document.createElement("button");
          save.id = "end-save-" + item.problem_id;
          save.className = "primary sm";
          save.textContent = "保存评分";
          var ratingLabel = document.createElement("label");
          ratingLabel.id = "end-rating-label-" + item.problem_id;
          ratingLabel.setAttribute("for", rating.id);
          ratingLabel.textContent = "为“" + title + "”评分（1-5）";
          var noteLabel = document.createElement("label");
          noteLabel.id = "end-note-label-" + item.problem_id;
          noteLabel.setAttribute("for", note.id);
          noteLabel.textContent = "为“" + title + "”添加备注";
          var error = document.createElement("p");
          error.id = "end-error-" + item.problem_id;
          error.className = "inline-error hidden";
          error.setAttribute("aria-live", "polite");
          function showCardError(message) {
            error.textContent = message;
            error.classList.remove("hidden");
          }
          save.addEventListener("click", function () {
            var value = parseInt(rating.value, 10);
            if (value < 1 || value > 5) {
              showCardError("请输入 1-5 的评分");
              return;
            }
            post("/feedback", {
              item_type: "problem", item_id: item.problem_id,
              rating: value, note: note.value.trim(),
            }).then(function () {
              updateSession(item.problem_id, { state: "rated" });
              card.remove();
              remaining -= 1;
              if (!remaining) pending.innerHTML = "<p>全部评完 ✓</p>";
            }).catch(function (err) { showCardError(err.message || "保存失败"); });
          });
          card.appendChild(error);
          card.appendChild(ratingLabel);
          card.appendChild(rating);
          card.appendChild(noteLabel);
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
  var aiProviderLoadError = "";

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
    if (aiProviderLoadError) {
      aiProviderOptions.innerHTML = "<p class='inline-error'>Agent 服务暂不可用。请稍后重试。</p>";
    } else if (!aiProviders.length) {
      aiProviderOptions.innerHTML = "<p class='inline-error'>暂无可用 Agent。请先配置一个提供方。</p>";
    }
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
    var providerRequest = api("/ai/providers").then(function (items) {
      aiProviders = items || [];
    }).catch(function () {
      aiProviderLoadError = "Agent 服务暂不可用。";
      if (aiSessionEmpty) {
        aiSessionEmpty.textContent = aiProviderLoadError;
        aiSessionEmpty.classList.remove("hidden");
      }
    });
    Promise.all([
      providerRequest,
      aiRefreshSessionList(),
    ]);
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
