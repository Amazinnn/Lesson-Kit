# IMPLEMENTATION-LOG — graph-node-visual-language

> **本文件是图谱 change 的实现日志（新建）**。
> 记录每一波的产出、门禁实测结果、以及**待裁决项**。
> 纪律（承自主线）：**待裁决项必须显式登记**，不许靠时间戳、代码现状或个人猜测静默选边。
>
> **本波（第一波）只做两件事**：
> ① 把 126 条任务 / 14 组拆成 **13 份可派发的任务书**（`briefs/IMPL-GRP01..13.md`）；
> ② **复核 SI-0 门禁**，把实测输出写进本文件，**作为「图谱 change 开工前门禁仍然绿」的证据**。
>
> **本波没有改任何产品代码**（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py` 一行未动），
> 也没有改本 change 的既有文件（`proposal.md` / `design.md` / `tasks.md` / `acceptance.md` / `specs/`）。

---

## 0. 一句话结论

| 项 | 结果 |
|---|---|
| 任务书 | **13 份**（`briefs/IMPL-GRP01.md` … `IMPL-GRP13.md`），覆盖 **126 条任务 / 14 组** |
| **SI-0 门禁（开工前）** | **绿**：`node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json` ⇒ **`total differences: 0`**，退出码 **0** |
| 基线锚点 | `workbench/server/static/graph-physics-core.js` 的 **sha256 = `c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997`**（与 `tools/graph-baseline/baseline.json` 记录**一致**） |
| 基线文件指纹 | `tools/graph-baseline/baseline.json` sha256 = `8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc` |
| 产品代码改动 | **零** |
| 发现的既有文件矛盾 | **9 条**（见 §4），全部**未自行修改**，已登记待裁决 |
| 仓库级检查 | 6 条全绿（见 §3） |

---

## 1. SI-0 门禁复核（开工前的实测证据）

### 1.1 命令与原样输出

工作目录 = 仓库根目录；时点 = 2026-10-22（`git rev-parse HEAD` = `6eb81ae9`，
仓库在并行提交，**HEAD 会动** ⇒ 锚点用**文件 sha256**，不用 commit SHA）。

```console
$ node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
=== graph-layout-diff (diff) ===

[quantization — the comparison contract]
  decimals        : 6
  sort key        : nodeId (code-unit ascending)
  comparison      : exact string equality of toFixed(decimals) (no epsilon anywhere)

[input]
  graph           : synthetic-deterministic-v1
  nodes / edges   : 96 / 338  (12 chapters x 8)
  view / gravity  : structure / 85
  stage           : 1800 x 1550
  iteration budget: 600 ticks (settled at tick 268, via safety-valve)

[source]
  module          : workbench/server/static/graph-physics-core.js
  sha256          : c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997
[baseline]
  path            : tools/graph-baseline/baseline.json
  module sha256   : c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997
  budget / settle : 600 / 268

[node id set]
  baseline ids    : 96
  current ids     : 96
  only in baseline: (none)
  only in current : (none)


[converged coordinates — SI-0 target]
  differences     : 0


[initial coordinates (seed) — the 'same initial condition' half]
  differences     : 0

[summary]
  compared nodes  : 96
  coordinate diffs: 0
  seed diffs      : 0
  id set diffs    : 0
  total differences: 0

RESULT: PASS — converged coordinate diff = 0 (SI-0 green)
EXIT_CODE=0
```

**没有出现** `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
⇒ 当前工作区的 `graph-physics-core.js` 与基线记录的**同一份字节**（sha256 逐字相同，
已用 `sha256sum` 独立核对，见 §1.2）⇒ **基线仍然有效，SI-0 门禁仍然绿**。

### 1.2 锚点独立核对

```console
$ sha256sum workbench/server/static/graph-physics-core.js tools/graph-baseline/baseline.json
c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997  workbench/server/static/graph-physics-core.js
8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc  tools/graph-baseline/baseline.json
```

