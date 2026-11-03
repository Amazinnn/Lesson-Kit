# UI-B · 文案·术语·冗余·注释型字段缺陷审计报告

> 审计对象：lesson-kit 工作台前端用户可见文案
> 权威依据：`component-spec` §3.7 零注释型字段 / `copy-table.md` / `docs/GLOSSARY.md`
> 方式：**纯静态读代码**（Read / Grep）。无浏览器工具，未做可视化核验，也未记录 E 类流程发现（E 类需真实点击，见文末说明）。
> 已逐条 Read 确认行号与内容一致；引用的行号/原文均为当前检出状态。
> 范围文件：pages.py / records.py / experience_page.py / agent-ui.js / practice-flow.js / paper-practice.js / part-practice.js / kp-experience.js / runtime.js / live-editor.js / middle-navigation.js

---

### B-01 · 记录-备考视图标题直接写「掌握度估计（能力分）」，用了明令禁止的「掌握度/能力分」
- 严重度: 高
- 证据: `workbench/server/records.py:789` —— `<div class='card exam-ability'><h3>掌握度估计（能力分）</h3>`
- 违反: copy-table §0.3 硬约束 1「不得引入掌握度」；GLOSSARY「个人难度 / Learner Difficulty」_Avoid_「掌握度、统一能力分、自动升降题目难度」；「行动提醒」_Avoid_「掌握度」
- 为什么是缺陷: 产品全线禁止向学生呈现「掌握度/能力分」这类未定义且带断言的口径，这里却作为一个栏目名正面写出，且「能力分」不是 GLOSSARY 术语。
- 建议方向: 改为无断言的证据式表述（如「作答分布」或直接去掉该块标题的评分含义），去掉「掌握度」「能力分」字样。

### B-02 · 记录-备考视图「每日正确率」用了明令禁止的「正确率」
- 严重度: 高
- 证据: `workbench/server/records.py:798` —— `<h3>每日正确率</h3>`
- 违反: copy-table §0.3 硬约束 1「不得引入正确率」；GLOSSARY「覆盖 / Coverage」_Avoid_「正确率」；「行动提醒」_Avoid_「分数」
- 为什么是缺陷: 「正确率」是被显式列为不得出现的承诺性指标词，出现在用户可见栏目标题里与契约直接冲突。
- 建议方向: 改为事实陈述口径（如「每日作答」并只显示 `对/错` 计数），去掉「正确率」。

### B-03 · 小问解析区「你的答案（Agent 提炼）」括号内暴露内部机制（已清理项的残留）
- 严重度: 高
- 证据: `workbench/server/static/part-practice.js:33` —— `line('你的答案（Agent 提炼）',g.extracted_answer)`
- 违反: §3.7 禁「（内部机制）」括号注释；P-1 少字原则；任务书已清理清单「（Agent 提炼）」的未删净残留
- 为什么是缺陷: 「（Agent 提炼）」是给学生解释后台由谁产出的实现细节，用户不需要知道，且属任务书点名已清理却仍存在于 part-practice.js 的残留。
- 建议方向: 删掉括号注释，仅保留「你的答案」。

### B-04 · 小问解析区「参考来源 → Agent 独立推导」暴露 provenance 元信息（已清理项的残留）
- 严重度: 高
- 证据: `workbench/server/static/part-practice.js:35` —— `line('参考来源','Agent 独立推导')`
- 违反: §3.7 禁 provenance 元信息；任务书已清理清单「解析纸 参考来源/Agent 独立推导」的未删净残留
- 为什么是缺陷: 「参考来源/Agent 独立推导」是内容生产 provenance，对学生无操作价值；任务书点名已清理但 part-practice.js 仍渲染。
- 建议方向: 整行删除；如确需披露，并入折叠的诊断区而非正文标签。

### B-05 · 小问状态串里硬拼「答案：」「过程：」字段名前缀
- 严重度: 高
- 证据: `workbench/server/static/part-practice.js:8-9` —— `+ (g.answer_conclusion ? ' · 答案：' + labels[g.answer_conclusion] : '')` / `+ (g.process_conclusion ? ' · 过程：' + (… '未提供过程' : labels[g.process_conclusion]) : '')`
- 违反: §3.7 禁「字段名: 值」硬前缀
- 为什么是缺陷: 在一行状态文本里用「答案：」「过程：」把内部结论维度名当界面标签硬拼，是典型的注释型「字段名: 值」堆砌。
- 建议方向: 状态点/几何承担维度区分，或改成自然语句；去掉「字段名：」前缀。

