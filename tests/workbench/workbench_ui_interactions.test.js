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
  elements, storage = new FakeStorage(), fetch, reducedMotion = false, physics = GraphPhysics,
}) {
  const document = {
    getElementById(id) {
      return elements[id] || null;
    },
    createElement(tag) {
      return new FakeElement(tag);
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
    fetch,
    console,
    setInterval,
    clearInterval,
    requestAnimationFrame(callback) {
      rafCalls += 1;
      return setImmediate(() => callback(0));
    },
    cancelAnimationFrame(handle) { clearImmediate(handle); },
  }, { filename: "workbench.js" });
  return { elements, storage, window, get rafCalls() { return rafCalls; } };
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
  return {
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
  };
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
  const rating = card.children.find((child) => child.id === "end-rating");
  const note = card.children.find((child) => child.id === "end-note");
  const save = card.children.find((child) => child.id === "end-save");
  rating.value = "5";
  note.value = "已掌握";
  save.click();
  await flush();
  const feedback = calls.find((call) => call.url.endsWith("/feedback"));
  assert.deepEqual(JSON.parse(feedback.options.body), {
    item_type: "problem", item_id: "p-1", rating: 5, note: "已掌握",
  });
});

test("native graph reads the live model and saves a state only after confirmation", async () => {
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
      return jsonResponse({ state: "mastered" });
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
  assert.equal(calls.some((call) => call.url.endsWith("/graph/state")), false);

  const select = detail.children.find((child) => child.id === "graph-state");
  const save = detail.children.find((child) => child.id === "graph-state-save");
  select.value = "mastered";
  save.click();
  await flush();
  const stateWrite = calls.find((call) => call.url.endsWith("/graph/state"));
  assert.deepEqual(JSON.parse(stateWrite.options.body), {
    item_type: "kp", item_id: "kp-1", state: "mastered",
  });
  assert.equal(app.window.location, "");
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
    (child) => (child.className || "").startsWith("graph-node "),
  ).length, 2);
});

test("graph filtering rebuilds layout and dragging reheats the simulation", async () => {
  let creates = 0;
  let reheats = 0;
  const physics = Object.assign({}, GraphPhysics, {
    createSimulation(...args) {
      creates += 1;
      return GraphPhysics.createSimulation(...args);
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

test("native graph saves knowledge content only from its explicit save control", async () => {
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
        nodes: [{ id: "kp-1", title: "容斥原理", body: "旧正文", fragile: "旧说明" }], edges: [],
      });
      return jsonResponse({ body: "新正文", fragile: "新说明" });
    },
  });
  await flush();
  const node = canvas.children[0].children.find((child) => child.dataset.kpId === "kp-1");
  node.click();
  assert.equal(calls.some((call) => call.url.endsWith("/graph/kp")), false);
  assert.ok(detail.children.some((child) => child.id === "graph-body"));
  assert.ok(detail.children.some((child) => child.id === "graph-fragile"));
  assert.ok(detail.children.some((child) => child.id === "graph-content-save"));
  const body = detail.children.find((child) => child.id === "graph-body");
  const fragile = detail.children.find((child) => child.id === "graph-fragile");
  const save = detail.children.find((child) => child.id === "graph-content-save");
  body.value = "新正文";
  fragile.value = "新说明";
  save.click();
  await flush();
  const contentWrite = calls.find((call) => call.url.endsWith("/graph/kp"));
  assert.deepEqual(JSON.parse(contentWrite.options.body), {
    kp_id: "kp-1", body: "新正文", fragile: "新说明",
  });
});

test("native graph exposes related problem state as an explicit overwrite", async () => {
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
        nodes: [{ id: "kp-1", title: "容斥原理", body: "正文", fragile: "" }], edges: [],
      });
      if (url.endsWith("/kp/kp-1")) return jsonResponse({ problems: [{
        problem_id: "p-1", display_title: "整数条件计数", topic_label: "容斥原理", current_state: null,
      }] });
      return jsonResponse({ state: "needs_work" });
    },
  });
  await flush();
  canvas.children[0].children.find((child) => child.dataset.kpId === "kp-1").click();
  await flush();
  const problem = detail.children.find((child) => child.id === "graph-problem-p-1");
  assert.ok(problem);
  const state = problem.children.find((child) => child.id === "graph-problem-state");
  const save = problem.children.find((child) => child.id === "graph-problem-save");
  state.value = "needs_work";
  save.click();
  await flush();
  const write = calls.find((call) => call.url.endsWith("/graph/state"));
  assert.deepEqual(JSON.parse(write.options.body), {
    item_type: "problem", item_id: "p-1", state: "needs_work",
  });
});
