# IMPL-W5b — 文档收尾：L4 工作流图同步 · §10.1 落地状态更新 · 派活清单整理

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **28.3**（L4 同步）
> 与 **28.1 / 28.2** 的收口。**只改 `docs/` 下的文件。**

## 背景
第 28 组（28.1–28.5）刚交完六份职责文档的同步，但**留了两处尾巴**：
1. `docs/action-graph/README.md` 要求新增 / 退役 / 改级动作**同步 L4**，
   而 `docs/action-graph/L4-workflows.md` 不在上一波的文件范围里 ⇒ **L4 未同步**。
2. `docs/PRODUCT-MANUAL.md` **§10.1「本轮视觉改造的落地状态」** 里列的六条 CSS 缺口，
   已被登记进 `contract-drift.md` **CD-171**（由主会话登记），文档要与登记表口径一致。

## 硬约束
- **只改 `docs/` 下的文件**：
  `docs/action-graph/L4-workflows.md` · `docs/PRODUCT-MANUAL.md` · `docs/ACTION-GRAPH.md` ·
  `docs/action-graph/L3-actions.md`（若需要）· `docs/GLOSSARY.md`（若需要）。
- **绝不改**产品代码（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）——
  **另有几个 agent 正在并行改那些文件**。
- **不要**改 `openspec/` 下任何文件（主会话统一维护）、**不要**改 `tasks.md` 的复选框。
- ⚠️ `docs/PENDING-DEFINITIONS.md` **不要提交也不要还原**（工作区里有别人 2026-10-18 的未提交改动）。
- 写**已实现的事实**；**不许**把「已定义」写成「已实现」，也**不许**把「计划」写成「现状」。

## 要做什么

### 1. L4 工作流图同步（28.3 的最后一腿）
- 读 `docs/action-graph/README.md` 里对 L4 的要求（**它规定了同步口径**），再读
  `docs/action-graph/L3-actions.md` 里上一波登记的 4 条：
  **新增**「切换主题（暖纸 / 夜纸，走台灯转场）」·「连对升级反馈（三级计数器 + 火苗簇 + 一份参数化横幅 + 断裂负反馈）」；
  **退役**「跨页练习范围托盘」；**改级**「渲染阅读内容」挂载名 `.rich-text` → `.wb-reading`。
- ⇒ 在 `L4-workflows.md` 里把对应的**工作流图**补上/改掉，**按 README 规定的写法**。
- ⚠️ 如果某条动作**在 L4 里没有对应的工作流**（例如「连对升级反馈」是练习流程内部的一段），
  **不要硬造一条工作流** —— 在回报里说明「这条属于 L3 粒度，L4 无对应」，
  由主会话决定是登记还是不加。

### 2. PRODUCT-MANUAL §10.1 的落地状态更新
- 上一波在 §10.1 列了六条「本波 CSS 未跟上的部分」：状态圆点 · 章节计数条 · 连对三档配色 ·
  作答区沉底底色与题号大数字 · 日历格子高度与图例 · 完成页进度带。
- 这些**正在被下一波 CSS agent 修**（`briefs/IMPL-W2d.md` 收了一部分，
  另一部分在排队）。⇒ 你的写法：**如实写成「实现已落地、样式在本波补齐中」**，
  并**逐条标注它属于哪一波**（`briefs/IMPL-W2d.md` 还是排队中的 CSS 波）。
  **不要**写成「已完成」——那是撒谎；也不要写成「未做」——那是过时。
- 若这六条在**你动手时**已经落地了（别的 agent 可能刚好补完），就按实际状态写。

### 3. 派活清单整理（供主会话直接用）
把上一波与本波汇总出的**待派实现清单**整理成一份**可执行的清单**，
落在 `openspec/changes/workbench-visual-language-v2/IMPLEMENTATION-LOG.md` **不要动** ——
改为**追加到 `docs/PRODUCT-MANUAL.md` 的 §10.1 末尾**一小节「**本轮未落地的实现项**」，
每条写清：**现象 / 涉及文件 / 归哪一波 / 验收怎么看**。
清单至少含（以你**当场核对到的现状**为准）：
- CSS 侧：`.lk-streak` / `.practice-streak` / `.lk-flames` 三档配色与布局 ·
  `.lk-stat` / `.lk-stat__value` / `.lk-stat__label` 完成页数字槽排版 ·
  `.lk-error-nudge` 类规则 · `.lk-celebrate-anchor` 定位 · **火苗形状**（`.lk-flame-off`/`.lk-flame-on` 不可见）·
  `.paper-answer-block` / `.paper-answer-label`（作答区沉底块与 16px 标签，**CSS 里零命中**）·
  `.level-0` 档位 · 日历格子高度编码 · 章节计数条 / 状态圆点样式
- 服务端侧：作答日历的 fill + height 双编码 + 五档阈值具名常量 + 档位图例
- 交互侧：连对反馈补到试卷流（**A-54**）· 降级档里程碑音效仍响（**A-53**）
- 结构侧：知识点页「分组卡片」（`pages.py` 目前是**扁平清单**，spec 18.1 要的是分组）
- 已登记漂移：CD-166（组卷报告显示 id）· CD-167（里程碑第二条件不可判定）·
  CD-168（D-13 vs layout-spec 互斥）· CD-169（图谱页 z-index 取舍）· CD-170（日历双编码缺一半）·
  CD-171（§10.1 六条 CSS 未跟上）

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```
- **自检**：你写进文档的每一条用户可见行为，都要能在实现里指出落点；
  **不许出现产品里不存在的功能**；**不许把「已定义」写成「已实现」**。

## 落盘纪律与回报
- **小步提交**：L4 一个 commit、§10.1 一个 commit，分开，**只 add `docs/` 下你改的文件**，
  **不要 `git add -A`**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**L4 同步了哪几条、哪几条「L4 无对应」** + **§10.1 六条的实际状态（逐条）** +
**「本轮未落地的实现项」清单的条目数** + 四条验证命令结果 + 待裁决项。
- 事实一律以**当场核对到的现状**为准，不要照抄任务书里的旧描述。