### B-06 · 备考视图暴露原始 IRT 参数 theta 与机器知识点 id
- 严重度: 高
- 证据: `workbench/server/records.py:744` —— `f"<span class='exam-theta'>{row['theta']:.0f}</span>"`（同行 `exam-kp` 直接输出 `row['kp_id']`）
- 违反: §3.7 显人读名不显机器 ID；GLOSSARY「行动提醒」_Avoid_「调度参数」；「调度」参数永不对学生露出
- 为什么是缺陷: 直接把能力模型参数 `theta` 数值与 `dmath-ch06-kp-NNN` 形式的机器 id 渲染给学生，既无解读口径又暴露内部 id/参数。
- 建议方向: 知识点显示人读名；theta 一类模型量不直接露出（如需展示改为无承诺的相对表述）。

### B-07 · 完成页 kicker 用英文口号「A LITTLE FURTHER, TOGETHER.」
- 严重度: 高
- 证据: `workbench/server/pages.py:522` —— `<p class='section-kicker'>A LITTLE FURTHER, TOGETHER.</p>`
- 违反: copy-table §4 中英混排（界面文案统一中文，仅产品名/契约英文名可留）；17.4「文案语气 → 简洁功能陈述」；P-1 少字原则
- 为什么是缺陷: 全大写英文口号式 kicker，既非产品名也非契约词，属零信息装饰文案（庆祝应由动效承担），且违反界面统一中文。
- 建议方向: 删除该 kicker（庆祝由完成页动效/数字承担），或改为一句中文功能陈述。

### B-08 · 试卷判定「判定：正确 / 判定：错误」用「字段名: 值」硬前缀（存疑）
- 严重度: 中
- 证据: `workbench/server/static/paper-practice.js:733` —— `parts.push("<p class='micro-verdict ok'>判定：正确</p>")`；`:734` —— `…>判定：错误</p>`
- 违反: §3.7 禁「字段名: 值」硬前缀；任务书已清理清单「判定：」前缀
- 为什么是缺陷: 「判定：」是把内部字段名当界面标签的硬前缀。存疑：copy-table §2（行 996）对 Q-34/Q-35「判定：正确/错误」判为「留（契约词「判定」）」，与任务书「已清理」口径冲突，故标存疑，请所有者裁决。
- 建议方向: 徽标/状态点承担判定，正文只留「正确 / 错误」；若契约要求保留「判定」词，去掉冒号前缀形态。

### B-09 · 完成页统计句同一句内混用「判定正确」与裸「错误」两种判定口径
- 严重度: 中
- 证据: `workbench/server/static/paper-practice.js:1508-1510` —— `"共 " + stats.total + " 题；判定正确 " + stats.correct + " 题，错误 " + stats.wrong + " 题；不会 " + stats.stuck + " 题；待评价 " + stats.pendingRatings + " 题。"`
- 违反: 判定状态词两套口径；GLOSSARY「判定 / Verdict」取值（对 / 错）
- 为什么是缺陷: 同一句里「判定正确」与「错误」不对齐（一个带「判定」前缀一个不带），且用「正确/错误」而 GLOSSARY 判定取值为「对/错」（records R-02/R-03 亦用「对/错」），同一概念三种写法。
- 建议方向: 统一判定词口径（对 / 错），并列项保持同一句式。

### B-10 · 小问状态机把批改管线内部状态（待批改/批改中/已批改/批改失败/等待揭晓…）直接暴露给学生
- 严重度: 中
- 证据: `workbench/server/static/part-practice.js:3` —— `var labels = {correct:'正确',wrong:'错误',partially_correct:'部分正确',needs_confirmation:'待确认',unprovided:'未作答',pending:'待批改',running:'批改中',completed:'已批改',failed:'批改失败',not_requested:'未请求',hidden:'等待揭晓',submitted:'已提交',withdrawn:'已撤回'}`；`:6-10` 拼成 `已提交 · 不会 · 批改中 · 答案：… · 正确` 一行
- 违反: §3.7 显人读名不显机器状态；用户不需要知道实现细节；判定取值应为 GLOSSARY「对 / 错」而此处用「正确/错误」
- 为什么是缺陷: 把内部批改管线状态与判定混在一行状态串里直出，且用「正确/错误」而非契约「对/错」；part-practice.js 整文件未纳入 copy-table 清单，属契约外裸奔文案。
- 建议方向: 对学生只保留「已提交 / 未作答 / 不会 / 对 / 错」等契约状态，批改中间态用状态点承担，判定词统一为「对 / 错」。

