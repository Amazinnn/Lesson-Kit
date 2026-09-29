"use strict";

(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.GraphPhysics = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  function nodeRadius(problemCount) {
    return Math.min(30, 8 + 2.4 * Math.sqrt(Math.max(0, problemCount || 0)));
  }

  function metricRadius(score) {
    return 10 + 20 * Math.sqrt(Math.max(0, Math.min(1, Number(score) || 0)));
  }

  function labelLineCount(title) {
    var label = String(title || "").replace(/\s+/g, " ").trim();
    if (!label) return 1;
    var maxChars = 14;
    var lines = 1;
    var line = "";
    Array.from(label).forEach(function (char) {
      if (line && line.length + char.length > maxChars) {
        lines += 1;
        line = char;
      } else {
        line += char;
      }
    });
    return lines;
  }

  function collisionRadius(radius, title) {
    return Math.min(150, radius + 6 + labelLineCount(title) * 16);
  }

  function edgeVisual(attraction) {
    var score = Math.max(
      0, Math.min(1, ((Number(attraction) || 1) - 0.75) / 1.125),
    );
    var width = 1.35 + score * 2.65;
    return {
      score: score,
      width: width,
      shadowWidth: width + 3.5,
      highlightWidth: Math.max(0.55, width * 0.24),
      opacity: 0.28 + score * 0.52,
    };
  }

  function projectionValue(node, projection) {
    if (projection === "problem_count") {
      return Math.max(0, Number(node.problem_count) || 0);
    }
    if (projection === "importance") {
      return node.importance === "core" ? 1 : 0;
    }
    if (projection === "state") {
      return node.state === "needs_work" ? 1
        : node.state === "review" ? 0.66
          : node.state === "mastered" ? 0 : 0.33;
    }
    return 0;
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
    processed.forEach(function (id) {
      maxLevel = Math.max(maxLevel, levels.get(id));
    });
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

  function hierarchyDimensions(sourceNodes, levels, width, height) {
    var counts = new Map();
    sourceNodes.forEach(function (node) {
      var level = levels.get(node.id) || 0;
      counts.set(level, (counts.get(level) || 0) + 1);
    });
    var maxCount = Math.max.apply(null, [1].concat(Array.from(counts.values())));
    var maxLevel = Math.max.apply(null, [0].concat(Array.from(counts.keys())));
    return {
      width: Math.max(1200, width || 800, maxCount * 190 + 180),
      height: Math.max(800, height || 600, (maxLevel + 1) * 190 + 180),
    };
  }

  function scoreMap(nodes, projection) {
    var scores = new Map();
    if (!projection || projection === "structure") {
      nodes.forEach(function (node) { scores.set(node.id, 0); });
      return scores;
    }
    var values = nodes.map(function (node) {
      return projectionValue(node, projection);
    });
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    var span = max - min;
    nodes.forEach(function (node) {
      var value = projectionValue(node, projection);
      scores.set(node.id, span ? (value - min) / span : 0.5);
    });
    return scores;
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

  function applyHierarchyProjection(graph, projection) {
    if (!graph || !graph.nodes) return graph;
    var scores = scoreMap(graph.nodes, projection);
    var groups = new Map();
    graph.nodes.forEach(function (node) {
      var level = node.hierarchyLevel || 0;
      if (!groups.has(level)) groups.set(level, []);
      groups.get(level).push(node);
    });

    Array.from(groups.keys()).sort(function (a, b) { return a - b; })
      .forEach(function (level, levelIndex) {
        var group = groups.get(level);
        group.sort(function (a, b) {
          if (projection && projection !== "structure") {
            var difference = scores.get(b.id) - scores.get(a.id);
            if (difference) return difference;
          }
          return String(a.id).localeCompare(String(b.id));
        });
        var centerX = graph.width / 2;
        group.forEach(function (node, index) {
          var score = scores.get(node.id) || 0;
          node.projection = projection || "structure";
          node.projectionScore = score;
          node.structureRadius = node.structureRadius || nodeRadius(node.problem_count);
          node.radius = (!projection || projection === "structure")
            ? node.structureRadius : metricRadius(score);
          node.collisionRadius = collisionRadius(node.radius, node.title);
          node.x = centerX + (index - (group.length - 1) / 2) * 190;
          node.y = 100 + levelIndex * 190;
          node.fx = null;
          node.fy = null;
        });
      });

    graph.projection = projection || "structure";
    decorateParallelEdges(graph.edges);
    return graph;
  }

  function layoutHierarchy(sourceNodes, sourceEdges, width, height, projection) {
    var levels = hierarchyLevels(sourceNodes, sourceEdges);
    var dimensions = hierarchyDimensions(sourceNodes, levels, width, height);
    var nodes = sourceNodes.map(function (source) {
      var radius = nodeRadius(source.problem_count);
      return Object.assign({}, source, {
        radius: radius,
        structureRadius: radius,
        collisionRadius: collisionRadius(radius, source.title),
        hierarchyLevel: levels.get(source.id) || 0,
        x: dimensions.width / 2,
        y: 100,
        fx: null,
        fy: null,
      });
    });
    var byId = new Map(nodes.map(function (node) { return [node.id, node]; }));
    var edges = sourceEdges.map(function (edge) {
      return Object.assign({}, edge, {
        sourceNode: byId.get(edge.source),
        targetNode: byId.get(edge.target),
      });
    }).filter(function (edge) {
      return edge.sourceNode && edge.targetNode;
    });
    var graph = {
      nodes: nodes,
      edges: edges,
      width: dimensions.width,
      height: dimensions.height,
      hierarchical: true,
      projection: "structure",
    };
    return applyHierarchyProjection(graph, projection || "structure");
  }

  return {
    nodeRadius: nodeRadius,
    metricRadius: metricRadius,
    labelLineCount: labelLineCount,
    collisionRadius: collisionRadius,
    edgeVisual: edgeVisual,
    projectionValue: projectionValue,
    hierarchyLevels: hierarchyLevels,
    applyHierarchyProjection: applyHierarchyProjection,
    layoutHierarchy: layoutHierarchy,
  };
}));
