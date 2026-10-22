# IMPL-W2f — 任务 2.3：别名期收尾（删旧 token + 删 `.rich-text` 规则 + 冻结块改钉新名）

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **2.3**。
> **只改 `workbench/server/static/workbench.css`**（+ 权威表补一个 token，见下）。
> ⚠️ **本任务必须是一个独立提交**（A-44）。

## 这是本轮最后一块硬骨头
别名期（任务 2.1）建了 24 条 `--lk-*` / `--dsw-*` → `var(新 token)` 的别名，
供旧引用点使用。**现在 HTML 侧的旧引用已全部迁完**（`.py` / `.js` 里 `rich-text` 命中 **0**），
⇒ 可以把别名**连同引用点一起删干净**。

⚠️ **风险点**：别名删完后，**图谱页的取值必须一字不变**（G-5）。
别名期期间图谱之所以没变，是因为「图谱页冻结块」把旧值钉了回来 ——
**删别名时冻结块也必须一起改**（A-43 原文：「别名期结束（任务 2.3）时，
这块要改成钉**新** token 名」）。

## 硬约束
- **只改 `workbench/server/static/workbench.css`**。
  **绝不改** `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` /
  `middle-navigation.js` / `records.py` / `agent-ui.css` / `tests/` / `docs/` /
  `openspec/`（**另有几个 agent 正在并行改其中几个**）。
- **不要**改 `tasks.md` 的复选框（主会话统一勾）。
- **知识图谱区段（`/* Knowledge graph V2` 起）与图谱 12 个裸名一行都不许碰。**
- **不动图谱的算法**（`graph-physics*.js` / `graph-renderer.js` 一律不碰）。
- **零新增请求、零池写入、零交互逻辑改动** —— 本任务只动 CSS。
- 动效红线不变；新增/修改的规则**起始态只写在 `@keyframes` 内**。

## 要做什么（逐项；每项都要有「改前 → 改后 + 证据」）

### 1. 5 处 `--dsw-label-caption` + 1 处 `--dsw-label-dimmed` → `--ink-faint`
- 位置（**按选择器现场定位，不要用行号**）：`.topbar-separator` · `.side-heading span` ·
  `.item-id` · `::placeholder` 等共 6 处。
- **为什么零差异**：别名 `--dsw-label-caption: var(--ink-faint)` 本身已解析到 `--ink-faint`
  ⇒ 换成 `--ink-faint` **取值完全相同**（图谱页也相同：冻结块钉的是 `--ink-faint`）。
- ⚠️ 这正是 **A-43** 裁定的「字面合并 + 同波改冻结块」。

### 2. 3 处 `--dsw-border-l1` → **新增 token `--rule-faint`**
- 位置：`#graph-detail-panel .graph-dashboard-metrics`（border + background）与
  `.graph-relation-row`（border）。
- **为什么不能直接换 `--rule-hair`**：图谱页上 `--dsw-border-l1` 被冻结块钉成
  `rgb(0 0 0 / 4%)`，而 `--rule-hair` 是 10% ⇒ 直接换会**改图谱像素**。
- **做法**：
  1. 在**权威表** `design-notes/night-paper-tokens.md`（§3 值集）新增 **`--rule-faint`**：
     亮 = `rgb(0 0 0 / 4%)`（**就是改造前 `--dsw-border-l1` 在图谱页的取值**），
     夜 = 给一个同量级的暖白低透明值（例：`rgb(255 238 210 / 4%)`，你自己定并说明）。
  2. 在 `workbench.css` 的新 token 层（`:root`）**定义它**（值集块，不在别名块里）。
  3. 3 处引用改成 `var(--rule-faint)`。
  4. **不要**在冻结块里给它加 pin —— 这 3 条规则**只出现在图谱页**
     （`#graph-detail-panel` / `.graph-relation-row`），
     非图谱页根本看不到它 ⇒ **非图谱页的值无关紧要**，零像素影响。
- ⚠️ **同时在权威表里写清它的用途**（「更弱一档的发丝线」），
  并在 `docs/GLOSSARY.md` 里**若需要**补一句（**先问主会话**，不要自己改 GLOSSARY）。

### 3. 删掉 `--lk-ripple-base` 这个**回退名**
- CSS 现在读 `var(--ripple-base, var(--lk-ripple-base, var(--surface-base)))`。
- ⚠️ **`--ripple-base` 与 `--lk-ripple-base` 都不许在 CSS 里定义** ——
  定义了就会**遮蔽 JS 在 `:root` 上的 inline 写入**（A-42）。
- ⇒ 改成 `var(--ripple-base, var(--surface-base))`（去掉旧名回退即可；
  **不要**顺手把 `--ripple-base` 定义进 CSS）。
