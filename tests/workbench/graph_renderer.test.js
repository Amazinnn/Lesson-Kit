"use strict";

const assert = require("node:assert/strict");
const path = require("node:path");
const test = require("node:test");

const ROOT = path.join(__dirname, "../..");
const renderer = require(path.join(ROOT, "workbench/server/static/graph-renderer.js"));

test("renderer consumes the exact cubic path produced by graph physics", () => {
  const curve = renderer.parseCurve("M 10.0 20.0 C 30.0 40.0 50.0 60.0 70.0 80.0");
  assert.deepEqual(curve, {
    p0: [10, 20],
    p1: [30, 40],
    p2: [50, 60],
    p3: [70, 80],
  });
  assert.deepEqual(renderer.cubic(curve, 0), curve.p0);
  assert.deepEqual(renderer.cubic(curve, 1), curve.p3);
  assert.equal(renderer.parseCurve("not a graph path"), null);
});

test("renderer derives viewport and LOD geometry from the Workbench camera", () => {
  const stage = { style: { transform: "translate(120px,-40px) scale(0.5)" } };
  const host = { clientWidth: 800, clientHeight: 600 };
  const viewport = renderer.viewportFor(stage, host, 0);
  assert.deepEqual(viewport, { x0: -240, y0: 80, x1: 1360, y1: 1280, scale: .5 });
  assert.equal(renderer.nodeInViewport({ x: 100, y: 100, size: 40 }, viewport), true);
  assert.equal(renderer.nodeInViewport({ x: 3000, y: 3000, size: 40 }, viewport), false);
  assert.equal(renderer.stageScale(stage), .5);
});

test("renderer fails explicitly without its browser surface", () => {
  assert.throws(
    () => renderer.attach({ state: {} }, {}),
    /requires a browser graph runtime/
  );
});

test("renderer fails explicitly when WebGL2 is unavailable", () => {
  const stage = { insertBefore() {}, firstChild: null };
  const host = { classList: { add() {}, remove() {} } };
  const document = {
    getElementById(id) { return id === "graph-stage" ? stage : id === "graph-canvas" ? host : null; },
    createElement() { return { getContext() { return null; } }; },
  };
  assert.throws(
    () => renderer.attach({ state: {} }, { document }),
    /requires WebGL2/
  );
});
