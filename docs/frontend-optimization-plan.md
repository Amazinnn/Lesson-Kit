# 工作台前端：审查意见与优化方案（v3 · 三方交叉验证收敛：协调方 / Claude Code / 独立顾问）

> 日期：2026-08-16 · 审查方式：只读代码审查（前端实现 + DSH 运行实例实测 + 独立审查顾问交叉验证）
> 基准：`docs/DISCUSSION-RECORD.md`（专题 14–17、附录 B6）、`openspec/changes/workbench-ui/specs/workbench-ui/spec.md`、DeepSeek Harness 运行实例（http://127.0.0.1:3080/）实测设计系统
> 范围：只评审 `workbench/server/pages.py`、`workbench/server/app.py`、`workbench/server/api.py`、`workbench/server/static/workbench.js`、`workbench/server/static/workbench.css`；不改后端行为契约（domain/data/bridge/cli）。

---

## 一、结论摘要

三栏骨架（左导航 / 中页面 / 右 AI 栏）符合讨论记录，页面清单齐全（练习、知识点、图谱、会话末自评），极简范围守住。但当前版本是“有骨架、没章法”：

1. **练习核心链路有 4 个致命断点**：`.hidden` 规则缺失导致全部显隐编排失效（一切控件常显）；第 2 题起作答框永久禁用；第 2 题起评分/卡点点击全部无效；会话末自评入口随 composer 隐藏而不可达。
2. **知识图谱页是摆设**：iframe 指向返回 JSON 的 API，产物存在时 iframe 里显示 JSON 文本。
3. **“照搬 DSH”没照搬对**：workbench.css 令牌是旧值/近似值，与运行实例实测有多处方向性偏差（bg-base、brand、label-dimmed、阴影、气泡、输入条、消息形态）。
4. 少量操作死路与语义错位（看答案后无“直接下一题”、再练同类必“已练完”、AI“发送”恒等于讲解、评分后提示“未反馈”）。
5. 好消息：架构、API 契约、极简范围都守住了；多数问题集中在 JS/CSS/路由层，可在不动后端契约的前提下修完。

---

## 二、审查基准：DSH 运行实例实测设计系统（对照表）

以下为 http://127.0.0.1:3080/ 构建产物中实测的令牌值（非文档推断）：

| 令牌/组件 | DSH 实测值（light） | workbench.css 现状 | 偏差 |
|---|---|---|---|
| bg-base（页面底色） | #ffffff（bluish-00） | #f9fafb | ✗ 反了 |
| 侧栏底色（sidebar-fill） | #f9fafb（bluish-50） | 左栏用 bg-layer-2 #f1f2f4 | ✗ |
| brand-primary（主按钮底） | #0f1115（近黑） | #3964fe（蓝） | ✗ |
| 蓝色 accent（business-primary） | #4176e6（deepseek-500） | 无此角色 | 缺 |
| label-primary / secondary / tertiary | #0f1115 / #61666b / #81858c | 同 | ✓ |
| label-dimmed（占位符等） | #e1e5ee（浅灰，比 tertiary 更浅） | #a8adb4（深灰，比 tertiary 更深） | ✗ 方向反 |
| label-caption | #adb2b8 | 无 | 缺 |
| border-l1 / l2 | rgba(0,0,0,.04) / .10 | .06 / .10 | 近似 |
| shadow-lv1 | 0 2px 4px rgba(0,0,0,.05) | 0 1px 2px rgba(0,0,0,.06) | ✗ |
| shadow-lv3 | 0 0 1px rgba(0,0,0,.2) + 0 0 4px .02 + 0 12px 32px .08 | 0 12px 32px .12 + 0 4px 12px .08 | ✗ |
| 用户气泡 | 右对齐、radius 22、填充 deepseek-50 #edf3fe、padding 10px 16px、max-width 525px/82%、字号 16/24 | 全宽 .msg.user #eef3ff、radius 12 | ✗✗ 形态完全不同 |
| 输入条（composer） | 浮起胶囊：radius 22、边框 l2-darkmode-thin、bg input-major、shadow-lv2、字号 16/24、底部 8px | 贴底普通 textarea + 按钮行 | ✗✗ |
| 按钮 | md 高 36 / radius 18；sm 高 28 / radius 14；primary 黑底白字 hover #43454a；ghost hover 用 interactive-bg-hover | 同尺寸；primary 蓝底 | 部分 ✗ |
| pill 标签 | 高 24 / radius 12 / 字号 12 | 无此组件 | 缺 |
| 布局几何 | 侧栏 280 默认（264–420 可拖），右栏 360 默认（300–520），中心 ≥640，视口 <1024 自动折叠侧栏；frame 满高 grid | 固定 232 / 1fr / 320，无断点无折叠 | ✗ |
| 消息形态 | 助手消息扁平无边框；只有用户消息是气泡；内容列 ≤736 居中 | 每条消息都套 .card 边框 | ✗✗ |
| 其他 | 自定义细滚动条、focus-visible、100ms hover transition、prefers-reduced-motion、菜单 radius 12 shadow-lv3 | 无 | 缺 |

