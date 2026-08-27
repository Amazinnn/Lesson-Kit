"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const GraphPhysics = require("../../workbench/server/static/graph-physics.js");

const SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/workbench.js"),
  "utf8",
);

class FakeClassList {
  constructor() {
    this.values = new Set();
  }

  add(value) {
    this.values.add(value);
  }

  remove(value) {
    this.values.delete(value);
  }

  toggle(value, force) {
    if (force === undefined) force = !this.values.has(value);
    if (force) this.add(value);
    else this.remove(value);
    return force;
  }

  contains(value) {
    return this.values.has(value);
  }
}

class FakeElement {
  constructor(id, options = {}) {
    this.id = id;
    this.dataset = options.dataset || {};
    this.value = options.value || "";
    this.checked = options.checked || false;
    this.disabled = false;
    this.listeners = {};
    this.classList = new FakeClassList();
    this.children = [];
    this.attributes = {};
    this.style = {};
    this.clientWidth = options.clientWidth || 800;
    this.clientHeight = options.clientHeight || 600;
    this.queryAll = options.queryAll || (() => []);
    this.queryOne = options.queryOne || (() => null);
    this._innerHTML = "";
    this._textContent = "";
  }

  addEventListener(type, callback) {
    (this.listeners[type] ||= []).push(callback);
  }

  trigger(type, event = {}) {
    for (const callback of this.listeners[type] || []) callback({ target: this, ...event });
  }

  click() {
    this.trigger("click");
  }

  appendChild(child) {
    this.children.push(child);
    this.scrollHeight = this.children.length;
    return child;
  }

  replaceChildren(...children) {
    this.children = children;
    this._innerHTML = "";
  }

  querySelectorAll(selector) {
    return this.queryAll(selector);
  }

  querySelector(selector) {
    return this.queryOne(selector);
  }

  closest(selector) {
    return selector === ".card" ? this.card : null;
  }

  remove() {
    this.removed = true;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  getAttribute(name) {
    return this.attributes[name] || null;
  }

  hasAttribute(name) {
    return Object.hasOwn(this.attributes, name);
  }

  removeAttribute(name) {
    delete this.attributes[name];
  }

  focus() {}

  getBoundingClientRect() {
    return { left: 0, top: 0, width: this.clientWidth, height: this.clientHeight };
  }

  setPointerCapture() {}

  set innerHTML(value) {
    this._innerHTML = String(value);
    this.children = [];
  }

  get innerHTML() {
    return this._innerHTML || this._textContent;
  }

  set textContent(value) {
    this._textContent = String(value);
  }

  get textContent() {
    return this._textContent;
  }
}

class FakeStorage {
  constructor(values = {}) {
    this.values = new Map(Object.entries(values));
  }

  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }

  setItem(key, value) {
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

function runWorkbench({
  elements, storage = new FakeStorage(), local = new FakeStorage(), fetch,
  reducedMotion = false, physics = GraphPhysics, setTimeoutFn = () => 0,
}) {
  const document = {
    hidden: false,
    listeners: {},
    addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); },
    trigger(type) { for (const callback of this.listeners[type] || []) callback(); },
    getElementById(id) {
      return elements[id] || null;
    },
    createElement(tag) {
      return new FakeElement(tag);
    },
    createElementNS(namespace, tag) {
      const element = new FakeElement(tag);
      Object.defineProperty(element, "className", {
        get() { return { baseVal: element.getAttribute("class") || "" }; },
      });
      return element;
    },
    querySelectorAll() {
      return [];
    },
  };
  let rafCalls = 0;
  const window = {
    innerWidth: 1280,
    location: "",
    addEventListener() {},
    matchMedia() { return { matches: reducedMotion }; },
  };
  vm.runInNewContext(SOURCE, {
    document,
    window,
    GraphPhysics: physics,
    sessionStorage: storage,
    localStorage: local,
    fetch,
    console,
    setInterval,
    clearInterval,
    setTimeout: setTimeoutFn,
    clearTimeout,
    requestAnimationFrame(callback) {
      rafCalls += 1;
      return setImmediate(() => callback(0));
    },
    cancelAnimationFrame(handle) { clearImmediate(handle); },
  }, { filename: "workbench.js" });
  return { elements, storage, window, document, get rafCalls() { return rafCalls; } };
}

async function flush() {
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
}

function jsonResponse(value) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(value) });
}

function layout(workspace = "alpha") {
  return new FakeElement("layout", { dataset: { workspace } });
}

function practiceElements() {
  const elements = {
    stream: new FakeElement("stream"),
    composer: new FakeElement("composer"),
    "answer-box": new FakeElement("answer-box"),
    "answer-submit": new FakeElement("answer-submit"),
    "show-answer": new FakeElement("show-answer"),
    "no-time": new FakeElement("no-time"),
    "start-practice": new FakeElement("start-practice"),
    "goto-session-end": new FakeElement("goto-session-end"),
    "composer-actions": new FakeElement("composer-actions"),
    "feedback-area": new FakeElement("feedback-area"),
    "feedback-note": new FakeElement("feedback-note"),
    "rating-input": new FakeElement("rating-input"),
    "save-rating": new FakeElement("save-rating"),
    "practice-mode-immediate": new FakeElement("practice-mode-immediate"),
    "practice-mode-batch": new FakeElement("practice-mode-batch"),
    "start-area": new FakeElement("start-area"),
    "session-end-entry": new FakeElement("session-end-entry"),
    "practice-error": new FakeElement("practice-error"),
    "retry-practice": new FakeElement("retry-practice"),
  };
  elements["retry-practice"].classList.add("hidden");
  return elements;
}

