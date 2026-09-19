# 附图打通：figure-patch 门禁 + 存量迁移（2026-09-20）

## 背景

附图的决定链（REQUIREMENTS #10 → ADR 0017 → knowledge-figures spec）与代码管道
（figures 路由、figure_paths 列、服务端 Markdown 重写）早已建成，但从未打通：
真实池 0 张图、6 道题的题干嵌着 `images/<hash>.jpg` 引用，在练习页上是坏图。
grilling 定案：存量修复 + 正式入池通道；图是题目文本的附庸；文件名**全部内容哈希**
（spec 旧规则 `{owner_id}-fig-{NNN}.png` 作废）。

## 关键实测发现

**存量文件名与当前字节的 sha256 全部不符（6/6 失配）**——抽取时的旧哈希已失真。
因此门禁不信任任何"声称的名字"：落图时读取字节现算 sha256，名字 =
`<hex>.<小写原扩展名>`。内容寻址使同图去重天然成立。

## 实现

- **figure-patch 门禁**（ingest recipe 家族新增 `figures`）：manifest 携带图源路径
  与题干全文替换，门禁校验（源存在、扩展白名单、按内容派生名字、题干必须引用每张
  图、目标冲突检测）后单事务：备份 → 复制文件 → UPDATE `problem_text` 与
  `figure_paths`（旧值并集追加）→ 批次登记。失败零写入。文件复制在 commit 前完成
  ——commit 失败只留无引用孤儿文件（无害、幂等），绝不会出现行指向缺失文件。
- **不碰 `ingest_batch_id`**：题目行的批次戳记是其创建批次的溯源；figure-patch 只
  更新 text/figure_paths。回滚从 apply 时写入的前值快照恢复（快照 = manifest +
  previous 数组），已落盘的图文件保留（内容寻址、无引用、无害）。
- **`migrate-figures`**：扫描 `](images/…)` 引用 → `intermediate/**/images/` 定位
  源 → 预计算真名重写文本 → 组装 figure-patch → 走同一条门禁。默认 dry-run，
  `--apply` 执行。
- **前端修正（走查发现）**：`workbench.js` 的 `richInline` 渲染题干 Markdown 图片
  时，裸逻辑路径会按相对当前页面解析而打不到 figures 路由。现把裸路径解析为
  `/api/w/{ws}/figures/{path}`（已指向 figures 路由或 /static 的引用原样保留）。
  设计里"网页端零改动"的预期被走查推翻——这正是走查的价值。

## 真机迁移与走查

- `lesson-kit ingest lesson-kit migrate-figures --apply`：batch-001，
  6 题 / 6 图落盘为真名，旧引用清零（迁移前全池备份在 `pool/backups/`）。
- 浏览器走查：kp-017 综合题练习流翻到 prob-218，**教材原图（图 6.5）在题干内
  真实渲染**（src 重写为 figures 路由，naturalWidth=106 确认字节解码）。
- 图路由验证：存在 200 `image/jpeg`，缺失 404。

## 文档

- knowledge-figures spec：命名规则改为内容哈希；新增「Gated figure patch
  channel」「Legacy source-image migration」两条需求。
- GLOSSARY 新增「附图 / Figure」条目；PRODUCT-MANUAL §6.1 补题干附图说明；
  ACTION-GRAPH L2 ingest 行更新（八子链）。
- 范围：v1 只支持题目；KP 附图（列已存在）延后——KP body 编辑权归属知识点页，
  避免两条写路径纠缠。
