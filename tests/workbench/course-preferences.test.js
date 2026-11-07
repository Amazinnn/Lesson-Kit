"use strict";

/* Confirmed course learning preferences: initial hydration, server-wins,
   explicit save, and the saved reveal timing a new Paper consumes. */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const STATIC = path.join(__dirname, "../../workbench/server/static");
const WORKBENCH_SOURCE = fs.readFileSync(path.join(STATIC, "workbench.js"), "utf8");
const PAPER_SOURCE = fs.readFileSync(path.join(STATIC, "paper-practice.js"), "utf8");
const PRACTICE_FLOW_SOURCE = fs.readFileSync(path.join(STATIC, "practice-flow.js"), "utf8");
const PracticeDeck = require(path.join(STATIC, "practice-deck.js"));

/* ---------- the workbench shell ---------- */

class FakeElement {
  constructor(id, options = {}) {
    this.id = id;
    this.dataset = options.dataset || {};
    this.value = options.value || "";
    this.checked = options.checked || false;
    this.disabled = false;
    this.hidden = false;
    this.listeners = {};
    this.children = [];
    this.attributes = {};
    this.style = { setProperty() {}, removeProperty() {} };
    this.classList = {
      add() {}, remove() {}, toggle() {}, contains() { return false; },
    };
    this._innerHTML = "";
    this._textContent = "";
  }
  addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  trigger(type, event = {}) {
    for (const callback of this.listeners[type] || []) callback({ target: this, ...event });
  }
  click() { this.trigger("click"); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  insertBefore(child) { this.children.push(child); return child; }
  querySelectorAll() { return []; }
  querySelector() { return null; }
  closest() { return null; }
  remove() {}
  focus() {}
  scrollIntoView() {}
  setPointerCapture() {}
  getBoundingClientRect() { return { left: 0, top: 0, width: 800, height: 600 }; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] || null; }
  hasAttribute(name) { return Object.hasOwn(this.attributes, name); }
  removeAttribute(name) { delete this.attributes[name]; }
  get firstChild() { return this.children[0] || null; }
  set innerHTML(value) { this._innerHTML = String(value); this.children = []; }
  get innerHTML() { return this._innerHTML; }
  set textContent(value) { this._textContent = String(value); }
  get textContent() { return this._textContent; }
}

class FakeStorage {
  constructor(values = {}) { this.values = new Map(Object.entries(values)); }
  getItem(key) { return this.values.has(key) ? this.values.get(key) : null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
}

function jsonResponse(value) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(value) });
}

function failure(status, message) {
  return Promise.resolve({
    ok: false,
    status,
    json: () => Promise.resolve({ error: message }),
  });
}

function layout(dataset = { workspace: "alpha" }) {
  return new FakeElement("layout", { dataset });
}

function runWorkbench({ elements, local = new FakeStorage(), fetch }) {
  const document = {
    documentElement: new FakeElement("html"),
    hidden: false,
    listeners: {},
    addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); },
    trigger(type, event = {}) {
      for (const callback of this.listeners[type] || []) callback(event);
    },
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new FakeElement(tag); },
    createElementNS(_namespace, tag) {
      const element = new FakeElement(tag);
      Object.defineProperty(element, "className", {
        get() { return { baseVal: element.getAttribute("class") || "" }; },
      });
      return element;
    },
    querySelectorAll() { return []; },
    querySelector() { return null; },
  };
  const alerts = [];
  const window = {
    innerWidth: 1280,
    location: "",
    listeners: {},
    addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); },
    trigger(type, event = {}) {
      for (const callback of this.listeners[type] || []) callback(event);
    },
    scrollTo() {},
    matchMedia() { return { matches: false }; },
    localStorage: local,
    alert(message) { alerts.push(String(message)); },
  };
  const sandbox = {
    document,
    window,
    sessionStorage: new FakeStorage(),
    localStorage: local,
    fetch,
    console,
    setInterval,
    clearInterval,
    setTimeout: () => 0,
    clearTimeout,
    requestAnimationFrame(callback) { return setImmediate(() => callback(0)); },
    cancelAnimationFrame(handle) { clearImmediate(handle); },
    PracticeDeck,
  };
  const context = vm.createContext(sandbox);
  vm.runInContext(PRACTICE_FLOW_SOURCE, context, { filename: "practice-flow.js" });
  vm.runInContext(WORKBENCH_SOURCE, context, { filename: "workbench.js" });
  return { alerts, document, elements, localStorage: local, window };
}

