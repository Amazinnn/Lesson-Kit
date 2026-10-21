# Tasks — workbench-visual-language-v2

> **视觉基线唯一依据**：`openspec/changes/workbench-visual-language-v2/decisions.md`「# 收口：最终基线」。
> **实施口径**：请求与持久化不变（冻结清单见 `proposal.md`「Frozen」）；本变更只改表现层。
> **交付分两段**：**样板线**（第 1–18 组，用户验收前）与**铺开**（第 19–25 组，样板线验收通过后）。
> **分支**：`feat/workbench-visual-language-v2`，不并入 main；每个可验证单元单独提交，
> 提交信息用 `feat/` `fix/` `docs/` `chore/` `refactor/` 前缀，工作区不留脏。
> **硬约束**：无框架、无构建步骤、无 npm、无 CDN、无图标字体；纯 CSS + 原生 JS。
> **知识图谱页完全不在范围内**：`workbench/server/static/workbench.css:1497-1884` 及其图谱专用
> `:root`（L1505 起，含 `--paper:#fffdf7`、`--ink:#191816`、`--hair:#ddd8cd`）一行不改，
> 新 token 层不得改变图谱依赖的取值。
>
> **口径说明**：写本清单时 `design.md` 仍是空模板、`specs/` 尚未生成（G01/G02/G03 未就绪），
> 因此**本任务拆解未参考 design.md 与 spec delta**；二者完成后需回头复核本清单，
> 重点复核第 9、13、14 组（新增能力与新行为最密集）。
>
> **每组末尾的「阶段验收」任务统一要求跑 AGENTS.md 的四条验证命令**：
> `python -m pytest tests -q`、`python -m compileall -q lessonkit.py workbench pipeline pool tests`、
> `openspec validate --specs --strict`、`python lessonkit.py guard extract-problems --course dmath --chapter ch06`；
> 截图走查一律在**池数据库副本 + 隔离注册表 + 独立端口**上点检，**永不写真实池**。

---

## 第一段：样板线（token 地基 + 外壳 + 练习页 + 知识点页 + 记录页 + 设置视图）

## 1. 视觉基线与 token 地基

- [ ] 1.1 在 `workbench/server/static/workbench.css` 的 `:root`（L4-46）内建立结构 token 段：新增 `--radius-*`（统一 12px，派生 sm/md/lg/pill）、`--space-*`（4/8/12/16/24/32/48 阶梯）、`--type-*`（正文 17px/1.75 与界面无衬线字号阶梯）、`--shadow-*`（暖调柔影）、`--motion-*`、`--z-*` 六个族；验证：每个新 token 只在 `:root` 声明一次（`grep -c "^\s*--radius-ui:"` 等计数为 1），且文件内不存在第二处裸名 `:root`（图谱专用 `:root` 除外）。
- [ ] 1.2 在同一 `:root` 内写入亮色值集：底色 `--surface-base:#fdf8ef`、墨色 `--ink:#221f1a`，并定义纸面层级四层 `--paper-base/--paper-card/--paper-raised/--paper-ink`；四层靠圆角 + 柔影区分，**不加描边、不铺背景纹理**；验证：`grep -n "background-image" workbench/server/static/workbench.css` 无新增噪声/纹理层。
- [ ] 1.3 把圆角统一收成 12px：`--dsw-radius-sm:6px` / `--dsw-radius-md:6px` / `--dsw-radius-lg:22px`（workbench.css:43-45）改为指向 `--radius-ui:12px` 的派生值，并逐条替换按钮 / 卡片 / 标签 / 输入框的硬编码圆角；验证：`grep -nE "border-radius:\s*(6px|22px)" workbench/server/static/workbench.css` 归零。
- [ ] 1.4 把三角色色提到更高饱和并建立语义配额层：新增 `--role-blue`（主按钮 + 链接 + 当前选中）、`--role-yellow`（当前项 + 复习强调 + 连对进度）、`--role-red`（失败 + 阻塞），三色各只有一个定义点，并在 `:root` 上方用注释写明配额与「不加第五色」；验证：三个 `--role-*` 的声明计数各为 1，新增色相为 0。
- [ ] 1.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝hub + 练习页 + 知识点列表三页的基色 / 圆角 / 卡片层级；确认本组只改 token 段，图谱样式未动。

## 2. 旧 token 迁移与别名期

