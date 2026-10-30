# 2026-10-30 — 稳定运行时与安全热更新（stable-runtime-live-reload）

分支 `codex/runtime-live-reload`，基线 `2d1242b9`。修复全局 editable 安装绑定陈旧来源、
仅按 PID 复用守护进程、HTTP 进程无重载机制的问题。

## 交付内容

- 运行来源：dashboard/daemon/serve 默认跟随安装源码的 Git 主 checkout；`--project-root PATH`
  显式预览 worktree；子进程以目标 cwd + PYTHONPATH 启动，显示与导入一致。
- 监督/工作进程：稳定 supervisor 持有 HTTP worker；`daemon.json` 记录来源、双 PID、代次与本地
  凭据；复用/停止只作用于已验证身份，旧版身份只诊断不强杀。
- 安全更新：0.5s mtime/size 快照 + 两次一致确认；语法/入口导入预检失败保留旧 worker 并显示
  诊断，修正后才替换；资源变化只递增 assets_generation。HTTP admission 先关新写入并排空在途
  写请求，再在 Bridge 锁内检查活动/排队/审批占用，最后排空全部已接纳 GET 后才关监听。
- 浏览器恢复：每秒轮询 `/api/runtime`；代次变化时按稳定身份暂存并恢复输入/选区，不触发发送或
  提交；IME 组字、未确认写请求、异步 Paper/目标/心得脏编辑延后刷新并显示提示。
- 文档：GLOSSARY/ARCHITECTURE/PRODUCT-MANUAL/ACTION-GRAPH/L2-interfaces 已同步；
  OpenSpec change `stable-runtime-live-reload` 严格校验通过。

## 验收证据（task 1–2、3.1）

- 定向回归 54 项通过（CLI daemon/surface、runtime admission/process、runtime_source）。
- 真实隔离子进程：复制源码 + 显式 `--project-root` + 独立 `LESSONKIT_WB_HOME` + 空闲端口，
  验证忙碌延后、语法错误保旧、修正重载、资源更新不换 Python PID、安全停止。
- 浏览器 fixture（通用 CodeMirror + 异步 Paper）：文字/选区恢复、只读不覆盖、零提交、IME 延后。

## 复审修复（本日）

- `prepare_runtime_reload` 不再把无活动 owner 的持久化 running/waiting_for_stop 记录当作忙碌：
  那是旧服务中断留下的孤儿，`_recover_interrupted` 会在会话下次读取时转为诚实失败；此前它们会
  永久阻塞 reload 与 stop。真实排队消息与待批准 Paper 仍照常延后（回归
  `tests/test_runtime_admission.py`）。
- 浏览器恢复改为同步页面模型：恢复赋值后派发 input/change，队列编辑草稿（`aiQueueEdit`）等
  input 驱动的模型在队列重绘后不再丢字（真实浏览器 RED→GREEN，含 IME 复验）。
- 手册与架构限定重载范围：自动替换的是 HTTP worker；supervisor 自身与
  `workbench.cli.runtime`/`workbench.cli.service` 编排模块的修改下次启动才生效。

## 未完成与边界

- task 3.2（独立全量验收）未完成，不得勾选；独立 reviewer 复审仍在进行。
- 未合并、未部署：本分支未并入 main，全局安装与真实 3081 服务未切换到本实现。
- 隔离测试纪律：不改真实课程、全局安装、真实服务；复制源码 + 显式来源 + 独立 home + 空闲端口。
