# IMPL-C1 — 组件形态裁定 A 类 · **样式波**（workbench.css + agent-ui.css）

> 来源：所有者的组件样式裁定（`design-notes/styleboard-picks.md` · A-115）。
> **形态定义以 `component-spec.md` §4.30 为准**（§4.30 > 各节裁定框 > 各节正文）。
> **只改 `workbench/server/static/workbench.css` 与 `workbench/server/static/agent-ui.css`。**

## 你要落地的 20 条（A 类里**纯样式**的那批）

| § | 组件 | 目标形态 | 关键点 |
|---|---|---|---|
| 4.1 | 主按钮 | 无影平底 | 蓝底 **无描边、无阴影**；高度 40px；hover 抬起 1px；底色瞬切 |
| 4.2 | 次按钮 | 沉底次按钮 | `--surface-sunken` + **内发丝线**（不是描边） |
| 4.3 | 文字按钮 | 带箭头 | `::after` 画右箭头（**不引 SVG**）；gap 8px；随文字墨色 |
| 4.4 | 图标按钮 | 圆形图标按钮 | **40×40 圆形** + 沉底面；**命中区 ≥44px**（伪元素补） |
| 4.5 | 输入框 | spec 输入框 | 44px 高 · 12px 圆角 · `padding: 0 14px` · 聚焦蓝边 + 3px 蓝洗底光晕 |
| 4.6 | 文本域 | spec 文本域 | 最小高 96px · 行高 1.6 · 12px 圆角 · `resize: vertical` |
| 4.10 | 开关 | 迷你开关 | 轨道 32×18；**命中区 ≥44px**（伪元素）；关态仍 `--ink-disabled` |
| 4.11 | 分段控件 | 药丸分段 | 整组胶囊槽；**选中项是白色药丸**（`--surface-raised`）⇒ **不用角色蓝** |
| 4.12 | 标签 | 角色色标签 | 角色色洗底 + **左侧状态点**；黄**不承载文字**；同卡 ≤2 个 |
| 4.13 | 徽标 | 胶囊计数 | 胶囊轮廓 + 沉底实心；11px 字 |
| 4.14 | 状态圆点 | spec 全几何集 | 补 **ring / half / filled** 三档；**尺寸收到 10px** |
| 4.15 | 进度条 | 胶囊进度 | 8px 胶囊 · 轨道 `--veil-active` · 填充角色蓝 |
| 4.17 | 题号格 | spec 形态 | **36px 方 + 12px 圆角** + 六态；「当前」用**黄实心** |
| 4.18 | 卡片 | spec 留白 | 留白 **24px**（`--sp-5`） |
| 4.19 | 纸面层级 | spec 四层 | 底 / 卡 / 浮起 / 沉底，靠圆角 + 柔影 + 内发丝线 |
| 4.20 | 沉底块 | 竖线沉底 | 沉底面 + **左侧 4px 黄竖线**（黄只承载面积） |
| 4.21 | 空态 | 卡面空态 | **卡面 + 柔影**（不是沉底面） |
| 4.22 | 骨架屏 | **呼吸式** | **不做横扫**；底色**整体明暗呼吸**；**无表面渐变** |
| 4.23 | 吐司 | spec 吐司 | 右上角浮起面 · 12px 圆角 · 13px 字 · 左侧状态点 · 浅底深字 |
| 4.26 | 时间线节点 | 分隔线时间线 | **不画竖线**；发丝线分隔 + 小圆点；**两套几何合一** |
| 4.27 | 折叠段 | 手风琴折叠段 | 卡面 + 48px 头 + 内容在同一张卡里；四处**统一** |
| 4.28 | Tab | 分段式标签页 | 用分段控件形态；与 §4.11 **合并成同一个类** |

（表里 21 行 ⇒ 20 类；§4.8 / §4.9 / §4.16 / §4.24 / §4.25 / §4.7 见下。）

