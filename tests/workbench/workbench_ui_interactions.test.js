"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const GraphPhysics = require("../../workbench/server/static/graph-physics.js");
const PracticeDeck = require("../../workbench/server/static/practice-deck.js");

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
    child.parentElement = this;
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
    const found = this.queryOne(selector);
    if (found) return found;
    if (selector.startsWith(".")) {
      const wanted = selector.slice(1);
      const walk = (node) => {
        for (const child of node.children || []) {
          if (typeof child.className === "string"
            && child.className.split(/\s+/).includes(wanted)) return child;
          const deep = walk(child);
          if (deep) return deep;
        }
        return null;
      };
      return walk(this);
    }
    return null;
  }

  closest(selector) {
    if (selector === ".card") return this.card;
    const wanted = selector.slice(1);
    let node = this;
    while (node) {
      if (typeof node.className === "string"
        && node.className.split(/\s+/).includes(wanted)) return node;
      node = node.parentElement;
    }
    return null;
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

  scrollIntoView() {}

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
    trigger(type, event = {}) {
      for (const callback of this.listeners[type] || []) callback(event);
    },
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
    querySelector() {
      return null;
    },
  };
  let rafCalls = 0;
  const window = {
    innerWidth: 1280,
    location: "",
    addEventListener() {},
    scrollTo() {},
    matchMedia() { return { matches: reducedMotion }; },
  };
  vm.runInNewContext(SOURCE, {
    document,
    window,
    GraphPhysics: physics,
    PracticeDeck,
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
    "practice-rating-immediate": new FakeElement("practice-rating-immediate"),
    "practice-rating-batch": new FakeElement("practice-rating-batch"),
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

test("corrupt session state is discarded instead of breaking page startup", () => {
  const storage = new FakeStorage({ wb_session_alpha: "{broken" });
  runWorkbench({
    elements: { layout: layout() },
    storage,
    fetch: () => jsonResponse([]),
  });
  assert.equal(storage.getItem("wb_session_alpha"), null);
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
    kp_ids: ["kp-1"], n: 1, mode: "exam", exclude_ids: [],
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
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([{ problem_id: "p-0" }]),
    wb_kps_alpha: JSON.stringify(["kp-1", "kp-2"]),
    wb_kp_selection_alpha: JSON.stringify(["kp-1", "kp-2"]),
  });
  const similar = new FakeElement("practice-similar");
  const pending = new FakeElement("pending-ratings");
  const sessionEndCalls = [];
  const sessionEnd = runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending, "practice-similar": similar },
    storage,
    fetch: (url) => { sessionEndCalls.push(url); return jsonResponse({}); },
  });
  similar.click();
  await flush();
  assert.equal(storage.getItem("wb_session_alpha"), null);
  assert.equal(storage.getItem("wb_practice_mode_alpha"), null);
  assert.deepEqual(JSON.parse(storage.getItem("wb_kp_selection_alpha")), ["kp-1", "kp-2"]);
  assert.equal(sessionEndCalls.some((url) => url.includes("/weak?")), false);
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

test("content-mode practice uses only the explicit knowledge selection", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  delete elements["practice-mode-immediate"];
  delete elements["practice-mode-batch"];
  elements["practice-mode-exam"] = new FakeElement("practice-mode-exam");
  elements["practice-mode-micro"] = new FakeElement("practice-mode-micro");
  elements["practice-mode-flash_card"] = new FakeElement("practice-mode-flash_card");
  elements["practice-mode-yes_no"] = new FakeElement("practice-mode-yes_no");
  elements["practice-empty-state"] = new FakeElement("practice-empty-state");
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1", "kp-2"]),
  });
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({ problems: [] });
    },
  });
  elements["practice-mode-micro"].checked = true;
  elements["practice-mode-micro"].trigger("change");
  elements["practice-rating-immediate"].checked = true;
  elements["practice-rating-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.equal(calls.some((call) => call.url.includes("/weak?")), false);
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.deepEqual(JSON.parse(pull.options.body), {
    kp_ids: ["kp-1", "kp-2"], n: 1, mode: "micro", exclude_ids: [],
  });
  assert.match(elements.stream.innerHTML, /暂无可用的小测题目/);
});

test("micro choice items hide the free-text answer box", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  delete elements["practice-mode-immediate"];
  delete elements["practice-mode-batch"];
  elements["practice-mode-micro"] = new FakeElement("practice-mode-micro");
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1"]),
  });
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/pull")) {
        return jsonResponse({ problems: [{
          problem_id: "mq-1", display_title: "小测题", problem_text: "2 是偶数？",
          micro_quiz: {
            quiz_type: "single_choice", options: ["是", "否"], answer_key: "是",
            error_reason: "r", source_evidence: "s",
          },
        }] });
      }
      return jsonResponse({});
    },
  });
  elements["practice-mode-micro"].checked = true;
  elements["practice-mode-micro"].trigger("change");
  elements["practice-rating-immediate"].checked = true;
  elements["practice-rating-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.equal(JSON.parse(pull.options.body).mode, "micro");
  assert.match(elements.stream.innerHTML, /data-choice-option/);
  assert.equal(elements["answer-box"].classList.contains("hidden"), true);
});

