## ADDED Requirements

### Requirement: Paper pixel progress and confirmed-answer feedback

Paper practice SHALL display a pixel progress band whose completion reflects answered or stuck items in per-item mode and filled or stuck items in on-submit mode, never the cursor or correctness percentage. Its palette SHALL progress from deep orange through yellow to sky blue, using square cells and eight brightness levels. Equal-width compression and rarefaction bands SHALL travel horizontally, with denser regions brighter and the integrated grey-white end cell brightening as a compression arrives. Wave speed and contrast SHALL grow with completion.

A newly confirmed correct per-item answer SHALL bounce the visible question and option cards twice. Every five consecutive objective correct answers SHALL show the approved rectangular blue/yellow banner with smooth italic combo revealed by a paintbrush and a temporary alternate-color density band. Failed requests, navigation, archived review, self-rating, ungraded answers and on-submit drafts SHALL NOT trigger correct-answer or combo feedback.

#### Scenario: Cursor does not masquerade as completion
- **WHEN** a learner navigates to the last item without answering
- **THEN** pixel completion remains based on the answered or filled item states

#### Scenario: Confirmed per-item streak
- **WHEN** five consecutive objective correct answers have been confirmed in per-item mode
- **THEN** the combo banner appears once and does not change progress or create additional writes

### Requirement: Paper completion celebration settles into real results

After successful final submission and successful archived-run readback, the completion card SHALL enter prominently with colorful confetti behind it, then settle into the central completion view with actual counts and per-item status/review links below it. The same card SHALL remain in the result view. Existing review, retry, again and return actions SHALL remain usable. Loading an archived record or returning from review SHALL show the stable result without replay. A failed submission or failed readback SHALL NOT fabricate results or play successful celebration.

The Paper animation SHALL obey the existing motion preference: explicit on permits full motion, explicit off disables it, and the system reduced-motion preference disables continuous and ceremonial motion when no explicit on is set. Reduced motion SHALL immediately present the same stable card, accurate progress and results, with no confetti. Hidden documents SHALL stop scheduling animation frames; disposal on middle navigation SHALL cancel frames, timers, observers and transient decoration.

#### Scenario: Successful submit and settling
- **WHEN** final submission and archived readback succeed
- **THEN** the card celebrates once, settles, and the real item results become visible

#### Scenario: Reduced motion and historical review
- **WHEN** reduced motion is effective or an archived result is opened
- **THEN** the final card and real results are immediately available without ceremonial motion
