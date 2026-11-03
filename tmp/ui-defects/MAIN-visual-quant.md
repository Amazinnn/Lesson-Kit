# 主会话可视化/量化审计发现（Playwright 实测，非静态读代码）

> 采集人：主会话（唯一浏览器实例）· 服务 `http://127.0.0.1:3081/w/lesson-kit/practice?paper=ps-001`
> 采集方式：browser_evaluate 量化 DOM（getBoundingClientRect / computedStyle / overflow）+ 截图目视
> 视口：亮纸 1536×?、1440×900、夜间主题；窄屏 375→实测 clientWidth 562

---

## M-01 · 命中区普遍 <44px，系统性违反 §3.1 ≥44×44 硬约束（高危，成簇）

**证据（browser_evaluate，亮纸练习页，clickableTotal=84，其中 30 个命中区 <44px）**：
实测可点元素 getBoundingClientRect（w×h，均 <44）：

| 元素 | 选择器/文案 | 实测尺寸 |
|---|---|---|
| 顶栏品牌链接 | `a.brand` "lesson-kit" | 132×**22** |
| 工作区切换器 | `select#workspace-select` | 300×**34** |
| **章透镜开关 checkbox** | `input#chapter-lens-switch` | **13×13** |
| 顶栏搜索按钮 | `button#topbar-search` "搜索" | 66×**40** |
| Agent 对话顶栏按钮 | `button#mobile-ai-toggle` | 99×**40** |
| **左栏 5 个导航项** | `a` 练习/试卷/知识点/知识图谱/记录 | 232×**32** |
| **设置入口** | `a#setting-view-toggle` | 256×**22** |
| **优先回看条目（3 个）** | `a` 乘法规则/加法规则/计数对象… | 214×**22** |
| 开始今日题单 | `button#start-today` | 114×**40** |
| **继续练习主按钮** | `button#paper-start` | 86×**40** |
| **试卷列表链接** | `a.outline.button-link` | 56×**19** |
| 目标与时间安排（折叠） | `summary` | 1540×**22** |
| 添加目标（折叠） | `summary#goal-editor-summary` | 1540×**22** |
| 考试日期输入 | `input#exam-date-input` | 108×**20** |
| 目标起止日期输入（2 个） | `input#goal-start-date`/`#goal-deadline` | 512×**20** |
| 目标类型下拉 | `select#goal-kind` | 512×**34** |
| 保存目标 | `button#goal-submit.primary.sm` | 68×**28** |
| 让 Agent 代填 | `button#goal-assist-send.outline.sm` | 95×**28** |
| Agent 新建会话 | `button#ai-new-session.outline.sm` | 44×**28** |
| 重命名会话（✎） | `button.ghost.sm.icon-only` | 40×**40** |

- **违反**：component-spec §3.1「命中区 ≥44×44 CSS px（无障碍硬约束）」；live spec `workbench-ui`「Focus visibility and contrast floors」配套可达性；所有者明令「唯一不可让步：命中区 ≥44px 与焦点环」。
- **为什么是缺陷**：主按钮（继续练习 40px）、左栏导航（32px）、设置入口（22px）、优先回看条目（22px）、顶栏品牌（22px）、多个表单输入（20px）、链接（19px）**成片低于 44px**，触屏/运动障碍用户难命中；这是系统性基线尺寸问题，非个别元素。
- **建议方向**：在 `workbench.css` 用基类统一把交互元素最小命中区抬到 44×44（注意 skill 教训：`:where()` 特异度 0 会被 base class 盖住，尺寸修饰符靠源顺序取胜）；对内联小控件（13px checkbox、20px input）给透明扩展命中区。
- **严重度：高**（硬约束 + 成簇 30 处）

## M-02 · 开关控件 track 内容溢出容器

**证据（亮纸练习页，overflowX 检测）**：
- `label.lk-switch--labelled`：scrollWidth 98 > clientWidth 92
- `span.lk-switch__track`：scrollWidth 38 > clientWidth 32（顶栏「对话视图」「夜纸」两处开关均现）

- **违反**：§4.10 开关形态（track 应完整容纳 thumb 不溢出）；通用「无横向溢出」。
- **为什么是缺陷**：开关滑轨内容宽于容器，视觉上 thumb/轨道被裁或溢出，窄容器下更明显。
- **建议方向**：核对 `.lk-switch__track` 宽度与 thumb 定位，确保 track 不小于内容盒。
- **严重度：中**

