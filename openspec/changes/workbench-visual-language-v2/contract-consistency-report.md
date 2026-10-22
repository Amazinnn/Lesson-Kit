# 契约一致性核对报告（IMPL-N2）

> **性质**：**只读审计报告**。本文件**只登记不一致**，**不修任何一边**。
> 修哪一边（spec delta / docs 同步 / 产品代码）由主会话裁决。
>
> **审计对象**：本变更的两份 spec delta（`workbench-ui` / `workbench-settings`）、
> 一份 `calendar-workload` delta、`design-notes/component-spec.md`（28 组件 × 8 态）、
> `design.md`（D-1…D-15）、权威表 `design-notes/night-paper-tokens.md`、
> `docs/GLOSSARY.md` / `docs/PRODUCT-MANUAL.md`。
>
> **核对基准（代码状态）**：
> - **审计起点** `git rev-parse HEAD` = `51791b1d5121d60e6b06d21df0ddabfab758ce99`
> - **审计落笔时** `git rev-parse HEAD` = `82e4c962e246885df9c6b2421942aa4635867cd9`
> - 两者之间有 **14 个并发提交**（见 §6），其中 **4 个提交动了本报告的核对对象**：
>   `b0e48f31`（补进 `specs/workbench-ui/spec.md` 4 处条款：进度带 / 焦点环 / 空态沉底面 /
>   知识点按章分组）、`187a3bd2` + `e137d608`（`night-paper-tokens.md` 补 A-83 两个图谱作用域
>   token、修正 §3.11 合计式；`GLOSSARY.md` 补六个词条）、`8bd0edcd`（`GLOSSARY.md` 记
>   `.rich-text` 已退役）、`bb32c148` + `82e4c962`（资产规格修正 + 实物插画核实结论）。
>   ⇒ **本报告的所有结论都是按 `82e4c962` 那一轮的代码状态写的**；
>   起点 `51791b1d` 与终点 `82e4c962` 之间
>   **产品代码只有 `workbench/server/static/paper-practice.js` 与 `practice-flow.js` 两个文件变动**
>   （`git diff --stat 51791b1d 82e4c962 -- workbench/server/static/ workbench/server/` 的完整输出）；
>   **`workbench.css` / `agent-ui.css` / `pages.py` / `records.py` 一行未动**
>   ⇒ §2、§3、§4 的全部结论**不受并发影响**（见 §6.2）。
>
> **复核命令**（本轮全部实跑，输出见 §7）。

---

## 0. 覆盖统计总表

| 核对组 | 查了多少条 | 不一致 | 一致 |
|---|---|---|---|
| 1. spec delta → 实现（`workbench-ui` 25 条 Requirement） | 25 条 Requirement / 116 个 Scenario | **9** 条 Requirement | 16 条 |
| 1b. spec delta → 实现（`workbench-settings` 7 条） | 7 条 Requirement / 27 个 Scenario | **1** 条 Requirement | 6 条 |
| 1c. spec delta → 实现（`calendar-workload` 1 条） | 1 条 Requirement / 14 个 Scenario | **2** 个 Scenario | 12 |
| 2. `component-spec.md` 28 组件 × 8 态 → 实现 | 28 组件（224 个状态位） | **21** 个组件 | 7 个组件 |
| 3. `design.md` D-1…D-15 → 实现 | 15 条决策 | **3** 条部分失守 | 12 条 |
| 4. `night-paper-tokens.md` ↔ 实现（定义集合 / 引用集合 / 亮夜配对） | 53 值 token + 66 结构 token + 2 图谱专用 | **5** 处 | 值 token 53/53 全对 |
| 5. `GLOSSARY` / `PRODUCT-MANUAL` 名词 ↔ 实现 | 13 条视觉名词 + 1 处实现另起叫法 | **2** 处 | 12 条 |

**合计**：不一致 **43** 条（其中 **7 条**是「任务清单已登记为待办」而非契约冲突，
**36 条**是需要主会话裁决的真不一致）。

---

## 1. spec delta → 实现

### 1.1 `workbench-ui` delta（`openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`）

**逐条落点核对结果**

| # | Requirement | 落点 | 判定 |
|---|---|---|---|
| 1 | Paper levels and elevation（`:3-30`） | `workbench.css:43-244`（`:root` 四层 token）、`:134-139`（surface 六件） | ✅ |
| 2 | Theme preference and the night paper value set（`:32-70`） | `workbench.js:350-366`（`storedTheme`/`effectiveTheme`/`applyTheme`）、`workbench.css:253-318`（夜纸块） | ✅ |
| 3 | Lamp transition carries the theme change（`:72-114`） | `workbench.js:680-782`（`runLampTransition`）、`workbench.css:2988-3016`（4 条 keyframes） | ✅ |
| 4 | Reading face and interface face（`:116-145`） | `workbench.js:368-386`、`workbench.css:2840-2875` | ⚠️ **部分不一致 → INC-01** |
| 5 | Motion system and reduced-motion downgrade（`:147-210`） | `workbench.css:3432-3451`（降级闸门）、`workbench.js:387-419` | ✅ |
| 6 | Round completion celebration in two tiers（`:212-273`） | `workbench.js:786-1001` | ⚠️ **第二条件恒 false → INC-02** |
| 7 | Consecutive-correct escalation feedback（`:262-312`） | `workbench.js:529-679`、`workbench.css:3140-3210` | ✅ |
| 8 | View transition and skeleton loading state（`:314-361`） | `middle-navigation.js:72-141`、`workbench.css:3034-3058` | ✅ |
| 9 | Key feedback audio cues（`:363-401`） | `sfx.js:22-144`、`workbench.js:1450-1570` | ✅ |
| 10 | Focus visibility and contrast floors（`:403-427`） | `workbench.css:838-841`/`:967`/`:1323`/`:1371`/`:1915`/`:2213` | ✅ |
| 11 | Density zoning（`:429-449`） | `workbench.css:2840-2862`（阅读刻度）vs `:2780-2796`（记录数据面） | ✅ |
| 12 | Shared reading typographic layer（`:450-478`） | `workbench.css:1760-1880`（`.wb-reading`）、`tests/test_markdown_render_parity.py` | ✅ |
| 13 | Interface copy voice（`:480-506`） | `pages.py:92-105`（空态三段） | ⚠️ **文案未清 → INC-03** |
| 14 | Workspace card information hierarchy（`:507-533`） | `pages.py:144-170`（`hub_page`）、`workbench.css:2194-2198` | ❌ **未实现 → INC-04** |
| 15 | Accumulated work made visible on existing learning facts（`:535-574`） | `pages.py:123-140` + `:611`（知识点计数条）、`records.py:360-393`（四张摘要卡） | ✅ |
| 16 | Knowledge-point list grouped by chapter（新增，`:610-650`） | `pages.py:625-627`、`workbench.css:1093-1135`、`workbench.js:199-232` | ✅ |
| 17 | Soft Mondrian visual foundation（MODIFIED，`:657-...`） | `workbench.css` token 层 + `:795-823`（左栏）+ `:3146-3200`（连对档位） | ✅ |
| 18 | Learning content is the visual anchor（MODIFIED） | `workbench.css:2840-2862`、`:3462-3500` | ✅ |
| 19 | Redundant state cues（MODIFIED） | `pages.py:17-19`（三态点）、`workbench.css:1179-1250` | ⚠️ **Paper 状态点几何缺失 → INC-05** |
| 20 | Records center（MODIFIED） | `records.py:60-130`、`:360-393`、`:495-580`；`workbench.css:2494-2760` | ✅ |
| 21 | Learner settings in the left rail（MODIFIED） | `pages.py:987-996`、`workbench.js:1308-1326`、`practice-flow.js:483` | ⚠️ **标签文案与契约不符 → INC-06** |
| 22 | Agent rail presentation keeps the learning page primary（MODIFIED） | `agent-ui.css:25-51`（chips）、`agent-ui.js:98-100`（composer 增高） | ⚠️ **会话列表无滚动容器 → INC-07** |
| 23 | Accessible Paper status dots（MODIFIED） | `paper-practice.js:575-621`、`workbench.css:3957-3980` | ⚠️ **几何冗余通道不齐 → INC-05（同一处）** |
| 24 | Same-workspace middle navigation preserves the Agent rail（MODIFIED） | `middle-navigation.js` 全文 | ✅ |
| 25 | Three-column shell with navigation（MODIFIED） | `workbench.css:640-665`（几何单一真值）、`pages.py:223-240`（顶栏三段式） | ✅ |

#### INC-01 —— 「阅读字面」切换只换了字族，但**没换的那一半（17px / 1.75 / 38em）实际被读面 token 绑住**，属**已兑现但表述有歧义**

- **条款位置**：`workbench-ui` delta `:116-145`「Reading face and interface face」
  与 `workbench-settings` delta `:136-158`「Reading face preference selects the reading type family」。
- **实现落点**：
  - `workbench.js:377-386` `applyReadingFace()`：`root.dataset.face = "serif"|"sans"`，
    且 `sans` 时 `root.style.setProperty("--font-read", "var(--font-ui)")`。
  - `workbench.css:2840-2848`：`:is(.wb-reading, .wb-reading--stem), .practice-question-card,
    .knowledge-body, .practice-solution, .linked-problem-text { font-family: var(--font-read);
    line-height: 1.75; }` + `:is(.wb-reading, .wb-reading--stem) { font-size: var(--fs-reading); }`
  - `:is(.wb-reading, .wb-reading--stem) > *, … { max-width: var(--measure); }`（`:2853-2862`）
