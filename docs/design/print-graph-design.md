# lesson-kit 知识导览视图设计（Pool → 叙述型 Markdown 提纲）

**Date:** 2026-07-02（修订）
**Status:** MVP 设计收敛
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）、[pipeline-create-design.md](./pipeline-create-design.md)（Pipeline 目录约定）

## 定位

知识导览视图是 lesson-kit 当前第一视图。`pool/scripts/print-graph.py` 将 SQLite 池子里的 KP 数据导出为学生可直接阅读的 Markdown 知识提纲，供 Obsidian 浏览器消费。

**核心原则：脚本只做机械搬移。** 不推导、不生成、不抽取语义。每个字符都来自 SQLite 已有字段。

## 文档结构（叙述型）

```markdown
# 数字逻辑设计 — ch02

#### §2-3 布尔代数基本定理

**布尔代数基本定理** [[dld-ch02-kp-001]] 由亨廷顿在 1904 年给出公理化定义，包含 0/1 两个值、五条公理（交换律、结合律、分配律、0-1律、补元律）。由公理可推导出 23 条基本定理，包括交换律对偶、分配律展开、吸收律、德摩根律等。这些定理是数字电路设计的代数基础。

**德摩根定理** [[dld-ch02-kp-002]] 两条形式：(AB)' = A' + B' 和 (A+B)' = A'B'。必须同时取反所有变量，且「与」「或」互换。

两条形式容易混淆——必须同时取反所有变量，且「与」「或」互换。

[[dld-ch02-kp-001]]

#### §2-5 卡诺图化简

**卡诺图化简** [[dld-ch02-kp-003]] 是布尔函数化简的几何工具。原则：圈尽可能大的相邻 1 块（2、4、8 个相邻单元），每个 1 必须被至少一个圈覆盖，圈可以重叠。变量数为 2-4 时手工有效，5+ 变量时使用 Quine-McCluskey 算法。

[[dld-ch02-kp-001]] [[dld-ch02-kp-002]] [[dld-ch02-kp-008]]
```

## 标题层级标准

| 层级 | 用途 |
|---|---|
| `#` H1 | 章标识（每章 1 次） |
| `####` H4 | 节组（按 source_location 分组，跳过 H2/H3 表达「叶节点」） |
| `**name**` 粗体 | 知识点名（段首） |

**为何跳过 H2/H3**：节组是「具体知识点单位」，没有进一步嵌套子节。H4 直接表达这种「叶节点」地位。H2/H3 留给未来全文框架（不在 MVP 范围）。

## 节点结构（每 KP 占一段）

```
**{name}** [[{self-kp-id}]] {body}

[如 fragile 非 NULL，独立一段：]{fragile}

[[{related-kp-id-1}]] [[{related-kp-id-2}]] ...
```

- **段首**：`**name** [[self-kp-id]]` —— 主 KP 自指
- **段中**：body 正文（可含加粗、引用、列表等任意 Markdown）
- **段末**：关联 wiki links（不显眼、不换行）
- **脆弱点**：独立一段，紧跟正文段后

## 显示 vs 隐藏

| 字段 | 显示 |
|---|---|
| `knowledge_item` | ✅ 粗体 |
| `body` | ✅ 正文 |
| `fragile` (TEXT) | ✅ 独立一段（如非 NULL） |
| `kp_id` (自身) | ✅ 段首自指 |
| `kp_id` (关联) | ✅ 段末 wiki links |
| `learning_action` | ❌ 不显示（学生已经在学习，Agent 元注释） |
| `importance` | ❌ 不显示（内部字段） |
| `difficulty` | ❌ 不显示（内部字段） |
| `knowledge_type` | ❌ 不显示（内部字段） |
| `source_location` | ❌ 不显示（仅用于节分组） |
| `created_at/updated_at` | ❌ 不显示 |
| 「KP 索引」「KP 详情」标签 | ❌ 不显示（元结构） |

## 解析规约（脚本可解析）

每个 KP 节点必须满足：

1. 占**一段**（段间空行）
2. 段首正则：`^\*\*.+?\*\*\s*\[\[(?P<self_id>{course}-ch\d{2}-kp-\d{3})\]\]`
3. 段末正则（如有）：`\[\[(?P<rel_id>{course}-ch\d{2}-kp-\d{3})\]\](\s+\[\[(?P<rel_id2>{course}-ch\d{2}-kp-\d{3})\]\])*\s*$`
4. wiki link 必须是 kp_id 格式 `[[{course}-ch{NN}-kp-{NNN}]]`

