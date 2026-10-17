# 2026-10-17 Paper 独立进度实施交接

## 范围与当前状态

实施 `decouple-paper-progress-and-content`：每卷独立未完成进度、文本/选择草稿、精确重置、历史保留删除、明确原卷更新和逐题呈现。所有者明确要求的重复「AI 生成解析」展示已移除，正常解析及持久数据保留。

前项外键迁移修复已通过 PR #141 合并到 main（`2dc66ef0`）；本项从该 main 基线实施。Agent 消息队列/中断、失败消息保留、右栏 DOM 独立和浮窗收起仍属于 `complete-agent-message-lifecycle`，本项没有把这些能力宣称完成。

## 实现与验证

- 复用 active singleton 表示选中执行，暂停卷快照进入 `paper_state`；草稿与 attempt 分开，不制造学习证据。
- 共用 Domain 作答语义比较；内容更新、批量 patch 和镜像走同一 Data 失效规则。学习写入前核验执行/结构/内容版本。
- 题目删除用历史行保留身份和证据；清当前引用时保留其他题进度。卷 JSON 修改使用提交后的持久文件意图；多题删除失败注入证明事务回滚不改文件。
- `papers` CLI 增加显式 ID 的 list/get/preview/update/delete；结构修改必须确认当前影响。保存清单原有回执与不写 SQLite 边界保留。
- Python 完整套件 1037 passed（200.30 秒）；最后浏览器缓存修复后官方 Node 全集 202 passed，Python 的 Node 包装检查也通过。compileall、extract-problems guard、diff check 均通过。OpenSpec 暂在 active change，最终同步/归档后再记录严格检查结果。
- 独立浏览器验收曾发现服务端已切 B 但页面保留 A 缓存的真实缺陷。已修复选中执行的缓存同步；相同题号也按执行/版本区分，A 的迟到回执不能污染 B。同一执行未确认的提交请求保留原请求用于重试。两项 Node 回归测试覆盖这两个边界。

## 副本与真实数据边界

17 个正式注册池的迁移副本均通过原字段/原行投影保留、完整性及幂等检查；临时 `c05-thin-tempval` 和 `w5-replica` 排除。证据与可重复脚本：
`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-all-course-20261017\batch-report.json` / `batch_migrate.py`。

独立验收另取大学物理乙 II、高级数据结构与算法分析、计算机组成的 SQLite backup 副本和隔离注册表。迁移前后全部原字段/原行保持，Physics 120 项/cursor 3、ADS 98 条 attempts、CO 原异常均保留。证据：
`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-acceptance-20261017\review-run-02\migration-preservation.json`。

本项新增字段在真实库中的应用与隔离浏览器验收结果应在发布段追加；上面的副本结果本身不代表真实库已更新。复核由独立 gpt-6-luna max 执行运行验收，主线程负责代码与契约审查；本运行环境无法确认 constrained reviewer 的强制只读隔离，因此不使用其自动 ACCEPT 门。

## CO 恢复单独处理

CO 当前旧执行仍是已消失的 70 个题号、19 个 stuck 标记及缺失 attempt 父记录；保存容器是另一组 22 题。结构迁移不重映射、不清除这些标记，不补造作答，也不挂到新卷。界面保留旧状态并列出不可用题号，禁止恢复空白题。实际恢复需要另行找到能证明身份对应和原学习记录的备份，验证恢复方案后取得明确授权；本 change 不完成数据恢复。
