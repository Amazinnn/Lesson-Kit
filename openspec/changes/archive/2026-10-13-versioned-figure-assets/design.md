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
therefore keep their current hash-based logical paths such as
`dmath/ch06/<sha256>.png`; this byte projection does not rename them. A legacy
64-lowercase-hex filename remains a content-hash identity, not a mutable stable
path. Other existing non-hash paths, including
`dmath/ch06/dmath-ch06-prob-017/fig-001.png`, can be edited through an explicit
direction. The repository project does not settle the broader naming strategy.

`figures/<course-id>/_index.json` is a derived navigation index generated from
the pool references on every push, including an empty reference list. Its UTF-8
JSON envelope is `{schema_version: 1, course_id, figures}`; each `figures` item
contains its full `logical_path` and all `{owner_type, owner_id}` pairs. It
records each problem/KP owner so a repository browser can find a legacy
hash-named figure by authored object id. It is not a second authority: editing
the index never changes pool membership or `figure_paths`, and the next push
rewrites it canonically. The resolved index path is checked against the supplied
checkout before any figure copy, even when there are no figure references.

## 3. Workspace compatibility

After the legacy identity check passes, mirror operations resolve a logical
figure in this order:

1. `<workspace>/figures/<logical>` — the future visible authored-asset area;
2. `<workspace>/.lessonkit/figures/<logical>` — the current runtime/ingest area.

For eligible assets, push uses the first existing copy. Pull writes the
repository bytes to both locations. This dual-write is transitional: the current workbench server and
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
- `push`: for assets that pass legacy identity checks, workspace bytes are
  authoritative for this invocation and are copied to the repository; the
  owner index is then written canonically.
- `pull`: repository bytes are authoritative for this invocation and are copied
  to the workspace canonical and legacy compatibility locations.

There is no automatic winner. `check` never overwrites a differing file.
Other existing non-hash paths may be overwritten only by an explicit push or
pull. For a legacy hash identity, every existing workspace and
repository copy must contain the same bytes; any mismatch is a conflict and
blocks the full planned operation before file writes. Pull also refuses a
repository-only hash file when both workspace copies are missing, because no
local baseline can establish that the bytes still match the identity. A local
copy may seed the repository or a matching compatibility copy. No new hash is
computed and no logical path is renamed.

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
bytes. These are per-file replacements, not an all-file transaction; a later
operating-system write failure may leave earlier files applied. Resolved
workspace asset roots/targets must remain inside the registered workspace, and
resolved repository asset roots/targets/index must remain inside the supplied
checkout. This includes roots or targets redirected by symlinks or Windows
junctions. Unsafe paths are rejected before they are read or written.

This version never deletes or prunes an extra repository/workspace image. That
is intentionally conservative because Git history already handles obsolete
files well and the current local repair workflow may have uncommitted assets.

## 6. Git transport

As with the JSON mirror, Lesson Kit only reads/writes a supplied local checkout.
Clone, fetch, pull, branch creation, commit, push, and pull-request operations
remain external Git/hosting operations. This keeps the data contract usable by
local Agents and by ChatGPT's GitHub connection without teaching the application
about credentials or remotes.