function settingsElements() {
  const ids = [
    "setting-show-rating-view", "setting-show-source-view", "setting-submission-granularity",
    "setting-theme", "setting-motion", "setting-sound", "settings-close", "setting-view-toggle",
    "setting-show-rating", "setting-show-source",
  ];
  return Object.fromEntries(ids.map((id) => [id, new FakeElement(id)]));
}

async function flush() {
  for (let i = 0; i < 6; i += 1) await new Promise((resolve) => setImmediate(resolve));
}

const PREFERENCES = "/api/w/alpha/course-preferences";

function preferenceCalls(calls) {
  return calls.filter((call) => call.url === PREFERENCES);
}

test("no preference request is made before the surface that shows them opens", async () => {
  const calls = [];
  const app = runWorkbench({
    elements: { layout: layout() },
    fetch: (url, options) => { calls.push({ url, options }); return jsonResponse({}); },
  });
  await flush();
  assert.deepEqual(calls, [], "reading a setting never fetches");
  assert.equal(typeof app.window.lkCoursePreferences.ready, "function");
});

test("a practice page with the Paper entry hydrates the confirmed projection once", async () => {
  const calls = [];
  const elements = { layout: layout(), "paper-practice": new FakeElement("paper-practice") };
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES) return jsonResponse({ saved: false, values: {} });
      return jsonResponse({});
    },
  });
  await flush();
  assert.equal(preferenceCalls(calls).length, 1);
  assert.equal(
    preferenceCalls(calls).filter(
      (call) => call.options && call.options.method === "PATCH").length,
    0,
    "an absent projection with no explicit browser keys creates nothing",
  );
});

test("received course preferences win over a stale browser mirror", async () => {
  const calls = [];
  const local = new FakeStorage({
    wb_settings_alpha: JSON.stringify({
      showRating: false, showSource: false, theme: "night", revealTiming: "per_item",
    }),
  });
  const elements = { layout: layout({ workspace: "alpha", page: "settings" }), ...settingsElements() };
  const app = runWorkbench({
    elements,
    local,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES) {
        return jsonResponse({
          saved: true,
          values: { showRating: true, showSource: true, revealTiming: "on_submit" },
        });
      }
      return jsonResponse({});
    },
  });
  await flush();

  const mirror = JSON.parse(local.getItem("wb_settings_alpha"));
  assert.equal(mirror.showRating, true);
  assert.equal(mirror.showSource, true);
  assert.equal(mirror.revealTiming, "on_submit");
  assert.equal(mirror.theme, "night", "device appearance stays outside the course projection");
  assert.equal(elements["setting-show-rating-view"].checked, true);
  assert.equal(app.document.documentElement.getAttribute("data-show-rating"), "on");
  assert.equal(
    preferenceCalls(calls).filter((call) => call.options && call.options.method === "PATCH").length,
    0, "received values are never overwritten by the stale mirror");
  assert.deepEqual(app.window.lkCoursePreferences.values(), {
    showRating: true, showSource: true, revealTiming: "on_submit",
  });
});

