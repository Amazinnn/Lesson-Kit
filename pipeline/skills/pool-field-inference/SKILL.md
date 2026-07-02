# Skill: Pool Field Inference

三个 SQLite 独有字段（`importance` / `difficulty` / `fragile`）在 V17 中没有等价物。Agent 在生成 `pool-insert-manifest.json` 时需要从源材料关系分析中**推断**这些字段。

本 skill 定义推断规则和默认行为。

## 何时加载

在抽取管线第 6 步（生成 `pool-insert-manifest.json`）加载，用于将 `02_analysis/knowledge-points.md` 翻译为 manifest JSON。

## 字段推断规则

### 1. `importance` ∈ {core, supplementary, optional}

**判断依据（按优先级）**：

1. **源材料处理**（最权威）
   - 出现在章首「学习目标」/「本章要点」中 → `core`
   - 标有「*」「选读」「拓展」字样 → `optional`
   - 例题、习题衍生 KP → `supplementary`
   - 默认 → `supplementary`

2. **结构位置**（次权威）
   - 章首前 1/3 → `core` 概率高
   - 章末 1/3 → `optional` 概率高
   - 中段 → 看依赖数

3. **被依赖数**（补充）
   - `related_kp_ids` 中**被反向引用** ≥3 次 → `core`
   - 反向引用 = 其他 KP 的 `related_kp_ids` 含此 KP
   - 0 次反向引用 → `supplementary` 或 `optional`

**冲突时如何决策**：源材料标记 > 依赖分析 > 位置。源材料说「选读」就 `optional`，不论被多少其他 KP 引用。

### 2. `difficulty` ∈ {1, 2, 3, 4, 5}

**判断依据（按 knowledge_type + 复杂度）**：

| knowledge_type | 默认 difficulty |
|---|---|
| `concept-property`（记忆型） | 1-2 |
| `formula-calculation`（公式） | 2-3 |
| `method-modeling`（建模方法） | 3 |
| `algorithm-process`（算法流程） | 3-4 |
| `code-implementation`（代码实现） | 3-4 |
| `system-timing`（时序/系统） | 4 |
| `lab-implementation`（实验/操作） | 3-4 |
| `memory-recall`（纯记忆） | 1 |

**复杂度调整**：

- 在 `related_kp_ids` 中作为被依赖的前置 KP → +1（更难，因为后续 KP 都依赖它）
- 含「证明」「推导」「分析」「综合」字样 → +1
- 跨章节综合 → 5

**默认**：无法推断时填 `2`（"有条件的直接应用"），并在 `metadata.field_inference_notes.difficulty` 记录「默认 fallback」。

### 3. `fragile` ∈ {0, 1}

**判断依据**：

1. `related_kp_ids` 分析中存在以下关系 → 1
   - `contrast`（对照/反例）
   - `analogy`（类比易混）
   - `opposite`（对立）

2. 学科已知常见混淆对 → 1
   - 例如 DLD：setup time vs hold time、阻塞赋值 vs 非阻塞赋值

3. 源材料主动标注「易混淆」「注意区别」→ 1

4. 知识陈述含「类似」「相似」字样 + 不同细节 → 1

**默认**：无法判断时填 `0`。**宁缺毋滥**——false positive（误标易错）会污染场景判断 MCQ 的提示语，false negative 只是少一个提醒。

## 输出形式

在 `pool-insert-manifest.json` 中，这三个字段已经填在每个 KP 对象里。本 skill 不在 manifest 中再产生额外字段，但**建议**在 `metadata.field_inference_notes` 中记录：

```json
{
  "metadata": {
    "field_inference_notes": {
      "importance": "全部按源材料'本章要点'列表判断",
      "difficulty": "12 个 KP 用默认 2 fallback, 16 个按 knowledge_type 推断",
      "fragile": "未做 false-positive 控制, 待 validate-pool 检查"
    }
  }
}
```

## 跟 validate-pool.py 的关系

- `schema-conformance` gate 验证枚举值合法性
- `difficulty-range` gate 验证 1-5 范围
- 没有专门的「importance 合理性」或「fragile 准确性」gate——这些是软质量，由 Agent 后续用 Update 修