# Design — workbench-component-forms

> 本文件回答「**怎么落地**」。动机与范围见 `proposal.md`；
> 形态依据 `../workbench-visual-language-v2/design-notes/styleboard-picks.md`
> 与 `component-spec.md` **§4.30**（唯一形态定义）+ §4.7 / §4.16 / §4.24 / §4.25 四节正文
> + §6 可访问性要求；裁决链 `../workbench-visual-language-v2/decisions.md` **A-115**。
> 行为契约见 `specs/workbench-ui/spec.md`（4 条 ADDED / 20 个 Scenario）。
>
> **硬边界（贯穿全文）**
> 1. **不写池、不新增持久字段、不新增学习事实、不改请求契约**——
>    请求的**方法 / 路径 / 载荷键集合逐条不变**（**G-1**）。
> 2. **既有 Tab 顺序不得被打乱**（**G-8**）：自绘下拉与对话框都**不新增** Tab 停靠点。
> 3. **无障碍缺陷不是可选项**：焦点陷阱、焦点归还、键盘可达**必须实现**，
>    不得以「以后再修」为理由降级。
> 4. **尺寸数字是设计默认值、不是硬约束**（A-115.2 / §4.30.2）：
>    唯一不可让步的是**命中区 ≥ 44×44 CSS px** 与**焦点环不被压死**。
> 5. **不写实现细节进 spec**：`specs/workbench-ui/spec.md` 只写**用户可观察的行为**；
>    本文件里的 DOM / 类名 / 取值来源是**实现指引**，不是契约。
> 6. **无框架、无构建步骤、无 npm、无 CDN、无外部图标字体** —— 纯 CSS + 原生 JS + 内联 SVG。
>
> **证据标记**：〔实证〕= 有 `文件:行号` 或可复算的实测数据；
> 〔裁决〕= 所有者或 A-115 已定的；
> 〔推断〕= 由已定决策与实测事实推出、原始裁决未逐字写明；
> 〔待核〕= 需在实现时复核；〔待裁决〕= **需所有者拍板**，本文件给默认口径并登记。

---

## 0. 四条共用的一条腿：先答「焦点去哪」

自绘下拉与对话框都是**会抢焦点**的控件，而 G-8 要求既有 Tab 顺序不变。
这两条不是靠「小心一点」满足的，而是靠**两个结构性约束**满足：

| 约束 | 落法 |
|---|---|
| **不新增 Tab 停靠点** | 自绘下拉的**触发器本身就是唯一的 Tab 停靠点**；面板打开时**焦点不离开触发器**（用 `aria-activedescendant` 指向当前项）。对话框**接管**焦点，但关闭时**归还**。 |
| **焦点有唯一去处** | 每处「焦点离开原处」都必须配一条「焦点回原处」：下拉开→焦点留触发器（无需归还）；对话框开→焦点入面板，**关→归还触发元素**。 |

⇒ **验收时只要录一段 Tab 序列，焦点停靠点数量与顺序必须与改造前一致**（G-8 的可执行判据）。

---

## D-1 · 自绘下拉（§4.7 `select-spec`）

### D-1.1 DOM 形态

```
<div class="lk-select" data-open="false" data-state="idle|disabled|loading|error">
  <button type="button" class="lk-select__trigger"
          role="combobox" aria-expanded="false" aria-controls="{panelId}"
          aria-haspopup="listbox" aria-labelledby="{labelId}">
    <span class="lk-select__value">当前值文本</span>
    <svg class="lk-select__chevron" aria-hidden="true" focusable="false">…</svg>
  </button>
  <input type="hidden" id="{原 id}" name="{原 name}" value="{原 value}">
  <div class="lk-select__panel" id="{panelId}" role="listbox" aria-labelledby="{labelId}" hidden>
    <div class="lk-select__option" role="option" id="{panelId}-opt-0"
         aria-selected="true|false" data-value="…">…</div>
    …
  </div>
</div>
```

**关键的三条结构约定**（〔推断〕，理由如下）：

1. **hidden input 沿用原来的 `id`** —— 〔实证〕7 个控件的值是页面脚本用
   `document.getElementById(id).value` 读的
   （`workbench.js:202 / 1301 / 1318 / 3259 / 4458 / 5183`、`paper-practice.js:32`）。
   ⇒ **id 不变 ⇒ 现有读取代码一行不改**，载荷链不产生漂移。
2. **触发器不沿用原 `id`** —— 一个 id 只能有一个元素。
   ⇒ 触发器用 `{原 id}-trigger`；面板用 `{原 id}-panel`；选项 `{原 id}-opt-{n}`。
