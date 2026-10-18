## ADDED Requirements

### Requirement: Paper update approval pauses conversation dispatch

The Bridge SHALL retain an Agent-proposed existing-Paper update and its approval state in the existing conversation/turn artifacts without applying it. Before the proposing provider turn releases ownership to the next queued message, the Bridge SHALL persist the pending approval and pause that conversation's dispatch. Waiting for learner approval SHALL NOT keep a provider task running. While approval is pending, accepted messages SHALL remain queued with their captured context, and queue continuation or an interrupt routing choice SHALL NOT bypass the decision.

Only the page's explicit learner-approval operation SHALL apply this proposed update through the existing Paper preview/confirmation and update rules. A stale impact SHALL cause no write and require refreshed impact plus another learner click. Cancellation SHALL cause no Paper write. Both approval and cancellation SHALL retain older queued messages and leave continuation manual. Repeated approval attempts SHALL NOT apply the update or reset progress twice.

Pending approval SHALL survive page reload/reopen and service recovery with dispatch paused and no automatic approval or replay. Workspace, conversation, proposing turn, target Paper and operation revision SHALL scope each decision. This integration SHALL NOT alter historical attempts/ratings, question entities, unrelated Papers or the existing direct manual CLI contract.

#### Scenario: A proposes a Paper update with B/C queued
- **WHEN** provider turn A completes with a Paper update requiring approval while B/C are queued
- **THEN** its pending approval is persisted and dispatch is paused before ownership handoff; B/C do not start even with the browser closed

#### Scenario: Approval is resolved
- **WHEN** the learner approves or cancels the pending operation
- **THEN** only a current valid approval may write the target Paper, B/C remain retained and paused, and explicit continuation is required

#### Scenario: New work is accepted during approval
- **WHEN** another message is accepted while the conversation has a pending Paper approval
- **THEN** its text and submission context are retained without provider dispatch or implicit resolution of the approval

#### Scenario: Recover a pending operation
- **WHEN** the service recovers a conversation with a persisted pending Paper approval
- **THEN** the operation remains pending, the queue stays paused, and neither the Paper update nor a queued provider starts automatically
