# Proposal: disclose-ignored-action-blocks

## Why

Owner acceptance (conv-023, provider Claude) exposed two defects working
together: the bridge parser read only the FIRST lessonkit-action block, and the
frontend intent regex missed the natural phrasing 「补两张闪卡」. The reply's
manifest was silently dropped and the agent then claimed — twice, in prose —
that cards had been written. Nothing was written. A silently ignored action
block is the same honesty failure the bridge spec already forbids for
malformed blocks.

## What Changes

- The bridge parses EVERY lessonkit-action block in a reply and applies the
  first one matching the active intent, instead of only the first block.
- Blocks that match no intent are stripped from the mirrored answer and an
  ignored disclosure is recorded; the next turn's provider context states that
  nothing was written, so the agent cannot claim phantom writes.
- The frontend check-intent detection accepts natural card/quiz phrasing
  (「补两张闪卡」「生成几道微题」) without matching ordinary discussion.

## Impact

- specs: ai-teacher-bridge (+1 requirement)
- code: workbench/bridge/conversations.py, workbench/server/static/workbench.js
