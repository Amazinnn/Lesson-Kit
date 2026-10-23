# IMPL-W3h — 走查执行器补全：把「可运行」做到「能出验收结论」

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 22 组**（验收关卡）。
> **只新建 / 只改 `tools/walkthrough/` 下的文件。**

## 前置
上一波（W3g）已交付 `tools/walkthrough/launch.py` · `recorder.py` · `shots.py` · `README.md`，
并跑通了冒烟（47 条请求、字节数一致、2 张截图、chromium 148 可用、PIL 可用）。
**先读 `tools/walkthrough/README.md` 与三个模块的源码** —— 在它们之上补，不要重写。

## 硬约束
- **只动 `tools/walkthrough/`**（可新建 `tools/walkthrough/*.py`）。
  **绝不改产品代码**（`workbench/` 一律不动 —— 另有几个 agent 正在并行改那些文件）。
- **不写 `docs/` / `openspec/`**（主会话统一改）。
- **永不写真实池**：池副本 + 隔离注册表（`LESSONKIT_WB_HOME`）+ **独立端口（不要 3081）**。
- **以仓库根为 cwd 启动服务**（本机 pip 装着 `lesson-kit 0.1.0`，从别处启动会解析到
  site-packages 的**安装快照**）。启动后必须比对
  `curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c` 与
  `wc -c workbench/server/static/workbench.css` —— **两个数必须相等**。
- **不动图谱的算法**（`node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
  必须仍是 0 条差异）。

## 已定的两条口径（**不要再问，照做**）
- **A-49**：验收的「改造前」基线提交 = **`cf9d596d`**（本分支第一个产品提交 `16d3ff89` 的父提交）。
  ⇒ 取「改造前」的代码**必须用 `git worktree` 检出 `cf9d596d`**，**不要**用
  `tmp/frontend-audit/00-baseline-*.png`（视口 / DPR 不可控，**未纳入像素判定**）。
- **A-48**：G-5 判为 **R-2 + R-3**：
  - **R-2** = `.graph-workspace` 的裁剪矩形逐像素一致；
  - **R-3** = 在 R-2 之上，画布矩形 + 三栏各取 1 个纯色像素；
  - **R-1 整页**改为「**除左栏与顶栏外**像素级一致」（左栏导航与顶栏的结构变化是
    11.3–11.5 / 12.1 的既定要求，不算误伤）。
  ⇒ **三口径全跑并列、不选边**；口径影响结论时记 **PENDING**（**PENDING 不算 PASS**），
  三口径一致时直接 PASS / FAIL。

## 要交付什么

### 1. `tools/walkthrough/exercise.py` —— 脚本化跑一遍练习（E0–E9）
- 产出一条**完整的请求序列**（方法 / 路径 / 载荷键集合 / 顺序），供 **G-1** 判定。
- 覆盖：进入练习 → 选范围 → 拉题 → 交卷 → 看完成页 → 自评 → 进入下一题。
- ⚠️ **请求序列必须与改造前一致** —— 本模块**只驱动页面，不改请求**。
- 造「建卷」：当前浏览器无入口 ⇒ 用 CLI / API 建卷，且**两侧（改造前 / 改造后）用同一组参数**。
- 产出 S-3「进行中」态的截图。

### 2. `tools/walkthrough/dbexport.py` —— 持久化 / 学习投影 / schema 导出
- 导出 `problem_attempts` / `feedback_events` / `practice_runs` 的**行数与关键列**（**G-2**）、
  **学习投影**与**复习建议集合**（**G-3**）、**池 schema**（**G-6**）、`/due` + `/weak`（**G-4**）。
- 导出格式要**可逐行 diff**（稳定的列顺序 + 稳定的行排序）。

### 3. `tools/walkthrough/frames.py` —— 关键帧采集（M-1…M-10）
- 每条动效采一串帧，并**同时采 reduced-motion 版**。
- ⚠️ **降级帧的终态必须与动效帧的终态逐像素一致**（8.9 / 21.6 的铁律）——
  这一条要**脚本化判定**，不是「目视觉得一致」。

### 4. `tools/walkthrough/probe.py` —— 浏览器探针
- **G-7**：装饰层的 `pointer-events` 检查（`elementFromPoint` 命中检查）。
- **G-8**：换页前后的**焦点序列**对比。
- **§3 的 38 条交互清单**逐条探针。

### 5. `tools/walkthrough/run.py` —— 三段编排
- `before`（worktree 检出 `cf9d596d`）→ `after`（当前 HEAD）→ `diff`。
- 一条命令跑完，产物落 `tmp/acceptance/<run-id>/`。
- 支持**只跑某几条判据**（G-1 / S-4 / M-7 …），便于增量复跑。

### 6. `tools/walkthrough/README.md` 更新
写清：每个模块的用法、产物位置、**哪些判据已实现、哪些还没有**（诚实标注，别写成都能跑）。

## 硬要求（自查时逐条贴证据）
- **不要为了让报告好看而放宽判据**。判据宁可记 PENDING，也不能判 PASS。
- **缺证据 ≠ 通过**：某个判据拿不到证据时，**整体结论不是 PASS** ——
  执行器已有 `INCOMPLETE` 概念（缺证据的判据若按原算法会被算成「通过」），
  **沿用它**，不要新造。
- 每条判据的产出要能**独立复核**：给出命令 + 输出 + 产物路径。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
python -m compileall -q tools/walkthrough
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```

## 落盘纪律与回报
- **小步提交**：一个模块一个 commit，只 `git add tools/walkthrough/`（`tmp/` 不提交），**不要 `git add -A`**。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 + **每个新模块的真实运行输出** +
  **哪些判据现在能跑、哪些还不能** + **PENDING 列表** + 四条验证命令结果 + **待裁决项**。
- 数字一律以**当场跑出来的命令输出**为准。