- [ ] 2.1 把 `workbench/server/static/workbench.css` 中的硬编码 hex 收编进三角色 + 灰阶 token：4 个蓝（`#2457c5` `#2864dc` `#456fc9` `#193f91`）、9 个红系（`#d6453d` `#b62f28` `#b42318` `#d12c2c` `#922d26` `#c75a52` `#f6d8d5` `#fff0ed` `#fdeceb`）、10 个黄橙（`#f2c94c` `#d3a914` `#e1aa12` `#d9aa18` `#c3a128` `#b88700` `#b58b00` `#8c6b00` `#332900` `#fff7cf`）、6 个绿（`#1a7f37` `#4f9870` `#54a778` `#e6f4ea` `#d9ebdd` `#22c55e`）；绿系**不得引入第四色相**，「正确 / 已掌握」改用文案 + 几何表达；验证：`grep -nE "#[0-9a-fA-F]{3,6}" workbench/server/static/workbench.css` 的命中全部落在 token 声明行内。
- [ ] 2.2 设别名期：保留全部旧 `--dsw-*` 变量名作为指向新 token 的别名（例 `--dsw-bg-base: var(--surface-base)`、`--dsw-brand-primary: var(--role-blue)`），每条加 `/* deprecated: 迁移到 --xxx */` 注释；验证：`grep -n -- "--dsw-" workbench/server/static/workbench.css` 中无裸色值，且旧名仍被其它样式引用不报错。
- [ ] 2.3 补齐未定义变量与 `.muted`：修 `workbench.css:1051` 使用的未定义 `--dsw-text-muted`；新增 `.muted` 规则（当前只有 `li.muted` L1034，导致空态与正文同色）；验证：`.muted` 与正文的对比度实测 ≥ 4.5:1 并记录数值。
- [ ] 2.4 修焦点环：删除 `workbench.css:338`、`:427`、`:833` 三处 `outline: none`，改用统一的 `:focus-visible` 环（颜色取 `--role-blue`）；验证：`grep -c "outline: *none" workbench/server/static/workbench.css` 为 0，且 Tab 遍历顶栏 / 左栏 / 中栏 / 右栏控件时每个都有可见焦点环。
- [ ] 2.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝6 类页面的基色 / 圆角 / 卡片层级 / 焦点态；确认硬编码色归零后视觉无回退。

## 3. 字体与双字族

- [ ] 3.1 打包阅读面衬线字体：在 `workbench/server/static/fonts/` 下加入思源宋体子集 `.woff2`（简体中文 + 常用标点）与 `OFL.txt`（SIL Open Font License 全文）；子集化用 `pyftsubset` 等离线工具一次性完成，仓库不保留构建脚本、不引入 npm；验证：目录内含 woff2 与许可文件，许可文件写明 SIL OFL 且文件名可追溯。
- [ ] 3.2 在 `workbench.css` 声明 `@font-face`（`font-display: swap`、`unicode-range` 限定简体中文）并把阅读面字族接到 `--font-reading`；界面字族沿用现有无衬线栈 `--dsw-font-family`（L11-13），等宽第三族保留 `--dsw-font-code`（L14-15）；验证：computed style 在阅读面为衬线族、在按钮 / 导航为无衬线族、在代码块为等宽族。
- [ ] 3.3 落实阅读面字号规格：正文 17px / 行高 1.75 / 行宽 38em，作为 `--type-reading-*` 落到题面、知识点正文、解析三处；验证：三处 computed `font-size:17px`、`line-height:29.75px`、`max-width:38em`。
- [ ] 3.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝知识点正文 / 题面 / 解析三处的字号、行宽、字族与单侧结构线；确认字体文件体积可接受（woff2 单文件 ≤ 数百 KB 量级），无构建脚本入库。

## 4. 动效系统基座

