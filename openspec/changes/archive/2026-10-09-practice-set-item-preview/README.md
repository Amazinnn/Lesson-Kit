# practice-set-item-preview

A saved paper folds to its head, and its items open in place — so the 组卷 page
can be read as a list of papers and of problems.

| file | what it holds |
|---|---|
| `proposal.md` | Why a card that lists only titles (all of them) cannot be read, and what replaces it |
| `design.md` | Why `<details>`, why the controls sit outside the toggle's effect, why the body is the knowledge page's body, why the fold lives in the tab |
| `tasks.md` | What was touched |
| `specs/workbench-ui/spec.md` | The two added requirements and their seven scenarios |

## What it is

`practice_sets_page` rendered every paper as its full problem list — a page with
two papers was 150 rows — and each row was an index, a title and three buttons,
enough to manage a paper and not enough to read one. Two folds now:

- **the card** folds to its head (title, size, controls); folded is the default,
  and a card the learner opened comes back open after the reload an edit causes,
  per tab
- **the item** opens to the problem's own text: rendered like the knowledge point
  page (`_render_markdown` into `linked-problem-text rich-text`), stem and source
  line only, no solution

## What is not here

Answers in the preview, any paper data change, and any new endpoint — the fold is
a reading state that is never sent anywhere.