test("flash card session pulls cards, reveals the back, and rates as card", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  delete elements["practice-mode-immediate"];
  delete elements["practice-mode-batch"];
  elements["practice-mode-flash_card"] = new FakeElement("practice-mode-flash_card");
  elements["practice-columns"] = new FakeElement("practice-columns");
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1"]),
  });
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/pull-cards")) {
        return jsonResponse({ cards: [
          { card_id: "c-1", kp_id: "kp-1", front: "正面F", back: "背面B" },
        ] });
      }
      return jsonResponse({});
    },
  });
  elements["practice-mode-flash_card"].checked = true;
  elements["practice-mode-flash_card"].trigger("change");
  elements["practice-rating-immediate"].checked = true;
  elements["practice-rating-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.equal(elements["practice-columns"].classList.contains("hidden"), true);
  const pull = calls.find((call) => call.url.endsWith("/pull-cards"));
  assert.deepEqual(JSON.parse(pull.options.body), { kp_ids: ["kp-1"], exclude_ids: [] });
  assert.match(elements.stream.innerHTML, /闪卡/);
  assert.match(elements.stream.innerHTML, /正面F/);
  assert.equal(elements["show-answer"].textContent, "揭示背面");
  assert.match(elements.stream._innerHTML, /card-back-section' class='practice-solution hidden/);
  elements["show-answer"].click();
  assert.doesNotMatch(elements.stream._innerHTML, /card-back-section' class='practice-solution hidden/);
  assert.match(elements.stream._innerHTML, /背面B/);
  elements["rating-input"].value = "4";
  elements["save-rating"].click();
  await flush();
  const fb = calls.find((call) => call.url.endsWith("/feedback"));
  assert.deepEqual(JSON.parse(fb.options.body), {
    item_type: "card", item_id: "c-1", rating: 4, note: "",
  });
  const next = calls.filter((call) => call.url.endsWith("/pull-cards"))[1];
  assert.deepEqual(JSON.parse(next.options.body), {
    kp_ids: ["kp-1"], exclude_ids: ["c-1"],
  });
});

test("batch flash cards mark played cards unrated for session-end", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  delete elements["practice-mode-immediate"];
  delete elements["practice-mode-batch"];
  elements["practice-mode-flash_card"] = new FakeElement("practice-mode-flash_card");
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1"]),
  });
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/pull-cards")) {
        return jsonResponse({ cards: [
          { card_id: "c-1", kp_id: "kp-1", front: "F1", back: "B1" },
        ] });
      }
      return jsonResponse({});
    },
  });
  elements["practice-mode-flash_card"].checked = true;
  elements["practice-mode-flash_card"].trigger("change");
  elements["practice-rating-batch"].checked = true;
  elements["practice-rating-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["show-answer"].click();
  assert.doesNotMatch(elements.stream._innerHTML, /card-back-section' class='practice-solution hidden/);
  assert.equal(elements["feedback-area"].classList.contains("hidden"), true);
  let session = JSON.parse(storage.getItem("wb_session_alpha"));
  assert.equal(session.items[0].state, "unrated");
  elements["no-time"].click();
  await flush();
  session = JSON.parse(storage.getItem("wb_session_alpha"));
  assert.equal(session.items[0].state, "unrated");
});

test("session-end lists played cards with front and back for rating", async () => {
  const calls = [];
  const pending = new FakeElement("pending-ratings");
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([
      { problem_id: "c-1", card: true, front: "正面F", back: "背面B",
        answer_text: "", state: "unrated" },
    ]),
  });
  runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending }, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({ problem: { problem_id: "p-1" } });
    },
  });
  await flush();
  assert.match(pending.children[0].innerHTML, /闪卡/);
  assert.match(pending.children[0].innerHTML, /正面F/);
  assert.match(pending.children[0].innerHTML, /背面B/);
  const rating = pending.children[0].children.find((el) => el.id === "end-rating-c-1");
  const save = pending.children[0].children.find((el) => el.id === "end-save-c-1");
  rating.value = "3";
  save.click();
  await flush();
  const fb = calls.find((call) => call.url.endsWith("/feedback"));
  assert.deepEqual(JSON.parse(fb.options.body), {
    item_type: "card", item_id: "c-1", rating: 3, note: "",
  });
  assert.equal(calls.some((call) => call.url.includes("/problem/")), false);
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
  const exhausted = JSON.stringify({
    v: 2, cursor: 0, ended: true,
    items: [{ problem_id: "p-1", state: "unrated" }],
  });
  const storage = new FakeStorage({
    wb_practice_mode_alpha: "batch",
    wb_session_alpha: exhausted,
  });
  const app = runWorkbench({ elements, storage, fetch: () => jsonResponse({}) });
  assert.equal(app.window.location, "session-end");
  assert.equal(storage.getItem("wb_session_alpha"), exhausted);
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
      : Promise.resolve({
        ok: false, status: 503,
        json: () => Promise.resolve({ error: "review service unavailable" }),
      }),
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.match(elements["practice-error"].textContent, /review service unavailable/);
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
  assert.equal(labels.filter((label) => label.style.display !== "none").length, 14);
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