- [ ] 4.1 在 `workbench.css` 新增动效 token：交互 120–180ms、场景 240–520ms、庆祝 517ms，各配 `--ease-standard` / `--ease-rebound` / `--ease-out`；把现有散落的硬编码时长（如 `transition: grid-template-columns 200ms` L161、`background-color 100ms`）收编到 token；验证：`grep -nE "transition:[^;]*[0-9]+ms" workbench/server/static/workbench.css` 每处都引用 token。
- [ ] 4.2 定义两组关键帧：`@keyframes lk-squash`（挤压回弹，抄多邻国 5 段关键帧 17 / 33 / 83 / 167 / 217ms，配 4 条贝塞尔曲线）与 `@keyframes lk-rise`（上浮 8–12px + 淡入，180–240ms）；验证：squash 关键帧含 5 个百分比节点且总时长为 517ms。
- [ ] 4.3 降级与禁用项：`@media (prefers-reduced-motion: reduce)` 下全部动画降级为状态直切（涟漪直接切、庆祝直接落终态）；在 CSS 注释中登记动效落点白名单（交互反馈 / 数据层 / 视图转场 / 里程碑仪式）与禁止项（全局背景 canvas、鼠标跟随、视差、光标辉光）；验证：开启 reduced-motion 后 `getComputedStyle(...).animationName` 为 `none`，且仓库内无背景 canvas 层与 `mousemove` 视差代码。
- [ ] 4.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝按钮 hover / active、卡片入场、空态入场三处动效（逐帧截图或录屏）；确认所有动效只动 `transform` / `opacity` / 颜色，不触发布局重排。

## 5. 导航静物 SVG 资产（可独立验收）

- [ ] 5.1 新建 `workbench/server/static/assets/icons/`，手写 5 枚导航静物 SVG：`practice-book.svg`（翻开的书）、`practice-sets-paper.svg`（一叠纸）、`kps-bookmark.svg`（书签）、`records-notebook.svg`（笔记本）、`graph-nodes.svg`（节点连线）；统一 `stroke-width:2`、统一圆角语言、不含 `<text>`、不外链字体；验证：5 个文件存在，`grep -l "<text" workbench/server/static/assets/icons/*.svg` 为空。
- [ ] 5.2 图标容器用彩色圆底色块，圆底**只取三角色色**（不同功能区对应不同角色色），不引入第四色相；验证：SVG 内的 `fill` / `stroke` 色值 ⊂ 三角色色 + 墨色 + 纸色，grep 无第四色相。
- [ ] 5.3 暗色适配与左栏接线：SVG 用 `currentColor` 或 CSS 变量取前景，暗色下降饱和提亮；把图标接入 `workbench/server/pages.py` 的 `_left_column` 导航项（`nav_items` L628-635）；验证：切夜纸后 5 枚图标仍清晰可见，左栏每项均为「图标 + 文字」并列。
- [ ] 5.4 阶段验收（SVG 资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝左栏 5 项图标在亮 / 暗两主题下的特写；确认资产目录内无构建脚本、无 base64 内联、无外链、无图标字体。

## 6. 空态静物插画资产（可独立验收）

- [ ] 6.1 新建 `workbench/server/static/assets/illustrations/`，手写学习器物静物插画（花瓶、果篮、画布、杯子、书本、台灯、钢笔，至少 6 件），写意线稿 + 淡彩晕染 + 克制高光，与 `assets/icons/` 同一套线宽与圆角语言；验证：文件数 ≥ 6，单文件色值数 ≤ 8（`grep -oE "#[0-9a-fA-F]{6}" | sort -u | wc -l`）。
- [ ] 6.2 单套资产双主题：插画前景 / 背景用 CSS 变量取色，暗色下自动反相，不做第二份资产；渐变只允许出现在图标与插画内部，并定义一套有限渐变语言（同一方向、同一组色阶）；验证：插画目录只有一套 SVG；`grep -n "linear-gradient" workbench/server/static/workbench.css` 的命中全部落在图标 / 插画作用域内。
- [ ] 6.3 空态三段式组件：新增 `.empty-state`（静物插画 + 一句说明 + 满宽圆角主按钮，按钮文案即动作，如「去组卷」），先落到记录中心空态；验证：三段齐备且按钮文案是动词短语，无「还没有……」式冷陈述。
- [ ] 6.4 阶段验收（插画资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝各空态在亮 / 暗两主题下的插画与按钮；确认插画笔触与图标笔触同源（同一线宽、同一圆角语言）。

## 7. 台灯与主题转场资产（可独立验收）

- [ ] 7.1 新增 `workbench/server/static/assets/illustrations/lamp.svg`（台灯，与第 6 组静物同一支笔），并在 DOM 中挂 `#theme-lamp` 容器与触发按钮（顶栏主题切换位）；验证：文件存在且容器 / 按钮可被定位到。
- [ ] 7.2 实现台灯转场：探出 ~180ms → 点亮（灯罩内亮起 + 暖色溢出）→ 涟漪从灯下扩散铺满 ~450ms → 灯收回，共 ~700ms；涟漪用放大的径向渐变遮罩做 mask，**只动 `transform` / `opacity`**，不阻塞交互、不改请求时序；验证：该转场的动画属性集合中只有 `transform` 与 `opacity`。
- [ ] 7.3 阶段验收（转场资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝亮→暗、暗→亮各录一遍完整 700ms 序列；确认 reduced-motion 下为直接切换、且转场期间可正常点击其它控件（`pointer-events` 未被遮罩吞掉）。

