"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "../..");
const pages = fs.readFileSync(path.join(root, "workbench/server/pages.py"), "utf8");
const css = fs.readFileSync(path.join(root, "workbench/server/static/agent-ui.css"), "utf8");
const workbench = fs.readFileSync(path.join(root, "workbench/server/static/workbench.js"), "utf8");
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
    this.type = "";
    this.href = "";
  }
  appendChild(child) { this.children.push(child); return child; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  trigger(name, event = {}) { (this.listeners[name] || []).forEach((fn) => fn({ target: this, ...event })); }
  click() { this.trigger("click"); }
  set innerHTML(value) { this.children = []; this._text = String(value); }
  get innerHTML() { return this._text; }
  set textContent(value) { this._text = String(value); }
  get textContent() { return this._text; }
}

function setup() {
  const elements = {
    layout: new Element("layout", { workspace: "alpha", page: "kp", objectId: "kp-7" }),
    "ai-column": new Element("ai-column"),
    "ai-messages": new Element("ai-messages"),
    "ai-context-chips": new Element("ai-context-chips"),
    "ai-input": new Element("ai-input"),
    "ai-input-row": new Element("ai-input-row"),
    "ai-approval-slot": new Element("ai-approval-slot"),
    middle: new Element("middle"),
    "agent-activity-float": new Element("agent-activity-float"),
    "agent-activity-body": new Element("agent-activity-body"),
    "agent-bottom-dock": new Element("agent-bottom-dock"),
    "agent-bottom-dock-body": new Element("agent-bottom-dock-body"),
    "agent-artifact-split": new Element("agent-artifact-split"),
    "agent-artifact-title": new Element("agent-artifact-title"),
    "agent-artifact-body": new Element("agent-artifact-body"),
    "agent-artifact-actions": new Element("agent-artifact-actions"),
  };
  ["agent-activity-float", "agent-bottom-dock", "agent-artifact-split", "ai-approval-slot"].forEach((id) => {
    elements[id].classList.add("hidden");
  });
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelectorAll() { return []; },
  };
  const storage = new Map([["wb_kp_selection_alpha", JSON.stringify(["kp-1", "kp-2"])]]);
  const window = { sessionStorage: { getItem(key) { return storage.get(key) || null; } } };
  return { elements, ui: factory(document, window) };
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
  const { elements, ui } = setup();
  assert.equal(elements["ai-context-chips"].children.length, 3);
  assert.equal(elements["ai-context-chips"].children[0].textContent, "知识点");
  assert.equal(elements["ai-context-chips"].children[2].textContent, "范围 2 个知识点");
  ui.collapseAux();
  assert.equal(ui.state.userCollapsed, true);
  assert.equal(elements["agent-bottom-dock"].classList.contains("hidden"), true);
});

test("one activity uses the float and multi-step work graduates to the bottom dock", () => {
  const { elements, ui } = setup();
  ui.resetTurn();
  ui.activity({ activity_id: "a1", label: "读取题库", status: "running", activity_type: "tool" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
  assert.equal(elements["agent-bottom-dock"].classList.contains("hidden"), true);
  ui.activity({ activity_id: "a1", label: "读取题库", status: "done", activity_type: "tool" });
  ui.activity({ activity_id: "a2", label: "生成试卷", status: "running", activity_type: "tool" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), true);
  assert.equal(elements["agent-bottom-dock"].classList.contains("hidden"), false);
  assert.equal(elements["agent-bottom-dock-body"].children.length, 2);
});

test("explicit collapse prevents runtime from reopening auxiliary work until the next turn", () => {
  const { elements, ui } = setup();
  ui.resetTurn();
  ui.activity({ activity_id: "a1", label: "检索", status: "running" });
  ui.collapseAux();
  ui.activity({ activity_id: "a2", label: "整理", status: "running" });
  assert.equal(elements["agent-bottom-dock"].classList.contains("hidden"), true);
  ui.resetTurn();
  ui.activity({ activity_id: "b1", label: "新一轮", status: "running" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
});

test("Approval Gate replaces the composer and restores it after an explicit decision", () => {
  const { elements, ui } = setup();
  let approved = 0;
  let denied = 0;
  assert.equal(ui.confirm({
    title: "整批回滚",
    reason: "这会撤销当前入库批次。",
    impact: "该批内容会从池中删除。",
    approveLabel: "确认回滚",
  }, () => { approved += 1; }, () => { denied += 1; }), true);
  assert.equal(elements["ai-input-row"].classList.contains("hidden"), true);
  assert.equal(elements["ai-approval-slot"].classList.contains("hidden"), false);
  const card = elements["ai-approval-slot"].children[0];
  const actions = card.children[card.children.length - 1];
  actions.children[0].click();
  assert.equal(denied, 1);
  assert.equal(elements["ai-input-row"].classList.contains("hidden"), false);
  ui.confirm({ title: "整批回滚" }, () => { approved += 1; });
  elements["ai-approval-slot"].children[0].children.slice(-1)[0].children[1].click();
  assert.equal(approved, 1);
});

test("Paper Artifact stays in chat and opens only a native safe Adaptive Split target", () => {
  const { elements, ui } = setup();
  const first = {
    type: "paper_artifact", practice_set_id: "ps-017", title: "期中复习",
    item_count: 12, summary: "覆盖薄弱知识点。", url: "https://evil.invalid/",
  };
  assert.equal(ui.artifact(first), true);
  assert.equal(elements["ai-messages"].children.length, 1);
  assert.equal(elements["agent-artifact-split"].classList.contains("hidden"), false);
  assert.equal(elements.middle.classList.contains("agent-split-open"), true);
  assert.equal(elements["agent-artifact-actions"].children[0].href, "/w/alpha/practice-sets");
  assert.notEqual(elements["agent-artifact-actions"].children[0].href, first.url);

  ui.collapseAux();
  assert.equal(ui.artifact({
    type: "paper_artifact", practice_set_id: "ps-018", title: "第二张卷",
  }), true);
  assert.equal(elements["ai-messages"].children.length, 2);
  assert.equal(elements["agent-artifact-split"].classList.contains("hidden"), true,
    "an artifact must not force open a surface the user collapsed");

  const secondCard = elements["ai-messages"].children[1];
  const controls = secondCard.children[secondCard.children.length - 1];
  controls.children[0].click();
  assert.equal(elements["agent-artifact-split"].classList.contains("hidden"), false,
    "an explicit Preview action may reopen the split");
  assert.equal(elements["agent-artifact-actions"].children[0].href, "/w/alpha/practice-sets");
});

test("restored historical Artifact cards do not take over the current page", () => {
  const { elements, ui } = setup();
  assert.equal(ui.artifact({
    type: "paper_artifact", practice_set_id: "ps-021", title: "历史试卷",
  }, { restore: true }), true);
  assert.equal(elements["ai-messages"].children.length, 1);
  assert.equal(elements["agent-artifact-split"].classList.contains("hidden"), true);
  assert.equal(elements.middle.classList.contains("agent-split-open"), false);
});

test("Workbench runtime keeps typing available and maps runtime and Artifact state", () => {
  assert.equal(workbench.includes("aiInput.disabled = running"), false);
  assert.ok(workbench.includes("AgentUISurfaces.activity"));
  assert.ok(workbench.includes("AgentUISurfaces.confirm"));
  assert.ok(workbench.includes("AgentUISurfaces.resetTurn"));
  assert.ok(workbench.includes("AgentUISurfaces.artifact"));
  assert.ok(workbench.includes("paper_artifact"));
});
