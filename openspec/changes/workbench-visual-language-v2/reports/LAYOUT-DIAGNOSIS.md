# LAYOUT-DIAGNOSIS —— 版式诊断：五类可测缺陷

> **所有者把问题说精确了**：
> 「当前**组件样式没什么问题**，但是**布局极度不合理**，导致：
> **字段漂移到边框甚至超出、组件之间重叠或留白严重、分布密度不均匀、部分组件过小导致视觉上很骨感。**」
>
> 这份报告就按这五条**逐条判**。
> 每条给：**实测值 + 具体元素 + `file:line`**。
> 第 3 节保留原来的 11 项指标，但它们降级为**病因解释**（"为什么会这样"），
> 不再当判定用，也**不再给合成的"积木感指数"** —— 五条独立缺陷逐条判，比一个总分有用。

---

## 0. 测量现场、口径与复现

### 0.1 现场

| 项 | 实测值 |
|---|---|
| 仓库 HEAD（定稿时） | **`349b6868`**（并发 agent 在推 `workbench.css` ⇒ 见 §0.3） |
| 本报告的 CSS 锚点 | **commit `bc488a40`** 的 `workbench/server/static/workbench.css`：**228 671 字节 / 4 862 行 / sha256 `6046575b1b204545…f17b9`** |
| A-39 核对 | 服务返回 **228 671** == 磁盘 **228 671**，sha 相同 ✅（`workbench.css` / `agent-ui.css` / `kp-experience.css` / `workbench.js` / `paper-practice.js` 全部逐字相同） |
| 服务 | `http://127.0.0.1:3311`（独立端口，不在禁用清单内） |
| 隔离 | 池副本 `tmp/layout-diag/ws-walk/pool/dmath.db` + `LESSONKIT_WB_HOME=tmp/layout-diag/registry`；`launch.py` 的 A1/A2/A3 硬断言通过，`realPoolUnchanged: true` |
| 种子 | 120 条作答记录 + 40 条 AI 会话；`tools/walkthrough/exercise.py` 建 1 份试卷 `ps-001`（3 题）并跑完一轮 |
| 视口 / DPR / 主题 | 1440×900 / DPR 1 / 暖纸 `{"theme":"paper"}` 与夜纸 `{"theme":"night"}`（显式写 localStorage，不靠系统偏好） |
| 代理 | 全程 `env -u http_proxy -u https_proxy -u all_proxy` |

### 0.2 **两种数据态都要看**（这是本报告最重要的一条口径）

| 态 | 怎么来的 | 为什么重要 |
|---|---|---|
| **有对话**（40 条） | `launch.py --seed-sessions 40` | 对话栏被塞满 ⇒ **看不见右栏的空** |
| **无对话**（0 条） | 把副本里的 `conv-001…conv-040/` 挪走 | **这就是所有者截图那一态**：右栏只剩「对话」标签 +「新建」按钮 +「还没有对话」 |

⇒ **全部 D1–D5 的判定以「无对话」态为准**（与所有者截图一致），
「有对话」态只作为对照列出。证据截图两套都留（附录 B）。

### 0.3 口径

| 概念 | 定义 |
|---|---|
| **可见** | `display≠none`、`visibility≠hidden/collapse`、`opacity≠0`；`svg` 内部与 `<script>/<style>/<template>` 跳过 |
| **块级** | `display` ∈ {`block`,`flex`,`grid`,`flow-root`,`list-item`,`table*`}；`inline-block` 不算块 |
| **有面（面块）** | `background-color` 非透明 **或** `box-shadow≠none` **或** 有 `border`（宽>0 且 style≠none）；面积 ≥ 4000 px² |
| **所在容器**（D1） | 文本节点的**最近块级可见祖先**；量它到该容器 **padding box 内缘**（= content box 边缘）的距离 |
| **列**（D3） | `#left-column` / `#middle-page` / `#ai-column` |
| **内容占用率**（D3） | 列的**可见盒**（`clientWidth × clientHeight`）里，被**叶子内容块**（最深的带文字的元素）覆盖的面积占比 |
| **叶子块** | 有直接文本、且没有任何后代元素带文本的元素 |
| **视觉事件**（D4） | 一个 painted 元素的 `(底色, 阴影, 边框)` 三元组 |
| **骨感比**（D5） | 列表行 `font-size ÷ 行高` 与 `line-height ÷ 行高` 两个比值 |

### 0.4 复现

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
mkdir -p tmp/layout-diag
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  python tools/walkthrough/launch.py --scratch tmp/layout-diag --port 3311 \
    --side after --ws walk --course dmath --chapter ch06 \
    --seed-records 120 --seed-sessions 40 \
    --out tmp/layout-diag/evidence/after/requests.jsonl --ready-file tmp/layout-diag/ready.json

# A-39 核对（服务字节 == 磁盘字节）
env -u http_proxy -u https_proxy -u all_proxy python -c "
import urllib.request, hashlib, pathlib
for f in ['workbench.css','agent-ui.css','kp-experience.css','workbench.js','paper-practice.js']:
    s = urllib.request.urlopen('http://127.0.0.1:3311/static/'+f, timeout=10).read()
    d = (pathlib.Path('workbench/server/static')/f).read_bytes()
    print(f, len(s), len(d), s == d, hashlib.sha256(s).hexdigest()[:12])"

# 建一份试卷（让练习页与试卷列表有内容）
env -u http_proxy -u https_proxy -u all_proxy \
  python tools/walkthrough/exercise.py --base-url http://127.0.0.1:3311 --ws walk \
    --out tmp/layout-diag/evidence/after

# 跑两批探针（11 项指标 + D1…D5）
env -u http_proxy -u https_proxy -u all_proxy python tmp/layout-diag/measure.py \
    --base-url http://127.0.0.1:3311 --ws walk --paper ps-001 \
    --out tmp/layout-diag/measurements.json --shots tmp/layout-diag/shots
env -u http_proxy -u https_proxy -u all_proxy python tmp/layout-diag/defects.py \
    --base-url http://127.0.0.1:3311 --ws walk --paper ps-001 \
    --out tmp/layout-diag/defects-seeded.json --shots tmp/layout-diag/shots-seeded

# 无对话态：把副本里的会话挪走再跑一遍
mkdir -p tmp/layout-diag/conv-backup
mv tmp/layout-diag/ws-walk/.lessonkit/jobs/conv-* tmp/layout-diag/conv-backup/
env -u http_proxy -u https_proxy -u all_proxy python tmp/layout-diag/defects.py \
    --base-url http://127.0.0.1:3311 --ws walk --paper ps-001 \
    --out tmp/layout-diag/defects-noconv.json --shots tmp/layout-diag/shots-noconv
