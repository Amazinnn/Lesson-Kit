# 任务 B 报告 —— 老 change 未勾选任务完成度核对

工作区：`D:\.codex\worktrees\course-sync\lesson-kit`（分支 `codex/course-sync`，HEAD `e5dc981b`）。
只读审计：未改任何源码 / 测试 / openspec / 文档，未起服务、未开浏览器、未提交。

## 判定口径（先说明本报告的读法）

- B.md 的严格口径是「实现 + node/pytest 用例」。本报告把结论拆成两种标记：
  - **SHIPPED（测试）**：仓库里有实现，且有 node `*.test.js` 或 pytest 用例覆盖。
  - **SHIPPED（证据）**：实现存在，且有该任务自己要求的验收证据（浏览器走查报告 / 截图 / 审计器退出码），
    **但没有自动化用例**。这类在 B.md 的字面口径下不算 SHIPPED，勾选前请自行确认是否接受证据口径。
- **PARTIAL**：实现/证据存在，但任务要求的某个入口、形态或验收面缺失。
- **UNSURE**：缺具体证据，已写明缺哪一条。
- 所有 `path:line` 相对仓库根目录；node 用例按 `tests/workbench/xxx.test.js::用例名` 给出。
- 为免每行重复长前缀：形如 `reports/...`、`acceptance*.md`、`contract-drift.md`、`IMPLEMENTATION-LOG.md`、
  `proposal.md`、`design.md`、`tasks.md` 的引用，均相对该节对应的 `openspec/changes/<change-name>/` 目录；
  其余路径均为仓库根相对。
- 数据类结论另用只读 SQLite 查询核对（`ads-answer-gap-repair`）。

---

## workbench-visual-language-v2（112/173）

verdict: **MOSTLY**（61 项未勾；其中 45 项是真实任务、16 项是 tasks.md 自检 meta。真实任务里 13 项可勾、17 项部分、11 项未开始、4 项缺证据；第 23–24 组未开工、第 25 组部分）

未勾任务在 `tasks.md` 的行号（便于逐条点开）：5.5=`77`、6.5=`85`、8.6=`102`、8.10=`106`、13.4=`149`、15.5=`164`、16.6=`173`、16.8=`175`、17.4=`182`、17.5=`183`、17.6=`184`、17.7=`185`、17.9=`187`、18.6=`196`、19.5=`204`、20.1=`208`、20.4=`211`、21.4=`218`、21.7=`221`、22.1=`225`、22.2=`226`、22.3=`227`、22.4=`228`、22.5=`229`、22.6=`230`、22.7=`231`、22.8=`232`、23.1=`240`、23.2=`241`、23.3=`242`、24.1=`246`、24.2=`247`、24.3=`248`、25.1=`252`、25.2=`253`、25.3=`254`、25.4=`255`、27.4=`268`、28.6=`277`、29.1=`285`、29.2=`286`、29.3=`287`、29.4=`288`、29.5=`289`、29.6=`290`；自检 `296-322`。

### 已交付、可按测试或证据勾选

- [8.6] **SHIPPED（证据）** — 动效 M-7 / M-8 / M-9 均已走查：M-7 在原始报告里按字面判 FAIL（`reports/MOTION-VERIFICATION.md:23`），A-134 改写判据后在 IMPL-M1 复跑 PASS（`reports/IMPL-M1-report.md:28-29`）；M-8 / M-9 原始报告即 PASS（`reports/MOTION-VERIFICATION.md:24-25`）。
- [17.7] **SHIPPED（证据）** — 几何爆点 + 12 片内联 SVG 纸片已实现：`workbench/server/static/workbench.js:938`（`mountMilestoneBurst`）、`:962`（`mountConfetti`）；浏览器证据 `reports/MOTION-VERIFICATION.md:19`（M-3 全对档：爆点 + 12 张纸片 + CTA 不被遮挡）。无 node 用例。
- [20.1] **SHIPPED（测试+证据）** — 逐柱 24ms 错峰：服务端 `workbench/server/records.py:470` 写 `animation-delay:{index * 24}ms`，CSS `workbench/server/static/workbench.css:3626` 的 `.bar-fill` 有 `animation: lk-bar-grow 320ms`（`CD-174` 曾指出旧实现缺这条动画）；用例 `tests/workbench/workbench_ui_interactions.test.js::time view renders thin goal tracks and an exact fixed-axis workload`（断言 3 根柱、14 个日期、峰值/重日标记）；浏览器证据 `reports/MOTION-VERIFICATION.md:26`（M-10 含“逐柱错峰 24ms ✔”）。
- [20.4] **SHIPPED（证据）** — M-10 在 IMPL-M1 后由 FAIL 转 PASS：`reports/IMPL-M1-report.md:28-29`、`reports/MOTION-VERIFICATION.md:26`（原 FAIL 原因是日历格无动画，已修）。
- [21.4] **SHIPPED（证据）** — M-8 / M-9 均 PASS，G-7 装饰层 `pointer-events:none` 有实测：`reports/MOTION-VERIFICATION.md:24-25`、`:119`；IMPL-M1 修复后再次 PASS：`reports/IMPL-M1-report.md:28-29`。
- [21.7] **SHIPPED（证据）** — M-8 / M-9 的 reduced-motion 孪生帧终态差异 0：`reports/MOTION-VERIFICATION.md:397` 及 `reports/MOTION-VERIFICATION-AFTER/extra/twins.json`（M-1…M-12 均有 `terminalEqual:true`）。
- [22.1] **SHIPPED（证据）** — G-1…G-8 全部 PASS：`acceptance-manual-review.md:14`（“`summary.overall = FAIL`；G-1…G-8 全 PASS，FAIL 落在清单层”）。
- [25.1] **SHIPPED（测试）** — 会话列表滚动容器 + 今天/昨天/更早分组：`workbench/server/static/workbench.css:2552`（`#ai-session-list` 的 `overflow-y:auto`）、`workbench/server/static/workbench.js:5793`（分组定义）、`:5898`（`aiRenderSessionList`）；用例 `tests/workbench/agent_session_ui.test.js::the session list groups its entries by recency`（3 组、组标题无计数、`aria-labelledby`）。
- [29.1] **SHIPPED（证据）** — 资产机检闸门：`tools/audit-assets.py:1`；通过证据 `IMPLEMENTATION-LOG.md:1365`（“审计 234/234 全通过，退出码 0（基线 228/234）”）。
- [29.2] **SHIPPED（证据）** — §3.12 实测偏差逐项修正：`IMPLEMENTATION-LOG.md:1365-1388` 逐张列出圆规/画布/地球仪/花瓶/茶杯/果篮/笔筒/钢笔/墨水瓶/叠书/台灯改动；审计 234/234 退出码 0（`:1365`）。
- [29.3] **SHIPPED（证据）** — 可辨认度：`IMPLEMENTATION-LOG.md:1370-1383`（圆规不再读成三脚架、画布不再读成镜子、地球仪支架/网格对称化），且所有者已作判读（`:1178-1188`）。
- [29.4] **SHIPPED（证据）** — 跨图一致性：`IMPLEMENTATION-LOG.md:1385-1388`（十张最长边极差 1.442 ≤ 1.6；`compare-light.png` / `compare-night.png` / `grid-after.png` / `grid-night.png` 已生成）。
- [29.5] **SHIPPED（证据）** — 双主题渲染图：`IMPLEMENTATION-LOG.md:1366-1368`（`compare-light.png` / `compare-night.png`），夜纸渲染见 `grid-night.png`。

