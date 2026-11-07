# 任务清单 —— V1 基线收敛

> 靶子：`openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html`
> 工具：`tools/walkthrough/view.py`（三列对照板）、`tools/walkthrough/probe.py`（响应式与抽屉判据）
>
> ⚠️ **每完成一项就出一次对照板**（靶子 | 改前 | 改后），给所有者看。
> ⚠️ **同文件串行**：`workbench.css` / `workbench.js` / `pages.py` 一波只碰一个文件的**同一段**。

## 1. 开工前（必做，不写码）

- [x] 1.1 读 `design.md` 的 D-1…D-4 与两个 Open Questions；**搜索通路与状态词表两项要先定**
      （未定就停，不要在产品里试词）
      —— 两个 Open Question 都已按文档裁定（见 `design.md` 末尾），裁定写进 design.md。
- [x] 1.2 读 V1 拼版：`design-notes/mockup-baseline/v1.html`（对照页）
- [x] 1.3 起隔离走查服务（`tools/walkthrough/launch.py`，**避开禁用端口**，用 `tmp/` 下的独立
      scratch + 池副本 + `LESSONKIT_WB_HOME`），抓一份「改前」基线图
      —— 端口 3599（不在禁用名单里）；每组各抓一对「改前 / 改后」。
- [x] 1.4 跑一遍 `pytest tests -q` 确认起点是绿的 —— 起点 1198 passed。

## 2. 顶栏动作区（§2.2 · DRIFT-2）

- [x] 2.1 在 `docs/GLOSSARY.md` 落新状态词的**契约词面**（若第 1 组未定词表，先做其余三项）
      —— **不需要新词**：复用「行动提醒」的 重点练习 / 可以复习，第三态**没有词**（保持中性）；
      GLOSSARY 写明那是「学生侧唯一允许的状态词汇」，另造第四个词会与该条目冲突。
- [x] 2.2 `pages.py`：把 `#workspace-select` **搬进顶栏段二**（**id 不变** ⇒ JS 绑定与测试照旧）
- [x] 2.3 `pages.py`：段三放四个控件 —— 搜索 · 对话视图 · 夜纸 · Agent 对话
      （顺序照靶子段三；A-143「构图以靶子为准」）
- [x] 2.4 `workbench.css`：四个控件按 V1 的形态（34×34 卡面 / 圆角 12px / 18px 图形）
      —— ⚠️ **形态听 A-115 不听 V1**（`component-spec.md` §4.30 / V1-1 §2 权威分工）：
      文字按钮 = 既有 `button.ghost`（40px + 12px 圆角 + 命中区补到 44px）、
      两个开关 = 既有 `.lk-switch`（轨道 32×18）、Agent 对话 = 既有 `button.outline`（沉底次按钮）。
      靶子的「药丸卡面外壳 + 40×22 轨道 + `aria-pressed`」**不抄**。
- [x] 2.5 `workbench.js`：Agent 开关接 `data-ai-collapsed`（桌面端折叠右栏）；
      主题开关接 `saveSetting("theme", …)`；对话视图开关接既有 rail 视图切换 —— **不新增机制**
      —— 顺带补上此前缺失的那一环：宽屏折叠此前只把第三轨归零、`#ai-column` 仍被
      `min-width: 360px` 撑住 ⇒ 补折叠规则；学习者自己收起的右栏不因 resize 弹回来。
- [x] 2.6 键盘可达 + 焦点环 + 可访问名（`acceptance.md` 的 G-7/G-8 口径）
      —— 开关用原生 `checkbox[role=switch]`（§6.2）、命中区 ≥44px、焦点环落在轨道上。
- [x] 2.7 出对照板；跑 `probe.py static`（3.5-1/2/3 仍须 PASS）—— ✅ `tmp/wt-v1/board-w1.html`

## 3. 右栏会话分组（§6.1）

