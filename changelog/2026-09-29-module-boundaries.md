# 工作台模块边界拆分

**日期：** 2026-09-29

**类型：** 内部重构

## 变化

- 将练习页 DOM 与请求生命周期移至 `practice-flow.js`；页面入口仍由 `workbench.js` 启动，练习 session 数据仍由 `practice-deck.js` 管理。
- 将结构化对话动作解析与契约校验移至 `bridge/conversation_actions.py`，保留 `conversations._extract_action` 兼容入口。
- 将 JSON 工件读写和暂存清单读取移至 `ingest/artifacts.py`，保留 `workbench.ingest` 的现有入口。
- 更新架构文档和静态资源路由测试。

## 不变

- 不改变练习、对话动作或导入的用户行为与 HTTP 接口。
- 暂存清单仍只能读取当前对话 jobs 目录内的相对 JSON 路径。
