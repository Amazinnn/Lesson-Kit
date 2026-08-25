# Agent 原生工作台对话与内容治理

## 最终状态

- `wb data <workspace>` 提供知识点、正式题、候选题和关系的 JSON 查询、搜索、历史、显式修改、状态覆盖、门禁和晋升；只读操作不写入 SQLite。
- 新内容使用课程/章节范围内的可读顺序 ID；候选编辑会重置双门禁；正式题只能由双门禁候选晋升；题目和知识点删除按单事务清理从属学习记录。
- 右栏改为自由 Agent 对话：自动发现 PATH 中的 Codex/Claude，Provider 会话锁定，支持原生续聊、事件轮询、停止、最近会话、可选每日新会话和练习草稿显式附带。
- 服务端按工作区、路由、对象 ID 和 SQLite 重建上下文，不发送整页 DOM；未提交作答默认不进入 Agent 上下文；旧 explain/diagnose API 保留兼容。
- Paseo 仅作为生命周期交互参考，没有引入远程服务、守护进程或新依赖。Claude 只保留 PATH 发现，不启动、不调用。

## 验证证据

- `python -m pytest tests -q`：`207 passed`。
- `node --check workbench/server/static/workbench.js`：通过。
- `node --test tests/workbench/workbench_ui_interactions.test.js`：`17 passed`。
- `openspec validate agent-native-workbench-conversation --strict`：通过。
- `python lessonkit.py guard extract-problems --course dmath --chapter ch06`：PASS。
- `python lessonkit.py guard problem-set --course dmath --chapter ch06`：PASS。
- `:3081` HTTP 冒烟：练习、知识点、图谱、会话末均返回 200；新 AI 栏可见、旧讲解/诊断按钮不再渲染；Provider 列表返回 Codex/Claude。
- 隔离临时目录真实 Codex CLI：返回 `LESSONKIT_CODEX_OK`；真实桥接 fixture turn：`done`。未启动 Claude。
