# IMPL-W2j — CSS 收口三：夜纸巡检的 6 处 + 负荷柱错峰 + 状态点几何

> 来源：**N1 夜纸全站巡检**（`night-sweep-report.md`）+ **N2 契约一致性核对**
> （`contract-consistency-report.md`）+ 主会话自查。
> **只改 `workbench/server/static/workbench.css`**（+ `agent-ui.css` 的一处硬编码色）。

## 硬约束
- **只改 `workbench/server/static/workbench.css`** 与 `workbench/server/static/agent-ui.css`。
  **绝不改** `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` /
  `records.py` / `middle-navigation.js` / `assets/` / `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **知识图谱区段与 12 个裸名一行都不许碰**（`grep -n "Knowledge graph V2" workbench.css`）。
  ⚠️ **图谱页冻结块**（`body:has(#layout[data-page="graph"])`）**要改，但只许「补钉」**，
  **不许改动它已钉的 20 来条新名 pin**。
- 现有交互逻辑一个字都不许改。
- 只用现有 token；**不许硬编码浅色值**（要改主题相关取值，**先改 OpenSpec** —— 见 A-96）。
- 动效红线：起始态只写在 `@keyframes` 内；**只动 `transform` / `opacity`**；状态色瞬切；
  **静态样式 = 终态**（降级档下必须直接是终态）。
- 提交一律 `git commit -- <明确的路径列表>` 限定范围（**不要 `git add -A` / `-a`**）。

## 一、N1 巡检的 P0：图谱页章节透镜面板**夜纸下变了**（**最高优先**）
- 现象：`/w/<ws>/graph` 的 `#chapter-lens-panel`（`workbench.css:589-603`）
  底色亮 `rgb(255,255,255)`（`--surface-raised` 浅）→ 夜 `rgb(43,38,32)`；
  展开后**整页 AE = 109,912 px**（面板矩形内 7,800 px）。
- 根因：**图谱冻结块漏钉** `--surface-raised` / `--elev-2` / `--elev-3` 等 token。
- 修法：**在冻结块里补钉**这些 token 到**改造前的取值**（与已钉的 20 来条新名 pin 同一口径）。
  ⚠️ **不要**改成「把顶栏浮层移出图谱作用域」——那是结构改动。
- 验证：夜纸下展开面板的**底色 / 阴影**与亮色**逐字节相同**；整页 AE = 0。
  （默认态已经逐字节相同 —— 别弄坏它。）

## 二、CD-175：删掉死规则，**全站旧名归零**
- `.status-dot` / `.status-dot.ok` / `.status-dot.warn`（`workbench.css:2123-2125`）
  **零引用**（`grep -rn "status-dot" --include=*.py --include=*.js --include=*.html` 无命中），
  连带 `:244` 的 `--dsw-state-success: #22c55e`（**全站唯一的旧名残留**）也是死代码。
- ⇒ **删掉这四条** ⇒ 任务 2.3 当时保留的「契约外绿」例外**作废**，
  **全站 `--dsw-` / `--lk-` 引用归零**。
- ⚠️ 删前**自己 grep 确认零引用**（含 `pool/` 与内容模板）。

## 三、CD-174：负荷柱的**逐柱 24ms 错峰**补实现（`tasks.md` 20.1 曾被误勾，已改回未勾）
- 现状：服务端**确实**逐柱写了行内 `animation-delay:{index * 24}ms`，
  但 CSS 的 `.bar-fill` **没有任何 `animation` 属性** ⇒ 延迟挂在一个**不存在的动画**上。
- 修法：给 `.bar-fill` 加一条**只动 `transform`** 的生长关键帧
  （`transform-origin: bottom`，`scaleY` 从 0 长到 1），**静态样式 = 终态**（`scaleY(1)`），
  降级档下**直接满格**（现有的降级闸门 `animation-name: none` 会兜住）。
  ⇒ 行内那 24ms 延迟随即生效。
- ⚠️ 高度编码（`style="height:Npx"`）**保持不变** —— 那是另一重编码。
- 验证：录帧确认**逐柱错峰**（第 N 柱比第 N-1 柱晚 24ms 起）且**终态一致**。

## 四、N1 的三处 P1（一行 CSS 级的修）
| # | 现象 | 修法 |
|---|---|---|
| 1 | **记录中心热力日历在夜纸下倒转** —— `.level-0..4` 用 `color-mix(in srgb, var(--role-blue) N%, white)`，**混色底写死 `white`** ⇒ 夜纸下仍是亮块（level-0 卡面对比 **14.89:1**、level-1 13.61:1、level-2 11.51:1，83 个元素三通道均 ≥200）⇒ **「0 次」档成了最亮项** | 混色底改**主题底**（`var(--asset-paper)` 一类的 token）⇒ **亮色取值也会变** ⇒ **按 A-96 先改 OpenSpec 再改实现**（**不要**只改一边） |
| 2 | **练习页「今天」日历圆点** —— `.calendar-cell.today .calendar-day`（`workbench.css:2381-2384`）用 `color: var(--ink-strong)` 落 `--role-yellow` 底 ⇒ 夜纸 **1.51:1**（亮色同元素 10.07:1 ✅）⇒ 日期数字几乎不可见 | 文字改 `var(--ink-on-warm)`（夜纸 10.61:1 ✅，**亮色零变化**） |
| 3 | **`lk-dot--ink`** —— `--dot-fill: var(--ink-strong)` ⇒ 夜纸 13.96:1（达线）但**中性点成了三点里最亮的**（红 5.00:1、黄 9.86:1）⇒ 语义漂移 | `--dot-fill` 改 `var(--ink-faint)`（夜 4.97:1 / 亮 3.59:1） |

## 五、N2 的 INC-05：Paper 状态点**补几何**（灰度下不可分）
- 现状：`paper-practice.js` 出 6 态，但 `workbench.css:3957-3980` **只有 `correct` 有几何**，
  `wrong` / `stuck` 同一行规则 ⇒ **灰度下不可分**；`filled` / `unanswered` 只差颜色。
- 修法：**复用已经存在的** `.lk-dot--cross` / `--dash` / `--check` 几何族
  （W2e 刚补的那一族）⇒ 每态有**形状 + 颜色**两通道。
- ⚠️ **只改 CSS**：markup 侧由 `paper-practice.js` 产出的 class **不要动**
  （那是别的 agent 的文件）⇒ 若需要 markup 加类，**在回报里写明「需要 markup 侧加什么」**。

## 六、N1 的两处亮色主题既有缺陷（顺手修）
- `lk-combo-banner__count` **黄字 1.54:1** ❌ · `lk-dot--yellow` **1.60:1** ❌
  （均违反权威表 §4.4-10；夜纸下反而达标）。
- 修法：把这两处的**黄**换成**承载文字该用的** `--role-yellow-deep`
  （权威表 §3.4：黄色填充承载面积，**文字走 `--role-yellow-deep`**）。

## 七、`agent-ui.css` 一处硬编码
- `agent-ui.css:346` 的 `.agent-approval-card` 硬编码 `background: #fff9df`
  ⇒ 夜纸下是亮块。⇒ 改用**主题 token**（浅/夜两套值）。
  ⚠️ 这条 N1 没能触达（无 AI 会话）⇒ **你要顺带核一遍 `agent-ui.css` 里还有没有别的硬编码浅色**
  （`grep -nE "#[0-9a-fA-F]{6}" agent-ui.css`），一并改成 token。

## 八、两处**要人工裁决的，不要自己拍板**
- **`.primary` 按钮的墨色描边 + 硬阴影**在夜纸下读作发光（描边 vs 蓝面 2.64:1；文字 6.07:1 ✅）
  —— **需人工看图**（`night-sweep-shots/practice-completion-night.png` / `practice-stem-night.png`），
  可能要给权威表 §6.3 补一条窄例外。**你只把它列出来，不要擅自改**。
- **`.lk-dot--ink` 的语义**（已掌握 vs 未标记）⇒ 决定换成 `--ink-faint` 还是新钉一个中性点 token。
  **先按 `--ink-faint` 落地**（N1 给的建议），并在回报里标明这是**按建议落地、语义待裁**。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **图谱零差异**：区段**逐字节不变**；R-2 差异像素 0；
  **夜纸下展开章节透镜面板的整页 AE = 0**（这是本波的主目标）。
- **热力日历**：亮/夜两态的 `.level-0..4` 取值都**随主题变**（不再是写死 `white`）。
  ⚠️ 改亮色取值**必须先改 OpenSpec**（`specs/workbench-ui/spec.md` 的 Records center 条款
  + `night-paper-tokens.md` §3.10）—— **主会话已裁 A-96**，你按它落地。
- 走查：仓库根 cwd、独立端口、池副本 + `LESSONKIT_WB_HOME`；服务字节数 == 磁盘字节数。
  打开**记录中心**（热力日历 + 图例）、**练习页**（今天的圆点）、**图谱页**（展开透镜）各截一张**夜纸**图。

## 落盘纪律与回报
- **一个主题一个 commit**，只 `git add workbench/server/static/workbench.css workbench/server/static/agent-ui.css`，
  **不要 `git add -A``**；**提交用 `git commit -- <明确的路径列表>` 限定范围**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**八项逐条的「改前 → 改后 + 实测值」** +
**夜纸下展开透镜面板整页 AE = 0 的证据** +
**负荷柱逐柱错峰的录帧证据** + **图谱区段逐字节未变** +
**两处要人工裁决的** + 四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