- **判定**：**一致**。契约说「switching the reading face SHALL change the type family only:
  body size, line height and measure SHALL NOT change with it」——实测**只换 `--font-read`**，
  `--fs-reading`(17px) / `line-height: 1.75` / `--measure`(38em) 三者**未被触碰**。
  `workbench.css:2871-2874` 的 Agent 长文也是同刻度。
- **⚠️ 但有一处实现细节值得登记**：`d.dataset.face`（`workbench.js:380`、
  `pages.py:1474` 的首屏引导脚本）**在 CSS 里零命中**（`grep -rn "data-face" workbench/ --include=*.css`
  无输出）⇒ 这个属性是**死钩子**，真正生效的是 `--font-read` 的 inline 覆盖。
  ⇒ **不是契约不一致，是实现冗余**；建议在代码侧删掉死钩子，或在 CSS 侧补一条
  `html[data-face="sans"] { --font-read: var(--font-ui); }` 让首屏引导脚本真正起作用
  （当前首屏先渲染衬线、JS 跑完才切成无衬线 ⇒ **首屏会闪一次字族**，与
  `workbench-settings` delta `:91-95`「the workbench SHALL take the system setting at the
  moment the page is first painted, without a flash of the other value set」的精神相悖 ——
  但该句只约束**主题**，不约束字面 ⇒ **归为「实现冗余 + 首屏闪字族」的低优先项**）。

#### INC-02 —— 里程碑档的**第二条件「章节首次完成」恒为 false**（契约可满足性缺陷）

- **条款位置**：`workbench-ui` delta `:220-222`
  「A round SHALL reach the milestone tier when it is finished fully correct **or** when it
  completes a chapter for the first time.」
- **实现落点**：`workbench.js:797-805` `isMilestoneRound(facts)` —
  `if (facts.chapterFirstCompletion === true) return true;`
  + `workbench.js:817-821` `completionFacts()` — `chapterFirstCompletion: data.lkChapterFirst === "true"`
  + `paper-practice.js:1401` — `ids.completion.dataset.lkChapterFirst = "false";`（**写死**）
- **判定**：**不一致（事实层）**。客户端与服务端**都**把第二条件写成恒 false ⇒
  **规格承诺的两个触发条件里有一个永远不触发**。
- **旁证**：本变更自己的 `contract-drift.md` **CD-167** 已登记同一事实
  （「`practice_runs` 没有章列、没有『首次完成』标志 ⇒ 该条件不可判定」），
  `IMPLEMENTATION-LOG.md:435` 记「里程碑第二条件不可判定（CD-167）」。
  **实测复核 schema**：`pool/scripts/pool_schema.py:725-740` 的
  `CREATE TABLE practice_runs` 字段为
  `id / source_kind / source_ref / source_label / kp_ids_json / practice_mode /
  rating_mode / items_json / status / started_at / finished_at`
  —— **无章列、无「首次完成」标志** ⇒ 第二条件**无数据来源**。
  ⇒ **这不是新发现，是实现按 `decisions.md` A-29 如实登记后的悬空条款**。
- **建议改哪一边**：**改 spec delta**（把第二条件降级为「待数据来源定义」或移出本 delta），
  **不要**改代码去造近似口径（A-29 明令禁止代理指标）。
  改动需同步 `docs/DATA_MODEL.md`（若将来给 `practice_runs` 加章列）。

#### INC-03 —— 「一个标签/一句话里不混中英」未落地（4 处英文标签）

- **条款位置**：`workbench-ui` delta `:480-506`「Interface copy voice」
  → 「SHALL NOT mix Chinese and English within one label or one sentence」
  + Scenario `:501-505`「One language per label」。
- **实现落点（4 处未译英文标签）**：
  | 文件:行 | 现状 | 应为（依 `copy-table.md`） |
  |---|---|---|
  | `workbench/server/pages.py:273` | `<p class='agent-surface-kicker'>Agent activity</p>` | `Agent 活动`（copy-table P-16） |
  | `workbench/server/pages.py:286` | `<p class='agent-surface-kicker'>Artifact</p>` | `工件`（copy-table P-21） |
  | `workbench/server/pages.py:405` | `<p class='section-kicker'>Congratulations!</p>` | `本轮完成`（copy-table P-68） |
  | `workbench/server/pages.py:465` | `>让 Agent 填<` | 保留 `Agent`（产品名，**不算违规**） |
- **判定**：**不一致**。前 3 处是**纯英文**标签（不是混排，但违反「界面文案统一中文」的
  `copy-table.md` 口径）；契约原文只禁「同一标签内混排」，**纯英文标签是否违规需要裁决**。
- **旁证**：`design-notes/copy-table.md:910`/`:915`/`:965` 逐条给出「改前 → 改后」；
  本变更 `tasks.md` **第 26 组（文案清理）0/3 完成**；同目录 `copy-table-gap.md`
  （并发提交 `54653388` 落的 IMPL-N3 产物）也记了这条。
- **建议改哪一边**：**改代码**（按 `copy-table.md` 落地 3 处译文），
  因为 `copy-table.md` 已经是定案且 `PRODUCT-MANUAL.md` 已按中文口径写。
  ⚠️ 但本轮**不得**动代码（IMPL-N2 是只读任务）。

#### INC-04 —— 「工作区卡片信息层级」**整条未实现**

- **条款位置**：`workbench-ui` delta `:507-533`「Workspace card information hierarchy」
  + 3 个 Scenario（最近使用置顶 / 计数带色点 / 计数不只靠颜色）。
- **实现落点**：`workbench/server/pages.py:144-170` `hub_page()`：
  ```python
  detail = (f"{stats.get('kps')} 个知识点 · {stats.get('problems')} 道题 · "
            f"{stats.get('due')} 项待复习")
  ...
  "<section class='workspace-grid' aria-label='工作区列表'>{''.join(cards)}</section>"
  ```
  `workbench.css:2194` `.workspace-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin-top: 28px; }`
- **判定**：**不一致**。实测：
  1. **无「最近使用置顶」**——`hub_page()` 按 `workspaces` 传入顺序平铺，
     **无排序、无置顶区、无大小卡**；
  2. **三个计数挤在一个 `<p>` 里**（用 `·` 分隔），**没有「每个计数前一个小色点」**；
  3. 计数用 `.workspace-card p { color: var(--ink-muted); }`（默认 14px），
     **不是契约要求的「更小字号一行排开」**；
  4. 卡片一律 `min-height: 150px` **等权**，没有「名称是卡上最大字号」的分级。
- **旁证**：`tasks.md:244-248` **第 24 组 0/3 完成**；
  `contract-drift.md` **CD-096** 已登记「首页 22 张卡片完全等权…三个计数与普通正文同字号同灰」。
- **建议改哪一边**：**改代码**（tasks 第 24 组尚未开工，是明确的待办而非契约冲突）；
  若排期紧张，**改 spec delta** 把这条降级为「后续 change」也是一种合法裁决。

#### INC-05 —— Paper 状态点的**冗余状态通道（几何）只覆盖 6 个状态里的 1 个**

- **条款位置**：`workbench-ui` delta `:920-925`（`Accessible Paper status dots` 的正文）
  「Every dot SHALL carry the redundant state channel: the dot's colour states the status
  and **a geometric difference states it a second time**, so that the panel is readable
  without colour.」
  + Scenario `:927-931`「A dot states its status twice」。
- **实现落点**：`workbench/server/static/paper-practice.js:575-602` `itemStatus()` 产出
  **6 个状态**：`unanswered` / `filled` / `stuck` / `correct` / `wrong` / `locked`；
  `workbench/server/static/workbench.css:3957-3980`：
  ```css
  .paper-dot.state-filled   { background: var(--role-yellow); color: var(--ink-on-warm); }
  .paper-dot.state-locked   { background: var(--role-blue-wash); color: var(--role-blue); }
  .paper-dot.state-correct  { … box-shadow: inset 0 0 0 2px var(--ink-strong); }  /* + 勾形 */
  .paper-dot.state-wrong, .paper-dot.state-stuck { background: var(--role-red-wash); … }
  ```
- **判定**：**不一致**。
  - `correct` 有几何（内墨环 + 勾形伪元素，`:3962-3978`）✅
  - `wrong` / `stuck` **只有颜色**（红洗底）❌ —— 且**两态同色同形**（同一行规则），
    灰度下 `wrong` 与 `stuck` **完全无法区分**；
  - `filled`（黄底）/ `unanswered`（默认底）**只有颜色**；
    `filled` 与 `unanswered` 在**灰度下都读作「一个圆点」**。
  ⇒ 契约的「colour states it and a geometric difference states it a second time」
  **只兑现了 1/6**（只有 `correct` 一态有几何）。
- **注意**：这**不是**「全靠颜色」——`aria-label`（`paper-practice.js:615-616`）带了状态文字，
  但契约明写「冗余通道**不是文字标签**」（`GLOSSARY.md:375-381`「冗余状态通道」_Avoid_「状态文字标签」）
  ⇒ 文字 aria-label **不算**冗余通道。
- **建议改哪一边**：**改代码**（给 `wrong`/`stuck`/`filled` 补几何：叉形 / 半填充 / 描边档），
  `component-spec.md` §4.14 的 `.lk-dot--cross/--dash/--check` 三件套已在产品里，
  可直接复用同一套几何语言。

#### INC-06 —— 左栏自评开关的**标签文案与契约不符**

- **条款位置**：`workbench-ui` delta `:817-820`（`Learner settings in the left rail`）
  「Its first preference SHALL be a checkbox, **「练习与组卷显示自评」**, defaulting to on」。
