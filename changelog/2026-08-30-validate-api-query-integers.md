# Validate API integer query parameters

- Return structured HTTP 400 responses for malformed or out-of-range list limits.
- Reject invalid and negative conversation event cursors instead of dropping the connection.
- Cap list limits at 1000 to prevent accidental oversized responses.
