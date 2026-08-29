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
  var INCLUDE_KEY = "wb_practice_include_" + WS;
  var RATING_MODE_KEY = "wb_practice_rating_mode_" + WS;
  var SELECTION_KEY = "wb_kp_selection_" + WS;
  var AI_CONVERSATION_KEY = "wb_ai_conversation_" + WS;
  var AI_RECENT_KEY = "wb_ai_recent_" + WS;
  var selectedGraphKpId = null;

  function selectedKpIds() {
    var ids = load(SELECTION_KEY, []);
    return Array.from(new Set((Array.isArray(ids) ? ids : []).filter(Boolean)));
  }

  function saveSelectedKpIds(ids) {
    var unique = Array.from(new Set((ids || []).filter(Boolean)));
    store(SELECTION_KEY, unique);
    document.querySelectorAll("[data-kp-selection]").forEach(function (input) {
      var id = input.dataset.selectionKpId || input.dataset.kpId;
      input.checked = unique.indexOf(id) >= 0;
    });
    var count = document.getElementById("selection-count");
    if (count) count.textContent = "已选 " + unique.length + " 个知识点";
    var handoff = document.getElementById("practice-selected");
    if (handoff) handoff.disabled = !unique.length;
    renderStagedList();
    return unique;
  }

  function bindSelectionControls() {
    var ids = selectedKpIds();
    document.querySelectorAll("[data-kp-selection]").forEach(function (input) {
      var id = input.dataset.selectionKpId || input.dataset.kpId;
      input.checked = ids.indexOf(id) >= 0;
      input.addEventListener("change", function () {
        var next = selectedKpIds().filter(function (item) { return item !== id; });
        if (input.checked) next.push(id);
        saveSelectedKpIds(next);
      });
    });
    saveSelectedKpIds(ids);
    var handoff = document.getElementById("practice-selected");
    if (handoff) handoff.addEventListener("click", function () {
      if (selectedKpIds().length) window.location = "/w/" + encodeURIComponent(WS) + "/practice";
    });
  }

  bindSelectionControls();

  /* ---------- staged practice list (selection view + on-demand suggestions) ---------- */

  function renderStagedList() {
    var list = document.getElementById("staged-list");
    if (!list) return;
    var names = {};
    try { names = JSON.parse(list.dataset.kpNames || "{}") || {}; } catch (_) { names = {}; }
    var ids = selectedKpIds();
    list.innerHTML = ids.map(function (id) {
      return "<li class='staged-row' data-kp-id='" + escapeHtml(id) + "'>"
        + "<span class='staged-title'>" + escapeHtml(names[id] || id) + "</span>"
        + "<button class='ghost sm staged-remove' type='button' data-kp-id='"
        + escapeHtml(id) + "' aria-label='移除'>✕</button></li>";
    }).join("");
    var empty = document.getElementById("staged-empty");
    if (empty) empty.classList.toggle("hidden", ids.length > 0);
    updateSuggestions();
  }

  function updateSuggestions() {
    var toggle = document.getElementById("suggestions-toggle");
    if (!toggle) return;
    var container = document.getElementById("suggestion-list");
    var selected = selectedKpIds();
    var visible = 0;
    (container ? container.querySelectorAll(".suggestion-row") : []).forEach(function (row) {
      var staged = selected.indexOf(row.dataset.kpId) >= 0;
      row.classList.toggle("hidden", staged);
      if (!staged) visible += 1;
    });
    var emptyLine = document.getElementById("suggestions-empty");
    if (emptyLine) emptyLine.classList.toggle("hidden", visible > 0);
    toggle.textContent = "＋ 加今天要练的" + (visible ? "（" + visible + "）" : "");
  }

  var stagedListEl = document.getElementById("staged-list");
  if (stagedListEl) {
    stagedListEl.addEventListener("click", function (event) {
      var target = event.target;
      var button = target && target.closest ? target.closest(".staged-remove") : null;
      if (!button) return;
      saveSelectedKpIds(selectedKpIds().filter(function (id) {
        return id !== button.dataset.kpId;
      }));
    });
    var suggestionsToggle = document.getElementById("suggestions-toggle");
    var suggestionsBox = document.getElementById("suggestions");
    if (suggestionsToggle) suggestionsToggle.addEventListener("click", function () {
      var open = false;
      if (suggestionsBox) open = suggestionsBox.classList.toggle("hidden") === false;
      suggestionsToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (suggestionsBox) suggestionsBox.addEventListener("click", function (event) {
      var target = event.target;
      var button = target && target.closest ? target.closest(".suggestion-join") : null;
      if (!button) return;
      var next = selectedKpIds();
      if (next.indexOf(button.dataset.kpId) < 0) next.push(button.dataset.kpId);
      saveSelectedKpIds(next);
    });
    renderStagedList();
  }

  function bindKnowledgeSort() {
    var list = document.getElementById("knowledge-list");
    if (!list && document.querySelector) list = document.querySelector(".knowledge-list");
    var sort = document.getElementById("knowledge-sort");
    var direction = document.getElementById("knowledge-sort-direction");
    if (!list || !sort) return;
    var descending = false;
    function apply() {
      var rows = Array.from(list.children || []).filter(function (row) {
        return row && row.classList && row.classList.contains("knowledge-row");
      });
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
      if (rows.length) list.replaceChildren.apply(list, rows);
      if (direction) direction.textContent = descending ? "↓" : "↑";
    }
    sort.addEventListener("change", apply);
    if (direction) direction.addEventListener("click", function () { descending = !descending; apply(); });
    apply();
  }

  bindKnowledgeSort();

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
    var graphGravity = document.getElementById("graph-gravity");
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
    var graphProjection = "structure";
    var graphLabelZoomed = false;
    var graphFocusedId = null;
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
      graphFocusedId = null;
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
        entry.edge.distanceFactor = 1;
      });
      updateGraphLabels();
      if (graphSimulation) {
        GraphPhysics.reheat(graphSimulation, 0.3);
        runGraphSimulation();
      }
    }

    function focusGraph(nodeId) {
      graphFocusedId = nodeId;
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
        entry.edge.distanceFactor = sourceDistance <= 1 && targetDistance <= 1 ? 1.15
          : sourceDistance !== undefined && targetDistance !== undefined ? 1.08 : 1;
      });
      updateGraphLabels();
      GraphPhysics.reheat(graphSimulation, 0.35);
      runGraphSimulation();
    }

    function updateGraphLabels() {
      var search = (graphSearch && graphSearch.value || "").trim().toLowerCase();
      graphNodeElements.forEach(function (elements, id) {
        var node = graphSimulation.nodes.find(function (item) { return item.id === id; });
        var matched = search && node && (node.title + " " + node.id).toLowerCase().includes(search);
        elements.label.style.display = "";
        elements.label.setAttribute("aria-hidden", matched ? "false" : "false");
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
      GraphPhysics.applyProjection(graphSimulation.nodes, graphProjection,
        graphCanvas.clientWidth, graphCanvas.clientHeight);
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
        button.className = "graph-node " + (node.state || "unmarked")
          + (node.projection ? " projection-" + node.projection : "");
        button.dataset.kpId = node.id;
        button.style.width = (node.radius * 2) + "px";
        button.style.height = (node.radius * 2) + "px";
        if (button.style.setProperty) button.style.setProperty("--projection-score", String(node.projectionScore || 0));
        else button.style["--projection-score"] = String(node.projectionScore || 0);
        button.setAttribute("aria-label", node.title);
        button.title = node.title;
        button.addEventListener("click", function () {
          renderGraphDetail(node);
          focusGraph(node.id);
        });
        button.addEventListener("mouseenter", function () {
          graphNodeElements.get(node.id).hovered = true;
          updateGraphLabels();
        });
        button.addEventListener("mouseleave", function () {
          graphNodeElements.get(node.id).hovered = false;
          updateGraphLabels();
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
        var select = document.createElement("input");
        select.type = "checkbox";
        select.className = "graph-kp-selection";
        select.dataset.selectionKpId = node.id;
        select.setAttribute("data-kp-selection", "");
        select.setAttribute("aria-label", "选择 " + node.title);
        select.checked = selectedKpIds().indexOf(node.id) >= 0;
        select.addEventListener("pointerdown", function (event) {
          if (event.stopPropagation) event.stopPropagation();
        });
        select.addEventListener("click", function (event) {
          if (event.stopPropagation) event.stopPropagation();
        });
        select.addEventListener("change", function () {
          var next = selectedKpIds().filter(function (id) { return id !== node.id; });
          if (select.checked) next.push(node.id);
          saveSelectedKpIds(next);
        });
        stage.appendChild(select);
        var label = document.createElement("span");
        label.className = "graph-node-label";
        label.textContent = node.title;
        stage.appendChild(label);
        graphNodeElements.set(node.id, { node: button, select: select, label: label });
      });
      if (!nodes.length) {
        var empty = document.createElement("p");
        empty.className = "muted graph-empty";
        empty.textContent = "没有符合条件的知识点。";
        stage.appendChild(empty);
      }
      graphCanvas.replaceChildren(stage);
      applyGraphView();
      updateGraphLabels();
      if (reducedGraphMotion) {
        GraphPhysics.settle(graphSimulation, 1600);
        settleLabelClearance();
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
        var obstructed = graphSimulation.nodes.some(function (node) {
          if (node === source || node === target) return false;
          var ratio = Math.max(0, Math.min(1,
            ((node.x - source.x) * dx + (node.y - source.y) * dy) / (length * length)));
          return Math.hypot(node.x - source.x - ratio * dx,
            node.y - source.y - ratio * dy) < node.radius + 10;
        });
        var bend = obstructed ? Math.min(28, length * 0.1) : 0;
        var controlX = (source.x + target.x) / 2 - dy / length * bend;
        var controlY = (source.y + target.y) / 2 + dx / length * bend;
        entry.element.setAttribute("d", bend ? "M " + source.x + " " + source.y
          + " Q " + controlX + " " + controlY + " " + target.x + " " + target.y
          : "M " + source.x + " " + source.y + " L " + target.x + " " + target.y);
      });
      if (!graphSimulation) return;
      graphSimulation.nodes.forEach(function (node) {
        var elements = graphNodeElements.get(node.id);
        if (!elements) return;
        elements.node.style.left = node.x + "px";
        elements.node.style.top = node.y + "px";
        if (elements.select) {
          elements.select.style.left = (node.x + node.radius - 4) + "px";
          elements.select.style.top = (node.y - node.radius - 4) + "px";
        }
        elements.label.style.left = node.x + "px";
        elements.label.style.top = (node.y + node.radius + 6) + "px";
      });
    }

    // The force model separates node circles; wrapped labels are wide
    // rectangles a circular footprint cannot represent. After settling, one
    // deterministic pass nudges nodes until the measured label boxes stop
    // overlapping each other and nearby node circles.
    function labelBox(node) {
      var entry = graphNodeElements.get(node.id);
      var width = 168;
      var height = 16;
      if (entry && entry.label) {
        if (entry.label.offsetWidth) width = Math.min(entry.label.offsetWidth, 168);
        if (entry.label.offsetHeight) height = entry.label.offsetHeight;
      }
      return {
        x1: node.x - width / 2,
        x2: node.x + width / 2,
        y1: node.y + node.radius + 6,
        y2: node.y + node.radius + 6 + height,
      };
    }

    function boxIntersectsCircle(box, cx, cy, radius) {
      var nx = Math.max(box.x1, Math.min(cx, box.x2));
      var ny = Math.max(box.y1, Math.min(cy, box.y2));
      return Math.hypot(cx - nx, cy - ny) < radius - 2;
    }

    function resolveLabelOverlaps() {
      if (!graphSimulation) return;
      var nodes = graphSimulation.nodes;
      for (var round = 0; round < 40; round += 1) {
        var moved = false;
        for (var i = 0; i < nodes.length; i += 1) {
          for (var j = i + 1; j < nodes.length; j += 1) {
            var a = labelBox(nodes[i]);
            var b = labelBox(nodes[j]);
            var overlapX = Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1);
            var overlapY = Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1);
            var pushX = 0;
            var pushY = 0;
            if (overlapX > 0 && overlapY > 0) {
              if (overlapX <= overlapY) {
                pushX = ((nodes[i].x <= nodes[j].x ? 1 : -1)) * (overlapX / 2 + 2);
              } else {
                pushY = ((nodes[i].y <= nodes[j].y ? 1 : -1)) * (overlapY / 2 + 2);
              }
            } else if (boxIntersectsCircle(a, nodes[j].x, nodes[j].y, nodes[j].radius)
                || boxIntersectsCircle(b, nodes[i].x, nodes[i].y, nodes[i].radius)) {
              var dx = nodes[j].x - nodes[i].x;
              var dy = nodes[j].y - nodes[i].y;
              var distance = Math.max(0.01, Math.hypot(dx, dy));
              pushX = dx / distance * 4;
              pushY = dy / distance * 4;
            } else {
              continue;
            }
            if (nodes[i].fx === null) {
              nodes[i].x -= pushX;
              nodes[i].y -= pushY;
            }
            if (nodes[j].fx === null) {
              nodes[j].x += pushX;
              nodes[j].y += pushY;
            }
            moved = true;
          }
        }
        if (!moved) break;
      }
      var width = graphSimulation.width;
      var height = graphSimulation.height;
      nodes.forEach(function (node) {
        node.x = Math.max(node.radius, Math.min(width - node.radius, node.x));
        node.y = Math.max(node.radius, Math.min(height - node.radius, node.y));
      });
    }

    function settleLabelClearance() {
      resolveLabelOverlaps();
    }

    function runGraphSimulation() {
      if (!graphSimulation || reducedGraphMotion || graphFrame !== null) return;
      function frame() {
        graphFrame = null;
        var stable = GraphPhysics.tick(graphSimulation);
        if (stable) settleLabelClearance();
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
      graphLabelZoomed = true;
      graphView.scale = Math.max(0.4, Math.min(2.5, scale));
      applyGraphView();
      updateGraphLabels();
    }

    function fitGraph() {
      if (!graphSimulation || !graphSimulation.nodes.length) return;
      var xs = graphSimulation.nodes.map(function (node) { return node.x; });
      var ys = graphSimulation.nodes.map(function (node) { return node.y; });
      var minX = Math.min.apply(null, xs) - 48;
      var maxX = Math.max.apply(null, xs) + 48;
      var minY = Math.min.apply(null, ys) - 48;
      var maxY = Math.max.apply(null, ys) + 68;
      graphView.scale = 1;
      graphView.x = (graphCanvas.clientWidth - (minX + maxX) * graphView.scale) / 2;
      graphView.y = (graphCanvas.clientHeight - (minY + maxY) * graphView.scale) / 2;
      graphAutoFit = false;
      applyGraphView();
      updateGraphLabels();
    }

    if (graphSearch) graphSearch.addEventListener("input", renderGraph);
    if (graphFilter) graphFilter.addEventListener("change", renderGraph);
    if (graphGravity) graphGravity.addEventListener("input", function () {
      if (!graphSimulation) return;
      GraphPhysics.setGravity(graphSimulation, graphGravity.value);
      runGraphSimulation();
    });
    var zoomIn = document.getElementById("graph-zoom-in");
    var zoomOut = document.getElementById("graph-zoom-out");
    var graphFit = document.getElementById("graph-fit");
    var graphProjectionSelect = document.getElementById("graph-projection");
    if (graphProjectionSelect) graphProjectionSelect.addEventListener("change", function () {
      graphProjection = graphProjectionSelect.value || "structure";
      renderGraph();
    });
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
        var edge = 32;
        if (event.clientX < edge) graphView.x += 8;
        else if (event.clientX > graphCanvas.clientWidth - edge) graphView.x -= 8;
        if (event.clientY < edge) graphView.y += 8;
        else if (event.clientY > graphCanvas.clientHeight - edge) graphView.y -= 8;
        applyGraphView();
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
        GraphPhysics.setSoftAnchor(draggedNode, draggedNode.fx, draggedNode.fy);
        draggedNode.fx = null;
        draggedNode.fy = null;
        GraphPhysics.reheat(graphSimulation);
        runGraphSimulation();
      }
      draggedNode = null;
      panStart = null;
    });
    window.addEventListener("resize", renderGraph);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        if (graphFrame !== null) cancelAnimationFrame(graphFrame);
        graphFrame = null;
      }
    });
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
  var similarRound = sessionStorage.getItem(SIMILAR_KEY) === "1";
  var scopedMatch = String(window.location.search || "").match(/[?&]kp=([^&]+)/);
  var scopedKpId = layout.dataset.practiceKpId || (scopedMatch && decodeURIComponent(scopedMatch[1])) || "";
  if (scopedKpId) saveSelectedKpIds([scopedKpId]);
  var storedKps = load(KPS_KEY, []);
  var practiceDeck = PracticeDeck.deserialize(load(SESSION_KEY, null));
  // Legacy tabs stored the rendered payload of the current item separately;
  // adopt it into the deck so a refresh restores without pulling again.
  var legacyCurrent = load(CURRENT_KEY, null);
  if (legacyCurrent && practiceDeck.items.length) {
    var legacyTail = practiceDeck.items[practiceDeck.items.length - 1];
    if (legacyTail.id === legacyCurrent.problem_id && !legacyTail.payload) {
      legacyTail.payload = legacyCurrent;
    }
  }
  if (stream && scopedKpId && (storedKps.length !== 1 || storedKps[0] !== scopedKpId)) {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(CURRENT_KEY);
    sessionStorage.removeItem(MODE_KEY);
    sessionStorage.removeItem(RATING_MODE_KEY);
    store(KPS_KEY, [scopedKpId]);
    practiceDeck = PracticeDeck.deserialize(null);
  }

  function persistDeck() {
    store(SESSION_KEY, PracticeDeck.serialize(practiceDeck));
  }


  function currentProblem() {
    return PracticeDeck.current(practiceDeck);
  }

  function session() {
    return practiceDeck.items;
  }

  function currentKps() {
    return load(KPS_KEY, selectedKpIds());
  }

  function updateSession(problemId, values) {
    PracticeDeck.settle(practiceDeck, problemId, values);
    persistDeck();
  }

  if (stream) {
    var modeExam = document.getElementById("practice-mode-exam");
    var modeMicro = document.getElementById("practice-mode-micro");
    var modeFlashCard = document.getElementById("practice-mode-flash_card");
    var modeYesNo = document.getElementById("practice-mode-yes_no");
    var modeImmediate = document.getElementById("practice-mode-immediate");
    var modeBatch = document.getElementById("practice-mode-batch");
    var ratingImmediate = document.getElementById("practice-rating-immediate");
    var ratingBatch = document.getElementById("practice-rating-batch");
    var legacyModeControls = !!(modeImmediate || modeBatch);
    var actions = document.getElementById("composer-actions");
    var feedbackArea = document.getElementById("feedback-area");
    var ratingInput = document.getElementById("rating-input");
    var feedbackNote = document.getElementById("feedback-note");
    var saveRating = document.getElementById("save-rating");
    var sessionEntry = document.getElementById("session-end-entry");
    var startArea = document.getElementById("start-area");
    var practiceError = document.getElementById("practice-error");
    var retryPractice = document.getElementById("retry-practice");
    var cardNav = document.getElementById("card-nav");
    var cardPrev = document.getElementById("card-prev");
    var cardNext = document.getElementById("card-next");
    var pulling = false;
    var VERDICT_HOLD_MS = 2000;
    var advanceToken = 0;

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

    function selectedContentMode() {
      if (modeExam && modeExam.checked) return "exam";
      if (modeMicro && modeMicro.checked) return "micro";
      if (modeYesNo && modeYesNo.checked) return "yes_no";
      if (modeFlashCard && modeFlashCard.checked) return "flash_card";
      return "";
    }

    function selectedRatingMode() {
      if (ratingImmediate && ratingImmediate.checked) return "immediate";
      if (ratingBatch && ratingBatch.checked) return "batch";
      if (modeImmediate && modeImmediate.checked) return "immediate";
      if (modeBatch && modeBatch.checked) return "batch";
      return "";
    }

    function readyToStart() {
      var content = selectedContentMode() || (legacyModeControls ? "exam" : "");
      return !!content && !!selectedRatingMode()
        && (legacyModeControls || selectedKpIds().length > 0);
    }

    function microQuiz(problem) {
      var payload = problem && problem.micro_quiz;
      if (!payload || typeof payload !== "object") return null;
      return payload;
    }

    function problemOptions(problem) {
      var quiz = microQuiz(problem);
      if (quiz) {
        var type = quiz.quiz_type;
        if (type === "yes_no") return (quiz.options || ["是", "否"]).map(function (text) { return { id: text, text: text }; });
        if (type === "single_choice" || type === "multiple_choice") {
          return (quiz.options || []).map(function (text) { return { id: text, text: text }; });
        }
        return [];
      }
      var raw = problem && problem.options_json;
      if (!raw) return [];
      if (typeof raw === "string") {
        try { raw = JSON.parse(raw); } catch (_) { return []; }
      }
      if (!Array.isArray(raw)) return [];
      return raw.map(function (option, index) {
        if (typeof option === "string") return { id: String(index + 1), text: option };
        return {
          id: String(option.id || option.option_id || index + 1),
          text: String(option.text || option.label || option.value || ""),
        };
      }).filter(function (option) { return option.text; });
    }

    function showComposer(show) {
      if (composer) composer.classList.toggle("hidden", !show);
      if (sessionEntry) sessionEntry.classList.toggle("hidden", !show);
    }

    function setPracticeFocus(active) {
      var columns = document.getElementById("practice-columns");
      if (columns) columns.classList.toggle("hidden", active);
      var flow = document.querySelector(".practice-flow");
      if (active && flow && flow.scrollIntoView) flow.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function setComposerLayout(mode) {
      // "card": no answer row (reveal instead); "choice": options only;
      // "text": textarea + submit (ordinary exam answers).
      var row = document.getElementById("composer-row");
      if (row) row.classList.toggle("hidden", mode === "card");
      if (answerBox) answerBox.classList.toggle("hidden", mode !== "text");
      if (showAnswer) showAnswer.textContent = mode === "card" ? "揭示背面" : "查看解析";
    }

    function ratingNow() {
      return sessionStorage.getItem(RATING_MODE_KEY) === "immediate"
        || (legacyModeControls && sessionStorage.getItem(MODE_KEY) === "immediate");
    }

    function batchNow() {
      return sessionStorage.getItem(RATING_MODE_KEY) === "batch"
        || (legacyModeControls && sessionStorage.getItem(MODE_KEY) === "batch");
    }

    function deckItemAnswered(item) {
      if (item.kind === "card") return false;
      return !!(item.choices && item.choices.length)
        || !!(item.answer_text || "").trim()
        || item.state === "unrated" || item.state === "rated";
    }

    function verdictLine(item) {
      if (typeof item.verdict !== "boolean") return "";
      var quiz = microQuiz(item.payload) || {};
      return "<p id='micro-quiz-verdict' class='micro-verdict "
        + (item.verdict ? "ok" : "bad") + "'>"
        + (item.verdict ? "回答正确。" : "回答错误。 " + (quiz.error_reason || "")) + "</p>";
    }

    function optionHtmlFor(item) {
      var problem = item.payload || {};
      var quiz = microQuiz(problem);
      var options = problemOptions(problem);
      if (!options.length) return "";
      var multiple = !!quiz && quiz.quiz_type === "multiple_choice";
      var answered = deckItemAnswered(item);
      var keyList = multiple ? (quiz.answer_key || []) : [quiz.answer_key];
      return "<fieldset class='problem-options'" + (answered ? " disabled" : "") + "><legend>选择答案</legend>"
        + options.map(function (option) {
          var selected = answered && (item.choices || []).indexOf(option.id) >= 0;
          var correct = keyList.indexOf(option.id) >= 0;
          var classes = [];
          if (selected) classes.push("option-selected");
          if (answered && item.verdict === false && correct) classes.push("option-correct");
          return "<label" + (classes.length ? " class='" + classes.join(" ") + "'" : "") + ">"
            + "<input data-choice-option type='" + (multiple ? "checkbox" : "radio")
            + "' name='problem-option' value='" + escapeHtml(option.id) + "'"
            + (selected ? " checked disabled" : "") + "> "
            + escapeHtml(option.text) + "</label>";
        }).join("") + "</fieldset>";
    }

    function updateCardNav(item) {
      var isCard = item.kind === "card";
      if (cardNav) cardNav.classList.toggle("hidden", !isCard);
      if (!isCard) return;
      if (cardPrev) cardPrev.disabled = practiceDeck.cursor <= 0;
      if (cardNext) cardNext.disabled = pulling;
    }

    function renderDeckItem(item) {
      updateCardNav(item);
      if (item.kind === "card") {
        var back = "<section id='card-back-section' class='practice-solution"
          + (item.revealed ? "'" : " hidden'") + ">"
          + "<p class='section-kicker'>背面</p>"
          + "<div class='rich-text'>" + richText(item.payload.back || "") + "</div></section>";
        stream.innerHTML = "<article class='practice-question-card card'>"
          + "<p class='context-line'>闪卡</p>"
          + "<p class='muted'>先在心里回忆，再揭示对照。</p>"
          + "<div class='problem-text rich-text'>" + richText(item.payload.front || "") + "</div>"
          + back
          + (item.state === "rated" ? "<p class='muted'>已评分。</p>" : "")
          + "</article>";
        renderMath(stream);
        setComposerLayout("card");
        if (showAnswer) showAnswer.classList.toggle("hidden", item.revealed);
        if (feedbackArea) {
          feedbackArea.classList.toggle("hidden",
            !(ratingNow() && item.revealed && item.state !== "rated"));
        }
        if (actions) actions.classList.remove("hidden");
        return;
      }
      var problem = item.payload || {};
      var answered = deckItemAnswered(item);
      stream.innerHTML = "<article class='practice-question-card card'>"
        + "<p class='context-line'>练习题</p><h2>"
        + escapeHtml(problem.display_title || "未命名题目") + "</h2>"
        + "<div class='problem-text rich-text'>" + richText(problem.problem_text || "") + "</div>"
        + optionHtmlFor(item) + verdictLine(item) + "</article>";
      renderMath(stream);
      setComposerLayout(
        microQuiz(problem) && problemOptions(problem).length ? "choice" : "text");
      answerBox.value = (answered && !(item.choices && item.choices.length))
        ? (item.answer_text || "") : "";
      if (answered) {
        answerBox.disabled = true;
        submitAnswer.classList.add("hidden");
        actions.classList.remove("hidden");
        feedbackArea.classList.add("hidden");
      } else {
        answerBox.disabled = false;
        submitAnswer.classList.remove("hidden");
        actions.classList.add("hidden");
        feedbackArea.classList.add("hidden");
        answerBox.focus();
      }
    }

    function gradeMicroQuiz(problem, submittedTexts) {
      var quiz = microQuiz(problem);
      if (!quiz) return null;
      var type = quiz.quiz_type;
      var answer = quiz.answer_key;
      if (type === "multiple_choice") {
        if (!Array.isArray(submittedTexts) || !Array.isArray(answer)) return false;
        return submittedTexts.slice().sort().join("|") === answer.slice().sort().join("|");
      }
      return submittedTexts[0] === answer;
    }

    function finishExhausted() {
      var mode = sessionStorage.getItem(MODE_KEY);
      var ratingMode = sessionStorage.getItem(RATING_MODE_KEY);
      var emptyMessage = similarRound
        ? "暂无更多同类题。"
        : (mode === "flash_card" ? "当前范围暂无可用的闪卡，请选择其他模式。"
          : mode === "micro" ? "当前范围暂无可用的小测题目，请选择其他模式。"
          : mode === "yes_no" ? "当前范围暂无可用的 Yes / No 题目，请选择其他模式。"
            : "本轮相关题目已练完。");
      advanceToken += 1;
      practiceDeck.ended = true;
      persistDeck();
      stream.innerHTML = "<p class='muted'>" + emptyMessage + "</p>";
      similarRound = false;
      sessionStorage.removeItem(SIMILAR_KEY);
      showComposer(false);
      setPracticeFocus(false);
      if (ratingMode === "batch") window.location = "session-end";
      else {
        sessionStorage.removeItem(MODE_KEY);
        sessionStorage.removeItem(RATING_MODE_KEY);
        [modeExam, modeMicro, modeFlashCard, modeYesNo, modeImmediate, modeBatch].forEach(function (input) {
          if (input) input.checked = false;
        });
        startPractice.disabled = true;
        if (startArea) startArea.classList.remove("hidden");
      }
    }

    function cancelScheduledAdvance() {
      advanceToken += 1;
    }

    function scheduleAdvance() {
      var token = advanceToken;
      setTimeout(function () {
        if (token !== advanceToken) return;
        advance();
      }, VERDICT_HOLD_MS);
    }

    // Advance replays the presented history first; only past its end does a
    // new pull happen. This is what makes flash-card paging and the batch
    // verdict hold one rule instead of two.
    function advance() {
      cancelScheduledAdvance();
      if (!PracticeDeck.atEnd(practiceDeck)) {
        renderDeckItem(PracticeDeck.goTo(practiceDeck, practiceDeck.cursor + 1));
        persistDeck();
        return;
      }
      loadNext();
    }

    function loadNext() {
      var kps = currentKps();
      var mode = sessionStorage.getItem(MODE_KEY);
      if (!kps.length || !mode || pulling) return;
      var exclude = PracticeDeck.ids(practiceDeck);
      var includeIds = load(INCLUDE_KEY, null);
      clearPracticeError();
      pulling = true;
      if (mode === "flash_card") {
        api("/pull-cards", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kp_ids: kps, exclude_ids: exclude }),
        }).then(function (result) {
          pulling = false;
          var card = (result.cards || [])[0];
          if (!card) {
            finishExhausted();
            return;
          }
          PracticeDeck.append(practiceDeck, {
            id: card.card_id, kind: "card",
            payload: { card_id: card.card_id, front: card.front, back: card.back },
          });
          persistDeck();
          renderDeckItem(PracticeDeck.current(practiceDeck));
          ratingInput.value = "";
          feedbackNote.value = "";
          showComposer(true);
        }).catch(function (error) { pulling = false; showPracticeError(error, true); });
        return;
      }
      var pullBody = {
        kp_ids: kps, n: 1,
        mode: mode,
        exclude_ids: exclude,
      };
      if (includeIds && includeIds.length) pullBody.include_ids = includeIds;
      api("/pull", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pullBody),
      }).then(function (result) {
        pulling = false;
        sessionStorage.removeItem(INCLUDE_KEY);
        if (!result.problems.length) {
          finishExhausted();
          return;
        }
        var problem = result.problems[0];
        PracticeDeck.append(practiceDeck, {
          id: problem.problem_id, kind: "problem", payload: problem,
        });
        persistDeck();
        recordRecent("problem", problem.problem_id);
        renderDeckItem(PracticeDeck.current(practiceDeck));
        showComposer(true);
      }).catch(function (error) { pulling = false; showPracticeError(error, true); });
    }

    function startSession() {
      var contentMode = selectedContentMode();
      var ratingMode = selectedRatingMode();
      if (legacyModeControls && !ratingMode) ratingMode = selectedRatingMode();
      if (!contentMode && legacyModeControls) contentMode = "exam";
      if (!contentMode || !ratingMode) return;
      advanceToken += 1;
      practiceDeck = PracticeDeck.deserialize(null);
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.setItem(MODE_KEY, contentMode);
      sessionStorage.setItem(RATING_MODE_KEY, ratingMode);
      if (legacyModeControls && scopedKpId) {
        store(KPS_KEY, [scopedKpId]);
        if (startArea) startArea.classList.add("hidden");
        setPracticeFocus(true);
        loadNext();
        return;
      }
      if (legacyModeControls) {
        api("/weak?limit=200").then(function (items) {
          store(KPS_KEY, items.map(function (item) { return item.kp_id; }));
          if (startArea) startArea.classList.add("hidden");
          setPracticeFocus(true);
          loadNext();
        }).catch(showPracticeError);
        return;
      }
      var ids = selectedKpIds();
      if (!ids.length) {
        if (practiceError) showPracticeError("请先在知识点视图选择范围", false);
        return;
      }
      store(KPS_KEY, ids);
      if (startArea) startArea.classList.add("hidden");
      setPracticeFocus(true);
      loadNext();
    }

    function bindMode(mode) {
      if (mode) mode.addEventListener("change", function () {
        startPractice.disabled = !readyToStart();
      });
    }

    bindMode(modeExam);
    bindMode(modeMicro);
    bindMode(modeFlashCard);
    bindMode(modeYesNo);
    bindMode(modeImmediate);
    bindMode(modeBatch);
    bindMode(ratingImmediate);
    bindMode(ratingBatch);
    var restoredMode = sessionStorage.getItem(MODE_KEY);
    var restoredRatingMode = sessionStorage.getItem(RATING_MODE_KEY)
      || (restoredMode === "batch" ? "batch" : "");
    var restoredItem = currentProblem();
    var hasPendingRatings = restoredRatingMode === "batch" && session().some(function (item) {
      return item.state === "unrated";
    });
    if (hasPendingRatings && restoredItem && practiceDeck.ended) {
      window.location = "session-end";
    } else if (restoredMode && restoredItem) {
      if (modeExam) modeExam.checked = restoredMode === "exam";
      if (modeMicro) modeMicro.checked = restoredMode === "micro";
      if (modeFlashCard) modeFlashCard.checked = restoredMode === "flash_card";
      if (modeYesNo) modeYesNo.checked = restoredMode === "yes_no";
      if (modeImmediate) modeImmediate.checked = restoredMode === "immediate";
      if (modeBatch) modeBatch.checked = restoredMode === "batch";
      if (ratingImmediate) ratingImmediate.checked = restoredRatingMode === "immediate";
      if (ratingBatch) ratingBatch.checked = restoredRatingMode === "batch";
      if (startArea) startArea.classList.add("hidden");
      setPracticeFocus(true);
      renderDeckItem(restoredItem);
      showComposer(true);
    }
    if (startPractice) {
      startPractice.disabled = !readyToStart();
      startPractice.addEventListener("click", startSession);
    }
    if (retryPractice) retryPractice.addEventListener("click", loadNext);

    if (submitAnswer) submitAnswer.addEventListener("click", function () {
      var item = currentProblem();
      if (!item || item.kind === "card") return;
      var answer = answerBox.value.trim();
      var choiceInputs = (stream && stream.querySelectorAll)
        ? Array.prototype.slice.call(stream.querySelectorAll("[data-choice-option]:checked"))
        : [];
      var choiceTexts = choiceInputs.map(function (input) { return input.value; });
      if (choiceTexts.length) answer = choiceTexts.join(", ");
      var patch = { answer_text: answer };
      if (choiceTexts.length) patch.choices = choiceTexts.slice();
      var graded = gradeMicroQuiz(item.payload, choiceTexts);
      if (graded !== null) patch.verdict = graded;
      if (batchNow()) patch.state = "unrated";
      PracticeDeck.settle(practiceDeck, item.id, patch);
      persistDeck();
      renderDeckItem(currentProblem());
      if (batchNow()) {
        // Instant verdict, deferred rating: hold the verdict (and the
        // highlighted correct options) briefly, then advance. Nothing is
        // written — ratings still happen only at session end.
        if (graded !== null) scheduleAdvance();
        else advance();
        return;
      }
    });

    if (showAnswer) showAnswer.addEventListener("click", function () {
      var item = currentProblem();
      if (!item) return;
      clearPracticeError();
      if (item.kind === "card") {
        var patch = { revealed: true };
        if (batchNow() && item.state !== "rated") patch.state = "unrated";
        PracticeDeck.settle(practiceDeck, item.id, patch);
        persistDeck();
        renderDeckItem(currentProblem());
        return;
      }
      api("/problem/" + item.id).then(function (detail) {
        var quiz = microQuiz(detail.problem) || microQuiz(item.payload);
        var section;
        if (quiz) {
          section = "<section class='practice-solution'><p class='section-kicker'>答案</p>"
            + "<div class='rich-text'>" + richText(String(quiz.answer_key || "")) + "</div>"
            + "<p class='section-kicker'>为什么</p>"
            + "<div class='rich-text'>" + richText(quiz.error_reason || "") + "</div></section>";
        } else {
          var solution = detail.problem.solution || "（本题无解析，请基于自身作答自评）";
          section = "<section class='practice-solution'><p class='section-kicker'>解析</p>"
            + "<div class='rich-text'>" + richText(solution) + "</div></section>";
        }
        stream.innerHTML += section;
        renderMath(stream);
        showAnswer.classList.add("hidden");
        if (!batchNow()) feedbackArea.classList.remove("hidden");
      }).catch(showPracticeError);
    });

    if (saveRating) saveRating.addEventListener("click", function () {
      var rating = parseInt(ratingInput.value, 10);
      var item = currentProblem();
      if (!item) return;
      if (rating < 1 || rating > 5) {
        showPracticeError("请输入 1-5 的评分");
        return;
      }
      clearPracticeError();
      post("/feedback", {
        item_type: item.kind === "card" ? "card" : "problem",
        item_id: item.id,
        rating: rating, note: feedbackNote.value.trim(),
      }).then(function () {
        updateSession(item.id, { state: "rated" });
        advance();
      }).catch(showPracticeError);
    });

    if (noTime) noTime.addEventListener("click", function () {
      var item = currentProblem();
      if (!item) return;
      // Skipping applies only to items never answered: a graded problem or a
      // revealed card keeps its played (unrated) state when moving on.
      var state = (item.state === "active" || item.state === "skipped")
        ? ((item.kind === "card" && item.revealed) ? "unrated" : "skipped")
        : item.state;
      updateSession(item.id, { state: state });
      advance();
    });

    var gotoBtn = document.getElementById("goto-session-end");
    if (gotoBtn) gotoBtn.addEventListener("click", function () {
      var item = currentProblem();
      if (item) {
        var endState = (item.state === "active" || item.state === "skipped")
          ? ((item.kind === "card" && item.revealed) ? "unrated" : "skipped")
          : item.state;
        updateSession(item.id, { state: endState });
      }
      cancelScheduledAdvance();
      showComposer(false);
      if (batchNow()) {
        window.location = "session-end";
      } else {
        sessionStorage.removeItem(MODE_KEY);
        sessionStorage.removeItem(RATING_MODE_KEY);
        stream.innerHTML = "<p class='muted'>本轮练习已提前结束。</p>";
        setPracticeFocus(false);
        if (startArea) startArea.classList.remove("hidden");
      }
    });

    if (cardPrev) cardPrev.addEventListener("click", function () {
      if (practiceDeck.cursor <= 0) return;
      cancelScheduledAdvance();
      renderDeckItem(PracticeDeck.goTo(practiceDeck, practiceDeck.cursor - 1));
      persistDeck();
    });
    if (cardNext) cardNext.addEventListener("click", function () {
      advance();
    });
  }

  var recalculatePlan = document.getElementById("recalculate-plan");
  if (recalculatePlan) {
    recalculatePlan.addEventListener("click", function () {
      recalculatePlan.disabled = true;
      post("/plan/recalculate", {}).then(function () {
        recalculatePlan.disabled = false;
        if (window.location && typeof window.location.reload === "function") {
          window.location.reload();
        }
      }).catch(function () { recalculatePlan.disabled = false; });
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
          .then(function () { window.location.reload(); })
          .catch(function (error) { goalStatus("删除失败：" + (error.message || "未知错误")); });
      });
    });

    if (goalCancel) goalCancel.addEventListener("click", resetGoalForm);

    goalForm.addEventListener("submit", function (event) {
      if (event.preventDefault) event.preventDefault();
      var title = document.getElementById("goal-title");
      var kind = document.getElementById("goal-kind");
      var deadline = document.getElementById("goal-deadline");
      var description = document.getElementById("goal-description");
      if (!title || !title.value.trim()) {
        goalStatus("请填写目标名称。");
        return;
      }
      var payload = {
        title: title.value.trim(),
        kind: kind ? kind.value : "stage",
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
        if (window.location && typeof window.location.reload === "function") {
          window.location.reload();
        } else {
          window.location = "/w/" + encodeURIComponent(WS) + "/practice";
        }
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
        goalStatus("暂无可用 Agent。请先配置一个提供方，或手动填写字段。");
        return;
      }
      if (!aiConversation || aiTurn) {
        if (typeof aiShowProviderPicker === "function") aiShowProviderPicker();
        goalStatus("请先在右侧选择 Agent 开始对话，再点一次「让 Agent 填」。");
        return;
      }
      var body = aiContextBody(text);
      body.goal_intent = true;
      goalStatus("已发给 Agent，等待代填…");
      post("/ai/sessions/" + encodeURIComponent(aiConversation) + "/turns", body)
        .then(function (turn) {
          aiTurn = turn.turn_id;
          aiPollSequence = 0;
          aiPollConversationTurn();
        })
        .catch(function (error) {
          goalStatus("发送失败：" + (error.message || "未知错误"));
        });
    }
    if (goalAssistSend) goalAssistSend.addEventListener("click", sendGoalAssist);
  }

  /* ---------- session-end ---------- */

  var pending = document.getElementById("pending-ratings");
  if (pending) {
    var unrated = session().filter(function (item) { return item.state === "unrated"; });
    if (!unrated.length) {
      pending.innerHTML = "<p>没有待评的题。</p>";
    } else {
      var remaining = unrated.length;
      var buildRatingCard = function (contentHtml, itemType, entryId, title) {
        var card = document.createElement("article");
        card.className = "pending-rating-card card";
        card.dataset.pid = entryId;
        card.innerHTML = contentHtml;
        var rating = document.createElement("input");
        rating.id = "end-rating-" + entryId;
        rating.type = "number";
        rating.min = "1";
        rating.max = "5";
        rating.placeholder = "输入 1–5";
        var note = document.createElement("textarea");
        note.id = "end-note-" + entryId;
        note.placeholder = "可选备注";
        var save = document.createElement("button");
        save.id = "end-save-" + entryId;
        save.className = "primary sm";
        save.textContent = "保存评分";
        var ratingLabel = document.createElement("label");
        ratingLabel.id = "end-rating-label-" + entryId;
        ratingLabel.setAttribute("for", rating.id);
        ratingLabel.textContent = "为“" + title + "”评分（1-5）";
        var noteLabel = document.createElement("label");
        noteLabel.id = "end-note-label-" + entryId;
        noteLabel.setAttribute("for", note.id);
        noteLabel.textContent = "为“" + title + "”添加备注";
        var error = document.createElement("p");
        error.id = "end-error-" + entryId;
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
            item_type: itemType, item_id: entryId,
            rating: value, note: note.value.trim(),
          }).then(function () {
            updateSession(entryId, { state: "rated" });
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
      };
      unrated.forEach(function (item) {
        if (item.kind === "card") {
          var card = item.payload || {};
          buildRatingCard(
            "<p class='context-line'>闪卡</p>"
            + "<div class='problem-text rich-text'>" + richText(card.front || "") + "</div>"
            + "<p class='section-kicker'>背面</p><div class='rich-text'>" + richText(card.back || "") + "</div>",
            "card", item.id, String(card.front || "闪卡"));
          return;
        }
        api("/problem/" + item.id).then(function (detail) {
          var problem = detail.problem;
          var title = problem.display_title || "未命名题目";
          var quiz = problem.micro_quiz && typeof problem.micro_quiz === "object"
            ? problem.micro_quiz : null;
          var solutionHtml = quiz
            ? "<p class='section-kicker'>答案</p><div class='rich-text'>"
              + richText(String(quiz.answer_key || "")) + "</div>"
              + "<p class='section-kicker'>为什么</p><div class='rich-text'>"
              + richText(quiz.error_reason || "") + "</div>"
            : "<p class='section-kicker'>解析</p><div class='rich-text'>"
              + richText(problem.solution || "（本题无解析）") + "</div>";
          buildRatingCard(
            "<p class='context-line'>练习题</p><h2>" + escapeHtml(title) + "</h2>"
            + "<div class='problem-text rich-text'>" + richText(problem.problem_text) + "</div>"
            + "<p class='section-kicker'>我的作答</p><div class='rich-text'>" + richText(item.answer_text || "（未作答）") + "</div>"
            + solutionHtml,
            "problem", item.id, title);
        });
      });
    }
    var similar = document.getElementById("practice-similar");
    if (similar) similar.addEventListener("click", function () {
      var scope = currentKps();
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.removeItem(MODE_KEY);
      sessionStorage.removeItem(RATING_MODE_KEY);
      if (scope.length) {
        store(KPS_KEY, scope);
        saveSelectedKpIds(scope);
      }
      sessionStorage.setItem(SIMILAR_KEY, "1");
      window.location = "practice";
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

  function aiApplyAction(action) {
    if (!action) return;
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
        "goal-deadline": action.deadline, "goal-description": action.description,
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

  function aiApplyCheckAction(action) {
    if (action.error) {
      aiAddCheckCard("入库未执行", "校验未通过：" + action.error, null);
      return;
    }
    var result = action.result;
    if (!result || !result.batch_id) return;
    var detail = "批次 " + result.batch_id + " · " + (result.kind || "?")
      + " · 入库 " + (result.applied != null ? result.applied : "?") + " 条"
      + " · 备份 " + (result.backup_path || "无");
    aiAddCheckCard("Check 入库完成", detail, result.batch_id);
  }

  function aiAddCheckCard(title, detail, batchId) {
    if (!messages) return;
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
  }

  function aiRollbackBatch(batchId, button) {
    if (window.confirm && !window.confirm("整批回滚 " + batchId + "？该批全部内容行将从池中撤销。")) return;
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
      if (message.action && message.action.type === "check_ingest") {
        aiApplyCheckAction(message.action);
      }
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
      practice_intent: /练习|做题|刷题|复习题/.test(message),
      check_intent: /出题|出几道|补池|加题|入库/.test(message),
    };
    if (layout.dataset.objectType) body.object_type = layout.dataset.objectType;
    if (layout.dataset.objectId) body.object_id = layout.dataset.objectId;
    if (layout.dataset.page === "kp") body.kp_id = layout.dataset.objectId;
    if (layout.dataset.page === "practice" && currentProblem()) {
      body.problem_id = currentProblem().id;
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
      aiApplyAction(data.turn.action);
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
    if (!layout) return;
    if (window.innerWidth < 1024) layout.setAttribute("data-ai-collapsed", "1");
    else layout.removeAttribute("data-ai-collapsed");
  }

  var leftWidth = 280;
  var rightWidth = 420;
  var middleMinWidth = 420;
  function applyColumnWidths() {
    if (!layout || !layout.style) return;
    if (window.innerWidth < 1024) {
      layout.style.gridTemplateColumns = "";
      return;
    }
    var available = (layout.clientWidth || window.innerWidth) - middleMinWidth;
    leftWidth = Math.max(200, Math.min(480, Math.min(leftWidth, available - rightWidth)));
    rightWidth = Math.max(360, Math.min(560, Math.min(rightWidth, available - leftWidth)));
    layout.style.gridTemplateColumns = leftWidth + "px minmax(420px, 1fr) " + rightWidth + "px";
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
  bindColumnResizer("left-resizer", "left", 200, 480);
  bindColumnResizer("right-resizer", "right", 360, 560);
  fitAiColumn();
  applyColumnWidths();
  window.addEventListener("resize", function () { fitAiColumn(); applyColumnWidths(); });

  /* ---------- time view (calendar + workload) ---------- */

  var timeView = document.getElementById("time-view");
  if (timeView) {
    var calendarGrid = document.getElementById("calendar-grid");
    var workloadBars = document.getElementById("workload-bars");
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
      var daysInMonth = new Date(year, month + 1, 0).getDate();
      var lead = (first.getDay() + 6) % 7; /* Monday-first */
      var byDate = {};
      var offGrid = [];
      goals.forEach(function (goal) {
        if (goal.deadline && typeof goal.deadline === "string") {
          var key = goal.deadline.slice(0, 10);
          if (key.slice(0, 7) === isoDate(first).slice(0, 7)) {
            (byDate[key] ||= []).push(goal);
            return;
          }
        }
        offGrid.push(goal);
      });
      if (offGrid.length) {
        var offLine = offGrid.map(function (goal) {
          return escapeHtml(goal.title || "未命名目标")
            + (goal.deadline ? "（" + escapeHtml(goal.deadline.slice(0, 10)) + "）" : "");
        }).join("、");
        calendarGrid.insertAdjacentHTML("afterend",
          "<p class='muted time-off-note'>本月之外到期：" + offLine + "。</p>");
      }
      var html = WEEKDAYS.map(function (label) {
        return "<div class='calendar-head'>" + label + "</div>";
      }).join("");
      for (var blank = 0; blank < lead; blank += 1) html += "<div class='calendar-cell blank'></div>";
      for (var day = 1; day <= daysInMonth; day += 1) {
        var key = isoDate(new Date(year, month, day));
        var isToday = day === today.getDate();
        var cards = (byDate[key] || []).map(function (goal) {
          return "<span class='calendar-goal' title='" + escapeHtml(goal.title || "") + "'>"
            + escapeHtml(goal.title || "未命名目标") + "</span>";
        }).join("");
        html += "<div class='calendar-cell" + (isToday ? " today" : "") + "'>"
          + "<span class='calendar-day'>" + day + "</span>" + cards + "</div>";
      }
      calendarGrid.innerHTML = html;
    }

    function renderBars(days) {
      var max = 0;
      days.forEach(function (day) { max = Math.max(max, day.count); });
      var nonzero = days.filter(function (day) { return day.count > 0; });
      var average = nonzero.length
        ? Math.max(3, nonzero.reduce(function (sum, day) { return sum + day.count; }, 0) / nonzero.length)
        : 3;
      workloadBars.innerHTML = days.map(function (day) {
        var height = max ? Math.round((day.count / max) * 72) : 0;
        var heavy = day.count >= average && day.count > 0;
        var label = day.date.slice(8) === "01" || day.count
          ? day.date.slice(8) : "";
        return "<div class='bar-col" + (heavy ? " heavy" : "") + "' data-bar-date='" + day.date + "'>"
          + "<div class='bar-fill'" + (height ? " style='height:" + height + "px'" : "") + "></div>"
          + (heavy ? "<span class='bar-heavy-flag'>重</span>" : "")
          + "<span class='bar-label'>" + label + "</span>"
          + "<span class='bar-count'>" + (day.count || "") + "</span></div>";
      }).join("");
      var heavyDays = days.filter(function (day) {
        return day.count >= average && day.count > 0;
      });
      if (heavyDays.length) {
        workloadPrefill.classList.remove("hidden");
        var busiest = heavyDays.reduce(function (a, b) { return b.count > a.count ? b : a; });
        workloadPrefill.dataset.busiestCount = String(busiest.count);
      }
    }

    api("/calendar").then(function (data) {
      var goals = data.goals || [];
      var days = data.days || [];
      var hasWorkload = days.some(function (day) { return day.count > 0; });
      if (!goals.length && !hasWorkload) {
        timeView.classList.remove("hidden");
        timeViewEmpty.classList.remove("hidden");
        return;
      }
      timeView.classList.remove("hidden");
      renderMonthGrid(goals);
      renderBars(days);
      if (!goals.length) {
        calendarGrid.insertAdjacentHTML("afterend",
          "<p class='muted'>还没有带截止日期的目标。</p>");
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

})();
