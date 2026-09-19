# land-source-figures 提案

## Why

附图的决定链（REQUIREMENTS #10 → ADR 0017 → knowledge-figures spec）与代码管道
（figures 路由、`figure_paths` 列、前端 Markdown 重写）在早前 change 中已建成，但
「最后一公里」从未打通：没有任何代码写入过 `figure_paths`，真实池 0 张图，
`.lessonkit/figures/` 目录不存在。**当前 6 道题（prob-078/127/175/212/218/286）的
题干里嵌着 `images/<hash>.jpg` 引用，在练习页上是坏图**——图文件躺在
`intermediate/dmath/extraction/ch06/00_source/images/`，没有任何路由能到达。

grilling 定案（2026-09-20，所有者签字）：附图第一版 = 存量修复 + 正式入池通道；
图是题目文本的附庸；文件名**全部采用内容哈希**（spec 原定的
`{owner_id}-fig-{NNN}.png` 规则作废）。实测补充事实：存量文件名并非当前字节的
sha256（6/6 失配），因此落图时按**真实内容哈希重命名**，名字由门禁计算。

## What Changes

- **spec 命名规则变更**：图文件名 = `<sha256hex>.<原扩展名>`，内容寻址、天然去重；
  `{owner_id}-fig-{NNN}.png` 规则移除。
- **figure-patch 门禁通道**（ingest 家族新增 recipe `figures`）：manifest 携带图源
  路径与新的题干全文，门禁校验（源存在、哈希命名、题干必须引用每张图、目标无冲突）
  后单事务落图 + 更新 `problem_text` 与 `figure_paths`；失败零写入；批次登记；
  回滚恢复前值（快照携带 previous 值）。`ingest_batch_id` 不被改写，原批次溯源保持。
- **存量迁移**：ingest 家族新增 `migrate-figures` 动作——扫描题干中
  `](images/<文件名>)` 引用，从 `intermediate/**/images/` 定位源文件，生成
  figure-patch manifest（默认 dry-run，`--apply` 执行），复用同一条门禁通道。
- **范围**：v1 只支持题目（problems）；KP 附图延后。网页端预期零改动
  （`_image_replace` 已把逻辑路径映射到 figures 路由），以走查验证。

## Capabilities

### Modified Capabilities

- `knowledge-figures`：图命名改为内容哈希；新增门禁化的落图通道要求。

## Impact

- 代码：`workbench/ingest/__init__.py`（figure-patch gate/apply/rollback、
  migrate 函数、recipe 注册）、`workbench/cli/main.py`（recipe 选择项 +
  migrate-figures 动作）。
- 数据：真实池 6 题 `problem_text` 重写 + `figure_paths` 首次写入（走备份+批次）；
  图文件落到 `.lessonkit/figures/dmath/ch06/`。无 schema 变更（列已存在）。
- 文档：GLOSSARY「附图」条目、PRODUCT-MANUAL、ACTION-GRAPH、changelog。
- 风险：AGENTS.md「禁止哈希」指代码设计纪律；内容哈希**文件名**是所有者签字的
  命名决定，不适用该条。