## 8. 关键反馈音效资产（可独立验收）

- [ ] 8.1 新建 `workbench/server/static/assets/audio/`，放入四个关键反馈短音效：答对、答错、完成、里程碑；每条时长 < 200ms（借鉴多邻国「完成 1 声 + 统计卡 3 声」的节奏，不喧宾夺主）；验证：4 个文件存在，逐个测时长 < 200ms 并记录数值。
- [ ] 8.2 绕过浏览器自动播放限制：首次音效必须挂在一次用户手势之后（首次交互时解锁 / 预热音频上下文），并给出控制台不报错的处理路径；验证：首屏加载后不发声且控制台无自动播放告警，首次点击后可发声。
- [ ] 8.3 声音偏好与 MIME：音效开关并入「声音与动效」偏好（第 9 组），不擅自播放；在 `workbench/server/app.py` 的 `CONTENT_TYPES`（L26-34）补 `.mp3` / `.ogg`；验证：关闭偏好后不发声；请求音频返回正确 Content-Type。
- [ ] 8.4 阶段验收（音效资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；确认音效不进入任何学习事实或持久化路径（无对应 API 调用、池内无新增记录）。

## 9. 设置视图与偏好存储

- [ ] 9.1 新增「工作台设置视图」页面：在 `workbench/server/pages.py` 新增 `settings_page()`，在 `workbench/server/app.py` 的 `_send_page`（L234-261）注册 `/w/{name}/settings` 分支；验证：请求该路径返回 200 且中栏渲染设置页（注册前为 404）。
- [ ] 9.2 左栏入口与导航稳定性：在 `_left_column`（L622-676）加入「设置」入口；同时修 `workbench/server/static/middle-navigation.js` 的 `updateActiveNavigation`（L53，按 index 匹配 nav-item）——改为按稳定 key 匹配，否则新增 nav 项会让选中态错位；验证：客户端换页后左栏选中项始终正确。
- [ ] 9.3 偏好存储（按工作区）：主题偏好、阅读字面、动效偏好、声音偏好写入 `localStorage`（key 含工作区名），**不写池、不发请求**；验证：两个工作区各自独立；grep 确认无对应 API 调用。
- [ ] 9.4 无 FOUC 应用主题：在 `pages.py` 的 `_base`（L1096）头部内联一段极小脚本，读取偏好即设 `data-theme` / `data-reading` / `data-motion` / `data-sound`；验证：刷新页面无浅色 / 深色闪烁（逐帧录屏确认）。
- [ ] 9.5 偏好语义边界：阅读字面只切换阅读面字族（界面层不变）；动效偏好覆盖系统 `prefers-reduced-motion`（三态：跟随系统 / 开 / 关）；验证：切换阅读字面后按钮与导航字体不变；动效三态行为符合预期。
- [ ] 9.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝设置视图的亮 / 暗两主题；确认整条设置链路零请求、零池写入。

## 10. 夜纸值集与暗色对比度

- [ ] 10.1 在 `workbench.css` 新增 `[data-theme="night"]` 值集：底色 `#1c1a16`、墨色反相为暖浅色，并重设纸面四层（仍靠圆角 + 柔影，不加描边）；验证：夜纸下 `getComputedStyle(document.body).backgroundColor` 为 `rgb(28, 26, 22)`。
- [ ] 10.2 暗色下三角色色同源、圆底图标降饱和提亮、渐变换更暗色阶与更弱高光（沿用同一套 SVG，不换资产）；验证：夜纸下图标与插画可见且不刺眼；资产文件数不变。
- [ ] 10.3 对比度复测：暖纸与夜纸两套下，正文 ≥ 4.5:1、次要文字 ≥ 4.5:1、非文本控件 ≥ 3:1；把实测值写成一张对照表随 PR 提交；验证：表中无低于阈值项（逐项重测 F08 §7 的现状对比表）。
- [ ] 10.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝6 类页面的亮 / 暗双主题对照；确认图谱页在两主题下均与基线一致（不随主题变化）。

## 11. 外壳几何与左栏导航

