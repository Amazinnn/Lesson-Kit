# introduce-check-pipeline 提案

## Why

队列④立项。Check 管线（原名 generate 桥）的口径在 2026-08-29 动作面问卷
（DISCUSSION-RECORD 专题 21）升级，立项 grilling（专题 22）定案：

- **形态**：生成 → 校验 → 直接入正式池，无候选中间态（不设 staging 区）。
- **触发权**：Agent 可直接触发 ingest——「门禁步骤是决断辅助，不是权限
  闸门」（推翻旧定义的「所有者触发」条款）。
- **安全网**：每次 apply 记批次 id、内容行带批次标记、一条命令整批撤销
  （GLOSSARY「批次 id」「整批回滚」词条已在案，机制属定义、实现为零）。
- **范围吸收**：候选题贴标签/归类/出入库并入校验环节；「Agent 组织面板」
  挂名条目了结；candidate_problems 退役。
- **定名 Check**（强调校验准入，替代「generate 桥」）。

池子现状 345 题 / 66 卡 / 31 KP 全覆盖；micro-quiz / flash-card 两种门禁
配方已在真实池跑通。实现缺口只有三个：批次 id 无处记录、内容行无批次
标记、没有一条命令的整批撤销。产出链入口经所有者拍板走对话桥结构化
动作（外部会话写文件跑 CLI 的通道照旧可用）。

## What Changes

- schema additive：problems / flash_cards 增列 `ingest_batch_id`；新增
  `ingest_batches` 批次登记表（幂等 ensure_* 迁移）。
- 三个 recipe apply（micro-quiz / flash-card / problems）统一记批次 id、
  内容行戳记、manifest 快照落 `pool/ingest/<batch_id>.json`。
- 新增 `wb ingest rollback --batch <id>`：锁内校验批次 → 依赖记录检查 →
  安全备份 → 单事务删行 → accounting 核对；对话桥结果卡片的回滚按钮
  走同一条 `rollback_batch` 函数。
- 对话桥新增结构化动作 `check_ingest`：check_intent 意图门 → 内联
  manifest → 服务端过既有确定性门禁 → apply → 独立结果卡片进对话流；
  门禁失败逐条显式呈现（仅本动作改变现有坏 JSON 静默丢弃行为）。
- candidate_problems 退役：pull / mastery / hub 停读候选与候选尝试；表与
  `wb data candidate` 子命令保留、标「待退役」，不 DROP。

## Capabilities

### New Capabilities

（无——批次治理并入 workbench-content-governance，桥动作并入
ai-teacher-bridge，均不立新 capability。）

### Modified Capabilities

- `workbench-content-governance`：ingestion 命令族加 rollback；新增批次
  溯源与整批回滚 requirement；显式写边界承认桥 check_ingest 动作通道。
- `flash-card` / `micro-quiz-content`：ingestion requirement 补批次戳记。
- `ai-teacher-bridge`：新增 check ingest action requirement（意图门、门禁
  失败显式化、独立结果卡片、回滚 affordance）。
- `review-workbench`：pull 停走候选回退、shortage 指向 Check 管线；data
  CLI 候选命令族标待退役、formal problem 生产路径改指 Check。
- `mastery-evaluation`：候选证据退役（不再贡献知识点证据）。

## Impact

代码集中：`pool/scripts/pool_schema.py`、`workbench/ingest/`、
`workbench/cli/main.py`、`workbench/bridge/conversations.py`、
`workbench/server/`（context、api、app）、`workbench/data/`（pool、
mastery、queries）、`workbench.js`/`workbench.css`、两侧测试。
GLOSSARY / PENDING-DEFINITIONS / DISCUSSION-RECORD 已随 PR1 同步；
PRODUCT-MANUAL 第 8/9 章、ACTION-GRAPH 各层随交付回填。真实池迁移
幂等且有备份。
