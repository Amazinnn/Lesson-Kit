# design — bootstrap-workspace-init

## 决策一：bootstrap 走调用，不复制逻辑

`pipeline/scripts/create-tables.py` 是从零建池的既有入口（16 表全量 + 自动接
`ensure_workbench_schema`），且它通过 `__file__` 解析 `pool/scripts` 导入路径，
因此可以**以绝对路径调用、cwd 设为新工作区文件夹**（`--db pool/<course>.db`）。
AGENTS.md 禁改 pipeline 行为契约——本 change 只调用。候选表顾虑已排除：
`ensure_problem_candidate_schema` 自 2026-08-30 起是兼容空壳（只 ensure
learner_signals），新池不会复活候选存储。

## 决策二：判定「已成型」复用既有谓词

`registry._looks_like_workspace` 升为公开 `looks_like_workspace`（registry 内部
与 cmd_init 共用同一判定），init 在其失败时才走 bootstrap——已成型文件夹行为
完全不变（spec 场景「Initializing an existing workspace never rewrites it」）。

## 决策三：bootstrap 需要 --course，chapter 可后补

池库名即 `pool/<course>.db`，无 course 则无法命名——bootstrap 缺 course 直接
报错退出（不静默）。chapter 缺省为空字符串，之后用 `lesson-kit use` 补——这与
既有注册语义一致（course/chapter 可空），避免为对称发明新约束。

## 决策四：use 的参数形状

`lesson-kit use <course> <chapter>` 定位为"当前工作区"的命令：单工作区时直接
生效；多工作区要求 `--workspace <name>` 显式指定（与 `_resolve_name` 的单工作区
约定同源，但 course/chapter 占位在前，name 不能再挤第一个位置）。切换只改
注册表 JSON 两个字节段，不碰任何池文件——spec「Switching never happens
silently on error」由 update_active 的 KeyError 路径保证。

## 决策五：骨架只建目录，不写 state.yaml

`.lessonkit/{figures,explain,jobs}` 三个目录是服务端已知的运行面（figures 路由、
job 存储）。`.lessonkit/state.yaml` 是 `lessonkit.py`（管线运行时）的产物，由
guard/init 写——workbench 侧代写会制造第二套真相，违反本 change「存储不动」的
共识。新工作区要跑抽取管线时，自然会在其根目录获得 state.yaml。

## 风险

- init 的 `mkdir(parents=True, exist_ok=True)` 会创建拼错的路径——与 `git init`
  行为一致，接受。
- create-tables.py 子进程失败（磁盘/权限）转译为 SystemExit + stderr 消息，
  不留半成品注册（注册发生在 bootstrap 成功之后）。
