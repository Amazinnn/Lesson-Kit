"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/workbench.js"), "utf8",
);
const PracticeDeck = require("../../workbench/server/static/practice-deck.js");
const AgentUISurfaces = require("../../workbench/server/static/agent-ui.js");
const PRACTICE_FLOW_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/practice-flow.js"), "utf8",
);

class ClassList {
  constructor() { this.values = new Set(); }
  add(value) { this.values.add(value); }
  remove(value) { this.values.delete(value); }
  toggle(value, force) {
    if (force === undefined) force = !this.values.has(value);
    force ? this.add(value) : this.remove(value);
    return force;
  }
  contains(value) { return this.values.has(value); }
}

class Element {
  constructor(id, options = {}) {
    this.id = id;
    this.dataset = options.dataset || {};
    this.value = options.value || "";
    this.checked = !!options.checked;
    this.children = [];
    this.listeners = {};
    this.classList = new ClassList();
    this.attributes = {};
    this._html = "";
    this._text = "";
  }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  trigger(name, event = {}) {
    (this.listeners[name] || []).forEach((callback) => callback({ target: this, ...event }));
  }
  click() { this.trigger("click"); }
  appendChild(child) { this.children.push(child); return child; }
  set innerHTML(value) { this._html = String(value); this.children = []; }
  get innerHTML() { return this._html || this._text; }
  set textContent(value) { this._text = String(value); }
  get textContent() { return this._text; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] || null; }
  hasAttribute(name) { return Object.hasOwn(this.attributes, name); }
  removeAttribute(name) { delete this.attributes[name]; }
  querySelectorAll() { return []; }
  querySelector() { return null; }
  focus() { this.focused = true; this.trigger("focus"); }
}

class Storage {
  constructor() { this.values = new Map(); }
  getItem(key) { return this.values.get(key) || null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
}

function response(value, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(value),
  });
}

function setup(fetch, options = {}) {
  const storage = new Storage();
  const localStorage = new Storage();
  Object.entries(options.seed || {}).forEach(([key, value]) => storage.setItem(key, value));
  Object.entries(options.localSeed || {}).forEach(([key, value]) => localStorage.setItem(key, value));
  const route = options.route || "/w/alpha/kp/kp-7";
  const elements = {
    layout: new Element("layout", { dataset: { workspace: "alpha", page: "kp" } }),
    "ai-session-list-view": new Element("ai-session-list-view"),
    "ai-session-list": new Element("ai-session-list"),
    "ai-session-empty": new Element("ai-session-empty"),
    "ai-new-session": new Element("ai-new-session"),
    "ai-provider-picker": new Element("ai-provider-picker"),
    "ai-provider-options": new Element("ai-provider-options"),
    "ai-chat-view": new Element("ai-chat-view"),
    "ai-session-back": new Element("ai-session-back"),
    "ai-messages": new Element("ai-messages"),
    "ai-column": new Element("ai-column"),
    "ai-context-chips": new Element("ai-context-chips"),
    "ai-input": new Element("ai-input"),
    "ai-input-row": new Element("ai-input-row"),
    "ai-approval-slot": new Element("ai-approval-slot"),
    "ai-send": new Element("ai-send"),
    "ai-send-action": new Element("ai-send-action", { value: "default" }),
    "ai-pending-queue": new Element("ai-pending-queue"),
    "ai-pending-list": new Element("ai-pending-list"),
    "ai-queue-status": new Element("ai-queue-status"),
    "ai-queue-continue": new Element("ai-queue-continue"),
    "ai-handoff-status": new Element("ai-handoff-status"),
    "ai-paper-approval": new Element("ai-paper-approval"),
    "ai-paper-approval-status": new Element("ai-paper-approval-status"),
    "ai-paper-approval-details": new Element("ai-paper-approval-details"),
    "ai-paper-approval-approve": new Element("ai-paper-approval-approve"),
    "ai-paper-approval-cancel": new Element("ai-paper-approval-cancel"),
    "setting-running-send": new Element("setting-running-send", { value: "queue" }),
    "ai-stop": new Element("ai-stop"),
    "ai-status": new Element("ai-status"),
    "goal-form": new Element("goal-form"),
    "goal-nl": new Element("goal-nl"),
    "goal-assist-send": new Element("goal-assist-send"),
    "goal-form-status": new Element("goal-form-status"),
    "agent-activity-float": new Element("agent-activity-float"),
    "agent-activity-body": new Element("agent-activity-body"),
    "agent-bottom-dock": new Element("agent-bottom-dock"),
    "agent-bottom-dock-body": new Element("agent-bottom-dock-body"),
    "agent-artifact-split": new Element("agent-artifact-split"),
    "agent-artifact-title": new Element("agent-artifact-title"),
    "agent-artifact-body": new Element("agent-artifact-body"),
    "agent-artifact-actions": new Element("agent-artifact-actions"),
  };
  ["agent-activity-float", "agent-bottom-dock", "agent-artifact-split", "ai-approval-slot",
    "ai-paper-approval"]
    .forEach((id) => elements[id].classList.add("hidden"));
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  const window = {
    location: { pathname: route, search: options.search || "", hash: options.hash || "" },
    innerWidth: 1280, addEventListener() {},
    matchMedia() { return { matches: false }; },
    prompt() { return "我的会话"; }, confirm() { return true; },
    sessionStorage: storage, localStorage,
  };
  const ui = AgentUISurfaces(document, window);
  const sandbox = {
    document, window, fetch, PracticeDeck, AgentUISurfaces: ui,
    sessionStorage: storage, localStorage, console,
    setInterval, clearInterval,
    setTimeout: options.setTimeout || setTimeout,
    clearTimeout: options.clearTimeout || clearTimeout,
    requestAnimationFrame: (callback) => setImmediate(() => callback(0)),
    cancelAnimationFrame: clearImmediate,
  };
  const context = vm.createContext(sandbox);
  vm.runInContext(PRACTICE_FLOW_SOURCE, context, { filename: "practice-flow.js" });
  vm.runInContext(SOURCE, context, { filename: "workbench.js" });
  return { elements, window, localStorage, ui };
}

async function flush() {
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
}

test("agent column starts with history and requires an explicit provider for new sessions", async () => {
  const calls = [];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([{ name: "codex" }, { name: "claude" }]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      { conversation_id: "conv-001", provider: "codex", title: "复习极限", status: "idle", updated_at: "2026-08-26" },
    ]);
    if (url.endsWith("/ai/sessions/conv-001")) return response({
      conversation_id: "conv-001", provider: "codex", title: "复习极限", status: "idle", messages: [],
    });
    return response({});
  });
  await flush();
  assert.equal(app.elements["ai-session-list"].children.length, 1);
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
  app.elements["ai-new-session"].click();
  assert.equal(app.elements["ai-provider-picker"].classList.contains("hidden"), false);
  assert.equal(calls.some((item) => item.url.endsWith("/ai/sessions/conv-001")), false);
});

test("history entry opens a minimal fixed-provider chat and list row owns actions", async () => {
  const calls = [];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([{ name: "codex" }]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      { conversation_id: "conv-001", provider: "codex", title: "旧会话", title_source: "agent", status: "idle" },
    ]);
    if (url.endsWith("/ai/sessions/conv-001")) return response({
      conversation_id: "conv-001", provider: "codex", title: "旧会话", status: "idle", messages: [],
    });
    return response({ conversation_id: "conv-001", title: "我的会话", title_source: "user" });
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-session-back"].textContent, "");
  assert.equal(app.elements["ai-session-back"].getAttribute("aria-label"), "返回对话列表");
  assert.equal(app.elements["ai-session-title"], undefined);
  assert.equal(app.elements["ai-session-provider"], undefined);
  assert.equal(app.elements["ai-session-rename"], undefined);
  assert.equal(app.elements["ai-session-delete"], undefined);
  const row = app.elements["ai-session-list"].children[0];
  assert.equal(row.children.length, 2);
  row.children[1].children[0].click();
  await flush();
  const rename = calls.find((item) => item.url.endsWith("/ai/sessions/conv-001") && item.options && item.options.method === "PATCH");
  assert.deepEqual(JSON.parse(rename.options.body), { title: "我的会话" });
  row.children[1].children[1].click();
  await flush();
  assert.ok(calls.some((item) => item.url.endsWith("/ai/sessions/conv-001") && item.options && item.options.method === "DELETE"));
  app.elements["ai-session-back"].click();
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), false);
});

