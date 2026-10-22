# 交接 — workbench-visual-language-v2 + graph-node-visual-language

> 生成时间：2026-10-22
> 分支：`feat/workbench-visual-language-v2` —— **不要并入 main**
> 仓库根：`D:\Projects\Academic Workflow\lesson-kit`
> 本文件是这两个变更的**唯一入口文档**；所有细节都能从这里指到具体文件。
>
> ⚠️ **实现已开工**（2026-10-22）。接手时请**先读 `IMPLEMENTATION-LOG.md`** ——
> 它记录波次进度、已落地的提交、已裁决的实现期新增裁决、以及当前在跑的 agent。
> 本文件是**范围与操作提示**；`IMPLEMENTATION-LOG.md` 是**进度与连续性**。

---

## 1. 一句话状态

前端视觉语言重做已**全部定案并落成可执行契约**，并且**已经开工**：
主变更覆盖练习 / 知识点 / 记录 / 试卷 / 设置视图 / 壳层 / hub，图谱变更单独覆盖知识图谱的节点外观。
**当前进度 47 / 167 条任务完成**，基线四条验证命令全绿。

> 📌 **接手第一步**：读 `IMPLEMENTATION-LOG.md` **§8「第二次收工快照」** ——
> 那是**当前状态的唯一权威**（§7 是第 1 次关机时的旧快照）。
> 紧接着读 `decisions.md` 的 **A-41 / A-42**（第 6/8 组这次交付留下的两处拆分裁决）。

| 指标 | 主变更 | 图谱变更 |
|---|---|---|
| 位置 | `openspec/changes/workbench-visual-language-v2/` | `openspec/changes/graph-node-visual-language/` |
| 需求 / 场景 | **32 条 / 150 场景** | **16 条 / 89 场景** |
| 任务 | **167 条（已完成 47）** | **126 条（未开工）** |
| 设计件 | 8 份 / 15921 行 | — |
| 状态 | `openspec validate --specs --strict` → ✓ 19 passed | 同 |

**已知缺陷 165 条已登记在册**（`contract-drift.md`），每条带「改成什么 / 谁来定」。
这是**刻意留下的账**，不是遗漏。

---

## 2. 四件必读的操作提示

### 2.1 rebase 冲突（合并前必做）

本分支从 `944b867c` 切出。**main 之后已前进 7 个提交**（另一个会话的
「CLI 技能打包」工作：`workbench/cli/main.py`、`tests/workbench/`、`.claude/skills/`、
`FILE_CONTRACT.md`、`.gitattributes`，以及 `openspec/changes/archive/2026-10-22-…`）。

与本分支**重叠的只有 4 个文件**：

```
docs/GLOSSARY.md
docs/PRODUCT-MANUAL.md
docs/ACTION-GRAPH.md
docs/ARCHITECTURE.md
```

冲突是**文字型**（main 改 CLI 技能那些段落，本分支改视觉语言那些段落），
按段落手工合并即可。`openspec/` 与产品代码**完全不重叠**。

> ⚠️ 另注：`docs/PENDING-DEFINITIONS.md` 的改动是**别人在 2026-10-18 的未提交改动**，
> 不是本轮产物。**不要提交它，也不要还原它。**

### 2.2 归档顺序（硬性，不可颠倒）

`Redundant state cues` 与 `Soft Mondrian visual foundation` 这两条需求，
**两个 change 都 MODIFIED 了**。

> **必须先合入 `workbench-visual-language-v2`，再把 `graph-node-visual-language` 的这两块
> re-base 到 v2 的版本上**，否则图谱 change 先落地会覆盖 v2 已写的扩展内容。

归档时逐字复核这两条的最终文本 = 「v2 的版本 + 图谱例外段落」的合流结果。
见 `decisions.md` **A-10.2**。

### 2.3 主题默认来源

主题偏好**默认跟随系统** `prefers-color-scheme`；**学习者显式选择优先并覆盖系统**。
实现见 `tasks.md` 11.3 / 11.4（`_base()` 内联脚本：无已存偏好读系统，有则读它，
都写 `<html data-theme>`，首屏无闪烁，无 JS 时降级为亮色）。
`docs/GLOSSARY.md` 与 `docs/PRODUCT-MANUAL.md` 已向用户承诺这一点，**承诺正确，不要改**。
见 `decisions.md` **A-11**。

### 2.4 165 条已登记漂移

