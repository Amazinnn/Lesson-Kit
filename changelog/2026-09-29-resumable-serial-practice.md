# Resumable serial practice UI

**日期：** 2026-09-29

## 变化

- 真实练习页以后端 `/practice/current` 为权威状态，旧 sessionStorage 仅保留兼容缓存。
- 开始练习时一次性选出完整题组并冻结，不再每做一题动态 `pull n=1`。
- 新增轻量题量选择：5 / 10 / 20，默认 10。
- 练习页显示唯一“继续上次练习”卡片与进度条。
- 已有未完成练习时，新开始会明确询问继续还是替换。
- “不会，下一题”对 problem 复用 `stuck` 并推进进度；对 flashcard 记录低评分后推进。
- “暂停本轮”不会完成当前题，也不会写学习记录。
- answer 请求携带 `practice_position`，使 attempt 与 active-practice 推进保持事务一致。

## 边界

本变更不新增试卷持久化或组卷 UI；题目来源仍复用现有 pull/facet/search 能力。
