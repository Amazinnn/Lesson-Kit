> Historical entry: this retention policy was superseded on 2026-10-10 by [PR106 restoration](2026-10-10-restore-pr106-problem-label-removal.md). Current registered databases physically omit `problems.topic_label`.

# 既有课程题目标签值保护

逻辑退役题目主题分组不等于删除历史数据。用户强调已有课程数据库操作须谨慎，当前交付以非破坏兼容为默认：普通 schema ensure 停止删除旧 `problems.topic_label`；已存在的列和值在兼容表升级中保留，没有该列的升级目标不新增它。题目新写入、搜索与 UI 仍不使用该字段，闪卡标签保持原有能力。

未来需要物理删除时，须另行明确迁移与恢复验证；本次未运行实池迁移，也没有推断任何实际删除授权。

2026-10-09 从注册表定位实池，用 SQLite `mode=ro`、`query_only` 读取并备份到临时副本。仅对副本运行两次 ensure，结果如下：

| 课程 | 题目行 | 有历史标签的行 | 标签与既有学习行保留 | 实池写入 |
|---|---:|---:|---|---:|
| dmath | 345 | 303 | 是 | 0 |
| c02 | 497 | 497 | 是 | 0 |
| ncmc | 182 | 182 | 是 | 0 |
| c04 | 1021 | 1021 | 是 | 0 |

临时旧表重建与重复 ensure 的失败回归已先复现；修复后迁移、微题、展示元数据、problem-patch 定向检查共 64 项通过。独立最终验收仍由后续阶段承担。
