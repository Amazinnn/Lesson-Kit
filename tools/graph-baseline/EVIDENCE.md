# SI-0 取证记录 —— 图谱布局坐标基线

> 服务于 `openspec/changes/graph-node-visual-language/` 的 **第 14 组（14.1–14.6）**
> 与 `acceptance.md` **§0.2 SI-0**。
>
> **本波只做取证与工具**：没有改动任何图谱绘制代码，
> 没有改动 `workbench/server/static/graph-physics-core.js` ·
> `graph-physics.js` · `graph-renderer.js` · `graph-physics-worker.js` ·
> `workbench.css` · `workbench.js` · `pages.py` 中的任何一个。
> 本次落地的新文件只有三个：
> `tools/graph-layout-diff.js`、`tools/graph-baseline/baseline.json`、
> `tools/graph-baseline/README.md`、以及本文件 `tools/graph-baseline/EVIDENCE.md`。

---

## 0. 一句话结论

| 项 | 结果 |
|---|---|
| 工具 | `tools/graph-layout-diff.js`（纯 Node，无第三方依赖，只读） |
| 基线 | `tools/graph-baseline/baseline.json`（96 节点 + 96 初值，16 196 字节） |
| 连跑两次 `--capture` | **逐字节相同**（`cmp` 退出码 0，sha256 相同） |
| `--diff` 自比基线 | **0 条差异**，退出码 **0** |
| 负向对照（人为扰动基线） | **2 条差异**，退出码 **1** —— 判据不是空的 |
| 基线对应的提交 | `69b50128e59299e4897056dd138953c68bab2c16` |
| 物理核心指纹 | `graph-physics-core.js` sha256 = `c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997` |

---

## 1. 工具用法

```bash
# 出一份基线快照
node tools/graph-layout-diff.js --capture <out.json>

# 与一份基线逐点比对（0 条差异 → 退出码 0；非 0 → 退出码 1）
node tools/graph-layout-diff.js --diff <baseline.json>

# 可选：控制打印多少条差异（默认 20）
node tools/graph-layout-diff.js --diff <baseline.json> --max-report 50

node tools/graph-layout-diff.js --help
```

| 退出码 | 含义 |
|---|---|
| `0` | `--capture` 成功；或 `--diff` 的差异条数为 0 |
| `1` | `--diff` 的差异条数非 0 |
| `2` | 用法错误 / 基线文件读不了 / **本次运行没有收敛**（工具拒绝把半路状态当基线存下来） |

工具的约束（写在源码里，也写在这里）：

- **纯 Node**，`node` v24.13.1，**无第三方依赖**，仓库无 npm 构建步骤；
- **只读产品代码**：它 `require` 的是 DOM-free 的
  `workbench/server/static/graph-physics-core.js`（该文件的 UMD 头在
  `typeof module === "object" && module.exports` 时导出 `GraphPhysics`），
  **不需要浏览器、不需要 Worker**；
- **不写池**：不碰任何 SQLite，不读任何课程数据；
- **只写它被指定的那一个文件**（`--capture` 的目标路径）。

---

## 2. 三条命令的真实输出（含退出码）

以下输出是**当场跑出来的原样拷贝**，工作目录 = 仓库根目录。

### 2.1 命令一 —— 出基线

```console
$ node tools/graph-layout-diff.js --capture tools/graph-baseline/baseline.json
=== graph-layout-diff (capture) ===

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
[output]
  path            : tools/graph-baseline/baseline.json
  bytes           : 16196
  sha256          : 8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc
  node rows       : 96
  seed rows       : 96

RESULT: OK — baseline written
EXIT_CODE=0
```

### 2.2 命令二 —— 再出一次（确定性）

```console
$ node tools/graph-layout-diff.js --capture /tmp/baseline-again.json
=== graph-layout-diff (capture) ===

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
[output]
  path            : C:/Users/yanwei/AppData/Local/Temp/baseline-again.json
  bytes           : 16196
  sha256          : 8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc
  node rows       : 96
  seed rows       : 96

RESULT: OK — baseline written
EXIT_CODE=0
```

### 2.3 命令三 —— 与基线比对（SI-0 主判据）

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

---

## 3. 「两次 capture 逐字节相同」的证明