### 部分交付

- [8.10] **PARTIAL** — M-1 / M-2 / M-5 / M-6 / M-8 / M-9 均有分镜条与降级帧（`reports/MOTION-VERIFICATION.md` 各条 PASS），但 **M-3 仍 PENDING**（`reports/MOTION-VERIFICATION.md:19`：章节首次完成档不可判定）；“每条分镜条”不齐。
- [13.4] **PARTIAL** — 四档视口无横向滚动已有实测：`reports/IMPL-L1-report.md:38-55`（1440/1280/1024/768 逐档）；**缺 G-8 焦点顺序对比**（全仓无 focus-order 用例，`grep -rn "tab order\|focus order\|G-8" tests/` 无命中）。
- [16.6] **PARTIAL** — S-2 / S-3 截图与 G-1…G-4 全 PASS 有记录（`acceptance-manual-review.md:14`），但截图索引明确“数字对应那一轮；后续修复后需要重跑”（`acceptance-shots/index.md:3`），且 S-7 两侧题目不同（`:55`）。
- [16.8] **PARTIAL** — 16.7 承载位有 pytest：`tests/workbench/test_ui_routes.py::UiRouteTests.test_practice_completion_page_has_the_celebration_slots`；S-3 静帧与 M-2/M-3 降级帧存在，但 M-3 章节首次完成档 PENDING（`reports/MOTION-VERIFICATION.md:19`）。
- [17.4] **PARTIAL** — 日常档/里程碑档两档输出已实现（`workbench/server/static/workbench.js:994` `celebrateCompletion`；M-2 PASS、M-3 全对档 PASS），但任务的里程碑条件包含“章节首次完成”，该条件恒为 false（见 17.6）。
- [17.5] **PARTIAL** — M-2 / M-4 / M-5 / M-6 / M-7 均 PASS，M-3 仍 PENDING：`reports/MOTION-VERIFICATION.md:18-27`。
- [17.6] **PARTIAL** — 两条件判定函数已落地：`workbench/server/static/workbench.js:832`（`isMilestoneRound`，全对 / `chapterFirstCompletion`）；但客户端把章节首次完成硬编码为 false：`workbench/server/static/paper-practice.js:1495`（`dataset.lkChapterFirst = "false"`），注释说明 `practice_runs` 无章节列/首完标志，禁止用代理指标（`:1488-1492`）。⇒ 条件 ① 可用、条件 ② 不可用。
- [17.9] **PARTIAL** — M-2…M-6 / M-11 分镜与降级帧存在（`reports/MOTION-VERIFICATION.md:18-27`），但“两个里程碑条件各一次”缺章节首次完成档（M-3 PENDING）。
- [18.6] **PARTIAL** — S-4 / S-5 截图存在（`acceptance-shots/index.md` 的 S-4/S-5 行），但索引声明采集后代码已变、需重跑（`:3`）；无本轮实时走查。
- [19.5] **PARTIAL** — S-6 / S-7 截图存在，同样需重跑（`acceptance-shots/index.md:3`、`:55`）。
- [22.2] **PARTIAL** — 12 张 S 系列对照图已产出但未入库（`tmp/` 被 `.gitignore` 忽略），且索引自述“后续修复后需要重跑”（`acceptance-shots/index.md:3`）；S-7 两侧题目不同（`:55`）；人工判读页不给结论（`acceptance-manual-review.md:1-6`）。
- [22.3] **PARTIAL** — M-1…M-13 报告与分镜条已产出（`reports/MOTION-VERIFICATION.md`），PASS 11 · FAIL 0 · PENDING 1，PENDING 即 M-3（`:19`）。
- [22.6] **PARTIAL** — 同上；13 条中 M-3 不可判定，且 M-7 的判据已按 A-134 改写（`reports/IMPL-M1-report.md:28-29`）。缺“每条附一行判据核对结果”的统一表。
- [22.7] **PARTIAL** — 降级孪生帧 13/13 终态一致（`reports/IMPL-M1-report.md:28-29`、`MOTION-VERIFICATION-AFTER/extra/twins.json`），但 M-3 章节首次完成档缺；四组偏好组合的截图仅 M-12 目录有 4 张（`reports/MOTION-VERIFICATION-AFTER/M-12/`）。
- [25.2] **PARTIAL** — 用户消息已改沉底面 + 内发丝线：`workbench/server/static/workbench.css:1382-1389`；Agent 长文挂 `.wb-reading`（`workbench/server/static/workbench.js:4858-4866`）；但 Agent 消息仍是扁平 `.msg`（`workbench/server/static/workbench.css:1356-1361` 无底色/圆角/卡片），未成“每条消息一张圆角卡”。
- [25.3] **PARTIAL** — 执行计划已是圆点 + 发丝线（`workbench/server/static/workbench.css:2626-2659`）；但 composer 仍是固定 `rows='2'` 的 textarea（`workbench/server/pages.py:1196`），全仓无 `field-sizing` / `scrollHeight` 自动增高；工具摘要无 ≤240 字截断（`workbench/server/static/workbench.js:4898-4901` 直接写全文）；活动仍是消息流内的 `.ai-activity`（`:5028`），不是右上角可收起浮层。
- [29.6] **PARTIAL** — 审计 234/234 + 并排渲染图已交（`IMPLEMENTATION-LOG.md:1365-1368`）；但该条要求的四条仓库级命令未在此节留输出，且 `3.6-4` 人工判读在 A-99 中仍记“待第 29 组落地后重取”（`IMPLEMENTATION-LOG.md:1307`）。

