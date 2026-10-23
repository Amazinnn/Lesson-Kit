# IMPL-F1b — 组件样式一览（新版）：清单对齐 + 并排变体板

> 所有者原话：「每一界面都自己提供了同一组件的超多样式，之后可以做一个组件样式一览，
> 让我来选出我最喜欢的样式~」
> 对应 `decisions.md` **F-1**（组件样式一览）。
> ⚠️ `briefs/IMPL-F1.md` 是**另一个东西**（第一波的 CSS 地基任务书）—— 不要改它。
> **这是评审件，不是产品代码。**

## 目标（两件事，按顺序）

### 第一件：清单对齐（**先做，它是第二件的前提**）
`design-notes/component-spec.md` §4 定义了 **28 个组件**（§4.1–§4.28），
但**实现里的类名是另一套** —— 例如 spec 写「主按钮」，产品里是 `.primary`；
spec 写「分段控件」，产品里是 `.seg` / `.chip`；spec 写「卡片」，产品里同时有
`.card` 与 `.lk-card`。

⇒ 产出一份**一一对应的对照表**，每行：

| 列 | 内容 |
|---|---|
| spec 组件 | §4.N 的名字 |
| spec 给的类名 | 原样抄 |
| **产品里的真实类名** | 从 `workbench.css` / `pages.py` / `*.js` 里**实测**出来的 |
| 状态 | ✅ 有独立形态 / ⚠️ 存在但**没有专属样式**（用的是原生控件或别的组件） / ❌ **产品里根本没有这个界面** |
| 备注 | 命名分歧的原因、你建议怎么收敛 |

**实测方法**（不许凭 spec 猜）：
`grep -n "<类名>" workbench/server/static/workbench.css` ·
`grep -rn "class='[^']*<类名>" workbench/server/pages.py` ·
`grep -rn "<类名>" workbench/server/static/*.js`

**已知需要核实的几个**（我粗查的结果，**以你实测为准**）：
复选框 / 单选 / 对话框 / 时间线节点 / 折叠段 —— 在 CSS 里**没找到专属规则**，
要确认它们到底是「用原生控件」还是「产品里压根没有这个界面」。

**写到哪里**：新建
`openspec/changes/workbench-visual-language-v2/component-inventory.md`（**只新建，不改
`component-spec.md`** —— 它是设计权威文件，改动由主会话统一做）。

### 第二件：样式板（**要能真看、真选**）
**旧的样式板不能用**：`tmp/frontend-audit/styleboard/index.html` 是**仿古方向**做的
（F-1 里已写明不适用）⇒ **重做**，输出到
`tmp/frontend-audit/styleboard-v2/index.html`（`tmp/` 被 gitignore ⇒ 不入库，它是评审件）。

**硬要求**：

1. **必须用真实的 token 层**：`<link rel="stylesheet" href="../../workbench/server/static/workbench.css">`
   （相对路径；`file://` 下能加载 —— 已实测）。
   ⇒ **不许**在样式板里重写一套颜色/字号/圆角，**不许**硬编码 hex。
   ⇒ 这样「现状」那一列永远是真的，且 CSS 后续演进后重新打开就是最新的。
2. **两套主题并排**：暖纸 + 夜纸。夜纸靠 `<html data-theme="night">`（与设置视图同口径）。
3. **每个组件一页**（或一节），给出 **「现状 + 2–3 个候选」并排**：
   - **现状**：就是产品现在的样子（链接真实 CSS）—— **不美化、不改写**。
   - **候选**：在同一套 token 下做的**另一种形态**，用**样式板自己的内联样式**实现
     （写在页面里的 `<style>` 块里，**带 `data-variant` 标记**，便于事后回写）。
   - 候选必须**真的能落地**（只用现有 token；不引新依赖、不引外部资源）。
4. **能选、能导出**：
   - 每个候选旁给一个「★ 选它」的**可点标记**（用 radio 或 button）；
   - 底部给一个「**导出我的选择**」按钮 ⇒ 点一下把选择**复制到剪贴板**并显示
     （`navigator.clipboard`，**带 `file://` 降级**：失败就把结果渲染到页面上让人手抄）。
   - 选择**存 localStorage**（键名 `lk-styleboard-v2`）⇒ 刷新不丢。
5. **组件清单以第一件的对照表为准**：只对「产品里确实存在」的组件做「现状 + 候选」；
   对 ⚠️ / ❌ 的组件，单独开一节「**产品里还没有的形态**」，
   给**设计候选**（明确标注「这是新设计，产品里还没有」）——
   这样你既能看到现状，也能看到缺口长什么样。
6. **可读性**：一屏能看完一两个组件；字号别太小；每个候选下方一行**一句话说明它改变了什么**
   （例如「更紧凑 / 更强存在感 / 更适合长文本」）。

**候选从哪来**：每个组件给 2–3 个**真的不同**的形态，不是同一形态换颜色。
设计取舍请照 `design-notes/component-spec.md` 的**组件规格**与
`design-notes/layout-spec.md` 的方向（暖纸 + 现代圆润、12px 圆角、三角色色克制、
状态靠颜色 + 几何双通道、零状态文字）。
**若某组件的形态在 spec 里已经唯一确定**（例如「题号格」的规则），
就**只给 1 个候选**并注明「spec 已定稿，仅供确认」—— 不要硬凑三种。

## 硬约束
- **只写**：`tmp/frontend-audit/styleboard-v2/`（评审件，不入库）
  与 `openspec/changes/workbench-visual-language-v2/component-inventory.md`（**新建**）。
- **绝不改**产品代码（`workbench/` 一律不动 —— **另有几个 agent 正在并行改那些文件**）、
  **绝不改** `component-spec.md`（设计权威）、`decisions.md`、`tasks.md`、`docs/`、`openspec/` 下其它文件。
- **不引外部资源**：无 CDN、无 npm、无外部字体/图片。
  图形一律用 CSS 或内联 SVG。
- **不要覆盖旧的 `tmp/frontend-audit/styleboard/`**（那是审计证据，另作他用）。
- ⚠️ `file://` 下 **`fetch` 会被 CORS 拦** ⇒ 样式板**不许**用 `fetch` 读本地文件
  （CSS 用 `<link>` 没问题；数据请**内联**在页面里）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```
- **自己打开看一眼**（`file://` 双击可开）⇒ 确认：token 命中（`--surface-base` 暖纸
  `#fdf8ef` / 夜纸 `#1c1a16` / `--r-md` 12px / `--ink-strong` `#221f1a`）、
  **控制台 0 错误**、亮/暗两套都对、点「导出」能出结果。
- 报告里贴：**控制台错误数（应为 0）** 与**你核对过的 token 取值**。

## 落盘纪律与回报
- `component-inventory.md` 与样式板**分开**（样式板在 `tmp/` 不入库，只提交 inventory）。
- **不要 `git add -A`** —— 只 `git add openspec/changes/workbench-visual-language-v2/component-inventory.md`。
- 最终回报（中文）必须复述：
  **① 清单对齐表**（28 个组件逐个：spec 类名 / 产品真实类名 / 状态 / 备注）+
  **② 样式板做出来了哪些组件、每个给了几个候选** +
  **③ 你认为最值得让所有者挑的三个组件（并说明为什么）** +
  **④ 产品里缺失的形态清单** +
  **⑤ 控制台错误数与 token 取值核对** + 四条验证命令结果 + 待裁决项。
- 数字与类名一律以**当场 grep 出来的**为准，不要照抄本任务书里的粗查结果。
