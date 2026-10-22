# Load only for Lesson Kit

The canonical `SKILL.md` and `TERMINOLOGY.md` ship together in the installed
Lesson Kit package at
`workbench/resources/skills/source-bounded-learning-drill/`. This repository
entry is a compatibility reference; update the canonical package resources
together when changing teaching content.

The Lesson Kit Bridge automatically passes `--skill <absolute bundled path>`
to Pi in print and RPC mode, including model-specific and pinned argument lists.
No manual copy, per-course installation, provider/model argument edit, or Pi
global configuration change is required. Pi started outside Lesson Kit receives
no additional skill argument.

Existing other arguments, skills, models, credentials and native session state
remain intact. At launch only, exact arguments for the old managed directory
`~/.lessonkit-workbench/skills/source-bounded-learning-drill/` or the current
bundled directory are replaced with one bundled argument. Configuration files,
conversation records and the old deployed files are not rewritten or deleted.

For a zero-generation load check, start an isolated Pi RPC process through the
Bridge with `--no-session` and request `get_commands`; confirm
`skill:source-bounded-learning-drill` is present. This checks loading, not
question quality. A wheel installation must also contain both files.

An already running Pi RPC process keeps its loaded resources. Start a new
Lesson Kit conversation or wait for normal idle recycling; do not interrupt an
active turn to force a reload. Stored pinned model arguments remain unchanged;
the shared command builder adds the packaged skill on the next process launch.
