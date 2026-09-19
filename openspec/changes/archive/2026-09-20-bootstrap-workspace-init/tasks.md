# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（MODIFIED Unified CLI entry point + ADD Course and chapter switching）strict 通过
- [x] 1.2 design + tasks

## 2. 实现

- [x] 2.1 `workbench/registry.py`：`update_active(name, course, chapter)`；`_looks_like_workspace` 升为公开 `looks_like_workspace`
- [x] 2.2 `workbench/cli/main.py`：`cmd_init` 的 bootstrap 分支（缺 `--course` 报错；调 create-tables.py；建 `.lessonkit/{figures,explain,jobs}`）；注册仍走 `registry.register`
- [x] 2.3 `workbench/cli/main.py`：`cmd_use` + 解析器（`use <course> <chapter> [--workspace]`；多工作区未指定时报错）
- [x] 2.4 人面命令 help 文案核对（init/use/dashboard/daemon/ls/bridge），不改 Agent 面文案

## 3. 测试

- [x] 3.1 空目录 init 全流程（池库、骨架、注册、hub 可见）
- [x] 3.2 已成型文件夹 init 不触碰池/不建骨架（幂等）
- [x] 3.3 bootstrap 缺 `--course` 报错且零副作用
- [x] 3.4 use 切换生效（注册表更新）；多工作区未指定 `--workspace` 报错；未知工作区报错且注册表不变

## 4. 验证与交付

- [x] 4.1 全量基线：pytest / node --test / compileall / openspec specs strict / guard
- [x] 4.2 真机走查：临时空目录 `lesson-kit init` → `lesson-kit ls` / hub 可见
- [x] 4.3 文档：README / PRODUCT-MANUAL 补 use；ACTION-GRAPH L2 命令计数；changelog
- [x] 4.4 归档 change
