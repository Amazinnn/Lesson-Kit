# Keep undated rows out of review overview

- Review overview now ignores schedule rows with no usable ISO due date.
- Unscheduled and malformed rows are no longer presented as if they were due
  today, and they do not inflate the later-work count.
- Due-list behavior remains unchanged and uses the same truthful date policy.
