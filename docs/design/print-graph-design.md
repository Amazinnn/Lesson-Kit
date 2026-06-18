# lesson-kit Print 功能设计（Pool → Obsidian 知识图谱）

**Date:** 2026-06-18
**Status:** 设计完成
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）、[pipeline-create-design.md](./pipeline-create-design.md)（Pipeline 目录约定）

## 定位

Print 是 Pipeline 系统的 **Read** 操作——将 SQLite 池子里的结构化 KP 数据导出为 Obsidian 可读的 Markdown 知识网络。

| | query-pool.py | print-graph.py |
|------|------|------|
| 职责 | 供 Agent 查询（JSON） | 供人阅读和 Obsidian 图谱（Markdown） |
| 消费者 | views/ → Agent | 学生/Obsidian |
| 输出 | stdout JSON | 文件夹 + .md 文件 |

## 脚本接口

```bash
python pool/scripts/print-graph.py --db pool/dld.db --course dld --out "知识笔记/数字逻辑设计/graph/"
```

参数：
- `--db`：SQLite 数据库路径（整本教材库）
- `--course`：课程缩写（用于过滤 kp_id 前缀，如 `dld`）
- `--chapter`：可选——仅导出指定章节（如 `ch02`）。省略则导出全部章节
- `--out`：输出目录（建议为 Obsidian vault 下的知识笔记目录）

## 输出结构

```
知识笔记/{课程}/graph/
├── INDEX.md                     ← 课程级 MOC：章列表 + 每章 KP 数量
├── {chapter}.md                 ← 一章一个文件：KP 索引 + 详情
├── {chapter}.md                 ← ...
└── ...
```

## 章文件格式

面向读者的简洁版面，隐藏所有内部字段。

```
# 第X章 章名

## 本章脉络
[through-line 简述——脚本从池子数据推导：列出 fragmented KP 的共同特征、主要知识类型分布]

## KP 索引
### 第N节 节标题
- [布尔代数基本定理](#dld-ch02-kp-001)
- [德摩根定理](#dld-ch02-kp-002)
- ...

---

## 第N节 节标题

### 布尔代数基本定理

**学习动作：** 区分单变量定理与多变量定理的适用范围，能在化简中识别正确的应用条件。

**关联知识点：**
- [[dld-ch02-kp-002]] — 两条定理的不同形式容易搞混——德摩根要求同时取反所有变量
- [[dld-ch02-kp-008]]
- [[dld-ch04-kp-003]]

---

### 德摩根定理

...
```

### 字段展示规则

| Pool 字段 | 展示？ | 展示形式 |
|-----------|--------|---------|
| `knowledge_item` | ✅ | 三级标题 `### {knowledge_item}` |
| `learning_action` | ✅ | `**学习动作：** {learning_action}` |
| `related_kp_ids` | ✅ | `- [[{kp_id}]]` 列表。fragile=1 的关联加一句提醒 |
| `fragile` | ❌ 隐藏 | 融入关联链接描述中——fragile=1 的关联自动生成提醒语句 |
| `kp_id` | ❌ 隐藏 | 仅作为 `[[链接]]` 目标存在，不单独展示 |
| `knowledge_type` | ❌ 隐藏 | 内部字段 |
| `importance` | ❌ 隐藏 | 内部字段 |
| `difficulty` | ❌ 隐藏 | 内部字段 |
| `source_location` | ❌ 隐藏 | 内部字段 |
| `created_at` / `updated_at` | ❌ 隐藏 | 内部字段 |

### fragile 融入规则

从 SQLite 查询时，脚本对每个关联做判断：
```python
for related_id in related_kp_ids:
    if is_fragile(related_id):  # 查 related KP 的 fragile 字段
        fragile_hint = generate_hint(related_id)  # 从 learning_action 提取关键差异
        print(f"- [[{related_id}]] — {fragile_hint}")
    else:
        print(f"- [[{related_id}]]")
```

不显式标注"⚠️ 易错"——hint 语句本身就是提醒。

### KP 索引

文件顶部放置快速导航部分——每节一个 KP 列表，锚点链接到后文的详情段落。Obisidian 图谱不依赖这部分，但人在阅读和快速跳转时有用。

## INDEX.md 格式

```markdown
# 数字逻辑设计 — 知识图谱

## 章节

| 章节 | KP 数量 | 链接 |
|------|--------|------|
| 第1章 数字系统与信息 | 12 | [[ch01]] |
| 第2章 组合逻辑电路 | 28 | [[ch02]] |
| 第3章 时序逻辑电路 | — | — |
```

## 脚本实现

`pool/scripts/print-graph.py`

- 仅用 Python stdlib（sqlite3, argparse, os, pathlib）
- 读 knowledge_points 表
- related_kp_ids 从 JSON TEXT 解析
- source_location 解析节号（用于排序和分组）
- fragile 查询：对每个 related_kp_id 查对应 KP 的 fragile 和 learning_action
- 输出 UTF-8 Markdown 文件

## 与 Obsidian 的集成

- 文件夹 知识笔记/{课程}/graph/ 被 Obsidian vault 识别
- `[[kp_id]]` wiki links 自动形成图谱节点
- 即使节点文件不存在（章文件用 `###` 标题而不是独立文件），Obsidian 仍识别链接关系
- 未来如需细分：在 INDEX.md 生成时支持 `--individual` 模式（每个 KP 独立文件）

## 后续

- 实现 print-graph.py
- 和 pipeline 的 Populate 联动——入库后自动 print
- across-course 交叉链接（如 dld-ch04-kp-003 被 dld-ch02-kp-001 引用——跨章链接）
