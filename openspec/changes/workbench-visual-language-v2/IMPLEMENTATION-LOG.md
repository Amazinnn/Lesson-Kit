# 实现日志 — workbench-visual-language-v2

> **本文件是「防失忆」保险**：会话中断 / 换人接手时，先读本文件，再读 `HANDOFF.md`。
> 更新纪律：**每完成一个波次就更新**（提交 hash、完成的任务组、发现的裁决、待办、下一步）。
> 任务完成度的权威仍是 `tasks.md` 的复选框；本文件是**上下文与决策的连续性**。

---

## 0. 怎么用这份日志

1. 读 `HANDOFF.md` §2 的**四件必读提示**（rebase / 归档顺序 / 主题默认 / 165 条漂移）。
2. 读本文件的「§3 当前状态」与「§4 波次记录」。
3. 读 `decisions.md`（裁决总账，**任何设计冲突以它为准**）。
4. 看 `git log --oneline -15` 确认磁盘实况。

---

## 1. 实施口径（不可变的边界）

| 边界 | 内容 |
|---|---|
| 分支 | `feat/workbench-visual-language-v2`，**不并入 main** |
| 交付两段 | **样板线 = tasks 第 1–22 组**（所有者验收前）· **铺开 = 第 23–28 组**（样板线验收通过后） |
| **第 22 组是验收关卡** | 关卡未过**不得启动第 23 组** |
| 冻结 | 请求与持久化不变。冻结 = API 请求序列与载荷、持久化内容、学习事实、状态机、由请求驱动的可见性切换 |
| **知识图谱** | **本变更完全不碰图谱**（`decisions.md` A-8）。图谱区段 `workbench.css:1497-1884` 与其 12 个裸名（`:1505-1518`）**一行不改**；新 token 与那 12 个名字**零同名**。本变更对图谱的唯一责任是**不误伤**（`acceptance.md` G-5 否定式断言，图谱页截图逐像素差异 = 0）。图谱的夜纸适配与节点重画归**独立 change** `graph-node-visual-language` |
| 硬约束 | 无框架 · 无构建步骤 · 无 npm · 无 CDN · 无外部图标字体 · 纯 CSS + 原生 JS |
| 提交 | 每个可验证单元单独提交，前缀 `feat/` `fix/` `chore/` `docs/`；**工作区不留脏** |
| 每组验收 | 跑 AGENTS.md 四条：`pytest tests -q` · `compileall -q lessonkit.py workbench pipeline pool tests` · `openspec validate --specs --strict` · `guard extract-problems --course dmath --chapter ch06` |
| 复选框 | **实现 agent 不改 `tasks.md` 的复选框**（并行会抢文件）——由主会话按回报统一勾 |

---

## 2. 关键文件索引

| 用途 | 路径 |
|---|---|
| 裁决总账（**冲突时以它为准**） | `decisions.md`（A-1…A-36 · G-1…G-24 · P-1/P-2 · F-1） |
| 实现方案 | `design.md`（D-1…D-16） |
| 任务清单 | `tasks.md`（28 组 / 167 条） |
| 验收口径 | `acceptance.md`（G-1…G-8 · S-1…S-12 · M-1…M-13 · §3.1–§3.8） |
| **token 唯一权威** | `design-notes/night-paper-tokens.md`（结构 66 + 值 52，两主题） |
| 组件规格 / 动效规格 / 走查执行器 / 资产规格 / 文案表 / 版式 / 图谱移交 | `design-notes/{component-spec,motion-spec,walkthrough-harness,asset-spec,copy-table,layout-spec,graph-isolation}.md` |
| 已知缺陷登记（**登记表，不是待修清单**） | `contract-drift.md`（165 条，`CD-001`…`CD-165`） |
| 视觉评审件（`tmp/` 已 gitignore，不进版本库） | `tmp/frontend-audit/mockups/`（6 页 / 17 截图）· `tmp/frontend-audit/styleboard/` · `tmp/frontend-audit/motionlab/` |

---

## 3. 当前状态

