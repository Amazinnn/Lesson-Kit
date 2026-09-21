# design — single-cli-name

## 上下文

- `pyproject.toml:17-19` 同时声明 `wb` 与 `lesson-kit`，指向
  `workbench.cli.main` 的 `main()` / `lesson_kit_main()`，二者只差 `prog` 字符串
  （`main.py:703-715`）；`python -m workbench.cli.main` 走 `main()`，因此打印
  `usage: wb`。
- 本机 `Scripts/wb.exe` 实测是 `wandb 0.25.1` 的启动器（`wb --version` 打印
  `wb, version 0.25.1`，二进制里嵌的是 `wandb`），而 `lesson_kit-0.1.0.dist-info`
  的 RECORD 仍声明它——两个包争同一个文件，谁后装谁赢。
- live 引用统计：`wb` 作命令名 105 处——代码 5（全在 `cli/main.py`）、测试 9、
  live 文档 36（14 文件）、openspec（config.yaml + 3 个 spec + 1 个待实现 change）
  15；历史档案（archive 65 / changelog 25 / DISCUSSION-RECORD 7 / superpowers 16）
  按"不可变历史"排除。

## Goals / Non-Goals

**Goals**

- 一个命令名：`lesson-kit`；模块形式等价且同名。
- 装完 `wb` 回归 W&B，之后无论谁先装都不再互相覆盖。

**Non-Goals**

- 不改 Python 包名 `workbench`、环境变量 `LESSONKIT_WB_HOME`、浏览器存储键
  `wb_*`（已冻结且被 JS 测试断言，改了会让学习者浏览器里的既有状态失效）。
- 不动 legacy `python lessonkit.py`（另一条入口，AGENTS.md 验证节奏在用）。
- 不引入 `wb` 兼容别名——所有者要的是"不再多弄一个出来"。
- 不改任何子命令行为。

## 决策

### 一、单一入口函数

`main()` 保留（`python -m workbench.cli.main` 与既有测试都调它），`prog` 默认值
改为 `lesson-kit`；`lesson_kit_main()` 保留为 `pyproject` 的入口目标（两者同体）。
`_run(argv, prog)` 不动——它本来就接收 prog。

### 二、清扫范围 = live，历史不动

按 AGENTS.md「文档是资产」与既有先例（2026-09-17 曾有意不改
`DISCUSSION-RECORD.md`）：只改"当前指令性"文本；`archive/`、`changelog/`、
`DISCUSSION-RECORD.md`、`superpowers/plans` 视为不可变历史。

### 三、安装次序（有踩坑史）

先改 `pyproject.toml`，再 `pip install -e . --no-deps`（不再声明 `wb.exe`，pip 会
按旧 RECORD 删掉它）；因为该文件现在归 W&B，随后把 W&B 的启动器装回——**必须钉版本**
`pip install --force-reinstall --no-deps "wandb==0.25.1"`：实测裸的
`--force-reinstall --no-deps wandb` 会重解析到最新版（0.30.0）且因 `--no-deps`
缺 `xxhash`，直接把 `wb` 弄成 ImportError。验证：`lesson-kit --help` 显示
`lesson-kit`、`python -m workbench.cli.main --help` 同名、`wb --version` 是
`wandb 0.25.1`。

### 四、保留"提示词不得出现 wb"的护栏

`tests/workbench/test_conversations.py:650-651` 的 `assertNotIn("wb data"...)`
是防 Agent 被教去跑 W&B 的反向断言——改名后依然成立，保留原样。

## Risks / Trade-offs

- 文档清扫面广（14 文件 36 处），漏一处就会留下"命令不存在"的假指令；
  缓解：改完全仓 grep `\bwb\b`，只剩历史档案与出局项。
- 重装 edibale 安装会重写 `Scripts/lesson-kit.exe`；`--no-deps` 是硬要求，
  否则会顺手升级本机 pytest（记忆里已有先例）。
