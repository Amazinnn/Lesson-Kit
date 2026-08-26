# 2026-08-26 linked reading and minimal Agent chat

- 关联题主题改为默认折叠；展开后直接显示短标题与完整安全 Markdown 题干，不再渲染摘要、截断片段、嵌套全文 disclosure 或原始题目 ID。
- `display_summary` 元数据门槛调整为规范化题干超过 500 字且可选；题池清单回填为 303 道题、19 条摘要。
- Agent 客户端删除 Provider 记忆、每日自动建会话、自动打开首个会话和旧 explain/diagnose 控制台；聊天态只保留返回图标、消息、输入和运行中停止，列表行负责重命名/删除。
- 验证：`python -m pytest tests -q`（215 passed）；Node UI（22 passed）；`node --check` workbench/graph；OpenSpec strict；extract-problems 与 problem-set guards 均 PASS。
