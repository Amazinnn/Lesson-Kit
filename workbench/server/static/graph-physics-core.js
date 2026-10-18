"use strict";

/* Knowledge-graph physics: the constrained semantic layout.
 *
 * This module is a direct port of the implementation blueprint
 * (`Lesson_Kit_Knowledge_Graph_BLUEPRINT.html`): same constants, same curves,
 * same order of solver passes.  It is DOM-free — the page owns nodes' DOM,
 * this module owns positions.
 *
 * Non-negotiable rules carried from the blueprint:
 *  - relation strength asks for a distance; readability is a hard floor;
 *  - under pressure the layout expands its footprint and lets Fit zoom out —
 *    it never shrinks the readability floor;
 *  - one circular node body; edges leave through per-node ports and lanes.
 *
 * Complexity ceiling: density and congestion passes are pairwise (O(n²) plus
 * one corridor pass per visible edge).  At course scale (≤ ~200 knowledge
 * points) that is a few milliseconds per tick; a much larger graph would need
 * the spatial buckets again.
 */

(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.GraphPhysics = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  var PHI = 2.399963229728653;
  var TAU = Math.PI * 2;

  var STATE_ATTENTION = { work: 1, review: .70, mastered: .22, new: .46 };
  var TYPE_WEIGHT = { prereq: 1, apply: .82, contrast: .70, related: .58 };
  var NEIGHBOR_WEIGHT = { prereq: 1.35, apply: 1.0, contrast: .82, related: .68 };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  /* The built-in two-argument hypotenuse is an order of magnitude slower than
   * sqrt; the solver runs hundreds of distance tests per tick. */
  function dist2d(dx, dy) {
    return Math.sqrt(dx * dx + dy * dy);
  }

  function strength01(value) {
    return clamp(((Number(value) || 1) - .75) / 1.125, 0, 1);
  }

  function sizeFor(score) {
    return 28 + 34 * Math.sqrt(clamp(Number(score) || 0, 0, 1));
  }

  function stateAttention(state) {
    return STATE_ATTENTION[state] === undefined ? .46 : STATE_ATTENTION[state];
  }

  function baseGapForStrength(strength) {
    return 218 - 118 * strength01(strength);
  }

  function compactness01(gravity) {
    var g = clamp(Number(gravity) / 100, 0, 1);
    // Saturating curve: the right half of the slider approaches the compact
    // readable limit rather than continuing to crush the graph.
    return (1 - Math.exp(-3 * g)) / (1 - Math.exp(-3));
  }

  function spreadFactor(gravity) {
    return 1.29 - .41 * compactness01(gravity);
  }

  function labelWidth(title) {
    return Math.min(168, Math.max(62, Array.from(String(title || "")).length * 12 + 18));
  }

  /* The room a point needs. This is not only about a label not covering its
   * neighbours: labelWidth is what the readability floor is built from, so the width
   * here also decides how close two points may sit, how small the whole graph can be,
   * and therefore how far Fit zooms out. The graph shows an abbreviated title, so the
   * room is measured from the abbreviation — otherwise the layout pays for text that
   * is not on screen. The full title still travels with the point for the hover. */
  function footprint(node) {
    var half = Math.max(node.size / 2 + 13, labelWidth(node.shortTitle || node.title) / 2);
    return {
      left: half,
      right: half,
      top: node.size / 2 + 13,
      bottom: node.size / 2 + 42,
    };
  }

  /* A hierarchy level is one centered row in the blueprint; real pools regularly
   * put a hundred relations-less knowledge points on level zero, and a single
   * 35k-pixel ribbon can only be answered by Fit shrinking to nothing. Wide
   * levels therefore wrap into stacked rows inside the same level band. */
  var BAND_MAX_WIDTH = 2400;

  function bandRows(widths, gap) {
    var rows = [];
    var current = [];
    var used = 0;
    widths.forEach(function (w, index) {
      var cost = current.length ? gap + w : w;
      if (current.length && used + cost > BAND_MAX_WIDTH) {
        rows.push(current);
        current = [];
        used = 0;
        cost = w;
      }
      current.push(index);
      used += cost;
    });
    if (current.length) rows.push(current);
    if (rows.length > 1) {
      // Rebalance to even chunk sizes; the stage keeps one footprint of slack
      // past the band ceiling, so the small width spread between rows is safe.
      var per = Math.ceil(widths.length / rows.length);
      var even = [];
      for (var start = 0; start < widths.length; start += per) {
        var chunk = [];
        for (var k = start; k < Math.min(widths.length, start + per); k += 1) chunk.push(k);
        even.push(chunk);
      }
      rows = even;
    }
    return rows;
  }

  function rowIndexOf(node) {
    return node.rowIndex === undefined || node.rowIndex === null
      ? (node.level || 0)
      : node.rowIndex;
  }

  /* A pool with no directed prerequisite relation has no hierarchy at all: every
   * point lands on one level, and row wrapping alone can only answer a wide level
   * with a longer ribbon — 86 points became a 2780x1268 diagonal band. Past this
   * many points a flat level is clustered in two dimensions instead. */
  var FLAT_LEVEL_CLUSTER_MIN = 12;
  // Roughly landscape; keeps the cluster inside a workbench canvas without a Fit
  // zoom that shrinks labels away. ponytail: fixed ratio, derive from the real
  // canvas if the projection ever moves away from the stage model.
  var CLUSTER_ASPECT = 1.35;

  function flatLevel(nodes, edges) {
    return nodes.length > FLAT_LEVEL_CLUSTER_MIN
      && new Set(nodes.map(function (n) { return n.level || 0; })).size === 1;
  }

  // Cell size is derived from label width and targetSize only. footprint() would be
  // NaN here: the stage is sized before create() gives nodes their real size, so only
  // the pre-layout fields are safe to read.
  function clusterCellWidth(node) {
    return Math.max(labelWidth(node.shortTitle || node.title), (node.targetSize || 0) + 34, 96);
  }

  function clusterCellHeight(node) {
    return (node.targetSize || 28) + 55 + 12 + 14;
  }

  // Needs the same grid the guides will use, and only one of the two callers owns the
  // state object — so it is self-contained: degrees come off the shared neighbour index.
  function clusterGeometry(nodes, edges, center) {
    if (!flatLevel(nodes, edges)) return null;
    var index = neighborIndex(edges);
    function degreeOf(node) {
      var seen = new Set();
      (index.get(node.id) || []).forEach(function (other) {
        if (nodes.indexOf(other) >= 0) seen.add(other.id);
      });
      return seen.size;
    }
    var cellWidth = 0;
    var cellHeight = 0;
    nodes.forEach(function (n) {
      var margin = 12 + Math.min(28, degreeOf(n) * 1.15);
      cellWidth = Math.max(cellWidth, clusterCellWidth(n) + margin);
      cellHeight = Math.max(cellHeight, clusterCellHeight(n) + margin);
    });
    var columns = Math.max(1, Math.round(Math.sqrt(nodes.length * CLUSTER_ASPECT)));
    var rows = Math.ceil(nodes.length / columns);
    var anchor = center || { x: 0, y: 0 };
    return {
      columns: columns,
      rows: rows,
      cellWidth: cellWidth,
      cellHeight: cellHeight,
      x0: anchor.x - columns * cellWidth / 2,
      y0: anchor.y - rows * cellHeight / 2,
    };
  }

  function clusterCellCenter(geometry, index) {
    var column = index % geometry.columns;
    var row = Math.floor(index / geometry.columns);
    return {
      x: geometry.x0 + (column + .5) * geometry.cellWidth,
      y: geometry.y0 + (row + .5) * geometry.cellHeight,
    };
  }

  function structureStageSize(nodes, levels, gravity) {
    var spread = spreadFactor(gravity);
    var gap = 64 + 38 * spread;
    var pitch = 155 * spread;
    var groups = new Map();
    nodes.forEach(function (n) {
      var level = levels.get(n.id) || 0;
      if (!groups.has(level)) groups.set(level, []);
      groups.get(level).push(n);
    });
    var rowCount = 0;
    var widestSingleRow = 0;
    var wrapped = false;
    groups.forEach(function (group) {
      var widths = group.map(function (n) { return Math.max(labelWidth(n.shortTitle || n.title), 96); });
      var rows = bandRows(widths, gap);
      if (rows.length > 1) wrapped = true;
      rowCount += rows.length;
      if (rows.length === 1) {
        var width = widths.reduce(function (a, b) { return a + b; }, 0)
          + gap * Math.max(0, widths.length - 1);
        widestSingleRow = Math.max(widestSingleRow, width);
      }
    });
    // A pool with no directed relation sorts every point onto one level, and row
    // wrapping answers it with a longer ribbon — 86 points became a 2780x1268
    // diagonal band. Past the threshold the guides become a 2-D cluster, so the
    // stage has to follow that cluster instead of the band ceiling.
    var flatOnly = new Set(nodes.map(function (n) { return levels.get(n.id) || 0; })).size === 1;
    var geometry = flatOnly
      ? clusterGeometry(nodes, [], null)
      : null;
    var size = geometry
      ? {
        width: Math.max(1800, geometry.columns * geometry.cellWidth + 260),
        height: Math.max(1550, geometry.rows * geometry.cellHeight + 420),
      }
      : {
        width: wrapped
          ? BAND_MAX_WIDTH + 320
          : Math.max(1800, widestSingleRow + 260),
        height: Math.max(1550, 125 + rowCount * pitch + 420),
      };
    size.width = Math.round(size.width);
    size.height = Math.round(size.height);
    return size;
  }

  /* Kahn longest-path levels over directed prerequisite edges.  Cycle members
   * (and everything downstream of them) share the row past the deepest level. */
  function hierarchyLevels(nodes, edges) {
    var ids = new Set(nodes.map(function (node) { return node.id; }));
    var outgoing = new Map(nodes.map(function (node) { return [node.id, []]; }));
    var indegree = new Map(nodes.map(function (node) { return [node.id, 0]; }));
    var structural = new Set();

    (edges || []).forEach(function (edge) {
      var s = edge.s === undefined ? edge.source : edge.s;
      var t = edge.t === undefined ? edge.target : edge.t;
      var type = edge.type === undefined ? edge.relation_type : edge.type;
      if (type !== "prereq") return;
      if (edge.direction === "symmetric") return;
      if (!ids.has(s) || !ids.has(t) || s === t) return;
      outgoing.get(s).push(t);
      indegree.set(t, indegree.get(t) + 1);
      structural.add(s);
      structural.add(t);
    });
    outgoing.forEach(function (targets) { targets.sort(); });

    var levels = new Map(nodes.map(function (node) { return [node.id, 0]; }));
    var queue = Array.from(structural).filter(function (id) {
      return indegree.get(id) === 0;
    }).sort();
    var processed = new Set();

    while (queue.length) {
      var id = queue.shift();
      processed.add(id);
      (outgoing.get(id) || []).forEach(function (target) {
        levels.set(target, Math.max(levels.get(target), levels.get(id) + 1));
        indegree.set(target, indegree.get(target) - 1);
        if (indegree.get(target) === 0) queue.push(target);
      });
    }
    var cycleLevel = 0;
    processed.forEach(function (id) { cycleLevel = Math.max(cycleLevel, levels.get(id) + 1); });
    Array.from(structural).forEach(function (id) {
      if (!processed.has(id)) levels.set(id, cycleLevel);
    });
    return levels;
  }

  function neighbors(state, id) {
    var one = new Set();
    var two = new Set();
    state.edges.forEach(function (edge) {
      if (edge.s === id) one.add(edge.t);
      if (edge.t === id) one.add(edge.s);
    });
    one.forEach(function (a) {
      state.edges.forEach(function (edge) {
        var b = edge.s === a ? edge.t : edge.t === a ? edge.s : null;
        if (b && b !== id && !one.has(b)) two.add(b);
      });
    });
    return { one: one, two: two };
  }

  function nodeSafetyMargin(state, node, densityMap) {
    var d = (densityMap && densityMap.get(node.id)) || 0;
    return 12 + Math.min(28, d * 3.1 + (state.degreeCount.get(node.id) || 0) * 1.15);
  }

  function readabilityFloor(state, a, b, ux, uy, densityMap) {
    var fa = footprint(a);
    var fb = footprint(b);
    var aw = Math.max(fa.left, fa.right);
    var ah = Math.max(fa.top, fa.bottom);
    var bw = Math.max(fb.left, fb.right);
    var bh = Math.max(fb.top, fb.bottom);
    var ea = Math.abs(ux) * aw + Math.abs(uy) * ah;
    var eb = Math.abs(ux) * bw + Math.abs(uy) * bh;
    var margin = (nodeSafetyMargin(state, a, densityMap) + nodeSafetyMargin(state, b, densityMap)) * .55;
    return ea + eb + margin;
  }

  function desiredEdgeLength(state, edge, densityMap) {
    var a = state.byId.get(edge.s);
    var b = state.byId.get(edge.t);
    if (!a || !b) return 0;
    var dx = b.x - a.x;
    var dy = b.y - a.y;
    var dist = Math.max(1, dist2d(dx, dy));
    var ux = dx / dist;
    var uy = dy / dist;
    var semantic = ((a.size + b.size) * .48
      + baseGapForStrength(edge.strength) * layoutSpread(state)) * LAYOUT_SCALE;
    // Relation strength is a preference. Readability is a hard floor, and it is
    // deliberately the one thing LAYOUT_SCALE does not touch: it is a lower bound
    // set by how wide the labels are, so it cannot shrink by scaling the layout.
    return Math.max(semantic, readabilityFloor(state, a, b, ux, uy, densityMap));
  }

  function localDensityMap(state, active) {
    var map = new Map();
    active.forEach(function (a) {
      var density = (state.degreeCount.get(a.id) || 0) * .20;
      active.forEach(function (b) {
        if (a === b) return;
        var d = dist2d(a.x - b.x, a.y - b.y);
        if (d < 300) density += (1 - d / 300);
      });
      map.set(a.id, density);
    });
    return map;
  }

  /* Overlap can only happen between nodes whose footprints touch, which caps
   * their center distance at ~202px in x and ~151px in y. Bucketing nodes into
   * 240px cells and testing only the same and three forward neighbor cells keeps
   * each pass proportional to local crowding: a 192-node course must not spend
   * 125ms per tick in an O(n^2) sweep. */
  var PAIR_CELL = 240;

  function forEachNearPair(active, callback) {
    var buckets = new Map();
    active.forEach(function (n, index) {
      var key = Math.floor(n.x / PAIR_CELL) + ":" + Math.floor(n.y / PAIR_CELL);
      var bucket = buckets.get(key);
      if (!bucket) {
        bucket = [];
        buckets.set(key, bucket);
      }
      bucket.push(index);
    });
    var offsets = [[0, 1], [1, -1], [1, 0], [1, 1]];
    active.forEach(function (n, index) {
      var cx = Math.floor(n.x / PAIR_CELL);
      var cy = Math.floor(n.y / PAIR_CELL);
      var own = buckets.get(cx + ":" + cy) || [];
      own.forEach(function (other) {
        if (other > index) callback(index, other);
      });
      offsets.forEach(function (offset) {
        var bucket = buckets.get((cx + offset[0]) + ":" + (cy + offset[1]));
        if (bucket) bucket.forEach(function (other) { callback(index, other); });
      });
    });
  }

  function congestionStats(state, active, densityMap) {
    var pairs = 0;
    var maxOverlap = 0;
    forEachNearPair(active, function (i, j) {
      var a = active[i];
      var b = active[j];
      var fa = footprint(a);
      var fb = footprint(b);
      var ma = nodeSafetyMargin(state, a, densityMap) * .42;
      var mb = nodeSafetyMargin(state, b, densityMap) * .42;
      var ox = Math.min(a.x + fa.right + ma, b.x + fb.right + mb)
        - Math.max(a.x - fa.left - ma, b.x - fb.left - mb);
      var oy = Math.min(a.y + fa.bottom + ma, b.y + fb.bottom + mb)
        - Math.max(a.y - fa.top - ma, b.y - fb.top - mb);
      if (ox > 0 && oy > 0) {
        pairs += 1;
        maxOverlap = Math.max(maxOverlap, Math.min(ox, oy));
      }
    });
    return { pairs: pairs, maxOverlap: maxOverlap };
  }

  function movable(state, node) {
    return node.anchorX === null && (!state.graph.drag || state.graph.drag.id !== node.id);
  }

  /* Structure rows are held inside a hierarchy band. A vertical separation step
   * that the band would immediately undo can never resolve an overlap: the pair
   * and the band clamp trade the same few pixels forever. Those pairs are
   * separated sideways instead, where nothing pulls back. */
  function verticalShiftAllowed(state, node, delta) {
    if (state.graph.view !== "structure") return true;
    var guide = node.guideY === undefined || node.guideY === null ? node.y : node.guideY;
    var band = 42 + 8 * layoutSpread(state);
    return Math.abs(node.y + delta - guide) <= band + .5;
  }

  function resolveCongestion(state, active, densityMap, rounds) {
    for (var round = 0; round < rounds; round += 1) {
      var moved = false;
      // Positions change as pairs resolve, so the neighbor grid is rebuilt
      // every round; rebuilding is O(n), the pair work stays local.
      forEachNearPair(active, function (i, j) {
        var a = active[i];
        var b = active[j];
        var fa = footprint(a);
        var fb = footprint(b);
        var ma = nodeSafetyMargin(state, a, densityMap) * .42;
        var mb = nodeSafetyMargin(state, b, densityMap) * .42;
        var ox = Math.min(a.x + fa.right + ma, b.x + fb.right + mb)
          - Math.max(a.x - fa.left - ma, b.x - fb.left - mb);
        var oy = Math.min(a.y + fa.bottom + ma, b.y + fb.bottom + mb)
          - Math.max(a.y - fa.top - ma, b.y - fb.top - mb);
        if (ox <= 0 || oy <= 0) return;
        moved = true;
        var canA = movable(state, a);
        var canB = movable(state, b);
        if (!canA && !canB) return;
        var share = canA && canB ? .5 : 1;
        // Project along the cheaper axis, but use a real safety gap. This is
        // non-negotiable even at Gravity=100.
        var vertical = oy < ox;
        if (vertical) {
          var dy1 = (a.y <= b.y ? -1 : 1) * (oy + 5) * share;
          if (canA && !verticalShiftAllowed(state, a, dy1)) vertical = false;
          if (canB && !verticalShiftAllowed(state, b, -dy1)) vertical = false;
        }
        if (vertical) {
          var dirY = a.y <= b.y ? -1 : 1;
          var shiftY = (oy + 5) * share;
          if (canA) { a.y += dirY * shiftY; a.vy *= .25; }
          if (canB) { b.y -= dirY * shiftY; b.vy *= .25; }
        } else {
          var dirX = a.x <= b.x ? -1 : 1;
          var shiftX = (ox + 5) * share;
          if (canA) { a.x += dirX * shiftX; a.vx *= .25; }
          if (canB) { b.x -= dirX * shiftX; b.vx *= .25; }
        }
      });
      if (!moved) break;
    }
    return congestionStats(state, active, densityMap);
  }

  function layoutSpread(state) {
    return spreadFactor(state.graph.gravity) * state.graph.layoutInflation;
  }

  function clusterCenters(state) {
    var present = ["work", "review", "mastered", "new"].filter(function (key) {
      return state.nodes.some(function (n) { return n.visible && n.state === key; });
    });
    var out = new Map();
    var radius = 265 * layoutSpread(state);
    var center = state.center;
    present.forEach(function (key, index) {
      var angle = -Math.PI / 2 + index * TAU / Math.max(1, present.length);
      out.set(key, {
        x: center.x + Math.cos(angle) * radius,
        y: center.y + Math.sin(angle) * radius,
      });
    });
    return out;
  }

  function visibleEdges(state) {
    var hiddenTypes = state.graph.hiddenEdgeTypes;
    var hiddenIds = state.graph.hiddenEdgeIds;
    return state.edges.filter(function (edge) {
      if (hiddenTypes && hiddenTypes[edge.type]) return false;
      if (hiddenIds && hiddenIds.has(edge.id)) return false;
      var a = state.byId.get(edge.s);
      var b = state.byId.get(edge.t);
      return a && b && a.visible && b.visible;
    });
  }

  /* One pass over the visible edges builds the whole adjacency index; the old
   * per-node rescan made ordering and dispersion O(n*m) (192 nodes x 736
   * edges), which dominated the profile for large pools. */
  function neighborIndex(activeEdges) {
    var index = new Map();
    activeEdges.forEach(function (edge) {
      var weight = (NEIGHBOR_WEIGHT[edge.type] || .68) * (.72 + .62 * strength01(edge.strength));
      var from = index.get(edge.s);
      if (!from) {
        from = [];
        index.set(edge.s, from);
      }
      from.push({ id: edge.t, w: weight, edge: edge });
      var to = index.get(edge.t);
      if (!to) {
        to = [];
        index.set(edge.t, to);
      }
      to.push({ id: edge.s, w: weight, edge: edge });
    });
    return index;
  }

  function weightedNeighbors(state, id) {
    return neighborIndex(visibleEdges(state)).get(id) || [];
  }

  function structureOrdering(state, active) {
    var index = neighborIndex(visibleEdges(state));
    var levels = Array.from(new Set(active.map(function (n) { return n.level; })))
      .sort(function (a, b) { return a - b; });
    var groups = new Map(levels.map(function (level) {
      return [level, active.filter(function (n) { return n.level === level; })
        .sort(function (a, b) { return a.x - b.x; })];
    }));
    function rankMap() {
      var out = new Map();
      levels.forEach(function (level) {
        (groups.get(level) || []).forEach(function (n, i) { out.set(n.id, i); });
      });
      return out;
    }
    for (var pass = 0; pass < 4; pass += 1) {
      var rank = rankMap();
      levels.slice(1).forEach(function (level) {
        groups.get(level).sort(function (a, b) {
          function bary(n) {
            var sum = 0;
            var w = 0;
            (index.get(n.id) || []).forEach(function (x) {
              var o = state.byId.get(x.id);
              if (!o || o.level >= level || !rank.has(o.id)) return;
              sum += rank.get(o.id) * x.w;
              w += x.w;
            });
            return w ? sum / w : rank.get(n.id);
          }
          return bary(a) - bary(b) || a.x - b.x;
        });
      });
      rank = rankMap();
      levels.slice(0, -1).reverse().forEach(function (level) {
        groups.get(level).sort(function (a, b) {
          function bary(n) {
            var sum = 0;
            var w = 0;
            (index.get(n.id) || []).forEach(function (x) {
              var o = state.byId.get(x.id);
              if (!o || o.level <= level || !rank.has(o.id)) return;
              sum += rank.get(o.id) * x.w;
              w += x.w;
            });
            return w ? sum / w : rank.get(n.id);
          }
          return bary(a) - bary(b) || a.x - b.x;
        });
      });
    }
    return { levels: levels, groups: groups };
  }

  function recomputeLayoutGuides(state) {
    var active = state.nodes.filter(function (n) { return n.visible; });
    if (!active.length) return;
    var center = state.center;
    var spread = layoutSpread(state);

    if (state.graph.view === "structure") {
      var ordered = structureOrdering(state, active);
      // Flat pool (no directed relation, one level, many points): a ribbon cannot
      // hold it, so the points cluster in two dimensions. Same footprint spacing,
      // only the arrangement changes.
      var geometry = clusterGeometry(active, visibleEdges(state), center);
      if (geometry) {
        var cluster = active.slice().sort(function (a, b) {
          return (b.targetSize - a.targetSize)
            || String(a.id).localeCompare(String(b.id));
        });
        cluster.forEach(function (n, index) {
          var cell = clusterCellCenter(geometry, index);
          n.guideX = cell.x;
          n.guideY = cell.y;
          n.rowIndex = Math.floor(index / geometry.columns);
        });
        return;
      }
      // Structure guides follow gravity only. Layout inflation must not move
      // them: the stage is sized from these same numbers, and a guide grid that
      // grows past its stage can only be answered by boundary clamping, which
      // feeds congestion the resolver can never finish clearing.
      var structureSpread = spreadFactor(state.graph.gravity);
      var gap = 64 + 38 * structureSpread;
      var pitch = 155 * structureSpread;
      var rowIndex = 0;
      ordered.levels.forEach(function (level) {
        var group = ordered.groups.get(level) || [];
        var widths = group.map(function (n) {
          return Math.max(labelWidth(n.shortTitle || n.title), n.targetSize + 34);
        });
        var bandWidths = group.map(function (n) {
          return Math.max(labelWidth(n.shortTitle || n.title), 96);
        });
        bandRows(bandWidths, gap).forEach(function (indexes) {
          var total = 0;
          indexes.forEach(function (i, k) { total += widths[i] + (k ? gap : 0); });
          var cursor = center.x - total / 2;
          indexes.forEach(function (i) {
            var n = group[i];
            n.guideX = cursor + widths[i] / 2;
            cursor += widths[i] + gap;
            n.guideY = 125 + rowIndex * pitch;
            n.rowIndex = rowIndex;
          });
          rowIndex += 1;
        });
      });
      return;
    }

    if (state.graph.view === "state") {
      var clusters = clusterCenters(state);
      var stateGroups = new Map();
      active.forEach(function (n) {
        if (!stateGroups.has(n.state)) stateGroups.set(n.state, []);
        stateGroups.get(n.state).push(n);
      });
      stateGroups.forEach(function (group, key) {
        group.sort(function (a, b) { return a.x - b.x || String(a.id).localeCompare(String(b.id)); });
        var c = clusters.get(key);
        if (!c) return;
        var ring = 58 + Math.sqrt(group.length) * 29 * spread;
        group.forEach(function (n, i) {
          var angle = i * PHI - Math.PI / 2;
          var scale = i ? 1 : 0;
          n.guideX = c.x + Math.cos(angle) * ring * scale;
          n.guideY = c.y + Math.sin(angle) * ring * scale;
        });
      });
      return;
    }

    // Metric projections keep the current topology/mental map, but stronger
    // metric nodes prefer the center.
    active.forEach(function (n, i) {
      var score = state.scoreFor(n);
      var dx = n.x - center.x;
      var dy = n.y - center.y;
      var dist = Math.max(1, dist2d(dx, dy));
      var ux = dx / dist;
      var uy = dy / dist;
      if (dist < 40) {
        var angle = i * PHI;
        ux = Math.cos(angle);
        uy = Math.sin(angle);
      }
      var targetR = (150 + (1 - score) * 450) * spread;
      n.guideX = center.x + ux * targetR;
      n.guideY = center.y + uy * targetR;
    });
  }

  function applyAngularDispersion(state, active, index, alpha) {
    active.forEach(function (hub) {
      var list = (index.get(hub.id) || [])
        .map(function (x) { return state.byId.get(x.id); })
        .filter(function (n) { return n && n.visible; });
      if (list.length < 3) return;
      var entries = list.map(function (n) {
        return { n: n, angle: Math.atan2(n.y - hub.y, n.x - hub.x) };
      }).sort(function (a, b) { return a.angle - b.angle; });
      var minGap = Math.min(.62, TAU / list.length * .68);
      for (var i = 0; i < entries.length; i += 1) {
        var a = entries[i];
        var b = entries[(i + 1) % entries.length];
        var gap = b.angle - a.angle;
        if (i === entries.length - 1) gap += TAU;
        if (gap >= minGap) continue;
        var push = (minGap - gap) * .42 * alpha;
        var ta = { x: -Math.sin(a.angle), y: Math.cos(a.angle) };
        var tb = { x: -Math.sin(b.angle), y: Math.cos(b.angle) };
        if (movable(state, a.n)) { a.n.vx -= ta.x * push; a.n.vy -= ta.y * push; }
        if (movable(state, b.n)) { b.n.vx += tb.x * push; b.n.vy += tb.y * push; }
      }
    });
  }

  function equalizeSpatialDensity(state, active, densityMap, alpha) {
    active.forEach(function (n) {
      if (!movable(state, n)) return;
      var crowd = densityMap.get(n.id) || 0;
      if (crowd < 2.2) return;
      var cx = 0;
      var cy = 0;
      var w = 0;
      var count = 0;
      active.forEach(function (o) {
        if (o === n) return;
        var d = dist2d(n.x - o.x, n.y - o.y);
        if (d >= 270) return;
        var ww = Math.pow(1 - d / 270, 1.35);
        cx += o.x * ww;
        cy += o.y * ww;
        w += ww;
        count += 1;
      });
      if (w < .01 || count < 2) return;
      cx /= w;
      cy /= w;
      var dx = n.x - cx;
      var dy = n.y - cy;
      var dist = Math.max(1, dist2d(dx, dy));
      var push = Math.min(.52, (crowd - 2.1) * .052) * alpha;
      n.vx += dx / dist * push;
      n.vy += dy / dist * push;
    });
  }

  function edgeCorridorRepulsion(state, active, activeEdges, densityMap, alpha) {
    // Keep unrelated nodes/labels out of busy edge corridors. This is soft: it
    // improves legibility without pretending edge crossings can always vanish.
    activeEdges.forEach(function (edge) {
      var a = state.byId.get(edge.s);
      var b = state.byId.get(edge.t);
      var dx = b.x - a.x;
      var dy = b.y - a.y;
      var l2 = dx * dx + dy * dy;
      if (l2 < 400) return;
      active.forEach(function (n) {
        if (n === a || n === b || !movable(state, n)) return;
        var t = ((n.x - a.x) * dx + (n.y - a.y) * dy) / l2;
        if (t < .12 || t > .88) return;
        t = Math.max(0, Math.min(1, t));
        var qx = a.x + t * dx;
        var qy = a.y + t * dy;
        var px = n.x - qx;
        var py = n.y - qy;
        var dist = Math.max(1, dist2d(px, py));
        var corridor = Math.min(72, 20 + n.size * .38 + nodeSafetyMargin(state, n, densityMap) * .45);
        if (dist >= corridor) return;
        var push = (corridor - dist) / corridor * .34 * alpha;
        n.vx += px / dist * push;
        n.vy += py / dist * push;
      });
    });
  }

  /* -------------------------------------------------------- Barnes-Hut --- */
  /* Obsidian 1.14.4 的电荷律（wasm visitCharge）：远场按 quad 质心折叠成点电荷，
   *   判据 d2 >= size2 / theta²，theta = 0.9；
   *   近场（d < sqrt(30)）用 distanceMin2 做软下限，避免 d -> 0 时力发散。
   * 实测口径（tools/charge-probe.js）：d >= 121 时与解析式 strength/d² 比值 1.0000。
   * 这里只取远场解析式——近场另有 readabilityFloor 与 congestion 兜底，
   * 官方那段近场增益来自其四叉树内部聚合路径，不是可推导的力律。
   * S 标定：BH 的 |Δv| = S/d（Δ 是向量，故除 d² 后仍带一个 d），旧式的 |Δv| = 11200/d²,
   * 两者在 d = 224（实测典型点距）处相等 → S = 11200/224 = 50。
   * 实测（tools/calibrate-bh-strength.js，dmath 31 点）：S=50 给出平均边长 497、
   * bbox 1099×837、各向异性 1.49、103 tick 收敛，与旧式的 494 / 1045×842 / 1.46 / 103
   * 逐项吻合，故这一步是纯实现替换：O(n²) → O(n log n)，观感不变。
   * 想真正采用 Obsidian 的量级（其 UI 默认 repel = 10³）需要先把舞台从"约束"
   * 降级为"结算后外接框"，否则自由力场会被边界钳制顶在墙上。 */
  var BH_THETA = .9;
  var BH_DISTANCE_MIN2 = 30;
  // Obsidian's own numbers are linkDistance 250, repelStrength -1000, collideRadius
  // 60 — all three in one pixel scale, the one its graph actually settles at. Our
  // points rest about 500 apart, k = 2 of that, and the charge has to follow the
  // scale it is balancing against. A relation's strength sets linkDistance per edge,
  // so the scale is also per edge; BH_STRENGTH is the value that holds for the
  // dmath spread and is re-tuned with tools/calibrate-bh-strength.js.
  // Obsidian ships linkDistance 250 and repelStrength 1000, and its graph settles at
  // a few times the first of those. At the semantic distance our relations ask for
  // (~500) 31 points came out at 5529x6036 — three times the stage, past what
  // graphFit can pull back, since its scale floor is .38. LAYOUT_SCALE brings the
  // physics distance back to Obsidian's own absolute value, which is what makes the
  // graph roughly the size Obsidian's own would be at this point count.
  var LAYOUT_SCALE = .28;
  // Obsidian's own numbers are linkDistance 250, repelStrength -1000, collideRadius
  // 60 — all three in one pixel scale. BH_STRENGTH has to hold Obsidian's ratio to
  // linkDistance (1000 at 250, so 0.016 * L^2) or the graph either collapses or
  // spreads without bound; at L = 275 that is about 1200.
  var BH_STRENGTH = 314;
  // d3 forceLink's linkStrength. Obsidian ships 1.
  var LINK_STRENGTH = 1;
  // Obsidian's cooldown: alpha += (alphaTarget - alpha) * (1 - 0.001^(1/300)).
  // Its alphaTarget is 0 and so is ours, so this is the same shape the old
  // alpha *= .962 already had — only the rate differs, and the slower one is better
  // on both axes that matter (tools/sweep-alpha-rate.js):
  //   dmath  travel 43 -> 53px, per-frame p50 0.26 -> 0.19, p95 3.57 -> 3.23
  //   c02    travel 81 -> 101px, per-frame p50 0.55 -> 0.40, p95 5.62 -> 5.50
  // Cost: settle 103 -> 164 ticks, about 1.7s -> 2.7s at 60fps.
  var ALPHA_DECAY = 1 - Math.pow(0.001, 1 / 300);
  // Obsidian's complete() uses 0.6; the old integrator used .81 with a hard 7px/tick
  // clamp on top. The clamp is gone, so this is now the only limiter.
  var VELOCITY_DECAY = .6;

  function bhBuild(nodes) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    var i, n;
    for (i = 0; i < nodes.length; i += 1) {
      n = nodes[i];
      // Collide takes each pair once, from the lower index, so both sides agree on
      // which of them owns the pair and the impulse is applied exactly once.
      n.__idx = i;
      if (n.x < x0) x0 = n.x;
      if (n.x > x1) x1 = n.x;
      if (n.y < y0) y0 = n.y;
      if (n.y > y1) y1 = n.y;
    }
    var root = {
      x0: x0, y0: y0, x1: x1, y1: y1,
      leaf: null, bucket: null, kids: null,
      cx: 0, cy: 0, value: 0,
    };
    if (!nodes.length) return root;

    function makeChild(px0, py0, px1, py1, fig) {
      var mx = (px0 + px1) / 2, my = (py0 + py1) / 2;
      var c = { leaf: null, bucket: null, kids: null, cx: 0, cy: 0, value: 0 };
      if (fig === 0) { c.x0 = px0; c.y0 = py0; c.x1 = mx; c.y1 = my; }
      else if (fig === 1) { c.x0 = mx; c.y0 = py0; c.x1 = px1; c.y1 = my; }
      else if (fig === 2) { c.x0 = px0; c.y0 = my; c.x1 = mx; c.y1 = py1; }
      else { c.x0 = mx; c.y0 = my; c.x1 = px1; c.y1 = py1; }
      return c;
    }

    for (i = 0; i < nodes.length; i += 1) {
      n = nodes[i];
      var node = root;
      var px0 = root.x0, py0 = root.y0, px1 = root.x1, py1 = root.y1;
      for (;;) {
        var mx = (px0 + px1) / 2, my = (py0 + py1) / 2;
        var ax = n.x >= mx ? 1 : 0, ay = n.y >= my ? 1 : 0;
        var fig = (ax << 1) | ay;
        if (node.leaf || node.bucket) {
          var other = node.leaf || node.bucket[0];
          if (n.x === other.x && n.y === other.y) {
            // 完全重合：顺链挂同一格，避免无限下钻
            if (node.leaf) { node.bucket = [node.leaf, n]; node.leaf = null; }
            else node.bucket.push(n);
            break;
          }
          node.kids = [null, null, null, null];
          var prev = node.leaf ? [node.leaf] : node.bucket.slice();
          node.leaf = null; node.bucket = null;
          for (var p = 0; p < prev.length; p += 1) {
            var q = prev[p];
            var pmx = (px0 + px1) / 2, pmy = (py0 + py1) / 2;
            var pf = ((q.x >= pmx ? 1 : 0) << 1) | (q.y >= pmy ? 1 : 0);
            var child = makeChild(px0, py0, px1, py1, pf);
            child.leaf = q;
            node.kids[pf] = child;
          }
        }
        if (!node.kids) { node.leaf = n; break; }
        if (!node.kids[fig]) node.kids[fig] = makeChild(px0, py0, px1, py1, fig);
        node = node.kids[fig];
        if (ax) px0 = mx; else px1 = mx;
        if (ay) py0 = my; else py1 = my;
      }
    }

    // 自底向上汇总质心与电荷和；包围盒取子节点并集（叶子收紧到点）。
    // 少了收紧这一步，远场判据会误判，斥力被系统性放大。
    (function accumulate(node) {
      var x0i = Infinity, y0i = Infinity, x1i = -Infinity, y1i = -Infinity;
      if (node.leaf || node.bucket) {
        var list = node.bucket || [node.leaf];
        var v = 0, cx = 0, cy = 0;
        for (var k = 0; k < list.length; k += 1) {
          var e = list[k];
          v += 1; cx += e.x; cy += e.y;
          if (e.x < x0i) x0i = e.x;
          if (e.x > x1i) x1i = e.x;
          if (e.y < y0i) y0i = e.y;
          if (e.y > y1i) y1i = e.y;
        }
        node.value = v; node.cx = cx / v; node.cy = cy / v;
        node.x0 = x0i; node.y0 = y0i; node.x1 = x1i; node.y1 = y1i;
        return;
      }
      var vv = 0, ccx = 0, ccy = 0;
      for (var j = 0; j < 4; j += 1) {
        var kid = node.kids[j];
        if (!kid) continue;
        accumulate(kid);
        vv += kid.value;
        ccx += kid.cx * kid.value;
        ccy += kid.cy * kid.value;
        if (kid.x0 < x0i) x0i = kid.x0;
        if (kid.y0 < y0i) y0i = kid.y0;
        if (kid.x1 > x1i) x1i = kid.x1;
        if (kid.y1 > y1i) y1i = kid.y1;
      }
      node.value = vv;
      node.x0 = x0i; node.y0 = y0i; node.x1 = x1i; node.y1 = y1i;
      if (vv) { node.cx = ccx / vv; node.cy = ccy / vv; }
    })(root);
    return root;
  }

  function bhApply(root, node, strength) {
    var theta2 = BH_THETA * BH_THETA;
    (function walk(tree) {
      if (!tree.value) return;
      if (tree.leaf || tree.bucket) {
        var list = tree.bucket || [tree.leaf];
        for (var k = 0; k < list.length; k += 1) {
          var o = list[k];
          if (o === node) continue;
          var ddx = o.x - node.x, ddy = o.y - node.y;
          var dd2 = ddx * ddx + ddy * ddy;
          if (dd2 === 0) continue;
          if (ddx === 0) ddx = 1e-6;
          if (ddy === 0) ddy = 1e-6;
          var denom = dd2 < BH_DISTANCE_MIN2 ? Math.sqrt(dd2 * BH_DISTANCE_MIN2) : dd2;
          var kk = strength / denom;
          node.vx += ddx * kk;
          node.vy += ddy * kk;
        }
        return;
      }
      var dx = tree.cx - node.x, dy = tree.cy - node.y;
      var d2 = dx * dx + dy * dy;
      var span = Math.max(tree.x1 - tree.x0, tree.y1 - tree.y0);
      if (d2 * theta2 >= span * span) {
        if (d2 === 0) return;
        var den = d2 < BH_DISTANCE_MIN2 ? Math.sqrt(d2 * BH_DISTANCE_MIN2) : d2;
        var gain = (strength * tree.value) / den;
        node.vx += dx * gain;
        node.vy += dy * gain;
        return;
      }
      for (var j = 0; j < 4; j += 1) if (tree.kids[j]) walk(tree.kids[j]);
    })(root);
  }

  var BH_COLLIDE_DV = .25;
  // Obsidian's default centerStrength. See the comment at its use site.
  var CENTER_STRENGTH = .1;
  // Obsidian's alphaInit. This matters more than it looks like it should: alpha scales
  // every force, so starting at 1 instead of .3 makes the first frame's forces 3.3x the
  // reference's. With the centre force at full measured strength that put a 325px jump
  // into the first frame — the same class of teleport the guide seed was fixed for.
  var ALPHA_INIT = .3;

  /* Upper bound on collideRadius, used only to prune subtrees during the collide
   * walk. Keeping it generous costs a few extra descents; keeping it too tight would
   * silently drop real contacts. */
  var BH_COLLIDE_MAX_R = 220;

  /* Collide, Obsidian's shape. Walks the same tree the charge uses; a subtree is
   * skipped when its centre is further than the pair radius plus the subtree's own
   * span, which only prunes pairs that provably cannot touch. dv = 0.25 * (R - d) —
   * no division by d, so a fully overlapping pair gets a finite kick instead of an
   * unbounded one, and no alpha term, so colliding does not fade as the solve cools.
   * Each pair is taken once, from the lower index. */
  function bhCollide(root, node) {
    var rNode = collideRadius(node);
    var cx = node.x + node.vx, cy = node.y + node.vy;
    (function walk(tree) {
      if (!tree.value) return;
      if (tree.leaf || tree.bucket) {
        var list = tree.bucket || [tree.leaf];
        for (var k = 0; k < list.length; k += 1) {
          var o = list[k];
          if (o === node) continue;
          if (o.__idx <= node.__idx) continue;
          var twoR = rNode + collideRadius(o);
          var dx = (o.x + o.vx) - cx, dy = (o.y + o.vy) - cy;
          var d2 = dx * dx + dy * dy;
          if (!(d2 < twoR * twoR)) continue;
          var d = Math.sqrt(d2) || 1e-6;
          var ux = dx / d, uy = dy / d;
          var dv = BH_COLLIDE_DV * (twoR - d);
          node.vx -= ux * dv;
          node.vy -= uy * dv;
          o.vx += ux * dv;
          o.vy += uy * dv;
        }
        return;
      }
      var mx = tree.cx - cx, my = tree.cy - cy;
      var span = Math.max(tree.x1 - tree.x0, tree.y1 - tree.y0);
      if (Math.sqrt(mx * mx + my * my) - span > rNode + BH_COLLIDE_MAX_R) return;
      for (var j = 0; j < 4; j += 1) if (tree.kids[j]) walk(tree.kids[j]);
    })(root);
  }

  /* Radius the collision impulse works from, per node. Obsidian's number is a flat
   * 60, and that is the honest value *for its dots* — it draws a node as a small
   * circle and lets labels overlap. Our nodes carry their label in their footprint,
   * so the faithful port of "60" is the node's own footprint, not the constant.
   * The constant was also too small to reach the readability floor: with 2R = 120
   * against a floor near 150, collide settled every graph at a 120px minimum pair
   * distance and the floor could never be met, which is what kept overlaps on screen.
   * Reading the node radius instead lets a wide label claim the room it needs. */
  function collideRadius(node) {
    var fp = footprint(node);
    var halfW = (fp.left + fp.right) / 2;
    var halfH = (fp.top + fp.bottom) / 2;
    // Half the diagonal of the footprint: a circle that covers the label box, so two
    // nodes are pushed apart until their boxes clear rather than until their circles do.
    return Math.sqrt(halfW * halfW + halfH * halfH);
  }
  /* The seat is still the guide grid. With the bands and the resolver gone nothing
   * holds the points there once the solve starts, so it is only a starting frame —
   * but it is a well-spread one, and the graph then opens out of it into whatever
   * the free force field settles on. That is where the visible growth comes from:
   * measured travel went from 53px to 1195px when the guides stopped being a
   * destination and became a departure point.
   * A contracted seat still does not work, for the original reason — the guide grid
   * already sits on the readability floor, so contracting it creates the overlaps
   * that resolveCongestion used to shove apart at 593.8px (uniform 0.7) and 615.4px
   * (y-only 0.55) on the first frame. */
  var SEED_CONTRACTION_Y = 1;

  function enforceHierarchyBands(state, active) {
    if (state.graph.view !== "structure") return;
    // The band tightens as the solve cools. A contracted seat puts every point up
    // to 0.3 * half-spread away from its own guide (116px on dmath, ~156px on
    // c02); holding those to the final 49px band on frame one is exactly the
    // 953px snap this replaced. Wide while alpha is high, exact once it is gone.
    var band = (42 + 8 * layoutSpread(state)) * (1 + 4 * state.graph.alpha);
    active.forEach(function (n) {
      if (!movable(state, n)) return;
      var dy = n.y - n.guideY;
      if (Math.abs(dy) > band) n.y = n.guideY + Math.sign(dy) * band;
    });
  }

  function tickPhysics(state) {
    var graph = state.graph;
    if (graph.alpha <= 0) return;
    var active = state.nodes.filter(function (n) { return n.visible; });
    var alpha = graph.alpha;
    var activeEdges = visibleEdges(state);
    var densityMap = localDensityMap(state, active);
    graph.solveStep += 1;
    if (graph.solveStep % 12 === 1 && alpha > .14) recomputeLayoutGuides(state);

    // d3 forceLink, the form Obsidian runs. Four things it does that the previous
    // spring did not:
    //   · no dead zone — every link pulls every tick, so a resting layout is still
    //     being held rather than drifting until the gap passes a threshold
    //   · the error is relative, divided by the current distance, so what is applied
    //     is |d - linkDistance| * alpha * linkStrength / min(count)
    //   · k is divided by min(count) of the two ends, so a hub cannot yank a leaf
    //   · the split follows count_s / (count_s + count_t) instead of an even half
    // It also reads positions as (pos + vel), so the force acts on where the node is
    // going rather than where it is, which is what removes the last-frame overshoot.
    // linkDistance stays lesson-kit's own: a relation's strength asks for a distance,
    // and Obsidian has no equivalent of that. The law around it is now d3's.
    activeEdges.forEach(function (edge) {
      var a = state.byId.get(edge.s);
      var b = state.byId.get(edge.t);
      var countA = Math.max(1, state.degreeCount.get(a.id) || 1);
      var countB = Math.max(1, state.degreeCount.get(b.id) || 1);
      var k = alpha * LINK_STRENGTH / Math.min(countA, countB);
      var dx = (b.x + b.vx) - (a.x + a.vx);
      var dy = (b.y + b.vy) - (a.y + a.vy);
      var d = Math.max(1, dist2d(dx, dy));
      var f = (d - desiredEdgeLength(state, edge, densityMap)) / d * k;
      var w = countA / (countA + countB);
      if (movable(state, b)) { b.vx -= dx * f * w; b.vy -= dy * f * w; }
      if (movable(state, a)) { a.vx += dx * f * (1 - w); a.vy += dy * f * (1 - w); }
    });

    // Charge becomes Barnes-Hut (Obsidian's visitCharge): one quadtree per tick,
    // distant subtrees fold into a single point charge. Same far-field magnitude
    // as the old min(1.18, 11200/d^2) — it was already 11200/d^2 above d = 97 —
    // but the hard cap that made the near field non-physical is gone, and the
    // cost drops from every pair to n log n.
    var chargeTree = bhBuild(active);
    var chargeStrength = -BH_STRENGTH * alpha * (.74 + .20 * layoutSpread(state));
    active.forEach(function (n) {
      if (movable(state, n)) bhApply(chargeTree, n, chargeStrength);
    });

    // Collide, Obsidian's: dv = 0.25 * (120 - d), alpha-independent, and not divided
    // by d, so a fully overlapping pair gets 30 rather than an unbounded kick. It is
    // the only thing keeping nodes apart now — there is no readability floor pushing
    // them and no congestion resolver shoving them, and Obsidian's graph does let
    // labels overlap rather than pay for legibility with a hard constraint.
    active.forEach(function (n) {
      if (movable(state, n)) bhCollide(chargeTree, n);
    });

    // A big pool keeps every hard constraint on every tick, but the purely
    // cosmetic spacing passes run on a rota: their frames average out and the
    // settle stays interactive instead of turning into a minutes-long freeze.
    var largePool = active.length > 120;
    applyAngularDispersion(state, active, neighborIndex(activeEdges), alpha);
    if (!largePool || graph.solveStep % 2 === 0) {
      equalizeSpatialDensity(state, active, densityMap, alpha);
    }
    if (!largePool || graph.solveStep % 3 === 0) {
      edgeCorridorRepulsion(state, active, activeEdges, densityMap, alpha);
    }

    var center = state.center;
    var spread = layoutSpread(state);
    active.forEach(function (n) {
      if (graph.drag && graph.drag.id === n.id) return;
      if (n.anchorX !== null) {
        n.vx += (n.anchorX - n.x) * .052 * alpha;
        n.vy += (n.anchorY - n.y) * .052 * alpha;
      } else {
        var gx = n.guideX === undefined || n.guideX === null ? n.x : n.guideX;
        var gy = n.guideY === undefined || n.guideY === null ? n.y : n.guideY;
        if (graph.view === "structure") {
          // No guide force. Obsidian's graph has no rows to sit in: the link springs
          // set the extent (charge pushes out, springs pull in, equilibrium lands at
          // a few times linkDistance) and the only positional anchor is the weak
          // centring below, which exists to stop the whole graph translating, not to
          // shape it. Pulling y onto a guide grid is what made every extra unit of
          // charge widen the graph instead of spreading it.
        } else if (graph.view === "state") {
          n.vx += (gx - n.x) * .015 * alpha;
          n.vy += (gy - n.y) * .015 * alpha;
          n.vy += (125 + rowIndexOf(n) * 155 * spread - n.y) * .0017 * alpha;
        } else {
          n.vx += (gx - n.x) * .010 * alpha;
          n.vy += (gy - n.y) * .010 * alpha;
          n.vy += (125 + rowIndexOf(n) * 155 * spread - n.y) * .0028 * alpha;
        }
      }
      // Obsidian's centring force. Measured in isolation against its own module: the
      // velocity change is -pos * alpha * centerStrength, coefficient exactly 1.0, and
      // the default centerStrength is 0.1. Ours was 0.00025, four hundred times weaker,
      // and that is the whole reason an unlinked point drifts out of the picture: it
      // has no spring holding it to anything, so the only force pointing inward was set
      // to a four-hundredth of what the reference uses. At 0.1 an unlinked point settles
      // well inside the cluster instead of outside it.
      // Note this fades with alpha exactly as the reference does, so it steers the point
      // during the solve and then stops; the position it reached is what stays.
      n.vx += (center.x - n.x) * CENTER_STRENGTH * alpha;
      n.vy += (center.y - n.y) * CENTER_STRENGTH * alpha;
      // Obsidian's complete(x, y, 0.6): damp, then integrate. No velocity clamp —
      // the damping is the limiter, and it is what caps per-frame motion instead of
      // a cutoff that leaves the fastest nodes pinned at the ceiling.
      n.vx *= VELOCITY_DECAY;
      n.vy *= VELOCITY_DECAY;
      n.x += n.vx;
      n.y += n.vy;
    });

    // Hierarchy bands and the congestion resolver are both gone. They were the two
    // hard positional writers, and between them they were what made the layout a row
    // grid no matter which force law ran underneath: the band pinned y to guideY
    // +/- 49, and the resolver shoved pairs apart after every tick. Obsidian has
    // neither. What holds the graph apart now is collide, and what holds it together
    // is the link springs, so the layout is whatever those two settle on.
    // The cost is real and is Obsidian's own: labels can overlap.

    // If the logical area is still under pressure, expand the layout footprint
    // and let Fit zoom out. Never respond by shrinking the readability floor.
    if (false && graph.solveStep % 10 === 0) {
      var pressure = 0;
      var target = 1;
      graph.layoutInflation += (target - graph.layoutInflation) * (pressure > 0 ? .24 : .07);
      graph.layoutInflation = Math.max(1, Math.min(1.50, graph.layoutInflation));
      if (Math.abs(target - graph.layoutInflation) > .008) recomputeLayoutGuides(state);
    }

    // The stage is no longer a wall. Measured on real data, a free force field
    // pins against it instead of finding its own extent: growing the charge 56x
    // (strength 200 -> 11200) moved the mean edge only 638 -> 758 and left the
    // bounding box at 1636 against a usable width of 1560 — the clamp, not the
    // physics, was deciding the layout. Nothing needs the wall: graphFit() fits
    // the node extent rather than the stage box, and .graph-edges is
    // overflow: visible, so a node outside the stage still draws.
    // state.stageWidth/stageHeight now only place the centre and size the DOM box.

    var avg = 0;
    active.forEach(function (n) { avg += dist2d(n.vx, n.vy); });
    avg /= Math.max(1, active.length);
    var finalStats = congestionStats(state, active, densityMap);
    graph.alpha += (0 - graph.alpha) * ALPHA_DECAY;
    if (finalStats.pairs === 0 && graph.alpha < .032 && avg < .075) graph.stableFrames += 1;
    else graph.stableFrames = 0;
    // Safety valve: forces have faded (alpha < .01) and the resolver has had
    // two more seconds of rounds; finish even if a residual overlap survives,
    // so an impossible packing can never spin the solver forever.
    if (graph.alpha < .01) graph.settleWatch = (graph.settleWatch || 0) + 1;
    else graph.settleWatch = 0;
    if (graph.settleWatch > 120) graph.stableFrames = 15;
    if (graph.stableFrames > 14) {
      // No cleanup projection. Obsidian ends on the forces alone: it stops when
      // alpha runs out, and whatever the layout looks like then is the layout.
      graph.alpha = 0;
      active.forEach(function (n) { n.vx = 0; n.vy = 0; });
      graph.settled = true;
    }
  }

  function reheat(state, alpha, autoFit) {
    state.graph.alpha = Math.max(state.graph.alpha, alpha === undefined ? .9 : alpha);
    state.graph.stableFrames = 0;
    state.graph.settleWatch = 0;
    state.graph.solveStep = 0;
    state.graph.layoutInflation = Math.max(1, state.graph.layoutInflation * .94);
    state.graph.autoFitAfterSettle = autoFit === undefined ? true : autoFit;
    state.graph.settled = false;
    recomputeLayoutGuides(state);
  }

  /* Ports: incident edges are grouped by angle and get evenly spaced slots so
   * adjacent edges do not all leave from the same point. */
  function computePortSlots(state, activeEdges) {
    var map = new Map();
    var incident = new Map(state.nodes.map(function (n) { return [n.id, []]; }));
    activeEdges.forEach(function (edge) {
      var a = state.byId.get(edge.s);
      var b = state.byId.get(edge.t);
      if (!a.visible || !b.visible) return;
      incident.get(a.id).push({ edge: edge, angle: Math.atan2(b.y - a.y, b.x - a.x) });
      incident.get(b.id).push({ edge: edge, angle: Math.atan2(a.y - b.y, a.x - b.x) });
    });
    incident.forEach(function (rawList, nodeId) {
      if (!rawList.length) return;
      var list = rawList.slice().sort(function (a, b) { return a.angle - b.angle; });
      if (list.length > 1) {
        var cut = 0;
        var maxGap = -1;
        for (var i = 0; i < list.length; i += 1) {
          var gap = list[(i + 1) % list.length].angle - list[i].angle;
          if (i === list.length - 1) gap += TAU;
          if (gap > maxGap) { maxGap = gap; cut = i + 1; }
        }
        list = list.slice(cut).concat(list.slice(0, cut));
      }
      var groups = [];
      var group = [list[0]];
      for (var k = 1; k < list.length; k += 1) {
        var gap2 = list[k].angle - list[k - 1].angle;
        if (gap2 < 0) gap2 += TAU;
        if (gap2 < .78) group.push(list[k]);
        else { groups.push(group); group = [list[k]]; }
      }
      groups.push(group);
      groups.forEach(function (g) {
        var mid = (g.length - 1) / 2;
        g.forEach(function (item, i) {
          map.set(item.edge.index + "|" + nodeId, {
            slot: i - mid, count: g.length, angle: item.angle,
          });
        });
      });
    });
    state.portSlots = map;
    return map;
  }

  function edgeStyle(edge) {
    var score = strength01(edge.strength);
    return { width: 1.05 + score * 2.35, baseOpacity: .15 + score * .43 };
  }

  function edgePath(state, edge) {
    var a = state.byId.get(edge.s);
    var b = state.byId.get(edge.t);
    var baseAB = Math.atan2(b.y - a.y, b.x - a.x);
    var sa = state.portSlots.get(edge.index + "|" + a.id) || { slot: 0, count: 1, angle: baseAB };
    var sb = state.portSlots.get(edge.index + "|" + b.id) || { slot: 0, count: 1, angle: baseAB + Math.PI };
    var ra = a.size / 2 + 2;
    var rb = b.size / 2 + 2;
    var ga = Math.min(12, 5 + a.size * .06);
    var gb = Math.min(12, 5 + b.size * .06);
    // +10/+11 used to sit the endpoint outside the ring, leaving a gap at both ends
    // that read as the edge failing to reach its node. +2 sits it on the ring.
    // The port spread is an arc along the boundary, not a sideways shift. A tangential
    // shift leaves the circle: at slot 4 on a 57-unit node the endpoint landed 16 units
    // outside the ring and 50 degrees away from the direction it was meant to leave in,
    // so the line both missed the node and aimed at the wrong place. Dividing the arc
    // by the radius converts it to the equivalent angle, which keeps the endpoint on
    // the ring and keeps the fan converging toward the far node.
    var angA = sa.angle + (sa.slot * ga) / Math.max(1, ra);
    var angB = sb.angle + (sb.slot * gb) / Math.max(1, rb);
    var ua = { x: Math.cos(angA), y: Math.sin(angA) };
    var ub = { x: Math.cos(angB), y: Math.sin(angB) };
    var x1 = a.x + ua.x * ra;
    var y1 = a.y + ua.y * ra;
    var x2 = b.x + ub.x * rb;
    var y2 = b.y + ub.y * rb;
    var dx = x2 - x1;
    var dy = y2 - y1;
    var len = Math.max(1, dist2d(dx, dy));
    var px = -dy / len;
    var py = dx / len;
    var base = edge.type === "related" ? 18 : edge.type === "contrast" ? -20 : edge.type === "apply" ? 14 : 0;
    var lane = (sa.slot - sb.slot) * 7;
    var shift = Math.max(-40, Math.min(40, base + lane));
    var outA = 18 + Math.abs(sa.slot) * 4 + Math.min(12, len * .06);
    var outB = 18 + Math.abs(sb.slot) * 4 + Math.min(12, len * .06);
    var c1x = x1 + ua.x * outA + px * shift;
    var c1y = y1 + ua.y * outA + py * shift;
    var c2x = x2 + ub.x * outB + px * shift;
    var c2y = y2 + ub.y * outB + py * shift;
    return "M " + x1.toFixed(1) + " " + y1.toFixed(1)
      + " C " + c1x.toFixed(1) + " " + c1y.toFixed(1)
      + " " + c2x.toFixed(1) + " " + c2y.toFixed(1)
      + " " + x2.toFixed(1) + " " + y2.toFixed(1);
  }

  /* Create a layout for one graph.  Nodes/edges arrive in the mapped shape:
   *   node: {id, title, state, kind, importance, problems}
   *   edge: {s, t, type: prereq|related|apply|contrast|legacy, strength, direction}
   */
  function create(inputNodes, inputEdges, options) {
    options = options || {};
    var stageWidth = options.stageWidth || 1800;
    var stageHeight = options.stageHeight || 1550;
    var center = { x: stageWidth / 2, y: stageHeight / 2 };

    var edges = (inputEdges || []).map(function (edge, index) {
      return Object.assign({}, edge, { index: index });
    });

    var levels = hierarchyLevels(
      inputNodes.map(function (n) { return { id: n.id }; }),
      edges
    );

    var problems = inputNodes.map(function (n) { return Number(n.problems) || 0; });
    var problemMin = Math.min.apply(null, problems.concat([0]));
    var problemMax = Math.max.apply(null, problems.concat([0]));
    var degreeRaw = new Map(inputNodes.map(function (n) { return [n.id, 0]; }));
    var degreeCount = new Map(inputNodes.map(function (n) { return [n.id, 0]; }));
    edges.forEach(function (e) {
      var w = .72 + strength01(e.strength) * .82 + (e.type === "prereq" ? .16 : 0);
      if (degreeRaw.has(e.s)) degreeRaw.set(e.s, degreeRaw.get(e.s) + w);
      if (degreeRaw.has(e.t)) degreeRaw.set(e.t, degreeRaw.get(e.t) + w);
      if (degreeCount.has(e.s)) degreeCount.set(e.s, degreeCount.get(e.s) + 1);
      if (degreeCount.has(e.t)) degreeCount.set(e.t, degreeCount.get(e.t) + 1);
    });
    var degreeMin = Math.min.apply(null, Array.from(degreeRaw.values()).concat([0]));
    var degreeMax = Math.max.apply(null, Array.from(degreeRaw.values()).concat([0]));

    function norm(value, min, max) {
      return (value - min) / ((max - min) || 1);
    }

    var state = {
      nodes: [],
      edges: edges,
      byId: new Map(),
      degreeCount: degreeCount,
      degreeRaw: degreeRaw,
      stageWidth: stageWidth,
      stageHeight: stageHeight,
      center: center,
      portSlots: new Map(),
      graph: {
        view: options.view || "structure",
        gravity: options.gravity === undefined ? 30 : options.gravity,
        selected: null,
        filters: new Set(),
        drag: null,
        hover: null,
        alpha: 0,
        stableFrames: 0,
        settleWatch: 0,
        solveStep: 0,
        settled: false,
        layoutInflation: 1,
        autoFitAfterSettle: true,
        userMovedViewport: false,
        hiddenEdgeTypes: options.hiddenEdgeTypes || {},
        hiddenEdgeIds: options.hiddenEdgeIds || new Set(),
      },
      scoreFor: function (node, view) {
        view = view || state.graph.view;
        if (view === "structure") return norm(degreeRaw.get(node.id) || 0, degreeMin, degreeMax);
        if (view === "problem_count") return norm(Number(node.problems) || 0, problemMin, problemMax);
        if (view === "importance") return clamp(Number(node.importance) || 0, 0, 1);
        if (view === "state") return stateAttention(node.state);
        return 0;
      },
    };

    state.nodes = inputNodes.map(function (node, index) {
      var x = center.x + Math.cos(index * PHI) * (85 + Math.sqrt(index + 1) * 70);
      var y = 120 + (levels.get(node.id) || 0) * 145 + Math.sin(index * PHI) * 42;
      var size = sizeFor(state.scoreFor(node));
      return {
        id: node.id,
        title: node.title || node.id,
        // View-layer abbreviation, supplied by the workbench. Everything that measures
        // how much room a point needs reads this, so the layout is sized for the text
        // actually on screen; the full title stays here for the hover and the detail.
        shortTitle: node.shortTitle || node.title || node.id,
        kind: node.kind || "core",
        state: node.state || "new",
        importance: Number(node.importance) || 0,
        problems: Number(node.problems) || 0,
        level: levels.get(node.id) || 0,
        x: x,
        y: y,
        vx: 0,
        vy: 0,
        size: size,
        targetSize: size,
        opacity: 1,
        targetOpacity: 1,
        focusWeight: 1,
        visible: true,
        anchorX: null,
        anchorY: null,
        guideX: x,
        guideY: y,
      };
    });
    state.byId = new Map(state.nodes.map(function (n) { return [n.id, n]; }));

    recomputeLayoutGuides(state);
    // Start the solve on the guide grid, not on the seed spiral. The spiral sat up
    // to 1135px from the point's own guide (p50 666px), and the only thing standing
    // between that and the first frame was the hierarchy band clamp — which answers
    // by teleporting y to guideY +/- band, measured at 953px on real dmath data.
    // Contracted toward the centre so the learner still sees the graph grow out;
    // nothing has been simulated yet here, so the seat costs no layout quality.
    // Contracted in y only, so the learner still sees the rows fan out; x keeps the
    // guide spacing it already has, and nothing starts overlapping.
    var seat = { x: state.stageWidth / 2, y: state.stageHeight / 2 };
    state.nodes.forEach(function (n) {
      n.x = n.guideX;
      n.y = seat.y + (n.guideY - seat.y) * SEED_CONTRACTION_Y;
    });
    reheat(state, ALPHA_INIT, true);

    return {
      state: state,
      nodes: state.nodes,
      edges: state.edges,
      byId: state.byId,
      graph: state.graph,
      scoreFor: state.scoreFor,
      updateProjection: function () {
        state.nodes.forEach(function (n) { n.targetSize = sizeFor(state.scoreFor(n)); });
      },
      setEdgeVisibility: function (next) {
        // Relation visibility is a physics-level fact: a hidden relation is not
        // a constraint either, so the layout re-solves without it. Types cover
        // the legend toggles, ids cover the display budget.
        next = next || {};
        state.graph.hiddenEdgeTypes = next.types || {};
        state.graph.hiddenEdgeIds = next.ids || new Set();
        reheat(state, .85, true);
      },
      setView: function (view) {
        state.graph.view = view;
        state.graph.userMovedViewport = false;
        reheat(state, 1, true);
      },
      setGravity: function (gravity) {
        state.graph.gravity = clamp(Number(gravity) || 0, 0, 100);
        state.graph.userMovedViewport = false;
        reheat(state, .62, true);
      },
      reheat: function (alpha, autoFit) { reheat(state, alpha, autoFit); },
      tick: function () { tickPhysics(state); },
      visibleEdges: function () { return visibleEdges(state); },
      neighbors: function (id) { return neighbors(state, id); },
      computePortSlots: function (activeEdges) { return computePortSlots(state, activeEdges); },
      edgePath: function (edge) { return edgePath(state, edge); },
      edgeStyle: edgeStyle,
      layoutSpread: function () { return layoutSpread(state); },
      clusterCenters: function () { return clusterCenters(state); },
      congestion: function () {
        var active = state.nodes.filter(function (n) { return n.visible; });
        return congestionStats(state, active, localDensityMap(state, active));
      },
    };
  }

  return {
    PHI: PHI,
    clamp: clamp,
    strength01: strength01,
    sizeFor: sizeFor,
    stateAttention: stateAttention,
    baseGapForStrength: baseGapForStrength,
    compactness01: compactness01,
    spreadFactor: spreadFactor,
    labelWidth: labelWidth,
    footprint: footprint,
    bandRows: bandRows,
    structureStageSize: structureStageSize,
    hierarchyLevels: hierarchyLevels,
    nodeSafetyMargin: nodeSafetyMargin,
    readabilityFloor: readabilityFloor,
    desiredEdgeLength: desiredEdgeLength,
    localDensityMap: localDensityMap,
    congestionStats: congestionStats,
    resolveCongestion: resolveCongestion,
    create: create,
  };
}));