**分支提交数：见 `git log --oneline -1` 之后的全部提交。**

| 波 | 任务组 | 状态 | 备注 |
|---|---|---|---|
| W1 | 1–4 CSS 地基 | ✅ **完成并提交**（Step 1 `16d3ff89`、Step 2 收编 22 色 `4957c3bc`） | Step 1 = 新 token 层 + 旧 token 别名期，零 class/JS/结构变化 = 最安全回滚点 |
| W1 | 5.1–5.2 字体资产 | ✅ **完成并提交**（`072f540c`） | Regular 已落（923KB）。**600 字重因体积超标被砍**（规则：超标先砍字重不砍字表）→ 只声明 `font-weight: 400` |
| W1 | 7 Markdown parity | ✅ **完成并提交** | 见 §4 |
| W1 | 9 SVG 资产 · 10 音效 | ✅ **完成并提交** | 16 件 SVG + 4 条自制音效 |
| W2 | 6 阅读层 · 8 动效 token · 5.3 @font-face | ⚠️ **CSS 侧已提交**（`e60fd920`），**JS 侧与 HTML 侧未做** | 见 **§8** 与 `decisions.md` **A-41 / A-42** |
| W2 | 11 设置视图 · 5.4 缓存策略 | ✅ **完成并提交**（`eed1f138`） | 含主题 / 动效 / 声音三项外观偏好 |
| W2 | `agent-ui.css` 旧名迁移（2.3 的前置） | ✅ **完成，零差异**（见 §8） | 75 处引用 → 0 处残留，全部精确落到别名目标 |
| W3 | 16–17 练习页 · 18 知识点+试卷 · 19–20 记录中心+时间视图 | 待派 | 分属不同文件，可并行 |
| W2c | 12–15 夜纸值集 · 三栏几何 · 标志带 · 顶栏 | 待派 | 与第 6/8 组同改 `workbench.css` ⇒ 只能串行 |
| W4 | 21 骨架屏+转场 · 22 验收关卡 | 待派 | 22 是所有者的签字关卡 |
| W5 | 23–28 铺开 | 待派 | **等第 22 组关卡签字** |

### 已发现并已裁决的「实现期新增裁决」

| # | 内容 | 落在 |
|---|---|---|
| A-3 | 关键反馈音效音色 = **清脆木琴 / 玻璃**，各 <200ms | `decisions.md`（第 5 组 grilling 已定，实现时沿用） |
| A-30 | `--surface-ink` → `--surface-code` 改名成立（取值不变、零可见变化） | `decisions.md` |
| A-35 | **主要动作控件（含发送按钮）一律 `--role-blue` + 纸白字**；近黑底只剩代码块 | `decisions.md` |
| A-36 | 漂移册「建议归属」允许值扩为**六值**（增 `docs/PRODUCT-MANUAL.md`） | `decisions.md` + `contract-drift.md` |
| A-37 | 字体 **600 字重砍掉**，只留 400；`@font-face` 不得声明不存在的 SemiBold | `design.md` D-4「体积实测」 |
| CD-165 | 围栏语言在 Python 侧 `\w` 兼容 Unicode、JS 侧只认 ASCII ⇒ 两侧解析分叉（本轮已统一到 ASCII 口径） | `contract-drift.md` |

---

## 4. 波次记录

### W1

#### 第 7 组 · Markdown 双渲染器统一 + parity 测试 —— ✅ 完成
- 提交：`adcaaf3f`（`feat: unify markdown renderers with a character-exact parity test`）
- 改动：`workbench/server/pages.py`（围栏补 `class='language-xx'`、引用改 `^\s*>\s?`）·
  `workbench/server/static/workbench.js`（客户端标题从 `<h2>` 起步，**只改标签层级未碰字号**）·
  **新建** `tests/test_markdown_render_parity.py` ·
  连带更新 `tests/workbench/workbench_ui_interactions.test.js` 两条写死旧层级的断言
  （不改则 `pytest` 无法全绿）。
