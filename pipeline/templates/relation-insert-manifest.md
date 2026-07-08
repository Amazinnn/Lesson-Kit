# Template: Relation Insert Manifest

`relation-insert-manifest.json` 是 Course Learning Network 的关系灌库格式。

它只承载已经审计过的低层级知识点关系。BFS 路径、共同邻居、团簇、生成树等图论发现不写入这个 manifest；它们属于按需计算的 Graph Finding。

**位置**：`intermediate/{course}/extraction/{chapter}/02_analysis/relation-insert-manifest.json`

**消费方**：`pipeline/scripts/insert-knowledge-relations.py`

## 完整 Schema

```json
{
  "metadata": {
    "course": "dmath",
    "chapter": "ch06",
    "relationship_analysis_md": "intermediate/dmath/extraction/ch06/02_analysis/knowledge-relationship-analysis.md"
  },
  "relations": [
    {
      "relation_id": "dmath-ch06-rel-001",
      "source_kp_id": "dmath-ch06-kp-001",
      "target_kp_id": "dmath-ch06-kp-009",
      "relation_type": "prerequisite",
      "direction": "directed",
      "strength": "high"
    }
  ]
}
```

## 字段规范

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `relation_id` | string | 推荐 | 缺失时导入脚本生成稳定 ID |
| `source_kp_id` | string | 是 | 关系起点 KP |
| `target_kp_id` | string | 是 | 关系终点 KP |
| `relation_type` | enum | 是 | 见下方核心词表 |
| `direction` | enum | 是 | `directed` 或 `symmetric` |
| `strength` | enum | 是 | `high` / `medium` / `low` |

## 核心关系词表

| relation_type | 含义 |
|---|---|
| `prerequisite` | A 是理解或使用 B 的前置 |
| `part_of` | A 是 B 的组成部分，或 B 是包含 A 的结构 |
| `contrasts` | A 和 B 需要对比、区分或防混淆 |
| `generalizes` | A 推广到 B，或 B 是 A 的推广方向 |
| `variant_of` | A 和 B 是同一知识/题型空间中的变体 |
| `applies_to` | A 应用于 B，或 A 是 B 的使用场景 |

## 方向规范

- `directed`：只表示 `source_kp_id -> target_kp_id`。
- `symmetric`：表示双向关系。导入脚本会按 KP ID 排序后存储，避免双写。

## 审计边界

- 长篇理由保留在 `knowledge-relationship-analysis.md` 等审计文件中。
- 数据库只保留轻量关系字段，供图谱筛选、路径和 Focus Map 使用。
- 算法生成的隐藏关系或路径结果不得进入本 manifest。
