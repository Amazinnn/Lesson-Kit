# Change: Render Agent work as a readable execution plan

## Why

The Agent panel currently replaces its status line with raw provider event names such as
`turn.started` and `item.completed:command_execution`. This hides the actual sequence of
work, makes tool and CLI activity indistinguishable, and lets long status text displace the
conversation instead of helping the learner follow it.

## What Changes

- Normalize Codex and Claude tool, command, search, and turn lifecycle events into a small
  provider-neutral activity contract.
- Render each turn's activities as an in-flow execution plan with localized status, stable
  row updates, collapsible output, and bounded text layout.
- Keep the streamed assistant response as the ordinary answer bubble rather than mixing it
  into tool output.
- Store successful-turn activity records with the local conversation mirror so the plan is
  restored with the answer.
- Stop showing raw provider protocol labels in the status line.

## Scope

This change does not alter provider commands, learning-data writes, page context, or the
Agent panel's page-to-page visibility lifecycle.
