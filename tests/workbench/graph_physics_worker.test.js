"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const ROOT = path.join(__dirname, "../..");
const corePhysics = require(path.join(ROOT, "workbench/server/static/graph-physics-core.js"));
const graphRenderer = require(path.join(ROOT, "workbench/server/static/graph-renderer.js"));
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
    this.terminateCount = 0;
    FakeWorker.last = this;
  }
  postMessage(message) { this.messages.push(message); }
  terminate() {
    this.terminated = true;
    this.terminateCount += 1;
  }
}

function rendererStub() {
  return {
    attach(runtime) {
      runtime.rendererAttached = true;
      return { destroy() { runtime.rendererDestroyed = true; } };
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
      write() { throw new Error("core is already loaded; no parser write expected"); },
    },
  };
  context.globalThis = context;
  return context;
}

function rendererEnvironment({ webgl = true, failFragment = false, failInsert = false, reducedMotion = false } = {}) {
  const frames = new Map();
  const createdShaders = [];
  const deletedShaders = [];
  const createdPrograms = [];
  const deletedPrograms = [];
  const createdBuffers = [];
  const deletedBuffers = [];
  const drawCalls = [];
  const bufferUploads = [];
  const gl = {
    VERTEX_SHADER: 1, FRAGMENT_SHADER: 2, COMPILE_STATUS: 3, LINK_STATUS: 4,
    ARRAY_BUFFER: 5, DYNAMIC_DRAW: 6, FLOAT: 7, TRIANGLES: 8,
    COLOR_BUFFER_BIT: 9, BLEND: 10, SRC_ALPHA: 11, ONE_MINUS_SRC_ALPHA: 12,
    createShader(type) {
      const shader = { type };
      createdShaders.push(shader);
      return shader;
    },
    shaderSource() {},
    compileShader(shader) { shader.failed = failFragment && shader.type === this.FRAGMENT_SHADER; },
    getShaderParameter(shader) { return !shader.failed; },
    getShaderInfoLog() { return "shader compile failed"; },
    deleteShader(shader) { deletedShaders.push(shader); },
    createProgram() {
      const program = {};
      createdPrograms.push(program);
      return program;
    },
    attachShader() {},
    linkProgram() {},
    getProgramParameter() { return true; },
    getProgramInfoLog() { return "program link failed"; },
    deleteProgram(program) { deletedPrograms.push(program); },
    createBuffer() {
      const buffer = {};
      createdBuffers.push(buffer);
      return buffer;
    },
    deleteBuffer(buffer) { deletedBuffers.push(buffer); },
    viewport() {},
    useProgram() {},
    bindBuffer() {},
    bufferData() { bufferUploads.push(true); },
    getAttribLocation(_program, name) { return name === "a_pos" ? 0 : 1; },
    enableVertexAttribArray() {},
    vertexAttribPointer() {},
    getUniformLocation() { return {}; },
    uniform2f() {},
    drawArrays(_mode, _first, count) { drawCalls.push(count); },
    clearColor() {},
    clear() {},
    enable() {},
    blendFunc() {},
  };
  const children = [];
  const stage = {
    firstChild: null,
    style: { transform: "" },
    insertBefore(element) {
      if (failInsert) throw new Error("canvas insertion failed");
      element.parentNode = this;
      children.push(element);
    },
    removeChild(element) {
      const index = children.indexOf(element);
      if (index >= 0) children.splice(index, 1);
      element.parentNode = null;
    },
  };
  const classes = new Set();
  const canvasHost = { classList: {
    add(name) { classes.add(name); },
    remove(name) { classes.delete(name); },
    contains(name) { return classes.has(name); },
  } };
  const styles = [];
  const head = {
    appendChild(style) { style.parentNode = this; styles.push(style); },
    removeChild(style) {
      const index = styles.indexOf(style);
      if (index >= 0) styles.splice(index, 1);
      style.parentNode = null;
    },
  };
  let nextFrame = 1;
  const context = {
    console,
    Worker: FakeWorker,
    GraphPhysics: corePhysics,
    GraphRenderer: graphRenderer,
    document: {
      readyState: "loading",
      head,
      getElementById(id) {
        if (id === "graph-stage") return stage;
        if (id === "graph-canvas") return canvasHost;
        if (id === "graph-renderer-style") return styles.find((style) => style.id === id) || null;
        return null;
      },
      createElement(tag) {
        if (tag === "style") return { id: "", textContent: "" };
        return {
          className: "",
          style: {},
          getContext(name) { return name === "webgl2" && webgl ? gl : null; },
        };
      },
    },
    devicePixelRatio: 1,
    matchMedia() { return { matches: reducedMotion }; },
    requestAnimationFrame(callback) {
      const id = nextFrame++;
      frames.set(id, callback);
      return id;
    },
    cancelAnimationFrame(id) { frames.delete(id); },
  };
  context.globalThis = context;
  return {
    context, frames, createdShaders, deletedShaders, createdPrograms, deletedPrograms,
    createdBuffers, deletedBuffers, drawCalls, bufferUploads, stage, canvasHost, children, styles,
  };
}