test("explicit practice intent applies an Agent selection replacement", async () => {
  const pageLayout = layout();
  pageLayout.dataset.page = "kps";
  const elements = { layout: pageLayout, ...aiElements() };
  const storage = new FakeStorage({ wb_kp_selection_alpha: JSON.stringify(["kp-1"]) });
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([
        { conversation_id: "conv-001", provider: "codex", status: "idle" },
      ]);
      if (url.endsWith("/ai/sessions/conv-001/turns")) return jsonResponse({ turn_id: "turn-001" });
      if (url.includes("/turns/turn-001")) return jsonResponse({
        turn: { status: "done", action: { type: "replace_practice_selection", kp_ids: ["kp-2"] } },
        events: [],
      });
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle", messages: [],
      });
      return jsonResponse({});
    },
  });
  await openFirstAiSession(elements);
  elements["ai-input"].value = "帮我安排练习";
  elements["ai-send"].click();
  await flush();
  await flush();
  assert.deepEqual(JSON.parse(storage.getItem("wb_kp_selection_alpha")), ["kp-2"]);
});

function checkIngestHarness(turnAction, sessionMessages) {
  const calls = [];
  const pageLayout = layout();
  pageLayout.dataset.page = "kps";
  const elements = { layout: pageLayout, ...aiElements() };
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options, method: options && options.method });
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([
        { conversation_id: "conv-001", provider: "codex", status: "idle" },
      ]);
      if (url.endsWith("/ai/sessions/conv-001") && !options) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle",
        messages: sessionMessages || [],
      });
      if (url.endsWith("/turns") && options) return jsonResponse({ turn_id: "turn-001" });
      if (url.includes("/turns/turn-001")) return jsonResponse({
        turn: { status: "done", action: turnAction },
        events: [],
      });
      return jsonResponse({});
    },
  });
  return { calls, elements };
}

test("explicit check intent is forwarded with the turn request", async () => {
  const { calls, elements } = checkIngestHarness(null);
  await openFirstAiSession(elements);
  elements["ai-input"].value = "帮我给这个知识点出几道题";
  elements["ai-send"].click();
  await flush();
  await flush();
  const turnPost = calls.find((call) => call.url.endsWith("/turns") && call.options);
  assert.equal(JSON.parse(turnPost.options.body).check_intent, true);
  assert.equal(JSON.parse(turnPost.options.body).practice_intent, false);
});

test("natural card phrasing toggles check intent without false positives", async () => {
  const positive = checkIngestHarness(null);
  await openFirstAiSession(positive.elements);
  positive.elements["ai-input"].value = "请你给 dmath-ch06-kp-028 补两张闪卡";
  positive.elements["ai-send"].click();
  await flush();
  await flush();
  const post = positive.calls.find((call) => call.url.endsWith("/turns") && call.options);
  assert.equal(JSON.parse(post.options.body).check_intent, true);

  const negative = checkIngestHarness(null);
  await openFirstAiSession(negative.elements);
  negative.elements["ai-input"].value = "这张闪卡是什么意思";
  negative.elements["ai-send"].click();
  await flush();
  await flush();
  const plainPost = negative.calls.find((call) => call.url.endsWith("/turns") && call.options);
  assert.equal(JSON.parse(plainPost.options.body).check_intent, false);
});

