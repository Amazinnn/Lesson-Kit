from pathlib import Path


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    s = text.find(start)
    if s < 0:
        raise SystemExit(f"{label}: start marker missing")
    e = text.find(end, s + len(start))
    if e < 0:
        raise SystemExit(f"{label}: end marker missing")
    return text[:s] + replacement.rstrip() + "\n\n" + text[e:]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# PRODUCT-MANUAL: keep it operational, but stop teaching staged-list/manual-pick
# as the product model. Existing compatibility controls are named as such.
# ---------------------------------------------------------------------------
manual_path = Path("docs/PRODUCT-MANUAL.md")
manual = manual_path.read_text(encoding="utf-8")
manual = replace_between(
    manual,
    "### 2.2 准备练习：今天要练的",
    "## 3. 选定范围：知识点页与知识图谱",
    r'''### 2.2 先定范围，再组一张 Paper

练习页是**练习出发页**。知识点页、知识图谱、建议区和 Agent 都可以帮你回答「这次想练什么」，但它们给出的只是**组卷范围（Scope）**，不是一份会被直接执行的题目队列。

范围为空时，先去知识点页或图谱选知识点；已经有范围时，练习页可以把它紧凑地列出来供你核对和删除。这个列表只是 Scope 的显示，不再叫「准备练习列表」，也不是第二份数据。

### 2.3 建议：作为组卷起点

到期、薄弱和每日计划仍可以按需给出建议。每条建议只有知识点名称和一句人话原因；接受建议的含义是**把它作为这次组卷的范围或方向**，不是向正在执行的练习里加题。已经开始的 Paper 不会因为新建议而改变。

### 2.4 组卷：系统决定具体题

范围确定后，由 Lesson Kit / Agent 依据范围、来源、难度、薄弱、到期、错题等条件形成一张具体 **Paper（试卷）**。Paper 是最小可执行单位；真正进入 Practice Run 前，题目顺序已经冻结。

当前实现里仍可能看到 `exam / micro / yes_no / flash_card` 等兼容模式控件，它们描述内容怎样呈现和作答，不再意味着「一轮练习只能有一种题型」这个产品约束。后续混合题型 Paper 可以在同一张卷里组合不同作答形式。

命令行 `lesson-kit pull` 是确定性组卷引擎。例如：

```bash
lesson-kit pull <工作区> --kp dmath-ch06-kp-002 --n 8
lesson-kit pull <工作区> --source-kind final --exam-year 2023
lesson-kit pull <工作区> --origin-kinds source_problem --origin-kinds adapted_problem
lesson-kit pull <工作区> --wrong --n 20
```

`--problem <id>` 仍保留，但它是 **Agent/CLI 作者工具**：用于组卷时精确固定某一道题，不是学生侧「手动挑题加入练习」入口。

`pull --plan` / `pull --print` 继续用于导出可复现清单与打印稿；`lesson-kit papers <工作区> save --input <清单>` 把一张 Paper 保存进当前兼容存储。`.lessonkit/practice-sets/`、`ps-NNN` 和 manifest 的 `kind: practice-set` 是迁移期实现名，不等于产品层的 Practice Set（题单）。

### 2.4.1 来源筛选：约束组卷，不手选题

来源筛选面板保留四个维度：来源类型、题目来源方式、考查年份、来源文档。**维度内是 OR，维度间是 AND**；这些条件只约束下一次 Paper Assembly。

旧的「题干关键词 / 来源关键词搜索后勾具体题加入本轮」已经退役。搜索接口可以继续用于只读查找或 Agent/CLI 作者工作流，但浏览器不再把命中题通过 `include_ids` 注入练习。想精确固定某题，由 Agent/CLI 在组卷阶段使用 `--problem`。

筛选条件仍是浏览器临时状态，不写学习记录；开始一张 Paper 后，再修改筛选也不会改变正在进行的 Practice Run。

### 2.5 开始与结束

点击开始后，Lesson Kit 执行**已经确定的 Paper**。Practice Run 负责当前 item、作答、判定、自评与进度；它不会在中途因为 Scope、来源筛选、到期状态或建议变化而再拉新题。

做完或提前结束后回到出发页。若选择「再练同类」，系统据刚才的范围/结果**重新组一张新 Paper**，不会向旧 Paper 继续追加题目。

### 2.6 一个完整的开场例子

1. 在知识图谱勾选「链式法则」和「隐函数求导」；这只是 Scope。
2. 回练习页，把来源限制为「期末 + 2023」。
3. 点击组卷/开始；系统先确定本次 Paper 的题目，再进入 Practice Run。
4. 做题途中即使切换章透镜或出现新的到期建议，这张 Paper 也不变。
5. 做完后若想继续巩固，选择「再练同类」会组一张新的 Paper。
''',
    "manual chapter 2 practice model",
)
manual = replace_once(
    manual,
    "范围（要练哪些知识点）只有两个加入入口：知识点页和知识图谱页。两个页面的勾选与练习页的准备练习列表**实时是同一份数据**——在哪边改都一样。阅读、导航、排序都不会改变勾选。",
    "Scope（这次想练哪些知识点）主要从知识点页和知识图谱页显式选择；练习页只是同一 Scope 的汇总与组卷入口，不再维护一份独立的「准备练习列表」。阅读、导航、排序都不会改变 Scope；Scope 变化也不会改写已经开始的 Paper。",
    "manual chapter 3 scope intro",
)
manual = replace_once(
    manual,
    "练习范围**只能**来自你的显式勾选（或建议区里你亲手点的「加入」）。对话里随便聊天、系统的弱项排序、每日建议，都不会悄悄改你的范围。唯一的例外也握在你手里：Agent 只有在收到你的**明确练习意图**时才可能替换范围（见第 8 章）；普通对话永远只读。",
    "Scope 只在你明确选择、接受建议或明确要求 Agent 调整时变化；普通对话、弱项排序、每日计划不会偷偷改它。Scope 只约束后续组卷，**已经开始的 Paper 永远不因 Scope 变化而增删题目**。Agent 的 `replace_practice_selection` 兼容动作也只表示替换组卷 Scope，不直接创建或修改 Practice Run。",
    "manual scope invariant",
)
manual_path.write_text(manual, encoding="utf-8")


