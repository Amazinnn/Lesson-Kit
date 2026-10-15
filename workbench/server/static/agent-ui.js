/* Agent UI v1 surface controller.
   Owns presentation only; provider/session/runtime behavior stays in workbench.js. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory;
  else root.AgentUISurfaces = factory(root.document, root);
})(typeof globalThis !== "undefined" ? globalThis : this, function (document, window) {
  "use strict";

  var state = {
    initialized: false,
    userCollapsed: false,
    running: false,
  };

  function byId(id) {
    return document && document.getElementById ? document.getElementById(id) : null;
  }

  function setHidden(element, hidden) {
    if (!element || !element.classList) return;
    element.classList.toggle("hidden", !!hidden);
  }

  function pageLabel(page) {
    return ({
      practice: "练习",
      "practice-sets": "组卷",
      kp: "知识点",
      kps: "知识点",
      graph: "知识图谱",
      records: "记录",
      goals: "目标",
    })[page] || "当前页";
  }

  function selectedKpCount(layout) {
    if (!layout || !window || !window.sessionStorage) return 0;
    var workspace = layout.dataset && layout.dataset.workspace;
    if (!workspace) return 0;
    try {
      var raw = window.sessionStorage.getItem("wb_kp_selection_" + workspace);
      var value = raw ? JSON.parse(raw) : [];
      return Array.isArray(value) ? value.filter(Boolean).length : 0;
    } catch (_) {
      return 0;
    }
  }

  function chip(text, primary) {
    var span = document.createElement("span");
    span.className = "agent-context-chip" + (primary ? " is-primary" : "");
    span.textContent = text;
    return span;
  }

  function renderContext() {
    var host = byId("ai-context-chips");
    var layout = byId("layout");
    if (!host || !layout) return;
    host.innerHTML = "";
    var page = layout.dataset ? layout.dataset.page : "";
    host.appendChild(chip(pageLabel(page), true));
    if (layout.dataset && layout.dataset.objectId) {
      host.appendChild(chip(layout.dataset.objectId, false));
    }
    var count = selectedKpCount(layout);
    if (count) host.appendChild(chip("范围 " + count + " 个知识点", false));
  }

  function autosizeInput() {
    var input = byId("ai-input");
    if (!input || !input.style) return;
    input.style.height = "auto";
    var height = Math.max(40, Math.min(160, input.scrollHeight || 40));
    input.style.height = height + "px";
  }

  function bindComposer() {
    var input = byId("ai-input");
    if (!input || input.__agentUiBound) return;
    input.__agentUiBound = true;
    input.addEventListener("input", autosizeInput);
    autosizeInput();
  }

  function collapseAux() {
    state.userCollapsed = true;
    ["agent-activity-float", "agent-bottom-dock", "agent-artifact-split"].forEach(function (id) {
      setHidden(byId(id), true);
    });
    var middle = byId("middle");
    if (middle && middle.classList) middle.classList.remove("agent-split-open");
  }

  function bindAuxCollapse() {
    if (!document || !document.querySelectorAll) return;
    Array.prototype.forEach.call(document.querySelectorAll("[data-agent-aux-collapse]"), function (button) {
      if (button.__agentUiBound) return;
      button.__agentUiBound = true;
      button.addEventListener("click", collapseAux);
    });
  }

  function resetTurn() {
    state.userCollapsed = false;
    state.running = false;
    setHidden(byId("agent-activity-float"), true);
    setHidden(byId("agent-bottom-dock"), true);
  }

  function setRunning(running) {
    state.running = !!running;
    var rail = byId("ai-column");
    if (rail && rail.classList) rail.classList.toggle("is-agent-running", state.running);
  }

  function init() {
    if (!document || state.initialized) return api;
    state.initialized = true;
    var rail = byId("ai-column");
    if (rail && rail.classList) rail.classList.add("agent-rail");
    renderContext();
    bindComposer();
    bindAuxCollapse();
    return api;
  }

  var api = {
    init: init,
    renderContext: renderContext,
    resetTurn: resetTurn,
    setRunning: setRunning,
    collapseAux: collapseAux,
    autosizeInput: autosizeInput,
    state: state,
  };

  if (document && document.getElementById) init();
  return api;
});
