# Tasks

## 1. 读路径退化

- [ ] 1.1 先写失败测试：最小旧池（仅 `problem_attempts` 等迁移前表）上
  `part_practice.project()` 返回整题投影、`grading_status='not_requested'`、零异常。
- [ ] 1.2 `workbench/data/part_grading.py` 增加 `has_schema(pool)` 守卫；
  `get`/`list_revisions` 在缺 schema 时返回 `None`/`[]`。
- [ ] 1.3 `workbench/data/grading_jobs.py` 的 `target`/`get` 同样退化（沿用既有
  `_has_table` 模式）；`part_practice.project` 跳过 job 查询。

## 2. 写路径退化

- [ ] 2.1 先写失败测试：最小旧池上 `part_practice.submit` 成功记录 attempt，
  不出现 `part_id/content_revision/part_attempt_context/part_grading_jobs` 依赖错误。
- [ ] 2.2 `_submit_item` 按 `has_schema` 分支：缺 schema 时只写迁移前字段，虚拟
  `whole` 小问语义不变。

## 3. 显式批改可操作失败

- [ ] 3.1 `grading.apply/withdraw/retry` 与 `dispatch_pending` 在缺 schema 时抛带
  `pool/scripts/migrate-progress.py` 指引的 `ValueError`，零写入。
- [ ] 3.2 既有 HTTP/CLI 守卫用例保持通过（`test_grading_pool_guard.py`）。

## 4. 缺口可见性

- [ ] 4.1 `lesson-kit doctor` 增加每池批改 schema 就绪检查（缺则列缺项 + 迁移命令）。
- [ ] 4.2 用例：旧池报缺、已迁移池报就绪。

## 5. 真实池迁移（运维）

- [ ] 5.1 备份并迁移 `计算机组成/pool/co.db`，复核 ch02 主观题卷子可打开、可提交。
- [ ] 5.2 备份并迁移其余 18 个未迁移已注册池；迁移后全量只读复核 22 个池。
- [ ] 5.3 重启 daemon，浏览器验证一个生产课程的可作答状态。

## 6. 文档与验收

- [ ] 6.1 `docs/DATA_MODEL.md` 补退化路径说明；`docs/PRODUCT-MANUAL.md` 补未迁移池行为；
  `changelog/` 记录。
- [ ] 6.2 `python -m pytest tests -q`、`compileall`、`openspec validate --specs --strict`、
  `guard extract-problems` 全绿。