3. **原生 `<select>` 在 JS 模式下从 DOM 移除**（不是 `display:none`）——
   〔理由〕留着它就会**多提交一个同名键**（`#goal-kind` 有 `name='kind'`）⇒ **G-1 破**。
   移除后，DOM 里**只有一个**载荷载体。

### D-1.2 状态机

```
        ┌──────────── Esc / Tab / 外点 ────────────┐
        │                                        ▼
   [closed] ──Enter/Space/↓/↑──▶ [open] ──Enter/Space──▶ [closed · 已提交]
        ▲                            │
        └──────── Esc（不改值）───────┘
                                        │
                          loading ──▶ error ──▶ idle
```

| 状态 | 进入条件 | 触发器 | 面板 | 值 |
|---|---|---|---|---|
| `closed`（默认） | 初始 / 关闭后 | 卡面底 + 1px 规则色；箭头朝下 | `hidden` | 不变 |
| `open` | Enter / Space / ↓ / ↑ | 聚焦蓝边 + 蓝洗底光晕；箭头转 180° | 浮起面 + 抬升阴影 | **未提交**（活动项 ≠ 已选项时不改） |
| `selected` | 提交后 | 文字用强墨色 | 关闭 | 面板里**当前项**蓝洗底 + **行尾蓝点** |
| `disabled` | 控件被禁用 | 底色降一档 + 失活墨色 | 不开 | 不变 |
| `loading` | 取值中 | `aria-busy="true"`，箭头位换成指示器 | 不开 | 不变 |
| `error` | 取值失败 | 红边 + 红洗底光晕 | 不开 | 不变 |

**选中项的双通道**（色 + 几何）：蓝洗底 **+ 行尾 8px 蓝实心点**
⇒ 与既有 `Redundant state cues` 一致（状态不得只靠颜色）。

### D-1.3 键盘模型（全部断言-able）

**面板关闭时**（焦点在触发器上）

| 键 | 行为 |
|---|---|
| `Enter` / `Space` | 打开面板，活动项 = **当前已选项** |
| `↓` | 打开面板并把活动项设为**当前已选项** |
| `↑` | 打开面板并把活动项设为**当前已选项**（**不**改成上一项） |
| `Tab` | **正常移到下一个控件**（面板此时是关的）⇒ **G-8 不变** |

**面板打开时**（**焦点仍在触发器上**，用 `aria-activedescendant` 指向活动项）

| 键 | 行为 |
|---|---|
| `↓` / `↑` | 活动项下移 / 上移（**循环**：到底回到头） |
| `Home` / `End` | 活动项跳到第一项 / 最后一项 |
| `Enter` / `Space` | **提交**活动项 → 关闭面板 → 值更新 → 焦点**仍在触发器** |
| `Esc` | **关闭面板，不改值** → 焦点**仍在触发器** |
| `Tab` | 关闭面板、**不改值**、焦点移到下一个控件（**G-8**） |
| 可打印字符 | **首字母跳转**：移到下一个**以该字符开头**的选项（短缓冲，连续输入累加） |

〔待裁决 T-1〕**Tab 是否提交活动项**？本文件取「**不提交**」——
理由：值只应由**显式动作**（Enter/Space）改变；且「不提交」对 G-8 最安全
（Tab 序列与改造前逐字相同）。若所有者取「提交」，改 `specs/workbench-ui/spec.md`
的对应一句 + `tasks.md` 1.6 即可。

### D-1.4 ARIA

| 元素 | 角色 / 属性 |
|---|---|
| 触发器 | `role="combobox"` · `aria-expanded` · `aria-controls="{panelId}"` · `aria-haspopup="listbox"` · 打开时 `aria-activedescendant="{活动项 id}"` |
| 面板 | `role="listbox"` · `aria-labelledby`（指向原有 `<label>` 或 `aria-label`） |
| 选项 | `role="option"` · `aria-selected` · 唯一 `id` |
| 图标 | `aria-hidden="true"` + `focusable="false"` |

〔裁决〕角色组合照 `component-spec.md` §6.2「自绘下拉」行；
`aria-activedescendant`（而非 roving tabindex）是因为
**焦点必须留在触发器上**才能满足 G-8（roving tabindex 会把面板项塞进 Tab 序列）。

### D-1.5 取值来源与载荷（**G-1 红线**）

