# IMPL-L1 · 三栏几何与响应式四档（`layout-spec.md` §1 + §7）

> **Wave ①** —— 版式重做的第一波。**只动外壳几何**，不碰组件形态、不碰图谱。
>
> 规格：`design-notes/layout-spec.md` §1（三栏几何规格）· §7（响应式）
> 裁决：`decisions.md` **A-136**（夹取顺序）· **A-137**（地板随档位）·
> **A-140**（单一轨 880）· **A-141**（C 档 + 写进 delta）
> 口径：`acceptance.md` §3.5（S-11）· `tools/walkthrough/probe.py`
> （`probe_responsive` / `probe_drawer`）

---

## 0. 三条不可让步的边界（`AGENTS.md`）

1. **只动 Shell 层**：DOM 结构与顺序、视觉分组、纯装饰、动效。
   **不新增请求、不改载荷、不改状态机。**
2. **不动图谱**：图谱页按 `layout-spec.md` §0.2「范围外」处理 ⇒
   本波在图谱作用域里**冻结**三处外壳值（见 §4.3），保住 G-5「逐像素零变化」。
3. **不并 main、不 push**（所有者未授权）。同文件**串行**——本波只有一条线。

---

## 1. 交付内容

| # | 内容 | 规格出处 |
|---|---|---|
| 1.1 | 列宽族 `--shell-col-*` **从 `:root` 移到 `#layout`** | §0.4（D-10：「写在 `#layout` 上，不写 `:root`」） |
| 1.2 | 四档列宽 + 地板 + 上限**全部落在 CSS**（JS 只读不算） | §1.4 · A-137 |
| 1.3 | 四档 `@media`：**B** ≤1439 · **C** ≤1279（右栏出栅格转抽屉）· **D** ≤1023 · **E** ≤767 | §7.1 |
| 1.4 | C 档：右栏成覆盖层抽屉 + 顶栏「Agent 对话」常驻入口；`fitAiColumn()` 阈值 1024 → **1279** | §7.4 · §7.7 · §1.2 配套规则 5 |
| 1.5 | 夹取按「**先夹右**」；地板随档位（A 360 / B 340） | **A-136** · **A-137** |
| 1.6 | 中栏内边距 `28/32/72`（A）→ `28/28/64`（B）→ `24/24/64`（C）→ `24/18/48`（D）→ `16/12/40`（E） | §1.7 · §7.1 |
| 1.7 | 栏间分隔线 `1px solid var(--ink-strong)` → `1px solid var(--rule-hair)` | §1.7（「删除纯黑 1px 线」） |
| 1.8 | 标题 h1 = `30px / 38px / -0.02em`（A/B）→ 28px（C）→ 24px（D）→ 22px（E） | §4.1② · §7.1 |
| 1.9 | 拖拽柄**整体收进栏内**（`right:-4px` → `right:0`） | §1.2 验收第 7 条 |
| 1.10 | 顶栏工作区名 `max-width:36ch` + 省略号（断点守卫第 3 条） | §7.8 |
| 1.11 | **四档表写进 spec delta**（MODIFIED「Three-column shell with navigation」补一段 + 三个 Scenario） | **A-141** · `AGENTS.md` 纪律 3 |
| 1.12 | **图谱页冻结**（中栏内边距 / 栏间分隔线 / h1） | §0.2 · G-5 |

---

## 2. 独占文件（**不要碰别的**）

| 文件 | 动什么 |
|---|---|
| `workbench/server/static/workbench.css` | 1.1–1.10、1.12 |
| `workbench/server/static/workbench.js` | 1.4–1.5 的阈值与夹取 |
| `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md` | 1.11 |

⚠️ **不碰**：`pipeline/` · `pool/scripts/` · `lessonkit.py` · `workbench/server/pages.py`
· `agent-ui.css`（§6 的右栏是下一波）· 任何图谱 JS。

---

## 3. 关键实现口径（**照抄，别自己发挥**）

### 3.1 列宽的唯一来源在 CSS

