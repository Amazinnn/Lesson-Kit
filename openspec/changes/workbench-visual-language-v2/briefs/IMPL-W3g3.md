# IMPL-W3g3 — 知识点分组卡片（18.1）+ 章节透镜面板的 JS（15.4）

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **18.1** 与 **15.4 的 JS 侧**。
> **只改 `workbench/server/pages.py` 与 `workbench/server/static/workbench.js` 这两个文件。**

## 为什么必须由**同一个人**同时改这两个文件
W3b 已把 `pages.py` 侧做完了，但**分组卡片有���硬依赖**：
`workbench.js` 的 `bindKnowledgeSort()` 用 `list.children` 过滤 `.knowledge-row`，
再 `list.replaceChildren(rows)`。**分组把行下沉一层** ⇒ `list.children` 里没有行了
⇒ `rows` 为空 ⇒ **排序控件静默失效**（不报错、只是不动）。

⚠️ 这撞「现有所有交互逻辑一个字都不许改」这条底线 ⇒ **只做 markup 会让排序当场变哑**。
⇒ **markup 与那段 JS 必须一起改**，且**排序必须仍然可用**。

## 硬约束
- **只改 `workbench/server/pages.py` 与 `workbench/server/static/workbench.js`**。
  不碰 `workbench.css`（**另一个 agent 正在并行改它**）、`practice-flow.js` /
  `paper-practice.js` / `middle-navigation.js` / `records.py` / `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **不要**改 `tasks.md` 的复选框（主会话统一勾）。
- **现有所有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、排序控件的**语义**、
  章节切换的请求与内容、焦点行为一律不动。
- **零新增请求、零池写入**：分组只用**已有的知识点列表**分组，不新增取数。
- 知识图谱：`pages.py` 里与图谱相关的函数 / 分支**一行都不许碰**。

## A. 18.1 知识点分组卡片

**要求**（任务 18.1 原文）：列表改**分组卡片** —— 按**章节或状态**分组，
每组一个标题 + 组内圆角卡；`data-kp-order` 仍可保持课程顺序排序。

**你要做的**：
1. **分组策略由你定**（章节 or 状态），但要**写清你选了哪个、为什么**。
   ⚠️ 状态分组要考虑三态（`needs_work` / `review` / `mastered`）与「未标记」；
   章节分组要考虑**当前透镜口径**（本章 / 全课程）—— **分组必须与透镜口径一致**。
2. markup：每组 = 一个**组标题** + 组内**圆角卡列表**；
   组的顺序与组内顺序都要**稳定**（课程顺序 / 状态优先级，**说清你用的排序键**）。
3. **排序控件必须仍然可用**：
   - 把 `bindKnowledgeSort()` 从 `list.children` 改成能**跨分组**取到全部行
     （例如 `list.querySelectorAll('.knowledge-row')`），
     排序后把行**重新分配回各组**（不能 `replaceChildren` 把组头冲掉）；
   - 排序后的**分组归属是否变化**，由你定并写清（建议：组头按**排序后的首项**重算，或
     **组头不随排序移动、只重排组内** —— 二选一，说明理由）。
   - **验证**：排序控件点几次，行的顺序真的变了，**且组头不丢**、**不报错**。
4. 空态、零记录态**不受影响**。

## B. 15.4 章节透镜面板的 JS

**现状**：`pages.py` 的 markup 已给（面板 + `.chapter-lens-option` + `aria-selected` + 保留原生 `<select>` 兜底），
但**打开 / 关闭 / Esc / 焦点归位 / 点外部关闭 / `aria-expanded` 同步的 JS 还没有**
（`workbench.js` 仍只绑 `#chapter-lens-switch` / `#chapter-lens-select`，两者 DOM 身份未动）。
面板默认 `hidden` ⇒ 当前零可见变化。

**你要做的**：
1. 面板的**开合行为**：`#chapter-lens-switch` 打开面板；**Esc** 关闭；**点外部**关闭；
   关闭后**焦点归位**到开关；打开时焦点进面板（或第一个选项）。
2. **`aria-expanded`** 在开关上**同步**；面板用 `role="listbox"` + 选项 `role="option"`；
   **键盘可达**：↑/↓ 移动、Enter/Space 选中、Home/End 跳首尾（**按既有同类控件的行为**，
   别自创一套）。
3. 选一个章节 ⇒ **走既有的章节切换路径**（`#chapter-lens-select` 已经在用的那条），
   **不要**新增请求或改载荷。
4. ⚠️ **面板内不得出现任何每章计数 / 统计 / 选择理由**（现行 spec 明令，`decisions.md` 9.4 已删计数）。
5. **原生 `<select>` 保留**作无 JS 兜底（**不要删**）。

## C. 顶栏「动作」段的桌面内容 —— **本轮不做**（已裁决）
顶栏三段式（品牌 / 当前身份 / 动作区）**已就位**，动作区当前只有窄屏抽屉按钮。
桌面段的「Agent 对话开关 + 主题切换」**不在本轮范围**：
主题切换已由**设置视图**提供（组 11），Agent 右栏也有自己的入口。
⇒ **不要**新增这两个可交互控件（G-8 的焦点序列要跟着登记，代价大而收益小）。
已登记为后续增量。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
```
- **排序控件必须真的能用**（点几次、顺序变、组头不丢）。
- 透镜面板：开 / 关 / Esc / 点外部 / 焦点归位 / 键盘六项**逐项实测**。
- 走查按 **A-39**：仓库根为 cwd、**独立端口**（**不要 3081 / 3092 / 3099 / 3411**）、
  池副本 + 隔离注册表；启动后比对服务字节数与磁盘字节数**必须相等**。

## 落盘纪律与回报
- **小步提交**：A（分组）与 B（透镜 JS）分开提交，
  A 的 commit 可以同时含 `pages.py` 与 `workbench.js`（它们**必须一起改**），
  B 只动 `workbench.js`。**只 add 你改的那两个文件，不要 `git add -A`**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**分组策略与排序键（说清选择与理由）** + **排序改造前后的代码对照（贴代码）** +
**透镜面板六项行为的实测结果** + **你发现的 CSS 侧缺口（类名清单）** +
四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