| 控件 | 原生形态 | 值怎么来 | 载荷键 |
|---|---|---|---|
| `#chapter-lens-select` | `<select>`（**无 name**） | 隐藏域 `.value` → 页面脚本读它 → 触发既有 `applyChapter` | **无表单键**（JS 驱动） |
| `#paper-reveal-timing` | `<select>`（无 name） | 同上 | 无 |
| `#goal-kind` | `<select name='kind'>` | 同上 | **`kind`**（键名与值都不变） |
| `#knowledge-sort` | `<select>`（无 name） | 同上 | 无 |
| `#workspace-select` | `<select>`（无 name） | 同上 | 无 |
| `#setting-running-send` | `<select>`（无 name） | 同上 | 无 |
| `#ai-model-switch` | `<select>`（无 name） | 同上 | 无 |
| `#ai-send-action` | `<select>`（无 name） | 同上 | 无 |

⇒ **提交出去的载荷键集合 = 改造前**（只有 `kind` 一个键）；
⇒ **每个控件触发的请求的方法 / 路径 / 载荷逐条不变**（G-1）。

### D-1.6 降级（无脚本 / 窄屏 / 打印）

〔裁决 A-115.5〕「原生 `<select>` 在窄屏与打印下要有回落」。
〔待裁决 T-2〕**回落具体指哪一种**？本文件给三档口径：

| 情形 | 本文件的默认口径 |
|---|---|
| **无脚本** | 原生 `<select>` 原样呈现（服务端渲染时它就在那儿）⇒ 选项集合与值与改造前完全一致 |
| **窄屏** | 面板**不浮起**，改为**贴触发器的全宽面板**（不裁切、不横向溢出）⇒ 仍是自绘控件 |
| **打印** | 只打印**触发器当前值文本**，不打印打开的面板；隐藏域不打印但**照样提交** |

〔待裁决 T-2 的三个选项〕**(a)** 只要求「无脚本回落」；
**(b)** 无脚本 + 窄屏都用原生控件；**(c)** 三档全都要（本文件的默认）。
⇒ 本 change 的 spec 只写**可断言的那一档**：**无脚本时给出同样的选项、报同样的值**；
窄屏与打印的具体形态属实现层，登记在 `tasks.md` 第 1 组。

### D-1.7 失败态

| 失败 | 表现 |
|---|---|
| 取值失败（异步加载选项） | 触发器转 `error`（红边 + 红洗底光晕）+ `aria-invalid="true"`；**值不变**；面板不开 |
| 选项为空 | 面板显示一条「暂无可选项」文案（不是空白面板） |
| 脚本异常 | **降级回原生 `<select>`**（把原生 select 放回 DOM 并去掉隐藏域）⇒ 页面**不会因为下拉坏掉而不可用** |

### D-1.8 已存在的一段先例：章节透镜的自绘面板**必须被统一**

〔实证〕`workbench/server/static/workbench.js:74-190` + `pages.py:207-213` + `workbench.css:613-660`
已经有一段**自绘章节面板**（`.chapter-lens-panel` · `role="listbox"` · `.chapter-lens-option` · `role="option"`）。
它是本仓库里**同一个组件的第二套实现**，与 D-1 的口径**有三处不一致**：

| 维度 | 现有章节面板 | D-1 口径 |
|---|---|---|
| 焦点 | 打开时**焦点进面板**（`target.focus()`，`workbench.js:110`）；选项是真 `<button>` ⇒ **可聚焦、进 Tab 序列** | **焦点留在触发器**（`aria-activedescendant`）⇒ **不新增 Tab 停靠点**（G-8） |
| 归还对象 | 关闭后焦点回到**开关**（`workbench.js:117` 的 `toggle.focus()`） | 关闭后焦点回到**触发器** |
| 值载体 | **原生 `<select>` 留在 DOM**（`workbench.js:124` 写回 `select.value`） | 载荷由**隐藏域**承载；原生 select 在 JS 模式下**不在 DOM** |

⇒ **必须把这段面板并进统一的 `.lk-select`**，否则仓库里会留下
「同一个组件两套实现」——正是本轮要消灭的那类病。
（`component-spec.md` §5.2 已经写明 `#chapter-lens-select` 要替换为 `.lk-select`。）

〔待裁决 T-9〕**章节透镜的「章」开关（`#chapter-lens-switch`）与新的下拉触发器怎么摆？**
本文件取：**开关保留**（它承载透镜的开 / 关语义，`workbench-ui`「Chapter switch in the top bar」
明令「off state means the whole course」）· **下拉触发器独立**（选章）；
现有「点开关开面板」的手感**并入**下拉触发器的正常开合路径。

---

