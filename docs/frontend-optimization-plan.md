# 工作台前端：审查意见与优化方案（v3.1 · 三方交叉验证收敛；2 阶段制：阶段 1 已完成，阶段 2 一次交付）

> 日期：2026-08-16 · 审查方式：只读代码审查（前端实现 + DSH 运行实例实测 + 独立审查顾问交叉验证）
> 基准：`docs/DISCUSSION-RECORD.md`（专题 14–17、附录 B6）、`openspec/specs/workbench-ui/spec.md`（累积规范）、DeepSeek Harness 运行实例（http://127.0.0.1:3080/）实测设计系统
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

## 七、优化方案（2 阶段制：用户要求不分细碎阶段，一次交付一轮验证）

### 阶段 1：P0 修复（纯 JS/CSS/路由，无新功能）—— ✅ 已完成（2026-08-16，commit `792caeb`，157 测试全绿，冒烟通过，见 changelog/2026-08-16-frontend-phase0.md）
- F0 定义 `.hidden` 规则（P0-1）；F1 复位 answerBox.disabled（P0-2）；F2 bindFeedback 绑定当前消息（P0-3）；F3 会话末入口移出 composer 常显（P0-4）；F4 图谱 raw-HTML 路由（P0-5）

### 阶段 2：P1 契约与逻辑修复 + 观感对齐 DSH + 收尾（一次实施、一次验证）—— ✅ 已完成（2026-08-16，160 测试全绿，冒烟通过，见 changelog/2026-08-16-frontend-phase2.md）

**2.1 P1 契约与逻辑**
- KP 页 renderMath 初始化（P1-6）；评分提示与 attempt 语义（P1-7）；会话末过滤 unrated（P1-8）；再练同类清队列（P1-9）
- api.py 异步化 AI 任务（P1-10）；右栏折叠开关 + 1024 断点（P1-11）；反馈框“下一题（不反馈）”（P1-12）
- AI 最近题进 context（P1-13）：按待确认项 2 的决定执行或标注后置

**2.2 观感对齐 DSH（令牌 + 组件形态）**
- 令牌表按“二、对照表”右列更新（B6.10 按待确认项 1 的决定）
- 消息扁平化 + 用户气泡 + 内容列 736 居中（五-1/2）；composer 胶囊化（五-3）；主按钮黑底白字（五-5）；消息字号 16（五-6）
- 滚动条 / focus-visible / transition / reduced-motion（P2-23）

**2.3 收尾（极简，不做任何新功能）**
- 死代码清理（wbKpId / AI_KEY / data-workspace）；无障碍小项；attempt 语义修正；hub 标题中文化；图床 Content-Type 与缺图占位；md 渲染表格；pull n=1（P2-26）；ai_run ValueError 404（P2-27）；CURRENT_KEY 恢复（P2-28）；`__import__` 修正（P2-25）

**阶段 2 验证**：pytest 全绿（含新增断言）；openspec validate；3099 冒烟（两题连做 / 中途会话末 / 图谱两态 / AI 无 provider 优雅提示 / 任务轮询 / 折叠交互 / 窄窗 <1024）；与 3080 实例逐项目测比对；node --check

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

---

## 十一、v4 信息架构优化（2026-08-22）

### 目标

保留已确认的三栏工具形态和 DSH 浅色设计令牌，但以“任务导向的编辑式工作台”
重整层级：学习者先看见自己在哪里、这一页要完成什么，再阅读主内容和按语义收纳的辅助信息。

### 结构契约

- 顶栏：产品入口与工作区 / 课程 / 章节上下文。
- 左栏：工作区切换、页面导航、当前薄弱项三组信息。
- 中栏：context line、页面 H1、主内容或主动作、带标题的辅助区；卡片只用于独立内容单元。
- 右栏：AI 身份与上下文、操作、对话、输入四段；窄屏继续沿用既有收起行为。
- 练习页保持题目 → 作答 → 揭晓 → 可选反馈的连续流；会话末以待补评和下一步为主；知识点详情以正文为主，信号、关联题、调度为辅。

### 兼容与验证

- 不修改后端接口、路由、学习数据、DSH token、既有 DOM ID 或 `wb_session_*`、`wb_kps_*`、`wb_current_*` 语义。
- 共享脚本按页面实际节点绑定，避免非练习页因缺少练习控件中断；“再练同类”空结果显示 `暂无更多同类题。`，普通练习耗尽文案不变。
- 自动化覆盖工作区切换保留记录、会话末评分移除条目、再练同类新轮次与空结果、wiki 链接跳转；交付前执行 pytest、OpenSpec、JS 语法检查和 :3081 人工冒烟。

## 十二、v5 知识结构与练习会话（2026-08-22）

