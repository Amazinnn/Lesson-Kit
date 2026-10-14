## Context

See `proposal.md` for the user-visible problem. The desktop right column is a height-constrained flex layout; the provider picker currently keeps its intrinsic height, and its options have no scroll owner. The shared `.hidden` rule uses `!important` to control picker visibility.

## Goals / Non-Goals

**Goals:** Make the options list the native scroll area while preserving the picker heading and helper text.

**Non-Goals:** Change model selection, session creation, JavaScript event handling, or the existing narrow-screen drawer behavior.

## Decisions

- Make the visible picker a flex column that can shrink inside session controls, then let the options grid fill the remaining space with `min-height: 0` and `overflow-y: auto`. This gives native wheel input a bounded scroll owner. Keeping overflow on the outer column would move the heading out of view; JavaScript wheel handlers are unnecessary.
- Keep `.hidden { display: none !important; }` as the visibility authority. Use `align-content: start` so a short options list does not stretch its grid rows.

## Risks / Trade-offs

- **Narrow screens use the existing drawer scroll behavior** → leave the responsive column rule unchanged and verify the picker remains accessible there.
- **Few options could stretch to fill the available list area** → align grid content to the start and verify option button sizing.

## Migration Plan

No data or runtime migration is needed. Deploy the stylesheet change; restoring the prior stylesheet rolls it back.
