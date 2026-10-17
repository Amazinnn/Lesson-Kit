# Attempt 外键修复实施交接 · 2026-10-17

追加：按用户要求已完成真实物理/CO 库副本与浏览器验收，见
[真实副本验收](audits/2026-10-17-attempt-real-copy-acceptance.md)。以下原实施记录中的
“仅合成测试”“未创建快照”描述是该次实施结束时的状态，由本次验收记录补充；原始课程库仍未写入。

Change：`repair-attempt-migration-references`。实施分支：`fix/attempt-migration-references`，
基于文档提交 `351eeeb0`，隔离目录 `.worktrees/repair-attempt-references/`。

## 已实施

- 在既有 `pool/scripts/pool_schema.py` 中修复状态约束迁移；直接沿用旧 DDL，只扩展状态枚举。
  原有列、约束、值、ID、自增高水位、索引、触发器和健康入向引用保留。
- 检查全部表的实际外键，修复临时父表引用，即使正式父表约束已是当前版本。
  重建不先改名原父表；字段默认值中的同名文字不被替换。
- savepoint 保留调用方事务边界和设置；故障回滚。外键开启且已有事务时写入前拒绝。
- 缺失父数据保留并警告，列出剩余外键问题及可解析的 attempt ID；不删除检查点、不补造作答。
- 同步 live governance spec、DATA_MODEL、Architecture、Product Manual 和 Action Graph。
  FILE_CONTRACT 无新工件/字段，GLOSSARY 无新名词，CLI/API 入口未改变。

## 验证与验收边界

13 项聚焦回归覆盖两种外键入口、健康/已损坏结构、多张子表、祖孙引用、额外旧列、索引/触发器、
自增高水位、幂等、缺失父行、调用方事务、故障回滚、默认值保留、文件重开和既有迁移命令。
测试数据库均为内存或 pytest 临时目录中的合成数据。

本实施 Agent 对最终代码运行的检查：`PYTHONUTF8=1 python -m pytest tests -q`
1022 passed（202.78s）；相关 Python 检查 72 passed，其中新增回归 13 passed；
全部官方 `*.test.js` 196 passed；compileall、`openspec validate --all --strict --concurrency 3`
26/26、`guard extract-problems --course dmath --chapter ch06` 和 `git diff --check` 通过。

独立验收任务 2.2 保持未完成：本 Agent 的检查不冒充另一位 Agent 的独立验收。
由用户指定验收 Agent 后，对候选提交运行所需完整检查及隔离迁移保全比较；本轮不自行委派。
未归档 change，未部署运行服务，未合并 main。

## 真实 CO 保持待授权

未读写或迁移真实课程库，也未创建或宣称验证新的课程备份。
此前事实与备份检查来源见 `docs/audits/2026-10-17-paper-agent-investigation.md`；本次没有重查，
不得把该快照说成实时状态。已知风险是旧题引用与 attempt 父记录缺失；此结构修复不恢复那 19 个标记
所指向的作答。执行真实修复前，另行取得授权、验证可恢复备份、在副本比较受影响数据与非目标结构，
记录当时完整 `PRAGMA foreign_key_check` 结果和备份来源。无自动题号重映射或进度转挂。

## 给 Paper 实施 Agent

结构修复代码已可在本分支测试；合并前仍需独立验收。健康旧状态可以据此验证迁移；
真实 CO 的缺失题目/作答仍不满足无损进度迁移前提，不得因为外键名称修好了就接受或清除异常进度。
其余两个 change 的任务和实现均未改动。
