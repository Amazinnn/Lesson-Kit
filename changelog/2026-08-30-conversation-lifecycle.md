# Recoverable conversation lifecycle

- Persisted `running` turns with no live workbench worker are now marked failed
  on first access, allowing the provider-locked conversation to continue after
  a server restart.
- Active in-process turns are tracked separately so normal polling is never
  mistaken for restart recovery.
- Provider cancellation and timeout now escalate from terminate to kill after
  a short grace period.
- Unexpected provider-thread failures are mirrored as literal failed turns
  instead of leaving a conversation permanently busy.