```console
$ cmp /tmp/baseline-again.json tools/graph-baseline/baseline.json
cmp EXIT_CODE=0                      # cmp 无输出即字节相同

$ sha256sum /tmp/baseline-again.json tools/graph-baseline/baseline.json
8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc */tmp/baseline-again.json
8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc *tools/graph-baseline/baseline.json

$ wc -c /tmp/baseline-again.json tools/graph-baseline/baseline.json
16196 /tmp/baseline-again.json
16196 tools/graph-baseline/baseline.json
32392 total
```

**两个 sha256 相同、字节数相同、`cmp` 退出码 0 ⇒ 两份产物逐字节相同。**

### 3.1 更强的一层：原始 double 也是逐位相同的

6 位小数的量化有可能「盖住」真实的非确定性。为了排除这一点，
把工具的量化改成「不量化、直接存原始 double」再跑两次：

```console
$ sed -e 's/decimals: 6,/decimals: 17,/' \
      -e 's|return Number(value.toFixed(QUANT.decimals));|return value;|' \
      tools/graph-layout-diff.js > tools/_tmp_rawcheck.js
$ node tools/_tmp_rawcheck.js --capture /tmp/raw-a.json
RESULT: OK — baseline written
$ node tools/_tmp_rawcheck.js --capture /tmp/raw-b.json
RESULT: OK — baseline written
$ cmp /tmp/raw-a.json /tmp/raw-b.json
cmp EXIT_CODE=0                      # 未量化的原始 double 也逐字节相同
$ rm -f tools/_tmp_rawcheck.js
```

**结论：本机上的力导向计算本身是逐位可复现的，
6 位小数的量化没有掩盖任何东西。**（该临时文件已删除，工作区无残留。）

---

## 4. 负向对照 —— 证明这个判据不是空的

一个「永远返回 0」的 diff 也满足「diff = 0」。所以做一次人为扰动：

```console
$ cp tools/graph-baseline/baseline.json /tmp/perturbed.json
$ # nodes[7].x += 0.0001 ; nodes[40].y -= 0.5
$ node tools/graph-layout-diff.js --diff /tmp/perturbed.json
[converged coordinates — SI-0 target]
  differences     : 2
  #   id          baseline x      baseline y      current x       current y       dx            dy
  1   c01n07      1284.517715     890.741358      1284.517615     890.741358      -0.0001       0
  2   c06n00      1003.742555     877.823322      1003.742555     878.323322      0             0.5

[summary]
  compared nodes  : 96
  coordinate diffs: 2
  seed diffs      : 0
  id set diffs    : 0
  total differences: 2

RESULT: FAIL — diff = 2 (SI-0 red: locate the out-of-scope change and revert it)
EXIT_CODE=1
```

**1e-4 世界像素的位移被抓住了**，退出码 1。

---

## 5. 量化口径（diff 判据本身）

| 口径项 | 取值 |
|---|---|
| 小数位数 | **6**（`Number(value.toFixed(6))`） |
| 排序键 | **`nodeId`** |
| 排序方式 | **码位序（code-unit）升序**，不是 locale collation |
| 比较方式 | **`toFixed(6)` 字符串全等 —— 全程无 epsilon** |
| 比较对象 | ① 收敛坐标（SI-0 主判据）② 初值坐标（SI-0「同一初始条件」那一半）③ 节点 id 集合 |
| 坐标系 | 世界像素（**未乘画布缩放**；相机不参与判定） |
| 迭代预算 | **固定 600 tick**（收敛发生在第 268 tick，之后的 tick 是空转） |

**为什么不调容差把 diff 糊成 0**：本次的 diff **第一次跑出来就是 0**，
没有出现需要解释的非零差异，因此不存在「调容差」这件事发生过的可能。
若将来 diff 非 0，正确动作是**定位越界改动并回退**
（`tasks.md` 14.5），不是放宽容差。

**检测下限的诚实说明**：diff 在 1e-6 世界像素的分辨率上严格为 0。
比这更小的位移在物理上不可分辨（画布缩放约 0.4，1e-6 世界像素 ≈ 4e-7 屏幕像素），
而任何**有意的**算法改动（改一个力系数、改一次 alpha 衰减、改碰撞半径……）
造成的位移在 0.01–10 px 量级，比检测下限高 4–7 个数量级。
§3.1 的未量化复跑进一步证明：底层计算逐位可复现，量化没有藏东西。

