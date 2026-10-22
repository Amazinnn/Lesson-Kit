# IMPL-W3g4 — A-58：连对实现抽成公共 `window.lkStreak`（两条流共用一份）

> 实现任务：`decisions.md` **A-58**（裁决已下，**实现未跟上** —— 上一波 agent 实测
> `window.lkStreak` 在全仓 **0 命中**）。
> **只改 `workbench/server/static/workbench.js` · `practice-flow.js` · `paper-practice.js` 这三个文件。**

## 为什么非做不可（这不是「重构洁癖」）
`practice-flow.js` 与 `paper-practice.js` 现在**各持一份连对状态机**：
计数 / 三级档 / 递增 / 断裂 / 复位 / 横幅 / 火苗 —— 两份几乎一样的实现。

**这一轮要治的病就是「同一个组件存在多个形态」**（见 `decisions.md` **F-1** 的说明）。
**同一个连对反馈有两份实现 = 同一个病的两个实例。**
⇒ 而且它已经造成过一次实际偏差：两份实现的**档位阈值**曾需要分别校准。

## 硬约束
- **只改那三个文件**。不碰 `workbench.css`（**另有 agent 正在并行改它**）、
  `pages.py` / `middle-navigation.js` / `records.py` / `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **不要**改 `tasks.md` 的复选框。
- **现有所有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、选项判定分支、
  自评、排序、两种练习流各自的判定来源 —— 一律不动。
- **零新增请求、零池写入**。
- 起始态只写在 CSS 的 `@keyframes` 内部（JS 只切 class / 写 `textContent`）。

## 要做什么

### 1. 在 `workbench.js` 落公共 API `window.lkStreak`
与既有的 `window.lkTicker` / `window.lkFlame` **同级**（它们就在旁边，照抄它们的写法与风格）。
API 负责**状态机**，不负责「判定来源」：
- 计数（+1 / 归零）
- 三级档（灰 → 黄 → 黄→蓝）与**档位的冗余通道**（底色档 + 内边距 + 火苗簇数）
- 递增时**点亮火苗簇**（`window.lkFlame.set`）
- 每逢 5 的倍数**点亮同一份横幅**（`.lk-combo-banner` / `.lk-combo-banner__count`）
- 断裂：连对 **> 4** 时**明确负反馈**（`lk-error-nudge`）→ 火苗**逐簇熄灭** → 归零
- 数字滚动走 `window.lkTicker.set`

⚠️ **阈值逐项保持现值**（两条流现在**本来就一致**，不许趁机改）：
`TIER_HOT 30`（第三档起点）· `FLAME_CAP 10`（火苗最多 10 簇）· `STAGGER 80ms`（点亮错峰）·
`STEP 40ms`（熄灭错峰）· `BANNER_EVERY 5`（每逢 5 的倍数）· `BREAK_OVER 4`（连对 > 4 必须明示负反馈）。

### 2. 两条流**都改为调它**（`practice-flow.js` 与 `paper-practice.js`）
- **判定来源仍留在各自的流里**：
  快速练习流读**微测判定**；试卷流读**提交载荷里的 `verdict`**。
  ⇒ 公共 API 只管「拿到判定之后怎么反馈」，**判定语义不动**。
- 删掉两份**各自的状态机**（`streakCount` / `streakTier` / `streakHtml` / `growStreak` /
  `breakStreak` / `judgeStreak` / `applyStreak` 之类）与**各自那份常量**，
  改为调用公共 API。⚠️ **横幅资产仍然只有一份**（同一套 `.lk-combo-banner`）。

### 3. 三条**不得改变**的行为（回归清单，逐条验）
| 行为 | 现在的口径 |
|---|---|
| 横幅触发 | **每逢 5 的倍数**（不是只有 5 与 10） |
| 断裂阈值 | 连对 **> 4** 答错**必须**明示负反馈（≤4px / 160ms，**不做屏幕级震动**）+ 计数器归零 |
| 火苗 | 最多 10 簇；点亮 80ms 错峰、熄灭 40ms 错峰；**逐簇**点亮与**逐簇**熄灭 |
| 档位冗余 | 颜色**之外**还有**内边距**与**火苗簇数**（不靠字重 —— 基线已是 700） |

### 4. **A-59 的口径要保住**（上一波刚落地）
试卷流的 `on_submit` 模式（**没有逐题判定** ⇒ 连对恒为 0）⇒ **不挂连对计数器**
（显示一个恒为 0 的数字是没有信息量的假事实）。判据用**既有的** `currentMode() === "on_submit"`。
⇒ 抽公共 API 时**不许**把这层判断弄丢。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node --check workbench/server/static/workbench.js
node --check workbench/server/static/practice-flow.js
node --check workbench/server/static/paper-practice.js
```
- **两条流各实测一遍**（用 `tools/walkthrough/launch.py`，**仓库根 cwd**、**独立端口**
  （**不要 3081 / 3092 / 3099 / 3191 / 3177 / 3178 / 3184 / 3411**）、池副本 + `LESSONKIT_WB_HOME` 隔离注册表）：
  1→5 连**逐格增长** · 5 连**点亮横幅** · 断裂时火苗**逐簇熄灭**（5→0）+ **明示负反馈** + **归零**；
  试卷流的 `on_submit` 模式**不挂**计数器。
- **前后对照**：改造前后的**请求序列完全一致**（before/after 各跑一遍对比）——
  这次是**纯重构**，任何请求差异都是回归。
- 真实池 `pool/dmath.db` 的 mtime / sha256 **全程未变**。

## 落盘纪律与回报
- **一个 commit**（或两个：先加公共 API、再迁两条流），
  只 `git add` 那三个文件，**不要 `git add -A`**。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**公共 API 的实际签名（贴代码）** +
**两条流的调用点（贴代码）** +
**删掉了哪些重复实现（逐个列出）** +
**§「三条不得改变的行为」逐条的实测值（两条流各一份）** +
**before/after 的请求序列对照** + 四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
