# single-cli-name 提案

## Why

本项目给同一个 CLI 发了两个命令名（`wb` 与 `lesson-kit`）。`wb` 在世界上属于
Weights & Biases：本机 `Scripts/wb.exe` 实测归 `wandb 0.25.1`，两个包都声明它，
谁后装谁赢——`pip install -e .` 会把 W&B 的名字抢过来（记忆里已咬过两次）。
所有者定案：**只留 `lesson-kit` 一个名字**，不再多弄一个出去。

## What Changes

- `pyproject.toml` 只声明 `lesson-kit = "workbench.cli.main:lesson_kit_main"`；
  删除 `wb` 入口，`main()` 与 `lesson_kit_main()` 合并为一个入口（`prog` 恒为
  `lesson-kit`，`python -m workbench.cli.main` 打印同一名字）。
- 运行期唯一还在提示 `wb` 的错误文案（`no workspaces registered — run: wb init
  <path>`）改为 `lesson-kit`。
- **live 文档全量清扫**（14 个文件、36 处）：README / CONTRIBUTING / AGENTS.md /
  START_HERE / docs 下 ARCHITECTURE、REQUIREMENTS、GLOSSARY、PRODUCT-MANUAL、
  PENDING-DEFINITIONS、FUTURE-DEVELOPMENT-NOTES、frontend-optimization-plan、
  action-graph L0–L3、adr 0009/0020/0022；其中"两个名字等同"的定义句按单名重写。
- 规格同步：`review-workbench`（Unified CLI entry point、Workspace registry、
  Unified Agent data CLI）、`mastery-evaluation`（Read-only mastery experiment
  command）、`ai-teacher-bridge`（Provider configuration、CLI is a data
  interface、Native session continuity）；`openspec/config.yaml` 项目上下文。
- 待实现的两个 change（`dashboard-chapter-filter`）里遗留的 `wb` 一并改。
- **不动**（明确出局）：Python 包名 `workbench`、环境变量
  `LESSONKIT_WB_HOME`、浏览器存储键 `wb_*`（已声明冻结并被 JS 测试断言）、
  legacy `python lessonkit.py`、`test_conversations.py` 里"提示词不得出现 `wb`"
  的反向护栏、以及一切历史档案（`openspec/changes/archive/**`、`changelog/**`、
  `docs/DISCUSSION-RECORD.md`、`docs/superpowers/**`）。

## Capabilities

### Modified Capabilities

- `review-workbench`：Unified CLI entry point 由双名改为单名；Workspace registry
  与 Unified Agent data CLI 的场景示例命令改名。
- `mastery-evaluation`：实验命令示例改名。
- `ai-teacher-bridge`：provider 配置、数据接口、会话连续性三条需求的示例命令改名。

## Impact

- 代码：`workbench/cli/main.py`（docstring、`prog` 默认值、单一入口、错误文案）。
- 打包：`pyproject.toml`；装完需补 `pip install --force-reinstall --no-deps wandb`
  把 `wb.exe` 还给 W&B（它现在归 W&B，重装 lesson-kit 会把它删掉）。
- 测试：`tests/workbench/test_cli_daemon.py`（双入口断言 → 单名）、`test_cli.py`
  文档串；provider JSON 夹具里的 `wb pull` 字样属装饰性，保持不动。
- 文档：上列 live 文档 + `openspec/config.yaml`。
- 学习者可见行为零变更（命令只是少了一个别名）；`lesson-kit` 行为一字不动。