## D-2 · 分段进度条（§4.16 `steps-num`）

### D-2.1 DOM 形态

```
<div class="lk-steps" role="progressbar" aria-valuemin="0" aria-valuemax="{总数}"
     aria-valuenow="{已完成}" aria-label="{进度名}">
  <span class="lk-steps__dot" data-state="done|current|todo|failed" aria-hidden="true">
    <span class="lk-steps__num">1</span>
  </span>
  <span class="lk-steps__link" aria-hidden="true"></span>
  …
</div>
```

〔裁决〕形态 = **编号圆点 + 连接线**（`steps-num`）。
〔裁决 §4.16〕**编号是组件的核心** ⇒ 圆点里放**步骤序号**，
连接线只是把点串起来（点本身带序号 ⇒ 「第几轮」一眼可数）。

**几何与颜色的分工**（〔裁决 §6.2 / §3.6〕状态不得只靠颜色）：

| 状态 | 几何 | 颜色 |
|---|---|---|
| 已完成 | **实心**圆点 | 蓝（通用语义）或黄（连对语义） |
| 当前 | **半填**圆点 | 中性底 + 半边角色色 |
| 未开始 | **空心环** | 规则色 |
| 失败 | **实心**圆点 + 叉 | 红 |

⇒ 四态**几何各不相同** ⇒ 不依赖颜色也能分辨（`Redundant state cues`）。

### D-2.2 段数上限与溢出形态

〔裁决 §4.30.1 明列「段数上限、溢出时的形态」必须写清〕

| 项 | 口径 |
|---|---|
| 上限 | **可调参数**，默认 **7 个编号点**（编号点要能放下两位数才不至于挤 ⇒ 7 步以内最稳） |
| 溢出 | **折叠为紧凑摘要**：「已完成 n / 共 m」文本 + 一条胶囊进度带（**不是**把点挤成一条线） |
| 折叠后 | 仍**不得只靠颜色** ⇒ 摘要里带**数字**（数字就是几何通道） |
| 折叠触发 | 由**宿主**决定（宿主知道总数）；组件本身只提供两种形态 |

〔待裁决 T-3〕**上限取 7 是否合适**？本文件取 7（理由：编号点串在 44px 命中区约束下
能舒展放数字的步数有限，且连对的两个档位是 5 与 10 —— 7 恰好把「第一档」完整显示、
「第二档」交给摘要）。若所有者取 5 或 10，改 `design.md` 与 `tasks.md` 的常量即可，
**spec 不受影响**（spec 只写「折叠为紧凑摘要」这个可观察行为）。

### D-2.3 是否可点

〔裁决 §4.30.1：「是否可点（可点就要新行为）」〕

**本文件取「不可点」**：它是**显示**，不是控件。

| 判据 | 结论 |
|---|---|
| 进 Tab 序列吗 | **不进**（`role="progressbar"` 是静态角色） |
| 能激活吗 | **不能**（无 `tabindex`、无按钮语义） |
| 会发请求吗 | **不会** |
| 会改任何值吗 | **不会** |

〔待裁决 T-4〕**若所有者要它可点**（比如点第 n 步跳到第 n 轮），
则**必须新增一条可观察行为**（「点击第 n 步 ⇒ 跳到第 n 轮」），
而那属于**另一个需求**，应当**另开 change 或在本 change 追加一条 ADDED** ——
**不许**在本 change 的实现阶段悄悄加上。

### D-2.4 取值来源

| 项 | 口径 |
|---|---|
| 完成步数 | **宿主已有的值**（例如连对计数器的当前连对数） |
| 总步数 | **宿主已有的值**（例如该轮的步数上限） |
| 新统计 | **无** ⇒ 不写池、不新增统计行、不引入比率或分数 |
| 失败步 | 宿主已有的失败事实（连对中断） |

〔协调〕宿主第一站是**连对计数器的进度指示器** ——
v2 待归档 delta 的 `Consecutive-correct escalation feedback` 说它是
「逐簇点亮的指示器」；本条把它**定形**为编号点串。
⇒ **归档顺序**：v2 先归档，本 change 在其之上补形态；两处措辞需一致（登记在 proposal 的协调点）。

### D-2.5 降级

reduced-motion 下**直接呈现终态**（已完成的就是实心的、当前的就是半填的），
不逐个点亮 ⇒ 终态与开启动效时**逐字相同**（沿用 v2 `Motion system and reduced-motion downgrade`
的「终态铁律」）。

---

## D-3 · 对话框（§4.24 `dialog-spec`）

### D-3.1 DOM 形态