- **实现落点**：`workbench/server/pages.py:993`
  `"练习显示自评"`（**少了「与组卷」三字**）
- **判定**：**不一致（用户可见文案）**。
- **旁证**：`PRODUCT-MANUAL.md:610` 已按契约写「练习与组卷显示自评」⇒
  **手册与产品不一致**（手册对、实现错）。
- **建议改哪一边**：**改代码**（`pages.py:993` 补齐「与组卷」三字），
  同步核对 `docs/PRODUCT-MANUAL.md` 已一致、无需动。

#### INC-07 —— Agent 右栏的**会话列表没有自己的滚动容器**

- **条款位置**：`workbench-ui` delta `:889-895`
  「The rail's session list SHALL have its **own scrolling container**, so that a long list
  stays reachable instead of being cut off by the rail's own bounds.」
  + Scenario `:897-901`「A long session list stays reachable」。
- **实现落点**：
  - `workbench.css:1617` `#ai-session-list { display: grid; gap: 2px; }` —— **没有 `overflow-y`**；
  - `workbench.css:681-690` `#ai-column { … overflow: hidden; … }` —— 祖先**裁切**；
  - `workbench.css:1604-1605` `#ai-session-list-view, #ai-chat-view { min-height: 0; }` —— 无滚动。
  ⇒ **实测：长会话列表被 `#ai-column` 的 `overflow:hidden` 静默裁掉**。
- **旁证**：`tasks.md:250`（25.1）原文即写「现状 `#ai-session-list`（`workbench.css:611`）
  无滚动容器（`overflow:visible` + 祖先 `overflow:hidden` ⇒ 被静默裁掉）」——
  **契约与实现一致地确认了缺陷**，且该组 **0/4 完成**。
- **建议改哪一边**：**改代码**（tasks 25.1 待办）；契约侧无需动。

### 1.2 `workbench-settings` delta（`specs/workbench-settings/spec.md`）

| # | Requirement | 落点 | 判定 |
|---|---|---|---|
| 1 | Workbench settings view（`:10-45`） | `pages.py:879-932`（`settings_page`）、`workbench.js:1328-1448`、`app.py:317`（路由） | ✅ |
| 2 | Appearance preferences are browser preferences stored per workspace（`:47-79`） | `workbench.js:288`（`SETTINGS_KEY = "wb_settings_" + WS`）、`sfx.js:32`（`SETTINGS_PREFIX = "wb_settings_"`） | ✅ |
| 3 | Theme preference switches the night paper value set（`:81-134`） | `workbench.js:350-366`、`workbench.css:253-318`、`pages.py:1447-1478`（首屏引导） | ✅ |
| 4 | Reading face preference selects the reading type family（`:136-158`） | `workbench.js:368-386` | ✅（死钩子见 INC-01） |
| 5 | Motion preference and system reduced motion（`:160-189`） | `workbench.js:387-419`、`workbench.css:3432-3451` | ✅ |
| 6 | Sound preference limits audio to key feedback（`:191-215`） | `sfx.js:22-144` | ✅ |
| 7 | Appearance preferences never change learning facts（`:217-240`） | 四项偏好**全部只写 `localStorage`**（`workbench.js:302-308`、`sfx.js:73`），**零 `api()` 调用** | ✅ |

**逐 Scenario 关键点复核**：
- 「Preferences are independent per workspace」✅ —— key 前缀含 `WS`；
- 「Preferences survive a restart」✅ —— `localStorage`；
- 「Nothing reaches the pool」✅ —— `saveSetting()` 只碰 `window.localStorage`，
  `grep -n "saveSetting" workbench.js` 的 6 个调用点（`:1314`/`:1324`/`:1406`/`:1419`/`:1427`/`:1435`）
  **无一个发请求**；
- 「The switch takes effect immediately」（声音）✅ —— `sfx.js:126-135` `setEnabled()` 立即改
  `readEnabled()` 读的值，无 reload。

**唯一不一致**：**INC-08**（见下）。

#### INC-08 —— 设置视图的**四个偏好控件命名与契约的「控制项承载自身名称 + 当前值」不完全对齐**（低优先）

- **条款位置**：`workbench-settings` delta `:23-25`
  「every preference is presented as a control that carries its own name and its current value,
  and prose that merely restates a control SHALL be omitted.」
- **实现落点**：`pages.py:892-928` —— 每一行是
  `<label class='preference-name'>主题</label>` + `<span class='preference-value'>暖纸</span>`
  + 控件（开关 / 分段控件）。
- **判定**：**基本一致，但有两处措辞偏差**（**不是违规，是命名不齐**）：
  1. 契约的名词是「**主题偏好 / 阅读字面 / 动效偏好 / 声音偏好**」
     （`GLOSSARY.md:382`/`:402`/`:409`/`:415`）；
     实现把设置项的**显示名**写成「**主题** / **阅读字面** / **动效** / **声音**」
     （`pages.py:894`/`:904`/`:913`/`:921`）—— 三个少了「偏好」二字。
  2. **契约只规定设置视图承载「theme, reading face, motion and sound」四类**，
     实现做到了 ✅；但左栏那个**自评开关**的显示名与契约不符（已记 INC-06）。
- **建议改哪一边**：**改代码或改 spec，二选一**（这属于「同名同义」的低优先分歧，
  不影响可观察行为；建议**保留现状**并在 spec 里把「偏好」二字省掉，
  因为设置视图里一行只可能是一种偏好，写「主题偏好」反而冗余）。

### 1.3 `calendar-workload` delta（`specs/calendar-workload/spec.md`）

| # | Requirement | 落点 | 判定 |
|---|---|---|---|
| 1 | Calendar and workload view（`:3-138`） | `workbench.js:5757-5960`（时间视图）、`workbench.css:2340-2470`、`:2511-2620` | ⚠️ **2 个 Scenario 不一致** |

**逐 Scenario 复核（14 个）**：

| Scenario | 落点 | 判定 |
|---|---|---|
| Overlapping goal periods | `workbench.js:5890-5895`（`--calendar-lanes` 平行道） | ✅ |
| Goals on one deadline | 同上 | ✅ |
| Existing deadline-only goal | `workbench.js` 渲染分支 | ✅ |
| Goal crossing a week boundary | `workbench.css:2386-2400`（`.calendar-goal`） | ✅ |
| Exact workload on a fixed axis | `workbench.js:5912-5934` | ✅ |
| Zero workload day | `workbench.js:5930`（`day.count ? … : ""`） | ✅ |
| Heavy day with reallocation prefill | `workbench.js:5921`/`:5931`/`:5967-5975` | ✅ |
| Nothing scheduled | `workbench.js:5948-5956` | ✅ |
| Bar height encodes the day's exact load | `workbench.js:5920`（`height = count/max*132`） | ✅ |
| A heavy day is identifiable without colour | `workbench.js:5931`（`.bar-heavy-flag` 圆点）+ `workbench.css:2461-2465` | ✅ |
| **Load change animates without changing the data** | — | ❌ **INC-09** |
| **Reduced motion lands on the same final state** | — | ❌ **INC-09** |
| Today is marked on the numeral | `workbench.css:2381-2384`（`.calendar-cell.today .calendar-day` 圆角药丸 + 黄底） | ✅ |
| The view stays read-only | `workbench.js:5757-5960` 全段零写操作 | ✅ |

#### INC-09 —— 14 天负荷柱**没有任何生长动画**（逐柱 24ms 错峰未实现）

- **条款位置**：`calendar-workload` delta `:48-57`
  「When the 14-day load is rendered or refreshed, the bars SHALL **grow from the shared
  baseline with a per-column stagger of 24 ms**, animating only transform and opacity,
  with each animation duration inside the workbench's interaction and scene duration bands.」
  + Scenario `:120-123`「Load change animates without changing the data」
  + Scenario `:125-128`「Reduced motion lands on the same final state」。
- **实现落点**：`workbench/server/static/workbench.js:5930`
  ```js
  + (day.count ? "<div class='bar-fill' style='height:" + height + "px'></div>" : "")
  ```
  ⇒ **柱高是行内 `height`，不是 `transform`** ⇒ **结构上无法做「只动 transform / opacity」的生长**。
- **证据（穷举）**：
  ```bash
  # CSS 里 .bar-* 家族的任何规则中含 animation 的 —— 输出为空
  python - <<'EOF'
  import re, pathlib
  css = pathlib.Path("workbench/server/static/workbench.css").read_text(encoding="utf-8")
  for m in re.finditer(r'[^{}]*\.bar[^{}]*\{[^}]*\}', css):
      if 'animation' in m.group(0): print(m.group(0))
  EOF
  # → 无输出
  grep -rn "24ms\|24 ms" workbench/server/static/*.css workbench/server/static/*.js  # → 无输出
  grep -rn "lk-stagger" workbench/server/static/*.js workbench/server/*.py           # → 无输出
  ```
  `workbench.css:3034-3043` 的 `.lk-stagger` 错峰类是**另一个组件**（40ms 档），
  **没有被负荷柱引用**（`grep -rn "lk-stagger" *.js *.py` 无命中）。
- **判定**：**不一致**。契约要求的两条（错峰生长 + 降级同终态）**都没有实现**；
  降级场景之所以「看起来对」，是因为**根本没有动画**（柱子直接就是终态）——
  **是实现缺失，不是降级正确**。