function aiElements() {
  return {
    "ai-session-list-view": new FakeElement("ai-session-list-view"),
    "ai-session-list": new FakeElement("ai-session-list"),
    "ai-session-empty": new FakeElement("ai-session-empty"),
    "ai-new-session": new FakeElement("ai-new-session"),
    "ai-provider-picker": new FakeElement("ai-provider-picker"),
    "ai-provider-options": new FakeElement("ai-provider-options"),
    "ai-chat-view": new FakeElement("ai-chat-view"),
    "ai-session-back": new FakeElement("ai-session-back"),
    "ai-messages": new FakeElement("ai-messages"),
    "ai-input": new FakeElement("ai-input"),
    "ai-send": new FakeElement("ai-send"),
    "ai-stop": new FakeElement("ai-stop"),
    "ai-status": new FakeElement("ai-status"),
  };
}

async function openFirstAiSession(elements) {
  await flush();
  elements["ai-session-list"].children[0].children[0].click();
  await flush();
}

test("workspace selector navigates to the selected workspace practice page", () => {
  const selector = new FakeElement("workspace-select", { value: "beta" });
  const app = runWorkbench({
    elements: { layout: layout(), "workspace-select": selector },
    fetch: () => jsonResponse([]),
  });
  selector.trigger("change");
  assert.equal(app.window.location, "/w/beta/practice");
});

test("practice requires an explicit mode and excludes questions already seen", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  const app = runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [{ problem_id: "p-1", problem_text: "题目一" }] });
    },
  });
  assert.equal(elements["start-practice"].disabled, true);
  assert.equal(calls.length, 0);
  elements["practice-mode-batch"].checked = true;
  elements["practice-mode-batch"].trigger("change");
  assert.equal(elements["start-practice"].disabled, false);
  elements["start-practice"].click();
  await flush();
  assert.equal(calls[0].url, "/api/w/alpha/weak?limit=200");
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.deepEqual(JSON.parse(pull.options.body), {
    kp_ids: ["kp-1"], n: 1, mode: "weak", exclude_ids: [],
  });
  assert.equal(app.window.location, "");
});

test("skipping a question advances without a practice or feedback write", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      const body = JSON.parse(options && options.body || "{}");
      return jsonResponse({ problems: [{
        problem_id: (body.exclude_ids || []).length ? "p-2" : "p-1", problem_text: "题目",
      }] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["no-time"].click();
  await flush();
  assert.equal(calls.some((call) => /\/(practice|feedback)$/.test(call.url)), false);
  const pulls = calls.filter((call) => call.url.endsWith("/pull"));
  assert.deepEqual(JSON.parse(pulls[1].options.body).exclude_ids, ["p-1"]);
});

test("immediate self-rating writes only when saving and then moves to the next question", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      if (url.endsWith("/pull")) return jsonResponse({ problems: [{
        problem_id: "p-1", problem_text: "题目一",
      }] });
      if (url.endsWith("/problem/p-1")) return jsonResponse({ problem: { solution: "解析" } });
      return jsonResponse({});
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["answer-box"].value = "作答";
  elements["answer-submit"].click();
  elements["show-answer"].click();
  await flush();
  assert.equal(calls.some((call) => call.url.endsWith("/feedback")), false);
  elements["rating-input"].value = "4";
  elements["feedback-note"].value = "复习后会做";
  elements["save-rating"].click();
  await flush();
  const feedback = calls.find((call) => call.url.endsWith("/feedback"));
  assert.ok(feedback);
  assert.deepEqual(JSON.parse(feedback.options.body), {
    item_type: "problem", item_id: "p-1", rating: 4, note: "复习后会做",
  });
});

test("practice similar returns to the mode chooser without auto-pulling", async () => {
  const storage = new FakeStorage({ wb_session_alpha: JSON.stringify([{ problem_id: "p-0" }]) });
  const similar = new FakeElement("practice-similar");
  const pending = new FakeElement("pending-ratings");
  const sessionEnd = runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending, "practice-similar": similar },
    storage,
    fetch: (url) => jsonResponse(url.includes("/weak?") ? [{ kp_id: "kp-1" }] : {}),
  });
  similar.click();
  await flush();
  assert.equal(storage.getItem("wb_session_alpha"), null);
  assert.equal(storage.getItem("wb_practice_mode_alpha"), null);
  assert.equal(sessionEnd.window.location, "practice");

  const elements = { layout: layout(), ...practiceElements() };
  const calls = [];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => { calls.push({ url, options }); return jsonResponse({ problems: [] }); },
  });
  await flush();
  assert.equal(calls.length, 0);
  assert.equal(elements["start-practice"].disabled, true);
});

