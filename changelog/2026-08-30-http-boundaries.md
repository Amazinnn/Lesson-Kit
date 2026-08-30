# HTTP boundary hardening

- Malformed, non-UTF-8, negative-length, and oversized JSON requests now receive
  a stable JSON `400` response instead of breaking the request handler.
- JSON request bodies are capped at 2 MiB, comfortably above the workbench's
  bounded action and content payloads.
- Write requests require an `application/json` object, which also prevents
  simple cross-origin form posts from mutating the local workbench.
- Figure serving now uses a resolved path containment check, closing the sibling
  directory prefix escape while preserving valid workspace figures.