### 未开始 / 缺证据

- [23.1] **MISSING** — 试卷列表仍是 `<details>` 列表卡，无卡片网格与状态圆点：`workbench/server/pages.py:822` 起的 `practice_sets_page`，`workbench/server/static/workbench.css:2974` 仍是 `.practice-set-card { padding: 20px 22px; border-top: 5px solid … }`；测试仍断言旧结构 `tests/workbench/test_ui_routes.py::UiRouteTests`（`:337-341`、`:413`）。
- [23.2] **MISSING** — 5px 黄带仍在：`workbench/server/static/workbench.css:2974`（`.practice-set-card` 的 `border-top: 5px solid var(--role-yellow)`）。
- [24.1] **MISSING** — hub 仍是等权网格，无“最近使用 4 张置顶”：`workbench/server/pages.py:188-215`（`hub_page` 直接遍历 `workspaces`），`workbench/server/static/workbench.css:3267`（`auto-fit` 等权网格）。
- [24.2] **MISSING** — 卡片信息层级未改：`workbench/server/pages.py:202-207` 仍是单行 `N 个知识点 · N 道题 · N 项待复习`，无 22px 工作区名 / 13px 三计数 / 三个色点。
- [22.4] **MISSING** — 验收关卡未提交签字：人工判读页仍留“需要你确认”签字位（`acceptance-manual-review.md:408`），且整体 `overall = FAIL`（`:14`）。
- [22.5] **MISSING** — 无最终四条命令输出与 §4 通过标准判定记录（`reports/` 下无对应文件）。
- [22.8] **MISSING** — 无动效关卡提交记录（22.6/22.7 的逐条勾选表与未过项清单未入库）。
- [23.3] **MISSING** — 依赖 23.1/23.2，未开始。
- [24.3] **MISSING** — 依赖 24.1/24.2，未开始。
- [25.4] **MISSING** — 依赖 25.2/25.3，且 25.2/25.3 未完成。
- [28.6] **MISSING** — 最终验收未做：变更未归档、S-1/S-8/S-11 未补齐；当前分支相对 `main` 仍领先 45 个提交（`git log --oneline main..HEAD | wc -l` = 45），图谱页逐像素零变化与池 schema 零变更未在本轮复核。
- [5.5] **UNSURE** — 缺证据（任务在 `tasks.md:77`）：字体 fallback / 首次加载无闪烁的走查记录。实现只有 `workbench/server/static/workbench.css:33-38` 的 `@font-face` + `font-display: swap`；没有本轮截图或实测（半粗体文件也不存在，CSS 注释 `:22` 已说明）。
- [6.5] **UNSURE** — 缺证据（任务在 `tasks.md:85`）：题面 / 知识点正文 / 解析三处的字号、行高、行宽、字族与标题层级走查截图。
- [15.5] **UNSURE** — 缺证据（任务在 `tasks.md:164`）：顶栏三段 + 章节面板展开态 + 左栏选中态的走查截图；实现与 pytest 结构断言存在（`workbench/server/pages.py:218-260`，`tests/workbench/test_ui_routes.py::UiRouteTests` `:288-293`），但不构成本任务要求的视觉走查。
- [27.4] **UNSURE** — 缺证据（任务在 `tasks.md:268`）：`contract-drift.md` 存在（`:29` 声明 186 条），但没有本轮“只登记、不动实现”的 diff 证据；当前只能确认文档表存在。

