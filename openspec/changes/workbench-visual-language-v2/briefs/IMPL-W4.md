# IMPL-W4 — 第 22 组样板线验收关卡：底线守卫判定 + 可视化走查产物

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 22 组（22.1–22.x）**。
> **这是所有者的签字关卡。** 目标是**判定**，不是修代码。

## 前置（自己核实，不要相信任何人的口头汇报）
- 第 3 波（W2c / W3a / W3b / W3c / W3d / W3e）**已全部收工并提交**。
  动手前先 `git log --oneline -20` + `git status --porcelain` 核实工作区干净。
- 走查执行器在 `tools/walkthrough/`（上一波的 W3g 建）：
  `launch.py`（隔离服务）· `recorder.py`（请求序列 + 报告）· `shots.py`（对照截图）。
  **先读 `tools/walkthrough/README.md`** —— 怎么跑、前置条件、产物在哪。
- 上一轮审计留下的**改造前**基线截图在 `tmp/frontend-audit/00-baseline-*.png`（**gitignore**）。
  ⚠️ 那是**上一轮**（不是本轮起点）的快照，只能当参考，不能当严格基线。

## 硬约束
- **只读产品代码。** 验收 agent **不改任何产品文件**（`workbench/` 一律不动），
  **不改** `tasks.md` / `decisions.md` / `acceptance.md` / `docs/`。
  发现缺陷 ⇒ **写进报告**，由主会话决定怎么修。
  你唯一可以写的地方是 `tmp/acceptance/`（产物与截图）与
  `openspec/changes/workbench-visual-language-v2/acceptance-report.md`（**新建**一个文件）。
- **永不写真实池**：池副本 + 隔离注册表（`LESSONKIT_WB_HOME`）+ **独立端口（不要 3081）**。
- **以仓库根为 cwd 启动服务**。本机 `pip` 装着 `lesson-kit 0.1.0`，
  从别处启动会解析到 site-packages 的**安装快照**（表现为「新 token 全部取不到值」但**不报错**）。
  ⇒ 启动后必须比对：
  `curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c` 与
  `wc -c workbench/server/static/workbench.css` —— **两个数必须相等**，不等就换端口重启。
- **不动知识图谱的算法**（图谱 change 的 SI-0 判据：`tools/graph-layout-diff.js --diff` 必须仍为 0）。
- 截图/录屏要能区分「动效帧」与「降级帧」——
  **降级帧的终态必须与动效帧的终态逐像素一致**（这是 8.9 / 21.6 的铁律）。

## 必读
1. `tasks.md` 的 **第 22 组全文**（这是你的任务书，逐条执行）
2. `acceptance.md`（**你的判定标准全文**）：§0 底线守卫 G-1…G-8 · §1 对照截图 S-1…S-12 ·
   §2 关键帧 M-1…M-13 · §3 交互清单 §3.1–§3.8
3. `design-notes/walkthrough-harness.md`（执行器的设计：请求序列捕获、判定与报告、32 条风险）
4. `design-notes/layout-spec.md`（版式基线）· `design-notes/motion-spec.md`（分镜条与降级矩阵）
5. `decisions.md` 的 **A-1**（不压平卡片）· **A-2**（动效偏好优先级）· **A-8**（图谱不在本变更范围）·
   **A-19 / A-43**（图谱零变化怎么验）· **A-46**（骨架屏不进图谱页）

## 要交付什么

### 1. 底线守卫 G-1…G-8（**脚本化 + 留证**）
逐条执行，每条给出 **PASS / FAIL / 无法判定** + **证据**（命令输出 / diff / 截图）：
- **请求序列**：脚本化跑一遍练习，diff 请求**方法 / 路径 / 载荷键集合**（改造前后必须一致）。
- **持久化**：比对池中 `problem_attempts` / `feedback_events` / `practice_runs` 的**行数与关键列**。
- **学习投影 / 复习建议集合**：必须一致。
- **图谱页像素**：逐像素 diff **必须为 0**。
- **池 schema 零变更**。
- **装饰层 `pointer-events`** 检查（装饰层不得吃点击）。
- **焦点序列**：换页前后对比。
- 任何一条红 ⇒ **整体 FAIL**，并在报告首行写明。

### 2. 可视化走查产物（**所有者要看的**）
| 产物 | 内容 |
|---|---|
| 六类页面 × 亮/暗双主题 | 工作台 / 练习 / 知识点 / 记录中心 / 试卷 / 设置视图 —— **一页两份并排对照** |
| 动效分镜条 | 庆祝两档（日常 / 里程碑）/ 台灯转场四段 / 连对反馈 / 错误摆动 / 骨架扫光 |
| 降级对照帧 | 每个动效都要有 **reduced-motion 版**，且**终态逐像素一致** |
| 图谱页 | 像素零差异的证据（**不参与美化**，它是「不许变」的证明） |
| 夜纸全套 | 同一批页面的夜纸版 —— 夜纸**不是新色系**，是同一套三角色的第二套值 |

### 3. `acceptance-report.md`（**给所有者的一页纸**）
- 首行：**总体判定**（PASS / FAIL + 哪几条红）。
- G-1…G-8 逐条一行：判定 + 证据路径。
- S-1…S-12 逐条：判定 + 截图路径。
- M-1…M-13 逐条：判定 + 分镜条路径。
- 「**发现的问题**」清单：每条写清 **现象 / 复现步骤 / 涉及文件 / 建议修法（但不修）**。
- 「**本轮没验到的**」清单：诚实写明哪些判据无法判定、为什么。

## 验证
- 跑 AGENTS.md 四条验证命令（确认基线是绿的）：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json` ⇒ 差异必须 **0 条**。

## 落盘纪律与回报
- 产物落 `tmp/acceptance/`（截图 / 录屏 / 请求序列 / 池快照），
  报告落 `openspec/changes/workbench-visual-language-v2/acceptance-report.md`。
- 报告**要提交**（`git add` 只加那个报告文件；`tmp/` 不提交）。
- 最终回报（中文）必须复述：**总体判定 + G-1…G-8 逐条判定 + S / M 逐条判定** +
  **产物路径清单（每张截图、每条分镜）** + **图谱像素零差异的实测数字** +
  **四条验证命令结果** + **问题清单** + **没验到的清单**。
- 数字一律以**当场跑出来的命令输出**为准。**不要为了让报告好看而放宽判据。**