> 注：讨论记录 B6.10 确认的令牌清单（bg-base #f9fafb、brand #3964fe 等）与运行实例实测不符——大概率抄自启动页 fallback 值（AppRoot 的 boot 样式用 #f9fafb/#3964fe 作兜底）。**更新令牌 = 修改已确认的 B6.10，需用户点头**（见“待确认项”）。

---

## 三、功能问题（按优先级）

### P0（必须修：核心链路断裂）

1. **`.hidden` 规则缺失，显隐编排全废**
   - 位置：`workbench.css`（缺失）+ `workbench.js`（9 处 classList）+ `pages.py`（3 处初始 hidden）
   - 问题：`.hidden` 在 CSS 中未定义。后果：未开始练习就可见作答框/“看答案”/“没时间批改”（无题时点击 → `currentProblem` 为 null → TypeError）；start-area 永不隐藏（可重复开课、双会话）；提交后“提交作答”按钮仍可见；composer-actions 全程可见。
   - 修复：CSS 加 `.hidden { display: none !important; }`（或更窄的作用域规则）；并按 F3 调整按钮归属。
2. **第 2 题起作答框永久禁用**
   - 位置：`workbench.js` `submitAnswer` 处理器与 `loadNext`
   - 问题：提交作答后 `answerBox.disabled = true`；`loadNext` 载入下一题只清 value、不恢复 disabled。
   - 修复：`loadNext` 中 `answerBox.disabled = false`。
3. **第 2 题起的评分/卡点点击全部失效**
   - 位置：`workbench.js` `bindFeedback`
   - 问题：`stream.querySelector(".feedback:last-of-type")` 按文档序返回第一条满足条件的 .feedback——永远是第一条消息的反馈框；新消息的反馈框无监听，stuckStep 也绑定旧消息的块。
   - 修复：绑定当前消息元素：`showAnswer` 中 `addMessage` 后对返回的消息节点调 `bindFeedback(msgEl)`，内部用 `msgEl.querySelector(".feedback")` 与 `msgEl.querySelectorAll(".solution-block")`。
4. **会话末自评入口不可达（操作死路）**
   - 位置：`pages.py` `practice_page` + `workbench.js` `loadNext`
   - 问题：`#goto-session-end` 是 `#composer` 的子元素；补上 .hidden 规则后，池耗尽分支先 `showComposer(false)` 再显示按钮 → 按钮随父容器一起隐藏；中途也无任何结束会话入口（专题 15：自评时机=会话末，用户决定何时是会话末）。
   - 修复：按钮移到 composer 之外（#stream 之后独立元素），并常显或置于顶栏；用户可随时去会话末。
5. **知识图谱 iframe 显示 JSON 文本**
   - 位置：`pages.py` `graph_page`（iframe src=/api/w/{name}/graph）+ `api.py` `graph_artifact`（返回 {"html": ...} JSON）
   - 问题：iframe 加载 JSON 响应，产物存在时显示一坨 JSON，不是图谱。
   - 修复：新增原始 HTML 输出路由（如 /api/w/{name}/graph/html 以 text/html 返回 `path.read_text()`），iframe 指向它；产物缺失时维持现有生成指引（该指引正确，保留）。

