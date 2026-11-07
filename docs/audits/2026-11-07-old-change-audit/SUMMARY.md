# 2026-11-07 老 change 完成度核对（快照）

只读审计：把仓库里每个未完成 change 的**未勾选任务**逐条对照当前代码、测试与提交，判断哪些其实已经交付、哪些确实没做。结论只用于**补勾**，本快照不实现任何功能。

两份原始报告在同目录：

- `A-report.md`：后端/数据类 10 个 change
- `B-report.md`：前端/图谱/运行时 9 个 change

## 补勾结果（已提交）

| change | 勾选前 | 勾选后 | 依据 |
|---|---|---|---|
| `remove-micro-quiz-error-reason` | 0/18 | **18/18 complete** | 13 项实现/文档/测试逐条核对 + 4 条全仓命令由本会话运行通过 + grep gate 无命中 |
| `evaluation-terminology-and-agent-crud` | 0/31 | 25/31 | CRUD/CLI/契约/测试 21 项 + 4 条全仓命令；**未勾** 1.2/1.3/1.4（live 文案仍有「自评」：`docs/PRODUCT-MANUAL.md:9`、`openspec/specs/workbench-ui/spec.md:1066,1080`）、4.6/4.9（缺专门用例）、5.6（prompt 行无断言） |
| `import-attempts-into-paper-progress` | 0/37 | 33/37 | 29 项实现/契约/测试 + 4 条全仓命令；**未勾** 4.4/4.8（缺用例）、5.1（归档时才做）、6.5（临时工作区 smoke 未跑） |
| `ingest-integrity-and-observability` | 3/44 | 6/44 | 只有 7.1–7.3 的决定记录已写入 change 设计；其余 38 项确实未做 |
| `workbench-visual-language-v2` | 112/173 | 125/173 | 动效/里程碑/时间视图走查、会话列表分组用例、资产机检 234/234 |
| `workbench-component-forms` | 0/62 | 1/62 | 只有 7.1 的 7 个 GLOSSARY 词条；实现组全部未开工 |
| `graph-settle-smoothness` | 27/31 | 28/31 | 9.4「未合并 main」已被 `adb68806 ∈ origin/main` 推翻 |
| `graph-free-force-field` | 143/160 | 145/160 | 8.5（动作已记 REMOVED）、8.7（同上合并状态） |

## 确实未开始（未勾任何项）

`mature-course-content-operations`、`retire-project-approval-gates`、`stabilize-agent-message-continuity`、`complete-practice-continuity-and-rich-titles`、`connect-evidence-guided-learning`。审批门仍完整存在（`pages.py` 的 paper-approval、`approval_pending` 暂停逻辑），这是它们未开始的直接证据。

## 两个 pre-existing delta 缺陷（阻塞归档，本轮未修）

`openspec validate <change> --strict` 失败，且**在本次补勾之前就存在**（这两个提交只改 tasks.md，delta 文件未被触碰）：

1. `graph-free-force-field`：MODIFIED "Complete primary learning text" 漏了现行场景 `Read paragraphs inside a card`。
2. `import-attempts-into-paper-progress`：MODIFIED "Durable attempt records for every surface" 漏了现行场景 `Submit remaining parts without duplicates`。

两处都是「MODIFIED 块必须带现行 spec 的全部场景」这条规则；归档前必须补齐，否则 archive 会拒。

## 未核（无法从本仓库核实）

- `json-content-repository-sync` 7.1/7.3：要求改外部仓库 `Lesson-Kit-Content` 的布局与验收样本，本仓库内无法核实，未勾。
- `workbench-visual-language-v2` 23–25 组、`graph-node-visual-language` 绘制层：确认为未实现（`.lk-select`/`.lk-steps`/`.lk-dialog` 全仓 0 命中、图谱仍五层圆盘）。
