# 验收关卡 · 人工判读一页纸（第 22 组 · 4 条 SEMI / MANUAL 判据）

> **这份材料不给结论，只给数字和证据。** 机器（走查执行器）按 §7.5.1 的规矩，
> SEMI / MANUAL 一律 `PENDING`，**不替人勾选**（`design-notes/walkthrough-harness.md:1409-1420`）。
> 下面每一条都分成五段：**判据原文 / 机器测到的数值 / 证据路径 / 建议判定 + 理由 /
> 判读时该看什么**。最后的「**需要你确认**」一节是签字位，**执行器不代签**。

| | |
|---|---|
| **对应判据** | `3.2-3` · `3.4-4` · `3.6-2` · `3.6-4`（`acceptance.md` §3.2 / §3.4 / §3.6） |
| **证据来源** | 第 22 组走查第 1 轮 —— `tmp/wt-run-7/`（产物在 `tmp/`，**已被 `.gitignore:51` 忽略**，重新拿到它们要重跑，见下） |
| **那一轮的代码状态** | before 侧 = 提交 `cf9d596d`（A-49 基线）；after 侧 = 工作区内容指纹 = 提交 `4b4be87f` 的树（CSS 逐字节相同，见 `acceptance-shots/index.md` §0） |
| **重跑命令** | `python tools/walkthrough/run.py --out tmp/wt-run-7` |
| **本轮整体** | `run.json` 的 `summary.overall = FAIL`；G-1…G-8 全 PASS，FAIL 落在清单层 |

> ⚠️ **这些数字对应那一轮；后续修复后需要重跑。**
> 走查期间另有 agent 在并行改产品代码，after 侧采的是**当时工作区的那一份**；
> 现在 `workbench/server/static/workbench.css` 已经和采集时不是同一个内容了。

---

## 0. 读之前先说四件事

### 0.1 判据原文抄自哪里（为什么不是任务书里的描述）

判据原文逐字抄自 **`design-notes/walkthrough-harness.md` §7.5.3「交互清单逐条对应表」**
（`walkthrough-harness.md:1484` / `:1506` / `:1524` / `:1525`）与
**`acceptance.md` §3 的清单行**（`acceptance.md:110` / `:126` / `:138` / `:140`）。
这两处是判据的权威原文；**任务书 `briefs/IMPL-W3j.md:21` 对 `3.2-3` 的一句话描述与判据原文不符**
（它写「状态语义与用户侧措辞一致」，而判据原文是「夜纸下图标圆底为『降饱和 + 提亮』版本」）。
本页一律以判据原文为准 ⇒ **`3.2-3` 这一节写的是「降饱和 + 提亮」，不是「措辞与状态」。**
这条错述已列入末尾「需要你确认」的第 ① 条。

### 0.2 机器给的是分布，不是结论

`3.6-2`（线宽与圆角是否同一套）、`3.6-4`（插画是否具象）本质是审美判断，
探针按设计**只给数值不给结论**（`walkthrough-harness.md:1524`：「机器只能列分布 → 人判」）。
`3.2-3` 的「幅度」同理（`:1484`：「幅度由人判」）。

### 0.3 before / after 的数字**不可直接比**

- `3.4-4`：before 侧探针只枚举出 **12** 条红色声明，after 侧 **36** 条。
  **这不是「红色变多了」** —— before 侧大量用 `--lk-red` / `--dsw-state-error` 旧名与硬编码
  `#d6453d` / `#d12c2c`，探针按新 token 名匹配，before 侧**漏采**。
  ⇒ **不要用 12 → 36 当作回归证据**，两条列表要逐点比语义，不是比条数。
- `3.6-2`：before 侧 `svgCount = 0`（改造前全仓 0 个 SVG），after 侧 5 个 —— 这是**资产从无到有**。

### 0.4 本页引用的**行号**是「那一轮」的，不是现在的

探针产物里记的行号属于**采集时**的那份 CSS（after 侧 = 提交 `4b4be87f` 的树）。
⇒ 本页所有 `workbench.css:NNN` **一律指 `git show 4b4be87f:workbench/server/static/workbench.css`**
（before 侧那几处指 `git show cf9d596d:workbench/server/static/workbench.css`）。
**现在工作区的 `workbench.css` 已经往后挪了**（例如 `.ai-plan-summary` 现在在 `:1747`，
采集时在 `:1685`）⇒ 拿现在的文件按本页行号去翻会翻错。
（`agent-ui.css` / `workbench.js` / `records.py` 自采集时**未变**，行号仍有效；
`pages.py` / `practice-flow.js` 正在被并行修改，本页引它们时行号取**当前工作区**。）

---

## 1. `3.2-3` —— 夜纸下图标圆底为「降饱和 + 提亮」版本

