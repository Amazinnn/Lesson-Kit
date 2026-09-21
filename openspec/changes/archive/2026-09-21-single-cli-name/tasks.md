# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（review-workbench / mastery-evaluation / ai-teacher-bridge 三条改名）
- [x] 1.2 design + tasks
- [x] 1.3 `openspec validate "2026-09-21-single-cli-name" --strict` 通过

## 2. 实现

- [x] 2.1 `pyproject.toml`：删 `wb` 入口，只留 `lesson-kit`
- [x] 2.2 `workbench/cli/main.py`：模块 docstring、`build_parser(prog="lesson-kit")`、`main()` 的 prog 与 docstring、错误文案改 `lesson-kit`
- [x] 2.3 测试：`test_cli_daemon.py` 单名断言（含模块形式同名）；`test_cli.py` docstring
- [x] 2.4 live 文档 36 处（README / CONTRIBUTING / AGENTS.md / START_HERE / docs 10 个 + action-graph L0–L3 + adr 0009/0020/0022），"两个名字"定义句按单名重写
- [x] 2.5 `openspec/config.yaml` + 三个 spec 的正文示例（经 delta 归档落地）；`dashboard-chapter-filter` 里遗留的 `wb`
- [x] 2.6 全仓复核：live 文件零 `wb` 命令名，仅剩历史档案、出局项（包名/环境变量/存储键/夹具/护栏）与 7 个 gitignore 的旧 job 状态文件

## 3. 安装与验证

- [x] 3.1 `pip install -e . --no-deps`（先改 pyproject 后装），确认 `wb.exe` 被移除
- [x] 3.2 W&B 启动器装回——**钉版本** `"wandb==0.25.1"`（裸 `--force-reinstall --no-deps wandb` 实测升到 0.30.0 且缺 xxhash → `wb` ImportError，已修回）
- [x] 3.3 `lesson-kit --help` 与 `python -m workbench.cli.main --help` 都显示 `lesson-kit`；`wb --version` → `wb, version 0.25.1`
- [x] 3.4 全量基线：pytest 432 / node 107 / compileall OK / `openspec validate --specs --strict` 11 / guard PASS
- [x] 3.5 ACTION-GRAPH 留痕 + 记忆更新
- [x] 3.6 归档：`openspec archive 2026-09-21-single-cli-name`