# ---------------------------------------------------------------------------
# REQUIREMENTS: current human summary follows the live OpenSpec vocabulary.
# ---------------------------------------------------------------------------
req_path = Path("docs/REQUIREMENTS.md")
req = req_path.read_text(encoding="utf-8")
req = replace_once(
    req,
    "- 练习由弱项、显式选区、题型、来源、到期和可选难度条件拉取；任何排序都不得锁题。",
    "- 练习先由显式 Scope、题型策略、来源/难度条件和弱项/到期/错题证据**组装 Paper**；Practice Run 只执行已经冻结的 Paper items，任何排序或调度都不得锁题或中途注入新题。",
    "requirements current scope",
)
req = replace_once(
    req,
    "  两参数都空返回空集而非全池，命中后由浮窗按 `include_ids` 显式指定。",
    "  两参数都空返回空集而非全池；命中结果只用于只读发现或 Agent/CLI 作者工作流，浏览器不再通过 `include_ids` 把具体题注入练习。",
    "requirements browser include",
)
req = replace_between(
    req,
    "## 组一次练习与打印",
    "## 接口归属",
    r'''## 组卷、Paper 与打印

- `lesson-kit pull` 是当前确定性 **Paper Assembly** 引擎：可组合 Scope（`--kp`，缺省章透镜）、条件筛选、薄弱（`--weak`）、到期（`--due`）、错题（`--wrong`）和上限；每题回报 `scope / weak / due / wrong / explicit` 等入卷理由。
- `--problem <id>` 只作为 Agent/CLI **作者工具**保留，用来在组卷时精确固定某题；浏览器不提供手动逐题选择，也不允许 `include_ids` 改变 Practice Run。
- `--plan` 写可复现的 Paper manifest；v1 wire-level `kind: practice-set` 与 `ps-NNN` / `.lessonkit/practice-sets/` 仍是兼容实现名，不把产品级 Practice Set 定义成可执行对象。
- `lesson-kit papers <workspace> save --input <manifest>` 把一张 Paper 保存到工作台兼容存储；产品级 Practice Set 是组织多张 Paper 的容器，本身不执行。
- `--print <目录>` 输出学生卷与解答卷；`--check` 零写入检查题数、缺口、缺解、重复和泄漏。
- 新 Practice Run 的产品来源语义统一为 `paper`。历史 `quick / practice_set / agent` 可读、可重放，但重放的新执行按 Paper 语义创建。
- “练习某知识点”“建议复习”“再练同类”都先形成一个新的 Paper；已经开始或已经结束的 Paper 不会被动态追加题目。

''',
    "requirements Paper section",
)
req_path.write_text(req, encoding="utf-8")