### 1.1 判据原文（逐字抄）

`design-notes/walkthrough-harness.md:1484`：

> | 3.2-3 | 夜纸下图标圆底为「降饱和 + 提亮」版本 | `contrast_probe` + `asset_probe` 取圆底色，验 HSL 饱和度降、亮度升 | `probe/3.2-3.json` | **SEMI** | 数值可算（「降饱和 + 提亮」的方向可验），但**幅度**由人判 |

`acceptance.md:110`：

> - [ ] 夜纸下图标圆底为「降饱和 + 提亮」版本

### 1.2 机器测到的数值

- 探针结论：`level = SEMI` · `auto = false` · `verdict = PENDING` · `note = 证据已采集，需人工判读`。
- **`data.pairs`（探针实际取到的圆底色）只有 2 条，且全是「透明」**：

  | `cls` | `light` | `night` | `lightHsl` | `nightHsl` |
  |---|---|---|---|---|
  | `nav-item__icon` | `rgba(0, 0, 0, 0)` | `rgba(0, 0, 0, 0)` | `[0.0, 0.0]` | `[0.0, 0.0]` |
  | `[object SVGAnimatedString]` | `rgba(0, 0, 0, 0)` | `rgba(0, 0, 0, 0)` | `[0.0, 0.0]` | `[0.0, 0.0]` |

  ⇒ **探针没有测到「圆底实际渲染色」**：`.nav-item__icon` 是 `<span>`，圆底是 SVG 内部的
  `<circle fill="var(--asset-ground-blue, …)">`，**不落 CSS background**，所以
  `getComputedStyle` 读出来是 `rgba(0,0,0,0)`。
- **`data.lightRoles` / `data.nightRoles`（探针读到的 token 值，各 10 个）**：

  | token | 亮色 | 夜纸 |
  |---|---|---|
  | `--role-blue` | `#2b62e8` | `#7291de` |
  | `--role-yellow` | `#f5c518` | `#e0c151` |
  | `--role-red` | `#d1392b` | `#d4736b` |
  | `--role-red-ink` | `#b8331f` | `#e08878` |
  | `--role-yellow-deep` | `#8a6a00` | `#f0d98a` |
  | `--role-blue-wash` | `#f2f0ef` | `#292929` |
  | `--role-blue-soft` | `#e0e3ee` | `#31343c` |
  | `--role-yellow-soft` | `#fcf0cd` | `#3d3721` |
  | `--role-red-wash` | `#f9e9df` | `#352821` |
  | `--role-red-soft` | `#f6d9d0` | `#432f28` |

- **当场复算的 HSL**（对上面三个圆底角色色；权威表 `design-notes/night-paper-tokens.md:790` §5
  的算式是 `H' = H`、`S' = S + ΔS (ΔS < 0)`、`L' = L + ΔL (ΔL > 0)`）：

  | 角色 | 亮色 HSL | 夜纸 HSL | 复算 ΔS / ΔL | 权威表 §5 写的 ΔS / ΔL | 是否吻合 |
  |---|---|---|---|---|---|
  | 学习蓝 | H222.5 S80.4 L53.9 | H222.8 S62.1 L65.9 | **−18.3 / +12.0** | S−18 / L+12 | ✅ |
  | 阳光黄 | H47.0 S91.7 L52.7 | H47.0 S69.8 L59.8 | **−21.9 / +7.1** | S−22 / L+7 | ✅ |
  | 注意红 | H5.1 S65.9 L49.4 | H4.6 S55.0 L62.5 | **−10.9 / +13.1** | S−11 / L+13 | ✅ |

- before 侧：`pairs = []`、`lightRoles = {}`、`nightRoles = {}`（改造前无夜纸，与 `walkthrough-harness.md:1484` 的基线栏一致）。

### 1.3 证据路径（逐条已 `ls` 核过，零缺失）

| 东西 | 路径 |
|---|---|
| 探针产物（after） | `tmp/wt-run-7/evidence/after/probe/3.2-3.json` |
| 探针产物（before） | `tmp/wt-run-7/evidence/before/probe/3.2-3.json` |
| 38 条清单总表 | `tmp/wt-run-7/evidence/after/probe/checklist.json` |
| 本轮运行元数据 | `tmp/wt-run-7/run.json` |
| 权威 token 表（§5） | `openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md` |
| 圆底取色的代码链路 | `workbench/server/static/workbench.css` —— `:root` 的 `--asset-ground-blue: var(--role-blue)`（**:218**）；夜纸块 `html[data-theme="night"]`（**:253**）的 `--role-blue: #7291de`（**:275**） |
| 圆底的画法 | `workbench/server/static/assets/icons/icon-practice.svg` 等 5 个 |
| 夜纸对照截图 | `tmp/wt-run-7/evidence/after/shots/S-10-night-dark.png`（**⚠️ 见下，这张图拍不到圆底**） |