| 项 | 值 | 与基线记录一致？ |
|---|---|---|
| `graph-physics-core.js` sha256 | `c4e9e8e5…e59997` | **是**（`baseline.json` 的 `source.sha256` 同值） |
| `baseline.json` sha256 | `8c1b7639…6cc6cc` | **是**（`tools/graph-baseline/README.md` 记的同值） |

> **锚点是文件 sha256，不是 commit SHA**：仓库此刻有多个 agent 在并行提交
> （`git log` 显示 `workbench.css` / `workbench.js` / `pages.py` 都在动），
> `HEAD` 会随时移动 ⇒ 用 commit SHA 当锚点会失效。

### 1.3 「门禁在开工前绿」这句话的**边界**（必须写清，否则会被误用）

1. **绿的是「坐标 diff = 0」**，不是「文件哈希不变」。
2. 第 5 组（关系线）**按设计必须**改 `graph-physics-core.js` 的 `edgeStyle()`
   （design.md D-7.2）⇒ **sha256 一定会变** ⇒ 工具**必然**打出
   `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
   ⇒ **这个 WARNING 是预期的，不是失败**。
   我在 `/tmp` 的**隔离副本**上实测确认过（**未碰仓库任何文件**）：

   | 只改 `edgeStyle()` 两行 + `NODE_FACE_INSET` 改 0 后的实测 | 值 |
   |---|---|
   | `coordinate diffs` | **0** |
   | `seed diffs` | **0** |
   | `id set diffs` | **0** |
   | `total differences` | **0** |
   | 退出码 | **0** |
   | 新的 core sha256 | `38225398b9cfde4733b4abc0a97b7b4aef9194ed79629e6bb1f98237f2c9fe0f`（**变了**） |
   | 工具输出 | 打出 `*** WARNING: …` |

   ⇒ **判据是坐标，不是文件哈希。**
   ⇒ **绝不许**为了让 WARNING 消失而 `--capture` 覆盖基线
   ——那会毁掉「改造前坐标」这份证据本身。
3. 「物理核心零 diff」**不能**当门禁（会与第 5 组正面打架）—— 见 §2.1。

---

## 2. W3f 查出的三处「不该动但容易被误读」（实测复核后写进任务书）

### 2.1 ① `graph-physics-core.js` 里**混着四段纯绘制代码**

实测位置（2026-10-22）：

| 段 | 位置 | 性质 | 消费点 |
|---|---|---|---|
| `edgeStyle()` | `graph-physics-core.js:1326-1329` | **纯绘制**（线宽 / alpha） | `graph-renderer.js:275` |
| `NODE_FACE_INSET` | `:1343` | **纯绘制**（与 CSS `.node-face { inset: 7% }` coupled） | `endpointRadius()` |
| `endpointRadius()` | `:1345-1347` | **纯绘制**（端点落点） | `edgePath()` |
| `edgePath()` | `:1349-…` | **纯绘制**（路径几何） | `graph-renderer.js:179` |

⇒ **「物理核心零 diff」不能当门禁**：第 5 组按 D-7.2 **必须**改 `edgeStyle()`。
⇒ 门禁必须落在**坐标**上（§1.3 已用隔离副本实测确认）。
⇒ 已写进 `IMPL-GRP05.md`（坑 1）与 `IMPL-GRP13.md`（坑 1 / 坑 3）。

### 2.2 ② 布局路径里有**两处 `localeCompare`**

实测：`graph-physics-core.js:613` 与 `:664`。
⇒ 排序**依赖 locale collation** ⇒ 换一台 ICU 数据不同的机器，坐标**可能**不一致。
⇒ **登记**为跨机器确定性隐患；**本轮不改**（改它 = 动算法 = 越界）。
⇒ 基线之所以可复现：工具用**定宽 ASCII id**（`c01n00`…`c12n07`），
collation 与码位序在该 id 集上一致。
⇒ 已写进 `IMPL-GRP13.md`（坑 4）。

### 2.3 ③ 浏览器端**每帧迭代步数随节点数变**

实测：`graph-physics.js:284` `count: state.nodes.length > 120 ? 3 : 1`。
⇒ 「同一迭代预算」在浏览器端**不是固定值**（>120 节点时每帧走 3 步）。
⇒ **SI-0 必须在 Node 侧跑**（固定 600 tick 预算，`tools/graph-layout-diff.js`），
**不能**用浏览器端跑出来的坐标比。
⇒ 已写进 `IMPL-GRP13.md`（坑 5）。

---

## 3. 仓库级检查（第一波实测）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python -m pytest tests -q` | 0 | 见 §6（本波实测） |
| `python -m compileall -q lessonkit.py workbench pipeline pool tests` | 0 | 无输出（全部通过） |
| `openspec validate --specs --strict` | 0 | `Totals: 19 passed, 0 failed (19 items)` |
| `python lessonkit.py guard extract-problems --course dmath --chapter ch06` | 0 | `Result: PASS` |
| `openspec validate graph-node-visual-language --strict` | 0 | `Change 'graph-node-visual-language' is valid` |
| `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json` | **0** | **`total differences: 0`（SI-0 green）** |

