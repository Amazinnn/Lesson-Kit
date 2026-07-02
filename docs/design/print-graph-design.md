# lesson-kit Print 功能设计（Pool → 学生视角知识提纲）

**Date:** 2026-07-02（修订）
**Status:** MVP 设计收敛
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）、[pipeline-create-design.md](./pipeline-create-design.md)（Pipeline 目录约定）

## 定位

Print 是 Pipeline 系统的 **Read** 操作——将 SQLite 池子里的 KP 数据导出为学生可直接阅读的 Markdown 知识提纲，供 Obsidian 浏览器消费。

**核心原则：脚本只做机械搬移。** 不推导、不生成、不抽取语义。每个字符都来自 SQLite 已有字段。

| | query-pool.py | print-graph.py |
|------|------|------|
| 职责 | 供 Agent 查询（JSON） | 供学生阅读（Markdown 知识提纲） |
| 消费者 | views/ → Agent | 学生 / Obsidian |
| 输出 | stdout JSON | 文件夹 + 多个 .md 文件 |
| 智能程度 | 0（透传） | 0（机械格式化） |

## 脚本接口

```bash
python pool/scripts/print-graph.py \
    --db pool/dld.db \
    --course dld \
    [--chapter ch02] \
    --course-name "数字逻辑设计" \
    --out "知识笔记/数字逻辑设计/graph/"
```

参数：
- `--db` (必填)：整本教材 SQLite 库
- `--course` (必填)：课程缩写，用于过滤 kp_id 前缀
- `--chapter` (可选)：仅导出指定章节（如 `ch02`）。省略则导出该课程全部章节
- `--course-name` (必填)：课程中文名，用于章文件标题
- `--out` (必填)：输出目录（建议为 Obsidian vault 下的知识笔记目录）

## 输出结构

```
知识笔记/{课程}/graph/
├── ch02.md
├── ch04.md
└── ...
```

**MVP 不生成 INDEX.md。** 暂不做课程级 MOC。

## 数据库字段与展示映射

每个 KP 是一个有完整正文的有机体，不是只有标题的占位。

| Pool 字段 | 展示？ | 展示形式 |
|---|---|---|
| `knowledge_item` | ✅ | 三级标题 `### {knowledge_item}` |
| `body` | ✅ | 正文段落。缺失时写 `*[正文待补充]*` |
| `fragile` | ✅（条件） | 若 `fragile=1`，标题下方插入 `> ⚠ 易错点` 批注块 |
| `learning_action` | ✅（可选） | `**学习动作：** {learning_action}` |
| `related_kp_ids` | ✅ | `- [[{kp_id}]]` 列表（wiki 链接形式） |
| `kp_id` | ❌ 隐藏 | 仅作为 `[[链接]]` 目标存在 |
| `knowledge_type` | ❌ 隐藏 | 内部字段 |
| `importance` | ❌ 隐藏 | 内部字段 |
| `difficulty` | ❌ 隐藏 | 内部字段 |
| `source_location` | ❌ 隐藏 | 内部字段（**仅用于分组**，不显示） |
| `created_at` / `updated_at` | ❌ 隐藏 | 内部字段 |

## 章文件格式

```markdown
# 数字逻辑设计 — ch02

## KP 索引

### §2-3 布尔代数基本定理
- [布尔代数基本定理](#布尔代数基本定理)
- [德摩根定理](#德摩根定理)

### §2-5 卡诺图化简
- [卡诺图化简](#卡诺图化简)

---

## KP 详情

### 布尔代数基本定理

布尔代数由亨廷顿在 1904 年给出公理化定义，包含 0/1 两个值、五条公理（交换律、结合律、分配律、0-1律、补元律）。由公理可推导出 23 条基本定理，包括交换律对偶、分配律展开、吸收律、德摩根律等。

**学习动作：** 区分单变量定理与多变量定理的适用范围

**关联知识点：**
- [[dld-ch02-kp-002]]
- [[dld-ch02-kp-008]]

### 德摩根定理

> ⚠ 易错点

德摩根律的两条形式：(AB)' = A' + B' 和 (A+B)' = A'B'。两条形式易混淆——必须同时取反所有变量。

**学习动作：** 区分两条定理的不同形式

**关联知识点：**
- [[dld-ch02-kp-001]]

...
```

### KP 索引分组

按 `source_location` 用正则 `§\s*([\w\-]+)` 抽取节号，分组输出。无 `source_location` 的 KP 归到「未分组」。

### 锚点格式

GitHub / Obsidian 兼容：`#知识标题 slug`。`slugify()` 把空格替换为 `-`、去除特殊字符。中文字符保留（Unicode range `一-鿿`）。

### fragile 批注

单独作为批注块（`> ⚠ 易错点`），放在 `###` 标题下、body 上。**不**在 `[[关联]]` 链接后追加提示文案。

学生自己通过 Obsidian 笔记沉淀易错经验，不该由工具代写。

## body 字段要求

`body` 是 KP 的正文（定义、推导、例题），从源材料中提取。**新增 SQLite 列**：

```sql
ALTER TABLE knowledge_points ADD COLUMN body TEXT;
```

- 必填：否
- 默认值：NULL
- 缺失时 print-graph 输出 `*[正文待补充]*`，不报错

Pipeline `insert-knowledge-points.py` 接受 manifest 中的 `body` 字段。manifest template (`pool-insert-manifest.md`) 已更新。

## 脚本实现

`pool/scripts/print-graph.py`

- 仅 Python stdlib（sqlite3, argparse, os, pathlib, json, re, collections）
- 单文件，单函数 main
- 读 knowledge_points 表
- `related_kp_ids` 从 JSON TEXT 解析
- `source_location` 用正则抽 `§X-Y` 分组
- 输出 UTF-8 Markdown 文件

## 与 Obsidian 的集成

- 文件夹被 Obsidian vault 识别
- `[[kp_id]]` wiki links 自动形成图谱节点
- 节点不独立成文件（章文件用 `###` 标题），但 wiki 链接仍能被 Obsidian 解析为图谱边
- 中文锚点通过 slugify 处理，Obsidian 在 Windows / macOS 上都能识别

## MVP 拒绝实现（明示）

- ❌ INDEX.md — 课程级 MOC，用户明确推迟
- ❌ 「本章脉络」自动生成段 — 脚本不做任何语义推导
- ❌ fragile 智能提示文案 — 学生自己的经验不该由工具代写
- ❌ 在 `[[关联]]` 链接后追加 fragile 提示 — fragile 仅作为批注块
- ❌ 每个 KP 独立文件模式（`--individual`）— 后续可选
- ❌ 跨课程交叉链接高亮 — 后续可选

## 后续（不阻塞 MVP）

- INDEX.md 重新启用（用户主动要求时再加）
- across-course 交叉链接高亮
- 每个 KP 独立文件模式
- 「本章脉络」从 SQLite 显式字段（如 `chapter_summary`）读取（如果以后需要）
- 自动按章节顺序对 chXX.md 重命名为「第X章 {中文章名}.md」（需 `--chapter-titles` 参数）