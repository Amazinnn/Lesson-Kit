# IMPL-W2g — 组件收口之一：三个「渲染是空的」组件 + 焦点环 + 两个 token 口径

> 来源：`component-inventory.md`（28 个组件的实测清单）· `decisions.md` **A-75 / A-78**。
> **只改 `workbench/server/static/workbench.css` 这一个文件。**

## 铁律：本波**不涉及风格挑选**
样式板（`tmp/frontend-audit/styleboard-v2/`）正在等所有者挑形态。
本波只修**「有缺陷 / 缺实现 / 口径不一致」**的条目 ——
**凡是「挑哪种形态」的，一律不许在本波动**（等挑完再统一改）。

## 要做什么（四件）

### 1. 三个「markup 已落地、CSS 零命中 ⇒ 现在渲染是空的」组件
实测：`grep -c` 在 `workbench.css` 里**全部为 0**，而 markup 在用：

| 类名 | markup 用量 | 现在是什么 |
|---|---|---|
| **`.lk-switch`**（开关） | `pages.py` **9 处** | 渲染是空的（继承不到任何样式） |
| **`.lk-seg`**（分段控件） | `pages.py` **3 处** | 渲染是空的 |
| **`.icon-only`**（图标按钮） | `pages.py` 5 处 + `workbench.js` 2 处 | 渲染是空的（借了文字按钮的底子，但**图标是字符不是 SVG**） |

⇒ 给它们补上**基本可用的形态**（不是「挑形态」，是「让它有形态」）：
- **`.lk-switch`**：一个**真正的开关**（轨道 + 滑块），开 = `--role-blue`，
  关 = 中性面；**滑块位置用 `transform` 切换**（只动 `transform`，不许动 `left`/`width`）。
  ⚠️ 开关是**可交互控件** ⇒ 要有**可见焦点环**（见第 2 条）与**足够的点击区**（≥24px）。
- **`.lk-seg`**：分段控件 = 一排**互斥选项**（`role="radiogroup"` 那类），
  当前项用**角色色**（`--role-blue` 或 `--role-blue-wash`）+ 文字色区分；
  **不描边**（D-2），靠**沉底面 + 选中项的色块**分层。
- **`.icon-only`**：只放**图标**的按钮 ⇒ 必须是**正方形**（宽高相等）、
  尺寸 ≥ 32px（图标按钮的最小点击区）、**图标居中**、`aria-label` 由 markup 负责。
  ⚠️ 现在**图标是字符**（`◎` `⌗` 之类）⇒ 保留现状（改图标是资产问题，不在本波），
  但**尺寸、形状、焦点、悬停态**要定下来。

### 2. 三处 `outline: none` → **补可见焦点环**（**可访问性缺陷**，A-75）
```
workbench.css:885   select:focus { border-color: var(--role-blue); outline: none; }
workbench.css:973   textarea:focus, input:focus { border-color: var(--role-blue); outline: none; }
workbench.css:1738  #answer-box:focus { border: none; outline: none; }
```
**A-1 禁止去掉焦点环**，而这三处让**键盘用户看不见焦点在哪**。
⇒ 改成 `:focus-visible` 的焦点环，用权威表的 token：
`--focus-outer`（亮 `#2b62e8` / 夜 `#9dbcff`）· `--focus-inner`（亮 `#fffdf7` / 夜 `#14120f`）。
⚠️ **只改 `:focus-visible`**（鼠标点击不该冒出焦点环），**`:focus` 不加环**。
⚠️ 第 3 处（`#answer-box`）还顺带 `border: none` ⇒ 聚焦时**连边框都没有**，
⇒ 要给它一个**聚焦态的边界**（别让它聚焦时完全失去轮廓）。

### 3. `.lk-dot--filled` 补规则（A-78）
- 现在是**空规则**，但 `pages.py` **在用**（1 处）⇒ 现在靠 `.lk-dot--red` 顺带渲染成实心。
- ⇒ 补：**实心圆盘、**无几何符号**，与 `--cross` / `--dash` / `--check` **互斥**。
- 颜色由**状态类**给（`--red` / `--yellow` / `--ink` 等），`--filled` 本身**只管形状**。

### 4. `.lk-dot` 的圆角统一到 `--r-pill`（A-78）
- 现在用 `--r-round`，spec §4.14 明写 `--r-pill` —— **视觉相同但取值口径要统一**。
- ⇒ 改成 `var(--r-pill)`（若 `--r-pill` 未定义，**先在 token 层补上**，取值与 `--r-round` 一致，
  并在权威表里登记）。

## 硬约束
- **只改 `workbench.css`**。绝不碰 `pages.py` / `workbench.js` / `practice-flow.js` /
  `paper-practice.js` / `middle-navigation.js` / `records.py` / `agent-ui.css` /
  `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **不要**改 `tasks.md` 的复选框（主会话统一勾）。
- **知识图谱区段与 12 个裸名一行都不许碰**（按选择器定位：`grep -n "Knowledge graph V2" workbench.css`）；
  **不要动图谱页冻结块**。⚠️ `.seg`（图谱的 tablist）与 `.chip`（图谱的可点筛选）
  **一个字都不许碰**（A-76：它们是图谱的，且 `.chip` 是**可点**的，与新标签语义相反）。
- **不动图谱的算法**。
- 现有交互逻辑一个字都不许改（本波只动 CSS 外观）。
- 只用**现有 token**（必要时**补** token 到 token 层 + 权威表），**不许硬编码 hex**。
- 动效红线：起始态只写在 `@keyframes` 内；只动 `transform` / `opacity`；状态色瞬切。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **走查实测**（要有运行时 `getComputedStyle` 证据 + 截图）：
  - **开关**：在设置视图里找到那 9 处 `.lk-switch` 的用法，量它的 computed 值
    （宽高、圆角、轨道色、滑块位置与 transform）；**开/关两态**各截一张；
  - **分段控件**：同上（`.lk-seg` 的 3 处用法）；
  - **图标按钮**：`.icon-only` 的**宽 == 高**、≥32px、图标居中；
  - **焦点环**：用键盘 **Tab** 到输入框 / 文本域 / 答题框，截**三张**聚焦态图，
    确认**焦点可见**；再用**鼠标点击**确认**不冒焦点环**（`:focus-visible` 的行为）。
- **图谱区段逐字节不变**（自己 `diff`），R-2 差异像素 **= 0**。
- 走查按 **A-39**：仓库根 cwd、**独立端口**（**不要 3081 / 3092 / 3099 / 3191 / 3177 / 3178 / 3184 / 3411**）、
  池副本 + `LESSONKIT_WB_HOME` 隔离注册表；服务字节数与磁盘字节数**必须相等**。

## 落盘纪律与回报
- **一个主题一个 commit**（四件 ⇒ 最多四个 commit），
  只 `git add workbench/server/static/workbench.css`（权威表若补了 token，另 add 那个文件），
  **不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**四件逐条的「改前 → 改后 + 运行时实测值」** +
**聚焦态的三张截图 + 鼠标点击不冒环的证据** +
**图谱区段逐字节未变的证据** + 四条验证命令结果 + **待裁决项**。
- 数字一律以**当场跑出来的命令输出**为准。