---

## 4. 在图谱 change 既有文件里发现的矛盾（**逐条登记，未自行修改**）

> 纪律来源：AGENTS.md「Contract Reconciliation」——
> **发现既有契约冲突时先显式登记/解决，不得靠时间戳、代码现状或个人猜测选边**；
> 且本任务书明确：**图谱 change 的既有文件由主会话统一维护，本波不改**。

### C-01（高）`tasks.md` 第 14 组要求「按 dmath/ch06 的真实图谱模型」比对，但已落地的工具用的是**合成图谱**

- `tasks.md:236-244`（14.1 / 14.2）写：「取指定章节（**默认 dmath/ch06**）的图谱模型」、
  「清空 `lk_graph_layout_v1_<workspace>`，从零求解」、「等收敛（`#graph-solver-state` 不再带
  `.solving` 且 DOM 静止签名连续 N 次不变）」。
- `acceptance.md:62`（SI-0）同样写「取同一章节（**dmath/ch06**）的图谱模型」。
- **实际**：`tools/graph-layout-diff.js` 用的是**合成确定性图谱**
  （`synthetic-deterministic-v1`，12 章 × 8 点 = 96 节点 / 338 边），
  **不读池、不用浏览器、不用 localStorage、不看 DOM 收敛**；
  `tools/graph-baseline/README.md` 明确解释了为什么（真实池是活的，基线会漂）。
- **影响**：SI-0 的**判据内核**（坐标 diff = 0）**成立且已实测为绿**；
  但**执行方式**与 `tasks.md` / `acceptance.md` 的字面描述**不一致**。
- **建议裁决**：把 `tasks.md` 14.1/14.2 与 `acceptance.md` SI-0 的「dmath/ch06 + 浏览器 + DOM 收敛」
  改写为「**以 `tools/graph-layout-diff.js` 的合成基线为准**；若另需真实课程基线，
  **另立一份**（`tools/graph-baseline/README.md` 已写明「届时另立一份，不覆盖本份」）」。
  ⇒ **未改任何文件**。

### C-02（高）`tasks.md` 10.1 的「区段外引用 0 次」验证命令**现在必然跑出非 0**

- `design.md:1113` / `tasks.md:181` 给的命令是：
  `awk 'NR<1497||NR>1884' workbench.css | grep -cE 'var\(--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\b'`
- **实测**（当前 `workbench.css`）：用该**原版**命令 ⇒ **170**（不是 0）。
- 两个原因叠加：
  1. **行号边界过时**：图谱区段现在在 `:3566-3954`，不是 `:1497-1884`
     （主线 v2 改造把 `workbench.css` 从约 1900 行撑到 3989 行）；
  2. **正则过宽**：`\b` 会把主线的 `--ink-strong` / `--ink-muted` / `--ink-faint` 一并匹配
     （它们**不是**图谱的 12 个裸名）。
