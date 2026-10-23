# IMPL-A1 — 实物插画精修：把 10 张空态插画 + 台灯贴回规格

> 对应 `tasks.md` **第 29 组**（所有者追加：「那些插画式的实物组件不够精致」）。
> **只改 `workbench/server/static/assets/` 下的资产文件。**

## 背景（已核实的现状）
10 张空态插画（`assets/empty/*.svg`：books / canvas / compass / cup / fruit-basket / globe /
inkwell / pen / pencil-cup / vase）+ 台灯（`assets/motion/lamp.svg`）已入库，
**结构上贴住了规格**（viewBox、圆端点、线宽 3:2:1.5、预混淡彩、四个语义组）。
但所有者看了渲染结果，判断「**不够精致**」。

主会话已把 11 件资产**渲染成并排图**看过（`tmp/asset-shots/grid.png`），问题定位如下：

| 资产 | 问题 | 依据 |
|---|---|---|
| **`empty-compass`** | 读起来像**三脚架 / 旗杆**，不像圆规 | `decisions.md` **§13.3**「插画是**具象静物**，不是抽象几何团块」+ `asset-spec` §3.0「**禁止**…抽象几何团块」⇒ **这是违反规格，不是口味** |
| **`empty-canvas`** | 读起来像**镜子 / 屏风**（方框 + 两条几何腿） | 同上 |
| **`empty-globe`** | 球体网格**不对称**、支架是纯几何三角 | 同上 + 29.4 跨图一致性 |
| **`empty-vase`** | 花枝是**一团黑线**，看不出是柳枝 | §3.1「一枝柳」 |
| `empty-pen` | 太素（几乎一根光杆） | 29.4 跨图一致性（每张都要有淡彩与高光） |
| **十张并排** | 视觉重量差太大（花瓶最重、笔最轻） | §3.12 跨图一致性：最长边极差 ≤1.6 倍 |

## 闸门已经建好（**先跑它，再动手**）
`tools/audit-assets.py` —— 主会话写的**资产审计器**，逐条机检 `asset-spec.md`：
viewBox · 根上无 width/height · 端点连接 round · **线宽只许 3:2:1.5 三档** ·
无 SVG filter · 淡彩用预混色不用 alpha · 四个语义组齐全 ·
桌面横线 y=168 且长 144–168 u · 高光 ≤2 · 阴影不透明度 ≤12% ·
**外接框与 §3.12 的实测表比对（容差 ±2 u）** · 最长边 60–132 u · 高 ≤132 u ·
左右留白 ≥40 u · 压线 165–168 u · 水平偏移 ≤6 u。

```bash
python tools/audit-assets.py            # 人看的表
python tools/audit-assets.py --strict   # 有任一不通过则退出码 1  ← 你的完成判据
```

**当前基线：228/234 项通过，6 项不通过**（你自己跑一遍确认）。

### 已知的 6 项不通过（其中两项主会话已修口径）
| 资产 | 现象 | 处置 |
|---|---|---|
| `empty-cup` | y 偏差 **−44 u** | **口径问题**：蒸汽被算进了器物本体。⇒ 蒸汽**必须**放进 `class="asset-empty__extension"` 的分组（`asset-spec` §3.0 已补这条规则）⇒ 测量即排除 |
| `empty-vase` | x 偏差 ±4.4 u、最长边 131.1 | 同上：花枝归 `asset-empty__extension`；**器物本体**（瓶腹）另须落在 §3.12 的 78→158 之内 |
| `empty-fruit-basket` | y 上缘偏 **5.8 u** | 真偏差 ⇒ 果篮本体按 §3.12 的 74→166 × 85→167 重画 |
| `empty-pencil-cup` | x 偏 4 u、离横线 164.6（未压到 165–168） | 真偏差 ⇒ 按 §3.12 的 92→146 × 44→166 重画 |
| `empty-cup` | 最长边 60–132 | 口径已由主会话把上限从 125 改为 132（§3.0 与 §3.12 原本互斥：表里花瓶 130 却标 ✓） |
| `empty-vase` | 最长边 131.1 | 同上（≤132 即合规） |

## 要做什么

### 1. 归组延伸元素
- 蒸汽（`empty-cup`）、花枝（`empty-vase`）放进 `class="asset-empty__extension"`。
- ⚠️ **四个语义组（`__shadow` / `__wash` / `__line` / `__highlight`）保持不变** ——
  宿主 CSS 与 `pages.py::_inline_asset` 按这些类名挂载。
- ⚠️ **延伸元素仍然是画面的一部分**（要好看），只是**不计入器物外接框**。

### 2. 修 §3.12 的实测偏差
逐张把**器物本体**贴到 §3.12 的表（容差 ±2 u）——
`audit-assets.py` 的输出就是逐条对照，不用自己重算。