### 1.4 建议判定 + 理由

**建议判定：`需你定`（证据指向 PASS，但「渲染层」没有被机器测到）。**

**依据（三条成立、两条缺口）：**

1. **token 层已经对上了。** 探针实测的夜纸三角色色，复算 HSL 与权威表 §5 的
   「降饱和 + 提亮」三组 ΔS / ΔL **逐位吻合**（上表）—— 方向与幅度都对得上表。
2. **取色链路成立。** 圆底是 `<circle fill="var(--asset-ground-blue, #2b62e8)">`；
   `--asset-ground-blue` 在 `:root` 上取 `var(--role-blue)`，而 `:root` 与
   `html[data-theme="night"]` **是同一个 `<html>` 元素** ⇒ 夜纸下 `--role-blue = #7291de`
   ⇒ 圆底实际渲染色就是 `#7291de`。（`workbench.css` 里 `:377-381` 那段注释讲的是**图谱页**
   在 `body` 上冻结 `--role-blue` 的另一种情形，不适用于普通页面。）
3. **机器没有独立验证第 2 条。** `data.pairs` 取到的是 `rgba(0,0,0,0)` —— 探针采的是
   `<span>` 的 background，而圆底在 SVG 内部 ⇒ **「圆底渲染色 = 降饱和 + 提亮档」这句
   本轮是读 CSS 推出来的，不是机器测出来的**。
4. **S-10 这张夜纸图不能当圆底证据。** `S-10` 的 URL 是 `/`（hub），
   画面上只有「工作区选择卡」，**左栏导航图标根本不出现** —— 夜纸圆底在图里零像素。
   （before 侧 S-10 与 S-1 **sha256 完全相同** `4be9eeef2cfc…` ⇒ 改造前没有夜纸主题，
   after 侧才分叉成 `6a9614d41853…`。）
5. **本条判的是「幅度由人判」**（`walkthrough-harness.md:1484`）。表上的 ΔS / ΔL
   与权威表一致，但「这个幅度对不对眼」本身是审美判断，机器替不了。

### 1.5 判读时该看什么（需要你确认）

**打开任一带左栏导航的页面**（`/w/walk/practice`、`/w/walk/kps` …）**切到夜纸**
（设置视图 → 外观设置 → 主题），然后盯**左栏那五个导航图标的小圆底**：

| 图标 | 圆底应为什么 | 怎么判 |
|---|---|---|
| 练习 / 知识点 / 知识图谱 | **降饱和 + 提亮**的学习蓝 `#7291de` | 如果看到的是发闷的 `#2b62e8`（深、艳、饱和）⇒ **没收档，FAIL** |
| 试卷 / 记录 | **降饱和 + 提亮**的阳光黄 `#e0c151` | 同理，对照 `#f5c518` 判 |
| 圆底上的字形 | 夜纸下三个圆底**统一深墨** `#14120f`（权威表 §5 的「关键反相」） | 字形若还是纸白 `#fffdf7` 在深底上 ⇒ 反相没做 |

（`S-10-night-dark.png` 拍不到这些 ⇒ **要么另拍一张带导航的夜纸页，要么开页面现场看**。）

---

## 2. `3.4-4` —— 错误态明确（红色仅用于失败与阻塞）

### 2.1 判据原文（逐字抄）

`design-notes/walkthrough-harness.md:1506`：

> | 3.4-4 | 错误态明确（**红色仅用于失败与阻塞**） | `error_color_probe`：枚举所有红色 token 的使用点，逐点判语义 | `probe/3.4-4.json` | **SEMI** | 现状红色相关声明 22 处，需逐点判「是否真是失败/阻塞」——**机器列点，人判语义** |

`acceptance.md:126`：

> - [ ] 错误态明确（**红色仅用于失败与阻塞**）

### 2.2 机器测到的数值

