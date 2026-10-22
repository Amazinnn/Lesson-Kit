# IMPL-C2 — 组件形态裁定 A 类 · **markup 波**（pages.py + JS）

> 来源：所有者的组件样式裁定（`design-notes/styleboard-picks.md` · A-115）。
> **形态定义以 `component-spec.md` §4.30 为准**。
> **只改 `workbench/server/pages.py` 与 `workbench/server/static/*.js`。**

## 你要落的四条（A 类里**需要 markup** 的那批）

| § | 组件 | 目标形态 | markup 要做的事 |
|---|---|---|---|
| 4.8 | 复选框 | **整行选中** | 每个选项**包一层行级容器** `.lk-check__row`（**类名必须与 CSS 波 IMPL-C1 一致**）；行内含 `.lk-check`（框）+ 标签文本 |
| 4.9 | 单选 | **整行卡选中** | 同上，容器类名 `.lk-radio-row`；行内含 `.lk-radio`（环）+ 标签文本 |
| 4.26 | 时间线节点 | **分隔线时间线** | **把两套几何合成一套**：`.agent-milestone`（18px 圆环）与 `.ai-plan-step`（9px 方块）⇒ 统一为「**发丝线分隔 + 小圆点**」。⚠️ 这一条主要在 `agent-ui.css` / `workbench.css`（CSS 波做），**你只负责 markup 的类名收敛**：两处产出**同一套类名**（建议 `.lk-timeline` / `.lk-timeline__item` / `.lk-timeline__dot`），让 CSS 波有唯一目标 |
| 4.27 | 折叠段 | **手风琴折叠段** | 四处原生 `<details>/<summary>` 各写各的 ⇒ **统一**成一套类名（建议 `.lk-disclosure` / `.lk-disclosure__head` / `.lk-disclosure__body`），**保留原生 `<details>` 的语义与键盘行为**（不要自己写开合逻辑！）⇒ 只加类名与结构包裹，**不动开合行为** |

## 硬约束
- **现有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、事件绑定、判定分支 —— 一律不动。
  ⚠️ §4.27 **不许**自己实现开合逻辑（原生 `<details>` 已经在做）—— 只统一结构与类名。
  ⚠️ §4.8 / §4.9 **不许**改选项的取值与提交方式（载荷键不变，G-1）。
- **知识图谱一行都不许碰**（`pages.py` 里的图谱函数 / 分支）。
- **不许新增请求、零池写入、零新增 localStorage 键**。
- 只加类名与包裹结构，**不要**顺手改文案（文案是 P26 的活，**另一个 agent 正在改 `pages.py`**）。
  ⚠️ **并发提示**：P26（文案清理）正在改 `pages.py` 与 `static/*.js` ⇒
  **开工前先 `git pull`/确认工作树状态**，若发现对方未提交，**等它提交后再动手**，
  或只改与你无关的行并**在报告里写明冲突点**。**不许** `git add -A` / `git commit` 不带路径。
- 提交一律 `git commit -- <明确的路径列表>`。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
```
- **选项的载荷与提交不变**：改前改后各跑一遍练习提交，比对**请求方法 + 路径 + 载荷键集合**
  （底线守卫 G-1 的精神）⇒ 在报告里贴出来。
- **键盘可达性**：选项仍能被 Tab / 方向键选中（原生 radio/checkbox 行为不能被包裹破坏）——
  实测一遍，在报告里写结果。
- 走查：仓库根 cwd · 独立端口 · 池副本 + `LESSONKIT_WB_HOME`；
  ⚠️ **服务字节数 == 磁盘字节数**（A-39）；⚠️ 代理坑 ⇒
  `env -u http_proxy -u https_proxy -u all_proxy`。

## 落盘纪律与回报
- **一个组件一个 commit**，只 `git add --` 你自己改的那几个路径。
- 报告写到**新文件**：`openspec/changes/workbench-visual-language-v2/reports/IMPL-C2-report.md`。
  ⚠️ **不要**写 `decisions.md` / `IMPLEMENTATION-LOG.md` / `contract-drift.md` / `tasks.md` /
  `component-spec.md`（主会话的活）。
- 回报（中文）必含：已落盘路径 + 每个 commit 的 hash 与内容 +
  **逐条「改前 → 改后」**（尤其：新增行级容器的类名与结构、折叠段四处统一的类名、
  时间线两套类名的收敛）· **载荷与请求序列未变的证据** · **键盘可达性实测** ·
  截图路径 · 六条验证命令结果 · **待裁决项**。