**为何这套约束保证可解析**：
- 段首 `**...**` 粗体短语 + kp_id 在第一行，定位 KP 节点稳定
- wiki link 格式严格（`{course}-ch{NN}-kp-{NNN}` 三个组件都是固定模式），可精确正则匹配
- body 和 fragile 内的 `**加粗**`、`[[wiki]]` 等允许出现——但**主 KP 自指的 kp_id 仅出现一次**（段首），不会误匹配
- 关联 link 在段末单行内聚集，单独的 wiki link 段落不会与 KP 节点混淆

**未来非 LLM 修改脚本示例**（伪代码）：
```python
para_re = re.compile(
    r"^\*\*(?P<name>.+?)\*\*\s*\[\[(?P<self_id>...)\]\]\s*(?P<body>.*?)(?:\n\n|\Z)",
    re.DOTALL
)
link_re = re.compile(r"\[\[(?P<kp_id>{course}-ch\d{{2}}-kp-\d{{3}})\]\]")
for para in markdown.split("\n\n"):
    m = para_re.match(para)
    if m:
        kp_id = m["self_id"]
        related = link_re.findall(para.replace(f"[[{m['self_id']}]]", ""))
        # ... update SQLite
```

## 数据库字段

### fragile: TEXT (NOT INTEGER)

```sql
fragile TEXT  -- NULL = 不脆弱；非 NULL = Markdown 格式的脆弱描述
```

- NULL：KP 不是脆弱点，print 不渲染
- 非 NULL：Markdown 文本（单行或多行），紧跟正文段后作为独立段落

**绝对不**接受 INTEGER 0/1。

### body: TEXT

```sql
body TEXT  -- KP 正文（定义、推导、例题）。NULL 时 print 输出 *[正文待补充]*
```

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
- `--course` (必填)：课程缩写，用于 kp_id 前缀过滤
- `--chapter` (可选)：仅导出指定章节
- `--course-name` (必填)：课程中文名，用于 H1 标题
- `--out` (必填)：输出目录

## 输出结构

```
{out}/
├── ch02.md
├── ch04.md
└── ...
```

**MVP 不生成 INDEX.md**。课程级 MOC 暂不做。

## MVP 拒绝实现（明示）

- ❌ INDEX.md — 课程级 MOC
- ❌ 「本章脉络」自动生成段
- ❌ 「学习动作」字段
- ❌ 「易错点」任何标志（引用块、标题、emoji、批注）
- ❌ 「关联知识点：」列表（靠段末 wiki links + Obsidian 图谱）
- ❌ 「KP 索引」/「KP 详情」元结构标签
- ❌ 每个 KP 独立文件
- ❌ 跨课程交叉链接高亮

## 后续（不阻塞 MVP）

- INDEX.md 重新启用
- 每个 KP 独立文件（与叙述结构并存，按需）
- across-course 交叉链接高亮
- 「本章脉络」从 SQLite 显式字段读取
- Update / Delete CRUD（基于段首正则解析 KP 节点）

## 学生心理学（设计动机）

为什么不做这些「该有的」结构？

- **不要「KP 索引」/「KP 详情」**：学生拿到提纲想直接读，不是先看一份目录。Obsidian 自身的 outline 面板已经能做这件事
- **不要「学习动作」**：元注释，告诉 Agent「应该怎么学」。学生已经在学了，看到「区分两条定理的不同形式」这种话会觉得被指挥
- **不要「易错点」标志**：脆弱点跟正文一体最自然。标志（emoji、引用块、标题）反而暗示「这里需要警惕」，破坏了叙述连贯
- **不要独立「关联」列表**：相关性靠叙述里自然表述（"这条定理与德摩根定理互为对偶"），不靠显式列表。Obsidian 双向链接让图谱自动形成
- **段末 wiki links 不显眼**：避免视觉干扰，但保留机器可解析性
- **节组用 H4 而非 H2/H3**：节组是叶节点，没有进一步嵌套。标题层级表达语义而不是装饰