`contract-drift.md` 登记了 **165 条**（`CD-001`…`CD-165`）「本轮不改、待后续 change 处理」
的契约漂移。**它是登记表，不是本轮要修的清单。**

- 不得为了让本轮看起来干净而把其中任何一条静默修掉；
- 不得把它当成「已处理」；
- 交接时应在 `docs/PENDING-DEFINITIONS.md` 或本文件里提示「存在 165 条已登记漂移」
  ——**提示写在 HANDOFF（本文件）**，不要往 PENDING-DEFINITIONS 追加。

---

## 3. 工件清单

### 3.1 主变更 `workbench-visual-language-v2/`

| 文件 | 行数 | 作用 |
|---|---|---|
| `proposal.md` | 180 | 为什么改、改什么、冻结清单、能力清单 |
| `decisions.md` | 1647 | **裁决总账**：收口基线 + A-1…A-42 + G-1…G-24 + P-1/P-2 + F-1 |
| `design.md` | 1397 | D-1…D-16 实现决策（每条含「决策/理由/否掉的备选/代价」） |
| `tasks.md` | 309 | 167 条任务 / 28 组（**1–18 组 = 样板线，19–25 组 = 铺开，26–28 = 清理与验收**）；**已完成 47** |
| `acceptance.md` | 192 | 底线守卫 G-1…G-8 · 12 张对照截图 S-1…S-12 · 13 条关键帧 M-1…M-13 · 交互清单 §3.1–§3.8 |
| `contract-drift.md` | 465 | 165 条已登记漂移（**登记表，不是待修清单**） |
| `specs/workbench-ui/spec.md` | 1106 | 24 条 Requirement / 109 场景（**主战场**） |
| `specs/workbench-settings/spec.md` | 253 | 新能力：7 条 / 27 场景 |
| `specs/calendar-workload/spec.md` | 151 | 1 条 MODIFIED / 14 场景 |
| `design-notes/night-paper-tokens.md` | 1046 | **token 唯一权威**（结构 66 + 值 52，两主题） |
| `design-notes/component-spec.md` | 2098 | 28 组件全 8 态规格 + 42 段 CSS |
| `design-notes/motion-spec.md` | 1319 | 20 条 `@keyframes` + 19 行交互映射 + 降级矩阵 |
| `design-notes/walkthrough-harness.md` | 2204 | 走查执行器（请求序列捕获、判定与报告、32 条风险） |
| `design-notes/layout-spec.md` | 1825 | 26 张 ASCII 线框 + 响应式 + 密度分区 |
| `design-notes/copy-table.md` | 1805 | 671 条界面文案分类（删 31/改 70/译 20/留 550） |
| `design-notes/asset-spec.md` | 1906 | 5 图标 + 10 插画 + 台灯三姿态 + 交付规则 |
| `design-notes/graph-isolation.md` | 1716 | 图谱**移交清单**（图谱交给另一 change） |

### 3.2 图谱变更 `graph-node-visual-language/`

| 文件 | 行数 | 作用 |
|---|---|---|
| `proposal.md` | 364 | 为什么改（图谱节点「塑料感」的根因）+ A-24→A-28 决策链 + 冻结清单 |
| `design.md` | 1316 | D-1…D-14（含 **D-13 的 14 项冻结 + 6 项只绘制的允许清单**） |
| `tasks.md` | 240 | 126 条 / 14 组（第 14 组 = 算法冻结与 diff=0 证据） |
| `acceptance.md` | 281 | **SI-0（坐标 diff = 0）** 与 SI-1…SI-5 并列 + AV-1…AV-4 + M-1…M-6 |
| `specs/graph-visual-language/spec.md` | 333 | 新能力 9 条 / 39 场景 |
| `specs/workbench-ui/spec.md` | 343 | 7 条 MODIFIED / 50 场景 |

### 3.3 职责文档（`docs/`，6 份，+268/−18）

| 文件 | 改动 |
|---|---|
| `docs/GLOSSARY.md` | 「柔和蒙德里安」**改写**为 v2（暖色+现代圆润）+ **17 个新词条**（纸面层级/夜纸/冗余状态通道/主题偏好/阅读字面/动效偏好/声音偏好/工作台设置视图/静物插画/台灯转场/少字原则/图案适配原则/图谱暖色板/同心圆节点/图谱色键/屏幕空间尺寸） |
| `docs/PRODUCT-MANUAL.md` | 新增第 10 章「外观与主题」；§3.2 知识点页、§3.3 图谱页、§6.1 练习页、§7.1.2 记录中心 |
| `docs/ACTION-GRAPH.md` + `action-graph/L3-actions.md` | 登记「打开/关闭工作台设置视图」与「修改外观偏好」两条动作（**已定义未实现**；不新增其它动作） |
| `docs/ARCHITECTURE.md` | §1 静态资产目录（`fonts/` `assets/` `audio/` `settings.css/js`）+ §4 前端扩展点（图谱暖色板限域例外） |