### B-11 · 小问汇总行用「批改 / 答案 / 过程」字段名前缀堆计数，且无标签时回落机器键
- 严重度: 中
- 证据: `workbench/server/static/part-practice.js:69` —— `text+=' · '+({grading:'批改',answer:'答案',process:'过程'}[d])+' '+(labels[k] || k)+' '+s[d][k]`
- 违反: §3.7 禁「字段名: 值」硬前缀、显人读名不显机器 ID
- 为什么是缺陷: 「批改 X N」「答案 Y N」「过程 Z N」是把内部维度名当界面标签的硬前缀堆叠；`labels[k] || k` 在标签缺失时直接露出机器键 `k`。
- 建议方向: 用人读维度名或图形分组；去掉裸机器键回落（无标签就不显示该项）。

### B-12 · 小问预览「详情」按钮（题号格「详情」已清理项的残留）
- 严重度: 中
- 证据: `workbench/server/static/part-practice.js:83` —— `details.textContent='详情'`
- 违反: 任务书已清理清单「题号格「详情」按钮」的未删净残留；P-1 少字原则
- 为什么是缺陷: 任务书点名已清理的「详情」按钮仍存在于 part-practice.js 预览路径，属未删净残留。
- 建议方向: 与全站一致——预览区常驻或用明确的展开/收起控件与 aria-expanded 文案，去掉孤立「详情」字样按钮。

### B-13 · 记录-备考视图 kicker「备考」与标题「备考倒排」同字冗余
- 严重度: 中
- 证据: `workbench/server/records.py:785-786` —— `<p class='section-kicker'>备考</p>` + `<h2>备考倒排</h2>`
- 违反: §3.7 条目不与组名同字、卡片页头不盖注释型 kicker；copy-table §3「kicker 与正标题同义是结构性冗余」
- 为什么是缺陷: kicker「备考」与紧邻 h2「备考倒排」同字，属结构性冗余（copy-table §3 把同类 kicker 全列删除，但漏了这条备考视图 kicker）。
- 建议方向: 删除 kicker，仅保留 h2「备考倒排」。

### B-14 · 经验面板空态「暂无关联题目」与 copy-table 定稿措辞漂移
- 严重度: 中
- 证据: `workbench/server/static/kp-experience.js:93` —— `"<p class='muted'>暂无关联题目</p>"`
- 违反: copy-table E-15 定稿「这个知识点暂时没有关联题目。」；文案契约一致性
- 为什么是缺陷: 可选题清单空态在 copy-table 有定稿措辞，实现写成更短的「暂无关联题目」，属实现与文案契约不一致（漂移），且与同文件 `:122`「暂时没有经验时…」等长句风格不统一。
- 建议方向: 与 copy-table E-15 定稿对齐，或反向更新 copy-table 登记当前措辞，二者取一，避免双口径。

### B-15 · 备考倒排用「薄弱点」，GLOSSARY 权威术语为「弱项 / Weak Point」
- 严重度: 中
- 证据: `workbench/server/records.py:732` —— `f" · 薄弱点 {plan.get('weak_kp_count', 0)}</p>"`；`:740` —— `" 分钟，优先薄弱点与真题。</p>"`；`:791` —— `<h3>弱项排序</h3>`（同视图内两种叫法）
- 违反: GLOSSARY「弱项 / Weak Point（weakness score）」为唯一权威名；术语不一致
- 为什么是缺陷: 同一备考视图里既写「薄弱点」又写「弱项」，同一概念两种叫法，且「薄弱点」不是 GLOSSARY 权威名。
- 建议方向: 统一为 GLOSSARY「弱项」。

### B-16 · 备考视图「回忆质量分布 / 每日投入」暴露 SM-2 调度内部概念（存疑）
- 严重度: 中
- 证据: `workbench/server/records.py:794` —— `<h3>回忆质量分布</h3>`；`:796` —— `<h3>每日投入</h3>`；`:754` 等级映射 `{forgot:'忘了',hard:'勉强',good:'记得',easy:'轻松'}`
- 违反: GLOSSARY「调度」参数永不对学生露出；「复习负荷 / Review Workload」为权威口径（存疑）
- 为什么是缺陷: 「回忆质量」是 SM-2 调度的内部量（recall quality），直接作为栏目名与等级词（忘了/勉强/记得/轻松）露出，属把调度内部概念暴露给学生。存疑：该视图整体为实验性备考视图，是否面向学生待核。
- 建议方向: 若面向学生，改为「复习负荷」等权威口径，去掉 SM-2 内部等级词；若纯内部诊断，移出学生可见范围。