- **旁证**：`design-notes/motion-spec.md:267` 第 19 条「进度带 … **逐柱错峰 24ms** … 320ms」
  与 `:1253`「错峰 40ms（列表）/ **24ms（负荷柱）**」都把这条写成设计契约；
  `tasks.md:207`（20.1）标 `[x]` **已完成**，但**代码里查不到** ⇒
  **任务勾选与实现事实不符**（这是比契约不一致更严重的**流程问题**）。
- **建议改哪一边**：**改代码**（补 `@keyframes lk-bar-grow`（`scaleY 0→1`，
  `transform-origin: bottom`）+ `.bar-col:nth-child(n)` 的 24ms 递增 delay，
  并把行内 `height` 改成 `transform: scaleY()`）；
  同时**修正 `tasks.md` 20.1 的勾选状态**（它标了 `[x]` 但没实现）。
  ⚠️ 若决定「不做这个动画」，则应**改 spec delta** 把两条 Scenario 删掉。

### 1.4 本组小结：7 条真不一致

| ID | 类型 | 位置 | 建议改哪一边 |
|---|---|---|---|
| INC-01 | 实现冗余（死钩子 `data-face`）+ 首屏闪字族（低） | `workbench.js:380`、`pages.py:1474` | 改代码（补 CSS 消费或删钩子） |
| INC-02 | 契约可满足性 | `workbench-ui` delta `:220-222` | 改 spec delta（降级该条件） |
| INC-03 | 用户可见文案 | `pages.py:273`/`:286`/`:405` | 改代码（按 `copy-table.md`） |
| INC-04 | 整条未实现 | `workbench-ui` delta `:507-533` | 改代码（tasks 24 组待办） |
| INC-05 | 冗余通道不齐 | `paper-practice.js:575-602`、`workbench.css:3957-3980` | 改代码 |
| INC-06 | 用户可见文案 | `pages.py:993` | 改代码 |
| INC-07 | 整条未实现 | `workbench-ui` delta `:889-895` | 改代码（tasks 25.1 待办） |
| INC-08 | 命名不齐（低） | `pages.py:894`/`:904`/`:913`/`:921` | 改代码或改 spec（二选一，建议改 spec） |
| INC-09 | 动画整条未实现 + 任务勾选不实 | `calendar-workload` delta `:48-57`、`:120-128`；`workbench.js:5930` | 改代码 + 修正 `tasks.md` 20.1 勾选 |

---

## 2. `component-spec.md`（28 组件 × 8 态）→ 实现

**核对方法**：把 `component-spec.md` §4.1–§4.28 每节的 CSS 代码块里的类名逐个在
`workbench.css` + `agent-ui.css` 里 grep，再对**已存在的类**检查 8 态
（默认/hover/active/focus-visible/disabled/loading/selected/error）在 CSS 里是否有对应规则。

### 2.1 类名落点总表（28 组件）

| § | 组件 | spec 类名 | 产品类名（实测） | 判定 |
|---|---|---|---|---|
| 4.1 | 主按钮 | `.lk-btn` | `.primary` / `button.primary` | ❌ **类名不符** |
| 4.2 | 次按钮 | `.lk-btn--secondary` | `.outline` | ❌ |
| 4.3 | 文字按钮 | `.lk-btn--text` | `.ghost` | ❌ |
| 4.4 | 图标按钮 | `.lk-iconbtn` | `.icon-only` | ❌ |
| 4.5 | 输入框 | `.lk-input` | 原生 `<input>` + `workbench.css:906-960` | ❌ |
| 4.6 | 文本域 | `.lk-textarea` | 原生 `<textarea>` | ❌ |
| 4.7 | 自绘下拉 | `.lk-select*` | 原生 `<select>`（`workbench.css:826-836`） | ❌ **契约明确要求自绘** |
| 4.8 | 复选框 | `.lk-check*` | 原生 `<input type=checkbox>`（`.lk-switch` 是开关不是复选框） | ❌ |
| 4.9 | 单选 | `.lk-radio*` | 原生 `<input type=radio>` | ❌ |
| 4.10 | 开关 | `.lk-switch*` | **同名** ✅ | ⚠️ 状态缺 5 项 |
| 4.11 | 分段控件 | `.lk-seg*` | **同名** ✅ | ⚠️ 状态缺 4 项 + 2 变体缺 |
| 4.12 | 标签 | `.lk-tag*` | `.chip` / `.count-badge` | ❌ |
| 4.13 | 徽标 | `.lk-badge*` | `.count-badge` | ❌ |
| 4.14 | 状态圆点 | `.lk-dot*` | **同名** ✅ | ⚠️ 8 变体缺 8 个 |
| 4.15 | 进度条 | `.lk-progress*` | **同名** ✅ | ⚠️ 3 变体缺 |
| 4.16 | 分段进度条 | `.lk-steps*` | — | ❌ **产品里没有** |
| 4.17 | 题号格 | `.lk-qcell*` | `.paper-dot`（`workbench.css:3957-3980`） | ❌ |
| 4.18 | 卡片 | `.lk-card` | `.card` + `.lk-card`（**两者都在**） | ⚠️ 双轨 |
| 4.19 | 纸面层级 4 层 | `.lk-surface-0..3` | token `--surface-*`（无类名） | ❌ 类名未落地 |
| 4.20 | 沉底块 | `.lk-sunkenblock*` | token `--surface-sunken` + 各类各写一遍 | ❌ |
| 4.21 | 空态 | `.lk-empty*` | **同名** ✅ | ✅ |
| 4.22 | 骨架屏 | `.lk-skeleton*` | **同名** ✅ | ✅ |
| 4.23 | 吐司 | `.lk-toast*` | — | ❌ **产品里没有** |
| 4.24 | 对话框 | `.lk-dialog*` | — | ❌ **产品里没有** |
| 4.25 | 工具调用卡 | `.lk-tool*` | `.ai-plan` / `.ai-activity` | ❌ |
| 4.26 | 时间线节点 | `.lk-timeline*` | `.ai-plan-step`（点+线） | ⚠️ 改名落地 |
| 4.27 | 折叠段 | `.lk-disclosure*` | 原生 `<details>/<summary>` | ❌ |
| 4.28 | Tab | `.lk-tab*` | `.record-tab` | ❌ |

**统计**：**同名落地 6 个**（4.10/4.11/4.14/4.15/4.21/4.22），
**类名不符 18 个**，**产品里根本没有 3 个**（4.16/4.23/4.24），
**双轨 1 个**（4.18）。

### 2.2 8 态覆盖（只对同名落地的 6 个做逐态核）

| 组件 | 已实现态 | 缺失态 | 证据 |
|---|---|---|---|
| §4.10 开关 | 默认 / focus-visible / selected(on) | **hover / active / disabled / loading / error** | `workbench.css:1286-1327`：只有 `input:checked + .lk-switch__track`、`input:focus-visible + .lk-switch__track` 两条状态规则；`grep -n "lk-switch:hover\|lk-switch:active\|lk-switch.*disabled" workbench.css` → 无输出 |
| §4.11 分段控件 | 默认 / hover / focus-visible / selected | **active / disabled / loading / error** | `workbench.css:1328-1381`：有 `:hover`、`:has(input:checked)`、`:has(input:focus-visible)`；`grep -n "lk-seg.*disabled\|lk-seg.*aria-invalid" workbench.css` → 无输出 |
| §4.14 状态圆点 | 默认 + 6 变体 | 缺 **8 变体**：`--blue` `--half` `--muted` `--sm` `--lg` `--on-paper` `--on-ink` | `grep -o "lk-dot--[a-z-]*" workbench.css \| sort -u` → 仅 `check/cross/dash/filled/ink/red/yellow` |
| §4.15 进度条 | 默认 + fill | 缺 `--yellow` `--error` `--indeterminate` | `workbench.css:3210-3250` 只有 `.lk-progress` / `.lk-progress__fill` / `.is-filled` |
| §4.18 卡片 | 默认 | hover / active / focus / disabled / loading / selected / error | `.lk-card` 只定义形态，不定义交互态（可接受，卡片本非交互控件） |
| §4.21 空态 | 三段结构 ✅ | — | `pages.py:100-105` + `workbench.css:1498-1531` |
| §4.22 骨架屏 | 默认 + 扫光 ✅ | — | `workbench.css:3046-3058` |

### 2.3 结论与建议

- **INC-10（类名体系未落地）**：`component-spec.md` 是**设计权威**（其自述 §8「§4 仍然是组件形态的
  唯一设计权威」），但 28 个组件里只有 **6 个**用了 `lk-` 名。
  ⇒ **建议改 spec delta / component-spec**，而不是改代码去重命名 3000+ 处引用点：
  把 `component-spec.md` 的「实现名」列**改成产品实际类名**（或明确标注「设计名 ↔ 实现名」对照），
  否则每次走查都要重新对一遍。
  ⚠️ 本变更**已有**一份实测对齐表 `component-inventory.md`（2026-10-22），
  其 §1 总览给出的结论是「✅ 13 / ⚠️ 12 / ❌ 3」——
  **与本报告的分类口径不同**（它按「有没有独立形态」判，本报告按「类名是否一致」判），
  **两份表不冲突但口径不同**，建议在文档里点明这一点。