- **证据**：改造前 7 failed / 3 passed（差异三类：标题层级 / 围栏语言 / 引用规则）→ 改造后 10 passed；
  另 45 例边界探针 0 差异；**池里 336 条真实内容**全量两侧对跑 0 差异；
  `pytest tests -q` → **1158 passed**；四条验证命令全绿。
- ⚠️ **已知副作用**：「客户端 `#` → h2」是本变更**唯一让既有可见文字变小**的地方
  （`.rich-text` 现行 `h1 21px → h2 18px`）；AI 会话气泡复用同一 `richText`，助手回答里的 `#` 也降一级。
  验收截图需单列这一项（`tasks.md` 7.5 有此要求）。
- ⚠️ 跨组待办：`.rich-text` 没有 `h4` 规则（`h3 16px < h4 17px` 倒挂），现两侧 `###` 都落 h4，
  **倒挂会在两个渲染器同时显形** ⇒ 须由第 6 组的 `.wb-reading` 自带 h1–h4 规则消除。

#### 第 1–4 组 · CSS 地基 —— 进行中
- Step 1 已提交：`16d3ff89`（`feat(workbench): 落 token 地基 Step 1 —— 新 token 层 + 旧 token 别名期`）
- 剩余 Step 2（描边/抬升/文字灰 + 22 个硬编码色收编）→ Step 3（纸面四层/暖调柔影/取消描边/墨阶收敛/
  契约外绿移除 →「答对」改中性墨 + 勾形几何）→ 2.2 补 4 个从未定义变量（**单独提交**，
  其中 `--dsw-border-subtle` 补齐后表格线会从「正文色」变成新规则色，**属可见变化**）→ 2.3 别名期收尾。

#### 第 5 组 · 字体 —— 进行中
- `static/fonts/`：`SourceHanSerifSC-Regular.woff2`（923KB）· `LICENSE-OFL.txt` · `README.md`
- **600 字重因体积超标被砍**（只留 400）；`@font-face` 只声明 400。
- 待办：5.3（`@font-face` + 三族分工）· 5.4（字体缓存策略，`app.py` 的 `_send_static`）

#### 第 10 组 · 关键反馈音效 —— ✅ 完成
- 新建 `workbench/server/static/sfx.js`（音效引擎）+ `assets/audio/sfx-{right,wrong,complete,milestone}.wav`
  （**自制合成**，Python 标准库 `wave` 加法合成，pytest 重渲染逐样本比对 ±4 LSB ⇒ 手改/下载会测试失败）
- 4 条时长 0.140 / 0.140 / 0.185 / 0.190s（全部 < 200ms）；16-bit 44.1kHz 单声道，峰值归一 0.72 不削顶
- 改 `workbench.js`（+142，4 个触发点接入）+ `app.py`（CONTENT_TYPES 加 wav/mp3/ogg）+ `pyproject.toml`（package-data）
- 新建 `tests/workbench/sfx_assets.py`（合成器）· `sfx.test.js`（node 14 例）· `test_sfx_assets.py`（pytest 6 例）
- **自动播放限制**：模块加载只注册监听器、不建元素；首次用户手势才预建 4 个 `Audio`；此前 `playCue()` 直接返回 false
- **发声闸门**：判定/完成只有在「最近一次交互是对应提交按钮」时才发声 ⇒ 回看旧答案 / 重渲染 / hover / 展开 / 导航**一律零发声**
- 验证：pytest **1164 passed** / compileall 0 / openspec 19 / guard PASS；node 14/14；file:// 与 http 双测 console 0 error
- ⚠️ 跨组硬前置见 **A-38**：第 11 组用同名字段 `sound`（默认开）；第 8/17 组的爆点必须带 `lk-celebrate-burst`

#### 第 9 组 · 静物 SVG 资产 —— 进行中
- 只新建 `static/assets/`；另出 `static/assets/preview.html`（全部资产排开、浅/夜两底）便于目检。

#### 第 10 组 · 关键反馈音效 —— 进行中
- 首选 **Web Audio 实时合成**（零二进制资产、零版权、可精确控时长）；文件方案为备选。
- 硬点：加载后零发声 · 首条等用户手势 · 静音后零发声但视觉反馈不受影响 · 其它事件零发声。