function paintNextFrame(surface) {
  const next = surface.frames.entries().next().value;
  assert.ok(next, "a paint was requested");
  surface.frames.delete(next[0]);
  next[1]();
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
  assert.equal(api.workerBacked, true);
  assert.deepEqual(Object.keys(api).sort(), Object.keys(corePhysics).sort());
  assert.deepEqual(Object.keys(api).sort(), Object.keys(corePhysics).sort());
  runtime.tick();
  assert.equal(worker.messages.at(-1).type, "step", "a successful runtime submits a solver step");

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
  assert.equal(context.GraphPhysics, undefined, "the synchronous core is not left as the public API");
});

test("browser adapter requires the renderer to be loaded without writing scripts", () => {
  const context = browserContext();
  context.GraphRenderer = undefined;
  let writes = 0;
  context.document.write = () => { writes += 1; };
  assert.throws(
    () => vm.runInNewContext(adapterSource, context, { filename: "graph-physics.js" }),
    /graph renderer failed to load/
  );
  assert.equal(writes, 0);
});

test("a Worker error terminates the runtime and prevents every later post", () => {
  const context = browserContext();
  const logged = [];
  context.console = { error() { logged.push(Array.from(arguments)); } };
  vm.runInNewContext(adapterSource, context, { filename: "graph-physics.js" });
  const runtime = context.GraphPhysics.create(
    [node("a"), node("b")], [edge("a", "b")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  const worker = FakeWorker.last;

  runtime.tick();
  assert.equal(worker.messages.at(-1).type, "step");
  const messageCount = worker.messages.length;
  const onerror = worker.onerror;

  worker.onerror({ message: "worker crashed" });
  assert.equal(worker.terminated, true);
  assert.equal(worker.terminateCount, 1);
  assert.equal(worker.onmessage, null);
  assert.equal(worker.onerror, null);
  assert.equal(runtime.failed, true);
  assert.equal(runtime.graph.alpha, 0);
  assert.match(runtime.error, /图谱计算失败/);

  runtime.tick();
  runtime.reheat(1, true);
  onerror({ message: "duplicate error" });
  runtime.dispose();
  assert.equal(worker.messages.length, messageCount, "failure is terminal and posts no retry");
  assert.equal(worker.terminateCount, 1, "the Worker is terminated once");
  assert.equal(logged.length, 1, "the failure is reported once");
});

test("real renderer startup failure terminates its Worker and returns a failed runtime", () => {
  const surface = rendererEnvironment({ webgl: false });
  surface.context.console = { error() {} };
  vm.runInNewContext(adapterSource, surface.context, { filename: "graph-physics.js" });

  const runtime = surface.context.GraphPhysics.create(
    [node("a"), node("b")], [edge("a", "b")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  const worker = FakeWorker.last;

  assert.equal(runtime.failed, true);
  assert.match(runtime.error, /WebGL2|渲染/);
  assert.equal(worker.terminated, true);
  assert.equal(worker.terminateCount, 1);
  assert.equal(worker.onmessage, null);
  assert.equal(worker.onerror, null);
  assert.equal(surface.frames.size, 0);
  assert.equal(surface.children.length, 0);
  assert.equal(surface.styles.length, 0);
  assert.equal(surface.canvasHost.classList.contains("graph-renderer-active"), false);
});

test("real renderer paints on invalidation, parks after each frame, and coalesces requests", () => {
  const surface = rendererEnvironment();
  vm.runInNewContext(adapterSource, surface.context, { filename: "graph-physics.js" });
  const runtime = surface.context.GraphPhysics.create(
    [node("a"), node("b")], [edge("a", "b")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  const worker = FakeWorker.last;

  assert.equal(surface.frames.size, 0, "attach waits for the Workbench paint signal");
  runtime.renderer.render();
  runtime.renderer.render();
  assert.equal(surface.frames.size, 1, "multiple normal-motion invalidations share one frame");
  paintNextFrame(surface);

  assert.equal(surface.drawCalls.length, 1);
  assert.ok(surface.drawCalls[0] > 0, "the graph relation is painted with WebGL");
  assert.equal(surface.bufferUploads.length, 1);
  assert.ok(runtime.state.portSlots.size > 0, "the physics geometry supplies edge ports");
  assert.equal(surface.frames.size, 0, "a completed paint does not schedule an idle frame");

  runtime.renderer.resize();
  assert.equal(surface.frames.size, 1, "resize requests one paint");
  paintNextFrame(surface);
  assert.equal(surface.drawCalls.length, 2);
  assert.equal(surface.frames.size, 0);

  runtime.renderer.render();
  assert.equal(surface.frames.size, 1);
  runtime.dispose();
  assert.equal(surface.frames.size, 0);
  assert.equal(worker.terminated, true);
});

test("reduced-motion renderer paints synchronously without requesting animation frames", () => {
  const surface = rendererEnvironment({ reducedMotion: true });
  vm.runInNewContext(adapterSource, surface.context, { filename: "graph-physics.js" });
  const runtime = surface.context.GraphPhysics.create(
    [node("a"), node("b")], [edge("a", "b")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );

  assert.equal(surface.frames.size, 0);
  assert.equal(surface.drawCalls.length, 0, "attachment waits for the stable Workbench paint");
  runtime.renderer.render();
  assert.equal(surface.drawCalls.length, 1);
  assert.equal(surface.frames.size, 0);
  runtime.renderer.resize();
  assert.equal(surface.drawCalls.length, 2);
  assert.equal(surface.frames.size, 0);
  runtime.dispose();
});

test("renderer shader setup failure deletes partial GL resources before rethrowing", () => {
  const surface = rendererEnvironment({ failFragment: true });
  assert.throws(
    () => graphRenderer.attach({ state: {} }, surface.context),
    /shader compile failed/
  );
  assert.equal(surface.deletedShaders.length, 2);
  assert.equal(surface.deletedPrograms.length, 1);
  assert.equal(surface.children.length, 0);
  assert.equal(surface.styles.length, 0);
  assert.equal(surface.frames.size, 0);
});

test("renderer attach failure after GL setup releases its partial resources", () => {
  const surface = rendererEnvironment({ failInsert: true });
  const routePorts = function () {};
  const routePath = function () {};
  const runtime = {
    state: { stageWidth: 800, stageHeight: 600, graph: {}, byId: new Map(), portSlots: new Map() },
    computePortSlots: routePorts,
    edgePath: routePath,
    visibleEdges() { return []; },
    edgeStyle() { return {}; },
  };
  assert.throws(
    () => graphRenderer.attach(runtime, surface.context),
    /canvas insertion failed/
  );
  assert.equal(surface.deletedPrograms.length, 1);
  assert.equal(surface.deletedBuffers.length, 1);
  assert.equal(surface.children.length, 0);
  assert.equal(surface.styles.length, 0);
  assert.equal(surface.frames.size, 0);
  assert.equal(surface.canvasHost.classList.contains("graph-renderer-active"), false);
  assert.equal(runtime.computePortSlots, routePorts);
  assert.equal(runtime.edgePath, routePath);
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
