## Why

The workbench is functionally complete but visually inert: every surface is the same
flat gray rectangle on the same warm paper, so the product reads as "cardboard"
rather than as a finished learning instrument. This is not a taste complaint — it has
measurable causes in the current implementation:

- The two cues that could express depth are both disabled at once. `--dsw-bg-layer-1`
  (`#fffefa`) differs from the page base (`#fffdf7`) by RGB `(0,−1,−3)`, and
  `--dsw-shadow-lv1` is `rgb(0 0 0 / 5%)` — so nothing can read as raised.
- Colour no longer decodes. 22 hard-coded hex values sit outside the token system
  (two blues, four reds, four oranges), so a learner cannot tell "click me" from
  "this is the current item".
- There is no type scale. Body text is 14px and page titles are ~30px; nothing sits
  between them, so learning content is not the visual anchor.
- `.muted` has no rule, so 39 empty states render identically to body text.
- Three `outline: none` declarations kill the global `:focus-visible` ring on every
  control on the main path; two grey levels fall below 4.5:1.
- Motion is effectively absent: 57 transitioned elements carry only
  `background-color 100ms` and `grid-template-columns 200ms`; `animationName` count is 0.

Now is the right time to fix this: the pool, the practice contract, and the content
model are settled, and the remaining surface is presentation only. Refactoring it
later means re-doing it against a moving data contract.

## What Changes

- **A role-based token layer** replaces the copied "DeepSeek Harness" palette: one set
  of structural tokens plus two theme value sets (warm-paper light / night-paper dark),
  applied through one switchable theme attribute. Layout, spacing, radius, elevation,
  typography, motion and z-index scales become explicit instead of emergent.
- **A paper-layering model** replaces flat cards-on-paper. A surface has a defined
  level (page base, card, raised, ink block), a rule colour that is warm-derived rather
  than black-alpha, and an elevation that actually reads.
- **Colour discipline**: the 22 out-of-token hex values are folded into the five
  existing semantic roles (warm paper / ink / learning blue / sunlight yellow /
  alert red), each with an explicit usage quota. No new hue is introduced.
- **Dual typography**: reading surfaces (problem statements, knowledge-point body,
  solutions, long-form text, captions) use a bundled serif; interface surfaces
  (navigation, buttons, tables, status chips, numerals) stay sans-serif; monospace
  remains a separate third family for code.
- **State expression gets a redundant channel.** Every state carries geometry and text
  in addition to colour, closing the existing gap where Paper status dots and the
  unanswered answer-grid cells are distinguishable only by colour.
- **Focus visibility and a contrast floor**: visible focus rings on every interactive
  control, and a 4.5:1 / 3:1 contrast requirement for body and secondary text.
- **A motion system**: explicit duration and easing scales, and motion applied to the
  data-visualisation and status layer only (review-load bars, activity calendar, status
  indicators, loading and empty states). No global background canvas, no cursor
  tracking or parallax. `prefers-reduced-motion` downgrades every effect to a state
  cut.
- **A new middle-column settings view** holds appearance preferences — theme
  (light/dark), reading face (serif/sans), and motion on/off. The left rail opens and
  closes it. Preferences are browser preferences stored per workspace, and write
  nothing to the pool.
- **A copy pass**: one consistent Chinese voice across the interface, removing the
  current CN/EN mixing and function-describing phrasing.
- **Density zoning**: reading surfaces stay generous; list and data surfaces tighten.
  One page may hold both, decided by the nature of the content.
- **Shell repair**: the dead 128px `scope-tray` reservation (a retired feature) is
  removed, the three-column geometry is driven by one source of truth instead of a CSS
  rule that JavaScript silently overrides, the left rail gains a navigation grammar,
  and the hub page's workspace cards gain real information hierarchy.
- **Records centre rebuilt as a data surface**: real tables instead of 98 individually
  bordered cards, an activity calendar that stops reading as a disabled spreadsheet,
  and a stat block with actual hierarchy.
- **A `.reading` typographic layer** for Markdown, replacing the currently
  unattached `.rich-text` rules, and unifying the server-side and client-side Markdown
  renderers that currently emit different HTML for the same source.
- **A contract-drift register** is filed for the defects the audit surfaced. This
  change records them; it does not change their behaviour.

### Frozen (must not change)

Requests and payloads, persisted content, learning facts, state machines, and any
visibility switch driven by a request. Existing actions keep their meaning. No new
learning fact is introduced. Presentation-only additions must be inert to hit-testing
and must not alter focus order beyond the additions this proposal names.

### Explicitly out of scope

The knowledge graph page. Its rendering, physics, layout seeds and appearance stay
exactly as they are; the new token layer must leave graph-dependent token values
untouched so the graph page is visually unchanged by this change.

## Capabilities

### New Capabilities
- `workbench-settings`: A middle-column settings view holding appearance preferences
  (theme, reading face, motion), opened and closed from the left rail, persisted per
  workspace as browser preferences, writing nothing to the pool.

### Modified Capabilities
- `workbench-ui`: The visual foundation changes — paper layering and elevation, the
  five-role colour quota and removal of out-of-token colours, the dual-family type
  scale, redundant state channels, focus visibility and contrast floors, the motion
  system with its reduced-motion downgrade, density zoning, the shell and navigation
  grammar, the hub card hierarchy, the records-centre presentation, and the shared
  `.reading` typographic layer. The learner-settings requirement is extended so the
  appearance preferences are reachable from the new settings view.
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
  `practice-flow.js`, `paper-practice.js`, `middle-navigation.js` — theme application,
  the settings view, and data-layer motion only.
- **New files**: a settings-view stylesheet and script; bundled serif font files under
  `workbench/server/static/fonts/` (SIL Open Font License, redistributed with its
  licence file); no new runtime dependency.
- **Serving**: `workbench/server/app.py` gains the settings route and the new static
  assets; cache headers must be reviewed so a stylesheet change is not masked by a
  stale cache.
- **Documents in the same delivery**: `docs/GLOSSARY.md` (new terms: the refined
  visual language, night paper, paper levels, theme preference), `docs/PRODUCT-MANUAL.md`
  (the settings view and the copy pass), `docs/ACTION-GRAPH.md` (the settings view
  entry), `docs/ARCHITECTURE.md` (the static-asset layout and the settings view).
- **No schema change, no API change, no CLI change.** The pool schema, the JSON API
  surface and the `lesson-kit` command surface are untouched.
- **Known contract drift, recorded but not fixed here**: the advice rows and the daily
  plan queue have glossary entries but no UI outlet; "accuracy rate" is printed by the
  records centre but is not defined in the glossary and is listed as an `_Avoid_` term
  for coverage; the completed-practice count is limited to the most recent 100 rounds
  while the attempt count is unbounded. These are filed for a separate change.
