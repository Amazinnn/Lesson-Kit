# Tasks

## 1. Spec

- [x] 1.1 proposal（Why / What / Capabilities / Impact）
- [x] 1.2 specs delta：`review-workbench`（MODIFIED Workspace registry、MODIFIED Course and chapter switching、ADD Chapter list derived from pool content、ADD Chapter lens scoping）+ `workbench-ui`（MODIFIED Three-column shell、ADD Chapter switch in the top bar）
- [x] 1.3 design + tasks
- [x] 1.4 `openspec validate 2026-09-20-dashboard-chapter-filter --strict` 通过（补上 workspace-file-isolation 带来的 5 条新场景后）
- [x] 1.5 前置：GLOSSARY「章」条目（含"透镜只改看什么"与 _Avoid_）

## 2. 实现

- [x] 2.1 `workbench/data/pool.py`：`chapters()` 按右侧类型段解析三类 id（kp/prob/mq/fc），`SELECT DISTINCT` + 排序；无表跳过、解析不出忽略
- [x] 2.2 `Pool.scope_prefix()` 收敛前缀（queries/content/server 共 8 处 → 一处）
- [x] 2.3 `queries.hub_stats`：四项统一整课程口径（kps 改全课程，其余本就是全池）
- [x] 2.4 `server/api.py` `set_chapter_lens` + 路由 `POST /api/w/{name}/chapter`（走 `registry.update_active`）；`registry.update_active` 增加章标识符校验（契约层）
- [x] 2.5 `server/pages.py`：顶栏 `_chapter_lens()`（关 = 全课程；开 = 下拉）；`_lens_label()` 让页头/标题如实说明当前透镜
- [x] 2.6 `static/workbench.js` `bindChapterLens()` + CSS（含 640px 窄屏修正）
- [x] 2.7 `cli/main.py`：`use <course> ""` = 全课程（help 写明），输出打印 `<全课程>`
- [x] 2.8 选区零改动：`/pull` 仍按显式 kp 列表取题（回归项见 3.5）

## 3. 测试

- [x] 3.1 `Pool.chapters()`：两章池列出两章、异课 id 与不成形 id 忽略、空课程为空
- [x] 3.2 `scope_prefix()`：有章 = `course-chapter`，无章 = `course-`（全课程）
- [x] 3.3 `POST /chapter` 写注册表（含空串回退）并返回章名单；非法值 400 且注册表不变
- [x] 3.4 hub 四项口径：开 ch07 透镜时 kps/problems 仍是整课程（2/2）
- [x] 3.5 选区跨章：透镜开到 ch07 时，用 ch06+ch07 两个 kp 拉题仍取到两章的题
- [x] 3.6 视图跟随透镜：ch07 透镜下知识点页只有 ch07 的 KP；页头/标题按透镜显示全课程/本章
- [x] 3.7 错误路径：非法章名 400、未知工作区 404、`use` 空章可切全课程
- [x] 3.8 既有用例更新：顶栏 meta 不再含章（移入开关）；`_left_column` 标签随透镜

## 4. 走查（真机，截图）

- [x] 4.1 双章种子：临时工作区用真实 `dmath` 池（ch06）× 1 + 新章 ch07（种子 KP + **真实门禁**入池的微题 batch-002）
- [x] 4.2 三种状态各截一张：全课程、ch06 透镜、ch07 透镜（`.playwright-mcp/lk-walk-d-*.png`）
- [x] 4.3 hub 卡片四项在开关切换前后完全一致（32/346/6/1 三种状态相同）
- [x] 4.4 跨章选区演练：勾选 ch06+ch07 各一个 → 打开 ch06 透镜 → 托盘仍是「已选 2 个」且存储里两个 id 都在
- [x] 4.5 窄视口 375px：发现顶栏被挤压（工作区名换行、下拉被裁成 "ch"）→ 640px 规则修正（品牌只留色块、名字单行省略、下拉定宽），复截确认单行不裁切

## 5. 文档与交付

- [x] 5.1 `docs/GLOSSARY.md`：「章」条目补顶栏开关、透镜作用域与 _Avoid_
- [x] 5.2 `docs/PRODUCT-MANUAL.md`：§3 新增「3.1 章透镜」小节（原 3.1–3.4 顺延）
- [x] 5.3 `docs/ACTION-GRAPH.md` + L1/L2/L3：新增写当前章动作、路由表中加 `POST /chapter`（30→31 条）、queries 口径说明
- [x] 5.4 全量基线：pytest 464 / node 107 / compileall / `openspec validate --specs --strict` 11 / guard
- [x] 5.5 归档：`openspec archive 2026-09-20-dashboard-chapter-filter`

## 备注

- 走查顺手修掉两处：页头「本章/全课程」口径（原先恒定写「当前章节」）与 375px 顶栏挤压。
- 未做（设计非目标）：多选章范围、章显示名/顺序、`pipeline/` 与池 schema 的任何改动。
