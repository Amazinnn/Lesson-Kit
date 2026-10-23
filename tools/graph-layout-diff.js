#!/usr/bin/env node
"use strict";

/* graph-layout-diff.js — SI-0 baseline capture / diff tool for the knowledge-graph layout.
 *
 * Why this exists
 * ---------------
 * The owner's hard line is "do not touch the graph's algorithm — we are only changing
 * how it looks".  `openspec/changes/graph-node-visual-language/acceptance.md` §0.2 SI-0
 * turns that line into an executable gate: same input + same initial condition + same
 * iteration budget => the converged coordinate set must diff to exactly 0 across the
 * visual change.  This script is that gate.
 *
 * It is deliberately small and read-only:
 *   - pure Node, no third-party dependency (the repo has no npm build);
 *   - it loads the DOM-free core directly, so no browser is involved;
 *   - it never touches the pool database, never writes product code, never mutates
 *     anything outside the file it is told to write.
 *
 * Usage
 * -----
 *   node tools/graph-layout-diff.js --capture <out.json>
 *   node tools/graph-layout-diff.js --diff <baseline.json>
 *   node tools/graph-layout-diff.js --help
 *
 * Exit codes
 * ----------
 *   0  diff is exactly 0 (or --capture succeeded)
 *   1  diff is non-zero
 *   2  usage error, unreadable file, or the run did not converge
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

/* ---------------------------------------------------------------------------
 * Frozen knobs.  These are part of the tool's contract: changing any of them
 * invalidates every baseline captured with the old values.
 * ------------------------------------------------------------------------- */

const QUANT = {
  /* Decimal places kept for every coordinate.  Fixed, not a tolerance knob:
   * the diff below compares the *strings* produced by toFixed(decimals), so
   * there is no epsilon anywhere in the comparison. */
  decimals: 6,
  /* Rows are ordered by this key so the snapshot is byte-stable. */
  sortKey: "nodeId",
  /* ...and ordered by code unit, not by locale collation. */
  order: "code-unit ascending",
  /* How two coordinates are judged equal. */
  comparison: "exact string equality of toFixed(decimals)",
};

/* Iteration budget.  Fixed: every run gets exactly this many ticks.  The core
 * zeroes alpha once the layout settles, so any tick past the settle point is a
 * no-op — the result is the converged layout and does not depend on where the
 * budget happens to sit, as long as it is above the settle tick (which the
 * snapshot records). */
const TICK_BUDGET = 600;

/* ---------------------------------------------------------------------------
 * The deterministic input graph.
 *
 * Synthetic on purpose: the product's own pool is a moving target (a chapter
 * gains and loses knowledge points every time somebody edits it), and a
 * baseline must stay comparable with the code that produced it.  A synthetic
 * graph with a fixed shape is the only input that is guaranteed to still be
 * the same input next year.
 *
 * Scale: 12 chapters x 8 knowledge points = 96 nodes, ~360 relations.
 *   - >= 80 nodes, so the layout exercises the Barnes-Hut charge and the
 *     pairwise collide pass at a size where both actually do work (the module
 *     header quotes a measured cost of 15.83ms/tick at 192 points / 727 edges,
 *     so 96 points sits comfortably above the size where a naive O(n^2) pass
 *     would still be fast enough to hide a change);
 *   - 12 groups, so the graph spans many chapters and the "several chapter
 *     groupings" shape of a real course is covered;
 *   - a prereq chain inside every chapter plus prereq-free links between
 *     chapters, so the layout spans 8 hierarchy levels (a flat, single-level
 *     pool would take a completely different code path — see flatLevel() in
 *     the core) and every edge type the core knows about;
 *   - mean degree ~7.5, the density of a real course graph (the 习概 pool
 *     measures 192 points / 727 edges), so the spring / charge / collide
 *     balance the layout settles into is a realistic one.
 *
 * Determinism: no Math.random anywhere; every value is a pure function of the
 * node index.  The ids are fixed-width lowercase alphanumerics on purpose:
 * the core sorts by id with String.localeCompare in two places
 * (graph-physics-core.js:613 and :664), and for equal-width ASCII ids the
 * locale collation and the code-unit order agree, so the layout does not
 * depend on the machine's ICU data.
 * ------------------------------------------------------------------------- */

const GROUPS = 12;
const PER_GROUP = 8;

