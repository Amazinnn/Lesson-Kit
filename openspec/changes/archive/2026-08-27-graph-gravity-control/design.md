## Context

The graph already has a center-attraction term in its zero-dependency simulation. It is currently fixed, so every layout uses the same compactness.

## Goals / Non-Goals

Expose that existing term as one small range input. Do not add presets, saved preferences, graph metrics, or a new settings panel.

## Decisions

The range is 0–100 and defaults to 30, mapping linearly to a gravity coefficient of 0–0.00117. Input changes reheat the current simulation; the value is not persisted.

## Risks / Trade-offs

- Zero gravity lets components drift → semantic springs and repulsion still keep the graph readable; fit remains available.
- Strong gravity can compact labels → existing circle clearance and always-visible label styling remain authoritative.
