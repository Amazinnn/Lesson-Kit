# Recover from corrupt client state

- Discard malformed session-storage values and continue page startup with safe defaults.
- Surface structured server error messages in the study UI, with the HTTP status as fallback.
- Cover recovery and visible API errors in the browser interaction tests.
