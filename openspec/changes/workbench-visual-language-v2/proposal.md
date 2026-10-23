## Why

The workbench is functionally complete but visually inert, and the cause is now
clear: it reads as "cardboard" because every surface is the same flat gray rectangle
on the same warm paper. This is measurable, not a matter of taste:

- The two cues that could express depth are disabled at once. `--dsw-bg-layer-1`
  (`#fffefa`) differs from the page base (`#fffdf7`) by RGB `(0,−1,−3)`, and
  `--dsw-shadow-lv1` is `rgb(0 0 0 / 5%)` — so nothing can read as raised.
- Colour no longer decodes. 22 hard-coded hex values sit outside the token system
  (two blues, four reds, four oranges), so a learner cannot tell "click me" from
  "this is the current item".
- There is no type scale: body text is 14px and page titles are ~30px, with nothing
  between them, so learning content is not the visual anchor.
- `.muted` has no rule, so 39 empty states render identically to body text.
- Three `outline: none` declarations kill the global `:focus-visible` ring on every
  control on the main path; two grey levels fall below 4.5:1.
- Motion is effectively absent: 57 transitioned elements carry only
  `background-color 100ms` and `grid-template-columns 200ms`; `animationName` count is 0.

A first pass explored the opposite remedy — a more faithful "book" aesthetic with
paper texture, hairline rules and serif body text — and that exploration was
rejected. **Chasing a book-like, antique feel is itself a cause of the dullness.**
The direction that follows instead is a warm, modern, rounded interface with real
motion, in the spirit of the best learning software: warm ground instead of cold
white, generous 12px radii instead of tight corners, saturated primary-colour
accents instead of hairlines, and stillness replaced by celebration.

Now is the right time to fix this: the pool, the practice contract and the content
model are settled, and the remaining surface is presentation only. Refactoring it
later means re-doing it against a moving data contract.

## What Changes

- **A role-based token layer** replaces the copied "DeepSeek Harness" palette: one
  set of structural tokens plus two theme value sets (warm cream / night paper),
  applied through one switchable theme attribute. Layout, spacing, radius, elevation,
  typography, motion and z-index scales become explicit instead of emergent.
  The night-paper set covers the exercise pages, the knowledge-point pages, the
  records centre and the settings view; the knowledge graph page is out of scope
  (see "Explicitly out of scope" below).
- **A warm, rounded visual language**: warm cream ground (`#fdf8ef`), warm charcoal
  ink (`#221f1a`), a uniform 12px radius, four paper levels separated by radius and
  soft warm shadow rather than rules, and no background texture.
- **Colour discipline**: the 22 out-of-token hex values fold into the three existing
  semantic roles — learning blue (primary action, link, current selection),
  sunlight yellow (current item, review emphasis, streak progress), alert red
  (failure, blocked) — at higher saturation. No new hue, no fifth role.
- **Redundant state channels without words**: every state carries a colour plus a
  geometric cue (a status dot), never colour alone and never a pile of explanatory
  labels. The two principles the owner set directly — *prefer element and colour over
  annotation* and *graphics must be logically at home in their background* — are
  contract requirements, not preferences.
- **A pictographic asset language**: navigation uses hand-authored still-life SVGs
  (an open book, a stack of paper, a bookmark, a notebook, a node graph) on
  saturated circular grounds drawn only from the three role colours; empty states
  use still-life illustrations (vase, fruit basket, canvas, cup, books, lamp) in a
  loose sketch line with a pale watercolour wash. One SVG set serves both themes
  through CSS variables.
- **Dual typography**: reading surfaces (problem statements, knowledge-point body,
  solutions, long-form text) use a bundled serif; interface surfaces (navigation,
  buttons, tables, status chips, numerals) stay sans-serif; monospace remains a
  separate third family. Body text is 17px on 1.75 line height at a 38em measure.
- **Focus visibility and a contrast floor**: visible focus rings on every interactive
  control, and a 4.5:1 / 3:1 contrast requirement for body and secondary text.
- **A motion system**: explicit duration and easing scales; motion across four
  surfaces — interaction feedback, data visualisation, view transition and milestone
  ceremony — with a squash-and-stretch rebound, an upward fade-in entrance, a
  skeleton with a travelling highlight, and a layered completion celebration
  (rolling numbers, a progress band, geometric bursts, and paper flutter at
  milestones). No global background canvas, no cursor tracking, no parallax.
- **A theme transition with a narrative**: switching theme reveals a desk lamp that
  leans out and clicks on, and the ground colour change ripples outward from it.
- **Escalating streak feedback**: a three-tier streak indicator, a single
  parameterised banner that interjects at five and ten in a row, an animated streak
  progress form, and an explicit negative signal when a streak breaks past four.
- **A new middle-column settings view** holds appearance preferences — theme, reading
  face, motion and sound. The left rail opens and closes it. Preferences are browser
  preferences stored per workspace and write nothing to the pool.
- **A copy pass**: one consistent Chinese voice, with interface annotations deleted
  wherever they can be rather than restyled.
- **Density zoning**: reading surfaces stay generous; list and data surfaces tighten.
- **Shell repair**: the dead 128px `scope-tray` reservation (a retired feature) is
  removed, the three-column geometry is driven by one source of truth instead of a
  CSS rule that JavaScript silently overrides, the left rail gains icon-and-label
  navigation with a full-row selected block, the chapter lens becomes a self-drawn
  dropdown, and the hub page gains recent-use prominence and card hierarchy.
