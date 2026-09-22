# 投入使用前收尾：设计讨论检查点

**日期：** 2026-09-21  
**状态：** 设计已定稿；本文件保留调查证据与决策索引，规范性行为以三个 active OpenSpec change 为准。  
**当前分支：** `feat/pi-agent-and-cli`，检查时 HEAD 为 `7d1b081`。

## 1. 本轮目标

投入正式使用前完成最后收尾，重点有三条：

1. 批判性吸收旧开发文档，清除现行文档与 OpenSpec 的冲突，建立唯一权威口径。
2. 完善题目难度模型，使它符合早期“客观难度与学生感知难度分离”的设计思想。
3. 改善 Agent 对话中的过程输出：先只支持 Pi，把读、写、工具调用、命令等活动像消息一样逐条实时呈现。

同时发现一个必须先修的投入使用阻塞项：Agent 会话 JSON 在 Windows 上存在真实读写竞态。

## 2. 已核实的仓库事实

### 2.1 旧文档不是外部缺失材料

用户指定的旧文档目录：

`C:\Users\yanwei\Desktop\Document_In_University\Projects\active\Academic Workflow\lesson-kit\docs`

其中 13 个文件与当前仓库 `docs/` 下的对应文件逐字相同（SHA-256 相同）。因此后续工作不是“复制旧文档”，而是：

- 判断旧设计中哪些原则仍有效；
- 把仍有效的原则提升到当前 GLOSSARY / OpenSpec / PRODUCT-MANUAL；
- 把已失效内容明确标成历史，或从现行入口中移除；
- 不能让旧文件继续以 `Current v1 contract` 身份与新规格竞争权威。

### 2.2 已发现的主要文档冲突

- `openspec/specs/workbench-ui/spec.md` 同时要求“讲解/诊断按钮存在”和“讲解/诊断按钮已移除”。
- `openspec/specs/review-workbench/spec.md` 一边声明候选机制不存在，一边仍要求 candidate 的增改、门禁、晋升和顺序 ID。
- `FILE_CONTRACT.md` 仍把候选题生成管线和 `.lessonkit/explain/` 讲解产物写成现行契约。
- `TASK_ROUTER.md` 仍把生成练习路由到已退役的 `generate-problem-candidates`。
- `.claude/CLAUDE.md` 仍写 `problems` v1 不应有 difficulty，与当前 schema、GLOSSARY 和 OpenSpec 冲突。
- `docs/REQUIREMENTS.md` 正文保留大量历史 candidate / explain / diagnose 条款；虽然顶部声明后文是历史，但仍容易被 Agent 当作当前要求。
- `CONTRIBUTING.md` 在“只提供 `lesson-kit`”之后又写“不安装 `lesson-kit`，因为它属于 W&B”，明显应为旧 `wb` 名称残留。
- OpenSpec strict 目前 11/11 通过，但它只验证结构，不能发现上述语义矛盾。

### 2.3 当前难度实现

现行实现只提供：

- `knowledge_points.difficulty` 与 `problems.difficulty`：可空整数 1–5；
- 声明难度时必须同时给 `difficulty_basis`；
- `difficulty_basis` 只在门禁当下校验，不落库；
- 旧题不回填；当前计划、选题和学生界面不消费难度；
- legacy KP 提取缺失难度时仍默认 2，这是冻结的 pipeline 行为。

当前模型的问题：

- 1–5 档位只有重叠的粗描述，没有每档、每维的操作性锚点；
- 评分依据不落库，无法审计、校准或重新计算；
- 只表达内容的客观复杂度，未承接旧哲学中“客观难度与学生感知难度不同”的核心区分；
- `docs/REQUIREMENTS.md` 曾承诺日计划考虑难度，但 `workbench/domain/planning.py` 实际只统计 `problem_type_mix`，没有使用 difficulty。

### 2.4 当前 Pi 过程流实现

Pi 已接入且真机可用：