test("check ingest success renders a batch result card whose rollback calls the API", async () => {
  const { calls, elements } = checkIngestHarness({
    type: "check_ingest",
    result: {
      batch_id: "batch-001", kind: "flash-card-patch", applied: 6,
      counts: {}, backup_path: "pool/backups/dmath-pre-batch-001.db",
    },
  }, [
    { role: "user", content: "给 kp-001 补 6 张闪卡" },
    { role: "assistant", content: "好的", action: {
      type: "check_ingest",
      result: {
        batch_id: "batch-001", kind: "flash-card-patch", applied: true,
        counts: { flash_cards: 6 },
        backup_path: "C:/pool/backups/dmath-pre-batch-001.db",
      },
    } },
  ]);
  await openFirstAiSession(elements);
  elements["ai-input"].value = "给 kp-001 补 6 张闪卡";
  elements["ai-send"].click();
  await flush();
  await flush();
  const messages = elements["ai-messages"];
  const cards = messages.children.filter(
    (node) => node.className === "msg ai check-card");
  assert.ok(cards.length >= 1);
  const card = cards[cards.length - 1];
  const body = card.children[0];
  assert.equal(body.children[0].textContent, "Check 入库完成");
  assert.match(body.children[1].textContent, /batch-001/);
  assert.match(body.children[1].textContent, /flash-card-patch/);
  assert.match(body.children[1].textContent, /入库 6 条/);
  assert.match(body.children[1].textContent, /dmath-pre-batch-001\.db/);
  assert.doesNotMatch(body.children[1].textContent, /backups\/dmath/);
  const rollback = body.children[2];
  assert.equal(rollback.className, "check-card-rollback");
  rollback.click();
  await flush();
  const rollbackPost = calls.find((call) => call.url.endsWith("/ingest/rollback") && call.options);
  assert.ok(rollbackPost);
  assert.deepEqual(JSON.parse(rollbackPost.options.body), { batch_id: "batch-001" });
  assert.ok(rollback.removed);
  assert.match(body.children[1].textContent, /已整批回滚/);
});

test("check ingest gate failure renders explicit reasons and no rollback button", async () => {
  const { elements } = checkIngestHarness({
    type: "check_ingest",
    error: "mq-003: problem id already exists\nfc-002: missing source_evidence",
  }, [
    { role: "assistant", content: "尝试入库", action: {
      type: "check_ingest",
      error: "mq-003: problem id already exists\nfc-002: missing source_evidence",
    } },
  ]);
  await openFirstAiSession(elements);
  const messages = elements["ai-messages"];
  const card = messages.children.map((node) => node).filter(
    (node) => node.className === "msg ai check-card")[0];
  assert.ok(card);
  const body = card.children[0];
  assert.equal(body.children[0].textContent, "入库未执行");
  assert.match(body.children[1].textContent, /mq-003: problem id already exists/);
  assert.match(body.children[1].textContent, /missing source_evidence/);
  assert.equal(body.children.length, 2);
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

test("micro quiz renders yes/no options and grades the objective answer", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  const yesNoProblem = {
    problem_id: "mq-1", problem_text: "1 是质数吗？",
    micro_quiz: { quiz_type: "yes_no", answer_key: "否",
                  error_reason: "1 只有一个正因数。" },
  };
  const app = runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [yesNoProblem] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("是"));
  assert.ok(elements.stream._innerHTML.includes("否"));
  assert.equal(elements.stream._innerHTML.includes("micro-quiz-verdict"), false);
  elements.stream.queryAll = (selector) =>
    selector === "[data-choice-option]:checked" ? [{ value: "是" }] : [];
  elements["answer-submit"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("micro-quiz-verdict"));
  assert.ok(elements.stream._innerHTML.includes("回答错误"));
  assert.ok(elements.stream._innerHTML.includes("只有一个正因数"));
  assert.ok(elements.stream._innerHTML.includes("option-correct"));
  const pull = calls.find((call) => call.url.endsWith("/pull"));
  assert.equal(JSON.parse(pull.options.body).mode, "exam");
});

test("a correct micro quiz choice reports success without an extra write", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => {
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [{
        problem_id: "mq-2", problem_text: "3 是质数吗？",
        micro_quiz: { quiz_type: "yes_no", answer_key: "是",
                      error_reason: "3 恰有两个正因数。" },
      }] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements.stream.queryAll = (selector) =>
    selector === "[data-choice-option]:checked" ? [{ value: "是" }] : [];
  elements["answer-submit"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("回答正确"));
  assert.equal(elements.stream._innerHTML.includes("错误"), false);
});

test("multiple choice micro quizzes render checkboxes and grade subsets", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => {
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [{
        problem_id: "mq-3", problem_text: "哪些是质数？",
        micro_quiz: { quiz_type: "multiple_choice", options: ["2", "4", "5"],
                      answer_key: ["2", "5"], error_reason: "4 有因数 2。" },
      }] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("type='checkbox'"));
  elements.stream.queryAll = (selector) =>
    selector === "[data-choice-option]:checked"
      ? [{ value: "2" }, { value: "5" }] : [];
  elements["answer-submit"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("回答正确"));
});

