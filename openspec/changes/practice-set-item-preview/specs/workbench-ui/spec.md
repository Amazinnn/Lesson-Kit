## ADDED Requirements

### Requirement: Saved paper items preview their problem

The 组卷 page SHALL let a learner read the problems a saved paper holds without
leaving the page. Each item SHALL be an expandable block whose summary keeps the
index, title and reorder/remove controls it has today, and whose opened body
shows the problem's full text together with its recorded source line when one
exists. The body SHALL render through the same safe Markdown subset as the
knowledge point page's linked problems, so mathematics, figures and code render
identically on both surfaces. Items SHALL arrive collapsed, and the disclosure
affordance SHALL be visible on every item. Expanding an item SHALL change
nothing about the paper: the preview is a reading surface, never a second
editor.

#### Scenario: Read one problem of a saved paper

- **WHEN** a learner opens an item of a saved paper card
- **THEN** the problem's own text appears under the item title, with its source
  line when one is recorded

#### Scenario: A long paper stays scannable

- **WHEN** a saved paper holds dozens of problems
- **THEN** every item is collapsed on arrival and the card lists titles only

#### Scenario: Preview does not disturb the paper

- **WHEN** items are expanded and the learner then moves or removes items
- **THEN** those controls act on the same item rows as before, and only the
  saved order changes

### Requirement: Saved paper cards fold

The 组卷 page SHALL present every saved paper as a foldable card: the head — the
paper's title, its size, and its controls — stays visible while the problem list
folds away beneath it. Cards SHALL arrive folded, so the page reads as the
learner's papers rather than the concatenation of their problems. Within a
browser tab, a card the learner opened SHALL come back open after the reload an
edit performs: moving or removing items must not require re-opening the paper
after every click. Folding SHALL be a reading state only — opening or closing a
card sends no request and changes no stored order. A control in the head SHALL
act on the paper without folding the card as a side effect.

#### Scenario: A folded card shows its head only

- **WHEN** the 组卷 page renders saved papers
- **THEN** each card shows its title, its size and its controls, with its
  problem list folded away

#### Scenario: An edit leaves the paper open

- **WHEN** a learner opens a paper, moves one of its problems, and the page
  reloads the saved order
- **THEN** that paper is open again in that tab

#### Scenario: A control does not fold the card

- **WHEN** a learner presses 导出 or 开始练习 on an open card
- **THEN** the control runs and the card stays as the learner left it

#### Scenario: An error remains visible on a folded card

- **WHEN** a rename or export command fails while its paper card is folded
- **THEN** the error status remains visible outside the folded problem list
