# WP02 2.4 独立有效单元（四类通道全部完成）

任务原文：> 将 bundle/problem-patch/card/quiz/figure相关应用拆为独立完整单元；修改旧all-or-nothing场景，保持单元一致、批次provenance和重试身份。

前置：`docs/audits/2026-11-08-wp02-review.md` 的三条 P1（重复内容落库、悬空闪卡、附件故障破坏独立语义）全部修复并有回归用例；stash `36ce6819` 未被采纳，作为对照参考。

## 门禁：拒收单元不产出计划

`workbench/ingest/__init__.py::_gate_content_bundle` / `_gate_micro_quiz` / `_gate_flash_cards` / `_gate_figure_patch` / `_gate_problem_patch`：

- 每个条目循环内记录 `refused_before = len(errors)`，条目结束时任一新增错误即不产出 plan。机制细节按门禁而异：bundle 三段与 micro-quiz 在条目尾部判定；flash-card 在 validate_card_row 之后判定；figure-patch 在落图后判定且「无 files 的纯文本修订」不视为错误；problem-patch 原本就逐条 `continue`。
- bundle 的重复内容：`_problem_identity_errors` 改为同时返回 `(errors, refused_ids)`，被拒 id 对应的 problem plan 被剔除——审计 P1-1（报 duplicate 仍落库）；
- micro-quiz / flash-card 门禁同样返回 `items`（仅接受单元），`ok` 仍表示"整份清单是否全合规"；
- figure 门禁：course/chapter 层错误是**全局错误**（manifest-wide）→ 无 plans、整体拒绝；条目级错误只拒该条。

## 依赖完整

- bundle：`known_kps = 库内 ∪ 已接受的包内知识点`（不再包含被拒 id）；题目 `kp_ids`、闪卡 `kp_id` 命中被拒知识点 → 该单元报 `depends on a rejected knowledge point`、零写入（审计 P1-2 的悬空闪卡即此）；
- 问题/闪卡的插入改用显式列集（bundle 内不再复用全列 dict），旧池缺列仍安全。

## 应用：单元一致（行 + 附件 + 批次记录）

| 通道 | 单元粒度 | 关键行为 |
|---|---|---|
| content-bundle | 章 = 一批（行+图+快照+批次记录同生共死），章内每单元独立 savepoint | 题目插图在**同一 savepoint 内**发布，失败回滚该题行并删除已复制文件（审计 P1-3：不再触发整包回滚）；批次只覆盖实际落库的章与行；`ingest_batch_id` 在批次记录事务内写回 |
| problem-patch | 每行一个 savepoint | 行不存在/rowcount≠1 只拒该行；快照 `previous`/`post` 只含已应用行；`cleared` 只计成功行 |
| micro-quiz / flash-card patch | 每条一个 savepoint | 快照 `items` 只含已应用条目；批次只记已应用数量 |
| figure-patch | 每个条目一个 savepoint（复制文件 + 改行同生共死） | 失败删除本单元已复制文件；快照 previous/post 只含已应用条目 |

所有通道：`ok = 无错误`、`partial = 有拒收但有落库`、`errors` 逐条给原因；**完全没有有效单元时才抛错零写入**。快照从"回滚护栏"改为"应用于记录"（2.5 已定语义）。

## 用例

- content-bundle：5 条旧原子断言改写为单元语义（`test_missing_required_image…→test_a_problem_with_a_missing_image_is_refused_alone` 等）；新增 5 条：拒收单元不挡邻居、重复内容零写入、被拒知识点的闪卡零写入、注入 `_publish_figure` 失败只回滚本单元（42 passed）
- problem-patch：`test_an_unknown_problem_refuses_only_its_unit`（部分成功 + 批次仍记录）、`test_a_rejected_patch_unit_keeps_its_neighbour`（重复 id 只拒第二行）
- figure：`test_a_refused_figure_unit_keeps_the_other_problem`（缺图源单元零写入、另一题正常落图落行）
- micro/card：既有 gate 断言 + 部分应用经由 `_apply_patch` 覆盖
- 汇总：全仓 **1572 passed / 441s**（micro-quiz 两条旧原子用例改写后经全仓复核）；Node UI 297 断言通过；compileall OK

## 边界

- 部分成功时回执 `ok=False`、`partial=True`：调用方（CLI/桥）需检查 `errors`；重试同一清单时，已应用单元会以 `already exists` 拒收（不产生重复），新增单元照常落库。
- 章 = 一批的 provenance 语义不变；单元独立不改变"每章一个批次 id"。
- figure-patch 的全局错误（course/chapter 缺失或不符）仍整体拒绝，不做单元级放宽。