test("revealing a micro quiz answer shows the key and reason instead of a solution", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => {
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      if (url.endsWith("/problem/mq-1")) return jsonResponse({
        problem: { problem_id: "mq-1", solution: null,
                   micro_quiz: { quiz_type: "yes_no", answer_key: "否",
                                 error_reason: "1 只有一个正因数。" } },
      });
      return jsonResponse({ problems: [{
        problem_id: "mq-1", problem_text: "1 是质数吗？",
        micro_quiz: { quiz_type: "yes_no", answer_key: "否",
                      error_reason: "1 只有一个正因数。" },
      }] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["answer-submit"].click();
  await flush();
  elements["show-answer"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("答案"));
  assert.ok(elements.stream._innerHTML.includes("为什么"));
  assert.ok(elements.stream._innerHTML.includes("只有一个正因数"));
  assert.equal(elements["feedback-area"].classList.contains("hidden"), false);
});

test("ordinary problems render without a verdict element or micro quiz controls", async () => {
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    fetch: (url) => {
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      return jsonResponse({ problems: [{
        problem_id: "p-1", problem_text: "普通题目", solution: "S1",
      }] });
    },
  });
  elements["practice-mode-immediate"].checked = true;
  elements["practice-mode-immediate"].trigger("change");
  elements["start-practice"].click();
  await flush();
  assert.ok(elements.stream._innerHTML.includes("普通题目"));
  assert.equal(elements.stream._innerHTML.includes("data-choice-option"), false);
  elements.stream.queryAll = (selector) =>
    selector === "[data-choice-option]:checked" ? [{ value: "x" }] : [];
  elements.stream.queryOne = (selector) =>
    selector === "#micro-quiz-verdict" ? new FakeElement("v") : null;
  elements["answer-submit"].click();
  await flush();
  assert.ok(elements["composer-actions"] !== undefined);
  assert.equal(elements["feedback-area"].classList.contains("hidden"), true);
});

function stagedElements(names = {}, rows = []) {
  const elements = { layout: layout() };
  elements["staged-list"] = new FakeElement("staged-list", {
    dataset: { kpNames: JSON.stringify(names) },
  });
  elements["staged-empty"] = new FakeElement("staged-empty");
  elements["suggestions-toggle"] = new FakeElement("suggestions-toggle");
  elements["suggestions"] = new FakeElement("suggestions");
  elements["suggestions"].classList.add("hidden");
  elements["suggestion-list"] = new FakeElement("suggestion-list");
  elements["suggestion-list"].queryAll = (selector) =>
    selector === ".suggestion-row" ? rows : [];
  elements["suggestions-empty"] = new FakeElement("suggestions-empty");
  elements["suggestions-empty"].classList.add("hidden");
  return elements;
}

test("staged list renders the selection with names and removes rows in sync", () => {
  const elements = stagedElements({ "kp-1": "数列极限", "kp-2": "导数定义" });
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1", "kp-2"]),
  });
  runWorkbench({ elements, storage, fetch: () => jsonResponse({}) });
  assert.ok(elements["staged-list"]._innerHTML.includes("数列极限"));
  assert.ok(elements["staged-list"]._innerHTML.includes("导数定义"));
  assert.equal(elements["staged-empty"].classList.contains("hidden"), true);
  const remove = new FakeElement("remove");
  remove.dataset.kpId = "kp-1";
  remove.closest = (selector) =>
    selector === ".staged-remove" ? remove : null;
  elements["staged-list"].trigger("click", { target: remove });
  assert.deepEqual(JSON.parse(storage.getItem("wb_kp_selection_alpha")), ["kp-2"]);
  assert.ok(elements["staged-list"]._innerHTML.includes("导数定义"));
  assert.equal(elements["staged-list"]._innerHTML.includes("数列极限"), false);
});

test("joining a suggestion stages it, hides its row, and lowers the count", () => {
  const row1 = new FakeElement("row-1");
  row1.dataset.kpId = "kp-1";
  const row2 = new FakeElement("row-2");
  row2.dataset.kpId = "kp-2";
  const elements = stagedElements({ "kp-1": "数列极限", "kp-2": "导数定义" }, [row1, row2]);
  const storage = new FakeStorage();
  runWorkbench({ elements, storage, fetch: () => jsonResponse({}) });
  assert.equal(elements["suggestions-toggle"]._textContent, "＋ 加今天要练的（2）");
  const join = new FakeElement("join");
  join.dataset.kpId = "kp-1";
  join.closest = (selector) =>
    selector === ".suggestion-join" ? join : null;
  elements["suggestions"].trigger("click", { target: join });
  assert.deepEqual(JSON.parse(storage.getItem("wb_kp_selection_alpha")), ["kp-1"]);
  assert.equal(row1.classList.contains("hidden"), true);
  assert.equal(row2.classList.contains("hidden"), false);
  assert.equal(elements["suggestions-toggle"]._textContent, "＋ 加今天要练的（1）");
  assert.ok(elements["staged-list"]._innerHTML.includes("数列极限"));
  assert.equal(elements["staged-empty"].classList.contains("hidden"), true);
});