test("an absent server projection adopts the explicit browser learning keys once", async () => {
  const calls = [];
  const local = new FakeStorage({
    wb_settings_alpha: JSON.stringify({
      showRating: false, submissionGranularity: "whole_problem", theme: "night",
      runningSendAction: "interrupt",
    }),
  });
  const elements = { layout: layout({ workspace: "alpha", page: "settings" }), ...settingsElements() };
  const app = runWorkbench({
    elements,
    local,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES && (!options || options.method !== "PATCH")) {
        return jsonResponse({ saved: false, values: {} });
      }
      if (url === PREFERENCES) {
        return jsonResponse({
          saved: true, values: JSON.parse(options.body),
        });
      }
      return jsonResponse({});
    },
  });
  await flush();

  const patches = preferenceCalls(calls).filter((call) => call.options.method === "PATCH");
  assert.equal(patches.length, 1, "the migration is one explicit save, not a stream of them");
  assert.deepEqual(JSON.parse(patches[0].options.body), {
    showRating: false, submissionGranularity: "whole_problem",
  });
  assert.deepEqual(app.window.lkCoursePreferences.values(), {
    showRating: false, submissionGranularity: "whole_problem",
  });

  const before = preferenceCalls(calls).length;
  await app.window.lkCoursePreferences.ready();
  assert.equal(preferenceCalls(calls).length, before, "a second read reuses the first answer");
});

test("an unreadable preference projection never authorizes overwriting it", async () => {
  const calls = [];
  const local = new FakeStorage({
    wb_settings_alpha: JSON.stringify({ showRating: false }),
  });
  const elements = { layout: layout({ workspace: "alpha", page: "settings" }), ...settingsElements() };
  const app = runWorkbench({
    elements,
    local,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES) return failure(500, "course preferences unreadable");
      return jsonResponse({});
    },
  });
  await flush();

  assert.equal(
    preferenceCalls(calls).filter((call) => call.options && call.options.method === "PATCH").length,
    0, "a failed read is not permission to replace the server copy");
  assert.equal(app.window.lkCoursePreferences.values(), null);
  assert.equal(JSON.parse(local.getItem("wb_settings_alpha")).showRating, false);
  assert.equal(elements["setting-show-rating-view"].checked, false);
});

test("a settings change is saved through the course preference writer", async () => {
  const calls = [];
  const elements = { layout: layout({ workspace: "alpha", page: "settings" }), ...settingsElements() };
  const local = new FakeStorage({
    wb_settings_alpha: JSON.stringify({ showRating: true }),
  });
  const app = runWorkbench({
    elements,
    local,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES && (!options || options.method !== "PATCH")) {
        return jsonResponse({ saved: true, values: { showRating: true } });
      }
      if (url === PREFERENCES) {
        return jsonResponse({ saved: true, values: { showRating: false } });
      }
      return jsonResponse({});
    },
  });
  await flush();

  elements["setting-show-rating-view"].checked = false;
  elements["setting-show-rating-view"].trigger("change");
  elements["setting-submission-granularity"].value = "whole_problem";
  elements["setting-submission-granularity"].trigger("change");
  await flush();

  const bodies = preferenceCalls(calls)
    .filter((call) => call.options && call.options.method === "PATCH")
    .map((call) => JSON.parse(call.options.body));
  assert.deepEqual(bodies, [
    { showRating: false }, { submissionGranularity: "whole_problem" },
  ]);
  assert.equal(JSON.parse(local.getItem("wb_settings_alpha")).showRating, false);
  assert.equal(app.alerts.length, 0);
});

test("a rejected save is reported and never counted as confirmed", async () => {
  const calls = [];
  const elements = { layout: layout({ workspace: "alpha", page: "settings" }), ...settingsElements() };
  const local = new FakeStorage({
    wb_settings_alpha: JSON.stringify({ showRating: true }),
  });
  const app = runWorkbench({
    elements,
    local,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url === PREFERENCES && (!options || options.method !== "PATCH")) {
        return jsonResponse({ saved: true, values: { showRating: true } });
      }
      if (url === PREFERENCES) return failure(400, "showRating must be a boolean");
      return jsonResponse({});
    },
  });
  await flush();

  elements["setting-show-rating-view"].checked = false;
  elements["setting-show-rating-view"].trigger("change");
  await flush();

  assert.equal(app.alerts.length, 1, "the learner sees one short failure, no panel");
  assert.match(app.alerts[0], /未保存|not saved/);
  assert.deepEqual(
    app.window.lkCoursePreferences.values(), { showRating: true },
    "the rejected value is not described as saved",
  );
  assert.equal(elements["setting-show-rating-view"].checked, false,
    "the local mirror still follows the control, as before");
});

