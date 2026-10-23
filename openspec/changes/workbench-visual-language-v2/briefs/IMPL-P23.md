# IMPL-P23 — 第 23 组：试卷列表页改卡片网格

> ✅ **前置核实（2026-10-23，逐处读过 —— 省得你再找）**
>
> | 事实 | 位置 |
> |---|---|
> | 列表容器 = **单列** grid（`display: grid; gap: 18px`）⇒ 23.1 的「改卡片网格」= 把它改成**多列**（如 `repeat(auto-fill, minmax(320px, 1fr))`） | `<section id='practice-set-list' class='practice-set-list'>`（`pages.py:833`）· `.practice-set-list { display: grid; gap: 18px; }`（`workbench.css:2572`） |
> | **5px 黄带就在这里**：`.practice-set-card { padding: 20px 22px; border-top: 5px solid var(--role-yellow); }` ⇒ 23.2 就是删掉这个 `border-top` 并让状态由圆点承载 | `workbench.css:2573` |
> | 卡片 markup：`<article class='practice-set-card card' data-practice-set-id='…'>` 内含 `<details class='practice-set-card-body'>` | `pages.py:792` 起 |
> | 卡内还有逐题条目 `.practice-set-item`（`<details class='practice-set-item-body'>`）—— **顺带可见 §4.27 折叠段的一处** | `pages.py:778-791` |
>
> ⚠️ **状态圆点必须复用已有的 `.lk-dot` 族**（含几何符号），不要另造一套；
> 且 `§4.14` 已把圆点尺寸定到 **10px**（形态见 `component-spec.md` §4.30）。
>
> ⚠️ 状态现在承载在哪：**卡片上没有单独的「状态」文字** ——
> 阻塞原因等由 `.practice-set-continuation-details` / 执行情况承载
> ⇒ **23.2 落地前先确认「用哪个状态驱动圆点」**（`record` 里现成的字段，不要新算）；
> 找不到现成字段就**登记**，不要发明。

> 对应 `tasks.md` **第 23 组（23.1–23.3）**。**只改 `workbench/server/pages.py` 与
> `workbench/server/static/workbench.css`**（两文件是**一组**，别拆给两个 agent）。

## 要做
- **23.1** 试卷列表改**卡片网格**：每张卡显示**标题 / 题数 / 状态圆点**（`practice_sets_page`）。
- **23.2** **去掉试卷卡的 5px 黄带**：现状**每张卡**都顶一条 5px 黄带 ——
  语义黄被降级成装订线，而卡片已带阻塞原因时黄色已无信号价值
  ⇒ 改用**状态圆点**承载状态，**让黄色回到稀缺语义色**。
  验证：那条黄带规则在 CSS 里**消失**；列表中只有「当前 / 到期复习」才出现黄色面积。
- **23.3** 阶段验收：四条验证命令 + `acceptance.md` §1 **S-8** 走查 + 截图（试卷列表页）。

## 硬约束
- **现有交互逻辑一个字都不许改**：请求序列、载荷键、DOM 身份、卡片点击与打开行为一律不动。
- **不许新增请求、零池写入**。
- 知识图谱：`pages.py` 里与图谱相关的函数 / 分支**一行都不许碰**。
- 图谱区段与 12 个裸名**一行都不许碰**（`workbench.css`）。
- 状态圆点复用**已有的** `.lk-dot` 族（含几何符号），**不要**另造一套。
- ⚠️ **空态已经是合规形态**（插画 + 一句 + 满宽主按钮，走查判据 3.4-5 已过）⇒
  **不要动空态的结构**，只让它在网格里排布正常。
- 提交一律 `git commit -- <明确的路径列表>` 限定范围（**不要 `git add -A` / `-a`**）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
```
- 走查：仓库根 cwd、**独立端口**（避开 3081 / 3092 / 3099 / 3191 / 3177 / 3178 / 3184 / 3200 / 3201 / 3281 / 3282 / 3288 / 3411 / 3460 / 3461 / 3462 / 3477 / 3481 / 3482）、
  池副本 + `LESSONKIT_WB_HOME` 隔离注册表；**服务字节数 == 磁盘字节数**。
- 截图：试卷列表页（有卡 + 空态各一张）；实测**卡内三要素齐全**、**黄带消失**、网格成立。

## 落盘纪律与回报
- 两个 commit（markup 一个、样式一个），只 `git add` 那两个路径。
- 回报（中文）必含：已落盘路径 + commit 内容 + **卡片三要素的实测** + **黄带规则消失的证据** +
  **黄带消失前后同页对照截图** + 四条验证命令结果 + 待裁决项。