```

> ⚠️ **行号全部按 `bc488a40` 对**，别按当前工作树对（并发 agent 一直在改 `workbench.css`）：
> ```bash
> git show bc488a40:workbench/server/static/workbench.css | sed -n '1322p'
> ```

---

## 1. 五类缺陷的判定

### 1.1 D1 —— 字段漂移到边框甚至超出

**判定**：三个子判据各判各的。
D1-a **贴边**：文本到所在容器 content box 内缘 < 8px。
D1-b **真的溢出**：`scrollWidth > clientWidth + 1`（横向）或 `scrollHeight > clientHeight + 1`（竖向且 `overflow` 非 auto/scroll）。
D1-c **子元素越界**：子元素右缘 > 父元素 content box 右缘。

| 页面 | D1-a 贴边文本 | D1-b 溢出元素 | D1-c 越界 | 判定 |
|---|---|---|---|---|
| 练习页（组卷入口） | 65 | 6 | 5 | **命中** |
| 练习页（已载入试卷） | 65 | 5 | 5 | **命中** |
| 练习页（练习进行中） | 73 | 19 | 5 | **命中（最重）** |
| 记录中心 | **127** | 15 | 2 | **命中（最重）** |
| 知识点列表 | 80 | 2 | 2 | **命中** |
| 试卷列表 | 26 | 2 | 2 | **命中** |

**逐条证据（知识点列表 · 无对话态 · 最刺眼的那几条）**

| 元素 | 文本 | 所在容器 | 距左内缘 | 距右内缘 | 规则 |
|---|---|---|---|---|---|
| `span.knowledge-meta` | **"20 题"** | `div`（行的 flex 容器） | 599.77 | **0.00** | `workbench.css:1341` `.knowledge-row > div { display:flex; justify-content:space-between }` |
| `h1` | **"知识点"** | `header.page-header` | **0.00** | **0.00** | `workbench.css:777` `.page-header { padding-bottom: 24px; border-bottom: 2px … }` —— **没有左右内距** |
| `p.context-line` | "学习 / 当前章节" | `header.page-header` | **0.00** | 571.03 | `workbench.css:783` `.context-line { margin: 0 0 6px }` |
| `p.side-label` ×4 | "工作区 / 页面 / 设置 / 优先回看" | `nav.side-section.primary-nav` 等 | **0.00** | 217–230 | `workbench.css:785` `.side-label { margin: 0 0 6px }` |
| `label.setting-row` / `a.setting-row` | "运行中发送方式 / 外观设置" | `section.side-section.settings-section` | **0.00** | 171 / 207 | `workbench.css:833` `.setting-row { display:flex; gap:7px }` |
| `span.count-badge` | "3" | `section.side-section.weak-section` | 242.67 | **6.00** | `workbench.css:846` `.count-badge` |
| `a.brand` | "lesson-kit" | `div.topbar-brand` | 59 | **0.00** | `workbench.css:559` |
| `span.meta` | "walk" | `div.topbar-identity` | **0.00** | 42 | `workbench.css:560` |
| `span` | "章" | `label.chapter-lens-toggle` | 17 | **0.00** | `workbench.css:616` |

⇒ **"20 题"贴着右缘**（距右内缘 **0.00 px**）与 **页面大标题左右都贴着**
（`h1` 距左右内缘都是 **0.00 px**）是**两处不同性质的贴边**：
前者是"行内右对齐项没有右侧余量"，后者是**"页头容器压根没有水平内距"**。

**D1-b 真的溢出（可点名的那几类）**

| 元素 | 溢出 | 规则 | 判读 |
|---|---|---|---|
| `aside#left-column` | 横向 **4px** | `workbench.css:726`（`#left-column`）| **resizer 压出内容盒 4px** —— 见 D2 |
| `span.record-activity-weekday` ×7 | 竖向 **8px**（client 14 / scroll 22） | `workbench.css:3209` | 日历星期标签的行盒被截 |
| `a.record-tab` ×4 | 竖向 **4px**（client 36 / scroll 40） | `workbench.css:1700` `.record-tab { min-height: 36px }` | 分段控件的项比槽矮 4px |
| `span.record-verdict-dist-label` | 横向 **2px**（client 34 / scroll 36） | `workbench.css:3365` `.record-verdict-dist-row { grid-template-columns: 34px … }` | 34px 的列装不下"未判定" |
| `input` ×4（练习进行中） | 横向 **13px** / 竖向 **13px**（18×18） | `workbench.css:1821` | 勾选框的盒被内容撑破 |
| `section#time-view.card.lk-card` | 横向 **+14px**（660 / 674） | `workbench.css:2792` `.time-view` | 时间卡的日历比卡宽 14px |
| `div#time-view-content` | 横向 **+36px**（616 / 652） | `workbench.css:2796` `.time-view-content { display:grid; gap:30px }` | **日历网格比容器宽 36px** |
| `span.visually-hidden` | 横向 32 / 竖向 17 | — | **只读屏的 1×1 裁剪元素，按设计如此 ⇒ 不算缺陷** |

**D1-c 越界**

| 父 | 子 | 越界 | 规则 | 判读 |
|---|---|---|---|---|
| `aside#left-column` | `div#left-resizer.column-resizer` | 右 **4px** | `workbench.css:2123` `.column-resizer` | 拖拽手柄按设计压在内容上 |
| `aside#ai-column.agent-rail` | `div#right-resizer.column-resizer` | 左 **20px** | 同上 | 同上 |

### 1.2 D2 —— 组件之间重叠

| 页面 | 兄弟重叠对数 | 重叠配对 | 重叠面积 | 文字压出容器 |
|---|---|---|---|---|
| 全部六页 | **各 1 对** | `div.side-sections` × `div#left-resizer.column-resizer` | **2 788 px²** | 2–5 处（`partial`） |

- **唯一的那一对是拖拽手柄**（`workbench.css:2123` `.column-resizer`）压在左栏内容上 ——
  **按设计如此**（它就是拖拽热区），但它确实覆盖了 2 788 px² 的内容。
- **文字压出容器**：`span.visually-hidden`（1×1 裁剪，按设计）、
  `h1`（页头大字，`partial` —— 字的墨盒比 `h1` 的 border box 高，**行盒/边框盒差异，非布局错**）、
  `h2`、`span.lk-combo-banner__count`、`span.bar-value`。

⇒ **D2 的判定是「不成立」**：**没有一对业务组件真的重叠**。
（唯一重叠的是 resizer 热区，且它是拖拽热区。）

### 1.3 D3 —— 留白严重

**内容占用率（无对话态）**