test("legacy provider-memory and daily-create branches are absent", () => {
  assert.equal(SOURCE.includes("AI_PROVIDER_KEY"), false);
  assert.equal(SOURCE.includes("AI_DAILY_KEY"), false);
  assert.equal(SOURCE.includes("aiLocalDate"), false);
  assert.equal(SOURCE.includes("aiTask("), false);
  assert.equal(SOURCE.includes("wb_plan_heartbeat_"), false);
});

function session(conversationId, status = "idle", currentTurnId = null) {
  return {
    conversation_id: conversationId, provider: "codex", title: conversationId,
    status, current_turn_id: currentTurnId, messages: [],
  };
}

function nodesWithClass(root, className) {
  const found = [];
  const visit = (node) => {
    if (typeof node.className === "string"
        && node.className.split(/\s+/).includes(className)) found.push(node);
    for (const child of node.children || []) visit(child);
  };
  visit(root);
  return found;
}

function queueRowIds(list) {
  return list.children.map((row) => row.dataset.turnId);
}

function queueAction(row, action) {
  return nodesWithClass(row, "ai-pending-actions")[0].children.find((node) =>
    node.dataset.action === action);
}

function recoveryAction(root, action) {
  return nodesWithClass(root, "ai-send-recovery").flatMap((card) => card.children)
    .find((node) => node.dataset.action === action);
}

function paperApproval(overrides = {}) {
  return {
    conversation_id: "conv-a", turn_id: "turn-a", revision: 1, status: "pending",
    practice_set_id: "ps-001", title: "微积分复习",
    current_problem_ids: ["p-1", "p-2"], proposed_problem_ids: ["p-2", "p-3"],
    added_problem_ids: ["p-3"], removed_problem_ids: ["p-1"],
    order_changed: false, structure_changed: true, resets_progress: true,
    completed_items: 2, draft_items: 1,
    ...overrides,
  };
}

function paperProposalMessage(approval) {
  return {
    role: "assistant", turn_id: "turn-a", content: "我建议更新这张 Paper。",
    action: {
      type: "paper_update_proposal", practice_set_id: approval.practice_set_id,
      problem_ids: approval.proposed_problem_ids, paper_approval: approval,
    },
  };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("one POST is gated until acceptance, then another message can queue behind the active turn", async () => {
  const calls = [];
  const timers = [];
  const firstPost = deferred();
  let turnPosts = 0;
  let polls = 0;
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([{ provider: "codex", name: "codex" }]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a"));
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      turnPosts += 1;
      return turnPosts === 1 ? firstPost.promise
        : response({ turn_id: "turn-b", status: "queued" });
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-a?")) {
      polls += 1;
      return response({ events: [], turn: { status: polls === 1 ? "running" : "done" } });
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-b?")) {
      return response({ events: [], turn: { status: "running" } });
    }
    return response({});
  }, {
    setTimeout: (callback) => { timers.push(callback); return timers.length; },
    clearTimeout: () => {},
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();

  let prevented = 0;
  const input = app.elements["ai-input"];
  input.value = "first message";
  input.trigger("keydown", { key: "Enter", shiftKey: false, preventDefault() { prevented += 1; } });
  input.value = "second message";
  input.trigger("keydown", { key: "Enter", shiftKey: false, preventDefault() { prevented += 1; } });

  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST").length, 1);
  assert.equal(input.value, "second message");
  assert.equal(input.disabled, false);
  assert.equal(prevented, 2);
  app.elements["goal-nl"].value = "a goal request";
  app.elements["goal-assist-send"].click();
  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST").length, 1);
  assert.match(app.elements["goal-form-status"].textContent, /仍在提交/);

  firstPost.resolve({ ok: true, json: () => Promise.resolve({ turn_id: "turn-a" }) });
  await flush();
  input.trigger("keydown", { key: "Enter", shiftKey: false, preventDefault() {} });
  const posts = calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST");
  assert.equal(posts.length, 2);
  assert.equal(JSON.parse(posts[1].options.body).message, "second message");
  assert.equal(JSON.parse(posts[1].options.body).queue_action, "queue");
  assert.equal(timers.length, 1);
  assert.equal(input.value, "");
});

test("an unknown send survives reload and reconciles with the same identity without replacing a draft", async () => {
  const outboxKey = "wb_ai_message_outbox_alpha_conv-a";
  const firstCalls = [];
  const first = setup((url, options) => {
    firstCalls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a"));
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ error: "temporary outage" }, 503);
    }
    return response({});
  });
  await flush();
  first.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  first.elements["ai-input"].value = "Keep this message";
  first.elements["ai-send"].click();
  await flush();

  const initialPost = firstCalls.find((call) => call.options?.method === "POST");
  const initialBody = JSON.parse(initialPost.options.body);
  assert.ok(initialBody.submission_id);
  assert.equal(first.elements["ai-input"].value, "");
  const saved = JSON.parse(first.localStorage.getItem(outboxKey));
  assert.equal(saved[initialBody.submission_id].status, "unknown");
  assert.equal(saved[initialBody.submission_id].body.message, "Keep this message");

  const retryCalls = [];
  const reopened = setup((url, options) => {
    retryCalls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a"));
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ turn_id: "turn-reconciled" });
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-reconciled?")) {
      return response({ events: [], turn: { status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    localSeed: { [outboxKey]: JSON.stringify(saved) },
    setTimeout: () => 1,
  });
  await flush();
  assert.equal(retryCalls.some((call) => call.options?.method === "POST"), false,
    "reopening must not automatically replay a possibly accepted send");
  const recovery = reopened.elements["ai-messages"].children.find((item) =>
    item.className === "ai-send-recoveries");
  assert.ok(recovery);
  reopened.elements["ai-input"].value = "newer draft";
  recoveryAction(recovery, "reconcile").click();
  await flush();
  const retry = retryCalls.find((call) => call.options?.method === "POST");
  const retryBody = JSON.parse(retry.options.body);
  assert.equal(retryBody.submission_id, initialBody.submission_id);
  assert.equal(retryBody.message, initialBody.message);
  assert.equal(reopened.elements["ai-input"].value, "newer draft");
});

test("a rejected send keeps its message recoverable and will not overwrite a newer draft", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a"));
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ error: "invalid request" }, 400);
    }
    return response({});
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  app.elements["ai-input"].value = "Rejected but saved";
  app.elements["ai-send"].click();
  await flush();

  const recovery = app.elements["ai-messages"].children.find((item) =>
    item.className === "ai-send-recoveries");
  assert.ok(recovery);
  assert.ok(nodesWithClass(recovery, "ai-send-recovery")[0].children[0].textContent);
  app.elements["ai-input"].value = "Do not replace me";
  recoveryAction(recovery, "restore").click();
  assert.equal(app.elements["ai-input"].value, "Do not replace me");
});

test("a failed accepted send offers a new linked attempt from its saved context", async () => {
  const outboxKey = "wb_ai_message_outbox_alpha_conv-a";
  const original = {
    conversation_id: "conv-a", submission_id: "send-original", status: "accepted",
    turn_id: "turn-001", created_at: 1,
    body: { message: "Retry me", route: "/w/alpha/kp/kp-7", submission_id: "send-original" },
  };
  const calls = [];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response({
      ...session("conv-a"), messages: [
        { role: "user", content: "Retry me", status: "failed", turn_id: "turn-001",
          submission_id: "send-original", error: "provider exit code 3" },
        { role: "assistant", content: "Partial reply", partial: true, status: "failed" },
      ],
    });
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ turn_id: "turn-002" });
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-002?")) {
      return response({ events: [], turn: { status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    localSeed: { [outboxKey]: JSON.stringify({ [original.submission_id]: original }) },
    setTimeout: () => 1,
  });
  await flush();

  const inlineRetry = nodesWithClass(app.elements["ai-messages"], "ai-inline-retry")[0];
  assert.ok(inlineRetry, "accepted failures expose their retry in conversation history");
  inlineRetry.click();
  await flush();
  const retry = calls.find((call) => call.options?.method === "POST");
  const body = JSON.parse(retry.options.body);
  assert.notEqual(body.submission_id, "send-original");
  assert.equal(body.retry_of, "turn-001");
  assert.equal(body.message, "Retry me");
  assert.equal(body.route, "/w/alpha/kp/kp-7");
});

