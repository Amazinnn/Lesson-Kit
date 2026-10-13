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

  function footprint(node) {
    var half = Math.max(node.size / 2 + 13, labelWidth(node.title) / 2);
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
      var widths = group.map(function (n) { return Math.max(labelWidth(n.title), 96); });
      var rows = bandRows(widths, gap);
      if (rows.length > 1) wrapped = true;
      rowCount += rows.length;
      if (rows.length === 1) {
        var width = widths.reduce(function (a, b) { return a + b; }, 0)
          + gap * Math.max(0, widths.length - 1);
        widestSingleRow = Math.max(widestSingleRow, width);
      }
    });
    var size = {
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
    var semantic = (a.size + b.size) * .48
      + baseGapForStrength(edge.strength) * layoutSpread(state);
    // Relation strength is a preference. Readability is a hard floor.
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
          return Math.max(labelWidth(n.title), n.targetSize + 34);
        });
        var bandWidths = group.map(function (n) {
          return Math.max(labelWidth(n.title), 96);
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

  function enforceHierarchyBands(state, active) {
    if (state.graph.view !== "structure") return;
    var band = 42 + 8 * layoutSpread(state);
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

    // Relation strength asks for a distance; it can never pull beneath the
    // direction-aware readability floor.
    activeEdges.forEach(function (edge) {
      var a = state.byId.get(edge.s);
      var b = state.byId.get(edge.t);
      var dx = b.x - a.x;
      var dy = b.y - a.y;
      var dist = Math.max(1, dist2d(dx, dy));
      var ux = dx / dist;
      var uy = dy / dist;
      var desired = desiredEdgeLength(state, edge, densityMap);
      var error = dist - desired;
      var dead = 16 + desired * .03;
      if (Math.abs(error) <= dead) return;
      var da = Math.max(1, state.degreeCount.get(a.id) || 1);
      var db = Math.max(1, state.degreeCount.get(b.id) || 1);
      var hubNorm = Math.min(1, 1.66 / Math.sqrt(da * db));
      var strength = .70 + .46 * strength01(edge.strength);
      var magnitude = Math.min(1.45, Math.max(0, (Math.abs(error) - dead) / Math.max(96, desired) * 1.42))
        * hubNorm * (TYPE_WEIGHT[edge.type] || .58) * strength * alpha;
      var f = Math.sign(error) * magnitude;
      if (movable(state, a)) { a.vx += f * ux; a.vy += f * uy; }
      if (movable(state, b)) { b.vx -= f * ux; b.vy -= f * uy; }
    });

    // Density-aware repulsion: crowded hubs automatically get more personal
    // space. The user does not need to tune another slider for this.
    for (var i = 0; i < active.length; i += 1) {
      for (var j = i + 1; j < active.length; j += 1) {
        var a = active[i];
        var b = active[j];
        var dx = b.x - a.x;
        var dy = b.y - a.y;
        var dist = Math.max(1, dist2d(dx, dy));
        var ux = dx / dist;
        var uy = dy / dist;
        var densityBoost = 1 + Math.min(1.8, ((densityMap.get(a.id) || 0) + (densityMap.get(b.id) || 0)) * .10);
        var floor = readabilityFloor(state, a, b, ux, uy, densityMap);
        var nearBoost = dist < floor * 1.45 ? 1.8 : 1;
        var rep = Math.min(1.18, 11200 / (dist * dist)) * densityBoost * nearBoost
          * (.74 + .20 * layoutSpread(state)) * alpha;
        if (movable(state, a)) { a.vx -= rep * ux; a.vy -= rep * uy; }
        if (movable(state, b)) { b.vx += rep * ux; b.vy += rep * uy; }
      }
    }

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
          n.vx += (gx - n.x) * .016 * alpha;
          n.vy += (gy - n.y) * .072 * alpha;
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
      n.vx += (center.x - n.x) * .00025 * alpha;
      n.vy += (center.y - n.y) * .00025 * alpha;
      n.vx *= .81;
      n.vy *= .81;
      var speed = dist2d(n.vx, n.vy);
      if (speed > 7) { n.vx *= 7 / speed; n.vy *= 7 / speed; }
      n.x += n.vx;
      n.y += n.vy;
    });

    // Hierarchy is semantically strong, but readability wins conflicts.
    enforceHierarchyBands(state, active);
    var before = congestionStats(state, active, densityMap);
    var after = before.pairs > 0 ? resolveCongestion(state, active, densityMap, 10) : before;

    // If the logical area is still under pressure, expand the layout footprint
    // and let Fit zoom out. Never respond by shrinking the readability floor.
    if (graph.solveStep % 10 === 0) {
      var pressure = before.pairs + after.pairs * 2 + Math.min(4, before.maxOverlap / 12);
      var target = 1;
      if (pressure > 0) target = Math.min(1.50, 1 + .024 * pressure);
      graph.layoutInflation += (target - graph.layoutInflation) * (pressure > 0 ? .24 : .07);
      graph.layoutInflation = Math.max(1, Math.min(1.50, graph.layoutInflation));
      if (Math.abs(target - graph.layoutInflation) > .008) recomputeLayoutGuides(state);
    }

    active.forEach(function (n) {
      var fp = footprint(n);
      var m = nodeSafetyMargin(state, n, densityMap) * .35;
      var left = fp.left + m + 22;
      var right = state.stageWidth - fp.right - m - 22;
      var top = fp.top + m + 22;
      var bottom = state.stageHeight - fp.bottom - m - 22;
      n.x = Math.max(left, Math.min(right, n.x));
      n.y = Math.max(top, Math.min(bottom, n.y));
    });

    var avg = 0;
    active.forEach(function (n) { avg += dist2d(n.vx, n.vy); });
    avg /= Math.max(1, active.length);
    var finalStats = congestionStats(state, active, densityMap);
    graph.alpha *= .962;
    if (finalStats.pairs === 0 && graph.alpha < .032 && avg < .075) graph.stableFrames += 1;
    else graph.stableFrames = 0;
    // Safety valve: forces have faded (alpha < .01) and the resolver has had
    // two more seconds of rounds; finish even if a residual overlap survives,
    // so an impossible packing can never spin the solver forever.
    if (graph.alpha < .01) graph.settleWatch = (graph.settleWatch || 0) + 1;
    else graph.settleWatch = 0;
    if (graph.settleWatch > 120) graph.stableFrames = 15;
    if (graph.stableFrames > 14) {
      // Final order matters: semantic band first, then the hard readability
      // projection, and it has to be the last writer. A dense row can need a
      // few passes (every pass can jostle the next pair), and the boundary
      // clamp earlier in this tick may well have re-created a contact, so the
      // cleanup repeats until the packing is actually clean.
      enforceHierarchyBands(state, active);
      var passes = 0;
      var clean = congestionStats(state, active, densityMap);
      while (clean.pairs > 0 && passes < 12) {
        clean = resolveCongestion(state, active, densityMap, 14);
        passes += 1;
      }
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
    var ra = a.size / 2 + 10;
    var rb = b.size / 2 + 11;
    var ga = Math.min(12, 5 + a.size * .06);
    var gb = Math.min(12, 5 + b.size * .06);
    var ua = { x: Math.cos(sa.angle), y: Math.sin(sa.angle) };
    var ta = { x: -ua.y, y: ua.x };
    var ub = { x: Math.cos(sb.angle), y: Math.sin(sb.angle) };
    var tb = { x: -ub.y, y: ub.x };
    var x1 = a.x + ua.x * ra + ta.x * sa.slot * ga;
    var y1 = a.y + ua.y * ra + ta.y * sa.slot * ga;
    var x2 = b.x + ub.x * rb + tb.x * sb.slot * gb;
    var y2 = b.y + ub.y * rb + tb.y * sb.slot * gb;
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
    var c1x = x1 + ua.x * outA + ta.x * sa.slot * 2.5 + px * shift;
    var c1y = y1 + ua.y * outA + ta.y * sa.slot * 2.5 + py * shift;
    var c2x = x2 + ub.x * outB + tb.x * sb.slot * 2.5 + px * shift;
    var c2y = y2 + ub.y * outB + tb.y * sb.slot * 2.5 + py * shift;
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
    reheat(state, 1, true);

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