- **INC-11（§4.10 / §4.11 的状态缺失 + 取值偏差）**：
  - **状态缺失**：开关缺 **hover / active / disabled**（spec §4.10 的 `loading` 与 `error`
    两行本来就写「不适用」⇒ 那两态**不构成不一致**）；分段控件缺 **active / disabled / error**
    （`loading` 写「不适用」）。
    **穷举证据**（列出 `workbench.css` 里全部含 `lk-switch` / `lk-seg` 的规则）：
    ```
    .lk-switch                    .lk-switch input
    .lk-switch__track             .lk-switch__thumb
    .lk-switch input:checked + .lk-switch__track
    .lk-switch input:checked + .lk-switch__track .lk-switch__thumb
    .lk-switch input:focus-visible + .lk-switch__track
    .lk-seg                       .lk-seg__item
    .lk-seg__item input           .lk-seg__item:hover
    .lk-seg__item:has(input:checked)
    .lk-seg__item:has(input:focus-visible)
    .lk-seg__item:has(input:checked):has(input:focus-visible)
    ```
    ⇒ **没有一条 `:active` / `:disabled` / `[aria-invalid]`**。
  - **取值偏差（§4.11 分段控件）**：spec §4.11 写「容器 `--surface-base`」、
    「selected 项 `background: var(--surface-raised)` + `color: var(--ink-strong)`」；
    实现是「容器 `--surface-sunken` + `inset 0 0 0 1px var(--rule-hair)`」
    （`workbench.css:1328-1336`）、「selected 项 `background: var(--role-blue)` +
    `color: var(--ink-on-role)`」（`:1364-1369`）。
    ⚠️ **但 `docs/GLOSSARY.md` 的新词条「分段控件 / Segmented control」
    （并发提交 `187a3bd2` 引入）写的正是实现的写法**
    （「容器是一道**沉底槽**（`--surface-sunken` + 1px 内发丝线…）」、
    「**选中项 = 一块学习蓝色块 + 纸白文字**」）⇒
    **是 `component-spec.md` 落后于 GLOSSARY 与实现**，不是实现违反 GLOSSARY。
    ⇒ **建议改 `component-spec.md`**（把 §4.11 的容器与 selected 取值改成 GLOSSARY 的口径），
    同时补 3–4 条状态规则。
  - **§4.10 开关滑块位移**：spec §4.10 正文写「滑块 `translateX(4px → 20px)`」，
    而**同一节的 CSS 块**写 `translateX(0)` → `translateX(18px)`；
    实现取的是后者（`workbench.css:1317`/`:1321`）⇒
    **spec 自身前后不一致**，实现与 CSS 块一致 ⇒ 建议改 spec 正文。
- **INC-12（§4.7 自绘下拉未落地）**：`component-spec.md` §4.7 要求 `<select>` → 自绘下拉，
  产品里**仍是原生 `<select>`**（`workbench.css:826-836` 的 `select { … }` 规则）。
  但本变更的 `workbench-ui` delta **没有**任何 Requirement 要求自绘下拉
  ⇒ **这是设计件与 spec 之间的缺口**（不是实现违反 spec）。
  ⇒ 建议**改 spec delta 或明确记为「后续 change」**。
- **INC-13（§4.14 圆点变体缺 8 个）**：与 INC-05 相关（几何语言不够用）。
  `component-inventory.md:84` 已记同一事实（「⚠️ 缺 8 个变体」）。

---

## 3. `design.md` D-1…D-15 → 实现

> **核对说明**：任务书写「D-1…D-16」，但 `design.md` **实际只有 D-1…D-15**
> （`design.md:1363-1364` 自检写「D-1 … D-15 每条都有…**全部 15 条齐备，无缺项**」）。
> `HANDOFF.md:99` 与 `IMPLEMENTATION-LOG.md:39` 写的「D-1…D-16」是**文档笔误**。
> ⇒ **INC-14（文档笔误，低）**：建议把 `HANDOFF.md` / `IMPLEMENTATION-LOG.md` 的
> 「D-1…D-16」改成「D-1…D-15」。

| 决策 | 关键冻结项 / 允许清单 / 禁止项 | 实现落点 | 判定 |
|---|---|---|---|
| **D-1** token 架构 | 结构 token 一套 + 值 token 两套；旧 token 走别名期退役；图谱裸名零同名 | `workbench.css:43-244`（`:root`）、`:253-318`（夜纸）；图谱裸名在 `:3574-3590` 独立块 | ✅ 值 token 53/53 全对（§4）；旧名 `--dsw-*` 只剩 `--dsw-state-success` 一个（`workbench.css:244`，注释 `:236-243` 已登记为「契约外遗留」） |
| **D-2** 纸面层级 4 层 | 底/卡/浮起/沉底；12px 圆角；不用描边；沉底无柔影、内发丝线 | `workbench.css:134-139`（四 token）、`:977-1010`（沉底规则块） | ✅ 沉底带 `inset 0 0 0 1px var(--rule-hair)` 且无 `--elev-*`（`:1000-1005`） |
| **D-3** 色彩收编 | 三角色 + 墨阶 + 表面阶；**绿整体移除**；答对 = 中性墨 + 勾形 | `workbench.css:163-174`（三角色 11 token） | ⚠️ **INC-15：绿仍在** |
| **D-4** 双字族分工 | 阅读面衬线 + 界面无衬线 + 等宽第三族 | `workbench.css:79-86`、`:460`/`:2788`/`:2846`/`:2872`/`:3156` | ✅ |
| **D-5** 阅读版式规格 | 17 / 1.75 / 38em；`.wb-reading` 自成一层 | `workbench.css:2840-2862`（`--fs-reading` / `line-height:1.75` / `--measure`） | ✅ |
| **D-6** Markdown 双渲染器 | 统一到服务端语义；pytest 锁住两侧一致 | `tests/test_markdown_render_parity.py` + `tests/workbench/renderer_parity_cases.js` | ✅ 逐字符比对（测试注释 `:12-16`） |
| **D-7** 动效系统 | CSS 为主、JS 辅；五档时长 + 三档缓动 + 白/黑名单；只动 transform/opacity | `workbench.css:96-111`（5+8 token）、`:2889-3020`（20 条 keyframes） | ⚠️ **INC-16：负荷柱不在其中**（= INC-09） |
| **D-8** 动效偏好与 reduced-motion | 未设置才跟随系统，显式优先 | `workbench.js:394-409`（`motionMode()` 三档）、`workbench.css:3432-3451` | ✅ 四种组合都成立 |
| **D-9** 设置视图形态与主题应用时机 | 中栏视图；左栏开关开合；偏好按工作区存浏览器 | `pages.py:879-932`、`workbench.js:1328-1448`、`workbench.css:1385-1400` | ✅ |
| **D-10** 三栏几何单一真值 | CSS 持模板；JS 只写**两个列宽变量**；不改拖拽语义 | `workbench.css:656-665`（`--wb-col-left` → `--shell-col-left` 转发）、`workbench.js:5709-5720` | ⚠️ **INC-17：变量名多了一层** |
| **D-11** 128px 死预留退役 | 删 `padding-right:128px` 与 `.scope-tray-*`；标题带改 2px 结构线；中栏 880px | `grep -n "padding-right: 128px\|scope-tray" workbench.css` → **无输出** ✅；`workbench.css:698-710`（`--shell-measure: 880px`） | ✅ |
| **D-12** 焦点可见性与对比度 | 焦点环只在 `:focus:not(:focus-visible)` 时让位 | `workbench.css:2213-2216`（全局 `:focus-visible`）、`:838`/`:967`/`:1323`/`:1371`/`:1915` | ✅ |
| **D-13** 记录中心卡片流 | 圆角卡片流（不是表格）；六项字段一个不少 | `records.py:98-113`（`<article class='record-row card'>`，六字段齐）、`workbench.css:2704` | ✅ |
| **D-14** 作答日历 | 7 行 × 12 列、格 ~13px、填色 **且** 高度双编码；5 档阈值显式化 + 图例 | `workbench.css:2520-2530`（`repeat(12, minmax(13px,1fr))` × `repeat(7,30px)`）、`:2546-2576`（`.level-0..4` + fill/height）、`records.py:16-29`（`_CALENDAR_LEVELS`）+ `:529-549`（图例） | ✅ |
| **D-15** 契约漂移登记 | 登记在 `openspec/changes/` 下的独立登记文件，不进 `docs/` | `contract-drift.md` 存在（174 条）；`docs/` 下无同名文件 ✅ | ✅ |

#### INC-15 —— D-3 要求的「绿整体移除」**未完成**（权威表无绿档，但产品里还有绿）

- **条款位置**：`design.md` **D-3**（`:266-...`）与 `night-paper-tokens.md` §3.4
  （三角色 = 蓝 / 黄 / 红，**不加第四色相**）；
  `decisions.md` **A-20-3**：「『答对』不再用绿，本轮整体移除」。
- **实现落点**：
  - `workbench/server/static/workbench.css:244` — `--dsw-state-success: #22c55e;`（**绿色**）
  - `workbench/server/static/workbench.css:2124` — `.status-dot.ok { background: var(--dsw-state-success); }`
- **判定**：**不一致（轻微）**。产品里**还有一处绿**（`#22c55e`）。
  实现侧**自己标注了**（`workbench.css:236-243`：「契约外遗留：DSH 的 success 态…
  **本条按 4.4「本条不动它」保留原名原值**… ⇒ **全站唯一的旧名残留**」），
  且 `contract-drift.md` 已把它登记为「契约外的局部例外」。
- **补充事实（实测）**：`grep -rn "status-dot" workbench/server/pages.py workbench/server/records.py
  workbench/server/static/*.js` → **零命中** ⇒ `.status-dot` 这条 CSS 规则**在产品里已经没人用**
  （知识点三态走 `pages.py:17-19` 的 `.lk-dot`）。⇒ **这是一条死规则 + 一个死 token**。
- **建议改哪一边**：**改代码**（删 `workbench.css:2123-2126` 的 `.status-dot` 一族
  + `:244` 的 `--dsw-state-success`），**零用户可见变化**（已无引用点）。
  这是「三角色配额」这条契约最干净的一次收口。