# ---------------------------------------------------------------------------
# ACTION-GRAPH summary: preserve implemented action names but correct semantics.
# ---------------------------------------------------------------------------
summary_path = Path("docs/ACTION-GRAPH.md")
summary = summary_path.read_text(encoding="utf-8")
summary = summary.replace("PULL[拉题/拉卡]", "PAPER[组卷 / Paper Assembly]")
summary = summary.replace("SEL[replace_practice_selection]", "SCOPE[replace_practice_selection<br/>设置组卷 Scope]")
summary = summary.replace("PULL --> DB", "PAPER --> DB")
summary = summary.replace("CONV -->|明确练习意图| SEL --> P", "CONV -->|明确练习意图| SCOPE --> P")
summary_path.write_text(summary, encoding="utf-8")


# ---------------------------------------------------------------------------
# L3 actions: rename the practice loop without pretending compatibility APIs vanish.
# ---------------------------------------------------------------------------
l3_path = Path("docs/action-graph/L3-actions.md")
l3 = l3_path.read_text(encoding="utf-8")
old_rows = '''| 选定练习范围（选择是唯一来源） | UI 勾选 | 人 | 选区键 | 已实现 |
| 加入今日要练 | UI 建议区 | 人 | 选区键 | 已实现 |
| 开始本轮练习（模式+自评时机必选） | UI | 人 | 牌组 | 已实现 |
| 拉题/拉卡 | API/CLI | 双 | 牌组 | 已实现 |
| 组一次练习（范围/单题/条件筛选/薄弱·到期·错题；逐题 reason） | CLI `pull` | Agent | —（只读选择） | 已实现（2026-09-25） |
'''
new_rows = '''| 选定组卷 Scope（回答「想练什么」） | UI 勾选 / 范围托盘 | 人 | 选区键 | 已实现（兼容 UI） |
| 接受建议作为组卷范围 | UI 建议区 | 人 | 选区键 | 已实现（按钮文案可继续迁移） |
| 组装 Paper（Scope/条件筛选/薄弱·到期·错题；逐题 reason） | UI / CLI `pull` | 双 | —（只读选择） | 已实现（v1 兼容组卷） |
| 精确固定题目进 Paper | CLI `pull --problem` / Agent | Agent | —（只读选择） | 已实现；**非学生手选入口** |
| 开始 Practice Run（执行固定 Paper） | UI / active-practice API | 人 | active practice checkpoint | 已实现；新来源语义 `paper` |
'''
if old_rows not in l3:
    raise SystemExit("L3 practice rows drifted")
l3 = l3.replace(old_rows, new_rows, 1)
l3_path.write_text(l3, encoding="utf-8")