- [ ] 11.1 三栏几何单一真值：`#layout` 的 `grid-template-columns`（workbench.css:160、164）改为由 CSS 变量驱动，删掉 JS 里对列宽的覆盖路径（F02 D12 的 CSS / JS 双源问题）；验证：grep JS 中不再出现列宽字面量；拖动分隔条后布局仍正确。
- [ ] 11.2 清除死预留与退役化石：删掉 `#middle-page > .page-header { padding-right: 128px; }`（workbench.css:255）；删掉 `.scope-tray*` 全部规则（L178-234、L1197）与 `middle-navigation.js` 的 `updateScopeNames`（L62）；验证：`grep -rn "128px\|scope-tray" workbench/` 归零且页面无 JS 报错。
- [ ] 11.3 左栏导航语法：每项 = 静物图标 + 文字（第 5 组资产）；左栏 4 个分区加结构分隔，收敛下半截空纸；验证：5 个导航项均含图标，分区间距可辨。
- [ ] 11.4 左栏选中态：改为整行圆角色块（现为 1px 黑框，workbench.css:318-321）；验证：选中项无边框、整行浅色块、圆角与 `--radius-ui` 一致。
- [ ] 11.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝桌面 1555px 与宽 2040px 两档下的左栏 / 顶栏 / 中栏边距；确认中栏不再被 128px 预留夹住。

## 12. 顶栏与章节透镜

- [ ] 12.1 顶栏改三段式：左＝品牌方块 + 名字，中＝当前身份（工作区 / 课程 / 章节），右＝动作（主题切换、设置、其它）；重排 `pages.py` 的 `shell()` 顶栏（L71-85）；验证：三段 DOM 结构在页面上可辨，身份信息不再退化成最弱的一行小字。
- [ ] 12.2 章节透镜自绘下拉：`_chapter_lens`（pages.py:41-64）从裸 `<select>` 改为自绘圆角面板（阴影 + 分隔 + 每项显示章节名与知识点计数）；验证：面板展开正常且每项带计数。
- [ ] 12.3 自绘面板可用性：Esc 关闭、焦点归位、`aria-expanded` 同步、点击外部关闭；验证：键盘走查四项全过。
- [ ] 12.4 页面标题带统一规格（context / title / summary / actions 四段）并补齐当前完全缺失的动作区样式（F02 D14：`page-header-actions` 无规则）；验证：五类页面标题带一致，动作区有可见样式。
- [ ] 12.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝顶栏三段 + 章节面板展开态 + 五类页面标题带。

## 13. 练习页版式

- [ ] 13.1 题面成为一张独立的纸：`_paper_practice_html`（pages.py:198-235）内的 `#paper-question`（L216）从卡片内段落改为独立纸面（比卡片更亮 + 淡结构线），并加 24px 大号题号（像书的章节号）；验证：题号 computed `font-size:24px`，题面与卡片的层级差可辨。
- [ ] 13.2 解析与题面同级：`#paper-reference`（L221）改为同规格的另一张纸（17px 衬线 + 淡结构线），用小标题区隔；验证：解析 computed `font-size:17px` 且与题面同级。
- [ ] 13.3 作答区成为明显的分隔区：`#paper-answer`（L219）前加淡结构线 + 「你的作答」标签 + 墨块底；验证：题 / 答两段一眼可分。
- [ ] 13.4 题号导航冗余编码：`#paper-dots`（L215、workbench.css:1888）每个题号位加彩色圆点，已答 / 未答 / 不会三态各有几何形状 + 颜色（零可见文字，颜色 + 形状双通道）；验证：三态可辨且圆点带 `aria-label`。
- [ ] 13.5 setup 区、完成页与时间安排层级：`#paper-setup`（L203）、`#paper-completion`（L227）、`#practice-planning` + `_daily_plan`（L237）统一到新卡片规格与阅读面层级（时间安排降级为可展开的次级信息）；验证：三处层级一致，完成页容器可挂第 14 组的数字滚动。
- [ ] 13.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝练习全流程（setup → 题面 → 作答 → 解析 → 自评 → 完成页）；确认请求序列与载荷与基线一致（冻结项不变量）。

## 14. 连对反馈与分层庆祝

