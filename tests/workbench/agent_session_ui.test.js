"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/workbench.js"), "utf8",
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

function response(value) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(value) });
}

function setup(fetch) {
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
    "ai-session-title": new Element("ai-session-title"),
    "ai-session-provider": new Element("ai-session-provider"),
    "ai-session-rename": new Element("ai-session-rename"),
    "ai-session-delete": new Element("ai-session-delete"),
    "ai-messages": new Element("ai-messages"),
    "ai-input": new Element("ai-input"),
    "ai-send": new Element("ai-send"),
    "ai-stop": new Element("ai-stop"),
    "ai-status": new Element("ai-status"),
    "ai-collapse": new Element("ai-collapse"),
  };
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelectorAll() { return []; },
  };
  const window = { location: "", innerWidth: 1280, addEventListener() {}, matchMedia() { return { matches: false }; } };
  vm.runInNewContext(SOURCE, {
    document, window, fetch, sessionStorage: new Storage(), localStorage: new Storage(), console,
    setInterval, clearInterval, setTimeout, clearTimeout, requestAnimationFrame: (callback) => setImmediate(() => callback(0)),
    cancelAnimationFrame: clearImmediate,
  }, { filename: "workbench.js" });
  return { elements, window };
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

test("history entry opens a fixed-provider chat that can be renamed, deleted, or left", async () => {
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
  assert.equal(app.elements["ai-session-provider"].textContent, "codex");
  assert.equal(app.elements["ai-session-rename"].value, "旧会话");
  app.elements["ai-session-rename"].value = "我的会话";
  app.elements["ai-session-rename"].trigger("change");
  await flush();
  const rename = calls.find((item) => item.url.endsWith("/ai/sessions/conv-001") && item.options && item.options.method === "PATCH");
  assert.deepEqual(JSON.parse(rename.options.body), { title: "我的会话" });
  app.elements["ai-session-delete"].click();
  await flush();
  assert.ok(calls.some((item) => item.url.endsWith("/ai/sessions/conv-001") && item.options && item.options.method === "DELETE"));
  app.elements["ai-session-back"].click();
  assert.equal(app.elements["ai-session-list-view"].classList.contains("hidden"), false);
});
