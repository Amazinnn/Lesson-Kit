# introduce-pi-agent-and-cli 提案

## Why

现有 Bridge 只发现 Codex 与 Claude 两个 Agent CLI，两者 harness 都偏重（系统提示、
工具脚手架、会话机制占用大量往返 token），日常练习的对话成本高。所有者 2026-09-17
决定引入 Pi（`@earendil-works/pi-coding-agent`）作为第三个、更轻的 provider，用于
降低每次对话的 token 开销。

接入前实测暴露两个必须一并处理的事实：

1. **本机存在两个 Pi 版本**（全局 0.85.1 与另一项目锁定的本地 0.80.10），且本机有两个
   npm 前缀同时挂在 PATH 上。当前 `discover()` 只能靠 `shutil.which` 探测，"lesson-kit
   用哪个可执行文件"完全由 PATH 顺序决定——这类静默解析已经在本机把 codex 遮蔽掉一份。
   provider 必须能被显式钉死。
2. **Pi 在 API 报错时进程退出码仍为 0**（实测 401 鉴权失败时 `exit=0`）。Bridge 现有的
   失败判定依赖退出码，若不同时解析流内错误，真实原因会被吞成"未返回回答"。

同时缺少首版顶层 CLI：注册工作区、后台起服务、打开工作台现在都要手打
`python -m workbench.cli.main ...`，且服务只能前台阻塞运行，关掉终端即断。

## What Changes

- **Pi 接入 Bridge**：`SUPPORTED` 增加 `pi`；`build_command` 增加显式分支
  （`--print --mode json`，恢复会话用 `--session <id>`）；`normalize_event` 增加显式
  分支（会话头取原生会话 id、文本增量、推理/工具活动行、终态取权威回答）。两处回退
  分支是既有实现里"默认落到 Claude"的位置，不加显式分支会静默套用 Claude 的 flag 与
  事件解析。
- **显式可执行文件优先**：`bridges.json` 中配置的 `command` 优先于 PATH 探测，使
  provider 究竟使用哪个可执行文件可被钉死。
- **流内错误必须上报**：Pi 的 `stopReason` / `errorMessage` 归一化为 error 事件，避免
  退出码为 0 的真实失败被表述成"未返回回答"。
- **Bridge CLI 补齐**：`bridge add` 增加 `--model`（模型由所有者自行配置，当前无法写入）；
  新增 `bridge list` 显示每个 provider 解析到的可执行文件与来源，使解析失败不再静默。
- **首版顶层 CLI**：新增 `lesson-kit` 命令，与 `wb` 并存、共用同一实现。
  `lesson-kit init` 与 `wb init` 语义完全一致（注册工作区）；新增
  `daemon start|stop|status` 承载后台服务（pid 文件与日志落在用户级 registry 目录，
  单实例）；新增 `dashboard` = 确保服务在跑并打开工作台。不新增第四个页面。
- **不改动**：不搬迁、不重装本机任何 Pi；不改动 codex / claude 的既有命令与事件语义；
  不改动前端（`/ai/providers` 已由服务端驱动，无 provider 名硬编码）。

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`：provider 发现与原生会话命令扩展到 Pi；显式 `command` 覆盖
  PATH 探测；流内错误必须显式上报。
- `review-workbench`：新增后台工作台服务与顶层 `lesson-kit` 入口（init / daemon /
  dashboard）。

## Impact

- 代码：`workbench/bridge/conversation_providers.py`、`workbench/ingest/__init__.py`、
  `workbench/cli/main.py`、新增 `workbench/cli/service.py`、`pyproject.toml`。
- 测试：`tests/workbench/test_conversation_providers.py`、
  `test_conversation_api.py`、新增 `tests/workbench/test_cli_daemon.py`。
- 文档：`docs/GLOSSARY.md`（守护进程）、新建 ADR 0022（推翻 ADR 0004 与
  FUTURE-DEVELOPMENT-NOTES 中"不做常驻后台服务"的记载）、`docs/ACTION-GRAPH.md` 与
  `docs/action-graph/L2-interfaces.md`（命令计数）、`docs/PRODUCT-MANUAL.md`、
  `README.md`、`CONTRIBUTING.md`、`changelog/`。
- 数据：无池结构变更、无迁移。服务进程引入 `.lessonkit-workbench/daemon.json` 与
  `daemon.log` 两个用户级运行文件。
- 机器环境：本机两个 Pi 版本共存，本变更通过显式 `command` 固定使用全局 0.85.1；
  另一个属于其他项目的本地安装不受影响。