### tasks.md 自检项（296–322，共 16 条）

- [296–317, 319–322] **可直接核** — 编号连续无重复（`grep -oE '^- \[[ x]\] [0-9]+(\.[0-9]+[a-z]?)?' | sort | uniq -d` 无输出）；样板线/铺开分界在 `tasks.md:38` 与 `:236`；设计决策覆盖与 spec delta 清单见 `:300-316`；无构建步骤/npm 由 `tasks.md:21` 与仓库无 `package.json` 佐证。
- [318] **PARTIAL（文案过期）** — 该行要求漂移表“写清 128 处”，实际 `contract-drift.md:29` 已登记 186 条（`CD-001`…`CD-186`）；数字不一致，勾选前应改文案。

---

## workbench-component-forms（0/62）

verdict: **NOT-STARTED**（这是规格先行 change，`proposal.md:14` 明写“只写规格，不写产品代码”；实现任务全部未开工。62 项里只有 7.1 的 GLOSSARY 词条已交付）

- [7.1] **SHIPPED（证据）** — 7 个词条全部在 `docs/GLOSSARY.md`：工具调用卡 `:867`（含“单行流水”形态 `:870-873`）、自绘下拉 `:957`、载荷承载域 `:966`、焦点陷阱 `:973`、焦点归还 `:979`、编号点串 `:985`、模态对话框 `:992`；`docs/PENDING-DEFINITIONS.md` 无这些名词的未定义条目。
- [第 1 组 1.1–1.9] **MISSING**（`tasks.md:37-49`）— 全仓无 `.lk-select`（`grep -rc "lk-select" workbench/` = 0）；原生控件仍在：`workbench/server/pages.py:253`（章节透镜）、`:457`（解析时机）、`:539`（目标类型）、`:733`（排序）、`:976`（运行中发送）、`:1015`（提交粒度）、`:1173`（模型切换）。
- [第 2 组 2.1–2.9] **MISSING**（`tasks.md:51-79`）— 无共享初始化；`<select>` 仍 9 处（`workbench/server/pages.py:253/281/457/539/733/976/1015/1173`）；章节透镜仍是 `.chapter-lens-panel` / `.chapter-lens-option`（`workbench/server/pages.py:237-257`），未并入 `.lk-select`。
- [第 3 组 3.1–3.9] **MISSING**（`tasks.md:81-99`）— 无 `.lk-steps`（全仓 0 命中）；无 `role="progressbar"` 的编号点串组件。
- [第 4 组 4.1–4.9] **MISSING**（`tasks.md:101-118`）— 无 `.lk-dialog`（全仓 0 命中）；`window.confirm` 仍在：`workbench/server/static/kp-experience.js:149`、`practice-flow.js:1353`、`workbench.js:3396/3435/3516/5349/5886`。
- [第 5 组 5.1–5.5] **MISSING**（`tasks.md:120-136`）— 无共享对话框 API；7 个 `window.confirm` 调用点未替换（同上）。
- [第 6 组 6.1–6.8] **MISSING**（`tasks.md:138-164`）— 无 `.lk-tool`（全仓 0 命中）；工具输出仍是 `.ai-plan-output`（`workbench/server/static/workbench.css:2677`），未合并 `.ai-plan-step` / `.ai-activity`。
- [7.2] **MISSING** — `docs/PRODUCT-MANUAL.md` 无自绘下拉 / 分段进度条 / 对话框 / 工具调用卡的章节（`grep -n "自绘下拉\|编号点串\|工具调用卡\|模态对话框" docs/PRODUCT-MANUAL.md` 无命中）。
- [7.3] **MISSING** — `docs/ACTION-GRAPH.md` 无“原生 confirm → 对话框”的改级记录；只有 `:146` 的 agent-chat-simplify 退役记录。
- [7.4] **MISSING** — 归档顺序未发生：v2 与本 change 均未归档。
- [7.5] **MISSING** — 无法完成：`Focus visibility and contrast floors` 在 `openspec/specs/workbench-ui/spec.md` 中不存在（只在 v2 / component-forms 的 delta 里），需先归档 v2。
- [7.6] **MISSING** — 阶段验收未做。
- [第 8 组 8.1–8.7] **MISSING** — 边界复核未做（因为实现未开工）。

---

## workbench-display-redundancy-cleanup（17/21）

verdict: **MOSTLY**（4 条未勾全是验证/走查项；实现侧 17 条已勾，代码里对应元素确实已消失）