```
<div class="lk-dialog-backdrop" data-open="true">
  <div class="lk-dialog" role="dialog" aria-modal="true" aria-labelledby="{titleId}">
    <h2 class="lk-dialog__title" id="{titleId}">标题</h2>
    <div class="lk-dialog__body">…</div>
    <p class="lk-dialog__error" role="alert" hidden>…</p>
    <div class="lk-dialog__actions">
      <button type="button" class="lk-dialog__action" data-role="cancel">取消</button>
      <button type="button" class="lk-dialog__action primary" data-role="confirm">确认</button>
    </div>
  </div>
</div>
```

**遮罩是面纱、不是纸面**（〔裁决 §4.24〕）：半透明落在**背景色自身**上，
不用容器的 `opacity`（否则面板一起变半透明）；**不用 backdrop-filter 模糊**（禁玻璃拟态）。

### D-3.2 状态机

```
[无对话框] ──触发──▶ [open · 焦点在面板内]
   ▲                     │
   │                     ├─ 取消 / Esc ──▶ [closing] ──▶ [无对话框 · 焦点已归还]
   │                     ├─ 遮罩点击 ──▶ （无变化）
   │                     ├─ 确认 ──▶ [busy] ──成功──▶ [closing]
   │                     │                └──失败──▶ [open · error 就地报告]
   └─────────────────────┘
```

| 状态 | 表现 |
|---|---|
| `open` | 遮罩 + 面板；焦点在面板内**第一个可聚焦元素** |
| `busy` | 面板**不关**；`aria-busy="true"`；确认按钮切 loading 态（禁用） |
| `error` | 面板**不关**；顶部行内错误条（红点 + 文字）；焦点**留在面板内** |
| `closing` | 面板退场；**焦点归还**给触发元素 |

### D-3.3 焦点模型（**本条是 4.24 的核心**）

| 时机 | 焦点去哪 |
|---|---|
| 打开 | 面板内**第一个可聚焦元素**，**默认是「取消」**（〔裁决 §4.24〕：默认「取消」⇒ 误按 Enter 不会执行破坏性动作） |
| 打开时面板内无可聚焦元素 | 焦点落在**面板容器**上（容器 `tabindex="-1"`） |
| `Tab` / `Shift+Tab` | **在面板内循环**（到最后一项 `Tab` 回第一项；`Shift+Tab` 到第一项回最后一项）—— **焦点陷阱** |
| 关闭（取消 / Esc / 成功） | **归还给触发元素** |
| 关闭时触发元素已从 DOM 消失 | 归还给它**所在区域**（最近的仍在的祖先容器，`tabindex="-1"`）；**不得**留在 `body` 上 |
| 打开期间 | 面板**之外**的内容 `inert`（指针与辅助技术都够不着） |

〔裁决 §6.2「对话框」行〕`role="dialog"` + `aria-modal="true"` + `aria-labelledby` + 背景 `inert`。
〔裁决 §6.1 A-9〕**只有**对话框接管焦点；吐司 / 骨架屏 / 浮层出现**不抢焦点**。

### D-3.4 遮罩点击是否关闭

〔裁决 §4.30.1 明列「遮罩点击是否关闭」必须写清〕

**本文件取「遮罩点击不关闭」**：关闭必须是**显式动作**（面板内按钮或 `Esc`）。

| 理由 | 说明 |
|---|---|
| 误触 | 遮罩面积远大于面板，误触概率高；对「删除试卷」「整批回滚」这类动作，误关 = 意外放行 |
| 与 Esc 一致 | `Esc` 是**显式**取消；遮罩点击是**位置性**输入 |
| 可断言 | 「点遮罩 ⇒ 面板还在、焦点还在面板内」是一个可自动判的验收项 |

〔待裁决 T-5〕**若所有者要遮罩可点关闭**（对非破坏性对话框友好），
则需要**分级规则**（「破坏性对话框遮罩不可关 / 非破坏性可关」）——
那会让「遮罩点击是否关闭」从一条规则变成一条**按类型分叉**的规则，
spec 与验收都要多写一条分支。**本文件默认不关闭**，等拍板。

### D-3.5 哪些确认改用它

