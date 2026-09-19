# Tasks

> 归档于 2026-09-17。除 5.4 外全部完成；5.4 有一半是有意不做，见该条备注。

## 1. Pi provider 接入

- [x] 1.1 `workbench/bridge/conversation_providers.py`：`SUPPORTED` 增加 `pi`
- [x] 1.2 同文件 `discover()`：配置了 `command` 时优先采用，否则退回 `shutil.which`
- [x] 1.3 同文件 `build_command()`：在 Claude 回退分支之前增加显式 `pi` 分支
      （`--print --mode json`、`--model`、`--session <id>`）
- [x] 1.4 同文件 `normalize_event()`：在 Claude 回退分支之前增加显式 `pi` 分支，
      按 design 的映射表实现（含只认 assistant 角色、流内错误上报、权威文本兜底）
- [x] 1.5 allow-list 三处补 `pi`：`workbench/ingest/__init__.py`（provider 校验与产物
      来源门禁）、`workbench/cli/main.py`（`ingest run --provider` 选择项）。
      实际做法改为直接引用 `conversation_providers.SUPPORTED`，消除重复元组以防漂移。

## 2. Bridge CLI

- [x] 2.1 `bridges.json` 支持 `model` 与 `command` 的写入：`bridge add` 增加 `--model`
- [x] 2.2 新增 `bridge list`：报告每个 provider 的发现结果与解析到的可执行文件路径
- [x] 2.3 `registry.add_bridge` 支持 `model` 字段落盘

## 3. 首版 CLI

- [x] 3.1 `pyproject.toml`：增加 `lesson-kit = "workbench.cli.main:lesson_kit_main"` 入口点
- [x] 3.2 `workbench/cli/main.py`：`build_parser` 的 `prog` 参数化，按入口函数区分
      （`main` → wb，`lesson_kit_main` → lesson-kit；保持 `build_parser()` 无参调用兼容）
- [x] 3.3 新增 `workbench/cli/service.py`：pid 文件读写、进程存活探测
      （Windows 用 ctypes `OpenProcess`，禁用 `os.kill(pid, 0)`）、分离启动、终止、
      端口应答确认；另含拒绝终止被回收进程号的防护
- [x] 3.4 `daemon start|stop|status` 三个子命令接线
- [x] 3.5 `dashboard` 子命令：确保服务在跑并打开浏览器到 hub
- [x] 3.6 `pip install -e . --no-deps` 使 `lesson-kit` 命令可用，并验证 `wb` 仍可用
      （用 `--no-deps` 而非 `[dev]`，避免升级所有者已有的 pytest 8.4.2）

## 4. 测试

- [x] 4.1 `tests/workbench/test_conversation_providers.py`：`shutil.which` side_effect
      集合加入 `pi`；pi 的 argv 断言（新建与恢复）、command 覆盖优先断言
- [x] 4.2 同文件：pi 的事件归一化用例（会话头 / 文本增量 / 工具活动 / 流内错误 /
      权威文本兜底 / 用户消息不被当作回答 / 推理文本不外泄 / 协议噪音丢弃 /
      嵌套工具结果提取 / 失败工具标记 / partial 更新同行）
- [x] 4.3 `tests/workbench/test_conversation_api.py`：以 pi 形状的假 provider 走一遍
      HTTP 端到端，断言回答、会话 id 与失败上报
- [x] 4.4 新增 `tests/workbench/test_cli_daemon.py`：pid 生命周期、存活探测、陈旧 pid、
      端口占用、启动失败上报、解析器；走 `LESSONKIT_WB_HOME` 隔离
- [x] 4.5（计划外）`test_conversations.py`：新增断言禁止教师契约再出现 `wb`
      （本机 `wb` 属于 Weights & Biases，契约原文会指错程序）

## 5. 文档与规范同步

- [x] 5.1 `docs/GLOSSARY.md`：新增「守护进程」「工作台命令」「显式可执行文件」三条
- [x] 5.2 新建 `docs/adr/0022-background-workbench-service.md`
- [x] 5.3 `docs/ACTION-GRAPH.md` 与 `docs/action-graph/L2-interfaces.md`：登记新增动作、
      更新命令计数（顺带修正 ACTION-GRAPH 里过期的 API 路由数 33 → 实测 30）
- [x] 5.4 修正 `docs/action-graph/L1-services.md` 与 `docs/DISCUSSION-RECORD.md` 中已退役的
      `task-providers` 陈述 —— **仅完成前半**：L1-services 已改（含移除已删除的
      runner/contracts/teacher 行并补 provider 单一发现口径）。
      `DISCUSSION-RECORD.md` **有意不改**：该文件头部写明「逐字级保真记录」，
      且专题 21 已记录相关行为退役；改历史记录会破坏文档自身的保真契约。
- [x] 5.5 `docs/PRODUCT-MANUAL.md`、`README.md`、`CONTRIBUTING.md`：补 CLI 与 Pi 的用法；
      CONTRIBUTING 另记录 trust 陷阱、`--append-system-prompt` 用法、
      「配置热读 / 代码不热读」的重启要求
- [x] 5.6 `changelog/2026-09-17-pi-agent-and-cli.md`
- [x] 5.7（计划外）`AGENTS.md` 补「项目地图」：指出 `.claude/CLAUDE.md`、`TASK_ROUTER.md`、
      `docs/GLOSSARY.md`、`skills/` 等不会被自动加载的文件，并写明 `skills/` 按路径引用、
      不要批量加 frontmatter。这是跨 harness 缺口（pi/codex 都只自动读 AGENTS.md）

## 6. 验证

- [x] 6.1 全量基线：pytest 406 / node 107 / compileall / openspec validate --specs --strict
      11 通过 + change strict / guard extract-problems PASS
- [x] 6.2 真机实测：从任意目录（`/tmp`）`lesson-kit dashboard` 起服务并打开工作台；
      `/ai/providers` 与界面选择器均出现 pi
- [x] 6.3 真机实测真实对话：用 DeepSeek `deepseek-v4-flash` 跑通成功路径（一轮含 12 次
      工具调用的回合，状态 done，增量与权威回答逐字一致，执行计划各行正确收尾）。
      据此修正三处推断错误：嵌套工具结果、推理行不收尾、每 token 协议噪音