- [2.2] **PARTIAL** — hover / focus / 点击钉住 / Esc 已有 node 用例：`tests/workbench/part_practice.test.js::Escape resets pinned preview, so the next mouseleave hides it`、`::preview supports Enter/Space pinning and outside-pointer dismissal`、`::Escape from the focused preview restores question focus without reopening it`；但“手测四态”没有浏览器走查记录，reduced-motion 也未单测（`.part-preview` 本身无动画，`workbench/server/static/workbench.css:5251`）。
- [4.3] **MISSING** — `tools/walkthrough/view.py` 存在，但 change 目录下没有任何三列对照板产物（`tasks.md:44`；`find openspec/changes/workbench-display-redundancy-cleanup -type f` 只有 proposal/design/tasks/specs）。
- [5.3] **UNSURE** — 缺证据（任务在 `tasks.md:50-52`）：没有渲染后逐条核对两条 Requirement 每个 Scenario 的记录；实现侧可指认（例如 `.part-details` 0 命中、`count-badge` 0 命中、`ai-session-entry-meta` 0 命中、`agent-milestone-state` 0 命中、`agent-surface-kicker` 0 命中、设置入口名 `偏好与主题` 在 `workbench/server/pages.py:1099`），但没有对应的验收产物。
- [5.4] **UNSURE** — 缺证据（任务在 `tasks.md:53`）：无屏幕阅读器 / 焦点遍历复核记录；移除里程碑可见状态文字后靠 `aria-label`（`workbench/server/static/agent-ui.js:121-130`）这一条没有辅助技术实测。

---

## stable-runtime-live-reload（6/7）

verdict: **MOSTLY**（全部实现任务已勾；唯一未勾的 3.2 在 changelog 里被明确记为“未完成，不得勾选”）

- [3.2] **MISSING** — 独立全量验收与真实隔离终审未完成：`changelog/2026-10-30-runtime-live-reload.md:55` 明写“task 3.2（独立全量验收）未完成，不得勾选：真实页面验收为修复方自验…独立终审随 reviewer 会话中断未完成”；同文件 `:60` 另记“尚未部署”。
  - 实现与定向测试存在（供对照，不改变结论）：`tests/test_runtime_process.py::test_real_reload_invalid_edit_assets_and_stop`、`tests/test_runtime_admission.py::test_http_held_get_drains_before_shutdown`、`tests/test_runtime_admission.py::test_live_turn_owner_blocks_reload`；但 3.2 要求的是“独立”验收，不是这些用例本身。

---

## graph-settle-smoothness（27/31）

verdict: **MOSTLY**（4 条未勾：2 条明确阻塞、1 条协议变更未做、1 条“未合并/未推远端”已被事实推翻）

- [9.1] **MISSING** — 明确阻塞（`tasks.md:51`）：采用 Obsidian 真实电荷量级，等枢纽节点取代行网格；当前物理核心仍无 hub 结构（`workbench/server/static/graph-physics-core.js:1115` 的注释只说明 hub 在弹簧里被抑制，没有枢纽节点布局）。
- [9.2] **MISSING** — 明确阻塞（`tasks.md:52`）：可见的生长（起点适度收拢），同 9.1。
- [9.3] **MISSING** — Worker 自驱动固定节拍未做（`tasks.md:53`）；当前仍是主机侧 `tick()` 逐次发 `step`：`workbench/server/static/graph-physics.js:278-287`（`tick` 里 `send("step", …)`），worker 侧 `graph-physics-worker.js:89-94` 仅响应 `step`。
- [9.4] **SHIPPED（证据）** — “未合并 main、未推远端”已不成立：图谱重构提交 `adb68806` 在 `origin/main` 与 `origin/HEAD` 中（`git branch -r --contains adb68806` 命中 `origin/main`）。该条是状态备注，事实已翻转，可勾。

---

## graph-node-visual-language（0/126）

verdict: **NOT-STARTED**（126 项全未勾；绘制层改造未开工。只有文档/证据类任务 12.5、12.6、14.1、14.6 已交付，12.4/14.2/14.4 部分）

### 关键反证（说明为什么不是“已实现只是没勾”）

- 节点仍是五层叠加：`workbench/server/static/workbench.js:2313-2325` 创建 `.metric-track` / `.status-ring` / `.node-face` / `.node-unit` / `.node-satellite`；CSS `workbench/server/static/workbench.css:4901-4945`。
- 缩放补偿未做：全仓无 `--inv-scale` / `--stage-scale` / `--node-d`（`grep -rn -- "--inv-scale\|--node-d\|--stage-scale" workbench/server/static/*` = 0）；节点仍写 `--size`（`workbench/server/static/workbench.js:2656`）。
- 统一绘制半径不存在：`grep -rn "nodeScreenRadius" workbench/server/static/*.js` = 0。
- 标签硬阈值仍在：`workbench/server/static/workbench.js:2628`（`LABEL_MIN_RADIUS_PX = 14`）、`:2630`（`labelScaleThreshold`）、`:2660`（可见性判定）。
- 图谱色板/夜纸值未落：`grep -c "graph-paper\|graph-state-new\|graph-scale-1\|graph-ink-1" workbench/server/static/workbench.css` = 0。
- 端点仍按 `NODE_FACE_INSET` 算：`workbench/server/static/graph-physics-core.js:1343-1346`；`edgeStyle` 仍是 `1.05 + score * 2.35` / `.15 + score * .43`（`:1326-1329`）；渲染器未用端点回退（`workbench/server/static/graph-renderer.js` 无 `endpointRadius` 调用）。
- 初始相机仍是硬编码：`workbench/server/static/workbench.js:2041`（`{ scale: .7, panX: 52, panY: -18 }`）。
- 死规则仍在：`.node-wrap.in-scope .status-ring`（`workbench/server/static/workbench.css:4945`）、空函数 `graphSyncScope`（`workbench/server/static/workbench.js:2415`）、`.node-wrap.dim` 的 `.18`（`:4885`）、图例“相关”仍是 `#aaa399`（`workbench/server/static/workbench.css:5033`）。
- 所有 126 条均为 `- [ ]`：`openspec/changes/graph-node-visual-language/tasks.md:67-260`。