### 信息架构

- 题目拥有短标题和单一主题标签；左栏薄弱项、知识点索引和关联题以名称或标题为第一信息，ID 降为辅助信息。
- 图谱不是嵌套在中栏的独立产品：中栏只保留画布与最少控制，外层右栏在“知识点详情”和“AI 教师”之间切换。
- 图谱模型读当前 SQLite，而不是 `output/` 下的静态 HTML 快照；可编辑范围只限既有知识点正文、薄弱说明和当前学习状态。

### 练习阅读流

- 进入练习先选定“每题自评”或“完成后统一自评”，未选模式不拉题。
- 一次会话连续显示一张替换式阅读卡；每次拉题传递已见 ID，不追加聊天消息，也不重复同题。
- 每题模式为“作答 → 看解析 → 评分输入（1–5）+ 可选备注 → 保存并下一题”。统一模式只在结束题目阶段后集中评分。
- `跳到下一道题目` 和 `提前结束本次练习` 是会话级操作；前者不写记录，后者在统一模式进入集中评分。

### 记录与兼容

- 评分仍复用既有 feedback 行为；明确评分才创建 feedback、信号、进度和调度更新。
- 图谱状态是覆盖式当前值，手动修改不会追加 feedback event 或 learner signal；调度通过状态对应的既有评分规则更新。
- 路由、既有 feedback body 和 `wb_session_*` / `wb_kps_*` / `wb_current_*` 含义保持；会话值只兼容地扩展模式、已见题和待评分项。
- 本轮不增加筛选、题数、目标、深色主题、拖拽栏宽或 AI 教师能力。

## 十三、v6 关联题完整阅读（2026-08-25）

- 2026-08-26 修订：主题默认折叠，展开后直接显示短标题与完整题干，不再形成标题、摘要、disclosure 三层重复。
- `display_summary` 只保留为超过 500 字题干的可选兼容元数据，不在关联题区域渲染。
- 完整题干使用统一安全 Markdown 渲染，不做字符截断或省略；原始 ID 不作为用户文本。
- 展示元数据来自可追踪 sidecar 并显式回填 SQLite，打开页面不会调用 Agent 或产生学习记录。

## 十四、v7 原生力导向图谱（2026-08-25）

- 中栏图谱从固定百分比网格改为真实力导向画布：已有语义边提供弹簧力，节点之间有斥力与圆形碰撞，中心引力和阻尼负责收敛。
- 边将显式关系强度与共同正式题数量合成为牵引权重；共同题只增强已有边。反向或重复边合并，避免重复施力。
- 知识点以圆形节点加外置名称呈现；圆半径随正式题数量的平方根增长，学习状态继续用颜色区分。
- 搜索、状态筛选、容器尺寸变化与拖拽会重热模拟；支持节点拖拽、画布平移、滚轮/按钮缩放和适应画布。
- 动画由 `requestAnimationFrame` 驱动并在稳定后停止；减少动态效果环境使用同步稳定布局并只绘制一次。
- 所有位置与视图变换均在浏览器内存中，不写 SQLite、不建立浏览日志，也不改变图谱右栏既有编辑范围。

## 十五、v8 Agent 原生对话（2026-08-25）

- 右栏从“讲解 / 诊断”任务按钮改为普通 Agent 对话：顶部选择本机可用 provider 与当前/最近会话，中段显示成功问答和当前事件，底部输入与发送；运行中发送替换为停止。
- 每个会话锁定 Codex 或 Claude，并沿用其 CLI 原生 session；工作台只镜像成功问答、上下文锚点与变更摘要。
- 每轮只上传消息、路由、页面类型、对象 ID、筛选/选中状态、最近三个对象和显式 draft 开关；服务端从 SQLite 重新构建权威上下文。
- 练习草稿默认不提供给 Agent；知识点页带正文/状态/信号/调度/邻居/关联题，图谱页带筛选/选中节点/关系摘要。
- 每日新会话是默认关闭的浏览器本地偏好；最近十个会话按工作区隔离。取消、失败和 provider session 丢失均原样呈现。
- Agent 写入由 `wb data` 的显式命令治理；普通问答零写入。结构变化后允许保留 conversation id 的受控刷新。

## 十六、v9 富文本与信息架构收尾（2026-08-26）

- 富文本统一为零依赖安全子集：标题、段落、列表、引用、代码、强调、安全链接、wiki、数学和工作区图片；服务端与客户端以同一组向量保持一致。
- Agent 右栏默认是完整历史会话列表；新建先选 Provider，创建后 Provider 锁定；标题只接受首轮成功结果的显式 metadata，用户重命名后不再覆盖；删除只移除 Lesson Kit 镜像。
- 图谱右栏改为学习看板，只显示状态、正式题数、邻居/关系、信号、调度和知识点深链；正文、薄弱说明和关联题全文由正式知识点页承载，状态快速编辑沿用覆盖式 graph/state。
- 每页控制保持单一主动作，低频图谱工具收进紧凑视图区域，避免解释文字、表单和重复保存按钮形成“驾驶舱”密度。