test("tool activity cards show terminal failures and only explicit known impact", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) {
      return response([session("conv-a", "running", "turn-1")]);
    }
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response(session("conv-a", "running", "turn-1"));
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-1?")) return response({
      events: [
        { sequence: 1, kind: "activity", activity_id: "failed-write", activity_type: "tool",
          label: "Write file", status: "error", output: "permission denied" },
        { sequence: 2, kind: "activity", activity_id: "provider-command", activity_type: "command",
          label: "Run command", status: "done", output: "exit code 0" },
        { sequence: 3, kind: "activity", activity_id: "verified-ingest", activity_type: "tool",
          label: "Store batch", status: "done", impact: { status: "known", summary: "batch-9 applied" } },
      ],
      turn: { status: "running" },
    });
    return response({});
  }, { setTimeout: () => 1 });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  const rows = app.elements["ai-messages"].children[0].children[1].children;
  const failed = rows.find((item) => item.activityParts?.label.textContent === "Write file");
  const command = rows.find((item) => item.activityParts?.label.textContent === "Run command");
  const verified = rows.find((item) => item.activityParts?.label.textContent === "Store batch");
  assert.ok(failed.className.includes("is-failed"));
  assert.equal(failed.activityParts.state.textContent, "失败");
  assert.equal(failed.activityParts.impact.textContent, "影响未知");
  assert.equal(command.activityParts.impact.textContent, "影响未知");
  assert.equal(verified.activityParts.impact.textContent, "已知影响：batch-9 applied");
});

test("reloaded failed history renders saved activities without a blank assistant answer", async () => {
  const app = setup((url) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !url.includes("/conv-a")) {
      return response([session("conv-a")]);
    }
    if (url.endsWith("/ai/sessions/conv-a")) return response({
      ...session("conv-a"),
      messages: [
        { role: "user", content: "Inspect", status: "failed", turn_id: "turn-001" },
        { role: "assistant", turn_id: "turn-001", status: "failed", activities: [
          { activity_id: "cmd-failed", activity_type: "command", label: "运行命令",
            status: "failed", output: "permission denied" },
        ] },
      ],
    });
    return response({});
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();

  const children = app.elements["ai-messages"].children;
  assert.ok(children.some((child) => child.className === "ai-plan"));
  assert.equal(children.filter((child) => child.className === "msg ai").length, 0,
    "a failure with no assistant text does not render an empty answer bubble");
  assert.ok(nodesWithClass(children[0], "ai-turn-inline-status").length,
    "the failed user turn carries its truthful inline failure status");
  assert.match(deepHtml(app.elements["ai-messages"]), /permission denied/);
});

test("switching conversations clears approval and activity state and reloads events from zero", async () => {
  const calls = [];
  let timerId = 0;
  const timers = new Map();
  const stalePoll = deferred();
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      session("conv-a", "running", "turn-a"), session("conv-b", "running", "turn-b"),
    ]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a", "running", "turn-a"));
    if (url.endsWith("/ai/sessions/conv-b")) return response(session("conv-b", "running", "turn-b"));
    if (url.endsWith("/ai/sessions/conv-a/turns/turn-a?after=0")) return response({
      events: [{ sequence: 50, kind: "activity", activity_id: "a-activity", label: "A", status: "running" }],
      turn: { status: "running" },
    });
    if (url.endsWith("/ai/sessions/conv-a/turns/turn-a?after=50")) return stalePoll.promise;
    if (url.includes("/ai/sessions/conv-b/turns/turn-b?")) return response({
      events: [
        { sequence: 1, kind: "activity", activity_id: "b-1", label: "B one", status: "running" },
        { sequence: 2, kind: "activity", activity_id: "b-2", label: "B two", status: "running" },
      ],
      turn: { status: "running" },
    });
    return response({});
  }, {
    setTimeout: (callback) => { const id = ++timerId; timers.set(id, callback); return id; },
    clearTimeout: (id) => timers.delete(id),
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  assert.equal(app.ui.state.activities["a-activity"].label, "A");
  assert.equal(app.ui.state.running, true);
  const [pollTimerId, pollTimer] = timers.entries().next().value;
  timers.delete(pollTimerId);
  pollTimer();
  await flush();
  assert.ok(calls.some((call) => call.url.endsWith("/ai/sessions/conv-a/turns/turn-a?after=50")));

  let staleApprovalRuns = 0;
  app.ui.collapseAux();
  app.ui.confirm({ title: "Rollback A" }, () => { staleApprovalRuns += 1; });
  const staleApprove = app.elements["ai-approval-slot"].children[0].children[3].children[1];

  app.elements["ai-session-back"].click();
  await flush();
  assert.equal(app.ui.state.userCollapsed, false);
  assert.deepEqual(app.ui.state.activityOrder, []);
  assert.deepEqual(app.ui.state.activities, {});
  assert.equal(app.ui.state.approvalOpen, false);
  assert.equal(app.elements["ai-approval-slot"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-input-row"].classList.contains("hidden"), false);
  staleApprove.click();
  assert.equal(staleApprovalRuns, 0);

  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  assert.ok(calls.some((call) => call.url.endsWith("/ai/sessions/conv-b/turns/turn-b?after=0")));
  assert.deepEqual(app.ui.state.activityOrder, ["b-1", "b-2"]);
  assert.equal(app.ui.state.activities["a-activity"], undefined);
  assert.equal(app.ui.state.running, true);
  assert.equal(timers.size, 1);

  stalePoll.resolve({ ok: true, json: () => Promise.resolve({
    events: [{ sequence: 51, kind: "activity", activity_id: "a-stale", label: "A stale", status: "running" }],
    turn: { status: "running" },
  }) });
  await flush();
  assert.equal(app.ui.state.activities["a-stale"], undefined);
  assert.deepEqual(app.ui.state.activityOrder, ["b-1", "b-2"]);
  assert.equal(timers.size, 1);
});

test("a temporary progress read failure keeps the turn pending and permits a distinct queued message", async () => {
  const calls = [];
  const timers = [];
  let pollCount = 0;
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a", "running", "turn-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response(session("conv-a", "running", "turn-a"));
    if (url.includes("/ai/sessions/conv-a/turns/turn-a?")) {
      pollCount += 1;
      if (pollCount === 1) return Promise.reject(new Error("network unavailable"));
      return response({ events: [], turn: { status: "running" } });
    }
    return response({});
  }, { setTimeout: (callback) => { timers.push(callback); return timers.length; } });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();

  assert.equal(pollCount, 1);
  assert.equal(app.ui.state.running, true);
  assert.equal(app.elements["ai-send"].disabled, false);
  assert.equal(app.elements["ai-stop"].classList.contains("hidden"), false);
  assert.match(app.elements["ai-status"].textContent, /状态暂时未知/);
  assert.equal(app.ui.state.activities["turn-failure"], undefined);
  assert.equal(timers.length, 1);

  timers[0]();
  await flush();
  assert.equal(pollCount, 2);
  assert.equal(app.ui.state.running, true);
  assert.equal(app.elements["ai-status"].textContent, "Agent 正在处理…");
  app.elements["ai-input"].value = "duplicate";
  assert.equal(calls.some((call) => call.options?.method === "POST"
    && call.url.endsWith("/ai/sessions/conv-a/turns")), false,
  "a different message is only sent after the learner explicitly submits it");
});

