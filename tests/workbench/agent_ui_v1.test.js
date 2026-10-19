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
    this.attributes = {};
    this.type = "";
    this.href = "";
  }
  appendChild(child) { this.children.push(child); return child; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
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
    "agent-activity-toggle": new Element("agent-activity-toggle"),
    "agent-artifact-split": new Element("agent-artifact-split"),
    "agent-artifact-title": new Element("agent-artifact-title"),
    "agent-artifact-body": new Element("agent-artifact-body"),
    "agent-artifact-actions": new Element("agent-artifact-actions"),
  };
  ["agent-activity-float", "agent-artifact-split", "ai-approval-slot"].forEach((id) => {
    elements[id].classList.add("hidden");
  });
  const document = {
    getElementById(id) { return elements[id] || null; },
    createElement(tag) { return new Element(tag); },
    querySelectorAll() { return []; },
  };
  const storage = new Map([["wb_agent_scope_alpha", JSON.stringify(["kp-1", "kp-2"])]]);
  const window = { sessionStorage: {
    getItem(key) { return storage.get(key) || null; },
    setItem(key, value) { storage.set(key, String(value)); },
  } };
  return { elements, ui: factory(document, window), storage };
}

test("server shell loads Agent UI v1 foundation and declares transient surfaces", () => {
  for (const id of [
    "ai-context-chips", "ai-composer-shell", "ai-approval-slot",
    "agent-activity-float", "agent-activity-toggle", "agent-artifact-split",
  ]) assert.ok(pages.includes(id), `${id} missing from shell`);
  assert.equal(pages.includes("agent-bottom-dock"), false, "task progress must not render a Bottom Dock");
  assert.ok(pages.includes("aria-controls='agent-activity-body'"));
  assert.ok(pages.includes("/static/agent-ui.css"));
  assert.ok(pages.includes("/static/agent-ui.js"));
  assert.ok(css.includes("var(--lk-paper)"));
  assert.ok(css.includes("var(--lk-blue)"));
  assert.equal(css.includes("#0b0f19"), false, "Agent UI must not introduce a dark island");
});

test("surface controller renders compact context chips and respects explicit collapse", () => {
  const { elements, ui, storage } = setup();
  assert.equal(elements["ai-context-chips"].children.length, 3);
  assert.equal(elements["ai-context-chips"].children[0].textContent, "知识点");
  assert.equal(elements["ai-context-chips"].children[2].textContent, "范围 2 个知识点");
  storage.set("wb_agent_scope_alpha", JSON.stringify(["kp-1"]));
  ui.renderContext();
  assert.ok(elements["ai-context-chips"].children[2].textContent.includes("1"));
  ui.collapseAux();
  assert.equal(ui.state.userCollapsed, true);
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
});

test("short and sustained Agent work use only the latest Activity Float summary", () => {
  const { elements, ui } = setup();
  ui.resetTurn();
  ui.activity({ activity_id: "a1", label: "读取题库", status: "running", activity_type: "tool" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
  ui.activity({ activity_id: "a1", label: "读取题库", status: "done", activity_type: "tool" });
  ui.activity({ activity_id: "a2", label: "生成试卷", status: "running", activity_type: "tool" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
  assert.equal(elements["agent-activity-body"].children.length, 1);
  assert.equal(elements["agent-activity-body"].children[0].children[1].children[0].textContent, "生成试卷");
  assert.equal(css.includes(".agent-bottom-dock"), false, "task progress must not add bottom-page layout");
});

test("Activity Float collapse keeps a compact control, supports reopen, resets next turn, and clears at idle", () => {
  const { elements, ui } = setup();
  ui.resetTurn();
  ui.activity({ activity_id: "a1", label: "检索", status: "running" });
  const toggle = elements["agent-activity-toggle"];
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  toggle.click();
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
  assert.equal(elements["agent-activity-float"].classList.contains("is-collapsed"), true);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(toggle.getAttribute("aria-label"), "展开 Agent 活动");
  ui.activity({ activity_id: "a2", label: "整理", status: "running" });
  assert.equal(elements["agent-activity-float"].classList.contains("is-collapsed"), true,
    "same-turn activity must not force the Float open");
  assert.equal(elements["agent-activity-toggle"].getAttribute("aria-expanded"), "false");
  toggle.click();
  assert.equal(elements["agent-activity-float"].classList.contains("is-collapsed"), false);
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.equal(elements["agent-activity-body"].children[0].children[1].children[0].textContent, "整理");

  toggle.click();
  ui.resetTurn();
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), true);
  assert.equal(elements["agent-activity-float"].classList.contains("is-collapsed"), false);
  ui.activity({ activity_id: "b1", label: "新一轮", status: "running" });
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), false);
  assert.equal(elements["agent-activity-toggle"].getAttribute("aria-expanded"), "true");
  ui.finishTurn();
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), true,
    "the Float and its toggle must disappear when no runtime activity remains");
});

test("switching conversations clears transient activity and collapse state", () => {
  const { elements, ui } = setup();
  ui.resetTurn();
  ui.activity({ activity_id: "a1", label: "read", status: "running" });
  elements["agent-activity-toggle"].click();
  ui.resetConversation();
  assert.equal(elements["agent-activity-float"].classList.contains("hidden"), true);
  assert.equal(elements["agent-activity-float"].classList.contains("is-collapsed"), false);
  assert.equal(elements["agent-activity-body"].children.length, 0);
  assert.equal(ui.state.activityOrder.length, 0);
  assert.equal(ui.state.userCollapsed, false);
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