| 页面 | 左栏 279px | 中栏 660px | 右栏 419px |
|---|---|---|---|
| 练习页（组卷入口） | 21.1% | 22.9% | **2.9%** |
| 练习页（已载入试卷） | 21.1% | 23.0% | **2.9%** |
| 练习页（练习进行中） | 21.1% | 19.6% | **2.9%** |
| 记录中心 | 21.1% | 18.9% | **2.9%** |
| 知识点列表 | 21.1% | **16.8%** | **2.9%** |
| 试卷列表 | 21.1% | 23.2% | **2.9%** |

**判定（地板 20%）**：
- **右栏 2.9% ⇒ 六页全部命中「空得严重」**（左栏 21.1% 刚好压线；中列 16.8%–23.2% 部分命中）
- **内容横向跨度**：右栏 92.4%（**横向几乎占满，竖向几乎空**）⇒ 这正是"看起来很空"的形状：
  **一根 419px 宽、848px 高、只有三小块东西的竖条**。

**纵向断档（> 72px）**

| 列 | 断档数 | 断档值 px | 判读 |
|---|---|---|---|
| 左栏 | 2 | **85 / 211** | 「页面」区与「设置」区之间 85px；设置区与「优先回看」之间 211px |
| 中栏 | 1–3 | 73 / 81 / 86 / 98 / 104 / 110 / 137 | 区块之间的大留白（**这一档是设计里的章节呼吸**，不算缺陷） |
| **右栏** | **2** | **83 / 725** | **725px 的断档 = 右栏从「还没有对话」到底部一片空白** |

⇒ **D3 成立**：右栏 2.9% 占用率 + 725px 断档；
左栏 211px 断档（左栏下半截空纸，`workbench.css:816-825` 记着「下半截空纸收敛」的历史）。

### 1.4 D4 —— 分布密度不均匀

**200×200 px 网格（8 列 × 5 行 = 40 格，无对话态）**

| 页面 | 字符/格 均值 | **方差** | 标准差 | 最大格 | 空格占比 | 左列事件 | 中列事件 | **右列事件** |
|---|---|---|---|---|---|---|---|---|
| 练习页（组卷入口） | 6.98 | 104.57 | 10.23 | 46 | **50%** | 5 | 12 | **1** |
| 练习页（已载入试卷） | 6.55 | 106.75 | 10.33 | 46 | **57.5%** | 5 | 11 | **1** |
| 练习页（练习进行中） | 5.85 | 144.43 | 12.02 | 56 | **60%** | 5 | 17 | **1** |
| 记录中心 | 5.28 | 84.35 | 9.18 | 46 | **57.5%** | 5 | 19 | **1** |
| 知识点列表 | 13.63 | **892.93** | 29.88 | 140 | **52.5%** | 5 | 7 | **1** |
| 试卷列表 | 11.15 | **1 158.88** | 34.04 | 211 | **57.5%** | 5 | 5 | **1** |

**最密 / 最空的三格（知识点列表）**

| | 格坐标 | 字符数 | 内容摘要 |
|---|---|---|---|
| 密 | (400, 600) | **140** | 鸽巢原理 (Pigeonhole Principle) — Theorem 1；鸽巢原理推论：非单射函数 (Corollary 1) |
| 密 | (400, 800) | **126** | r-排列计数公式 P(n,r) = n(n-1)…(n-r+1)；r-排列的阶乘形式 P(n,r) = n!/(n-r)! |
| 密 | (400, 400) | 49 | 减法规则 / 容斥原理（两集合）；除法规则 (Division Rule) |
| 空 | (400, 0) / (600, 0) / (800, 0) | **0** | 顶栏底下那一排 —— 中列顶部有大片空纸 |

⇒ **D4 成立**，两条独立的证据：
1. **列间不均**：右栏 419px 宽，却只有 **1 种视觉事件**（左栏 5、中栏 5–19）
   ⇒ **列间差异 > 2×**，中列 7–19 种 vs 右栏 1 种。
2. **格间不均**：知识点列表方差 **892.93**（其余页 84–1 159），
   **最密格 140 字符 vs 空格 0 字符**，极差 140。
   **中列 (400,600) 格挤进 140 字符，右列 (1000–1200) 那几格几乎是空的。**

### 1.5 D5 —— 部分组件过小 → 骨感

| 页面 | 字号 < 12px 的文字节点 | 分布 | 高度 < 40px 的块 | 分布 | 渲染 < 12px 的点/图标 |
|---|---|---|---|---|---|
| 练习页（组卷入口） | 2 | `span.visually-hidden`×1, `span.count-badge`×1 | 6 | `select#goal-kind`, `span.count-badge`, `div.nav-item.active` | 0 |
| 练习页（已载入试卷） | 2 | 同上 | 6 | 同上 | 0 |
| 练习页（练习进行中） | 2 | 同上 | 17 | `input`×4, `button.outline`×2, `button.primary`×2 | 0 |
| 记录中心 | 9 | `span.record-activity-weekday`×7, `span.visually-hidden`×1, `span.count-badge`×1 | 140 | `level-0`×81, `record-spark-block`×12, `span`×10 | 5 |
| 知识点列表 | 2 | `span.visually-hidden`×1, `span.count-badge`×1 | **42** | **`knowledge-row`×31**, `lk-dot--dash`×4, `div.nav-item.active`×1 | **6** |
| 试卷列表 | 2 | 同上 | 6 | `button.outline`×3, `span.count-badge`, `div.nav-item.active` | 0 |

> `span.visually-hidden` 是只读屏的 1×1 裁剪元素，**按设计如此，不算过小**。

**骨感参照（中列列表行）**

| 页面 | 行类 | 行数 | 行高 | 字号 | 行高 | **字号/行高** | **行高/行高** | 上下内距 |
|---|---|---|---|---|---|---|---|---|
| 知识点列表 | `knowledge-row` | **31** | **38 px** | 14 px | 22 px | **0.368** | 0.579 | 8 + 8 |
| 记录中心 | `record-row` | 8 | **57 px** | 14 px | 20 px | **0.246** | **0.351** | 7 + 7 |

⇒ **D5 成立**，三处：
1. **知识点列表的行高 38px，文字只占 36.8%**（14px 字 / 38px 行）
   ⇒ 所有者例举的 "20px 字 / 38px 行 = 0.53" 在本仓库是
   **"14px 字 / 38px 行 = 0.368"** —— **比那个例子更骨**。
   行的上下内距各 8px，**文字带只占 22/38 = 57.9%**。
2. **31 个 `.knowledge-row` 全部 < 40px**（正好 38px），
   **6 个 `.knowledge-state-dot` 渲染成 10×10px**（< 12px）。
3. **记录中心 140 个块 < 40px**，其中 81 个是日历热力格（`level-0`）—— **那是有意为之的密网格，不算缺陷**；
   但 **`record-spark-block`×12** 与日历星期标签（`span.record-activity-weekday` **11px**，`workbench.css:3209`）
   是**真的过小**。

