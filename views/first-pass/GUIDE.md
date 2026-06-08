# 速览视图（First-Pass View）

## 视图定位

速览是面向初学者的**源材料导航层**。

它告诉学生：这一章有哪些珍珠、长什么样、在源材料里怎么找到它们。它不是摘要、不是迷你教案、不是考试重点——它是你打开课本之前的那张"寻宝图"。

和 V17 的关键区别：
- **V17**：每次从源材料重新提取 KP → 分析 → 渲染。流程固定，产物一次性。
- **lesson-kit**：KP 和题目已在 SQLite 池子中。每次生成速览时，Agent 从池子查询数据、重新选择贯穿视角（through-line）、重新撰写 quick_absorption、按学生当前状态定制产出。**同样的池子，不同的速览**——首次接触时完整探索，复习时聚焦薄弱点，快速扫读时仅 1 句提示。

## 适用场景

### 何时使用速览

| 场景 | 学生状态 | 速览行为 |
|------|---------|---------|
| 首次接触新章节 | 全部 KP 为 `new` | 全量 KP + 场景判断 MCQ。标准深度。通过贯穿视角建立章节认知框架 |
| 课后快速回顾 | 部分 KP 为 `confused`/`stable` | 全量 KP，但 confused KP 加提示、stable KP 轻量。通过进度数据精准定位 |
| 只想快速扫一遍 | 不在意进度 | Light 深度——每 KP 1 句话。可跳过 MCQ。最低认知负荷 |
| 对某几节不熟 | 特定节 KP 为 `confused` | 优先节全量、其余节 lighter。聚焦薄弱区域 |

### 何时不用速览

- 需要完整的公式推导和例题讲解 → 深度讲解视图（lesson，未来）
- 需要大量练习题训练 → 习题集视图（problem-set，后续）
- 需要模拟考试 → 真题卷视图（exam，未来）
- 章节的 SQLite 池子尚未创建 → 先运行抽取管线（pipeline）

## 设计原理

速览的每一个设计决策都有教育理论支撑：

### 测试效应（Testing Effect）— Roediger & Karpicke
每个 KP 配一道场景判断 MCQ。学生必须主动检索，而非被动阅读。错误的干扰项暴露认知盲区——"我以为我会了"的瞬间就是学习的起点。

**体现在速览中：** 步骤 7 的 question_draft 设计。MCQ 不考定义回忆，考场景判断——需要学生把 KP 放进一个具体情境中判断适用性。

### 认知负荷理论（Cognitive Load Theory）— Sweller
1-3 句 quick_absorption 是刻意设计的上限。不把一切嚼碎喂给学生——嚼碎了反而不消化。学生在源材料中自己发现细节，比被告诉更有效。

**体现在速览中：** quick_absorption 的 120 字上限和 1-3 句限制。不是偷懒，是克制。

### 先行组织者（Advance Organizer）— Ausubel
贯穿视角（through-line）给每一个 KP 提供同一个"挂钩"。学生读到第 5 个 KP 时感觉"啊，又是这个东西"，而不是面对 30 个孤立的定义。

**体现在速览中：** 步骤 6 的 through-line 选择。每个 KP 的 quick_absorption 第二句必须回响这个视角。"逻辑等价变换"不只出现在 KP-008——它出现在每一个相关的 KP 中。

### ICAP 框架（Interactive-Constructive-Active-Passive）— Chi & Wylie
MCQ 将学生从 Passive（阅读）推到 Active（选择/判断）。场景判断进一步推到 Constructive——学生必须在脑中构建"如果我在这个场景中，我该用什么工具"的心智模型。

**体现在速览中：** 场景判断 MCQ 的设计。不是"以下哪个是 X 的定义"（Active 层），而是"在这个场景中你应该用哪个公式/条件"（Constructive 层）。

### 错误驱动学习（Error-Driven Learning）
干扰项不是随机生成的——它们基于 `fragile=1` KP 的常见误解。学生选错不是因为"没记住"，而是因为"一直以为是对的"。错误被触发、被识别、被修正，比顺利答对学得更深。

**体现在速览中：** scene-judgment-mcq skill 中的"每个干扰项必须基于真实常见错误"规则。mcq-quality gate 中的"禁止稻草人选项"检查。

### 个性化与认知状态
通过查询 `kp_progress` 和 `question_progress` 表，速览知道学生对每个 KP 的掌握状态。`confused` KP 获得额外关注，`stable` KP 轻量处理。不是所有学生拿到同一份速览——但差异是教育性的，不是界面性的。

**体现在速览中：** 步骤 2 的进度查询和步骤 7 的配置覆盖规则。

## 文件地图

```
views/first-pass/
├── GUIDE.md                         ← 你在这里
├── command.md                       ← 10 步工作流编排
├── skills/
│   ├── through-line-selection.md    ← 贯穿视角选择
│   ├── quick-absorption-writing.md  ← 知识阐释写作
│   ├── scene-judgment-mcq.md       ← 场景判断 MCQ 设计
│   └── knowledge-framing.md        ← 多角度阐释模式
├── gates/
│   ├── coverage.md                 ← KP 覆盖率检查
│   └── mcq-quality.md             ← MCQ 质量检查
└── templates/
    ├── lesson-template.md          ← 最终 Markdown 骨架
    ├── structure-plan-template.md  ← 渲染计划结构
    └── view-scope-template.md     ← 范围确认 + 学生意图
```

## 相关资源

- `docs/design/view-layer-design.md` — 视图层完整设计文档
- `docs/design/kp-pool-modular-views.md` — SQLite Pool Schema
- `RED_LINES.md` — 核心红线（所有视图必须遵守）
- `STYLE.md` — 写作风格规范
- `.claude/skills/educational-theory/SKILL.md` — 教育理论参考手册
