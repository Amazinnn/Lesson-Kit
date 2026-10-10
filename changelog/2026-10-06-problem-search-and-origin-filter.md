# 搜索与来源维度升级

**日期：** 2026-10-06

## 变化

- 搜索从「一个 haystack 一次子串」拆成**两个关键词域**：`GET /search/problems` 收
  `stem` 与 `source`；题干域 = 标题 + 题面，来源域 = 来源证据 + 考查年份 +
  题面开头的 `【…】` 标签段（老池把卷面身份只写在那里）。
- 每个域按**空格切多个词、每个词都必须在本域文字里出现**（域内 AND）；两个域都写则跨域
  AND。两边都没有词返回空集，**不是列出全池**。
- 两个域的定义**全仓库只有一份**（`workbench/domain/facets.stem_text` / `source_text`），
  搜索端点与选题引擎都读它——一道题不可能搜得到却筛不出来。
- `origin_kind` 由单值升为**第四个筛选维度**：`/pull-facets` 返回 `origin_kinds`；
  `pull.select(origin_kinds=…)` 任一命中；`POST /pull` 收 `filters.origin_kinds` 与顶层
  `origin_kinds`。
- 练习页来源筛选浮窗：多一组「历年原题 / 改编 / AI生成」；一个搜索框换成**「题干关键词」
  与「来源关键词」两个框**；结果行先给题面摘要、下面给来源；存储键升为
  `wb_practice_filters_v2_<ws>`。
- `lesson-kit pull`：`--origin-kind` → 可重复的 `--origin-kinds`，新增 `--search-stem` 与
  `--search-source`；`lesson-kit data search` 的查询改多词 AND。

## 边界

- **零兼容**：旧 `?q=` 参数、单值 `origin_kind`、旧浮窗存储键一律**删除，不映射不迁移**。
  `?q=` 映射到 `stem` 会悄悄改变命中的含义；旧存储键里的状态点一次就能重建。
- 不写池、不改池 schema；`origin_kinds` 读的是每行本来就有的列。
- 不做迁移：筛选状态升级后需要重新勾选一次，这是明确接受的代价。
- 练习页难度筛选控件仍未做（`docs/REQUIREMENTS.md` 保持「明确不做」）。
- 未重启 3081 daemon（由主会话负责）。