test("an exhausted immediate round returns to a fresh mode choice", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => jsonResponse(url.includes("/weak?") ? [{ kp_id: "kp-1" }] : { problems: [] }),
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.equal(elements["practice-mode-immediate"].checked, false);
  assert.equal(elements["start-practice"].disabled, true);
});

test("ending a batch round early opens final review without a learning write", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  const app = runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [{ problem_id: "p-1", problem_text: "题目" }] });
    },
  });
  elements["practice-mode-batch"].checked = true;
  elements["practice-mode-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["goto-session-end"].click();
  assert.equal(app.window.location, "session-end");
  assert.equal(calls.some((call) => /\/(practice|feedback)$/.test(call.url)), false);
});

test("batch self-rating writes only from its final review card", async () => {
  const pending = new FakeElement("pending-ratings");
  const calls = [];
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([
      { problem_id: "p-1", answer_text: "我的作答", state: "unrated" },
    ]),
  });
  runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending }, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/problem/p-1")) {
        return jsonResponse({ problem: { problem_id: "p-1", problem_text: "题目", solution: "解析" } });
      }
      return jsonResponse({});
    },
  });
  await flush();
  assert.equal(calls.some((call) => call.url.endsWith("/feedback")), false);
  assert.equal(pending.children.length, 1);
  const card = pending.children[0];
  const rating = card.children.find((child) => child.id === "end-rating-p-1");
  const note = card.children.find((child) => child.id === "end-note-p-1");
  const save = card.children.find((child) => child.id === "end-save-p-1");
  rating.value = "5";
  note.value = "已掌握";
  save.click();
  await flush();
  const feedback = calls.find((call) => call.url.endsWith("/feedback"));
  assert.deepEqual(JSON.parse(feedback.options.body), {
    item_type: "problem", item_id: "p-1", rating: 5, note: "已掌握",
  });
});

test("native graph dashboard limits student detail to title, reminder, and formal link", async () => {
  const canvas = new FakeElement("graph-canvas");
  const detail = new FakeElement("graph-detail-panel");
  const calls = [];
  const app = runWorkbench({
    elements: {
      layout: layout(),
      "graph-canvas": canvas,
      "graph-search": new FakeElement("graph-search"),
      "graph-state-filter": new FakeElement("graph-state-filter"),
      "graph-zoom-in": new FakeElement("graph-zoom-in"),
      "graph-zoom-out": new FakeElement("graph-zoom-out"),
      "graph-fit": new FakeElement("graph-fit"),
      "graph-detail-tab": new FakeElement("graph-detail-tab"),
      "ai-teacher-tab": new FakeElement("ai-teacher-tab"),
      "graph-detail-panel": detail,
      "ai-teacher-panel": new FakeElement("ai-teacher-panel"),
    },
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/graph/model")) {
        return jsonResponse({ nodes: [{
          id: "kp-1", title: "加法规则", body: "正文", fragile: "易混", state: "review",
          problem_count: 4,
        }], edges: [] });
      }
      return jsonResponse({});
    },
  });
  await flush();

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/w/alpha/graph/model");
  assert.equal(canvas.children.length, 1);
  const node = canvas.children[0].children.find((child) => child.dataset.kpId === "kp-1");
  const label = canvas.children[0].children.find(
    (child) => child.className === "graph-node-label",
  );
  assert.equal(label.textContent, "加法规则");
  assert.equal(node.style.width, "25.6px");
  node.click();
  assert.match(detail.innerHTML, /加法规则/);
  assert.match(detail.innerHTML, /可以复习/);
  assert.equal(calls.some((call) => call.url.endsWith("/graph/state")), false);

  assert.equal(detail.children.some((child) => child.id === "graph-state"), false);
  assert.equal(detail.children.some((child) => child.id === "graph-state-save"), false);
  assert.equal(calls.some((call) => call.url.endsWith("/kp/kp-1")), false);
  assert.equal(app.window.location, "");
});

test("unified rating controls have unique accessible labels and titled cards", async () => {
  const pending = new FakeElement("pending-ratings");
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([
      { problem_id: "p-1", answer_text: "one", state: "unrated" },
      { problem_id: "p-2", answer_text: "two", state: "unrated" },
    ]),
  });
  runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending }, storage,
    fetch: (url) => jsonResponse({ problem: {
      problem_id: url.endsWith("p-1") ? "p-1" : "p-2",
      display_title: url.endsWith("p-1") ? "First title" : "Second title",
      problem_text: "Text", solution: "Solution",
    } }),
  });
  await flush();
  const cards = pending.children;
  const ratings = cards.map((card) => card.children.find((child) => /^end-rating-p-/.test(child.id)));
  const labels = cards.map((card) => card.children.find((child) => /^end-rating-label-/.test(child.id)));
  assert.deepEqual(ratings.map((item) => item.id), ["end-rating-p-1", "end-rating-p-2"]);
  assert.deepEqual(labels.map((item) => item.getAttribute("for")), ["end-rating-p-1", "end-rating-p-2"]);
  assert.match(cards[0].innerHTML, /First title/);
  assert.match(cards[1].innerHTML, /Second title/);
});