- 探针结论：`level = SEMI` · `auto = false` · `verdict = PENDING`。
- **`data.count = 36`**（after 侧；before 侧 `count = 12`，但**两者不可直接比**，见 §0.3）。
- 36 条逐点分类（分类依据 = 采集时的 CSS，行号取 `4b4be87f` 那一份）：

  | 类别 | 条数 | 明细 |
  |---|---|---|
  | **① token 定义 / 图谱冻结块 / 旧值兼容块**（不是使用点） | **13** | `workbench.css` `:170 :171 :172 :173`（浅色 `--role-red` 四档）、`:220`（`--asset-ground-red`）、`:282 :283 :284 :285`（夜纸四档）、`:350 :351`（旧 `--lk-red` / `--dsw-state-error` 兼容值）、`:387`（图谱页冻结）、`:3511`（图谱 `:root` 的 `--red`） |
  | **② 明确的失败 / 阻塞** | **16** | `agent-ui.css` `:158`（`.ai-turn-inline-status`，JS 仅在 `status === "failed" \|\| "cancelled"` 时加，见 `workbench/server/static/workbench.js:5035`、`:5039`）、`:216`、`:321`、`:322`；`workbench.css` `:1195`（`.lk-dot--red`，用在 `workbench/server/pages.py:110-118` 的错误块）、`:1629`、`:1640`、`:1675`、`:1676`（均 `.is-failed`）、`:2026`（`.inline-error`）、`:2064`（`.status-dot.err`）、`:2246`（`.micro-verdict.bad`）、`:2355`（`.calendar-goal.overdue`）、`:2611`、`:2664`（判定 bad）、`:3908`（`.paper-dot.state-wrong, .state-stuck`） |
  | **③ 落在「非失败 / 非阻塞」的语义上** | **4** | ① `workbench.css:549` `#topbar .brand::before` 的 `box-shadow` 第三颗 = 红 —— **品牌三色点（蓝 0 / 黄 17px / 红 34px），纯装饰**；② `workbench.css:1687` `.ai-plan-summary { color: var(--role-red-ink); }` —— **无条件**施加，该节点装的是「查看输出」/摘要文字（`workbench.js:4529 / 4617 / 4685`），**不是失败态**；③ `workbench.css:2002` `.flash-card-answer { border-color: var(--role-red); }` —— 闪卡「**另一面**」与「提示面」的**分类色**（`practice-flow.js:1022`，`aria-label='另一面'`），不是失败；④ `workbench.css:2392` `.bar-heavy-flag { background: var(--role-red); }` —— 「**重日**」负荷量标记（`workbench/server/records.py:440, 473`：当天作答数 ≥ 非零日均的 2 倍），**量的高 ≠ 失败** |
  | **④ 要你拍板 / 机器噪声** | **1 + 2** | **要拍板 1 条**：`workbench.css:1535` `.graph-relation-row.relation-contrasts { border-left: 3px solid var(--role-red); }`（图谱「矛盾关系」算不算阻塞？图谱本轮不碰，见 A-8）；**机器噪声 2 条**：`workbench.css:2639` 与 `:2662` 是**注释行**里的 `--role-red-ink` 字样（不渲染，但探针按字符串扫、把它们算进来了） |

- **这 4 条非失败红色是不是本轮引入的？不是。** 采集时的 before 侧 CSS 里它们同样红：
  `.ai-plan-summary` 用 `var(--dsw-state-error)`（`cf9d596d` 的 `workbench.css:742`）、
  `.flash-card-answer` 用硬编码 `#d12c2c`（`:982`）、`.bar-heavy-flag` 用 `#d6453d`（`:1343`）、
  品牌三色点用 `var(--lk-red)`（`:123`）。
  ⇒ **本轮没新增红色，但本轮把它们统一并进了语义红色 token（`--role-red` / `--role-red-ink`）**，
  也就是把「红色用于非失败」这件事**在 token 层固定下来**了 —— 这正是本判据要卡的位置。

### 2.3 证据路径（逐条已 `ls` 核过，零缺失）

| 东西 | 路径 |
|---|---|
| 探针产物（after，36 条） | `tmp/wt-run-7/evidence/after/probe/3.4-4.json` |
| 探针产物（before，12 条） | `tmp/wt-run-7/evidence/before/probe/3.4-4.json` |
| 采集时的 CSS（after 侧树） | `git show 4b4be87f:workbench/server/static/workbench.css`（行号以此为准） |
| 采集时的 CSS（before 侧树） | `git show cf9d596d:workbench/server/static/workbench.css` |
| 另一个 CSS 文件 | `workbench/server/static/agent-ui.css` |
| 语义代码引用 | `workbench/server/static/workbench.js`、`workbench/server/static/practice-flow.js`、`workbench/server/records.py`、`workbench/server/pages.py` |
| 可看的画面 | `tmp/wt-run-7/evidence/after/shots/S-9-settings-1440.png`（右栏对话）、`S-6-records-overview-1440.png`（14 天负荷柱）、`S-1-hub-1440.png`（顶栏品牌点） |

### 2.4 建议判定 + 理由

**建议判定：`FAIL`（现状有 4 处红色用在了非失败 / 非阻塞的语义上）。**

**依据：**

