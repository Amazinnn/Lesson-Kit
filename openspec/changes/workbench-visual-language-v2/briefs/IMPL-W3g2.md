# IMPL-W3g2 — 连对反馈补到试卷流 + 降级档里程碑音效仍响

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **17.1 / 17.8** ·
> **10.6**（A-53 / A-54）。
> **只改 `workbench/server/static/paper-practice.js` 与 `workbench/server/static/workbench.js`。**

## 背景
- **A-53**：`workbench.js` 的 `celebrateCompletion` 在 `motionMode() !== "full"` 时**直接 return**
  ⇒ 不挂爆点 ⇒ 挂在爆点上的**里程碑音效也不响**。
  ⇒ 裁决：降级档下**里程碑音效照响**（声音是独立通道；`prefers-reduced-motion` 管运动不管声音；
  降级档里爆点本就不存在，若音效也不响，这一档就完全无声无息）；
  ⇒ 音效要挂在**「进入里程碑档」这个判定**上，而不是挂在「爆点元素出现」上，**两者解耦**。
- **A-54**：连对反馈目前只挂在**快速练习流**（`practice-flow.js`）；
  **试卷流**（`paper-practice.js` 的逐题提交）同样有判定但没有这套反馈。
  ⇒ 任务 17.1 写的是「**常驻练习页**」⇒ **两个练习流都要挂**，
  且**复用同一套**（`window.lkTicker` / `window.lkFlame` / 同一份横幅），**不得另造一套**。

## 硬约束
- **只改 `workbench/server/static/paper-practice.js` 与 `workbench/server/static/workbench.js`**。
  不碰 `workbench.css`（**另一个 agent 正在并行改它**）、`practice-flow.js`、
  `pages.py`、`records.py`、`middle-navigation.js`、`docs/`、`openspec/`、`tasks.md`。
- **现有所有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、选项判定分支、自评一律不动。
  本轮只做「把既有反馈挂到另一个流」+「把音效从爆点上解耦」。
- **音效仍然只在四个点发**（答对 / 答错 / 完成 / 里程碑）—— **不许出现第 5 处**。
- 起始态只写在 CSS 的 `@keyframes` 内部（JS 只切 class / 写 `textContent`）。

## 要做什么

### 1. A-53：里程碑音效与爆点**解耦**
- 现在「里程碑音效」是靠**爆点元素出现**触发的（观察器 / 回调）。
  ⇒ 改成：命中**里程碑档判定** ⇒ 直接 `playCue("milestone")`；**动效档**另挂爆点（爆点不再负责发声）。
- ⚠️ **降级档（weak / off）也要响**；**日常档不响**。
- ⚠️ **绝不能因此出现第 5 处 `playCue` 调用点** —— 全仓仍**恰好 4 处**。
  ⇒ 把现有的里程碑调用点**改造**成「判定驱动」，而不是**新增**一处。
  验证：`grep -rn "lkSfx.playCue(" workbench/` 的调用点**恰好 4 处**。

### 2. A-54：连对反馈挂到试卷流
- 把 `practice-flow.js` 里那套（**三级计数器 + 火苗簇 + 一份参数化横幅 + 断裂负反馈**）
  **复用**到 `paper-practice.js` 的逐题提交路径。
- ⚠️ **复用**已有实现：Ticker 走 `window.lkTicker.set`、火苗走 `window.lkFlame.set`、
  横幅用**同一份** `.lk-combo-banner` 资产（**不得**为试卷流另做一份横幅）。
- ⚠️ **不得**自造第二套 Ticker / 火苗实现（`practice-flow.js` 里的那套是参考，但**优先复用 workbench.js 的公共 API**）。
- 判定的分叉点：答对 → 连对数 +1；答错且连对 **> 4** → 明确负反馈 + 归零；否则归零。
  （连对 > 4 答错**必须**明示负反馈，不得沉默 —— 17.3。）
- ⚠️ **试卷流有它自己的**「提交即判定」流程 —— 别改它的判定语义，只**加反馈**。

### 3. CSS 缺口只**报告**、不要自己改
- 以下类名**目前 CSS 里没有规则**（由另一波 CSS agent 补）：
  `.lk-streak` · `.practice-streak` · `.lk-flames`（计数器三档配色与布局）·
  `.lk-stat` · `.lk-stat__value` · `.lk-stat__label`（完成页数字槽排版）·
  `.lk-error-nudge`（类规则缺，现用内联 animation 兜底）· `.lk-celebrate-anchor`（现用内联定位兜底）·
  **火苗形状**（`.lk-flame-off` / `.lk-flame-on` 只有定位与透明度，**没有底色/图形 ⇒ 火苗不可见**）。
- ⇒ 你**照常挂这些类名**（结构先落地，样式后补），并在回报里逐条列出「CSS 侧还缺什么」。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js     # 13 个文件应全绿
```
- **`grep -rn "lkSfx.playCue(" workbench/` 恰好 4 处**。
- 截图/录屏走查：试卷流连对 1/3/5/10 四个时点 + 一次断裂负反馈 + 降级档下的里程碑（**要听得见**）。

## 落盘纪律与回报
- **小步提交**：A-53 一块、A-54 一块，分开 commit，只 add 你那两个文件，**不要 `git add -A`**。
- **不要**改 `tasks.md` 的复选框。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**音效四处落点的文件与行号（贴代码）** + **降级档里程碑发声的证据** +
**试卷流连对反馈的落点清单** + **CSS 侧还缺的类名清单（逐条）** +
四条验证命令 + node 测试结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
