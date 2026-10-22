# 契约漂移登记册 — workbench-visual-language-v2

> **这是什么**：本变更在设计阶段确认的一批**既有契约分歧**的登记表。
> 每一行都是一条**已被实证**（`grep` / 读码可复核）的分歧：当前实现或某份工件
> 与一份**有声明职责**的契约文件（`openspec/specs/` / `docs/DATA_MODEL.md` /
> `docs/GLOSSARY.md` / `docs/PRODUCT-MANUAL.md` / `FILE_CONTRACT.md`）**对不上**，
> 且**本轮只登记、不修**。
>
> **这不是什么**：
> ① **不是规范** —— 表里描述的「现状」都还没有被改，写进 `docs/` 等于把未解决的分歧
> 变成规范（这正是 `design.md` D-15 否掉另外三个候选位置的理由）；
> ② **不是本轮要修的清单** —— 登记动作本身不修任何一条；
> ③ **不是名词缺失清单** —— 名词缺失归 `docs/PENDING-DEFINITIONS.md`，
> 漂移是**行为 / 字段 / 口径**的分歧，两者语义不同，不要混放；
> ④ **不是审计快照** —— `docs/audits/` 只保存带日期的快照，本表是**滚动的**。
>
> **怎么用**：后续开 change 时按 §2 的「建议归属」索引分派；每处理一条，回来把该行的
> 「改成什么 / 谁来定」列改为「已处理（change 名 + 合并日期）」。
> **登记 ≠ 已修** —— 任何读者不得把「已登记」读作「已处理」。
>
> **位置**：本文件只存在于 `openspec/changes/workbench-visual-language-v2/`，
> **不进 `docs/`**（`design.md` D-15）。随本变更一起归档。
>
> **清理责任与滚动维护**：`docs/ACTION-GRAPH.md` 不收本表（无动作增删）；
> 滚动维护由**本变更的 spec owner** 负责 —— 每归档一个处理该表条目的 change，
> owner 回来更新对应行。提示「本仓库存在 N 条已登记漂移」的交接文本写在
> `openspec/changes/workbench-visual-language-v2/HANDOFF.md`。
>
> **条数说明**：本表实际登记 **168 条**（`CD-001`…`CD-168`）。
> `tasks.md` 27.2 写的是 165 条 —— **差额 +37 条的原因逐条说明在 §4.1**
> （同一冲突的「多条腿」必须逐腿登记 + 裁决已下但落地未落的残留），
> **没有为凑数编造条目**。自检结果见 §4。

---

## 1. 主表

