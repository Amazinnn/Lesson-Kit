# WP02 §1 基线与失败边界（1.1 / 1.2 / 1.3）

## 1.1 工件、身份与重叠

- 工件：proposal、specs（6 个 capability delta）、design、tasks 全读；execution-guide、contract-reconciliation、data-exchange-matrix、benchmarks/catalog 按需查（DATA-01–05/CONTENT-01/FLOW-03 定义驱动 3.2）。
- 身份：main 检出 `D:\Projects\Academic Workflow\lesson-kit`，分支 `main`；实现期提交序列见 `git log`（`84b4f9cf`→`8ade79ea`→`6aef571c`→`ee2396c8`）；editable 安装 = 主检出（RELEASE-02 核对）。
- 重叠 change：`json-content-repository-sync`（33/36，mirror 语义与 FILE_CONTRACT 相邻——只读其差异，未接手）；`adaptive-paper-content-lifecycle`（题目归档恢复已被 WP01 引用为 FS-08）；`agent-chat-simplify`（对话区，未触碰）。
- 交接：`STATUS.md` 各时段记录 + `docs/audits/2026-11-08-wp02-review.md`（审查拒收史）。

## 1.2 delta 逐条核对

门禁 delta 清单（脚本核对，2026-11-09）：

| delta | 操作 | MODIFIED 头不在 live |
|---|---|---|
| `ai-teacher-bridge` | MODIFIED | 无 |
| `flash-card` | MODIFIED | 无 |
| `knowledge-content-operations` | ADDED（新能力） | — |
| `knowledge-figures` | REMOVED + MODIFIED | 无（MODIFIED 头均在 live） |
| `micro-quiz-content` | MODIFIED | 无 |
| `workbench-content-governance` | MODIFIED | 无 |

- 场景保全扫描：5 个 MODIFIED 块对 live 的场景**零丢失**；扫描器把 `knowledge-figures` 的 REMOVED（"Rollback deletes newly unreferenced figures"）报为场景缺失属误报——REMOVED 本就不携带场景，且其 Reason/Migration 与 2.5 的整批撤销退役一致（Reason 引 Q098/S008，Migration 指向治理直接修正）。
- 次级引用：GLOSSARY（方法提案、运行时来源、整批回滚退役）、DATA_MODEL（`chapter` 列）、FILE_CONTRACT（bundle/patch 单元语义、方法提案、批次快照=应用记录）、PRODUCT-MANUAL、ACTION-GRAPH（2026-11-08/09 三条留痕）+ L0–L4、agent_contracts——均在各段提交内同步；`views/**` 冻结层按所有者决定不改（边界记录于 2.3 证据）。
- 一处扫描发现的 docstring 残留（`_gate_problem_patch` 仍写 "whole batch can be rolled back"）由独立验收条件闭环修正（`ee2396c8`）。

## 1.3 失败检查先行

| 缺口 | 先失败的证据 | 期望差异 → 修复 → 回归 |
|---|---|---|
| 审计三条 P1（重复落库/悬空闪卡/附件破坏独立语义） | 审查者用独立进程对 stash 复现（`docs/audits/2026-11-08-wp02-review.md`）；2.4 重做后全仓首跑暴露 micro 门禁 per-item 闸缺失（2 条失败） | 被拒单元零写入、依赖阻断、插图失败只回滚本单元 | 
| 旧原子契约 | 2.4 WIP 期间内容包 17 条用例失败（编码旧"整批原子"） | 逐条改写为单元语义，工作区不留红 |
| 退役批次 undo | `test_batch_undo_retired.py` 前先确认 CLI 报 SystemExit | 命令消失 + 历史可读 |

（WIP 过程、stash 位置与恢复方法见 `STATUS.md` 2026-11-08 末段。）
