# 交接 — workbench-visual-language-v2

> 生成时间：2026-10-22（因电脑需关机，subagents 被暂停）
> 分支：`feat/workbench-visual-language-v2` —— **未并入 main**
> 仓库根：`D:\Projects\Academic Workflow\lesson-kit`

---

## 1. 状态一句话

合同面（proposal / decisions / acceptance / design / 三份 spec delta / tasks）
与四份职责文档（`docs/`）**已完成并通过 `openspec validate --strict`**；
八份设计件中**三份完整、五份被关机打断在写入中途**（内容大部分已在盘上，见 §4）。

---

## 2. 已完成并提交

| 工件 | 规模 | 备注 |
|---|---|---|
| `proposal.md` | 161 行 | 范围、冻结清单、能力清单 |
| `decisions.md` | 700+ 行 | 17 组 68 问的收口基线 + 两条全局原则 + 追加裁决 A-1…A-5 |
| `acceptance.md` | 160 行 | 底线守卫 G-1…G-8 / 12 张对照截图 / 10 条关键帧 / 7 组交互清单 |
| `design.md` | 1258 行 | D-1…D-15，每条含「决策/理由/否掉的备选/代价」；13 条 Risks；6 条 Open Questions |
| `specs/workbench-ui/spec.md` | 809 行 | 9 ADDED + 9 MODIFIED，84 场景 |
| `specs/workbench-settings/spec.md` | 新能力 | 7 需求 / 25 场景 |
| `specs/calendar-workload/spec.md` | delta | 1 需求 / 14 场景（整块复制后改写） |
| `tasks.md` | 226 行 | 25 组；样板线 1–18 组 / 铺开 19–25 组，第 18.4 条是用户验收关卡 |
| `design-notes/motion-spec.md` | 1266 行 | 20 条 `@keyframes`、19 行交互映射、19 行降级矩阵、42 条出处索引 ✅完整 |
| `design-notes/component-spec.md` | 1981 行 | 28 组件全 8 态规格、42 段无硬编码色值的 CSS ✅完整 |
| `design-notes/night-paper-tokens.md` | 666 行 | 97 个 token、76 行对比度实算、11 项不达标全部修正 ✅完整 |
| `docs/GLOSSARY.md` | +107 | 「柔和蒙德里安 v2」改写 + 12 个新词条 |
| `docs/PRODUCT-MANUAL.md` | +49 | 新增第 10 章「外观与主题」；129-130 硬约束原文保留 |
| `docs/ACTION-GRAPH.md` + `docs/action-graph/L3-actions.md` | +8 / +18 | 登记设置视图与外观偏好两条动作 |
| `docs/ARCHITECTURE.md` | +13 | 仅 §1 静态资产目录与 §4 前端扩展点 |

**验证状态**：`openspec validate workbench-visual-language-v2 --strict` → valid；
`openspec validate --specs --strict` → 19 passed / 0 failed；
`pytest` → 1148 passed；`guard extract-problems` → PASS。

---

## 3. 追加裁决（已写入 `decisions.md`）

| # | 裁决 |
|---|---|
| A-1 | 涟漪扩散时**不压平**卡片，只有底色从灯下扩散 |
| A-2 | 动效偏好：**用户显式设置优先**于系统 `prefers-reduced-motion`（系统仍作默认值） |
| A-3 | 关键反馈音效音色：**清脆木琴 / 玻璃**，各 < 200ms，自制（多邻国 mp3 有版权） |
| A-4 | 「当前」的蓝/黄分工：**交互层=蓝，内容层=黄**；黄色一律不承载文字 |
| A-5 | 自绘控件的**载荷兼容铁律**：自绘下拉必须保留同名 hidden input 承载原 `name`/`value` |

**由 A-2 派生的实现铁律**：`workbench.css:1126-1131` 有全局
`animation: none !important` 兜底 —— **动效的静态样式必须等于终态**，
起始态只能写在 `@keyframes` 内部，否则降级后元素永远停在 `opacity: 0`。

---

## 4. 被关机打断的设计件（**需要收尾**）

下列文件在 agent 写入途中被停止，**末尾句子可能截断**，但主体内容已在盘上。
接手后应「先读盘 → 只补缺口 → 重写整份文件」，不要从头再来。

