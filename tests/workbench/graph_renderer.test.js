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

test("renderer keeps stroke compensation tied to the Workbench stage scale", () => {
  assert.equal(renderer.stageScale({ style: { transform: "translate(12px,-4px) scale(0.5)" } }), .5);
  assert.equal(renderer.stageScale({ style: { transform: "" } }), 1);
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
