# 工作台富文本与信息架构收尾

## 最终行为

- Agent、练习、解析、会话末作答、知识点和图谱文本统一使用零依赖安全 Markdown 子集，支持标题、列表、引用、代码、强调、安全链接、wiki、数学和工作区图片；流式 Agent partial 合并为一个消息。
- Agent 右栏默认显示完整本地会话列表；新建先明确选择 Codex/Claude，创建后 Provider 锁定；会话支持显式标题、用户重命名、返回列表和删除本地 Lesson Kit 镜像，运行中删除返回冲突；不再自动每日新建。
- 图谱右栏改为学习看板，显示状态、正式题数、邻居/主要关系、信号、调度和知识点深链；仅保留知识点状态快速编辑，正文和关联题深读回到正式知识点页。
- 服务端 Markdown 页面与客户端语义同步；三栏和既有路由、学习记录、API/Bridge 契约保持兼容。

## 验证证据

- `python -m pytest tests -q`：`215 passed`。
- `node --test tests/workbench/workbench_ui_interactions.test.js tests/workbench/agent_session_ui.test.js`：`21 passed`。
- `node --check workbench/server/static/workbench.js`、`graph-physics.js`：通过。
- `openspec validate unified-workbench-rich-text --strict`、`agent-session-list-ia --strict`、`graph-learning-dashboard --strict`：通过；三个变更已归档，`openspec doctor` 干净。
- `python lessonkit.py guard extract-problems --course dmath --chapter ch06`、`problem-set --course dmath --chapter ch06`：均 PASS。