/* ---------- the saved reveal timing a new Paper consumes ---------- */

function element(id) {
  const listeners = {};
  const classes = new Set();
  return {
    id,
    value: "",
    checked: false,
    disabled: false,
    hidden: false,
    textContent: "",
    innerHTML: "",
    dataset: {},
    children: [],
    style: {},
    handlers: listeners,
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        const enabled = force === undefined ? !classes.has(name) : !!force;
        if (enabled) classes.add(name); else classes.delete(name);
        return enabled;
      },
    },
    addEventListener(type, callback) { (listeners[type] ||= []).push(callback); },
    dispatch(type, event = {}) {
      event.target ||= this;
      return (listeners[type] || []).map((callback) => callback(event)).at(-1);
    },
    appendChild(child) { this.children.push(child); return child; },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this[name] = String(value); },
    removeAttribute(name) { delete this[name]; },
    getAttribute(name) { return this[name] || null; },
    querySelectorAll() { return []; },
    closest() { return null; },
  };
}

const PAPER_IDS = [
  "paper-practice", "paper-setup", "paper-title", "paper-count", "paper-reveal-timing",
  "paper-start", "paper-error", "paper-work", "paper-question", "paper-answer",
  "paper-options", "paper-item-submit", "paper-reference", "paper-rating", "paper-toolbar",
  "paper-prev", "paper-next", "paper-stuck", "paper-final-submit", "paper-dots",
  "paper-stem-index", "paper-pause", "paper-completion", "paper-completion-stats",
  "paper-review", "paper-return", "paper-again", "paper-links", "legacy-practice",
];

function paperRun(revealTiming = "per_item") {
  return {
    execution_id: 91,
    source_ref: "ps-017",
    source_label: "期中练习卷",
    paper_generation: 3,
    reveal_timing: revealTiming,
    rating_mode: "immediate",
    cursor: 0,
    items: [{
      position: 0,
      item_type: "problem",
      item_id: "p-1",
      content_revision: 7,
      state: "pending",
      draft_sequence: 0,
      draft: { answer: "", choices: [], stuck: false, reference_viewed: false },
      payload: {
        problem_id: "p-1",
        display_title: "题目 p-1",
        problem_text: "题面 p-1",
        micro_quiz: { quiz_type: "single_choice", options: ["A", "B"], answer_key: "A" },
        solution: "解析 p-1",
      },
    }],
  };
}

function paperFixture(options = {}) {
  const calls = [];
  const ids = Object.fromEntries(PAPER_IDS.map((id) => [id, element(id)]));
  ids["legacy-practice"].hidden = true;
  ids["paper-reveal-timing"].value = "per_item";
  const document = {
    getElementById(id) { return ids[id] || null; },
    createElement(tag) { return element(tag); },
    querySelectorAll() { return []; },
  };
  const local = options.localStorage || new Map();
  const window = {
    location: { href: options.href || "http://lesson-kit.test/w/alpha/practice" },
    history: {
      replaceState(_state, _title, target) {
        window.location.href = new URL(target, window.location.href).href;
      },
    },
    localStorage: {
      getItem(key) { return local.has(key) ? local.get(key) : null; },
      setItem(key, value) { local.set(key, String(value)); },
      removeItem(key) { local.delete(key); },
    },
    crypto: { randomUUID: (() => { let id = 0; return () => "request-" + (++id); })() },
  };
  const api = async (requestPath) => {
    calls.push({ method: "GET", path: requestPath });
    if (requestPath === "/practice/current") return { practice: options.active || null };
    if (requestPath.startsWith("/practice-sets/")) {
      return options.savedPaper || {
        practice_set_id: "ps-017", title: "期中练习卷", count: 1,
        plan: { items: [{ problem_id: "p-1" }] },
      };
    }
    return {};
  };
  const write = async (method, requestPath, body) => {
    calls.push({ method, path: requestPath, body });
    if (requestPath === "/practice-sets/ps-017/start") {
      return { practice: paperRun(body.reveal_timing === "on_submit" ? "on_submit" : "per_item") };
    }
    return {};
  };
  const deps = {
    api,
    post: (requestPath, body) => write("POST", requestPath, body),
    patch: (requestPath, body) => write("PATCH", requestPath, body),
    store() {},
    load(_key, fallback) { return fallback; },
    showRatingEnabled() { return true; },
    showSourceEnabled() { return false; },
    renderMath() {},
    escapeHtml(value) { return String(value); },
    richText(value) { return "<span>" + String(value) + "</span>"; },
    navigate() {},
  };
  if ("preferences" in options) deps.coursePreferences = () => options.preferences;
  if ("ready" in options) deps.coursePreferencesReady = () => options.ready;
  const context = {
    document, window, URL, Promise, Array, Object, JSON, Number, String, Math, Date,
    setTimeout, clearTimeout,
  };
  vm.runInNewContext(PAPER_SOURCE, context);
  context.PaperPractice.start(deps, () => ({
    currentProblem() { return null; }, session() { return []; },
    selectionContext() { return {}; }, dispose() {},
  }));
  return { calls, ids };
}