---

## 5. 未决 / 待所有者

| # | 事项 | 状态 |
|---|---|---|
| 1 | **第 22 组验收关卡** | 等样板线跑完 → 交对照截图 + 关键帧分镜条 + 交互清单 → **所有者签字**才开第 23 组 |
| 2 | **F-1 组件样式一览** | 已排队（F-1）。等方向定稿后**重做** `styleboard`（现版本是旧方向的 25 组/103 候选） |
| 3 | 「破纪录」比较范围 | CD-164，待定义。**在此之前不得用代理指标近似触发里程碑** |
| 4 | 167 条已登记漂移 | 刻意留账，需后续 change 逐批处理 |
| 5 | 夜纸下知识图谱 | 归 `graph-node-visual-language` change（与节点重画一起做，避免两次改图谱） |

---

## 6. 本轮沉淀的方法（换人接手时值得知道）

1. **覆盖率矩阵**：135 条裁决逐条核 ✅/⚠️/❌，抓到方向被写反、凭空蒸发、违反现行 spec 三类。
2. **逐值 grep + 语义追问**：抓到三族 token 并存、同名两值、**取值相同但语义不同**。
   逐值比对只能发现第一层，必须再问「它在那个语境里说的是不是这个东西」。
3. **用现成实现当参照**：Obsidian 的参数来自**本机安装包 `app.js` 源码**；
   而仓库里 `frontend/editable-graph` 那份参照实现**自己就不是 faithful 克隆**。
4. **agent 的自检可能验证错对象**：它用本地 http 服务自检，就漏掉 `file://` 下 Chrome 禁外链 SVG
   导致图标全丢 —— 而用户是**双击打开**的。
5. **空回报要信盘不信话**：D-03 跑满 26 次工具调用只落 11 行。交接时一律核 `wc -l` + `tail`。
6. **漂移登记会自己过期**：修完东西后，先前登记的「此处待改」会变成假警报 —— 必须回头收口。
7. **并行改同一个文件必丢改动**：复选框统一由主会话勾；`workbench.css` 严格串行。

---

## 7. 关机快照（2026-10-22 15:5x，第 1 次关机前）

**任务完成度：33 / 167**（`tasks.md` 复选框为准）

### 已完成的组
| 组 | 内容 | 提交 |
|---|---|---|
| 1.1–1.5 · 2.1 · 2.2 · 2.4 · 3.2–3.4 · 4.1–4.2 · 4.4–4.5 | CSS 地基：新 token 层 + 别名期 + 纸面层级 + 色彩收编 | `16d3ff89` `4957c3bc` `b582f6e0` `b245bcd2` `57d87f2d` |
| 5.1–5.2 | 思源宋体子集化 + OFL 许可 | `072f540c` |
| 7.1–7.5 | Markdown 双渲染器统一 + parity 测试 | `adcaaf3f` |
| 9.1–9.4 | 静物 SVG 资产 16 件 | `be5b283b` `68980fab` |
| 10.1–10.7 | 关键反馈音效 4 条（自制合成 WAV） | `cb42b16d` |

### 关机时仍在跑的 3 个 agent（改动都在盘上，未提交）
| Agent | 范围 | 落在哪些文件 |
|---|---|---|
| W2a | 第 6 组阅读层 + 第 8 组动效 token + 5.3 字体声明 + 3.1b 沉底内发丝线 | `workbench.css` |
| W2b | 第 11 组设置视图与偏好存储 + 5.4 缓存策略 | `pages.py` `workbench.js` `app.py` |
| F11 | `agent-ui.css` 70 处旧名迁移 + `test_ui_routes.py` 逐字断言更新（**2.3 别名期收尾的前置**） | `agent-ui.css` `tests/` |

> **冷启动第一件事**：先 `git status` 看这三个 agent 留下了什么（若它们已收工则把改动提交），
> 再跑四条验证命令确认基线是绿的。

