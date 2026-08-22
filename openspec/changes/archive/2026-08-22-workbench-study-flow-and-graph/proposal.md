## Why

当前工作台把机器 ID、静态图谱页面和练习消息流直接暴露给学习者，导致难以定位知识点、连续练习会重复题目，且大量无意义交互被误认为学习记录。需要把已有知识池与学习机制组织成可读、连续且克制的学习界面。

## What Changes

- 为正式题和候选题增加可读短标题与受控主题标签，并以经过抽检的元数据回填现有题池。
- 将知识图谱改为读取实时 SQLite 模型的原生工作台视图；图谱状态使用覆盖式当前值，不追加交互日志。
- 将练习改为显式选择“每题自评”或“完成后统一自评”的多题会话；跳题和未提交草稿不写入学习记录。
- 将知识点列表、薄弱项和关联题改为以名称、状态、标题和主题呈现，原始 ID 降为辅助信息。
- **BREAKING** 旧的“每次作答即记录 attempt”不再适用于工作台练习；只有显式提交评分才形成学习记录。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `review-workbench`: 明确显式评分、覆盖式当前学习状态和零写入会话交互的持久化边界。
- `workbench-ui`: 重做题目可读性、图谱呈现和练习会话的可观察行为。
- `knowledge-figures`: 明确题目展示身份元数据与既有 Markdown 图形引用共同呈现时的稳定性。

## Impact

- 增量 SQLite 迁移、workbench data/domain/query 层、内部图谱 JSON 操作、服务端页面与 vanilla JS/CSS。
- 保留既有工作台路由和评分 API；不改 pipeline、pool 脚本行为、lessonkit.py 或 Bridge 契约。
- 不新增依赖、构建步骤、学习筛选、题量目标或 AI 教师功能。