| 原生确认 | 位置 | 语义 | 改用对话框 |
|---|---|---|---|
| 删除做题经验 | `kp-experience.js:149` | 轻（不动学习记录） | ✅ |
| 删除试卷 | `workbench.js:3162` | 轻（做题记录保留） | ✅ |
| 放弃未完成练习 / 开始新练习 | `practice-flow.js:1333`、`workbench.js:3201` | 中 | ✅ |
| 删除目标 | `workbench.js:3282` | 中 | ✅ |
| 整批回滚 | `workbench.js:5026` | 重（从池里删内容） | ✅ |
| 删除本地 Agent 会话 | `workbench.js:5543` | 中 | ✅ |
| **Agent 内联确认卡** | `agent-ui.js:351` | Agent 审批门 | ❌ **保持内联** |

〔裁决〕**Agent 的审批门不改成模态**：
审批门是**对话流里的一张卡**（`Approval Gate` / `ai-teacher-bridge` 契约管），
它不是「打断」——它就住在对话流里、等着用户回应。
把它提成模态会改写 Agent 契约的可观察行为，属**越界**。

〔待裁决 T-6〕**是否也要把 Agent 审批门提为模态**？本文件取「不要」。

### D-3.6 载荷与时序（**G-1 红线**）

| 阶段 | 请求 |
|---|---|
| 打开对话框 | **不发任何请求** |
| 取消 / Esc / 遮罩点击 | **不发任何请求** |
| 确认 | **发与原生 confirm 之前完全相同的那一个请求**（方法 / 路径 / 载荷键集合逐条相同） |

⇒ 对话框只把**「确认」这一步的 UI**换掉了，**没有新增或提前任何请求**。

### D-3.7 降级

reduced-motion 下**直接出现终态**（遮罩 + 面板已在位），不做上浮淡入；
进入与退出的终态与开启动效时**逐字相同**。

---

## D-4 · 工具调用卡（§4.25 `tool-line`）

### D-4.1 DOM 形态

```
<article class="lk-tool" data-state="running|done|failed|blocked">
  <button type="button" class="lk-tool__head" aria-expanded="false" aria-controls="{detailId}">
    <span class="lk-tool__dot" data-shape="half|filled|cross|ring" aria-hidden="true"></span>
    <span class="lk-tool__name">工具名</span>
    <span class="lk-tool__cost">0.4s</span>
    <svg class="lk-tool__chevron" aria-hidden="true" focusable="false">…</svg>
  </button>
  <p class="lk-tool__summary">≤240 字摘要（不展开即可读）</p>
  <div class="lk-tool__detail" id="{detailId}" role="region" aria-labelledby="{headId}" hidden>
    <pre class="lk-tool__payload">参数 / 结果</pre>
  </div>
</article>
```

**头行是一行**（〔裁决〕`tool-line`：一行摘要）**；摘要行独立一行、默认可见**；
**折叠的是 payload 区**（〔裁决 §4.25〕「折叠时只给 ≤240 字摘要」）。

⚠️ **注意与既有契约的相容性**：既有
`Failed activities expose a concise error summary` 要求「失败摘要**不展开即可读**」
⇒ **摘要行必须在折叠态就可见**（不能把摘要也塞进展开区）。
这就是「一行摘要」的准确含义：**头一行 + 摘要一行**，不是「只有一行」。

### D-4.2 展开 / 收起的键盘路径

| 键 | 行为 |
|---|---|
| `Tab` | 焦点到头行按钮（**一个停靠点**） |
| `Enter` / `Space` | 展开 / 收起；`aria-expanded` 同步翻转 |
| `Esc` | 不做特殊处理（不是浮层，不需要） |

〔裁决 §6.2「工具调用卡」行〕头是 `<button aria-expanded aria-controls>`，
内容区 `role="region"` + `aria-labelledby`（**由头行按钮的可访问名承担**）。

⚠️ **现状差距**（〔实证〕）：现在是原生 `<details>/<summary>`
（`workbench.js:4648` / `:4716`）⇒ **没有 `aria-expanded`**。
⇒ 本条是**真实的新增行为**（可断言的 ARIA 契约），不是纯外观。

### D-4.3 取值来源

| 字段 | 来源 | 没有证据时 |
|---|---|---|
| 工具名 / 动作名 | 活动自报的**语义动作名**（既有契约：语义动作卡） | 不显示（不臆造） |
| 状态 | 活动自报的**真实状态**（running / done / failed / blocked） | 不推断 |
| **耗时** | 活动**自报的时长** | **不显示耗时这一格**（〔裁决 §4.30.1 明列「工具名 + 耗时」的取值来源必须写清〕） |
| 结果 / 影响 | 活动或后端**可验证的证据** | **如实标为「未知」**（既有契约，不得推断成功） |
| 摘要 | 净化后的诊断，**≤240 字** | 空输出 ⇒ **明确的通用失败文案**（既有契约） |

