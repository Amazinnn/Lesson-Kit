# Multi-hop corrections and full-size diagnostic

Source: followup to `5d11d979`, isolated `codex/course-sync` checkout, 2026-11-07.

## Verified correction

Received registered files remain managed without copying the source media configuration. Explicit file and entity deletion records remain portable across subsequent exports. Missing live files block export rather than becoming implicit deletion. Minimal file deletion records retain safe paths; execution items without content fail validation. Focused receive/data/execution checks: **50 passed in29.88s**. F03 supplied the independent failing multi-hop probes; coordinator implemented and verified the fixes.

## F2 diagnostic, before these followup corrections

The accompanying script and result describe one isolated, full-size run:20 chapters,1000 knowledge points,10000 problems,100 Papers,10000 attempts,30 unfinished exercises,500 learning files and100MiB attachments. Export125.441s, initial inspect42.837s, receive264.865s, repeat inspect64.175s. Export/receive30s and unchanged-inspection5s gates **failed**. This is not20-run/p95 acceptance. Concurrent tests and the older loaded module limit timing attribution. Repeat attachment-missing errors belong to the earlier multi-hop implementation and require rerun after corrections. No real course or live runtime was changed.

## Remaining work

Local content hard-deletion records and knowledge-point unlink semantics, typed nested references, native scheduled-task source binding, performance, free-LLM/remote/browser and independent acceptance remain incomplete. No WP01 completion or release claim.
