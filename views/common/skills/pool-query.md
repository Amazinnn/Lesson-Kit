# Pool Query Skill

## 一句话定位
从 SQLite 知识池查询指定章节的全部 KP、题目和学习进度，输出结构化 JSON 供后续 Agent 渲染步骤使用。

## 使用时机
- 工作流步骤 2（01_inputs 层）：查 kp_progress 做推荐配置
- 工作流步骤 5（02_analysis 层）：查询章节全部数据
- 需要验证池子完整性时
- 其他视图（习题集等）查询池子时同样使用此 Skill

## 操作指南

### 1. 执行查询脚本

```bash
python pool/scripts/query-pool.py --db pool/{course}-{ch}.db --chapter {ch} --view {view-name}
```

参数说明：
- `--db`：SQLite 数据库文件路径（如 `pool/dld-ch02.db`）
- `--chapter`：章节标识符（对应 `kp_id` 前缀，如 `dld-ch02`）
- `--view`：视图类型（`first-pass` | `problem-set` | 未来扩展）

脚本将 JSON 输出到 stdout。Agent 应将其重定向保存为中间文件：

```bash
python pool/scripts/query-pool.py --db pool/dld-ch02.db --chapter dld-ch02 --view first-pass \
  > intermediate/dld-ch02/first-pass/02_analysis/kp-query-result.json
```

### 2. 输出 JSON 结构

```json
{
  "kps": [
    {
      "kp_id": "dld-ch02-kp-001",
      "knowledge_item": "布尔代数基本定理",
      "source_location": "Section 2-3, pp. 45-47",
      "knowledge_type": "concept-property",
      "importance": "core",
      "difficulty": 2,
      "fragile": 0,
      "learning_action": "区分单变量定理与多变量定理的适用范围",
      "related_kp_ids": ["dld-ch02-kp-002", "dld-ch02-kp-008"]
    }
  ],
  "questions": [
    {
      "q_id": "dld-ch02-q-001",
      "question_text": "某电路需要同时满足 A=1 且 B=0 时输出为 1…",
      "answer_key": "B",
      "answer_explanation": "与运算要求所有输入同时为 1，或运算只需任一输入为 1。",
      "kp_id": "dld-ch02-kp-001",
      "difficulty": 1
    }
  ],
  "progress": {
    "kp_states": {
      "dld-ch02-kp-001": "new",
      "dld-ch02-kp-003": "confused"
    },
    "question_states": {}
  }
}
```

### 3. Agent 后续任务

收到 JSON 后，按以下步骤处理：

1. **保存原始 JSON** — 完整保留到 `02_analysis/kp-query-result.json`，不做任何修改
2. **解析 kps 数组** — 构建章节 KP 清单。按 `source_location` 排序以保持源顺序
3. **检查 progress.kp_states** — 标记 `confused` 和 `faded` 状态的 KP（需额外关注），`stable` 状态 KP（可轻量处理），`new` 状态 KP（标准处理）
4. **解析 questions 数组** — 将已有题目按 `kp_id` 分配到对应 KP。如果 config 要求 MCQ 而某 KP 无题，Agent 需加载 `scene-judgment-mcq` skill 自行设计
5. **检查 related_kp_ids** — 确认关系链完整，为 through-line 选择提供输入。孤立 KP（无关联）标记在分析中

### 4. 进度数据的使用

进度数据影响视图生成的方式取决于视图类型：

| 视图 | confused KP | stable KP | new KP |
|------|------------|-----------|--------|
| 速览 | quick_absorption 加一句提示（如"⚠ 这部分之前有混淆，注意区分 X 和 Y"） | 标准处理 | 标准处理 |
| 习题集 | 对应题目优先出现，可加变体 | 对应题目可减少 | 标准处理 |

⚠ 个性化是 Agent 的渲染决策，不是数据层的强制规则。Agent 根据教育判断决定如何使用进度数据。

## 数据库 Schema 参考

```sql
-- knowledge_points
CREATE TABLE knowledge_points (
    kp_id TEXT PRIMARY KEY,
    knowledge_item TEXT NOT NULL,
    source_location TEXT,
    knowledge_type TEXT NOT NULL,
    related_kp_ids TEXT,  -- JSON array
    importance TEXT NOT NULL,
    learning_action TEXT,
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    fragile INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- questions
CREATE TABLE questions (
    q_id TEXT PRIMARY KEY,
    question_text TEXT NOT NULL,
    answer_key TEXT NOT NULL,
    answer_explanation TEXT,
    kp_id TEXT NOT NULL REFERENCES knowledge_points(kp_id),
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5)
);

-- kp_progress
CREATE TABLE kp_progress (
    kp_id TEXT PRIMARY KEY REFERENCES knowledge_points(kp_id),
    mastery_state TEXT NOT NULL DEFAULT 'new',
    self_assessment TEXT
);

-- question_progress
CREATE TABLE question_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id TEXT NOT NULL REFERENCES questions(q_id),
    note TEXT NOT NULL,
    mastery_state TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## 错误处理

| 错误 | 原因 | 处理方式 |
|------|------|---------|
| `FileNotFoundError` | `--db` 路径不存在 | 提示：SQLite 文件必须由抽取管线先创建。池子必须先于视图存在 |
| `no such table: knowledge_points` | 表未创建 | 确认 pipeline 已执行建表脚本 |
| 查询返回空 `kps[]` | chapter 参数错误或该章节无数据 | 执行 `SELECT DISTINCT substr(kp_id, 1, 8) FROM knowledge_points` 查看已有章节前缀 |
| `progress` 为空对象 `{}` | progress 表为空或不存在 | **正常情况** — 学生尚未开始学习。Agent 将所有 KP 视为 `new`，流程继续 |
| `json.decoder.JSONDecodeError` | `related_kp_ids` 字段损坏 | 检查对应 KP 的 `related_kp_ids` 值，应为合法 JSON array 或 NULL |

## 跨视图使用

此 Skill 被所有视图共用。不同视图通过 `--view` 参数区分：

| --view 值 | 查询侧重 |
|-----------|---------|
| `first-pass` | KP 为主，题目为辅（仅场景判断 MCQ） |
| `problem-set` | 题目为主，KP 为背景（所有题型） |
| 未来视图 | 按需扩展 SQL 逻辑 |