## M-03 · 开关 input 被 `aria-hidden` track 拦截指针事件（Playwright 直点超时）

**证据**：`browser_click` 定位 `#topbar-theme`（role=switch checkbox）**超时 5000ms**，Playwright 日志：`<span aria-hidden="true" class="lk-switch__track"> intercepts pointer events`，重试 9 次仍被拦截；改点外层 `label:has(#topbar-theme)` 才成功。
- **违反**：§3.6 / 可达性——可视化装饰层（aria-hidden track）覆盖在真实 input 上，纯坐标/自动化/辅助技术直点 input 会被拦截；依赖 label 代理点击。
- **为什么是缺陷**：命中目标与视觉目标不一致；任何不经过 label 的点击路径（含部分辅助技术、自动化、触屏边缘）会被 aria-hidden 层吃掉。
- **建议方向**：确保 track 不拦截指针（`pointer-events:none` 于装饰层）或 input 覆盖其上承接点击。
- **严重度：中**

## M-04 · 响应式窄屏测试不确定（非确定缺陷，记录待验）

**证据**：`browser_resize` 到 375×667，但 `document.documentElement.clientWidth` 实测 **562**（非 375）；页面级 `scrollWidth==clientWidth`（无整页横向滚动）。但大量元素右边界到 **1137**（右栏 Agent 会话列表）、左栏导航 `left≈-519`（完全移出左屏）。
- **判读**：左右 rail 在窄屏移出视口，但存在 `mobile-nav-toggle`(☰) 与 `mobile-ai-toggle`(Agent 对话) 移动端开关 ⇒ **疑似有意的抽屉设计**，非确定缺陷。
- **结论**：`存疑`。需确认窄屏下 ☰ 抽屉能否正常唤出左栏、Agent 对话开关能否唤出右栏，且 `clientWidth 562 ≠ 375` 需查明（可能 body 有 min-width）。
- **严重度：低（存疑）**

## M-05 · 服务渲染 pages 与分支不一致（**非设计缺陷，记录以免误报**）

**证据**：`curl /w/lesson-kit/practice?paper=ps-001` 实测：`count-badge=1`、`待回看=1`、`偏好与主题=0`、`>设置</a>=1`（旧版条目）、`详情=0`。但 worktree `pages.py` grep `count-badge|count_badge|待回看` **=0**（已删净，HEAD=4ca1d5a2）。
- **判读**：静态 JS/CSS（part-practice.js、workbench.css）服务的是**我的分支**，但 **pages.py 服务端渲染的内容解析回了主检出旧版**（左栏「设置」套「设置」、优先回看计数徽标、题面「来源：」等）。这正是记忆所记「runtime_source 解析回 primary」坑。
- **结论**：**不是 UI 设计缺陷**，是 runtime 服务来源问题。**禁止**把「count-badge 存在/设置套设置/来源：前缀」当新缺陷报（它们在分支已修 B2/B3/A5）。已在本轮给 4 个 subagent 的消息里明确此坑。
- **建议方向**：让 daemon worker 真正 import worktree 的 pages.py（核查 worker cwd/PYTHONPATH/runtime_source），或热重载不要回退到 primary。
- **严重度：中（runtime，非 UI 设计）**

---

## 统计
主会话量化/可视化确认缺陷：**M-01（高危，含 30 子项）、M-02、M-03** 共 3 条主缺陷（M-01 内含成簇 30 元素）；M-04 存疑待验；M-05 为 runtime 服务问题非 UI 设计缺陷。

---

## E 类 · 交互流程合理性（船与木桩）— 主会话端到端实操发现

> 说明：以下在 daemon 当前 serve 的 UI（原始版，含详情按钮/计数徽标）上实走确认；部分条目我们的 `feat/workbench-display-redundancy-cleanup` 分支已修（标注「分支已修」），但 daemon 回退到主检出旧版故仍可见。E1/E3/E4/E6 为**分支也未处理的真流程缺陷**。