- **修正版实测**（严格正则 + 当前边界）⇒ **0**：
  ```
  awk 'NR<3566||NR>3954' workbench.css \
    | grep -cE 'var\(--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\)'
  → 0
  ```
  （图谱区段内 `var(--NAME)` 命中 **33** 处，全部在区段内。）
- **影响**：第 10 组若照抄原命令验收，会**误判 FAIL**；第 13 组若照抄原命令复核，会**误判越界**。
- **建议裁决**：把两处命令改成修正版（行号 + 严格正则）。
  ⇒ 已把修正版写进 `IMPL-GRP10.md`（§5 第 3 条 / 坑 1）与 `IMPL-GRP13.md`。
  ⇒ **未改任何文件**。

### C-03（高）`tasks.md` 12.3 引用的 v2 场景**标题与行号都不对**

- `tasks.md:212` / `proposal.md:259` / `design.md:1190` 写：退役 v2 里的场景
  「**The knowledge graph page is unchanged**」，位置 `v2 specs/workbench-ui/spec.md:367-371`。
- **实测** `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`：
  - `:367-371` **不是**那个场景（那里是「The transition survives the content being replaced」）；
  - 真正的场景标题是「**This foundation leaves the knowledge graph page unchanged**」，在 **`:720`**；
  - 同一断言的**需求正文**在 **`:686-691`**
    （"This foundation SHALL leave the knowledge graph page's appearance unchanged"）。
- **影响**：照抄 `:367-371` 会退役**错的地方**；只删场景标题会**留下正文里那句矛盾的断言**。
- **建议裁决**：把引用改成 `:720`（场景）与 `:686-691`（正文），并要求**两处一起处理**。
  ⇒ 已写进 `IMPL-GRP12.md`（坑 2）。**未改任何文件**。

### C-04（中）`design.md` / `tasks.md` / `acceptance.md` 里的**行号锚点大面积过时**

设计文档写的行号取自**主线 v2 改造前**的文件。实测（2026-10-22）：

| 文档里的锚点 | 文档含义 | **实际位置** |
|---|---|---|
| `workbench.css:1497-1884` | 图谱 CSS 区段 | `:3566-3954` |
| `workbench.css:1505-1518` | 12 个裸名声明 | `:3574-3587`（`:root` 块 `:3574`） |
| `workbench.css:1643-1719` | 节点规则 | `:3712-3788` |
| `workbench.css:1780-1799` | 图例 | `:3849-3868` |
| `workbench.js:957-1053` | `graphCreateNodes()` | `:2032-2129` |
| `workbench.js:1055-1061` | `graphProjectionDisplay()` | `:2130-2136` |
| `workbench.js:1063-1075` | `graphUpdateNodeAppearance()` | `:2138-2150` |
| `workbench.js:1077` | `graphSyncScope()` | `:2152` |
| `workbench.js:1080-1105` | `graphApplyVisibility()` | `:2154-2177` |
| `workbench.js:1104-1107` | `graphApplyView()` | `:2179-2191` |
| `workbench.js:1203-1229` | `graphFit()` | `:2278-2301` |
| `workbench.js:1290-1294` | `LABEL_MIN_RADIUS_PX` / `labelScaleThreshold()` | `:2365-2369` |
| `workbench.js:1296-1325` | `graphPaintNodes()` | `:2371-2404` |
| `workbench.js:578` | `STATE_SHORT` | `:1653` |
| `workbench.js:806-817` | `graphTitleCut()` | `:1883-1893` |
| `workbench.js:854-901` | `graphBuild()` | `:1929-…` |
| `workbench.js:703` | 初始相机 | `:1778` |
| `workbench.js:1482-1660` | `graphTide*` | `:2554-2710` |
| `workbench.js:1885` | 缩放 +/- | `:2958-2971` |
| `pages.py:410-481` | `graph_page()` | `:661-731` |
| `pages.py:462-467` | 图例 5 项 | `:713-718` |