### 已交付的少数项

- [12.4] **PARTIAL** — `docs/PRODUCT-MANUAL.md:188-196` 已写入新的节点/标签/关系线/选中/夜纸表述，但标题明确写“节点视觉语言已定稿、**尚未落地**”（`:188`），无法按“用户可观察行为”逐条验证。
- [12.5] **SHIPPED（证据）** — `docs/GLOSSARY.md:790`（图谱色键）、`:796`（屏幕空间尺寸）等词条已建，未留未定义名词。
- [12.6] **SHIPPED（证据）** — `docs/ACTION-GRAPH.md:195` 明写“本图谱的动作不新增、不退役、不改级”；`docs/action-graph/L3-actions.md:269` 同记录。
- [14.1] **SHIPPED（证据）** — 对比脚本 `tools/graph-layout-diff.js:1` 已交付；`tools/graph-baseline/EVIDENCE.md` 记录连跑两次逐字节相同、自比差异 0、负向对照 2 条差异退出码 1。
- [14.2] **PARTIAL** — 合成基线已入库：`tools/graph-baseline/baseline.json`（`schema=lessonkit.graph-layout-snapshot/1`，`input.graph=synthetic-deterministic-v1`，96 节点 / 338 边）；任务同时要求 dmath/ch06 的 31 节点真实基线，仓库里没有该文件（`tools/graph-baseline/` 只有 synthetic 一份）。
- [14.4] **PARTIAL** — 证据文件 `tools/graph-baseline/EVIDENCE.md` + README + 复跑命令已入库，但只有 baseline/自比；没有 `after.json` / `diff.json`（因为绘制改造未发生）。
- [14.6] **SHIPPED（证据）** — SI-0 已写进 `acceptance.md` §0.2（`:70`）与 §4（`:234`），并与 SI-1…SI-5 并列为核心门禁。
- [其余 119 条] **MISSING** — 未实现，或依赖未实现的绘制改造（1.x–11.x、13.x、14.3/14.5、第 15/16/17/18/19/20/21/22/23 组）。

---

## graph-free-force-field（143/160）

verdict: **MOSTLY**（17 条未勾；其中 4 条已由事件/文档/浏览器复核解决，3 条缺用户实测，10 条是明确记录的开放观察或待裁决项）

- [8.2] **MISSING** — 重叠对数仍有 10–56 对（任务自述 `tasks.md:88-90`），未修；当前布局仍按可读性下限投影（`workbench/server/static/graph-physics-core.js` 的碰撞/可读性逻辑）。
- [8.3] **MISSING** — 首帧仍有 49.7px 位移（任务自述 `tasks.md:91-93`），未改。
- [8.5] **SHIPPED（证据）** — `Finite crossing optimization` 已在 delta 中作为 `REMOVED` 登记并说明代码里不存在候选布局/交换优化：`openspec/changes/graph-free-force-field/specs/workbench-ui/spec.md:22-33`；该动作由已勾的 22.1 完成。
- [8.6] **UNSURE** — 缺证据：D5 的结论是“不额外标记，只把孤点拉进画面内”，但仓库没有“孤点确实在画布内”的实测/用例；`graph-physics.test.js` 无孤儿节点断言。
- [8.7] **SHIPPED（证据）** — 图谱重构提交 `adb68806` 已在 `origin/main`（`git branch -r --contains adb68806` 命中 `origin/main`），不再是“未合并/未推远端”。
- [9.8] **MISSING** — 适配缩放 1.05 封顶仍在：`workbench/server/static/workbench.js:2559-2561`（`Math.min(1.05, …)`）；是否抬高待所有者定（`tasks.md:122-123`）。
- [10.9] **MISSING** — 滑槽只能让图变松、不能再变紧；待所有者定（`tasks.md:142-143`）。
- [11.5] **MISSING** — 滑槽往返后布局更紧的起点依赖问题未修（`tasks.md:154-156`）。
- [12.4] **MISSING** — c02 的 86 个点尺寸全相同（重要性分数全 0）；属 8.6b 节点尺寸完整设计，已被推迟（`tasks.md:166-167`）。
- [15.6] **MISSING** — 明确“观察，未改”：端口扇出的斜出角未处理（`tasks.md:225-226`）。
- [15.7] **UNSURE** — 缺证据：需要所有者在真实浏览器目视确认“线头与点相接”；headless SwiftShader 不栅格化边层，仓库无真机判读记录。
- [17.4] **SHIPPED（证据）** — 由已勾的 17.5 浏览器复核覆盖：“平移仍保留选中；空白点击会清除选中并收起看板”（`openspec/changes/graph-free-force-field/tasks.md:250-252`）。
- [18.1] **SHIPPED（证据）** — 查清结论已写在任务里（选中放大来自 `graphCenterOn` 的 `Math.max(scale, .78)`），代码可指认：`workbench/server/static/workbench.js:2511`。
- [18.2] **MISSING** — 是否去掉 `Math.max(scale, .78)` 待所有者定（`tasks.md:259-260`）；代码仍是 `:2511`。
- [21.5] **MISSING** — 25ms 天花板的 A/B/C/D 四个选项待所有者定（`tasks.md:311-315`）；无选定后的实现。
- [22.7] **UNSURE** — 缺证据：tick 降到 8.35ms 后的真机复测未记录（`tasks.md:331-333`）；任务要求所有者用 `runs/fps-probe-snippet.js` 复测。
- [22.8] **MISSING** — 遗留仍在（`tasks.md:334-335`）：`resolveCongestion` 函数本体存在（`workbench/server/static/graph-physics-core.js:441`），`congestionStats` 仍导出（`:1600`）。

