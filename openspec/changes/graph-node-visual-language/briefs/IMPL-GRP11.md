# IMPL-GRP11 — 验收走查（tasks.md 第 11 组）

> 派发单元：**tasks.md 第 11 组**（11.1–11.15）。
> 依赖：**第 1–10 组全部落地**（本组是验收，不改产品代码）。
> 下游：本组的产出是第 13 组门禁复核的输入。

## 1. 目标

按 `acceptance.md` 逐条走查，产出**可复现的证据**：

- §0.1 底线守卫 **G-1…G-5**（请求序列 / 持久化 / 学习投影 / 复习建议 / 无新增学习事实）；
- §0.2 结构不变量 **SI-0…SI-5**（算法冻结 / 节点集合 / 边集合 / 收敛确定性 / 投影语义 / 交互行为）；
- §0.3 允许变化区 **AV-1…AV-4**（节点 / 标签 / 图例 / 底噪）的判据 + 差异像素 ⊆ 四区遮罩；
- §1 对照截图 **S-L1…S-L8**（亮色 8 张）与 **S-N1…S-N6**（夜纸 6 张）；
- §2 关键帧 **M-1…M-6**；
- §3 交互清单 7 小节；
- §4 通过标准逐条判定。

**本组原则上不改产品代码**——发现问题就**报告**，由对应组修。

## 2. 产物路径清单

| 路径 | 产物 |
|---|---|
| `openspec/changes/graph-node-visual-language/briefs/` | 本组的走查证据报告（新建，文件名自定但要在 IMPLEMENTATION-LOG.md 里登记） |
| `docs/audits/` | 离线复算结果（11.14 的「屏幕占用 / 标签可见数 / 直径」表） |
| `tmp/`（不入库） | 截图、帧序列、请求序列原始产物 |

**不得改**：`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`。
**不得改**：本 change 的 `proposal.md` / `design.md` / `tasks.md` / `acceptance.md` / `specs/`
（主会话统一维护）——发现问题**写进报告**，不要自己改。

## 3. 文件所有权

- **独占**：本组新建的证据文件。
- **共享，必须串行**：**无产品文件**（本组不改产品代码）⇒
  **本组可以在第 1–10 组全部落地后，与第 12 组（文档）并行**。
- **依赖**：`tools/walkthrough/`（主线的走查执行器，**只读、不改**）：
  `launch.py`（池副本 + 隔离注册表 + 独立端口）、`recorder.py`（请求序列）、
  `shots.py`（截图 + 像素判定）、`frames.py`（M-1…M-10 分镜条）、`probe.py`（浏览器探针）、
  `run.py`（三段编排）、`seed.py`（播种子）。详见 `tools/walkthrough/README.md`。

## 4. 不可动的红线（逐字照抄，每组都要带上）

1. **不动图谱的算法**：力模型 / 迭代 / 收敛判据 / 阻尼 / 引力斥力 / 碰撞分离 / 布局种子 /
   邻接与边集合 / 边类型与权重 / 筛选语义 / 投影语义 / 指标计算 / DOM 节点身份与顺序 /
   拖拽与聚焦的行为语义 —— **一条都不许改**。
2. **只许改绘制**：节点形状与颜色、**绘制**半径（与物理半径解耦）、标签绘制与位置、
   边的绘制、缩放补偿。
3. **可执行判据（SI-0）**：同一输入 + 同一初值 + 同一迭代预算 ⇒
   **收敛坐标集合 diff 必须严格为 0**。**diff ≠ 0 即回滚。**
4. **不要动图谱的 12 个裸名**（`--paper` / `--ink` / `--hair` / `--blue` / `--yellow` / `--red` /
   `--shadow` / `--graphite` / `--green` / `--blueSoft` / `--yellowSoft` / `--redSoft`）——
   主线的新 token 层**已经和它们零同名**（`decisions.md` **A-8**），别再引入同名的。
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 5. 验收标准（可机械判定）

1. **§0.1 G-1…G-5 全绿**：在池副本 + 隔离注册表 + 独立端口上脚本化走一遍图谱页
   （进页 → 切投影 → 搜索 → 筛选 → 选中节点 → 拖拽 → 缩放 → Fit），
   记录服务端收到的**请求方法 + 路径 + 载荷键集合**，改造前后各跑一次并 diff ⇒ **逐条相同**；
   `problem_attempts` / `feedback_events` / `practice_runs` 的行数与关键列 ⇒ **逐行相同**；
   受影响知识点 / 题目的当前状态与调度行 ⇒ **完全相同**；
   到期项集合与弱项排序 ⇒ **完全相同**；池 schema ⇒ **零变更**。
