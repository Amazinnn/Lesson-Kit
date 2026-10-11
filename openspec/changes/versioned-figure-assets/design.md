# Design: Versioned figure assets

## 1. Boundary

The knowledge pool remains the runtime source of truth for authored object
identity and for each object's `figure_paths` logical references. The authored
content repository stores the corresponding bytes so Git can review and version
image edits.

Binary assets are deliberately not JSON entities. They have no mirror revision
row, no repository-created identity, and no SQLite BLOB. The logical path in the
pool is the join key.

## 2. Repository layout

```text
<repo>/
├── courses/<course-id>/
│   ├── knowledge/<entity-id>.json
│   ├── problems/<entity-id>.json
│   └── relations/<entity-id>.json
├── figures/<course-id>/
│   ├── _index.json
│   └── <chapter>/...
└── delete-requests/<request-id>.json
```

The figure subtree sits outside `courses/<course-id>/` so the existing JSON
entity scanner never attempts to decode PNG/JPEG/SVG bytes as UTF-8 entity
files.

The repository path is exactly `figures/<logical figure path>`. Existing pools
therefore remain compatible with current hash-based names such as
`dmath/ch06/<sha256>.png`. Future owner-scoped paths such as
`dmath/ch06/dmath-ch06-prob-017/fig-001.png` fit the same contract without a
second storage scheme.

`figures/<course-id>/_index.json` is a derived navigation index generated from
the pool references on push. It records each logical path and every problem/KP
owner so a Git/GitHub client can find a legacy hash-named figure by authored
object id. It is not a second authority: editing the index never changes pool
membership or `figure_paths`, and the next push rewrites it canonically.

## 3. Workspace compatibility

Mirror operations resolve a logical figure in this order:

1. `<workspace>/figures/<logical>` — the future visible authored-asset area;
2. `<workspace>/.lessonkit/figures/<logical>` — the current runtime/ingest area.

Push uses the first existing copy. Pull writes the repository bytes to both
locations. This dual-write is transitional: the current workbench server and
ingest rollback logic continue reading `.lessonkit/figures`, while local Agents
may begin using the top-level `figures/` area immediately.

This change intentionally does not alter workbench serving, ingest destinations,
or rollback bookkeeping. A later migration can switch those consumers once
active bulk repair work is complete.

## 4. Directional synchronization

`lesson-kit mirror <workspace> figures --repo <checkout> --direction ...`
provides three explicit directions:

- `check`: read-only comparison. Reports same, different, repository-missing,
  workspace-missing, or invalid, and reports the index state separately.
- `push`: workspace bytes are authoritative for this invocation and are copied
  to the repository; the owner index is then written canonically.
- `pull`: repository bytes are authoritative for this invocation and are copied
  to the workspace canonical and legacy compatibility locations.

There is no automatic winner. A differing file is not silently overwritten by
`check`; the caller must choose push or pull.

`--dry-run` computes the same push/pull plan without writing.

## 5. Scope and safety

Only paths referenced by `knowledge_points.figure_paths` or
`problems.figure_paths` participate. Duplicate references to one logical path
copy one asset and retain all owners in the report and index.

Before any push/pull write, all referenced logical paths and required source
files are validated. Logical paths must:

- be POSIX relative paths;
- begin with the selected course id and a chapter segment;
- contain no empty, `.` or `..` segment and no backslash;
- use a supported image extension.

If any referenced source required by the selected direction is missing, the
operation writes nothing. Individual file replacement and index replacement use
a temporary sibling plus `os.replace` so readers do not observe half-written
bytes.

This version never deletes or prunes an extra repository/workspace image. That
is intentionally conservative because Git history already handles obsolete
files well and the current local repair workflow may have uncommitted assets.

## 6. Git transport

As with the JSON mirror, Lesson Kit only reads/writes a supplied local checkout.
Clone, fetch, pull, branch creation, commit, push, and pull-request operations
remain external Git/hosting operations. This keeps the data contract usable by
local Agents and by ChatGPT's GitHub connection without teaching the application
about credentials or remotes.
