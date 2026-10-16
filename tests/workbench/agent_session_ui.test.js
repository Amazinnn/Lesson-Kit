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
  focus() {}
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
  Object.entries(options.seed || {}).forEach(([key, value]) => storage.setItem(key, value));
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
  ["agent-activity-float", "agent-bottom-dock", "agent-artifact-split", "ai-approval-slot"]
    .forEach((id) => elements[id].classList.add("hidden"));
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  const window = {
    location: "", innerWidth: 1280, addEventListener() {},
    matchMedia() { return { matches: false }; },
    prompt() { return "我的会话"; }, confirm() { return true; },
    sessionStorage: storage,
  };
  const ui = AgentUISurfaces(document, window);
  const sandbox = {
    document, window, fetch, PracticeDeck, AgentUISurfaces: ui,
    sessionStorage: storage, localStorage: new Storage(), console,
    setInterval, clearInterval,
    setTimeout: options.setTimeout || setTimeout,
    clearTimeout: options.clearTimeout || clearTimeout,
    requestAnimationFrame: (callback) => setImmediate(() => callback(0)),
    cancelAnimationFrame: clearImmediate,
  };
  const context = vm.createContext(sandbox);
  vm.runInContext(PRACTICE_FLOW_SOURCE, context, { filename: "practice-flow.js" });
  vm.runInContext(SOURCE, context, { filename: "workbench.js" });
  return { elements, window, ui };
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

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("two Enter presses cannot submit another turn before the first POST is accepted", async () => {
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
      return turnPosts === 1 ? firstPost.promise : response({ turn_id: "turn-b" });
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
  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST").length, 1);
  assert.equal(timers.length, 1);
  assert.equal(input.value, "second message");

  timers[0]();
  await flush();
  input.trigger("keydown", { key: "Enter", shiftKey: false, preventDefault() {} });
  assert.equal(calls.filter((call) => call.url.endsWith("/ai/sessions/conv-a/turns")
    && call.options?.method === "POST").length, 2);
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

test("a temporary progress read failure keeps the turn pending and does not invite resend", async () => {
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
  assert.equal(app.elements["ai-send"].disabled, true);
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
  app.elements["ai-input"].trigger("keydown", { key: "Enter", shiftKey: false, preventDefault() {} });
  assert.equal(calls.some((call) => call.options?.method === "POST"
    && call.url.endsWith("/ai/sessions/conv-a/turns")), false);
});

const paperArtifact = {
  type: "paper_artifact", practice_set_id: "ps-001",
  title: "Managed paper", item_count: 2,
};

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

function deepText(element) {
  return (element.children || []).map(deepText).join(" ") + " " + (element.textContent || "");
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