---

## 6. 迭代预算的无关性（额外的稳健性证据）

「同一迭代预算」是 SI-0 的三个前提之一。实测证明：**只要预算 ≥ 收敛 tick，
结果与预算取值无关**（收敛之后 `graph.alpha = 0`，后续 tick 直接返回）：

| 迭代预算 | 收敛 tick | 收敛坐标 | 初值坐标 |
|---|---|---|---|
| 300 | 268 | 与 600 **逐点相同** | 与 600 **逐点相同** |
| 400 | 268 | 与 600 **逐点相同** | 与 600 **逐点相同** |
| 600（本基线） | 268 | — | — |
| 900 | 268 | 与 600 **逐点相同** | 与 600 **逐点相同** |
| 1200 | 268 | 与 600 **逐点相同** | 与 600 **逐点相同** |

⇒ 快照里记录的坐标是**收敛态**的坐标，不是「跑够 N 帧」的半路状态。

---

## 7. 本基线对应哪一次提交

| 项 | 值 |
|---|---|
| **采集时的树（工具提交）** | `69b50128e59299e4897056dd138953c68bab2c16` |
| 提交标题 | `feat(tools): 图谱布局坐标 diff 工具（SI-0 基线取证用）` |
| **存放基线的提交** | `1bacdc9e02841b55795001e62eecb08b104476d8` |
| 提交标题 | `feat(tools): 落下图谱布局坐标基线（改造前）+ 基线说明` |
| **物理核心指纹（真正的锚）** | `workbench/server/static/graph-physics-core.js` sha256 = `c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997` |
| **基线文件指纹** | `tools/graph-baseline/baseline.json` sha256 = `8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc` |

`git rev-parse HEAD` 在采集时刻的输出：`69b50128e59299e4897056dd138953c68bab2c16`。

> **为什么 sha256 才是锚**：本仓库此刻有多个 agent 并行提交，
> `HEAD` 会随时移动。仓库里别的文件在动，**不影响**这份基线；
> 只有 `graph-physics-core.js` 变了，锚才动。
> 工具在 `--diff` 时会比对这两个 sha256，不一致就直接打印告警（见 §9）。

---

## 8. 输入与规模（为什么是 96 个节点）

| 项 | 值 |
|---|---|
| 节点 | **96**（12 章 × 8 点） |
| 关系 | **338**（平均度 7.04） |
| 边类型分布 | `prereq` 84 / `apply` 93 / `related` 93 / `contrast` 59 / `legacy` 9 |
| 方向分布 | 有向 177 / 对称 161 |
| 层级数 | **8**（0…7，由章内先修链算出） |
| 视图 / 重力 / 舞台 | `structure` / `85` / `1800 × 1550`（**全部用核心自己的默认值**，工具不覆盖） |

**为什么选这个规模**：

1. **≥ 80 个点**：斥力与碰撞走 Barnes-Hut 四叉树，点数少到一定程度时
   「近邻对」表退化成全对扫描，布局会走上一条完全不同的路径。
   96 点落在真实课程图谱的量级里（`习概` 实测 192 点 / 727 边），
   又比最坏情况快得多（一次完整运行约 **0.25 秒**）。
2. **覆盖多个章节分组**：12 个章节组 ⇒ 布局要同时处理「组内紧密、组间稀疏」，
   「标签宽度参与占位」（`footprint()` → `labelWidth()`）这条真实约束被压到。
3. **多层级**：8 个层级 ⇒ 排除掉「扁平单层图谱」那条完全不同的分支
   （`flatLevel()`，`graph-physics-core.js:156`）。
4. **边类型与方向齐全**：五种边类型、有向与对称都有
   （`direction` 参与层级的计算：`hierarchyLevels()` 只读 `prereq` 且非 `symmetric` 的边）。

**输入构造**（`tools/graph-layout-diff.js` 的 `buildGraph()`）：
id 为 `c<两位章号>n<两位序号>`；`state` / `kind` 按下标轮转；
`importance = ((i*37)%101)/100`；`problems = (i*11)%23`；
边为章内先修链 + 章内跳过链 + 章间链接。**全程没有一个随机数。**