function startBody(calls) {
  const start = calls.find((call) => call.path === "/practice-sets/ps-017/start");
  return start && start.body;
}

test("the Paper setup shows the confirmed reveal preference", async () => {
  const app = paperFixture({
    href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017",
    preferences: { revealTiming: "on_submit", showRating: true },
  });
  await flush();
  assert.equal(app.ids["paper-reveal-timing"].value, "on_submit");
});

test("a new Paper starts with the confirmed reveal timing once hydration settles", async () => {
  let settle;
  const ready = new Promise((resolve) => { settle = resolve; });
  const preferences = {};
  const app = paperFixture({
    href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017",
    preferences,
    ready,
  });
  await flush();

  await app.ids["paper-start"].dispatch("click");
  await flush();
  assert.equal(startBody(app.calls), undefined, "no execution is created before the truth arrives");

  preferences.revealTiming = "on_submit";
  settle();
  await flush();
  assert.equal(startBody(app.calls).reveal_timing, "on_submit");
  assert.equal(app.ids["paper-reveal-timing"].value, "on_submit");
});

test("an explicit setup choice wins over the saved preference", async () => {
  const app = paperFixture({
    href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017",
    preferences: { revealTiming: "on_submit" },
  });
  await flush();
  app.ids["paper-reveal-timing"].value = "per_item";
  app.ids["paper-reveal-timing"].dispatch("change");
  await app.ids["paper-start"].dispatch("click");
  await flush();
  assert.equal(startBody(app.calls).reveal_timing, "per_item");
});

test("a continuing execution keeps its frozen reveal timing", async () => {
  const savedPaper = {
    practice_set_id: "ps-017", title: "期中练习卷", count: 1,
    plan: { items: [{ problem_id: "p-1" }] },
    continuation: { available: true, execution: { execution_id: 91, reveal_timing: "on_submit" } },
  };
  const app = paperFixture({
    href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017",
    savedPaper,
    preferences: { revealTiming: "per_item" },
  });
  await flush();
  assert.equal(app.ids["paper-reveal-timing"].value, "on_submit", "the active run stays frozen");
  assert.equal(app.ids["paper-reveal-timing"].disabled, true);
  await app.ids["paper-start"].dispatch("click");
  await flush();
  assert.equal(startBody(app.calls).reveal_timing, undefined, "continuing never rewrites the mode");
});

test("a Paper without a confirmed projection keeps the setup default", async () => {
  const app = paperFixture({ href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017" });
  await flush();
  assert.equal(app.ids["paper-reveal-timing"].value, "per_item");
  await app.ids["paper-start"].dispatch("click");
  await flush();
  assert.equal(startBody(app.calls).reveal_timing, "per_item");
});