test("unified rating rejects an invalid value visibly without a feedback write", async () => {
  const pending = new FakeElement("pending-ratings");
  const calls = [];
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([{ problem_id: "p-1", state: "unrated" }]),
  });
  runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending }, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({ problem: { problem_id: "p-1", display_title: "Title", problem_text: "Text", solution: "Solution" } });
    },
  });
  await flush();
  const card = pending.children[0];
  card.children.find((child) => child.id === "end-rating-p-1").value = "0";
  card.children.find((child) => child.id === "end-save-p-1").click();
  assert.match(card.children.find((child) => child.id === "end-error-p-1").textContent, /1-5/);
  assert.equal(calls.some((call) => call.url.endsWith("/feedback")), false);
});

test("mobile drawer buttons keep the study page mounted while toggling each side", () => {
  const page = layout();
  const elements = {
    layout: page,
    "mobile-nav-toggle": new FakeElement("mobile-nav-toggle"),
    "mobile-ai-toggle": new FakeElement("mobile-ai-toggle"),
    "left-column": new FakeElement("left-column"),
    "ai-column": new FakeElement("ai-column"),
  };
  runWorkbench({ elements, fetch: () => jsonResponse([]) });
  elements["mobile-nav-toggle"].click();
  assert.equal(page.classList.contains("left-drawer-open"), true);
  assert.equal(page.classList.contains("ai-drawer-open"), false);
  assert.equal(elements["mobile-nav-toggle"].getAttribute("aria-expanded"), "true");
  elements["mobile-ai-toggle"].click();
  assert.equal(page.classList.contains("left-drawer-open"), false);
  assert.equal(page.classList.contains("ai-drawer-open"), true);
  assert.equal(elements["mobile-nav-toggle"].getAttribute("aria-expanded"), "false");
  assert.equal(elements["mobile-ai-toggle"].getAttribute("aria-expanded"), "true");
});

test("practice restores the same tab's titled active card without pulling again", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  const storage = new FakeStorage({
    wb_practice_mode_alpha: "immediate",
    wb_kps_alpha: JSON.stringify(["kp-1"]),
    wb_session_alpha: JSON.stringify([{ problem_id: "p-1", state: "active" }]),
    wb_current_alpha: JSON.stringify({
      problem_id: "p-1", display_title: "Restored title", problem_text: "Restored text",
    }),
  });
  const calls = [];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => { calls.push({ url, options }); return jsonResponse({ problems: [] }); },
  });
  await flush();
  assert.equal(elements["practice-mode-immediate"].checked, true);
  assert.equal(elements["start-area"].classList.contains("hidden"), true);
  assert.match(elements.stream.innerHTML, /Restored title/);
  assert.equal(calls.some((call) => call.url.endsWith("/pull")), false);
});

test("practice starts a knowledge-point handoff without loading the weak list", async () => {
  const page = layout();
  page.dataset.practiceKpId = "kp-1";
  const elements = { layout: page, ...practiceElements() };
  const calls = [];
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({ problems: [{ problem_id: "p-1", display_title: "Scoped", problem_text: "Text" }] });
    },
  });
  elements["practice-mode-batch"].checked = true;
  elements["practice-mode-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.equal(calls.some((call) => call.url.includes("/weak?")), false);
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.deepEqual(JSON.parse(pull.options.body).kp_ids, ["kp-1"]);
});

test("practice restores an active card when the knowledge-point scope is unchanged", async () => {
  const page = layout();
  page.dataset.practiceKpId = "kp-scoped";
  const elements = { layout: page, ...practiceElements() };
  const storage = new FakeStorage({
    wb_practice_mode_alpha: "immediate",
    wb_kps_alpha: JSON.stringify(["kp-scoped"]),
    wb_session_alpha: JSON.stringify([{ problem_id: "p-scoped", state: "active" }]),
    wb_current_alpha: JSON.stringify({
      problem_id: "p-scoped", display_title: "Scoped restored", problem_text: "Restored text",
    }),
  });
  const calls = [];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => { calls.push({ url, options }); return jsonResponse({ problems: [] }); },
  });
  await flush();
  assert.equal(elements["practice-mode-immediate"].checked, true);
  assert.match(elements.stream.innerHTML, /Scoped restored/);
  assert.deepEqual(JSON.parse(storage.getItem("wb_kps_alpha")), ["kp-scoped"]);
  assert.equal(calls.some((call) => call.url.endsWith("/pull")), false);
});