---

## 4. 视觉基线速查

| 项 | 值 |
|---|---|
| 底色（浅 / 夜） | `#fdf8ef`… 见权威表 §3.1 / 夜纸 `#1c1a16` |
| 纸面 4 层 | 底 / 卡 / 浮起 / **沉底**（`--surface-sunken`；近黑 `--surface-code` **只**给代码块） |
| 圆角 | **12px** 统一 |
| 墨 | 暖炭褐 `#221f1a` |
| 三角色 | 蓝=主按钮+链接+当前选中 / 黄=当前+复习+连对进度 / 红=失败+阻塞（**黄色只承载面积与形状**） |
| 状态表达 | **颜色 + 几何**双通道，**零状态文字** |
| 正文 | 17px / 1.75 / 38em，衬线；界面无衬线 |
| 动效 | 交互 120–180ms；场景 240–520ms；**只动 transform/opacity**；reduced-motion 分级降级且**终态与开启时一致** |
| 主题转场 | 台灯探出 → 点亮 → 涟漪 → 收回（~700ms） |
| 庆祝 | 日常档（数字滚动+进度带） / 里程碑档（+几何爆点+彩带纸片）；里程碑**两条件**：全对 / 章节首次完成 |
| 连对 | 三级计数器 + 5/10 连参数化横幅 + 火苗簇 + **combo>4 答错必须明示** |

**图谱**：单层实心圆（无描边无阴影）· 半径 5–13px 屏幕像素 · 标签点下 5px 恒 12px ·
边屏幕恒定 1.25px 带方向箭头 · 非邻接 alpha 0.2 · **缩放只改间距不改尺寸**。

---

## 5. 图谱算法冻结（硬要求）

**冻结**：力模型 / 迭代 / 收敛判据 / 阻尼 / 引力斥力 / 碰撞分离 / 布局种子 /
邻接与边集合 / 边类型与权重 / 筛选语义 / 投影语义与分档 / 指标计算 /
DOM 节点身份与顺序 / 拖拽与聚焦的行为语义。

**只许改绘制**：节点形状与颜色、**绘制**半径（与物理半径解耦）、标签绘制与位置、
边的绘制、缩放补偿。

**可执行判据**：同一输入 + 同一初值 + 同一迭代预算，改造前后
**收敛坐标集合 diff 必须严格为 0**。落 `graph-node-visual-language/tasks.md` 14.1–14.6
（先基线 → 后改动 → 留证据），并作为 `acceptance.md` 的 **SI-0** 门禁。
**diff ≠ 0 即回滚。**

---

## 6. 视觉评审件（不进版本库）

`tmp/frontend-audit/mockups/`（`tmp/` 被 gitignore）—— **6 个页面 / 17 张截图**：

| 文件 | 内容 |
|---|---|
| `index.html` | 规格总览：token 色板、两主题并排、纸面分层、字号阶梯、对比度实测、动效档位 |
| `shell.html` | 壳层（四区）；`?rail=list` / `?rail=chat` 切右栏两态 |
| `practice.html` | 练习页（题面独立纸 / 24px 大题号 / 解析同级纸 / 作答分隔区 / 题号导航四态） |
| `knowledge.html` | 知识点页（分组卡片列表 + 衬线阅读面详情） |
| `records.html` | 记录中心（仪表盘卡片 / 热力方块日历 / 卡片流） |
| `graph.html` | 图谱（单层小圆点 / 四投影色键 / 随投影切换的图例） |

> ⚠️ **mockup 是静态的，只呈现终态。** 动效的实现要求在 spec delta 与 tasks 里
> （A-27 的 14 条清单，每条都有条款 + 任务 + 分镜条 + 降级对照帧）。
> **不要因为 mockup 上看不到运动就以为没有动效。**

**组件样式一览**（每个组件的并排变体，让你挑）已排为 **F-1**，等方向定稿后重做
（现有 `tmp/frontend-audit/styleboard/index.html` 是**旧方向**的 25 组/103 候选，不适用）。

