## ADDED Requirements

### Requirement: Latest Paper presentation remains separate from historical evidence
Current question and Paper views SHALL use latest content/membership without exposing version selection. Historical execution views SHALL preserve the content, submitted answer, option text, verdict, feedback and available draft facts recorded for their original identities. Later edits SHALL NOT reopen or alter completed runs. A current Paper showing a replacement absent from a selected completed run SHALL identify it as unanswered in that run rather than attach a predecessor's answer. Removed or archived questions SHALL remain reachable through historical records.

#### Scenario: Replacement after completion
- **WHEN** completed Paper once contained A and current membership now contains B
- **THEN** current Paper shows B as not answered in that run, the run remains complete, and its historical records show A with its original answer

#### Scenario: Option text changes
- **WHEN** a submitted choice referred to the old B option and new content changes options
- **THEN** historical evidence retains the submitted old option text and verdict without interpreting it using the replacement's B

### Requirement: Removed drafts remain readable without becoming Attempts
Removing, replacing or archiving an unfinished item or archiving a Paper SHALL retain durably saved unsubmitted input and execution identity for history reads. Such input SHALL be labelled unsubmitted and SHALL NOT create Attempts, verdicts, feedback or learning effects. Unsaved browser-only input SHALL NOT be claimed as server-retained; a late rejected input SHALL remain recoverable locally without being rebound to another identity.

#### Scenario: Remove an item containing saved input
- **WHEN** an item with a saved draft is removed before submission
- **THEN** history exposes the draft as unsubmitted under its original identity and no learning record is fabricated

#### Scenario: Draft was never durably saved
- **WHEN** browser input races with replacement and its save is rejected
- **THEN** the UI retains recoverable local input and reports the conflict without claiming it exists in server history
