# add-doctor-selfcheck 提案

## Why

grilling 定案（2026-09-20，所有者点选）：CLI 人面补一个环境自检命令。本机已多次
出现"配置静默失效"类问题——provider 被 PATH 顺序遮蔽、安装了但不在当前进程 PATH、
守护进程夜里消失、注册表指向不存在的库——全靠踩坑后手工排查。`doctor` 把这些
检查聚合成一条只读命令，健康/故障一眼可见。

## What Changes

- 新增 `lesson-kit doctor`（人面命令）：只读聚合检查——注册表可读、每个工作区
  数据库存在且可打开、provider 解析（可执行文件存在性）、守护进程状态与端口应答、
  goals/plan 文件可读性。全部通过退出 0，否则退出 2 并逐项列出。
- 不修任何东西、不写任何文件（纯只读）；`bridge list` 与 `daemon status` 保持
  原样，doctor 是它们的超集视角。

## Capabilities

### Added Capabilities

- `review-workbench`：环境自检命令要求。

## Impact

- 代码：新增 `workbench/cli/doctor.py`、`workbench/cli/main.py` 接线。
- 测试：`tests/workbench/test_cli_daemon.py` 增补（健康夹具、故障注入）。
- 文档：README / PRODUCT-MANUAL / ACTION-GRAPH L2（19→20 命令）。
