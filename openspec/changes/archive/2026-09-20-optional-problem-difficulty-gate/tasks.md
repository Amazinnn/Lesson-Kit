# Tasks

## 1. Spec

- [x] 1.1 proposal（Why / What / Capabilities / Impact）
- [x] 1.2 specs delta：`workbench-content-governance`（ADD Optional difficulty declaration）
- [x] 1.3 design + tasks
- [x] 1.4 `openspec validate --change 2026-09-20-optional-problem-difficulty-gate --strict` 通过
- [x] 1.5 前置：GLOSSARY 建「难度」条目（指什么 / 不指什么 / 正反例 / 谁负责解释）

## 2. 实现

- [x] 2.1 `pool/scripts/pool_schema.py`：`ensure_workbench_schema` 内为 `problems` 增列 `difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5)`（allow-null；幂等）
- [x] 2.2 `workbench/ingest/__init__.py`：难度校验的一个共用帮助函数（值域 + 依据同现），供微测门禁、正式题 apply、KP content-patch 三处调用
- [x] 2.3 `workbench/ingest/__init__.py`：`KP_FIELDS` 移出 `difficulty`；`_gate_content_patch` 改「填了才校验」
- [x] 2.4 `workbench/ingest/__init__.py`：微测 patch 与正式题 apply 读取可选 `difficulty` / `difficulty_basis` 并写入 `problems.difficulty`（依据不写库）
- [x] 2.5 生成侧：微测/正式题任务模板与审计清单补「逐项给出难度 + 一行依据；不确定可弃权并写明」
- [x] 2.6 `workbench/domain/planning.py`：`difficulty_mix` → `problem_type_mix`（含 `tests/workbench/test_planning.py`；历史计划文档不改写）

## 3. 测试

- [x] 3.1 填了合法值 + 依据 → 门禁通过且行里带值
- [x] 3.2 填了值缺依据 → 整批拒收并点名
- [x] 3.3 不填 → 通过且列为 NULL
- [x] 3.4 越界 / 非整数 → 拒收
- [x] 3.5 批内混合（有填有不填）→ 通过；依据不出现在池中（查询断言）
- [x] 3.6 KP 门禁：省略难度 → 通过；填了难度无依据 → 拒收（既有必填用例相应更新）
- [x] 3.7 迁移幂等：对既有池重复跑 `ensure_workbench_schema` 不报错、不丢数据

## 4. 走查（真机）

- [x] 4.1 用真实池把一个既有 mq 批改造成带难度 + 依据，走 prepare→gate→apply，确认入库值与台账
- [x] 4.2 反例走查：同批去掉一条依据 → 门禁拒收（截屏留档）
- [x] 4.3 确认学习者可见面无变化（练习页/知识点页无难度显示）

## 5. 文档与交付

- [x] 5.1 `docs/GLOSSARY.md`：「难度」条目（1.5）
- [x] 5.2 `docs/PENDING-DEFINITIONS.md`：「真题拟合」补记本变更为数据前奏（未启动立项）
- [x] 5.3 `docs/ACTION-GRAPH.md`：登记门禁动作改级（难度必填 → 可选 + 依据）
- [x] 5.4 全量基线：pytest / node --test / compileall / `openspec validate --specs --strict` / guard extract-problems
- [x] 5.5 归档：`openspec archive 2026-09-20-optional-problem-difficulty-gate`

## 备注（实现期发现，已处理）

- **旧池兼容**：workbench 从不在打开池时迁移 schema（只有 `create-tables.py` 与
  `pool/scripts/migrate-progress.py` 会）。因此给三条通道加了保护：未迁移的池上
  **不声明难度照常可用**（INSERT 动态列），**声明了则拒收**并给出
  `python pool/scripts/migrate-progress.py --db pool/<course>.db`。真机验证：
  未迁移 → 拒收 + 提示；迁移（新增 `problems.difficulty`）→ 入库 `difficulty=2`、
  未声明行保持 NULL、无 `difficulty_basis` 列、台账记 batch-003。
- **生成侧边界**：正式题的任务模板与审计清单活在被冻结的 `pipeline/`（分层铁律），
  本次只改 workbench 侧入口——会话提示词（微题字段 + 依据规则 + 弃权说明 + 示例）。
  正式题通道的门禁已能读写可选难度，但「要求逐项给出」的措辞落在 pipeline 任务
  文档，属后续（若所有者解冻该层）或拟合立项的事。
- **走查方式**：用真实池的**副本**走完整 CLI 门禁（不向真实池写测试数据），
  迁移也只在副本上执行；所有者真实池的迁移由交付报告提示。