const STATES = ["new", "review", "mastered", "work"];
const KINDS = ["core", "basic", "extended"];
const TOPICS = [
  "函数与极限", "导数与微分", "积分", "微分方程", "级数", "多元微积分",
  "向量与矩阵", "线性方程组", "特征值", "空间解析几何", "三重积分", "曲线曲面积分",
];

function nodeId(group, index) {
  return "c" + String(group + 1).padStart(2, "0") + "n" + String(index).padStart(2, "0");
}

function buildGraph() {
  const nodes = [];
  const edges = [];

  for (let g = 0; g < GROUPS; g += 1) {
    const chapter = String(g + 1).padStart(2, "0");
    for (let k = 0; k < PER_GROUP; k += 1) {
      const i = g * PER_GROUP + k;
      nodes.push({
        id: nodeId(g, k),
        title: "第" + chapter + "章 " + TOPICS[g] + " 知识点 " + String(k + 1).padStart(2, "0"),
        shortTitle: "知" + chapter + "-" + String(k + 1).padStart(2, "0"),
        state: STATES[i % STATES.length],
        kind: KINDS[i % KINDS.length],
        importance: ((i * 37) % 101) / 100,
        problems: (i * 11) % 23,
      });
    }
  }

  for (let g = 0; g < GROUPS; g += 1) {
    /* Intra-chapter prerequisite chain: this is what builds the hierarchy
     * levels (hierarchyLevels() only reads prereq edges that are not
     * symmetric). */
    for (let k = 0; k + 1 < PER_GROUP; k += 1) {
      edges.push({
        s: nodeId(g, k),
        t: nodeId(g, k + 1),
        type: "prereq",
        strength: 0.9 + 0.2 * (((g + k) % 5) / 4),
        direction: "directed",
      });
    }
    /* Intra-chapter skip links: apply (directed) reaches forward past the
     * chain, related and contrast cross it. */
    for (let k = 0; k + 2 < PER_GROUP; k += 1) {
      edges.push({
        s: nodeId(g, k), t: nodeId(g, k + 2),
        type: "apply", strength: 1.05 + 0.1 * ((k % 3) / 2), direction: "directed",
      });
      edges.push({
        s: nodeId(g, k), t: nodeId(g, k + 2),
        type: "related", strength: 0.85 + 0.1 * ((k % 4) / 3), direction: "symmetric",
      });
    }
    for (let k = 0; k + 4 < PER_GROUP; k += 1) {
      edges.push({
        s: nodeId(g, k), t: nodeId(g, k + 4),
        type: "contrast", strength: 0.8 + 0.1 * ((k % 2)), direction: "symmetric",
      });
    }
    /* Chapter-to-chapter links: apply is directed, the rest are symmetric. */
    if (g + 1 < GROUPS) {
      edges.push({
        s: nodeId(g, PER_GROUP - 1), t: nodeId(g + 1, 0),
        type: "apply", strength: 1.1, direction: "directed",
      });
      edges.push({
        s: nodeId(g, 4), t: nodeId(g + 1, 5),
        type: "contrast", strength: 0.8, direction: "symmetric",
      });
      edges.push({
        s: nodeId(g, 6), t: nodeId(g + 1, 1),
        type: "related", strength: 0.9, direction: "symmetric",
      });
    }
    if (g + 2 < GROUPS) {
      edges.push({
        s: nodeId(g, 1), t: nodeId(g + 2, 3),
        type: "related", strength: 0.85, direction: "symmetric",
      });
      edges.push({
        s: nodeId(g, 2), t: nodeId(g + 2, 6),
        type: "apply", strength: 0.95, direction: "directed",
      });
    }
    if (g + 3 < GROUPS) {
      edges.push({
        s: nodeId(g, 6), t: nodeId(g + 3, 2),
        type: "legacy", strength: 0.75, direction: "symmetric",
      });
    }
  }

  return { nodes: nodes, edges: edges };
}

/* ---------------------------------------------------------------------------
 * Quantization helpers.
 * ------------------------------------------------------------------------- */

function quantize(value) {
  if (!Number.isFinite(value)) {
    throw new Error("non-finite coordinate: " + value);
  }
  if (Math.abs(value) > 1e9) {
    throw new Error("coordinate out of the quantization-safe range: " + value);
  }
  return Number(value.toFixed(QUANT.decimals));
}

function qtext(value) {
  return value.toFixed(QUANT.decimals);
}

