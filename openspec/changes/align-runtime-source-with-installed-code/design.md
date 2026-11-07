## Context

`workbench/cli/runtime_source.py::project_root()` 目前有三个分支：显式 `--project-root`、默认回溯、回落。默认回溯读安装源码目录下的 `.git`；若它是 worktree 指针文件（`gitdir: …`），再读 `commondir` 得到共享 `.git`，取它的父目录当 primary checkout 并返回。

这条回溯是上一个 change（未归档 `stable-runtime-live-reload`）为"课程 cwd 与 worktree cwd 都不影响默认来源"而写的：它假设 primary checkout 才是长期代码仓，worktree 只是临时预览。当实现本身在 worktree 里进行、且 editable 安装指向 worktree 时，这个假设直接错位——CLI import 的是 worktree 的 `workbench`，服务却 import primary 的 `workbench`。

## Goals / Non-Goals

**Goals**

- 运行时来源与"实际被 import 的代码"一致：安装在哪份 checkout，就服务哪份。
- 课程工作目录与 worktree 归属都不再改变默认来源。
- 显式覆盖保持原语义，非法路径继续如实拒绝。

**Non-Goals**

- 不加配置键、环境变量、命令行开关或自动切换逻辑。
- 不改课程解析、`daemon.json` 身份校验规则、重载机制与 HTTP 形状。
- 不处理"同一台机器想同时服务多份源码"——那仍用 `--project-root` + 独立端口。

## Decisions

### D1 默认来源 = 安装源码，删除 Git 指针回溯

`project_root()` 默认返回被 import 的 `workbench` 包所在仓库根。删除整段 worktree → primary 解析。

替代方案与其被否原因：

| 方案 | 否因 |
|---|---|
| 默认 primary + 检测到安装源码是 worktree 时告警 | 仍留下"服务和导入不是同一份代码"的错位；告警要额外通道，不改变结果 |
| 默认按当前工作目录解析 | 与既有契约冲突：课程 cwd 不得影响运行时来源；在课程目录启动会挑错 |
| 新增 `--follow-install` 开关 | 多一个需要用户记得的设置；默认仍错 |

删除而非保留分支，是本 change 唯一实质代码改动：`installed` 关键字参数保留，作为测试接缝与未来显式注入点。

### D2 非法路径继续拒绝

`--project-root` 校验（必须含 `workbench/cli`）保持原样并进 spec：它今天就是可观察行为，且是"拒绝服务非源码目录"的唯一守卫。

### D3 迁移与身份

- primary checkout 的 editable 安装：`source == primary`，可观察行为零变化。
- worktree 的 editable 安装：默认来源变为该 worktree。升级前已在跑的旧守护进程记录的是 primary，`daemon start` 会按既有规则报"running service source/port/reload differs; stop it safely before switching"，`daemon stop` 仍能按记录身份正常停止。不做静默杀进程、不做自动重启。
- 该迁移只在"从 worktree 安装"的场景出现，属本 change 的目标场景，不需要额外数据迁移。

### D4 契约协调

| 资产 | 现状 | 本 change 的处置 |
|---|---|---|
| `openspec/specs/review-workbench/spec.md` | 规定后台服务生命周期，未规定来源 | 新增 requirement `Runtime source selection`（delta ADDED），归档时并入 |
| `openspec/changes/stable-runtime-live-reload/specs/runtime-live-reload/spec.md` | ADDED requirement 把"默认 primary checkout"写成目标，含"Editable install in a worktree → imports the primary checkout"场景 | 撤下被取代的首句与该场景；保留显式覆盖、子进程导入、身份报告、拒绝猜测杀进程等条款 |
| `docs/PRODUCT-MANUAL.md` §工作台运行与自动更新 | 写"默认使用安装来源的主 Git checkout" | 改为安装代码所在 checkout，并保留覆盖说明 |
| `docs/ARCHITECTURE.md` §Stable runtime lifecycle | 同上 | 同步一句 |
| `docs/GLOSSARY.md` | 无"运行时来源"条目 | 新增术语条目（先定义后使用） |
| `docs/design/…/contract-reconciliation.md` | 无该项 | 新增 CR16 行 |

不修改 live spec 文件本身：按 OpenSpec 流程由归档同步。

## Risks / Trade-offs

- **旧守护进程**：来源不匹配时 `daemon start` 报错而非自动切换。这是既有已声明行为（"来源或端口不匹配时先安全停止旧服务"），代价是一次手动 `daemon stop`，换来不猜测身份、不误杀无关进程。
- **多 checkout 场景**：仍只能默认服务一份；`--project-root` 覆盖不变，未退化。
- **测试接缝**：`installed=` 关键字参数保留但生产路径不再传值；若未来删除该参数，测试需改为返回值注入。

## Migration Plan

无数据迁移。发布即生效：下次 `daemon start` 按新规则选源；正在运行的旧服务先 `daemon stop` 再 `daemon start`。

## Open Questions

无。
