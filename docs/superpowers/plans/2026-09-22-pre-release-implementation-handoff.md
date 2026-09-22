# Lesson Kit 投入使用前收尾：最终验收交接

**日期：** 2026-09-22  
**分支：** `feat/pi-agent-and-cli`  
**起始 HEAD：** `7d1b081`  
**工作区：** 有未提交改动；没有创建 commit。不要 reset、checkout 或覆盖现有改动。

## 1. 本次交付边界

当前 Agent 已完成三项 change 的设计、具体代码、确定性测试与 current docs 同步：

1. `pre-release-contract-reconciliation`
2. `problem-difficulty-and-provenance`
3. `pi-activity-message-stream`

用户明确把最终真实测试与发布验收交给下一位 Agent。因此本交接之后只剩：全仓检查、
disposable 池副本验证、真实 Pi scratch 走查、live spec 合并/归档，以及用户另行授权后的提交。
不要重新讨论已定稿的产品决定，也不要把这些验收项误报为已经完成。

权威读取顺序：

1. 本文件；
2. 三个 active change 的 `proposal.md`、`design.md`、`tasks.md` 与 spec deltas；
3. `docs/superpowers/specs/2026-09-21-pre-release-design-checkpoint.md`（只保留调查来路）；
4. 当前 `git status --short`。

## 2. 已完成实现

### 2.1 文档真相与会话竞态

- `workbench/bridge/conversations.py` 使用同一个 `threading.RLock` 保护镜像 JSON、事件
  JSONL 与 transcript 的进程内读写，同时保留临时文件替换。
- 确定性同步测试证明读者持锁时写者等待，未用 sleep/retry 掩盖 Windows sharing violation。
- `REQUIREMENTS.md` 已重写为当前需求；`FILE_CONTRACT.md`、`TASK_ROUTER.md`、
  `.claude/CLAUDE.md`、CONTRIBUTING、OpenSpec config 与产品/架构入口已纠偏。
- `tests/workbench/test_current_docs.py` 防止旧 candidate 命令、`.lessonkit/explain`、
  `difficulty_basis` 和旧 CLI 名称回到 current 入口。
- live specs 的最终删除/合并必须通过归档 `pre-release-contract-reconciliation` 完成；在归档前，
  consistency test 校验 active removal overlay，归档后会直接校验 live specs。

### 2.2 来源双轴与惰性四维难度

- 新纯领域模块 `workbench/domain/difficulty.py`：四维 1–5、模型
  `cognitive-v1-equal-mean`、Decimal `ROUND_HALF_UP` 一位小数、balanced 档位。
- 新 Data 模块 `workbench/data/difficulty.py`：1–N 题 check 零写入、apply 整批原子覆盖。
- 公开 CLI：`lesson-kit difficulty <workspace> check|apply --input <file|->`。
- `problems` 重建为 `origin_kind` + REAL 总分 + 四维 + model，全空/全有 CHECK；旧标量清空。
- 文件数据库测试覆盖 `foreign_keys=ON`、两类子表、约束、索引、幂等与空
  `foreign_key_check`。没有对真实池运行迁移。
- Agent-managed 正式题/微题要求 `source_kind + origin_kind`；生成微题不再用 quiz 冒充来源。
- `source_group` 互斥推导；pull 支持来源交集、总分/分维范围与显式 balanced，默认顺序不变。
- 日计划增加只供系统/Agent 使用的隐藏分布与建议配比；学生 UI 不显示难度。
- prompt 已移除 inline difficulty/basis，并明确只有用户要求评级时才 check→apply。
- 题干、解析、知识点关联、题型变化和删除知识点导致的关联变化都会清空完整评级。
- formal solution apply 会按旧表实际存在的难度列清空，兼容尚未升级的测试/旧池形状。

### 2.3 Pi 消息式活动流

- `conversation_providers.py` 将 Pi 具体工具映射为读取文件、更新文件、搜索、运行命令、
  操作 Lesson Kit 或调用具体工具名。
- Bridge 在落事件前遮盖 assignment-style secret 与 bearer token；detail 最长 500，output
  最长 4000。写工具摘要只取路径，不包含写入正文。
- Pi 的 turn/progress/thinking/answer 通用活动不再生成消息；hidden reasoning 和协议噪声仍丢弃。
- 成功 Pi 镜像只保存合并后的具体活动；失败/取消仍不写 transcript。
- 前端按 provider 分流：Pi 活动是独立紧凑消息，同 id 原位更新，输出默认折叠；具体活动
  切开前后文本气泡。Codex/Claude 保持原执行计划组件。
- 恢复成功 Pi 会话时显示合并活动和最终答案，不伪造瞬时 delta 顺序。
- 仍使用现有 350 ms polling，没有 WebSocket/SSE、依赖或第二套协议。

## 3. 当前验证证据（含接管后的验收进展）

以下均在 2026-09-22 当前工作树重新运行：