**仍然准确**（这些文件主线没动）：`graph-physics-core.js` 的
`:60-61` `sizeFor` / `:83-85` `labelWidth` / `:93-101` `footprint` /
`:1326-1329` `edgeStyle` / `:1343-1347` `NODE_FACE_INSET`+`endpointRadius` /
`:1349` `edgePath` / `:1463-1470` `scoreFor`；
`graph-renderer.js` 的 `:15-21` `EDGE_COLORS` / `:267` `stageScale`；
`graph-physics.js` 的 `:43-48` 布局种子。
（**例外**：`design.md` / `tasks.md` 说 `NEIGHBOR_WEIGHT` 在 `graph-physics-core.js:527`
—— 实测**声明在 `:32`**；`:527` 只是**使用点**。⇒ 见 C-05。）

- **影响**：照抄行号会改错地方。
- **处置**：**13 份任务书全部改用「符号名 + 当前实测行号」**，
  并在每份的「已知坑」里写明「行号锚点过时，按符号名重新 grep」。
  ⇒ **未改任何文件**（行号在 `design.md` / `tasks.md` / `acceptance.md` 里，属主会话维护）。

### C-05（中）`NEIGHBOR_WEIGHT` 的行号指向**使用点**而非**声明点**

- `design.md:1125` / `tasks.md:223` / `tasks.md:125` 写 `NEIGHBOR_WEIGHT` 在
  `graph-physics-core.js:527`。
- **实测**：**声明在 `:32`**；`:527` 是 `neighborIndex()` 里的**使用点**。
  ⇒ 照 `:527` 复核「零改动」会**验错位置**。
- **建议裁决**：把三处引用改成 `:32`（或改成「声明点，用 grep 定位」）。
  ⇒ 已写进 `IMPL-GRP13.md`（§5 第 4 条）。**未改任何文件**。

### C-06（中）`tasks.md` 8.4 / 8.5 与 `2.3` 的**归属重复**

- `tasks.md:160`（8.4）：删 `.node-satellite` 的 CSS 规则，「**DOM 已在第 2 组 2.3 删**」。
- `tasks.md:161`（8.5）：删 `.node-unit { display: none }` 与对应写入，**没写归属**。
- `tasks.md:82`（2.3）：`graphCreateNodes()` 改子层，**只说**删 `.metric-track` / `.status-ring`
  的 DOM 创建，**没说** `.node-satellite` / `.node-unit`。
- **实测**：`.node-satellite` 与 `.node-unit` 的 DOM 创建分别在
  `workbench.js:2061-2064` 与 `:2057-2059`（`.node-unit` 在 `:2057`，`.node-value` 在 `:2055`）。
- **影响**：8.4 假定第 2 组已删 `.node-satellite` DOM，但 2.3 没写这条 ⇒
  两组都以为对方做了 ⇒ **可能漏删**（留下一个永不显示的 `<span>`，无害但脏）。
- **建议裁决**：在 2.3 里补上「一并删 `.node-satellite` / `.node-unit` 的 DOM 创建」，
  或在 8.4 / 8.5 里改成「本组自己删 DOM」。
  ⇒ 已在 `IMPL-GRP08.md` 里按「8.4/8.5 由本组负责 DOM 与 CSS 两边」写，并请主会话定稿。
  **未改任何文件**。

### C-07（中）`design.md` D-3 的「结构投影度数」与代码里**两个不同的度数**

- `design.md:317` / `tasks.md:68` 的结构投影公式是 `clamp(5 + 2.2·√degree, 5, 13)`，
  并在 D-3 里说「结构投影用的是**原始度数**而非归一化 score，但归一化是度数的单调变换 ⇒ 两者仍同序」。
- **实测**：核心里有**两个**度数 map：
  - `degreeRaw`（`:1419-1424`）= **按边强度加权**的原始度；
  - `degreeCount`（`:1420-1426`）= **纯边数**。
  `scoreFor('structure')`（`:1465`）归一化的是 **`degreeRaw`**；
  而工作台现在显示的「结构投影圆心数字」用的是 `degreeCount`
  （`workbench.js:2132`）。
