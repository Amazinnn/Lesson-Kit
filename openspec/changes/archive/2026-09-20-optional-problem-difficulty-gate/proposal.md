# optional-problem-difficulty-gate 提案

## Why

8-27/8-30 的讨论已定案：难度评价是跨题型的统一评价体系问题，具体拟合/评估算法
排到「真题拟合」联合立项（PENDING-DEFINITIONS，等 Check 首期真实使用后启动）。
但池里**题的难度今天完全不存在**——`problems` 表没有 difficulty 列，正式题与
微测的门禁字段里也没有它（真实池 8 个 ingest manifest 一次都没出现过）。真到
拟合立项那天将无数据可用。

本变更只做第一步：把难度定为**可选属性**并给出门禁语义——填了受形式校验、
不填放行——为拟合攒下第一批能用的难度值，不引入任何消费者。

## What Changes

- `problems` 增列 `difficulty INTEGER`（可空、允许 1-5）；正式题与微测共用一列；
  闪卡不加。
- 入池通道（微测 patch、正式题 apply、KP content-patch）对难度取**可选**语义：
  填了必须是 int 1-5，且同一 item 必须带非空依据 `difficulty_basis`；缺依据 →
  拒收整批；不填 → 放行。
- KP content-patch 的难度从**必填**放宽为可选（与题一致）。`pipeline/` 的
  legacy 路径（`insert-knowledge-points.py` 缺失默认 2）按分层铁律不动；两条
  路径的行为差写进 spec。
- 生成侧（任务模板与审计清单）要求逐项给出难度 + 一行依据，**允许弃权**
  （不确定就不填）——「可选」体现在允许弃权，而不是没人提。
- **依据不落盘**：只在门禁当下校验非空，不写池、不新增依据列。
- 量纲沿用 KP 既有 1-5 语义（`pool-field-inference`：按 knowledge_type 默认
  1-4、含证明/推导/综合 +1、跨章节综合 = 5）并给出题面映射；写进 GLOSSARY
  「难度」条目。
- 顺手修正一个误名：日计划队列项里的 `difficulty_mix` 实际装的是**题型直方图**
  （`planning.py:64`），改名 `problem_type_mix`，避免它看起来已在消费难度。
- 不做消费者、不回填 303 道旧题（保持 NULL）。

## Capabilities

### Modified Capabilities

- `workbench-content-governance`：新增「可选难度声明」要求（形式校验 + 依据
  同现 + 依据不落盘 + KP 与题共享同一可选语义）。

## Impact

- 代码：`pool/scripts/pool_schema.py`（`ensure_workbench_schema` 内为 problems
  增列，allow-null + CHECK 1-5，走既有 ensure_* 增量迁移）、
  `workbench/ingest/__init__.py`（微测门禁、`_gate_content_patch`、正式题 apply
  的校验与写入、`KP_FIELDS` 的必填集合）、`workbench/domain/planning.py`（字段
  改名）。
- 生成侧：微测/正式题的任务模板与审计清单（`workbench/ingest` recipe 与配套
  任务文件）。
- 测试：`tests/workbench/`（填非法值拒收 / 填了缺依据拒收 / 不填放行 / 批内混合 /
  KP 门禁放宽后的既有用例更新 / 计划字段改名）。
- 文档：GLOSSARY「难度」条目（前置）；PENDING-DEFINITIONS「真题拟合」补记本
  变更为数据前奏（未启动立项）；ACTION-GRAPH 登记门禁动作改级。
- 学习者可见面零变更（难度不展示；PRODUCT-MANUAL「不显示算法参数」不变）。
