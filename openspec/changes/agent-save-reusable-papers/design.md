## Approved design
Reuse the existing managed saved-paper store and `create_saved` function. Add a thin `papers` CLI extension through `entry.py`; keep `pull`, `--plan`, `--print` and all existing routes unchanged. This follows Shell → Domain → Data and adds no new design term.

## Input and persistence
The input is the existing `practice-set` manifest, loaded with the existing UTF-8/BOM-aware reader. Data validates its kind, allowed fields, nonempty unique ordered IDs and existence in the selected workspace before writing. A supplied course must match the selected course. The existing writer validates title/request and atomically creates one managed JSON record. Preserve ordered IDs and request metadata, leave the source manifest untouched, and do not modify SQLite or learning state. Each explicit successful invocation creates one paper, as the browser already does; do not add deduplication or retries.

## Receipt and Agent instructions
Return JSON with `practice_set_id`, `title`, `count`, and `url` (workspace-relative group-paper page). Invalid input returns JSON error and exit 2 with no saved file; successful writes exit 0. Agent instructions require managed saving when a learner asks for a paper to be saved or made available in Workbench, allow export-only requests, and prohibit claiming a managed save from a job artifact alone. Existing sessions load the updated practice topic on demand where supported; old running code may need its normal idle service refresh, never restart active work.

## Verification
Real isolated SQLite fixture plus CLI dispatch and browser list GET/render: ordered selection and request survive; errors including malformed input, unknown/duplicate IDs and course mismatch create no paper. Compare DB bytes, source manifest and existing papers before/after. No live course writes or paid model calls. Independent final repository acceptance and release gates follow implementation.
