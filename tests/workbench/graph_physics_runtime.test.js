"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const publicPhysics = require("../../workbench/server/static/graph-physics.js");
const corePhysics = require("../../workbench/server/static/graph-physics-core.js");
const loaderSource = fs.readFileSync(
  require.resolve("../../workbench/server/static/graph-physics.js"),
  "utf8"
);
const coreSource = fs.readFileSync(
  require.resolve("../../workbench/server/static/graph-physics-core.js"),
  "utf8"
);

function node(id, extra) {
  return Object.assign({
    id: id,
    title: id,
    state: "new",
    kind: "core",
    importance: .5,
    problems: 1,
  }, extra || {});
}

function edge(s, t, type, strength) {
  return {
    s: s,
    t: t,
    type: type || "prereq",
    strength: strength === undefined ? 1.25 : strength,
  };
}

function settle(api) {
  const sim = api.create(
    [node("a"), node("b"), node("c"), node("d")],
    [edge("a", "b"), edge("b", "c"), edge("c", "d"), edge("a", "d", "related")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  for (let i = 0; i < 500 && sim.graph.alpha > 0; i += 1) sim.tick();
  return {
    alpha: sim.graph.alpha,
    congestion: sim.congestion(),
    nodes: sim.nodes.map((item) => ({
      id: item.id,
      x: item.x,
      y: item.y,
      size: item.size,
    })),
  };
}

test("graph physics public seam exposes the semantic core contract", () => {
  assert.deepEqual(
    Object.keys(corePhysics).sort(),
    Object.keys(publicPhysics).sort(),
    "the public seam must expose the current core implementation without a second solver"
  );
  assert.deepEqual(settle(corePhysics), settle(publicPhysics));
});

test("parser-inserted core can load after the public loader returns", async () => {
  const insertedScripts = [];
  const browser = vm.createContext({
    document: {
      readyState: "loading",
      write(markup) {
        const match = markup.match(/<script src="([^"]+)"><\/script>/);
        assert.ok(match, "the loader writes one external script");
        insertedScripts.push(match[1]);
      },
    },
  });

  assert.doesNotThrow(() => vm.runInContext(loaderSource, browser));
  assert.deepEqual(insertedScripts, ["/static/graph-physics-core.js"]);
  assert.equal(vm.runInContext("typeof GraphPhysics", browser), "undefined");

  await new Promise((resolve) => setImmediate(resolve));
  vm.runInContext(coreSource, browser);
  assert.equal(
    vm.runInContext("typeof GraphPhysics.create === 'function'", browser),
    true
  );
});

test("browser loader still refuses non-parser loading", () => {
  const browser = vm.createContext({
    document: { readyState: "complete", write() {} },
  });

  assert.throws(
    () => vm.runInContext(loaderSource, browser),
    /must be parser-loaded before workbench\.js/
  );
});
