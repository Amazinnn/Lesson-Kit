## Design

The CLI shell owns one argparse tree. Existing extension parsers contribute their
actual argument definitions and dispatch to their existing namespace handlers;
there is no fake help list or generic argument serialization. `entry`, `main`
and the console script delegate to this tree. Command inventory derives from
the parser itself.

The canonical skill files live under
`workbench/resources/skills/source-bounded-learning-drill/` and are included in
wheel package data. Existing repository discovery paths retain thin references.
The teaching text and local terminology remain unchanged. Bridge appends one
absolute `--skill` argument when constructing Pi print or RPC commands, after
provider/model arguments are selected, including pinned conversation arguments.
Only exact bundled and previously managed
`~/.lessonkit-workbench/skills/source-bounded-learning-drill` arguments are
deduplicated; other skill paths and provider flags remain intact.

No configuration/history is rewritten. Pi outside Lesson Kit receives no new
arguments. Existing RPC processes keep their loaded resources until a new
conversation or normal idle recycling; active work is never interrupted solely
to reload a skill.

## Verification

Red tests reproduce hidden commands and missing resources. Focused tests cover
real help, entry parity, invalid arguments, isolated papers save/list/get, and
Pi print/RPC argument preservation. Build and install a wheel in isolation to
prove resource inclusion and non-editable loading. A no-prompt Pi RPC
`get_commands` check proves discovery only, not generated-question quality.
Run repository checks and reconcile affected contracts before main integration.
