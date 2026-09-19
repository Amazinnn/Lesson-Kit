# design — introduce-pi-agent-and-cli

## 背景与约束

三个事实决定了本次设计的形状，全部来自 2026-09-17 的真机实测：

1. **Pi 已存在于本机**：全局 `C:\Users\yanwei\.npm-global\pi.cmd` = 0.85.1；另有
   另一项目锁定的本地 0.80.10。本机同时有两个 npm 前缀挂在 PATH 上（`D:\nodejs\node_global`
   与 `C:\Users\yanwei\.npm-global`），后者今天才被追加进注册表 User PATH。
2. **Pi 在 API 报错时进程退出码仍为 0**。实测 401 鉴权失败时 `exit=0`，错误只出现在
   事件流内。Bridge 现有的失败判定看退出码，因此必须新增流内错误解析。
3. **`normalize_event` 与 `build_command` 的回退分支都是 Claude**。任何新增 provider
   若不写显式分支，会静默套用 Claude 的 flag 与事件解析——这是接入新 provider 的最高
   风险点。

## 决策一：显式可执行文件优先于 PATH 探测

`discover()` 目前忽略 `bridges.json` 里的 `command`，只用 `shutil.which(name)`
（既有测试断言了这一行为）。本次改为：**配置了 `command` 就使用它，否则退回 PATH 探测**。

理由：本机两个 Pi 版本 + 两个 npm 前缀，使"lesson-kit 用哪个可执行文件"完全由 PATH
顺序决定。这类静默解析已经在本机真实发生——`codex` 装了两份，`D:\nodejs\node_global`
那份遮蔽了 `.npm-global` 那份。允许钉死可执行文件是把"用哪个"从环境偶然性变成显式配置。

产物同时回报解析结果（`bridge list`），使解析失败可见，而不是让 Agent 面板静默显示"暂无可用"。

## 决策二：Pi 的命令形状

```
pi --print --mode json [--model <provider/id>] [*args] [--session <id>]
```

- `--print` 是非交互模式；`--mode json` 输出逐行 JSON 事件。
- **prompt 由 stdin 投递，实测成立**：在无位置参数、仅管道输入的情况下，事件流中的
  `message_start` 携带了完整的用户消息（实测见下）。因此不需要修改
  `conversations.py` 的 provider 无关投递路径。
- 恢复会话用 `--session <id>`，id 取自 provider 自己的会话头。
- `--model` 接受 `provider/id` 形式，由 `bridges.json` 的 model 字段传入。

## 决策三：Pi 事件归一化映射

实测事件序列（`pi --print --mode json --no-tools`，鉴权失败路径，10 行）：

```
{"type":"session","version":3,"id":"<uuid>","timestamp":"...","cwd":"..."}
{"type":"agent_start"}
{"type":"turn_start"}
{"type":"message_start","message":{"role":"user","content":[...],"timestamp":...}}
{"type":"message_end","message":{"role":"user",...}}
{"type":"message_start","message":{"role":"assistant","content":[],"...","stopReason":"error","errorMessage":"401 ..."}}
{"type":"message_end","message":{"role":"assistant",...}}
{"type":"turn_end","message":{...},"toolResults":[]}
{"type":"agent_end","messages":[...],"willRetry":false}
{"type":"agent_settled"}
```

注意 `agent_settled` **未见于官方文档**，是实测发现的终态事件；`session` 头携带
`id`（即原生会话 id）与 `version`。

映射表：

| Pi 事件 | 归一化结果 |
|---|---|
| `session` | `phase provider.ready` + `provider_session_id = id` |
| `agent_start` | `phase provider.working` |
| `turn_start` | activity `provider-turn` running「Agent 正在处理」 |
| `message_start`（assistant） | activity `provider-turn` running「Agent 正在处理」 |
| `message_update` → `text_delta` | `text`（增量，供流式渲染） |
| `message_update` → `thinking_delta` | activity `reasoning` running「分析任务」 |
| `message_update` → `toolcall_start` | activity `tool` running「调用工具」 |
| `tool_execution_start` | activity（`activity_id = toolCallId`），`bash` 类→`command`「运行命令」，其余→`tool`「调用工具」，detail 取 args |
| `tool_execution_end` | 同一 `activity_id` 收敛为 done / failed（`isError`），output 取结果 |
| `message_end`（assistant，含文本） | `result`（权威回答） |
| `message_end`（assistant，`stopReason == "error"`） | `error`，文本取 `errorMessage` |
| `agent_end` | 从最后一条 assistant 消息取 `result`（兜底，防止增量缺失时无回答） |
| 其他 | `phase provider.working` |

