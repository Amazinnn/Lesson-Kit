"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const ROOT = path.join(__dirname, "../..");
const corePhysics = require(path.join(ROOT, "workbench/server/static/graph-physics-core.js"));
const adapterSource = fs.readFileSync(
  path.join(ROOT, "workbench/server/static/graph-physics.js"), "utf8"
);

function node(id) {
  return { id, title: id, state: "new", kind: "core", importance: .5, problems: 1 };
}

function edge(s, t) {
  return { s, t, type: "prereq", strength: 1.25 };
}

class FakeWorker {
  constructor(url, options) {
    this.url = url;
    this.options = options;
    this.messages = [];
    this.terminated = false;
    FakeWorker.last = this;
  }
  postMessage(message) { this.messages.push(message); }
  terminate() { this.terminated = true; }
}

function rendererStub() {
  return {
    attach(runtime) {
      runtime.rendererAttached = true;
      return {
        destroy() { runtime.rendererDestroyed = true; },
      };
    },
  };
}

function browserContext() {
  const context = {
    console,
    Worker: FakeWorker,
    GraphPhysics: corePhysics,
    GraphRenderer: rendererStub(),
    document: {
      readyState: "loading",
      write() { throw new Error("dependencies are already loaded; no parser write expected"); },
    },
  };
  context.globalThis = context;
  return context;
}

test("browser module preserves the graph runtime interface while delegating steps", () => {
  const context = browserContext();
  vm.runInNewContext(adapterSource, context, { filename: "graph-physics.js" });

  const api = context.GraphPhysics;
  assert.equal(api.baseGapForStrength(1.875), corePhysics.baseGapForStrength(1.875));
  assert.equal(api.structureStageSize([node("a")], new Map([["a", 0]]), 30).width, 1800);

  const runtime = api.create(
    [node("a"), node("b")], [edge("a", "b")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  const worker = FakeWorker.last;
  assert.equal(worker.url, "/static/graph-physics-worker.js");
  assert.equal(worker.messages[0].type, "init");
  assert.equal(runtime.nodes.length, 2);
  assert.equal(typeof runtime.tick, "function");
  assert.equal(typeof runtime.edgePath, "function");
  assert.equal(runtime.rendererAttached, true);

  runtime.graph.gravity = 70;
  runtime.nodes[0].visible = false;
  runtime.nodes[0].x = 444;
  runtime.nodes[0].y = 555;
  runtime.nodes[0].anchorX = 444;
  runtime.nodes[0].anchorY = 555;
  runtime.graph.drag = { id: "a" };
  runtime.reheat(.62, true);
  const reheat = worker.messages.at(-1);
  assert.equal(reheat.type, "reheat");
  assert.equal(reheat.controls.gravity, 70);
  assert.equal(reheat.controls.nodes[0].visible, false);

  worker.onmessage({ data: {
    type: "snapshot", revision: reheat.revision - 1, kind: "step",
    nodes: [
      { id: "a", x: 1, y: 2, vx: 0, vy: 0, guideX: 1, guideY: 2 },
      { id: "b", x: 3, y: 4, vx: 0, vy: 0, guideX: 3, guideY: 4 },
    ],
    graph: { alpha: 0, stableFrames: 15, settleWatch: 0, solveStep: 1, settled: true, layoutInflation: 1 },
  } });
  assert.equal(runtime.nodes[0].x, 444, "stale snapshots cannot overwrite a newer drag");
  assert.notEqual(runtime.graph.alpha, 0, "stale snapshots cannot stop a reheated solver");

  worker.onmessage({ data: {
    type: "snapshot", revision: 999, kind: "step",
    nodes: [
      { id: "a", x: 101, y: 202, vx: 0, vy: 0, guideX: 100, guideY: 200 },
      { id: "b", x: 303, y: 404, vx: 0, vy: 0, guideX: 300, guideY: 400 },
    ],
    graph: {
      alpha: 0, stableFrames: 15, settleWatch: 0,
      solveStep: 80, settled: true, layoutInflation: 1.1,
    },
  } });
  runtime.tick();
  assert.equal(runtime.nodes[0].x, 444, "dragged/anchored coordinates stay main-thread authoritative");
  assert.equal(runtime.nodes[1].y, 404);
  assert.equal(runtime.graph.alpha, 0);
  assert.equal(runtime.graph.settled, true);
  runtime.dispose();
  assert.equal(runtime.rendererDestroyed, true);
  assert.equal(worker.terminated, true);
});

test("browser module fails explicitly when Worker support is unavailable", () => {
  const context = {
    console,
    GraphPhysics: corePhysics,
    GraphRenderer: rendererStub(),
    document: { readyState: "loading", write() {} },
  };
  context.globalThis = context;
  assert.throws(
    () => vm.runInNewContext(adapterSource, context, { filename: "graph-physics.js" }),
    /requires Web Worker support/
  );
});

test("worker protocol runs the single semantic core and publishes snapshots", () => {
  const source = fs.readFileSync(
    path.join(ROOT, "workbench/server/static/graph-physics-worker.js"), "utf8"
  );
  const published = [];
  const imported = [];
  const context = {
    console,
    postMessage(message) { published.push(message); },
    close() {},
  };
  context.self = context;
  context.importScripts = function (url) {
    imported.push(url);
    context.GraphPhysics = corePhysics;
  };
  vm.runInNewContext(source, context, { filename: "graph-physics-worker.js" });
  assert.deepEqual(imported, ["/static/graph-physics-core.js"]);

  context.onmessage({ data: {
    type: "init", revision: 1,
    nodes: [node("a"), node("b")], edges: [edge("a", "b")],
    options: { stageWidth: 1800, stageHeight: 1550, gravity: 30, hiddenEdgeIds: [] },
  } });
  assert.equal(published.at(-1).kind, "init");
  const initialAlpha = published.at(-1).graph.alpha;

  context.onmessage({ data: {
    type: "step", revision: 2, count: 3,
    controls: {
      view: "structure", gravity: 30, dragId: null,
      hiddenEdgeTypes: {}, hiddenEdgeIds: [],
      nodes: [
        { id: "a", visible: true, size: 40, targetSize: 40, anchorX: null, anchorY: null },
        { id: "b", visible: true, size: 40, targetSize: 40, anchorX: null, anchorY: null },
      ],
    },
  } });
  const step = published.at(-1);
  assert.equal(step.kind, "step");
  assert.ok(step.graph.alpha < initialAlpha);
  assert.ok(step.nodes.every((item) => Number.isFinite(item.x) && Number.isFinite(item.y)));
});
