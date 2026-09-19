# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（MODIFIED Declared figure area + ADDED Gated figure patch channel / Legacy source-image migration）strict 通过
- [x] 1.2 design + tasks

## 2. 实现

- [x] 2.1 `workbench/ingest/__init__.py`：figure-patch gate（源存在/哈希派生命名/扩展白名单/文本引用强制/目标冲突检测）+ `_apply_figure_patch`（备份→复制→UPDATE→批次）+ 前值快照
- [x] 2.2 `rollback_batch`：figure-patch 分支（从快照恢复 text/figure_paths；不动已落盘文件）
- [x] 2.3 `migrate_legacy_figures`：扫描引用→定位源→预计算真名重写→组装 manifest；dry-run 默认、`--apply` 执行
- [x] 2.4 recipe `figures` 注册 + CLI（recipe 选择项、`ingest migrate-figures [--apply]` 动作）

## 3. 测试

- [x] 3.1 gate/apply 成功路径：文件落盘（真名）、text/figure_paths 更新、ingest_batch_id 不变、批次登记
- [x] 3.2 失败零写入：缺源文件 / 文本缺引用 / 目标冲突（同名不同字节）/ 未知题目
- [x] 3.3 回滚恢复前值（figure_paths 为 NULL 的行恢复 NULL）
- [x] 3.4 迁移：dry-run 零写入 + apply 后文本重写为真名逻辑路径、文件落盘
- [x] 3.5 渲染：`_image_replace` 把逻辑路径映射到 figures 路由

## 4. 验证与交付

- [x] 4.1 全量基线：pytest / node --test / compileall / openspec specs strict / guard
- [x] 4.2 真机迁移：`ingest migrate-figures lesson-kit --apply`（真实池，先备份）+ 练习页 prob-078 截图走查
- [x] 4.3 文档：GLOSSARY「附图」、PRODUCT-MANUAL、ACTION-GRAPH、changelog
- [x] 4.4 归档 change