**初值**：核心自己在 `create()` 里用确定性的座位螺旋
（`seatPositions()`，`graph-physics-core.js:938`）摆好。**工具不覆写它** ——
产品用的初值就是要冻结的那个初值；换成工具自造的初值，
反而会让「座位布局被改」逃过 diff。工具把这份初值也存进 `baseline.json` 的 `seed` 段并纳入 diff。

**为什么不用真实课程（如 dmath/ch06）的图谱模型**：
真实池是活的 —— 每改一次课程，节点与边就变一次，基线会跟着漂，
「改造前 / 改造后」就不在同一个输入上了。
合成图谱的形状固定，是唯一能保证明年还能复现的输入。
第 14 组最终接真实池时，用同一套工具、换一份输入重出一份基线即可（届时**另立**一份，不覆盖本份）。

---

## 9. ⚠️ 越界告警（必读）

> **任何对 `workbench/server/static/graph-physics-core.js` 或
> `workbench/server/static/graph-physics.js` 的改动，
> 都必须先重跑 `--capture` 并把差异写进本文件 —— 否则 SI-0 失效。**
>
> **为什么**：SI-0 的全部力量来自「基线来自**改造之前**」这件事。
> 如果改了物理核心却不重出基线，基线描述的就已经是**另一个**算法，
> diff 报告的 0 就不再证明「算法没动」，只证明「两次跑的是同一段新代码」。
>
> **落到动作上**：
> 1. `git diff` 一旦出现 `graph-physics-core.js` / `graph-physics.js`，
>    **先**跑 `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`；
> 2. 退出码非 0 ⇒ 按 `tasks.md` 14.5 逐行归类到 D-13.2 的六条「允许改」，
>    **回退**越界的那一处并重跑；
>    **不得**用「差异很小」「四舍五入」「换个容差」解释掉；
> 3. 确实需要改物理 ⇒ 先改 OpenSpec（proposal → specs），
>    再重跑 `--capture`，把新旧两份坐标与差异说明写进本文件，
>    并把基线对应到新的 commit SHA。
>
> **工具会自己喊**：一旦 `graph-physics-core.js` 的 sha256 与基线里记的不一致，
> `--diff` 会打印
> `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
> —— 这只**提醒**，不代替第 1–3 步。

---

## 10. 本波**没有**碰的东西（复核）

本波只新建文件，**未修改任何既有文件**。落盘清单：

```
tools/graph-layout-diff.js          （新建）
tools/graph-baseline/baseline.json  （新建）
tools/graph-baseline/README.md      （新建）
tools/graph-baseline/EVIDENCE.md    （新建）
```

下列文件**一行未动**（六个 agent 正在并行改其中几个，本波完全不碰）：

```
workbench/server/static/graph-physics-core.js
workbench/server/static/graph-physics.js
workbench/server/static/graph-renderer.js
workbench/server/static/graph-physics-worker.js
workbench/server/static/workbench.css
workbench/server/static/workbench.js
workbench/server/pages.py
```

`openspec/changes/**` 下的任何文件也未改动（由主会话统一改）。

---

## 11. 复跑清单（任何人拿到仓库都能复现）

```bash
# 0) 环境
node --version          # v24.13.1
git rev-parse HEAD

# 1) 重出基线（退出码 0）
node tools/graph-layout-diff.js --capture tools/graph-baseline/baseline.json

# 2) 再出一次，验证确定性（两份逐字节相同）
node tools/graph-layout-diff.js --capture /tmp/baseline-again.json
cmp /tmp/baseline-again.json tools/graph-baseline/baseline.json && echo "byte-identical"

# 3) SI-0 主判据（0 条差异，退出码 0）
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json

# 4) 仓库级检查
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

---

## 12. 仓库级检查的实测结果（本波交付时）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `python -m pytest tests -q` | **0** | `1164 passed in 233.48s (0:03:53)` |
| `python -m compileall -q lessonkit.py workbench pipeline pool tests` | **0** | 无输出（全部通过） |
| `openspec validate --specs --strict` | **0** | `Totals: 19 passed, 0 failed (19 items)` |
| `python lessonkit.py guard extract-problems --course dmath --chapter ch06` | **0** | `Result: PASS` |

```console
$ python lessonkit.py guard extract-problems --course dmath --chapter ch06
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
GUARD_EXIT=0
```

（本波没有改任何产品代码，四条命令只是**确认没碰坏别的**。）
