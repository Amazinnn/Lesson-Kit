# IMPL-W2h — CSS 补两处：设置视图的行样式 · 全局焦点环对齐权威表

> 来源：组件收口（IMPL-W2g）交工后的复核。**只改 `workbench/server/static/workbench.css` 这一个文件。**
> 两件，都是**缺陷**不是风格挑选。

## 1. 设置视图的行样式 —— **零 CSS，现在渲染是散的**

实测：`grep -c` 在 `workbench.css` 里**全部为 0**，而 markup 在用（`pages.py` 5 处）：

```html
<section class='settings-view' aria-label='外观偏好'>
  <div class='preference-row'>
    <label class='preference-name' for='setting-theme'>主题</label>
    <span class='preference-value' id='setting-theme-value'>暖纸</span>
    <label class='lk-switch'> … </label>
  </div>
  …
</section>
```

⇒ 现在这些行**没有任何布局规则**：标签与值**挤在一行**、开关**跟在后面**、
行与行之间**没有分隔**。

**要做的**：
- `.settings-view` —— 偏好区容器：一条**低调的分区**（不是新卡片；按「少字原则」不加标题、不加说明句）。
- `.preference-row` —— 一行 = **名称（左）· 当前值（中）· 控件（右）**：
  用 flex 布局，名称与控件**两端对齐**，当前值**次级墨**；
  行高与内距按「列表 / 数据面」的密度（**别用阅读面的宽松刻度**）。
  行与行之间用**内发丝线或留白**分隔（**不描边**、不要整条边框）。
- `.preference-name` —— 名称用**界面字族**、正常字重、`--ink-strong`。
- `.preference-value` —— 当前值用 `--ink-muted`（次级信息），**不要**做成强调色。
  ⚠️ 它的内容是**当前值的文字**（如「暖纸」）—— 按 spec 的「少字原则」，
  **不要**额外加解释句。
- 四个偏好项（主题 / 阅读字面 / 动效 / 声音）**排布一致**。

⚠️ **不要动 `.lk-switch`**（W2g 刚做好的，开关自己有形态）——
`.preference-row` 只负责**把它放到该在的位置**。

## 2. 全局 `:focus-visible` 对齐权威表 §8 规则 1

现状（`workbench.css:2145`）：
```css
::focus-visible { outline: 2px solid var(--role-blue); outline-offset: 1px; }
```
而权威表 `night-paper-tokens.md` **§8 规则 1** 要求全局统一用
**`--focus-outer`**（外圈色）与 **`--focus-offset`**（`2px`）。
W2g 已经把 `input` / `textarea` / `select` / `#answer-box` 改成了
`outline: var(--focus-width) solid var(--focus-outer); outline-offset: var(--focus-offset);`
⇒ **现在全局与输入框两套焦点环不一致**（同色 `--role-blue` == `--focus-outer`，
但**偏移 1px vs 2px**）。

⇒ 把全局那条也改成同一套 token：
```css
::focus-visible { outline: var(--focus-width) solid var(--focus-outer); outline-offset: var(--focus-offset); }
```
（`--focus-width` 若未定义，**先在 token 层补上**，取值与现状 `2px` 一致，并登记进权威表。）

⚠️ **两处不许动**（**在图谱区段内**，属冻结范围）：
`.control-toggle:focus-visible` 与 `.legend-item:focus-visible`
（它们用的是图谱自己的硬编码色 `#d3a914`）。
⚠️ **G-5 不受影响**：焦点环**只在聚焦时出现**，而 G-5 的像素比对是**未聚焦**的截图
⇒ 全局偏移 1px→2px **不会**改变图谱页的任何截图像素。**但你要自己验一遍**（见下）。

## 硬约束
- **只改 `workbench.css`**。绝不碰 `pages.py` / `workbench.js` / `practice-flow.js` /
  `paper-practice.js` / `middle-navigation.js` / `records.py` / `agent-ui.css` /
  `tests/` / `docs/` / `openspec/` / `tasks.md`。
- **不要**改 `tasks.md` 的复选框。
- **知识图谱区段与 12 个裸名一行都不许碰**（`grep -n "Knowledge graph V2" workbench.css`）；
  **不要动图谱页冻结块**。
- 现有交互逻辑一个字都不许改。
- 只用现有 token（必要时补 token 到 token 层 + 权威表），**不许硬编码 hex**。
- 动效红线：起始态只写在 `@keyframes` 内；只动 `transform` / `opacity`；状态色瞬切。
- **不许**在设置视图里加任何说明性文字（少字原则）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **走查实测**（运行时 `getComputedStyle` + 截图）：
  - 打开**设置视图**（`/w/<ws>/settings`）⇒ 报四行的 computed 值
    （flex 布局 / 名称左对齐 / 值次级墨 / 控件右对齐 / 行间距 / 分隔方式）+ **截一张图**；
  - **键盘 Tab** 走一遍设置视图与一个输入框 ⇒ 确认**焦点环都是同一套**
    （同色 + **同偏移 2px**），截一张聚焦态图；
  - **鼠标点击**按钮 ⇒ 确认**不冒环**。
- **图谱零差异**：图谱区段**逐字节不变** + **R-2 差异像素 = 0** +
  **图谱页未聚焦截图 AE = 0**（自己 diff 一遍，确认全局焦点环的偏移变化**没有**影响它）。
- 走查按 **A-39**：仓库根 cwd、**独立端口**（**不要 3081 / 3092 / 3099 / 3191 / 3197 / 3177 / 3178 / 3184 / 3411 / 3455 / 3457 / 3460 / 3461 / 3477**）、
  池副本 + `LESSONKIT_WB_HOME` 隔离注册表；**服务字节数与磁盘字节数必须相等**。

## 落盘纪律与回报
- **两个 commit**（设置视图一个、全局焦点环一个），只 `git add workbench/server/static/workbench.css`
  （权威表若补了 token，另 add 那个文件），**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**两件逐条的「改前 → 改后 + 运行时实测值」** +
**设置视图截图路径** + **焦点环统一的证据（键盘聚焦 / 鼠标不冒环）** +
**图谱区段逐字节未变 + 图谱页未聚焦截图 AE = 0** +
四条验证命令结果 + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