1. 判据是**排他性**的：红色**只能**出现在失败与阻塞上。第 ② 类 16 条都合格，
   第 ① 类 13 条是定义不算使用点，但第 ③ 类 4 条**明确违反**：
   - 顶栏品牌三色点的第三颗是红 —— 纯装饰，零语义；
   - `.ai-plan-summary` 无条件红，而它承载的是「查看输出」这类**中性**文案；
   - 闪卡「另一面」用红边框 —— 那是**两面卡的分类色**，不是失败；
   - 「重日」负荷点用红 —— 那是**量的高低**。
2. 这 4 条**不是本轮引入的**，但本轮把它们**并进了语义红色 token**，
   使「红色 = 失败/阻塞」这条契约在 token 层**第一次真正被这些用法违反**。
   修法要由你定（换中性色 / 换几何编码 / 或正式扩写判据），**执行器不自行改产品**。
3. 第 ④ 类里**只有 1 条真要你拍板**：图谱「矛盾关系」的红算不算阻塞
   （我倾向**不算** —— 它是知识关系类型，不是学习状态，且图谱本轮冻结在 A-8）。
   另外 2 条是**注释行**，不影响渲染，但说明**探针按字符串扫、会把注释算进来** ——
   判读时心里有数即可（**不许为了少两条去改探针**：判据是判据，不是产品）。

### 2.5 判读时该看什么（需要你确认）

**三处，各看一个具体东西：**

1. **顶栏品牌点**（任何页面，页眉 `lesson-kit` 左边）—— 第三颗小方块是红的。
   它表达什么？（我读：**什么都不表达**，纯装饰。）
2. **右栏「对话」面板** —— 展开一条 AI 计划的详情，「**查看输出**」那行是不是**红的**？
   （`workbench.js:4617` / `:4685` 写的就是这四个字。若是红的 ⇒ 红色被用在了中性文案上。）
3. **记录中心 → 概览 → 14 天负荷柱** —— 「重日」顶上那个 7px 红点。
   它表达「今天做得多」，不是「今天做错了」。红色放这儿合不合判据？

（另有 1 处要你定：**图谱页**关系行左边的红色竖条 —— 「矛盾关系」算不算「阻塞」。）

---

## 3. `3.6-2` —— 图标与插画在同一套线宽与圆角语言内（写意线稿 + 淡彩）

### 3.1 判据原文（逐字抄）

`design-notes/walkthrough-harness.md:1524`：

> | 3.6-2 | 图标与插画在同一套**线宽与圆角语言**内（写意线稿 + 淡彩） | `asset_probe`：取全部 SVG 的 `stroke-width` 分布与 `rx/ry` 集合，人工核「是否同语言」 | `probe/3.6-2.json` | **SEMI** | 「同一套语言」是**审美判断**，机器只能列分布 → 人判 |

`acceptance.md:138`：

> - [ ] 图标与插画在同一套线宽与圆角语言内（写意线稿 + 淡彩）

### 3.2 机器测到的数值

- 探针结论：`level = SEMI` · `auto = false` · `verdict = PENDING`。
- **`data.svgCount = 5`** —— 探针在页面上只找到 **5** 个 inline SVG，全部在 `nav-item__icon` 里
  （`data.sample` 五条的 `parent` 都是 `nav-item__icon`，`src` 都是 `""` = inline）。
- **`data.strokeWidths`（分布）= `{ "3": 11, "2": 14, "1.5": 16 }`** —— 只有三档。
- **`data.radii` = `{}`（空集）**，且 `data.sample` 每条的 `radii` 都是 `[]`
  ⇒ **这 5 个 SVG 里一个 `rx` / `ry` 都没有**。
- before 侧：`svgCount = 0`、`strokeWidths = {}`、`radii = {}`（改造前全仓 0 个 SVG）。
- **补充（不在探针产物里，来自资产文件本体，用 `git show 4b4be87f:…` 逐文件扫的）**：
  仓库里有 **15** 个本轮资产 SVG（5 个导航图标 + 10 张空态插画），**当页只有 5 个在 DOM 里**。

  | 集合 | 文件数 | `stroke-width` 分布 | `rx/ry` 取值 |
  |---|---|---|---|
  | 导航图标 `assets/icons/*.svg` | 5 | `{2: 14, 3: 11, 1.5: 16}` | **空集** |
  | 空态插画 `assets/empty/*.svg` | 10 | `{3: 47, 2: 31, 1.5: 34}` | **18 个不同取值**：`2, 2.5, 5.5, 6, 6.5, 7, 8, 9, 11, 17, 20, 26, 28, 30, 33, 34, 35, 40, 46, 50` |

  ⇒ **线宽**：图标与插画**同属 `{1.5, 2, 3}` 三档**，且全部 `stroke-linecap="round"` +
  `stroke-linejoin="round"`。
  ⇒ **圆角**：图标侧**一个半径都没有**，插画侧**18 种**（`rx=50` 是正圆、`rx=2` 是小圆角）
  —— **机器给不出「是否同一套圆角语言」的结论**。