---

## agent-chat-simplify（18/19）

verdict: **MOSTLY**（唯一未勾的 6.4 是真实浏览器验收，任务自己已把未执行项写清）

- [6.4] **PARTIAL** — 已执行并记录的浏览器事实：`data-plain-text` 生效（`workbench/server/pages.py:1196`）、Enter/Ctrl+Enter 发送、Shift+Enter 换行、满宽、IME 229 不发送、字号 16px、chips/kicker/side-label/placeholder 消失、长气泡折叠（`tasks.md:39`）。**明确未执行**：真实 provider 轮次下工具卡输出/审批详情/恢复卡的浏览器折叠、审批单卡与空队列直发的浏览器级走查、真实触控设备（`tasks.md:40`）。
  - 实现侧可指认：`workbench/server/static/workbench.js:4831`（`wbApplyCollapse`）、`:4152`（审批详情折叠）、`:4699`（恢复卡折叠）；用量见 `workbench/server/static/workbench.css:2705-2737`。
  - 已有自动化：`tests/workbench/workbench_ui_interactions.test.js::tool activity cards show terminal failures and never display impact`（`:3556`/`:3606` 断言输出块是 collapse host）、`tests/workbench/agent_session_ui.test.js::pending Paper approval restores beside the composer and accepts sends into the paused queue`（`:1322`）；但浏览器级折叠/审批单卡仍缺。

---

## ads-answer-gap-repair（18/22）

verdict: **MOSTLY**（修复主体已落：3 个基线空解析已补、客观题只剩 1 个已知 keyless；但 7.1 的 40 字门槛与基线快照无法复核、7.2 校验器对当前池不通过、7.3 无快照、8.3 只完成一半）

本轮只读核对：`c02` 池不在本 worktree（`pool/` 下无 `c02.db`，只有 `dmath.db.ingest-backup` 与 `ingest/`、`scripts/`），实际注册库在用户级注册表指向的
`D:\Documents\Document_In_University\课程\2026-2027 秋冬 大二上\高级数据结构与算法分析\.lessonkit\pool\c02.db`
（`~/.lessonkit-workbench/workspaces.json`）。以下查询均为 `mode=ro`。

- [7.1] **PARTIAL** — 对“基线 497 行”的实体修复大体成立，但不能算全绿：
  - 3 个基线空解析已补齐：`c02-ch04-prob-001`（674 字）、`c02-ch13-prob-004`（423 字）、`c02-ch07-prob-021`（485 字）均有 `【答案】【解析】`。
  - 客观题 keyless 只剩 1 行：`c02-ch07-mq-007`（yes_no），正是 2026-10-09 复核里登记的 residual（`tasks.md:87-96`）；另外 74 个无 `answer_key` 的行是 `quiz_type=None` 的 `other/calculation/design` 题，按设计不带客观答案键。
  - `error_reason` 分布：108 行 ≤15 字（对应“新增 109 条短标签”的例外，接近 1 行差）、216 行在 20–39 字（**满足 4.1 的 20–100 字，但低于 7.1 字面的 sub-40 = 0**，两条判据自身冲突）、131 行 40–79 字、5 行 80+ 字、1 行为空。
  - **无法证明的两项**：“346 existing keys untouched” 与 “497 IDs retained” 需要基线 JSON，仓库里没有（`pool/` 下无 `c02.db`；`c02.db` 在用户注册表指向的外部路径）；当前 535 行中 496 行 `created_at` 早于 2026-10-09、39 行是 2026-10-11 之后新增，无法逐 ID 对齐。
- [7.2] **MISSING** — `python pipeline/scripts/validate-pool.py --db <c02> --chapter ch01` 退出码 **2**，报告 `ERROR: 2`（`missing required table 'candidate_problems'` / `'candidate_attempts'`），不是 0；与 change 里“current audit exits 1 with 108 findings；frozen validator’s retired-schema failures cannot prove pool quality”的记录一致（`tasks.md:87-96`）。
- [7.3] **UNSURE** — 缺证据：没有找到应用后立即保存的 `problem_progress` / `problem_attempts` / `review_schedule` 字节一致快照；当前计数为 280 / 392 / 280（基线是 36 / 39 / 36，`tasks.md:8-9`），只能说明后来有真实练习，无法证明修复未改动学习记录。change 自己的复核也写“No saved immediate post-apply byte-identical learning snapshot was found for 7.3”（`tasks.md:92-95`）。
- [8.3] **PARTIAL** — `openspec validate ads-answer-gap-repair --strict` 通过（实测输出 “Change 'ads-answer-gap-repair' is valid”，退出码 0；`openspec validate --specs --strict` 为 21/21 passed）；但 `tasks.md` 的复选框仍未勾（“check off this change’s tasks”这一半未做，`tasks.md:84-85`）。