### B-17 · 练习反馈「我的评价：★★★☆☆（3/5）」同一评分双通道重复呈现
- 严重度: 中
- 证据: `workbench/server/static/practice-flow.js:968-969` —— `"<p>我的评价：" + "★".repeat(feedback.rating) + "☆".repeat(5 - feedback.rating) + "（" + feedback.rating + "/5）</p>"`
- 违反: 同一信息相邻重复呈现；P-1 少字原则
- 为什么是缺陷: 星标个数已编码 3/5，紧随又写「（3/5）」，同一评分用两套符号相邻重复，属展示冗余。
- 建议方向: 保留一种编码（星标或数字），去掉另一个。

### B-18 · 备考倒排区 kicker「备考倒排」与同节 aria-label 重复（存疑）
- 严重度: 低
- 证据: `workbench/server/pages.py:463-465` —— `aria-label='备考倒排'` + `<p class='section-kicker'>备考倒排</p>`
- 违反: 同名三写（函数名/aria-label/kicker）；注释型 kicker
- 为什么是缺陷: 可访问名与可见 kicker 同字，可见层再重复一次无信息量文字。存疑：该节标题由 JS 后续填充，kicker 或承担标题职责，故降为低。
- 建议方向: 二者留一——可见标题或可访问名，不重复。

### B-19 · 备考倒排空值句重复「倒排」且指向绕
- 严重度: 低
- 证据: `workbench/server/records.py:735` —— `"<p class='exam-count-line'>未设置考试日期——在练习页的备考倒排里设置后开始倒排。</p>"`
- 违反: 文案简洁/语焉不详（一句内两次「倒排」，且指向另一个页面的同名模块）
- 为什么是缺陷: 一句里「倒排」出现两次，读起来拗口；且要求学生跨页去设置，信息不足。
- 建议方向: 改为一句动作导向（如「先在练习页设置考试日期」）。

### B-20 · runtime 更新守卫提示「更新等待中：正在等待当前任务完成」同义重复
- 严重度: 低
- 证据: `workbench/server/static/runtime.js:68` —— `notice('更新等待中：正在等待当前任务完成')`
- 违反: 同一信息重复；P-1 少字原则
- 为什么是缺陷: 「更新等待中」已表达"在等"，后半句「正在等待…完成」同义复述，无新增信息。
- 建议方向: 合并为一句（如「当前任务结束后更新」）。

### B-21 · 复习负荷摘要占位直出「共 0 项」
- 严重度: 低
- 证据: `workbench/server/pages.py:1656` —— `"<strong id='workload-total'>共 0 项</strong>"`
- 违反: 展示冗余/占位直出（未取数即显示 0）
- 为什么是缺陷: 服务端渲染即硬编码「共 0 项」，JS 取数前会把 0 当真实值闪现，属占位当数据。
- 建议方向: 初始留空或骨架占位，取数后再填。

---

## E 类 · 交互流程合理性

无条目。E 类要求在浏览器里真实走通操作路径后记录（「必须真点过」），本组为纯静态审计、无浏览器工具，未做任何点击，故不臆造流程缺陷。E 类主责在 C 组。

## 工具与环境说明（诚实汇报）

- **无浏览器工具**：本会话仅具备 Read / Grep / Bash(只读)，无 Playwright / browser_* 工具，故未做可视化核验，未起服务、未起浏览器。
- 全部条目均为静态读代码所得，行号与原文已逐条 Read/grep 复核。
- 存疑项已在正文标注「存疑」（B-08 / B-16 / B-18），不硬凑。

## 统计

共 21 条（高 7 / 中 10 / 低 4）。

- 高：B-01 掌握度估计（能力分）、B-02 每日正确率、B-03（Agent 提炼）、B-04 参考来源/Agent 独立推导、B-05 答案：/过程：硬前缀、B-06 暴露 theta+机器 id、B-07 英文口号 kicker
- 中：B-08～B-17
- 低：B-18～B-21

> 集中提示：`workbench/server/static/part-practice.js` 整个文件未纳入 copy-table 文案清单，却承载大量学生可见文案，且仍残留任务书点名「已清理」的「（Agent 提炼）」「参考来源/Agent 独立推导」「详情」三项（B-03 / B-04 / B-12）；`records.py` 的 exam 备考视图（VIEWS 含 "exam"，`pages.py:960` 渲染，reachable）集中出现「掌握度/正确率/回忆质量/薄弱点」等违禁与不一致术语（B-01 / B-02 / B-15 / B-16）。建议优先处置这两处。
