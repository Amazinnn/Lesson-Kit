# Template: Pool Insert Manifest

`pool-insert-manifest.json` 是 Agent ↔ Python 脚本的桥接格式。Agent 产出 JSON，Python 脚本消费灌库。

**位置**：`intermediate/{course}/{pipeline|view}/{chapter}/02_analysis/pool-insert-manifest.json`

**消费方**：`pipeline/scripts/insert-knowledge-points.py`

## 完整 Schema

```json
{
  "metadata": {
    "course": "dld",
    "chapter": "ch02",
    "source_files": ["Logic Computer Design Fundamentals Chapter 2.md"],
    "knowledge_points_md": "intermediate/dld/extraction/ch02/02_analysis/knowledge-points.md",
    "relationship_analysis_md": "intermediate/dld/extraction/ch02/02_analysis/knowledge-relationship-analysis.md",
    "consolidation_analysis_md": "intermediate/dld/extraction/ch02/02_analysis/kp-consolidation-analysis.md",
    "structure_plan_md": "intermediate/dld/extraction/ch02/03_plans/structure-plan.md",
    "field_inference_notes": {
      "importance": "判断依据摘要",
      "difficulty": "fallback 数量及理由",
      "fragile": "判断依据摘要"
    }
  },
  "knowledge_points": [
    {
      "kp_id": "dld-ch02-kp-001",
      "knowledge_item": "布尔代数基本定理",
      "source_location": "Section 2-3, pp. 45-47",
      "knowledge_type": "concept-property",
      "related_kp_ids": ["dld-ch02-kp-002", "dld-ch02-kp-008"],
      "importance": "core",
      "learning_action": "区分单变量定理与多变量定理的适用范围",
      "body": "布尔代数由亨廷顿在 1904 年给出公理化定义，包含 0/1 两个值、五条公理（交换律、结合律、分配律、0-1律、补元律）。由公理可推导出 23 条基本定理，包括交换律对偶、分配律展开、吸收律、德摩根律等。",
      "difficulty": 2,
      "fragile": null
    }
  ]
}
```

## 字段规范

### metadata 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `course` | ✅ | 课程缩写（与 kp_id 前缀一致） |
| `chapter` | ✅ | 章节标识（如 `ch02`，无连字符） |
| `source_files` | ✅ | 源材料文件名列表 |
| `knowledge_points_md` | ✅ | 02_analysis 中 KP 分析文件的相对路径 |
| `relationship_analysis_md` | ⚠️ 推荐 | 关系分析文件路径 |
| `consolidation_analysis_md` | ⚠️ 推荐 | KP 合并分析路径 |
| `structure_plan_md` | ⚠️ 推荐 | 视图渲染用的结构计划 |
| `field_inference_notes` | ⚠️ 推荐 | pool-field-inference skill 推断过程的备注 |

### knowledge_points 数组字段

| 字段 | 类型 | 必填 | 校验 |
|------|------|------|------|
| `kp_id` | string | ✅ | 必须符合 `{course}-{chapter}-kp-{NNN}` 格式 |
| `knowledge_item` | string | ✅ | 非空 |
| `source_location` | string | ❌ | 推荐填，缺失不报错 |
| `knowledge_type` | enum | ✅ | 在合法枚举内（见下） |
| `related_kp_ids` | list<string> | ❌ | 数组，可为空 `[]` |
| `importance` | enum | ✅ | core / supplementary / optional |
| `learning_action` | string | ❌ | 推荐填 |
| `body` | string | ❌ | KP 正文（定义、推导、例题）。缺失时 print-graph 输出 `*[正文待补充]*` |
| `difficulty` | int | ❌ | 1-5，未填或 null 时 insert 脚本填默认 2 |
| `fragile` | string | ❌ | **Markdown 格式的脆弱点描述**。`null` 或缺失 = 不脆弱。非空 = 该 KP 的易错点（多行多段 Markdown） |

### knowledge_type 合法枚举

```
concept-property | method-modeling | formula-calculation |
algorithm-process | code-implementation | system-timing |
lab-implementation | memory-recall
```

### importance 合法枚举

```
core | supplementary | optional
```

## kp_id 命名约定

格式：`{course}-{chapter}-kp-{NNN}`

- `course`：metadata.course 字段一致
- `chapter`：metadata.chapter 一致（如 `ch02`）
- `NNN`：三位数字，从 001 开始，按 KP 在章节内出现的顺序

示例：
- ✅ `dld-ch02-kp-001`
- ❌ `dld-ch2-kp-1`（chapter 必须 `ch` + 零填充数字）
- ❌ `dld-2-kp-001`（chapter 不能省略）

## related_kp_ids 字段

- **本章节内**：直接用完整 kp_id，如 `dld-ch02-kp-005`
- **跨章节**：完整 kp_id，如 `dld-ch04-kp-003`
- **空数组**：填 `[]`，不要省略字段

## 校验失败的常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `kp_id 不符合命名约定` | chapter 没用零填充 | 改成 `ch02` 而非 `ch2` |
| `knowledge_type 不在合法枚举内` | 拼写错误（如 `concept_property`） | 改成连字符 `concept-property` |
| `importance 不在合法枚举内` | 大小写错误或拼写错误 | 严格小写 |
| `difficulty 超出 1-5` | 填了 0 或 6 | 严格 1-5 |
| `fragile 类型错误` | 填了 `true`/`false` 或数字 | 必须是 Markdown 字符串或 `null` |
| `重复的 kp_id` | 两个 KP 用了同一个 id | 重新编号 |

## 章节伴生题不写入 manifest

`pool-insert-manifest.json` **只承载 KP**。场景判断 MCQ 由视图层在渲染时按 `scene-judgment-mcq` skill 临时生成，不入池。

持久化题目使用独立 manifest：`pipeline/templates/problem-insert-manifest.md`。题目统一写入 `problems` 表，并通过 `source_kind` 区分课本、小测、期中、期末等逻辑题池。
