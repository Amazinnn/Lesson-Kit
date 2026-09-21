# course-identifier-and-name 提案

## Why

课程串现在身兼两职：**所有者给课程起的名字** 与 **每一条内容 id 的前缀**（池文件名
同源）。这个耦合的代价是：在中文课程文件夹（`…\大学物理乙(II)`）里跑
`lesson-kit init` 会被要求补一个 ASCII 缩写——名字不能随意起，参数也省不掉。

所有者定案：**分离**——名字随你（中文/括号/空格，默认取文件夹名，就是工作区名），
**标识符**由程序生成；`init` 任何文件夹都零参可用。自动短码取顺序编号
`c01`、`c02`…（所有者选定）。

## What Changes

- `lesson-kit init` 的课程标识符按序推导：显式 `--course`（须为合法小写 ASCII
  slug）› 已成型池的文件名 › 文件夹名的 ASCII 推导（`Linear Algebra` →
  `linear-algebra`）› **自动顺序短码 `c01`/`c02`…**（扫注册表已用编号 + 本文件夹
  `pool/*.db` 取 max+1）。
- **取消"中文文件夹名 → 报错要参数"**：现在自动分配短码，名字仍是文件夹名。
- `--course` 显式值**首次获得校验**（此前完全没校验，`--course 大学物理` 会原样
  写进注册表并埋进 id 契约）；`use <course> <chapter>` 的 course 同样校验。
- 顶栏不再露机器短码：只显示工作区名（+ 有章时显示章）。
- 文档：GLOSSARY 新增「课程标识符 / Course Slug」条目并更新「池」「章」措辞；
  PRODUCT-MANUAL 快速开始改为"站进文件夹 `lesson-kit init`（任何文件夹名都行）"；
  ACTION-GRAPH 与 L2 留痕；FILE_CONTRACT 注明 `{course}` = 标识符。

## Capabilities

### Modified Capabilities

- `review-workbench`：Unified CLI entry point 的课程来源次序加自动短码、显式
  `--course` 的 slug 校验；"非 ASCII 文件夹名报错"场景改写为"自动分配短码"。
- `workbench-ui`：Three-column shell 的顶栏上下文改为工作区名 + 章（不再塞课程
  标识符）。

## Impact

- 代码：`workbench/cli/main.py`（`_init_course` 增短码分支与校验、`_next_course_code`、
  `cmd_use` 校验）、`workbench/server/pages.py`（顶栏 meta）。
- 测试：`test_cli_daemon.py`（非 ASCII → `c01`、再 init → `c02`、显式非法 course
  报错、`use` 校验、既有"报错要参数"用例改写）、`test_ui_routes.py`（顶栏不含短码）。
- 学习数据零变更：id 格式、池结构、既有 `dmath` 数据都不动。
