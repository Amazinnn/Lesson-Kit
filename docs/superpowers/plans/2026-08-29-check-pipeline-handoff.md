# 2026-08-29 Check 管线立项交接（队列④）

> **✅ 已交付（2026-08-29/30，introduce-check-pipeline）**：定名 Check（专题 22）、
> 批次 id+整批回滚、桥 check_ingest 动作、candidate_problems 退役全部落地；
> 走查与归档完成。详见 `changelog/2026-08-29-introduce-check-pipeline.md`。
> 本文档以下内容保留为立项时的开场材料。

> 给下一对话的开场材料。读完本份 + `AGENTS.md` + `docs/ACTION-GRAPH.md`
> （README 队列 + L3 动作登记）即可立项。上一阶段交接见
> `2026-08-29-practice-loop-ux-completion-handoff.md`（含当天全景）。

## 一、Check 管线是什么（定义现状）

原名「generate 桥」，PENDING-DEFINITIONS 有旧定义（所有者触发、逐题免审）。
2026-08-29 动作面问卷（DISCUSSION-RECORD 专题 21 + 问卷文件）**升级了口径**：

- **触发权**：Agent 可直接跑 `wb ingest --apply`——「门禁步骤是决断辅助，
  不是权限闸门」（推翻旧定义的「所有者触发」条款）。
- **管线形态**：生成 → 校验 → **直接入正式池**。无候选中间态
  （不设 staging 区；`candidate_problems` 表去留随本阶段定）。
- **安全网**：每次 apply 记**批次 id**、内容行带批次标记、**一条命令整批撤销**
  （GLOSSARY 已有「批次 id / 整批回滚」词条；机制属定义，实现为零）。
- **范围并入**：候选题贴标签/归类/出入库不是独立功能，是校验环节的一部分
  （原「Agent 组织面板」挂名条目被此吸收）。
- **名字**：所有者倾向 **Check**（「生成、校验、入库」强调校验准入），
  定稿时终定。
- 池子现状：345 题 / 66 卡 / 31 KP 全覆盖；门禁配方两种已实现
  （micro-quiz-patch / flash-card-patch）；综合题 AI 出题 = 本阶段新范围。

## 二、本阶段要定/要做的

1. **定义落笔**：PENDING-DEFINITIONS 条目升级（或更名 Check 后新写）、
   GLOSSARY 词条、DISCUSSION-RECORD 专题记录——走定稿三要素
   （指什么/正反例/谁负责解释）。
2. **首期实现范围**（grilling 定）：manifest 产出链（Agent 怎么产出合规
   manifest——提示词/技能/校验反馈）、批次 id 列与标记（schema additive）、
   整批回滚命令、（可选）综合题出题配方。
3. **交付**：OpenSpec change（workbench-content-governance 必有 delta，
   flash-card/micro-quiz-content 视范围）→ 实现 → 走查 → 归档。

## 三、开场 grilling 问题（新会话从这些问起）

1. 定名：Check / 保留 generate 桥 / 其他？
2. 批次回滚的粒度与命令形态（`wb ingest rollback --batch <id>`？）？
3. manifest 产出链首期：只闪卡+微题（门禁现成）还是连综合题配方一起立？
4. Agent 产出的入口：外部 agent 会话里直接写文件跑 CLI（现状即可用）
   还是要在对话桥里加结构化动作？
5. `candidate_problems` 表处置（退役 or 保留给抽取管线）？

## 四、配方与纪律（防复发）

- codex 子代理：`codex exec -m gpt-5.6-sol -c model_reasoning_effort=high
  --sandbox workspace-write`；**最多 2 并行、职能不交叉**（见 memory
  feedback-subagent-parallel-rules）；大机械活适合，精确小改自己做。
- 门禁流程：manifest → 副本演练（LESSONKIT_WB_HOME 隔离）→ 整池备份 →
  apply → 计数核对 → 走查。乘号 `×`；重复 id 拒收是特性。
- 基线：pytest 307 / node 87 / 11 specs / 双 guard。git 通道偶发 TLS 抖动，
  重试即可；中文 JSON 走 `--data-binary @file`。
- 走查是验收线；测试绿 ≠ 完成。