---

## 2. 专门回答：中栏挤满、右栏空

### 2.1 事实

| 项 | 实测 |
|---|---|
| 右栏宽度 | **419–420 px**（`--shell-col-right: 420px`，`workbench.css:127` / `709`） |
| 右栏可见高 | 848 px |
| 右栏**内容占用率** | **2.9%**（无对话） / 27.9%（有 40 条对话） |
| 右栏**内容横向跨度** | 92.4%（**横向占满、竖向空**） |
| 右栏里的东西 | 「对话」标签 + 「新建」按钮 + 底部一行「还没有对话」 = **18 个叶子块**（有对话时 177 个） |
| 右栏纵向断档 | **83 px** 与 **725 px** |
| 右栏的视觉事件种类 | **1 种**（全页 419px × 848px 只用了一种底/影/边组合） |
| 中列内容宽 | **660 px**（`#middle` 740 − 左右各 40px 内距，`workbench.css:734` `#middle { padding: 34px 40px 48px }`） |
| 中列的内容上限 | `--shell-measure: 880px`（`workbench.css:124`）⇒ **880px 这一档此刻完全没被用上**（660 < 880） |

### 2.2 **布局能不能自己解决？—— 能，而且机制已经存在**

**`#layout` 的三栏模板（`workbench.css:713`）**

```css
#layout {
  --wb-col-left:  var(--shell-col-left, 280px);
  --wb-col-right: var(--shell-col-right, 420px);
  grid-template-columns: var(--wb-col-left) minmax(0, 1fr) var(--wb-col-right);
}
/* workbench.css:725 —— 收起机制已经写好了 */
#layout[data-ai-collapsed] { grid-template-columns: var(--wb-col-left) minmax(0, 1fr) 0px; }
/* workbench.css:752 */
#layout[data-ai-collapsed] #ai-column { padding: 0; border-left: none; min-width: 0; }
```

**但它没有触发器**：`workbench.js:5700-5704`

```js
function fitAiColumn() {
  if (!layout) return;
  if (window.innerWidth < 1024) layout.setAttribute("data-ai-collapsed", "1");
  else layout.removeAttribute("data-ai-collapsed");
}
```

⇒ **只有窗口 < 1024px 时才置位**；1440px 下这个属性**从不出现**。
`workbench.css:719` 的注释也写着「宽屏 `data-ai-collapsed` 从不出现（JS 只在 < 1024px 置位）」。

### 2.3 三条路的实测收益（在 1440px 的知识点列表页当场量）

| 方案 | 右栏 | 中栏容器 | **中列内容宽** | 相对现状 | 动什么 |
|---|---|---|---|---|---|
| **A 现状** | 420px | 740px | **660 px** | — | — |
| **B 右栏拖到地板 360px** | 360px | 800px | **720 px** | **+60 px（+9.1%）** | 纯 CSS：`--shell-col-right: 420px → 360px`（`workbench.css:127`）；或用户拖 `right-resizer`（`workbench.js:5714` `COLUMN_MIN.right = 360`） |
| **C 置 `data-ai-collapsed="1"`** | **0 px** | 1160px | **880 px**（被 `--shell-measure` 封顶） | **+220 px（+33.3%）** | **需要触发器** —— 属交互变更 |

**结论**：
- **纯布局（不动交互）能拿到的**：只有 **B**，最多 **+60px**（9.1%）——
  因为 `#ai-column { min-width: 360px }`（`workbench.css:749`）与
  `COLUMN_MIN.right = 360`（`workbench.js:5714`）**都是硬地板**。
  ⇒ **单靠调 CSS，右栏最多缩到 360px，中列最多 +60px。**
- **要真正解决（+220px，右栏整列让位）**，必须让 `data-ai-collapsed` 在宽屏也有机会置位
  —— 而「什么时候置位」取决于**数据状态（有没有对话）**，那是一个**行为/交互决策**。
  ⚠️ **按约定，本报告只登记、不实现**（见 §4 的 F3）。
- **另一条纯布局的路**：中列的内容轨宽 `--shell-measure: 880px`（`workbench.css:124`）
  在 1440px 下**根本没被用上**（中列只有 660px）⇒
  **即使不动右栏，把中列的内容轨宽放到 880px 也没有地方放**（列本身就窄）。
  ⇒ **必须从右栏拿空间**，或**从左栏拿**（左栏 280px，地板 200px ⇒ 最多再拿 80px）。

---

## 3. 病因解释（原来的 11 项指标）

> 这一节回答"**为什么会出现上面五条缺陷**"。
> 数字全部来自同一轮测量（`tmp/layout-diag/measurements.json`，对应 CSS `6046575b…`）。

### 3.1 面的数量：「同一个带影卡被重复 8–31 次」

| 页面 | 面块数（面积口径） | （尺寸口径） | 中列 | 有影比例 | 贡献最多的类 |
|---|---|---|---|---|---|
| 练习页（组卷入口） | 17 | 13 | 9 | 17.6% | `side-section`×3, `<input>`×3, `card`×2 |
| 练习页（已载入试卷） | 17 | 13 | 9 | 17.6% | 同上 |
| 练习页（练习进行中） | 24 | 20 | 16 | 16.7% | `option-row`×4, `side-section`×3, `<input>`×3 |
| 记录中心 | **37** | 31 | 29 | **62.2%** | `record-row`×8, `record-run`×5, `record-run-progress`×5, `record-summary`×4 |
| 知识点列表 | **42** | **8** | 34 | **76.2%** | **`knowledge-row`×31** |
| 试卷列表 | 13 | 12 | 5 | 38.5% | `side-section`×3, `practice-set-item-body`×3 |

> ⚠️ **面积口径 vs 尺寸口径**：题干写「面积 ≥ 100×40 px」。
> 面积口径 = 面积 ≥ 4000 px²；尺寸口径 = 宽≥100 **且** 高≥40。
> **知识点列表的每一行是 660×38 —— 正好差 2px 落在尺寸口径门外**
> ⇒ 两种口径下这一页的面块数是 **42 vs 8**。
> **下一棒若只按尺寸口径看，会完全看不见这一页最严重的问题。**

### 3.2 砖块群专项：**每一块都一模一样**

| 页面 | 重复最多的类 | 个数 | 高 min/中位/max | 高 σ | 带影 | 行间留白 px |
|---|---|---|---|---|---|---|
| 记录中心 | `record-row` | 8 | 57/57/57 | **0.0** | **8/8** | 6, 6, 6, 6, 6, 6 |
| 知识点列表 | `knowledge-row` | **31** | 38/38/38 | **0.0** | **31/31** | 8, 8, 8, 8, 8, 8 |
| 练习页（进行中） | `option-row` | 4 | 68/68/68 | 0.0 | 0/4 | 18, 18, 18 |

