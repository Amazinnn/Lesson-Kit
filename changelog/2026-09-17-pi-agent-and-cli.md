# Pi 接入与首版 lesson-kit CLI（2026-09-17）

## Pi provider 接入

- **Pi 成为第三个 provider**：`SUPPORTED` 扩为 codex / claude / pi。命令形状
  `pi --print --mode json [--model …] [--session <id>]`，prompt 仍由 stdin 投递；
  原生会话 id 取自 pi 自己的 `session` 事件头。
- **发现规则变更（推翻旧行为）**：`bridges.json` 为某 provider 配置的 `command`
  现在**优先于 PATH 探测**。本机同时存在两份 pi（全局 0.85.1 与另一项目锁定的
  0.80.10）和两个 npm 前缀，旧行为下"lesson-kit 用哪个"完全由 PATH 顺序决定——
  这类静默解析在本机已真实遮蔽掉一份 codex。`wb bridge list` 报告解析结果与来源。
- **流内错误不再被吞**：实测 pi 在 API 报错时进程退出码仍为 0，错误只出现在事件流里。
  归一化把 `stopReason: error` / `errorMessage` 上抛为 error 事件，轮次失败原因
  取 provider 自报的原因，而不是"未返回回答"。
- **bridge CLI 补齐**：`bridge add` 新增 `--model`；新增 `bridge list`。
  `--args` 若要传以 `-` 开头的值需用等号写法（`--args=--no-tools`）。
- **教学契约里的 CLI 名改为 `lesson-kit data`**：原文写的是 `wb data` / `wb ingest`，
  而本机 `wb` 属于 Weights & Biases——照契约行事的 Agent 会调到别的程序。
  同时新增断言禁止契约里再出现 `wb`。

## 事件归一化（真机实测后定稿）

用 DeepSeek 官方 key 跑通成功路径后，按**真实事件流**修正了三处：

- **工具结果是嵌套对象不是字符串**：`tool_execution_end.result` 形如
  `{content:[{type:"text",text:"…"}], details:{…}}`，`args` 也是对象。
  归一化提取 `content[*].text` 并在命令类工具上取 `args.command` 作为 detail，
  否则输出区会显示一整坨 JSON。已补 `tool_execution_update`（实时 partialResult）。
- **推理行永不收尾**：pi 用 `thinking_start` / `thinking_delta` / `thinking_end` 三件套，
  原先只在 delta 上发 running，导致计划里的"分析任务"永远停在进行中。改为
  `thinking_start` → running、`thinking_end` → done、**delta 直接丢弃**。
- **协议噪音撑大事件日志**：pi 每个 token 都发一个 `thinking_delta`。实测一轮
  1406 条 `phase`、1278 条 running 活动行，全是用户看不见的噪音。现在
  `normalize_event` 可返回 `None`，调用方跳过——`thinking_delta` / `text_start` /
  `text_end` / `toolcall_delta` 不进日志。同一轮在修正后降到 phase 53 / activity 119
  （含 12 次工具调用），纯文本轮约 phase 10 / activity 11。

## 首版 CLI

- **`lesson-kit` 命令**：与 `wb` 同一实现、仅 prog 名不同；`pip install -e .` 后两者都可用。
- **从任意目录可用**（实测 `cd /tmp`）：`lesson-kit dashboard` 起了服务并打开
  `http://127.0.0.1:3081/w/lesson-kit/`。原因：命令由 editable 安装全局解析、
  注册表与 pid 走绝对路径、served 子进程固定以仓库根为 cwd。
- **后台服务**：`daemon start|stop|status` 管唯一实例（默认 3081），pid 与日志在
  `~/.lessonkit-workbench/`。`start` 只在端口真的应答后报成功；`stop` 遇到进程号
  被回收成非 Python 进程时拒绝终止并清记录。**Windows 上不用 `os.kill(pid, 0)` 探活**
  ——它会真的终止进程；改用 ctypes `OpenProcess` + `GetExitCodeProcess`。
- **`dashboard`**：确保服务在跑并打开浏览器。**不新增第四个页面**。
- **配置热读，代码不热读**：`bridges.json` 每次请求重读，改 model 无需重启；
  但 **provider 归一化等代码改动必须 `daemon stop && start`**——实测踩过：
  旧进程继续用启动时的代码，出现 1278 条 running 行，重启后即正常。

## 端到端实测结果（DeepSeek deepseek-v4-flash）

一轮含工具调用的真实回合：状态 `done`（24s），流式增量拼接与权威回答**逐字一致**
（1009 字），原生会话 id 取到，transcript 镜像正确，执行计划 12 条命令行全部
`done` 且带可读输出——Agent 自己读仓库、用 CLI 查了真实池数据（kp-006 鸽巢 /
kp-008 广义鸽巢、345 题），并在回答里引用了真实 kp_id。测试会话已删除。

## 文档

- 新建 **ADR 0022**（记录引入常驻后台服务，推翻 ADR 0004 与
  FUTURE-DEVELOPMENT-NOTES 中"应用未打开时不运行"的记载，并说明原意——不排程、
  不自启、无客户端时不消耗 Agent 调用——仍然保留）。
- **GLOSSARY** 新增守护进程、工作台命令、显式可执行文件三条。
- **AGENTS.md 补成完整入口**：新增「项目地图」，指出 `.claude/CLAUDE.md`（池契约）、
  `TASK_ROUTER.md`、`docs/GLOSSARY.md`、`skills/` 等**不会被自动加载**的文件，
  并写明 `skills/` 是路径引用而非 Agent Skills 标准包（无 frontmatter，
  不要为了"被发现"批量加）。这是跨 harness 的缺口：只读 AGENTS.md 的 CLI
  （pi、codex）此前看不到运行时地图与池契约。
- **CONTRIBUTING** 新增「Configuring an Agent provider」：provider 配置、Pi 的
  trust 陷阱（非交互模式不弹提示，默认 `ask` 会静默忽略 `.pi/settings.json` 与
  项目级 skills；`AGENTS.md` 不受限）、以及用 `--append-system-prompt` 纠正
  pi 默认"编程助手"系统提示的用法。
- **ACTION-GRAPH** 登记服务生命周期六个动作；修正 L1-services 里已退役的
  runner/contracts/teacher 与 task-providers 陈述。
- 有意**未改** `docs/DISCUSSION-RECORD.md`：该文件头部写明「逐字级保真记录」，
  且专题 21 已记录相关行为退役；改历史会破坏文档自身的契约。
