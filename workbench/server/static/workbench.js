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
  var AI_PROVIDER_KEY = "wb_ai_provider_" + WS;
  var AI_RECENT_KEY = "wb_ai_recent_" + WS;
  var AI_DAILY_KEY = "wb_ai_daily_" + WS;
  var AI_DAILY_DATE_KEY = "wb_ai_daily_date_" + WS;
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
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function richText(text) {
    return escapeHtml(text)
      .replace(/\$\$([\s\S]+?)\$\$/g, function (_, m) {
        return "<span class='math display'>" + m + "</span>";
      })
      .replace(/\$([^$\n]+)\$/g, function (_, m) {
        return "<span class='math'>" + m + "</span>";
      })
      .replace(/\n/g, "<br>");
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
      graphDetail.innerHTML = "<p class='side-label'>知识点详情</p><h2>"
        + escapeHtml(node.title) + "</h2><p class='item-id'>" + escapeHtml(node.id)
        + "</p><p class='graph-detail-body'>" + richText(node.body || "暂无正文")
        + "</p><p class='graph-fragile-summary'>薄弱说明：" + escapeHtml(node.fragile || "—") + "</p>"
        + "<label for='graph-state'>当前学习状态</label>";
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
      var body = document.createElement("textarea");
      body.id = "graph-body";
      body.rows = 5;
      body.value = node.body || "";
      body.placeholder = "知识点正文";
      var fragile = document.createElement("input");
      fragile.id = "graph-fragile";
      fragile.value = node.fragile || "";
      fragile.placeholder = "薄弱说明";
      var contentSave = document.createElement("button");
      contentSave.id = "graph-content-save";
      contentSave.className = "outline sm";
      contentSave.textContent = "保存内容";
      contentSave.addEventListener("click", function () {
        post("/graph/kp", {
          kp_id: node.id, body: body.value, fragile: fragile.value,
        }).then(function (data) {
          node.body = data.body;
          node.fragile = data.fragile;
          renderGraphDetail(node);
        });
      });
      graphDetail.appendChild(body);
      graphDetail.appendChild(fragile);
      graphDetail.appendChild(contentSave);
      appendRelatedProblems(node);
      showGraphPanel(true);
    }

    function appendRelatedProblems(node) {
      api("/kp/" + node.id).then(function (detail) {
        var problems = detail.problems || [];
        if (!problems.length) return;
        var heading = document.createElement("p");
        heading.className = "side-label";
        heading.textContent = "关联题目状态";
        graphDetail.appendChild(heading);
        problems.forEach(function (problem) {
          var row = document.createElement("section");
          row.id = "graph-problem-" + problem.problem_id;
          row.className = "graph-problem-state";
          row.innerHTML = "<p>" + escapeHtml(problem.display_title || problem.problem_id)
            + "</p><span class='item-id'>" + escapeHtml(problem.topic_label || "未分类") + " · "
            + escapeHtml(problem.problem_id) + "</span>";
          var state = document.createElement("select");
          state.id = "graph-problem-state";
          state.innerHTML = "<option value='needs_work'>待攻克</option>"
            + "<option value='review'>待复习</option><option value='mastered'>已掌握</option>";
          state.value = problem.current_state ? problem.current_state.state : "review";
          var save = document.createElement("button");
          save.id = "graph-problem-save";
          save.className = "outline sm";
          save.textContent = "保存状态";
          save.addEventListener("click", function () {
            post("/graph/state", {
              item_type: "problem", item_id: problem.problem_id, state: state.value,
            }).then(function (data) {
              problem.current_state = { state: data.state };
              save.textContent = "已保存";
            });
          });
          row.appendChild(state);
          row.appendChild(save);
          graphDetail.appendChild(row);
        });
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

  function updateAiContext() {
    var el = document.getElementById("ai-context");
    if (!el) return;
    var pageLabels = {
      practice: "练习", kp: "知识点", kps: "知识点列表",
      graph: "知识图谱", "session-end": "统一自评",
    };
    var label = pageLabels[layout.dataset.page] || "工作台";
    if (currentProblem) label += " · 当前题 " + currentProblem.problem_id;
    else if (layout.dataset.objectId) label += " · " + layout.dataset.objectId;
    el.textContent = "当前页面：" + label;
  }

  function currentKps() {
    return load(KPS_KEY, []);
  }

  function setCurrent(problem) {
    currentProblem = problem || null;
    store(CURRENT_KEY, currentProblem);
    if (currentProblem) recordRecent("problem", currentProblem.problem_id);
    updateAiContext();
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
        + "<div class='problem-text'>" + richText(problem.problem_text) + "</div></article>";
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
          + "<div>" + richText(solution) + "</div></section>";
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
            + "<div class='problem-text'>" + richText(problem.problem_text) + "</div>"
            + "<p class='section-kicker'>我的作答</p><p>" + richText(item.answer_text || "（未作答）") + "</p>"
            + "<p class='section-kicker'>解析</p><p>" + richText(problem.solution || "（本题无解析）") + "</p>";
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
  var aiProvider = document.getElementById("ai-provider");
  var aiSession = document.getElementById("ai-session");
  var aiNew = document.getElementById("ai-new");
  var aiDaily = document.getElementById("ai-daily");
  var aiSend = document.getElementById("ai-send");
  var aiStop = document.getElementById("ai-stop");
  var aiStatus = document.getElementById("ai-status");
  var aiDraft = document.getElementById("ai-include-draft");
  var aiConversation = load(AI_CONVERSATION_KEY, "");
  var aiTurn = null;
  var aiPollTimer = null;
  var aiPollSequence = 0;

  function aiAdd(html, cls) {
    var div = document.createElement("div");
    div.className = "msg " + (cls || "ai");
    div.innerHTML = html;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    renderMath(div);
  }

  function aiTask(operation) {
    var current = load(CURRENT_KEY, null);
    if (!current || !currentProblem || current.problem_id !== currentProblem.problem_id) {
      aiAdd("<p>先打开一道题再发起讲解/诊断。</p>", "user");
      return;
    }
    var note = aiInput ? aiInput.value.trim() : "";
    var body = { problem_id: currentProblem.problem_id, note: note };
    if (current.answer_text) {
      body.user_answer = current.answer_text;
    } else {
      aiAdd("<p>本题尚未作答，将不附作答文本。</p>", "user");
    }
    if (stuckStep) {
      body.stuck_step = stuckStep;
    }
    aiAdd("<p>已发起：" + operation + " " + currentProblem.problem_id + "</p>", "user");
    if (aiInput) aiInput.value = "";
    post("/ai/" + operation, body).then(function (data) {
      pollJob(data.job_id, operation, currentProblem.problem_id);
    }).catch(function () {
      aiAdd("<p>桥接不可用：请先配置 provider（wb bridge add）。记录不受影响。</p>");
    });
  }

  function pollJob(jobId, operation, problemId) {
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      api("/ai/jobs/" + jobId).then(function (status) {
        if (status.state === "done") {
          clearInterval(timer);
          api("/explain/" + problemId).then(function (data) {
            aiAdd(renderResult(data.markdown, operation), "ai");
          });
        } else if (status.state === "failed") {
          clearInterval(timer);
          aiAdd("<p>任务失败：" + escapeHtml(status.error || "未知原因") + "</p>");
        } else if (tries > 60) {
          clearInterval(timer);
          aiAdd("<p>任务尚未完成。<button id='retry-poll' class='outline sm'>"
            + "重试查询</button></p>");
          var retry = document.getElementById("retry-poll");
          if (retry) {
            retry.addEventListener("click", function () {
              pollJob(jobId, operation, problemId);
            });
          }
        }
      }).catch(function (err) {
        if (err && err.message === "404") {
          return; /* job record not visible yet — keep polling */
        }
        clearInterval(timer);
        aiAdd("<p>状态查询失败。</p>");
      });
    }, 2000);
  }

  function renderResult(markdown, operation) {
    var html = "<p><b>" + operation + " 结果</b></p>";
    markdown.split(/\n## /).forEach(function (section) {
      var lines = section.trim().split("\n");
      var title = lines.shift().replace(/^#+\s*/, "");
      if (!title) return;
      html += "<div class='section'><h4>" + escapeHtml(title) + "</h4><p>"
        + richText(lines.join("\n")) + "</p></div>";
    });
    return html;
  }

  var explain = document.getElementById("ai-explain");
  var diagnose = document.getElementById("ai-diagnose");
  var fresh = document.getElementById("ai-new");
  var send = document.getElementById("ai-send");
  if (explain) explain.addEventListener("click", function () { aiTask("explain"); });
  if (diagnose) diagnose.addEventListener("click", function () { aiTask("diagnose"); });
  if (false && send) send.addEventListener("click", function () { aiTask("explain"); });
  if (false && fresh) fresh.addEventListener("click", function () {
    messages.innerHTML = "";
    aiAdd("<p>新会话已开始（记录仍在池中）。</p>");
  });

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
    messages.innerHTML = "";
    (record.messages || []).forEach(function (message) {
      aiAdd(richText(message.content || ""), message.role === "user" ? "user" : "ai");
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
    if (aiSession) aiSession.value = conversationId;
    return api("/ai/sessions/" + encodeURIComponent(conversationId)).then(aiRenderConversation);
  }

  function aiPopulateSessions(items) {
    if (!aiSession) return;
    aiSession.innerHTML = "";
    (items || []).forEach(function (item) {
      var option = document.createElement("option");
      option.value = item.conversation_id;
      option.textContent = item.conversation_id + " · " + item.provider;
      aiSession.appendChild(option);
    });
    var preferred = aiConversation || (items && items[0] && items[0].conversation_id);
    if (preferred) aiLoadConversation(preferred);
  }

  function aiCreateConversation() {
    var provider = aiProvider && aiProvider.value;
    if (!provider) return;
    post("/ai/sessions", { provider: provider }).then(function (record) {
      aiConversation = record.conversation_id;
      store(AI_CONVERSATION_KEY, aiConversation);
      if (messages) messages.innerHTML = "";
      aiLoadConversation(aiConversation);
    }).catch(function (err) {
      aiSetStatus("无法新建对话：" + (err.message || "未知错误"));
    });
  }

  function aiLocalDate() {
    var now = new Date();
    return now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0")
      + "-" + String(now.getDate()).padStart(2, "0");
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
      if (event.kind === "text") aiAdd(richText(event.text || ""), "ai");
      else if (event.kind === "error") aiSetStatus(event.text || "Agent 返回错误");
      else if (event.kind === "phase" && event.label !== "provider.started") aiSetStatus(event.label || "");
    });
    if (!data.turn) return;
    if (data.turn.status === "done") {
      aiTurn = null;
      aiSetRunning(false);
      aiSetStatus("");
      aiLoadConversation(aiConversation);
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
    aiAdd(richText(message), "user");
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

  if (aiProvider) {
    api("/ai/providers").then(function (providers) {
      aiProvider.innerHTML = "";
      (providers || []).forEach(function (provider) {
        var option = document.createElement("option");
        option.value = provider.name;
        option.textContent = provider.name + (provider.model ? " · " + provider.model : "");
        aiProvider.appendChild(option);
      });
      var remembered = localStorage.getItem(AI_PROVIDER_KEY);
      if (remembered && (providers || []).some(function (provider) { return provider.name === remembered; })) {
        aiProvider.value = remembered;
      } else if (providers && providers[0]) {
        aiProvider.value = providers[0].name;
      }
      if (aiProvider.value) localStorage.setItem(AI_PROVIDER_KEY, aiProvider.value);
      api("/ai/sessions").then(function (sessions) {
        aiPopulateSessions(sessions);
        var today = aiLocalDate();
        if (aiDaily && aiDaily.checked && localStorage.getItem(AI_DAILY_DATE_KEY) !== today
          && !sessions.some(function (item) { return item.status === "running"; })) {
          localStorage.setItem(AI_DAILY_DATE_KEY, today);
          aiCreateConversation();
        }
      }).catch(function () {
        aiSetStatus("无法读取最近对话。");
      });
    }).catch(function () {
      aiSetStatus("未发现可用 Agent CLI。");
    });
    aiProvider.addEventListener("change", function () {
      localStorage.setItem(AI_PROVIDER_KEY, aiProvider.value);
    });
  }
  if (aiSession) aiSession.addEventListener("change", function () {
    aiTurn = null;
    aiLoadConversation(aiSession.value);
  });
  if (aiNew) aiNew.addEventListener("click", aiCreateConversation);
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
  if (aiDaily) {
    aiDaily.checked = localStorage.getItem(AI_DAILY_KEY) === "1";
    aiDaily.addEventListener("change", function () {
      localStorage.setItem(AI_DAILY_KEY, aiDaily.checked ? "1" : "0");
    });
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

  var aiCollapse = document.getElementById("ai-collapse");
  var AI_COLLAPSED_KEY = "wb_ai_collapsed_" + WS;
  if (layout && aiCollapse) {
    function applyAiCollapsed(collapsed, persist) {
      if (collapsed) layout.setAttribute("data-ai-collapsed", "1");
      else layout.removeAttribute("data-ai-collapsed");
      aiCollapse.textContent = collapsed ? "›" : "‹";
      aiCollapse.title = collapsed ? "展开" : "折叠";
      if (persist) {
        sessionStorage.setItem(AI_COLLAPSED_KEY, collapsed ? "1" : "0");
      }
    }
    var remembered = sessionStorage.getItem(AI_COLLAPSED_KEY) === "1";
    applyAiCollapsed(window.innerWidth < 1024 || remembered, false);
    aiCollapse.addEventListener("click", function () {
      applyAiCollapsed(!layout.hasAttribute("data-ai-collapsed"), true);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth < 1024) {
        layout.setAttribute("data-ai-collapsed", "1");
      } else if (sessionStorage.getItem(AI_COLLAPSED_KEY) !== "1") {
        layout.removeAttribute("data-ai-collapsed");
      }
    });
  }

  updateAiContext();
})();