- 配置固定到 `C:/Users/yanwei/.npm-global/pi.cmd`；
- 版本 `0.85.1`；模型配置为 `deepseek/deepseek-v4-flash`；
- Bridge 已解析 Pi 的 `text_delta`、thinking 生命周期、tool call、tool execution start/update/end、流内错误与最终回答；
- 前端每 350ms 轮询 turn event；文本 delta 合并成一个增长中的回答；
- 活动目前集中在一张“执行计划”卡中，同一 activity 原位更新状态，命令/工具输出可展开；
- 成功轮次会把合并后的 activities 存进本地对话镜像，重新打开可恢复；
- 隐藏推理和原始协议事件不展示。

因此用户提出的“流式展示工具、读写、命令”并不是从零建设协议；主要缺口是 Pi 活动的呈现方式和文案粒度。Ponytail 原则下应复用现有 Pi event → normalized activity → polling 链路，不新增 WebSocket、SSE 或第二套事件协议，除非实测证明 350ms 轮询不够。

## 3. 已确认的难度设计决定

以下决定已经与用户确认：

### 3.1 双层难度，轻量消费

- **客观难度**：描述题目本身的认知复杂度。
- **个人难度**：描述这名学生当前觉得它有多难；不新增一个主观星级字段，优先复用现有自评、作答、卡点、信号和调度证据。
- 两者绝不互相覆盖：客观简单但学生卡住、客观复杂但学生熟练，都必须能表达。
- 投入使用前只做轻量消费：用于选题与计划配比；学生界面不显示裸分或难度星级。
- 真题拟合、IRT、自动个体校准仍属后续，不在本轮伪装完成。

### 3.2 客观难度采用多维向量

用户选择了多维向量，而不是“单值 + 文本依据”。已确认的四个维度是：

1. **知识跨度**：完成题目所需知识点的数量、分散程度与跨章节程度。
2. **推理深度**：最短可靠解法中的非平凡推理/操作链深度。
3. **迁移距离**：从已学范式到本题条件、表征或情境的变化程度。
4. **构造开放性**：答案需要选择、组织、证明、建模或设计的自由度与约束不完备程度。

明确不混入客观难度的因素：学生当天状态、历史正确率、个人耗时、界面操作负担、纯排版长度。这些属于个人难度、可访问性或呈现质量。

### 3.3 总难度由独立算法生成

用户最新确认：

- 每道题从一开始就同时保存四个分维度和总难度；
- 总难度不由 Agent 随手填写，而由一个独立函数生成；
- 该函数放在单独程序/模块中，成为唯一计算口径；
- 初版算法可以简单，但必须可替换、可版本化，后续筛选会同时使用分维度与总难度；
- 初版模型固定为 `cognitive-v1-equal-mean`：四维等权算术平均，使用 Decimal
  `ROUND_HALF_UP` 保留一位小数；`[2,2,2,3] → 2.3`，`[2,2,3,4] → 2.8`。

## 4. 已定稿的难度口径

四维统一使用 1–5 整数；要么四维、总分与模型 id 全有，要么整组为空。题型本身不决定分数，
知识跨度看必要知识结构而不机械数 `kp_ids`，推理深度看最短可靠解法而不看答案字数。

| 分值 | 知识跨度 | 推理深度 | 迁移距离 | 构造开放性 |
|---|---|---|---|---|
| 1 | 单一局部事实或概念 | 识别、回忆或一步直接代入 | 与教材定义/例题同构 | 选择、判断或唯一短答 |
| 2 | 单一概念加直接前置，或同节两点 | 一次标准变换或计算 | 只改数值、措辞或表面情境 | 边界清晰的计算/短解释 |
| 3 | 同章内 2–3 个概念协同 | 多个相依步骤，含一次方法选择 | 表征或组合陌生，但方法族明确 | 目标明确、允许多条有效路径 |
| 4 | 跨小节整合多个概念 | 多阶段推理，需组织中间结论和方法 | 无明确方法提示，需识别并适配 | 证明、建模或设计中存在实质选择 |
| 5 | 跨章节或跨框架综合 | 需规划子目标、组合方法，可能回溯 | 新条件/领域下需推广、重构方法 | 约束不完备，需权衡并论证方案 |