---

## 7. 下一步

### 7.1 波次顺序（**同一文件必串行**）

> 这是本轮最贵的一条教训：**并行 agent 抢同一份 `workbench.css` 是所有返工的根源。**
> 派活前先查这张表的「文件」列，**同一个文件不许出现在两行里**。

| 顺序 | 波 | 内容 | 文件 | 前置 |
|---|---|---|---|---|
| 1 | **W2c** | 第 12–15 组（夜纸值集 / 三栏几何 / 标志带 / 顶栏）+ 6.1 的 `.wb-reading--stem` + `--lk-ripple-base` 改名 | **只动 `workbench.css`** | 无（W2a 已收工） |
| 2 | **W3** | 第 16–20 组（练习页 / 知识点+试卷 / 记录中心+时间视图）+ **6.2/6.3 的 HTML 迁移** + **动效 JS 编排**（8.4 / 8.7JS / 8.8JS） | `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` / 记录页脚本 | W2c 收工 |
| 3 | **W4** | 第 21 组骨架屏+转场、**第 22 组验收关卡** | 依赖前面全部 | W3 收工 |
| 4 | **W5** | 第 23–28 组铺开 | — | **等所有者签第 22 组关卡** |
| 5 | 图谱 change | 126 任务 / 13 组 | 触及 `workbench.js`(10) / `workbench.css`(9) / `graph-physics-core.js`(3) | 与 W2c / W3 正面冲突 ⇒ 排最后 |

**第 22 组是所有者的签字关卡**，签字前不得启动第 23 组。

### 7.2 尚未做的两块（**别以为做完了**）

1. **第 6 组的 HTML 段**：`.rich-text` 的 **20 个挂载点**（`pages.py` 4 / `workbench.js` 2 /
   `practice-flow.js` 9 / `paper-practice.js` 4）还没改名，`.rich-text` 的规则也没删。
   CSS 侧已把两侧写成**同值**（所以现在看不出差别）—— 但 **6.2 / 6.3 未完成**。
   落地口径见 `decisions.md` **A-41**。
2. **第 8 组的 JS 段**：统计数字滚动 / 火苗 / 进度带 / 台灯转场写目标底色 / 两档庆祝落点，
   **全部未做**（CSS 关键帧已在，但没有落点就等于没发生）。归属见 `decisions.md` **A-42**。

### 7.3 落地前必跑（`AGENTS.md` 每个 PR 必跑）

```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

### 7.4 走查

`design-notes/walkthrough-harness.md` 定义了执行器：请求序列捕获器拦在
`app.py` 的分发处（进程内，非外部代理），池副本 + 隔离注册表 + 独立端口，
**永不写真实池**。

---

## 8. 复现命令

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
git checkout feat/workbench-visual-language-v2
git log --oneline -15
openspec status --change "workbench-visual-language-v2" --json
openspec status --change "graph-node-visual-language" --json
python -m workbench.cli.main daemon start   # http://127.0.0.1:3081/
```

---

## 9. 这一轮沉淀下来的方法（换个人接手时值得知道）

1. **覆盖率矩阵**：135 条裁决逐条核 ✅/⚠️/❌，抓到**方向被写反**（A-1 涟漪）、
   **凭空蒸发**（5.2b 进度与成就）、**违反现行 spec**（章节透镜计数）。
   没有这张矩阵，这三条会一路带进实现。
2. **逐值 grep + 语义追问**：抓到三族 token 并存（A-9/A-13）、同名两值（A-21）、
   **取值相同但语义不同**（A-32 的 `--ink-on-warm`）。**逐值比对只能发现第一层，
   必须再问一句「它在那个语境里说的是不是这个东西」。**
3. **用现成实现当参照，而不是从零学**：Obsidian 的节点参数是从**本机安装包 `app.js` 源码**
   挖出来的；而仓库里 `frontend/editable-graph` 那份参照实现**自己就不是 faithful 克隆**
   （双层 + 描边 + 阴影）—— 「塑料感」的来源正在于此。
4. **agent 的自检可能验证错了对象**：它用本地 http 服务自检，就漏掉了 `file://` 下
   Chrome 禁外链 SVG 导致图标全丢 —— 而用户是**双击打开**的。
5. **空回报要信盘不信话**：D-03 跑满 26 次工具调用、847K token，只落 11 行。
   每次交接都核 `wc -l` + `tail`，是这一轮没有丢东西的原因。
