## Context

五轮访谈已确认产品行为，见 proposal、delta specs 与 STATUS。当前 `active_practice.mark` 只处理首次 pending 转换、推进到下一待答题，并在最后一题后自动归档；普通题回看是只读覆盖层、每次进入折叠答案。当前草稿仅支持文本/选项，不能独自表达不会、锁定和已看答案。以上是必须显式协调的旧契约，不能只改前端按钮。

## Goals / Non-Goals

目标：固定 Paper 内任意前后导航、按答案展示方式提交/锁定、显式交卷、完整独立恢复，以及完成页与答卷往返。

非目标：不改学习算法、不改题目内容和 Paper 名单、不改闪卡作答语义、不重写历史 Attempt、不重构导入管线、不部署或迁移真实课程库。手动组卷渠道删除由另一 change 承担；用户自行决定实现者，不在本设计阶段委派实现。

## Decisions

### 1. Reuse the existing execution and records

保留 Paper ID、execution_id、paper_generation、content_revision 与 request_id 边界，复用 active/parked checkpoint 与 practice_runs，而非新建第二套练习系统。可编辑输入留在 execution checkpoint；正式 Attempt 仍只增不改。旧轮次已有 Attempt 视为锁定，不能把它变回可改草稿。

拟扩展轮次元数据以保存答案展示方式；每题状态保存输入、是否显式不会、提交/锁定、曾看参考答案与 Attempt/自评链接。这些是待实现的持久语义，**不是 DATA_MODEL 当前已经存在的字段声明**。实现者须以最小增量确定实际字段/兼容 JSON 结构，并在同一 PR 更新 DATA_MODEL 与 ensure 迁移。已有 draft sequence/revision 校验继续适用；状态版本不能靠浏览器短期内存独自承担。

旧检查点缺少新模式元数据时按已有逐题作答语义兼容：已记录题锁定并保留原 Attempt，未提交草稿保持未提交；不得重算或复制历史证据。已完成旧轮次不重新打开，历史不具备的输入/展开事实不伪造。进入新流程后最后一题不再自动归档。

### 2. Separate navigation, submission and completion

展示位置可持久化，但不依赖“下一待答题”才能访问某题。前后/圆点导航只保存输入和位置；不会、逐题提交、整卷提交分别是明确写入动作。不能再用旧 mark 的自动推进/自动归档作为所有动作的后效。

| 行为 | 逐题显示 | 交卷后统一显示 |
|---|---|---|
| 单选/判断选定 | 提交成功后锁定并展开结果 | 保存可编辑输入，不判定展示 |
| 多选/文字输入 | 保存输入，提交答案后锁定并展开 | 保存输入，无逐题提交按钮 |
| 上下题/圆点 | 保存输入和位置，不提交 | 同左 |
| 不会 | 显式记录、锁定并展开参考答案 | 保存可改不会标记并展开；新答案清标记，保留已看答案事实 |
| 提交试卷 | 已提交题复用；其余非空输入提交；空题不会 | 所有最终非空输入提交；空题不会 |
| 自评 | 启用时提交后可评，可跳过、可改 | 启用时交卷后可评，可跳过、可改 |

文字题及无答案键题没有客观判定。统一显示模式不能通过状态圆点、进度摘要或历史区域泄露当前题判定/参考答案。看过答案是披露事实，不等同于不会，更不自动等同于答对。

### 3. Keep one durable conclusion per submission

逐题明确提交复用现有 Attempt/feedback 流程及关闭自评时的 verdict 投影。统一显示模式在最终交卷前只有可编辑执行状态，不生成不可重写 Attempt。整卷提交复用已有逐题提交记录，仅补未提交的最终内容；不会沿用既有 stuck 记录语义，不新造客观错误。

整卷提交使用稳定 request_id、锁定执行及版本快照，由 Data 层在一个事务内校验并完成补写/归档；Domain 负责纯规则决定题目动作，Shell 只调度和展示。失败不展示完成，响应丢失重试取回同一结果。延迟草稿不能覆盖已锁定提交；并发旧标签请求继续受 sequence/generation/revision 检查拒绝。不要另建通用事务框架或新依赖。

自评第一次保存使用已有学习反馈规则；同轮后续覆盖只改已链接的分数/评语，不重复学习投影。未自评不阻止完成。不能为了完成页统计而补造反馈。

### 4. Restore and review from authoritative execution state

恢复包含本轮方式、每题输入/标记/锁定/已看参考答案/自评和当前题。UI 依据服务端返回区分已保存、正在保存与失败，失败保留编辑，不声称刷新即可恢复尚未确认的数据。切换 Paper 复用现有停放机制，不放弃旧卷。

完成页与答卷视图携带同一 execution_id，切换只是读取同一归档记录，不重新执行提交、pull 或 start。答卷原文固定，自评使用已有同轮编辑规则；再练一次明确创建新 execution，保留旧归档。管理页从后端状态显示继续或开始，不以“所有题已答”冒充“已交卷”。

### 5. UI uses existing visual components

沿用现有卡片、按钮、色板和安全 Markdown 渲染，无新 UI 框架或动画依赖。题目区导航三按钮，多选/文字的逐题提交是明确例外；试卷级工具栏放暂停练习/提交试卷。状态点同时显示题号、可访问状态和当前边框；题多时换行或局部滚动，不能遮题。完成页的 congratulations 表示完成，不能表示全对；计数清楚区分不会、错误及无判定。

## Contract reconciliation and implementation handoff

| 职责文件 | 同步要求 |
|---|---|
| openspec/specs | 将本 change 的替换项同步为当前契约，不遗留自动末题归档和强制回看折叠 |
| docs/GLOSSARY.md | 答案展示方式已以计划术语登记；实现时协调 Practice Review/Rating Mode/Practice Run 引用，保留草稿与 Attempt 区分 |
| docs/DATA_MODEL.md | 列明新增轮次/题目状态及 archive、writer/consumer、默认兼容与幂等键 |
| docs/ARCHITECTURE.md | 同步实际执行接口/模块职责；保持 Shell → Domain → Data |
| docs/PRODUCT-MANUAL.md | 更新开始、提交/不会、任意导航、暂停恢复、自评、答卷与完成页；删除旧提示 |
| docs/ACTION-GRAPH.md | 登记旧回看/逐题继续的替换、整卷提交、状态跳题、完成页往返动作 |
| FILE_CONTRACT.md / interface surface | 仅实际改变命令/API/工件时同步；本设计不授权改变 Agent Attempt Manifest |

## Risks / Trade-offs

主要风险是旧 mark 自动归档与新显式交卷冲突、可编辑草稿过早变成不可改 Attempt，以及完成页复查导致重复写入。先完成 Data/Domain 生命周期，再接 UI，使用小型确定性集成用例覆盖。旧轮次兼容与资料修订仍沿用现有不可静默映射规则；本 change 不批量修复真实数据。

## Open Questions

无待用户裁决的产品问题。具体字段布局、接口形状由实现者按本行为契约选择最小方案并同步职责文档；不能以实现自由重新开放已确认行为。