#### INC-16 —— D-7 的「五档时长 + 白名单」对**负荷柱**这一族未兑现（= INC-09 的设计侧腿）

见 §1.3 INC-09。此处补设计侧证据：`motion-spec.md:267` 第 19 条把「负荷柱逐柱错峰 24ms」
写成 motion 规格，`:1253` 复述 ⇒ **D-7 声明覆盖的「数据层」这一族里，负荷柱这一格是空的**。

#### INC-17 —— D-10 要求的「JS 只写两个列宽变量」实际**多了一层转发变量**

- **条款位置**：`design.md` **D-10**（`:866-...`）：
  「**JS 只写两个数值变量**：`workbench.js:4587` … 改为
  `layout.style.setProperty("--shell-col-left", …)` / `setProperty("--shell-col-right", …)`」
- **实现落点**：
  - `workbench.js:5719-5720` — `layout.style.setProperty("--wb-col-left", leftWidth + "px");`
    `layout.style.setProperty("--wb-col-right", rightWidth + "px");`
  - `workbench.css:656-657` — `--wb-col-left: var(--shell-col-left, 280px);`
    `--wb-col-right: var(--shell-col-right, 420px);`
  - `workbench.js:5674-5675`（注释）— 「The stylesheet owns the grid template (`#layout` reads
    --wb-col-left and --wb-col-right, which forward to the authoritative --shell-col-* pair)」
- **判定**：**功能等价，但与 D-10 的字面写法不同**。
  D-10 说的是 JS 直接写 `--shell-col-*`；实现让 JS 写 `--wb-col-*`，再由 CSS 转发到 `--shell-col-*`。
  **单一真值的意图达成了**（模板形状只在 CSS 一处、具体宽度只在 JS 一处、权威 token 名仍是
  `--shell-col-*`），但**多了一层转发** ⇒ 「权威 token 名被 JS 直接写」这条被绕开了。
- **建议改哪一边**：**改代码**（JS 直接写 `--shell-col-left/right`，删 CSS 的转发层），
  **或改 `design.md` D-10**（把决策改成「JS 写 `--wb-col-*`，CSS 转发到 `--shell-col-*`」）。
  后者成本低得多，且不触碰代码。**建议改 design.md**。

---

## 4. 权威表 `night-paper-tokens.md` ↔ 实现

### 4.1 定义集合 vs 引用集合（求差）

**方法**：
```python
# 定义集合：CSS 里 `--name:` 形式的声明（workbench.css + agent-ui.css + preview.html + pages.py）
# 引用集合：CSS 里 var(--name) 形式的引用
```

| 集合差 | 结果 | 判定 |
|---|---|---|
| **被引用但未定义** | `--agent-split-width`（`agent-ui.css:272` 定义了，`:258`/`:266` 引用 ⇒ **实为已定义**，脚本误判） | ✅ 实际无缺 |
| 同上 | `--kind-color` / `--state-color` / `--metric-angle` / `--size` | ✅ **图谱区段专用**（`workbench.css:3720-3776`），由 `graph-renderer.js` 行内注入，不属本变更 token 层 |
| 同上 | `--ripple-base` | ✅ **有意不定义**（`workbench.css:3312`：「一旦定义就会遮蔽 JS 的 inline 写入」） |
| 同上 | `--asset-` / `--size` | ✅ 模板串（`var(--asset-xxx, #回退值)` 写法），非真 token |
| **定义但未被本表收录** | `--asset-*` 共 **14** 个 | ✅ **归 `asset-spec.md` §1.7**（`:217-234`）管，不属本表 ⇒ **不是漂移**（但权威表 §0 摘要表没提这一层，**建议补一行**） |
| 同上 | `--graph-page-caption` / `--graph-page-dimmed` | ✅ **并发提交 `187a3bd2` 已补进本表 §3.3 附表**（A-83）⇒ 已收口 |
| 同上 | `--dot-fill` / `--dot-mark` | ⚠️ **INC-18（低）**：`.lk-dot` 的组件内局部变量，未在本表登记 |
| 同上 | `--streak-accent` / `--verdict-line` / `--level-bg` / `--track-color` / `--calendar-lanes` / `--wb-col-left` / `--wb-col-right` | ⚠️ **INC-18（低）**：8 个组件/布局局部变量未登记 |
| 同上 | `--dsw-state-success` | ⚠️ **INC-15**：契约外绿（权威表无此名） |
| 同上 | `--asset-lamp-warm` | ⚠️ **INC-19（低）**：`asset-spec.md:234` 自己也写「权威表无对应 token → 待裁决」 |
| **本表定义但实现里没有** | `--surface-graph-sheet`（A-16 已退役）· `--surface-ink`（A-30 已更名 `--surface-code`）· `--lk-radius-full`（A-18 已并入 `--r-pill`）· `--fs-h1`（表内明写「本表不定义 `--fs-h1`」）· `--mk-h2/--mk-h3`（表内明写「任何设计件不得另立局部标题字号变量」） | ✅ **全部是「已退役 / 明写不定义」**，非漂移 |

### 4.2 值 token 亮/夜配对（53 个）

**方法**：把本表 §3 每行的「浅色 / 夜纸」两列与 `workbench.css` 的 `:root` / `html[data-theme="night"]`
两个块逐 token 比对（去空白、小写）。

**结果**：
```
parsed value tokens: 55   （53 值 token + 2 图谱作用域专用）
value token mismatches: 1 of 55
  DIFF night: --veil-hover spec 'rgb(255 244 224 / 6%)`（夜纸用**亮面纱**…）' impl 'rgb(255 244 224 / 6%)'