test("the suggestion entry expands and collapses with honest empty state", () => {
  const elements = stagedElements();
  runWorkbench({
    elements,
    storage: new FakeStorage(),
    fetch: () => jsonResponse({}),
  });
  assert.equal(elements["suggestions-toggle"]._textContent, "＋ 加今天要练的");
  assert.equal(elements["suggestions-empty"].classList.contains("hidden"), false);
  elements["suggestions-toggle"].click();
  assert.equal(elements["suggestions"].classList.contains("hidden"), false);
  assert.equal(
    elements["suggestions-toggle"].getAttribute("aria-expanded"), "true",
  );
  elements["suggestions-toggle"].click();
  assert.equal(elements["suggestions"].classList.contains("hidden"), true);
  assert.equal(
    elements["suggestions-toggle"].getAttribute("aria-expanded"), "false",
  );
});

function timeElements() {
  const elements = {
    layout: layout(),
    "time-view": new FakeElement("time-view"),
    "calendar-grid": new FakeElement("calendar-grid"),
    "workload-bars": new FakeElement("workload-bars"),
    "workload-prefill": new FakeElement("workload-prefill"),
    "time-view-empty": new FakeElement("time-view-empty"),
    "ai-input": new FakeElement("ai-input"),
  };
  elements["time-view"].classList.add("hidden");
  elements["workload-prefill"].classList.add("hidden");
  elements["time-view-empty"].classList.add("hidden");
  return elements;
}

test("time view renders goal calendar, heavy day marking, and prefill", async () => {
  const elements = timeElements();
  const today = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const plus3 = iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3));
  const deadline = iso(today); /* stays inside the rendered month */
  const monthStart = iso(new Date(today.getFullYear(), today.getMonth(), 1));
  const monthEnd = iso(new Date(today.getFullYear(), today.getMonth() + 1, 0));
  runWorkbench({
    elements,
    storage: new FakeStorage(),
    fetch: (url) => {
      if (url.includes("/calendar")) {
        return jsonResponse({
          goals: [
            { id: "goal-001", kind: "stage", title: "覆盖率 80%", start_date: monthStart, deadline: monthEnd },
            { id: "goal-002", kind: "long_term", title: "期末复习", start_date: monthStart, deadline: monthEnd },
            { id: "goal-003", kind: "stage", title: "旧目标", deadline },
          ],
          days: Array.from({ length: 14 }, (_, offset) => ({
            date: iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() + offset)),
            count: offset === 3 ? 3 : 0,
            overdue: 0,
          })),
        });
      }
      return jsonResponse({});
    },
  });
  await flush();
  assert.equal(elements["time-view"].classList.contains("hidden"), false);
  assert.ok(elements["calendar-grid"]._innerHTML.includes("覆盖率 80%"));
  assert.ok(elements["calendar-grid"]._innerHTML.includes("calendar-cell today"));
  assert.ok(elements["calendar-grid"]._innerHTML.includes("calendar-goal long-term"));
  assert.ok(elements["calendar-grid"]._innerHTML.includes("grid-row:2"));
  assert.ok((elements["calendar-grid"]._innerHTML.match(/覆盖率 80%/g) || []).length > 1);
  assert.ok(elements["calendar-grid"]._innerHTML.includes("旧目标"));
  assert.ok(elements["workload-bars"]._innerHTML.includes("重"));
  assert.equal(elements["workload-prefill"].classList.contains("hidden"), false);
  elements["workload-prefill"].click();
  assert.ok(elements["ai-input"].value.includes("帮我重排一下"));
  assert.ok(elements["ai-input"].value.includes("3 项"));
});

test("time view shows an honest empty state without goals or workload", async () => {
  const elements = timeElements();
  const today = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  runWorkbench({
    elements,
    storage: new FakeStorage(),
    fetch: (url) => {
      if (url.includes("/calendar")) {
        return jsonResponse({
          goals: [],
          days: Array.from({ length: 14 }, (_, offset) => ({
            date: iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() + offset)),
            count: 0,
            overdue: 0,
          })),
        });
      }
      return jsonResponse({});
    },
  });
  await flush();
  assert.equal(elements["time-view"].classList.contains("hidden"), false);
  assert.equal(elements["time-view-empty"].classList.contains("hidden"), false);
  assert.equal(elements["workload-prefill"].classList.contains("hidden"), true);
});

