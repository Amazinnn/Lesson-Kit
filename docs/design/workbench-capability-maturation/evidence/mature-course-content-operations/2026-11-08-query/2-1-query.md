# WP02 2.1 知识点组合查询（DATA-01）

任务原文：> 修改 data.content 查询和 installed CLI 筛选：type/章/文字组合，经验与来源检索，基础投影及关联题目去重。F2 100次查询验证 DATA-01。

## 实现（最小改动，复用现有）

`workbench/data/content.py`：

| 函数 | 行为 |
|---|---|
| `knowledge_query(pool, *, types=(), chapter=None, text=None)` | 按**现有** `knowledge_type` 值与章节收窄；文字匹配 `knowledge_item`、`graph_label`、`body`、`source_location` 与 `kp_experiences.content`；多关键词 AND（复用 `facets.keyword_words`/`matches_all`） |
| `related_problems(pool, kp_ids)` | 命中**任一**关联知识点即返回；按题目身份去重；归档题不返回（复用 `list_items` 的 `deleted_at` 过滤） |

CLI（`workbench/cli/main.py`、`docs/action-graph/L2-interfaces.md` 已同步）：

```
lesson-kit data <ws> search kp "<text>" [--knowledge-type T]... [--chapter chNN] --json
lesson-kit data <ws> related problem <kp-id>[,<kp-id>...] --json
```

无 `--knowledge-type`/`--chapter` 时 `search kp` 仍走原 `content.search`，不改变既有行为。

## 用例

`tests/workbench/test_content_queries.py`（7 passed）：

- 关键词只在经验里出现 → 找到且只找一次；
- type/章/文字组合收窄；
- 基础投影带内容与分类（`knowledge_type` 非空）；
- 两个关联知识点同时命中 → 题目只出现一次；
- 归档题不返回；
- 两条 CLI 用例（组合筛选、related 去重）。

## DATA-01 计时（`data-01-query-timing.json`）

夹具：512 知识点（4 种真实 `knowledge_type`，8 章）+ 2,024 题；预热后 **100 次** `knowledge_query`，随机 type+chapter+关键字组合：

| 指标 | 值 | 门槛 |
|---|---|---|
| query p50 | 0.0015s | — |
| **query p95** | **0.0022s** | ≤ 1s ✅ |
| query max | 0.0033s | — |
| related（25 次）p95 | 0.0161s | — |

匹配正确性另行抽查：纯文字 50 命中、type+文字 25、chapter+type 12、仅来源出处 `R7` 1。

## 边界

- 章节目前由 `kp_id` 的 `chNN` token 判定；独立章节归属是 WP02 2.3（`ensure_*` 迁移）才引入的列，届时该过滤改读列。
- 查询是内存全表扫描 + 过滤（512 点量级 p95 2ms）。真实课程池更大时若超门槛，再考虑 SQL 侧筛选；暂不预优化。