**只认 assistant 角色的消息**：实测 `message_start` / `message_end` 也回显用户消息，
不判角色会把用户输入当成 Agent 回答。

**为什么同时发 `text` 增量和 `result`**：与 Claude 现有形状一致，且两条路径各有职责。
前端只渲染 `text`（`workbench.js:2383`），`result` 只用于服务端生成权威回答并镜像进
transcript；回合结束时前端会重新拉取会话并按 `message.content` 重渲染
（`aiRenderConversation`），所以即使增量路径缺失，回答也不会在界面上丢失。服务端
`answer = result_text or "".join(text_parts)` 保证不重复拼接。

## 决策四：后台服务

- pid 与日志放在 `registry.base_dir()`（即 `LESSONKIT_WB_HOME`，默认
  `~/.lessonkit-workbench`），与 `workspaces.json`、`bridges.json` 同级：测试天然隔离，
  用户级运行文件集中一处。
- `start` 以分离进程启动 `python -m workbench.cli.main serve --port N`，
  Windows 用 `CREATE_NO_WINDOW | DETACHED_PROCESS`，POSIX 用 `start_new_session=True`。
- **`start` 只有在端口真的应答之后才报成功**，符合 spec 的"不得在未真正服务时报成功"。
- **绝不用 `os.kill(pid, 0)` 探活**：Windows 上它会真的调用 TerminateProcess，即"探活"
  本身就是杀进程。改用 ctypes `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` +
  `GetExitCodeProcess`；POSIX 侧仍用 `os.kill(pid, 0)`。
- 单实例：pid 文件存在且进程存活即视为已在运行，`start` 幂等。
- `stop` 终止进程、等待端口释放、清除 pid 文件；进程已消失（陈旧 pid）时清理并如实报告。

## 决策五：`dashboard` 与既有在案决定的冲突

`DESIGN.md:7` 明确"不做 dashboard"，`docs/GLOSSARY.md:69` 把"第四个页面"列为 _Avoid_，
且「学习看板」一词已被图谱右栏占用。因此 `lesson-kit dashboard` **不新增页面**，语义为
"确保服务在跑 + 打开工作台"，并把这条边界写进 spec 场景以免日后漂移。

`daemon` 则与 `ADR 0004:37`（不引入 dashboarding）和 `FUTURE-DEVELOPMENT-NOTES.md:219`
（不做常驻后台服务，应用未打开时不运行）正面冲突。这是所有者在 2026-09-17 明确要求的
能力，故新建 **ADR 0022** 显式推翻上述记载，并保留其原始理由作为取舍记录。

## 风险与已消除的不确定性

**已于 2026-09-17 用 DeepSeek 官方 key（`deepseek-v4-flash`）真机验证成功路径**，
原先按文档推断的三处假设全部被实测修正：

- 实测事件序列（纯文本轮，10 类）：`session`(带 `id`) → `agent_start` → `turn_start`
  → `message_start`(user) → `message_end`(user) → `message_start`(assistant) →
  `message_update`×N → `message_end`(assistant, `stopReason: stop`) → `turn_end`
  → `agent_end` → **`agent_settled`**（官方文档未记载，只有实跑才能看到）。
- `message_update.assistantMessageEvent.type` 的取值比文档多：除 `text_delta` /
  `thinking_delta` / `toolcall_start` 外，还有 `thinking_start`、`thinking_end`、
  `text_start`、`text_end`、`toolcall_delta`。后四个只作分帧用途。
- 工具事件形状：`tool_execution_end.result` 是 `{content:[{type,text}], details}`，
  **不是字符串**；`args` 是对象且 `tool_execution_end` 不带 `args`。失败时
  `isError: true`。

因此本设计新增一条 provider 侧契约：**`normalize_event` 可以返回 `None`，
表示该事件对学习者没有任何呈现意义**（`thinking_delta` 等纯协议噪音），
两个调用方（对话轮次、ingest）都跳过它。否则 pi 每 token 一个事件会把
事件日志撑到一轮 1400 行，而这些行用户完全看不见。

其余残留风险：

- 若 Pi 未来版本改变事件名，未知事件退化为 `provider.working` 相位而非报错，
  表现为执行计划不动——可接受的降级，但真实使用时需要留意。
- pi 的全工具权限意味着它能改工作区文件（与 codex/claude 现有风险同级）。
  这是所有者明确选择的工具权限；若日后要省 token 或收缩权限，
  可用 `--args=--tools=read`（或 `--no-tools`）从配置层调整，无需改代码。