```css
#layout {
  --shell-col-left: 280px;        /* A 档默认 */
  --shell-col-right: 420px;
  --shell-col-middle-min: 420px;
  --shell-col-left-min: 200px;    /* A-137：地板随档位 */
  --shell-col-left-max: 480px;
  --shell-col-right-min: 360px;
  --shell-col-right-max: 560px;
  --wb-col-left: var(--shell-col-left, 280px);   /* JS 的写入点 */
  --wb-col-right: var(--shell-col-right, 420px);
}
```

- ⚠️ **JS 必须写 `--wb-col-*` 而不是 `--shell-col-*`**：
  JS 要从样式表读**档位默认**；若把默认值也写成行内，下次换档时
  `getComputedStyle` 读到的就是**上一档的行内值**，档位永远切不过去。
- ⚠️ `:root` 里**必须删掉**这五个变量（§0.4 明写「不写 `:root`」）。

### 3.2 夹取：**先夹右**（A-136）

```js
// 先夹右（用当前左栏宽）→ 再夹左（用已夹好的右栏宽）
var right = clamp(rawRight, bounds.rightMin,
             Math.min(bounds.rightMax, width - rawLeft - middleMinWidth));
var left  = clamp(rawLeft,  bounds.leftMin,
             Math.min(bounds.leftMax,  width - right  - middleMinWidth));
```

⇒ 1440 / 左 480 / 右 560 时得到 **480 / 540 / 中栏 420**（§1.5 那一格）。
⚠️ **先夹左会得到左栏 460** —— 与 §1.5 的表和 §1.2 的验收第 5 条不符。

### 3.3 夹取**只实现一次**

初始布局与拖拽路径**必须走同一个函数**；拖拽时只记录**原始指针宽度**，
夹取交给同一个函数。否则又是一套双源（A-90 的教训）。

### 3.4 C 档（≤1279）右栏的形态

- `position: fixed` + `top: 52px`（顶栏高维持 52px，A-21-3）+ `bottom: 0` + `right: 0`
- 宽 `min(380px, 92vw)`、`max-width: 100vw`、**`min-width: 0`**（否则窄视口被 base 的 360px 撑出横向滚动）
- `padding: 16px`（§1.7：右栏内边距 16 保持）、`border-left: 1px solid var(--rule-hair)`
- `transform: translateX(105%)` → 开：`translateX(0)`；过渡 `var(--dur-base)`（160ms）
- **无遮罩**（`acceptance.md:117`：抽屉打开时背景仍可交互）

### 3.5 顶栏两个抽屉按钮的分档可见性

- ≤1279：**只有**「Agent 对话」出现（C 档左栏仍是常驻列）
- ≤1023：两个都出现（D 档左栏也成抽屉）

---

## 4. 验收（**每条都要有可指认的证据**）

### 4.1 四档几何（浏览器实测，不是读 CSS）

| 视口 | 期望左 / 中 / 右 | 期望中栏 padding | 期望 h1 |
|---|---|---|---|
| **1440** | `280 / 740 / 420` | `28px 32px 72px` | `30px` |
| **1280** | `248 / 652 / 380` | `28px 28px 64px` | `30px` |
| **1024** | `232 / 792 / 抽屉 380` | `24px 24px 64px` | `28px` |
| **768** | `抽屉 300 / 768 / 抽屉 380` | `24px 18px 48px` | `24px` |
| **640**（E 档抽查） | `抽屉 92vw / 640 / 抽屉 100vw` | `16px 12px 40px` | `22px` |

### 4.2 §1.2 的七条验收口径

1. 1440 → 三列 `280 / 740 / 420`（±1px）
2. 1280 → 三列 `248 / 652 / 380`（±1px）
3. 1024 → **无横向滚动条**（`documentElement.scrollWidth <= innerWidth`）
4. 拖左栏到 200 → **右栏不低于 360**、中栏无横向滚动条
5. 拖左栏到 480（右栏在 560 时）→ **右栏收到 540、中栏落在 420**
6. 桌面端 `#layout` 的行内 `style` **不含 `grid-template-columns`**，只有两个宽度变量
7. 拖拽柄**在 `#left-column` 右缘 10px 内可命中**（`elementFromPoint`）

### 4.3 图谱页 G-5（图谱作用域的三处必须回到 HEAD 取值）