- [x] 3.1 在**客户端**按会话时间戳分桶（今天 / 昨天 / 更早）—— 不加后端端点
      —— 按**本地日历日**分桶（`updated_at` 是 UTC ISO；取 UTC 日期切片会把深夜会话算到昨天）。
- [x] 3.2 组标题只写recency措辞，**不带任何计数/统计**
- [x] 3.3 分组不影响滚动容器（`#ai-session-list` 自滚）与消息流
      —— `#ai-session-list` 早已是 `overflow-y: auto`（3.4-6 PASS）；分组是它里面的容器。
- [x] 3.4 出对照板；`probe.py static` 复核 —— ✅ `tmp/wt-v1/board-w2.html`

## 4. 优先回看状态点（§6 状态几何）

- [x] 4.1 从**理由类别**映射到三个状态（重点练习 / 可以复习 / 保持中性）
      —— 新增纯函数 `weak.review_states`（Domain 层、零 IO）：有学习信号 = 重点练习；
      无信号但复习已到期 = 可以复习；其余 = 中性。**不按分数阈值**（阈值会随公式漂移）。
- [x] 4.2 复用既有 `.lk-dot` 家族的 10px 盒与几何（filled / ring / half / dash / cross / check）—— **不新画**
      —— 颜色与几何取 `component-spec.md` §3.6 / §4.14 的映射表；产品**没有蓝色档**，
      故第三态走「未开始 = 中性墨 + ring」（靶子的蓝环已登记契约漂移）。
- [x] 4.3 条目形态按 V1：卡面 + 柔影 + 12px 圆角 + 8/12 内距 + 状态点在前
- [x] 4.4 出对照板 —— ✅ `tmp/wt-v1/board-w3.html`
      —— 状态在**服务端渲染路径**上算 ⇒ `/api/w/{name}/weak` 的载荷仍是原四个字段（实测未变）。

## 5. 左栏分组结构（§3.1/§3.2）

- [x] 5.1 首组名改「学习」，容纳五个学习入口（练习 / 试卷 / 知识点 / 知识图谱 / 记录）
      —— 导航项名**一个都不改**（copy-table §2.12 P-151 定稿为「留」）；copy-table P-158 同步改判。
- [x] 5.2 设置组、优先回看组按 V1 的分组与间距 —— 组间 24px、**组间不再画分隔线**；
      组标题与组内内容同一条 12px 文字列；左栏内距 16px 12px。
- [x] 5.3 出对照板 —— ✅ `tmp/wt-v1/board-w4.html`

## 6. 收口

- [x] 6.1 四档几何未被破坏：跑 `probe.py static`（3.5-1/2/3）与四档实测
      （1440 `280/740/420` · 1280 `248/652/380` · 1024 `232/792/抽屉380` ·
      768 `抽屉300/768/抽屉380`）—— ✅ 全中；A-39 服务字节 == 磁盘字节
- [x] 6.2 图谱页零变化（G-5）：图谱作用域的冻结三处仍在
      —— 中栏 padding `34px 40px 20px` · 两根 `var(--ink-strong)` 分隔线 · h1 `28px`
- [x] 6.3 `pytest tests -q` 全绿 · `compileall` OK · `openspec validate --specs --strict` ·
      `guard extract-problems` PASS
- [x] 6.4 契约同步：`docs/PRODUCT-MANUAL.md`（顶栏与左栏的用户可见说明）·
      `docs/GLOSSARY.md`（新状态词）· `docs/ACTION-GRAPH.md`（若新增动作）
      —— 状态词**不新增**（复用「行动提醒」）；GLOSSARY 与 copy-table §5.1 同步写明；
      PRODUCT-MANUAL 与 ACTION-GRAPH 同步。
- [x] 6.5 交接文档回写（`docs/STATUS-workbench-visual-language-v2-2026-10-23.md` §10）
- [x] 6.6 **不合并 main、不 push**（所有者另行指示）