test("batch wrong answers hold the verdict with the correct option before advancing", async () => {
  const calls = [];
  const timers = [];
  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    setTimeoutFn: (callback, delay) => { timers.push({ callback, delay }); return timers.length; },
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.includes("/weak?")) return jsonResponse([{ kp_id: "kp-1" }]);
      const body = JSON.parse((options && options.body) || "{}");
      return jsonResponse({ problems: [{
        problem_id: (body.exclude_ids || []).length ? "p-2" : "p-1",
        problem_text: "题目",
        micro_quiz: { quiz_type: "yes_no", answer_key: "否", error_reason: "1 只有 一个正因数。" },
      }] });
    },
  });
  elements["practice-mode-batch"].checked = true;
  elements["practice-mode-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements.stream.queryAll = (selector) =>
    selector === "[data-choice-option]:checked" ? [{ value: "是" }] : [];
  elements["answer-submit"].click();
  await flush();
  // The verdict is instant and the correct option is highlighted, but the
  // session holds instead of pulling the next item right away.
  assert.ok(elements.stream._innerHTML.includes("回答错误"));
  assert.ok(elements.stream._innerHTML.includes("option-correct"));
  assert.equal(calls.filter((call) => call.url.endsWith("/pull")).length, 1);
  assert.equal(calls.some((call) => call.url.endsWith("/feedback")), false);
  const holds = timers.filter((timer) => timer.delay === 2000);
  assert.equal(holds.length, 1);
  holds[0].callback();
  await flush();
  const pulls = calls.filter((call) => call.url.endsWith("/pull"));
  assert.equal(pulls.length, 2);
  assert.deepEqual(JSON.parse(pulls[1].options.body).exclude_ids, ["p-1"]);
});

test("flash cards page back and forth through history and only pull at the end", async () => {
  const calls = [];
  const elements = { layout: layout(), ...practiceElements() };
  elements["card-nav"] = new FakeElement("card-nav");
  elements["card-prev"] = new FakeElement("card-prev");
  elements["card-next"] = new FakeElement("card-next");
  delete elements["practice-mode-immediate"];
  delete elements["practice-mode-batch"];
  elements["practice-mode-flash_card"] = new FakeElement("practice-mode-flash_card");
  const storage = new FakeStorage({
    wb_kp_selection_alpha: JSON.stringify(["kp-1"]),
  });
  const cards = [
    { card_id: "c-1", kp_id: "kp-1", front: "正面一", back: "背面一" },
    { card_id: "c-2", kp_id: "kp-1", front: "正面二", back: "背面二" },
    { card_id: "c-3", kp_id: "kp-1", front: "正面三", back: "背面三" },
  ];
  runWorkbench({
    elements, storage,
    fetch: (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/pull-cards")) {
        const body = JSON.parse(options.body);
        const next = cards.find((card) => (body.exclude_ids || []).indexOf(card.card_id) < 0);
        return jsonResponse({ cards: next ? [next] : [] });
      }
      return jsonResponse({});
    },
  });
  elements["practice-mode-flash_card"].checked = true;
  elements["practice-mode-flash_card"].trigger("change");
  elements["practice-rating-batch"].checked = true;
  elements["practice-rating-batch"].trigger("change");
  elements["start-practice"].click();
  await flush();
  elements["show-answer"].click();
  elements["no-time"].click();
  await flush();
  elements["show-answer"].click();
  assert.match(elements.stream._innerHTML, /正面二/);
  const pullsBefore = calls.filter((call) => call.url.endsWith("/pull-cards")).length;
  // Back to the first card: its reveal state persists and nothing is pulled.
  elements["card-prev"].click();
  assert.match(elements.stream._innerHTML, /正面一/);
  assert.doesNotMatch(elements.stream._innerHTML, /card-back-section' class='practice-solution hidden/);
  assert.equal(calls.filter((call) => call.url.endsWith("/pull-cards")).length, pullsBefore);
  assert.equal(JSON.parse(storage.getItem("wb_session_alpha")).cursor, 0);
  assert.equal(elements["card-prev"].disabled, true);
  // Forward replays history without pulling; only past the end pulls a new card.
  elements["card-next"].click();
  assert.match(elements.stream._innerHTML, /正面二/);
  assert.equal(calls.filter((call) => call.url.endsWith("/pull-cards")).length, pullsBefore);
  elements["card-next"].click();
  await flush();
  const pulls = calls.filter((call) => call.url.endsWith("/pull-cards"));
  assert.equal(pulls.length, pullsBefore + 1);
  assert.deepEqual(JSON.parse(pulls[pulls.length - 1].options.body).exclude_ids, ["c-1", "c-2"]);
  assert.match(elements.stream._innerHTML, /正面三/);
});