## ⚠️ **不在你这一波里的**（别碰）
- **§4.8 复选框整行选中 / §4.9 单选整行卡选中** ⇒ 需要**行级容器 markup**
  （另一波 `IMPL-C2` 负责 markup）。你**只**把
  `.lk-check__row` / `.lk-radio-row` 的**样式**写好（选中时整行蓝洗底 + 框的几何），
  **markup 由 C2 落**。⇒ **类名必须与 C2 完全一致**：
  `.lk-check__row` · `.lk-radio-row`（C2 也按这个名字写）。
- **§4.7 自绘下拉 / §4.16 分段进度条 / §4.24 对话框 / §4.25 工具调用卡**
  ⇒ **B 类**：产品里没有，**必须先改 OpenSpec**（单开 change `workbench-component-forms`）。
  **你不许实现它们**，只允许把**已有的同名/近名**样式归并到 spec 形态
  （例如 §4.11 的药丸分段可以顺带作为 §4.28 Tab 的复用底座）。

## 硬约束
- **现有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、事件绑定、判定分支 —— 一律不动。
- **知识图谱区段与 12 个裸名一行都不许碰**（`grep -n "Knowledge graph V2" workbench.css`）；
  **图谱页冻结块**（`body:has(#layout[data-page="graph"])`）只许「补钉」。
  ⚠️ **图谱页的 `.toast`（仿古硬编码）与 `.seg` 归 `graph-node-visual-language` change（图谱冻结）**
  ⇒ **不许改**它们，只改非图谱页的同名件。
- 只用现有 token；**不许硬编码 hex**。
- **动效红线**：起始态只写在 `@keyframes` 内；**只动 `transform` / `opacity`**；
  状态色**瞬切**；**静态样式 = 终态**（降级档必须直接是终态）。
  ⚠️ §4.22 的呼吸式**只动 `opacity`**（或底色），**不得动位置**，且**不得用渐变**。
- **命中区 ≥44px** 与**焦点环**是**唯一不可让步**的两条。
- 提交一律 `git commit -- <明确的路径列表>`；**不许 `git add -A` / `-a` / `git add <目录>`**。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **暖纸 + 夜纸各截一轮**：练习页 / 记录中心 / 设置视图 / Agent 右栏。
- **对比度**：改完跑 `python tools/verify_tokens.py`（新增/改动的那几组不许跌破阈值）。
- **图谱零差异**：区段**逐字节不变** + R-2 差异像素 0。
- 走查：仓库根 cwd · 独立端口 · 池副本 + `LESSONKIT_WB_HOME`；
  ⚠️ **服务字节数 == 磁盘字节数**（A-39）；⚠️ 本机代理会吞 localhost ⇒
  `env -u http_proxy -u https_proxy -u all_proxy`。

## 落盘纪律与回报
- **一个组件一个 commit**（或一个主题一个），只 `git add --` 那两个 CSS 路径。
- 报告写到**新文件**：`openspec/changes/workbench-visual-language-v2/reports/IMPL-C1-report.md`。
  ⚠️ **不要**写 `decisions.md` / `IMPLEMENTATION-LOG.md` / `contract-drift.md` / `tasks.md`
  / `component-spec.md` —— 那是主会话的活（共享台账，并发写会冲突）。
- 回报（中文）必含：已落盘路径 + 每个 commit 的 hash 与内容 +
  **逐条「改前 → 改后 + 实测值」**（尤其：主按钮无影、次按钮沉底、
  图标按钮 40×40 且命中区 ≥44、开关 32×18、状态圆点 10px 且补齐三档几何、
  题号格 36px 方、卡片留白 24px、骨架屏呼吸且无渐变、时间线两套几何合一、
  Tab 与分段控件合类）· 暖/夜双主题截图路径 · 对比度实测 · 图谱零差异证据 ·
  六条验证命令结果 · **待裁决项**（拿不准的登记，**不要自行拍板**）。