test("a queued send keeps the active stream and uses the saved interrupt preference", async () => {
  const calls = [];
  const activeMessages = [{
    role: "user", content: "A", turn_id: "turn-a", status: "running",
  }];
  const timers = [];
  let acceptedB = false;
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      session("conv-a", "running", "turn-a"),
    ]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a", "running", "turn-a"),
      current_turn_id: "turn-a", queue_paused: false,
      messages: acceptedB ? [...activeMessages, {
        role: "user", content: "B", turn_id: "turn-b", status: "queued",
        queue_revision: 1, submission_id: "send-b",
      }] : activeMessages,
    });
    if (url.includes("/ai/sessions/conv-a/turns/turn-a?")) return response({
      turn: { turn_id: "turn-a", status: "running" },
      events: [{ sequence: 1, kind: "text", text: "A is still streaming" }],
    });
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      acceptedB = true;
      return response({ turn_id: "turn-b", status: "queued", message: "B" });
    }
    return response({
      ...session("conv-a", "running", "turn-a"),
      current_turn_id: "turn-a", queue_paused: false,
      messages: [...activeMessages, {
        role: "user", content: "B", turn_id: "turn-b", status: "queued",
        queue_revision: 1, submission_id: "send-b",
      }],
    });
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    localSeed: { wb_settings_alpha: JSON.stringify({ runningSendAction: "interrupt" }) },
    setTimeout: (callback) => { timers.push(callback); return timers.length; },
  });
  await flush();
  assert.equal(app.elements["ai-send"].disabled, false);
  assert.equal(app.elements["setting-running-send"].value, "interrupt");
  const stream = app.elements["ai-messages"].children.find((child) =>
    child.innerHTML.includes("A is still streaming"));
  assert.ok(stream);

  app.elements["ai-input"].value = "B";
  app.elements["ai-send"].click();
  await flush();

  const send = calls.find((call) => call.options?.method === "POST"
    && call.url.endsWith("/ai/sessions/conv-a/turns"));
  assert.equal(JSON.parse(send.options.body).queue_action, "interrupt");
  assert.equal(app.elements["ai-send"].disabled, false);
  assert.equal(app.ui.state.running, true);
  assert.ok(app.elements["ai-messages"].children.includes(stream));
  assert.equal(calls.some((call) => call.url.includes("/turns/turn-b?")), false);
  assert.equal(app.elements["ai-pending-queue"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-pending-list"].children.length, 1);
  assert.ok(timers.length >= 1, "the original turn poll remains scheduled");

  app.elements["setting-running-send"].value = "queue";
  app.elements["setting-running-send"].trigger("change");
  assert.equal(JSON.parse(app.localStorage.getItem("wb_settings_alpha")).runningSendAction, "queue");
});

