# PR113 figure identity and containment repair — started 2026-10-12, completed 2026-10-13

The figure mirror now preserves legacy 64-hex content identities. It refuses a
sync when existing copies differ, and `pull` refuses a repository-only hash-named
asset when neither workspace copy provides a baseline. Existing local bytes can
still seed the repository or a matching compatibility copy; existing non-hash
owner paths remain editable through an explicit direction. No new hash is
computed and no `figure_paths` value is renamed.

Resolved workspace figure roots/targets, repository figure roots/targets, and
the derived owner-index path must remain inside their workspace or supplied
checkout. The index path is preflighted before any asset copy, including when
there are no figure references. Windows junction fixtures cover the top-level
workspace root, legacy runtime root, checkout asset root, and empty-reference
index path.

Figure reads now require an existing regular pool database and both managed
owner tables before an empty reference list can be trusted. Older pools with
the two owner tables but without `figure_paths` columns remain supported.

The contract documents now define the binary projection and derived index, show
the index envelope, distinguish it from JSON mirror state, and document explicit
directions, exit behavior, no pruning/Git transport, current runtime layout, and
per-file replacement limits. The broader figure naming strategy and any runtime
root migration remain unresolved follow-up work. No current-spec synchronization
or archive is claimed here.

Focused figure and existing JSON mirror checks: 56 passed, including the
missing/non-file database CLI regression. Compile, strict OpenSpec validation,
diff check, and the existing invalid-index CLI exit-code check passed. Full
repository exact-head CI and archive acceptance remain pending in the root
workflow. All filesystem fixtures were confined to temporary test directories;
no real course database or image files were written.