### 未派（按依赖排队）
| 顺序 | 波 | 内容 | 为什么现在不能派 |
|---|---|---|---|
| 2 | W2c | 第 12–15 组 CSS 版式层（夜纸值集 / 三栏几何 / 标志带 / 顶栏） | 与 W2a 同改 `workbench.css` |
| 3 | W3 | 第 16–20 组（练习页 / 知识点+试卷 / 记录中心+时间视图） | `pages.py` `workbench.js` 与 W2b 冲突 |
| 4 | W4 | 第 21 组骨架屏+转场、第 22 组**验收关卡** | 依赖前面全部完成 |
| 5 | W5 | 第 23–28 组铺开 | **等所有者签第 22 组关卡** |
| 6 | 图谱 change | 图谱节点重设计 126 任务 / 13 组 | 触及 `workbench.js`(10) `workbench.css`(9) `graph-physics-core.js`(3)，与 W2a/W2b/W2c 正面冲突 |

### 三个未决（等所有者，可延后）
1. **4.3 的 caption/dimmed 两档**：字面合并会改**图谱页像素**；留旧名则零差异（取值仍走 `--ink-faint`）。
   倾向：留旧名，等 2.3 一起清。
2. **2.3 的提交边界**被并行 agent 的 `git add -A` 并进了 `cb42b16d`；拆分要 revert + 重提
   （会经过一个旧状态中间点）。倾向：**不拆**（内容逐行核对过是对的）。
3. **3 处硬编码硬阴影**（闪卡 `rgb(17 19 24 / 14%)` 等）权威表无对应 token，未动。

### 两条最容易再踩的坑（**别再踩**）
- **A-39 服务陈旧副本**：本机 pip 装着 `lesson-kit 0.1.0`；从**仓库根以外**的目录启动的服务
  `import workbench` 会解析到 site-packages 的**安装快照**。任何视觉验证前先比对
  `curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c` 与
  `wc -c workbench/server/static/workbench.css` —— **两个数必须相等**，不等就重启服务。
- **CSS 行号锚点会失效**：第 1–4 组在 `:root` 插了 318 行，`workbench.css` 以下所有行号位移
  且不均匀（+307 / +702，甚至 −100）。**一律按选择器 / 声明 / 注释文本定位**
  （`grep -n "<选择器>" workbench/server/static/workbench.css`），
  `briefs/ANCHOR-REMAP.md` 只作交叉核对（它自己也已过期）。

---

## 8. 第二次收工快照（2026-10-22 17:2x，第 2 次关机前）

> **本节是当前状态的唯一权威**（§7 是第 1 次关机时的快照，已过期但仍记录了当时的判断）。
> 触发原因：两名实现 agent（W2a、F11）**在收尾阶段因供应商鉴权失败（Unauthorized）退出**，
> 磁盘上的成果都还在，但**它们的最终回报没写出来** ⇒ 本节由主会话逐条核实后补写。

### 8.1 分支与提交

- 分支 `feat/workbench-visual-language-v2`（**未并入 main**），fork 点 `944b867c`。
- 收工时的 HEAD：`ba650e20`（勾选第 11 组 + 5.4）。
- 本次新增提交：W2a 的第 6/8 组 CSS（`e60fd920`）→ 随后补 F11 的 `agent-ui.css` 迁移与本节文档。

### 8.2 三个 agent 的最终交付（实测数字）

| agent | 范围 | 结果 | 提交 |
|---|---|---|---|
| W2b | 第 11 组设置视图 + 5.4 缓存策略 | ✅ 完成 | `eed1f138` |
| W2a | 第 6 组阅读层 · 第 8 组动效 · 5.3 @font-face | ⚠️ **CSS 侧完成，JS/HTML 侧未做** | `e60fd920` |
| F11 | `agent-ui.css` 旧名迁移（2.3 的前置） | ✅ **完成，零差异** | 本次提交 |

**W2a 的 CSS 侧实测**（`workbench.css`，提交后 115,923 B）：