```
⇒ **唯一那条是解析假阳性**（本表该格的说明文字被并进了取值列），
**取值本身逐字符相同**。

**结论**：**53/53 值 token 亮/夜两套全部成对且取值完全一致** ✅
（结构 token 66 个两主题同值 ⇒ 实测 `:root` 里比 `night` 块多的**全部**是结构 token
与 `--asset-*` 派生层，**无一条值 token 漏夜纸**）。

**唯一可查的例外**：`--focus-width` / `--focus-offset` 亮夜**同值**（2px / 2px）——
这是本表 §3.7 **明写**的取值（两主题同值），**不是漂移** ✅。

### 4.3 本组结论

- **INC-18（低）**：8 个组件内局部变量（`--dot-fill` `--dot-mark` `--streak-accent`
  `--verdict-line` `--level-bg` `--track-color` `--calendar-lanes` `--wb-col-left/right`）
  **未在本表登记**。它们**都不是**主题相关（两主题同值），所以不破坏「两套值集」的纪律，
  但按 D-1「唯一权威表」的纪律，**要么登记、要么明确声明「组件内局部变量不受本表管辖」**。
  ⇒ **建议改本表**（加一节「组件内局部变量」），成本低。
- **INC-19（低）**：`--asset-lamp-warm` 无权威 token（`asset-spec.md:234` 自认「待裁决」）。
  ⇒ **建议裁决**：要么在 `night-paper-tokens.md` 补一个 token，要么把它降级成 SVG 内部常量。

---

## 5. `GLOSSARY` / `PRODUCT-MANUAL` 名词 ↔ 实现（同名同义）

### 5.1 13 条视觉名词的落点核对

| 名词（GLOSSARY） | 实现落点 | 同名同义？ |
|---|---|---|
| 柔和蒙德里安 v2 / Soft Mondrian v2（`:328`） | 整体视觉语言（token 层） | ✅ 概念层，无实现锚点 |
| 纸面层级 / Paper level（`:351`） | `--surface-base/card/raised/sunken` + `--surface-code` | ✅ |
| 沉底面 / Sunken surface（`:359`） | `--surface-sunken` | ✅ |
| 夜纸 / Night paper（`:368`） | `html[data-theme="night"]`；设置视图显示名「夜纸」（`pages.py:895`） | ✅ |
| 冗余状态通道 / Redundant state channel（`:375`） | `.lk-dot--cross/--dash/--check`（`workbench.css:1199-1235`）、`.record-verdict-*::before/::after` | ⚠️ **语义成立，但 Paper 状态点侧缺几何 → INC-05** |
| 主题偏好 / Theme preference（`:382`） | `localStorage` key `wb_settings_<WS>` 的 `theme` 字段 | ✅ |
| 阅读面 / Reading surface（`:388`） | `.wb-reading` + 4 个兄弟类 | ✅ |
| 阅读字面 / Reading face（`:402`） | `readingFace` 字段 + `--font-read` 覆盖 | ✅ |
| 动效偏好 / Motion preference（`:409`） | `motion` 字段 + `data-motion` | ✅ |
| 声音偏好 / Sound preference（`:415`） | `sound` 字段 + `sfx.js` | ✅ |
| 工作台设置视图 / Workbench settings view（`:422`） | `pages.settings_page()` + `/w/<WS>/settings` | ✅ |
| 静物插画 / Still-life illustration（`:430`） | `.lk-empty__art` + `assets/empty/*.svg` | ✅ |
| 骨架屏 / Skeleton loading state（`:437`） | `.lk-skeleton` + `lk-skeleton-sweep` | ✅ |
| 台灯转场 / Lamp transition（`:445`） | `runLampTransition()` + `.lk-lamp`/`.lk-ripple`/`.lk-ripple-glow` | ✅ |
| 少字原则 / Minimal-annotation principle（`:452`） | 设置视图 `.settings-view`（`workbench.css:1398`：「不加标题、不加说明句」） | ✅ |
| 图案适配原则 / Contextual-graphic principle（`:459`） | `.nav-item .asset-icon`（`workbench.css:808-813`：`border-radius: var(--r-round)`） | ✅ |

### 5.2 发现

#### INC-20 —— 实现里把「**静物插画**」叫作 `asset-empty`，而词表说它是「空态用的具象器物插画」

- **名词位置**：`docs/GLOSSARY.md:430-435`「静物插画 / Still-life illustration」——
  「空态用的**具象器物**插画（花瓶、果篮、画布、杯子、书本、台灯、钢笔…）」。
- **实现落点**：`workbench/server/static/workbench.css:1510-1522`
  `.lk-empty__art { display: block; width: 180px; … }` +
  `pages.py:92-104`（`_empty_state()` 读 `assets/empty/*.svg`）。
- **判定**：**一致**（`assets/empty/` 是**目录名**，不是**给学习者看的词**，
  且 `.lk-empty__art` 用的就是静物资产）⇒ **不是不一致**。
  ⚠️ 但要注意：**词表说静物插画是「器物」**（花瓶 / 果篮 / 杯子），
  而**目录名叫 `empty`**、实现里叫 `.lk-empty__art` ⇒
  **资产目录的语义是「空态插画」，词表的语义是「静物插画」** ⇒
  **建议**：要么把资产目录改名为 `assets/still-life/`（牵动多处），
  要么在 `GLOSSARY.md` 的「静物插画」条里**补一句「实现目录名 `assets/empty/`」**
  （成本极低，**建议改 docs**）。
- **另注**：`GLOSSARY.md:437` 的「骨架屏」条目与 `.lk-skeleton` **同名同义** ✅；
  `GLOSSARY.md:388` 的「阅读面」条目**已经**记了实现名 `.wb-reading` ✅
  —— **说明词表在本轮已养成「词条 + 实现名」的写法**，静物插画条只是漏了一处。

#### INC-21 —— `PRODUCT-MANUAL.md` 与产品**已同步**，但与 `workbench-ui` delta **不同步**（3 处）

- **位置**：`docs/PRODUCT-MANUAL.md` 的 §10 外观与主题（`:569-...`）、
  §6.11 连对与断裂（`:292`）、§6.12 交卷庆祝的两档（`:308`）、§7.1（`:325`）。
- **核对结果**（**手册与实现一致**）：
  - 「主题偏好…默认跟随系统」✅ 与 `workbench.js:355-359` 一致；
  - 「阅读字面…默认衬线…正文 17px、行高 1.75、行宽 38em 不随它变化」✅ 与 `workbench.css:2840-2862` 一致；
  - 「声音偏好…默认开…四个时刻各有一条不到 200ms 的短音效」✅ 与 `sfx.js:22-27`（0.140/0.140/0.185/0.190 秒）一致；
  - 「按工作区分别保存，跨标签页与重启保留」✅ 与 `workbench.js:288` 一致；
  - 「台灯转场…约 700ms」✅ 与 `workbench.js:692-693`（590 + 700）一致；
  - 「换工作区要重设外观」✅ 与 key 前缀含 WS 一致。
- **但与 spec delta 有 3 处措辞不同步**：
  | 手册写法 | spec delta 写法 | 性质 |
  |---|---|---|
  | 「左栏『练习与组卷显示自评』」 | delta `:817-820` 同样是「练习与组卷显示自评」 | ✅ 一致（**产品**错，见 INC-06） |
  | §7.1 标题「『练习显示自评』开启时的四项更新」 | delta 用「练习与组卷显示自评」 | ⚠️ **手册自己内部就不一致**（§7.1 用短名、§10 用长名） |
  | §10「切换设置视图时右栏的 Agent 对话**不重建**——对话、滚动位置和没发出去的草稿都留在原处」 | delta `:18-21`「the Agent column and the conversation inside it **mounted as the same instance**… no lost scroll position or draft input」 | ✅ 措辞不同、语义相同 |
- **建议改哪一边**：**改 docs**（`PRODUCT-MANUAL.md:325` 的 §7.1 标题与 §10 的长名对齐），
  或反过来把 §10 改成短名 —— **属于低优先的措辞统一**，不影响行为。

### 5.3 名词层面**没有发现**的（明确记录，避免误判）

- 实现**没有另起一套叫法**：`.lk-dot` / `.lk-switch` / `.lk-seg` / `.lk-progress` /
  `.lk-skeleton` / `.lk-empty` / `.lk-celebrate-*` / `.lk-streak` / `.lk-flames` /
  `.lk-combo-banner` 这些实现类名，**与词表的「冗余状态通道 / 开关 / 分段控件 /
  进度带 / 骨架屏 / 静物插画 / 台灯转场 / 连对计数器」在语义上一一对应**，
  **没有出现「同一个东西两个名字」的情况**。
- 「连对」这个词：手册 §6.11 用「连对与断裂」，实现用 `.lk-streak` / `.lk-combo-banner`，
  `workbench.js:611` 的 aria-label 是「连对 N」⇒ **同名同义** ✅。
- 「静物插画」的唯一分歧是**目录名**（见 INC-20），不是**给学习者看的词**。

---

## 6. 可能因并发改动而**过期**的结论

**审计窗口**：`51791b1d` → `54653388`（12 个并发提交）+ 未提交工作区改动。

### 6.1 已被并发改动**修正**的（写报告时已按新状态复核）

| 项 | 变化 |
|---|---|
| 值 token 计数 52 → 53 | 并发提交 `187a3bd2` 修正了 `night-paper-tokens.md` §3.11 的合计式（3 → 4）并补了 A-83 的两个图谱 token。**本报告 §4 的 53/53 结论是按修正后的表写的** ✅ |
| `--graph-page-caption/dimmed` 被判为「本表未收录」 | 同上提交已补进 §3.3 附表 ⇒ **已收口**，本报告已改判为 ✅ |
| `.rich-text` 死 CSS | 并发提交 `e137d608` / `8bd0edcd` 记「已彻底退役」；实测 `grep -c "rich-text" workbench.css` = **3**（全是说明性注释，选择器命中 0）✅ 与文档一致 |
| `workbench-ui` delta 的 Requirement 数 24 → 25 | 并发提交 `b0e48f31` 新增 ADDED 第 16 条「Knowledge-point list grouped by chapter」+ 3 处条款补写（进度带 / 焦点环 / 空态沉底面）。**本报告 §1.1 已按 25 条重算**，新增那条**核对结果 ✅**（`pages.py:625-627` + `workbench.css:1093-1135` + `workbench.js:199-232`） |
| `GLOSSARY.md` 补 6 个词条（焦点环 / 分组卡片 / 开关 / 分段控件 / 图标按钮 / 进度带） | 并发提交 `187a3bd2`。**本报告 §5 已按新词表复核**，这些新词条与实现的落点**一致** ✅ |

### 6.2 可能因**并发改动**而过期的结论（已逐条复核）

审计窗口内**产品代码只有两个文件变动**（`git diff --stat 51791b1d 82e4c962 -- workbench/server/static/ workbench/server/`）：
```
workbench/server/static/paper-practice.js | 55 ++++++++++++++++++-------------
workbench/server/static/practice-flow.js  | 53 ++++++++++++++++-------------
```
两者的 diff **只碰「答对回弹的落点」**（`squashVerdict` → `squashCorrectOption`，
`paper-practice.js` 的 hunk 落在 `:753-790` 与 `:1116-1130`）。

⇒ **本报告涉及这两个 JS 的结论复核结果**：
- **INC-05**（Paper 状态点几何）：`paper-practice.js` 的 `itemStatus()` / `statusLabel()` /
  `renderDots()` 在 `575-621` 行 —— **diff 未触及这三处** ⇒ **结论仍有效**；
- **「答对回弹落点」**：并发改动把回弹从「判定元素 `.micro-verdict.ok`」改到
  「**被选中的那一项**」（`squashCorrectOption`）——
  ⚠️ 这与 `workbench-ui` delta `:180-184`「the confirmed element gives a squash-and-stretch
  rebound」的「confirmed element」**指代不明**有关（判定元素 vs 被选项），
  **本报告不判它为不一致**（条款未定义清楚），但**主会话裁决时须知**：并发 agent 已按
  `decisions.md` **A-89**（`motion-spec.md §3.1`）改成「被选中的那一项」，
  **A-89 的口径与 spec delta 的措辞尚未对齐** ⇒ 记为 **Q14**（待裁决）。
- **§3 INC-16 / §1.3 INC-09**（负荷柱无动画）：两个 JS 都**没碰**负荷柱渲染
  （`workbench.js:5899-5945`，该文件本轮**一行未动**）⇒ **结论仍有效**。

### 6.3 本报告**不受**并发影响的结论

审计窗口内**产品代码只有 `paper-practice.js` 与 `practice-flow.js` 两个文件变动**
（见 §6.2 的 `git diff --stat` 输出）⇒ 以下结论**全部基于未变动的文件**，不受并发影响：

- §4 的 53/53 值 token 全对（依据 `workbench.css`，**整轮未改**）；
- §2 的类名落点表与 8 态覆盖（依据 `workbench.css` + `agent-ui.css`，**整轮未改**）；
- §3 的全部 15 条决策核对（依据 `workbench.css` + `workbench.js`，
  两个文件**整轮未改**）；
- §1 的 INC-01 / INC-03 / INC-04 / INC-06 / INC-07 / INC-08 / INC-09
  （依据 `workbench.css` / `workbench.js` / `pages.py`，**整轮未改**）；
- §1 的 INC-05（依据 `paper-practice.js:575-621` + `workbench.css:3957-3980`，
  前者**diff 未触及**）；
- §5 的全部名词核对（依据 `workbench.css` / `pages.py` / `docs/`，**整轮未改**）。

### 6.4 审计窗口内**新出现**、本报告**未覆盖**的并发产物

并发提交 `bb32c148` + `82e4c962` 落了
`openspec/changes/workbench-visual-language-v2/night-sweep-report.md`、
`acceptance-manual-review.md`、`acceptance-shots/`、`night-sweep-shots/`
（夜纸巡检与验收人工判读材料）。
⇒ **它们与本报告是同一变更下的两份并行只读产物**，**存在结论重叠的可能**
（如都判了对比度 / 焦点环 / 夜纸值集）⇒
**主会话合并两份报告时，请以本报告的「条款 → 实现落点 → 证据」三段式为索引，
对重叠项取并集，不要因为两份都写了就只留一份**。

---

## 7. 验证（本轮实跑，输出原样）

```bash
$ python -m pytest tests -q
1181 passed in 294.12s (0:04:54)

$ python -m compileall -q lessonkit.py workbench pipeline pool tests
（无输出 = OK）

$ openspec validate --specs --strict
✓ spec/agent-assisted-practice-records
✓ spec/agent-context
✓ spec/agent-contract-disclosure
✓ spec/agent-learning-evidence
✓ spec/ai-teacher-bridge
✓ spec/calendar-workload
✓ spec/daily-learning-plan
✓ spec/flash-card
✓ spec/knowledge-figures
✓ spec/mastery-evaluation
✓ spec/micro-quiz-content
✓ spec/practice-experience
✓ spec/practice-review
✓ spec/practice-set-export
✓ spec/problem-difficulty
✓ spec/retrieval-evaluation
✓ spec/review-workbench
✓ spec/workbench-content-governance
✓ spec/workbench-ui
Totals: 19 passed, 0 failed (19 items)

$ python lessonkit.py guard extract-problems --course dmath --chapter ch06
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS
All required artifacts exist and check files contain no blocking markers.

$ openspec validate workbench-visual-language-v2 --strict
Change 'workbench-visual-language-v2' is valid
```

**注**：`openspec validate --specs --strict` 校验的是 `openspec/specs/` 下的**现有能力本体**，
**不含**本变更的三份 delta；delta 的合法性由最后一条命令校验（**通过**）。

---

## 8. 待裁决清单（给主会话）

| # | 裁决问题 | 建议 | 影响面 |
|---|---|---|---|
| Q1 | **INC-09** 负荷柱动画：补实现，还是删 spec 两条 Scenario？ | **补实现**（motion-spec 已写死 24ms 档），并**修正 `tasks.md` 20.1 的 `[x]` 勾选** | `calendar-workload` delta / `workbench.css` / `tasks.md` |
| Q2 | **INC-02** 里程碑第二条件「章节首次完成」：降级条款，还是给 `practice_runs` 加章列？ | **先降级条款**（A-29 禁代理指标）；加列是 schema 变更，**必须单开 change + 同步 `docs/DATA_MODEL.md`** | `workbench-ui` delta / `docs/DATA_MODEL.md` |
| Q3 | **INC-04** 工作区卡片信息层级：补实现（tasks 24 组），还是从 delta 移出？ | **补实现**（契约已写死，tasks 也排好了） | `pages.py` / `workbench.css` / `tasks.md` |
| Q4 | **INC-05** Paper 状态点几何：补几何（复用 `.lk-dot--cross/--dash`），还是放宽契约？ | **补几何**（契约 + `GLOSSARY` 的「冗余通道不是文字」双向约束） | `paper-practice.js` / `workbench.css` |
| Q5 | **INC-07** Agent 会话列表滚动容器：补，还是降级契约？ | **补**（tasks 25.1 已明写缺陷与修法） | `workbench.css` |
| Q6 | **INC-03 / INC-06** 文案：按 `copy-table.md` 落地 3 处译文 + 补「与组卷」三字？ | **补**（`copy-table.md` 已定案，手册已按新文案写） | `pages.py` |
| Q7 | **INC-15** 契约外的绿 `--dsw-state-success` + `.status-dot` 死规则：删掉？ | **删**（实测零引用点，零用户可见变化） | `workbench.css` |
| Q8 | **INC-12** 自绘下拉（§4.7）：补 spec 条款，还是明确记为「后续 change」？ | **记为后续 change**（`workbench-ui` delta 从未承诺自绘下拉） | `component-spec.md` / 新 change |
| Q9 | **INC-10** 组件类名：把 `component-spec.md` 的实现名改成产品实际类名，还是把产品改成 spec 名？ | **改 spec（成本低、不动 3000+ 引用点）**；同时点明与 `component-inventory.md` 的口径差 | `component-spec.md` |
| Q10 | **INC-17** D-10 的 JS 变量名：改代码还是改 design.md？ | **改 design.md**（把「JS 写 `--shell-col-*`」改成「JS 写 `--wb-col-*`，CSS 转发」） | `design.md` |
| Q11 | **INC-18 / INC-19** 局部变量与 `--asset-lamp-warm`：登记进权威表，还是声明「组件内局部变量不受本表管辖」？ | **在本表加一节声明**（成本最低） | `night-paper-tokens.md` |
| Q12 | **INC-20 / INC-21** 静物插画的资产目录名、手册 §7.1 与 §10 的自评开关名不一致 | **改 docs**（GLOSSARY 补一句实现目录名；手册统一措辞） | `docs/GLOSSARY.md` / `docs/PRODUCT-MANUAL.md` |
| Q13 | **INC-14** `HANDOFF.md` / `IMPLEMENTATION-LOG.md` 的「D-1…D-16」 | **改文档**为「D-1…D-15」 | `HANDOFF.md` / `IMPLEMENTATION-LOG.md` |
| Q14 | **A-89 口径**：答对回弹落点 = 判定元素还是被选中项？spec delta 措辞要不要跟着改？ | **改 spec delta 措辞**（现措辞「the confirmed element」指代不明） | `workbench-ui` delta / `workbench-ui` spec 本体 |

---

## 9. 附：复核命令（全部可在干净 checkout 上重跑）

```bash
# §4.2 值 token 亮夜配对（53/53）
python - <<'EOF'
import re, pathlib
md = pathlib.Path("openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md").read_text(encoding="utf-8")
lines = md.splitlines()
start = next(i for i,l in enumerate(lines) if l.startswith("## 3. 值 token"))
end   = next(i for i,l in enumerate(lines) if l.startswith("## 4."))
spec = {}
for l in lines[start:end]:
    if not l.startswith("|"): continue
    cells = [c.strip() for c in l.strip().strip('|').split('|')]
    if len(cells) < 3: continue
    m = re.match(r'`?(--[a-zA-Z][a-zA-Z0-9_-]*)`?', cells[0])
    if not m: continue
    spec.setdefault(m.group(1), (cells[1].strip('`').strip(), cells[2].strip('`').strip()))
css = re.sub(r'/\*.*?\*/', '', pathlib.Path("workbench/server/static/workbench.css").read_text(encoding="utf-8"), flags=re.S)
cl = css.splitlines()
def bb(p):
    for i,l in enumerate(cl):
        if re.match(p,l):
            d=0
            for j in range(i,len(cl)):
                d += cl[j].count('{')-cl[j].count('}')
                if j>i and d==0: return i,j