2. **§0.2 SI-0**：`node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
3. **§0.2 SI-1**：节点 id 集合（DOM `.node-wrap[data-kp-id]` 与后端节点清单）⇒ 改造前后**完全相同**。
4. **§0.2 SI-2**：边四元组 `(source, target, type, direction)` 全集 ⇒ **完全相同**。
5. **§0.2 SI-3**：清空 `lk_graph_layout_v1_<workspace>` 后**重跑两次**从零求解
   ⇒ 两次坐标**逐节点相同**（允许 ≤0.1px 的存储取整误差）。
6. **§0.2 SI-4**：四个投影都还在、含义不互换；同一节点同一投影量值相同；
   量值 → 视觉映射**单调**；圆心数字按投影决定。
7. **§0.2 SI-5**：搜索 / 筛选 / 缩放 / 平移 / Fit / 拖拽 / 聚焦 / 聚拢 / 看板
   ⇒ 每个交互结果与改造前一致；**未新增**任何交互态；
   筛选**只改成员、不改外观**；淡化强度变了但**谁被强调没变**。
8. **§0.3 AV-1…AV-4 判据逐条成立**，且**差异像素 ⊆ 四区包围盒并集**；
   **遮罩之外任何一个差异像素 ⇒ FAIL**。
9. **§1 截图**：亮色 S-L1…S-L8、夜纸 S-N1…S-N6，同一视口 **1440×900**、同一数据状态、同一滚动位置。
10. **§2 帧序列**：M-1…M-6，各出一条分镜条 + 一张 `prefers-reduced-motion` 降级对照帧。
11. **§3 交互清单 7 小节全部勾选**，或未勾选项**逐条列出**并说明为何可接受。
12. **§1.3 的前置固定**：`deviceScaleFactor = 1`、浏览器缩放 100%、
    WebGL 固定 flag（`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`）、
    `prefers-reduced-motion: reduce`、等 `document.fonts.ready`、
    两次都用**全新浏览器上下文**、`window.scrollTo(0, 0)` 并断言、导航前清缓存。
    ⇒ **先自证基线可复现**（连跑**两次改造前**基线截图并互比）；
    若基线自身不可复现 ⇒ 按 A-14 的顺序登记为**待裁决项**，**不**默默放宽标准。
13. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **「亮色逐像素不变」这条门禁对本变更不适用**（design.md D-12.3 / **A-12**）。
   v2 的 `acceptance.md` G-5 是**否定式断言**（「图谱页未被本变更触碰」），
   它**只对 v2 成立**；本变更存在的目的就是重画节点 ⇒ 逐像素相同**物理上不可能**。
   ⇒ 本变更的判据是「**结构不变量 + 算法冻结**」+「差异像素 ⊆ 四个允许变化区」。
   ⇒ **不许**把 v2 的 G-5 抄进本组的报告当门禁。
   ⇒ 反过来：**旧的**基线截图 `tmp/frontend-audit/10-baseline-graph.png`
   **退役**为「改造前参考」，**不再**是「必须逐像素一致」的判定基准。
2. **底噪画布是**已知差异区**（design.md D-12.3 代价段 / R-6）：
   第 7 组把底噪改成半分辨率预渲染 ⇒ 底噪像素**必然**变化。
   ⇒ 遮罩必须把 tide 画布整块列为差异区，否则会误判 FAIL。
   ⇒ 节点挖洞的柔化（半分辨率）也要在报告里点名。
3. **走查环境必须是池副本 + 隔离注册表 + 独立端口**（acceptance.md §5）。
   ⇒ **永不写真实池**。用 `tools/walkthrough/launch.py` 起环境。
4. **「基线自身不可复现」是一个合法结论**（acceptance.md §1.3）：
   先连跑**两次改造前**基线截图并互比；不可复现 ⇒ 登记为**待裁决项**，
   **不许**默默放宽标准。
5. **相机与底噪是不可比源**（graph-isolation.md §6 的三条冻结）：
   tide 的时间驱动、Worker 的迭代、`localStorage` 种子。
   ⇒ 必须按 §1.3 固定；且 `deviceScaleFactor` 与 dpr 影响 WebGL backing store 与 tide 分辨率。
6. **diff 工具的 sha256 告警**（第 5 组改过 `graph-physics-core.js` 之后）：
   `--diff` 会打印 `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
   ⇒ **这是预期的**（第 5 组只改了绘制辅助函数）。
   ⇒ 判据是**坐标 diff = 0**，不是「文件哈希不变」。
   ⇒ 本组**不许**因为这个告警就重跑 `--capture` 覆盖基线（那会毁掉「改造前」的证据）。
   ⇒ 在报告里明确写出这条口径。
7. **11.14 的离线复算要照抄三段逻辑**（tasks.md 明写）：
   `workbench.js:806-852` 的标题截断（当前 `:1883-1927`）、
   `:854-901` 的 `graphBuild`（当前 `:1929-…`）、
   `:1203-1229` 的 `graphFit`（当前 `:2278-2301`），
   喂真实 `graph_model` 数据 ⇒ 产出「屏幕占用 / 标签可见数 / 直径」表，
   与 design.md D-1 的表**比对**，偏差 >10% ⇒ 回看设计（R-5）。
   ⇒ **行号已变**，按符号名重新定位。
8. **`acceptance.md` 的截图清单 S-L1 的「直径 10–26px」等数字是改造目标值**，
   不是现状值 ⇒ 报告里要区分「目标」与「实测」。
9. **本组不改产品代码**。发现问题 ⇒ 写进报告并指名由**哪个组**修。

## 7. 诚实汇报要求

- 每一项判据都要贴**命令与原样输出**，不许用「已验证」「看起来正常」这类描述。
- **未通过的项必须显式列出**（判据、实测、差在哪、指名由哪个组修）。
  ⇒ **不许**为了让 §4 通过标准全绿而放宽判据。
- **不许**改产品代码来让判据通过。
- **不许**改 `acceptance.md`（主会话维护）——要改判据就写进报告。
- **不许**跑 `--capture` 覆盖 `tools/graph-baseline/baseline.json`。
- 走查环境**必须**是池副本 + 独立端口 ⇒ 报告里给出启动命令与端口，证明没写真实池。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的：**停下来报告**，写清疑问与两个候选，**不许**硬做。
- 汇报里必须包含：改了/新建了哪些文件、每处对应 tasks.md 哪一条、验证命令与原样输出、
  以及**你发现但没改**的问题清单。

## 8. 验证

```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate graph-node-visual-language --strict
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
