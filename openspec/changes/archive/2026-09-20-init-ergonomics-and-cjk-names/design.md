# design — init-ergonomics-and-cjk-names

## 上下文

- `workbench/cli/main.py:471` 的 `p.add_argument("path")` 是必填；`--name`/
  `--chapter` 本就可选，`--course` 只在 bootstrap 新目录时必需
  （`_bootstrap_workspace` 里报「init on a new folder requires --course」）。
- 池库名 = `pool/<course>.db`；course 是**全部内容 id 的前缀**，且微测/闪卡门禁
  正则只收小写 ASCII（`workbench/ingest/__init__.py:39,41`）。所以中文文件夹名
  不能直接当 course——这就是 `--course` 仍"十分必要"的技术原因。
- 服务端四条路径各自 `path.split("/")` 后直接拿段查注册表
  （`app.py` 的 `_match_route` :295、`_send_page` :180、`_send_figure` :250、
  `_send_graph_artifact` :275），全仓无 `unquote` → 百分号编码的 CJK 名必然查不到。
  实测：`WorkbenchHandler._match_route(None, "GET", "/api/w/%E5%A4%A7.../weak")`
  返回的 `name` 是编码串而非原名的。
- `registry._find_pool` 是私有的，被 `register` 用来取 `pool/*.db` 中排序第一份。

## Goals / Non-Goals

**Goals**

- 在课程文件夹里 `lesson-kit init --course <slug>` 一条命令完成；ASCII 安全的
  文件夹名连 `--course` 都能省（真零参）。
- 中文目录可正常 init、可正常打开工作台（路由解码）。
- 报错永远给出可粘贴的完整命令。

**Non-Goals**

- 不做交互式提问（所有者明确：现在没复杂到需要）。
- 不做拼音/转写依赖；不自动把 CJK 名变成 ASCII。
- 不改"已成型工作区注册"的池发现规则（仍取排序第一份 db），不改池 schema，
  不动 `pipeline/`。

## 决策

### 一、`path` 默认 `.`

唯一由「必填」变「可省」的既有参数；`lesson-kit init` 在 cwd 里等价于
`init .`。help 文案写明默认值。

### 二、course 的三个来源，次序与边界

`--course`（显式）> 已成型工作区的池文件名 > ASCII 安全的文件夹名。
- ASCII 安全 = 文件夹名 `isascii()`，且 `lower()` 后把非 `[a-z0-9]` 连续段折叠为
  `-`、两端去 `-`，结果匹配 `[a-z0-9][a-z0-9-]*`（例：`Linear Algebra (Spring)`
  → `linear-algebra-spring`）。
- 三者都拿不到（CJK 名 + 新目录）→ `SystemExit`，并打印
  `lesson-kit init --course <slug>`（若用户给了 path 参数则原样带回）。
- 为什么把池文件名放在文件夹名之前：已成型工作区的 id 前缀由池里既有内容决定，
  用文件夹名推导会与内容脱节（历史上空 course 导致 `wb ls` 全零、被演示抓到的坑）。

### 三、`--name` 保持默认文件夹名

修好路由解码后 CJK/带空格名可用；不再要求 ASCII，也不做名字收敛（URL 负责编码）。
真正的名字自由度归用户，`--name` 仍可覆盖。

### 四、路由逐段 `unquote`

四处（页面、API 匹配、附图、图谱工件）在查注册表/拼磁盘路径前对每个路径段解码；
`urllib.parse` 已经 import，改动量是每处一行。不做 slug 校验——保持"名字自由、
URL 负责编码"的单一职责。同时把 API 分派里 `registry.get_workspace(name)` 的
`KeyError` 收成 404 JSON：另外三条路径都有这个兜底，只有它没有——未知名会抛到
`BaseHTTPRequestHandler` 外面变成连接异常，与 spec 的"未知名字仍干净地 404"冲突。

### 五、公开 `registry.find_pool`

`init` 需要一个"从池文件名反推 course"的能力，而 `register` 已经用同一函数定位
db；把它提为公开，避免两套池发现逻辑（该逻辑历史上咬过一次：备份 db 排序靠前会
被当成工作区 db）。

## Risks / Trade-offs

- 推导出的 course 可能与用户预期不同（例如文件夹叫 `Slides` 却想要 `uphy2`）；
  显式 `--course` 永远覆盖，且 id 前缀一旦有内容入库再改代价高——所以"推导只在
  文件夹名 ASCII 时发生"是刻意保守。
- 中文文件夹名仍要打一次 `--course`：这是内容 id 前缀的硬约束，不是可绕的体验问题；
  报错里的可粘贴命令把输入成本压到"复制—改 slug—执行"。
- 路由解码后，注册表里同名的两个工作区（编码不同写法）仍按精确串匹配，不做归一化；
  单用户本机不构成问题。
