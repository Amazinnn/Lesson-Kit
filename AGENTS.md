# AGENTS.md — lesson-kit 开发纪律

> 阶段 2–3 产物（开工检查清单）。任何 Agent（Claude Code / DSH / Codex…）在本仓库
> 工作时必须遵守。新对话开场先复述：**分层方向、兼容边界、scope 边界**，复述不对请纠正。

## 兼容边界（硬规则，违反先问）

| 层 | 策略 |
|---|---|
| 用户数据格式 | 开发期可改测试数据；进入维护期必须向后兼容 |
| 用户可感知的行为 | 必须兼容，以旧为优先；有充足优化动机时先问再做 |
| 内部代码接口 | 允许删减重构，但必须在高度模块化前提下，禁止"自由重构" |
| 文档 / 规范 | 是资产不是负担；改动代码必须同步 OpenSpec / ARCHITECTURE.md / ADR |

## 分层铁律

- 单向依赖：Shell → Domain → Data；Content 读产物；Bridge 旁挂只被请求。
- Domain 纯规则零 IO；Data 是唯一碰 SQLite 的地方；CLI/Server 零业务逻辑。
- 新代码进 `workbench/`；**禁止修改** `pipeline/`、`pool/scripts/`、`lessonkit.py`
  的行为契约（可在 pool_schema.py 的 ensure_* 模式内做增量迁移）。

## 开发纪律

1. **需求先落文档再动代码**：spec 未覆盖的行为必须先改 OpenSpec（proposal→specs）或
   询问用户，禁止悄悄实现。
2. **Ponytail 阶梯**：写码前依次问——要不要写？有没有现成？标准库能否搞定？一行函数
   够不够？禁止过度工程、禁止防御性编程、禁止哈希。
3. **小步提交**：`feat/fix/docs/chore/refactor` 前缀；工作区不留脏；每完成一个可验证
   单元即提交。
4. **验证节奏**（交付前必跑）：
   ```bash
   python -m pytest tests -q
   openspec validate --specs --strict
   python lessonkit.py guard extract-problems --course dmath --chapter ch06
   python lessonkit.py guard problem-set --course dmath --chapter ch06
   ```
5. **单对话职责单一**：设计对话 / 实现对话 / 重构对话分开；长任务拆段，每段可恢复。
6. **低价值探索禁止**：实现前先走阶梯（见 2），不确定的设计先问。

## 运行时约定

- 所有 `lessonkit.py` / `wb` 命令按 CWD 解析相对路径——在仓库根目录运行。
- 运行时文件进隐藏点目录（`.lessonkit/`）：figures/ 与 explain/ 跟踪，
  jobs/ 忽略（`.gitignore` 已配）。
- 工作台注册表与 bridges 配置（JSON）在用户级 `~/.lessonkit-workbench/`。

## 新对话初始化（每次必做）

1. 喂三件套：本文件 + `docs/ARCHITECTURE.md` + 状态简报（上次到哪/这次做什么/坑）。
2. Agent 先复述关键规则（分层、兼容边界、scope），确认后再动手。
3. 交付前更新交接文档（changelog 或 STATUS 风格记录）。
