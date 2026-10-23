# IMPL-W2i — CSS 收口三：骨架屏有尺寸 · hover/active 反馈 · 动效只动 transform/opacity

> 来源：第 22 组验收关卡跑出的**清单 FAIL**（`3.4-1` · `3.4-2` · `3.4-3` · `3.7-1`）。
> **只改 `workbench/server/static/workbench.css` 这一个文件。**

## 背景（这一轮是「验收关卡判出来的」，不是设计偏好）
第 22 组的走查执行器已经跑完，**G-1…G-8 底线守卫全 PASS**（图谱三口径 R-1/R-2/R-3 全是 0），
但 38 条交互清单里有 4 条 CSS 相关的判成了 FAIL。逐条：

### 1. `3.4-3` 骨架屏**没有尺寸（0×0）** ⇒ 灰块与微光都无从显示（**同时判 M-9 FAIL**）
现状：
```css
.lk-skeleton { position: relative; overflow: hidden; background: var(--skeleton-base); }
.lk-skeleton::after { content: ""; position: absolute; inset: 0; background: linear-gradient(...); }
```
`.lk-skeleton` **没有 width / height / min-height** ⇒ 一个空 div 就是 **0×0** ⇒
**整个骨架屏是看不见的**（微光扫过也因此无从验证）。
⇒ 给它**尺寸**：
- 基类给一个**最小高度**（让空骨架块也有体积）；
- 补 `component-spec.md` 提到的三个变体：`.lk-skeleton--text`（文字行）·
  `.lk-skeleton--block`（块）· `.lk-skeleton--avatar`（头像），
  各自的宽高/圆角按规格给。
- ⚠️ **微光用的是 `linear-gradient`** —— 权威表 §3.3 说渐变只允许出现在图标与插画内部，
  但 **A-74 已裁定「骨架屏的微光（扫描光）」是渐变的明确例外**（它是扫描光，不是表面渐变）。
  ⇒ 保持渐变实现，**但把这条例外写进注释**（免得下一个 agent 又把它当违规删掉）。

### 2. `3.4-1` **4 个 hover 反馈不在 120–180ms**
判据：`:hover` 目标的 `transition-duration` 必须落在 **[120, 180]ms**。
⇒ 把那几处改成 `--dur-fast`（120ms）或 `--dur-base`（160ms）。
⚠️ **不要**用 `transition: all`（本项目禁用）；**逐个属性写**。

### 3. `3.4-2` **没有观察到按下（`:active`）反馈**
判据：`:active` 规则**必须命中**目标元素，且带**可观测的属性变化**
（**悬停已经改过的元素不算** —— 按下要比悬停**再多一层**变化）。
⇒ 给主要可交互元素（按钮 / 选项 / 卡片 / 导航项 / 开关）补 `:active`：
**只动 `transform` / `opacity`**（动效红线）——
例如按下时 `transform: scale(0.98)` 或 `translateY(1px)`。
⚠️ **不要**用 `background-color` 变化做按下反馈（那会撞 `3.7-1`）。

### 4. `3.7-1` **有动效动了 transform / opacity 之外的属性**
判据：枚举全部 `animation` / `transition` 涉及的属性名，出现 `transform`/`opacity` 之外的 ⇒ FAIL。
⇒ 把那些**颜色类过渡**（`background-color` / `color` / `border-color` / `box-shadow` 等）
**改成瞬切**（不写进 `transition`，直接换值），
或者**改用 `transform` / `opacity` 达成同样的视觉**。
⚠️ 权威表 §3.3：**状态色一律瞬切** ⇒ 颜色类过渡本来就该去掉。
⚠️ `box-shadow` 的过渡尤其要清（它是抬升变化的表达，改用 `transform: translateY()` 更符合动效红线）。

## 5. 设置视图的**值列对齐**（A-87）

现状（W2h 落地后）：四行里 **「当前值」那一列的起点不一致** ——
分段控件那行的值偏左约 29px（因为 `.lk-seg` 自身 133px 宽、`.lk-switch` 44px 宽，
而「控件尺寸归 W2g、`.preference-row` 只负责定位」是硬约束）。

⇒ **不要引入固定宽度魔数**（给控件列定死宽度会与两个控件的真实宽度打架）。
**改成 grid 并让值列左对齐**：
```css
.preference-row {
  display: grid;
  grid-template-columns: max-content 1fr auto;   /* 名称 | 值 | 控件 */
  align-items: center;
  gap: 16px;
}
.preference-value { text-align: start; }          /* 由居中改为左对齐 */
```
⇒ 这样**四行的值列起点一致**（名称列用 `max-content`，宽度取四行里最宽的那个），
**控件列右缘一致**（`auto` 列 + 右对齐），而**不引入任何魔数**。
⚠️ 改完实测：四行的 `preference-value` 的 `getBoundingClientRect().x` **完全相同**。

## 硬约束
- **只改 `workbench.css`**。绝不碰 `pages.py` / `workbench.js` / `practice-flow.js` /
  `paper-practice.js` / `middle-navigation.js` / `records.py` / `agent-ui.css` /
  `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **不要**改 `tasks.md` 的复选框。
- **知识图谱区段与 12 个裸名一行都不许碰**（`grep -n "Knowledge graph V2" workbench.css`）；
  **不要动图谱页冻结块**。⚠️ 图谱区段里**也有**颜色类过渡 —— **那些不许动**
  （属冻结范围，动了会破 G-5）。
- 现有交互逻辑一个字都不许改。
- 只用现有 token，**不许硬编码 hex**。
- 动效红线：起始态只写在 `@keyframes` 内；只动 `transform` / `opacity`；状态色瞬切。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **用走查执行器自证**（`tools/walkthrough/` 已就绪，这是本轮最省事的验证）：
  `python tools/walkthrough/run.py --only 3.4-1,3.4-2,3.4-3,3.7-1`（按它的 `--help` 实际用法）
  ⇒ 报告里这 4 条应从 FAIL 变 **PASS**。
  ⚠️ **不许**为了让判据变绿而改**探针**（探针是判据，不是产品）。
- **图谱零差异**：区段**逐字节不变** + R-2 差异像素 0 + 图谱页未聚焦截图 AE = 0。
- 走查按 **A-39**：仓库根 cwd、**独立端口**（**不要 3081 / 3092 / 3099 / 3191 / 3197 / 3177 / 3178 / 3184 / 3411 / 3455 / 3457 / 3460 / 3461 / 3477 / 3281 / 3282**）、
  池副本 + `LESSONKIT_WB_HOME` 隔离注册表；**服务字节数与磁盘字节数必须相等**。

## 落盘纪律与回报
- **一个主题一个 commit**（四件 ⇒ 最多四个），只 `git add workbench/server/static/workbench.css`，
  **不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**四件逐条的「改前 → 改后 + 实测值」** +
**走查执行器重跑后这 4 条的判定（FAIL → PASS）** +
**图谱区段逐字节未变 + R-2 = 0 + 图谱页未聚焦 AE = 0** +
四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