⇒ **"组件尺寸乱"是伪命题**：重复群体的高度一致性是**完美的（σ = 0）**。
⇒ 这也解释了 D5 的骨感：**38px 的行里只有 14px 的字**，
**行高被"统一"到了比字高 2.7 倍**，于是每一行都是"一条细线 + 两圈空"。

### 3.3 样式种类：**已经被管住了**

| 页面 | 底色档 | 阴影档 | 圆角档 | 底色取值（暖纸） | 圆角取值 |
|---|---|---|---|---|---|
| 练习页（组卷/载卷） | 3 | 2 | 3 | `rgb(242,236,225)`, `rgb(255,253,247)`, `rgb(255,255,255)` | 0px, 12px, 6px |
| 练习页（进行中） | 3 | 4 | 4 | 同上 | 0px, 12px, 6px, `0px 0px 12px 12px` |
| 记录中心 | 3 | 3 | 3 | + `rgba(61,52,37,.11)` | 0px, 12px, 999px |
| 知识点列表 | **2** | 2 | 3 | `rgb(242,236,225)`, `rgb(255,253,247)` | 0px, 12px, 6px |
| 试卷列表 | **2** | 2 | 2 | 同上 | 0px, 12px |

⇒ **"样式太杂"不是病因** ⇒ **"统一圆角 / 统一阴影"这类改法本身治不了问题**。

### 3.4 间距刻度：**样式表有 8 档尺子，只用了 6 档**

| 页面 | 间距取值种类 | 落在 `--sp-*` 档上的种类 | 散值种类 | 散值 Top6 |
|---|---|---|---|---|
| 练习页（组卷/载卷） | 29 | **6** | 22 | 2×200, 7×108, 9×107, 5×89, 10×39, 15×30 |
| 练习页（进行中） | 31 | **6** | 24 | 2×204, 7×109, 9×107, 5×89, 10×42, 6×42 |
| 记录中心 | **36** | **6** | 29 | 2×188, 7×123, 9×111, 14×54, 6×49, 10×31 |
| 知识点列表 | 27 | **6** | 20 | 2×197, 7×108, 9×107, 6×96, 10×26, 1×13 |
| 试卷列表 | 29 | **6** | 22 | 2×190, 9×107, 7×103, 10×44, 6×26, −1×12 |

`--sp-1..--sp-8` = 4/8/12/16/24/32/48/64（`workbench.css:53-60`），
**六个页面都只用了 6 档**（`--sp-6`=32 从未出现），
其余 **20–29 个取值全是散值**：1, 2, 3, 5, 6, 7, 9, 10, 14, 15, 18, 20, 22, 26 px。
⇒ **卡片内距档数 8–13**，落在 `--sp-*` 上的边值只占 **15.4%–41.7%**。

### 3.5 两套竖向节奏

| 页面 | 中列留白序列 | 频次 |
|---|---|---|
| 知识点列表 | `[28, 16, 92, 8×30]` | **8px×30** + 章节级 28/16/92 |
| 记录中心 | `[28, 20, 36×3, 116, 10×4, 138, 6×7]` | **6px×7** + 10px×4 + 36px×3 + 116/138 |
| 练习页（组卷） | `[28, 196]` | 两档 |

⇒ **视觉节奏本身不乱**（每页留白只有 **2–7 种**取值），
**问题是"行堆自带的 6–8px 缝"插进了"章节级 28–40px 的缝"中间** ——
两套缝差 3.5–5 倍 ⇒ 眼睛读到的是"另一种材质"，这就是"积木堆"的来源。

### 3.6 其它（供下一棒参考）

- **对齐同盟**：记录中心左边界 **10 种**（参照 4）——
  四张统计卡的栅格是 `320 / 488 / 656 / 824`，实测 `320 / 488 / 655 / 823`（相邻差 168/167/168）
  ⇒ **浮点百分比让四条边各差 1px**（`workbench.css:3174`）。
  知识点列表中列只有 **2 种**（320 / 1020）⇒ **它其实是最对齐的一页**。
- **嵌套深度**：六页都是 **3**（参照 ≥3 即高），但那 3 层是**外壳三件套**，内容侧最深只有 2 层。
- **字号档**：8–14 档，但 **96.9%–99.3% 的文字命中 `--fs-*`**；
  真正越界的只有 `13.33px`（浏览器默认 `<small>`，每页 2–8 个）与 15/20/22/30px（各 1 个）。
- **首屏视觉事件**：11–15（参照 10）⇒ 六页全部"眼睛没有落点"。

### 3.7 所以：**「面太多」还是「尺寸/样式不齐」？**

**照数字读：尺度不齐更重。**
把 11 项指标各自除以参照线再按族取均值（面族 6 项 / 尺度族 4 项）：

| | 面族 | 尺度族 |
|---|---|---|
| 六页合计 | 6.66 | **14.59** |
| 占比 | **31%** | **69%** |

**但这个 31/69 有一个已知偏差，当场说清**：

1. **尺度族四项全部超线，且「间距档」与「内距档」是同一件事的两个测法**
   （散值高度重叠：1/2/5/6/7/9/14/18/20/22 px 同时出现在两者里）⇒ **尺度族被这一条重复加权**。
2. **「间距取值档」是样式表纪律指标，不是视觉指标** —— 它对页面上每个元素统计（含控件内部）。
   视觉节奏（§3.5）只有 **2–7 种**取值。
3. **组件尺寸其实已经很齐** —— 砖块群高度 σ = **0.0**，字号 97%–99% 命中 token，
   底色/阴影/圆角档数**全部 ≤ 参照线**。

**⇒ 裁决（三条）：**

1. **五条缺陷的形状由"布局"决定，不是由"组件样式"决定** ——
   组件本身（圆角 12px、阴影 `--elev-1`、字号 14px）是统一的；
   病在**这些统一件被放在什么位置、之间留多少、谁占了哪一栏**。
2. **"面太多"与"尺度不齐"不是两条并列的路，是同一条路的两端**：
   去掉"每行一张卡"（→ 面变少）与"行缝回到页面节奏同一档"（→ 节奏合一），
   改的是**同一段 CSS**（`workbench.css:1322` / `3401`）。
   **只做其一都不够**。
3. **"把卡片尺寸调一致"这条路已经被数据堵死** —— 它们本来就一致（σ=0）。
   **不该**把预算花在"统一圆角 / 统一阴影 / 统一字号"上。

---

## 4. 按可改动性排序的修复清单

> 排序 = **（能消掉几条缺陷）× 确定性 ÷ 代价**。
> 「碰不碰交互逻辑」逐条查过：**F1–F2、F4–F11 全部是纯 CSS**；
> **F3 明确需要交互变更 ⇒ 只登记、不实现**。