- **影响**：公式里的 `degree` 若取 `degreeCount`，就**与物理半径不同序**
  （物理半径来自 `sizeFor(scoreFor(...))` = `degreeRaw` 归一化）⇒
  违反 design.md D-3 自己写的「与物理半径单调同源」与 spec delta
  「The drawn radius SHALL be derived from the node's metric in the same order as the
  physical radius」。
- **建议裁决**：在 D-3 的公式旁注明 `degree` = **`state.degreeRaw`**（与 `scoreFor` 同源）。
  ⇒ 已在 `IMPL-GRP02.md`（坑 2）里按 `degreeRaw` 写，并请主会话定稿。**未改任何文件**。

### C-08（中）`importance` 投影的量在数据里**只有两个取值**，四档分档必然空两档

- `tasks.md:103`（3.7）：「用 dmath/ch06 的**真实 score 分布**确认 `.25/.5/.75` 四档**不空置**；
  若某档空置，改用分位数分档」。
- **实测**：`pool/dmath.db` 的 `knowledge_points.importance` 分布 =
  **`core` 17 / `supplementary` 14**（只有两类）；
  `workbench.js:1941` 把它映射成数值 **`0.55` 或 `1`** 两个值。
  ⇒ `scoreFor('importance')`（`:1467`）只产出 `{0.55, 1}` ⇒
  **橙阶四档里必然空两档**（`0.55` 落第 3 档、`1` 落第 4 档）。
- **影响**：3.7 的验收在 `importance` 投影上**天然不成立**；D-4 说的「重要性投影 = 橙阶 4 档」
  在当前数据下只用到 2 档。
- **建议裁决**：确认「四档是**色键的设计上限**，实际占用档数随数据而变；
  `importance` 投影当前只会占用 2 档」——把这一条**显式写进 acceptance.md 的 AV-1 ③**
  （否则验收会误判）。**改 `scoreFor` / `graphBuild` 的映射是越界（投影语义冻结），不许改。**
  ⇒ 已在 `IMPL-GRP03.md`（坑 1）里写明并要求报告。**未改任何文件**。

### C-09（低）`docs/PRODUCT-MANUAL.md` 与 `docs/ACTION-GRAPH.md` 里的图谱描述**还是 A-24 的旧形态**

- `docs/PRODUCT-MANUAL.md:164` 写「节点视觉语言**已定稿、尚未落地**」，
  `:166` 写「**同心圆节点**——淡色内核套一圈同色相的实色外环」，
  `:168` 写「圆心只有一个数字，即该知识点关联的正式题数，**四个投影下都是同一个数**」，
  `:170` 写「节点填充、**外环**、连线与标签」，`:174` 写「选中的节点**外环加粗变实**」。
- `docs/ACTION-GRAPH.md:29` 写「**同心圆节点形态**」。
- **最终形态**（A-28 / A-34）：**单层实心圆**、无描边无投影、**无外环**、
  圆心数字**按投影决定**（结构 / 状态无数字）、选中是**换色 + 1px 环 + 放大 + 标签提亮**。
- **影响**：这两份是**用户可见的正式文档**，与最终形态不符；
  `tasks.md` 12.4 / 12.6 覆盖了它们，但 12.6 写的是「**无变更**」——
  **动作集确实无变更，但既有条目的描述需要校正**。
- **建议裁决**：12.6 改成「动作集无变更；但把 `:29` 那条的「同心圆节点形态」
  按 A-28 校正为「单层实心圆」」。⇒ 已在 `IMPL-GRP12.md`（坑 3 / 坑 4）里写明。
  **未改任何文件**。

---

## 5. 任务书清单（13 份 / 覆盖 126 条任务 / 14 组）

