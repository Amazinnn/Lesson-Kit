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
  var FLASH_DIRECTION_KEY = "wb_flash_direction_" + WS;
  var SELECTION_KEY = "wb_kp_selection_" + WS;
  var SCOPE_TRAY_KEY = "wb_scope_tray_open_" + WS;
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
    renderScopeTray();
    renderStagedList();
    return unique;
  }

  function scopeTrayNames() {
    var tray = document.getElementById("scope-tray");
    if (!tray) return {};
    try { return JSON.parse(tray.dataset.kpNames || "{}") || {}; }
    catch (_) { return {}; }
  }

  function renderScopeTray() {
    var list = document.getElementById("scope-tray-list");
    if (!list) return;
    var ids = selectedKpIds();
    var names = scopeTrayNames();
    list.innerHTML = ids.map(function (id) {
      var title = names[id] || id;
      return "<li class='scope-tray-item'><span>" + escapeHtml(title) + "</span>"
        + "<button class='ghost sm icon-only scope-tray-remove' type='button' "
        + "data-kp-id='" + escapeHtml(id) + "' aria-label='移除 "
        + escapeHtml(title) + "'>×</button></li>";
    }).join("");
    var count = document.getElementById("scope-tray-count");
    if (count) count.textContent = "已选 " + ids.length + " 个";
    var triggerCount = document.getElementById("scope-tray-trigger-count");
    if (triggerCount) triggerCount.textContent = String(ids.length);
    var empty = document.getElementById("scope-tray-empty");
    if (empty) empty.classList.toggle("hidden", ids.length > 0);
    var practice = document.getElementById("scope-tray-practice");
    if (practice) practice.disabled = !ids.length;
  }

  function setScopeTrayOpen(open) {
    var toggle = document.getElementById("scope-tray-toggle");
    var panel = document.getElementById("scope-tray-panel");
    if (!toggle || !panel) return;
    toggle.classList.toggle("hidden", open);
    panel.classList.toggle("hidden", !open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    store(SCOPE_TRAY_KEY, !!open);
  }

  function bindChapterLens() {
    var lens = document.getElementById("chapter-lens");
    var toggle = document.getElementById("chapter-lens-switch");
    var select = document.getElementById("chapter-lens-select");
    if (!lens || !toggle || !select) return;
    function applyChapter(chapter) {
      post("/chapter", { chapter: chapter }).then(function () {
        window.location.reload();
      }, function (error) {
        window.alert("切换章节失败：" + error.message);
        window.location.reload();
      });
    }
    toggle.addEventListener("change", function () {
      applyChapter(toggle.checked ? select.value : "");
    });
    select.addEventListener("change", function () {
      applyChapter(select.value);
    });
  }

  function bindScopeTray() {
    var toggle = document.getElementById("scope-tray-toggle");
    var collapse = document.getElementById("scope-tray-collapse");
    var list = document.getElementById("scope-tray-list");
    var practice = document.getElementById("scope-tray-practice");
    if (!toggle) return;
    toggle.addEventListener("click", function () { setScopeTrayOpen(true); });
    if (collapse) collapse.addEventListener("click", function () {
      setScopeTrayOpen(false);
    });
    if (list) list.addEventListener("click", function (event) {
      var target = event.target;
      var button = target && target.closest ? target.closest(".scope-tray-remove") : null;
      if (!button) return;
      saveSelectedKpIds(selectedKpIds().filter(function (id) {
        return id !== button.dataset.kpId;
      }));
    });
    if (practice) practice.addEventListener("click", function () {
      if (selectedKpIds().length) {
        window.location = "/w/" + encodeURIComponent(WS) + "/practice";
      }
    });
    setScopeTrayOpen(!!load(SCOPE_TRAY_KEY, false));
    renderScopeTray();
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
  }

  bindChapterLens();
  bindScopeTray();
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
      return resp.json().catch(function () { return {}; }).then(function (data) {
        if (!resp.ok) throw new Error(data.error || resp.status);
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
      var resolved;
      if (/^\/(?:api\/w\/|static\/)/.test(src)) {
        resolved = src;
      } else if (/^[\w./-]+$/.test(src)) {
        resolved = "/api/w/" + encodeURIComponent(WS) + "/figures/" + src.replace(/^\//, "");
      } else {
        return alt;
      }
      return token("<img alt='" + alt + "' src='" + resolved.replace(/'/g, "&#39;") + "'>");
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
    value = value.replace(/(?<![A-Za-z0-9_])__([^_\n]+)__(?![A-Za-z0-9_])/g, "<strong>$1</strong>");
    value = value.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
    value = value.replace(/(?<![A-Za-z0-9_])_([^_\n]+)_(?![A-Za-z0-9_])/g, "<em>$1</em>");
    value = value.replace(/\$\$([\s\S]+?)\$\$/g, function (_, math) {
      return token("<span class='math display'>" + math + "</span>");
    });
    value = value.replace(/\$([^$\n]+)\$/g, function (_, math) {
      return token("<span class='math'>" + math + "</span>");
    });
    return value.replace(/\u0000(\d+)\u0000/g, function (_, index) { return tokens[Number(index)]; });
  }

  var TABLE_DELIMITER_CELL = /^:?-{1,}:?$/;

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
    var lines = String(text == null ? "" : text).replace(/\r\n?/g, "\n").split("\n");
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
    var graphFilterSummary = document.getElementById("graph-filter-summary");
    var graphFilterClear = document.getElementById("graph-filter-clear");
    var graphFilterInputs = ["needs_work", "review", "mastered", "null"].map(
      function (state) { return document.getElementById("graph-filter-" + state); }
    ).filter(Boolean);
    var graphGravity = document.getElementById("graph-gravity");
    var graphProjectionHint = document.getElementById("graph-projection-hint");
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
    var graphRecovered = false;
    var graphRelaxed = false;
    var graphProjection = "structure";
    var graphLabelZoomed = false;
    var graphFocusedId = null;
    var graphFilterVersion = 0;
    var graphPendingPositions = null;
    var graphEnteringIds = new Set();
    var draggedNode = null;
    var panStart = null;
    var reducedGraphMotion = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function actionReminder(node) {
      return node.state === "needs_work" ? "重点练习"
        : node.state === "review" ? "可以复习" : "";
    }

    function mixGraphColor(from, to, score) {
      var ratio = Math.max(0, Math.min(1, Number(score) || 0));
      function channel(index) {
        return Math.round(parseInt(from.slice(index, index + 2), 16) * (1 - ratio)
          + parseInt(to.slice(index, index + 2), 16) * ratio);
      }
      return "rgb(" + channel(1) + ", " + channel(3) + ", " + channel(5) + ")";
    }

    function graphNodeColors(node) {
      var score = node.projectionScore || 0;
      if (node.projection === "problem_count") {
        return [mixGraphColor("#edf3ff", "#2457c5", score),
          mixGraphColor("#9bb5e8", "#153a8a", score)];
      }
      if (node.projection === "importance") {
        return [mixGraphColor("#fff8dc", "#f2c94c", score),
          mixGraphColor("#cdbf8c", "#9b7610", score)];
      }
      if (node.projection === "state") {
        if (node.state === "mastered") return ["#2457c5", "#153a8a"];
        if (node.state === "review") return ["#f2c94c", "#9b7610"];
        if (node.state === "needs_work") return ["#d6453d", "#8f211c"];
        return ["#f4f0e7", "#7a746a"];
      }
      return ["#fffdf8", "#171717"];
    }

    function updateGraphNodeAppearance(node) {
      var elements = graphNodeElements.get(node.id);
      if (!elements) return;
      ["structure", "problem_count", "importance", "state"].forEach(function (name) {
        elements.node.classList.remove("projection-" + name);
      });
      elements.node.classList.add("projection-" + (node.projection || "structure"));
      var colors = graphNodeColors(node);
      elements.node.style.backgroundColor = colors[0];
      elements.node.style.borderColor = colors[1];
      elements.node.style.boxShadow = node.projection === "structure"
        ? "0 2px 8px rgba(23, 23, 23, .12)"
        : "0 0 0 " + (2 + (node.projectionScore || 0) * 5) + "px rgba(36, 87, 197, .10)";
    }

    function updateGraphProjectionHint() {
      if (!graphProjectionHint) return;
      graphProjectionHint.textContent = graphProjection === "problem_count"
        ? "越大、越靠内、蓝色越深 = 题量越多"
        : graphProjection === "importance"
          ? "越大、越靠内、黄色越深 = 越重要"
          : graphProjection === "state"
            ? "越大、越靠内 = 关注优先级越高 · 蓝/黄/红/灰 = 掌握/复习/待加强/未标记"
            : "关系决定位置 · 大小表示题量";
    }

    function showGraphProjectionHint() {
      if (!graphProjectionHint) return;
      graphProjectionHint.hidden = false;
      if (graphProjection && typeof graphProjection.offsetLeft === "number") {
        graphProjectionHint.style.left = Math.max(24, graphProjection.offsetLeft) + "px";
      }
    }

    function hideGraphProjectionHint() {
      if (graphProjectionHint) graphProjectionHint.hidden = true;
    }

    function activeGraphStates() {
      return graphFilterInputs.filter(function (input) { return input.checked; })
        .map(function (input) { return input.value; });
    }

    function graphState(node) {
      return node.state === "needs_work" || node.state === "review" || node.state === "mastered"
        ? node.state : "null";
    }

    function updateGraphFilterControls() {
      var count = activeGraphStates().length;
      if (graphFilterSummary) graphFilterSummary.textContent = count ? "已筛 " + count + " 类" : "筛选状态";
      if (graphFilterClear) graphFilterClear.disabled = count === 0;
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
      var states = new Set(activeGraphStates());
      var nodes = graphData.nodes.filter(function (node) {
        return (!search || (node.title + " " + node.id).toLowerCase().includes(search))
          && (!states.size || states.has(graphState(node)));
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
      graphSimulation = graphPendingPositions
        ? GraphPhysics.createSimulation(nodes, edges, graphCanvas.clientWidth,
          graphCanvas.clientHeight, graphPendingPositions)
        : GraphPhysics.layoutGraph(nodes, edges, graphCanvas.clientWidth, graphCanvas.clientHeight);
      graphPendingPositions = null;
      GraphPhysics.applyProjection(graphSimulation.nodes, graphProjection,
        graphCanvas.clientWidth, graphCanvas.clientHeight);
      if (states.size) {
        GraphPhysics.setStateClusters(graphSimulation, Array.from(states),
          graphCanvas.clientWidth, graphCanvas.clientHeight);
      }
      graphAutoFit = true;
      if (graphProjection === "structure") {
        var edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        edgeLayer.setAttribute("class", "graph-edge-layer");
        edgeLayer.setAttribute("aria-hidden", "true");
        stage.appendChild(edgeLayer);
        graphSimulation.edges.slice().sort(function (a, b) {
          return (Number(a.attraction) || 1) - (Number(b.attraction) || 1)
            || String(a.source + a.target).localeCompare(String(b.source + b.target));
        }).forEach(function (edge) {
          var visual = GraphPhysics.edgeVisual(edge.attraction);
          var pipe = document.createElementNS("http://www.w3.org/2000/svg", "g");
          pipe.setAttribute("class", "graph-edge-pipe");
          pipe.setAttribute("data-strength", visual.score.toFixed(3));
          [
            ["--edge-width", visual.width.toFixed(2) + "px"],
            ["--edge-shadow-width", visual.shadowWidth.toFixed(2) + "px"],
            ["--edge-highlight-width", visual.highlightWidth.toFixed(2) + "px"],
            ["--edge-opacity", visual.opacity.toFixed(3)],
          ].forEach(function (property) {
            if (pipe.style.setProperty) pipe.style.setProperty(property[0], property[1]);
            else pipe.style[property[0]] = property[1];
          });
          var paths = ["shadow", "body", "highlight"].map(function (layer) {
            var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("class", "graph-edge graph-edge-" + layer);
            pipe.appendChild(path);
            return path;
          });
          if (!reducedGraphMotion
              && (graphEnteringIds.has(edge.source) || graphEnteringIds.has(edge.target))) {
            pipe.classList.add("graph-filter-enter");
          }
          edgeLayer.appendChild(pipe);
          graphEdgeElements.push({ element: pipe, paths: paths, edge: edge });
        });
      }
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
        if (!reducedGraphMotion && graphEnteringIds.has(node.id)) {
          button.classList.add("graph-filter-enter");
        }
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
        if (!reducedGraphMotion && graphEnteringIds.has(node.id)) {
          select.classList.add("graph-filter-enter");
        }
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
        if (!reducedGraphMotion && graphEnteringIds.has(node.id)) {
          label.classList.add("graph-filter-enter");
        }
        stage.appendChild(label);
        graphNodeElements.set(node.id, { node: button, select: select, label: label });
        updateGraphNodeAppearance(node);
      });
      if (!nodes.length) {
        var empty = document.createElement("p");
        empty.className = "muted graph-empty";
        empty.textContent = "没有符合条件的知识点。";
        stage.appendChild(empty);
      }
      graphCanvas.replaceChildren(stage);
      if (!reducedGraphMotion && graphEnteringIds.size) {
        requestAnimationFrame(function () {
          graphNodeElements.forEach(function (elements) {
            elements.node.classList.remove("graph-filter-enter");
            elements.select.classList.remove("graph-filter-enter");
            elements.label.classList.remove("graph-filter-enter");
          });
          graphEdgeElements.forEach(function (entry) {
            entry.element.classList.remove("graph-filter-enter");
          });
        });
      }
      graphEnteringIds = new Set();
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
        var path = bend ? "M " + source.x + " " + source.y
          + " Q " + controlX + " " + controlY + " " + target.x + " " + target.y
          : "M " + source.x + " " + source.y + " L " + target.x + " " + target.y;
        entry.paths.forEach(function (layer) { layer.setAttribute("d", path); });
      });
      if (!graphSimulation) return;
      graphSimulation.nodes.forEach(function (node) {
        var elements = graphNodeElements.get(node.id);
        if (!elements) return;
        elements.node.style.left = node.x + "px";
        elements.node.style.top = node.y + "px";
        elements.node.style.width = (node.radius * 2) + "px";
        elements.node.style.height = (node.radius * 2) + "px";
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
        node.x = Math.max(node.collisionRadius || node.radius, Math.min(width - (node.collisionRadius || node.radius), node.x));
        node.y = Math.max(node.collisionRadius || node.radius, Math.min(height - (node.collisionRadius || node.radius), node.y));
      });
    }

    function settleLabelClearance() {
      resolveLabelOverlaps();
    }

    function runGraphSimulation() {
      if (!graphSimulation || reducedGraphMotion || graphFrame !== null) return;
      graphRecovered = false;
      graphRelaxed = false;
      function frame() {
        graphFrame = null;
        var stable = GraphPhysics.tick(graphSimulation);
        if (stable && !graphRecovered) {
          // 定格前先做标签避让，再用一小段物理把推挤吸收掉（恢复圆形间距、平滑收尾）
          settleLabelClearance();
          GraphPhysics.reheat(graphSimulation, 0.08);
          graphRecovered = true;
          stable = false;
        } else if (stable && !graphRelaxed
            && GraphPhysics.crowdedPairs(graphSimulation) > 0) {
          // 手动拖成一团后：再跑一轮完整放松，让斥力把拥挤布局重新撑开
          GraphPhysics.reheat(graphSimulation, 0.8);
          graphRelaxed = true;
          stable = false;
        }
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
      if (graphStage) {
        graphStage.classList.add("graph-fit-anim");
        setTimeout(function () { graphStage.classList.remove("graph-fit-anim"); }, 320);
      }
      applyGraphView();
      updateGraphLabels();
    }

    function transitionGraphFilter() {
      graphFilterVersion += 1;
      var version = graphFilterVersion;
      updateGraphFilterControls();
      var states = new Set(activeGraphStates());
      var search = (graphSearch && graphSearch.value || "").trim().toLowerCase();
      var visibleIds = new Set(graphData.nodes.filter(function (node) {
        return (!search || (node.title + " " + node.id).toLowerCase().includes(search))
          && (!states.size || states.has(graphState(node)));
      }).map(function (node) { return node.id; }));
      var positions = new Map();
      if (graphSimulation) {
        graphSimulation.nodes.forEach(function (node) {
          if (visibleIds.has(node.id)) positions.set(node.id, { x: node.x, y: node.y });
        });
      }
      graphEnteringIds = new Set(Array.from(visibleIds).filter(function (id) {
        return !positions.has(id);
      }));
      function rebuild() {
        if (version !== graphFilterVersion) return;
        graphPendingPositions = positions;
        renderGraph();
      }
      if (reducedGraphMotion || !graphSimulation) {
        rebuild();
        return;
      }
      graphNodeElements.forEach(function (elements, id) {
        if (visibleIds.has(id)) return;
        elements.node.classList.add("graph-filter-exit");
        elements.select.classList.add("graph-filter-exit");
        elements.label.classList.add("graph-filter-exit");
      });
      graphEdgeElements.forEach(function (entry) {
        if (!visibleIds.has(entry.edge.source) || !visibleIds.has(entry.edge.target)) {
          entry.element.classList.add("graph-filter-exit");
        }
      });
      setTimeout(rebuild, 160);
    }

    if (graphSearch) graphSearch.addEventListener("input", renderGraph);
    graphFilterInputs.forEach(function (input) {
      input.addEventListener("change", transitionGraphFilter);
    });
    if (graphFilterClear) graphFilterClear.addEventListener("click", function () {
      graphFilterInputs.forEach(function (input) { input.checked = false; });
      transitionGraphFilter();
      if (graphFilter) graphFilter.open = false;
    });
    updateGraphFilterControls();
    if (graphGravity) graphGravity.addEventListener("input", function () {
      if (!graphSimulation) return;
      GraphPhysics.setGravity(graphSimulation, graphGravity.value);
      runGraphSimulation();
    });
    var zoomIn = document.getElementById("graph-zoom-in");
    var zoomOut = document.getElementById("graph-zoom-out");
    var graphFit = document.getElementById("graph-fit");
    var graphProjectionSelect = document.getElementById("graph-projection");
    if (graphProjectionSelect) {
      updateGraphProjectionHint();
      graphProjectionSelect.addEventListener("mouseenter", showGraphProjectionHint);
      graphProjectionSelect.addEventListener("focus", showGraphProjectionHint);
      graphProjectionSelect.addEventListener("mouseleave", hideGraphProjectionHint);
      graphProjectionSelect.addEventListener("blur", hideGraphProjectionHint);
      graphProjectionSelect.addEventListener("change", function () {
      graphProjection = graphProjectionSelect.value || "structure";
      updateGraphProjectionHint();
      if (!graphSimulation) return;
      var structurePositions = null;
      if (graphProjection === "structure") {
        var structure = GraphPhysics.layoutGraph(
          graphSimulation.nodes, graphSimulation.edges,
          graphCanvas.clientWidth, graphCanvas.clientHeight,
        );
        structurePositions = new Map(structure.nodes.map(function (node) {
          return [node.id, { x: node.x, y: node.y }];
        }));
      }
      GraphPhysics.setProjection(graphSimulation, graphProjection,
        graphCanvas.clientWidth, graphCanvas.clientHeight, structurePositions);
      graphSimulation.nodes.forEach(updateGraphNodeAppearance);
      if (reducedGraphMotion) {
        GraphPhysics.settle(graphSimulation, 1600);
        settleLabelClearance();
        drawGraph();
      } else {
        runGraphSimulation();
      }
      });
    }
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

  /* ---------- practice flow ---------- */

  var practiceRuntime = PracticeFlow.start({
    api: api,
    post: post,
    patch: patch,
    store: store,
    load: load,
    renderMath: renderMath,
    escapeHtml: escapeHtml,
    richText: richText,
    selectedKpIds: selectedKpIds,
    saveSelectedKpIds: saveSelectedKpIds,
    recordRecent: recordRecent,
  });
  var currentProblem = practiceRuntime.currentProblem;
  var session = practiceRuntime.session;
  var visiblePracticeImages = practiceRuntime.visiblePracticeImages;
  var draftAnswer = practiceRuntime.draftAnswer;
  var draftNote = practiceRuntime.draftNote;
  var practiceSelectionContext = practiceRuntime.selectionContext
    || function () { return {}; };

  /* ---------- saved papers ---------- */

  var practiceSetList = document.getElementById("practice-set-list");

  function practiceSetIds(card) {
    return Array.prototype.slice.call(
      card.querySelectorAll(".practice-set-item")
    ).map(function (row) { return row.dataset.problemId; });
  }

  function practiceSetStatus(card, message) {
    var status = card.querySelector(".practice-set-status");
    if (!status) return;
    status.textContent = message || "";
    status.classList.toggle("hidden", !message);
  }

  function reloadPage() {
    if (window.location && typeof window.location.reload === "function") {
      window.location.reload();
    }
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
    practiceSetList.addEventListener("click", function (event) {
      var card = event.target.closest && event.target.closest(".practice-set-card");
      if (!card) return;
      var practiceSetId = card.dataset.practiceSetId;
      layout.dataset.practiceSetId = practiceSetId;
      var button = event.target.closest && event.target.closest("button");
      if (!button) return;
      var encoded = encodeURIComponent(practiceSetId);

      if (button.hasAttribute("data-set-start")) {
        post("/practice-sets/" + encoded + "/start", {}).then(function () {
          window.location = "/w/" + encodeURIComponent(WS) + "/practice";
        }).catch(function (error) {
          if (window.confirm && window.confirm(
            "当前还有一轮练习没有完成。开始这张试卷会清除旧进度，继续吗？"
          )) {
            post("/practice-sets/" + encoded + "/start", { replace: true }).then(function () {
              window.location = "/w/" + encodeURIComponent(WS) + "/practice";
            }).catch(function (retryError) {
              practiceSetStatus(card, retryError.message || "无法开始练习");
            });
          } else {
            practiceSetStatus(card, error.message || "当前练习未完成");
          }
        });
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
          .catch(function (error) { practiceSetStatus(card, error.message); });
        return;
      }

      if (button.hasAttribute("data-set-delete")) {
        if (window.confirm && !window.confirm("删除这张试卷？做题记录不会被删除。")) return;
        api("/practice-sets/" + encoded, { method: "DELETE" })
          .then(reloadPage)
          .catch(function (error) { practiceSetStatus(card, error.message); });
        return;
      }

      if (button.hasAttribute("data-set-export")) {
        api("/practice-sets/" + encoded + "/render").then(function (rendered) {
          var heading = card.querySelector("h2");
          var title = heading ? heading.textContent : practiceSetId;
          downloadPaper(title, "-problem-set.md", rendered.practice_set || "");
          downloadPaper(title, "-solutions.md", rendered.solutions || "");
        }).catch(function (error) { practiceSetStatus(card, error.message); });
        return;
      }

      var row = button.closest(".practice-set-item");
      if (!row) return;
      var list = row.parentNode;
      if (button.hasAttribute("data-set-up") && row.previousElementSibling) {
        list.insertBefore(row, row.previousElementSibling);
      } else if (button.hasAttribute("data-set-down") && row.nextElementSibling) {
        list.insertBefore(row.nextElementSibling, row);
      } else if (button.hasAttribute("data-set-remove")) {
        row.remove();
      } else {
        return;
      }
      var ids = practiceSetIds(card);
      if (!ids.length) {
        practiceSetStatus(card, "试卷至少需要一道题；如不再需要请删除整张试卷。");
        reloadPage();
        return;
      }
      patch("/practice-sets/" + encoded, { problem_ids: ids })
        .then(reloadPage)
        .catch(function (error) { practiceSetStatus(card, error.message); });
    });
  }

  /* ---------- goals ---------- */

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
          .then(function () { window.location.reload(); })
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
  var aiExecutionPlan = null;
  var aiCurrentProvider = "";
  var aiPiActivities = {};

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

  function aiActivityState(status) {
    if (status === "done") return "已完成";
    if (status === "failed") return "失败";
    return "进行中";
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
      body.appendChild(heading);
      body.appendChild(detail);
      row.appendChild(marker);
      row.appendChild(body);
      row.activityParts = { label: label, state: state, detail: detail, body: body };
      plan.rows[id] = row;
      plan.list.appendChild(row);
    }
    var status = activity.status === "done" || activity.status === "failed"
      ? activity.status : "running";
    row.className = "ai-plan-step is-" + status;
    if (activity.label != null || !row.activityParts.label.textContent) {
      row.activityParts.label.textContent = activity.label || "执行步骤";
    }
    row.activityParts.state.textContent = aiActivityState(status);
    if (activity.detail != null) row.activityParts.detail.textContent = activity.detail || "";
    row.activityParts.detail.classList.toggle("hidden", !row.activityParts.detail.textContent);
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
      body.appendChild(heading);
      body.appendChild(detail);
      body.appendChild(summary);
      row.appendChild(body);
      row.activityParts = {
        label: label, state: state, detail: detail, summary: summary, body: body,
        disclosure: null, output: null,
      };
      aiPiActivities[id] = row;
      messages.appendChild(row);
    }
    var status = activity.status === "done" || activity.status === "failed"
      ? activity.status : "running";
    row.className = "msg ai-activity is-" + status;
    if (activity.label != null || !row.activityParts.label.textContent) {
      row.activityParts.label.textContent = activity.label || "调用工具";
    }
    row.activityParts.state.textContent = aiActivityState(status);
    if (activity.detail != null) row.activityParts.detail.textContent = activity.detail || "";
    row.activityParts.detail.classList.toggle("hidden", !row.activityParts.detail.textContent);
    if (activity.summary != null) {
      row.activityParts.summary.textContent = String(activity.summary);
    }
    // A provider-reported failure shows its reason without expanding anything.
    var hasSummary = activity.status === "failed"
      && !!row.activityParts.summary.textContent;
    row.activityParts.summary.classList.toggle("hidden", !hasSummary);
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
    var single = aiAddCheckCard("Check 入库完成", aiResultDetail(result), result.batch_id);
    var line = single ? single.querySelector(".check-card-detail") : null;
    if (line) line.dataset.assets = aiAssetSummary(result.counts || {});
    // A reopened card shows the batch's current state, not the state at the time
    // it ran: an already rolled-back batch offers no second rollback.
    aiBatchState(result.batch_id).then(function (batch) {
      if (batch && batch.rolled_back_at) aiMarkRolledBack(single, result.batch_id);
    });
  }

  function aiAddMultiBatchCard(result, batches) {
    var card = aiAddCheckCard("Check 入库完成", aiMultiBatchDetail(result, batches), null);
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
    aiCurrentProvider = record.provider || "";
    aiSyncModelSwitch(record);
    aiStreamingMessage = null;
    aiExecutionPlan = null;
    aiPiActivities = {};
    (record.messages || []).forEach(function (message) {
      if (message.role === "user") {
        aiAddMarkdown(message.content || "", "user");
      } else {
        aiPiActivities = {};
        aiRenderActivities(message.activities || []);
        aiAddMarkdown(message.content || "", "ai");
        // A single-action turn records both keys; render the list, and fall back
        // to the single action only when the list is absent (one card, never two).
        var actions = message.actions || [];
        if (actions.length) {
          actions.forEach(function (restored) {
            if (restored && restored.type === "check_ingest") aiApplyCheckAction(restored);
          });
        } else if (message.action && message.action.type === "check_ingest") {
          aiApplyCheckAction(message.action);
        }
        aiExecutionPlan = null;
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
      return record;
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
        .then(function () {
          aiSetStatus(failure ? "无法切换模型：" + failure
                              : "模型已切换，下一轮生效。");
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
      // Attached for this turn only: the server bounds these and stores none of
      // them, so an unsent draft never becomes a learning record.
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
      body.selected_kp_id = selectedGraphKpId;
      body.graph_filter = {
        query: (document.getElementById("graph-search") || {}).value || "",
        states: ["needs_work", "review", "mastered", "null"].filter(function (state) {
          var input = document.getElementById("graph-filter-" + state);
          return input && input.checked;
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
      else if (event.kind === "error") aiSetStatus(event.text || "Agent 返回错误");
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
    aiExecutionPlan = null;
    aiPiActivities = {};
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
    aiTurn = null;
    aiConversation = "";
    sessionStorage.removeItem(AI_CONVERSATION_KEY);
    aiSetView("list");
    aiRefreshSessionList();
  });
  if (aiSessionList) {
    aiSetView("list");
    var providerRequest = aiRefreshProviders().then(function () {
      if (aiProviderLoadError && aiSessionEmpty) {
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
          "<p class='muted time-off-note'>本月之外或未排期：" + offLine + "。</p>");
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
        + (nonzero.length ? "" : "<p class='muted workload-empty'>未来 14 天暂无到期复习项。</p>");
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