test("pending messages can be edited, removed, and continued after reload", async () => {
  const calls = [];
  let messageB = "Queued B";
  let revisionB = 1;
  let statusB = "queued";
  let launchedC = false;
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      session("conv-a", launchedC ? "running" : "idle", launchedC ? "turn-c" : null),
    ]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a", launchedC ? "running" : "idle", launchedC ? "turn-c" : null),
      queue_paused: !launchedC,
      messages: [
        { role: "user", content: messageB, turn_id: "turn-b", status: statusB,
          queue_revision: revisionB, submission_id: "send-b" },
        { role: "user", content: "Queued C", turn_id: "turn-c",
          status: launchedC ? "running" : "queued", queue_revision: 1, submission_id: "send-c" },
      ],
    });
    if (url.endsWith("/turns/turn-b") && options?.method === "PATCH") {
      const body = JSON.parse(options.body);
      messageB = body.message;
      revisionB += 1;
      return response({ turn_id: "turn-b", status: "queued", message: messageB,
        queue_revision: revisionB });
    }
    if (url.endsWith("/turns/turn-b") && options?.method === "DELETE") {
      statusB = "cancelled";
      return response({ turn_id: "turn-b", status: statusB });
    }
    if (url.endsWith("/queue/continue") && options?.method === "POST") {
      launchedC = true;
      return response({ conversation_id: "conv-a", queue_paused: false,
        turn: { turn_id: "turn-c", status: "running" } });
    }
    if (url.includes("/turns/turn-c?")) {
      return response({ events: [], turn: { turn_id: "turn-c", status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();

  assert.equal(app.elements["ai-pending-queue"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-queue-continue"].classList.contains("hidden"), false);
  let card = app.elements["ai-pending-list"].children[0];
  queueAction(card, "edit").click();
  card = app.elements["ai-pending-list"].children[0];
  let editor = nodesWithClass(card, "ai-pending-editor")[0];
  assert.equal(editor.value, "Queued B");
  editor.value = "Edited B";
  queueAction(card, "save").click();
  await flush();
  const edit = calls.find((call) => call.options?.method === "PATCH");
  assert.equal(JSON.parse(edit.options.body).message, "Edited B");
  assert.equal(JSON.parse(edit.options.body).expected_revision, 1);
  card = app.elements["ai-pending-list"].children[0];
  queueAction(card, "remove").click();
  await flush();

  const remove = calls.find((call) => call.options?.method === "DELETE");
  assert.equal(JSON.parse(remove.options.body).expected_revision, 2);
  assert.equal(statusB, "cancelled");
  assert.equal(app.elements["ai-pending-list"].children.length, 1);

  app.elements["ai-queue-continue"].click();
  await flush();
  assert.ok(calls.some((call) => call.url.endsWith("/queue/continue")
    && call.options?.method === "POST"));
  assert.equal(app.ui.state.running, true);
  assert.equal(app.elements["ai-stop"].classList.contains("hidden"), false);
});

test("waiting-for-stop is outside the queue and does not keep an empty queue panel visible", async () => {
  const timers = [];
  const app = setup((url) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !url.includes("/conv-a")) {
      return response([session("conv-a")]);
    }
    if (url.endsWith("/ai/sessions/conv-a")) return response({
      ...session("conv-a", "running", "turn-a"),
      queue_order: [],
      messages: [
        { role: "user", content: "Interrupt D", turn_id: "turn-d",
          status: "waiting_for_stop", queue_revision: 3 },
      ],
    });
    if (url.includes("/turns/turn-a?")) {
      return response({ events: [], turn: { turn_id: "turn-a", status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: (callback, delay) => { timers.push({ callback, delay }); return timers.length; },
  });
  await flush();

  assert.equal(app.elements["ai-pending-queue"].classList.contains("hidden"), true);
  assert.deepEqual(queueRowIds(app.elements["ai-pending-list"]), []);
  assert.ok(app.elements["ai-handoff-status"].textContent);
  assert.ok(timers.some((timer) => timer.delay === 350),
    "waiting-for-stop keeps polling after it leaves the queued-only list");
});

test("keyboard reorder and send-now use the confirmed order and captured revision", async () => {
  const calls = [];
  const timers = [];
  let queueOrder = ["turn-b", "turn-c"];
  let statusC = "queued";
  const queued = {
    "turn-b": { role: "user", content: "Queued B", turn_id: "turn-b",
      status: "queued", queue_revision: 2 },
    "turn-c": { role: "user", content: "Queued C", turn_id: "turn-c",
      status: "queued", queue_revision: 7 },
  };
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !url.includes("/conv-a")) {
      return response([session("conv-a", "running", "turn-a")]);
    }
    if (url.endsWith("/ai/sessions/conv-a") && !options) {
      return response({ ...session("conv-a", "running", "turn-a"), queue_order: queueOrder,
        messages: [
          { role: "user", content: "Running A", turn_id: "turn-a", status: "running" },
          ...queueOrder.map((id) => ({ ...queued[id],
            status: id === "turn-c" ? statusC : "queued" })),
          ...(statusC === "waiting_for_stop"
            ? [{ ...queued["turn-c"], status: "waiting_for_stop" }] : []),
        ],
      });
    }
    if (url.endsWith("/queue/reorder") && options?.method === "POST") {
      const body = JSON.parse(options.body);
      queueOrder = body.turn_ids;
      return response({ conversation_id: "conv-a", queue_order: queueOrder });
    }
    if (url.endsWith("/turns/turn-c/interrupt") && options?.method === "POST") {
      statusC = "waiting_for_stop";
      queueOrder = queueOrder.filter((id) => id !== "turn-c");
      return response({ turn_id: "turn-c", status: "waiting_for_stop" });
    }
    if (url.includes("/turns/turn-a?")) {
      return response({ events: [], turn: { turn_id: "turn-a", status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: (callback, delay) => { timers.push({ callback, delay }); return timers.length; },
  });
  await flush();

  assert.deepEqual(queueRowIds(app.elements["ai-pending-list"]), ["turn-b", "turn-c"]);
  let cHandle = nodesWithClass(app.elements["ai-pending-list"], "ai-pending-handle")
    .find((node) => node.dataset.turnId === "turn-c");
  assert.ok(cHandle, "each row exposes a keyboard-operable drag handle");
  const originalRow = app.elements["ai-pending-list"].children.find((row) =>
    row.dataset.turnId === "turn-c");
  cHandle.focus();
  const queuePoll = timers.find((timer) => timer.delay === 350);
  assert.ok(queuePoll, "queued work keeps its refresh poll active");
  queuePoll.callback();
  await flush();
  cHandle = nodesWithClass(app.elements["ai-pending-list"], "ai-pending-handle")
    .find((node) => node.dataset.turnId === "turn-c");
  const polledRow = app.elements["ai-pending-list"].children.find((row) =>
    row.dataset.turnId === "turn-c");
  assert.strictEqual(polledRow, originalRow, "an unchanged row keeps its DOM node across polling");
  assert.equal(cHandle.focused, true, "polling preserves focus on the same row handle");
  cHandle.trigger("keydown", { key: "ArrowUp", preventDefault() {} });
  await flush();

  const reorder = calls.find((call) => call.url.endsWith("/queue/reorder"));
  assert.ok(reorder, "keyboard movement is confirmed by the reorder endpoint");
  assert.deepEqual(JSON.parse(reorder.options.body), {
    expected_order: ["turn-b", "turn-c"], turn_ids: ["turn-c", "turn-b"],
  });
  assert.deepEqual(queueRowIds(app.elements["ai-pending-list"]), ["turn-c", "turn-b"]);

  const cRow = app.elements["ai-pending-list"].children.find((row) =>
    row.dataset.turnId === "turn-c");
  queueAction(cRow, "send-now").click();
  await flush();
  const sendNow = calls.find((call) => call.url.endsWith("/turns/turn-c/interrupt"));
  assert.ok(sendNow);
  assert.deepEqual(JSON.parse(sendNow.options.body), { expected_revision: 7 });
  assert.deepEqual(queueRowIds(app.elements["ai-pending-list"]), ["turn-b"]);
  assert.ok(app.elements["ai-handoff-status"].textContent);
});

test("queue polling preserves an edit draft and focus while saving with its original revision", async () => {
  const calls = [];
  const timers = [];
  let revision = 1;
  let queuedText = "Queued B";
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !url.includes("/conv-a")) {
      return response([session("conv-a", "running", "turn-a")]);
    }
    if (url.endsWith("/ai/sessions/conv-a") && !options) {
      return response({ ...session("conv-a", "running", "turn-a"), queue_order: ["turn-b"],
        messages: [
          { role: "user", content: "Running A", turn_id: "turn-a", status: "running" },
          { role: "user", content: queuedText, turn_id: "turn-b", status: "queued",
            queue_revision: revision },
        ],
      });
    }
    if (url.includes("/turns/turn-a?")) {
      return response({ events: [], turn: { turn_id: "turn-a", status: "running" } });
    }
    if (url.endsWith("/turns/turn-b") && options?.method === "PATCH") {
      return response({ turn_id: "turn-b", status: "queued" });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: (callback, delay) => { timers.push({ callback, delay }); return timers.length; },
  });
  await flush();

  let row = app.elements["ai-pending-list"].children[0];
  const editAction = queueAction(row, "edit");
  assert.ok(editAction, "queued rows expose an edit action");
  editAction.click();
  let editor = nodesWithClass(app.elements["ai-pending-list"], "ai-pending-editor")[0];
  editor.value = "Learner's unsaved draft";
  editor.trigger("input");
  revision = 2;
  const queuePoll = timers.find((timer) => timer.delay === 350);
  assert.ok(queuePoll, "queued work keeps its refresh poll active");
  queuePoll.callback();
  await flush();

  row = app.elements["ai-pending-list"].children[0];
  editor = nodesWithClass(row, "ai-pending-editor")[0];
  assert.ok(editor, "the row remains in edit mode after polling");
  assert.equal(editor.value, "Learner's unsaved draft");
  assert.equal(editor.focused, true);
  queueAction(row, "save").click();
  await flush();
  const save = calls.find((call) => call.url.endsWith("/turns/turn-b")
    && call.options?.method === "PATCH");
  assert.deepEqual(JSON.parse(save.options.body), {
    message: "Learner's unsaved draft", expected_revision: 1,
  });
});

test("recovery summary is compact and accepted failures retry inline with captured context", async () => {
  const outboxKey = "wb_ai_message_outbox_alpha_conv-a";
  const records = {
    unknown: { conversation_id: "conv-a", submission_id: "uncertain", status: "unknown",
      created_at: 1, body: { message: "Unknown send", submission_id: "uncertain" } },
    rejected: { conversation_id: "conv-a", submission_id: "rejected", status: "rejected",
      created_at: 2, body: { message: "Rejected send", submission_id: "rejected" } },
    "failed-send": { conversation_id: "conv-a", submission_id: "failed-send", status: "accepted",
      turn_id: "turn-failed", created_at: 3,
      body: { message: "Accepted failed", route: "/w/alpha/kp/kp-7",
        selected_kp_ids: ["kp-7"], queue_action: "interrupt", submission_id: "failed-send" } },
  };
  const calls = [];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !url.includes("/conv-a")) {
      return response([session("conv-a")]);
    }
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a"),
      messages: [
        { role: "user", content: "Accepted failed", status: "failed", turn_id: "turn-failed",
          submission_id: "failed-send", error: "provider exit code 3" },
        { role: "assistant", content: "Partial output", partial: true,
          status: "failed", turn_id: "turn-failed" },
      ],
    });
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ turn_id: "turn-retry", status: "queued" });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    localSeed: { [outboxKey]: JSON.stringify(records) },
    setTimeout: () => 1,
  });
  await flush();

  const recoveries = nodesWithClass(app.elements["ai-messages"], "ai-send-recoveries");
  assert.equal(recoveries.length, 1);
  assert.match(recoveries[0].children[0].textContent, /2/);
  assert.equal(nodesWithClass(recoveries[0], "ai-send-recovery").length, 2);
  assert.equal(nodesWithClass(app.elements["ai-messages"], "ai-inline-retry").length, 1);
  assert.match(nodesWithClass(app.elements["ai-messages"], "ai-turn-inline-status")[0].textContent,
    /provider exit code 3/);

  nodesWithClass(app.elements["ai-messages"], "ai-inline-retry")[0].click();
  await flush();
  const retry = calls.find((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST");
  const body = JSON.parse(retry.options.body);
  assert.equal(body.message, "Accepted failed");
  assert.equal(body.route, "/w/alpha/kp/kp-7");
  assert.deepEqual(body.selected_kp_ids, ["kp-7"]);
  assert.equal(body.retry_of, "turn-failed");
  assert.notEqual(body.submission_id, "failed-send");
  assert.equal(body.queue_action, "queue");
});

test("pending Paper approval restores beside the composer and accepts sends into the paused queue", async () => {
  const calls = [];
  const approval = paperApproval({ confirmation: "opaque-confirmation", draft_answer: "private answer" });
  const queued = [
    { role: "user", content: "Queued B", turn_id: "turn-b", status: "queued", queue_revision: 1 },
  ];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a"), queue_paused: true,
      pending_paper_approval: approval,
      messages: [...queued, paperProposalMessage(approval)],
    });
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      const body = JSON.parse(options.body);
      queued.push({ role: "user", content: body.message, turn_id: "turn-c", status: "queued",
        queue_revision: 1, submission_id: body.submission_id });
      return response({ turn_id: "turn-c", status: "queued", message: body.message });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  const panel = app.elements["ai-paper-approval"];
  assert.equal(panel.classList.contains("hidden"), false);
  assert.equal(app.elements["ai-queue-continue"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-input"].disabled, false);
  const approvalText = app.elements["ai-paper-approval-status"].textContent
    + deepText(app.elements["ai-paper-approval-details"]);
  assert.match(approvalText, /微积分复习/);
  assert.match(approvalText, /p-1.*p-2/);
  assert.match(approvalText, /p-2.*p-3/);
  assert.match(approvalText, /未完成练习中的进度（当前已完成 2 项）/);
  assert.match(approvalText, /草稿 1 份/);
  assert.doesNotMatch(approvalText, /opaque-confirmation|private answer/);

  app.elements["ai-input"].value = "Queued C";
  app.elements["ai-send"].click();
  await flush();
  await flush();

  assert.equal(app.elements["ai-input"].disabled, false);
  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-queue-continue"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-pending-list"].children.length, 2);
  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST").length, 1);
  assert.equal(calls.some((call) => call.url.endsWith("/queue/continue")), false);
  assert.equal(calls.some((call) => call.url.includes("/turns/turn-c?")), false);
});