其余决定：

- 正式题和微题使用此模型；闪卡不评级；`knowledge_points.difficulty` 只保留为 legacy 内容复杂度。
- 评级是显式、惰性的独立事务；创建、入池、练习和展示均不依赖评级，也不自动排队或提示评级。
- 评级清单只提交四维，不保存 `difficulty_basis`，总分和模型 id 由领域函数生成。
- 旧标量清空，不伪造向量；题干、解析、知识点关联或题型变化时整组清空。
- 个人证据只影响知识点范围与到期优先级，不生成“能力等级”，也不回写客观难度。
- 来源是独立双轴：`source_kind` 表示依据材料，`origin_kind` 表示原题、改编或基于材料生成；
  派生组按 AI 生成优先，再分考试、课本和 other。

## 5. Pi 流式展示的定稿设计

用户目标：像聊天消息一样，一条条实时弹出“正在调用什么工具、读什么、写什么、运行什么命令”等信息；当前只需 Pi。

最小实现方向：

- 复用现有 normalized activity 和轮询接口；
- Pi 的 `toolName` + args 已足够区分 read/write/bash/search，并能取得 path/command/pattern/query；
- Pi 将当前整块“执行计划”改为对话流中的独立紧凑活动消息；Codex/Claude 保持原样；
- 同一 `activity_id` 仍原位从进行中更新到完成/失败，避免开始/结束刷两条；
- 默认只显示动作类型 + 对象，例如“读取 `docs/GLOSSARY.md`”“运行 `pytest …`”；输出继续折叠；
- hidden reasoning、provider-turn、thinking、answer 等通用阶段和原始 JSON 事件均不展示；
- 连续文本 delta 合并；具体活动会结束当前文本段，后续文本新开气泡；
- 输出始终默认折叠，摘要只显示经遮盖和截断的路径、查询或命令，不显示文件内容；
- 只在成功轮次镜像合并后的具体活动；失败和取消过程不进入长期镜像。

## 6. 投入使用前 P0：Agent 会话 JSON 竞态

### 现象与证据

- 首次全量：`469 passed, 1 failed`；失败为前台读取 `conversation.json` 时 `PermissionError`。
- 目标用例单独连续跑 12 次均通过。
- 随后整份 `test_conversations.py`：`34 passed, 1 failed`；这次后台线程在
  `temporary.replace(conversation.json)` 时触发 `WinError 5`。
- 两次失败位置不同但根因相同：轮询读者与后台写者同时访问同一 Windows 文件。

### 根因

`workbench/bridge/conversations.py` 的 `_write_json` 用临时文件 + `Path.replace`，写路径通常持有全局 `_LOCK`；但 `_read_json` 不持锁。Windows 不允许替换正被读取的目标文件，所以 350ms 轮询与后台状态写入会发生真实 sharing violation。

### 计划要求

- 修复必须落在共享 JSON 读写边界，不能通过给测试加 sleep 掩盖。
- 最小候选方案：将 `_LOCK` 改成可重入锁，并让 `_read_json` / `_write_json` 共享同一进程内锁；保留临时文件替换以避免半写 JSON。
- 先写能稳定放大并发读写的失败测试，再实施单点修复；随后重复对话测试和全量测试。
- 这是实际使用 Pi 流式轮询前的 P0，不应被 UI 改动遮蔽。

## 7. 建议的工作拆分与顺序

这三条不是一个大而混乱的变更，建议拆成可独立验收的 OpenSpec changes：

1. **pre-release-contract-reconciliation**
   - 修复 Agent 会话 JSON 竞态；
   - 清理 live OpenSpec 与当前入口文档的已证实矛盾；
   - 明确历史文档的状态和权威顺序；
   - 建立发布基线。
2. **problem-difficulty-and-provenance**
   - 定义四维量尺、独立总难度算法、schema、迁移与轻量消费者；
   - 同步 GLOSSARY、OpenSpec、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH。
3. **pi-activity-message-stream**
   - 只改 Pi 活动的归一化细节与对话流呈现；
   - 复用现有轮询和 activity contract；
   - 不扩大到 Codex/Claude，不新建流协议。
