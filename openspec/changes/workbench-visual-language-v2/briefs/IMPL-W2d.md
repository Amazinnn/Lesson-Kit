# IMPL-W2d — CSS 收尾：记录中心卡片密度 · 取消 `.card` 描边 · 判定符号统一 · 孤儿 CSS 清理

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` 的
> **19.2（页高落在 5500–6500px）** · **3.3（取消描边）** 的收口，以及跨组 CSS 遗留。
> **只改 `workbench/server/static/workbench.css`**。

## 前置（自己核实，不要相信任何人的口头汇报）
第 3 波的 CSS 部分（W2c）已落地：token 层 + 夜纸值集 + 三栏几何 + 标志带 + 顶栏 +
`.wb-reading` 阅读层 + `.wb-reading--stem` 变体 + 动效 token + 分级降级闸门。
**动手前先读 `workbench.css` 现状**（`git log --oneline -- workbench/server/static/workbench.css`）。

## 硬约束
- **只改 `workbench/server/static/workbench.css` 这一个文件。**
  **绝不改** `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` /
  `middle-navigation.js` / `records.py` / `tests/` / `docs/` / `openspec/`
  （**另有几个 agent 正在并行改其中几个**，且 `records.py` 的内联 SVG 需要你这边先落伪元素）。
- **不要**改 `tasks.md` 的复选框（主会话统一勾）。
- **知识图谱区段与图谱 12 个裸名一行都不许碰**（按选择器定位：`grep -n "Knowledge graph V2" workbench.css`）。
- **不动图谱页冻结块**（`body:has(#layout[data-page="graph"])`）—— 那是 G-5 的保护机制。
- 现有交互逻辑一个字都不许改。

## 要做什么

### 1. 19.2 页高：记录中心明细从 8951px 收到 5500–6500px
- 实测：`?view=attempts` 中栏 `scrollHeight = 8951px`（目标 5500–6500px，改造前 8895px）。
- 差距全在卡片密度：`.record-row` 的 `padding 12px×2 + margin 12px` ≈ 36px/卡。
- ⇒ 把 `.record-row` 收到约 **22px/卡** 量级（建议 `padding: 8px 14px; margin: 0 0 6px`），
  实测目标 ≈6300px。
- ⚠️ **不要靠删字段解决** —— 六项字段一个不少（题目 + 评语 + 摘录 + 判定 + 自评 + 时间）。
- ⚠️ **页高目标以「单列卡片流」为准**（`design.md` **D-13**）。`design-notes/layout-spec.md` §5.6
  里「明细卡流用 2 列网格」的说法与 D-13 **互斥**，已由 `decisions.md` **A-50** 裁定采信 D-13
  ⇒ **你不要改成 2 列**。
- 验证：把实测页高贴进回报（`?view=attempts` 的 `scrollHeight`）。

### 2. 3.3 收口：`.card` 基类去掉描边
- D-13 要求卡片流「**不描边**，靠留白 + `--elev-1` 分隔」，
  但 `.card` 基类仍带 `border: 1px solid var(--ink-strong)`。
  ⇒ 去掉该描边（改用留白 + `--elev-1`）。
- ⚠️ `records.py` 侧目前用**内联 `border:0`** 兜住了明细/错题卡；你改完 CSS 后那些内联声明
  就成了冗余（等值无害）。**你不要去改 `records.py`** —— 在回报里写明「可以删掉那些内联 `border:0` 了」，
  由主会话安排。
- ⚠️ 但**运行卡 / 图表卡**等仍是描边的 —— 一并按同一规则去掉，保持卡片语言一致。

### 3. 判定符号统一为伪元素（避免双标记）
- `records.py` 目前给「错 / 未判定」两态输出**内联 SVG** 几何符号，
  而「对」态的勾形是 CSS 伪元素（`.record-verdict-ok`）⇒ **三态实现不统一**。
- ⇒ 在 CSS 里给 `.record-verdict-bad` / `.record-verdict-open` 补上**同语言的伪元素**
  （红叉 / 空心环，线宽与圆角对齐 `.record-verdict-ok` 的勾形，**只动 `transform` / `opacity` 无关**，
  静态样式即终态）。
- ⚠️ 补完之后 `records.py` 里的内联 SVG 会变成**双标记**（伪元素 + 内联 SVG 同时出现）。
  ⇒ **你只做 CSS 那一半**，在回报里写清「`records.py` 的两处内联 SVG 现在要删」，
  由主会话安排（`records.py` 的 owner 已收工，可安全改）。

### 4. 孤儿 CSS 清理
- `.record-trend` / `.record-day` / `.record-day-bar` / `.record-day-value` / `.record-day-label`
  这一族**已成孤儿**（趋势图改用 `.bar-*` 组件后无引用）⇒ 删掉。
- 验证：删前 `grep -n "record-day\|record-trend" workbench/` 应只有这些定义处；
  删后命中 0，且记录中心页面观感不变（由 owner 在验收时核）。

### 5. 判定分布图不要复用 `.record-rating-*`
- 判定分布图当前**复用了** `.record-rating-*` 类名（条形填充色用内联覆盖为墨/红/淡墨）——
  语义上应拆成 `.record-verdict-*`。
- ⇒ CSS 里**新增** `.record-verdict-dist*` 一族（或等价命名）承载判定分布条，
  并把 `.record-rating-*` 留给自评圆点。**类名由你定**，但要在回报里写明最终类名，
  主会话再让 `records.py` 侧对齐（**你不要改 `records.py`**）。

## 验证
- 跑 AGENTS.md 四条验证命令：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- **图谱页逐像素零变化**（G-5）：改完后用 `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
  （必须仍是 0 条差异 —— 它查的是物理坐标，但**同时**要确认你没动图谱区段的 CSS）。
- 走查服务按 **A-39**：仓库根为 cwd、独立端口（不要 3081 / 3092 / 3099）、
  池副本 + 隔离注册表；启动后比对服务字节数与磁盘字节数必须相等。
  ⚠️ **本机有端口上残留旧进程的先例**（`SO_REUSEADDR` 会让你以为接管了，其实请求打到了旧副本）——
  截图前确认端口上的服务是**你刚起的那个**（比对字节数 + 看进程启动时间）。
- 记录中心 4 个视图 + 零记录空态各截一张（headless Chrome 可用，chromium 148 已装）。

## 落盘纪律与回报
- **小步提交**：一个主题一个 commit，只 `git add workbench/server/static/workbench.css`，
  **不要 `git add -A`**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 + **记录中心 `?view=attempts` 的实测页高**
  + **新定的类名清单**（`.record-verdict-dist*` 等）+ **需要主会话去 `records.py` 删/改的清单**（逐条）+
  **图谱区段未动的证据** + 四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