### F1 ★★★★★ —— 行内右对齐项没有右侧余量（"20 题"贴着右缘）

- **缺陷**：D1-a ｜ **实测**：`span.knowledge-meta` 距右内缘 **0.00 px**（知识点列表 31 行全中）
- **规则**：`workbench.css:1341` `.knowledge-row > div { display:flex; justify-content:space-between; gap: var(--sp-3) }`
  ＋ `workbench.css:1333` `.knowledge-meta { float: right; … }`
  （行容器 `workbench.css:1322` 的 padding 是 `var(--sp-2) var(--sp-4)` = 8px 16px，
  ⇒ **距卡片边 16px 是有的，距内容区边 0px**）
- **碰交互逻辑吗**：**不碰**（`justify-content` / `padding`）
- **代价**：**1–2 行 CSS**。给 `.knowledge-meta` 加 `padding-right: var(--sp-2)`，
  或把行容器改成 `padding-right: var(--sp-5)`。
  ⚠️ 加内距会让 38px 的行变 40/42px ⇒ **与 F2 一起改，别分两次**。

### F2 ★★★★★ —— 页头容器没有水平内距（标题左右都贴）

- **缺陷**：D1-a ｜ **实测**：`h1`("知识点") 距左内缘 **0.00**、距右内缘 **0.00**；
  `p.context-line` 距左 **0.00**；左栏 `p.side-label`×4 / `setting-row`×2 距左 **0.00**
- **规则**：
  - `workbench.css:777` `.page-header { position: relative; padding-bottom: 24px; border-bottom: 2px solid var(--rule-structure) }`
    ⇒ **只有 `padding-bottom`，没有左右内距**（`workbench.css:771` 的 `.page-header, .page-content { max-width: var(--shell-measure); margin: auto }` 也无内距）
  - `workbench.css:783` `.context-line, .section-kicker, .side-label { margin: 0 0 6px; … }` ⇒ 零内距
  - `workbench.css:833` `.setting-row { display:flex; align-items:flex-start; gap:7px; … }` ⇒ 零内距
  - `workbench.css:785` `.side-label { margin: 0 0 6px; color: var(--ink-faint); font-size: 12px; font-weight: 600; letter-spacing: .05em }`
- **碰交互逻辑吗**：**不碰**
- **代价**：**几行 CSS**（给 `.page-header` 加 `padding-inline: var(--sp-2)`，
  给 `.side-label` / `.setting-row` 加左内距）。
  ⚠️ **左栏的总内距已经是 `16px 12px 20px`（`workbench.css:825`）** ——
  加内距会把左栏内容整体右移，**要连带核 `.nav-item` 的命中区与 `#left-resizer` 的位置**。

### F3 ★★★★★ —— 右栏 2.9% 占用率 / 725px 断档（**需交互 ⇒ 只登记**）

- **缺陷**：D3 + D4 ｜ **实测**：右栏 419×848，内容占用率 **2.9%**，
  纵向断档 **83 / 725 px**，视觉事件 **1 种**，空格占比 **50–60%**
- **规则**：
  - `workbench.css:713` `grid-template-columns: var(--wb-col-left) minmax(0, 1fr) var(--wb-col-right)`
  - `workbench.css:127` `--shell-col-right: 420px`；`workbench.css:749` `#ai-column { min-width: 360px }`
  - `workbench.css:725` `#layout[data-ai-collapsed] { grid-template-columns: var(--wb-col-left) minmax(0, 1fr) 0px; }` ← **机制已在**
  - `workbench.js:5700-5704` `fitAiColumn()` ← **只在 < 1024px 置位**
- **纯布局能拿到多少**（当场实测）：**+60px**（右栏 420→360），
  因为 `min-width: 360px` 与 `workbench.js:5714` `COLUMN_MIN.right = 360` 都是硬地板。
- **真正的解（+220px，右栏整列让位、中列内容 660 → 880px）**：
  让 `data-ai-collapsed` 在**宽屏 + 无对话**时置位。
  ⚠️ **这是行为/交互决策**（什么时候收起、能不能手动再展开、收起状态存哪）
  ⇒ **按约定只登记，不实现**。⇒ **交给所有者裁决**。
- **纯布局的次优解（不改交互）**：把 `--shell-col-right` 从 420 降到 360（`workbench.css:127`）
  ⇒ 中列内容 660 → **720px**（+9.1%），一行 CSS。**代价：右栏本来就不够宽，聊天标题会换行**。

### F4 ★★★★☆ —— 日历比容器宽 36px（时间卡横向溢出）

- **缺陷**：D1-b ｜ **实测**：`div#time-view-content` 横向 **+36px**（client 616 / scroll 652）、
  `section#time-view.card.lk-card` 横向 **+14px**（660 / 674）
- **规则**：`workbench.css:2792` `.time-view { … }`、`workbench.css:2796` `.time-view-content { display: grid; gap: 30px }`
  ＋ 服务端 `grid-auto-rows:30px` 的 7×12 日历（`workbench.css:3022` `.calendar-cell` 一族）
- **碰交互逻辑吗**：**不碰**（纯宽度 / 网格列）
- **代价**：**几行 CSS**（网格列宽改成 `minmax(0, 1fr)` 或减小固定列宽）。
  ⚠️ **要保住"格宽 ~13px / gap 4px"的既有几何**（`workbench.css` 注释里写明那是「宽扁块」的根因）

### F5 ★★★★☆ —— 分段控件与判定分布的标签装不下

- **缺陷**：D1-b ｜ **实测**：`a.record-tab` ×4 竖向 **+4px**（36/40）；
  `span.record-verdict-dist-label` 横向 **+2px**（34/36）；`span.record-activity-weekday` ×7 竖向 **+8px**（14/22）
- **规则**：`workbench.css:1700` `.record-tab { min-height: 36px; padding: 0 14px; border-radius: var(--r-pill) }`；
  `workbench.css:3365` `.record-verdict-dist-row { grid-template-columns: 34px minmax(0,1fr) 24px; gap: 8px }`；
  `workbench.css:3209` `.record-activity-weekday { … }`
- **碰交互逻辑吗**：**不碰**
- **代价**：**各 1 行 CSS**（把 36 → 40、34 → 36、日历星期行盒 14 → 22）。
  ⚠️ 改 `.record-tab` 高度会让分段控件整体高 4px（`workbench.css:1690` 的槽高要一起改）。

### F6 ★★★☆☆ —— 知识点行 38px × 14px 字 = 骨感 0.368

- **缺陷**：D5 ｜ **实测**：31 行全部 38px 高（< 40），
  字号/行高比 **0.368**（所有者例举的是 0.53 ⇒ 本仓库**更骨**）；
  6 个状态点渲染 **10×10px**（< 12）
