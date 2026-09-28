## ADDED Requirements

### Requirement: Named model entries

Bridge configuration SHALL support named model entries — a display name chosen
by the learner, a harness, a model id, and optional extra arguments — and the
provider picker SHALL present these entries by their display name, decoupled
from the harness and the raw model id. When no entries are configured the
picker SHALL fall back to one entry per discovered harness (the historical
behaviour). An entry whose harness is not discoverable SHALL be skipped rather
than breaking discovery.

#### Scenario: Entries replace the harness labels

- **WHEN** named model entries are configured and the learner opens the picker
- **THEN** each button shows the entry's own name, and creating a conversation from it records both the harness and the model

#### Scenario: The fallback keeps working

- **WHEN** no model entries are configured
- **THEN** the picker lists one entry per harness exactly as before

### Requirement: A conversation carries its model

A conversation SHALL record the model it runs on (chosen at creation or switched
later) and every turn SHALL launch with that model, overriding the harness
default. Switching the model SHALL take effect on the next turn, SHALL be
refused while a turn is running, and SHALL discard the cached RPC process so no
stale process keeps serving the old model. Switching SHALL keep the native
session id, and when the provider refuses a cross-model resume the bridge SHALL
start a fresh session once and disclose that in the conversation stream — the
local mirror's history SHALL be unaffected.

#### Scenario: The next turn runs on the switched model

- **WHEN** the conversation's model is switched and a new turn starts
- **THEN** the provider is launched with the new model and the mirror records it

#### Scenario: A cross-model resume failure is honest

- **WHEN** the provider refuses to resume the saved session under the new model
- **THEN** the bridge starts a fresh session for that turn, states so in the stream, and the mirror keeps the prior history
