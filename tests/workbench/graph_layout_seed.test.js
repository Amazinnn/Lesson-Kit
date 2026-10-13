"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const ROOT = path.join(__dirname, "../..");
const corePhysics = require(path.join(ROOT, "workbench/server/static/graph-physics-core.js"));
const source = fs.readFileSync(
  path.join(ROOT, "workbench/server/static/graph-physics.js"), "utf8"
);

function node(id) {
  return { id, title: id, state: "new", kind: "core", importance: .5, problems: 1 };
}

function edge(s, t) {
  return { id: s + "-" + t, s, t, type: "prereq", direction: "forward", strength: 1.25 };
}

class FakeWorker {
  constructor() {
    this.messages = [];
    FakeWorker.last = this;
  }
  postMessage(message) { this.messages.push(message); }
  terminate() {}
}

function makeContext(values, frames) {
  const context = {
    console,
    Worker: FakeWorker,
    GraphPhysics: corePhysics,
    GraphRenderer: { attach() { return { destroy() {} }; } },
    document: {
      readyState: "loading",
      write() { throw new Error("dependencies should already be loaded"); },
      getElementById(id) {
        return id === "layout" ? { dataset: { workspace: "course" } } : null;
      },
    },
    localStorage: {
      getItem(key) { return values.has(key) ? values.get(key) : null; },
      setItem(key, value) { values.set(key, value); },
    },
    requestAnimationFrame(callback) { frames.push(callback); return frames.length; },
    setTimeout(callback) { frames.push(callback); return frames.length; },
  };
  context.globalThis = context;
  vm.runInNewContext(source, context, { filename: "graph-physics.js" });
  return context;
}

test("layout cache stores readable graph identity and restores it only as a seed", () => {
  const values = new Map();
  const frames = [];
  const context = makeContext(values, frames);
  const api = context.GraphPhysics;
  const nodes = [node("a"), node("b")];
  const edges = [edge("a", "b")];

  const first = api.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550, gravity: 30 });
  const firstWorker = FakeWorker.last;
  firstWorker.onmessage({ data: {
    type: "snapshot",
    revision: 999,
    kind: "step",
    nodes: [
      { id: "a", x: 111, y: 222, vx: 0, vy: 0, guideX: 111, guideY: 222 },
      { id: "b", x: 333, y: 444, vx: 0, vy: 0, guideX: 333, guideY: 444 },
    ],
    graph: {
      alpha: 0, stableFrames: 15, settleWatch: 0,
      solveStep: 80, settled: true, layoutInflation: 1,
    },
  } });
  first.tick();

  const key = "lk_graph_layout_v1_course";
  assert.equal(values.has(key), true);
  const saved = JSON.parse(values.get(key));
  assert.deepEqual(JSON.parse(saved.identity), {
    nodes: ["a", "b"],
    edges: ["a|b|prereq|forward"],
  });
  assert.deepEqual(saved.positions.a, [111, 222]);
  assert.equal(saved.signature, undefined, "layout identity is stored directly; no hash signature is introduced");

  const second = api.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550, gravity: 30 });
  const secondWorker = FakeWorker.last;
  const restore = secondWorker.messages.find((message) => message.type === "reheat");
  assert.ok(restore, "restored coordinates are sent through the same Worker runtime");
  assert.equal(restore.controls.nodes[0].anchorX, 111);
  assert.equal(second.nodes[0].x, 111);
  assert.equal(frames.length, 1);

  frames.shift()();
  frames.shift()();
  assert.equal(second.nodes[0].anchorX, null);
  assert.equal(second.nodes[1].anchorY, null);
  assert.equal(secondWorker.messages.at(-1).type, "reheat");
  assert.equal(secondWorker.messages.at(-1).autoFit, true);
});
