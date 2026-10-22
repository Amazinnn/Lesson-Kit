# 图谱布局坐标基线（SI-0「改造前后 diff = 0」）

本目录是 `openspec/changes/graph-node-visual-language/` 的 **SI-0**（图谱算法冻结）
在**改造之前**留下的坐标基线。SI-0 的判据是：

> 同一输入 + 同一初值 + 同一迭代预算 ⇒ 改造前后**收敛后的节点坐标集合 diff 必须严格为 0**。

所有者的原话是「**不要动图谱的算法！我们只是修改外观。**」——
这条底线要能被**执行**，就得先有「改造前」的坐标，再有一个可重复运行的比对工具。
本目录就是那两样东西。

## 目录内容

| 文件 | 是什么 |
|---|---|
| `baseline.json` | 「改造前」的坐标快照（96 个节点的收敛坐标 + 96 个节点的初值坐标 + 全部生效参数 + 物理核心的 sha256） |
| `EVIDENCE.md` | 取证记录：三条命令的真实输出（含退出码）、量化口径、对应 commit SHA、越界告警 |
| `../graph-layout-diff.js` | 生成与比对工具（纯 Node、无第三方依赖、只读） |

## 怎么重新生成

在**仓库根目录**运行（工具用 `__dirname` 定位物理核心，输出路径按 CWD 解析）：

```bash
# 1) 重新出基线（会覆盖 baseline.json）
node tools/graph-layout-diff.js --capture tools/graph-baseline/baseline.json

# 2) 再出一次，验证工具本身是确定性的（两份必须逐字节相同）
node tools/graph-layout-diff.js --capture /tmp/baseline-again.json
cmp /tmp/baseline-again.json tools/graph-baseline/baseline.json

# 3) 与基线比对（SI-0 的主判据）
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
```

退出码：`0` = diff 严格为 0；`1` = diff 非 0；`2` = 用法错误 / 读不到文件 / 本次运行**没有收敛**
（未收敛时工具拒绝出快照，而不是把半路状态当基线存下来）。

## 坐标量化口径

| 口径项 | 取值 | 为什么 |
|---|---|---|
| 小数位数 | **6 位**（`Number(value.toFixed(6))`） | 固定值，不是可调容差。1e-6 世界像素 ≈ 1e-6 屏幕像素量级（画布缩放 ~0.4），远低于任何有意义的算法改动（改一个力系数造成的位移在 0.01–10 px 量级），又高到足以躲开不同平台的 libm 尾数噪声 |
| 排序键 | **`nodeId`** | 快照的行序只由 id 决定，与运行顺序无关 |
| 排序方式 | **码位序（code-unit）**，不是 locale collation | 物理核心内部有两处用 `String.localeCompare` 排 id（`graph-physics-core.js:613` / `:664`），那会让布局依赖运行机器的 ICU 数据。本工具自己排快照时用码位序，且基线用的 id 是**等宽小写字母数字**（`c01n00`…`c12n07`），两者在该 id 集上顺序一致（已实测） |
| 比较方式 | **`toFixed(6)` 字符串全等** | 全程**没有 epsilon**：不存在「差异小于某阈值就算相同」的判定 |
| 比较对象 | **收敛坐标**（SI-0 主判据）**+ 初值坐标**（SI-0「同一初始条件」那一半） | 初值也进 diff ⇒ 座位布局被改也会被抓到 |
| 坐标系 | 世界像素（未乘画布缩放） | 相机（缩放 / 平移 / Fit）不参与判定：SI-0 冻结的是**布局**，不是取景 |

**检测下限的诚实说明**：diff 在 1e-6 世界像素的分辨率上严格为 0。
比这更小的位移在物理上不可分辨（不到屏幕像素的百万分之一），
且**不**是「用容差糊成 0」——量化是事先声明的测量分辨率，比较本身是精确全等。
实测证据：本机两次运行的**未量化原始 double 也是逐字节相同**（见 `EVIDENCE.md`），
说明 6 位小数没有掩盖任何真实的非确定性。

## 节点规模与输入构造方式

**规模：12 章 × 8 点 = 96 个节点，338 条关系（平均度 ≈ 7.0）。**

选它的理由：

1. **≥ 80 个点**：物理核心里斥力与碰撞走的是 Barnes-Hut 四叉树，
   点数少到一定程度时「近邻对」表退化成全对扫描，布局会走上一条完全不同的路径。
   96 个点落在真实课程图谱的量级里（`习概` 实测 192 点 / 727 条边），
   又比最坏情况快得多（一次完整运行约 0.25 秒）。
2. **覆盖多个章节分组**：12 个章节组 ⇒ 布局要同时处理「组内紧密、组间稀疏」的结构，
   也让「节点标签的宽度参与占位」（`footprint()` → `labelWidth()`）这条真实约束被压到。
