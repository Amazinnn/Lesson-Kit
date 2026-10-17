## ADDED Requirements

### Requirement: Same-workspace middle navigation preserves the Agent rail

Navigating between pages and query states within one workspace SHALL update
only the middle page content and its route-owned lifecycle. The existing
`#ai-column` DOM and Agent controller SHALL remain mounted. Browser back and
forward SHALL follow the same behavior. Navigation SHALL update current page
context for future submissions while preserving the context already captured
by accepted work. External, cross-workspace, modified-click, download, and
explicitly targeted links SHALL keep native browser navigation.
The server-rendered `#ai-column` SHALL have the same structure on graph and
non-graph pages. Graph-only dashboard content SHALL belong to the graph middle
page, and selecting a graph node SHALL NOT hide or replace the Agent chat.

#### Scenario: Navigate within the workspace

- **WHEN** the learner follows a same-workspace page link from navigation, a
  page card, or middle content
- **THEN** the middle page changes while the existing Agent rail and its
  controller remain in place

#### Scenario: Navigate back or forward

- **WHEN** the learner uses browser Back or Forward after a same-workspace
  navigation
- **THEN** the middle page and its route-owned behavior change without
  rebuilding the Agent rail

#### Scenario: Send after navigating

- **WHEN** the learner sends a new message after changing the middle page
- **THEN** the request uses the current page context while previously accepted
  work retains its submitted context

#### Scenario: Enter and leave the graph page

- **WHEN** the learner enters or leaves the graph page within the same workspace
- **THEN** the graph dashboard mounts or disposes with the middle page while the
  same Agent rail remains visible and usable

#### Scenario: Follow a native navigation

- **WHEN** the learner uses a modified click, download, external link, or link
  to another workspace
- **THEN** the browser performs its normal navigation without middle-page
  interception