### 3.3 证据路径（逐条已 `ls` 核过，零缺失）

| 东西 | 路径 |
|---|---|
| 探针产物（after） | `tmp/wt-run-7/evidence/after/probe/3.6-2.json` |
| 探针产物（before） | `tmp/wt-run-7/evidence/before/probe/3.6-2.json` |
| 相邻判据（同一探针族） | `tmp/wt-run-7/evidence/after/probe/3.6-1.json`（FAIL：1 个位图）、`3.6-3.json`（PASS：圆底色都在三角色色里）、`3.6-5.json`（PASS：深浅共用同一批资源） |
| 5 个导航图标 | `workbench/server/static/assets/icons/icon-{practice,practice-sets,kps,graph,records}.svg` |
| 10 张空态插画 | `workbench/server/static/assets/empty/empty-{books,canvas,compass,cup,fruit-basket,globe,inkwell,pen,pencil-cup,vase}.svg` |
| 资产走查页（可直接开） | `workbench/server/static/assets/preview.html` |
| 看得见的图标 | `tmp/wt-run-7/evidence/after/shots/S-8-practice-sets-1440.png`（左栏五个导航图标） |

### 3.4 建议判定 + 理由

**建议判定：`需你定`（线宽那一半可以判 PASS，圆角那一半没有机器证据）。**

**依据：**

1. **线宽语言一致 —— 建议这一半判 PASS。** 图标 `{1.5, 2, 3}`、插画 `{1.5, 2, 3}`，
   **同一套三档**；端点与转角全部 `round`。探针自己采到的 5 个图标分布
   （`{3:11, 2:14, 1.5:16}`）与我扫文件本体的结果**逐位相同** ⇒ 探针没漏。
2. **圆角那一半机器给不出结论。** `data.radii` 是**空集** —— 这**不是**「圆角统一」的证据，
   只是「这 5 个图标压根没写 `rx/ry`」。而插画侧有 18 种半径。
   **判据问的是「图标与插画在同一套圆角语言内」**，现在等于：图标侧无圆角可对，
   插画侧自由取值 ⇒ **必须人判**（这正是探针设计里「机器只能列分布 → 人判」的意思）。
3. **一个必须说清的证据缺口：插画没进 DOM。** 探针只找到 5 个图标，
   10 张空态插画**一张都没被采到**（`3.6-4` 的 `data.illustrations` 也是空数组）——
   空态插画是 `c45eeb6c`（23:38）才接进页面的，**晚于本轮采集（22:42）**。
   ⇒ 本轮的截图标里**没有插画**可供对照。

### 3.5 判读时该看什么（需要你确认）

**把 5 个导航图标和 10 张空态插画并排看（`workbench/server/static/assets/preview.html` 是资产层走查页，可直接开）：**

1. **线宽**：插画的描边是不是也是「细（1.5）/ 中（2）/ 粗（3）」三档里的？
   拿 18px 的导航图标和 240px 的插画**缩到同样大小**比 —— 若插画看起来
   「一粗一细混着走」，那就不算同一套。
2. **圆角**：插画里的圆头/转角观感是不是一把尺子量出来的？
   （机器侧：插画 18 种半径，其中 `rx=50` 是正圆、`rx=2` 是小圆角 ——
   **这算不算「同一套圆角语言」要你定**。）
3. **淡彩**：插画的填色是不是「淡彩」（低饱和填充）而不是实色块？
   （判据原文后半句「写意线稿 + 淡彩」也在这一条的射程里。）

---

## 4. `3.6-4` —— 插画为具象器物（不出现抽象几何团块）

### 4.1 判据原文（逐字抄）

`design-notes/walkthrough-harness.md:1525`：

> | 3.6-4 | 插画为**具象器物**（不出现抽象几何团块） | 人工看 `S-12` 空态插画与图标集 | `shots/S-12-*.png` | **MANUAL** | 审美判断，无可靠自动手段 |

`acceptance.md:140`：

> - [ ] 插画为具象器物（不出现抽象几何团块）

### 4.2 机器测到的数值

- 探针结论：`level = MANUAL` · `auto = false` · `verdict = PENDING` ·
  `note = 插画是否为具象器物需人看渲染结果`。
- **`data.shot = "shots/S-12-*.png"`**，**`data.illustrations = []`（空数组）**。
- **`shots/S-12-*.png` 不存在。** 采集清单 `tools/walkthrough/shots.py:98-100` 的 S-12 条目写着
  `requires: 空工作区种子（第二份 seed）——本交付未包含` ⇒ 本轮**没有采 S-12**。
  实测：`tmp/wt-run-7/evidence/{before,after}/shots/` 下各 **12** 张 PNG，
  编号是 S-1、S-2、S-3、S-4、S-5、S-6、S-7、S-8、S-9、S-10、S-11(1024)、S-11(768)
  —— **没有 S-12**（`find tmp/wt-run-7 -iname "*S-12*"` 零命中）。
