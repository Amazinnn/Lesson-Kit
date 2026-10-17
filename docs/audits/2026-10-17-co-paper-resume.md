# 2026-10-17 CO 新版试卷可做性核验

## 用户授权与操作结果

用户明确表示旧版不需要恢复，只需保留旧记录、让新版能做；随后确认删除试卷容器应保留题目和逐题作答。当前组卷页只有新版 ps-001（22 题），没有另一个可删除的旧卷容器，不能误删新版。

操作先在 SQLite backup 副本验证，再在真实库事务中复用 active_practice.clear/start_saved：旧 70 项执行归档为 practice_runs id=1、status=abandoned，保留 19 个 stuck 标记及原 attempt_id；新版 ps-001 创建 execution_id=2，进度 0/22，22 项均可解析。没有恢复已删除旧题或补造缺失的 attempt 父记录，没有在真实库试答。

problems、knowledge_points、problem_attempts、feedback_events、learner_signals、review_schedule 等 22 个非执行表前后逐行一致；卷 JSON 字节不变，integrity_check=ok。备份后缀为 co.db.pre-new-paper-start-20261017-172750。

证据目录：C:/Users/yanwei/AppData/Local/Temp/lesson-kit-co-new-paper-20261017-49ob_3w7/，包括 repair.py、validated.json、old-execution.json、applied.json、http-verified.json。

HTTP 实测 current.progress 与 practice-sets.progress 均为 0/22。Playwright 点击继续后显示首道“存储程序计算机指令与数据共存原理”的“是/否”选项和提交按钮，未提交答案。旧执行保留在历史轮次，当前卷不再挂 19/70。

## 当时发现的通用状态问题

paper_progress.summary 原先仅按 source_ref 关联进度，practice_sets._saved_record 直接附到当前容器，而 start_saved 比较有序题号后拒绝。API 曾同时返回 count=22/progress.total=70，页面仍显示继续按钮；practice-flow 只检查 unavailable_item_ids。

该问题单列 align-paper-execution-status，后续实施与验收状态见 docs/STATUS-paper-execution-status-2026-10-17.md。本快照不作为滚动规范。

## 备份发现不等于恢复授权

只读检查 co.db.pre-del-batch095-20261015，发现 70 个旧题 co-ch02-prob-126 至 195 及 19 条 attempts；执行条目与真实库残留完全一致。真实库当时对应旧题和 attempts 已为空。用户明确不需要恢复，因此未拷回。

本操作更新了先前 STATUS 中“CO 仍被旧执行卡住”的运行状态，原快照保留为历史证据。
