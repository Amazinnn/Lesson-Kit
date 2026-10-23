# IMPL-G1 — 图谱 change 的任务书拆分（13 组 → 可派的任务书）+ SI-0 门禁口径复核

> 服务于 `openspec/changes/graph-node-visual-language/`（**图谱节点视觉重做**，126 任务 / 13 组）。
> **只新建 `openspec/changes/graph-node-visual-language/briefs/` 下的文件** +
> `openspec/changes/graph-node-visual-language/IMPLEMENTATION-LOG.md`（**新建**）。
> **绝不改产品代码。**

## 背景
图谱 change 已经**立好案**（`proposal.md` / `design.md` / `tasks.md` / `acceptance.md` /
两份 spec delta），但**一行实现都还没动**。主线的 `workbench.css` 与 `workbench.js`
还在被别的 agent 并行改 ⇒ **图谱的实现必须排队**，但**任务书可以现在备好**。

本任务：**把 126 条任务拆成 13 份可直接派出去的任务书**，并把 **SI-0 门禁**的口径钉死。

## 一、13 份任务书（每组一份）

`openspec/changes/graph-node-visual-language/tasks.md` 的 14 组，按**文件所有权**切成互不重叠的批次。
**拆分前先自己核对每组实际要改哪些文件**（`grep` 出来，不要照抄旧清单）——
已知的大致分布：组 1 / 6 偏 `workbench.css` + `workbench.js`；组 2 / 5 / 9 / 11 / 13 偏
`graph-physics*.js` / `graph-renderer.js`；组 3 / 4 偏 `pages.py` / `workbench.js`；
组 8 偏 `graph-renderer.js`；组 10 / 12 偏 `workbench.css` / `workbench.js`；组 14 是取证与门禁。

每份任务书必须含：
1. **目标**（这一组做完，产品里哪个可见变化）
2. **产物路径清单**（枚举到文件名）
3. **文件所有权**（这一组**只**改哪几个文件；并写明**与哪些组冲突**、必须串行的关系）
4. **不可动的红线**（见下）
5. **验收标准**（能机械判定的那种）
6. **已知坑**（至少一条来自 `design.md` / `acceptance.md` 的硬约束）
7. **诚实汇报要求**（拿不准就停下报告，**不许**硬做）

## 二、**不可动的红线**（每一份任务书都要抄进去）

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
   （`body:has(#layout[data-page="graph"])`）兼容 —— 冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 三、SI-0 门禁的口径复核（**本任务的重点**）

`tools/graph-layout-diff.js` + `tools/graph-baseline/` 已经落地（主线的 W3f 做的），
**基线已在**，可以**现在**跑一次确认它仍然有效：

```bash
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
# 必须：total differences: 0（96 节点坐标差 0 / seed 差 0 / id 集差 0）
```

⇒ 把这次实测的输出**写进** `openspec/changes/graph-node-visual-language/IMPLEMENTATION-LOG.md`，
作为「SI-0 门禁在图谱 change 开工前**仍然绿**」的证据（**基线锚点是
`graph-physics-core.js` 的 sha256**，不是 commit SHA —— 仓库在并行提交，HEAD 会动）。

⚠️ 同时把 **W3f 查出的三处「不该动但容易被误读」**写进任务书：
① `graph-physics-core.js` 里**混着四段纯绘制代码**（`edgeStyle()` / `NODE_FACE_INSET` /
   `endpointRadius()` / `edgePath()`）⇒ **「物理核心零 diff」不能当门禁**（会与第 5 组打架）——
   门禁要落在**坐标**上，不是**文件**上；
② 布局路径里有**两处 `localeCompare`**（`:613` / `:664`）⇒ 跨机器确定性隐患；
③ 浏览器每帧迭代步数**随节点数变**（`>120` 走 3 步）⇒「同一迭代预算」在浏览器端会漂。

## 四、硬约束
- **只新建** `openspec/changes/graph-node-visual-language/briefs/` 下的文件 与
  `openspec/changes/graph-node-visual-language/IMPLEMENTATION-LOG.md`。
- **绝不改** `workbench/` / `pool/` / `pipeline/` / `lessonkit.py`（**另有 agent 正在并行改**）。
- **不要**改图谱 change 的既有文件（`proposal.md` / `design.md` / `tasks.md` / `acceptance.md` /
  `specs/`）—— **主会话统一维护**；若发现它们内部有矛盾，**写进 IMPLEMENTATION-LOG 的待裁决段**，
  **不要**自己改。
- **不要**改主线的 `openspec/changes/workbench-visual-language-v2/` 下的任何文件。
- 图谱 change 的**设计权威**是 `design.md`（**D-13 的 14 项冻结 + 6 项只绘制的允许清单**）——
  任务书必须照它写，**不许**自创形态。

## 五、验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate graph-node-visual-language --strict
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```

## 六、落盘纪律与回报
- **13 份任务书 + 1 份日志**，**分多次 commit**（一次一个文件或一组同源文件），
  只 `git add openspec/changes/graph-node-visual-language/`，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**13 份任务书的清单**（组号 → 标题 → 独占文件 → 与哪些组串行）+
**SI-0 门禁的实测输出**（含基线锚点 sha256）+
**你在图谱 change 的既有文件里发现的矛盾（逐条）** + 待裁决项。
- 数字与事实一律以**当场跑出来的命令输出**与**当场读到的代码**为准。