### P1（应该修：功能/契约缺口）

6. **知识点详情页公式不渲染**
   - 位置：`workbench.js`（renderMath 仅在 addMessage/aiAdd 调用）+ `pages.py` `kp_page`
   - 问题：服务端渲染的 .math span 无 JS 触发 KaTeX；KP 正文 LaTeX 显示为原始文本（spec 要求 rendered math）。
   - 修复：页面加载时对 `#middle .math` 执行一次 renderMath。
7. **评分后提示“已记录：未反馈（不影响进度）”——误导**
   - 位置：`workbench.js` `finishProblem`
   - 问题：评分路径 result="skip"，确认消息说“未反馈”，实际 feedback/信号/排程都已更新；用户以为白评了。
   - 修复：按实际动作出消息（rated → “已记录评分”；skip → “未反馈”）；attempt 的 result 语义（评分题记 rated/correct/wrong 而非 skip）在 B3.5 中未定义，标注“可考虑”待协调方定，本轮先只改消息（顾问建议）。
8. **会话末列表包含已评分项 → 可重复评分**
   - 位置：`workbench.js` session-end 块
   - 问题：filter 只排除 skipped；流程中已评（state=rated）的题仍列出，再点 1–5 会二次写 feedback/信号。
   - 修复：过滤改为 `state === "unrated"`。
9. **“再练同类”必然“本组题目已练完”**
   - 位置：`workbench.js` practice-similar
   - 问题：不清 SESSION_KEY 就跳转 practice；新会话继承全部 exclude，弱项组无新题 → 立即弹“已练完”死循环。
   - 修复：跳转前清 SESSION_KEY（新会话语义）；池中确无同类题时提示“暂无更多同类题”。
10. **AI 任务同步阻塞 HTTP 请求**
    - 位置：`api.py` ai_run + `bridge/runner.py`（provider 在请求线程内同步执行）
    - 问题：POST /ai/{op} 直到 provider 跑完才返回；耗时超浏览器超时 → fetch reject → 显示“桥接不可用”，轮询从未启动，任务结果不可达。
    - 修复（不动 bridge）：api.py 用 threading.Thread/ThreadPoolExecutor 包住 run_ai_task，立即返回 job_id；轮询逻辑原样。注意两点：(a) provider 默认超时 300s（providers.py），线程化前 POST 最长阻塞 5 分钟；(b) 整段 run_ai_task 入线程后，job 文件在响应返回后 ~毫秒级才落盘，首个 poll 可能 404——`pollJob` 需把 404 视为 pending 容错重试，而非“状态查询失败”。
11. **右栏 AI 对话不可折叠**
    - 位置：`pages.py`/`workbench.css`
    - 问题：spec 明确 right AI conversation column (collapsible)；现状固定 320px 常驻。
    - 修复：右栏头部加折叠开关，折叠为 0 宽；配合 1024 断点自动折叠。
12. **看答案后没有“直接下一题（无反馈）”入口**
    - 位置：`workbench.js` showAnswer/bindFeedback
    - 问题：反馈是纯可选（spec: never required），但看答案后唯一推进方式是“没时间批改”（语义误导）或评分/卡点。
    - 修复：反馈框内加“下一题（不反馈）”ghost 按钮 → finishProblem("skip","","unrated")，会话末仍可补评。另：会话末评分时应一并补记 attempt/answer_text（answer_text 从 SESSION_KEY 读取），否则会话末补评不落尝试记录（顾问补充）。
13. **AI 上下文“最近题”没有真的给到 Agent**
    - 位置：`workbench.js` updateAiContext（只显示）+ api.py/runner.py（context 只有当前题）
    - 问题：专题 16 要求最近几道题作为重点提供给 Agent；现状仅右栏文本显示，任务 context 不含最近题。
    - 修复（需协调方决策）：见“待确认项 2”。

### P2（可修可不修：打磨）

