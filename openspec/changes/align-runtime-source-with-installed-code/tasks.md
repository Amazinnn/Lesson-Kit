## 1. 契约协调

- [x] 1.1 在 `docs/design/workbench-capability-maturation/contract-reconciliation.md` 登记 CR16：现行 PRODUCT-MANUAL/ARCHITECTURE 写"默认主检出"，与批准目标"安装代码所在 checkout"不一致，本 change 接管。（已登记 CR16，含负责文件清单）
- [x] 1.2 从 `openspec/changes/stable-runtime-live-reload/specs/runtime-live-reload/spec.md` 撤下被取代的默认来源首句与 "Editable install in a worktree" 场景，保留显式覆盖、子进程导入、身份报告与诊断条款；`openspec validate stable-runtime-live-reload --strict` 仍通过。（同 PR 同步其 proposal/design 并就地标注被本 change 取代；strict 有效）
- [x] 1.3 在 `docs/GLOSSARY.md` 新增"运行时来源"条目（先定义后使用），与 `review-workbench` delta 用词一致。（「运行时来源 / Runtime Source」条目 + _Avoid_ + 出处）

## 2. 实现

- [x] 2.1 `workbench/cli/runtime_source.py::project_root()` 默认返回安装源码 checkout，删除 worktree → primary 的 Git 指针回溯；`--project-root` 校验与报错保持不变。（函数 26 行降到 13 行；`installed` 接缝保留）
- [x] 2.2 改写 `tests/workbench/test_runtime_source.py`：linked worktree 默认服务自身、显式覆盖仍生效、非源码目录被拒绝并给出原因。（三条断言 + 新增 `test_explicit_path_must_be_a_lesson_kit_source`）
- [x] 2.3 核对 `workbench/cli/main.py::cmd_serve` 与 `workbench/cli/service.py::start`：默认路径下不再走"切换到 primary 子进程"的分支，来源记录与 `/api/runtime` 报告一致。（默认时 `root == parents[2]` 直接 in-process；显式覆盖才 spawn 子进程；`daemon.json` 与 `/api/runtime` 均报同一 `source_root`）

## 3. 文档同步

- [x] 3.1 `docs/PRODUCT-MANUAL.md` §工作台运行与自动更新：默认来源改为安装代码所在 checkout，说明 worktree 安装、显式覆盖与旧服务需先 `daemon stop`。（已改；"来源或端口不匹配时先安全停止旧服务"原句保留覆盖旧服务场景）
- [x] 3.2 `docs/ARCHITECTURE.md` §Stable runtime lifecycle：同步默认来源语句。（已改）
- [x] 3.3 `docs/design/workbench-capability-maturation/HANDOFF-2026-11-08.md` §7/§11 的 RELEASE-02 剩余项按实际结果更新（不改历史结论，只记本轮状态）。（新增 §14 补记，原文不动）

## 4. 验证

- [x] 4.1 聚焦用例：`PYTHONUTF8=1 python -m pytest tests/workbench/test_runtime_source.py tests/workbench/test_cli_daemon.py -q`。（45 passed）
- [x] 4.2 仓库级检查：全仓 `pytest tests -q`、`python -m compileall -q lessonkit.py workbench pipeline pool tests`、`openspec validate --specs --strict`、`openspec validate align-runtime-source-with-installed-code --strict`、`python lessonkit.py guard extract-problems --course dmath --chapter ch06`。（1557 passed / 593s；compileall OK；live specs 21/21；两个 change strict 有效；guard dmath ch06 PASS）
- [x] 4.3 真实隔离验收：在 worktree 内 `lesson-kit daemon start --port <空闲端口> --no-reload`（不带 `--project-root`），确认 `/api/runtime` 的 `source_root` 是本 worktree 而非 primary，然后 `daemon stop`；记录证据。（端口 3097，`source_root` = worktree；已 stop 复原。未做浏览器目视：本 change 不改页面行为，同一进程同时提供 API 与页面）
- [x] 4.4 显式覆盖回归：同一端口段用 `--project-root` 指定另一 checkout，确认覆盖生效且默认来源未被改写。（端口 3098 指向主检出，`source_root` = 主检出；已 stop）
