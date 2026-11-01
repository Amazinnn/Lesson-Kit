# 2026-11-01 — 计算机组成 ch01–ch03 主/客观题卷排版（按小问机制）

所有者要求用新的小问（`problems.parts`）机制完成 计算机组成 第 1–3 章主/客观题卷的排版。

## 结论与动作

- **客观题卷无需改动**：ps-007（23 题）／ps-009（58 题）／ps-011（29 题）全部 110 题都已带
  `micro_quiz`（判断/选择），即新机制下可自动判分的形态。
- **主观题卷按题内子问拆小问**：ps-006（17）／ps-008（49）／ps-010（23）去重 86 题中，
  逐题判读后确认 **9 道题有真实子问结构**，其余为单问（保持整题，走虚拟 `whole`）。
  通过 `problem-patch`（`ingest.apply_problem_patch`）一次原子批次写入：
  **batch-159，9 题 / 25 小问**，备份 `pool/co.db.pre-parts-20261101-232215`。

| 题目 | 小问 | 说明 |
|---|---|---|
| co-ch01-prob-001 | a, b | 全局 CPI / 执行时间 |
| co-ch01-prob-002 | a, b | IPS / 提高后的时钟频率 |
| co-ch01-prob-003 | a, b | 执行时间 / MIPS |
| co-ch01-prob-036 | a, b | 全局 CPI / 时钟周期数 |
| co-ch02-prob-002 | q1a, q1b, q1c, q2, q3a, q3b, q3c | C↔RISC-V 翻译、IEEE754 转换、指令编码 |
| co-ch02-prob-011 | q1–q4 | 同一机器字的四种表示 |
| co-ch02-prob-024 | p3, p4 | 补码/反码原值 |
| co-ch02-prob-063 | p1, p2 | IEEE754 −1、补码原值 |
| co-ch05-prob-055 | p1, p2 | 汇编与调用约定（题号属 ch05，出现在 ch02 卷） |

小问字段：`id`（小写字母开头）、`prompt`（原题子问逐字）、`type`（calculation /
open_response）、`short_answer`、以及从既有 `solution` 派生的 `reference_answer` /
`reference_reasoning`；`co-ch02-prob-002` 的 3.b 原卷无答案，`reference_answer` 留空并
在 reasoning 里注明（不编造）。

## 验证

- 只读 gate 预检通过后才写入；写入后复核 9 题 `parts` 长度与投影：
  `co-ch02-prob-011` → 4 小问、`co-ch01-prob-001` → 2 小问，`part_summary` 均为
  `not_requested`，三张卷 `can_start: True`。
- 副作用：受影响题目 content revision 递增，按既有规则只影响未完成的练习项。

## 登记（未处理，待所有者决定）

- 主观卷中混入 **7 道客观题**（无 `micro_quiz`，当前按自由作答自评）：
  ps-006 的 co-ch01-prob-019/020/023/032/034；ps-008 的 co-ch02-prob-118；
  ps-010 的 co-ch03-prob-028。
- **跨章号引用**：ps-008（ch02 卷）含 co-ch05-prob-055；ps-010（ch03 卷）含
  co-ch02-prob-011、co-ch02-prob-063。是否为内容归类有意为之待确认，未擅自移动。
