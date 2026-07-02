# fragile 字段从标签到文本 — 设计

**Date:** 2026-07-02
**Status:** 设计完成，待实施
**触发:** 用户反馈「fragile 应该是一个 text，而不只是一个标签」

## Context

lesson-kit 把每个 KP 看作一个有完整正文的节点。`fragile` 字段最初是 INTEGER（0/1 标签），输出时 `fragile=1` 显示一个 `> ⚠ 易错点` 固定批注。

但用户认为这不够——`fragile` 应该是**正文的一部分**：学生或教师精心填写的易错描述，包含「哪里易错、为什么、怎么避免」。固定批注无法承载这些信息。

本次重构把 `fragile` 从 INTEGER 标签改为 TEXT 内容。

## 最终决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| 字段类型 | INTEGER → **TEXT** | 承载描述性内容 |
| 默认值 | `0` → **NULL** | 不脆弱 = 无内容 |
| 必填规则 | **必须人工填**，Agent 不能给默认值 | 不确定时填 NULL，不污染池子 |
| 内容格式 | **Markdown**（可多行多段） | 与正文统一渲染 |
| 显示位置 | 标题下批注 → **KP 详情末尾** | 与其他正文段落地位平等 |
| 标题/标志 | `> ⚠ 易错点` → **不加任何标志** | 学生自己体会，工具不做强提示 |
| 多脆弱点 | 单字段 → **单 TEXT 多行表达** | 不引入数组/独立表 |
| 现有 1/0 整数 | **不再接受** | schema 改成 TEXT |

## 数据库 Schema 变更

```sql
-- 旧
fragile INTEGER DEFAULT 0

-- 新
fragile TEXT  -- NULL = 不脆弱；非 NULL = Markdown 格式的脆弱描述
```

`--force` 重建表（破坏性，已有的 0/1 整数会被丢弃——MVP 阶段无现存生产数据，可接受）。

## 字段语义

| 值 | 含义 |
|---|---|
| `NULL` | 该 KP 不是脆弱点。不渲染任何内容 |
| 非空 TEXT | Markdown 格式的脆弱描述（可以是单行、多行、含列表/引用/加粗等） |

## 渲染规则（print-graph.py）

每个 KP 详情的渲染顺序：

1. `<a id="anchor"></a>`
2. `### knowledge_item`
3. `body`（或 `*[正文待补充]*`）
4. `**学习动作：** ...`（如有）
5. `**关联知识点：**` 列表（如有）
6. **fragile 文本**（如有）—— 直接作为 Markdown 段落，无标题无 emoji 无引用块

如果 `fragile` 是 NULL，跳过第 6 步，不留空行。

## 多脆弱点处理

单个 TEXT 字段可承载多个脆弱点，例如：

```markdown
- 容易把 setup time 和 hold time 搞混，前者指数据早于时钟到达的时间，后者指数据晚于时钟到达的时间
- 静态时序分析时容易忽略跨时钟域路径
- 仿真时如果不设时钟约束，结果可能完全错误
```

学生用 Markdown 列表/段落组织多个点。**不**引入 JSON 数组或独立表。

## 实施范围

需要修改 7 个文件 + 1 个 spec：

| 路径 | 动作 |
|---|---|
| `pipeline/scripts/create-tables.py` | 修改：fragile INTEGER → TEXT，无 DEFAULT |
| `pipeline/scripts/insert-knowledge-points.py` | 修改：fragile 接受任意 TEXT，缺失默认 NULL |
| `pipeline/scripts/validate-pool.py` | 修改：fragile 验证不再限制 0/1 |
| `pipeline/templates/pool-insert-manifest.md` | 修改：fragile 字段说明改为 TEXT |
| `pool/scripts/query-pool.py` | 修改：fragile 输出 string 或 null |
| `pool/scripts/print-graph.py` | 修改：删除 `> ⚠ 易错点` 批注，渲染脆弱文本到 KP 详情末尾 |
| `docs/design/print-graph-design.md` | 修改：删除脆弱标签章节，加脆弱文本渲染规则 |
| `docs/design/kp-pool-modular-views.md` | 修改：fragile 字段定义 |

## 验证

```bash
# 1. schema 验证
rm pool/dld.db
python pipeline/scripts/create-tables.py --db pool/dld.db --force
python -c "
import sqlite3
conn = sqlite3.connect('pool/dld.db')
cols = conn.execute('PRAGMA table_info(knowledge_points)').fetchall()
for c in cols:
    if c[1] == 'fragile':
        print(c)
conn.close()
"
# 期望: fragile TEXT, notnull=0, default=None

# 2. 含脆弱文本的 manifest 入库
python pipeline/scripts/insert-knowledge-points.py --db pool/dld.db --manifest <test>

# 3. validate 不报错
python pipeline/scripts/validate-pool.py --db pool/dld.db --chapter ch02 --course dld
# 期望: PASS, 0 errors

# 4. query-pool 输出 fragile 为字符串
python pool/scripts/query-pool.py --db pool/dld.db --chapter dld-ch02 --view first-pass
# 检查 "fragile" 字段是字符串而不是 0/1

# 5. print 输出脆弱文本在 KP 详情末尾
python pool/scripts/print-graph.py --db pool/dld.db --course dld --chapter ch02 \
    --course-name "数字逻辑设计" --out /tmp/test-print/
grep -c "> ⚠" /tmp/test-print/ch02.md  # 期望: 0
grep -c "易错点" /tmp/test-print/ch02.md  # 期望: 仅出现在脆弱文本本身（agent 写的内容）
```

## 不在范围内

- 跨 KP 脆弱文本聚合（一个视图里列所有脆弱点）
- 脆弱文本的版本控制（学生 v1 vs v2 描述）
- Agent 自动建议脆弱点（必须人工填）
- 脆弱文本的多语言版本

## 后续（不阻塞 MVP）

- Update Command：单独修改某个 KP 的 fragile 文本
- 脆弱点的 `last_updated_by` 字段追踪（哪个学生/Agent 写的）