### E-01 · 单页三套并列练习入口，用户不知该走哪条（船与木桩典型）
- 严重度: 高
- 证据: `/w/lesson-kit/practice` 单页并存：①「今日题单」卡（12 题 + 「开始今日题单」主按钮）②「鸽巢原理 · dmath 演示卷」卡（6 题 + 「继续练习」主按钮）③ 6 个题号格（0–5）+「暂停练习/提交试卷」工具栏。三套练习入口同屏并列，且有两个都是主按钮（primary）。
- 为什么绕: 用户面对「开始今日题单 / 继续练习 / 点题号格」三条路径，不知哪条是主路径；两个 primary 按钮互相抢主次。
- 建议自然路径: 单一主练习入口 + 明确主次（今日题单为主，已有卷降为次要或折叠）。
- 分支是否已处理: **未处理（真流程缺陷）**

### E-02 · 题号格旁独立「详情」按钮（悬停已有预览仍多一按钮）
- 严重度: 中
- 证据: 每个题号格（第0–5题）旁各挂一个独立 `button "详情"`（ref f1e238/241/244/247/250/253）；悬停/聚焦题号格本就弹小问状态卡。
- 为什么绕: 看小问状态要点额外「详情」按钮，而悬停已可预览——多一个并排按钮，点击/触摸才钉住，路径冗余。
- 分支是否已处理: **分支已修（A1，详情按钮已删、钉住迁到弹卡）**；daemon 回退旧版故仍可见。

### E-03 · 今日题单「用时预估 48 / 45 分钟」自相矛盾
- 严重度: 低
- 证据: 「今日题单」副标题「共 12 题 · 用时预估 48 / 45 分钟」——预估用时 48 **超过** 预算 45，仍照常展示无提示。
- 为什么绕/缺陷: 预估超预算却无任何标记或建议（截取/顺延），用户看到 48>45 不知该不该做。
- 建议自然路径: 超预算时提示「超出今日预算 X 分钟，可截取/顺延」。
- 分支是否已处理: **未处理（真缺陷）**

### E-04 · 顶栏「对话视图」switch 与「Agent 对话」按钮语义重叠
- 严重度: 中
- 证据: 顶栏并存 `switch "对话视图"`（ref f1e15）与 `button "Agent 对话"`（ref f1e24），二者都控制/指向右栏 Agent 对话区。
- 为什么绕: 同一右栏两个入口、两种交互（开关 vs 按钮），用户不知该用哪个、二者状态如何联动。
- 建议自然路径: 合并为单一入口或明确分工（一个是显示/隐藏，一个是聚焦/新建）。
- 分支是否已处理: **未处理（真缺陷）**

### E-05 · 批改失败后的恢复路径依赖孤立「重试批改」
- 严重度: 中
- 证据: 小问 1 状态「已提交 · 批改失败」，textarea 残留 "q"，「提交小问」「不会」均 **disabled**，唯一出路是下方孤立的「重试批改」按钮（ref f1e295）。
- 为什么绕: 提交后失败，主操作按钮全禁用，恢复动作「重试批改」远离作答区、无提示为何失败/该不该改答案，用户易卡住。
- 建议自然路径: 失败态就地给出明确恢复指引（重试 + 是否可改答）。
- 分支是否已处理: **未处理（真缺陷）**

### E-06 · 右栏每个会话常驻 ✎ / × 两个操作按钮
- 严重度: 低
- 证据: 右栏「历史对话」每条会话旁常驻 `✎ 重命名对话` + `× 删除本地会话`（ref f1e316/317 等），3 条会话共 6 个小图标按钮常驻。
- 为什么绕: 低频操作（重命名/删除）常驻占用视觉，且 × 紧邻会话标题易误删；更自然的是悬停显出或收进「…」菜单。
- 建议自然路径: 悬停显出或收进溢出菜单。
- 分支是否已处理: **未处理（真缺陷）**

### E-07 · 「你的作答」标签位置游离
- 严重度: 低
- 证据: `paragraph "你的作答"`（ref f1e296）单独出现在小问作答区与「上一题/下一题」导航之间，看似孤立无邻近内容。
- 为什么绕/缺陷: 标签与其内容关联不明显（snapshot 中它无紧邻可读内容），疑似布局/关联缺失。
- 结论: 存疑（需结合解析全貌确认）。
- 分支是否已处理: 未处理（存疑）

### E 统计
E-01/E03/E04/E05/E06/E07 = **分支未处理的真流程缺陷 6 条**；E-02 = 分支已修（daemon 回退旧版故可见）。