- `@keyframes` 共 **23** 条，其中第 8 组要求的 20 条**全部在位**
  （`lk-squash-bounce` / `lk-rise-in-8` / `lk-rise-in-12` / `lk-skeleton-sweep` /
  `lk-error-nudge` / `lk-combo-in` / `lk-combo-out` / `lk-flame-ignite` / `lk-progress-fill` /
  `lk-celebrate-burst` / `lk-confetti-fall` / `lk-flip-roll` / `lk-spin` +
  台灯四段 7 条）。
- 动效 token 五档时长 + 三档缓动**全部落位**；散落 transition 已收编到 token
  （真实 `transition: all` 命中 **0**，只剩注释里的黑名单声明）。
- 分级降级闸门**已取代**旧的一刀切 `none !important`（`workbench.css` L2452 起：
  `animation-name: none !important` + `transition-property: opacity !important`），
  且**起始态只写在 `@keyframes` 内部**（静态样式 = 终态）。
- `@font-face`：`font-display: swap` + `unicode-range` 限中文 +
  `font-weight: 400 600`（可变声明，**不引用不存在的 SemiBold 文件**）→ 5.3 **完成**。
- **`.wb-reading--stem` 未实现**（全仓 0 命中）⇒ 6.1 暂不勾选。

**F11 的迁移实测（零差异，已用脚本证明）**：

- `agent-ui.css` 迁移前 **75 处**旧名引用（17 个不同名字），迁移后 **0 处**残留。
- 逐条比对：每个旧名的**新名字 == 该旧名在 `workbench.css` 里的别名目标**
  ⇒ **失配 0 条**，即**渲染结果零变化**。
- 同步改了 `tests/workbench/agent_ui_v1.test.js` 与
  `tests/workbench/test_ui_routes.py` 的**逐字断言**（旧名字面量 → 新名字面量）。

### 8.3 基线验证（第 2 次收工时全绿）

```bash
python -m pytest tests -q                                  # 1164 passed in 272.07s
python -m compileall -q lessonkit.py workbench pipeline pool tests   # OK
openspec validate --specs --strict                        # ✓ 19 passed, 0 failed
python lessonkit.py guard extract-problems --course dmath --chapter ch06   # Result: PASS
```

### 8.4 未完成清单（**下一波从这里接**）

| 条目 | 卡在哪 | 谁来做 |
|---|---|---|
| 6.1 | `.wb-reading--stem` 变体未实现 | 拥有 `workbench.css` 的下一波（与 6.2/6.3 同波） |
| 6.2 / 6.3 | 20 个 `.rich-text` 挂载点未改名；`.rich-text` 规则未删 | **必须**同时拥有 `pages.py` + `workbench.js` + `practice-flow.js` + `paper-practice.js` 的 agent（A-41 段二） |
| 6.4 / 6.5 | 密度分区的「记录页 20 行高度小于基线」需浏览器实测；阶段验收未跑 | 第 22 组验收关卡 |
| 8.4 / 8.7JS / 8.8JS | 统计数字滚动 / 火苗 / 进度带 / 台灯 JS 写色 / 两档庆祝落点 —— 全未做 | 动效 JS 编排小波（A-42） |
| 8.6 / 8.10 / 11.7 等阶段验收 | 截图走查未跑 | 各组收工时 + 第 22 组 |
| `--lk-ripple-base` | 新钩子落在 `--lk-*` 家族，会卡住 2.3 的「非图谱区 `--lk-` 归零」 | 下一波改 `workbench.css` 时顺带改名（A-42 第 2 条） |
| 3 处 `--dsw-border-l1` | **图谱详情面板**元素，受冻结块保护，换名会破 G-5 | **留旧名**，等图谱 change 接手（A-42 第 3 条） |
| 4.3 的 caption/dimmed | 同上 | **留旧名**（待所有者确认，见 §5） |

### 8.5 下一波的顺序与文件所有权

> **同一文件必串行** —— 本轮所有返工都源于此。

