"use strict";

(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.GraphPhysics = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  function nodeRadius(problemCount) {
    return Math.min(30, 8 + 2.4 * Math.sqrt(Math.max(0, problemCount || 0)));
  }

  function targetDistance(attraction) {
    return 120 / Math.sqrt(Math.max(0.1, attraction || 1));
  }

  function createSimulation(sourceNodes, sourceEdges, width, height) {
    width = Math.max(240, width || 800);
    height = Math.max(180, height || 600);
    var centerX = width / 2;
    var centerY = height / 2;
    var spread = Math.min(width, height) * 0.3;
    var nodes = sourceNodes.map(function (source, index) {
      var angle = index * 2.399963229728653;
      var distance = spread * Math.sqrt((index + 1) / Math.max(sourceNodes.length, 1));
      return Object.assign({}, source, {
        radius: nodeRadius(source.problem_count),
        collisionRadius: Math.max(
          nodeRadius(source.problem_count) + 10,
          Math.min(72, 20 + String(source.title || "").length * 2.4),
        ),
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance,
        vx: 0, vy: 0, fx: null, fy: null,
      });
    });
    var byId = new Map(nodes.map(function (node) { return [node.id, node]; }));
    var edges = sourceEdges.map(function (edge) {
      return Object.assign({}, edge, {
        sourceNode: byId.get(edge.source),
        targetNode: byId.get(edge.target),
      });
    }).filter(function (edge) { return edge.sourceNode && edge.targetNode; });
    return {
      nodes: nodes, edges: edges, width: width, height: height,
      alpha: 1, stable: nodes.length < 2, stableTicks: 0,
    };
  }

  function tick(simulation) {
    if (simulation.stable) return true;
    var nodes = simulation.nodes;
    var alpha = simulation.alpha;
    simulation.edges.forEach(function (edge) {
      var source = edge.sourceNode;
      var target = edge.targetNode;
      var dx = target.x - source.x;
      var dy = target.y - source.y;
      var distance = Math.max(0.01, Math.hypot(dx, dy));
      var attraction = edge.attraction || 1;
      var force = (distance - targetDistance(attraction)) * 0.018 * attraction * alpha;
      var fx = force * dx / distance;
      var fy = force * dy / distance;
      if (source.fx === null) { source.vx += fx; source.vy += fy; }
      if (target.fx === null) { target.vx -= fx; target.vy -= fy; }
    });
    for (var i = 0; i < nodes.length; i += 1) {
      for (var j = i + 1; j < nodes.length; j += 1) {
        var a = nodes[i];
        var b = nodes[j];
        var dx = b.x - a.x;
        var dy = b.y - a.y;
        var distance = Math.max(0.01, Math.hypot(dx, dy));
        var nx = dx / distance;
        var ny = dy / distance;
        var repulsion = Math.min(6, 2600 / (distance * distance)) * alpha;
        var overlap = a.collisionRadius + b.collisionRadius + 8 - distance;
        var separation = overlap > 0 ? overlap * 0.18 : 0;
        var force = repulsion + separation;
        if (a.fx === null) { a.vx -= force * nx; a.vy -= force * ny; }
        if (b.fx === null) { b.vx += force * nx; b.vy += force * ny; }
      }
    }
    var centerX = simulation.width / 2;
    var centerY = simulation.height / 2;
    var speed = 0;
    nodes.forEach(function (node) {
      if (node.fx !== null) {
        node.x = node.fx;
        node.y = node.fy;
        node.vx = 0;
        node.vy = 0;
        return;
      }
      node.vx += (centerX - node.x) * 0.0018 * alpha;
      node.vy += (centerY - node.y) * 0.0018 * alpha;
      node.vx *= 0.82;
      node.vy *= 0.82;
      var velocity = Math.hypot(node.vx, node.vy);
      if (velocity > 12) {
        node.vx *= 12 / velocity;
        node.vy *= 12 / velocity;
        velocity = 12;
      }
      node.x += node.vx;
      node.y += node.vy;
      speed += velocity;
    });
    simulation.alpha *= 0.985;
    var quiet = simulation.alpha < 0.02 && speed / Math.max(nodes.length, 1) < 0.03;
    simulation.stableTicks = quiet ? simulation.stableTicks + 1 : 0;
    simulation.stable = simulation.stableTicks >= 12;
    return simulation.stable;
  }

  function reheat(simulation) {
    simulation.alpha = 1;
    simulation.stableTicks = 0;
    simulation.stable = simulation.nodes.length < 2;
  }

  function settle(simulation, maxTicks) {
    var ticks = 0;
    while (!simulation.stable && ticks < (maxTicks || 1200)) {
      tick(simulation);
      ticks += 1;
    }
    return ticks;
  }

  return {
    nodeRadius: nodeRadius,
    targetDistance: targetDistance,
    createSimulation: createSimulation,
    tick: tick,
    reheat: reheat,
    settle: settle,
  };
}));