def defs(r):
    d={}; buf=""
    for l in cl[r[0]+1:r[1]]:
        if ';' in l:
            c=buf+l; buf=""
            m=re.match(r'\s*(--[a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*(.+?);\s*$', c)
            if m: d[m.group(1)]=re.sub(r'\s+',' ',m.group(2)).strip()
        else: buf+=l
    return d
L=defs(bb(r'^\s*:root \{')); N=defs(bb(r'html\[data-theme="night"\] \{'))
norm=lambda v: re.sub(r'\s+','',v).lower()
bad=0
for n,(sl,sn) in sorted(spec.items()):
    if n in ('--graph-page-caption','--graph-page-dimmed'): continue
    for tbl,tv,label in ((L,sl,'light'),(N,sn,'night')):
        if n not in tbl: print('MISSING',label,n); bad+=1
        elif norm(tbl[n])!=norm(tv): print('DIFF',label,n,tv,tbl[n]); bad+=1
print('mismatches:', bad)
EOF

# §1.3 INC-09 负荷柱无动画
python - <<'EOF'
import re, pathlib
css = pathlib.Path("workbench/server/static/workbench.css").read_text(encoding="utf-8")
print([m.group(0)[:80] for m in re.finditer(r'[^{}]*\.bar[^{}]*\{[^}]*\}', css) if 'animation' in m.group(0)])
EOF
grep -rn "24ms\|24 ms" workbench/server/static/*.css workbench/server/static/*.js
grep -rn "lk-stagger" workbench/server/static/*.js workbench/server/*.py

# §1.1 INC-03 / INC-06 英文标签与自评开关名
grep -n "Agent activity\|>Artifact<\|Congratulations!\|练习显示自评\|练习与组卷显示自评" workbench/server/pages.py

# §1.1 INC-07 会话列表无滚动容器
grep -n "ai-session-list\|overflow" workbench/server/static/workbench.css | grep -i "session"

# §3 INC-15 契约外的绿
grep -rn "dsw-state-success\|status-dot" workbench/server/static/workbench.css workbench/server/pages.py workbench/server/records.py

# §5 INC-20 资产目录名
grep -n "assets/empty" workbench/server/pages.py workbench/server/static/workbench.css
```