- 因此本轮**唯一被指定的证据文件是空的** ⇒ 这条 MANUAL 判据**没有取到证据**。
- **补充（资产文件本体，非探针产物）**：10 张空态插画各带一句 `<title>`，逐字抄：

  | 文件 | `<title>` |
  |---|---|
  | `empty-books.svg` | 静物插画：三本叠放的书 |
  | `empty-canvas.svg` | 静物插画：一块空白的画布 |
  | `empty-compass.svg` | 静物插画：一把绘图圆规 |
  | `empty-cup.svg` | 静物插画：一杯还冒着热气的茶 |
  | `empty-fruit-basket.svg` | 静物插画：果篮里放着两只果子 |
  | `empty-globe.svg` | 静物插画：一只小地球仪 |
  | `empty-inkwell.svg` | 静物插画：桌上的墨水瓶 |
  | `empty-pen.svg` | 静物插画：一支放在桌上的钢笔 |
  | `empty-pencil-cup.svg` | 静物插画：笔筒里插着两支笔 |
  | `empty-vase.svg` | 静物插画：一枝柳条插在花瓶里 |

### 4.3 证据路径（逐条已 `ls` 核过；**其中被指定的 `S-12` 是缺失的那一个**）

| 东西 | 路径 |
|---|---|
| 探针产物 | `tmp/wt-run-7/evidence/after/probe/3.6-4.json`（`illustrations: []`） |
| **被指定的证据文件（不存在）** | `tmp/wt-run-7/evidence/after/shots/S-12-*.png` —— ⚠️ **本轮未产出**（缺第二份种子） |
| 采集清单里的 S-12 条目 | `tools/walkthrough/shots.py:98-100` |
| 插画本体（10 张） | `workbench/server/static/assets/empty/*.svg` |
| 图标本体（5 张） | `workbench/server/static/assets/icons/*.svg` |
| 资产走查页 | `workbench/server/static/assets/preview.html` |
| 本轮 12 张对照图 | `openspec/changes/workbench-visual-language-v2/acceptance-shots/index.md` |

### 4.4 建议判定 + 理由

**建议判定：`需你定`（本轮没取到指定证据；资产本体倾向上 PASS，但那是「看文件」不是「看渲染结果」）。**

**依据：**

1. **判据指定的证据文件不存在。** `data.shot` 指向 `shots/S-12-*.png`，
   而 S-12 需要「空工作区种子（第二份 seed）」，本轮交付不含 ⇒ 采集器按设计**跳过**
   （`tools/walkthrough/shots.py` 的 `requires` 机制：报告为 skipped，**不报 pass**）。
   ⇒ 这条判据本轮**没有证据**，不是「证据为负」。
2. **插画当时也没进 DOM。** `data.illustrations = []`；空态插画是 `c45eeb6c`（23:38）
   才接到页面的，**晚于本轮采集（22:42）** ⇒ 本轮 24 张截图里**一张插画都没有**。
3. **资产本体上，10 张全是具象器物**（上表 10 个 `<title>` 逐字列出：
   书 / 画布 / 圆规 / 茶 / 果篮 / 地球仪 / 墨水瓶 / 钢笔 / 笔筒 / 花瓶），
   **不是抽象几何团块**。但这是我读**文件本体**得到的结论，**不是渲染结果**，
   也不构成判据要的那种「人看渲染结果」的签字。
4. 相邻的 `3.4-5`（空态 = 插画 + 一句 + 满宽主按钮）本轮 **FAIL**，
   `c45eeb6c` 刚把它修好 —— ⇒ **这两条要一起重跑才有意义**。

### 4.5 判读时该看什么（需要你确认）

**看渲染结果，不是看文件名。**

1. 开 `workbench/server/static/assets/preview.html`（资产层走查页，内嵌 **76 个 inline SVG**，
   亮色 / 夜纸两套主题各一份，10 张插画 + 5 个图标都在里面），
   **把 10 张空态插画和 5 个导航图标放在一张图上比较**：
   - 每张插画能不能**认出来是什么东西**（书？圆规？茶？地球仪？）？
     认不出来、只看到几个色块 ⇒ 就是判据禁止的「抽象几何团块」⇒ FAIL。
   - 图标是不是也是**具象静物**（能从轮廓认出是什么东西），而不是几何符号？
     （图标自身的 `<title>` 只是「练习 / 试卷 / 知识点 / 知识图谱 / 记录」五个功能名，
     **不描述画的是什么** ⇒ 只能看形状，别看标题。）