function byId(a, b) {
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

function sha256OfFile(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

/* ---------------------------------------------------------------------------
 * The run.
 * ------------------------------------------------------------------------- */

const CORE_REL = path.join("workbench", "server", "static", "graph-physics-core.js");
const CORE_ABS = path.join(__dirname, "..", CORE_REL);

function simulate() {
  /* The core is DOM-free and ships a CommonJS export, so it loads under Node
   * with no browser and no worker. */
  const GraphPhysics = require(CORE_ABS);

  const graph = buildGraph();

  /* No options are passed on purpose: the core's own defaults (view
   * "structure", gravity 85, stage 1800x1550) are the product's behaviour, and
   * the effective values are recorded in the snapshot below.  Pinning them
   * here would hide a change to those defaults from the diff — and a change to
   * them is exactly the kind of thing SI-0 must catch. */
  const mirror = GraphPhysics.create(graph.nodes, graph.edges);

  /* The initial condition, captured before the first tick.  The core seeds the
   * layout with its own deterministic seat spiral (seatPositions(),
   * graph-physics-core.js:938) — a fixed function of the node set and the
   * edge set, with no randomness.  We do not override it: the seed the product
   * uses is the seed that has to be frozen, and recording it here makes the
   * "same initial condition" half of SI-0 auditable rather than assumed. */
  const seed = mirror.nodes.map(function (n) {
    return { id: n.id, x: quantize(n.x), y: quantize(n.y) };
  }).sort(byId);

  let settledAtTick = null;
  let settledBy = null;
  let settledAlpha = null;
  let settledSettleWatch = null;
  for (let tick = 1; tick <= TICK_BUDGET; tick += 1) {
    mirror.tick();
    if (settledAtTick === null && mirror.graph.settled) {
      settledAtTick = tick;
      settledAlpha = mirror.graph.alpha;
      settledSettleWatch = mirror.graph.settleWatch || 0;
      /* The core has two ways to stop: the honest one (15 consecutive stable
       * frames: no overlapping pair and a low average speed) and the safety
       * valve (forces gone, 120 further rounds, stop anyway).  Which one fired
       * is part of the audit trail — a layout that only ever stops through the
       * safety valve is a layout that ends with residual overlap. */
      settledBy = settledSettleWatch > 120 ? "safety-valve" : "stable-frames";
    }
  }

  if (!mirror.graph.settled) {
    throw new Error(
      "the layout did not converge within the iteration budget (" + TICK_BUDGET
      + " ticks); refusing to snapshot a non-converged layout"
    );
  }

  const nodes = mirror.nodes.map(function (n) {
    return { id: n.id, x: quantize(n.x), y: quantize(n.y) };
  }).sort(byId);

  return {
    snapshot: {
      schema: "lessonkit.graph-layout-snapshot/1",
      generator: "tools/graph-layout-diff.js",
      quantization: {
        decimals: QUANT.decimals,
        sortKey: QUANT.sortKey,
        order: QUANT.order,
        comparison: QUANT.comparison,
      },
      input: {
        graph: "synthetic-deterministic-v1",
        nodeCount: graph.nodes.length,
        edgeCount: graph.edges.length,
        groupCount: GROUPS,
        nodesPerGroup: PER_GROUP,
        view: mirror.graph.view,
        gravity: mirror.graph.gravity,
        stageWidth: mirror.state.stageWidth,
        stageHeight: mirror.state.stageHeight,
        tickBudget: TICK_BUDGET,
        settled: true,
        settledAtTick: settledAtTick,
        settledBy: settledBy,
        settledAlpha: settledAlpha,
        settledSettleWatch: settledSettleWatch,
      },
      source: {
        module: CORE_REL.split(path.sep).join("/"),
        sha256: sha256OfFile(CORE_ABS),
      },
      nodes: nodes,
      seed: seed,
    },
    graph: graph,
  };
}

/* ---------------------------------------------------------------------------
 * Diff.
 * ------------------------------------------------------------------------- */

function compareSets(baselineRows, currentRows) {
  const baselineIds = baselineRows.map(function (r) { return r.id; });
  const currentIds = currentRows.map(function (r) { return r.id; });
  const baselineSet = new Set(baselineIds);
  const currentSet = new Set(currentIds);
  const onlyBaseline = baselineIds.filter(function (id) { return !currentSet.has(id); });
  const onlyCurrent = currentIds.filter(function (id) { return !baselineSet.has(id); });
  return { onlyBaseline: onlyBaseline, onlyCurrent: onlyCurrent };
}

function compareRows(baselineRows, currentRows) {
  const currentById = new Map(currentRows.map(function (r) { return [r.id, r]; }));
  const differences = [];
  baselineRows.forEach(function (base) {
    const cur = currentById.get(base.id);
    if (!cur) return; /* id-set difference is reported separately */
    const baseX = qtext(base.x);
    const baseY = qtext(base.y);
    const curX = qtext(cur.x);
    const curY = qtext(cur.y);
    if (baseX === curX && baseY === curY) return;
    differences.push({
      id: base.id,
      baseline: { x: baseX, y: baseY },
      current: { x: curX, y: curY },
      dx: Number((cur.x - base.x).toFixed(QUANT.decimals)),
      dy: Number((cur.y - base.y).toFixed(QUANT.decimals)),
    });
  });
  return differences;
}

function printDifferences(title, differences, limit) {
  console.log("");
  console.log("[" + title + "]");
  if (!differences.length) {
    console.log("  differences     : 0");
    return;
  }
  console.log("  differences     : " + differences.length);
  console.log("  " + "#".padEnd(4) + "id".padEnd(12) + "baseline x".padEnd(16) + "baseline y".padEnd(16)
    + "current x".padEnd(16) + "current y".padEnd(16) + "dx".padEnd(14) + "dy");
  differences.slice(0, limit).forEach(function (d, i) {
    console.log("  " + String(i + 1).padEnd(4) + d.id.padEnd(12)
      + d.baseline.x.padEnd(16) + d.baseline.y.padEnd(16)
      + d.current.x.padEnd(16) + d.current.y.padEnd(16)
      + String(d.dx).padEnd(14) + String(d.dy));
  });
  if (differences.length > limit) {
    console.log("  ... " + (differences.length - limit) + " more (raise --max-report to see them)");
  }
}

function printHeader(snapshot, label) {
  console.log("=== graph-layout-diff (" + label + ") ===");
  console.log("");
  console.log("[quantization — the comparison contract]");
  console.log("  decimals        : " + snapshot.quantization.decimals);
  console.log("  sort key        : " + snapshot.quantization.sortKey + " (" + snapshot.quantization.order + ")");
  console.log("  comparison      : " + snapshot.quantization.comparison + " (no epsilon anywhere)");
  console.log("");
  console.log("[input]");
  console.log("  graph           : " + snapshot.input.graph);
  console.log("  nodes / edges   : " + snapshot.input.nodeCount + " / " + snapshot.input.edgeCount
    + "  (" + snapshot.input.groupCount + " chapters x " + snapshot.input.nodesPerGroup + ")");
  console.log("  view / gravity  : " + snapshot.input.view + " / " + snapshot.input.gravity);
  console.log("  stage           : " + snapshot.input.stageWidth + " x " + snapshot.input.stageHeight);
  console.log("  iteration budget: " + snapshot.input.tickBudget + " ticks (settled at tick " + snapshot.input.settledAtTick
    + ", via " + snapshot.input.settledBy + ")");
  console.log("");
  console.log("[source]");
  console.log("  module          : " + snapshot.source.module);
  console.log("  sha256          : " + snapshot.source.sha256);
}

/* ---------------------------------------------------------------------------
 * Modes.
 * ------------------------------------------------------------------------- */

function capture(outPath) {
  const result = simulate();
  const snapshot = result.snapshot;
  const text = JSON.stringify(snapshot, null, 2) + "\n";
  fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
  fs.writeFileSync(outPath, text, "utf8");
  printHeader(snapshot, "capture");
  console.log("[output]");
  console.log("  path            : " + outPath);
  console.log("  bytes           : " + Buffer.byteLength(text, "utf8"));
  console.log("  sha256          : " + crypto.createHash("sha256").update(text, "utf8").digest("hex"));
  console.log("  node rows       : " + snapshot.nodes.length);
  console.log("  seed rows       : " + snapshot.seed.length);
  console.log("");
  console.log("RESULT: OK — baseline written");
  return 0;
}

function diff(baselinePath, maxReport) {
  let baseline;
  try {
    baseline = JSON.parse(fs.readFileSync(baselinePath, "utf8"));
  } catch (error) {
    console.error("cannot read baseline: " + error.message);
    return 2;
  }
  if (!baseline || !baseline.quantization || !baseline.nodes || !baseline.seed) {
    console.error("baseline file is not a graph layout snapshot");
    return 2;
  }
  if (baseline.quantization.decimals !== QUANT.decimals) {
    console.error(
      "baseline was captured with decimals=" + baseline.quantization.decimals
      + " but this tool quantizes with decimals=" + QUANT.decimals
      + "; the two are not comparable — re-capture the baseline"
    );
    return 2;
  }

  const current = simulate().snapshot;
  printHeader(current, "diff");

  console.log("[baseline]");
  console.log("  path            : " + baselinePath);
  console.log("  module sha256   : " + (baseline.source ? baseline.source.sha256 : "(unknown)"));
  console.log("  budget / settle : " + baseline.input.tickBudget + " / " + baseline.input.settledAtTick);
  if (baseline.source && baseline.source.sha256 !== current.source.sha256) {
    console.log("");
    console.log("  *** WARNING: graph-physics-core.js has changed since this baseline was captured.");
    console.log("  *** Any change to graph-physics-core.js / graph-physics.js must be re-captured");
    console.log("  *** and the difference explained in tools/graph-baseline/EVIDENCE.md,");
    console.log("  *** otherwise SI-0 has lost its meaning.");
  }
  console.log("");

  const nodeIdDiff = compareSets(baseline.nodes, current.nodes);
  const seedIdDiff = compareSets(baseline.seed, current.seed);

  console.log("[node id set]");
  console.log("  baseline ids    : " + baseline.nodes.length);
  console.log("  current ids     : " + current.nodes.length);
  console.log("  only in baseline: " + (nodeIdDiff.onlyBaseline.length ? nodeIdDiff.onlyBaseline.join(", ") : "(none)"));
  console.log("  only in current : " + (nodeIdDiff.onlyCurrent.length ? nodeIdDiff.onlyCurrent.join(", ") : "(none)"));
  console.log("");

  const nodeDiffs = compareRows(baseline.nodes, current.nodes);
  const seedDiffs = compareRows(baseline.seed, current.seed);

  printDifferences("converged coordinates — SI-0 target", nodeDiffs, maxReport);
  console.log("");
  printDifferences("initial coordinates (seed) — the 'same initial condition' half", seedDiffs, maxReport);

  const idDiffCount = nodeIdDiff.onlyBaseline.length + nodeIdDiff.onlyCurrent.length + seedIdDiff.onlyBaseline.length + seedIdDiff.onlyCurrent.length;
  const total = nodeDiffs.length + seedDiffs.length + idDiffCount;

  console.log("");
  console.log("[summary]");
  console.log("  compared nodes  : " + Math.min(baseline.nodes.length, current.nodes.length));
  console.log("  coordinate diffs: " + nodeDiffs.length);
  console.log("  seed diffs      : " + seedDiffs.length);
  console.log("  id set diffs    : " + idDiffCount);
  console.log("  total differences: " + total);
  console.log("");

  if (total === 0) {
    console.log("RESULT: PASS — converged coordinate diff = 0 (SI-0 green)");
    return 0;
  }
  console.log("RESULT: FAIL — diff = " + total + " (SI-0 red: locate the out-of-scope change and revert it)");
  return 1;
}

function usage() {
  console.log("graph-layout-diff — SI-0 layout baseline capture / diff (read-only, no pool access)");
  console.log("");
  console.log("  node tools/graph-layout-diff.js --capture <out.json>   write a baseline snapshot");
  console.log("  node tools/graph-layout-diff.js --diff <baseline.json>  compare against a baseline");
  console.log("  node tools/graph-layout-diff.js --help                  this text");
  console.log("");
  console.log("options:");
  console.log("  --max-report N   how many differing nodes to print (default 20)");
  console.log("");
  console.log("exit codes: 0 = diff is exactly 0, 1 = diff is non-zero, 2 = usage/IO error");
}

/* ---------------------------------------------------------------------------
 * CLI.
 * ------------------------------------------------------------------------- */

function main(argv) {
  let mode = null;
  let target = null;
  let maxReport = 20;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      usage();
      return 0;
    }
    if (arg === "--capture" || arg === "--diff") {
      mode = arg.slice(2);
      target = argv[i + 1];
      i += 1;
      continue;
    }
    if (arg === "--max-report") {
      maxReport = parseInt(argv[i + 1], 10);
      i += 1;
      continue;
    }
    console.error("unknown argument: " + arg);
    usage();
    return 2;
  }

  if (!mode || !target) {
    usage();
    return 2;
  }

  try {
    if (mode === "capture") return capture(target);
    if (mode === "diff") return diff(target, maxReport);
  } catch (error) {
    console.error("graph-layout-diff failed: " + error.message);
    return 2;
  }
  usage();
  return 2;
}

process.exitCode = main(process.argv.slice(2));
