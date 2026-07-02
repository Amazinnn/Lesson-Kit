# KP Consolidation Analysis — Discrete Math Ch.6

> Reviews `knowledge-points.md` for granularity and consolidation issues.

## Granularity check

Each KP represents a single atomic concept (one theorem, one rule, one formula). No excessive splitting detected.

## Consolidation candidates (considered but not merged)

| candidate A | candidate B | decision | reason |
|---|---|---|---|
| kp-010 P(n,r) | kp-011 P(n,r) factorial form | **keep separate** | textbook presents as separate Theorem 1 / Corollary 1 |
| kp-006 Pigeonhole T1 | kp-008 Generalized Pigeonhole T2 | **keep separate** | T1 is a special case, T2 generalizes — both pedagogically distinct |
| kp-013 C(n,r) | kp-014 Binomial Theorem | **keep separate** | C(n,r) is a counting formula, Binomial Theorem is an algebraic identity using C(n,r) |

## Fragility indicators (for future human authoring)

KP that may need fragility notes (per `pool-field-inference` skill criteria):

- **kp-003** (Subtraction Rule / Inclusion-Exclusion): two-set vs general case confusion
- **kp-004** (Division Rule): when to use division vs subtraction
- **kp-008** (Generalized Pigeonhole): parameter interpretation (k+1 objects → at least ⌈(k+1)/n⌉ in one box)
- **kp-009** vs **kp-012** (Permutation vs Combination): order matters vs not — common confusion
- **kp-013** C(n,r) symmetry: C(n,r) = C(n,n-r), often forgotten
- **kp-014** Binomial expansion: which coefficient goes to which term (signs)
- **kp-015** Pascal's Identity: combinatorial proof vs algebraic proof
- **kp-019** r-combinations with repetition: formula C(n+r-1, r) — "stars and bars" mnemonic

> These are observations for the human author to fill in `fragile` field later. **Not auto-generated.**

## Coverage check

- All 6 main sections (6.1-6.6) covered ✓
- 22 KP across 17 subsections
- Average ~1.3 KP per subsection (some subsections have 1 KP, some have 2-3)
- Higher-density subsections: 6.3.2 (Permutations) has 3 KP, 6.3.3 (Combinations) has 2 KP, 6.4 (Binomial) has 4 KP

## Missing considerations (intentionally deferred)

- **Examples** (EXAMPLE 1-23+): each is a worked problem, not a "knowledge item" in the strict sense. They are pedagogical illustrations, not theorems. The user said knowledge grows through co-learning, so leaving them as concrete examples in the body (when authored) rather than separate KP.
- **Exercises** (end-of-section problem sets): deferred to future `textbook_exercises` table
- **Figures** (FIGURE 1 IPv4, etc.): visual content, not text-extractable as KP. IPv4 example may eventually become a body field of kp-005 or a related example.

## Recommendation

Pool inventory is structurally complete. Proceed to manifest generation. After structural validation, the user will engage with each KP to author body/fragile.