- JS 侧（`workbench.js`）已经写 `--ripple-base` ⇒ 不需要改 JS。

### 4. 删掉 `.rich-text` 的 **36 处 CSS 规则**
- HTML 挂载点已全仓归零（`.py` / `.js` 命中 0）⇒ 这 36 处是**死规则**。
- ⚠️ 删之前**自己 grep 确认**：`grep -rn "rich-text" workbench/ --include=*.py --include=*.js`
  必须是 **0**（若不是，**停下报告**，别删）。
- 删干净：`.rich-text` 的**所有**选择器（含与 `.wb-reading` 并列写在一起的那些）。
  ⚠️ **注意**：很多规则是 `.wb-reading, .rich-text { … }` 这种**并列选择器** ——
  ⇒ 删的时候**只去掉 `.rich-text` 那半，保留 `.wb-reading` 那半**。

### 5. 别名块：删掉 24 条「别名期，勿新增引用」的别名定义
- 逐条删（`grep -c "别名期，勿新增引用"` 归零）。
- ⚠️ **两条例外，不许删**：
  1. **`--dsw-state-success: #22c55e`** —— 它是**契约外绿**（DSH 的 success 态，
     **不表达「答对」**），`tasks.md` 4.4 明写「**本条不动它**」。
     ⇒ 保留定义，并把引用点（`.status-dot.ok`）改成**直接用这个变量名**（它就是它的来源）。
  2. **权威表里没有名字、但实现需要**的项 —— 若你发现还有别的「不是别名而是字面值」
     的旧名定义，**逐条列出来报给我**，不要自己判断。

### 6. 冻结块：把 37 处**旧名 pin** 换成**新名 pin**
- 冻结块现在同时钉了**新名**（`--surface-base` / `--ink-strong` / `--role-blue` …，共 20 来条）
  与**旧名**（`--lk-paper` / `--lk-ink` / `--lk-blue` / `--lk-yellow` / `--lk-red` /
  `--dsw-font-family` / `--dsw-font-code` / `--dsw-border-l1` / `--dsw-state-*` 等，37 条）。
- ⇒ **旧名 pin 全删**（旧名本身随第 5 步消失，留着就是悬空定义）。
  **新名 pin 一条都不许动**（那是图谱取值不变的保证）。
- ⚠️ **字体栈要核**：`--dsw-font-family` / `--dsw-font-code` 原来被钉在冻结块里；
  而共享层现在用 `--font-ui` / `--font-mono`。
  ⇒ **先确认**新层的 `--font-ui` / `--font-mono` 的取值与旧的 `--dsw-font-family` /
  `--dsw-font-code` **逐项相同**（旧栈见 `workbench.css` 别名块的注释）。
  相同 ⇒ 删掉旧 pin 即可；**不同 ⇒ 停下报告**（那会改图谱页的字体）。

### 7. **一个独立提交**（A-44）
- 本任务的内容**必须在一个 commit 里**（不要拆成「删别名」+「删规则」两个）。

## 验证（每项都要有证据）
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
**字面验收**（任务 2.3 原文）：
```bash
# 旧名引用点：应只剩「允许的例外」
grep -rnE "var\(--(lk|dsw)-" workbench/ --include=*.css --include=*.js --include=*.py
# 别名定义：应归零（--dsw-state-success 除外）
grep -c "别名期，勿新增引用" workbench/server/static/workbench.css
# 新层定义 vs 被引用集合：差为空
grep -oE "var\(--[a-z0-9-]+" workbench/server/static/workbench.css | sed 's/var(//' | sort -u
```
⚠️ **图谱零差异是硬要求**：
- **图谱区段逐字节不变**（`awk 'NR>=<图谱起点>' workbench.css` 与改前基线 `diff` 无输出）；
- **R-2 口径**（画布区）**差异像素 = 0**；
- 走查时用 `tools/walkthrough/launch.py`（仓库根 cwd、**独立端口**、
  池副本 + `LESSONKIT_WB_HOME` 隔离注册表），并比对服务字节数与磁盘字节数相等。
- ⚠️ **R-3 的采样点**按 **A-65** 固定在**左栏纸面区域内**（那里改造前后都是 `--surface-sunken`）。

## 落盘纪律与回报
- **一个独立 commit**，只 `git add workbench/server/static/workbench.css`
  （权威表若改了，只 add `design-notes/night-paper-tokens.md`），
  **不要 `git add -A`**。
- **不要**改 `tasks.md` 的复选框。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**7 项逐条的「改前 → 改后 + 证据」** +
**字面验收的三条命令的真实输出** +
**「允许的例外」清单（逐条说明为什么允许）** +
**图谱区段逐字节未变的证据 + R-2 差异像素数** +
**字体栈比对的结论** + 四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