14. `richText` 不支持题目正文图片/wiki 链接（M6 problems.figure_paths 前端不渲染）；补 JS 侧 image/wiki 替换。
15. 服务端 md 渲染不支持表格/引用/嵌套列表（`_render_markdown`）；KP 正文含表格时显示原始 | 文本。
16. AI 栏“发送”恒等于 explain（语义混淆）；AI 消息刷新即失（AI_KEY 写入从不读取，死代码）。
17. `window.wbKpId`、`#ai-context data-workspace` 死代码/死属性，清理。
18. 图床 Content-Type 硬编码 image/png（`app.py` `_send_figure`），jpg/svg 图会错型；按后缀映射。另：B5.4 的“缺图 404+UI 占位”占位未实现，img 应加 onerror 换占位文本（顾问补充）。
19. math 正则 server/client 不一致（`_MATH_RE` vs richText 的 $ 规则），统一（去掉 ^ 锚，行中 display math 亦可转）；且 $$ 块当前用 inline span 渲染，应为块级（顾问补充）。
20. hub 页英文标题（“Workbenches”/“lesson-kit” title）违反中文界面要求；顶栏 brand 非链接、无返回 hub 入口（顾问补充）。
21. 弱项列表反馈后不刷新（左栏为页面加载时快照）；可 /feedback 成功后轻量重拉。
22. 无障碍：solution-block 无 role/tabindex/键盘事件；无 focus-visible；评分按钮无 title/aria-label。
23. 无 transition/prefers-reduced-motion（DSH 有 100ms hover 过渡与 reduced-motion 尊重）。
24. 深色主题缺失（范围外，不推荐本轮做）。
25. `pages.py` `kps_page` 用 `__import__("datetime").date.today()` 的非常规写法（line 75）——违反“代码简洁”工程约束，改 `from datetime import date`（Claude Code 评审新增）。
26. pull n=5 但只消费 problems[0]（`workbench.js` loadNext）：每次浪费 4 题、被丢弃题可被重新拉取；n 改 1 或缓存返回列表逐题消费（顾问新增，范围外实现细节）。
27. `api.py` `ai_run` 对未知 problem_id 抛 ValueError → 未捕获 → 500 裸堆栈（app.py 只捕 KeyError）；捕 ValueError 转 404（顾问新增）。
28. 页面加载不恢复 CURRENT_KEY：切到知识点/图谱页后 AI 上下文显示“无”、讲解/诊断只提示“先打开一道题”；启动时 load(CURRENT_KEY) 恢复 currentProblem（纯显示优先，不违反“只跟随不确认”）（顾问新增）。

---

## 四、设计逻辑问题（非代码 bug，是章法问题）

1. **会话状态机缺“结束”态**：练习会话只有“进行中”与“池耗尽”两个出口；用户想中途结束（去自评）无路（P0-4 同源）。会话边界应由用户定义（专题 15：理想是巨无霸长对话，现实由会话末自评兜底）。
2. **反馈语义分层不清**：1–5 评分（经 /feedback 驱动信号+排程）、卡点（经 /practice stuck 驱动排程+attempts）、没时间批改（仅记录）三者 UI 并列但后效不同，且评分后 attempt 记 skip（P1-7 同源）。建议反馈框内分组：评分行 / 卡点标记 / 跳过行。
3. **“再练同类”语义悬空**：B6.5 指它是“由薄弱项延展的生成/近似练习”，而 generate 桥操作后置（B7）；当前实现用“重拉同组”冒充且必死（P1-9）。generate 落地前应明确降级语义：“再练同类（新会话）”。
4. **AI 上下文显示与投喂脱节**（P1-13 同源）：右栏显示“当前题+最近 2 题”，任务却只带当前题。要么真投喂，要么改文案，二选一。
5. **KP 详情页信息层级**：正文/信号/关联题/调度四个 h2 平铺；可优化为正文主区 + 状态卡 + 关联题列表（极简优先，可后置）。

---

## 五、布局 / 观感问题（对照 DSH 实测）

