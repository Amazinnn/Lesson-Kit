# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（review-workbench：Unified CLI entry point + Course and chapter switching；workbench-ui：Three-column shell）
- [x] 1.2 design + tasks
- [x] 1.3 `openspec validate "2026-09-21-course-identifier-and-name" --strict` 通过

## 2. 实现

- [x] 2.1 `cli/main.py`：`_init_course` 加短码分支；`_next_course_code`；显式 `--course` 的 slug 校验（报错说明理由）
- [x] 2.2 `cli/main.py`：`cmd_use` 的 course 同样过 slug 校验
- [x] 2.3 `server/pages.py`：顶栏 meta 改为「工作区名 +（有章时）章」
- [x] 2.4 help 文案：init 的 `--course` 说明改为"缺省时自动推导或分配短码"

## 3. 测试

- [x] 3.1 非 ASCII 文件夹零参 init → 自动 `c01`，登记名仍是文件夹名（中文）
- [x] 3.2 再 init 一个同类文件夹 → `c02`
- [x] 3.3 ASCII 文件夹仍推导（`Linear Algebra (Spring)` → `linear-algebra-spring`）
- [x] 3.4 显式 `--course 中文` → SystemExit，报错含理由，零副作用
- [x] 3.5 `use 中文 ch01` → SystemExit，注册表不变
- [x] 3.6 顶栏：自动短码工作区的页面里，meta 行含名字、不含短码
- [x] 3.7 既有用例更新（"非 ASCII 报错要参数"改为"自动短码"）

## 4. 走查（真机）

- [x] 4.1 零参 `lesson-kit init` 在中文名文件夹（临时目录 `大学物理（乙）II`，`LESSONKIT_WB_HOME` 隔离以免污染真实注册表）→ `pool/c01.db` + 骨架；第二个文件夹 `微积分（甲）II` → `c02`；注册名保留中文；显式 `--course 微积分` 与 `use 微积分 ch01` 各自带理由拒绝
- [x] 4.2 浏览器（隔离服务、3091 端口）顶栏 meta = `大学物理（乙）II · ch06`，全页文本不含 `c01`（截图 `.playwright-mcp/lk-walk-b-topbar-cjk.png`）

## 5. 文档与交付

- [x] 5.1 GLOSSARY 新增「课程标识符 / Course Identifier」+ 更新「池」「章」「工作区」措辞
- [x] 5.2 PRODUCT-MANUAL 快速开始改"站进文件夹 `lesson-kit init`（任何文件夹名都行）"；README 同步
- [x] 5.3 ACTION-GRAPH + L2 + ARCHITECTURE（`{course}` = 标识符）
- [x] 5.4 全量基线：pytest 436 / node 107 / compileall / `openspec validate --specs --strict` 11 / guard extract-problems PASS
- [x] 5.5 归档：`openspec archive 2026-09-21-course-identifier-and-name`