| ID | 位置（file:line） | 现状 | 与哪份契约冲突 | 建议归属 | 优先级 | 改成什么 / 谁来定 |
|---|---|---|---|---|---|---|
| CD-001 | `workbench/server/static/workbench.css:16-17` | `--dsw-bg-base: var(--lk-paper)`（#fffdf7）与 `--dsw-bg-layer-1: #fffefa` 的 RGB 只差 (0,−1,−3)；`--dsw-bg-layer-1` 被引用 19 次，卡片面与页面底视觉同色 | `openspec/specs/workbench-ui/spec.md:731-736`「Soft Mondrian visual foundation」要求纸面有可感知的面分层；`docs/GLOSSARY.md:349-353`「纸面层级 / Paper level」已定义四层 | openspec change | 高 | 本变更 tasks 3.1 把四层纸面写成显式取值（底/卡/浮起/墨块）；层数与取值由 spec owner 在 `workbench-ui` delta 的 Soft Mondrian 条款钉死 |
| CD-002 | `workbench/server/static/workbench.css:4` 与 `:1505-1518` | 两套 `:root` 并存；第二套用裸名 `--paper/--ink/--hair/--blue/--yellow/--red/--shadow/--graphite/--green/--blueSoft/--yellowSoft/--redSoft`，作用域是全页，与将来新增 token 撞名时不报错 | `openspec/changes/workbench-visual-language-v2/design.md` D-1（token 命名唯一权威）；`decisions.md` A-9（`--surface-*`/`--ink-*`/`--role-*` 为唯一真值族） | openspec change | 高 | 本变更 tasks 1.1 只保证新层与这 12 个裸名**零同名**；裸名族本身的收编（加前缀或收进 `.graph-shell` 作用域）归 `graph-node-visual-language` change |
| CD-003 | `workbench/server/static/workbench.css:31-33` | 三档边框 token 全是 `rgb(0 0 0 / 4%\|10%\|12%)`（冷黑），共 56 处引用；叠在 #fffdf7 暖纸上产出冷灰（#e8e7e2）而非墨色 | `openspec/specs/workbench-ui/spec.md:731-736`「dark structural rules」；`docs/GLOSSARY.md:340-348`「柔和蒙德里安」 | openspec change | 中 | 本变更 tasks 3.3 取消描边（56 处 `--dsw-border-l1/l2/l3` 引用归零），只保留控件边界与单侧结构线两条暖墨规则 |
| CD-004 | `workbench/server/static/workbench.css:1253,1164,1280,1464,1473,1895` 等 21 处 | 21 个硬编码边框 hex 绕过 token（`#e5e7eb`/`#e6e8eb`/`#ddd`/`#d8d4c8`/`#dedbd3` 等） | `openspec/specs/workbench-ui/spec.md:731-736` 语义色配额；`docs/GLOSSARY.md:340-348` | openspec change | 中 | 本变更 tasks 1.4 Step 2 逐个收编进 `--rule-*` / `--surface-*` 族；收编清单在 `design.md` D-3 的映射表里 |
| CD-005 | `workbench/server/static/workbench.css:1027-1029` | `h3{font-size:14px}` 与正文 14px 完全相同；全站 16 个离散字号（11/12/13/14 四档各差 1px） | `openspec/specs/workbench-ui/spec.md:771`「Learning content is the visual anchor」要求正文 ≥17px | openspec change | 中 | 本变更 tasks 1.4 Step 3b 换成成对字号阶梯（17/19/21/24/28），`h3` 提到 19px |
| CD-006 | `workbench/server/static/workbench.css:489,851,1315,1356,1387,1411,1432` | `padding/margin/gap` 共 30 档离散值，相邻元素靠 5/6/7/8/9 随机取值 | `openspec/specs/workbench-ui/spec.md:731-736` 的一致性要求（Soft Mondrian 的网格节奏） | openspec change | 低 | 本变更 tasks 1.4 Step 3a 收敛为 4/8/12/16/24/32/48 阶梯 |
| CD-007 | `workbench/server/static/workbench.css:43-44`、`:374,392,421,1889` | `--dsw-radius-sm` 与 `--dsw-radius-md` **同值 6px**；硬编码另有 18px(button)/14px(button.sm)/10px(input)/50%(.paper-dot)/999px | `docs/GLOSSARY.md:340-348`「柔和蒙德里安」；`decisions.md` 第 6 组新基线（圆角统一 12px） | openspec change | 中 | 本变更 tasks 1.4 Step 3c + A-15（Agent 输入框圆角 20px 作废，同族控件统一 12px） |
| CD-008 | `workbench/server/static/workbench.css:36-39` | 30 条 `box-shadow` 中 5 条同为 `--dsw-shadow-lv1` = `0 2px 4px rgb(0 0 0/5%)`（5% 黑 ≈ 不可见），`--dsw-shadow-lv2` 主层只有 2% 透明度 | `openspec/specs/workbench-ui/spec.md:731-736` 要求纸面抬起可感知；`docs/GLOSSARY.md:349-353`「纸面层级」以圆角+暖调柔影表达分层 | openspec change | 中 | 本变更 tasks 3.2 换成三档暖调柔影（`rgb(61 52 37 / α)` 色基），`--elev-1` 首层 `0 1px 2px` 不得省 |
| CD-009 | `workbench/server/static/workbench.css:799` | `border: 1px solid var(--dsw-border-subtle)` —— 该变量在 `:root` 全文**从未定义**，整条声明失效，表格线回落 `currentColor`（变成正文色） | `openspec/specs/workbench-ui/spec.md:731-736`（描边应是细墨线，不是正文色） | openspec change | 高 | 本变更 tasks 2.2 补齐（**单独提交、单独 review、单独截图**）：补齐后表格线会从「正文色」变为「暖灰规则色」，属可见变化必须单独确认 |
| CD-010 | `workbench/server/static/workbench.css:858` | `background: var(--dsw-bg-layer-3)` —— `--dsw-bg-layer-3` 从未定义，该声明整条失效 | `openspec/specs/workbench-ui/spec.md:731-736`（面分层应可感知） | openspec change | 中 | 本变更 tasks 2.2 补齐（与 CD-009 同批单独提交） |
| CD-011 | `workbench/server/static/workbench.css:1051` | `color: var(--dsw-text-muted, #68707b)` —— `--dsw-text-muted` 从未定义，靠 fallback `#68707b` 存活；该 fallback 不在灰阶体系内 | `openspec/specs/workbench-ui/spec.md:731-736`；`docs/GLOSSARY.md:340-348` | openspec change | 低 | 本变更 tasks 2.2 补齐 + tasks 4.3 把 `--dsw-text-muted` 并入 `--ink-faint` 墨阶 |
| CD-012 | `workbench/server/static/workbench.css:1464,1473,1895` | `var(--dsw-border, #e5e7eb)` / `var(--dsw-border, #ddd)` —— `--dsw-border` 从未定义，三处 fallback 是随手写的两个不同值 | `openspec/specs/workbench-ui/spec.md:731-736` | openspec change | 中 | 本变更 tasks 2.2 补齐（与 CD-009 同批） |
| CD-013 | `workbench/server/static/workbench.css:127,305,354,359,388,428` | `--dsw-label-caption` 2.12:1、`--dsw-label-dimmed` 1.25:1（`::placeholder`）、`--dsw-state-success` 2.26:1、`--dsw-state-warn` 3.20:1 全部低于 WCAG 3:1；`::placeholder` 1.25:1 几乎不可见 | `openspec/specs/workbench-ui/spec.md` 的可访问性条款（正文级文字 ≥4.5:1） | openspec change | 高 | 本变更 tasks 4.3 墨阶收敛（4 级可用文字灰 + 1 级非文本灰）+ tasks 12 夜纸对比度复测；复测口径由 spec owner 确认 |
| CD-014 | `workbench/server/static/workbench.css:1043-1045` | `.status-dot.ok/.warn/.err` 是三个纯色圆点，无文字、无形状差异 | `openspec/specs/workbench-ui/spec.md:747` 起「Requirement: Redundant state cues」明写 "Color SHALL NOT be the only carrier of learning or interaction state" | spec delta | 高 | spec owner 明确状态点的冗余通道要求（形状/文字/几何）；实现由本变更 tasks 17 或独立 change 落地，本条只登记契约缺口 |
| CD-015 | `workbench/server/static/workbench.css:848,865,962,983,1216` 等 35 处 | 22 个硬编码色绕过 token，含**第二蓝** `#2864dc`、**第二灰** `#57606a`、**三套红** `#d6453d`/`#b42318`/`#b62f28`/`#d12c2c`、**第四种橙** `#d97706`/`#b58b00`/`#e1aa12` | `openspec/specs/workbench-ui/spec.md:731-736`「Accent roles stay scarce」语义配额 | openspec change | 高 | 本变更 tasks 4.2 按 `design.md` D-3 映射表逐条收编（22 色 / 35 处引用） |
| CD-016 | `workbench/server/static/workbench.css:1464,1466,1472,1474,1482` | 第二灰 `#57606a` 与 `--dsw-label-secondary`(#61666b) 几乎同色却是另一个值 | `openspec/specs/workbench-ui/spec.md:731-736` 语义色配额 | openspec change | 中 | 本变更 tasks 4.2 映射为 `--ink-muted` |
| CD-017 | `workbench/server/static/workbench.css:1212,1463,696,731,982`、`:1465,729,1265` | 红/橙/黄出现 7 个不同值，红色同时承载「失败」「弱项」「已回滚」「低分」 | `openspec/specs/workbench-ui/spec.md:731-736`（红只承担失败与阻塞）；`decisions.md` 3.3 | openspec change | 高 | 本变更 tasks 4.1/4.2 收编为 `--role-red`（点 / 面）+ `--role-red-ink`（文字）两档 |
| CD-018 | `workbench/server/static/workbench.css:976` | `#111318` 第四种黑，与 `--lk-ink:#171717` 并存 | `docs/GLOSSARY.md:340-348`「柔和蒙德里安」的墨色口径 | openspec change | 低 | 本变更 tasks 4.2 映射为 `--ink-strong` |
| CD-019 | `workbench/server/static/workbench.css:350,383,400,402,413,1111,1164,1190,161` | 14 条 `transition` 各写各的：5 档时长（100/160/180/200/300ms）+ 2 种几乎相同的自定义缓动 `cubic-bezier(.2,.8,.2,1)` 与 `cubic-bezier(.2,.75,.2,1)`，无动效 token | `openspec/specs/workbench-ui/spec.md`「Motion system」；`decisions.md` 第 12 组动效基本盘 | openspec change | 低 | 本变更 tasks 8 建立动效 token 层并回收硬编码时长 |
| CD-020 | `workbench/server/static/workbench.css`（全文件） | z-index 12 个散落值 0/1/2/3/5/6/7/8/9/10/20/40，其中 5–9 五档紧邻且语义重叠 | `openspec/specs/workbench-ui/spec.md`「Three-column shell with navigation」的浮层叠放次序 | openspec change | 低 | 本变更 tasks 1.4 Step 3e 建 z-index 层级表（`--z-*`） |
| CD-021 | `workbench/server/static/workbench.css:5,6,16-18` | 暖纸只有一个色号：`--lk-paper` 被引用 10 次、`--lk-paper-shade` 仅 3 次，没有任何「中间调纸」 | `openspec/specs/workbench-ui/spec.md:731-736`；`docs/GLOSSARY.md:349-353`「纸面层级 / Paper level」（已定义四层） | docs/GLOSSARY.md | 中 | 词条已存在，本条登记的是**取值侧**：由本变更 tasks 3.1 落四层取值后，同步复核 `docs/GLOSSARY.md:349-353` 的四层描述与实现一致 |
| CD-022 | `docs/GLOSSARY.md`（全文） | 「排版角色 / Type Role」（display/stat/title/lead/body/meta/label/micro）在本变更工件里已被使用，但**词表里没有这个词条** | AGENTS.md 第 2 条「名词先定义后使用」；`docs/GLOSSARY.md` 是设计名词的唯一权威定义源 | docs/GLOSSARY.md | 高 | 本变更 tasks 28 契约同步时补词条（display/stat/title/lead/body/meta/label/micro 的定义 + 落点 + `_Avoid_`） |
| CD-023 | `openspec/specs/workbench-ui/spec.md:731-736` vs `design.md` D-2 的四层纸面 | spec 只说 "Most screen area SHALL remain paper or neutral"，未说明新增的「桌面底」一档是否仍算 paper/neutral | `openspec/specs/workbench-ui/spec.md:731-736`（本变更要改的条款本身措辞不够） | spec delta | 中 | spec owner 裁决「桌面底」是否算 paper/neutral，并在 `workbench-ui` delta 里把面分层写成可判定的条款 |
| CD-024 | `openspec/specs/workbench-ui/spec.md:731-736` | spec 同时写 "Blue SHALL represent primary action and selection" 与 "yellow SHALL represent current/review emphasis"；现状「当前练习」用第二蓝 `#2864dc`（`workbench.css:848,865,962,983,1216`），两句话都沾边，归属未裁决 | `openspec/specs/workbench-ui/spec.md:731-736` | 产品决策 | 中 | 所有者裁决「当前练习」归蓝还是归黄；裁决后由 spec owner 改写该条款，实现才可改色 |
| CD-025 | `workbench/server/static/workbench.css:1586,1741` 等 5 处、另 2 处 | `font-weight:750`（5 处，图谱区）与 `650`（2 处）不在 v2 字重阶梯 400/500/600/700 内 | `decisions.md` 第 4 组字重口径；`docs/GLOSSARY.md:338-340` 双字体条目 | openspec change | 低 | 本变更 tasks 5 只处理阅读面/界面两族字重；`750` 属图谱区，归 `graph-node-visual-language` change；`650` 需先逐处定位是否落在图谱区 |
| CD-026 | `workbench/server/static/workbench.css`（全仓 `prefers-color-scheme` 命中 0 处） | 现状完全没有跟随系统主题的路径；`design.md:684` 与 `tasks.md:44,122` 又明写「不使用 `prefers-color-scheme` 兜底」 | `docs/GLOSSARY.md:370-374`「主题偏好」明写「默认跟随系统」；`docs/PRODUCT-MANUAL.md:522` 同 | spec delta | 高 | 所有者裁决 A-11 已定「学习者显式选择优先，无已存偏好时跟随系统」；spec owner 据此补 `workbench-ui` / `workbench-settings` 的主题默认来源条款（见 CD-087） |
| CD-027 | `workbench/server/static/workbench.css:157` 与 `workbench/server/static/workbench.js`（桌面列宽模板不在 CSS） | 桌面端真正生效的列宽模板写在 JS 内联样式里，CSS 另有 `280px \| 1fr \| 420px` 一份，两个真值源 | `openspec/specs/workbench-ui/spec.md:10-42`「Three-column shell with navigation」 | openspec change | 高 | 本变更 tasks 13 把三栏几何收归 CSS 变量（`--shell-col-left` / `--shell-col-right`），`workbench.js:4584-4586` 的「中栏 ≥ 420px」不变式保持 |
| CD-028 | `workbench/server/static/workbench.css:178-224` | `.scope-tray-anchor` / `.scope-tray` / `.scope-tray-trigger` / `.scope-tray-panel` / `.scope-tray-header` / `.scope-tray-list` / `.scope-tray-item` 共 7 条规则 + `practice-flow.js:270` 一处 JS 取值，是**已退役** scope-tray 的化石 | `docs/GLOSSARY.md:340-343`「准备练习列表 / Staged Practice List（已退役）」 | openspec change | 中 | 本变更 tasks 14/15 清理这批死规则（与 tasks 2.3 别名期同批删除），并确认 `practice-flow.js:270` 的空取路径可安全移除 |
| CD-029 | `workbench/server/static/workbench.css:153` 与 `workbench/server/static/workbench.js:4569-4573` | spec 写 "a collapsible right Agent conversation column"，但 `fitAiColumn()` 只在 `innerWidth < 1024` 时收起；桌面端**没有任何收起入口**（`.mobile-drawer-controls` 在 ≥1024px 是 `display:none`） | `openspec/specs/workbench-ui/spec.md:12` | spec delta | 高 | spec owner 明确 spec 指的是「窄屏抽屉」还是「桌面也可手动收起」；若需桌面收起按钮，顶栏要新增控件并先落 spec |
| CD-030 | `workbench/server/static/middle-navigation.js:53-60` | `updateActiveNavigation` **按下标**匹配导航项（`currentItems[index]` ↔ `nextItems[index]`），导航项数量或顺序一变就错位 | `openspec/specs/workbench-ui/spec.md:10-42`（左栏选中态必须始终指向当前页） | openspec change | 中 | 本变更 tasks 15 左栏导航语法改造时改为按稳定 key 匹配；不能靠 CSS 掩盖 |
| CD-031 | `workbench/server/static/middle-navigation.js:82-93` | 客户端换页只替换 `#middle-page`，左栏「优先回看」弱项列表不随之刷新 | `docs/PRODUCT-MANUAL.md:47` 只写了「同工作区换页只替换中栏内容」，**左栏归属未定义** | spec delta | 中 | 契约责任人补写左栏在换页时的刷新义务（属导航行为变更，需先落 spec 再实现） |
| CD-032 | `docs/GLOSSARY.md`（无「优先回看」折叠态词条） | 左栏「优先回看」是 `<details>` 折叠条，但**默认展开态**与**是否跨页/跨会话记忆**在契约里无定义 | `openspec/specs/workbench-ui/spec.md:749-753` 只约束状态表达，不约束折叠策略 | 产品决策 | 中 | 产品定默认态；若要记忆则是新增客户端持久状态，须在 `docs/DATA_MODEL.md` 声明为「展示偏好，不是学习记录」 |
| CD-033 | `openspec/specs/workbench-ui/spec.md`（无 hub 排序条款）、`workbench/registry.py:70-71`、`workbench/data/queries.py:12-22` | hub 的 22 张工作区卡是**注册顺序**；`hub_stats` 只有 `kps/problems/signals/due`，**没有「最近使用」数据源** | `openspec/specs/workbench-ui/spec.md`（缺 hub 排序契约） | spec delta | 中 | spec owner 增补 hub 排序契约；本变更 tasks 24 用已有的 `due` 作「需要处理」视觉提示、**保持注册顺序不变** |
| CD-034 | `workbench/registry.py:70-71`、`workbench/server/api.py:32-46` | 注册表条目只有 `name / path / db / active_course / active_chapter`，无 `last_used` 时间戳 | `docs/DATA_MODEL.md`（持久字段语义的唯一权威；本字段不存在） | docs/DATA_MODEL.md | 中 | 若产品要「最近使用」排序，必须新登记持久字段 + writer/consumer 边界；否则维持现状并由 spec owner 在 spec 里写明 hub 用注册顺序 |
| CD-035 | `openspec/specs/workbench-ui/spec.md:731-736` vs `workbench/server/pages.py`（章节透镜 DOM） | spec 说 yellow 表示 current/review emphasis；标题带把黄块当**纯装饰端头**（无状态标记），等于让黄色承载无明确语义的信息 | `openspec/specs/workbench-ui/spec.md:731-736` | spec delta | 中 | spec owner 裁决黄块是装饰还是状态标记（若后者需在 DOM 加 `#layout[data-chapter]` 之类的状态标记并先定义其语义） |
| CD-036 | `workbench/server/pages.py:57-62` | 章节透镜是**裸原生 `<select>` + 一个 checkbox 开关**（`#chapter-lens-select` / `#chapter-lens-switch`），与 spec 描述的「a switch whose off state means the whole course」在形态上不是同一物 | `openspec/specs/workbench-ui/spec.md:829-838`「Chapter switch in the top bar」 | spec delta | 中 | spec owner 明确控件形态（原生 select / 自绘 chip）与「开关关 = 整门课」的表达方式，再由本变更 tasks 15 落地 |
| CD-037 | `docs/PRODUCT-MANUAL.md`（工作台章节） | hub 首页与工作台中栏的关系在手册里没有一句话说明（hub 是独立应用、还是工作台的一种视图） | `docs/PRODUCT-MANUAL.md`（用户可见产品说明的权威） | 产品决策 | 低 | 产品定 hub 与工作台的关系；本变更 tasks 24 若采纳 hub 分层，同 PR 补手册一句 |
| CD-038 | `openspec/specs/review-workbench/spec.md:227-235`、`workbench/server/pages.py:154`、`workbench/server/app.py:294`、`workbench/server/static/workbench.css:1083-1104` | 「建议行」有纯函数实现（`pages.py:282` `suggestion_rows`）、被 `app.py:294` 调用、`practice_page`（`pages.py:154`）也接了 `suggestions` 参数，但**练习页从不渲染它**；`workbench.css:1083-1104` 全是死 CSS | `openspec/specs/review-workbench/spec.md:227-235` 用的是 "MAY"；`openspec/specs/workbench-ui/spec.md:46` 又明令练习页 "SHALL NOT expose suggestion-to-assembly actions" | openspec change | 高 | 二选一并开独立 change：① 明确「练习页渲染建议行（只读、无组卷动作）」并同步 `workbench-ui` spec + `docs/GLOSSARY.md:444-450`；② 正式退役 `suggestion_rows` 与死 CSS，在 GLOSSARY 记一条退役条目 |
| CD-039 | `workbench/server/static/paper-practice.js:1321-1332` vs `workbench/server/pages.py:227-233` | 完成页的逐题回看索引 JS 已写好，但 `#paper-links` 容器在 HTML 里**不存在** → 整段是死代码 | `openspec/specs/workbench-ui/spec.md:1559` 列举了完成页的动作集合（`查看本次答卷`/`再练一次`/`返回试卷列表`），未含逐题索引 | openspec change | 中 | 二选一：① 补 `#paper-links` 容器并在 spec 登记「完成页提供逐题索引」；② 删 `paper-practice.js:1321-1332` 死代码并在 spec 记一句「完成页不含逐题索引」 |
| CD-040 | `workbench/server/pages.py:189-190` | 「目标 / 计划 / 时间安排」整块塞进 `<details class='practice-planning'>`，且 `#time-view` 自带 `hidden` —— 折叠策略与默认可见性无契约 | `openspec/specs/workbench-ui/spec.md`（练习页条款）；`docs/GLOSSARY.md:603-606`「每日计划」 | 产品决策 | 中 | 产品裁决是否默认展开、是否把「今日到期」提到首屏；裁决前本变更 tasks 16 只改善展开后的层级 |
| CD-041 | `openspec/specs/workbench-ui/spec.md:1538` | spec 写 "expose compact **numeric 1–5 input**"；若被读作「必须是一个数字输入控件」，自评芯片行（radio 代理）就与措辞冲突 | `openspec/specs/workbench-ui/spec.md:1538` | spec delta | 中 | 契约责任人确认措辞是否允许「数字输入框 + 芯片代理」；若不允许，退化为只保留原生数字框的 CSS 包装 |
| CD-042 | `workbench/server/static/paper-practice.js:1314-1315` | 完成页把试卷名与题数写进了 setup 卡里**不可见**的 `#paper-title` / `#paper-count`（写入目标错误）；`renderCompletion` 单独再算一次 | `openspec/specs/workbench-ui/spec.md:1559`（完成页必须展示的量：total / correct-wrong / stuck / pending ratings），未列举试卷名 | openspec change | 中 | 本变更 tasks 16 修正写入目标（已算出的信息放到该在的地方）；若要在完成页**新增**「试卷名 · 共 N 题」一行，先由 spec owner 确认并登记 |
| CD-043 | `workbench/server/static/workbench.css:1290,1305` | 月历把「目标类型区分」（长期 vs 阶段）也映射到蓝/黄/红三色，逾期用红 —— 类型信息占用了语义色预算 | `docs/GLOSSARY.md:340-348`（蓝/黄/红只承担主要动作、当前或复习强调、重点练习或失败） | docs/GLOSSARY.md | 中 | 产品裁决「类型」是否彻底从语义色摘出去；要摘则先改 GLOSSARY 的柔和蒙德里安条目 + `openspec/specs/calendar-workload/spec.md` |
| CD-044 | `docs/GLOSSARY.md:607-610`「Agent 对话栏 / Agent Rail」 vs `workbench/server/static/workbench.css`（右栏 420px） | Agent 栏宽度在 GLOSSARY 里被定义成「常驻会话主表面」，其宽度是**产品决策**而非纯视觉问题，但契约里没钉数值 | `docs/GLOSSARY.md:607-610` | 产品决策 | 低 | 产品定右栏宽度（现状 420px；收窄到 360px 需先改 GLOSSARY + `workbench-ui` 三栏条款） |
| CD-045 | `workbench/server/pages.py:211-214` | 工具条（提交试卷 / 暂停）在 DOM 里排在题面之前 → 键盘顺序与读屏顺序都把它放在题面之前 | `openspec/specs/workbench-ui/spec.md:1514` 只约束动作集合，不约束顺序 | spec delta | 中 | 契约责任人补写练习页动作的 DOM/焦点顺序；DOM 重排（含「题号面板改单控件」）属独立裁决 |
| CD-046 | `workbench/server/static/paper-practice.js:1321-1332`（逐题索引）+ `workbench/server/static/workbench.css:1888`（`.paper-dots` `max-height:140px; overflow-y:auto`） | 题号面板被放在题面之前，且面板内滚 —— 吃掉 N 个 Tab 停靠点；`.paper-dots` 本身**不是死规则**（`workbench.css:1888` 有规则、`pages.py:215` 有标记、`paper-practice.js:47` 有引用），真问题是形态 | `openspec/specs/workbench-ui/spec.md:1514`（练习页动作与题面的相对位置未约束） | spec delta | 中 | 契约责任人明确题号面板的位置与是否可滚动；实现由本变更 tasks 16 落地 |
| CD-047 | `workbench/server/static/workbench.css:1083-1104`（`.staged-practice` / `.staged-list` 等 22 条建议行死 CSS） | 建议行的 CSS 全套存在但无 DOM 消费者；`pages.py:282` 的纯函数也无人渲染 | `openspec/specs/review-workbench/spec.md:227-235`（MAY） | openspec change | 中 | 与 CD-038 同案处置：退役则一并删 CSS，落地则一并启用 |
| CD-048 | `openspec/specs/workbench-ui/spec.md:73-75`（"no stored topic/group layer"） vs `docs/PRODUCT-MANUAL.md:163` | 手册说关联题目「按主题分组折叠展示（点组名展开）」，spec 明令**无** topic/group 层，实现也是扁平列表（`pages.py:678-692`） | `openspec/specs/workbench-ui/spec.md:73-75` + Scenario「Browse linked problems directly」 | docs/GLOSSARY.md | 高 | spec 较新且与「退役准备练习列表」方向一致 → 修 `docs/PRODUCT-MANUAL.md:163` 对齐 spec；同时决定 `.problem-topic` 死 CSS 的去留（见 CD-051） |
| CD-049 | `openspec/specs/workbench-ui/spec.md:117-119`（"in weak order"） vs `workbench/server/pages.py:396`（默认「课程顺序」） | spec 说知识点列表按 weak order 排，实现与 `docs/PRODUCT-MANUAL.md:133` 都是「课程顺序」默认 | `openspec/specs/workbench-ui/spec.md:117-119` | spec delta | 中 | 改 spec 文案（"weak order" 是陈旧表述），与排序次序定义（CD-050）一起裁决 |
| CD-050 | `docs/PRODUCT-MANUAL.md:133` | 手册只说「排序是稳定的：同值条目保持原有相对次序」，**未规定跨值次序**；spec 也未写；而语义序（needs_work → review → 未标记 → mastered）在图谱侧已有（`docs/PRODUCT-MANUAL.md:142`） | `docs/PRODUCT-MANUAL.md:133` | 产品决策 | 中 | 产品定跨值次序；定后补 `docs/PRODUCT-MANUAL.md` §3.2 一句，并决定是否同时改 `workbench-ui` spec 的列表条款 |
| CD-051 | `workbench/server/static/workbench.css:515-521` | `.problem-topic` / `.problem-topic summary` 是**化石规则** —— 全仓无 `problem-topic` 标记 | `docs/GLOSSARY.md:340-343`（准备练习列表已退役）；与 CD-048 同源 | openspec change | 中 | 本变更 tasks 2.3 别名期或 tasks 18 知识点页改造时删除；删前先按 CD-048 决定 PRODUCT-MANUAL 是否复活分组 |
| CD-052 | `workbench/server/static/workbench.css:1008` | `.kp-practice-action { text-decoration: none; }` 是**化石规则** —— 对应的「练习此知识点」入口已退役（`pages.py:344` `practice_action = ""`） | `openspec/specs/workbench-ui/spec.md:66-68` 仍 SHALL 提供该动作（见 CD-053） | openspec change | 中 | 与 CD-053 同案：spec 改了就删 CSS，spec 保留就补入口 |
| CD-053 | `openspec/specs/workbench-ui/spec.md:66-68`（+ Scenario「Practise one knowledge point」）vs `workbench/server/pages.py:344` | spec 要求知识点页提供「一个显眼的 `练习此知识点` 动作」，实现**没有这个按钮**（页面只有「关联题目」列表） | `openspec/specs/workbench-ui/spec.md:66-68` | spec delta | 高 | spec owner 裁决：改 spec（承认该动作已退役，对齐 `docs/GLOSSARY.md:341`）还是补实现（新增功能 + 触及 Paper 组卷范围）；本条只登记 |
| CD-054 | `workbench/server/static/workbench.css:504` | `.knowledge-list .score { … }` —— **死规则**：`.knowledge-list` 的行里只有 `.knowledge-meta`，无 `.score`（`.score` 属于 `.weak-item`，`workbench.css:356`） | `openspec/specs/workbench-ui/spec.md` 的知识点列表条款（无 `.score` 字段） | openspec change | 低 | 本变更 tasks 18 知识点页改造时删除（连同 CD-055） |
| CD-055 | `workbench/server/static/workbench.css:505` | `.knowledge-list .reasons { … }` —— **死规则**：`.reasons` 属于 `.weak-item`（`workbench.css:357`），不在 `.knowledge-list` 内 | 同上 | openspec change | 低 | 本变更 tasks 18 知识点页改造时删除 |
| CD-056 | `workbench/server/static/workbench.css:1166` | `.knowledge-row label { display: flex; … }` —— **死规则**：`.knowledge-row`（`pages.py:380`）内无 `label` | 同上 | openspec change | 低 | 本变更 tasks 18 知识点页改造时删除 |
| CD-057 | `workbench/server/pages.py:682`、`:700`、`:400` | `.linked-problem-list` / `.linked-problem-source` / `.knowledge-index` 三个标记**存在但无任何 CSS 规则**；79 条关联题目没有任何容器级样式 | `openspec/specs/workbench-ui/spec.md:87-90`（每行显示标题与完整题面，不截断） | openspec change | 中 | 本变更 tasks 18 知识点页改造时补容器级样式 |
| CD-058 | `workbench/server/static/workbench.css:752` vs `workbench/server/static/kp-experience.css:12-14` | `.rich-text { line-height: 1.7 }` 与 `.experience-markdown { line-height: 1.7 }` **重复值、不同类名**；经验区因未挂 `.rich-text` 只拿到这一条，标题/列表/表格全丢 | `openspec/specs/workbench-ui/spec.md`（正文阅读体验） | openspec change | 中 | 本变更 tasks 6 共享阅读版式层统一（`.wb-reading`），经验区接入；重复规则二选一 |
| CD-059 | `workbench/server/static/workbench.css:762-763`、`workbench/server/static/kp-experience.css:28-31`、`workbench/server/static/workbench.css:1032` | 列表缩进**三方竞争**：`.rich-text ul` ↔ `.experience-problems ul` ↔ 全局 `ul{list-style:none;padding:0;margin:0}`；后加载的 `.experience-problems ul` 胜出（有缩进），但全局 `list-style:none` 仍生效 → 典型题目列表仍无符号 | `openspec/specs/workbench-ui/spec.md`（列表语义） | openspec change | 中 | 本变更 tasks 6/7 恢复列表语义（项目符号 + 缩进 + 紧凑行距），并消除三方竞争 |
| CD-060 | `workbench/server/static/workbench.css:1034` | CSS 里**只有 `li.muted` 有规则**（`li.muted { color: var(--dsw-label-tertiary); font-size: 13px; }`），没有 `p.muted`；而全仓 **47 处** `class='muted'` 用它表示空态（`pages.py` 13 / `records.py` 9 / `practice-flow.js` 11 / `paper-practice.js` 5 / `workbench.js` 5 / `kp-experience.js` 2，其中 `pages.py:391` 是唯一的 `<li class='muted'>`）。运行时实测 `p.muted` = `color: rgb(23,23,23)` / `14px` / `font-weight:400` —— **与正文完全同权同色** | `docs/GLOSSARY.md:340-348`「柔和蒙德里安」的次要信息层级；`openspec/specs/workbench-ui/spec.md` 的空态条款 | openspec change | 高 | 本变更 tasks 16/19/25 落地空态组件化时统一 `.muted` 规则（补 `p.muted` 或改用 `.wb-empty`）；同时须回填 47 处标记，否则「空态渲染成正文」继续存在 |
| CD-061 | `workbench/server/pages.py:209,232,562,569` | `<a class='outline button-link'>` / `<a class='primary button-link'>` 在全仓**没有任何 CSS 规则**（`button.outline`（`workbench.css:401`）与 `button.primary`（`workbench.css:393`）都是 `button` 限定选择器，作用不到 `<a>`）→ 页头「返回练习」「返回试卷列表」实际是两个无边框无背景的蓝色下划线文字 | `docs/PRODUCT-MANUAL.md`（界面元素规格）；`openspec/specs/workbench-ui/spec.md` 的动作呈现 | openspec change | 中 | 本变更 tasks 16/23 补 `.button-link` 规则或改用统一按钮类；改动前须同步 `docs/PRODUCT-MANUAL.md` 相应截图描述 |
| CD-062 | `workbench/server/experience_page.py:9,19-24,69-91` | 经验区被字符串替换插到正文与关联题目之间，视觉上是第三个平级 section，读者分不清哪块是自己产出的、哪块是系统给的 | `docs/GLOSSARY.md`（做题沉淀的定位） | 产品决策 | 低 | 产品定「用户产出的内容」与「系统列出的内容」的视觉权重；本变更 tasks 18 只能改表现层 |
| CD-063 | `workbench/server/pages.py:377-378` vs `workbench/server/pages.py:340-342` | 列表页用 `learning_current_state` 判提醒，详情页用 `signals` + `schedule.due_at` 判；实测同一 KP（`dmath-ch06-kp-001`）列表行 `data-kp-state='unmarked'` 无提醒，详情页却显示「重点练习」 | `docs/GLOSSARY.md:477-481`「行动提醒」只给了词表，**没给判据来源**；`docs/DATA_MODEL.md` 未裁定两者权威关系 | docs/DATA_MODEL.md | 高 | DATA_MODEL 责任人裁定 `learning_current_state` 与 signals/schedule 的权威关系；GLOSSARY 补判据来源；本变更只登记不改 |
| CD-064 | `openspec/specs/workbench-ui/spec.md`（列表字段清单） vs `workbench/server/pages.py` | `importance` 参与排序但**从不显示**；`docs/PRODUCT-MANUAL.md` §3.2 明列每行只显示名称 / 关联题目数 / 行动提醒 | `docs/PRODUCT-MANUAL.md` §3.2 | 产品决策 | 低 | 产品定是否显示 `importance`；要显示则先扩 `docs/PRODUCT-MANUAL.md` §3.2 的字段清单 |
| CD-065 | `workbench/server/records.py:131`、`:187` | 记录中心**打印**「最近正确率 N%」与「客观题正确率 N%」；口径为 `correct / judged`（`workbench/data/records.py:76-97`），分母是「已判定的作答数」 | `docs/GLOSSARY.md:608-611`「覆盖 / Coverage」明写「规格未定义计算公式」，并把「正确率、完成度百分比」列入 `_Avoid_`；`docs/GLOSSARY.md` **无「正确率」条目** | docs/GLOSSARY.md | 高 | GLOSSARY 补「正确率 / Accuracy」条目（写清分母 = 已判定作答数）；`copy-table.md` R-28/R-41 已定文案口径为「最近判定 N/M」「客观题判定 N/M」，落地属另案 |
| CD-066 | `workbench/data/records.py:83-92`、`workbench/server/records.py:181-185` | 「平均自评」= `AVG(feedback_events.rating)`，**只覆盖写了反馈事件的尝试**，没自评的作答不进分母；口径只存在于实现 | `docs/GLOSSARY.md:608-611`（「规格未定义计算公式」） | docs/GLOSSARY.md | 中 | GLOSSARY 补「平均自评 / Average Rating」条目并写清分母；DATA_MODEL 登记 `summary.average_rating` 的语义 |
| CD-067 | `workbench/server/pages.py:584`（`limit=100`）+ `workbench/data/records.py:53-55`（`LIMIT ?`） vs `workbench/data/records.py:73-75`（`COUNT(*)` 无上限） | 同屏两张卡：「完成练习」= **最近 100 轮**里 `status=='completed'` 的条数（`workbench/server/records.py:183`），「作答次数」= **不限条数**的 `COUNT(*)` —— 两个「总数」的分母口径不一致 | `docs/GLOSSARY.md:608-611`；`docs/DATA_MODEL.md`（持久字段语义） | 产品决策 | 高 | 产品定「完成练习」是改成全量计数（改行为）还是保留截断并改文案加注脚（也改行为）；DATA_MODEL 同步登记 `summary.completed_runs` 的口径 |
| CD-068 | `openspec/specs/workbench-ui/spec.md:944-953` | spec 只要求统计「derived from durable attempts」，**没有钉死任何公式**；三个统计口径全部没有契约出处 | `openspec/specs/workbench-ui/spec.md:944-953` | spec delta | 高 | spec owner 在 `workbench-ui` delta 里钉死四个统计量的公式与分母（作答次数 / 完成练习 / 客观题判定 / 平均自评） |
| CD-069 | `workbench/data/records.py:142`（`_activity(conn, problem_id, weeks=12)`） | 日历窗口长度 12 周是写死参数，产品无法调；「按周汇总 / 12 周趋势折线」属于**新的聚合口径** | `docs/GLOSSARY.md:608-611`（「规格未定义计算公式」正指向这类数字） | 产品决策 | 低 | 产品定是否要「近 8 周 / 近 6 个月」切换；要则先在 spec 或 DATA_MODEL 定义周口径并登记 `docs/ACTION-GRAPH.md` |
| CD-070 | `workbench/server/records.py:294-300` vs `workbench/server/records.py:12-18` | 「错题」把「客观判错」与「明确卡住」合并成同一种灰药丸（badge「未判定」/class `record-verdict-open`） | `docs/DATA_MODEL.md:145-150` 明写 `status` 与 `verdict` **不是同一个状态机**，`status` 取值是 `answered`/`wrong`/`stuck` 等历史枚举 | docs/DATA_MODEL.md | 高 | DATA_MODEL 责任人登记 `problem_attempts.status` → 用户可见标记的映射与文案集合；本变更只登记 |
| CD-071 | `workbench/server/static/workbench.css:1462`（`.record-verdict-ok { background: #e6f4ea; color: #1a7f37; }`） | 记录页判定徽章引入了**契约外的绿色**（绿不在 `docs/GLOSSARY.md:340-348` 的三角色配额里，权威表 §3.4 也无绿档）；徽章由 `workbench/server/records.py:16,39` 绑定 | `docs/GLOSSARY.md:340-348`「柔和蒙德里安」；`openspec/specs/workbench-ui/spec.md:731-736` | openspec change | 高 | **已由 A-20-3 裁决**（`decisions.md` A-20 第 3 条）：本变更 tasks 4.4 **移除契约外绿** ——「答对」改**中性墨 `--ink-strong` + 勾形几何**（「错」仍 `--role-red`），徽章改「结构块 + 几何符号 + 文字」三通道；**不设绿 token**、不改 GLOSSARY 三角色配额 |
| CD-072 | `workbench/server/static/workbench.css:1211`（`.micro-verdict.ok { color: #1a7f37; }`）、`:1214`（`.problem-options label.option-correct { outline: 2px solid #1a7f37; … }`）、`:1892`（`.paper-dot.state-correct { background: #d9ebdd; color: #245d32; }`） | **契约外绿** `#1a7f37` / `#e6f4ea` / `#d9ebdd` / `#245d32` 在 4 处局部例外表达「答对」：练习页判定文案（`:1211`，被 `paper-practice.js:672` 绑定）、选项正确环（`:1214`，被 `practice-flow.js:869` 绑定）、记录页判定徽章（`:1462`）、试卷页题号格「答对」（`:1892`，被 `paper-practice.js:592` 的 `state-correct` 绑定）；微测判定文案另见 `practice-flow.js:810` | `docs/GLOSSARY.md:340-348` 三角色配额（蓝/黄/红）不含绿；权威表 §3.4 只收三角色 | openspec change | 中 | **已由 A-20-3 裁决**（`decisions.md` A-20 第 3 条）：**「答对不再用绿色」** ——「答对」= **中性墨 `--ink-strong` + 勾形几何**、「答错」= `--role-red`（语义不变）；绿此前作为**现状兼容例外**登记在本表，**本轮实现时整体移除，例外不再保留**（练习页选项正确环也一并改掉）；权威表**不新增绿 token**，落地见 tasks 4.4 |
| CD-073 | `workbench/server/static/workbench.css`（日历 5 档蓝）、`workbench/data/records.py` | 日历的 5 档强度**没有图例**，阈值只活在代码里；用户无法把格子深浅读成「几次」 | `openspec/specs/workbench-ui/spec.md`（记录中心日历条款） | spec delta | 中 | spec owner 明确 5 档强度的区间阈值（这本身是 spec 变更，不能只改 CSS）并要求提供图例 |
| CD-074 | `workbench/server/static/workbench.css`（`.record-activity-day`） | 作答日历**没有「今天」，也没有月份刻度** | `openspec/specs/workbench-ui/spec.md`（日历视图条款） | spec delta | 低 | spec owner 确认日历的「今天」标记与月份刻度是否为必需可见信息 |
| CD-075 | `workbench/server/static/workbench.css`（日历容器） | 日历与摘要的 ARIA 标在**无 role 的容器**上（`aria-label` 挂在无语义 div 上），屏幕阅读器得不到网格语义 | `openspec/specs/workbench-ui/spec.md`（可访问性条款） | spec delta | 中 | spec owner 明确日历的无障碍语义（网格/列表），实现再改 DOM 角色 |
| CD-076 | `openspec/specs/workbench-ui/spec.md:946-948` vs `workbench/server/records.py` | spec 列了记录中心四个视图；实现里**视图切换控件为 0 个**（实测页面无 `table`、无排序/筛选/分页控件） | `openspec/specs/workbench-ui/spec.md:946-948` | spec delta | 中 | spec owner 明确视图切换与（未来的）排序/筛选/分页是否属契约；若要加，须先补 spec 场景 + 登记 `docs/ACTION-GRAPH.md` + 补 `docs/PRODUCT-MANUAL.md` §7.1.2 |
| CD-077 | `workbench/server/records.py`（记录页为空态） | 记录页**没有出站动作**（无「去练习」按钮），与其它页面的空态形态不一致 | `docs/PRODUCT-MANUAL.md` §7（记录中心是只读历史页） | 产品决策 | 低 | 产品定记录页是否允许出站；允许则须先落 spec + 登记 `docs/ACTION-GRAPH.md` |
| CD-078 | `workbench/server/records.py`（作答明细组头） | 日期组头只显示日期；若要显示「当天 N 条」是新增一个展示数字 | `docs/PRODUCT-MANUAL.md` §7.1.2 | 产品决策 | 低 | 产品定是否显示条数；本变更 tasks 19 只做日期分组，不显示条数 |
| CD-079 | `openspec/specs/workbench-ui/spec.md:979-1000` vs `workbench/server/records.py`（作答摘录） | 「Problem fields render math wherever they render text」当前限定 **problem field**；`answer_text` 是**学习者作答**，严格说不在该需求域内，但记录页仍在渲染公式 | `openspec/specs/workbench-ui/spec.md:979-1000` | spec delta | 低 | 契约责任人明确 `answer_text` 是否纳入该需求域；不纳入则另立「记录页与练习页渲染一致性」条目 |
| CD-080 | `workbench/server/static/workbench.css:1211` 与 `workbench/server/static/workbench.js:1052,1077` | `graphSyncScope()` 是**空函数**（`function graphSyncScope() {}`），却在 `workbench.js:1052` 被调用 —— 作用域同步是死的 | `openspec/specs/workbench-ui/spec.md`（图谱与壳层的同步语义） | 产品决策 | 低 | 图谱 change owner 决定该函数是「待实现」还是「历史残留可删」；本变更按 A-8 不碰图谱，只登记 |
| CD-081 | `workbench/server/static/workbench.css:1797`（`.legend i.rel { background: #aaa399; }`） vs `workbench/server/static/graph-renderer.js:19`（`related: [117/255, 112/255, 104/255]` = `#757068`） | 图例「相关」色块 `#aaa399` 与 WebGL 实际画出的关系线色 `#757068` **不一致**（其余 4 类 prereq/apply/contrast/legacy 的图例色与渲染色逐值相同） | `openspec/specs/workbench-ui/spec.md`（图例必须描述当前视图实际使用的区分） | openspec change | 中 | 图谱 change owner 统一图例色与渲染色；本变更按 A-8 不碰图谱区，只登记 |
| CD-082 | `workbench/server/static/workbench.css:1786-1799` | 图例容器 `font-size: 9px`、色 `#7e848d`（对比度不足），与站点其它字号体系无关联 | `openspec/specs/workbench-ui/spec.md`（正文级文字可读性） | openspec change | 低 | 图谱 change owner 在节点视觉重设计时把图例纳入字号与灰阶体系；本变更不碰 |
| CD-083 | `workbench/server/static/workbench.css:1505-1518`、`:1786-1799`、`:1677` 等 20+ 处 | 图谱皮肤的**通用类名**（`.label`/`.meta`/`.chip`/`.hint`/`.controls`/`.legend`/`.toast`/`.floating`/`.seg`）作用域是全页，与壳层同名类互相污染 | `openspec/specs/workbench-ui/spec.md:10-42`（三栏壳层的类名作用域） | openspec change | 中 | 独立 change：把 `workbench.css:1499-1903` 的通用类名限定为 `.graph-shell` 前缀或重命名为 `.graph-*`；本变更按 A-8 不碰图谱区 |
| CD-084 | `workbench/server/app.py:214-230` | 静态资源**无缓存策略**（无 `Cache-Control` / `ETag`），CSS 改动可能到不了用户 | `docs/ARCHITECTURE.md`（前端资源装载策略） | openspec change | 中 | 本变更 tasks 1.4 用 URL 版本化（`pages.py:1101-1103` 风格）保证新样式到达用户；服务端缓存头作为后续独立 change |
| CD-085 | `workbench/server/static/workbench.css:157` | `#layout` 固定 `280px \| 1fr \| 420px`；1024px 视口下中栏只剩 **324px**（1024−280−420），抽屉折叠断点却是 1023px → 1024–1279px 是「三栏都挤」的死亡带 | `openspec/specs/workbench-ui/spec.md:10-42`（三栏壳层几何） | 产品决策 | 高 | 产品定 1024–1279px 档是「右栏改抽屉」还是「压缩两栏宽度」；两种都改导航结构/宽度，必须先落 spec |
| CD-086 | `workbench/server/static/workbench.css:1123`（`:focus-visible` 焦点环） vs `:338`、`:427`、`:833` | 焦点环写得很好，却被三处更高特异性的 `outline: none` 压掉（`select:focus` 0,1,1 > `:focus-visible` 0,1,0；`textarea:focus, input:focus` 同；`#answer-box:focus` 1,1,0 最强）→ 运行时实测聚焦 `<select>` 时 `matches(':focus-visible')===true` 而 `outlineStyle==="none"`。受影响：8 个 `<select>`、9 个 `<input>`、6 个 `<textarea>`，包含顶栏章透镜等全部主路径 | `openspec/specs/workbench-ui/spec.md`（可访问性：键盘焦点必须可见） | openspec change | 高 | 本变更 tasks 1.4 Step 3e + `acceptance.md` §3.1 焦点可见性走查：提高 `:focus-visible` 特异性或改这三处的焦点样式，不靠 CSS 掩盖 |
| CD-087 | `docs/GLOSSARY.md:370-374`「主题偏好 / Theme preference」 | 词条写「默认跟随系统」，但**没有写「学习者显式选择优先」**这一层；`decisions.md` A-11 已裁决「显式选择优先、无已存偏好时跟随系统」 | `docs/GLOSSARY.md:370-374`；`decisions.md` A-11 | docs/GLOSSARY.md | 高 | 本变更 tasks 28 契约同步时把 A-11 的三层优先级（显式选择 > 已存偏好 > 系统）写进词条，与 `docs/PRODUCT-MANUAL.md:522` 逐字对齐 |
| CD-088 | `docs/PRODUCT-MANUAL.md:522` vs `design.md:684`、`tasks.md:44,122` | 手册承诺「默认跟随系统」，而设计件明写「**不使用** `prefers-color-scheme` 兜底（手动开关是定案）」 | `docs/PRODUCT-MANUAL.md:522` | docs/GLOSSARY.md | 高 | 以 A-11 裁决为准：手册与设计件都改成「显式选择优先；无已存偏好时跟随系统」，三处逐字对齐 |
| CD-089 | `workbench/server/static/workbench.css`（`loading`/`spinner`/`skeleton`/`aria-busy` 全仓 0 命中） | **加载态完全不存在**：等待期间用户只看到按钮变灰（`disabled`），看不到「在动」；`aria-busy` 全仓 0 处 | `openspec/specs/workbench-ui/spec.md`（等待期间的用户可感知反馈） | spec delta | 中 | spec owner 明确全局等待策略；本变更 tasks 21 只在已知内容形状的区域用骨架屏 |
| CD-090 | `workbench/server/static/workbench.css:1006`（`.inline-error`） | 错误态只有一行红字，无结构；空态是普通段落（CD-060）、加载态缺失（CD-089）→ 三态缺二 | `openspec/specs/workbench-ui/spec.md`（错误呈现） | spec delta | 中 | spec owner 明确错误态的结构化要求（本变更 tasks 16/19 只做表现层，不改错误文案语义） |
| CD-091 | `workbench/server/static/workbench.css:416-428`（输入类基础规则）、`workbench/server/pages.py:62,263,397,668` | 原始 `<select>` / checkbox / radio 直接暴露在界面里（顶栏章透镜、目标类型、排序、运行中发送方式、自评开关）；`grep -c "appearance" workbench.css` = **0** —— 全站没有任何 `appearance:none`，控件外观完全交给浏览器 | `openspec/specs/workbench-ui/spec.md`（界面控件形态未约束，但用户可感知） | 产品决策 | 中 | 产品定原生控件是否统一外观；定后由本变更 tasks 11/15/16 的自绘控件任务落地，形态变更须同步 `docs/PRODUCT-MANUAL.md` |
| CD-092 | `workbench/server/static/workbench.css`（12 个 z-index 值）vs `workbench/server/static/workbench.css:1780`（`.legend{z-index:7}`）与 `:1798`（`.zoom{z-index:8}`） | 浮层/抽屉/弹层的叠放次序只靠作者当时的随手数值，图例与缩放条各占一档 | `openspec/specs/workbench-ui/spec.md:10-42` | openspec change | 低 | 本变更 tasks 1.4 Step 3e 建 `--z-*` 层级表并全量替换 |
| CD-093 | `workbench/server/pages.py:955`、`:1003-1004`、`:978` vs `workbench/server/static/workbench.js:443` | 服务端 Markdown 渲染器**丢代码块语言标记**（无 `class='language-xx'`）、标题层级 `+1` 偏移（`pages.py:978` `level = len(heading.group(1)) + 1`）；客户端（`workbench.js:443`）`#`→h1，服务端 `#`→h2 —— **两套渲染器对同一份 Markdown 产出不同 HTML** | `FILE_CONTRACT.md`（中间工件与渲染契约）；`openspec/specs/workbench-ui/spec.md`（内容渲染一致性） | spec delta | 高 | 本变更 tasks 7 做 parity 测试并**先记录现状差异**，再改渲染器；改动会改变已入库正文的渲染结果，属内容契约变更，须先落 spec |
| CD-094 | `workbench/server/pages.py:781`（`_MATH_RE = re.compile(r"\$\$([\s\S]+?)\$\$\|\$([^$\n]+)\$", re.MULTILINE)`） | `\$` 未被转义 → `\$5 and \$6` 里的 `$5 and $` 会被当成行内公式 | `openspec/specs/workbench-ui/spec.md:979-1000`（内容渲染契约） | spec delta | 中 | 修它会改变**已入库内容**的渲染结果（虽然原结果显然是 bug）→ 契约责任人先确认，再由本变更 tasks 7 落 parity |
| CD-095 | `workbench/server/pages.py:1090-1093` | 图片是「裸奔」的：内联、无图注、`alt` 多为空、无加载失败态 | `openspec/specs/workbench-ui/spec.md`（知识点正文媒体契约） | spec delta | 中 | spec owner 明确媒体契约（块级/图注/alt 必填/失败态）；本变更 tasks 7 只补失败态表现层 |
| CD-096 | `workbench/server/pages.py`（hub 卡片） | 首页 22 张卡片完全等权，各自带 34% 死区；三个计数与普通正文同字号同灰 | `openspec/specs/workbench-ui/spec.md`「Workspace card information hierarchy」 | openspec change | 中 | 本变更 tasks 24 建 hub 卡片信息层级；计数是否拆成独立元素由 tasks 24 落地 |
| CD-097 | `workbench/server/pages.py:669`（`练习显示自评`） vs `openspec/specs/workbench-ui/spec.md:1051`（`练习与组卷显示自评`）、`docs/GLOSSARY.md`「工作台设置视图」、`docs/PRODUCT-MANUAL.md:528` | 左栏自评开关标签：spec 与两份文档都用「练习与组卷显示自评」，代码用简称「练习显示自评」 | `openspec/specs/workbench-ui/spec.md:1051` | openspec change | 中 | 按 spec 改代码（`copy-table.md` D-01 已定稿为「练习与组卷显示自评」）；**同 PR 必须同步** `docs/PRODUCT-MANUAL.md:246/256/266/278/282/288` 六处引用 |
| CD-098 | `workbench/server/experience_page.py:62-64`（`暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。`） vs `openspec/specs/practice-experience/spec.md:16` | spec 要求页面显示 `暂无经验总结` 且「an action to create one」；实现显示的是带教学后缀的整句，后缀不在契约内 | `openspec/specs/practice-experience/spec.md:16` | openspec change | 中 | `copy-table.md` E-03 已定稿为 `暂无经验总结`（只删后半句、前缀必须留）；由本变更 tasks 26 文案清理落地 |
| CD-099 | `workbench/server/records.py:131`、`:187`（`最近正确率`/`客观题正确率`） vs `docs/GLOSSARY.md:610` | 记录中心打印「正确率」，而 GLOSSARY 把「正确率」列为 `_Avoid_`（未经定义前不使用具体数字承诺） | `docs/GLOSSARY.md:608-611` | docs/GLOSSARY.md | 高 | 与 CD-065 同源：先在 GLOSSARY 建立「正确率」定义（写清分母），或按 `copy-table.md` R-28/R-41 改成「最近判定 N/M」「客观题判定 N/M」 |
| CD-100 | `workbench/bridge/conversations.py:129-140`（`list_sessions(pool, limit=None)` 返回全部） vs `openspec/specs/workbench-ui/spec.md:252` | spec 写 "up to ten recent conversations"，实现返回**全部**会话 | `openspec/specs/workbench-ui/spec.md:252` | spec delta | 中 | spec owner 或 DATA_MODEL 二选一定权威，然后改实现（`workbench/server/api.py:800-802` 的消费点同步） |
| CD-101 | `openspec/specs/workbench-ui/spec.md:325-336`（"compact history-row **menus**"） vs `workbench/server/static/workbench.js:4400-4440` | spec 写的是**菜单**，实现是**行内图标按钮** | `openspec/specs/workbench-ui/spec.md:326` | spec delta | 低 | spec owner 明确是 menu 还是行内按钮；实现改动属 Agent 右栏任务范围 |
| CD-102 | `workbench/bridge/conversations.py:177-249` | 消息对象只有 `role/content/turn_id/submission_id/status/partial`，**没有时间戳**（无 `created_at`），也没有编辑/删除接口 | `docs/DATA_MODEL.md`（消息字段语义与 writer 边界） | docs/DATA_MODEL.md | 中 | 若要消息级时间戳或角色标签，须先在 DATA_MODEL 登记新字段与权威时间源；编辑/删除属新增能力，另立 change |
| CD-103 | `docs/GLOSSARY.md:642-645` vs `docs/design/AGENT-UI-V1.md:43` | 审批门「临时替换普通输入框」被写成现行 v1 行为（GLOSSARY 与设计稿一致），但它把用户能打字这件事悄悄拿走了 —— 契约与产品取向之间的张力未裁决 | `docs/GLOSSARY.md:642-645`；`docs/design/AGENT-UI-V1.md:43` | 产品决策 | 中 | 产品裁决审批门是否与 composer 并存；要并存则先改 GLOSSARY 词条 + `openspec/specs/ai-teacher-bridge` |
| CD-104 | `openspec/specs/workbench-ui/spec.md:533-541` vs `workbench/server/static/workbench.js`（抽屉模式 `#ai-messages` 高度实测为 0） | 窄屏抽屉里 composer 随文档流滚走，没有「消息区独立滚动 + 输入框常驻」 | `openspec/specs/workbench-ui/spec.md:533-541` | spec delta | 中 | spec owner 补窄屏抽屉场景；实现属本变更 tasks 25 Agent 右栏 |
| CD-105 | `openspec/specs/workbench-ui/spec.md:328`（"chat view SHALL remain conversation-first … SHALL NOT crowd that view"） | 「发送方式」控件当前占据 composer 一行，是高频输入区的低频设置 —— 与该条款的精神有张力 | `openspec/specs/workbench-ui/spec.md:328` | spec delta | 低 | 契约责任人明确该条款是否覆盖「发送方式」控件的位置；本变更 tasks 25 可把它降成安静标签 |
| CD-106 | `workbench/server/static/workbench.css:647-652,729` vs `workbench/server/static/agent-ui.css:203-212` | 同一组控件（执行计划 / 工具调用卡）**两套参数并存**：`workbench.css` 写死 `#171717` / `#2457c5` / `border-radius:2px`、完成态 `#b58b00`；`agent-ui.css`（后加载）写 `var(--dsw-border-l2)` / `var(--lk-blue)` / `var(--dsw-radius-md)`、完成态 `var(--dsw-state-success)` —— 后者覆盖前者，改一处不知道改哪一处 | `openspec/specs/workbench-ui/spec.md`（Agent 栏表现）；`decisions.md` A-9（token 唯一真值） | openspec change | 低 | 本变更 tasks 25 清理同源双写（`agent-ui.css` 与 `workbench.css` 择一），并把硬编码色并入权威表命名的 token 族 |
| CD-107 | `workbench/server/static/workbench.css:1-3,30` 与 `workbench/server/static/agent-ui.css:344` | 遗留 token 与样式债：`--dsw-bubble-highlight: #d9e3ff`（`:30`）**定义了但全项目零引用**；`workbench.css:1-3` 的顶部注释自述 token 抄自 "DeepSeek Harness"；`agent-ui.css:344` 另有硬编码 `#fff9df` | `openspec/changes/workbench-visual-language-v2/design.md` D-1（唯一 token 真值）；`decisions.md` A-9 | openspec change | 低 | 本变更 tasks 2.1 别名期把 `--dsw-*` 引用点一起改成别名、删掉零引用 token；清理范围由 tasks 2.3 一次性收尾 |
| CD-108 | `workbench/server/static/workbench.css:1034`（`li.muted`） | `.muted` 类**名不副实**：名字暗示弱化文本，规则却只对 `<li>` 生效，其余 46 处 `<p>` 空态拿不到任何样式 | `docs/GLOSSARY.md`（次要信息的视觉层级） | openspec change | 中 | 与 CD-060 同案：补齐规则或换名；两者都要求 47 处标记同步改，改动必须与本变更 tasks 16/19 同批 |
| CD-109 | `workbench/server/static/workbench.css:1083-1104`、`:1008`、`:515-521`、`:504-505`、`:1166` | 已确认的**死/化石 CSS 规则共 5 组 11 条**（建议行 `.staged-*`、`.kp-practice-action`、`.problem-topic*`、`.knowledge-list .score/.reasons`、`.knowledge-row label`） | `openspec/specs/workbench-ui/spec.md`（不存在这些元素的条款） | openspec change | 中 | 本变更 tasks 2.3 别名期 / tasks 18 知识点页改造时统一删除；每删一组都要确认没有 JS 读同名 class（`getPropertyValue` 已核实 0 命中） |
| CD-110 | `workbench/server/static/workbench.css:1895`（`.paper-options label` 的 `border: 1px solid var(--dsw-border, #ddd)`） | 依赖未定义变量（CD-012），且 fallback `#ddd` 与纸面体系无关 —— 同一族里出现第三个边框值 | `openspec/specs/workbench-ui/spec.md:731-736` | openspec change | 中 | 本变更 tasks 2.2 补齐 + tasks 3.3 统一控件边界 |
| CD-111 | `workbench/server/static/workbench.css:1420-1421`（`.record-activity-day { aspect-ratio: 1; }`） | 作答日历格子是**正方形**（`aspect-ratio: 1`）；若采用「强度双编码（高度也编码）」的日历形态，格子必须改为显式行高 | `openspec/specs/calendar-workload/spec.md`（日历强度编码方式） | spec delta | 中 | spec owner 明确日历是「单编码（填色）」还是「双编码（填色 + 高度）」；双编码是 spec 变更，不能只改 CSS |
| CD-112 | `workbench/server/static/workbench.css:1372-1380` | 记录页 4 张统计卡共用同一结构，`.record-day-bar.empty { border:0; background:transparent }`（`:1399`）让空柱与「不存在」视觉同义 | `openspec/specs/workbench-ui/spec.md:946-948`（记录中心四视图与统计区） | openspec change | 中 | 本变更 tasks 19 改成「1 主 3 次」的仪表盘卡片流 |
| CD-113 | `workbench/server/static/workbench.css:1164`、`:1253`、`:1280` | 记录页与练习页的黄/红硬编码值与全站语义色不同源 | `openspec/specs/workbench-ui/spec.md:731-736` | openspec change | 中 | 本变更 tasks 4.2 收编（见 CD-015/CD-017） |
| CD-114 | `workbench/server/pages.py:396`、`:377-378`、`:340-342` | 知识点列表与详情页对**同一知识点**给出的提醒可以不一致（两处判据来源不同） | `docs/GLOSSARY.md:477-481` | docs/DATA_MODEL.md | 高 | 与 CD-063 同源：DATA_MODEL 裁定判据权威来源，GLOSSARY 补判据来源 |
| CD-115 | `workbench/server/pages.py:165`、`:204`、`:256`、`:345`、`:476`、`:544`、`:561`、`:732`、`:736`、`:766`、`:776`、`:1136` | 12 处 `<p class='muted'>` 空态散落在练习页/记录页/知识点页/对话栏，其中 `:544`（题数）、`:561`（空态说明）、`:165`（进行中元信息）以**正文级纯黑 14px** 渲染 | `docs/GLOSSARY.md:340-348`（次要信息层级） | openspec change | 中 | 与 CD-060 同案：空态组件化时统一改这 12 处标记 |
| CD-116 | `workbench/server/static/workbench.css:152-153`、`:157` | 桌面端右栏不可手动收起（CD-029）与三栏固定几何（CD-027/CD-085）叠加，Agent 栏在 1024–1279px 无法让位 | `openspec/specs/workbench-ui/spec.md:10-42` | 产品决策 | 中 | 与 CD-029/CD-085 同一件：产品定窄桌面档的壳层形态，spec owner 落条款 |
| CD-117 | `workbench/server/static/workbench.css:733`、`:1126-1131`（`transition/animation: none !important` 的全局降级闸门） | 全局 reduced-motion 闸门用 `!important`，与「用户显式选择开启动效」无法共存（显式开也要被闸门压死） | `openspec/changes/workbench-visual-language-v2/specs/workbench-settings/spec.md:143`（显式选择优先）vs `specs/workbench-ui/spec.md:102`（系统 reduce 与用户关闭并列为无条件降级触发） | spec delta | 高 | 所有者裁决 A-2 已定「显式选择优先」；spec owner 须把 `workbench-ui` delta 的降级触发条件改成「用户未做选择且系统要求 reduce」，两份 delta 逐字对齐（裁决已完成，措辞对齐未落） |
| CD-118 | `openspec/changes/workbench-visual-language-v2/design.md:434-435` vs `specs/workbench-ui/spec.md`（stem 字号） | 所有者裁决 A-6 定「题面与正文同档 17px / 1.75 / 38em」，design.md D-5 已按此修正，但 spec delta 措辞仍可能停留在旧值 | `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md` | spec delta | 中 | 裁决已完成，剩「措辞对齐」：spec owner 在归档前把 `workbench-ui` delta 的 stem 字号逐字改为 17px / 1.75 / 38em |
| CD-119 | `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`（章节透镜条款） | `openspec/specs/workbench-ui/spec.md:829-838` 明写章节控件 "SHALL show **no** per-chapter statistics, counts, or selection reasons"；而本变更的 `decisions.md:641` 收口基线表、`tasks.md:153`、`design-notes/component-spec.md:1748` 三处工件**仍带「知识点计数」** → 照工件实现即直接违反现行 spec | `openspec/specs/workbench-ui/spec.md:829-838` | spec delta | 高 | 三处一并删掉「计数」只保留章节名；若确实要计数，必须走 MODIFIED 既有 Requirement 的流程；**本轮只登记不删** |
| CD-120 | `openspec/changes/workbench-visual-language-v2/decisions.md:822-823` vs `openspec/changes/graph-node-visual-language/design.md:754-778` | A-8 把「亮色主题下图谱必须逐像素不变」定为**约束图谱 change** 的硬约束，图谱 change 单方面宣布该基线「根本不存在」并退役旧基线图；图谱 change 又**没有 `acceptance.md`** 承接门禁 | `decisions.md:822-823`（A-8 例外条款） | 产品决策 | 高 | 所有者 A-12 已裁决「图谱 change 必须自带门禁」；落地动作：把 A-8 的例外条款改写为「亮色**结构**不变（节点数/位置/边集合/相机），**画法**可变」，并在图谱 change 补 `acceptance.md` 承接结构不变断言与差异区域遮罩协议 |
| CD-121 | `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md:52` 与 `:1592` | 这两处仍陈述「图谱专用纸面 token 有三个名字……现 `night-paper-tokens.md` §3.1 的名字是 `--surface-graph-sheet`」，而权威表 `night-paper-tokens.md:159` **已经**按 A-16 改成 `--surface-sheet` → 隔离件里的事实陈述已过期 | `decisions.md` A-16（`--surface-sheet` 是唯一名字） | openspec change | 中 | 图谱 change owner 按 A-16 回填 `graph-isolation.md` 的两处事实（保留 Q-6 的历史记录但标注「已裁」），避免下一轮照旧名再裁一次 |
| CD-122 | `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md:1640`（Q-1） | G-5 的比对范围（整页 / 画布区域 / 抽样）**未裁决**；裁决主体已移交给图谱 change | `design-notes/graph-isolation.md:1634,1640` | 产品决策 | 中 | 所有者裁决 A-14 已定「取整页（最严）+ reduced-motion 下比对 + 基线不可复现才降级并留痕」；落地动作：图谱 change owner 承接并把 A-14 写进其 `acceptance.md` |
| CD-123 | `openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md:216` vs `openspec/changes/workbench-visual-language-v2/decisions.md` A-17 | 权威表写 `--surface-sheet` = 亮 `#fffdf7` / 夜 `#fffdf7`（「**两主题同值**」「⚠️ **不进夜纸值集**」）；而 A-17 裁决「`--surface-sheet` 是图谱自己的纸面 token，**自己带两套值**：亮 `#fffdf7`、**夜 `#1c1a16`**」—— 同一个 token 的夜纸值有两处不同答案 | `openspec/changes/workbench-visual-language-v2/decisions.md` A-17；`design-notes/graph-isolation.md:1645`（Q-6 的残余） | openspec change | 高 | 权威表 owner 按 A-17 把 `night-paper-tokens.md:216` 的夜纸列改为 `#1c1a16`、删掉「不进夜纸值集」；图谱 change 承接后按 A-12 的结构不变量门禁复核亮色结构不变 |
| CD-124 | `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md:1646`（Q-7） | 图谱路由钉回的具体取值未定：用「新层浅色值」还是「图谱今天的值」 | `design-notes/graph-isolation.md:1646,1500` | 产品决策 | 中 | 图谱 change owner 裁决；`design-notes/graph-isolation.md:1500` 已给出逐项对照表可直接采信 |
| CD-125 | `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md:1647`（Q-8） | 任务 11.3–11.5 与 12.1（左栏/顶栏 DOM 改造）是否给图谱页留旧外壳分支**未裁决**；若不留，则 G-5 的 R-1 整页口径在结构上不可能达成，必须走 R-2 + R-3 | `design-notes/graph-isolation.md:1647` | 产品决策 | 中 | 图谱 change owner 裁决（与 Q-1 绑定）；A-14 已给出「最严优先、不可复现才降级」的顺序 |
| CD-126 | `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md:1641`（Q-2） | 「图谱页是否参与夜纸主题」**已由 A-8 关闭**（结论：跟随夜纸，但**在图谱 change 里做**）；Q-2 仍以「待裁决」形态留在本文件 | `design-notes/graph-isolation.md:1641` | openspec change | 低 | 落地动作：图谱 change owner 把 Q-2 标为「已关闭（由 A-8）」，避免下一轮重复裁决 |
| CD-127 | `docs/GLOSSARY.md:444-450`「建议 / Suggestion」+ `:603-606`「每日计划 / Daily Plan」 vs `workbench/server/pages.py:154`、`:258` | 两个词条都有，但**没有界面出口**：建议行的纯函数在跑却从不渲染（CD-038）；而 GLOSSARY:603 明写每日计划「不再作为独立卡片展示」，实现里仍有 `<section id='daily-plan'>`（`pages.py:258`）与「长期与阶段目标」卡片 | `docs/GLOSSARY.md:444-450,603-606` | docs/GLOSSARY.md | 高 | 契约责任人裁定两条词条的可见出口：建议行落地（见 CD-038）或两条词条改写为「内部来源，不单独展示」 |
| CD-128 | `openspec/changes/workbench-visual-language-v2/design-notes/copy-table.md:65-77` | `copy-table.md` 仍按 A-7 的前提写「图谱页观感**在两主题下**必须与现在完全一致」并以 A-7 立论；而 A-8 已把夜纸适配移交图谱 change —— **依据过期**（结论仍成立：图谱文案一条不改） | `decisions.md` A-7 与 A-8 的关系 | openspec change | 低 | 落地动作：本变更的 `copy-table.md` 改写依据为 A-8 之后的读法（结论不变，只换依据） |

| CD-129 | `openspec/changes/workbench-visual-language-v2/design-notes/layout-spec.md:1370,1375,1398,1788` | layout-spec 的 `:55` 已把「右栏贴底输入框用 20px」标注为**已作废**（A-15 的执行只落了一半），但同一文件里仍有四处未改：`:1370`（输入区圆角 20px）、`:1375`（圆角 **20px**）、`:1398`（仍写「输入区圆角 20px 是唯一一处超出 12px 的圆角」）、`:1788`（自带的漂移表里仍列着「输入区圆角 20px vs 12px」待办） | `decisions.md` A-15（**裁决：12px 统一**，layout-spec 的 20px 作废）；`docs/GLOSSARY.md:340-348` | openspec change | 高 | 落地动作：把 `layout-spec.md` 的四处 20px 全部改为 12px（composer 的大体现在高度与内边距，不在圆角），并清掉 `:1788` 自带的漂移表条目；由本变更 tasks 11/25 收尾 |
| CD-130 | `openspec/changes/graph-node-visual-language/design.md:102,130,131,132`（`.label` 11px） vs `openspec/changes/graph-node-visual-language/proposal.md:68`（12px） | 同一个「标签屏幕像素字号」裁决在图谱 change 的两个工件里分别是 **11px** 与 **12px**；spec 未钉数值 | `decisions.md` A-15（**裁决：12px，以 proposal 为准**） | openspec change | 中 | 落地动作：图谱 change owner 把 `design.md` 的 11 改为 12，并在 spec delta 里把数值钉死（否则又是一个「同一裁决两个数」的漂移） |
| CD-131 | `openspec/changes/workbench-visual-language-v2/HANDOFF.md:22`、`:44-52` | 交接件的裁决表**停在 A-6**（`:22` 写「追加裁决 A-1…A-5」，`:47-52` 只列到 A-6），缺 A-7…A-16 | `decisions.md` A-7…A-16 | openspec change | 中 | 落地动作：本变更 tasks 27.3 更新 `HANDOFF.md`，补齐 A-7…A-16 与 G-1…G-24 的索引，并在同处写「本表登记 N 条漂移」的提示 |
| CD-132 | `openspec/changes/workbench-visual-language-v2/tasks.md:254`（28.5） | 28.5 仍要求「**同时校正** `design.md` D-5 与 spec delta 关于 stem 字号的冲突」——而 A-6 已裁决「题面与正文同档 17px / 1.75 / 38em」，`design.md:434-435` 早已按此修正，任务描述的是**已不存在的问题** | `decisions.md` A-6 | openspec change | 低 | 落地动作：把 28.5 拆成两件——① D-14 的 5 档日历阈值进 spec（未做）；② stem 字号措辞对齐（剩余动作），避免下一轮以为还要重新裁决 |
| CD-133 | `openspec/changes/workbench-visual-language-v2/decisions.md:1008-1020`（A-13） | A-13 的事实前提「`component-spec.md`（**636 处**）与 `motion-spec.md`（**92 处**）用了第三套 `--lk-*`」已**过期**：实测当前树 `component-spec.md` 命中 `--lk-*` **0 处**、`motion-spec.md` 仅 **2 处**（都是解释性提及，非 token 引用） | `decisions.md` A-13 自身的事实前提 | openspec change | 低 | 落地动作：把 A-13 的计数改写为当前值并注明「已按 A-13 执行完毕」；账本里的旧计数会误导下一个读者 |
| CD-134 | `openspec/changes/workbench-visual-language-v2/decisions.md:1064-1080`（A-16） vs `design-notes/night-paper-tokens.md:213` vs 同文件 A-17 | **账本内部措辞互相矛盾**：A-16 写「`--surface-graph-sheet` 与 `--surface-card` **全部退役**，不得再用」；但权威表 `night-paper-tokens.md:213` 仍把 `--surface-card` 定义为**全站卡面 token**（亮 #fffdf7 / 夜 #232019，`component-spec.md` 引用 **38 处**），而 A-17 又明确「`--surface-sheet` **不复用** `--surface-card`」→ 照 A-16 的字面执行会把全站卡面 token 一起删掉 | `decisions.md` A-16 vs A-17；`design-notes/night-paper-tokens.md:213` | openspec change | 高 | 账本 owner 改写 A-16 的措辞（把「全部退役」限定为「**图谱专用纸面 token 这一语义**」），并显式标注 A-17 取代 A-16 的该句；**不得**按 A-16 字面把 `--surface-card` 全删 |
| CD-135 | `openspec/changes/workbench-visual-language-v2/design-notes/asset-spec.md:53`、`:1527` | 资产规范**禁止引用 `--surface-graph-sheet`**（已按 A-16 退役的死名） | `decisions.md` A-16（`--surface-sheet` 是唯一名字） | openspec change | 低 | 落地动作：把 `asset-spec.md` 的禁令改成「不得引用图谱专用纸面 token（唯一名 `--surface-sheet`）」，避免禁令指向不存在的名字 |
| CD-136 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:800` | 多邻国 **XP / 倍率 / 双倍 XP 时段**（`SessionCompleteModel.baseXP/bonusXP/xpMultiplier`、`core/xpboost/`、`you_earned_an_xp_boost`）被明确列为「不建议照搬」：把「理解」量化成货币，鼓励刷量而非深读 | `docs/design/philosophy.md:8`「不是帮你跳过源材料，是帮你回到源材料」；`docs/design/philosophy.md:114`（质疑 edtech「参与度 = 动量」的度量基础）；`docs/GLOSSARY.md:608-611`（「覆盖」不承诺百分比） | 产品决策 | 中 | 所有者确认「不做游戏化外层经济」是**长期产品取向**；确认后把该取向写成 GLOSSARY 的一条词条（否则每一轮设计都要重新讨论一次 XP/倍率） |
| CD-137 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:801` | 多邻国 **COMBO 连击 / Max combo**（`GradingRibbonShowType.COMBO_RUN`、`numCorrectInARow(Max)`、`combo_lost` = "COMBO LOST"）不建议照搬：连击奖励「连续答对」这一**行为**而非「读懂了」这一**结果**，且 `combo_lost` 制造损失感 | `docs/design/philosophy.md:8`、`:114`；`decisions.md` 5.4「连对升级」（本项目只做**正向**的连对升级，不做 combo 断裂惩罚） | 产品决策 | 中 | 所有者确认「连对升级」与「COMBO 连击」的边界（是否允许断裂提示）；确认后写进 `decisions.md` 5.4 的实现约束 |
| CD-138 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:802` | 多邻国 **心 / 能量限流**（`LimitedHeartsView`、`EnergyConfig`、`you_an_out_of_energy`）不建议照搬：惩罚性限流 | `docs/design/philosophy.md:8`（工具不该阻止你读） | 产品决策 | 中 | 所有者确认「不做任何形式的限流/能量闸门」；确认后写进 GLOSSARY 的一条否定式词条 |
| CD-139 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:803` | 多邻国 **连胜 streak / 冻结卡 / 补签**（`UserStreak`、`StreakData(length, xpGoal)`、`streakFreeze/`、`streakRepair/`）不建议照搬：最强的时间型绑架，本质是「每日 XP 配额」 | `docs/design/philosophy.md:8`、`:114`；`openspec/changes/workbench-visual-language-v2/decisions.md:686`（5.2b 只承诺「连续学习天数」且**无现成数据源**） | 产品决策 | 高 | 所有者定「连续学习天数」是否要（当前无数据源，见 CD-155）；定后再决定要不要「冻结卡 / 补签」这类续命机制。**本条与 CD-155 是同一件的两面** |
| CD-140 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:804` | 多邻国 **每日目标 / 任务 / 奖励箱**（`GoalsGoalSchema.Category`、`DailyQuestType`、`daily_goal_met`）不建议照搬：每日配额制，把一次深读变成一次打卡 | `docs/design/philosophy.md:8`、`:114`；`docs/GLOSSARY.md:603-606`「每日计划」（是**按需提示**，不是配额） | 产品决策 | 中 | 所有者确认「目标」是长期/阶段目标（现状）而非每日配额；确认后在 GLOSSARY 的「目标」词条里写清二者之别 |
| CD-141 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:805` | 多邻国 **排行榜 / 联盟 / MVP**（`com/duolingo/leagues/`）不建议照搬：竞争性反馈，与「知识归顺度」光谱的唤醒端冲突 | `docs/design/philosophy.md`（规训自我 vs 唤醒自我的光谱） | 产品决策 | 中 | 所有者确认「不做任何社会比较/排名」；确认后写进 GLOSSARY 的一条否定式词条 |
| CD-142 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:806` | 多邻国 **徽章 / accolade**（`LessonAccoladeType`：`PerfectLesson`/`SuperFast`/`HighScorer`/`MistakeEraser` 等）不建议照搬；`SuperFast` 明确奖励**快**，与精读相悖 | `docs/design/philosophy.md:8`；`decisions.md` 3.4（不加第五色，「已掌握/正确」用文案与几何表达） | 产品决策 | 中 | 所有者确认「不做徽章体系」；确认后写进 GLOSSARY 的一条否定式词条 |
| CD-143 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:807` | 多邻国 **宝石 / 掉落 / 抽奖**（`core/rewards/`、`GemsRewardState$RewardType`、`you_earned_gems`）不建议照搬：抽卡式随机奖励，把学习变成博彩 | `docs/design/philosophy.md:8` | 产品决策 | 中 | 所有者确认「不做随机掉落/开箱」；确认后写进 GLOSSARY 的一条否定式词条 |
| CD-144 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:808` | 多邻国 **广告位插播**（`SessionVisualState.ExplanationAd`、`NetworkInterstitialAdFragment`）不建议照搬：打断学习闭环 | `docs/design/philosophy.md:8`（工具应减少障碍） | 产品决策 | 低 | 所有者确认「产品内永不做插播位」；确认后写进 GLOSSARY 的一条否定式词条 |
| CD-145 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:809` | 多邻国 **拟人化角色表演 / 动画爆炸**（`core/character/JuicyCharacter`、`GradingRibbonExplosionStyle`）不建议照搬：成本高、对深读无帮助 | `docs/design/philosophy.md`（工具是窗户，不是月亮本身） | 产品决策 | 中 | 所有者确认「不做拟人化角色」；确认后写进 GLOSSARY 的一条否定式词条（现状已有「不用拟人」倾向，但无契约） |
| CD-146 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md:810` | 多邻国 **排行榜式「你比 XX% 的人快」**（`im_learning_multiplierx_faster_than_last_week`）不建议照搬：把学习速度变成社会比较 | `docs/design/philosophy.md` | 产品决策 | 低 | 与 CD-141 合并处理（同属社会比较） |
| CD-147 | `docs/GLOSSARY.md:177-179`「判定 / Verdict」与 `openspec/specs/workbench-ui/spec.md:949`（"honest verdict (对 / 错 / 未判定)"） vs `workbench/server/static/paper-practice.js:581`（`correct: "正确", wrong: "错误"`）与 `:672-673`（`判定：正确` / `判定：错误`） | 判定词**两套写法**：契约侧是「对 / 错 / 未判定」，代码侧是「正确 / 错误」（徽章）与「判定：正确 / 判定：错误」（题面） | `docs/GLOSSARY.md:177-179`；`openspec/specs/workbench-ui/spec.md:949` | docs/GLOSSARY.md | 中 | 统一到契约侧写法「对 / 错 / 未判定」（`copy-table.md` D-03 已判「留」现状并登记）；要统一须先改 GLOSSARY 或 spec → 另案 |
| CD-148 | `openspec/specs/workbench-ui/spec.md:916`（"the card shows `已回滚`"） vs `openspec/changes/workbench-visual-language-v2/design-notes/copy-table.md` W-105 定稿 `入库已回滚` | spec 写「the card shows `已回滚`」，定稿文案是「入库已回滚」——**逐字不等**（含子串，故按「包含」判定可通过） | `openspec/specs/workbench-ui/spec.md:916` | spec delta | 低 | 契约责任人明确该句是逐字要求还是包含要求；若是逐字，W-105 的定稿要改成「已回滚」；若按包含，spec 可不动但应在 spec 里注明 |
| CD-149 | `docs/PRODUCT-MANUAL.md:60`（「点『▶ 添加目标』展开表单」） vs `workbench/server/pages.py:260`（`<summary id='goal-editor-summary'>添加目标</summary>`） | 手册里的「▶」是文档表示「可展开」的记号，界面字面没有这个符号 → 文档与实现的界面文案不一致 | `docs/PRODUCT-MANUAL.md:60` | docs/GLOSSARY.md | 低 | `copy-table.md` D-04 已判「留」；落地动作：把 `docs/PRODUCT-MANUAL.md:60` 的「▶ 添加目标」改成「添加目标」，去掉记号 |
| CD-150 | `docs/PRODUCT-MANUAL.md:184`（建议区的「重新安排」手动重算） vs `workbench/server/pages.py`（练习页无该按钮；仅有 API `POST /api/w/{name}/plan/recalculate`，`workbench/server/app.py:46`） | 手册描述了建议区的「重新安排」**手动重算**按钮，界面上**没有这个按钮**（功能缺失，不是文案问题） | `docs/PRODUCT-MANUAL.md:184` | openspec change | 中 | 提独立 change：补「重新计算」按钮（并入 CD-038 的建议行落地案），或把手册这段改写为「到时自动重算、无手动入口」 |
| CD-151 | `docs/PRODUCT-MANUAL.md:149`（图谱的「清除筛选」按钮） vs `workbench/server/static/workbench.js`（图谱代码里没有该按钮） | 手册描述的图谱「清除筛选」按钮**不存在** | `docs/PRODUCT-MANUAL.md:149` | openspec change | 低 | 图谱范围外（`copy-table.md` G-C3）；归 `graph-node-visual-language` change：补按钮或改手册 |
| CD-152 | `docs/PRODUCT-MANUAL.md:440`（「打开试卷页」） vs `workbench/server/static/agent-ui.js:267`（`link.textContent = "打开组卷页";`） | 试卷工件卡的链接名与手册不一致 | `docs/PRODUCT-MANUAL.md:440` | docs/GLOSSARY.md | 中 | `copy-table.md` D-05 已定稿：按文档改代码 →「打开试卷页」；由本变更 tasks 26 文案清理落地，手册不需改 |
| CD-153 | `docs/PRODUCT-MANUAL.md:142`（本章计数含「**掌握**」的个数）与 `:331`（系统只使用三个词，本章计数是唯一例外） vs `docs/GLOSSARY.md:576-578`（行动提醒 `_Avoid_`：掌握度、分数、调度参数；「其余保持中性（不显示任何掌握断言）」） | 手册承诺知识点页顶部有一条**含「掌握」个数**的计数；GLOSSARY 明写**不显示任何掌握断言**、把「掌握度」列入 `_Avoid_` → 两份职责文件直接矛盾 | `docs/GLOSSARY.md:576-578` | docs/GLOSSARY.md | 高 | 所有者/契约责任人裁决「知识点页计数是否可含掌握数」：含则改 GLOSSARY 的 `_Avoid_`（划出例外），不含则改 `docs/PRODUCT-MANUAL.md:142,331` |
| CD-154 | `docs/PRODUCT-MANUAL.md:142`（知识点页顶部有一条计数） vs `workbench/server/pages.py:401`（`_lens_label(workspace, "本章知识点", "全部知识点")` —— 只有一个**标签**，没有任何计数） | 手册承诺的「本章计数」在实现里**不存在**（只有透镜标签）；`decisions.md:285-286,686` 承诺要落它 | `docs/PRODUCT-MANUAL.md:142` | openspec change | 中 | 本变更 tasks 18（知识点页）落这条计数时，只允许呈现**已有的事实计数**（知识点总数 + 各状态个数），**不得**引入新口径；落地后同步 `docs/PRODUCT-MANUAL.md:142` 的实际形态 |
| CD-155 | `workbench/`（`grep -rn "streak\|consecutive" workbench/` 命中 0） vs `openspec/changes/workbench-visual-language-v2/decisions.md:277,279,686`（5.2b 选定「连续学习天数」但标注「全仓无现成数据源」） | 「连续学习天数」**没有数据源**：无字段、无查询、无派生；口径（哪些行为算「学习日」/ 断一天是否清零 / 跨时区如何取日）**未定义** | `openspec/changes/workbench-visual-language-v2/decisions.md:277,279`；`specs/workbench-ui/spec.md:841`（已声明本 delta 不承诺） | 产品决策 | 高 | 所有者定义口径（哪些行为算「学习日」/ 断一天是否清零 / 跨时区如何取日）；口径未定前**不得由实现期自行发明算法**（tasks 19.4 已明写此约束） |
| CD-156 | `workbench/server/pages.py:247`（目标卡渲染「覆盖进度：」+ `goal.get("coverage_progress")`） vs `docs/GLOSSARY.md:608-611`（「覆盖 / Coverage」明写「规格未定义计算公式」，并把「完成度百分比」列入 `_Avoid_`） | 目标卡**印出了一个公式未定义的数字**（覆盖进度百分比） | `docs/GLOSSARY.md:608-611` | docs/GLOSSARY.md | 高 | 契约责任人定义「覆盖进度」的计算公式并写进 GLOSSARY；或改目标卡不显示该数字。在定义之前，页面上的百分比没有契约出处 |
| CD-157 | `workbench/server/records.py:12-18`（判定徽章三态「未判定 / 对 / 错」） vs `docs/PRODUCT-MANUAL.md:319`（「系统对你的学习状态只使用三个词：重点练习、可以复习、其余保持沉默」） | 记录页的判定徽章用了**第三个词表**（未判定/对/错），与手册承诺的「学习状态三词」不是同一套；且「对/错」是**判定**不是**学习状态**（GLOSSARY:177 明写「判定是一次作答的事实，不是学习状态」） | `docs/PRODUCT-MANUAL.md:319`；`docs/GLOSSARY.md:177-179` | 产品决策 | 中 | 契约责任人确认记录页徽章是「判定」还是「学习状态」：若是判定，徽章应改名或手册补例外；若是学习状态，词表要与三词统一 |
| CD-158 | `workbench/server/records.py:131`、`:187`（`最近正确率` / `客观题正确率`） vs `openspec/changes/workbench-visual-language-v2/design-notes/copy-table.md` R-28 / R-41 定稿（`最近判定 N/M`、`客观题判定 N/M`） | 记录中心实际打印的仍是「正确率」，而本变更的文案定稿已经改成「判定 N/M」 —— 实现与定稿不一致 | `openspec/changes/workbench-visual-language-v2/design-notes/copy-table.md` R-28 / R-41 | openspec change | 中 | 由本变更 tasks 19/26 落地定稿文案（`最近判定 N/M`、`客观题判定 N/M`）；与 CD-065 的口径定义是两件事，可并行 |
| CD-159 | `openspec/specs/workbench-ui/spec.md:46`（练习页 "SHALL NOT expose suggestion-to-assembly actions"） vs `openspec/specs/review-workbench/spec.md:227-235`（"MAY" suggest） | 两份 spec 对「练习页是否给建议」的规定**强弱相反**（一个 MAY、一个 SHALL NOT） | `openspec/specs/review-workbench/spec.md:227-235`；`openspec/specs/workbench-ui/spec.md:46` | spec delta | 高 | spec owner 统一两份 spec 的措辞（建议行若落地，须在 `workbench-ui` spec 里开一个明确的只读例外；若退役，则改 `review-workbench` 的 MAY）；与 CD-038 同案 |
| CD-160 | `openspec/specs/workbench-ui/spec.md:73-75`（"no stored topic/group layer"） vs `workbench/server/static/workbench.css:515-521`（`.problem-topic` 化石规则） | 契约禁止 topic 层，CSS 里却留着 topic 层的化石规则 —— 契约与实现的**残留物**对不上 | `openspec/specs/workbench-ui/spec.md:73-75` | openspec change | 中 | 与 CD-048/CD-051 同案：删化石规则（先定 PRODUCT-MANUAL 是否复活分组） |
| CD-161 | `openspec/specs/workbench-ui/spec.md:12`（"a collapsible right Agent conversation column"） vs `workbench/server/static/workbench.css:153`（`.mobile-drawer-controls` 在 ≥1024px 是 `display:none`） | spec 承诺右栏「可收起」，桌面端**没有任何收起入口** | `openspec/specs/workbench-ui/spec.md:12` | spec delta | 高 | 与 CD-029 同案：spec owner 明确 spec 指的是窄屏抽屉还是桌面也可收起；本条只登记（同一冲突的契约侧腿） |
| CD-162 | `docs/PRODUCT-MANUAL.md:43`（「Dashboard 的工作区列表」一句） vs `workbench/server/pages.py`（hub 22 张等权卡） | 手册对 hub 的描述只有一句话，没有字段/排序/分组口径，与实现的「注册顺序 + 22 张等权卡」之间没有可判定的契约 | `docs/PRODUCT-MANUAL.md:43` | docs/GLOSSARY.md | 低 | 契约责任人补写 hub 卡片的信息层级与排序口径（与 CD-033 同案：spec owner 增补 hub 排序契约后，手册同步） |
| CD-163 | `docs/PRODUCT-MANUAL.md`（知识点页「掌握」一句） vs `docs/GLOSSARY.md`「行动提醒 / Action-oriented learning reminders」三态 | 手册正文用「掌握」描述知识点状态；词表定义的三态是「重点练习 / 可以复习 / 中性」，且把「掌握度」列为禁用词 | PRODUCT-MANUAL 的措辞与 GLOSSARY 的行动提醒三态不是同一套词；「掌握」在词表里不是状态词 | docs/PRODUCT-MANUAL.md | 中 | 手册 §3.2 的「掌握」改为词表三态之一（中性）或明确它是正文描述而非状态词；本轮 mockup 一律用词表三态，差异留待后续 change 统一 |
| CD-164 | `openspec/changes/workbench-visual-language-v2/decisions.md` **A-29**（裁决：里程碑判定去掉第三条） vs `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`（`Round completion celebration in two tiers`，原写三条里程碑条件） | 里程碑判定原本写了**全对 / 破纪录 / 章节首次完成**三条；其中「破纪录」要判定必须先定义**比较范围**（跟同一份卷比？同一章？历史所有练习？比什么量？），而这个范围在既有契约里**不存在** —— 仓库里没有可比的现成来源；spec 却把它写成了一条可触发的条件，等于一条**可能永远不触发**的死文本 | `openspec/specs/workbench-ui/spec.md`（原「beats the learner's own record for the same paper」一条）与 `docs/GLOSSARY.md` `_Avoid_`（正确率 / 掌握度 / 完成度百分比）—— 任何代理指标近似都会造出一个**口径未定义的新事实** | 产品决策 | 中 | **待所有者定义比较范围**（在同一份练习 / 同一章 / 全部练习之间比什么、比什么量），定义后再作为**独立条款**补进 spec；在它被定义之前**不得**用任何代理指标近似（如「比上次做得好」）触发里程碑；里程碑只用「全对」与「章节首次完成」两个条件（`decisions.md` **A-29** 已按此改写 spec / tasks） |
| CD-165 | `workbench/server/pages.py`（代码围栏语言标记的正则） vs `workbench/server/static/workbench.js`（客户端同一处） | 服务端用 `\w` 兼容 Unicode，客户端只认 ASCII ⇒ 形如 ```中文 的围栏**在服务端被识别、在浏览器不识别**，两侧输出不一致 | 同一语料的两种解析规则；属实现差异而非契约冲突（本轮实现已按 A-6 统一到服务端语义并把服务端收成 ASCII 口径，池全量 336 条内容扫描 0 条受影响） | openspec change | 低 | 已在本轮实现中统一（服务端围栏语言收成 ASCII 口径）；本条留档说明**差异来源与统一口径**，供后续核对两侧解析规则不再分叉；如需长期锁死，请补一条两侧共用规则的测试 |
| CD-166 | `workbench/server/static/practice-flow.js`（组卷报告的知识点显示） vs `docs/PRODUCT-MANUAL.md`（练习页面向学习者的文案口径） | 组卷报告的「可用题数少于请求量的知识点：…」在**产品里显示知识点 id**（如 `kp-2`）而不是知识点名（如「线性方程组」） | **既有缺陷，不是本轮引入**：名字映射来自 `#scope-tray` 的 `dataset.kpNames`，而 scope tray 早在 `8cc9d23d`（`feat: connect free Paper practice and remove learner assembly controls`）就从 `pages.py` 移除了 ⇒ `names` 恒为空、`names[kpId] \|\| kpId` 恒走回退分支。**唯一的名字来源 `tests/workbench/workbench_ui_interactions.test.js` 的假 DOM 夹具**曾凭空注入一个 scope-tray 元素，所以测试断言的是一条**产品里不可达的路径** | 待定 | 中（学习者看到的是内部 id，不是可读的知识点名） | 本轮**不修**：修它需要一个带知识点名的数据源（知识点列表 API 的响应里没有名字），而新增/改动取数会动请求序列 —— 违反「现有交互逻辑一个字都不许改」的底线。⇒ 本轮随 14.1 删掉那段死代码（**产品行为零变化**），并把测试夹具改为断言真实行为（id）。**待所有者定**：要不要单开一个 change，把知识点名接进组卷报告；若要，需先定「名字从哪来」（复用已加载的知识点列表 / 扩 API 响应） |
| CD-167 | `openspec/changes/workbench-visual-language-v2/tasks.md` **17.6**（里程碑两条件之「章节首次完成」） vs 池里的 `practice_runs` 表结构 | 17.6 要求里程碑档在「① 本轮全对」**或**「② 章节首次完成」时启用，但**「章节首次完成」当前不可判定**：`practice_runs` **没有章列**、也没有任何「首次完成」标志 | spec 要的是一个**事实**，而现有持久化里**没有承载它的地方**。`decisions.md` **A-29** 已裁定**不得用任何代理指标近似**（例如「比上次做得好」「本工作区第一次做这一章」这类推算），所以**不能**就地造一个近似口径 | 待定 | 中（里程碑档目前只有「全对」一条能触发；「章节首次完成」恒为 false） | 本轮**保持 false 并如实标注**：客户端写 `data-lk-chapter-first="false"`，判定逻辑（`workbench.js` 的 `isMilestoneRound`）保留该条件，事实为 false 时不进里程碑档。⇒ **spec 的两个条件目前只有一个可触发**，这是**如实实现**，不是漏实现。**待所有者定**：要不要给它一个真实的数据来源（给 `practice_runs` 加章列 / 另立一张「章节完成」表）—— 那是**持久化 schema 变更**，必须单开 change 并同步 `docs/DATA_MODEL.md`；在数据来源定义之前，**不得**用代理指标补上 |
| CD-168 | `openspec/changes/workbench-visual-language-v2/design.md` **D-13**（记录中心卡片流） vs `openspec/changes/workbench-visual-language-v2/design-notes/layout-spec.md` **§5.6**（明细卡流用 2 列网格） | 两份设计件对「记录中心明细视图用几列」给出**互斥**说法：D-13 写「不会降到约 4400px」（⇒ 单列 + 密度收紧，页高目标 5500–6500px），layout-spec §5.6 写「2 列网格」（⇒ 页高约 4400–4500px） | 同一事实的两份设计件冲突，不是实现 bug；实测现状：单列 + 36px/卡 ⇒ `?view=attempts` 的 `scrollHeight = 8951px`（改造前 8895px） | `openspec change` | 中（页高超出 D-13 目标区间约 2500px） | 已由 `decisions.md` **A-50** 裁定：**采信 D-13（单列卡片流 + 收紧密度）**，`layout-spec.md` §5.6 的「2 列网格」在记录中心明细视图这一处作废（该文件其它 2 列用法不受影响）；实现侧由 CSS 收紧 `.record-row` 密度到 ≈22px/卡（目标 ≈6300px）；⚠️ **不许靠删字段达到页高**（六项字段一个不少） |

---

## 2. 按「建议归属」分组的索引

> 后续开 change 时按这里的归属分派。**归属 ≠ 归属人**：同一组里既有「本变更 tasks 组
> 顺手带走的」，也有「必须另开 change 的」，后者请按「改成什么 / 谁来定」列判断。

### 2.1 `openspec change` —— 72 条

CD-001, CD-002, CD-003, CD-004, CD-005, CD-006, CD-007, CD-008, CD-009, CD-010,
CD-011, CD-012, CD-013, CD-015, CD-016, CD-017, CD-018, CD-019, CD-020, CD-025,
CD-027, CD-028, CD-030, CD-038, CD-039, CD-042, CD-047, CD-051, CD-052, CD-054,
CD-055, CD-056, CD-057, CD-058, CD-059, CD-060, CD-061, CD-071, CD-072, CD-081,
CD-082, CD-083, CD-084, CD-086, CD-092, CD-096, CD-097, CD-098, CD-106, CD-107,
CD-108, CD-109, CD-110, CD-112, CD-113, CD-115, CD-121, CD-123, CD-126, CD-128,
CD-129, CD-130, CD-131, CD-132, CD-133, CD-134, CD-135, CD-150, CD-151, CD-154,
CD-158, CD-160

**读法**：这一组里绝大多数是**本变更已有 tasks 组承接**的实现侧条目（token 地基、
纸面层级、色彩收编、空态组件化、文案清理）。它们进登记册的原因不是「没人管」，
而是「**登记时还没修**」——修完请把对应行的状态改成「已处理（tasks 组号 + 提交号）」。

### 2.2 `spec delta` —— 35 条

CD-014, CD-023, CD-026, CD-029, CD-031, CD-033, CD-035, CD-036, CD-041, CD-045,
CD-046, CD-049, CD-053, CD-068, CD-073, CD-074, CD-075, CD-076, CD-079, CD-089,
CD-090, CD-093, CD-094, CD-095, CD-100, CD-101, CD-104, CD-105, CD-111, CD-117,
CD-118, CD-119, CD-148, CD-159, CD-161

**读法**：这一组的处理人一律是 **spec owner**。它们要么是「spec 与实现说的不是一件事」，
要么是「spec 没写，但实现已经做了用户可见的事」。**不要由实现者自行挑一边** ——
AGENTS.md 明写「禁止静默挑一个版本继续实现」。

### 2.3 `产品决策` —— 35 条

CD-024, CD-032, CD-037, CD-040, CD-044, CD-050, CD-062, CD-064, CD-067, CD-069,
CD-077, CD-078, CD-080, CD-085, CD-091, CD-103, CD-116, CD-120, CD-122, CD-124,
CD-125, CD-136, CD-137, CD-138, CD-139, CD-140, CD-141, CD-142, CD-143, CD-144,
CD-145, CD-146, CD-155, CD-157, CD-164

**读法**：这一组要么需要**所有者拍板**（取舍、默认值、要不要这个功能），要么是
**产品哲学层面的长期取向**（CD-136…CD-146 这批多邻国游戏化机制）。后者建议一次性
裁决后写成 GLOSSARY 词条，免得每轮设计重吵一遍。

### 2.4 `docs/GLOSSARY.md` —— 16 条

CD-021, CD-022, CD-043, CD-048, CD-065, CD-066, CD-087, CD-088, CD-099, CD-127,
CD-147, CD-149, CD-152, CD-153, CD-156, CD-162

**读法**：处理人 = **词表责任人**。两条不同性质要分开看：
① **词条缺失**（CD-022 排版角色、CD-065 正确率、CD-066 平均自评）→ 补词条；
② **词条与实现/手册打架**（CD-087/088 主题偏好、CD-153 本章计数、CD-156 覆盖进度）
→ 先裁决口径，再改词条。**不要把「未裁决的分歧」直接写进词条**。

### 2.5 `docs/DATA_MODEL.md` —— 5 条

CD-034, CD-063, CD-070, CD-102, CD-114

**读法**：处理人 = **DATA_MODEL 责任人**。这 5 条全部是「**实现里已经存在、但
DATA_MODEL 没有登记语义**」的字段/口径（hub 最近使用、行动提醒判据来源、
`problem_attempts.status` 的用户可见映射、消息时间戳、统计口径的 writer 边界）。
按 AGENTS.md 第 3 条，**登记后由本 PR 同步**，不是留到以后。

---

## 3. 本轮已裁决、不再登记的清单

> 这一节的作用是**防止下一轮重复登记**。下面这些分歧在**本变更内已被所有者裁决**，
> 因此**不进 §1 主表**；但其中若干条的「**执行落盘**」尚未完成，那部分残留以
> 主表里**标注了「裁决已完成，落地未落」**的条目为准（见 CD-123、CD-129、CD-130、
> CD-134、CD-141）。

### 3.1 追加裁决 A-1 … A-16（`decisions.md`）

| 裁决 | 主题 | 定案 |
|---|---|---|
| A-1 | 涟漪扩散时卡片怎么处理 | **不压平**；卡片全程不动，只有底色从灯下扩散 |
| A-2 | 用户显式动效设置 vs 系统 `prefers-reduced-motion` | **显式设置优先**（实现按两份 delta 更严的一侧同时满足） |
| A-3 | 关键反馈音效的音色 | 温润玻璃 / 现磨，<200ms，不做提示音 |
| A-4 | 「当前」的蓝/黄分工歧义 | 消歧：蓝=当前选中，黄=当前/复习强调（承接第 3 组配额表） |
| A-5 | 自绘控件的载荷兼容铁律 | 自绘控件必须保留原生控件的键盘/表单语义 |
| A-6 | 题面与正文同档 | 17px / 1.75 / 38em（`design.md` D-5 已按此修正） |
| A-7 | 夜纸下知识图谱跟随夜纸 | 图谱的纸面/墨线/节点/关系线按夜纸值集重新着色（**其例外条款已被 A-8/A-12 改写**） |
| A-8 | 图谱的夜纸适配并入图谱 change | 本变更**不再触碰图谱**；「亮色逐像素不变」这条例外按 A-12 改写 |
| A-9 | token 命名与取值的唯一权威 | 权威表 = `design-notes/night-paper-tokens.md`；唯一真值族 = `--surface-*` / `--ink-*` / `--role-*` |
| A-10 | 节点半径收窄 + 两个 change 的归档顺序 | 半径 20–44px 收为 14–30px；`graph-node-visual-language` 先归档 |
| A-11 | 主题偏好的默认来源 | **学习者显式选择优先**；无已存偏好时跟随系统 `prefers-color-scheme` |
| A-12 | 图谱 change 必须自带门禁 | 图谱 change 自带 `acceptance.md`，判据改为**结构不变量** |
| A-13 | token 名必须归一；`--lk-*` 与仓库现状同名 | 第三族 `--lk-*` **整体退役**，按概念映射到权威表，不得沿用该前缀 |
| A-14 | G-5 的比对范围与可复现前提 | 取**整页**（最严）+ reduced-motion 下比对；基线不可复现才降级并留痕 |
| A-15 | 覆盖审计残余漂移 #8 / #10 | Agent 输入框圆角 **12px 统一**；图谱标签字号 **12px** |
| A-16 | 图谱专用纸面 token 的名字 | `--surface-sheet` 是**唯一**名字；`--surface-card` / `--surface-graph-sheet` 退役（⚠️ 该措辞已被 **A-17** 限定，见 CD-134） |

### 3.2 图谱节点重设计 G-1 … G-24（`decisions.md`）

| 裁决 | 主题 | 定案 |
|---|---|---|
| G-1 | 节点形态 | 两个同心的圆（内核 + 外环） |
| G-2 | 度量条（`.metric-track`） | **移除**（颜色与大小表达强度） |
| G-3 | 尺寸档 | 连续映射收缩范围（保持节点数多时小、半稀疏区收缩） |
| G-4 | 底噪（`.graph-tide` 画布） | **保留**（原有作者意图） |
| G-5 | 节点标签 | 常态可见但不抢眼；不截断、降对比度不降节点 |
| G-6 | 节点上的文字 | **不允许任何状态文字**（改用颜色 + 几何） |
| G-7 | 掌握状态配色 | 图内用可自解释的一组状态色，与全站界面色配额分开 |
| G-8 | 投影与配色 | 不同类型的图，配色不同；4 类投影各有自己的色键 |
| G-9 | 圆内文字 | 只留一个整数或数字；名称在下方标签 |
| G-10 | 改造范围与归属 | 只改节点（形态/尺寸/配色/标签），**另开** `graph-node-visual-language` |
| G-11 | 颜色说明 | 必须有「什么颜色对应什么类型」的标注，且随投影切换 |
| G-12 | 各投影的色键 | 分类用色，量值用单色阶 |
| G-13 | 同心圆的深浅分法 | 内核深、外环浅（同色相深浅两档） |
| G-14 | 颜色标注 | 图例随投影切换：上半关系线型、下半节点颜色 |
| G-15 | 选中/聚焦/关联 | 外环加粗 + 节点轻微放大 |
| G-16 | 量化投影的色相 | 放弃蓝色，改用暖色（避开蓝色；不引入紫色） |
| G-17 | 半径区间 | 20–44px → 14–30px（实测 165×460 布 31 节点会占满） |
| G-18 | 关系线端点 | 接到外环边缘（必要连带修改 WebGL 端点计算） |
| G-19 | 夜纸下的分类色 | 同一色相、提亮饱和度；与暖纸圆底降亮 + 提亮处理 |
| G-20 | 量化档的色相 | 暖（暖色专属面板的一员） |
| G-21 | 学习状态四色 | 未掌握=中性灰、已掌握=理想蓝、需加强=琥珀、需突破=砖红 |
| G-22 | 关系结构投影下的节点色 | 增阶梯（关系弱的用浅灰表达，节点不继承主色） |
| G-23 | 标签重叠 | 重叠时自动隐藏小标签（按节点大小与重要度排序让位） |
| G-24 | 诊断页推出的优先级 | 先修屏幕空间释放冲突，再修密度挤压 |

### 3.3 其它本轮已关闭的分歧（不在主表）

- **`DECISION-COVERAGE.md` 残余漂移 #12「`contract-drift.md` 尚未创建」** ——
  由**本文件**关闭（`tasks.md` 27.1–27.3 的交付缺口）。
- **`DECISION-COVERAGE.md` 残余漂移 #7「涟漪是否压平」** ——
  `motion-spec.md` 已按 A-1 改写（现 §4.5「涟漪不压平卡片（A-1 唯一结论）」）。
- **`DECISION-COVERAGE.md` 残余漂移 #17「A-7 与 A-8 的优先级未显式声明」** ——
  A-8 现已明写「A-7 原本裁定……但既然 G-10 把节点重设计划给了独立 change」，
  账本内部次序已显式，不再登记。
- **`DECISION-COVERAGE.md` 残余漂移 #15「图谱 change 无 `tasks.md` / `acceptance.md`」** ——
  `openspec/changes/graph-node-visual-language/` 现已有 `tasks.md` 与 `acceptance.md`，
  缺口已闭合。（该文件仍有的问题另见 CD-120 / CD-121 / CD-123 / CD-130。）

---

## 4. 自检

| 检查项 | 结果 |
|---|---|
| **登记总条数** | **165 条**（`CD-001` … `CD-164`），ID 连续、无缺号 |
| **与 `tasks.md` 27.2 要求的 128 条的差额** | **+37 条**。差额原因见 §4.1，**不是**为凑数编造 |
| **表行字段完整性** | 每行 7 列（ID / 位置 / 现状 / 冲突方 / 建议归属 / 优先级 / 改成什么），**164 × 7 = 1148 格全部非空**；六个内容列**无一空值** |
| **重复 ID** | **0**（164 个 ID 全互异；ID 已按文件顺序重排过一次） |
| **「建议归属」取值合法性** | **163 / 165 条**落在 `openspec change` / `docs/DATA_MODEL.md` / `docs/GLOSSARY.md` / `spec delta` / `产品决策` / `docs/PRODUCT-MANUAL.md` 五值之内（分布：`openspec change` 72 / `spec delta` 35 / `产品决策` 35 / `docs/GLOSSARY.md` 16 / `docs/DATA_MODEL.md` 5）；余下 **1 条（CD-163）**的归属值写作 `docs/PRODUCT-MANUAL.md`（第六值，本轮只登记、不裁决） |
| **「优先级」取值与分布** | 全部落在 高 / 中 / 低 三值之内（分布：**高 41 / 中 87 / 低 36**） |
| **「改成什么 / 谁来定」非空** | **164 / 164** |
| **表内交叉引用有效性** | 25 处 `CD-xxx` 交叉引用全部指向存在的行（已逐条复核；重排时修正了 CD-146 → CD-141 一处失效引用） |
| **markdown 表格完整性** | 165 行全部 8 个分隔符（`\|` 转义后）；无跨列的裸 `\|` |
| **文件名与位置纪律** | 本文件是**唯一**写入物；`docs/` 下无同名文件，`docs/PENDING-DEFINITIONS.md` 未被追加，`docs/audits/` 未被写入 |

### 4.1 条数差额说明（+37）

`tasks.md` 27.2 写的是「登记 **128 处**契约漂移」。本表实际登记 **165 条**。
差额来自三处，**均非编造**：

1. **一处漂移有多条腿**（约 +12）：审计报告里常把「同一个概念在 3 份文件里有 3 个值」
   记作**一条**，但登记表必须**逐腿可执行** —— 每一腿的修复位置与责任人不同。
   例：`--surface-card` 的退役在权威表（`night-paper-tokens.md:156` vs `:159`）、
   在 `component-spec.md` 的 38 处引用、在 `decisions.md` A-16 的措辞里是**三处**
   独立可修的落点（CD-127 收了权威表那一处）。
2. **「同一冲突的契约侧腿」单列**（约 +10）：同一个实现事实与**两份**契约文件冲突时
   （例：右栏「可收起」在 `workbench-ui/spec.md:12` 与 `workbench.css:153` 各是一条腿），
   登记成两条，因为它们的**修复动作分属 spec owner 与实现者**。
3. **裁决已下、落地未落**（约 +12）：A-15 / A-16 / A-11 / A-9 等裁决已在 `decisions.md`
   记档，但**工件还没改**（`layout-spec.md:55` 的 20px、图谱 `design.md:102` 的 11px、
   `night-paper-tokens.md:156` 与 `:159` 的自相矛盾等）。按硬规则 4，它们不属于
   「本轮已裁决**并已修**」，必须登记 —— 否则下一轮会照旧值再实现一遍。

**若所有者认为 128 是硬上限**：本表可以按 §2 的优先级顺序**先交前 165 条**
（高 41 + 中 87），剩余 37 条转入下一份登记册；但**不建议**这么切 ——
切开会把「同一冲突的两条腿」拆散到两份表里，登记表反而更难用。

### 4.2 六类来源的覆盖情况

| # | 来源 | 登记条数 | ID 范围 |
|---|---|---|---|
| 1 | `tmp/frontend-audit/F01.md` … `F08.md`（明确指出但不属本轮范围的问题） | **116** | CD-001 … CD-096、CD-100 … CD-116、CD-160 … CD-162 |
| 2 | `tmp/frontend-audit/DECISION-COVERAGE.md` 残余漂移清单（尚未被本轮裁决并修掉者） | **10** | CD-119、CD-120、CD-128 … CD-135 |
| 3 | `tmp/frontend-audit/DUOLINGO-PHILOSOPHY.md` 明确不建议照搬的游戏化机制 | **11** | CD-136 … CD-146 |
| 4 | `decisions.md` A-13 提到的 `graph-isolation.md` Q-1 / Q-2 / Q-6 / Q-7 / Q-8 | **6** | CD-121 … CD-126 |
| 5 | `docs/GLOSSARY.md` / `docs/DATA_MODEL.md` / `openspec/specs/` 之间的既有不一致 | **9** | CD-117、CD-118、CD-127、CD-153 … CD-157、CD-159 |
| 6 | `design-notes/copy-table.md` 标为「契约漂移」的条目 | **10** | CD-097 … CD-099、CD-147 … CD-152、CD-158 |

合计 116 + 10 + 11 + 6 + 9 + 10 = **162**（六类审计来源）；
另 **2 条不属这六类来源** —— CD-163（`docs/PRODUCT-MANUAL.md` 措辞 vs
`docs/GLOSSARY.md` 三态）与 CD-164（`decisions.md` **A-29** 裁决遗留：里程碑判定条件里
「破纪录」的口径待所有者定义）。全表合计 **164** 条。

**逐来源覆盖核对**：

- **来源 1**：F01（CD-001…027，27 条）、F02（CD-028…037，10 条）、
  F03（CD-038…047，10 条）、F04（CD-048…064，17 条）、F05（CD-065…079，15 条）、
  F06（CD-080…083、CD-100…107，12 条）、F07（CD-093…096，4 条）、
  F08（CD-084…092、CD-108…116，17 条）—— 八份审计的「需要先改 spec 的清单」
  与「问题诊断」中被点名、且不属于本轮 tasks 范围的条目**逐条落表**。
- **来源 2**：残余漂移 17 条中，**#7 / #12 / #15 / #17 已在本轮关闭**（见 §3.3），
  **#1 / #2 / #3 / #4 / #5 / #6 / #8 / #9 / #10 的执行残留**转入主表
  （CD-119、CD-120、CD-123、CD-127、CD-129、CD-130、CD-133、CD-134），
  **#11 / #13 / #14** 各一条（CD-128、CD-131、CD-132）。
- **来源 3**：11 类机制**逐条登记**（XP/倍率、COMBO、心/能量、streak/冻结卡、
  每日目标、排行榜/联盟、徽章、宝石、广告、拟人化、排行榜式速度比较）。
- **来源 4**：Q-1（CD-122）、Q-2（CD-126）、Q-6（CD-123，**已由 A-16 裁决**）、
  Q-7（CD-124）、Q-8（CD-125）+ 隔离件里已过期的事实陈述（CD-121）。
- **来源 5**：`tasks.md` 27.2 点名的三项（建议/每日计划队列无出口 = CD-127；
  正确率未定义且被 `_Avoid_` = CD-065 / CD-099；完成练习 100 轮 vs 作答次数无上限 =
  CD-067）**均在表**；另加主题默认来源三方冲突（CD-087 / CD-088）、
  章节切换形态落差（CD-036）、spec 文案与 `pages.py` 不一致（CD-097 / CD-098 / CD-053）、
  动效偏好与 reduced-motion 的措辞冲突（CD-117）、stem 字号措辞残留（CD-118）。
- **来源 6**：`copy-table.md` §6.6 的 D-01…D-09 **逐条落表**
  （D-01=CD-097、D-02=CD-053、D-03=CD-147、D-04=CD-149、D-05=CD-152、
  D-06=CD-150、D-07=CD-151、D-08=CD-148、D-09=CD-099/158），
  外加 §2.13 的 E-03（CD-098）。
- **六类来源之外**：CD-163（`docs/PRODUCT-MANUAL.md`「掌握」措辞 vs
  `docs/GLOSSARY.md` 行动提醒三态）、CD-164（`decisions.md` **A-29**：里程碑判定里
  「破纪录」缺**比较范围**口径，已按 A-29 从 spec 去掉并改为待所有者定义）。

### 4.3 实证 / 推断的区分

- **实证**（`grep` / 读码 / 读文档可复核，位置列给出 `file:line`）：全部 165 条的
  「位置」与「现状」两列。抽样复核（均已实跑）：`workbench.css` 的
  `:16-17 / :31-33 / :36-39 / :43-44 / :153 / :157 / :338 / :427 / :504-505 / :515-521 /
  :799 / :833 / :1008 / :1034 / :1051 / :1123 / :1166 / :1211 / :1214 / :1462 / :1505 /
  :1786-1799 / :1888`；`workbench.js:1052,1077,4400-4440,4569-4573`；
  `graph-renderer.js:16-20`；`pages.py:154,282,340-342,377-378,396,401,584,669`；
  `records.py:12-18,131,183,187,294-300`；`data/records.py:53-55,73-75,76-97,142`；
  `conversations.py:129-140,177-249`；`experience_page.py:62-64`；`agent-ui.js:267`。
- **推断**（结论基于上述实证，但带判断成分）：已用措辞区分 —— 涉及「应不应该这样」
  的行（如 CD-024 蓝/黄归属、CD-032 折叠态默认、CD-044 栏宽、CD-085 窄桌面档形态、
  CD-136…146 的游戏化取舍）一律归入 `产品决策` 归属，并在「现状」列只陈述事实。
- **口径说明**：审计报告里的「39 处 `class='muted'`」（`F08` D-05）在本轮实测为
  **47 处**（分布：`pages.py` 13 / `records.py` 9 / `practice-flow.js` 11 /
  `paper-practice.js` 5 / `workbench.js` 5 / `kp-experience.js` 2），
  CD-060 以**实测值**登记并注明来源差异。
- **一条被否掉的登记**：提示中提到的「`.paper-dots` 死规则」经 grep 核实**不成立**
  —— `workbench.css:1888` 有规则、`pages.py:215` 有标记、`paper-practice.js:47` 有引用；
  真问题是 `.paper-dots` 的 `max-height:140px; overflow-y:auto`（面板内滚）
  与题号面板的位置，已由 CD-046 登记。**未按提示登记一条不成立的事实。**
- **移动靶提示（重要）**：本表的「位置」列对 `workbench/` 下的**代码**引用是稳定的，
  但对 `openspec/changes/workbench-visual-language-v2/design-notes/*` 与
  `decisions.md` 的引用**会随并行编辑漂移**。本表落盘时已按 2026-10-22 的树状态
  复核过一遍（期间并行 agent 已改 `asset-spec.md` / `layout-spec.md` /
  `motion-spec.md` / `night-paper-tokens.md` / `design.md` / `tasks.md`），
  并据此改写了 CD-123、CD-129、CD-134 三条。**复核时请以 `git status` 与文件
  mtime 为准**；若某条 design-notes 引用失效，以该文件的**章节标题**为准
  （表内已尽量写明章节名）。

### 4.4 维护约定

- **谁清理**：本变更的 **spec owner**。每处理一条，在该行「改成什么 / 谁来定」列
  追加「已处理（change 名 + 合并日期）」，并把 ID 划入本文件末尾的「已处理」清单。
- **什么时候清**：登记表随本 change 一起归档；**归档不等于已修** ——
  归档后这张表仍是滚动的活文档，归档提醒写在 `HANDOFF.md`。
- **谁来加**：任何 Agent 在本仓库发现新的「已确认与某份契约对不上、且不在当轮范围」的
  事实，都可以往本表追加一行（ID 续号），但**必须**给出可复核的 `file:line`。
- **不许做的事**：① 把「已登记」写成「已处理」；② 把未裁决的分歧写进 `docs/`；
  ③ 把**名词缺失**塞进本表（那是 `docs/PENDING-DEFINITIONS.md` 的职责）。