⚠️ **不得**为「凑出一行」而自造耗时、进度百分比或速度。
⚠️ **不得**用红字表达失败 —— 失败由**状态点**承担（〔裁决 §4.25 error 行〕）。

### D-4.4 状态与几何

| 状态 | 状态点 | 摘要位 |
|---|---|---|
| `running` | 蓝 · **半填** | 两行骨架屏（呼吸式，**不是**横扫 —— v2 已裁定） |
| `done` | 实心（蓝或黄） | 正常摘要 |
| `failed` | 红 · **实心** | ≤240 字摘要，末尾省略号，**不加红字** |
| `blocked` | 红 · **叉** | 正常摘要 |

### D-4.5 与既有形态的关系

现状有两套：

| 现状类 | 出处 | 处置 |
|---|---|---|
| `.ai-plan-step`（Codex / Claude 的执行计划行） | `workbench.css:1791`、`workbench.js:4638` | 换成工具调用卡形态 |
| `.ai-activity`（Pi 的活动行） | `workbench.css:1850`、`workbench.js:4705` | 换成工具调用卡形态 |
| `.ai-plan-output`（折叠输出） | `workbench.css:1833` | 并入工具调用卡的 `detail` 区 |

**不动的契约**（`workbench-ui` 现值）：
`Provider activity cards show evidenced outcomes`（`:1384`）·
`Failed activities expose a concise error summary`（`:922`）·
`Pi activities are conversation messages`（`:853`，**按活动 id 原地更新、不产生重复行**）·
`Execution Plan` 作为**时间线**的定位。

### D-4.6 降级

reduced-motion 下 running 态**直接是最终样子**（骨架屏照常，但**不呼吸**）；
展开 / 收起**直切**（不做高度动画）⇒ 终态与开启动效时逐字相同。

---

## D-5 · 四条的公共实现约定

| 约定 | 理由 |
|---|---|
| **一套命中区补偿**：所有新增控件的命中区 ≥ 44×44 CSS px，视觉尺寸可小于它 | A-115.2：数字不是定死的，**命中区是硬约束** |
| **一套焦点环**：不写 `outline: none`；浮层内的焦点环不得被 `overflow: hidden` 裁掉 | 既有 `Focus visibility and contrast floors` |
| **一套 reduced-motion 降级**：终态直切 | 既有 `Motion system and reduced-motion downgrade` 的终态铁律 |
| **一套图标**：内联 SVG + `aria-hidden="true"` + `focusable="false"` | 既有 §6.3 |
| **装饰层 `pointer-events: none`** | 既有 A-10 / G-7 |
| **零新增请求、零新增持久字段、零新增学习事实** | G-1 / G-6 |

---

## D-6 · 术语登记（待落 `docs/GLOSSARY.md`）

> ⚠️ `docs/GLOSSARY.md` **正被另一波写** ⇒ 本 change **不碰它**；
> 下列词条由主会话统一落。
> **已经存在、直接复用的**（不在此列表）：
> 柔和蒙德里安 v2 · 纸面层级 · 沉底面 · 夜纸 · 冗余状态通道 · 焦点环 ·
> 命中区（散见 §3.1 / 既有词条）· 动效偏好 · 少字原则 ·
> 执行计划 · 工具调用卡 · Agent 对话栏 · 审批门 · 走查。