test("knowledge-point handoff discards an unrelated restored active card", async () => {
  const page = layout();
  page.dataset.practiceKpId = "kp-scoped";
  const elements = { layout: page, ...practiceElements() };
  const storage = new FakeStorage({
    wb_practice_mode_alpha: "immediate",
    wb_kps_alpha: JSON.stringify(["kp-other"]),
    wb_session_alpha: JSON.stringify([{ problem_id: "p-other", state: "active" }]),
    wb_current_alpha: JSON.stringify({ problem_id: "p-other", display_title: "Unrelated", problem_text: "Old" }),
  });
  const calls = [];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({ problems: [{ problem_id: "p-scoped", display_title: "Scoped", problem_text: "New" }] });
    },
  });
  assert.doesNotMatch(elements.stream.innerHTML, /Unrelated/);
  assert.equal(storage.getItem("wb_current_alpha"), null);
  elements["practice-mode-batch"].checked = true;
  elements["practice-mode-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.deepEqual(JSON.parse(pull.options.body).kp_ids, ["kp-scoped"]);
});

test("a restored unified-rating queue opens final review without clearing its records", () => {
  const elements = { layout: layout(), ...practiceElements() };
  const storage = new FakeStorage({
    wb_practice_mode_alpha: "batch",
    wb_session_alpha: JSON.stringify([{ problem_id: "p-1", state: "unrated" }]),
  });
  const app = runWorkbench({ elements, storage, fetch: () => jsonResponse({}) });
  assert.equal(app.window.location, "session-end");
  assert.equal(storage.getItem("wb_session_alpha"), JSON.stringify([{ problem_id: "p-1", state: "unrated" }]));
});

test("practice shows titled cards and validates an invalid rating in place", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  const calls = [];
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      if (url.endsWith("/pull")) return jsonResponse({ problems: [{
        problem_id: "p-1", display_title: "Readable problem", problem_text: "Text",
      }] });
      if (url.endsWith("/problem/p-1")) return jsonResponse({ problem: { solution: "Solution" } });
      return jsonResponse({});
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.match(elements.stream.innerHTML, /Readable problem/);
  elements["answer-submit"].click();
  elements["show-answer"].click();
  await flush();
  elements["rating-input"].value = "9";
  elements["save-rating"].click();
  assert.equal(calls.some((call) => call.url.endsWith("/feedback")), false);
  assert.match(elements["practice-error"].textContent, /1-5/);
});

test("practice pull failures stay visible beside the active study flow", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => url.includes("/weak?")
      ? jsonResponse([{ kp_id: "kp-1" }])
      : Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({}) }),
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.match(elements["practice-error"].textContent, /503/);
  assert.equal(elements["retry-practice"].classList.contains("hidden"), false);
  elements["retry-practice"].click();
  await flush();
  assert.equal(elements["retry-practice"].classList.contains("hidden"), false);
});

test("reduced-motion graph settles without scheduling animation frames", async () => {
  const canvas = new FakeElement("graph-canvas");
  const app = runWorkbench({
    elements: { layout: layout(), "graph-canvas": canvas },
    reducedMotion: true,
    fetch: () => jsonResponse({
      nodes: [
        { id: "kp-1", title: "加法规则", problem_count: 1 },
        { id: "kp-2", title: "乘法规则", problem_count: 4 },
      ],
      edges: [{ source: "kp-1", target: "kp-2", attraction: 1.25 }],
    }),
  });
  await flush();
  assert.equal(app.rafCalls, 0);
  assert.equal(canvas.children[0].children.filter(
    (child) => typeof child.className === "string"
      && child.className.startsWith("graph-node "),
  ).length, 2);
});

test("graph filtering rebuilds layout and dragging reheats the simulation", async () => {
  let creates = 0;
  let reheats = 0;
  const physics = Object.assign({}, GraphPhysics, {
    layoutGraph(...args) {
      creates += 1;
      return GraphPhysics.layoutGraph(...args);
    },
    reheat(simulation) {
      reheats += 1;
      return GraphPhysics.reheat(simulation);
    },
  });
  const canvas = new FakeElement("graph-canvas");
  const search = new FakeElement("graph-search");
  const zoomIn = new FakeElement("graph-zoom-in");
  const fit = new FakeElement("graph-fit");
  runWorkbench({
    elements: {
      layout: layout(), "graph-canvas": canvas, "graph-search": search,
      "graph-state-filter": new FakeElement("graph-state-filter"),
      "graph-zoom-in": zoomIn, "graph-fit": fit,
    },
    physics,
    fetch: () => jsonResponse({
      nodes: [
        { id: "kp-1", title: "加法规则", problem_count: 1 },
        { id: "kp-2", title: "乘法规则", problem_count: 2 },
      ],
      edges: [{ source: "kp-1", target: "kp-2", attraction: 1 }],
    }),
  });
  await flush();
  assert.equal(creates, 1);
  search.value = "加法";
  search.trigger("input");
  assert.equal(creates, 2);
  const stage = canvas.children[0];
  const node = stage.children.find((child) => child.dataset.kpId === "kp-1");
  node.trigger("pointerdown", { clientX: 100, clientY: 100, pointerId: 1 });
  canvas.trigger("pointermove", { clientX: 140, clientY: 130 });
  canvas.trigger("pointerup", { clientX: 140, clientY: 130 });
  assert.ok(reheats >= 3);
  zoomIn.click();
  assert.match(stage.style.transform, /scale\(1\.1\)/);
  canvas.trigger("wheel", { deltaY: 1, preventDefault() {} });
  fit.click();
});

