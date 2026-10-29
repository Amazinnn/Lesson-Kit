## Why

学习者已经把主观题写在纸上，Agent 也能用 `lesson-kit attempts apply` 把作答和可选评价导入题池，但导入的 Attempt 是游离记录：它不会进入任何 Paper 的答题进度，也不会改变完成状态。用户希望导入时可以选择“绑定到某张已保存试卷的现有进度”，或在没有未完成进度时新开一份该卷的进度；同时允许把题池里完全缺失、但确实出现在原卷上的题目补进已有知识点和当前试卷，并让进度自适应。

## What Changes

- `lesson-kit attempts check|apply` 的 manifest 增加可选顶层 `paper_id`。带该字段时，清单内每道题必须属于这张已保存 Paper；写入在同一事务内把 Attempt 绑定到该卷的当前执行进度。
- 绑定目标按现状自动选择：该卷是当前活动卷 → 写 `active_practice_items`；该卷有暂停 checkpoint → 写 checkpoint；该卷没有未完成进度 → 新建暂停进度（`reveal_timing=on_submit`），不激活、不写 `practice_runs`。
- 目标卷不是当前活动卷时，导入只写该卷的暂停进度，不暂停或修改另一张正在做的卷。
- 目标题已有作答（含「不会」）时，追加一条新 Attempt 并把该题进度重新指向新 Attempt；旧 Attempt 保留在历史。
- 补齐最后一题是否完成跟随该卷现有模式：legacy 轮次按现有规则自动归档；`per_item` / `on_submit` 显式交卷模式仍等待用户交卷。
- 导入无 `rating` 时只改变 Paper 执行进度，不改变学习投影；带 `rating` 时继续走既有 feedback 四件套。
- 新增 `lesson-kit papers <workspace> append <ps-NNN> --problem <id>`：把题池中已存在、但该卷缺失的题目追加到卷末，保留现有题序、状态、Attempt、草稿和进度；不是“手工改名单/题序”路径，不重置进度。
- 缺题工作流固定为三步：先用现有内容命令把题建到已有知识点，再用 `papers append` 追加到卷末，最后用 `attempts apply --paper_id` 导入作答。导入命令不自动建题。
- 同步更新 Agent 注入提示词与按需契约：manifest 的 `paper_id`、绑定语义、缺题三步走、`papers append`。

## Capabilities

### New Capabilities

无。本 change 扩展既有作答记录与 Paper 执行能力。

### Modified Capabilities

- `agent-assisted-practice-records`：Attempt manifest 增加 `paper_id`；导入可绑定 Paper 执行进度；无 rating 只改执行进度；重绑保留旧 Attempt；幂等重放包含绑定结果。
- `practice-set-export`：导入可创建/更新暂停 Paper 进度而不启动 Practice Run；卷末追加缺失题保留现有进度；显式补题追加是“执行开始后不得静默增删题”的例外。
- `review-workbench`：区分 learning progress 与 Paper execution progress；允许显式补题追加；明确导入绑定不改另一张活动卷。
- `ai-teacher-bridge`：Agent 只能在用户明确要求导入/补题时执行；缺题走“建内容 → 追加 → 导入”；不得直接修改试卷 JSON。

## Impact

- Data：`workbench/data/attempts.py`、`paper_progress.py`、`active_practice.py`、`practice_sets.py`；不新增表/列，`paper_id` 只是 manifest 输入，不落 `problem_attempts`。
- CLI：`lesson-kit attempts check|apply` 的 manifest 与回执；新增 `lesson-kit papers append`。
- Agent 契约：`workbench/bridge/agent_contracts.py`（attempts / practice / content）与 `workbench/bridge/conversations.py::_prompt`。
- 契约文档：`FILE_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/GLOSSARY.md`、`docs/PRODUCT-MANUAL.md`、`docs/REQUIREMENTS.md`、`docs/ARCHITECTURE.md`、`docs/ACTION-GRAPH.md` 及 `docs/action-graph/L1-L4`。
- 既有冲突：本 change 明确把 `review-workbench` 的 “attempt row alone SHALL NOT move progress” 限定为 learning progress，并把显式补题追加写成“执行开始后不得静默增删题”的唯一例外；不静默选边。
- 非目标：不自动建题、不自动选 KP、不支持回填作答时间、不支持任意位置插入、不新增投影重建引擎、不让 parked 导入进度立即生成记录中心 run 卡片。
