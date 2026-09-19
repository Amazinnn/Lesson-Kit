# bootstrap-workspace-init 提案

## Why

grilling 讨论（2026-09-18，所有者定案）：`lesson-kit init` 目前只能注册**已成型**文件夹
（必须已有 `pool/*.db` 或 `lessonkit.py`），空目录直接报错；且 `active_course`/
`active_chapter` 注册后无法修改，换章节的唯一办法是重跑 `wb init`。所有者即将投入
真实使用（首场景：备考综合），「任意文件夹一条命令从零进工作台」是已定体验链的前半截，
换章是高频缺口。

定位共识一并落进 spec：CLI = 双受众分层——人面（init / use / dashboard / daemon /
ls / bridge / doctor）与 Agent 面（data / pull / practice / feedback / ingest /
goals）共用同一实现，人面命令就此封顶。

## What Changes

- `lesson-kit init <path>` 遇到**非工作区文件夹**时升级为「创建+注册」一体：自动创建
  池数据库（调用既有 `pipeline/scripts/create-tables.py`，不修改它）、建 `.lessonkit/`
  骨架目录（figures / explain / jobs），然后走既有注册流程。已成型文件夹行为不变。
- 新增 `lesson-kit use <course> <chapter>`：切换当前工作区的活动课程/章节，无需重跑
  init；未知工作区/非法参数报错不静默。
- spec 措辞补双受众分层；配置存储**不动**（course/chapter 权威仍在用户级注册表）。

## Capabilities

### Modified Capabilities

- `review-workbench`：Unified CLI entry point 扩展 init 的创建语义与 use 换章；
  双受众分层措辞。

## Impact

- 代码：`workbench/cli/main.py`（cmd_init 分支 + cmd_use + 解析器）、
  `workbench/registry.py`（活动课程/章节更新函数）。
- 测试：`tests/workbench/test_cli_daemon.py` 增补（空目录 bootstrap、幂等、use 切换、
  错误路径）。
- 文档：README / PRODUCT-MANUAL 快速开始补 use；ACTION-GRAPH L2 命令计数 18→19。
- 无池结构变更、无迁移；bootstrap 只新建文件，不触碰已有数据。
