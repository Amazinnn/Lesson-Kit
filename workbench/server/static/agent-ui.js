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
    activities: {},
    activityOrder: [],
    approvalOpen: false,
  };

  function byId(id) {
    return document && document.getElementById ? document.getElementById(id) : null;
  }

  function setHidden(element, hidden) {
    if (!element || !element.classList) return;
    element.classList.toggle("hidden", !!hidden);
  }

  function clear(element) {
    if (element) element.innerHTML = "";
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

  function statusLabel(status) {
    if (status === "done") return "已完成";
    if (status === "failed") return "失败";
    return "进行中";
  }

  function activityValues() {
    return state.activityOrder.map(function (id) { return state.activities[id]; })
      .filter(function (item) { return !!item; });
  }

  function latestActivity() {
    var values = activityValues();
    return values.length ? values[values.length - 1] : null;
  }

  function activityLine(item, compact) {
    var row = document.createElement("div");
    var status = item.status === "done" || item.status === "failed" ? item.status : "running";
    row.className = "agent-milestone is-" + status;
    var marker = document.createElement("span");
    marker.className = "agent-milestone-marker";
    marker.textContent = status === "done" ? "✓" : status === "failed" ? "!" : "·";
    var body = document.createElement("div");
    body.className = "agent-milestone-body";
    var label = document.createElement("strong");
    label.textContent = item.label || "执行步骤";
    var stateText = document.createElement("span");
    stateText.className = "agent-milestone-state";
    stateText.textContent = statusLabel(status);
    body.appendChild(label);
    body.appendChild(stateText);
    if (!compact && (item.summary || item.detail)) {
      var detail = document.createElement("p");
      detail.textContent = item.summary || item.detail;
      body.appendChild(detail);
    }
    row.appendChild(marker);
    row.appendChild(body);
    return row;
  }

  function renderActivityFloat() {
    var surface = byId("agent-activity-float");
    var body = byId("agent-activity-body");
    if (!surface || !body) return;
    clear(body);
    var item = latestActivity();
    if (!item) {
      setHidden(surface, true);
      return;
    }
    body.appendChild(activityLine(item, false));
    if (!state.userCollapsed) setHidden(surface, false);
  }

  function renderBottomDock() {
    var surface = byId("agent-bottom-dock");
    var body = byId("agent-bottom-dock-body");
    if (!surface || !body) return;
    clear(body);
    activityValues().forEach(function (item) {
      body.appendChild(activityLine(item, true));
    });
    if (!state.userCollapsed) setHidden(surface, false);
  }

  function activity(item) {
    if (!item) return;
    var id = String(item.activity_id || "activity-" + state.activityOrder.length);
    if (!state.activities[id]) {
      state.activities[id] = { activity_id: id };
      state.activityOrder.push(id);
    }
    Object.keys(item).forEach(function (key) { state.activities[id][key] = item[key]; });
    if (state.userCollapsed) return;
    if (state.activityOrder.length > 1) {
      setHidden(byId("agent-activity-float"), true);
      renderBottomDock();
    } else {
      setHidden(byId("agent-bottom-dock"), true);
      renderActivityFloat();
    }
  }

  function failure(message) {
    var id = "turn-failure";
    if (!state.activities[id]) state.activityOrder.push(id);
    state.activities[id] = {
      activity_id: id,
      label: "Agent 未能完成",
      status: "failed",
      summary: String(message || "未知错误"),
    };
    if (state.userCollapsed) return;
    if (state.activityOrder.length > 1) {
      setHidden(byId("agent-activity-float"), true);
      renderBottomDock();
    } else {
      renderActivityFloat();
    }
  }

  function restoreComposer() {
    state.approvalOpen = false;
    setHidden(byId("ai-approval-slot"), true);
    setHidden(byId("ai-input-row"), false);
    clear(byId("ai-approval-slot"));
  }

  function confirm(spec, onApprove, onDeny) {
    var slot = byId("ai-approval-slot");
    var inputRow = byId("ai-input-row");
    if (!slot || !inputRow) return false;
    state.approvalOpen = true;
    clear(slot);
    var card = document.createElement("section");
    card.className = "agent-approval-card";
    var kicker = document.createElement("p");
    kicker.className = "agent-surface-kicker";
    kicker.textContent = "需要确认";
    var title = document.createElement("strong");
    title.className = "agent-approval-title";
    title.textContent = spec && spec.title ? spec.title : "确认操作";
    var reason = document.createElement("p");
    reason.className = "agent-approval-reason";
    reason.textContent = spec && spec.reason ? spec.reason : "此操作需要你的明确确认。";
    card.appendChild(kicker);
    card.appendChild(title);
    card.appendChild(reason);
    if (spec && spec.impact) {
      var impact = document.createElement("p");
      impact.className = "agent-approval-impact";
      impact.textContent = "影响：" + spec.impact;
      card.appendChild(impact);
    }
    var actions = document.createElement("div");
    actions.className = "agent-approval-actions";
    var deny = document.createElement("button");
    deny.type = "button";
    deny.className = "outline sm";
    deny.textContent = "取消";
    deny.addEventListener("click", function () {
      restoreComposer();
      if (onDeny) onDeny();
    });
    var approve = document.createElement("button");
    approve.type = "button";
    approve.className = "primary sm";
    approve.textContent = spec && spec.approveLabel ? spec.approveLabel : "确认";
    approve.addEventListener("click", function () {
      restoreComposer();
      if (onApprove) onApprove();
    });
    actions.appendChild(deny);
    actions.appendChild(approve);
    card.appendChild(actions);
    slot.appendChild(card);
    setHidden(inputRow, true);
    setHidden(slot, false);
    return true;
  }

  function resetTurn() {
    state.userCollapsed = false;
    state.running = false;
    state.activities = {};
    state.activityOrder = [];
    setHidden(byId("agent-activity-float"), true);
    setHidden(byId("agent-bottom-dock"), true);
    clear(byId("agent-activity-body"));
    clear(byId("agent-bottom-dock-body"));
    restoreComposer();
  }

  function finishTurn() {
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
    finishTurn: finishTurn,
    activity: activity,
    failure: failure,
    confirm: confirm,
    restoreComposer: restoreComposer,
    collapseAux: collapseAux,
    autosizeInput: autosizeInput,
    state: state,
  };

  if (document && document.getElementById) init();
  return api;
});