test("graph progressively reveals ranked labels and soft-anchors a released drag", async () => {
  let anchors = 0;
  const physics = Object.assign({}, GraphPhysics, {
    setSoftAnchor(...args) { anchors += 1; return GraphPhysics.setSoftAnchor(...args); },
  });
  const canvas = new FakeElement("graph-canvas", { clientWidth: 1200, clientHeight: 800 });
  const zoomIn = new FakeElement("graph-zoom-in");
  runWorkbench({
    elements: { layout: layout(), "graph-canvas": canvas, "graph-zoom-in": zoomIn },
    reducedMotion: true,
    physics,
    fetch: () => jsonResponse({
      nodes: Array.from({ length: 14 }, (_, index) => ({
        id: "kp-" + index, title: "知识点 " + index, problem_count: 14 - index,
        importance: index < 8 ? "core" : "supplementary",
      })),
      edges: Array.from({ length: 13 }, (_, index) => ({
        source: "kp-" + index, target: "kp-" + (index + 1), attraction: 1,
      })),
    }),
  });
  await flush();
  const stage = canvas.children[0];
  const labels = stage.children.filter((child) => child.className === "graph-node-label");
  assert.equal(labels.filter((label) => label.style.display !== "none").length, 6);
  for (let i = 0; i < 8; i += 1) zoomIn.click();
  assert.equal(labels.filter((label) => label.style.display !== "none").length, 14);
  const node = stage.children.find((child) => child.dataset.kpId === "kp-0");
  node.trigger("pointerdown", { clientX: 100, clientY: 100, pointerId: 1 });
  canvas.trigger("pointermove", { clientX: 1190, clientY: 790 });
  canvas.trigger("pointerup", { clientX: 1190, clientY: 790 });
  assert.equal(anchors, 1);
});

test("graph renders curved paths and focuses one-hop and two-hop neighborhoods", async () => {
  const canvas = new FakeElement("graph-canvas");
  runWorkbench({
    elements: { layout: layout(), "graph-canvas": canvas },
    reducedMotion: true,
    fetch: () => jsonResponse({
      nodes: [1, 2, 3, 4, 5].map((id) => ({
        id: "kp-" + id, title: "知识点 " + id, problem_count: 1,
      })),
      edges: [[1, 2], [2, 3], [3, 4]].map(([source, target]) => ({
        source: "kp-" + source, target: "kp-" + target, attraction: 1,
      })),
    }),
  });
  await flush();
  const stage = canvas.children[0];
  const edgeLayer = stage.children.find(
    (child) => child.getAttribute("class") === "graph-edge-layer",
  );
  assert.equal(edgeLayer.children.length, 3);
  assert.equal(edgeLayer.children[0].getAttribute("class"), "graph-edge");
  assert.match(edgeLayer.children[0].getAttribute("d"), / [LQ] /);
  const nodes = Object.fromEntries(stage.children.filter(
    (child) => child.dataset.kpId,
  ).map((child) => [child.dataset.kpId, child]));
  nodes["kp-2"].click();
  assert.equal(nodes["kp-2"].classList.contains("graph-focus-selected"), true);
  assert.equal(nodes["kp-1"].classList.contains("graph-focus-near"), true);
  assert.equal(nodes["kp-3"].classList.contains("graph-focus-near"), true);
  assert.equal(nodes["kp-4"].classList.contains("graph-focus-mid"), true);
  assert.equal(nodes["kp-5"].classList.contains("graph-focus-far"), true);
  canvas.trigger("click");
  assert.equal(nodes["kp-5"].classList.contains("graph-focus-far"), false);
});

test("native graph dashboard removes duplicate content editors", async () => {
  const canvas = new FakeElement("graph-canvas");
  const detail = new FakeElement("graph-detail-panel");
  const calls = [];
  runWorkbench({
    elements: {
      layout: layout(), "graph-canvas": canvas,
      "graph-search": new FakeElement("graph-search"),
      "graph-state-filter": new FakeElement("graph-state-filter"),
      "graph-zoom-in": new FakeElement("graph-zoom-in"),
      "graph-zoom-out": new FakeElement("graph-zoom-out"),
      "graph-fit": new FakeElement("graph-fit"),
      "graph-detail-tab": new FakeElement("graph-detail-tab"),
      "ai-teacher-tab": new FakeElement("ai-teacher-tab"),
      "graph-detail-panel": detail,
      "ai-teacher-panel": new FakeElement("ai-teacher-panel"),
    },
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/graph/model")) return jsonResponse({
      nodes: [{ id: "kp-1", title: "容斥原理", problem_count: 3 }], edges: [],
      });
      return jsonResponse({ signals: [], schedule: null });
    },
  });
  await flush();
  const node = canvas.children[0].children.find((child) => child.dataset.kpId === "kp-1");
  node.click();
  assert.equal(calls.some((call) => call.url.endsWith("/graph/kp")), false);
  assert.equal(detail.children.some((child) => child.id === "graph-body"), false);
  assert.equal(detail.children.some((child) => child.id === "graph-fragile"), false);
  assert.ok(detail.children.some((child) => child.id === "graph-open-kp"));
});