| 顺序 | 波 | 内容 | 文件 |
|---|---|---|---|
| 1 | W2c | 第 12–15 组 + 6.1 的 `--stem` + `--lk-ripple-base` 改名 | 只动 `workbench.css` |
| 2 | W3 | 第 16–20 组 + **6.2/6.3 的 HTML 迁移** + **动效 JS 编排** | `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` / `records` 相关脚本 |
| 3 | W4 | 第 21 组骨架屏+转场、第 22 组**验收关卡** | 依赖前面全部 |
| 4 | W5 | 第 23–28 组铺开 | **等所有者签第 22 组关卡** |
| 5 | 图谱 change | 126 任务 / 13 组 | 与 W2c / W3 正面冲突 ⇒ 排最后 |

---

## 9. 第 3 波派工（2026-10-22 下午，第 2 次开机后）

### 9.1 按「同一文件必串行」重新切分（本波 7 个并行 agent）

| agent | 任务书 | 独占文件 | 任务 |
|---|---|---|---|
| W2c | `briefs/IMPL-W2c.md` | `workbench.css` | 第 12–15 组 + 附加（6.1 的 `--stem` / 3.1–3.1b / `--lk-ripple-base` 改名） |
| W3a | `briefs/IMPL-W3a.md` | `workbench.js` | 13 组 JS 侧 + 6.2/6.3 的 JS 段 + 8.4 / 8.7 / 8.8 动效编排 |
| W3b | `briefs/IMPL-W3b.md` | `pages.py` | 15 / 16 / 18 / 21 组服务端侧 + 6.2/6.3 的 PY 段 |
| W3c | `briefs/IMPL-W3c.md` | `practice-flow.js` · `paper-practice.js` | 14 组 JS 侧 + 10.5 音效四落点 + 17 组连对逻辑 |
| W3d | `briefs/IMPL-W3d.md` | `middle-navigation.js` | 21 组换页 / 骨架屏 / 焦点 |
| W3e | `briefs/IMPL-W3e.md` | `records.py` | 19 组记录中心 + 20 组负荷柱 |
| W3f | `briefs/IMPL-W3f.md` | **只新建** `tools/` | 图谱 **SI-0 基线取证**（坐标 diff 工具 + 改造前基线） |
| W3g | 见下 | **只新建** `tools/walkthrough/` | 走查执行器（`launch.py` / `recorder.py` / `shots.py`） |

> 任务书全部落盘在 `briefs/`（`tmp/` 被 gitignore，落那儿会丢）。

### 9.2 W3f 已收工：图谱 SI-0 基线已落盘 ✅

- `tools/graph-layout-diff.js`（22 KB）—— Node 脚本，直接 `require` **DOM-free** 的
  `graph-physics-core.js`；`--capture` / `--diff` 两个模式。
- `tools/graph-baseline/baseline.json`（96 节点 / 338 边 / 12 章 × 8 点）+
  `README.md` + `EVIDENCE.md`。
- **实测**：连跑两次 `--capture` **逐字节相同**（sha256 一致）；
  `--diff` **差异 0 条**，退出码 0；**负向对照**（人为改基线两处坐标）报 **2 条差异、退出码 1**
  ⇒ 判据不是空的。
- 量化口径：6 位小数 / 按 `nodeId` **码位序**排序 / `toFixed` 字符串全等，**全程无 epsilon**。
- 锚点是 `graph-physics-core.js` 的 **sha256**（不是 commit SHA —— 仓库在并行提交，HEAD 会动）。
- ⚠️ W3f 顺带查出 10 处「不该动但容易被误读」的地方，其中三处要紧：
  1. `graph-physics-core.js` 里混着**四段纯绘制代码**（`edgeStyle()` 等）
     ⇒ **「物理核心零 diff」不能当门禁**，会与图谱 change 第 5 组打架；
  2. 布局路径里有**两处 `localeCompare`**（`:613` / `:664`）⇒ **跨机器确定性隐患**，
     SI-0 的「严格 0」在不同 ICU 数据上不成立；
  3. 浏览器每帧迭代步数**随节点数变**（`>120` 走 3 步）⇒ 「同一迭代预算」在浏览器端会漂。
  ⇒ 这三条要登记进 `graph-node-visual-language` 的漂移册与第 14 组的判据说明。

