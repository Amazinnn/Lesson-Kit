# Knowledge Relationship Analysis — Discrete Math Ch.6

> Companion to `knowledge-points.md`. Documents the `related_kp_ids` for each KP and explains why.

## Type of relationships

- **depends-on**: KP requires another KP to make sense (e.g., binomial theorem depends on combination)
- **related**: shares concepts (e.g., permutation vs combination)
- **contrasts**: opposite or inverse of another KP
- **generalizes**: extends another KP (e.g., generalized pigeonhole generalizes pigeonhole)

## Per-KP relationships

| kp_id | name | related_kp_ids (kp_id : reason) |
|---|---|---|
| dmath-ch06-kp-001 | 乘法规则 | dmath-ch06-kp-002 (同属基本计数规则), dmath-ch06-kp-009 (r-排列的证明用乘法规则) |
| dmath-ch06-kp-002 | 加法规则 | dmath-ch06-kp-001, dmath-ch06-kp-003 (subtraction rule 跟加法 rule 对偶) |
| dmath-ch06-kp-003 | 减法规则 | dmath-ch06-kp-002 (依赖), dmath-ch06-kp-001 (对比) |
| dmath-ch06-kp-004 | 除法规则 | dmath-ch06-kp-003 (similar pattern, extension) |
| dmath-ch06-kp-005 | 树形图 | dmath-ch06-kp-001, dmath-ch06-kp-002 (tool based on basic rules) |
| dmath-ch06-kp-006 | 鸽巢原理 (T1) | dmath-ch06-kp-007 (Corollary 1 derives from it), dmath-ch06-kp-008 (generalization) |
| dmath-ch06-kp-007 | 鸽巢推论 (C1) | dmath-ch06-kp-006 (depends-on) |
| dmath-ch06-kp-008 | 广义鸽巢 (T2) | dmath-ch06-kp-006 (generalizes) |
| dmath-ch06-kp-009 | 排列/r-排列 | dmath-ch06-kp-001 (proof uses product rule), dmath-ch06-kp-010, dmath-ch06-kp-012 (contrasts with combination) |
| dmath-ch06-kp-010 | r-排列公式 P(n,r) | dmath-ch06-kp-009 (defines), dmath-ch06-kp-011 (alternative form), dmath-ch06-kp-013 (C(n,r) derives from P(n,r)) |
| dmath-ch06-kp-011 | P(n,r) 阶乘形式 | dmath-ch06-kp-010 (related — same thing, different form) |
| dmath-ch06-kp-012 | 组合/r-组合 | dmath-ch06-kp-009 (contrasts — order matters vs not), dmath-ch06-kp-013, dmath-ch06-kp-014 (binomial theorem involves combinations) |
| dmath-ch06-kp-013 | C(n,r) 公式 | dmath-ch06-kp-010 (derives from P(n,r)/P(r,r)), dmath-ch06-kp-012, dmath-ch06-kp-014, dmath-ch06-kp-015 (Pascal's identity involves C(n,r)) |
| dmath-ch06-kp-014 | 二项式定理 | dmath-ch06-kp-013 (binomial coefficients), dmath-ch06-kp-015 (proved using Pascal in some formulations), dmath-ch06-kp-016 |
| dmath-ch06-kp-015 | 帕斯卡恒等式 | dmath-ch06-kp-013, dmath-ch06-kp-014, dmath-ch06-kp-016, dmath-ch06-kp-017 |
| dmath-ch06-kp-016 | 帕斯卡三角形 | dmath-ch06-kp-013, dmath-ch06-kp-014, dmath-ch06-kp-015 |
| dmath-ch06-kp-017 | 范德蒙德恒等式 | dmath-ch06-kp-013, dmath-ch06-kp-015 (related combinatorial identity) |
| dmath-ch06-kp-018 | 允许重复的 r-排列 | dmath-ch06-kp-009 (contrasts — no repetition vs repetition), dmath-ch06-kp-001 (proof) |
| dmath-ch06-kp-019 | 允许重复的 r-组合 | dmath-ch06-kp-012 (contrasts), dmath-ch06-kp-013 (formula derives from C(n+r-1,r)) |
| dmath-ch06-kp-020 | 多项式系数/不可区分排列 | dmath-ch06-kp-010 (generalization — r-permutation when all distinct vs not), dmath-ch06-kp-014 (multinomial theorem uses these) |
| dmath-ch06-kp-021 | 对象分配到盒子 | dmath-ch06-kp-020 (uses multinomial coefficient) |
| dmath-ch06-kp-022 | 字典序生成排列 | dmath-ch06-kp-009 (algorithm on permutations) |

## Cross-section dependencies

- §6.2 (pigeonhole) is independent of §6.1 in mathematical content — different counting paradigm (existence proof, not constructive)
- §6.3 (permutations/combinations) is the natural follow-up to §6.1 (basic rules) — multiplication rule is the foundation
- §6.4 (binomial) heavily depends on §6.3.3 (combinations)
- §6.5 generalizes §6.3 — same questions but allowing repetition or indistinguishability
- §6.6 (generation) is computational view of §6.3 — algorithms rather than formulas

## Notes for consolidation

- kp-010 and kp-011 are mathematically the same (P(n,r) formula vs factorial form) — keep both as separate KP since they appear in the textbook as separate statements (Theorem 1 vs Corollary 1)
- kp-014 (Binomial Theorem) and kp-017 (Vandermonde) are presented as independent identities, not collapse
- kp-006 and kp-008: keep both — one is the basic pigeonhole, the other is generalized