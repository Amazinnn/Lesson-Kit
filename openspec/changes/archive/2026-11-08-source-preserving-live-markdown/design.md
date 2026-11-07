## Context
Existing browser richText and KaTeX implement the safe reading subset. All current long-text inputs are textareas; graph prototype uses a serializing rich-text editor.

## Goals / Non-Goals
Goals: exact source preservation, all formal long text, local assets, lifecycle compatibility.
Non-goals: short fields, new APIs/schema, unlock submitted answers, graph prototype redesign.

## Decisions
Use CodeMirror 6 text state plus Markdown syntax-tree block decorations; never serialize rich-text DOM. Expose the existing safe renderer rather than creating a second Markdown implementation. A textarea adapter preserves value, selection, focus and input events for callers, mirrors disabled/hidden state, observes dynamic insertion/removal and destroys detached editors. Standalone Vite library output contains no graph application entry. Existing Enter behavior remains with composition guard.

## Risks / Trade-offs
Block replacement must not disturb IME or cross-block selection. Rendering failures retain source. Large documents use CodeMirror view management. Browser acceptance must cover real selection, IME, queue lifecycle and navigation.

## Implementation sequence
1. Add failing source-preservation and integration tests.
2. Shared renderer access, editor, adapter and local build.
3. All long-text surfaces and readback, docs reconciliation.
4. Focused checks then independent full-suite/browser acceptance.
