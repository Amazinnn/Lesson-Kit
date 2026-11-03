# proposal — workbench-display-redundancy-cleanup

## Why

工作台前端反复出现"展示冗余"，且多以**注释型字段**形式呈现：题号旁的「详情」小字按钮、
解析纸里的 provenance 元信息（「参考来源 / Agent 独立推导」）、「（Agent 提炼）」括号注释、
「判定：」「来源：」等硬编码「字段名: 值」前缀、右栏会话的「provider · 日期 · 运行中」meta 行、
分组标题挂计数徽标、「设置」套「设置」同名、Agent 里程碑状态点+状态文字三通道叠放。
这些字段不是学习者需要的信息，而是实现注释 / 元信息复述 / 同一信息的重复呈现，
违背 component-spec §4.15「状态零文字」与「冗余状态通道」反模式，也让界面偏离
「学习内容是视觉锚点」的锚定原则。所有者已逐项确认为真实缺陷，需以规格落地清除并沉淀纪律。

### Contract drift（显式登记，本 change 一并协调）

- **DRIFT-CUE-1**：`openspec/specs/workbench-ui/spec.md:761`「Redundant state cues」现明文
  **允许**用 text 作为颜色之外的冗余通道；但 component-spec §4.15 / §4.30（A-115，组件形态权威）
  裁定状态「零文字」，状态语义走宿主 `aria-label` 而非可见文字。二者在「可见状态文字」上冲突。
  本 change 通过收紧该 Requirement 消除冲突（见 delta），不靠时间戳选边。
- **DRIFT-CUE-2**：`practice-flow.js:838` 用「回答正确。」、`paper-practice.js:733` 用「判定：正确」——
  同一判定信息两条流口径不一，属实现漂移，本 change 统一为一（见 design.md A4）。

## What Changes

- 移除题号格旁「详情」小字按钮（`part-practice.js:83`）：悬停/聚焦已弹小问状态卡，
  `.paper-dot` 的颜色+几何+`aria-label` 已表达同一状态，可见文字复述属冗余。
- 移除解析纸 provenance 元信息行「参考来源 / Agent 独立推导」（`part-practice.js:35`）。
- 去掉「你的答案（Agent 提炼）」中的括号注释，保留「你的答案」（`part-practice.js:33`）。
- 统一判定行口径：`paper-practice.js:733-734` 去「判定：」前缀，与 `practice-flow.js:838` 对齐。
- 去掉「来源：」硬编码字段名前缀（`paper-practice.js:688`、`practice-flow.js:2203`、`pages.py:1177`）；
  证据串本身与其显隐偏好（`Question source display preference`）不变，只去标签。
- 移除右栏会话条目「provider · 日期 · 运行中」meta 行（`workbench.js:5746-5751`）；
  靶子 `shell.html` 会话只有状态点+标题+预览，无 meta 行。
- 移除左栏「优先回看」分组标题旁的计数徽标（`pages.py:1125-1148`）；
  对齐 `workbench.js:5683` 自订规则「组标题不带任何计数」。
- 消除「设置」组标题与其下唯一条目同字（`pages.py:1142-1146`），条目改具象名（对齐靶子）。
- 移除 Agent 里程碑可见状态文字（`agent-ui.js:118-141`），状态走 marker 几何 + 宿主 `aria-label`
  （DRIFT-CUE-1 收紧后的一致结果）。
- 移除「影响：」「试卷：」「工件 · 试卷」kicker、「工作区/lesson-kit」注释型 eyebrow 等
  「标签: 值」堆砌；工件卡不再露出机器 ID（`agent-ui.js:209/261`、`workbench.js:3896`、`pages.py:204/211`）。
- 把「零注释型字段」上升为一条命名的跨切面设计纪律，写入权威文案/组件契约与术语表，防复发。

**不做**：不改任何请求序列/载荷/Tab 序列（G-1/G-8 红线）；不改来源显隐偏好行为；
不动图谱页算法与版式（范围外，A-8/A-26）；不实现 component-forms 的 4 条 B 类新行为。

## Capabilities

### New Capabilities

（无。本 change 是对既有 `workbench-ui` 能力的收紧与清理，不引入新能力面。）

### Modified Capabilities

- `workbench-ui`：
  - **MODIFIED**「Redundant state cues」——收紧为：颜色不得是唯一通道，且**可见状态文字**
    不作为冗余通道（状态语义走几何/outline/位置 + 宿主 `aria-label`），消除 DRIFT-CUE-1。
  - **ADDED**「No annotation-type display fields」——新增跨切面纪律：练习页与壳层/导航
    不得呈现注释型字段（provenance 元信息、实现方式括号注释、硬编码「字段名: 值」前缀、
    同一信息重复呈现、组标题计数、与组名同字的条目、机器 ID）。

## Impact

- 受影响代码：`workbench/server/pages.py`、`workbench/server/static/{workbench,agent-ui,part-practice,paper-practice,practice-flow}.js`。
- 契约同步：`openspec/specs/workbench-ui/spec.md`（经本 change delta）；组件/文案权威
  `openspec/changes/workbench-visual-language-v2/design-notes/{component-spec.md §3,copy-table.md}`；
  术语 `docs/GLOSSARY.md`（新名词「注释型字段」先定义）；`docs/PRODUCT-MANUAL.md` 对应章节；
  `docs/ACTION-GRAPH.md` 登记退役的「详情」入口。
- 无数据/schema 变更；无 API 变更；用户可感知行为为"减少冗余展示"，以旧为优先（移除项均为新增的冗余，非既有可用功能）。