test("stale Paper approval refreshes impact and requires a second click", async () => {
  const calls = [];
  let approval = paperApproval();
  const queued = [{ role: "user", content: "Queued B", turn_id: "turn-b", status: "queued",
    queue_revision: 1 }];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a"), queue_paused: true,
      pending_paper_approval: approval,
      messages: [...queued, paperProposalMessage(approval)],
    });
    if (url.endsWith("/paper-approval") && options?.method === "POST") {
      const body = JSON.parse(options.body);
      if (body.expected_revision === 1) {
        approval = paperApproval({ revision: 2, completed_items: 3, draft_items: 2 });
        return response({ conversation_id: "conv-a", turn_id: "turn-a", approval,
          queue_paused: true, stale: true });
      }
      approval = paperApproval({ revision: 2, status: "approved", completed_items: 3,
        draft_items: 2 });
      return response({ conversation_id: "conv-a", turn_id: "turn-a", approval,
        queue_paused: true, stale: false });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  app.elements["ai-paper-approval-approve"].click();
  app.elements["ai-paper-approval-approve"].click();
  await flush();
  await flush();
  const firstDecision = calls.find((call) => call.url.endsWith("/paper-approval"));
  assert.deepEqual(JSON.parse(firstDecision.options.body), {
    turn_id: "turn-a", expected_revision: 1, decision: "approve",
  });
  assert.equal(calls.filter((call) => call.url.endsWith("/paper-approval")).length, 1,
    "a repeated click cannot submit while the first decision is being reconciled");
  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), false);
  assert.match(app.elements["ai-paper-approval-status"].textContent, /已变化/);
  const refreshedImpact = deepText(app.elements["ai-paper-approval-details"]);
  assert.match(refreshedImpact, /未完成练习中的进度（当前已完成 3 项）/);
  assert.match(refreshedImpact, /草稿 2 份/);

  app.elements["ai-paper-approval-approve"].click();
  await flush();
  await flush();
  const decisions = calls.filter((call) => call.url.endsWith("/paper-approval"));
  assert.equal(decisions.length, 2);
  assert.equal(JSON.parse(decisions[1].options.body).expected_revision, 2);
  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-queue-continue"].classList.contains("hidden"), false);
  assert.match(deepText(app.elements["ai-messages"]), /已批准/);
  assert.equal(calls.some((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST"), false);
});

test("stale Paper cancellation asks for a fresh cancel decision", async () => {
  const calls = [];
  let approval = paperApproval();
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a"), queue_paused: true, pending_paper_approval: approval,
      messages: [paperProposalMessage(approval)],
    });
    if (url.endsWith("/paper-approval") && options?.method === "POST") {
      const body = JSON.parse(options.body);
      if (body.expected_revision === 1) {
        approval = paperApproval({ revision: 2, completed_items: 3, draft_items: 2 });
        return response({ conversation_id: "conv-a", turn_id: "turn-a", approval,
          queue_paused: true, stale: true });
      }
      approval = paperApproval({ revision: 2, status: "cancelled" });
      return response({ conversation_id: "conv-a", turn_id: "turn-a", approval,
        queue_paused: true, stale: false });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  app.elements["ai-paper-approval-cancel"].click();
  await flush();
  await flush();
  assert.match(app.elements["ai-paper-approval-status"].textContent, /再次点击「取消更新」/);
  assert.doesNotMatch(app.elements["ai-paper-approval-status"].textContent, /批准更新/);

  app.elements["ai-paper-approval-cancel"].click();
  await flush();
  await flush();
  const decisions = calls.filter((call) => call.url.endsWith("/paper-approval"));
  assert.equal(decisions.length, 2);
  assert.deepEqual(JSON.parse(decisions[1].options.body), {
    turn_id: "turn-a", expected_revision: 2, decision: "cancel",
  });
  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), true);
  assert.match(deepText(app.elements["ai-messages"]), /已取消/);
});

test("a late Paper approval response cannot change the newly selected conversation", async () => {
  const pendingPost = deferred();
  const calls = [];
  const approval = paperApproval();
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a"), session("conv-b")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a"), queue_paused: true, pending_paper_approval: approval,
      messages: [paperProposalMessage(approval)],
    });
    if (url.endsWith("/ai/sessions/conv-b") && !options) return response({
      ...session("conv-b"), messages: [{ role: "assistant", content: "B 的历史。" }],
    });
    if (url.endsWith("/paper-approval") && options?.method === "POST") return pendingPost.promise;
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  app.elements["ai-paper-approval-approve"].click();
  app.elements["ai-session-back"].click();
  await flush();
  assert.equal(app.elements["ai-session-list"].children.length, 2);
  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  await flush();
  assert.equal(JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-b");
  pendingPost.resolve(response({ conversation_id: "conv-a", turn_id: "turn-a",
    approval: paperApproval({ status: "approved" }), queue_paused: true, stale: false }));
  await flush();
  await flush();

  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), true);
  assert.ok(deepHtml(app.elements["ai-messages"]).includes("B 的历史。"));
  assert.doesNotMatch(deepHtml(app.elements["ai-messages"]), /已批准/);
  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a")
    && !call.options).length, 1, "the stale response does not refresh or replace conversation B");
});

test("cancelling a restored Paper approval leaves the queue paused for manual continuation", async () => {
  const calls = [];
  let approval = paperApproval();
  let continued = false;
  const queued = [{ role: "user", content: "Queued B", turn_id: "turn-b", status: "queued",
    queue_revision: 1 }];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a", continued ? "running" : "idle", continued ? "turn-b" : null),
      queue_paused: !continued,
      pending_paper_approval: approval.status === "pending" ? approval : null,
      messages: continued ? [{ ...queued[0], status: "running" }, paperProposalMessage(approval)]
        : [...queued, paperProposalMessage(approval)],
    });
    if (url.endsWith("/paper-approval") && options?.method === "POST") {
      approval = paperApproval({ status: "cancelled" });
      return response({ conversation_id: "conv-a", turn_id: "turn-a", approval,
        queue_paused: true, stale: false });
    }
    if (url.endsWith("/queue/continue") && options?.method === "POST") {
      continued = true;
      return response({ conversation_id: "conv-a", queue_paused: false,
        turn: { turn_id: "turn-b", status: "running" } });
    }
    if (url.includes("/turns/turn-b?")) {
      return response({ events: [], turn: { turn_id: "turn-b", status: "running" } });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), false,
    "a full page reopen restores the pending approval");
  app.elements["ai-paper-approval-cancel"].click();
  await flush();
  await flush();

  assert.equal(app.elements["ai-paper-approval"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-pending-list"].children.length, 1);
  assert.equal(app.elements["ai-queue-continue"].classList.contains("hidden"), false);
  assert.equal(calls.some((call) => call.url.endsWith("/queue/continue")), false);
  assert.match(deepText(app.elements["ai-messages"]), /已取消/);

  app.elements["ai-queue-continue"].click();
  await flush();
  assert.equal(calls.filter((call) => call.url.endsWith("/queue/continue")).length, 1);
  assert.equal(continued, true);
});

test("completed queued turns are adopted when continue finishes before polling", async () => {
  const calls = [];
  let continued = false;
  const messages = () => continued ? [
    { role: "user", content: "A", turn_id: "turn-a", status: "cancelled" },
    { role: "user", content: "D", turn_id: "turn-d", status: "done" },
    { role: "assistant", content: "Answer D", turn_id: "turn-d" },
    { role: "user", content: "B", turn_id: "turn-b", status: "done" },
    { role: "assistant", content: "Answer B", turn_id: "turn-b" },
    { role: "user", content: "C", turn_id: "turn-c", status: "done" },
    { role: "assistant", content: "Answer C", turn_id: "turn-c" },
  ] : [
    { role: "user", content: "A", turn_id: "turn-a", status: "cancelled" },
    { role: "user", content: "D", turn_id: "turn-d", status: "done" },
    { role: "assistant", content: "Answer D", turn_id: "turn-d" },
    { role: "user", content: "B", turn_id: "turn-b", status: "queued", queue_revision: 1 },
    { role: "user", content: "C", turn_id: "turn-c", status: "queued", queue_revision: 1 },
  ];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      session("conv-a", "idle"),
    ]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) return response({
      ...session("conv-a", "idle"), queue_paused: !continued, messages: messages(),
    });
    if (url.endsWith("/queue/continue") && options?.method === "POST") {
      continued = true;
      return response({ conversation_id: "conv-a", queue_paused: false, turn: null });
    }
    return response({});
  }, {
    seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") },
    setTimeout: () => 1,
  });
  await flush();

  assert.ok(deepHtml(app.elements["ai-messages"]).includes("Answer D"));
  app.elements["ai-queue-continue"].click();
  await flush();
  await flush();

  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a")
    && !call.options).length >= 3, true, "continue refreshes history after completion");
  assert.ok(deepHtml(app.elements["ai-messages"]).includes("Answer B"));
  assert.ok(deepHtml(app.elements["ai-messages"]).includes("Answer C"));
});