2. 再看**实际页面上的空态**（`/w/walk/practice-sets` 的空工作区，或 `/w/walk/records` 的
   无记录态）—— 插画是不是真的出现在那里、比例对不对。
3. **这条判据本轮等于「未取证」** ⇒ 建议要么**补第二份种子重跑**、要么你**当场人工签字**，
   不要把「资产文件看起来对」当成判据已过。

---

## 5. 需要你确认

> **执行器不代签。** 下面每一格由**所有者**填；`PENDING` 是走查执行器给的合法终态，
> 只有人能改成 PASS / FAIL（`walkthrough-harness.md:1409-1420`、`:2017` 的 X-7）。

### 5.1 四条判据的签字位

| # | 判据 | 机器给的 | 我的**建议** | **你的判定**（PASS / FAIL / 需返工） | 签字 | 日期 |
|---|---|---|---|---|---|---|
| 3.2-3 | 夜纸下图标圆底为「降饱和 + 提亮」版本 | `PENDING`（数值齐、渲染层未测） | `需你定`（倾向 PASS） | ☐ | | |
| 3.4-4 | 错误态明确（红色仅用于失败与阻塞） | `PENDING`（36 条已逐点分类） | `FAIL`（4 处非失败红色） | ☐ | | |
| 3.6-2 | 图标与插画在同一套线宽与圆角语言内 | `PENDING`（线宽分布齐、圆角空集） | `需你定`（线宽 PASS、圆角待判） | ☐ | | |
| 3.6-4 | 插画为具象器物（不出现抽象几何团块） | `PENDING`（`S-12` 未采、无插画进 DOM） | `需你定`（本轮未取证） | ☐ | | |

### 5.2 待你裁决的具体事项（逐条）

| # | 事项 | 出处 | 需要你回答的 |
|---|---|---|---|
| ① | **任务书对 `3.2-3` 的一句话描述与判据原文不符** | `briefs/IMPL-W3j.md:21` 写「状态语义与用户侧措辞一致」；判据原文是「夜纸下图标圆底为『降饱和 + 提亮』版本」（`walkthrough-harness.md:1484` / `acceptance.md:110`） | 确认本页按**判据原文**写（我的处理）；若「状态语义与措辞」另有其人，请指认是哪一条判据 —— **它不在 38 条清单里** |
| ② | 顶栏品牌三色点的红点 | `workbench.css:549` | 纯装饰算不算「红色用于失败与阻塞」的例外？若不算 ⇒ 要改成中性/几何 |
| ③ | `.ai-plan-summary` 无条件红 | `workbench.css:1687`（装的是「查看输出」/摘要） | 改中性墨，还是给它加失败态条件选择器？ |
| ④ | 闪卡「另一面」的红边框 | `workbench.css:2002` | 两面卡的分类色该不该占红色？还是改成几何区分？ |
| ⑤ | 「重日」负荷红点 | `workbench.css:2392` | 「量高」算不算阻塞？还是换成黄/几何？ |
| ⑥ | 图谱「矛盾关系」的红竖条 | `workbench.css:1535` | 算不算阻塞？另：图谱本轮冻结（A-8 归 `graph-node-visual-language`），这条要不要**整条豁免**本判据？ |
| ⑦ | 插画的 18 种 `rx/ry` 算不算「同一套圆角语言」 | `assets/empty/*.svg` | 这是 `3.6-2` 的核心审美判断，机器给不出结论 |
| ⑧ | `3.6-4` 本轮未取证 | `shots.py:98-100` 的 S-12 `requires` | 补第二份空工作区种子重跑，还是你当场人工签字？ |
| ⑨ | 夜纸圆底要不要另拍一张**带导航**的图 | `S-10` 拍的是 hub，画面上无导航图标 | 要补拍（`/w/walk/practice` + 夜纸），还是接受本轮无图 |

### 5.3 复跑与重判

- **重新拿到这些产物**：`python tools/walkthrough/run.py --out tmp/wt-run-7`
  （只跑判据：`--only 3.2-3 3.4-4 3.6-2 3.6-4`；只跑 after 侧自检：`--skip-before`）。
- **判据不因重跑而变** —— 机器只给数值与证据，**签字仍在人手里**。
- **⚠️ 这些数字对应那一轮（after 侧内容指纹 = `4b4be87f`）；后续修复后需要重跑。**
  尤其 §2.4 判 FAIL 的 4 处、§4 说的插画未进 DOM —— 修完必须重跑再判。
- 截图索引见 `openspec/changes/workbench-visual-language-v2/acceptance-shots/index.md`
  （含 12 张对照图的路径与重跑命令）。
