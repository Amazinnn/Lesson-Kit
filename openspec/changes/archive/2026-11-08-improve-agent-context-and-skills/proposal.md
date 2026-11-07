## Why
Pi 在提出制作闪卡后把用户“好”误读为结束问答；每轮页面焦点过强，缺乏持续要求和可管理的 Skill 入口。
## What Changes
- 明确消息与对话承接优先于页面默认焦点，注入最近两轮原文。
- 用户级全局要求、Skill 导入/列表/详情/启停/删除，下一轮生效。
- 持续授权下主动合并知识点经验，保留并发与真实成功边界。
## Capabilities
### New Capabilities
- `agent-resources`: 全局要求和本地受管 Skill 管理。
### Modified Capabilities
- `agent-context`: 页面锚点不覆盖任务承接。
- `ai-teacher-bridge`: 外部 Provider 的提示词和 Skill 发现。
- `practice-experience`: 持续请求构成经验记录授权。
- `workbench-ui`: 设置页全局要求和 Skill 管理。
## Impact
仅 workbench 新代码，用户级 JSON/文件资源，不改 Pool schema 或外部 Agent 全局配置；不实现内置 Agent、在线市场或对话 Skill 选择。main 合并与 ps-006 恢复已独立完成，恢复证据保存在真实工作区 recovery 目录。
