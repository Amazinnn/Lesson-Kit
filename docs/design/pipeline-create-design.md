# lesson-kit 抽取管线设计（Create）

**Date:** 2026-06-09
**Status:** 设计进行中 — 核心决策已定，实现细节待续
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）

## 定位

抽取管线（Pipeline）和视图构建（Views）是 lesson-kit 的两套独立系统：

| | Pipeline | Views |
|------|------|------|
| 职责 | 池子增删改查 | 从池子渲染学习产出 |
| 方向 | 源材料 → SQLite | SQLite → Markdown |
| 组织原则 | 按功能集中 | 按视图类型分区 |

本文档覆盖 **Create**（抽取 + 入库）。Update/Delete 后续设计。

## 核心决策

### 自动化程度：全自动

用户指定课程、章节、源文件路径 → Claude 自动完成全部步骤 → 池子填好。

- 不走用户审阅 checkpoints
- 不打断流程
- 质量策略："信得过，用的时候再说"——发现不对再 Update/Delete 修

### 提取方式：V17 完整分析流程

Claude 加载 V17 提取 skill，走严谨的 4 层分析流程（01_inputs → 02_analysis → 03_plans → 04_checks）。不是"直接读源材料凭感觉提取"。

### 中间文件：全部落地但不审

中间文件写入 `intermediate/{course}-{ch}/extraction/{layer}/`，用于：
- 将来出现问题时的审计追溯（「当时为什么把这个 KP 标为 core？」）
- 入库失败时保留排查现场
- 入库成功后保留作为历史记录

不用于用户实时审阅。

### 范围确定：用户命令中指定

用户在触发命令时明确指定：课程缩写、章节号、源文件路径。Claude 不自动推断。

### 池子与视图分离

维护数据库（Pipeline CRUD）和产出学习资料（Views）是两回事。Pipeline 负责池子里的数据正确，Views 负责从池子渲染学生面向的产出。各自有独立的 Command / Skill / Gate / Template。

## 待定

以下决策点尚未讨论，留待下次会话：

1. **Skill 组织**：Pipeline 是复制 V17 skill 到 pipeline/skills/（和 views/ 一样独立维护），还是直接引用 lesson-kit/skills/ 下的已有文件？
2. **Python 脚本**：JSON → SQLite 的机械操作需要哪些脚本？接口设计？
3. **JSON Manifest 格式**：Agent 产出和 Script 消费之间的桥接格式，schema 细节？
4. **Command 结构**：Pipeline 的 Command 文件（类似 views/first-pass/command.md 的 10 步工作流）怎么编排？
5. **池子独有字段推断**：importance（core/supplementary/optional）、difficulty（1-5）、fragile（0/1）——V17 没有这些字段，Claude 如何推断？需要新建一个 pool-field-inference skill 还是内嵌在 command 里？
6. **Pipeline gates**：入库前/后需要哪些质量检查？
7. **Update / Delete**：CRUD 中 C 之外的操作怎么设计？
