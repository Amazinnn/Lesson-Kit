# Lesson Kit Design System

## 1. Visual direction

Lesson Kit is a calm, sunlit learning studio with a soft Mondrian vocabulary.
Warm paper, dark structural lines, and restrained blue, yellow, and red blocks
make learning state visible without turning the workbench into a dashboard.
The knowledge graph owns the richest motion; reading and practice surfaces stay
quiet and content-first.

Retro terminal details are limited to code, command output, and Agent activity.
They are a supporting texture rather than a second visual theme.

## 2. Color roles

| Token | Value | Role |
|---|---:|---|
| Paper | `#fffdf7` | Main canvas and readable surfaces |
| Paper shade | `#f3f1ea` | Recessed and secondary regions |
| Ink | `#171717` | Text, structure, focus, and selected outlines |
| Learning blue | `#2457c5` | Primary actions, long goals, and mastered state |
| Sun yellow | `#f2c94c` | Current stage, review state, and active highlights |
| Attention red | `#d6453d` | Needs-work state, overdue items, and failures |

Most screen area remains paper or neutral. Color never acts as the only state
indicator: text, outline, fill, or a geometric marker accompanies it.

## 3. Typography and overflow

- Interface stack: system UI, then `PingFang SC`, `Noto Sans CJK SC`, and
  `Microsoft YaHei`.
- Learning content: `16px / 26px`; controls: `14px / 22px`; compact metadata:
  `12px / 16px` or `13px / 20px`.
- Flex and grid content children use `min-width: 0`.
- Prose and user-authored titles use `overflow-wrap: anywhere`.
- Ellipsis is reserved for secondary one-line metadata. Knowledge titles,
  questions, and graph labels remain complete.
- Code, wide mathematics, and tables scroll inside their own surface instead
  of widening the page or Agent column.

## 4. Geometry and layout

- Existing left navigation, flexible middle page, and right Agent column remain
  the product frame.
- Dark one-pixel rules establish structure. Ordinary cards use `2px` to `6px`
  corners; conversational surfaces may remain softer.
- The goal calendar expresses time with horizontal lanes, the Agent expresses
  work with a vertical execution plan, and the graph expresses knowledge with
  free relationship lines.
- Floating middle-column tools overlay content without changing the three-column
  widths. They become drawers or sheets on narrow screens.

## 5. Interaction hierarchy

- Each practice phase exposes one primary action.
- Explicit rating submission remains the only practice action that writes a
  learning conclusion.
- Practice scope is shown as an explicit selected set and is never inferred
  from browsing, sorting, or filtering.
- Agent actions report visible progress and results without exposing hidden
  reasoning or raw provider protocol states.

## 6. Motion grammar

| Motion | Ordinary timing | Meaning |
|---|---:|---|
| Hover or focus response | `100–140ms` | Direct acknowledgement |
| Page-content entrance | `140–160ms` | Context changed |
| Compact feedback reveal | `160ms` | Practice phase advanced |
| Floating tray or drawer | `180–220ms` | A secondary surface opened |
| Graph projection | physical settling, normally `600–900ms` | Knowledge changed position |

Layout motion preserves object identity and current camera position. Stable
graphs schedule no recurring frame. Reduced-motion mode computes or reveals the
final state without progressive spatial animation.

## 7. Knowledge graph channels

- Relationship structure remains the default projection.
- The formal states remain `needs_work`, `review`, `mastered`, and an absent
  value. Student text is respectively `重点练习`, `可以复习`, `已掌握`, and
  `未标记`.
- In the state projection, attention priority runs from `needs_work` at the
  center through `review` and the absent value to `mastered` at the outside.
- Metric projections may redundantly encode a value through node area, distance
  from its group center, and a documented palette. A visible legend explains
  the active meaning.
- Filtering is independent from projection. Multiple selected categories may
  create multiple soft centers while retaining visible cross-group relations.

## 8. Delivery discipline

New surfaces first reuse these roles and rules, then receive a whole-workbench
composition pass after their behavior is stable. Visual polish does not invent
learning fields, reinterpret absent data, or alter Shell, Domain, Data, or
Bridge contracts.