- [ ] 14.1 三级连对计数器 + 数字滚动：常驻练习页，档位＝灰 → 黄 → 黄→蓝渐变（对应多邻国的灰 → 绿 → 绿→蓝，我们用黄承载「当前做得顺」）；数字用 Ticker 方式滚动（vanilla rAF，只写 `textContent`）；验证：三档颜色可辨，数字滚动不引第三方库。
- [ ] 14.2 连对进度本身是动效 + 参数化横幅：进度以「火苗簇」逐簇点亮；5 连 / 10 连插播**一份**横幅，用参数化输入切不同数字（多邻国 `streakmidlesson_xinarow_31.riv` + 4 个输入的模式）；验证：横幅资产只有一份，两组参数产出不同文案。
- [ ] 14.3 连对负反馈：连对 > 4 时答错必须给明确负反馈（「连对中断」类提示），不得沉默；验证：构造连对 5 次后答错的场景，界面出现明确信号。
- [ ] 14.4 分层庆祝：日常交卷＝轻庆祝（完成页入场 + 数字滚动 + 一声音效）；只有全对 / 破纪录 / 章节首次完成才放大（再叠几何爆点 + 彩带 / 纸片飞散）；验证：日常与里程碑两种场景表现明显不同，且未出现全局背景 canvas。
- [ ] 14.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝连对 1 / 3 / 5 / 10 连四个时点 + 里程碑庆祝；确认庆祝全部在响应到达后触发，请求时序未变。

## 15. 知识点页

- [ ] 15.1 列表改分组卡片：`kps_page`（pages.py:368-408）按章节或状态分组，每组一个标题 + 组内圆角卡；验证：分组结构可见，条目仍可用 `data-kp-order` 保持课程顺序排序。
- [ ] 15.2 状态冗余通道：把现有文字标签（`state_labels` 的「重点练习 / 可以复习」，pages.py:378）改为彩色圆点（颜色主通道 + 几何冗余通道，零可见文字，圆点带 `aria-label` / `title`）；验证：列表中不再出现状态文字标签，圆点三态可辨。
- [ ] 15.3 正文阅读层：知识点详情正文套衬线阅读面 + **保留单侧结构线 2px**（`docs/PRODUCT-MANUAL.md:129-130` 硬性要求），结构线色随新体系取值；验证：结构线存在且宽度为 2px。
- [ ] 15.4 详情渲染与空态：`_render_markdown`（pages.py:923）输出接 `.reading` 层，表格有表头底色、列表符号不再被全局 `ul` 规则吃掉；知识点列表空态改第 6 组的插画 + 一句 + 满宽主按钮；验证：表格与列表渲染正确、空态三段齐备。
- [ ] 15.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝知识点列表（分组 + 圆点状态）+ 知识点详情（正文排版 + 单侧结构线）。

## 16. 记录中心

- [ ] 16.1 统计区改仪表盘卡片：`_summary_cards`（records.py:180）产出的四张卡各带一个迷你图（趋势线 / 环形）；验证：四卡各一图，数值与原实现一致（只读，不改口径）。
- [ ] 16.2 作答日历改热力方块：`_activity_calendar`（records.py:224）转置为 7 行 × 12 列、格约 13px，强度用填色**且**高度双编码；补「今天」标记与月份刻度；验证：双编码可辨，页面高度较基线显著下降。
- [ ] 16.3 作答明细改圆角卡片流：`_attempt_rows`（records.py:9）输出从带边框行改为圆角小卡流，不描边、靠留白与柔影分隔（**不用表格**）；六项字段（题目 / 判定 / 自评 / 评语 / 摘录 / 时间）一个不少；验证：字段无缺失且无 `<table>` 边框语义。
- [ ] 16.4 错题视图改错题卡片流（每题一张带摘要的卡：题面 + 错因）+ 收编判定徽章引入的契约外绿色 + 四个视图做视觉分级（这是只读历史页）；验证：错题卡摘要可见、grep 绿系 hex 归零。
- [ ] 16.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝记录中心 4 个视图（概览 / 练习 / 明细 / 错题）+ 零记录空态；确认记录页仍为只读、零新增请求。

## 17. 骨架屏与视图转场

- [ ] 17.1 换页转场必须是容器动画：`middle-navigation.js` 每次切页整体替换 `#middle-page` 的 innerHTML（L87 `middlePage.innerHTML = nextPage.innerHTML`），因此转场只能对 `#middle-page` 做 animation，**不能靠 JS 给子元素加一次性类名**（类名会被 innerHTML 替换冲掉）；验证：实现中无依赖一次性子元素类名的转场代码。
- [ ] 17.2 骨架屏：灰块 + 微光扫过（shimmer），容器替换期间展示骨架，消除「硬生生蹦出来」的空白；验证：切页时可见骨架帧。
- [ ] 17.3 状态三件套齐备：加载态带 `aria-busy`（不引 spinner 图标资源），空态 / 加载态 / 错误态各有组件（F08 D-06）；验证：三种状态各有可触发路径与对应渲染。
- [ ] 17.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝练习 ⇄ 知识点 ⇄ 记录三次客户端换页的中间帧。