---

## 需要人决断

1. **v2 铺开段是否继续**：23.1 / 23.2 / 24.1 / 24.2 / 25.2 / 25.3 是 6 个未实现的可见功能；22.4 关卡整体 `overall = FAIL`（`acceptance-manual-review.md:14`）且未签字（`:408`）。是补实现后重跑关卡，还是把这些条目退役/降级，需要所有者定。
2. **v2 17.6 条件 ② 的数据事实**：`practice_runs` 没有章节列/首完标志，客户端只能硬编码 false（`workbench/server/static/paper-practice.js:1495`）。要兑现“章节首次完成”，得先在 DATA_MODEL / OpenSpec 定义该事实（CD-164），不能由实现代理。
3. **v2 漂移表条数口径**：tasks 27.2 写 174、自检 318 写 128、`contract-drift.md:29` 写 186。勾选前需统一（否则 27.2/318 的“写清 N 处”自相矛盾）。
4. **component-forms 是否排期实现**：62 项只有 7.1 词条交付；4 个组件（自绘下拉 / 编号点串 / 对话框 / 工具调用卡）都没有代码。若继续，需按该 change 的 T-1…T-9 先拍板（`tasks.md:25-31`）。
5. **graph-node-visual-language 是否启动**：126 项 0 勾，且当前图仍是旧的五层圆盘 + 缩放阈值；需要决定它与 V1 视觉基线谁先、是否拆分重排。若暂不启动，建议明确标注“挂起”而不是保持 0/126。
6. **graph-free 4 个待裁决点**：9.8（Fit 上限 1.05）、10.9（滑槽只能变松）、18.2（选中放大 0.78）、21.5（40fps 天花板 A/B/C/D）——都需要所有者拍板，代码里仍保留现状（`workbench/server/static/workbench.js:2559-2561`、`:2511`）。
7. **ads-answer-gap-repair 的池口径**：当前池 535 行（496 行早于 2026-10-09、39 行之后新增）；客观题只余 `c02-ch07-mq-007` 一个 keyless，3 个基线空解析已补齐，但 19 个空 `solution` 全是 2026-10-11 新增行；`error_reason` 有 216 行在 20–39 字——满足 4.1 的 20–100，却不满足 7.1 字面的 sub-40 = 0。需要先决定“只对 497 行基线判”还是“对当前 535 行重开修复”，以及 7.1 的 40 字门槛与 4.1 的 20 字下限谁作准。另外 `validate-pool.py` 因退役 `candidate_*` schema 退出 2，需要先决定该校验器是否仍作数。
8. **stable-runtime 3.2**：独立终审随 reviewer 会话中断未完成、安装也尚未部署（`changelog/2026-10-30-runtime-live-reload.md:55-60`）；需要另派独立会话或明确由所有者代签。

---

## 总体总结

- **不建议整份勾**：`workbench-display-redundancy-cleanup` 的实现 17 条已勾，剩下 4 条只有 2.2 有 node 测试、4.3/5.3/5.4 是缺证据的走查项；`stable-runtime-live-reload` 除 3.2 外全部已勾，而 3.2 被 changelog 明确记为未完成；`agent-chat-simplify` 除 6.4 外全部已勾，6.4 已把未执行项写清。
- **可大量补勾但非整份**：`graph-free-force-field` 17 条未勾里 4 条可由既有事件/文档/浏览器复核解决（8.5 / 8.7 / 17.4 / 18.1），其余 10 条是明确的开放观察或待裁决，3 条缺用户实测；`graph-settle-smoothness` 的 9.4 可由 `origin/main` 已含 `adb68806` 直接勾掉，9.1/9.2/9.3 仍不能勾；`ads-answer-gap-repair` 只有 8.3 的 validate 一半完成，7.1 是“基线实体大体修复但 40 字门槛/基线快照无法复核”的部分状态，7.2 对当前池不成立（校验器退出 2），7.3 无快照。
- **v2 是“大部分实现 + 验收欠账 + 铺开段未做”**：112 条已勾之外，45 条真实未勾项里约 13 条可凭测试或既有报告补勾（8.6、17.7、20.1、20.4、21.4、21.7、22.1、25.1、29.1–29.5），17 条部分交付（主要是章首次完成条件、二次浏览器走查、25.2/25.3 的卡片与 composer），11 条未开始（23/24 全部、25.4、28.6、22.4/22.5/22.8），4 条缺证据（5.5/6.5/15.5/27.4）；另有 16 条是 tasks.md 自检 meta，其中 318 的“128 处”已过期。
- **两个基本未开始**：`workbench-component-forms` 62 项只有 7.1 词条交付（规格先行，实现另起 PR）；`graph-node-visual-language` 126 项只有 12.5/12.6/14.1/14.6 及部分文档交付（12.4/14.2/14.4 部分），绘制层改造完全未开工。
- **一句话**：本 worktree 能凭现有测试/证据安全补勾的约 19 项（v2 13 + free 4 + settle 1 + component 1）；display 的 2.2 只能算部分、agent 的 6.4 缺浏览器段、ads 与 runtime 的未勾项都不能补。其余要么是真实未完成，要么缺独立验收/用户实测证据，不能按印象勾。
