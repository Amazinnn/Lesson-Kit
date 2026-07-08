# Signal Map Template

Signal Map is an optional user-feedback layer for Focus Map queries. It records
where the learner feels weak, confused, blocked, or unable to transfer a
concept. It is not a low-level relation source and must not rewrite audited
knowledge relations.

Default path:

```text
intermediate/{course}/signals/{chapter}/signal-map.json
```

## JSON Shape

```json
{
  "metadata": {
    "course": "dmath",
    "chapter": "ch06",
    "source": "reflection",
    "created_at": "2026-07-08"
  },
  "signals": [
    {
      "signal_id": "sig:dmath-ch06-kp-014:weak",
      "target_type": "node",
      "target_id": "dmath-ch06-kp-014",
      "signal_type": "weak_node",
      "weight": "high",
      "note": "I can quote the theorem but fail to choose it in coefficient problems.",
      "source": "reflection"
    },
    {
      "signal_id": "sig:relation-gap:001",
      "target_type": "relation",
      "target_id": "rel:dmath-ch06-kp-014:applies_to:dmath-ch06-kp-020",
      "signal_type": "transfer_failure",
      "weight": "medium",
      "note": "The theorem-to-problem jump is not automatic yet.",
      "source": "problem-review"
    }
  ]
}
```

## Allowed Values

`target_type`:

- `node`
- `relation`

`signal_type`:

- `weak_node`: the learner reports weak grasp of a knowledge point.
- `confusion`: the learner confuses this point with another point.
- `missing_prerequisite`: the current point exposes a missing earlier point.
- `transfer_failure`: the learner understands the point locally but fails to
  apply it elsewhere.
- `relation_gap`: the learner suspects a relationship but it is not yet
  audited as a durable knowledge relation.

`weight`:

- `high`
- `medium`
- `low`

## Rules

- Use Signal Map for learner-specific attention and later graph exploration.
- Use relation-insert-manifest.json for durable low-level point-to-point
  relationships.
- Keep prose notes concise. Longer reflections belong in normal learning logs
  and may be summarized into signals later.
- A signal may point to a relation that does not exist yet, but Focus Map can
  only attach relation signals to relation ids present in the current graph.