const paperArtifact = {
  type: "paper_artifact", practice_set_id: "ps-001",
  title: "Managed paper", item_count: 2,
};

const liveArtifactKey = "wb_ai_live_artifact_alpha";
const route = "/w/alpha/kp/kp-7";

function liveArtifactMarker(conversationId = "conv-a", previewRoute = route) {
  return JSON.stringify({
    conversation_id: conversationId,
    practice_set_id: paperArtifact.practice_set_id,
    route: previewRoute,
  });
}

function artifactPreviewButton(app) {
  const card = app.elements["ai-messages"].children.find((child) =>
    child.className === "msg ai agent-artifact-card");
  assert.ok(card, "the restored conversation contains an Artifact card");
  return card.children[card.children.length - 1].children[0];
}

test("the finished turn artifact keeps its preview across the conversation reload", async () => {
  let loads = 0;
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([
      session("conv-a", "running", "turn-a"), session("conv-b"),
    ]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      loads += 1;
      // The first load still reports the running turn, so one poll observes the
      // finished answer; every later load is the durable record.
      return response({
        ...session("conv-a", loads === 1 ? "running" : "idle", loads === 1 ? "turn-a" : null),
        messages: [{
          role: "assistant", content: "saved ps-001.", action: paperArtifact,
        }],
      });
    }
    if (url.endsWith("/ai/sessions/conv-b")) return response(session("conv-b"));
    if (url.includes("/ai/sessions/conv-a/turns/turn-a?")) {
      return response({ events: [], turn: { status: "done", action: paperArtifact } });
    }
    return response({});
  });
  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();

  assert.equal(app.ui.state.latestArtifact.practice_set_id, "ps-001");
  assert.deepEqual(JSON.parse(app.window.sessionStorage.getItem(liveArtifactKey)), {
    conversation_id: "conv-a",
    practice_set_id: "ps-001",
    route,
  });
  app.ui.collapseAux();
  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
  artifactPreviewButton(app).click();
  assert.deepEqual(JSON.parse(app.window.sessionStorage.getItem(liveArtifactKey)), {
    conversation_id: "conv-a",
    practice_set_id: "ps-001",
    route,
  }, "explicitly reopening the current live Artifact restores its reload marker");
  assert.equal(
    app.elements["agent-artifact-split"].classList.contains("hidden"), false,
    "the newest artifact of a finished turn still previews after the reload",
  );

  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);

  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  assert.equal(
    app.elements["agent-artifact-split"].classList.contains("hidden"), true,
    "restored history cards stay closed and never auto-preview",
  );
  assert.ok(
    deepText(app.elements["ai-messages"]).includes("Managed paper"),
    "the artifact card itself is still restored in the conversation",
  );
});

test("a same-tab reload restores a live Paper preview for the same conversation and route", async () => {
  const seed = {
    wb_ai_conversation_alpha: JSON.stringify("conv-a"),
    [liveArtifactKey]: liveArtifactMarker(),
  };
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    return response({});
  }, { seed });
  await flush();
  await flush();

  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), false);
  assert.deepEqual(JSON.parse(app.window.sessionStorage.getItem(liveArtifactKey)), {
    conversation_id: "conv-a",
    practice_set_id: "ps-001",
    route,
  });
});

test("collapsing the Artifact preview clears its reload marker", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    return response({});
  }, { seed: {
    wb_ai_conversation_alpha: JSON.stringify("conv-a"),
    [liveArtifactKey]: liveArtifactMarker(),
  } });
  await flush();
  await flush();
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), false);

  app.ui.collapseAux();

  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);
});

test("starting a new user turn clears the live Artifact reload marker", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a") && !options) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ turn_id: "turn-new" });
    }
    return response({});
  }, {
    seed: {
      wb_ai_conversation_alpha: JSON.stringify("conv-a"),
      [liveArtifactKey]: liveArtifactMarker(),
    },
    setTimeout: () => 1,
  });
  await flush();
  await flush();

  app.elements["ai-input"].value = "new question";
  app.elements["ai-send"].click();
  await flush();

  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
});

test("goal-assist turns clear the live Artifact marker through the shared submit path", async () => {
  const calls = [];
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([{ provider: "codex", name: "codex" }]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    if (url.endsWith("/ai/sessions/conv-a/turns") && options?.method === "POST") {
      return response({ turn_id: "turn-goal" });
    }
    return response({});
  }, {
    seed: {
      wb_ai_conversation_alpha: JSON.stringify("conv-a"),
      [liveArtifactKey]: liveArtifactMarker(),
    },
    setTimeout: () => 1,
    clearTimeout: () => {},
  });
  await flush();
  await flush();
  assert.ok(app.window.sessionStorage.getItem(liveArtifactKey));

  app.elements["goal-nl"].value = "add a study goal";
  app.elements["goal-assist-send"].click();
  await flush();

  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
  assert.ok(calls.some((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST"));
});

test("explicit preview of a restored historical Artifact does not create a live reload marker", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();
  await flush();

  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);
  artifactPreviewButton(app).click();

  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), false);
  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
});

test("native navigation to another route clears the live Artifact reload marker", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      return response({ ...session("conv-a"), messages: [{
        role: "assistant", content: "saved ps-001.", action: paperArtifact,
      }] });
    }
    return response({});
  }, {
    route: "/w/alpha/practice-sets",
    seed: {
      wb_ai_conversation_alpha: JSON.stringify("conv-a"),
      [liveArtifactKey]: liveArtifactMarker(),
    },
  });
  await flush();
  await flush();

  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);
  assert.ok(deepText(app.elements["ai-messages"]).includes("Managed paper"));
});

test("a pending live Artifact reload from one conversation cannot open another conversation's history", async () => {
  const calls = [];
  const pendingAReload = deferred();
  let convALoads = 0;
  const app = setup((url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a"), session("conv-b")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      convALoads += 1;
      if (convALoads === 1) return response(session("conv-a", "running", "turn-a"));
      return pendingAReload.promise;
    }
    if (url.endsWith("/ai/sessions/conv-b")) {
      return response({ ...session("conv-b"), messages: [{
        role: "assistant", content: "same managed Paper in history.", action: paperArtifact,
      }] });
    }
    if (url.includes("/ai/sessions/conv-a/turns/turn-a?")) {
      return response({ events: [], turn: { status: "done", action: paperArtifact } });
    }
    return response({});
  }, { setTimeout: () => 1 });

  await flush();
  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  await flush();
  assert.equal(convALoads, 2, "the completed turn has started its follow-up conversation reload");
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), false);

  app.elements["ai-session-back"].click();
  await flush();
  assert.equal(app.window.sessionStorage.getItem(liveArtifactKey), null);
  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);
  assert.ok(deepText(app.elements["ai-messages"]).includes("Managed paper"));

  pendingAReload.resolve(response({ ...session("conv-a"), messages: [{
    role: "assistant", content: "late response from A.", action: paperArtifact,
  }] }));
  await flush();
  assert.equal(app.elements["agent-artifact-split"].classList.contains("hidden"), true);
  assert.ok(deepHtml(app.elements["ai-messages"]).includes("same managed Paper in history."));
  assert.equal(deepHtml(app.elements["ai-messages"]).includes("late response from A."), false);
});

function deepText(element) {
  return (element.children || []).map(deepText).join(" ") + " " + (element.textContent || "");
}