## 18. 样板线走查与用户验收

- [ ] 18.1 跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）并把输出贴进交接记录。
- [ ] 18.2 截图走查（在池数据库副本 + 隔离注册表 + 独立端口上点检，**永不写真实池**）：范围＝练习页、知识点页、记录页、工作台设置视图及其余两页，各自的亮 / 暗双主题；每页留基线 / 新版对照。
- [ ] 18.3 图谱页零变化校验：`workbench/server/static/workbench.css:1497-1884` 与其图谱 `:root`（L1505 起）一行未改；对图谱页截图做逐像素比对，差异必须为 0。
- [ ] 18.4 提交用户验收：先重跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）确认全绿，再把样板线截图与新基线对照表（decisions.md「# 收口：最终基线」）一并提交；**验收通过前不启动第 19–25 组**（铺开段）。

---

## 第二段：铺开（样板线验收通过后）

## 19. 阅读层与 Markdown 渲染统一

- [ ] 19.1 建共享 `.reading` 版式层：长正文（题面、知识点正文、解析、记录摘录）共用一套排版规格（17px / 1.75 / 38em / 单侧结构线 / 表格表头底色 / 代码块 / 公式 / 图片）；验证：四处正文的 computed 规格一致。
- [ ] 19.2 统一服务端与客户端 Markdown 渲染器：`pages.py` 的 `_render_markdown`（L923）与 `paper-practice.js` / `practice-flow.js` 的客户端渲染，对同一源产出同一 HTML 结构；验证：同一段 Markdown 在服务端页与客户端渲染下 DOM 结构一致（对比序列化结果）。
- [ ] 19.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝题面 / 知识点正文 / 解析 / 记录摘录四处同源 Markdown 的排版对照。

## 20. 试卷列表页

- [ ] 20.1 试卷列表改卡片网格：每张卡显示标题、题数、状态圆点（`practice_sets_page`，pages.py:484）；验证：网格布局成立，卡内三要素齐全。
- [ ] 20.2 去掉试卷卡的 5px 黄带：现状**每张卡**都顶一条 5px 黄带，把语义黄降级成装订线；改用状态圆点承载状态，让黄色回到稀缺语义色；验证：该黄带规则在 CSS 中消失，卡片状态靠圆点表达。
- [ ] 20.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝试卷列表页（含空态插画 + 满宽主按钮）。

## 21. hub 首页

- [ ] 21.1 hub 布局改「最近使用置顶 + 网格」：现状是 22 张完全等权卡片、无排序无分组（F02 D8 / F02-P11）；重排为最近用的 4 个置顶大卡、其余在下方网格；验证：置顶区与网格区可辨，4 张卡的数据来源可追溯。
- [ ] 21.2 hub 卡片信息层级：课程名 22px 最大，三个计数 13px 一行排开，用小色点区分（蓝＝知识点、黄＝待复习）；验证：字号与色点可辨，计数含义与原实现一致。
- [ ] 21.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝hub 首页（含空态）；确认 hub 仍为只读目录、零新增请求。

## 22. Agent 右栏

- [ ] 22.1 会话列表可滚动：现状 `#ai-session-list`（workbench.css:611）无滚动容器（`overflow:visible` + 祖先 `overflow:hidden` ⇒ 被静默裁掉）；补内部滚动容器；验证：长会话列表可滚动到末条且不再被裁。
- [ ] 22.2 会话列表分组 + 圆角条目：按「今天 / 昨天 / 更早」分组，每组小标题 + 组内圆角小块（标题 + provider 圆点 + 日期）；验证：三组结构成立。
- [ ] 22.3 消息流改卡片：每条消息一张圆角卡（Agent 消息可展开详情）；**不得演化成常驻任务面板**（GLOSSARY 既有契约）；验证：卡片流可滚动且无常驻面板。
- [ ] 22.4 输入区、执行计划与活动浮层：输入框贴底、大圆角、聚焦变蓝 + 轻微抬起；执行计划改圆点时间线（圆点 + 细线 + 文字），工具调用折叠成 ≤240 字摘要（展开看详情）；活动浮层改右上角圆角小卡，可收起、活动结束即消失；验证：三者渲染与行为正确，摘要长度受限。
- [ ] 22.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝Agent 右栏（会话列表 / 消息流 / 输入区 / 活动浮层 / 执行计划）；确认右栏交互的请求序列与载荷未变。

