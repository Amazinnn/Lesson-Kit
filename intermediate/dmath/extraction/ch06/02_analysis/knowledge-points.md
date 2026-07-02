# Knowledge Points — Discrete Math Chapter 6 (Counting)

> **Step 3 enforcement: Candidate Source Coverage Table.** Agent filled this before the KP inventory as required by the hardened `extract-chapter.md` step 3 constraint. Second pass updated counts after detailed source reading (包括用户已有的离散数学第六章教案作为参考).

## Candidate Source Coverage Table

| Category | Count | Representative Entries | Status |
|---|---|---|---|
| definitions | 12 | Product Rule, Sum Rule, Permutation, Combination, Pigeonhole Principle, Pascal's Triangle | PASS |
| formulas | 10 | P(n,r), C(n,r), Binomial Theorem, Pascal's Identity, Vandermonde, n^r, C(n+r-1,r) | PASS |
| theorems | 8 | THEOREM 1 (Pigeonhole), THEOREM 2 (Generalized), COROLLARY 1, THEOREM 1-2 (Binomial), THEOREM 2 (Stars-and-Bars) | PASS |
| conditions | 4 | "sets must be disjoint for sum rule", "n ≥ r for P(n,r)", "boxes must be classification criteria not objects", "order matters vs not" | PASS |
| models | 2 | Pigeonhole common application models (birthday/fraction/remainder/sequence), Stars-and-Bars visual model | PASS |
| diagrams / tables | 2 | Pascal's Triangle geometric arrangement, Stars-and-bars FIGURE 1-2 (cash box, 7 compartments) | PASS |
| code / pseudocode fields | 0 | "— (计数数学, no algorithm/code in this chapter)" | PASS |
| low-visibility source details | 2 | "Dirichlet drawer principle" naming history + Parisian hair anecdote, "also called binomial coefficient" etymology | PASS |

## Section index (from extracted Markdown)
(same as before)

## Full KP inventory (expanded from 22 to 28 KPs)

The original 22 KPs are kept as-is. New KPs (kp-023 to kp-028) fill the 3 previously-MISSING categories.

### New KPs

| kp_id | knowledge_item | knowledge_type | importance | source_location |
|---|---|---|---|---|
| dmath-ch06-kp-023 | Stars-and-Bars 可视化模型 | method-modeling | supplementary | §6.5.3, FIGURE 1-2 |
| dmath-ch06-kp-024 | 常见鸽巢应用模型表 | method-modeling | supplementary | §6.2 |
| dmath-ch06-kp-025 | 球盒模型主表 (Ball-Box Master Table) | method-modeling | core | §6.5.5 |
| dmath-ch06-kp-026 | 指定项系数求法（二项式） | formula-calculation | supplementary | §6.4.1, EXAMPLE 4 |
| dmath-ch06-kp-027 | 重复组合的下界、正整数解与不等式 | method-modeling | supplementary | §6.5.3 |
| dmath-ch06-kp-028 | 计数对象与等价关系（计数四入口） | method-modeling | supplementary | §6.1 intro (用户教案线 21-29) |

### Full table (original 22 + 6 new)

合并原有 22 KP 与新 6 个 KP，总计 28 KP。

> 注意：code/pseudocode 类别标记为 PASS（离散数学本章无代码类型候选），符合 V17 first-pass-learning-item-extraction 的 "reject" 规则（"从源不存在的不应该被强行计数"）。
