# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（MODIFIED Unified CLI entry point + ADD Encoded names resolve in workbench routes）
- [x] 1.2 design + tasks
- [x] 1.3 `openspec validate "2026-09-20-init-ergonomics-and-cjk-names" --strict` 通过

## 2. 实现

- [x] 2.1 `workbench/registry.py`：`_find_pool` → 公开 `find_pool`（register 与 main 共用）
- [x] 2.2 `workbench/cli/main.py`：`init` 的 `path` 改 `nargs="?"`、默认 `.`（help 写明）
- [x] 2.3 `workbench/cli/main.py`：`_slug_from_name`（ASCII + lower + 折叠 → `[a-z0-9][a-z0-9-]*`）+ 三个来源的 course 推导 + 可粘贴报错；`cmd_init` 先 `resolve()`（否则 `Path(".").name` 为空串——走查抓到）
- [x] 2.4 `workbench/server/app.py`：`unquote` 进 import；`_match_route` / `_send_page` / `_send_figure` / `_send_graph_artifact` 逐段解码；API 分派未知名收成 404
- [x] 2.5 人面 help 文案复核（init：path 默认值、course 可省的条件）

## 3. 测试

- [x] 3.1 `init --course X` 在 cwd（不带 path）可建区并注册
- [x] 3.2 ASCII 文件夹名（`Linear Algebra (Spring)`）→ course `linear-algebra-spring`；cwd 零参 → 取 resolve 后的目录名（`Graph Theory` → `graph-theory`）
- [x] 3.3 非 ASCII 文件夹名零参 init → SystemExit + 报错含可粘贴命令，且零副作用
- [x] 3.4 已成型未注册文件夹零参 init → course 取池名（CJK 目录 + `dmath.db` → `dmath`）
- [x] 3.5 路由：CJK 名的页面/接口 200；未知工作区页面与接口都 404
- [x] 3.6 既有用例回归（pytest 431 passed；1 个 Windows 文件锁 flake 单跑必过，未修）

## 4. 走查（真机，截图）

- [x] 4.1 中文名临时课程文件夹 + 隔离 `LESSONKIT_WB_HOME`，站在目录里 `lesson-kit init`（已有池 → course 取 `dmath`）
- [x] 4.2 3091 端口起隔离服务（3081 真工作台未动；3091 起前已确认无占用）
- [x] 4.3 浏览器（Playwright）打开 CJK 名工作区：hub / 练习页 / 知识点页 / 图谱页各一张截图（`walk-cjk-01..04-*.png`），页面显示 31 知识点 / 345 题的真实数据；console 仅缺 favicon 一条
- [x] 4.4 反例留档：中文目录零参 init 的报错文案（终端输出原样记录，非截图）
- [x] 4.5 `Linear Algebra` 目录零参 init 成功（终端输出：推导 `linear-algebra` 并建库）

## 5. 文档与交付

- [x] 5.1 `docs/PRODUCT-MANUAL.md` 快速开始：改为最短命令写法（站进文件夹 `lesson-kit init`，中文名提示补 `--course`）
- [x] 5.2 `docs/ACTION-GRAPH.md` + `docs/action-graph/L2-interfaces.md`：登记 init 改级与路由解码
- [x] 5.3 全量基线：pytest 431（+1 已知 flake）/ node 107 / compileall OK / `openspec validate --specs --strict` 11 / guard PASS
- [x] 5.4 归档：`openspec archive 2026-09-20-init-ergonomics-and-cjk-names`