```text
聚焦 Python（13 个受影响模块）: 210 passed in 50.10s
一次完整 Python:                 492 passed in 109.35s
全部 Node:                       109 passed, 0 failed
compileall（全仓目标）:           exit 0
live OpenSpec strict:            11 passed, 0 failed
workbench doctor:                all checks passed
extract-problems guard:          PASS
git diff --check:                 exit 0（仅 CRLF 提示，无 whitespace error）
```

完整 Python 首次发现 4 个旧 fixture 使用非法/缺失题型；只修测试数据后重跑得到 492 通过。
此后隔离 schema 验收又发现公开 ensure 的调用顺序缺陷，真实 Pi 验收发现 CLI 子串误判与
前缀 secret 名漏遮盖；三项生产修复的聚焦回归为 **3 passed**，但修改后尚未再跑完整套件。

## 4. 下一位 Agent 的验收清单

### 4.1 先确认边界

- 运行 `git status --short`，保留本工作区全部现有改动。
- 不迁移外部工作区或任何用户真实学习池。
- 仓库 `pool/dmath.db` 由用户明确认定为可丢弃测试池；仍优先复制到临时工作区验证。

### 4.2 全量自动化

```powershell
python -m pytest tests -q
node --test tests/workbench/*.test.js
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python -m workbench.cli.main doctor
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

只有对应输出存在时才运行 `problem-set` guard。若失败，先确认是本变更回归还是既有环境/日期
问题，不要通过删测试、sleep 或放松契约绕过。

### 4.3 disposable schema（已完成）与真实 Pi（需复验）

- 已在临时池副本运行公开 schema ensure 两次：345 problems、3 progress、3 attempts
  保持；303 `source_problem` + 42 `generated_grounded`；第二次零变化；外键检查为空，
  integrity 为 `ok`。验收过程发现并修复了公开 ensure 在 `foreign_keys=ON` 下的事务顺序。
- 重新用真实 Pi 0.85.1 跑一轮：读取文件 → 更新 scratch 文件 → 调用 Lesson Kit CLI →
  流式文本完成；核对消息顺序、原位状态、折叠输出、遮盖和重开恢复。
- 首轮真实 Pi 已完成上述操作并成功镜像，但发现普通命令因 scratch 路径含 `lesson-kit`
  被误标，以及 `*_API_KEY` 一类前缀 secret 名未遮盖。两项已修复并有聚焦测试；因此首轮
  不能作为最终 4.2 证据，必须用新的干净 scratch 重跑。
- 首轮 scratch 的事件文件曾包含未遮盖的环境敏感值，已在确认路径位于系统 TEMP 后整目录
  删除；该临时目录不可作为后续证据源。新验收必须新建隔离目录，且不得运行裸 `env`。
- 失败与取消继续由确定性 fixture 验收，不必为了制造失败污染真实工作区。

### 4.4 归档顺序

全量与真实验收通过后：

1. 归档 `pre-release-contract-reconciliation`，确认 retired `review-page` capability 消失，
   candidate/explain/diagnose 旧要求不再存在于 live specs；
2. 归档 `problem-difficulty-and-provenance`；
3. 归档 `pi-activity-message-stream`；
4. 重新运行 OpenSpec strict 与 `tests/workbench/test_current_docs.py`。

OpenSpec tasks 中所有未勾选项正是上述最终验收/归档责任。不要在证据出现前勾选。

## 5. 风险与非目标

- schema rebuild 已在 disposable dmath 副本验证；仍需完整套件确认最新调用顺序修复未引入回归。
- active live specs 在归档前仍含被 delta 覆盖的旧要求；这不是新权威，不能手工删 base spec
  后又保留失效 delta。通过 OpenSpec archive 一次性合并。
- 本轮不实现真题拟合、IRT、自动个体校准、评分历史、文字评分依据或练习页筛选控件。
- 不扩展 Codex/Claude 的消息样式，不新增依赖，不触碰 frozen pipeline 行为。
- 已运行 doctor、guard、一次完整 Python/Node、schema 副本与一次真实 Pi；最新三项验收修复后
  尚未重复完整 Python/Node 与真实 Pi。没有 archive、commit 或 push。

## 6. 主要改动入口

- 难度：`workbench/domain/difficulty.py`、`workbench/data/difficulty.py`
- schema：`pool/scripts/pool_schema.py`
- 来源/拉题/计划：`workbench/domain/pull.py`、`workbench/domain/planning.py`、
  `workbench/server/api.py`、`workbench/cli/main.py`
- 内容失效与 ingest：`workbench/data/content.py`、`workbench/ingest/__init__.py`
- Pi：`workbench/bridge/conversation_providers.py`、`workbench/bridge/conversations.py`、
  `workbench/server/static/workbench.{js,css}`
- 自动化：`tests/workbench/test_difficulty.py`、`test_current_docs.py` 及相关现有测试文件
- 规格：`openspec/changes/{pre-release-contract-reconciliation,problem-difficulty-and-provenance,pi-activity-message-stream}/`