1. **消息列无宽度约束**：中栏消息横贯整个 middle；DSH 内容列 ≤736 居中、气泡 ≤525px/82%。练习页应对齐：内容列 max-width 约 736px 居中。
2. **消息形态全错**：每条消息（含系统提示）都套边框卡片；DSH 助手消息扁平、只有用户消息是右对齐蓝气泡。建议 .msg.teacher 去边框去背景；.msg.user 改右对齐 radius-22 气泡（#edf3fe）。
3. **composer 形态全错**：普通 textarea 贴底；DSH 是浮起胶囊（radius 22、shadow-lv2、16/24 字号、按钮行在胶囊内）。建议重做为胶囊卡片，随内容列居中，sticky bottom。
4. **三栏几何固定**：232/1fr/320 无断点；窄窗压扁中栏。建议：侧栏 280（拖拽可后置）、右栏 360、视口 <1024 右栏自动折叠（配合 P1-11）、中心最小 640 的简化版。
5. **主按钮蓝色扎眼**：DSH 主按钮近黑 #0f1115、hover #43454a，蓝色只作 accent（链接、选中态、业务状态）。照搬后“开始练习/看答案”等主按钮应为黑底白字。
6. **字号层级**：聊天/题目正文 DSH 用 16/24；workbench 全局 14px。建议 UI 控件保持 14，消息正文与输入条 16。
7. **细节缺失**：自定义滚动条、focus-visible 环、hover 过渡、placeholder 用 label-dimmed（#e1e5ee）、评分 1–5 建议做成 pill 按钮组。

---

## 六、明确不需要动的地方（防过度修改）

- 三栏结构本身（左导航/中页面/右 AI）——用户两次确认的布局，不重构。
- 极简范围：不加摘要、看板、图表、批量揭晓（B7 后置项一律不碰）。
- KaTeX vendored 零构建方案、sessionStorage 会话方案（B6.11 已知取舍）、服务端渲染架构。
- 中文界面、hub 页（仅修英文标题）、工作区下拉切换。
- 后端一切行为契约（domain/data/bridge/cli/registry）与 API 路由清单。
- 图谱缺失时的生成指引（内容正确，仅修复 iframe 目标）。
- 现有测试文件与 openspec 契约。

---

## 七、优化方案（分阶段，每阶段独立交付验证）

### 阶段 0：P0 修复（纯 JS/CSS/路由，无新功能，1 个提交）—— ✅ 已实施（2026-08-16，commit `792caeb`，157 测试全绿，冒烟通过，见 changelog/2026-08-16-frontend-phase0.md）
- F0 定义 `.hidden` 规则（P0-1）
- F1 `loadNext` 复位 answerBox.disabled（P0-2）
- F2 bindFeedback 绑定当前消息元素（P0-3）
- F3 “去会话末统一自评”按钮移出 composer 且常显（P0-4）
- F4 图谱 iframe 指向原始 HTML 输出（P0-5）
- 验证：pytest 全绿；冒烟两题连做 / 中途会话末 / 图谱页两态；为 .hidden 规则与 graph 响应 Content-Type 各补一条廉价测试断言（防回归，顾问建议）

### 阶段 1：P1 契约与逻辑修复
- KP 页 renderMath 初始化（P1-6）；评分提示与 attempt 语义（P1-7）；会话末过滤 unrated（P1-8）；再练同类清队列（P1-9）
- api.py 异步化 AI 任务（P1-10）；右栏折叠开关 + 1024 断点（P1-11）；反馈框“下一题（不反馈）”（P1-12）
- 待协调方决策项：AI 最近题进 context（P1-13）、auto-grade（spec 要求但池内无机器可判题型时留空提示）
- 验证：冒烟 AI 无 provider 优雅提示、任务轮询、折叠交互

### 阶段 2：观感对齐 DSH（令牌 + 组件形态）
- 令牌表按“二、对照表”右列更新（待确认 B6.10 更新）
- 消息扁平化 + 用户气泡 + 内容列 736 居中（五-1/2）
- composer 胶囊化（五-3）；主按钮黑底白字（五-5）；消息字号 16（五-6）
- 滚动条 / focus-visible / transition / reduced-motion（P2-23）
- 验证：与 3080 实例逐项目测比对

### 阶段 3：收尾（可选、极简）
- 死代码清理（wbKpId / AI_KEY / data-workspace）；无障碍小项；attempt 语义修正；hub 标题中文化；图床 Content-Type；md 渲染表格
- 不做任何新功能

---

## 八、待确认项（不阻塞阶段 0/1，需用户或协调方点头）

