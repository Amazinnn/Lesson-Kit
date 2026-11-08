# WP02 §3 契约同步与发布核对（3.1 / 3.3 / 3.4 / 3.6）

## 3.1 契约同步清单（逐文件核对）

| 资产 | 同步内容 | 状态 |
|---|---|---|
| `docs/GLOSSARY.md` | 新增「方法提案 / Method proposal」；「整批回滚」标退役；「运行时来源」「知识点章节迁移」既有条目与本包一致 | 已同步 |
| `docs/DATA_MODEL.md` | `knowledge_points.chapter`（active，2.3）；其余字段无新增（方法提案只写既有列） | 已同步 |
| `FILE_CONTRACT.md` | bundle/problem-patch 单元化语义；方法提案（复用优先、不确定拒收零写入） | 已同步 |
| `docs/ARCHITECTURE.md` | 本包未改分层与模块边界（`apply_method_proposal` 属 Data 层既有文件），不机械改写 | 不受影响 |
| `docs/PRODUCT-MANUAL.md` | 方法提案段；批次单元语义（第 8 章）；批次 undo 退役表述 | 已同步 |
| `docs/ACTION-GRAPH.md` + `L0–L4` | 2026-11-09 方法提案留痕、2026-11-08 undo 退役留痕；L2 新增 method/related/move 行 | 已同步 |
| surface / HTTP | 本包全部入口为 CLI/Agent 面，无新路由；`surface.py` 仅 2.5 移除了退役的 rollback 路由 | 已核对 |
| 提示词及 agent_contracts | agent_contracts：方法提案复用句 + undo 退役措辞；`skills/**` 无本包语义（核对过 `ingest rollback`/`method kp` 均无命中） | 已核对 |
| `views/**`（冻结层边界） | 按所有者决定不改；`pool-query.md` 等旧视图仍按 ID 推章，已作为已知边界记录于 2.3 证据 | 已核对 |

## 3.3 RELEASE-01（全仓与相关检查）

- 全仓 `PYTHONUTF8=1 python -m pytest tests -q --tb=short`：**1582 passed / 432s**（2.2 后）；
- `compileall` OK；Node 套件 **297 断言 0 fail**（`workbench_ui_interactions` / `agent_ui_v1` / `course-preferences`）；
- `openspec validate --specs --strict` 23/23；WP02 strict 有效；
- `guard extract-problems --course dmath --chapter ch06` PASS；
- 浏览器检查：本包无浏览器面变更，未重复 WP01 的浏览器结论（如实登记，不引用替代）。

## 3.4 RELEASE-02（副本迁移 / 备份恢复 / 安装身份）

`release-02-run.py`（报告 `release-02-report.json`）：

| 项 | 结果 |
|---|---|
| 旧池副本迁移（DROP chapter 模拟旧池 → `migrate-progress.py`） | 列恢复、`ch06` 由 ID 回填、经验存活 |
| 备份恢复（bundle apply 的可恢复备份） | 备份存在；apply 后新点在池；备份持 apply 前状态；恢复副本与 apply 前一致 |
| 安装身份 | `workbench.__file__` = 主检出（main），非 worktree |

## 3.6 提交纪律

- 每个可验证单元按精确路径提交（`git log` 可核：`7c90d201`/`11629355`/`84b4f9cf`/`14843b2b`/…，均带 `-- <paths>`）；
- 工作区无遗留改动（仅 owner 侧既有未跟踪文件）；
- 运行切换遵守 S008 默认直接通过；只有实际验证过的行为标记已交付。
