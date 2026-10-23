# IMPL-W6 — 文档同步（收口轮）：把这一波的用户可感知变化写进职责文档

> 对应 `tasks.md` 的 **28.1–28.5** 的**收尾部分** + 第 18/19/20/21 组带来的
> **用户可感知行为变更**的契约同步。
> **只改 `docs/` 与 `openspec/changes/workbench-visual-language-v2/specs/`。**

## 为什么现在做
这一波有**六处用户可感知的行为变更**，按 `AGENTS.md` 的契约协调纪律，
**必须在同一个 PR 同步**职责文档（之前几轮的实现 agent 按硬约束不得碰 `docs/` 与 `openspec/`，
所以攒到这一轮一起做）。

## 本波要同步的六处（**逐条写清改哪个文件的哪一段**）

| # | 变更 | 要同步的文档 |
|---|---|---|
| 1 | **知识点列表改「按章分组」的卡片列表**（组头是章标识如 `ch06`；排序**跨分组可用**；组头不随排序移动、行不跨组迁移） | `docs/PRODUCT-MANUAL.md` §3.2（知识点页）· `openspec/.../specs/workbench-ui/spec.md` 的 Records/Knowledge 条款 |
| 2 | **完成页的进度带**（静态满格、庆祝时重放 0→100% 生长；**降级档直接是满格**） | `docs/PRODUCT-MANUAL.md` §6.x（练习页完成页）· 同上 spec |
| 3 | **三个此前「渲染是空的」组件现在有形态了**：`.lk-switch`（开关）· `.lk-seg`（分段控件）· `.icon-only`（图标按钮） | `docs/PRODUCT-MANUAL.md` §10（外观与主题）· `docs/GLOSSARY.md`（若引入新名词） |
| 4 | **焦点环恢复**：3 处 `outline: none` 改成 `:focus-visible` 的可见焦点环（**键盘用户能看见焦点**） | `docs/PRODUCT-MANUAL.md` §10（外观与主题）· 若 spec 有键盘可达条款则同步 |
| 5 | **图谱页的两个作用域专用 token**：`--graph-page-caption` / `--graph-page-dimmed`（**仅图谱页存在**，非图谱页回落 `--ink-faint`） | `design-notes/night-paper-tokens.md` §3.3 值集（**A-83**）· `docs/GLOSSARY.md` 若需要 |
| 6 | **别名期收尾**（任务 2.3）：旧 token 别名**全部退役**，`.rich-text` 挂载名**全部退役** | `docs/ARCHITECTURE.md`（若列了旧 token 名）· `docs/GLOSSARY.md`（若 `.rich-text` 有词条）· `docs/ACTION-GRAPH.md` 的「改级」条目（**已登记过，确认它写的是最终状态**） |

## 硬约束
- **只改** `docs/` 下的文件 与
  `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`
  与 `openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md`。
- **绝不改**产品代码（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）——
  **另有 agent 正在并行改那些文件**。
- **不要**改 `openspec/changes/workbench-visual-language-v2/` 下的其它文件
  （`decisions.md` / `contract-drift.md` / `tasks.md` / `design.md` / `briefs/` ——
  **主会话统一维护**）。
- ⚠️ `docs/PENDING-DEFINITIONS.md` **不要提交也不要还原**（工作区里有别人 2026-10-18 的未提交改动）。
- ⚠️ **写「已实现的事实」**：每条都要能在实现里指出落点（文件 + 位置）。
  **不许**把「已定义」写成「已实现」，也**不许**把「计划」写成「现状」。
- **不许**把「未落地」写成「已落地」—— 这一波**没有**实现的部分不许进文档。

## 一条硬要求（**这次是重点**）
**三处口径必须一致**：**页面 / 样式表 / 手册**写的日历五档区间必须都是
**0 / 1 / 2–3 / 4–7 / ≥8**（CD-170 已结案，别把它改回去）。
同理，这一波**新增或改动**的任何「数值口径」（档位、间距、字号、阈值），
都要在**文档里写清具体值**，不要写「若干」「大约」。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate workbench-visual-language-v2 --strict
```
- **自检**：本波写进文档的每一条用户可见行为，**都要能在实现里指出落点**；
  **不许出现产品里不存在的功能**。
- ⚠️ 有一处**实现先行、spec 还没写**的：**空态用沉底面**（`decisions.md` **A-73**）⇒
  **把它写进 `specs/workbench-ui/spec.md` 的空态条款**（spec 是设计权威，
  实现先行时要**把 spec 补到与实现一致**，并说明理由）。

## 落盘纪律与回报
- **一个职责文件一个 commit**，只 `git add` 你改的那几个文件，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**六处逐条的「改前 → 改后 + 实现落点（file:位置）」** +
**空态条款补进 spec 的那一段** + **三处口径一致的核对结果** +
四条验证命令结果 + 待裁决项。
- 数字与事实一律以**当场核对到的现状**为准。