4. **pre-release acceptance**
   - 全量 Python / Node / compileall / OpenSpec；
   - Windows 并发压力回归；
   - Pi 真机一轮包含 read、write、bash/tool、文本流、失败与取消的走查；
   - 使用池副本，不向真实池写测试内容。

## 8. 当前基线

- `openspec validate --specs --strict`：11 通过、0 失败，但语义冲突仍存在。
- Node：107/107 通过。
- `compileall`：通过。
- `lesson-kit doctor`：注册表、两个工作区、池、三种 provider、计划文件均通过；后台服务当前未运行。
- Pi：0.85.1，可执行文件和模型已显式配置。
- Python：存在上述会话 JSON 并发失败，当前不能宣称全绿。

## 9. 不得丢失的工程边界

- 依赖方向：Shell → Domain → Data；Content 读产物；Bridge 旁挂且按请求运行。
- 新代码进入 `workbench/`；不借本轮自由重构 `pipeline/`、`pool/scripts/` 或 `lessonkit.py` 行为契约。
- stdlib-only，不新增前后端依赖；优先复用现有事件链和数据结构。
- 普通对话零学习写入；难度元数据只走独立、显式的 difficulty check/apply 事务。
- 学生界面保持人话，不暴露裸内部状态、算法参数或协议事件名。
- 文档变更必须同步 OpenSpec、GLOSSARY、ARCHITECTURE、PRODUCT-MANUAL 与 ACTION-GRAPH；历史逐字记录不改写，只标清权威关系。
- 所有真实写入走副本验收；不使用真实池做开发走查。

## 10. 压缩后恢复入口

设计讨论已经结束，不再继续 grilling。接管时依次读取：

1. `docs/superpowers/plans/2026-09-22-pre-release-implementation-handoff.md`；
2. 三个 active change 的 `proposal.md`、`design.md`、`tasks.md` 与 spec deltas；
3. 当前 `git status --short`。

本文件只保留调查与决策来路；若文字与 active OpenSpec 冲突，以 active OpenSpec 为准。

## 11. 实施进度更新（2026-09-22）

> 后续实现以 `docs/superpowers/plans/2026-09-22-pre-release-implementation-handoff.md`
> 为接管入口。本节只给状态摘要，不能代替 OpenSpec tasks。

- 三个 OpenSpec change 已建立并通过 strict validation：
  `pre-release-contract-reconciliation`、`problem-difficulty-and-provenance`、
  `pi-activity-message-stream`。
- Windows 会话镜像竞态已经按 TDD 修复：共享 `RLock` 覆盖 JSON、事件 JSONL、
  transcript；两个确定性同步测试先红后绿；`test_conversations.py` 37 通过。
- 难度纯函数、schema 重建、独立 check/apply 事务与 CLI、所有已知内容变化失效、来源/
  难度 pull 过滤、balanced、API/CLI 接线、计划隐藏分布均已实现并有聚焦测试。
- 微题与通用正式题写入口均要求 `source_kind + origin_kind`；prompt 已移除旧 inline
  difficulty/basis，并把评级限制为用户明确请求下的独立 check→apply。
- Pi 工具分类、事件前遮盖/截断、仅具体活动镜像、独立消息、同 id 更新、文本分段和
  Codex/Claude 兼容均已实现。
- current entry docs 已同步，并新增文档一致性测试；live specs 的物理合并/删除等待最终
  验收后通过 OpenSpec archive 完成。
- 验收进展：一次完整 Python **492 passed**、全部 Node **109 passed**，compileall、
  live OpenSpec strict（11 项）、doctor、extract-problems guard 与 disposable dmath 副本
  schema 验收通过。验收随后发现并修复公开 ensure 调用顺序、Lesson Kit CLI 子串误判和
  前缀 secret 名漏遮盖，三项聚焦回归通过。
- 尚未完成：在上述最新修复后重跑完整自动化与一轮新的干净真实 Pi scratch 验收，随后
  归档三个 change；没有 commit/push。
