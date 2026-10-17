## ADDED Requirements

### Requirement: Accepted Agent messages survive failed turns
When a turn request includes a `submission_id`, the bridge SHALL persist the submitted user text, the original captured context, and stable submitted request fields in the existing turn artifact before launching the provider. Repeating that identity with the same submitted fields SHALL return the original turn without starting another provider execution, including while the original turn is running or has failed. Reusing the identity with changed submitted fields SHALL return a conflict. Duplicate resolution SHALL compare caller-submitted fields and SHALL NOT reject because server-derived context enrichment changed. Requests without `submission_id` SHALL retain their existing behavior.

Conversation history SHALL include accepted turn messages independently of successful transcript exchanges. A turn already represented by a legacy successful transcript SHALL appear exactly once. Failed turns SHALL expose only actual public partial output and their truthful terminal status; history SHALL NOT invent missing user text, assistant output, or legacy failures.

#### Scenario: Provider fails after acceptance
- **WHEN** the provider fails before producing an answer for an accepted turn
- **THEN** reopening history shows the original user text and failed status, with any actual public partial output

#### Scenario: Acceptance response is lost and retried
- **WHEN** the client repeats the same `submission_id` and submitted fields after an unknown response
- **THEN** the bridge returns the original turn without dispatching a second provider

#### Scenario: Same identity is reused with changed fields
- **WHEN** a request reuses a stored `submission_id` with different message or submitted context fields
- **THEN** the bridge returns a conflict and leaves the original turn unchanged

#### Scenario: Server enrichment changes before duplicate resolution
- **WHEN** the same submitted fields are retried after server-derived page enrichment has changed
- **THEN** the bridge returns the original turn and retains its originally captured context

#### Scenario: Read legacy successful history
- **WHEN** a conversation contains successful transcript exchanges created before this change
- **THEN** each exchange remains readable once and no missing failed-message text is synthesized