- **Records centre rebuilt as a data surface**: rounded card streams instead of
  bordered rows, an activity calendar that stops reading as a disabled spreadsheet,
  and a stat block with miniature charts.
- **A shared reading typographic layer** for Markdown, replacing the currently
  unattached `.rich-text` rules, and unifying the server-side and client-side
  Markdown renderers that currently emit different HTML for the same source.
- **A contract-drift register** is filed for the defects the audit surfaced. This
  change records them; it does not change their behaviour.

### Frozen (must not change)

Requests and payloads, persisted content, learning facts, state machines, and any
visibility switch driven by a request. Existing actions keep their meaning. No new
learning fact is introduced. Presentation-only additions must be inert to
hit-testing and must not alter focus order beyond the additions this proposal names.

### Explicitly out of scope

The knowledge graph page — entirely. This change does not touch it: not its
rendering, not its physics, not its layout seeds, and not its appearance in
either theme. The night-paper theme introduced here covers the exercise pages,
the knowledge-point pages, the records centre and the settings view; the graph's
own night-paper adaptation, together with the node visual redesign, belongs to
the separate `graph-node-visual-language` change (`decisions.md` A-8). Doing the
night adaptation here would touch the graph twice and leave an intermediate
state in which the graph is dark but its nodes are still the old ones.

The one thing this change still owes the graph is non-interference: the new
token layer must not damage it. The graph page is therefore a **negative
assertion** here (`acceptance.md` G-5) — before and after screenshots of the
graph page must be identical, because this change never went near it. The rule
that the graph must stay pixel-identical in the light theme binds the graph
change, not this one. The hard facts a graph change needs to know are collected
as a handover list in `design-notes/graph-isolation.md`.

## Capabilities

### New Capabilities
- `workbench-settings`: A middle-column settings view holding appearance preferences
  (theme, reading face, motion and sound), opened and closed from the left rail,
  persisted per workspace as browser preferences, writing nothing to the pool.

### Modified Capabilities
- `workbench-ui`: The visual foundation changes — warm rounded language, the
  three-role colour quota at higher saturation and removal of out-of-token colours,
  radius and elevation replacing rules, the dual-family type scale, redundant state
  channels, pictographic asset rules, focus visibility and contrast floors, the motion
  system across its four surfaces with its reduced-motion downgrade, the theme
  transition, the layered completion celebration, escalating streak feedback,
  density zoning, the shell and navigation grammar, the hub card hierarchy, the
  records-centre presentation, the empty-state pattern and the shared `.reading`
  typographic layer. The learner-settings requirement is extended so appearance
  preferences are reachable from the new settings view. The knowledge-graph page
  is outside this change: the token layer must leave the token values the graph
  depends on untouched, and the graph's own night-paper adaptation belongs to
  the `graph-node-visual-language` change.
- `calendar-workload`: The calendar and review-load view gains an explicit
  presentation contract — bar geometry, the motion applied when loads change, and the
  reduced-motion terminal state — while its content, thresholds and read-only
  guarantee stay as they are.

## Impact

- **Presentation assets**: `workbench/server/static/workbench.css` (1903 lines, the
  token layer and every surface rule), `agent-ui.css`, `kp-experience.css`.
- **Server-rendered structure**: `workbench/server/pages.py` (the practice page,
  knowledge-point pages, shell and the new settings view) and
  `workbench/server/records.py` (the records centre).
- **Client hooks**: `workbench/server/static/workbench.js`,
  `practice-flow.js`, `paper-practice.js`, `middle-navigation.js` — theme
  application, the settings view, motion and data-layer animation only.
- **New files**: a hand-authored SVG asset set (navigation still lifes, empty-state
  illustrations, the desk lamp); a settings-view stylesheet and script; bundled serif
  font files under `workbench/server/static/fonts/` (SIL Open Font License,
  redistributed with its licence file); short key-feedback audio. No new runtime
  dependency and no build step.
- **Serving**: `workbench/server/app.py` gains the settings route and the new static
  assets; cache headers must be reviewed so a stylesheet change is not masked by a
  stale cache.
- **Documents in the same delivery**: `docs/GLOSSARY.md` (the visual-language entry
  must be redefined, plus new terms: night paper, paper level, redundant state
  channel, theme preference, reading face, motion preference, workbench settings
  view, still-life illustration, lamp transition, and the two owner-set principles),
  `docs/PRODUCT-MANUAL.md` (the settings view and the copy pass),
  `docs/ACTION-GRAPH.md` (the settings view entry), `docs/ARCHITECTURE.md` (the
  static-asset layout and the settings view).
- **No schema change, no API change, no CLI change.** The pool schema, the JSON API
  surface and the `lesson-kit` command surface are untouched.
- **Known contract drift, recorded but not fixed here**: the advice rows and the daily
  plan queue have glossary entries but no UI outlet; "accuracy rate" is printed by the
  records centre but is not defined in the glossary and is listed as an `_Avoid_` term
  for coverage; the completed-practice count is limited to the most recent 100 rounds
  while the attempt count is unbounded. These are filed for a separate change.