| 项 | 期望（= HEAD `ec47783d`） |
|---|---|
| `#middle` padding | `34px 40px 20px` |
| `#left-column` 分隔线 | `1px solid var(--ink-strong)` |
| `#ai-column` 分隔线 | `1px solid var(--ink-strong)` |
| `.page-header h1` | `28px / 36px / -0.025em` |

### 4.4 探针与仓库级检查（**全绿才算完成**）

```bash
# A-39：服务字节 == 磁盘字节
# 四档实测 + D1–D5 对比
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/probe.py static \
  --base-url http://127.0.0.1:<port> --ws walk --out <out> --side after --repo-root .
# ⇒ 3.5-1 / 3.5-2 / 3.5-3 必须全 PASS

env -u http_proxy -u https_proxy -u all_proxy python -m pytest tests -q
env -u http_proxy -u https_proxy -u all_proxy python -m compileall -q lessonkit.py workbench pipeline pool tests
env -u http_proxy -u https_proxy -u all_proxy openspec validate --specs --strict
env -u http_proxy -u https_proxy -u all_proxy python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

---

## 5. benchmark（**机械可查；不达标 = 退货重做**）

| # | 判据 | 怎么查 |
|---|---|---|
| B-1 | 四档几何 **10 个数**逐格对上 §4.1 | 浏览器实测输出 |
| B-2 | 四档 **无横向滚动条** | `probe_responsive` ⇒ 3.5-1 PASS |
| B-3 | 抽屉在 1024 与 768 **都能打开**，背景仍可交互 | `probe_drawer` ⇒ 3.5-2 / 3.5-3 PASS |
| B-4 | §1.2 七条**全部**满足 | 逐条实测输出 |
| B-5 | 图谱页三处 = §4.3 | 图谱页 computed style 对比 |
| B-6 | `:root` 里 **零** `--shell-col-*` | `grep -n '\-\-shell-col-' workbench.css` 的 `:root` 块为空 |
| B-7 | 四档 `@media` **齐四档** | 出现 `max-width: 1439px` / `1279px` / `1023px` / `767px` |
| B-8 | spec delta 含**四档表 + 三个 Scenario** | `openspec validate --specs --strict` 通过 + 人工核对 |
| B-9 | 仓库级检查**四条全绿** | 上面 §4.4 的四条命令 |
| B-10 | 提交**只含三个文件**、显式路径 | `git show --stat HEAD` |

---

## 6. 坑（**都踩过**）

| # | 坑 | 怎么办 |
|---|---|---|
| L-1 | `:where()` 特异度 0 ⇒ 尺寸修饰符压不住基类 | 形态高度写在形态规则里 |
| L-2 | `git commit` 不带路径会扫进别人在途改动（已发生 5 次） | `git add -- <路径>` **和** `git commit -- <路径>` **两个都带**；**绝不** `git add -A` |
| L-3 | pip 里装了 `lesson-kit 0.1.0` ⇒ 仓库根外起服务会解析到 site-packages 快照 | 一律仓库根起服务 + 核对**服务字节 == 磁盘字节**（A-39） |
| L-4 | 本机 `http_proxy=127.0.0.1:7890` 吞掉 localhost 请求 | `env -u http_proxy -u https_proxy -u all_proxy` |
| L-5 | 端口冲突 | 避开 3081/3092/3099/3177/3178/3184/3200/3201/3281/3282/3288/3411/3460/3461/3462/3477/3481/3482 |
| L-6 | 井号注释里的 `/* */` 嵌套会**提前闭合** CSS 规则块 | 注释里不写 `*/`；写 `⇒` 或换行 |
| L-7 | **改了图谱页的中栏内边距就破 G-5** | 图谱作用域冻结三处（§1.12） |
| L-8 | 测 D1–D5 时**每次跑都会新增一条练习记录** ⇒ 记录卡数量会涨 | 同数据态对比（先固定 DB 状态再跑两次），别拿不同态的数字相减 |
| L-9 | 图谱画布有动画 ⇒ 截图不可逐字节比 | 比**外壳的 computed style**，别比画布像素 |