| 任务书 | 覆盖 tasks.md | 独占文件 | 与哪些组串行 |
|---|---|---|---|
| `briefs/IMPL-GRP01.md` | **第 1 组**（1.1–1.10）屏幕空间缩放补偿 | `graph-physics.js` | 全部下游（2/4/5/6/9 依赖它） |
| `briefs/IMPL-GRP02.md` | **第 2 组**（2.1–2.9）节点形态与尺寸映射 | — | **1** →（3 / 6） |
| `briefs/IMPL-GRP03.md` | **第 3 组**（3.1–3.11）暖色板与四投影色键 | `pages.py` | **2** →（6 / 8） |
| `briefs/IMPL-GRP04.md` | **第 4 组**（4.1–4.10）标签系统与重叠让位 | — | **2** →（8 / 9） |
| `briefs/IMPL-GRP05.md` | **第 5 组**（5.1–5.8）关系线 | `graph-physics-core.js`、`graph-renderer.js` | **1**（要 `nodeScreenRadius`）→ **10**（要改 renderer） |
| `briefs/IMPL-GRP06.md` | **第 6 组**（6.1–6.9）选中 / 悬停 / 聚焦 | — | **3**（要色阶）→ **8** |
| `briefs/IMPL-GRP07.md` | **第 7 组**（7.1–7.7）底噪光斑 | `workbench.js` 的 `graphTide*` 段 | 文件级排队（与 1/2/3/4/5/6/8/9 同文件）；逻辑上独立 |
| `briefs/IMPL-GRP08.md` | **第 8 组**（8.1–8.11）死规则清理 | — | **2 / 3 / 4 / 6** 之后 |
| `briefs/IMPL-GRP09.md` | **第 9 组**（9.1–9.7）相机与 auto-fit | `docs/PRODUCT-MANUAL.md`（缩放段） | **3**（同改 `pages.py`）→ **12**（同改手册） |
| `briefs/IMPL-GRP10.md` | **第 10 组**（10.1–10.8）夜纸适配 | — | **3 / 5 / 8** 之后（CSS 侧最后一棒） |
| `briefs/IMPL-GRP11.md` | **第 11 组**（11.1–11.15）验收走查 | 新建的证据文件 | 全部实现组之后；可与 **12 / 13** 并行 |
| `briefs/IMPL-GRP12.md` | **第 12 组**（12.1–12.9）契约协调 | `docs/GLOSSARY.md`、`docs/PENDING-DEFINITIONS.md`、`docs/ACTION-GRAPH.md` | **9** 之后；12.2 / 12.3 被 A-10.2 阻塞 |
| `briefs/IMPL-GRP13.md` | **第 13 组 + 第 14 组**（13.1–13.6 / 14.1–14.6）边界护栏 + SI-0 门禁 | `tools/graph-baseline/EVIDENCE.md`（追加） | 全部实现组之后；可与 **11** 并行 |

### 5.1 推荐的派发顺序（**按文件冲突排的，不是按组号**）

```
第 1 组（GRP01，foundation）
   ↓
第 2 组（GRP02）→ 第 3 组（GRP03）→ 第 5 组（GRP05，独占 core+renderer）
   ↓
第 4 组（GRP04）→ 第 6 组（GRP06）→ 第 8 组（GRP08，清理最后一棒）
   ↓
第 9 组（GRP09）→ 第 10 组（GRP10，CSS 侧最后一棒）
   ↓
第 7 组（GRP07，tide：同文件，但函数区间独立，可与 9/10 并行准备）
   ↓
第 11 组（GRP11）‖ 第 12 组（GRP12）‖ 第 13 组（GRP13）   ← 可三路并行
```

> **两个硬约束**：
> ① `workbench.css` 与 `workbench.js` 是**共享热点文件** ⇒ 触及它们的组
> （1/2/3/4/5/6/7/8/9/10）**必须串行落地**（按上表顺序），
> 即使函数区间不重叠（同文件并行改必冲突）。
> ② **主线 v2 还在改 `workbench.css` / `workbench.js` / `pages.py`**
> ⇒ 图谱的实现**必须等主线落定后再动**（或每次开工前 rebase 并重新 grep 定位）。

---

## 6. 本波实测记录（第一波）

