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

  // A wrapped label hangs below the node and occupies layout space; the
  // collision footprint must cover it or neighbouring labels overlap.
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
    var label = String(title || "").trim();
    var lines = labelLineCount(label);
    return Math.min(150, radius + 6 + lines * 16);
  }

  function targetDistance(attraction, sourceRadius, targetRadius, distanceFactor) {
    var normalized = Math.max(0, Math.min(1, ((attraction || 1) - 0.75) / 1.125));
    var gap = (144 - 72 * normalized) * (distanceFactor || 1);
    return (sourceRadius || 0) + (targetRadius || 0) + gap;
  }

  function createSimulation(sourceNodes, sourceEdges, width, height, positions) {
    width = Math.max(240, width || 800);
    height = Math.max(180, height || 600);
    var centerX = width / 2;
    var centerY = height / 2;
    var spread = Math.min(width, height) * 0.3;
    var nodes = sourceNodes.map(function (source, index) {
      var angle = index * 2.399963229728653;
      var distance = spread * Math.sqrt((index + 1) / Math.max(sourceNodes.length, 1));
      var position = positions && positions.get(source.id);
      var radius = nodeRadius(source.problem_count);
      return Object.assign({}, source, {
        radius: radius,
        structureRadius: radius,
        targetRadius: radius,
        collisionRadius: collisionRadius(radius, source.title),
        x: position ? position.x : centerX + Math.cos(angle) * distance,
        y: position ? position.y : centerY + Math.sin(angle) * distance,
        vx: 0, vy: 0, fx: null, fy: null,
        anchorX: null, anchorY: null,
        projectionTargetX: null, projectionTargetY: null,
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
      gravity: 0.000351, projection: "structure",
    };
  }

  function clampNode(node, simulation) {
    var bounds = simulation.bounds || {
      minX: 0, maxX: simulation.width, minY: 0, maxY: simulation.height,
    };
    var radius = node.collisionRadius || node.radius || 8;
    node.x = Math.max(bounds.minX + radius, Math.min(bounds.maxX - radius, node.x));
    node.y = Math.max(bounds.minY + radius, Math.min(bounds.maxY - radius, node.y));
  }

  function tickOne(simulation) {
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
      var desiredDistance = targetDistance(
        attraction, source.radius, target.radius, edge.distanceFactor || 1,
      );
      var projectionSpring = simulation.projection === "structure" ? 1 : 0.24;
      var force = (distance - desiredDistance) * 0.014 * attraction * alpha * projectionSpring;
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
        var repulsion = Math.min(6, 3200 / (distance * distance)) * alpha;
        var overlap = a.radius + b.radius + 24 - distance;
        var separation = overlap > 0 ? overlap * 0.28 : 0;
        var force = repulsion + separation;
        if (a.fx === null) { a.vx -= force * nx; a.vy -= force * ny; }
        if (b.fx === null) { b.vx += force * nx; b.vy += force * ny; }
      }
    }
    var centerX = simulation.centerX === undefined ? simulation.width / 2 : simulation.centerX;
    var centerY = simulation.centerY === undefined ? simulation.height / 2 : simulation.centerY;
    var speed = 0;
    nodes.forEach(function (node) {
      if (node.fx !== null) {
        node.x = node.fx;
        node.y = node.fy;
        node.vx = 0;
        node.vy = 0;
        return;
      }
      node.vx += (centerX - node.x) * simulation.gravity * alpha;
      node.vy += (centerY - node.y) * simulation.gravity * alpha;
      if (node.componentAnchorX !== undefined) {
        node.vx += (node.componentAnchorX - node.x) * 0.00022 * alpha;
        node.vy += (node.componentAnchorY - node.y) * 0.00022 * alpha;
      }
      if (node.anchorX !== null) {
        node.vx += (node.anchorX - node.x) * 0.012 * alpha;
        node.vy += (node.anchorY - node.y) * 0.012 * alpha;
      }
      if (node.projectionTargetX !== null) {
        node.vx += (node.projectionTargetX - node.x) * 0.045 * alpha;
        node.vy += (node.projectionTargetY - node.y) * 0.045 * alpha;
      }
      if (node.targetRadius !== undefined) {
        node.radius += (node.targetRadius - node.radius) * (0.06 + alpha * 0.16);
        if (Math.abs(node.targetRadius - node.radius) < 0.05) node.radius = node.targetRadius;
        node.collisionRadius = collisionRadius(node.radius, node.title);
      }
      node.vx *= 0.84;
      node.vy *= 0.84;
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
    simulation.alpha *= 0.986;
    var quiet = simulation.alpha < 0.035 && speed / Math.max(nodes.length, 1) < 0.3;
    simulation.stableTicks = quiet ? simulation.stableTicks + 1 : 0;
    simulation.stable = simulation.stableTicks >= 8;
    return simulation.stable;
  }

  function resolveCollisions(nodes, width, height, rounds) {
    function moveAway(node, other, x, y) {
      var choices = [[x, y], [-y, x], [y, -x]];
      var best = choices[0];
      var bestDistance = -Infinity;
      choices.forEach(function (choice) {
        var trial = { x: node.x + choice[0], y: node.y + choice[1], radius: node.radius,
          collisionRadius: node.collisionRadius };
        clampNode(trial, { width: width, height: height });
        var distance = Math.hypot(trial.x - other.x, trial.y - other.y);
        if (distance > bestDistance) {
          best = choice;
          bestDistance = distance;
        }
      });
      node.x += best[0];
      node.y += best[1];
      clampNode(node, { width: width, height: height });
    }
    for (var round = 0; round < rounds; round += 1) {
      var moved = false;
      for (var i = 0; i < nodes.length; i += 1) {
        for (var j = i + 1; j < nodes.length; j += 1) {
          var a = nodes[i];
          var b = nodes[j];
          var dx = b.x - a.x;
          var dy = b.y - a.y;
          var distance = Math.hypot(dx, dy);
          var minimum = (a.collisionRadius || a.radius || 8) + (b.collisionRadius || b.radius || 8) + 4;
          if (distance >= minimum) continue;
          var angle = distance < 0.01 ? (i * 7 + j * 11) : Math.atan2(dy, dx);
          var shift = (minimum - Math.max(distance, 0.01)) / 2;
          var moveX = Math.cos(angle) * shift;
          var moveY = Math.sin(angle) * shift;
          if (a._layoutComponent !== b._layoutComponent) {
            if (a._layoutComponent > b._layoutComponent && a.fx === null) {
              moveAway(a, b, -moveX * 2, -moveY * 2);
            } else if (b._layoutComponent > a._layoutComponent && b.fx === null) {
              moveAway(b, a, moveX * 2, moveY * 2);
            }
          } else {
            if (a.fx === null) { a.x -= moveX; a.y -= moveY; }
            if (b.fx === null) { b.x += moveX; b.y += moveY; }
          }
          clampNode(a, { width: width, height: height });
          clampNode(b, { width: width, height: height });
          moved = true;
        }
      }
      if (!moved) return;
    }
  }

  function relocateCrowdedNodes(nodes, width, height) {
    nodes.forEach(function (node, index) {
      var radius = node.collisionRadius || node.radius || 8;
      var crowded = nodes.some(function (other, otherIndex) {
        if (index === otherIndex) return false;
        if (other._layoutComponent > node._layoutComponent
          || (other._layoutComponent === node._layoutComponent && otherIndex > index)) return false;
        var otherRadius = other.collisionRadius || other.radius || 8;
        return Math.hypot(node.x - other.x, node.y - other.y) < radius + otherRadius;
      });
      if (!crowded) return;
      for (var y = radius; y <= height - radius; y += 12) {
        for (var x = radius; x <= width - radius; x += 12) {
          var clear = nodes.every(function (other, otherIndex) {
            if (index === otherIndex) return true;
            if (other._layoutComponent > node._layoutComponent
              || (other._layoutComponent === node._layoutComponent && otherIndex > index)) return true;
            var otherRadius = other.collisionRadius || other.radius || 8;
            return Math.hypot(x - other.x, y - other.y) >= radius + otherRadius + 2;
          });
          if (clear) {
            node.x = x;
            node.y = y;
            return;
          }
        }
      }
    });
  }

  function tick(simulation) {
    return tickOne(simulation);
  }

  function reheat(simulation, alpha) {
    simulation.alpha = alpha === undefined ? 1 : alpha;
    simulation.stableTicks = 0;
    simulation.stable = simulation.nodes.length < 2;
  }

  function setSoftAnchor(node, x, y) {
    node.anchorX = x;
    node.anchorY = y;
  }

  function setGravity(simulation, value) {
    simulation.gravity = Math.max(0, Math.min(100, Number(value) || 0)) / 100 * 0.00351;
    reheat(simulation, 0.5);
  }

  function projectionValue(node, projection) {
    if (projection === "problem_count") return Math.max(0, Number(node.problem_count) || 0);
    if (projection === "importance") return node.importance === "core" ? 1 : 0;
    if (projection === "state") {
      return node.state === "needs_work" ? 1 : node.state === "review" ? 0.66
        : node.state === "mastered" ? 0 : 0.33;
    }
    if (projection === "attraction") return Math.max(0, Number(node.attraction) || 0);
    return 0;
  }

  function applyProjection(nodes, projection, width, height, structurePositions) {
    if (!nodes.length) return nodes;
    if (!projection || projection === "structure") {
      nodes.forEach(function (node) {
        var position = structurePositions && structurePositions.get(node.id);
        node.projection = "structure";
        node.projectionScore = 0;
        node.targetRadius = node.structureRadius || nodeRadius(node.problem_count);
        node.projectionTargetX = position ? position.x : null;
        node.projectionTargetY = position ? position.y : null;
        node.vx = (node.vx || 0) * 0.25;
        node.vy = (node.vy || 0) * 0.25;
      });
      return nodes;
    }
    var values = nodes.map(function (node) { return projectionValue(node, projection); });
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    var span = max - min;
    var centerX = Math.max(240, width || 800) / 2;
    var centerY = Math.max(180, height || 600) / 2;
    var base = Math.min(Math.max(180, width || 800), Math.max(140, height || 600)) * 0.34;
    var ranked = nodes.slice().sort(function (a, b) {
      var difference = projectionValue(b, projection) - projectionValue(a, projection);
      return difference || String(a.id).localeCompare(String(b.id));
    });
    var topIsUnique = ranked.length === 1
      || projectionValue(ranked[0], projection) > projectionValue(ranked[1], projection);
    ranked.forEach(function (node, index) {
        var score = span ? (projectionValue(node, projection) - min) / span : 0.5;
        var angle = Math.max(0, index - (topIsUnique ? 1 : 0)) * 2.399963229728653;
        var distance = topIsUnique && index === 0 ? 0 : base * (0.2 + (1 - score) * 0.8);
        node.projection = projection;
        node.projectionScore = score;
        node.targetRadius = metricRadius(score);
        node.projectionTargetX = centerX + Math.cos(angle) * distance;
        node.projectionTargetY = centerY + Math.sin(angle) * distance;
        node.vx = (node.vx || 0) * 0.25;
        node.vy = (node.vy || 0) * 0.25;
      });
    return nodes;
  }

  function setProjection(simulation, projection, width, height, structurePositions) {
    simulation.projection = projection || "structure";
    applyProjection(simulation.nodes, simulation.projection, width, height, structurePositions);
    reheat(simulation, 0.82);
    return simulation;
  }

  function settle(simulation, maxTicks) {
    var ticks = 0;
    while (!simulation.stable && ticks < (maxTicks || 1200)) {
      tick(simulation);
      ticks += 1;
    }
    return ticks;
  }

  function connectedComponents(sourceNodes, sourceEdges) {
    var byId = new Map(sourceNodes.map(function (node) { return [node.id, node]; }));
    var neighbors = new Map(sourceNodes.map(function (node) { return [node.id, []]; }));
    sourceEdges.forEach(function (edge) {
      if (!byId.has(edge.source) || !byId.has(edge.target)) return;
      neighbors.get(edge.source).push(edge.target);
      neighbors.get(edge.target).push(edge.source);
    });
    var visited = new Set();
    return sourceNodes.map(function (node) {
      if (visited.has(node.id)) return null;
      var ids = new Set();
      var pending = [node.id];
      visited.add(node.id);
      while (pending.length) {
        var id = pending.shift();
        ids.add(id);
        neighbors.get(id).forEach(function (neighbor) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            pending.push(neighbor);
          }
        });
      }
      return {
        nodes: sourceNodes.filter(function (candidate) { return ids.has(candidate.id); }),
        edges: sourceEdges.filter(function (edge) {
          return ids.has(edge.source) && ids.has(edge.target);
        }),
      };
    }).filter(Boolean);
  }

  function candidateLayouts(sourceNodes, width, height) {
    var centerX = Math.max(240, width || 800) / 2;
    var centerY = Math.max(180, height || 600) / 2;
    var count = Math.max(sourceNodes.length, 1);
    var spread = Math.min(width || 800, height || 600) * 0.28;
    var columns = Math.ceil(Math.sqrt(count));
    var rows = Math.ceil(count / columns);
    var layouts = ["ring", "grid", "rows", "columns", "spiral", "golden"];
    return layouts.map(function (name) {
      return {
        name: name,
        nodes: sourceNodes.map(function (source, index) {
          var x = centerX;
          var y = centerY;
          var angle;
          if (name === "ring") {
            angle = (Math.PI * 2 * index) / count - Math.PI / 2;
            x += Math.cos(angle) * spread;
            y += Math.sin(angle) * spread;
          } else if (name === "grid") {
            x += (index % columns - (columns - 1) / 2) * spread * 1.35 / columns;
            y += (Math.floor(index / columns) - (rows - 1) / 2) * spread * 1.35 / rows;
          } else if (name === "rows") {
            x += (index - (count - 1) / 2) * spread * 1.65 / Math.max(count - 1, 1);
          } else if (name === "columns") {
            y += (index - (count - 1) / 2) * spread * 1.65 / Math.max(count - 1, 1);
          } else if (name === "spiral") {
            angle = index * Math.PI * 0.8;
            x += Math.cos(angle) * spread * (index + 1) / count;
            y += Math.sin(angle) * spread * (index + 1) / count;
          } else {
            angle = index * 2.399963229728653;
            x += Math.cos(angle) * spread * Math.sqrt((index + 1) / count);
            y += Math.sin(angle) * spread * Math.sqrt((index + 1) / count);
          }
          return { id: source.id, x: x, y: y };
        }),
      };
    });
  }

  function segmentsClutter(a, b, c, d) {
    function turn(p, q, r) {
      return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x);
    }
    function pointDistance(point, start, end) {
      var dx = end.x - start.x;
      var dy = end.y - start.y;
      var length = dx * dx + dy * dy;
      if (!length) return Math.hypot(point.x - start.x, point.y - start.y);
      var ratio = Math.max(0, Math.min(1, ((point.x - start.x) * dx + (point.y - start.y) * dy) / length));
      return Math.hypot(point.x - start.x - ratio * dx, point.y - start.y - ratio * dy);
    }
    var abC = turn(a, b, c);
    var abD = turn(a, b, d);
    var cdA = turn(c, d, a);
    var cdB = turn(c, d, b);
    if (abC * abD < 0 && cdA * cdB < 0) return true;
    return Math.min(pointDistance(a, c, d), pointDistance(b, c, d),
      pointDistance(c, a, b), pointDistance(d, a, b)) <= 3;
  }

  function scoreLayout(nodes, edges) {
    var byId = new Map(nodes.map(function (node) { return [node.id, node]; }));
    var crossings = 0;
    for (var i = 0; i < edges.length; i += 1) {
      for (var j = i + 1; j < edges.length; j += 1) {
        var first = edges[i];
        var second = edges[j];
        if (first.source === second.source || first.source === second.target
          || first.target === second.source || first.target === second.target) continue;
        if (segmentsClutter(byId.get(first.source), byId.get(first.target),
          byId.get(second.source), byId.get(second.target))) crossings += 1;
      }
    }
    var labelCollisions = 0;
    for (var a = 0; a < nodes.length; a += 1) {
      for (var b = a + 1; b < nodes.length; b += 1) {
        var radiusA = nodes[a].collisionRadius || nodes[a].radius || 8;
        var radiusB = nodes[b].collisionRadius || nodes[b].radius || 8;
        if (Math.hypot(nodes[a].x - nodes[b].x, nodes[a].y - nodes[b].y) < radiusA + radiusB) {
          labelCollisions += 1;
        }
      }
    }
    var minX = Infinity;
    var maxX = -Infinity;
    var minY = Infinity;
    var maxY = -Infinity;
    nodes.forEach(function (node) {
      var radius = node.collisionRadius || node.radius || 8;
      minX = Math.min(minX, node.x - radius);
      maxX = Math.max(maxX, node.x + radius);
      minY = Math.min(minY, node.y - radius);
      maxY = Math.max(maxY, node.y + radius);
    });
    return {
      crossings: crossings,
      labelCollisions: labelCollisions,
      waste: nodes.length ? (maxX - minX) * (maxY - minY) : 0,
    };
  }

  function chooseBestLayout(candidates) {
    return candidates.reduce(function (best, candidate) {
      if (!best) return candidate;
      var a = candidate.score;
      var b = best.score;
      if (a.crossings !== b.crossings) return a.crossings < b.crossings ? candidate : best;
      if (a.labelCollisions !== b.labelCollisions) return a.labelCollisions < b.labelCollisions ? candidate : best;
      return a.waste < b.waste ? candidate : best;
    }, null);
  }

  function packComponents(components, width, height) {
    width = Math.max(240, width || 800);
    height = Math.max(180, height || 600);
    var packed = [];
    components.slice().sort(function (a, b) { return b.nodes.length - a.nodes.length; })
      .forEach(function (component, componentIndex) {
      var minX = Infinity;
      var maxX = -Infinity;
      var minY = Infinity;
      var maxY = -Infinity;
      component.nodes.forEach(function (node) {
        var radius = node.collisionRadius || node.radius || 8;
        minX = Math.min(minX, node.x - radius);
        maxX = Math.max(maxX, node.x + radius);
        minY = Math.min(minY, node.y - radius);
        maxY = Math.max(maxY, node.y + radius);
      });
      var oldCenterX = (minX + maxX) / 2;
      var oldCenterY = (minY + maxY) / 2;
      var scale = Math.min(1, width / (maxX - minX), height / (maxY - minY));
      var placed = null;
      [0, Math.PI / 2].some(function (rotation) {
        var cosine = Math.cos(rotation);
        var sine = Math.sin(rotation);
        var relative = component.nodes.map(function (node) {
          var x = (node.x - oldCenterX) * scale;
          var y = (node.y - oldCenterY) * scale;
          return { node: node, x: x * cosine - y * sine, y: x * sine + y * cosine };
        });
        for (var y = 8; y <= height - 8 && !placed; y += 12) {
          for (var x = 8; x <= width - 8 && !placed; x += 12) {
            var positions = relative.map(function (item) {
              return { node: item.node, x: x + item.x, y: y + item.y };
            });
            var fits = positions.every(function (position) {
              var radius = position.node.collisionRadius || position.node.radius || 8;
              if (position.x - radius < 0 || position.x + radius > width
                || position.y - radius < 0 || position.y + radius > height) return false;
              return packed.every(function (other) {
                var otherRadius = other.collisionRadius || other.radius || 8;
                return Math.hypot(position.x - other.x, position.y - other.y) >= radius + otherRadius + 24;
              });
            });
            if (fits) placed = positions;
          }
        }
        return Boolean(placed);
      });
      if (!placed) {
        placed = component.nodes.map(function (node) {
          return { node: node, x: width / 2 + (node.x - oldCenterX) * scale,
            y: height / 2 + (node.y - oldCenterY) * scale };
        });
      }
      var centerX = 0;
      var centerY = 0;
      var placedMinX = Infinity;
      var placedMaxX = -Infinity;
      var placedMinY = Infinity;
      var placedMaxY = -Infinity;
      placed.forEach(function (position) {
        var node = position.node;
        node.x = position.x;
        node.y = position.y;
        node.vx *= scale;
        node.vy *= scale;
        node._layoutComponent = componentIndex;
        clampNode(node, { width: width, height: height });
        packed.push(node);
        centerX += node.x;
        centerY += node.y;
        var radius = node.collisionRadius || node.radius || 8;
        placedMinX = Math.min(placedMinX, node.x - radius);
        placedMaxX = Math.max(placedMaxX, node.x + radius);
        placedMinY = Math.min(placedMinY, node.y - radius);
        placedMaxY = Math.max(placedMaxY, node.y + radius);
      });
      component.centerX = centerX / component.nodes.length;
      component.centerY = centerY / component.nodes.length;
      component.bounds = {
        minX: Math.max(0, placedMinX), maxX: Math.min(width, placedMaxX),
        minY: Math.max(0, placedMinY), maxY: Math.min(height, placedMaxY),
      };
    });
    return packed;
  }

  function bestComponentLayout(component, width, height, maxTicks) {
    var candidates = candidateLayouts(component.nodes, width, height).map(function (layout) {
      var positions = new Map(layout.nodes.map(function (node) { return [node.id, node]; }));
      var simulation = createSimulation(component.nodes, component.edges, width, height, positions);
      settle(simulation, maxTicks);
      return { name: layout.name, simulation: simulation, score: scoreLayout(simulation.nodes, component.edges) };
    });
    return chooseBestLayout(candidates);
  }

  function layoutGraph(sourceNodes, sourceEdges, width, height, maxTicks) {
    var layoutWidth = Math.max(1200, width || 800);
    var layoutHeight = Math.max(800, height || 600);
    var layouts = connectedComponents(sourceNodes, sourceEdges).map(function (component) {
      if (component.nodes.length < 2) {
        return { component: component,
          simulation: createSimulation(component.nodes, component.edges, layoutWidth, layoutHeight) };
      }
      var best = bestComponentLayout(component, layoutWidth, layoutHeight, maxTicks);
      return { component: component, simulation: best.simulation, score: best.score, candidate: best.name };
    });
    var seededNodes = packComponents(layouts.map(function (layout) { return layout.simulation; }),
      layoutWidth, layoutHeight);
    resolveCollisions(seededNodes, layoutWidth, layoutHeight, 120);
    relocateCrowdedNodes(seededNodes, layoutWidth, layoutHeight);
    var positions = new Map(seededNodes.map(function (node) {
      return [node.id, { x: node.x, y: node.y }];
    }));
    var componentCenters = new Map();
    seededNodes.forEach(function (node) {
      if (!componentCenters.has(node._layoutComponent)) {
        componentCenters.set(node._layoutComponent, { x: 0, y: 0, count: 0 });
      }
      var center = componentCenters.get(node._layoutComponent);
      center.x += node.x;
      center.y += node.y;
      center.count += 1;
    });
    var unified = createSimulation(sourceNodes, sourceEdges, layoutWidth, layoutHeight, positions);
    var seededById = new Map(seededNodes.map(function (node) { return [node.id, node]; }));
    unified.nodes.forEach(function (node) {
      var seeded = seededById.get(node.id);
      var center = componentCenters.get(seeded._layoutComponent);
      node._layoutComponent = seeded._layoutComponent;
      node.componentAnchorX = center.x / center.count;
      node.componentAnchorY = center.y / center.count;
    });
    unified.seedComponents = layouts.map(function (layout) {
      return { candidate: layout.candidate || "isolate", score: layout.score || null,
        nodeIds: layout.component.nodes.map(function (node) { return node.id; }) };
    });
    return unified;
  }

  return {
    nodeRadius: nodeRadius,
    metricRadius: metricRadius,
    labelLineCount: labelLineCount,
    collisionRadius: collisionRadius,
    targetDistance: targetDistance,
    createSimulation: createSimulation,
    tick: tick,
    reheat: reheat,
    setSoftAnchor: setSoftAnchor,
    setGravity: setGravity,
    projectionValue: projectionValue,
    applyProjection: applyProjection,
    setProjection: setProjection,
    settle: settle,
    connectedComponents: connectedComponents,
    candidateLayouts: candidateLayouts,
    scoreLayout: scoreLayout,
    chooseBestLayout: chooseBestLayout,
    packComponents: packComponents,
    bestComponentLayout: bestComponentLayout,
    layoutGraph: layoutGraph,
  };
}));
