## Why

`lesson-kit` 以 editable 方式装在 linked worktree 时，`dashboard`、`daemon start`、`serve` 仍默认服务安装来源的 **primary Git checkout**：CLI 已经能列出新命令，浏览器跑的却是另一份代码。根因是 `runtime_source.project_root()` 顺着 worktree 的 `.git` 指针回溯到 primary。2026-11-08 的 P4/RELEASE-02 证据记录了这个错位，它直接造成"改了、页面还是旧行为"的反复误判——安装、导入与服务的不是同一份源码。

## What Changes

- 默认运行时来源改为**安装代码所在的 checkout**，即 CLI 实际会 import 的 `workbench` 包所在目录；从任何课程目录启动都不改变它，linked worktree 服务自己。
- 删除 worktree → primary 的 Git 指针回溯。不新增配置键、命令行开关或安装步骤。
- `--project-root PATH` 仍是显式覆盖，语义不变：仍要求该目录是 lesson-kit 源码目录，非法路径报原因且不启动服务；覆盖不改变默认来源与课程解析。
- `daemon status`、`doctor`、`/api/runtime` 报告的来源就是实际服务的来源（行为不变，取值随默认规则变化）。
- 契约协调：未归档 change `stable-runtime-live-reload` 的 delta 把"默认 primary checkout"写成了目标；本 change 接管该条款，并从其 requirement 文本与"Editable install in a worktree"场景中撤下，避免两个活跃 delta 对同一事实各说一套。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `review-workbench`：live spec 目前只规定后台服务的生命周期（start/stop/status），从未规定"服务哪份源码"。本 change 在该能力下新增 requirement `Runtime source selection`，覆盖默认来源、显式覆盖与非法路径拒绝。

## Impact

- 代码：`workbench/cli/runtime_source.py` 的 `project_root` 默认分支。无 schema、无 manifest、无 CLI 参数、无 HTTP 响应形状变化。
- 测试：`tests/workbench/test_runtime_source.py` 改写默认行为断言；daemon 身份用例沿用。
- 职责文档同 PR 同步：`docs/PRODUCT-MANUAL.md`（工作台运行与自动更新）、`docs/ARCHITECTURE.md`（Stable runtime lifecycle）、`docs/GLOSSARY.md`（运行时来源）、`docs/design/workbench-capability-maturation/contract-reconciliation.md`（CR16）。
- 未归档 delta：`openspec/changes/stable-runtime-live-reload/specs/runtime-live-reload/spec.md` 撤下被取代的条款与场景。
- 已切换的安装：在 primary checkout 做 editable 安装的用户不受影响（来源本来就是它）；从 worktree 安装的用户默认来源切到该 worktree，旧 `daemon.json` 来源不匹配时按既有规则拒绝复用并要求先安全停止，不静默杀进程。