## 23. 数据层微交互

- [ ] 23.1 负荷柱生长动画：逐柱错峰 24ms 生长；验证：生长过程可见且总时长落在场景档（240–520ms）内。
- [ ] 23.2 数字变化 / 统计块入场 / 图表切换：三类各配微交互；验证：三类均有实现，且在 reduced-motion 下降级为直切。
- [ ] 23.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝记录中心统计区与日历、练习页负荷条；确认动效不改数据、不改请求时序。

## 24. 文案清理

- [ ] 24.1 统一中文语气、消除中英混排：处理残留英文标签（如 `Agent activity`、`Artifact`、`Congratulations!` 及无衬线的状态键名）并保持语义不变；验证：走查页面无中英混排标签残留，改动前后语义逐条核对。
- [ ] 24.2 按少字原则删界面注释：能删的界面注释直接删除，而不是换成更漂亮的说明文字（P-1）；只保留承载操作必需的文字；验证：提交一张删除前后信息量核对表，逐条说明删除理由。
- [ ] 24.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝全部 6 类页面的文案；同步 `docs/PRODUCT-MANUAL.md` 对应章节（本组改了用户可见文案）。

## 25. 契约同步与最终走查

- [ ] 25.1 `docs/GLOSSARY.md`：改写「柔和蒙德里安 / Soft Mondrian」条目为「暖色 + 现代圆润」定义，并补入 13 条新名词（纸面层级、夜纸、冗余状态通道、主题偏好、阅读字面、动效偏好、声音偏好、工作台设置视图、静物插画、台灯转场、少字原则、图案适配原则）；验证：13 条词条齐全且措辞与 decisions.md 一致，「柔和蒙德里安」条目不再把「暖纸色 + 深色结构线」写成定义。
- [ ] 25.2 `docs/PRODUCT-MANUAL.md`：补「工作台设置视图」章节与文案清理后的用户操作说明；保留知识点正文「宽行距 + 单侧结构线」的既有硬性表述；验证：章节齐全且未与既有条目冲突。
- [ ] 25.3 `docs/ACTION-GRAPH.md`：登记新增动作（设置视图、主题切换、连对升级反馈）与退役动作（scope-tray 死预留清理）；验证：新增 / 退役 / 改级动作全部留痕。
- [ ] 25.4 `docs/ARCHITECTURE.md`：更新静态资产目录结构（新增 `assets/`、`fonts/`、设置视图样式与脚本）与设置视图路由；验证：文档里的目录树与仓库实际一致。
- [ ] 25.5 契约漂移登记：把审计发现但本轮不改的既有漂移登记到本变更目录下（建议行与每日计划队列无界面出口、「准确率」术语未定义且被列为 `_Avoid_`、完成练习数受最近 100 轮限制而作答次数无上限）；验证：三条全部登记，且本轮未擅自修复实现。
- [ ] 25.6 最终验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）并把输出贴进交接记录；截图走查（池数据库副本 + 隔离注册表 + 独立端口，**永不写真实池**）覆盖全部页面亮 / 暗双主题；确认图谱页逐像素零变化、请求与持久化零变化。

---

## Self-check

- [ ] 所有任务都是 `- [ ] X.Y` 复选框格式
- [ ] 编号连续、无重复（X 为组号，Y 在组内从 1 连续排到该组验收任务）
- [ ] 每条任务可验证（能看出改哪个文件、做什么、怎么算做完）
- [ ] 样板线与铺开两段之间有明确分界（`## 第一段：样板线` / `## 第二段：铺开`；第 18.4 条设用户验收关卡）
- [ ] 覆盖：token / 字体 / 动效 / 设置视图与暗色 / 外壳 / 练习页 / 知识点页与试卷页 / 记录中心 / Agent 右栏 / 文案 / 契约同步与走查
- [ ] 每组有验收任务，含 AGENTS.md 的四条验证命令
- [ ] 没有引入构建步骤、npm 或新框架
- [ ] 未修改任何产品代码（本文只落 `tasks.md`）
- [ ] SVG 资产（第 5、6、7 组）与音效资产（第 8 组）单列为可独立验收的任务组
- [ ] 知识图谱页零改动约束已落到具体任务（1.5 / 10.4 / 18.3）
