# Respect every directional due row in weak ranking

- Weakness ordering now evaluates every schedule direction for a knowledge
  point instead of stopping at the first row.
- An overdue reverse-direction review can no longer be hidden by an unscheduled
  or future forward-direction row.
- Invalid schedule dates remain neutral rather than breaking ranking.
