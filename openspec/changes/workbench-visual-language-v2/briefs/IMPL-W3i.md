# IMPL-W3i — 走查执行器：种子补全 + 音效探针（把 3 条 PENDING 变成可判定）

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` **第 22 组**。
> **只改 `tools/walkthrough/` 下的文件。**

## 背景
第 22 组的第一轮走查（`tmp/wt-run-7/`）跑完了，**G-1…G-8 底线守卫全 PASS**，
但有 4 条判据因为**证据不足**而判 PENDING —— 机器**只给数值与证据，不替人签字**。
本任务就是**把这几条的证据补齐**，让它们从 PENDING 变成可判定。

### 目标一：3.7-2（记录不足 98 条）· 3.4-6（会话列表内容不足）· M-3（未触达里程碑档）
这三条 PENDING 的根因都是**测试数据不够**：
- `3.7-2`：判据要 **98+ 条记录**的列表滚动流畅 ⇒ 池里 `problem_attempts` 只有几条；
- `3.4-6`：判据要 `#ai-session-list` 的 `scrollHeight > clientHeight` ⇒ 会话列表太短；
- `M-3`：判据要**里程碑档**（本轮全对 / 章节首次完成）⇒ **没有触达那一档的种子数据**。

⇒ 给走查执行器加一个**种子（seed）能力**：
- 在**隔离副本**里播下足够的记录 / 会话 / 一轮**全对**的练习；
- ⚠️ **绝不写真实池**（`pool/dmath.db`）—— 一切播种只发生在**副本**里
  （现成的隔离机制：`tools/walkthrough/launch.py` 的池副本 + `LESSONKIT_WB_HOME` 隔离注册表）；
- 播种脚本**可复跑、可参数化**（条数、是否全对），并把**播了什么**写进产物
  （报告里要能看出「这一轮用了多少条记录、是不是全对轮」）。

### 目标二：3.3-1「答题后没有观察到音效」
**这条要查清楚是「真没响」还是「探针没测到」**：
- 音效实现是 `workbench/server/static/sfx.js`（`window.lkSfx.playCue`），
  四个落点在 `workbench.js`（答对 / 答错 / 完成 / 里程碑）；
- ⚠️ **浏览器自动播放限制**：首次音效必须在**一次用户手势之后**（10.2 的要求）；
  ⇒ 探针若不先做手势，就**测不到**——那要分清「浏览器拦的」与「代码没触发」。
- 判定口径建议（**你来定，写进 README**）：
  ① 先做一次真实手势（点按钮）⇒ 解锁音频上下文；
  ② 答一题 ⇒ 观察 `playCue` 是否被调用（**在页面里挂钩计数**，别指望听到声音——
  headless 未必有音频设备）；
  ③ 报告里给出「调用次数 + 是否被浏览器拦」的**两段证据**。
- ⚠️ **只做探针，不改产品代码**（`sfx.js` / `workbench.js` 一律不动）。

### 目标三：把「M-3 里程碑」的判据做成可复现
- 若「章节首次完成」那条（A-29 / CD-167）仍**不可判定**（`practice_runs` 无章列），
  ⇒ **如实记 PENDING**，并把「缺什么数据才能判定」写清楚
  （**不要**为了让 M-3 过而发明代理指标 —— A-29 明令禁止）。
- 但「**本轮全对**」这一条是**可判定的** ⇒ 种子造一轮**全对**的练习，
  让 M-3 至少能验这一条。

## 硬约束
- **只改 `tools/walkthrough/` 下的文件**（`launch.py` / `exercise.py` / `dbexport.py` /
  `probe.py` / `frames.py` / `g5.py` / `run.py` / `recorder.py` / `shots.py` / `README.md`）。
  **绝不改产品代码**（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）——
  **另有几个 agent 正在并行改那些文件**。
- **不写 `docs/` / `openspec/`**（主会话统一维护）。
- **绝不写真实池**：`pool/dmath.db` 的 mtime / sha256 / size **全程必须不变**。
- 走查按 **A-39**：仓库根为 cwd、**独立端口**、池副本 + 隔离注册表；
  **服务字节数与磁盘字节数必须相等**。
- ⚠️ **探针是判据，不是产品** —— **不许**为了让判据变绿而改判据的判定逻辑
  （**分类 / 口径可以按 `decisions.md` 的裁决改，阈值不许放水**）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
python -m compileall -q tools/walkthrough
```
- **重跑一次完整走查**（`python tools/walkthrough/run.py`，产物落 `tmp/wt-run-8/`），
  报告里 **3.7-2 / 3.4-6 / 3.3-1 / M-3** 这几条要有**新的判定**（PASS / FAIL / PENDING 都行，
  **但不能还是「证据不足」**）。
- **真实池未被写**：`pool/dmath.db` 的 mtime / sha256 / size 与开工前逐项一致。
- ⚠️ **走查期间别的 agent 也在改产品代码** ⇒ 数字会漂，
  报告里写明**你那一轮对应的代码状态**（`git rev-parse HEAD`）。

## 落盘纪律与回报
- **一个模块一个 commit**，只 `git add tools/walkthrough/` 下的文件，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**种子能力的用法（命令 + 参数）** +
**重跑后那 4 条的新判定（附证据路径）** +
**3.3-1 的两段证据（调用次数 / 是否被浏览器拦）** +
**「M-3 还缺什么数据才能判定」的说明** +
**真实池未变的证据** + 待裁决项。
- 数字一律以**当场跑出来的命令输出**为准。
