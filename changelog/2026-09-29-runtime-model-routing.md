# Per-harness Agent model discovery

**日期：** 2026-09-29

**类型：** 功能增强 / Agent 模型路由

## 变化

- Agent conversation 在创建时绑定 Codex / Claude Code / Pi 中的一个 harness；同一聊天不再允许跨 harness 切换。
- 聊天头部模型选择器只展示当前 harness 的模型；更换 harness 需要新建聊天。
- 每个 harness 都通过统一模型枚举契约提供选择：
  - Codex 使用官方 app-server `model/list`，失败时回退到本机 `models_cache.json`；
  - Claude Code 使用官方支持模型 catalog，并保留用户配置的 named models；
  - Pi 使用 RPC `get_available_models`。
- 模型目标继续保存命名 entry、模型 id 与 entry 专属参数，修复 named model 实际 turn 丢失 args 的问题。
- Pi 常驻进程存在时，模型切换优先使用 RPC `set_model`。
- 删除 cross-harness native-session reset、transcript handoff 与跨 provider PATCH。
- 修复 PATCH `{"model": null}` 被误判为“没有更新字段”的问题。

## 兼容性

- 旧的 `conversation.json` 只有 `provider` / `model` 时仍可读取；新增的 `model_entry` / `model_args` 都是增量字段。
- 用户显式配置的 named models 始终保留，可为 gateway / 自定义模型携带额外参数。
- 运行时枚举失败时保留 configured/default target，不会让整个 Agent 功能不可用。
