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
| W1 | 1–4 CSS 地基 | **进行中**（Step 1 `16d3ff89`、Step 2 收编 22 色 `4957c3bc` 已提交） | Step 1 = 新 token 层 + 旧 token 别名期，零 class/JS/结构变化 = 最安全回滚点 |
| W1 | 5.1–5.2 字体资产 | ✅ **完成并提交**（`072f540c`） | Regular 已落（923KB）。**600 字重因体积超标被砍**（规则：超标先砍字重不砍字表）→ 只声明 `font-weight: 400` |
| W1 | 7 Markdown parity | ✅ **完成并提交** | 见 §4 |
| W2 | 6 阅读层 · 8 动效 token · 5.3–5.4 @font-face · 11–15 设置视图+主题+壳层 | 待派 | **全部要动 `workbench.css` ⇒ 必须等 W1 的 F1 收工**（同一文件不可并行） |
| W3 | 16–17 练习页 · 18 知识点+试卷 · 19–20 记录中心+时间视图 | 待派 | 分属不同文件，可并行 |
| W4 | 21 骨架屏+转场 · 9 SVG 资产 · 10 音效 · 22 验收关卡 | **9/10 已派**（不碰 CSS） | 21 与 22 待派 |
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
| 4 | 165 条已登记漂移 | 刻意留账，需后续 change 逐批处理 |
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
