# IMPL-GRP13 — 边界护栏 + 算法冻结门禁（tasks.md 第 13 组 + 第 14 组）

> 派发单元：**tasks.md 第 13 组（13.1–13.6）+ 第 14 组（14.1–14.6）**。
> 这是本变更**最后**一个派发单元，也是**门禁**。
> 依赖：**第 1–12 组全部落地**。
> 下游：无（本组产出最终判定）。

## 1. 目标

两件事合在一册，因为它们是**同一次审计的两个半边**：

**第 14 组（可执行门禁）**：用 `tools/graph-layout-diff.js` 证明
「**同一输入 + 同一初值 + 同一迭代预算 ⇒ 收敛坐标 diff 严格为 0**」（SI-0），
并把证据入库。

**第 13 组（边界护栏）**：逐项复核 D-13.1 的 **14 条冻结项**与 D-13.2 的 **6 条允许改**，
确认 `git diff` 里**每一处改动**都能归进那 6 条之一。

## 2. 产物路径清单

| 路径 | 产物 |
|---|---|
| `tools/graph-baseline/EVIDENCE.md` | 追加「改造后」一节：复跑命令与**原样输出**、新 sha256、坐标 diff = 0 的结论、以及**为什么 sha256 变了**（第 5 组只改了绘制辅助函数）（14.4） |
| `tools/graph-baseline/baseline.json` | **只读**（见坑 1：**绝不许** `--capture` 覆盖它） |
| `tools/graph-layout-diff.js` | **只读**（已由主线 W3f 落地并验证；见坑 2） |
| `openspec/changes/graph-node-visual-language/briefs/` | 本组的审计报告（新建；文件名自定，在 IMPLEMENTATION-LOG.md 登记） |
| `docs/audits/` | 若需要（13.4 的归类清单可放这里） |

**不得改**：任何产品代码（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）。
**不得改**：本 change 的 `proposal.md` / `design.md` / `tasks.md` / `acceptance.md` / `specs/`
（主会话统一维护）——发现问题**写进报告**。

## 3. 文件所有权

- **独占**：`tools/graph-baseline/EVIDENCE.md`（追加）、本组新建的审计报告。
- **只读、绝不改**：`tools/graph-layout-diff.js`、`tools/graph-baseline/baseline.json`。
- **共享，必须串行**：**无**（本组不改产品代码）⇒
  **本组在第 1–12 组全部落地后跑**；可与第 11 组（第 11 组走查）**并行**，
  但两份报告的「发现的问题」要合并给主会话。
- **下游**：主会话（最终判定）。

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
   （第 10 组已按 D-12.1 改名成 `--graph-*`。）
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。
   ⇒ **本组要专门核实**：第 10 组的改名**没有碰**冻结块（`:336-407`）。

## 5. 验收标准（可机械判定）

1. **SI-0 主判据**：
   ```
   node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
   ```
   ⇒ `total differences: 0`、`coordinate diffs: 0`、`seed diffs: 0`、`id set diffs: 0`、
   **退出码 0**。**输出原样贴进报告与 EVIDENCE.md。**
2. **`tools/graph-baseline/baseline.json` 未被覆盖**：
   `git diff --stat tools/graph-baseline/baseline.json` ⇒ **空**，
   且其 sha256 仍为 `8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc`。
3. **13.1 的物理与布局护栏**（逐条给证据）：
   - `git diff --stat workbench/server/static/graph-physics-worker.js` ⇒ **零改动**；
   - `graph-physics-core.js` 的改动**只有** `edgeStyle()` 的线宽 / 透明度两行
     （第 5 组 5.2）与端点相关注释（5.1）；
   - `sizeFor()`（当前 `graph-physics-core.js:60-61`）⇒ **零改动**；
   - `labelWidth()`（`:83-85`）、`footprint()`（`:93-101`）⇒ **零改动**。
4. **13.2 的数据与语义护栏**：
   `NEIGHBOR_WEIGHT`（当前 `:32`）、`baseGapForStrength()`（`:68`）、
   `scoreFor()`（`:1463-1470`）、`stateAttention()`（`:64`）⇒ **零改动**。
5. **13.3 的 DOM 与交互护栏**：
   - 节点 id 与顺序不变（对照第 11 组的 SI-1 证据）；
   - `graphApplyVisibility()`（当前 `workbench.js:2154-2177`）的**判定逻辑**零改动；
   - `aria-label` 仍在节点上（当前 `workbench.js:2048`）。
6. **13.4 的六条允许改**：把 `git diff` 的**每一处**改动归类到 D-13.2 的 6 条之一；
   ⇒ **归不进去的任何一处**都要么**回退**、要么**先补 OpenSpec**。
   产出一张**逐条归类表**（文件 → 行 → 归入哪条 → 依据 design.md 的哪一节）。
7. **13.5 的边界**：`pool/` / `pipeline/` / `workbench/data/` /
   `workbench.css:4-46`（全站 token 块）**零改动**；图谱区段外的页面**零 diff**。
8. **冻结块未被破坏**：`git diff workbench.css` 中 `body:has(#layout[data-page="graph"])` 块
   （当前 `:336-407`）⇒ **零改动**。
9. **EVIDENCE.md 已追加「改造后」一节**：命令 + 原样输出 + 新 sha256 +
   「为什么 sha256 变了（只改了绘制辅助函数）」+ 「坐标 diff 仍为 0」的结论。
10. **失败即回退的路径已就绪**（14.5）：若 diff ≠ 0 ⇒ **立刻**按 `git diff` 逐行归类，
    **回退**越界的那一处并重跑 ⇒ **不得**用「差异很小」「四舍五入」解释掉。
11. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **绝不许 `--capture` 覆盖基线**（这是本组最容易犯、代价最大的错）。
   `tools/graph-baseline/README.md` 的「越界告警」写着：任何对
   `graph-physics-core.js` / `graph-physics.js` 的改动都要「先重跑 `--capture`」，
   并把差异写进 EVIDENCE.md。
   **但本组恰恰不能这么做**：
   - 第 5 组**按设计必须**改 `graph-physics-core.js` 的 `edgeStyle()`（design.md D-7.2），
     所以 sha256 **一定会变**（实测：变成 `38225398…`）；
   - 而**基线必须保持「改造前」的那份**（它就是「改造前坐标」的证据）。
   ⇒ **正确的口径**（已在 `/tmp` 的**隔离副本**上实测确认）：
     **sha256 变了 + 坐标 diff 仍为 0 ⇒ 判据成立**。
     在 `/tmp` 里只改 `edgeStyle()` 的两行 + 把 `NODE_FACE_INSET` 改成 `0`：
     `coordinate diffs: 0`、`seed diffs: 0`、`id set diffs: 0`、
     `total differences: 0`、退出码 **0**，
     **同时**工具打出 `*** WARNING: graph-physics-core.js has changed since this
     baseline was captured.`
   ⇒ **判据是「坐标 diff = 0」，不是「文件哈希不变」**。
   ⇒ 本组**不许**因为看到那个 WARNING 就去重跑 `--capture`。
   ⇒ 本组**不许**为了让警告消失而改基线或改工具。
   ⇒ 报告里必须写清这条口径（**第 11 组的报告也会引用它**）。
2. **工具与基线是主线的 W3f 落的**（`tools/graph-layout-diff.js` + `tools/graph-baseline/`）。
   ⇒ 本组**只读**它们；**不许**改工具来「让它过」。
   ⇒ 工具的量化口径（6 位小数、码位序排序、`toFixed(6)` 字符串全等）**不许**放松。
3. **「物理核心零 diff」不能当门禁**（W3f 的发现①，已实测确认）。
   `graph-physics-core.js` 里**混着四段纯绘制代码**：
   `edgeStyle()`（当前 `:1326`）、`NODE_FACE_INSET`（`:1343`）、
   `endpointRadius()`（`:1345`）、`edgePath()`（`:1349`）。
   ⇒ 「物理核心零 diff」会与第 5 组**正面打架** ⇒ 门禁必须落在**坐标**上，不是文件上。
   ⇒ 报告里要把这条写成**口径**，让后续任何人都不会再拿文件哈希当门禁。
4. **两处 `localeCompare` 的跨机器确定性隐患**（W3f 的发现②，已实测确认）：
   `graph-physics-core.js:613` 与 `:664`。
   ⇒ 布局路径里的排序**依赖 locale collation** ⇒ 换一台 ICU 数据不同的机器，
   坐标**可能**不一致。
   ⇒ 本组**只登记**这条隐患（写进 EVIDENCE.md / 报告），
   **不许**在本组改它（改它会动算法 ⇒ 越界）。
   ⇒ 工具的基线用**定宽 ASCII id**（`c01n00`…`c12n07`）⇒ collation 与码位序在该 id 集上一致
   ⇒ 基线本身可复现。**这一条必须写进报告**，否则下次有人换机器跑会误判。
5. **浏览器端每帧迭代步数随节点数变**（W3f 的发现③，已实测确认）：
   `graph-physics.js:284` `count: state.nodes.length > 120 ? 3 : 1`。
   ⇒ 「同一迭代预算」在浏览器端**不是固定值**（>120 节点时每帧走 3 步）。
   ⇒ 所以 **SI-0 的判据必须跑在 Node 侧**（固定 600 tick 预算，`tools/graph-layout-diff.js`），
   **不能**用浏览器端跑出来的坐标比。
   ⇒ 登记这条口径。
6. **`--diff` 的退出码语义**：0 = diff 恰为 0；1 = 非 0；2 = 用法/IO 错误或**本次没收敛**。
   ⇒ 「没收敛」也是**红**（退出码 2），不是「跳过」。
7. **13.4 的归类表要逐行**：不许写「整体属于绘制层」这种概括；
   ⇒ 每处改动指到**具体的 design.md 节号**（D-1 / D-3 / D-5 / D-6 / D-7 / D-8 / D-9 / D-10 / D-11 / D-12）。
8. **13.1 说「`graph-physics-core.js` 的改动只有 `edgeStyle()` 的两行与端点相关注释」**——
   但第 5 组 5.1 允许处理 `NODE_FACE_INSET` / `endpointRadius()`（可能**不止注释**）。
   ⇒ 报告里要给出**逐项**说明：这两处到底是「注释」还是「代码改动」，
   以及若改了代码，它归进 D-13.2 的哪一条（端点落点 ⇒ 第 5 条「边的绘制」）。

## 7. 诚实汇报要求

- 每一项判据都要贴**命令与原样输出**。**不许**只写结论。
- **必须**贴 `--diff` 的**完整输出**（含 `*** WARNING: …` 那一段）。
- **必须**报告 `git diff --stat tools/graph-baseline/baseline.json` ⇒ 空，
  并给出 baseline.json 的 sha256（应是 `8c1b7639…`）。
- **必须**给出 13.4 的**逐处归类表**。
- **必须**报告坑 1 / 3 / 4 / 5 的口径结论（写进 EVIDENCE.md，让口径**留在仓库里**）。
- 若 diff ≠ 0：**立刻回退**越界改动并重跑；**不许**放宽容差；**不许**改工具。
- **不许**改产品代码来让门禁过。
- **不许**改 `acceptance.md` / `tasks.md` / `design.md`（主会话维护）——
  要改判据就写进报告提请主会话。
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