# ---------------------------------------------------------------------------
# L4 workflows: replace the old dynamic session loop and old 'single problem' paper flow.
# ---------------------------------------------------------------------------
l4_path = Path("docs/action-graph/L4-workflows.md")
l4 = l4_path.read_text(encoding="utf-8")
l4 = replace_between(
    l4,
    "## W1 · 练习回路",
    "## W2 · 内容入库（唯一合法写池通道）",
    r'''## W1 · Paper → Practice Run 练习回路

```mermaid
flowchart TD
  A[明确 Scope<br/>知识点页/图谱/建议/Agent] --> B[Paper Assembly<br/>来源·难度·薄弱·到期·错题]
  B --> C[冻结 Paper item 顺序]
  C --> D[开始 Practice Run]
  D --> E{当前 item 形式}
  E -- 闪卡 --> F[回忆→揭示]
  E -- 微题/判断 --> G[点选→本地判定]
  E -- 综合题 --> H[作答→揭示解析]
  F & G & H --> I{当前自评设置}
  I -- immediate --> J[记录自评/学习结论]
  I -- batch --> K[完成 item·末尾统一自评]
  I -- off --> L[按既有 off 规则结算]
  J & K & L --> M{Paper 还有 pending item?}
  M -- 有 --> E
  M -- 无 --> N[归档 Practice Run<br/>Paper items 不再变化]
  N --> O{再练同类?}
  O -- 是 --> B2[用结果/Scope 重新组一张新 Paper] --> C
  O -- 否 --> P[回练习出发页]
  X1[中途改 Scope/筛选/章透镜] -.只影响下次组卷.-> B
  X2[练习页发消息问 Agent] -.只带聚焦上下文·零写入.-> Z[(当前 Paper 不变)]
```

核心不变量：**Scope 回答想练什么，Paper 回答这次具体做什么，Practice Run 只负责把这张 Paper 做完。**
任何建议、筛选、调度或对话都不得向运行中的 Paper 动态加题；“再练同类”永远组新 Paper。

''',
    "L4 W1",
)
l4 = replace_between(
    l4,
    "## W6 · 组一次练习并打印（2026-09-25）",
    "## W7 · 做题记录、来源筛选与对话内换模型（2026-09-26）",
    r'''## W6 · 组一张 Paper、保存与打印

```mermaid
flowchart TD
  A[确定 Scope<br/>章透镜/--kp/显式知识点] --> B[加入组卷约束<br/>来源/难度/weak/due/wrong]
  B --> C[Paper Assembly · pull]
  X[Agent/CLI 需要精确某题] -.作者工具 --problem.-> C
  C --> D[固定顺序 + reason<br/>scope/weak/due/wrong/explicit]
  D --> E{下一步}
  E -- 直接开始 --> F[Practice Run<br/>执行固定 Paper]
  E -- --plan --> G[Paper manifest<br/>v1 kind: practice-set 兼容]
  G --> H{保存到工作台?}
  H -- 是 --> I[lesson-kit papers save] --> J[保存的 Paper]
  H -- 否 --> K{导出/检查?}
  J --> F
  K -- --check --> L[零写入预检]
  K -- --print --> M[学生卷 + 解答卷]
  Y[浏览器学生侧] -.不提供逐题搜索勾选/include_ids.-> C
```

`--problem` 只属于 Agent/CLI Paper authoring；学生控制 Scope 和策略，不逐题手选。产品级 Practice Set 是组织多张 Paper 的容器，不在本工作流直接执行。

''',
    "L4 W6",
)
l4_path.write_text(l4, encoding="utf-8")


# Guard only current docs, not historical records/archive.
for path in (manual_path, req_path, summary_path, l3_path, l4_path):
    text = path.read_text(encoding="utf-8")
    if path in (manual_path, req_path) and "命中后由浮窗按 `include_ids` 显式指定" in text:
        raise SystemExit(f"{path}: browser include_ids wording survived")

Path(".github/workflows/one-shot-align-practice-docs.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-align-practice-docs.py").unlink()