3. **多层级**：每章内部一条先修链（7 条 `prereq`）⇒ 核心算出 **8 个层级**。
   扁平的单层图谱在核心里走的是另一条分支（`flatLevel()`，
   `graph-physics-core.js:156`），布局形态完全不同，必须排除。
4. **边类型齐全**：`prereq` / `apply` / `contrast` / `related` / `legacy` 五种都出现，
   且有向边与对称边都有（`direction: "directed" | "symmetric"` 会改变层级的算法）。

**输入是怎么构造的**（`tools/graph-layout-diff.js` 里的 `buildGraph()`）：

- 节点 id：`c<两位章号>n<两位序号>`，例如 `c01n00`；**等宽小写字母数字**，理由见上表。
- 节点字段：`title` / `shortTitle` / `state`（四态轮转）/ `kind`（三类轮转）/
  `importance`（`((i*37)%101)/100`）/ `problems`（`(i*11)%23`）——
  全部是节点下标的纯函数，**没有一个随机数**。
- 边：章内先修链（强度在 0.9–1.1 之间按 `(g+k)%5` 轮转）+ 章内跳过链（`apply` / `related` /
  `contrast`）+ 章间链接（`apply` 有向、`contrast` / `related` / `legacy` 对称）。
- **初值不覆写**：核心自己在 `create()` 里用确定性的座位螺旋
  （`seatPositions()`，`graph-physics-core.js:938`）摆好初始坐标。
  本工具**不**替换它 —— 产品用的初值就是要冻结的那个初值，
  换成工具自造的初值反而会让「座位布局被改」这件事逃过 diff。
  工具把这份初值也存进了 `baseline.json` 的 `seed` 段。

**为什么不直接用真实课程（如 dmath/ch06）的图谱模型**：
真实池是活的 —— 每改一次课程，节点与边就变一次，
基线会跟着漂，「改造前 / 改造后」就不在同一个输入上了。
合成图谱的形状固定，是唯一能保证明年还能复现的输入。
`graph-node-visual-language` 第 14 组最终要接真实池时，
用同一套工具、换一份输入重出一份基线即可（本基线届时另立一份，不覆盖）。

## 本基线对应哪一次提交

| 项 | 值 |
|---|---|
| 采集时的树 | `69b50128e59299e4897056dd138953c68bab2c16`（`feat(tools): 图谱布局坐标 diff 工具（SI-0 基线取证用）`） |
| 物理核心指纹 | `workbench/server/static/graph-physics-core.js` 的 sha256 = `c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997` |
| 基线文件指纹 | `baseline.json` 的 sha256 = `8c1b76393df387108633df512204a21a0ad3be35f28b334605c3fd0dfb4ec6cc` |

**核心文件的 sha256 是真正的锚**：仓库里别的提交在动，不影响这份基线；
只有 `graph-physics-core.js` 变了，锚才动。

## ⚠️ 越界告警（必读）

> **任何对 `workbench/server/static/graph-physics-core.js` 或
> `workbench/server/static/graph-physics.js` 的改动，
> 都必须先重跑 `--capture` 并把差异写进 `EVIDENCE.md` —— 否则 SI-0 失效。**
>
> 原因：SI-0 的力量全部来自「基线来自改造之前」这件事。
> 如果改了物理核心却不重出基线，那么基线描述的已经是**另一个**算法，
> diff 报告的 0 就不再证明「算法没动」，只证明「两次跑的是同一段新代码」。
>
> 判据落到具体动作上：
> 1. `git diff` 一旦出现 `graph-physics-core.js` / `graph-physics.js`，
>    **先**跑 `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`；
> 2. 退出码非 0 ⇒ 按 `tasks.md` 14.5 定位越界改动并**回退**，
>    **不许**用「差异很小」「四舍五入」解释掉；
> 3. 确实需要改物理（例如将来确有必要）⇒ 先改 OpenSpec，
>    再重跑 `--capture`，把新旧两份坐标与差异说明写进 `EVIDENCE.md`，
>    并把基线对应到新的 commit SHA。
>
> 工具本身会在 `--diff` 时打印这条警告：一旦
> `graph-physics-core.js` 的 sha256 与基线里记的不一致，就直接报
> `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`

## 这份基线**不**覆盖什么

- **相机**：缩放 / 平移 / Fit 的结果不在坐标 diff 里（那是 D-11 组的范围，且与算法无关）。
- **真实池数据**：见上「为什么不直接用真实课程」。
- **绘制层**：颜色、字号、标签位置、边的线宽与箭头 —— 按 D-13.2 本来就允许改，
  SI-0 不管它们。