test("native graph dashboard does not render per-problem save controls", async () => {
  const canvas = new FakeElement("graph-canvas");
  const detail = new FakeElement("graph-detail-panel");
  const calls = [];
  runWorkbench({
    elements: {
      layout: layout(), "graph-canvas": canvas,
      "graph-search": new FakeElement("graph-search"),
      "graph-state-filter": new FakeElement("graph-state-filter"),
      "graph-zoom-in": new FakeElement("graph-zoom-in"),
      "graph-zoom-out": new FakeElement("graph-zoom-out"),
      "graph-fit": new FakeElement("graph-fit"),
      "graph-detail-tab": new FakeElement("graph-detail-tab"),
      "ai-teacher-tab": new FakeElement("ai-teacher-tab"),
      "graph-detail-panel": detail,
      "ai-teacher-panel": new FakeElement("ai-teacher-panel"),
    },
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/graph/model")) return jsonResponse({
        nodes: [{ id: "kp-1", title: "容斥原理", problem_count: 1 }], edges: [],
      });
      if (url.endsWith("/kp/kp-1")) return jsonResponse({ signals: [], schedule: null });
      return jsonResponse({ state: "needs_work" });
    },
  });
  await flush();
  canvas.children[0].children.find((child) => child.dataset.kpId === "kp-1").click();
  await flush();
  assert.equal(detail.children.some((child) => child.id === "graph-problem-p-1"), false);
  assert.equal(detail.children.some((child) => child.id === "graph-problem-save"), false);
});

test("AI column discovers providers but opens a conversation only after selection", async () => {
  const elements = { layout: layout(), ...aiElements() };
  const calls = [];
  runWorkbench({
    elements,
    storage: new FakeStorage({ wb_ai_conversation_alpha: JSON.stringify("conv-001") }),
    fetch: (url) => {
      calls.push(url);
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex", model: null }]);
      if (url.endsWith("/ai/sessions")) return jsonResponse([{
        conversation_id: "conv-001", provider: "codex", status: "idle",
      }]);
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle",
        messages: [
          { role: "user", content: "什么是乘法规则？" },
          { role: "assistant", content: "分步选择时相乘。" },
        ],
      });
      return jsonResponse({});
    },
  });
  await flush();
  assert.ok(calls.some((url) => url.endsWith("/ai/providers")));
  assert.equal(calls.some((url) => url.endsWith("/ai/sessions/conv-001")), false);
  await openFirstAiSession(elements);
  assert.ok(calls.some((url) => url.endsWith("/ai/sessions/conv-001")));
  assert.equal(elements["ai-messages"].children.length, 2);
  assert.match(elements["ai-messages"].children[1].innerHTML, /分步选择时相乘/);
});

test("the visible provider picker explains when no provider is available", async () => {
  const elements = { layout: layout(), ...aiElements() };
  runWorkbench({ elements, fetch: () => jsonResponse([]) });
  await flush();
  elements["ai-new-session"].click();
  assert.equal(elements["ai-provider-picker"].classList.contains("hidden"), false);
  assert.match(elements["ai-provider-options"].innerHTML, /暂无可用 Agent/);
});

test("provider discovery failures remain visible in the list and picker", async () => {
  const elements = { layout: layout(), ...aiElements() };
  runWorkbench({
    elements,
    fetch: (url) => url.endsWith("/ai/providers")
      ? Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({}) })
      : jsonResponse([]),
  });
  await flush();
  assert.match(elements["ai-session-empty"].textContent, /Agent 服务暂不可用/);
  elements["ai-new-session"].click();
  assert.match(elements["ai-provider-options"].innerHTML, /Agent 服务暂不可用/);
});

test("AI free message sends page identifiers and excludes a draft by default", async () => {
  const pageLayout = layout();
  pageLayout.dataset.page = "kp";
  pageLayout.dataset.objectType = "kp";
  pageLayout.dataset.objectId = "kp-001";
  const elements = { layout: pageLayout, ...aiElements() };
  const calls = [];
  runWorkbench({
    elements,
    setTimeoutFn: (callback) => setImmediate(callback),
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([{
        conversation_id: "conv-001", provider: "codex", status: "idle",
      }]);
      if (url.endsWith("/ai/sessions/conv-001/turns")) return jsonResponse({ turn_id: "turn-001" });
      if (url.includes("/turns/turn-001")) return jsonResponse({
        turn: { status: "done" },
        events: [{ sequence: 1, kind: "text", text: "回答" }, { sequence: 2, kind: "done" }],
      });
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle",
        messages: [{ role: "assistant", content: "回答" }],
      });
      return jsonResponse({});
    },
  });
  await openFirstAiSession(elements);
  elements["ai-input"].value = "解释当前知识点";
  elements["ai-send"].click();
  await flush();
  await flush();
  const turn = calls.find((call) => call.url.endsWith("/ai/sessions/conv-001/turns"));
  const body = JSON.parse(turn.options.body);
  assert.equal(body.message, "解释当前知识点");
  assert.equal(body.page_type, "kp");
  assert.equal(body.kp_id, "kp-001");
  assert.equal(Object.hasOwn(body, "draft_answer"), false);
});