## 十七、v10 最小 Agent 对话（2026-08-26）

- 默认视图是完整历史会话列表，新建入口进入一次性 Provider 选择；创建后 Provider 锁定。
- 聊天态只显示返回列表图标、消息、输入和运行中的停止；删除身份、上下文、Provider 设置、每日新建和旧 explain/diagnose 控制台。
- 重命名与删除移至列表行菜单，删除只移除 Lesson Kit 本地镜像。

## 十八、v11 日用就绪界面（2026-08-26）

### 学生信息边界

- 左栏、知识点页和图谱不再把 signal type、weight、weakness score、scheduler state、repetitions、ease 或手动三态编辑交给学生解释。
- 只保留直接行动语言：存在明确薄弱证据时为 `重点练习`；没有当前负证据但已到期时为 `可以复习`；其余不做掌握声明。
- 图谱右栏收敛为知识点名称、行动提醒和 `打开知识点`，完整证据继续供排序、CLI 与 Agent 权威上下文使用。

### 练习可靠性与移动布局

- 页面初始化从既有 sessionStorage 恢复模式、当前题、已见题和统一评分队列；刷新和同标签页往返不重置会话，也不制造学习记录。
- 练习卡与统一评分卡以 `display_title` 为主文本；重复动态控件使用唯一 ID 和隐藏可访问标签；非法评分不发请求。
- 知识点页只有一个 `练习此知识点` 主动作，进入该知识点限定的连续去重练习；关联题仍是纯阅读。
- 窄屏只保留中栏，左导航和右对话改为抽屉；顶栏提供两个图标入口。错误必须显示在当前可见的练习区、Provider 选择区或聊天区。

### 图谱可读性

- 完整图仍是默认视图，但连通分量分别运行既有力模拟，孤立节点单独排列后再打包到画布。
- 每个非平凡分量从六个确定性初始布局中择优，比较顺序固定为边交叉数、标签碰撞数、空间浪费；reduced-motion 直接绘制最优稳定布局。
- 残余相近边使用浅曲线；选中节点时一跳保持完整、二跳次级、更远拓扑淡化，点击背景恢复全图。
- 本轮不加入路径、桥节点、社区、Graph Findings 或参数面板，图谱坐标和交互继续不落库。

## 十九、v12 灵动图谱与阶段冻结（2026-08-27）

- 保留六起点择优作为稳定种子，删除分量运行期边界；全部节点进入统一力场，形成可跨网络传播的拖拽和关系弹性。
- 弹簧中心距拆为节点半径与语义间隙：强边约 72px、弱边约 144px；圆形碰撞独立保证 24px 净空，标签长度不再撑大物理节点。
- 逻辑画布无边界。边缘拖拽移动镜头，释放后落点为当前页面内弱锚点；fit、pan、zoom 均不改写坐标。
- 稳定图只有数像素确定性呼吸，后台与 reduced-motion 停止。聚焦在原地展开一跳/二跳而不自动居中。
- 标签按 core、正式题量、稳定 ID 排序，默认 6 个，缩放后 12 个或全部；搜索、悬停、选中和一跳邻居覆盖该限制。
- 图谱占满中栏剩余视口；线条只在遮挡时选择确定性浅曲线。本阶段归档后不再主动扩展产品功能。

## 二十、v13 图谱聚拢控制（2026-08-27）

- 在现有紧凑图谱工具栏中暴露全局中心引力滑槽（0–100，默认 30）。高值让所有节点更靠近中心，低值允许整体摊开。

## 二十一、v14 图谱稳定性与学习型方向记录（2026-08-27）

- 图谱稳定后完全静止，移除持续呼吸；拖拽、筛选、聚焦、尺寸变化和聚拢调节才重热统一力场，体验接近 Obsidian 的安静画布。
- 聚拢滑槽保留现有交互但扩大中心力范围，使高值明显收拢、低值明显分散；不改变关系边的语义距离、自由拖拽或非持久化边界。
- “模仿 Obsidian”在后续不只指视觉：未来可让图谱形态辅助学习，并在右栏提供少量基于掌握证据的结论与证据入口。证据口径、形态映射和参数展示另立 OpenSpec，本轮不猜测实现。
- 滑槽只改变当前统一力场并触发重热，不改变关系弹簧、节点净空、坐标、SQLite 或学习记录。
