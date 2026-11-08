# WP03 2.4 部署切换证据（2026-11-08）

S008：准备/备份/副本验证通过后直接切换，不等待另一批准。

## 切换性质

WP03 **无 schema 变更、无破坏性数据操作**：迁移是 JSON 级（会话/turn 工件内的 pending approval），Data 层零迁移；副本验证 = 全仓 pytest（1583）+ wb64 副本上的真实执行（见 2.1/2.2/2.3 证据）。真实池可恢复备份未新生成（本包不写池），切换失败时按既有备份机制恢复。

## 安装与运行身份（RELEASE-02 核对，全部实测）

- **installed CLI**：`lesson-kit`（editable，dist 0.1.0），`workbench.__file__`（中性 cwd）= `D:\Projects\Academic Workflow\lesson-kit\workbench\__init__.py` = 主检出。本会话早段纠正了 `.pth` 误指向 course-sync worktree 的问题（`pip install -e . --no-deps` 重装）。
- **daemon（临时 wb64，3123）**：`/api/runtime` = `source_root: D:\Projects\Academic Workflow\lesson-kit`、`supervisor_pid: 27040`、`worker_pid: 7352`、`assets_generation: 1`。
- **daemon（默认 home，验收端口 3099 临时启动后已 stop 复原）**：`/api/runtime` = source_root 主检出（pid 6928/14388）；`GET /static/workbench.js` 实服 253,507 字节 = 新代码（`ai-paper-approval` 0 处、replay `replace: true` 在、恢复卡折叠顺序修复在、`wbApplyCollapse` 在）；`/static/agent-ui.js` 的 `function confirm` 计数 0；`GET /api/w/lesson-kit/ai/sessions` 200（新代码读真实工作区会话）。验收后 `daemon stop` 已执行，3099 端口停止（000）。
- 静态资源版本：workbench.js 与 agent-ui.js 内容指纹与主检出工作树一致（grep 标记法核对）。

## 切换执行

主检出即安装来源，默认 daemon 停止态；所有者下次 `daemon start` 即服务本包代码，无残余审批入口。切换失败恢复：任何模块语法/入口错误由 live-reload 保留当前服务并显示诊断（runtime-live-reload 能力），池数据不受影响。