- **规则**：`workbench.css:1322` `.knowledge-group__cards > .knowledge-row { margin-top: var(--sp-2); padding: var(--sp-2) var(--sp-4); … }`
  ⇒ 行高 38 = 8 + 22（`--fs-body` 14px/22px）+ 8
- **碰交互逻辑吗**：**不碰**
- **代价**：**1 行 CSS**（`padding: var(--sp-2) var(--sp-4)` → `var(--sp-3) var(--sp-4)` ⇒ 行高 46px，比 0.368 变成 0.478）。
  ⚠️ **代价是页高**：31 行 × (+8px) = **+248px**。
  ⚠️ **和 F1、F7、F8 必须一起改**（同一个元素的三处值）。

### F7 ★★★☆☆ —— 行堆的 6–8px 缝 vs 章节级 28–40px 的缝（两套节奏）

- **缺陷**：D4 的"格间不均" + §3.5 ｜ **实测**：知识点列表 `[28, 16, 92, 8×30]`；
  记录中心 `[…, 36×3, …, 10×4, …, 6×7]`
- **规则**：`workbench.css:1322` `margin-top: var(--sp-2)`（8px）；
  `workbench.css:3401` `.record-row { margin: 0 0 6px; … }`（6px）；
  `workbench.css:3382` `.record-run { margin: 0 0 10px; … }`（10px）
- **碰交互逻辑吗**：**不碰**
- **代价**：**几行 CSS**（行缝提到 16px 那一档）。
  ⚠️ **代价是页高**：知识点 +248px、记录中心 +80px。
  ⚠️ 走查基线记着 `?view=attempts` 中栏 `scrollHeight = 8951px`（`workbench.css:3400` 注释）—— **改完要重核**。

### F8 ★★★☆☆ —— 11px 的小字与 10px 的状态点

- **缺陷**：D5 ｜ **实测**：每页 2 个 <12px 文字（`span.count-badge` 11px、浏览器默认 `small` 13.33px），
  记录中心另有 7 个 `span.record-activity-weekday` 11px；知识点列表 6 个 `lk-dot` 渲染 **10×10**
- **规则**：`workbench.css:846` `.count-badge`；`workbench.css:3209` `.record-activity-weekday`；
  `workbench.css` 的 `lk-dot` 族（`--r-pill` 圆点）
- **碰交互逻辑吗**：**不碰**
- **代价**：**1–2 行 CSS 兜底**（`small { font-size: var(--fs-label) }` 之类）+ 点直径 10 → 12。
  ⚠️ **点从 10px 改到 12px 会让 31 行的行高变化** ⇒ **与 F6 一起改**。

### F9 ★★☆☆☆ —— 四张统计卡没落在整数像素栅格上

- **缺陷**：D4 的"列间不均" ｜ **实测**：左边界 **10 种**（参照 4），
  统计卡落在 `320 / 488 / 655 / 823`（本该 `320 / 488 / 656 / 824`）
- **规则**：`workbench.css:3174` `.record-summary-grid { grid-template-columns: repeat(4, minmax(0,1fr)); gap: 10px }`；
  `workbench.css:3183` `.record-dashboard-grid { grid-template-columns: minmax(0,3fr) minmax(220px,2fr); gap: 12px }`
- **碰交互逻辑吗**：**不碰**
- **代价**：**1–2 行 CSS**。⚠️ **660px 轨宽 ÷ 4 不整除**（630/4 = 157.5）——
  要么轨宽改 648，要么接受"三列等宽 + 一列自适应"。**这是取舍，不是 bug。**

### F10 ★★☆☆☆ —— 练习页首屏被 21 个日历格占住

- **缺陷**：D4 ｜ **实测**：练习页首屏条目 = `calendar-cell`×21 / ×14；首屏视觉事件 14 / 15
- **规则**：`workbench.css:3022` `.calendar-cell` 一族 + `workbench.css:2796` `.time-view-content`
- **碰交互逻辑吗**：**不碰**
- **代价**：**几行 CSS**（格子密度）或**改布局顺序**（把日历挪出首屏）。
  ⚠️ **取舍题**：日历是"计划"信息，首屏价值低于"组卷"。

### F11 ★☆☆☆☆ —— resizer 手柄压在内容上（**按设计，但登记**）

- **缺陷**：D2（唯一的一对重叠）+ D1-c ｜ **实测**：
  `div.side-sections` × `div#left-resizer` 重叠 **2 788 px²**；
  `#left-resizer` 越出 `#left-column` content box **4px**；`#right-resizer` 越出 **20px**
- **规则**：`workbench.css:2123` `.column-resizer { … }`
- **碰交互逻辑吗**：**不碰**
- **代价**：**0–1 行 CSS**（把手柄改成贴边而不是压边）。⚠️ **改了会影响拖拽热区的手感** ⇒ 建议只登记。

---

## 5. 局限与诚实边界

1. **只测了 1440×900 一个视口**。窄视口（768 / 1024）三栏会折叠、度量会变 —— **没测，不猜**。
2. **D1-a 的"所在容器"取"最近块级祖先"**：很多贴边是"右对齐的 flex 子项贴内容区右缘"，
   距**卡片边**还有 16px。报告里同时列了"距容器内缘"与"距卡片内缘"两个数，
   **不要把它们混为一谈**。
3. **`span.visually-hidden` 的 1×1 裁剪**、**`h1` 的墨盒比 border box 高** ——
   这两类是**按设计 / 行盒差异**，已单独标注，不计成缺陷。
4. **D3 的"内容占用率"按"叶子内容块面积"算**，不是按"墨迹像素"算 ——
   换个算法数值会变，**但右栏 2.9% vs 中列 16.8–23.2% 这个量级差不会变**。
5. **记录中心的数字随练习轮次增长**（每轮多一条作答行）⇒ 跨轮比较要注明轮次。
6. **本报告的数字与 `file:line` 都锚在 `bc488a40`**（CSS sha `6046575b…`）。
   并发 agent 一直在改 `workbench.css` ⇒ **CSS 一改就要重跑**。
   （实测：CSS 改了 +5 187 字节之后，**11 项指标 × 6 页 × 2 主题里 372/372 个关键值一字未变**
   ⇒ **这些是结构性问题，不是某一版 CSS 的偶然。**）
7. **这一份没有提任何审美主张**，也**没有给合成分数**。
   "好看"不在本报告的能力范围内；**五条独立缺陷逐条判，才是下一棒能直接用的东西**。

---

## 附录 A：测量脚本

脚本在 `tmp/layout-diag/`（`tmp/` 被 `.gitignore` 忽略，不进版本库）。
**关键代码内联在下面**；完整脚本照着 §0.4 的命令即可复跑。

### A.1 D1-a：文本贴边

