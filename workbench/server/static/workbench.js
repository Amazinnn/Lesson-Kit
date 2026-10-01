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

  /* ---------- native knowledge graph (implementation blueprint port) ---------- */

  var graphCanvas = document.getElementById("graph-canvas");
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
    var graphZoomIn = document.getElementById("graph-zoom-in");
    var graphZoomOut = document.getElementById("graph-zoom-out");
    var graphZoomReset = document.getElementById("graph-reset");
    var graphDetail = document.getElementById("graph-detail-panel");
    var graphEdgeBudgetEl = null;
    var graphDetailTab = document.getElementById("graph-detail-tab");
    var teacherTab = document.getElementById("ai-teacher-tab");
    var teacherPanel = document.getElementById("ai-teacher-panel");

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
     * out of both the picture and the layout instead of papering over it. */
    var GRAPH_EDGE_BUDGET_RATIO = 0.5;

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
    var graphView = { scale: .7, panX: 52, panY: -18, userMoved: false };
    var graphPathScaled = 1;
    var graphLastPaintedScale = 0;
    var graphRenderDirty = true;
    var graphFrameHandle = null;

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

    function graphToastShow(text) {
      if (!graphToast) return;
      graphToast.textContent = text;
      graphToast.classList.add("show");
      setTimeout(function () { graphToast.classList.remove("show"); }, 1300);
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

    function graphBuild(model) {
      graphNodeData = (model.nodes || []).map(function (node) {
        return {
          id: node.id,
          title: node.title || node.id,
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
      graphEdgeEls = sim.edges.map(function (edge) {
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
        label.textContent = node.title;
        var meta = document.createElement("div");
        meta.className = "meta";
        wrap.appendChild(button);
        wrap.appendChild(label);
        wrap.appendChild(meta);
        button.addEventListener("click", function (event) {
          if (event.stopPropagation) event.stopPropagation();
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
        var select = document.createElement("input");
        select.type = "checkbox";
        select.className = "graph-kp-selection visually-hidden";
        select.dataset.selectionKpId = node.id;
        select.setAttribute("data-kp-selection", "");
        select.checked = selected.indexOf(node.id) >= 0;
        select.addEventListener("change", function () {
          var next = selectedKpIds().filter(function (id) { return id !== node.id; });
          if (select.checked) next.push(node.id);
          saveSelectedKpIds(next);
          graphSyncScope();
        });
        graphStage.appendChild(select);
        graphEls.get(node.id).select = select;
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

    function graphSyncScope() {
      var selected = selectedKpIds();
      graphEls.forEach(function (elements, id) {
        var member = selected.indexOf(id) >= 0;
        elements.wrap.classList.toggle("in-scope", member);
        if (elements.select) elements.select.checked = member;
      });
    }

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
      // Panning moves the existing picture and nothing else, and zooming only
      // changes stroke compensation and label thresholds. Rebuilding every edge
      // path on each wheel tick is what made a whole-course graph feel frozen,
      // so the viewport takes the light pass and geometry waits for the solver
      // or an interaction that actually moves nodes.
      if (graphView.scale !== graphLastPaintedScale) graphPaintViewport();
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
    }

    function graphNotePaint(kind) {
      if (graphStage.dataset) graphStage.dataset.lastPaint = kind;
    }

    function graphSelect(id, centerIt) {
      sim.graph.selected = id;
      selectedGraphKpId = id;
      recordRecent("kp", id);
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
      graphView.scale = Math.max(.38, Math.min(1.05,
        (graphCanvas.clientWidth - 36) / width,
        (graphCanvas.clientHeight - 36) / height));
      graphView.panX = graphCanvas.clientWidth / 2 - (minX + maxX) / 2 * graphView.scale;
      graphView.panY = graphCanvas.clientHeight / 2 - (minY + maxY) / 2 * graphView.scale;
      graphApplyView();
    }

    function graphRenderDetail(node) {
      if (!graphDetail) return;
      if (!node) {
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
        + "<button type='button' class='primary' id='graph-scope-toggle'>"
        + (member ? "移出练习范围" : "加入练习范围") + "</button></div>";
      var toggle = document.getElementById("graph-scope-toggle");
      if (toggle && !toggle.dataset.scopeBound) {
        toggle.dataset.scopeBound = "1";
        toggle.addEventListener("click", function () {
          var ids = selectedKpIds();
          var member2 = ids.indexOf(node.id) >= 0;
          var next = member2
            ? ids.filter(function (id) { return id !== node.id; })
            : ids.concat([node.id]);
          saveSelectedKpIds(next);
          graphSyncScope();
          graphRenderDetail(node);
          graphToastShow(member2 ? "已移出练习范围" : "已加入练习范围");
        });
      }
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
        var labelVisible = graphView.scale > .60 || focused || sim.graph.hover === node.id;
        elements.label.style.opacity = (labelVisible ? node.opacity : 0).toFixed(3);
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
    }

    function graphFrame() {
      graphFrameHandle = null;
      if (!sim) return;
      var wasSolving = sim.graph.alpha > 0;
      // One physics step per frame is plenty for a normal pool; a couple of
      // hundred nodes get a few steps per frame so the settle finishes in a
      // sensible wall-clock time instead of a minute of near-static frames.
      var steps = sim.nodes.length > 120 ? 3 : 1;
      while (steps > 0 && sim.graph.alpha > 0) {
        sim.tick();
        steps -= 1;
      }
      if (sim.graph.settled && sim.graph.autoFitAfterSettle && !graphView.userMoved) {
        sim.graph.autoFitAfterSettle = false;
        graphFit();
      }
      if (wasSolving !== (sim.graph.alpha > 0)) {
        graphSolver(sim.graph.alpha > 0);
        graphUpdateGapLegend();
      } else if (wasSolving) {
        graphUpdateGapLegend();
      }
      // A big pool makes one graph paint far more expensive than one physics
      // step, so the canvas repaints on a stride while the solver runs; every
      // interaction still forces a frame through graphRenderDirty, and the
      // settle frame always paints.
      var solving = sim.graph.alpha > 0;
      var stride = 1;
      if (solving) {
        if (sim.nodes.length > 300) stride = 12;
        else if (sim.nodes.length > 120) stride = 8;
      }
      var paintNow = graphRenderDirty || !solving || sim.graph.solveStep % stride === 0;
      if (paintNow) {
        graphRenderFrame();
        graphRenderDirty = false;
      }
      graphTideSurge(solving ? .06 : 0);
      // keep animating only while the solver runs or a frame was requested;
      // interactions call graphEnsureLoop() again when they change something
      if (solving || graphRenderDirty) graphEnsureLoop();
    }

    function graphEnsureLoop() {
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
      if (!graphTide || graphTideState.live) return;
      graphTideCtx = graphTide.getContext && graphTide.getContext("2d", { alpha: true });
      if (!graphTideCtx) return;
      graphTideState.reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
      graphTideState.live = true;
      if (typeof ResizeObserver === "function") {
        new ResizeObserver(function () {
          graphTideResize();
          graphMarkDirty();
          graphEnsureLoop();
        }).observe(graphCanvas);
      }
      window.addEventListener("resize", function () {
        graphTideResize();
        graphMarkDirty();
        graphEnsureLoop();
      });
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

    graphCanvas.addEventListener("pointerdown", function (event) {
      if (event.target.closest && event.target.closest(".node-wrap, .controls, .zoom, .legend")) return;
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
        sim.reheat(.34, false);
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
      if (event.target === graphCanvas || event.target === graphStage) {
        sim.graph.selected = null;
        selectedGraphKpId = null;
        graphApplyVisibility();
        graphRenderDetail(null);
        graphMarkDirty();
      }
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

    if (graphDetailTab) graphDetailTab.addEventListener("click", function () { showGraphPanel(true); });
    if (teacherTab) teacherTab.addEventListener("click", function () { showGraphPanel(false); });
    showGraphPanel(true);
    graphStartTide();
    api("/graph/model").then(function (model) {
      graphBuild(model);
      graphStartTide();
      graphEnsureLoop();
    }).catch(function (error) {
      if (typeof console !== "undefined" && console.error) {
        console.error("graph: model render failed", error && error.stack ? error.stack : error);
      }
      if (graphCanvas) graphCanvas.textContent = "图谱暂时无法读取。";
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

  var recordsCenter = document.querySelector(".records-center");
  if (recordsCenter) {
    recordsCenter.addEventListener("click", function (event) {
      var button = event.target.closest && event.target.closest("[data-run-replay]");
      if (!button) return;
      var runId = encodeURIComponent(button.dataset.runReplay);
      button.disabled = true;
      post("/practice/runs/" + runId + "/replay", {}).then(function () {
        window.location = "/w/" + encodeURIComponent(WS) + "/practice";
      }).catch(function (error) {
        button.disabled = false;
        if (error.message === "an unfinished practice already exists"
            && window.confirm
            && window.confirm("当前还有一轮练习没有完成。重新开始会清除旧进度，继续吗？")) {
          button.disabled = true;
          post("/practice/runs/" + runId + "/replay", { replace: true }).then(function () {
            window.location = "/w/" + encodeURIComponent(WS) + "/practice";
          }).catch(function (retryError) {
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
      var activeGraphFilters = sim && sim.graph ? sim.graph.filters : null;
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
