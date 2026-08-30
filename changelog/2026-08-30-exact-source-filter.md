# Exact source filtering

- Fixed multi-knowledge-point pulls so `source_kind` constrains the complete
  requested scope instead of only the final SQL branch.
- Made knowledge-point matching exact after decoding `kp_ids`, preventing one
  identifier from matching a longer identifier with the same prefix.
- Added Pool and pull-engine regression coverage for both cases.