test("goal cards edit and delete drive the API, and the agent prefill action fills the form", async () => {
  const calls = [];
  const card = new FakeElement("goal-card");
  card.dataset = {
    goalId: "goal-001", goalTitle: "期末掌握计数", goalKind: "stage",
    goalStartDate: "2026-09-01", goalDeadline: "2026-09-30", goalDescription: "重点鸽巢",
  };
  const editBtn = new FakeElement("goal-edit-btn");
  const deleteBtn = new FakeElement("goal-delete-btn");
  card.queryOne = (selector) => selector === "[data-goal-edit]" ? editBtn
    : selector === "[data-goal-delete]" ? deleteBtn : null;
  const goalCards = new FakeElement("goal-cards");
  goalCards.queryAll = (selector) => selector === ".goal-card" ? [card] : [];
  const elements = {
    layout: layout(), ...practiceElements(),
    "goal-cards": goalCards, "goal-form": new FakeElement("goal-form"),
    "goal-id": new FakeElement("goal-id"), "goal-title": new FakeElement("goal-title"),
    "goal-kind": new FakeElement("goal-kind"), "goal-start-date": new FakeElement("goal-start-date"),
    "goal-deadline": new FakeElement("goal-deadline"),
    "goal-description": new FakeElement("goal-description"),
    "goal-form-status": new FakeElement("goal-form-status"),
    "goal-submit": new FakeElement("goal-submit"), "goal-cancel": new FakeElement("goal-cancel"),
    "goal-editor-summary": new FakeElement("goal-editor-summary"),
    "goal-nl": new FakeElement("goal-nl"), "goal-assist-send": new FakeElement("goal-assist-send"),
    ...aiElements(),
  };
  runWorkbench({
    elements,
    fetch: (url, options) => {
      calls.push({ url, options, method: options && options.method });
      if (url.endsWith("/ai/providers")) return jsonResponse([{ name: "codex" }]);
      if (url.endsWith("/ai/sessions") && !options) return jsonResponse([
        { conversation_id: "conv-001", provider: "codex", status: "idle" },
      ]);
      if (url.endsWith("/ai/sessions/conv-001")) return jsonResponse({
        conversation_id: "conv-001", provider: "codex", status: "idle", messages: [],
      });
      if (url.endsWith("/turns") && options) return jsonResponse({ turn_id: "turn-1" });
      if (url.includes("/turns/turn-1")) return jsonResponse({
        turn: { status: "done", action: {
          type: "prefill_goal_form", title: "Agent 填的目标",
          kind: "long_term", start_date: "2026-09-15", deadline: "2026-10-01",
          description: "含 kp-006 与 kp-008",
        } },
        events: [],
      });
      return jsonResponse({});
    },
  });
  await flush();

  // 编辑：卡片字段载回表单，提交走 PATCH
  editBtn.click();
  assert.equal(elements["goal-id"].value, "goal-001");
  assert.equal(elements["goal-title"].value, "期末掌握计数");
  assert.equal(elements["goal-kind"].value, "stage");
  assert.equal(elements["goal-start-date"].value, "2026-09-01");
  assert.equal(elements["goal-submit"].textContent, "保存修改");
  elements["goal-start-date"].value = "2026-10-02";
  elements["goal-form"].trigger("submit");
  assert.match(elements["goal-form-status"].textContent, /开始日期不能晚于截止日期/);
  assert.equal(calls.some((call) => call.url.endsWith("/goals/goal-001") && call.method === "PATCH"), false);
  elements["goal-start-date"].value = "2026-09-01";
  elements["goal-form"].trigger("submit");
  await flush();
  const patch = calls.find((call) => call.url.endsWith("/goals/goal-001") && call.method === "PATCH");
  assert.ok(patch);
  assert.deepEqual(JSON.parse(patch.options.body).title, "期末掌握计数");

  // 助填动作镜像：先在右侧开会话，再从目标表单点「让 Agent 填」
  elements["ai-session-list"].children[0].children[0].click();
  await flush();
  elements["goal-nl"].value = "期末前掌握第六章计数";
  elements["goal-assist-send"].click();
  await flush();
  const turnPost = calls.find((call) => call.url.endsWith("/turns") && call.options);
  assert.deepEqual(JSON.parse(turnPost.options.body).goal_intent, true);
  assert.equal(elements["goal-title"].value, "Agent 填的目标");
  assert.equal(elements["goal-kind"].value, "long_term");
  assert.equal(elements["goal-start-date"].value, "2026-09-15");
  assert.equal(elements["goal-deadline"].value, "2026-10-01");
  assert.equal(elements["goal-description"].value, "含 kp-006 与 kp-008");
  assert.match(elements["goal-form-status"].textContent, /Agent 已代填/);

  // 删除：确认（无 confirm 环境直通）→ DELETE
  deleteBtn.click();
  await flush();
  assert.ok(calls.some((call) => call.url.endsWith("/goals/goal-001") && call.method === "DELETE"));
});