### 9.3 所有者的三个裁决：**按文档判，不按偏好判**

所有者的回答是「**看看已有的文档，它们是怎么要求的？**」⇒ 已逐条查证并落进
`decisions.md` **A-43 / A-44 / A-45**：

| 议题 | 文档依据 | 结论 |
|---|---|---|
| 4.3 caption/dimmed | 4.3「并入 `--ink-faint`」+ 2.3「非图谱区归零」+ 冻结块自述「2.3 时改成钉**新** token 名」 | **字面合并**，且**同波改冻结块**（图谱页旧值一字不变）；若 G-5 变红则按 A-19 教训回退并登记例外 |
| 2.3 提交边界 | 2.3 标题自带「**独立提交**」+ `AGENTS.md` 纪律 5 | **问早了** —— 2.3 本身还没做完（别名定义 / `.rich-text` 规则 / 图谱 3 处旧名都还在）。**不拆历史提交**；2.3 真正落地那一波必须独立提交 |
| 3 处硬编码硬阴影 | 4.2 验证「非图谱区硬编码 hex 只剩 token 声明行内的值」+ 权威表 §3.6 只有 `--elev-1/2/3` 柔影 | **收编成 token**（权威表新增「硬阴影」一档，亮/夜两套值）；顺带登记闪卡的 `2px solid var(--ink-strong)` 重描边待处理 |

### 9.4 本波之后：所有者已选「**先出验收关卡的可视化走查**」

不铺开第 23–28 组，先把样板线的验收产物做出来给所有者看：
六类页面的**亮 / 暗双主题对照截图** + 动效分镜条 + reduced-motion 降级对照帧
+ 底线守卫 G-1…G-8 的脚本化判定。
⇒ 走查执行器（W3g）**已并行开建**，与本波产品代码零冲突。
**签字前不启动第 23 组。**

### 9.5 本波收工记录（边收边补）

| agent | 结果 | 提交 |
|---|---|---|
| W3f | ✅ 图谱 SI-0 基线取证（diff 严格 0，见 §9.2） | 3 个（`tools/`） |
| W3d | ✅ 第 21 组 + **两处复核修正**：① 进图谱页不呈通用骨架（`54d540d8`）② 骨架用通用占位、不做 per-page（`decisions.md` **A-46**） | `14536daf` `73f3d541` `9cf4ae1e` `c7629b81` `754cfa1e` `54d540d8` |
| W3c | ✅ 第 17 组逻辑侧（连对计数器 / 火苗簇 / 参数化横幅 / 断裂负反馈） | `1077f010` … |
| W3e | ✅ 第 19 组（卡片流 / 错题视图 / 累计量可见） | `036cd426` `61fb0aad` `1d06acb9` … |
| W2c | 🔄 第 12–15 组 CSS（夜纸值集 / 三栏几何 / 标志带 / 顶栏 / 14.1 死代码退役） | `8b452780` `7ade44aa` … |

**W3d 复核时暴露的两个问题（已处理，记录在此以免复发）**：

1. **本波唯一的 pytest 失败项**是 `test_static_asset_served` 断言 CSS 里存在
   `.scope-tray-list {` —— 而任务 **14.1** 恰恰要求把 scope-tray 死代码删光
   （验收：`grep -rn "128px\|scope-tray" workbench/` 归零）。
   ⇒ **断言已改为否定式**（`fa369ae5`）。**教训：产品代码按 spec 删除后，
   断言旧字面量的测试必须同步改** —— 这类失败与产品代码无关，别误判成回归。
2. **新增行为不能落在图谱页**：CSS 侧的图谱排除只管**转场动画**，
   而骨架屏是**本次新增的 JS 行为**，没经过那道排除 ⇒ 进图谱页会闪一帧骨架。
   ⇒ 已修（`54d540d8`）。**教训：每加一处新行为，都要问「它落在图谱页上会怎样」。**

> 第 22 组验收关卡的任务书已落盘：`briefs/IMPL-W4.md`（**只读判定**，不改产品代码）。