| # | 词条（中 / 英） | 定义（一句话） | 出处 |
|---|---|---|---|
| 1 | **自绘下拉 / Custom select** | 从一组互斥选项里选一个的**自绘控件**：一个显示当前值的触发器 + 一个浮在页面上的选项面板；触发器是 `combobox`、面板是 `listbox`；面板打开时焦点**留在触发器**上，关闭后焦点也**回到触发器**；它占**一个** Tab 停靠点，**不新增**停靠点。 | `workbench-component-forms`（specs/workbench-ui/spec.md「Custom select replaces the native select」；design-notes/component-spec.md §4.7 / §6.2） |
| 2 | **载荷承载域 / Payload-carrying field** | 表单里**承载提交值的那一个字段**。自绘下拉替换原生控件后，它由一个**隐藏域**担任，并**保留原来的字段名与原来的选项值** ⇒ 请求的方法 / 路径 / 载荷键集合逐条不变。 | 同上（「载荷仍由 hidden input 承载」；G-1） |
| 3 | **焦点陷阱 / Focus trap** | 模态对话框打开期间，`Tab` 与 `Shift+Tab` **只在对话框内部**移动焦点，**到不了**背后的页面。 | 同上（「Modal dialog interrupts and owns focus」；component-spec.md §4.24 / §6.2） |
| 4 | **焦点归还 / Focus return** | 模态关闭后，焦点**回到打开它的那个元素**；该元素若已不在，落到它**所在的区域**，且**不得**留在文档 `body` 上。 | 同上 |
| 5 | **编号点串 / Numbered step rail** | 离散步数的完成度形态：**编号圆点 + 连接线**，圆点里放步骤序号；四态（已完成 / 当前 / 未开始 / 失败）**几何各不相同**，不靠颜色单独承载。 | 同上（「Segmented progress shows numbered steps」；component-spec.md §4.16 / §4.30） |
| 6 | **工具调用卡（单行形态）/ Tool call card (single-line form)** | 工具调用卡的一种形态：**头一行**（状态点 + 工具名 + 耗时 + 展开按钮）+ **摘要一行**（≤240 字，不展开即可读）+ **默认收起的详情区**。耗时**只取活动自报值**，没有就不显示。 | 同上（「Tool call card is one line」；component-spec.md §4.25） |
| 7 | **模态对话框 / Modal dialog** | 需要**打断**用户的确认界面：暖墨面纱遮罩 + 浮起面板 + 右对齐动作区；它是**唯一**接管焦点的界面（吐司 / 骨架屏不接管）。 | 同上；component-spec.md §4.24 / §6.1 A-9 |

---

## D-7 · 待裁决项（**不自行拍板**）

| # | 问题 | 本文件的默认口径 | 若拍板相反，影响面 |
|---|---|---|---|
| **T-1** | 自绘下拉**打开时按 `Tab`**：提交活动项，还是不改值直接离开？ | **不改值**（值只由 Enter/Space 改） | spec 的一句 + `tasks.md` 1.6 |
| **T-2** | §4.7 的「窄屏与打印回落」到底指哪几档？ | **三档都要**：无脚本 → 原生 select；窄屏 → 贴边全宽面板；打印 → 只印当前值 | spec 只写了「无脚本」这一档；窄屏 / 打印属实现层 |
| **T-3** | 分段进度条的**编号点上限**取几个？ | **7**（上限可调；溢出折叠为摘要） | spec 不受影响；只改常量与截图基准 |
| **T-4** | 分段进度条**要不要可点**（点第 n 步跳第 n 轮）？ | **不可点**（纯显示） | 若要可点 ⇒ **必须另加一条可观察行为**（新需求），不能悄悄加 |
| **T-5** | 对话框**遮罩点击**是否关闭？ | **不关闭**（关闭须显式动作） | spec 的一句 + 验收项 A-D4 |
| **T-6** | Agent 的**内联审批卡**要不要也提成模态？ | **不提升**（越界改 Agent 契约） | 若要 ⇒ 需另开 change（涉及 `ai-teacher-bridge`） |
| **T-7** | 分段进度条的**第一个宿主**是否就是连对计数器的进度指示器？ | **是**（v2 的「逐簇点亮的指示器」被本条定形） | 若是别的宿主 ⇒ `design.md` D-2.4 与归档时的措辞协调要改 |
| **T-8** | 「工具名 + 耗时」里的**耗时**若活动没自报，**是否显示占位**（如 `—`）？ | **整格不显示**（不臆造） | 只影响一格 |
| **T-9** | 章节透镜的**「章」开关**与新的下拉触发器怎么摆？现有的「点开关开面板」手感要不要保留？ | 开关保留（承载透镜开/关）+ 下拉触发器独立；手感并入触发器的正常开合 | 影响 D-1.8 的统一方式与 `tasks.md` 2.9 |

---

## D-8 · 实现期不可越界的清单（与 `acceptance.md` §0 对齐）

1. **不新增请求、不改请求的方法 / 路径 / 载荷键集合**（G-1）。
2. **不写池、不新增持久字段、不新增学习事实、不新增统计行**（G-6）。
3. **既有 Tab 停靠点数量与顺序不变**（G-8）。
4. **既有需求逐字继续成立**：`Provider activity cards show evidenced outcomes` ·
   `Failed activities expose a concise error summary` ·
   `Pi activities are conversation messages` · `Chapter switch in the top bar` ·
   `Focus visibility and contrast floors` · `Complete primary learning text`。
5. **Agent 契约不动**：`ai-teacher-bridge` 的活动事件与审批门语义。
6. **图谱不动**：知识图谱页不在本 change 范围内。
7. **另两个 change 的目录不动**：`workbench-visual-language-v2/` ·
   `graph-node-visual-language/`。
