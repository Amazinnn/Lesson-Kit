# design — land-source-figures

## 实测前提（2026-09-20）

真实池 6 道题嵌 `](images/<hash>.jpg)` 引用；6 个源文件都能在
`intermediate/dmath/extraction/ch06/00_source/images/` 下定位；但**文件名与当前字节
的 sha256 全部不符**（6/6 失配）——抽取时的旧哈希已失真。这决定了：名字必须由
门禁在落图时**按真实字节计算**，manifest 不声明名字。

## 决策一：内容哈希名由门禁派生，manifest 不携带

figure_files 只带 `source_path`；门禁读字节算 `sha256`，名字 =
`<hex>.<小写原扩展名>`（限 jpg/jpeg/png/gif/svg/webp）。内容寻址使去重天然成立
（同内容同名，两题引同一图零成本），"声称哈希"这一失败模式从根上消失。目标文件
已存在时校验其字节哈希一致后复用，不一致按冲突拒收（应对理论碰撞）。

## 决策二：文本与图同批进出门禁（图是题干的附庸）

manifest item = `{owner_type, owner_id, figure_files[], text}`，`text` 是**题干
全文替换**，门禁强制它以标准 Markdown 引用每一张图（`](<logical>)` 或
`](<name>)`）。apply 单事务：备份 → 复制文件 → UPDATE `problem_text` 与
`figure_paths`（旧值并集追加，去重）→ 批次登记。文件复制在 commit 前完成：
commit 失败只会留下无引用的孤儿文件（内容寻址、无害、幂等可重跑），绝不会出现
"行指向缺失文件"的坏图。

## 决策三：不碰 ingest_batch_id，回滚走前值快照

题目行的 `ingest_batch_id` 是其**创建**批次的溯源，figure-patch 只 UPDATE
text/figure_paths、绝不改戳记——否则原批次的回滚语义被破坏。快照在 apply 时把每个
item 的 previous（text、figure_paths 原值）写进 `pool/ingest/<batch>.json`；
`rollback_batch` 对 figure-patch 批次走恢复分支（从快照回写），已落盘的图文件保留
（内容寻址、无引用、无害）。

## 决策四：迁移复用同一条门禁

`migrate-figures` 扫描 `](images/<文件名>)` 引用 → 定位源文件 → **自己预计算真名**
重写文本 → 组装 figure-patch manifest → 走同一 gate/apply。默认 dry-run 只打印
计划与错误；`--apply` 才写。迁移与未来任何落图走同一条纪律通道，没有第二套路。

## 决策五：v1 只支持题目

KP 的 body 编辑权归属知识点页（knowledge-figures spec「Explicit graph content
updates」），figure-patch 若同时改 KP body 会与之纠缠。KP 附图（列已存在）延后
立项。

## 边界说明

- AGENTS.md「禁止哈希」是代码设计纪律（Ponytail 阶梯）；内容哈希**文件名**是
  所有者 2026-09-20 签字的命名决定，不适用该条。
- 网页端零改动预期：`pages._image_replace` 已把 Markdown 图片引用重写到
  `/api/w/{name}/figures/{path}`，走查验证 prob-078 实际显示。
