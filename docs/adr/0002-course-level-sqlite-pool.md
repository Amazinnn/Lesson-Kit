# Course-Level SQLite Pool

Each course uses one SQLite database at `pool/{course}.db`. This is less
isolated than one database per chapter, but it keeps cross-chapter querying,
learning state, and multi-view reuse straightforward.
