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

## 错位题处理（所有者 2026-11-01 决定后执行）

- **7 道混在主观卷里的客观题已转题型并归位**：
  `problem-patch` batch-160 把 co-ch01-prob-019/023 转为 `single_choice`（选项照原文，
  答案分别为 99.75% / Bus）、co-ch01-prob-020/032/034 与 co-ch02-prob-118、co-ch03-prob-028
  转为 `yes_no`；batch-161 补齐五道判断题的 `answer_key`（否/是/否/否/是）。
  备份 `co.db.pre-micro-convert-20261101-233220`。
- **卷子成员调整（走 preview → 确认 → update 的受治理流程）**：
  ps-006 17→12、ps-007 23→28、ps-008 49→47、ps-009 58→59、ps-010 23→21；
  ps-014 原本已含 co-ch05-prob-055，无需变更（该题现只保留在 ch05 主观卷）。
  **ps-008 的成员调整触发了检查点重置**（当时 1 项完成 / 49 份草稿），历史 Attempt
  记录不受影响；其余五卷无可重置的进行中进度。
- **跨章号归位**：ch05-prob-055 移出 ch02 卷（保留在 ch05 卷）；ch02-prob-011/063 移出
  ch03 卷（保留在 ch02 卷）。按所有者「按章号归位」的决定执行。