| 文件 | 当前行数 | 中断位置 | 需要做什么 |
|---|---|---|---|
| `design-notes/asset-spec.md` | 1239 | 结尾停在 §1.7 对比度重算的半句 | 补完 §1.7 之后的章节、5 个导航静物与 ≥8 张器物插画的逐张构图规格、台灯三姿态；补收尾自检节 |
| `design-notes/layout-spec.md` | 1156 | 结尾停在「面板项密度的填充与否（几何已经」 | 补完响应式四档形态、密度分区规则表收尾；核对三栏几何单一真值方案与 `workbench.js:4587` 的改法 |
| `design-notes/copy-table.md` | 1240 | 结尾停在表格中途 | 补完抓取尾段、`删/改/译/留` 四类统计、界面注释专项表收尾、冻结项清单 |
| `design-notes/graph-isolation.md` | 642 | 结尾停在契约冲突说明中途 | 补完禁止改动清单、像素级比对方案、隔离自检清单 |
| `design-notes/walkthrough-harness.md` | 1215 | 结尾停在交互清单对应表中途 | 补完判定与报告、风险与红线、编号对应表收尾 |
| `tasks.md` | 226 行 | 末条任务「知识点页面零改动约束已落到具体…」被截断 | 复核收尾；确认 D-6 的 **parity pytest 任务**、D-5 的 `.wb-reading` 挂载、D-10 的 JS 列宽变量、D-15 的漂移登记文件（任务 25.5）都在 |

> 另注：`docs/PENDING-DEFINITIONS.md` 仍有改动，那是**他人在 2026-10-18 的未提交改动**，
> 不是本轮产物，**不要提交也不要还原**。

---

## 5. 待所有者裁决（尚未拍板）

1. **夜纸下知识图谱页保持浅色，还是跟随夜纸？**
   D-02（`night-paper-tokens.md` §1.2）按「保持浅色」写的值：图谱裸名 token
   （`workbench.css:1505-1518`）与新 token **零同名**，夜纸不重定义，
   图谱路由需把 11 个 token 钉回浅色值。
   选「跟随夜纸」会违反「图谱页观感必须与现在完全一致」的冻结条款，**须另开 change**。
   → 建议维持「保持浅色」。

2. **两份 spec delta 对「动效偏好 vs 系统 reduce」直接矛盾，需在归档前逐字对齐。**
   `workbench-settings/spec.md:143` 写「显式选择优先」，并有场景
   "The learner overrides the system"；`workbench-ui/spec.md:102` 却把
   「系统要求 reduce」与「用户关闭」并列为**无条件**降级触发，没给「开」留出口。
   D-8 已按 A-2 取「显式优先」，但两份 delta 的文字仍需对齐（归档前由 spec owner 处理）。

3. **D-14 的作答日历 5 档强度阈值，任何 delta 都没钉死** —— 需裁决或明确交由实现测得。

---

## 6. 已登记但未裁决（实现期可定）

- **字体子集化的真实代价**（D-4）：审计里「≤600KB / 2 字重」的估算偏乐观 ——
  woff2 CJK 实际约 130–200 字节/字，600KB 只够约 2000–2500 字。
  目标已改写为 **2 字重合计 ≤1.2MB / GB2312 一级字表 3755 字**，
  代价是**教材正文字集不可预知**，超子集的字落到 Songti SC / SimSun，
  同一段内会出现两种字形。体积标注「待核」，超标时先砍字重、不砍字表。
- **D-2**：卡面与暖奶油底只有 1.06:1，卡片边界**完全依赖柔影** ——
  `--wb-shadow-1` 的第一层不能省。
- **D-11**：标题带右下那块 76×8 装饰黄块必须删（与「去掉试卷卡 5px 黄带」同源，
  否则黄色被降级成装订线）。
- **D-6 是本变更唯一一次让既有可见文字变小的地方**（客户端 `#` 从 h1 降到 h2 档），
  验收清单需单列一条。

---

## 7. 下一步

1. **收尾 §4 的六份文件**（先读盘、只补缺口）。
2. **对齐 §5-2 的两份 delta 矛盾**，并补上 §5-3 的日历阈值裁决。
3. 收口后跑：
   ```bash
   openspec validate workbench-visual-language-v2 --strict
   openspec validate --specs --strict
   python -m pytest tests -q
   ```
4. 交所有者审阅交付包；**用户明确说「走 apply」之后**再开实现阶段
   （样板线 = `tasks.md` 第 1–18 组；铺开 = 19–25 组；第 18.4 条是用户验收关卡）。

---

## 8. 复现命令

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
git checkout feat/workbench-visual-language-v2
git log --oneline -12
openspec status --change workbench-visual-language-v2
```

工作台服务（若需要看现状基线）：
```bash
python -m workbench.cli.main daemon start   # http://127.0.0.1:3081/
```
改造前的对照截图在 `tmp/frontend-audit/00-baseline-*.png`（7 张，hub / 练习页 /
知识点列表 / 知识点详情 / 记录中心 / 试卷列表 / 三栏壳层），
与 `acceptance.md` §1 的 S-1…S-12 对应。