| 项 | 值 |
|---|---|
| 分支 / HEAD（时点） | `6eb81ae9`（**会动**） |
| 工作区产品代码 | **未改**（`git status` 只有主线 agent 的 `workbench/server/pages.py`、`paper-practice.js`、`practice-flow.js` 等改动，与本波无关） |
| 本波新建文件 | `briefs/IMPL-GRP01..13.md`（13 份）+ `IMPLEMENTATION-LOG.md`（本文件） |
| `openspec validate graph-node-visual-language --strict` | `Change 'graph-node-visual-language' is valid` |
| `openspec validate --specs --strict` | `Totals: 19 passed, 0 failed (19 items)` |
| `python -m pytest tests -q` | `1181 passed in 396.05s (0:06:36)` |
| `python -m compileall -q lessonkit.py workbench pipeline pool tests` | 退出码 0，无输出 |
| `python lessonkit.py guard extract-problems --course dmath --chapter ch06` | `Result: PASS` |

---

## 7. 待裁决项（**提请主会话裁决，本波未自行决定**）

| # | 事项 | 建议 | 落点 |
|---|---|---|---|
| 1 | **SI-0 的执行方式**（C-01）：合成基线 vs dmath/ch06 + 浏览器 | 以 `tools/graph-layout-diff.js` 的合成基线为准；真实课程基线**另立一份** | `tasks.md` 14.1/14.2、`acceptance.md` SI-0 |
| 2 | **「12 裸名区段外 0 引用」的验证命令**（C-02）：原版跑出 170 | 换成修正版（当前行号 + 严格正则） | `design.md` D-12.1、`tasks.md` 10.1 |
| 3 | **v2 场景的标题与行号**（C-03）：实为 `:720` / 正文 `:686-691` | 改正引用；退役时场景 + 正文一起处理 | `tasks.md` 12.3、`proposal.md`、`design.md` D-14.2 |
| 4 | **行号锚点大面积过时**（C-04 / C-05） | 一次性把 `design.md` / `tasks.md` / `acceptance.md` 的 `workbench.css` / `workbench.js` / `pages.py` 行号刷新为当前实测值；`NEIGHBOR_WEIGHT` 改 `:32` | 同上三份 |
| 5 | **`.node-satellite` / `.node-unit` DOM 的归属**（C-06） | 明确归第 2 组或第 8 组其一 | `tasks.md` 2.3 / 8.4 / 8.5 |
| 6 | **结构投影公式里的 `degree` 取哪个**（C-07） | 取 `state.degreeRaw`（与 `scoreFor` 同源，保证与物理半径同序） | `design.md` D-3、`tasks.md` 1.2 / 2.7 |
| 7 | **importance 只有 2 个取值 ⇒ 四档空两档**（C-08） | 把「四档是设计上限，实际占用档数随数据」写进 acceptance AV-1 ③ | `acceptance.md` AV-1、`tasks.md` 3.7 |
| 8 | **产品手册 / ACTION-GRAPH 的旧形态描述**（C-09） | 12.6 改成「动作集无变更，但描述按 A-28 校正」 | `tasks.md` 12.4 / 12.6 |
| 9 | **第 10 组的 spec delta 落点**：本 change 的 `specs/**` 由主会话统一维护 | 第 10 组 10.3 的登记**交主会话落盘**，或明确授权第 10 组直接改 | 派发时的显式确认 |
| 10 | **第 12 组的 12.2 / 12.3 被 A-10.2 阻塞**（v2 未合入 ⇒ 无法 re-base） | 接受「第 12 组在 v2 合入前只做 12.4/12.5/12.6/12.7」，或调整派发时机 | 派发顺序 |

---

## 8. 下一波

1. **等主线 v2 落定**（`workbench.css` / `workbench.js` / `pages.py` 不再被并行改）。
2. 按 §5.1 的顺序派发 **GRP01**（foundation）⇒ 复跑 SI-0 ⇒ 绿 ⇒ 派发下一组。
3. 每组落地后**立刻**复跑 `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ 坐标 diff 必须仍为 **0**；**看到 WARNING 不等于失败**（§1.3）。
4. 第 13 组（GRP13）在**全部实现组之后**跑，出最终门禁判定与逐处归类表。
