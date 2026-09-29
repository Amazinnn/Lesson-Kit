# Agent runtime model routing

**日期：** 2026-09-29

**类型：** 功能增强 / 对话路由

## 变化

- Agent 对话不再锁死创建时的 harness；聊天头部模型选择器展示所有当前可用的模型目标，并可在 Pi / Codex / Claude 等已发现 harness 之间切换。
- 模型目标保存命名 entry、模型 id 与 entry 专属参数，修复“配置了 named model 但实际 turn 丢失 args”的问题。
- named model 只覆盖自己的 harness；配置 Pi 模型不会再让未配置 named model 的 Codex/Claude 从目录中消失。
- Pi 通过 RPC `get_available_models` 自动补充运行时模型，并在常驻进程存在时优先用 `set_model` 原地切换。
- 跨 harness 或需要 fresh native session 的切换保留 Lesson Kit 本地 transcript，并在新 transport 的首轮携带有界历史 handoff。
- 修复 PATCH `{"model": null}` 被误判为“没有更新字段”的问题。

## 兼容性

- 旧的 `conversation.json` 只有 `provider` / `model` 时仍可读取；新增的 `model_entry` / `model_args` 都是增量字段。
- Codex/Claude 不依赖未承诺的动态模型枚举接口，继续使用默认 harness 与显式配置的 named models。
- Pi 运行时模型发现失败只降级为静态目录，不会让 Agent 功能整体不可用。
