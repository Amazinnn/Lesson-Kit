"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

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
}

class FakeElement {
  constructor(id, options = {}) {
    this.id = id;
    this.dataset = options.dataset || {};
    this.value = options.value || "";
    this.disabled = false;
    this.listeners = {};
    this.classList = new FakeClassList();
    this.children = [];
    this.attributes = {};
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

  set innerHTML(value) {
    this._innerHTML = String(value);
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

function runWorkbench({ elements, storage = new FakeStorage(), fetch }) {
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
  const window = { innerWidth: 1280, location: "", addEventListener() {} };
  vm.runInNewContext(SOURCE, {
    document,
    window,
    sessionStorage: storage,
    fetch,
    console,
    setInterval,
    clearInterval,
  }, { filename: "workbench.js" });
  return { elements, storage, window };
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
    "start-area": new FakeElement("start-area"),
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

test("session-end rating keeps only unrated work and removes a rated item", async () => {
  const note = new FakeElement("end-note", { value: "reviewed" });
  const card = new FakeElement("card", {
    dataset: { pid: "p-1" },
    queryOne: (selector) => selector === ".end-note" ? note : null,
  });
  const rate = new FakeElement("rate", { dataset: { r: "4" } });
  rate.card = card;
  const pending = new FakeElement("pending-ratings", {
    queryAll: (selector) => selector === ".rate" ? [rate] : [],
    queryOne: (selector) => selector === ".card" && !card.removed ? card : null,
  });
  const calls = [];
  const app = runWorkbench({
    elements: { layout: layout(), "pending-ratings": pending },
    storage: new FakeStorage({
      wb_session_alpha: JSON.stringify([
        { problem_id: "p-1", state: "unrated" },
        { problem_id: "p-2", state: "rated" },
      ]),
    }),
    fetch: (url, options) => {
      calls.push({ url, options });
      return jsonResponse({});
    },
  });
  assert.match(pending.innerHTML, /p-1/);
  assert.doesNotMatch(pending.innerHTML, /p-2/);
  rate.trigger("click");
  await flush();
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    item_type: "problem", item_id: "p-1", rating: 4, note: "reviewed",
  });
  assert.equal(card.removed, true);
  assert.match(pending.innerHTML, /全部评完/);
  assert.equal(app.window.location, "");
});

test("practice similar starts a fresh round and gives its own empty message", async () => {
  const storage = new FakeStorage({
    wb_session_alpha: JSON.stringify([{ problem_id: "p-0", state: "unrated" }]),
  });
  const similar = new FakeElement("practice-similar");
  const pending = new FakeElement("pending-ratings");
  const sessionEnd = runWorkbench({
    elements: {
      layout: layout(), "pending-ratings": pending, "practice-similar": similar,
    },
    storage,
    fetch: (url) => jsonResponse(url.includes("/weak?") ? [{ kp_id: "kp-1" }] : {}),
  });
  similar.trigger("click");
  await flush();
  assert.equal(storage.getItem("wb_session_alpha"), null);
  assert.deepEqual(JSON.parse(storage.getItem("wb_kps_alpha")), ["kp-1"]);
  assert.equal(storage.getItem("wb_similar_round_alpha"), "1");
  assert.equal(sessionEnd.window.location, "practice");

  const elements = { layout: layout(), ...practiceElements() };
  runWorkbench({
    elements,
    storage,
    fetch: (url) => jsonResponse(url.endsWith("/pull") ? { problems: [] } : []),
  });
  await flush();
  assert.equal(storage.getItem("wb_similar_round_alpha"), null);
  assert.ok(elements.stream.children.some((message) =>
    message.innerHTML.includes("暂无更多同类题。")
  ));
});
