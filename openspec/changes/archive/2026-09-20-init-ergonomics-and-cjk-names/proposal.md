# init-ergonomics-and-cjk-names 提案

## Why

所有者真实使用中撞到两件事（2026-09-20）：

1. 站在课程文件夹（`…\大学物理乙(II)`）里跑 `lesson-kit init`，被 argparse 的必填
   `path` 拦下——人在该文件夹里，本应等价于 `init .`。人面命令每多一个必填参数
   就多一次输入成本；所有者定下原则：**人面命令尽量只有 ≤2 个参数，能推导就推导，
   推不出来时必须给可粘贴的完整命令**。
2. 顺带实测发现一个真 bug：`--name` 默认取文件夹名，而服务端路由**不做 URL 解码**
   （`workbench/` 全仓零 `unquote`），浏览器百分号编码后的 CJK 工作区名查不到注册表
   ——中文目录里 init 出来的工作区，页面 404、接口找不到。CJK 目录名是常态，不能
   靠"起个英文名"绕开。

## What Changes

- `lesson-kit init` 的 `path` 改为可选，默认 `.`（当前目录）。
- `--course` 可省：按 **显式 `--course` > 已成型工作区的池文件名 > ASCII 安全的
  文件夹名** 次序推导；三者都拿不到时（如中文文件夹名）报错，并**打印一条可粘贴的
  完整命令**，不静默猜值。
- `--name` 保持可选、默认文件夹名（修好路由解码后 CJK 名可用）。
- `--chapter` 保持可选（空 = 全课程，见 2026-09-20-dashboard-chapter-filter）。
- **修路由编码 bug**：页面 / API / 附图 / 图谱工件四条路径在查工作区与解析文件前
  一律对路径段做 URL 解码；顺带把 API 分派里未捕获的 `KeyError` 收成 404
  （其余三条路径已如此，未知名不应变成服务端异常）。
- 顺带把 `registry._find_pool` 提为公开 `find_pool`，让 init 与 register 共用同一
  池发现逻辑（历史上"取排序第一个 db"已咬过一次）。
- 规格侧把「人面命令 ≤2 参数 / 能推导就推导 / 报错给可粘贴命令」写进
  `review-workbench` 的 CLI 需求，并新增「编码名可解析」需求。

## Capabilities

### Modified Capabilities

- `review-workbench`：Unified CLI entry point 增补人面命令的参数纪律与 init 的
  默认值/推导规则；新增路由对百分号编码名的解析要求。

## Impact

- 代码：`workbench/cli/main.py`（init 解析器默认值、course 推导与报错文案）、
  `workbench/server/app.py`（四条路径的 `unquote`）、
  `workbench/registry.py`（`_find_pool` → `find_pool`）。
- 测试：`tests/workbench/test_cli_daemon.py`（当前目录 init、ASCII 推导、非 ASCII
  报错给命令、已成型工作区取池名）、`tests/workbench/test_ui_routes.py`（CJK 名的
  页面/接口/附图路由 200，未知名仍 404）。
- 文档：PRODUCT-MANUAL 快速开始与「选定范围」相邻段落改最短命令写法；
  ACTION-GRAPH 登记 init 动作改级与新增（写注册表/取池发现）。
- 无池结构变更；不动 `pipeline/`。