```javascript
// 文本节点 → 矩形
const range = document.createRange();
range.selectNodeContents(textNode);
const rects = Array.from(range.getClientRects()).filter(r => r.width > 0 && r.height > 0);

// 最近块级可见祖先 = 「所在容器」
function nearestBlock(el) {
  let p = el.parentElement;
  while (p && p !== document.body && p !== document.documentElement) {
    const cs = getComputedStyle(p);
    if (BLOCKISH(cs.display) && visible(p)) return p;
    p = p.parentElement;
  }
  return null;
}
// 容器的 padding box 内缘 = content box 边缘
function contentBox(el) {
  const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
  const bl = parseFloat(cs.borderLeftWidth) || 0, br = parseFloat(cs.borderRightWidth) || 0;
  const pl = parseFloat(cs.paddingLeft) || 0,  pr = parseFloat(cs.paddingRight) || 0;
  return {left: r.left + bl + pl, right: r.right - br - pr};
}
const dLeft  = textRect.left  - cb.left;
const dRight = cb.right - textRect.right;
if (dLeft < 8 || dRight < 8) { /* 贴边 */ }
```

### A.2 D1-b / D1-c：溢出

```javascript
// D1-b
const hOver = el.scrollWidth  - el.clientWidth;
const vOver = el.scrollHeight - el.clientHeight;
const scrollsY = cs.overflowY === 'auto' || cs.overflowY === 'scroll';
if (hOver > 1 || (vOver > 1 && !scrollsY)) { /* 溢出 */ }

// D1-c：子元素右缘 > 父 content box 右缘
const pcb = contentBox(el);
for (const child of el.children) {
  const cr = child.getBoundingClientRect();
  if (cr.right > pcb.right + 1) { /* 越界 */ }
}
```

### A.3 D2：兄弟重叠

```javascript
const kids = [...parent.children].filter(k =>
  visible(k) && getComputedStyle(k).position !== 'fixed' &&
  k.getBoundingClientRect().width > 0 && BLOCKISH(getComputedStyle(k).display));
for (let i = 0; i < kids.length; i++)
  for (let j = i + 1; j < kids.length; j++) {
    const a = kids[i].getBoundingClientRect(), b = kids[j].getBoundingClientRect();
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (w > 0.5 && h > 0.5) { /* 重叠 w×h */ }
  }
```

### A.4 D3：列占用率（叶子内容块）

```javascript
// 叶子块 = 有直接文本、且没有后代元素带文本
const leaves = [...col.querySelectorAll('*')].filter(el => {
  const own = [...el.childNodes].some(n => n.nodeType === 3 && n.nodeValue.trim());
  if (!own) return false;
  return ![...el.querySelectorAll('*')].some(c =>
    [...c.childNodes].some(n => n.nodeType === 3 && n.nodeValue.trim()));
});
// 分母 = 列的可见盒；分子 = 叶子块与可见盒的交集面积之和
const visW = col.clientWidth, visH = col.clientHeight;
let used = 0;
for (const el of leaves) {
  const r = el.getBoundingClientRect();
  const ix = Math.min(r.right, vis.right) - Math.max(r.left, vis.left);
  const iy = Math.min(r.bottom, vis.bottom) - Math.max(r.top, vis.top);
  if (ix > 0 && iy > 0) used += ix * iy;
}
const occupancy = used / (visW * visH);
```

### A.5 D4：200×200 网格密度

```javascript
const cols = Math.ceil(innerWidth / 200), rows = Math.ceil(innerHeight / 200);
const cells = Array.from({length: cols * rows}, (_, i) => ({
  x: (i % cols) * 200, y: Math.floor(i / cols) * 200, chars: 0, texts: [],
}));
// 文本按矩形中心落格，统计非空白字符数
// painted 元素按矩形中心落格，统计 (底色,阴影,边框) 三元组去重 = 视觉事件
```

### A.6 D5：骨感比

```javascript
// 中列里出现次数最多的类 = 列表行；取中位那行
const sample = rows[Math.floor(rows.length / 2)];
const textEl  = sample.querySelector('a, span, strong, p') || sample;
const fs = parseFloat(getComputedStyle(textEl).fontSize);
const lh = parseFloat(getComputedStyle(textEl).lineHeight);
text_height_ratio = fs / sample.offsetHeight;   // 知识点列表 14/38 = 0.368
line_height_ratio = lh / sample.offsetHeight;   // 知识点列表 22/38 = 0.579
```

---

## 附录 B：截图索引

`reports/LAYOUT-DIAGNOSIS-shots/`（1440×900，DPR=1，暖纸 + 夜纸各一套）

| 文件 | 页面状态 | 主题 |
|---|---|---|
| `practice-warm.png` / `practice-night.png` | 练习页（组卷入口，无试卷） | 暖 / 夜 |
| `practice-paper-warm.png` / `practice-paper-night.png` | 练习页（已载入试卷 `ps-001`） | 暖 / 夜 |
| `practice-in-progress-warm.png` / `practice-in-progress-night.png` | 练习页（练习进行中，第 1 题） | 暖 / 夜 |
| `records-warm.png` / `records-night.png` | 记录中心（总览） | 暖 / 夜 |
| `kps-warm.png` / `kps-night.png` | 知识点列表（31 行，**有 40 条对话**） | 暖 / 夜 |
| `practice-sets-warm.png` / `practice-sets-night.png` | 试卷列表（1 份试卷） | 暖 / 夜 |
| `noconv/*.png` | **同上一套，但对话栏为空**（= 所有者截图那一态） | 暖 / 夜 |

> **`noconv/kps-warm.png` 就是所有者那张图的可复现版本**：
> 中栏 31 行知识点挤满、右栏 419px 宽只剩「对话 / 新建 / 还没有对话」。

---

## 附录 C：与本报告相关的既有裁决

- `decisions.md` **A-124**：整体构成是独立于组件形态的一层问题；先出版式候选板让所有者挑。
- `decisions.md` **A-125**：积木感的病因**不是样式太杂**，是「同一卡片重复 8–31 次」＋「尺度不齐」。
  ⇒ 本报告的 §3 是 A-125 的完整实测底稿。
- `decisions.md` **A-126**：C1 交工的六条待裁决（三条主会话裁、三条留登记）。
  ⇒ 本报告**不选边**；F3 只登记不实现。

---

*探针脚本：`tmp/layout-diag/measure.py`（11 项指标）、`tmp/layout-diag/defects.py`（D1–D5）、
`tmp/layout-diag/analyse.py` + `tables.py` + `defect-tables.py`（出表）。
原始 JSON：`tmp/layout-diag/measurements.json`、`defects-seeded.json`、`defects-noconv.json`。
本报告只写不改任何产品文件；`workbench/` 在测量全程只读。*
