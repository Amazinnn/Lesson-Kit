# WP03 3.2 FLOW-01–03 / RELEASE-02 验收汇总（2026-11-08）

环境：wb64 隔离 daemon 3123（source_root=主检出）+ 协议忠实假 provider；隔离真实数据，零真实学习记录。

## FLOW-01（每个旧审批动作：无页面/打开页面/刷新状态执行；额外批准点击 0、待批准状态 0、审批暂停 0；实际正确写入 1 次）

- **无页面执行**：Bridge 侧直执行（`_store_answer` → `_apply_paper_update_action`），不经 UI；2.1 测试 + 浏览器新会话实测（proposal 直接落库，无任何审批 DOM）。
- **打开页面/刷新状态**：2.3 浏览器实测——旧对话重开/页面刷新后审批卡不在 DOM、无待确认措辞、无 continue 阻塞；proposal 结果随对话流呈现。
- **重做**：完成页「再练一次」直开（confirm 间谍 0 调用）；records-center replay = 单次 POST `{replace:true}`（node DOM 契约）。
- **写入一次**：ps-001 题序翻转落盘一次；直执行路径无重试循环（`_apply_paper_update_action` 单次 preview+update）。

## FLOW-02（升级含 pending approval 的隔离旧会话，重复打开/恢复）

- 2.2 单测（5/5）+ 2.3 浏览器双恢复证明：注入合法 legacy pending → 打开即按原身份执行一次（卷序复原、turn 状态 applied、queue_paused 解除）；**第二次重开**：顺序不变、状态仍 applied、resolved_at 未动。失效目标 → 如实 invalid；陈旧回调（已决议）→ 零写入。

## FLOW-03（错误内容直接修正、启动旧撤销入口）

- 旧撤销入口：`lesson-kit ingest --help` 无 rollback（WP02 退役，本包 CLI 复验 0 命中）。
- 直接修正通道实测（wb64 隔离）：`lesson-kit data wb64 update problem wb64-ch01-prob-001 --input patch.json` exit 0，读回确认正文已改（题号不变）；CLI `papers preview/update` 显式确认路径不变。

## RELEASE-02

- 见 `2026-11-08-impl/2-4-cutover.md`：installed CLI/主检出、两 daemon source_root/进程身份、静态资源为新代码、3099 验收端口 stop 复原。本包无 schema 迁移、无池写入，副本=全仓 pytest 1583 + wb64 实跑。

## 仓库级检查（RELEASE-01）

- node：`tests/workbench/*.test.js` 全部 0 fail（12 注册套件）。
- compileall：lessonkit.py/workbench/pipeline/pool/tests 全过。
- `openspec validate --specs --strict`：25/25；change strict：valid。
- `guard extract-problems --course dmath --chapter ch06`：PASS（无阻断标记）。
- 全仓 `pytest tests -q`：**1583 passed（502.67s）**（WP03 全部代码 + 3.1 文档改后终检，exit 0）。