### 3. 可辨认度（29.3）—— **这一条最重要**
十张插画必须**一眼能叫出名字**（花瓶 / 果篮 / 画布 / 茶杯 / 叠书 / 钢笔 / 笔筒 / 地球仪 / 墨水瓶 / 圆规）。
- `empty-compass` 现在读起来像三脚架：**圆规要有铰链头、握柄、一支针脚 + 一支铅脚**，两脚有夹角。
- `empty-canvas` 现在读起来像镜子：**画布要有绷框的厚度、木质边框与画布面、斜撑**。
- `empty-globe`：球体网格要**对称**（经线等距、纬线平行），支架要读得出是底座与转轴。
- `empty-vase`：柳枝要有**可辨的枝条与柳叶**（不是一团乱线）。
- 改完**自己渲染并看图**确认每张都叫得出名字（`tools/render-assets.py`）。

### 4. 跨图一致性（29.4）
- **同一张桌子**：桌面横线全部 y=168（已由闸门检查）。
- **视觉重量相当**：最长边极差 ≤1.6 倍（§3.12 跨图一致性表）。
- **同一支笔**：端点圆角一致、线宽只用同三档、圆角档按 §1.4 的比例。
- **每张都有淡彩与高光**（不许有的一张是纯线稿）——淡彩只用 §3.0 配方表里的写法
  （`var(--asset-wash-*)` 或 `color-mix(in oklab, var(--role-*) N%, var(--asset-paper))`）。
- **墨色**一律 `var(--asset-ink)`（夜纸自动反相）。

### 5. 双主题（29.5）
同一份文件在暖纸 / 夜纸下都成立 ⇒ **只准用 `var(--asset-*)` / `var(--art-*)` / `color-mix(... var(--asset-paper))`**，
**不许写死浅色值**（`#fffdf7` 之类只允许作为 `var()` 的 fallback）。

## 硬约束
- **只改 `workbench/server/static/assets/` 下的 `.svg` 文件**（10 张空态插画 + 台灯）。
  **五个导航图标**（`assets/icons/*.svg`）是**另一类工艺**（24px 单色线图标）⇒
  **本组不重画它们**；但闸门也会查它们的技术条款，**若闸门判它们不通过 ⇒ 只修技术违规，不改造型**。
- **不新增文件**：资产总数**恒为 16**（10 插画 + 1 台灯 + 5 图标）——
  `asset-spec` §5.1 的交付清单是硬约束。
- **不新增色相**：只许学习蓝 / 阳光黄 / 注意红 + 中性；淡彩按 §3.0 配方表。
- **禁止**：SVG filter（`feGaussianBlur` / `feDropShadow` / `feTurbulence`）·
  `fill-opacity` / `stroke-opacity`（用预混色）· 复杂 `clipPath` · 外部引用（http/https/`//`）·
  位图 · 人物 / 动物 / 文字 / 字母 / 品牌标识。
- **不许**在 `<svg>` 根上写 `width` / `height`（尺寸由宿主 CSS 控制）。
- **不许**改 `pages.py` / `workbench.css` / `workbench.js`（宿主与样式由别的 agent 负责）。
- **不许**改 `asset-spec.md`（主会话已改过；你只读它）。
- 体积上限见 §5.3（单件别超现有量级一个数量级）。

## 验证
```bash
python tools/audit-assets.py --strict      # 必须退出码 0
python tools/render-assets.py             # 渲染并排图 → tmp/asset-shots/grid.png
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```
- **并排图要自己看**：每张叫得出名字、十张是同一张桌子、视觉重量相当。
- **夜纸也要渲染一张**（把 `<html data-theme="night">` 加进渲染脚本的图里），
  确认夜纸下淡彩与墨线都成立。
- 走查：起隔离服务（仓库根 cwd、独立端口、池副本 + `LESSONKIT_WB_HOME`），
  打开**空态页面**与**设置视图**，确认插画显示正常（尺寸 180×150、无裁切、居中）。

## 落盘纪律与回报
- **一个资产一个 commit**（10+1 个），只 `git add workbench/server/static/assets/`，
  **不要 `git add -A``**，**提交时用 `git commit -- <明确的路径列表>` 限定范围**
  （⚠️ **工作区里有别的 agent 已暂存的文件**；不限定范围会把别人的东西卷进你的提交）。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**`audit-assets.py --strict` 的最终输出（退出码 0）** +
**改前 / 改后的并排渲染图路径** +
**逐张说明改了什么、为什么（尤其 compass / canvas / globe / vase 这四张）** +
**夜纸渲染图路径** + 四条验证命令结果 + 待裁决项。
- 数字与结论一律以**当场跑出来的输出**与**你自己看过的渲染图**为准。
