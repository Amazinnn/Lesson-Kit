"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "../..");
const pages = fs.readFileSync(path.join(root, "workbench/server/pages.py"), "utf8");
const css = fs.readFileSync(path.join(root, "workbench/server/static/agent-ui.css"), "utf8");
const factory = require("../../workbench/server/static/agent-ui.js");

class ClassList {
  constructor() { this.values = new Set(); }
  add(value) { this.values.add(value); }
  remove(value) { this.values.delete(value); }
  toggle(value, force) {
    if (force === undefined) force = !this.values.has(value);
    force ? this.values.add(value) : this.values.delete(value);
    return force;
  }
  contains(value) { return this.values.has(value); }
}

class Element {
  constructor(id, dataset = {}) {
    this.id = id;
    this.dataset = dataset;
    this.classList = new ClassList();
    this.children = [];
    this.listeners = {};
    this.style = {};
    this.scrollHeight = 40;
    this._text = "";
  }
  appendChild(child) { this.children.push(child); return child; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  set innerHTML(value) { this.children = []; this._text = String(value); }
  get innerHTML() { return this._text; }
  set textContent(value) { this._text = String(value); }
  get textContent() { return this._text; }
}

test("server shell loads Agent UI v1 foundation and declares transient surfaces", () => {
  for (const id of [
    "ai-context-chips", "ai-composer-shell", "ai-approval-slot",
    "agent-activity-float", "agent-bottom-dock", "agent-artifact-split",
  ]) assert.ok(pages.includes(id), `${id} missing from shell`);
  assert.ok(pages.includes("/static/agent-ui.css"));
  assert.ok(pages.includes("/static/agent-ui.js"));
  assert.ok(css.includes("var(--lk-paper)"));
  assert.ok(css.includes("var(--lk-blue)"));
  assert.equal(css.includes("#0b0f19"), false, "Agent UI must not introduce a dark island");
});

test("surface controller renders compact context chips and respects explicit collapse", () => {
  const elements = {
    layout: new Element("layout", { workspace: "alpha", page: "kp", objectId: "kp-7" }),
    "ai-column": new Element("ai-column"),
    "ai-context-chips": new Element("ai-context-chips"),
    "ai-input": new Element("ai-input"),
    middle: new Element("middle"),
    "agent-activity-float": new Element("agent-activity-float"),
    "agent-bottom-dock": new Element("agent-bottom-dock"),
    "agent-artifact-split": new Element("agent-artifact-split"),
  };
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelectorAll() { return []; },
  };
  const storage = new Map([["wb_kp_selection_alpha", JSON.stringify(["kp-1", "kp-2"])]]);
  const window = { sessionStorage: { getItem(key) { return storage.get(key) || null; } } };
  const ui = factory(document, window);
  assert.equal(elements["ai-context-chips"].children.length, 3);
  assert.equal(elements["ai-context-chips"].children[0].textContent, "知识点");
  assert.equal(elements["ai-context-chips"].children[2].textContent, "范围 2 个知识点");
  storage.set("wb_kp_selection_alpha", JSON.stringify(["kp-1"]));
  ui.renderContext();
  assert.ok(elements["ai-context-chips"].children[2].textContent.includes("1"));
  ui.collapseAux();
  assert.equal(ui.state.userCollapsed, true);
  assert.equal(elements["agent-bottom-dock"].classList.contains("hidden"), true);
});
  const panel = [...css.matchAll(/\.agent-artifact-split\s*\{[^}]*\}/g)]
    .map((match) => match[0])
    .find((block) => block.includes("position: absolute"));
  assert.ok(panel, "the split panel rule must be positioned inside the central column");
  assert.ok(panel.includes("width: var(--agent-split-width)"), "panel width must use the shared variable");
  assert.ok(panel.includes("min-width: 0"), "a minimum width can outgrow the reserved space");
  assert.match(css, /#middle\s*\{\s*--agent-split-width:\s*\d+px;\s*\}/);
  const open = css.match(/#middle\.agent-split-open\s*\{[^}]*\}/)[0];
  assert.ok(
    open.includes("padding-right: calc(var(--agent-split-width) + 22px)"),
    "the open state must reserve the panel width plus its gap",
  );
  const narrow = css.match(/@media \(max-width: 1100px\)\s*\{[\s\S]*?\n\}/)[0];
  assert.ok(narrow.includes("position: fixed"), "narrow viewports fall back to an explicit overlay");
  assert.ok(!/@media \(min-width: \d+px\) and \(max-width: \d+px\)/.test(css), "no width band may split the two branches");
