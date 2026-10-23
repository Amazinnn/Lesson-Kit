# IMPL-W3f — 图谱 SI-0 基线取证：写 `tools/graph-layout-diff.js` 并落下「改造前」坐标基线

> 服务于**另一个 change**：`openspec/changes/graph-node-visual-language/`
> 的 **第 14 组（14.1–14.6 · 算法冻结与 diff=0 证据）**。
> **本波只做「取证与工具」，不碰图谱的任何绘制代码。**

## 为什么是这一件（背景）
所有者的绝对底线之一是 **「不要动图谱的算法！我们只是修改外观。」**
这条底线要能被**执行**，就得有一个可重复运行的判据 ——
图谱 change 的 `acceptance.md` 把它钉成 **SI-0**：
> 同一输入 + 同一初值 + 同一迭代预算，改造前后**收敛坐标集合 diff 必须严格为 0**。

现在这个判据**还没有可执行的东西**：既没有工具，也没有「改造前」的基线。
一旦有人开始改图谱的绘制代码，就**再也拿不回基线**了。
所以：**先取证，后动手。**

## 硬约束
- **只新建这些文件**（本波全是新文件，**不碰任何既有文件**）：
  - `tools/graph-layout-diff.js`（Node 脚本）
  - `tools/graph-baseline/`（基线产物目录）
- **绝不改** `workbench/server/static/graph-physics.js` ·
  `graph-physics-core.js` · `graph-renderer.js` · `graph-physics-worker.js` ·
  `workbench.css` · `workbench.js` · `pages.py`（**六个 agent 正在并行改其中几个**）。
- **不要**改 `openspec/changes/**` 下任何文件（主会话统一改）。
- 知识图谱的**绘制**一行都不许碰 —— 本波**只读**图谱代码。

## 必读
1. `openspec/changes/graph-node-visual-language/tasks.md` 的 **第 14 组全文**
2. `openspec/changes/graph-node-visual-language/acceptance.md` 的 **SI-0**（判据的精确表述）
3. `openspec/changes/graph-node-visual-language/design.md`（**D-13 的 14 项冻结 + 6 项只绘制的允许清单**）
4. `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md`（**图谱移交清单 H-1…H-11**）
5. `workbench/server/static/graph-physics-core.js` 的**文件头注释**（它明确写着
   「It is DOM-free」且用 CommonJS 导出 `GraphPhysics`）—— 这是脚本能跑在 Node 里的前提。

## 要交付什么

### 1. `tools/graph-layout-diff.js` —— 可重复运行的坐标 diff 工具
要求：
- **纯 Node，无第三方依赖**（`node` v24 可用；仓库无 npm 构建）。
- 从 `workbench/server/static/graph-physics-core.js` 载入 `GraphPhysics`
  （`require` 即可，它是 DOM-free 的）。
- 用**确定性的输入**：同一份节点/边集合、同一份初始坐标（自己生成一个固定的种子布局，
  **不要用随机数** —— 随机会让 diff 不可复现）、**同一迭代预算**。
  节点数取一个**有代表性的规模**（例如 ≥ 80 个点、覆盖多个章节分组），
  并说明为什么选这个规模。
- 跑出**收敛后的坐标集合**，输出一个**稳定排序**的快照
  （例如 `nodeId: x, y` 按 `nodeId` 字典序；浮点**统一保留固定位数**，
  避免平台间的尾数噪声）。
- 支持两个模式：
  - `--capture <out.json>`：产出基线快照；
  - `--diff <baseline.json>`：与基线逐点比对，**打印差异条数与前 N 条差异**，
    **差异为 0 时退出码 0，非 0 时退出码非 0**。
- **同时打印被比较的坐标的量化口径**（小数位数、排序键），让 diff 口径本身可审计。

### 2. 确定性与噪声底（**必做，否则 SI-0 没有意义**）
- **连跑两次 `--capture`，两次产物必须逐字节相同** ⇒ 证明工具本身是确定性的。
- 再跑一次 `--diff` 拿自己刚生成的基线 ⇒ **diff 必须严格为 0**。
- 把这三个命令的**实际输出**（含退出码）**原样写进证据文件**。
- ⚠️ **如果 diff 不是 0**，**不要**去调容差把它糊成 0 ——
  **先查清是浮点尾数、排序、还是迭代预算不一致**，把根因写进证据文件。

### 3. 基线产物落到 `tools/graph-baseline/`
- 一份 JSON 快照 + 一份 `README.md`（写清：**怎么重新生成**、**坐标口径**、
  **节点规模与输入构造方式**、**本次生成的 commit SHA**）。

### 4. 证据文件
写一份 `tools/graph-baseline/EVIDENCE.md`（或 `.md` 放在同一目录），包含：
- 工具的用法（命令逐条）；
- 上面三个命令的**真实输出**；
- **量化口径**说明；
- **「本基线对应哪一次提交」**（`git rev-parse HEAD` 的结果）；
- **一条明确的警告**：**任何对 `graph-physics-core.js` / `graph-physics.js` 的改动，
  都必须先重跑 `--capture` 并把差异写进证据** —— 否则 SI-0 失效。

## 验证
```bash
node tools/graph-layout-diff.js --capture tools/graph-baseline/baseline.json
node tools/graph-layout-diff.js --capture /tmp/baseline-again.json
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
```
- 第一个命令退出码 0；第二个产物与第一个**逐字节相同**（用 `cmp` 或 `fc` 证明）；
  第三个命令**打印 0 条差异**且退出码 0。
- 仓库级检查仍要绿（你不改产品代码，但确认没碰坏别的）：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```

## 落盘纪律与回报
- **小步提交**：工具 → 基线 → 证据，**分三次 commit**。
- **不要 `git add -A`** —— 只 add `tools/` 下的文件。
- 最终回报必须复述：**已落盘路径 + 三个命令的真实输出（含退出码）** +
  **两次 capture 逐字节相同的证明** + **坐标量化口径** +
  **基线对应的 commit SHA** + **为什么选这个节点规模** +
  **四条验证命令结果** + **你发现的任何图谱代码里的「不该动但可能被误读」的地方**。
- 数字一律以**当场跑出来的命令输出**为准。