1. **B6.10 令牌更新**：把已确认令牌清单改为运行实例实测值（bg-base #ffffff、brand #0f1115、蓝 #4176e6 作 accent 等）。这是用户可感知的视觉变化，按 AGENTS.md 兼容边界需先问。推荐：采纳实测值（这才是“照搬”的本意）。
2. **AI 最近题上下文投喂**：涉及 bridge/runner 边界（任务文件禁改 bridge）。若批准，走 openspec 增量（api.py 传参或 runner 加参）；否则维持显示-only 并改文案。
3. **auto-grade**：spec 写了 machine-gradable 自动判分，池内题型需确认是否有可机判结构；没有则 spec 该条暂空（不实现），注明原因。
4. **右栏折叠默认态**：默认展开（对齐现状）或默认折叠（窄屏）——推荐默认展开 + 记忆折叠状态。

---

## 九、验证清单（每阶段交付时执行）

- `python -m pytest tests -q`（全绿，含 tests/workbench/test_ui_routes.py）
- `openspec validate workbench-ui --strict`
- 冒烟（--port 3099）：/、/w/{ws}/practice、/w/{ws}/kps、/w/{ws}/kp/{id}、/w/{ws}/graph、/w/{ws}/session-end、/static/workbench.css、/static/katex/katex.min.js
- 手动用例：两题连做（作答框可输入、第二题评分生效）；中途去会话末（可达、仅列未评）；评分后会话末不再出现该题；再练同类进入新会话；图谱产物存在时 iframe 显示图谱、缺失时显示指引；AI 无 provider 优雅提示；右栏折叠/展开；窄窗（<1024）右栏自动折叠。

---

## 十、与 Claude Code 的收敛记录

### 第 1 轮（2026-08-16）：Claude Code 只读交叉评审（claude_stream_bridge，--tool-mode read）

- **事实核查**：本方案 P0-1~5、P1-6~13、P2-14~24 全部确认，均给出文件:行号独立证据（workbench.js line 197/239/65 等），无一“不成立”；“无新增 P0/P1”。
- **新增 1 项**：P2-25 `pages.py` `__import__("datetime")` 写法（line 75）→ 改标准 import。
- **方案质疑**：无过度设计指控；阶段划分、优先级、范围边界（三栏不动/极简/后端契约不动/B7 后置不碰）全部认可；B6.10 令牌更新独立给出与本文一致的处理建议（采纳实测值 + 先问用户）。
- **结论**：Claude Code 明确“前次评审覆盖完整、可作为协调方实施蓝本”——**双方收敛，方案 v2 定稿**。
- 遗留分歧：无。需协调方/用户决定的项见“八、待确认项”（B6.10、AI 最近题投喂、auto-grade、折叠默认态）。

### 第 2 轮（2026-08-16）：独立只读审查顾问终稿（subagent 487349ae）交叉验证

- **确认**：.hidden 缺失、图谱 iframe JSON 两个 P0（与本文一致）；“不需要动”清单与本文一致；后端分层/API/池契约无可挑剔；152 绿测试全为字符串断言，无法发现 JS/CSS 层问题（测试盲区）。
- **顾问漏报**：answerBox disabled 不复位、bindFeedback `:last-of-type` 绑定错位两项 P0——二者已由 Claude Code（行号证据）与协调方代码核查各自独立确认，**保留**。
- **顾问独有发现（已并入）**：P2-26（pull 浪费 4 题）、P2-27（ai_run ValueError→500 裸堆栈）、P2-28（CURRENT_KEY 不恢复）、缺图占位（并入 P2-18）、hub 入口缺失（并入 P2-20）、display math 块级（并入 P2-19）、会话末补记 attempt（并入 P1-12）、/practice result 语义标注“可考虑”（并入 P1-7）。
- **结论**：三方（协调方 / Claude Code / 独立顾问）交叉验证收敛——问题全集 5×P0 + 13×P1 + 28×P2，**无任何事实分歧**；方案 v2 定稿并含全部三方发现。

### 后续轮（实施时）：每阶段完成后，用同一桥接以 read-only 复核改动，确认未越界后再提交。