test("practice drafts remain private because chat exposes no attachment setting", async () => {
  const pageLayout = layout();
  pageLayout.dataset.page = "practice";
  const elements = {
    layout: pageLayout, ...practiceElements(), ...aiElements(),
  };
  const storage = new FakeStorage({
    wb_current_alpha: JSON.stringify({ problem_id: "p-1", answer_text: "" }),
  });
  elements["answer-box"].value = "我的草稿";
  elements["feedback-note"].value = "尚未提交";
  const calls = [];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([{
        conversation_id: "conv-001", provider: "codex", status: "idle",
      }]);
      if (url.endsWith("/ai/sessions/conv-001/turns")) return jsonResponse({ turn_id: "turn-001" });
      return jsonResponse({ conversation_id: "conv-001", provider: "codex", status: "idle", messages: [] });
    },
  });
  await openFirstAiSession(elements);
  elements["ai-input"].value = "看看我的思路";
  elements["ai-send"].click();
  await flush();
  const turn = calls.find((call) => call.url.endsWith("/ai/sessions/conv-001/turns"));
  const body = JSON.parse(turn.options.body);
  assert.equal(Object.hasOwn(body, "include_draft"), false);
  assert.equal(Object.hasOwn(body, "draft_answer"), false);
  assert.equal(Object.hasOwn(body, "draft_note"), false);
});

test("a running native turn exposes stop and calls only its cancel endpoint", async () => {
  const elements = { layout: layout(), ...aiElements() };
  const calls = [];
  runWorkbench({
    elements,
    storage: new FakeStorage({ wb_ai_conversation_alpha: JSON.stringify("conv-001") }),
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([{
        conversation_id: "conv-001", provider: "codex", status: "running",
      }]);
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "running",
        current_turn_id: "turn-007", messages: [],
      });
      return jsonResponse({ status: "cancelling" });
    },
  });
  await openFirstAiSession(elements);
  assert.equal(elements["ai-send"].disabled, true);
  assert.equal(elements["ai-stop"].classList.contains("hidden"), false);
  elements["ai-stop"].click();
  await flush();
  assert.ok(calls.some((call) => call.url.endsWith("/ai/sessions/conv-001/cancel")));
});

test("rich text renders markdown structure and safe links in native messages", async () => {
  const elements = { layout: layout(), ...aiElements() };
  runWorkbench({
    elements,
    fetch: (url) => {
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions")) return jsonResponse([
        { conversation_id: "conv-001", provider: "codex", status: "idle" },
      ]);
      return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle",
        messages: [{ role: "assistant", content: "# 标题\n\n- **重点**\n\nx<sup>2</sup> <b>原始 HTML</b>\n\n[危险](javascript:alert(1)) [[kp-1|知识点]]\n\n```js\n<em>原样</em>\n```" }],
      });
    },
  });
  await openFirstAiSession(elements);
  const html = elements["ai-messages"].children[0].innerHTML;
  assert.match(html, /<h1>标题<\/h1>/);
  assert.match(html, /<ul>[\s\S]*<strong>重点<\/strong>[\s\S]*<\/ul>/);
  assert.match(html, /x<sup>2<\/sup>/);
  assert.match(html, /&lt;b&gt;原始 HTML&lt;\/b&gt;/);
  assert.match(html, /href='\/w\/alpha\/kp\/kp-1'/);
  assert.match(html, /<pre><code class=['"]language-js['"]>&lt;em&gt;原样&lt;\/em&gt;<\/code><\/pre>/);
  assert.doesNotMatch(html, /href=['"]javascript:/i);
});

test("streaming assistant text is coalesced into one markdown message", async () => {
  const elements = { layout: layout(), ...aiElements() };
  runWorkbench({
    elements,
    setTimeoutFn: () => 0,
    fetch: (url, options) => {
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([
        { conversation_id: "conv-001", provider: "codex", status: "idle" },
      ]);
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle", messages: [],
      });
      if (url.endsWith("/turns") && options) return jsonResponse({ turn_id: "turn-1" });
      if (url.includes("/turns/turn-1")) return jsonResponse({
        turn: { status: "running" },
        events: [
          { sequence: 1, kind: "text", text: "## 片段" },
          { sequence: 2, kind: "text", text: "\n\n完整回答" },
        ],
      });
      return jsonResponse({});
    },
  });
  await openFirstAiSession(elements);
  elements["ai-input"].value = "请回答";
  elements["ai-send"].click();
  await flush();
  assert.equal(elements["ai-messages"].children.length, 2);
  const assistant = elements["ai-messages"].children[1];
  assert.match(assistant.innerHTML, /<h2>片段<\/h2>/);
  assert.match(assistant.innerHTML, /完整回答/);
});
