"use strict";

(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.GraphPhysics = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  var GOLDEN_ANGLE = 2.399963229728653;
  var TAU = Math.PI * 2;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function nodeRadius(problemCount) {
    return Math.min(31, 14 + 3.2 * Math.sqrt(Math.max(0, Number(problemCount) || 0)));
  }

  function metricRadius(score) {
    return 14 + 17 * Math.sqrt(clamp(Number(score) || 0, 0, 1));
  }

  function labelLineCount(title) {
    var label = String(title || "").replace(/\s+/g, " ").trim();
    if (!label) return 1;
    return Math.max(1, Math.ceil(Array.from(label).length / 14));
  }

  function labelWidth(title) {
    return Math.min(168, Math.max(62, Array.from(String(title || "")).length * 12 + 18));
  }

  function collisionRadius(radius, title) {
    var vertical = radius + 18 + labelLineCount(title) * 16;
    var horizontal = Math.max(radius + 14, labelWidth(title) / 2);
    return Math.min(180, Math.max(vertical, horizontal));
  }

  function projectionValue(node, projection) {
    if (projection === "problem_count") return Math.max(0, Number(node.problem_count) || 0);
    if (projection === "importance") return node.importance === "core" ? 1 : 0.35;
    if (projection === "state") return node.state === "needs_work" ? 1
      : node.state === "review" ? 0.70
        : node.state === "mastered" ? 0.22 : 0.46;
    return 0;
  }

  function edgeVisual(attraction) {
    var score = clamp(((Number(attraction) || 1) - 0.75) / 1.125, 0, 1);
    var width = 1.05 + score * 2.35;
    return {
      score: score,
      width: width,
      shadowWidth: width + 2.8,
      highlightWidth: Math.max(0.45, width * 0.20),
      opacity: 0.18 + score * 0.48,
    };
  }

  function hierarchyLevels(sourceNodes, sourceEdges) {
    var ids = new Set(sourceNodes.map(function (node) { return node.id; }));
    var outgoing = new Map(sourceNodes.map(function (node) { return [node.id, []]; }));
    var indegree = new Map(sourceNodes.map(function (node) { return [node.id, 0]; }));
    var structural = new Set();

    sourceEdges.forEach(function (edge) {
      if (edge.relation_type !== "prerequisite" || edge.direction === "symmetric") return;
      if (!ids.has(edge.source) || !ids.has(edge.target) || edge.source === edge.target) return;
      outgoing.get(edge.source).push(edge.target);
      indegree.set(edge.target, indegree.get(edge.target) + 1);
      structural.add(edge.source);
      structural.add(edge.target);
    });
    outgoing.forEach(function (targets) { targets.sort(); });

    var levels = new Map(sourceNodes.map(function (node) { return [node.id, 0]; }));
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
        if (indegree.get(target) === 0) {
          queue.push(target);
          queue.sort();
        }
      });
    }

    var maxLevel = 0;
    processed.forEach(function (id) { maxLevel = Math.max(maxLevel, levels.get(id)); });
    var unresolved = Array.from(structural).filter(function (id) {
      return !processed.has(id);
    }).sort();
    if (unresolved.length) {
      var cycleLevel = maxLevel + 1;
      unresolved.forEach(function (id) { levels.set(id, cycleLevel); });
      maxLevel = cycleLevel;
    }

    var isolateLevel = structural.size ? maxLevel + 1 : 0;
    sourceNodes.map(function (node) { return node.id; })
      .filter(function (id) { return !structural.has(id); })
      .sort()
      .forEach(function (id) { levels.set(id, isolateLevel); });
    return levels;
  }

  function decorateParallelEdges(edges) {
    var groups = new Map();
    edges.forEach(function (edge) {
      var key = [edge.source, edge.target].sort().join("\u0000");
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(edge);
    });
    groups.forEach(function (group) {
      group.sort(function (a, b) {
        return String(a.relation_type || "").localeCompare(String(b.relation_type || ""))
          || String(a.id || "").localeCompare(String(b.id || ""));
      });
      group.forEach(function (edge, index) {
        edge.parallelIndex = index;
        edge.parallelCount = group.length;
      });
    });
  }

  function degreeStats(nodes, edges) {
    var count = new Map(nodes.map(function (node) { return [node.id, 0]; }));
    var weighted = new Map(nodes.map(function (node) { return [node.id, 0]; }));
    edges.forEach(function (edge) {
      if (!count.has(edge.source) || !count.has(edge.target)) return;
      var visual = edgeVisual(edge.attraction);
      var weight = 0.72 + visual.score * 0.82
        + (edge.relation_type === "prerequisite" ? 0.16 : 0);
      count.set(edge.source, count.get(edge.source) + 1);
      count.set(edge.target, count.get(edge.target) + 1);
      weighted.set(edge.source, weighted.get(edge.source) + weight);
      weighted.set(edge.target, weighted.get(edge.target) + weight);
    });
    return { count: count, weighted: weighted };
  }

  function normalizeMap(values, fallback) {
    var numbers = Array.from(values.values());
    var min = Math.min.apply(null, [0].concat(numbers));
    var max = Math.max.apply(null, [0].concat(numbers));
    var span = max - min;
    var out = new Map();
    values.forEach(function (value, id) {
      out.set(id, span ? (value - min) / span : fallback);
    });
    return out;
  }

  function scoreMap(graph, projection) {
    if (projection === "structure") return normalizeMap(graph.degreeWeighted, 0.5);
    var out = new Map();
    if (projection === "problem_count") {
      var values = new Map(graph.nodes.map(function (node) {
        return [node.id, Math.max(0, Number(node.problem_count) || 0)];
      }));
      return normalizeMap(values, 0.5);
    }
    if (projection === "importance") {
      graph.nodes.forEach(function (node) {
        out.set(node.id, node.importance === "core" ? 1 : 0.35);
      });
      return out;
    }
    if (projection === "state") {
      graph.nodes.forEach(function (node) {
        out.set(node.id, node.state === "needs_work" ? 1
          : node.state === "review" ? 0.70
            : node.state === "mastered" ? 0.22 : 0.46);
      });
      return out;
    }
    graph.nodes.forEach(function (node) { out.set(node.id, 0.5); });
    return out;
  }

  function weightedNeighbors(graph, id) {
    if (graph.adjacency && graph.adjacency.has(id)) return graph.adjacency.get(id);
    var out = [];
    graph.edges.forEach(function (edge) {
      if (edge.source !== id && edge.target !== id) return;
      var other = edge.source === id ? edge.target : edge.source;
      var visual = edgeVisual(edge.attraction);
      var relationWeight = edge.relation_type === "prerequisite" ? 1.35
        : edge.relation_type === "applies_to" ? 1.0
          : edge.relation_type === "contrasts" ? 0.82 : 0.68;
      out.push({ id: other, weight: relationWeight * (0.72 + visual.score * 0.62), edge: edge });
    });
    return out;
  }

  function structureOrdering(graph) {
    var levels = Array.from(new Set(graph.nodes.map(function (node) {
      return node.hierarchyLevel || 0;
    }))).sort(function (a, b) { return a - b; });
    var groups = new Map(levels.map(function (level) {
      return [level, graph.nodes.filter(function (node) {
        return (node.hierarchyLevel || 0) === level;
      }).sort(function (a, b) {
        return a.x - b.x || String(a.id).localeCompare(String(b.id));
      })];
    }));
    function rankMap() {
      var rank = new Map();
      levels.forEach(function (level) {
        (groups.get(level) || []).forEach(function (node, index) { rank.set(node.id, index); });
      });
      return rank;
    }
    for (var pass = 0; pass < 4; pass += 1) {
      var rank = rankMap();
      levels.slice(1).forEach(function (level) {
        groups.get(level).sort(function (a, b) {
          function bary(node) {
            var sum = 0, weight = 0;
            weightedNeighbors(graph, node.id).forEach(function (entry) {
              var other = graph.nodeById.get(entry.id);
              if (!other || other.hierarchyLevel >= level || !rank.has(other.id)) return;
              sum += rank.get(other.id) * entry.weight;
              weight += entry.weight;
            });
            return weight ? sum / weight : rank.get(node.id);
          }
          return bary(a) - bary(b) || String(a.id).localeCompare(String(b.id));
        });
      });
      rank = rankMap();
      levels.slice(0, -1).reverse().forEach(function (level) {
        groups.get(level).sort(function (a, b) {
          function bary(node) {
            var sum = 0, weight = 0;
            weightedNeighbors(graph, node.id).forEach(function (entry) {
              var other = graph.nodeById.get(entry.id);
              if (!other || other.hierarchyLevel <= level || !rank.has(other.id)) return;
              sum += rank.get(other.id) * entry.weight;
              weight += entry.weight;
            });
            return weight ? sum / weight : rank.get(node.id);
          }
          return bary(a) - bary(b) || String(a.id).localeCompare(String(b.id));
        });
      });
    }
    return { levels: levels, groups: groups };
  }

  function compactness01(value) {
    var g = clamp((Number(value) || 0) / 100, 0, 1);
    return (1 - Math.exp(-3 * g)) / (1 - Math.exp(-3));
  }

  function spreadFactor(graph) {
    return 1.29 - 0.41 * compactness01(graph.compactness);
  }

  function baseGapForAttraction(attraction) {
    return 218 - 118 * edgeVisual(attraction).score;
  }

  function nodeFootprint(node) {
    return {
      halfWidth: Math.max(node.radius + 14, labelWidth(node.title) / 2),
      top: node.radius + 13,
      bottom: node.radius + 42,
    };
  }

  function readabilityFloor(a, b, ux, uy) {
    var fa = nodeFootprint(a), fb = nodeFootprint(b);
    var ah = Math.max(fa.top, fa.bottom), bh = Math.max(fb.top, fb.bottom);
    var ea = Math.abs(ux) * fa.halfWidth + Math.abs(uy) * ah;
    var eb = Math.abs(ux) * fb.halfWidth + Math.abs(uy) * bh;
    var degreeBoost = Math.min(34, ((a.degree || 0) + (b.degree || 0)) * 1.6);
    return ea + eb + 18 + degreeBoost;
  }

  function desiredEdgeLength(graph, edge) {
    var a = edge.sourceNode, b = edge.targetNode;
    if (!a || !b) return 160;
    var dx = b.x - a.x, dy = b.y - a.y;
    var distance = Math.max(1, Math.hypot(dx, dy));
    var ux = dx / distance, uy = dy / distance;
    var semantic = (a.radius + b.radius) * 0.48
      + baseGapForAttraction(edge.attraction) * spreadFactor(graph);
    return Math.max(semantic, readabilityFloor(a, b, ux, uy));
  }

  function hierarchyDimensions(nodes, levels, width, height) {
    var counts = new Map();
    nodes.forEach(function (node) {
      var level = levels.get(node.id) || 0;
      counts.set(level, (counts.get(level) || 0) + 1);
    });
    var maxCount = Math.max.apply(null, [1].concat(Array.from(counts.values())));
    var maxLevel = Math.max.apply(null, [0].concat(Array.from(counts.keys())));
    return {
      width: Math.max(1200, width || 800, maxCount * 190 + 240),
      height: Math.max(820, height || 600, (maxLevel + 1) * 180 + 260),
    };
  }

  function buildGuides(graph) {
    var scores = scoreMap(graph, graph.projection);
    graph.scores = scores;
    graph.nodes.forEach(function (node) {
      node.projection = graph.projection;
      node.projectionScore = scores.get(node.id) || 0;
      node.radius = metricRadius(node.projectionScore);
      node.collisionRadius = collisionRadius(node.radius, node.title);
    });

    var centerX = graph.width / 2;
    var centerY = graph.height / 2;
    var spread = spreadFactor(graph);
    if (graph.projection === "structure") {
      var ordered = structureOrdering(graph);
      ordered.levels.forEach(function (level, levelIndex) {
        var group = ordered.groups.get(level) || [];
        var widths = group.map(function (node) {
          return Math.max(labelWidth(node.title), node.radius * 2 + 36);
        });
        var gap = 62 + 36 * spread;
        var total = widths.reduce(function (sum, value) { return sum + value; }, 0)
          + gap * Math.max(0, group.length - 1);
        var cursor = centerX - total / 2;
        group.forEach(function (node, index) {
          node.guideX = cursor + widths[index] / 2;
          cursor += widths[index] + gap;
          node.guideY = 130 + levelIndex * 170 * spread;
        });
      });
      return;
    }

    if (graph.projection === "state") {
      var order = ["needs_work", "review", "mastered", null];
      var present = order.filter(function (state) {
        return graph.nodes.some(function (node) { return (node.state || null) === state; });
      });
      var centers = new Map();
      var radius = 260 * spread;
      present.forEach(function (state, index) {
        var angle = -Math.PI / 2 + index * TAU / Math.max(1, present.length);
        centers.set(state, {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
        });
      });
      present.forEach(function (state) {
        var group = graph.nodes.filter(function (node) { return (node.state || null) === state; });
        var c = centers.get(state);
        var ring = 56 + Math.sqrt(group.length) * 31 * spread;
        group.sort(function (a, b) { return String(a.id).localeCompare(String(b.id)); });
        group.forEach(function (node, index) {
          var angle = index * GOLDEN_ANGLE - Math.PI / 2;
          var factor = index ? 1 : 0;
          node.guideX = c.x + Math.cos(angle) * ring * factor;
          node.guideY = c.y + Math.sin(angle) * ring * factor;
        });
      });
      return;
    }

    graph.nodes.forEach(function (node, index) {
      var score = scores.get(node.id) || 0;
      var dx = node.x - centerX, dy = node.y - centerY;
      var distance = Math.hypot(dx, dy);
      var ux, uy;
      if (distance < 24) {
        var angle = index * GOLDEN_ANGLE;
        ux = Math.cos(angle); uy = Math.sin(angle);
      } else {
        ux = dx / distance; uy = dy / distance;
      }
      var targetR = (150 + (1 - score) * 450) * spread;
      node.guideX = centerX + ux * targetR;
      node.guideY = centerY + uy * targetR;
    });
  }

  function spatialPairs(nodes, cellSize, callback) {
    var cells = new Map();
    nodes.forEach(function (node, index) {
      var cx = Math.floor(node.x / cellSize);
      var cy = Math.floor(node.y / cellSize);
      var key = cx + ":" + cy;
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(index);
    });
    var offsets = [[0, 0], [1, 0], [0, 1], [1, 1], [-1, 1]];
    cells.forEach(function (indices, key) {
      var parts = key.split(":");
      var cx = Number(parts[0]), cy = Number(parts[1]);
      offsets.forEach(function (offset) {
        var other = cells.get((cx + offset[0]) + ":" + (cy + offset[1]));
        if (!other) return;
        indices.forEach(function (i) {
          other.forEach(function (j) {
            if (offset[0] === 0 && offset[1] === 0 && j <= i) return;
            callback(nodes[i], nodes[j]);
          });
        });
      });
    });
  }

  function localDensity(graph) {
    var counts = new Map(graph.nodes.map(function (node) { return [node.id, 0]; }));
    spatialPairs(graph.nodes, 280, function (a, b) {
      var distance = Math.hypot(b.x - a.x, b.y - a.y);
      if (distance > 280) return;
      var weight = Math.pow(1 - distance / 280, 1.25);
      counts.set(a.id, counts.get(a.id) + weight);
      counts.set(b.id, counts.get(b.id) + weight);
    });
    return counts;
  }

  function resolveOverlaps(graph, rounds) {
    var nodes = graph.nodes;
    for (var round = 0; round < rounds; round += 1) {
      var moved = false;
      spatialPairs(nodes, 230, function (a, b) {
        var fa = nodeFootprint(a), fb = nodeFootprint(b);
        var ax1 = a.x - fa.halfWidth - 8, ax2 = a.x + fa.halfWidth + 8;
        var ay1 = a.y - fa.top - 8, ay2 = a.y + fa.bottom + 8;
        var bx1 = b.x - fb.halfWidth - 8, bx2 = b.x + fb.halfWidth + 8;
        var by1 = b.y - fb.top - 8, by2 = b.y + fb.bottom + 8;
        var ox = Math.min(ax2, bx2) - Math.max(ax1, bx1);
        var oy = Math.min(ay2, by2) - Math.max(ay1, by1);
        if (ox <= 0 || oy <= 0) return;
        moved = true;
        if (ox <= oy) {
          var xdir = a.x <= b.x ? -1 : 1;
          var xshift = (ox + 6) * 0.5;
          a.x += xdir * xshift; b.x -= xdir * xshift;
        } else {
          var ydir = a.y <= b.y ? -1 : 1;
          var yshift = (oy + 6) * 0.5;
          a.y += ydir * yshift; b.y -= ydir * yshift;
        }
      });
      if (!moved) break;
    }
  }

  function solve(graph) {
    buildGuides(graph);
    var nodes = graph.nodes;
    var n = nodes.length;
    if (!n) return graph;
    var iterations = n <= 32 ? 56 : n <= 80 ? 34 : n <= 180 ? 20 : 12;
    var damping = 0.78;

    nodes.forEach(function (node) {
      if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
        node.x = node.guideX; node.y = node.guideY;
      }
      node.vx = 0; node.vy = 0;
    });

    for (var step = 0; step < iterations; step += 1) {
      var alpha = 1 - step / iterations;
      graph.edges.forEach(function (edge) {
        var a = edge.sourceNode, b = edge.targetNode;
        if (!a || !b) return;
        var dx = b.x - a.x, dy = b.y - a.y;
        var distance = Math.max(1, Math.hypot(dx, dy));
        var ux = dx / distance, uy = dy / distance;
        var desired = desiredEdgeLength(graph, edge);
        var error = distance - desired;
        var dead = 16 + desired * 0.028;
        if (Math.abs(error) <= dead) return;
        var hubNorm = Math.min(1, 1.8 / Math.sqrt(Math.max(1, a.degree * b.degree)));
        var typeWeight = edge.relation_type === "prerequisite" ? 1
          : edge.relation_type === "applies_to" ? 0.82
            : edge.relation_type === "contrasts" ? 0.70 : 0.54;
        var strength = 0.70 + edgeVisual(edge.attraction).score * 0.46;
        var magnitude = clamp((Math.abs(error) - dead) / Math.max(120, desired), 0, 1.15)
          * hubNorm * typeWeight * strength * alpha;
        var force = Math.sign(error) * magnitude;
        a.vx += force * ux; a.vy += force * uy;
        b.vx -= force * ux; b.vy -= force * uy;
      });

      spatialPairs(nodes, 250, function (a, b) {
        var dx = b.x - a.x, dy = b.y - a.y;
        var distance = Math.max(1, Math.hypot(dx, dy));
        if (distance > 250) return;
        var ux = dx / distance, uy = dy / distance;
        var floor = readabilityFloor(a, b, ux, uy);
        var densityBoost = 1 + Math.min(1.8, (a.degree + b.degree) * 0.078);
        var nearBoost = distance < floor * 1.48 ? 1.9 : 1;
        var repulsion = Math.min(1.25, 12800 / (distance * distance))
          * densityBoost * nearBoost * alpha;
        a.vx -= repulsion * ux; a.vy -= repulsion * uy;
        b.vx += repulsion * ux; b.vy += repulsion * uy;
      });

      if (step % 4 === 0) {
        var density = localDensity(graph);
        nodes.forEach(function (node) {
          var crowd = density.get(node.id) || 0;
          if (crowd < 1.9) return;
          var dx = node.x - graph.width / 2;
          var dy = node.y - graph.height / 2;
          var length = Math.max(1, Math.hypot(dx, dy));
          var push = Math.min(0.38, (crowd - 1.8) * 0.045) * alpha;
          node.vx += dx / length * push;
          node.vy += dy / length * push;
        });
      }

      nodes.forEach(function (node) {
        var gx = node.guideX, gy = node.guideY;
        if (graph.projection === "structure") {
          node.vx += (gx - node.x) * 0.016 * alpha;
          node.vy += (gy - node.y) * 0.066 * alpha;
        } else if (graph.projection === "state") {
          node.vx += (gx - node.x) * 0.014 * alpha;
          node.vy += (gy - node.y) * 0.014 * alpha;
          node.vy += (142 + node.hierarchyLevel * 166 * spreadFactor(graph) - node.y)
            * 0.0012 * alpha;
        } else {
          node.vx += (gx - node.x) * 0.010 * alpha;
          node.vy += (gy - node.y) * 0.010 * alpha;
          node.vy += (142 + node.hierarchyLevel * 166 * spreadFactor(graph) - node.y)
            * 0.0023 * alpha;
        }
        node.vx *= damping; node.vy *= damping;
        var speed = Math.hypot(node.vx, node.vy);
        if (speed > 7) { node.vx *= 7 / speed; node.vy *= 7 / speed; }
        node.x += node.vx; node.y += node.vy;
      });

      if (step % 7 === 6) resolveOverlaps(graph, 2);
    }

    resolveOverlaps(graph, n <= 100 ? 12 : 6);

    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach(function (node) {
      var fp = nodeFootprint(node);
      minX = Math.min(minX, node.x - fp.halfWidth - 38);
      maxX = Math.max(maxX, node.x + fp.halfWidth + 38);
      minY = Math.min(minY, node.y - fp.top - 38);
      maxY = Math.max(maxY, node.y + fp.bottom + 38);
    });
    var shiftX = minX < 24 ? 24 - minX : 0;
    var shiftY = minY < 24 ? 24 - minY : 0;
    if (shiftX || shiftY) {
      nodes.forEach(function (node) { node.x += shiftX; node.y += shiftY; });
      maxX += shiftX; maxY += shiftY;
    }
    graph.width = Math.max(graph.width, maxX + 44);
    graph.height = Math.max(graph.height, maxY + 44);
    return graph;
  }

  function applyHierarchyProjection(graph, projection, compactness) {
    if (!graph || !graph.nodes) return graph;
    graph.projection = projection || "structure";
    if (compactness !== undefined) graph.compactness = clamp(Number(compactness) || 0, 0, 100);
    solve(graph);
    decorateParallelEdges(graph.edges);
    return graph;
  }

  function setCompactness(graph, compactness) {
    if (!graph) return graph;
    graph.compactness = clamp(Number(compactness) || 0, 0, 100);
    return applyHierarchyProjection(graph, graph.projection || "structure");
  }

  function layoutHierarchy(sourceNodes, sourceEdges, width, height, projection) {
    var levels = hierarchyLevels(sourceNodes, sourceEdges);
    var dimensions = hierarchyDimensions(sourceNodes, levels, width, height);
    var nodes = sourceNodes.map(function (source, index) {
      var angle = index * GOLDEN_ANGLE;
      var ring = 90 + Math.sqrt(index + 1) * 72;
      return Object.assign({}, source, {
        radius: nodeRadius(source.problem_count),
        hierarchyLevel: levels.get(source.id) || 0,
        x: dimensions.width / 2 + Math.cos(angle) * ring,
        y: 130 + (levels.get(source.id) || 0) * 160 + Math.sin(angle) * 36,
        vx: 0, vy: 0, fx: null, fy: null,
      });
    });
    var nodeById = new Map(nodes.map(function (node) { return [node.id, node]; }));
    var edges = sourceEdges.map(function (edge) {
      return Object.assign({}, edge, {
        sourceNode: nodeById.get(edge.source),
        targetNode: nodeById.get(edge.target),
      });
    }).filter(function (edge) { return edge.sourceNode && edge.targetNode; });
    decorateParallelEdges(edges);
    var stats = degreeStats(nodes, edges);
    nodes.forEach(function (node) {
      node.degree = stats.count.get(node.id) || 0;
      node.degreeWeighted = stats.weighted.get(node.id) || 0;
    });
    var adjacency = new Map(nodes.map(function (node) { return [node.id, []]; }));
    edges.forEach(function (edge) {
      var visual = edgeVisual(edge.attraction);
      var relationWeight = edge.relation_type === "prerequisite" ? 1.35
        : edge.relation_type === "applies_to" ? 1.0
          : edge.relation_type === "contrasts" ? 0.82 : 0.68;
      var weight = relationWeight * (0.72 + visual.score * 0.62);
      adjacency.get(edge.source).push({ id: edge.target, weight: weight, edge: edge });
      adjacency.get(edge.target).push({ id: edge.source, weight: weight, edge: edge });
    });
    var graph = {
      nodes: nodes,
      edges: edges,
      nodeById: nodeById,
      adjacency: adjacency,
      degreeCount: stats.count,
      degreeWeighted: stats.weighted,
      width: dimensions.width,
      height: dimensions.height,
      hierarchical: true,
      projection: projection || "structure",
      compactness: 30,
    };
    return applyHierarchyProjection(graph, projection || "structure");
  }

  return {
    nodeRadius: nodeRadius,
    metricRadius: metricRadius,
    labelLineCount: labelLineCount,
    labelWidth: labelWidth,
    collisionRadius: collisionRadius,
    edgeVisual: edgeVisual,
    projectionValue: projectionValue,
    hierarchyLevels: hierarchyLevels,
    desiredEdgeLength: desiredEdgeLength,
    applyHierarchyProjection: applyHierarchyProjection,
    setCompactness: setCompactness,
    layoutHierarchy: layoutHierarchy,
  };
}));