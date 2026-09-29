# Agent context from current learning state

**日期：** 2026-09-29

## 变化

- Agent 的练习上下文直接读取服务端 active practice，浏览器传来的临时 `seen` 不再是进度事实来源。
- 浏览器只补充当前可见的知识点选择、练习筛选条件与未提交草稿。
- 组卷页上下文包含保存试卷摘要；有焦点试卷时从受管理 practice-set 文件重建完整题目上下文。
- 做题记录页上下文读取最近的持久化 attempts / verdict / rating / note。
- 知识点列表页把当前勾选知识点解析为真实 Pool 对象。
- 所有新增上下文均有数量/文本边界，不抓整页 DOM，也不把普通问答变成写操作。

## 边界

本变更只增强 Agent 的读取上下文；不新增自动组卷、自动开始练习或隐式学习记录写入。
