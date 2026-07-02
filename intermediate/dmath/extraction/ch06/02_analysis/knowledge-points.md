# Knowledge Points — Discrete Math Chapter 6 (Counting)

> **First real-textbook E2E.** body and fragile intentionally null in the initial manifest. The user explicitly stated: "知识是人和 AI 共同学习中逐渐成长起来的，所以也没有必要在第一次的时候就把它填好，你只需要确保它能填就行" (Knowledge grows gradually through human-AI co-learning; no need to fill everything in the first pass—just ensure it CAN be filled).
>
> After structural inventory is validated, the user will review and engage with each KP to fill body/fragile over time.

## Section index (from extracted Markdown)

- 6.1 The Basics of Counting
  - 6.1.1 Introduction
  - 6.1.2 Basic Counting Principles
  - 6.1.3 More Complex Counting Problems
  - 6.1.4 The Subtraction Rule (Inclusion–Exclusion for Two Sets)
  - 6.1.5 The Division Rule
  - 6.1.6 Tree Diagrams
- 6.2 The Pigeonhole Principle
  - 6.2.1 Introduction
  - 6.2.2 The Generalized Pigeonhole Principle
  - 6.2.3 Some Elegant Applications of the Pigeonhole Principle
- 6.3 Permutations and Combinations
  - 6.3.1 Introduction
  - 6.3.2 Permutations
  - 6.3.3 Combinations
- 6.4 Binomial Coefficients and Identities
  - 6.4.1 The Binomial Theorem
  - 6.4.2 Pascal's Identity and Triangle
  - 6.4.3 Other Identities Involving Binomial Coefficients
- 6.5 Generalized Permutations and Combinations
  - 6.5.1 Introduction
  - 6.5.2 Permutations with Repetition
  - 6.5.3 Combinations with Repetition
  - 6.5.4 Permutations with Indistinguishable Objects
  - 6.5.5 Distributing Objects into Boxes
- 6.6 Generating Permutations and Combinations
  - 6.6.1 Introduction
  - 6.6.2 Generating Permutations
  - 6.6.3 Generating Combinations

## KP inventory

| kp_id | knowledge_item | knowledge_type | importance | source_location |
|---|---|---|---|---|
| dmath-ch06-kp-001 | 乘法规则 (Product Rule) | concept-property | core | §6.1.2 |
| dmath-ch06-kp-002 | 加法规则 (Sum Rule) | concept-property | core | §6.1.2 |
| dmath-ch06-kp-003 | 减法规则 / 容斥原理（两集合）| method-modeling | core | §6.1.4 |
| dmath-ch06-kp-004 | 除法规则 (Division Rule) | method-modeling | core | §6.1.5 |
| dmath-ch06-kp-005 | 树形图 (Tree Diagrams) | method-modeling | supplementary | §6.1.6 |
| dmath-ch06-kp-006 | 鸽巢原理 (Pigeonhole Principle) — Theorem 1 | concept-property | core | §6.2.1 |
| dmath-ch06-kp-007 | 鸽巢原理推论：非单射函数 (Corollary 1) | formula-calculation | core | §6.2.1 |
| dmath-ch06-kp-008 | 广义鸽巢原理 (Generalized Pigeonhole Principle) — Theorem 2 | concept-property | core | §6.2.2 |
| dmath-ch06-kp-009 | 排列 (Permutation) 与 r-排列 (r-permutation) | concept-property | core | §6.3.2 |
| dmath-ch06-kp-010 | r-排列计数公式 P(n,r) = n(n-1)...(n-r+1) | formula-calculation | core | §6.3.2, Theorem 1 |
| dmath-ch06-kp-011 | r-排列的阶乘形式 P(n,r) = n!/(n-r)! | formula-calculation | supplementary | §6.3.2, Corollary 1 |
| dmath-ch06-kp-012 | 组合 (Combination) 与 r-组合 | concept-property | core | §6.3.3 |
| dmath-ch06-kp-013 | r-组合计数公式 C(n,r) = n!/(r!(n-r)!) | formula-calculation | core | §6.3.3, Theorem 2 |
| dmath-ch06-kp-014 | 二项式定理 (Binomial Theorem) | formula-calculation | core | §6.4.1, Theorem 1 |
| dmath-ch06-kp-015 | 帕斯卡恒等式 (Pascal's Identity) | formula-calculation | core | §6.4.2 |
| dmath-ch06-kp-016 | 帕斯卡三角形 (Pascal's Triangle) | concept-property | supplementary | §6.4.2 |
| dmath-ch06-kp-017 | 范德蒙德恒等式 (Vandermonde's Identity) | formula-calculation | supplementary | §6.4.3 |
| dmath-ch06-kp-018 | 允许重复的 r-排列数 n^r | formula-calculation | core | §6.5.2, Theorem 1 |
| dmath-ch06-kp-019 | 允许重复的 r-组合数 C(n+r-1, r) | formula-calculation | core | §6.5.3 |
| dmath-ch06-kp-020 | 不可区分对象的排列 (Multinomial coefficient) | formula-calculation | core | §6.5.4 |
| dmath-ch06-kp-021 | 把对象分配到盒子 | algorithm-process | supplementary | §6.5.5 |
| dmath-ch06-kp-022 | 字典序生成排列算法 (Lexicographic permutation generation) | algorithm-process | supplementary | §6.6.2 |

## Notes

- **22 KP** extracted from a 63-page chapter.
- **核心 (core)**: 14 KP — 核心定理、公式、计数方法
- **补充 (supplementary)**: 8 KP — 推论、变体、应用方法
- 全部 exercise 题目暂不提取（按用户要求，等 textbook_exercises 表实现后再处理）
- body 字段全部 null（首次不过度提取，留待人机协作填充）
- fragile 字段全部 null（必须人工填，Agent 不给默认值）
- 详见 `02_analysis/knowledge-relationship-analysis.md` 和 `02_analysis/kp-consolidation-analysis.md`（下一步产出）