function deepHtml(element) {
  return [element.innerHTML || "", ...(element.children || []).map(deepHtml)].join(" ");
}
test("reopening a page restores the Agent conversation instead of the list", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return response({
      ...session("conv-a"),
      messages: [{ role: "assistant", content: "上一轮的回复", action: null }],
    });
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();
  await flush();

  assert.equal(
    app.elements["ai-chat-view"].classList.contains("hidden"), false,
    "the open conversation stays open when the middle view changes",
  );
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
  assert.deepEqual(
    JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-a");
  assert.ok(
    app.elements["ai-messages"].children.some(
      (child) => child.innerHTML.includes("上一轮的回复")),
    "the restored conversation renders its durable messages",
  );
});

test("a stored conversation that no longer exists falls back to the list", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([]);
    if (url.endsWith("/ai/sessions/conv-gone")) {
      return response({ error: "unknown conversation" }, 404);
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-gone") } });
  await flush();
  await flush();

  assert.equal(app.window.sessionStorage.getItem("wb_ai_conversation_alpha"), null);
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), false);
});

test("a stale 404 cannot clear a newer conversation selected during restore", async () => {
  const initial = deferred();
  const selected = deferred();
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) {
      return response([session("conv-old"), session("conv-new")]);
    }
    if (url.endsWith("/ai/sessions/conv-old")) return initial.promise;
    if (url.endsWith("/ai/sessions/conv-new")) return selected.promise;
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-old") } });
  await flush();

  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  initial.resolve({
    ok: false, status: 404, json: () => Promise.resolve({ error: "gone" }),
  });
  await flush();
  selected.resolve({ ok: true, status: 200, json: () => Promise.resolve(session("conv-new")) });
  await flush();

  assert.equal(
    JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-new",
  );
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
});

test("a stale 503 does not show a restore error over a newer selection", async () => {
  const initial = deferred();
  const selected = deferred();
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) {
      return response([session("conv-old"), session("conv-new")]);
    }
    if (url.endsWith("/ai/sessions/conv-old")) return initial.promise;
    if (url.endsWith("/ai/sessions/conv-new")) return selected.promise;
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-old") } });
  await flush();

  app.elements["ai-session-list"].children[1].children[0].click();
  await flush();
  initial.resolve({
    ok: false, status: 503, json: () => Promise.resolve({ error: "unavailable" }),
  });
  await flush();

  assert.equal(
    JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-new",
  );
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-status"].textContent, "");

  selected.resolve({ ok: true, status: 200, json: () => Promise.resolve(session("conv-new")) });
  await flush();
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
});

test("a stale same-session failure cannot override a newer successful load", async () => {
  const initial = deferred();
  const retry = deferred();
  let calls = 0;
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      calls += 1;
      return calls === 1 ? initial.promise : retry.promise;
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();

  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  retry.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({
      ...session("conv-a"), messages: [{ role: "assistant", content: "较新的会话内容" }],
    }),
  });
  await flush();
  initial.resolve({
    ok: false, status: 503, json: () => Promise.resolve({ error: "unavailable" }),
  });
  await flush();

  assert.equal(app.elements["ai-status"].textContent, "");
  assert.equal(app.elements["ai-send"].disabled, false);
  assert.ok(app.elements["ai-messages"].children.some(
    (child) => child.innerHTML.includes("较新的会话内容"),
  ));
});

test("a stale same-session success cannot replace the latest conversation content", async () => {
  const initial = deferred();
  const retry = deferred();
  let calls = 0;
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      calls += 1;
      return calls === 1 ? initial.promise : retry.promise;
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();

  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();
  retry.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({
      ...session("conv-a"), messages: [{ role: "assistant", content: "最新的会话内容" }],
    }),
  });
  await flush();
  initial.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({
      ...session("conv-a"), messages: [{ role: "assistant", content: "过期的会话内容" }],
    }),
  });
  await flush();

  assert.ok(app.elements["ai-messages"].children.some(
    (child) => child.innerHTML.includes("最新的会话内容"),
  ));
  assert.equal(app.elements["ai-messages"].children.some(
    (child) => child.innerHTML.includes("过期的会话内容"),
  ), false);
});

test("a current same-session retry failure stays visible after stale startup success", async () => {
  const initial = deferred();
  const retry = deferred();
  const unhandled = [];
  let calls = 0;
  const onUnhandled = (error) => unhandled.push(error);
  process.on("unhandledRejection", onUnhandled);
  try {
    const app = setup((url, options) => {
      if (url.endsWith("/ai/providers")) return response([]);
      if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
      if (url.endsWith("/ai/sessions/conv-a")) {
        calls += 1;
        return calls === 1 ? initial.promise : retry.promise;
      }
      return response({});
    }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
    await flush();

    app.elements["ai-session-list"].children[0].children[0].click();
    retry.resolve({
      ok: false, status: 503, json: () => Promise.resolve({ error: "unavailable" }),
    });
    await flush();
    initial.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        ...session("conv-a"), messages: [{ role: "assistant", content: "stale startup content" }],
      }),
    });
    await flush();

    assert.equal(
      JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-a",
    );
    assert.match(app.elements["ai-status"].textContent, /unavailable/);
    assert.equal(app.elements["ai-send"].disabled, true);
    assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
    assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
    assert.equal(app.elements["ai-messages"].children.some(
      (child) => child.innerHTML.includes("stale startup content"),
    ), false);
    assert.equal(unhandled.length, 0);
  } finally {
    process.removeListener("unhandledRejection", onUnhandled);
  }
});

test("a current 404 while opening a conversation returns to the list", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-gone")]);
    if (url.endsWith("/ai/sessions/conv-gone")) {
      return response({ error: "unknown conversation" }, 404);
    }
    return response({});
  });
  await flush();

  app.elements["ai-session-list"].children[0].children[0].click();
  await flush();

  assert.equal(app.window.sessionStorage.getItem("wb_ai_conversation_alpha"), null);
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-status"].textContent, "");
});

test("opening the provider picker supersedes an in-flight conversation restore", async () => {
  const initial = deferred();
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) return initial.promise;
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();

  app.elements["ai-new-session"].click();
  await flush();
  initial.resolve({ ok: true, status: 200, json: () => Promise.resolve(session("conv-a")) });
  await flush();

  assert.equal(app.elements["ai-provider-picker"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
});

test("opening the provider picker before startup restore prevents that restore", async () => {
  const providers = deferred();
  let providerCalls = 0;
  let restoreReads = 0;
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) {
      providerCalls += 1;
      return providerCalls === 1 ? providers.promise : response([]);
    }
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-a")]);
    if (url.endsWith("/ai/sessions/conv-a")) {
      restoreReads += 1;
      return response(session("conv-a"));
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-a") } });
  await flush();

  app.elements["ai-new-session"].click();
  await flush();
  providers.resolve(response([]));
  await flush();

  assert.equal(restoreReads, 0);
  assert.equal(app.elements["ai-provider-picker"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), true);
});

test("a 503 while restoring keeps the conversation selected and shows a retryable error", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-temporary")]);
    if (url.endsWith("/ai/sessions/conv-temporary")) {
      return response({ error: "service unavailable" }, 503);
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-temporary") } });
  await flush();
  await flush();

  assert.equal(
    JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-temporary",
  );
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
  assert.match(app.elements["ai-status"].textContent, /刷新页面可重试/);
  assert.equal(app.elements["ai-send"].disabled, true);
});

test("a network failure while restoring keeps the conversation selected and shows a retryable error", async () => {
  const app = setup((url, options) => {
    if (url.endsWith("/ai/providers")) return response([]);
    if (url.endsWith("/ai/sessions") && !options) return response([session("conv-network")]);
    if (url.endsWith("/ai/sessions/conv-network")) {
      return Promise.reject(new Error("Failed to fetch"));
    }
    return response({});
  }, { seed: { wb_ai_conversation_alpha: JSON.stringify("conv-network") } });
  await flush();
  await flush();

  assert.equal(
    JSON.parse(app.window.sessionStorage.getItem("wb_ai_conversation_alpha")), "conv-network",
  );
  assert.equal(app.elements["ai-chat-view"].classList.contains("hidden"), false);
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), true);
  assert.match(app.elements["ai-status"].textContent, /刷新页面可重试/);
  assert.equal(app.elements["ai-send"].disabled, true);
});
