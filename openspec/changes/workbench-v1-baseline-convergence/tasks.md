# 任务清单 —— V1 基线收敛

> 靶子：`openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html`
> 工具：`tools/walkthrough/view.py`（三列对照板）、`tools/walkthrough/probe.py`（响应式与抽屉判据）
>
> ⚠️ **每完成一项就出一次对照板**（靶子 | 改前 | 改后），给所有者看。
> ⚠️ **同文件串行**：`workbench.css` / `workbench.js` / `pages.py` 一波只碰一个文件的**同一段**。

## 1. 开工前（必做，不写码）

- [ ] 1.1 读 `design.md` 的 D-1…D-4 与两个 Open Questions；**搜索通路与状态词表两项要先定**
      （未定就停，不要在产品里试词）
- [ ] 1.2 读 V1 拼版：`design-notes/mockup-baseline/v1.html`（对照页）
- [ ] 1.3 起隔离走查服务（`tools/walkthrough/launch.py`，**避开禁用端口**，用 `tmp/` 下的独立
      scratch + 池副本 + `LESSONKIT_WB_HOME`），抓一份「改前」基线图
- [ ] 1.4 跑一遍 `pytest tests -q` 确认起点是绿的

## 2. 顶栏动作区（§2.2 · DRIFT-2）

- [ ] 2.1 在 `docs/GLOSSARY.md` 落新状态词的**契约词面**（若第 1 组未定词表，先做其余三项）
- [ ] 2.2 `pages.py`：把 `#workspace-select` **搬进顶栏段二**（**id 不变** ⇒ JS 绑定与测试照旧）
- [ ] 2.3 `pages.py`：段三放四个控件 —— Agent 对话开关 · 主题开关 · 对话视图开关 · 搜索
- [ ] 2.4 `workbench.css`：四个控件按 V1 的形态（34×34 卡面 / 圆角 12px / 18px 图形）
- [ ] 2.5 `workbench.js`：Agent 开关接 `data-ai-collapsed`（桌面端折叠右栏）；
      主题开关接 `saveSetting("theme", …)`；对话视图开关接既有 rail 视图切换 —— **不新增机制**
- [ ] 2.6 键盘可达 + 焦点环 + 可访问名（`acceptance.md` 的 G-7/G-8 口径）
- [ ] 2.7 出对照板；跑 `probe.py static`（3.5-1/2/3 仍须 PASS）

## 3. 右栏会话分组（§6.1）

- [ ] 3.1 在**客户端**按会话时间戳分桶（今天 / 昨天 / 更早）—— 不加后端端点
- [ ] 3.2 组标题只写recency措辞，**不带任何计数/统计**
- [ ] 3.3 分组不影响滚动容器（`#ai-session-list` 自滚）与消息流
- [ ] 3.4 出对照板；`probe.py static` 复核

## 4. 优先回看状态点（§6 状态几何）

- [ ] 4.1 从 `weak.score_all()` 的理由**类别**映射到三个状态（到期复习 / 阻塞 / 未开始）
- [ ] 4.2 复用既有 `.status-dot` 家族的 10px 盒与几何（filled / dash / cross / ring）—— **不新画**
- [ ] 4.3 条目形态按 V1：卡面 + 柔影 + 12px 圆角 + 8/12 内距 + 状态点在前
- [ ] 4.4 出对照板

## 5. 左栏分组结构（§3.1/§3.2）

- [ ] 5.1 首组名改「学习」，容纳五个学习入口（练习 / 试卷 / 知识点 / 图谱 / 记录）
- [ ] 5.2 设置组、优先回看组按 V1 的分组与间距
- [ ] 5.3 出对照板

## 6. 收口

- [ ] 6.1 四档几何未被破坏：跑 `probe.py static`（3.5-1/2/3）与四档实测
      （`tmp/wave1b/measure.py` 那套：1440 `280/740/420` · 1280 `248/652/380` ·
      1024 `232/792/抽屉380` · 768 `抽屉300/768/抽屉380`）
- [ ] 6.2 图谱页零变化（G-5）：图谱作用域的冻结三处仍在
- [ ] 6.3 `pytest tests -q` 全绿 · `compileall` OK · `openspec validate --specs --strict` ·
      `guard extract-problems` PASS
- [ ] 6.4 契约同步：`docs/PRODUCT-MANUAL.md`（顶栏与左栏的用户可见说明）·
      `docs/GLOSSARY.md`（新状态词）· `docs/ACTION-GRAPH.md`（若新增动作）
- [ ] 6.5 交接文档回写（`docs/STATUS-workbench-visual-language-v2-2026-10-23.md`）
- [ ] 6.6 **不合并 main、不 push**（所有者另行指示）
