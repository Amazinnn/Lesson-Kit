# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（review-workbench ×2 ADDED + registry MODIFIED；content-governance ADDED；ai-teacher-bridge MODIFIED；workbench-ui MODIFIED）
- [x] 1.2 design + tasks
- [x] 1.3 `openspec validate "2026-09-21-workspace-file-isolation" --strict` 通过

## 2. 会话文件包含性（穿越漏洞）

- [x] 2.1 `bridge/conversations.py`：`_conversation_dir` 校验 `conv-\d+`；`_turn_file`/`_events_file` 校验 `turn-\d+`；不匹配抛 `InvalidIdentifier(ValueError)`
- [x] 2.2 `server/api.py`：`InvalidIdentifier` 收成 400 JSON（不 500、不静默）
- [x] 2.3 测试：`%2F..%2F` 形状的 id 在 get/rename/delete 上全部被拒；真 id 仍可删；另一工作区的会话名不可达（404 且镜像不动）
- [x] 2.4 实证：临时放宽守卫后同一 id 会 `rmtree` 掉工作区外的目录（证明漏洞真实、守卫有效）

## 3. 注册表与池选择

- [x] 3.1 `registry.find_pool(folder, course="")` + `pool_candidates`：候选排除 `*.ingest-backup`；`pool/<course>.db` 优先；多候选无匹配 → 拒绝并列出；空 → 建库
- [x] 3.2 `cli/main.py`：`cmd_init` 把池选择的 ValueError 收成 SystemExit；`_init_course` 用同一候选逻辑
- [x] 3.3 `registry.register`：池必须在工作区内；同名不同文件夹拒绝；同文件夹换名拒绝；同文件夹同名幂等
- [x] 3.4 `_resolve_name`：多工作区时拒绝猜，报错给「`lesson-kit <cmd> <名>`」可粘贴形式
- [x] 3.5 章标识符校验：`init --chapter`、`use <course> <chapter>`（`_require_slug(value, "chapter")`；空 = 全课程仍允许）
- [x] 3.6 `data/pool.py`：`Pool.__init__` 拒绝落在工作区外的库（CLI + 服务 + 桥三条开库路径共用）
- [x] 3.7 `hub_workspaces`/`hub_page`：单个工作区读不了只影响它自己的卡片（不空整个 hub）
- [x] 3.8 测试：多池拒绝并列出、`--course` 指名选中、备份不当候选、重名拒绝、一文件夹两名字拒绝、池越界拒绝、`_resolve_name` 歧义（含可粘贴提示）、章非法拒绝、`use` 章非法拒绝

## 4. 入池门禁课程前缀

- [x] 4.1 `ingest`：`apply_batch`/`apply_micro_quiz`/`apply_flash_cards` 接受 `course=`（缺省用池文件名）；微题/闪卡 id 前缀不符 → 逐条报错并给期望前缀；门禁无课程 → 拒绝而非猜
- [x] 4.2 `_gate_figure_patch(conn, manifest, course)`：course 必须等于本工作区课程、chapter 必须是章标识符；`_figures_root` 加最终包含性断言
- [x] 4.3 `conversations` 的 check_ingest 通路传 `course=action_pool.course`
- [x] 4.4 测试：外课 id 拒绝（报错含期望前缀、无备份落盘）、门禁无课程拒绝、池名兜底仍可 apply、figure-patch 异课与 `../` 章拒绝且工作区外无文件

## 5. Agent 提示词

- [x] 5.1 `conversations._prompt`：示例 id 与 "id 形如" 说明改用 `context["workspace"]` 的课程/章（无上下文时用占位符）
- [x] 5.2 测试：示例断言改为 `uphy2-ch07-*` 且不含 `dmath`

## 6. 走查（真机，双学科）

- [x] 6.1 隔离 `LESSONKIT_WB_HOME` + 3091 端口起服务：两个中文名工作区各自建会话（各自 `conv-001`）、`ls` 各显本区统计、`weak` 不带名拒绝并给出可粘贴命令
- [x] 6.2 浏览器：用 B 区的会话 id 构造穿越请求打 A 区路由 → 400 `invalid conversation id`，B 区镜像完好且仍在列；截图 `.playwright-mcp/lk-walk-c-traversal-refused.png`、`.playwright-mcp/lk-walk-c-hub-two-workspaces.png`
- [x] 6.3 真机复现并确认修复：本仓库 `pool/` 的 `dmath-pre-readiness-2026-08-26.db` 不再被选中（`find_pool` 改为拒绝并列出两份候选，`--course dmath` 可指名）

## 7. 文档与交付

- [x] 7.1 GLOSSARY「工作区」条目补"一区一学科、路径不互通"的硬性局限与反例
- [x] 7.2 PRODUCT-MANUAL 快速开始旁补"一个工作区 = 一门课"与切换方式
- [x] 7.3 ACTION-GRAPH + L1/L2/L3 留痕（守卫点、拒绝语义、池候选规则）
- [x] 7.4 全量基线：pytest 453 / node 107 / compileall / `openspec validate --specs --strict` 11 / guard PASS（另见备注：会话轮次类用例有环境性偶发，见下）
- [x] 7.5 归档：`openspec archive 2026-09-21-workspace-file-isolation`

## 备注

- 全量 pytest 三次运行：453 通过 / 452+1（`test_explicit_provider_title_is_mirrored`）/ 453 通过；三次失败都不重样且单跑必过，属既有 Windows 文件锁与后台轮次竞态的偶发（非本 change 引入，未修）。
