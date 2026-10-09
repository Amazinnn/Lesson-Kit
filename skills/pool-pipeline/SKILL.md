# pool-pipeline

多份题库/试卷材料 → 一个可练习、可审计、可复跑的 Lesson Kit 题池。

本目录是仓库内维护的 canonical 操作 skill。`references/` 放按需读取的细则与历史证据，`scripts/` 放已经跑通过的机械辅助工具。

## 权威与边界

1. **当前 OpenSpec、实际 `lesson-kit` CLI、当前 SQLite schema 是权威事实**；本 skill 不覆盖产品契约。
2. problem schema、ingest/content CRUD、difficulty、relations、practice experience 或相关 CLI 改动时，同一 PR 必须同步本目录。
3. `KnowledgePoint ↔ Problem` 只有正式的 `problems.kp_ids` 直接关系；不要恢复 `topic_label` 或任何题目分组摘要层。
4. 课程特有策略放在课程工作区自己的 `policy-override.md`；`references/examples/` 只作格式示例，不得跨课程自动套用。
5. 批量修池不自动写“做题经验”；经验是用户拥有的学习总结，只在用户明确要求时通过 `lesson-kit experience` 写入。
6. 本 skill 不修改 Lesson Kit 产品代码。发现产品契约/渲染器/门禁本身有 bug，记录证据并转到 Lesson Kit 开发任务。

## 什么时候用

用：
- 新课程批量建题池；
- 把新找到的多份卷子并进已有池；
- 批量修复题型、选项、题干、知识点绑定、来源、重复、图片等；
- 大规模审计并生成可回滚 patch。

不用：
- 单题小改：直接用 `lesson-kit data ... update problem`；
- 只查统计：直接跑查询/审计；
- 讲义/论文等非题目材料。

## 核心形状：一次全局理解 + 单题判定 + 机械校验

不要让每个 agent 各自回原始素材考据。正确流程：

| 阶段 | 谁做 | 产物 |
|---|---|---|
| ① 全局理解 | 一个主力 agent，不拆 map-reduce | 源清单、课程画像、题目边界/切分规则、课程 override、必要时 sugared 第一版 |
| ② 题卡 | 脚本 | 一题一张自足卡，带来源指针 |
| ③ 判定 | LLM，单题一次调用 | 一行结构化决定；题面坏才输出修复文本 |
| ④ 校验/去重 | 脚本 | preflight、全局去重、例外/删除台账 |
| ⑤ 提交 | CLI + 脚本 | 批量 patch / relation / difficulty；硬证据删除 |

原则：脚本负责**搬运与核对不变量**，不负责语义判断。脚本能列文件、切块、算指纹、统计、校验、记账；它不能可靠判断“哪句是题干、这几块是不是同一道题、答案能否从证据推出”。

材料特别碎时，① 加重：先重建一道题的边界，再进入单题判定。材料本身不可信时，精炼层只当索引，原料层才是证据；不要把上游切分器的计数当事实。

## 现成工具

先读再用，不要重写：

| 工具 | 用途 |
|---|---|
| `scripts/normalize.py` | 统一指纹/骨架/公式归一化；去重、吸收核验、幂等台账必须共用 |
| `scripts/extract_formulas.py` | 从 HTML/MHTML 公式块取单副本，并自检双写损伤 |
| `scripts/anchors.py` | 用骨架在源 Markdown/HTML 表格中定位题目行 |
| `scripts/preflight.py` | 提交前检查答案键、选项、KP 数、标签长度与 markup 等不变量 |
| `scripts/sugar.py` | `emit/check/parse` 文本糖，让理解结果变成机器可检查 IR |
| `scripts/delete_rows.py` | 删除前逐行复验“无学习记录”，支持 dry-run 并留删除台账 |

辅助脚本已用当前 Python 语法编译检查；禁止提交 `__pycache__/` 或 `.pyc`。

## 默认判据

完整规则见 `references/policy-defaults.md`。这里只留硬边界：

- 选项逐字取源，保持顺序；题干中内联选项移入选项字段。
- 答案键只有证据充分才写；选择题写选项**文本**，不是字母；无证据就留空。
- `display_title` 是可读短标题；**没有 `topic_label`**，不要造“选择题补充/某类题目”等分组层。
- `kp_ids` 是题目到知识点的正式关系；判断/小测通常恰好一个，综合题可多个。
- 相似题不等于重复题。自动删除只接受两类硬证据：归一化后完全重复；或碎片内容已经证明被目标题吸收。
- 删除必须先快照/备份、逐条验证没有学习记录，并写台账。
- 脚本扫描出的“可疑”不是结论；缺失/多余/错位类结论至少用第二种独立口径复验。

## 文本糖（推荐 IR）

材料边界不稳定时使用 `references/sugar.md` 的块标记。下游遇到缺糖的候选块应报错而不是猜。

```markdown
<!-- Q id=c02-ch07-prob-020 chapter=ch07 mode=single_choice fp=... -->
来源: source.md#L1472
来源题号: R2-19
考点: 主定理
标题: 不可用主定理求解的递推式
题干: ...
选项:
A. ...
B. ...
答案证据: source.html#L11353 | R2-19 | checked=C + 判分正确
<!-- /Q -->
```

`考点:` 只是中间表示里的描述，用来辅助绑定 `kp_ids`，不是数据库字段或新的 relation layer。

## 查询与筛选：只使用当前真实 CLI

来源过滤：

```bash
lesson-kit pull <ws> --source-kind final --origin-kind source_problem --exam-year 2023
lesson-kit pull <ws> --source-evidence "合集A"
```

当前维度：
- `--source-kind`：可重复；
- `--origin-kind`：单值；
- `--source-group`：单值；
- `--exam-year`：前缀匹配；
- `--source-evidence`：可重复、子串匹配。

当前 CLI **没有** `--search-stem` / `--search-source`。关键词定位用：

```bash
lesson-kit data <ws> search problem "关键词"
```

`data search` 是对整道题 JSON 表示做**单个、大小写不敏感的连续子串**匹配；不会自动把空格拆成多个 AND 词。复合条件用正式 `pull` 维度或对 JSON 输出再做脚本过滤。

新数据优先把来源写进 `source_evidence` / `exam_year`，不要建立依赖题干 `【…】` 前缀的第二套来源结构。

## 难度

```bash
lesson-kit difficulty <workspace> check --input ratings.json
lesson-kit difficulty <workspace> apply --input ratings.json
```

- `check` 零写；`apply` 整批原子写。
- 四维各 1–5：`knowledge_breadth / reasoning_depth / transfer_distance / construction_openness`。
- 不要批量填同一个均值；难度没有区分度等于没有评分。
- 老池若缺 difficulty 列，先：

```bash
python pool/scripts/migrate-progress.py --db <pool>/<course>.db
```

## 关系

批量关系走正式 relation action，不要直接 SQL：

```bash
lesson-kit data <ws> check relation --input relations.json
lesson-kit data <ws> apply relation --input relations.json
```

关系允许字段只有 `source_kp_id / target_kp_id / relation_type / direction / strength`。禁止为了“图看起来更密”自动扫全课程补关系；只写有明确证据的边。

## 做题经验：只响应明确用户意图

做题经验是一知识点一份 learner-owned Markdown，总结可复用的解题经验，不是错题事实、题目元数据或 learner signal。

```bash
lesson-kit experience <ws> get <kp-id>
lesson-kit experience <ws> create <kp-id> --input experience.json
lesson-kit experience <ws> update <kp-id> --expected-revision <N> --input experience.json
lesson-kit experience <ws> delete <kp-id> --expected-revision <N>
```

`experience.json` 只含 `content` 和可选 `problem_ids`。引用题必须已通过 `problems.kp_ids` 正式属于该 KP；标题从题目实时解析，不复制。update/delete 必须使用刚读到的 revision；冲突时重新读、合并，禁止盲覆写。

**批量建库、审计、修池不得顺手生成经验。** 只有用户明确说“把这条记进经验/更新经验”才写。

## 提交前流程

1. 读课程自己的 `policy-override.md`（没有就用默认策略）。
2. 全局审计：源清单、重复率、缺陷占比、题型/答案证据可用率。
3. 若材料边界不稳，先生成并 `scripts/sugar.py check` 第一版。
4. 单题判定；损伤/视觉/跨源冲突才升级。
5. `scripts/preflight.py` + 全库 `normalize.identity` 去重检查。
6. 用正式 Lesson Kit 写通道提交；禁止直接改 DB 绕过校验。
7. 删除走 `scripts/delete_rows.py --dry-run`，核验后再真实删除。
8. 提交后再跑一次重复/内容卫生审计，并对数量做对账。

当前池内容卫生优先用：

```bash
lesson-kit data <ws> audit
# 或针对具体 check
lesson-kit data <ws> audit --check duplicates
```

### 关于 `pipeline/scripts/validate-pool.py`

截至 2026-10-08 复核 current main，它仍要求已退役的 `candidate_problems/candidate_attempts`，且老 ID 正则不识别 `-mq-`。因此**不要把它当现代池验收凭证**。这是冻结 pipeline 的历史兼容问题，不要在课程修池任务里偷偷修产品代码。

## 已知高风险陷阱

详见 `references/traps-2026-10.md`。开工前至少记住：

1. `ingest recipe` 不带 `--apply` 的 rc=0 不是校验通过；`cd` 也不能把注册工作区指向副本。
2. 扫描器不要硬编码 `[A-D]`；缺失/多余结论要二次复验。
3. 副本 DB 文件名若参与 course 推导，仍要保持 `<course>.db` 或显式传 course。
4. `*.recipe.json` 可能是目录；枚举清单前用 `os.path.isfile`。
5. 不要凭页面里 KaTeX 的视觉复制假象修改池；先读真实字段。

## Agent/subagent 纪律

- 全局理解只做一次，不能拆成多个彼此不知道上下文的章级 agent。
- 单题判定一次调用只看一张题卡；失败按题号重放，不重建全局上下文。
- 视觉/残缺升级一批不要塞太多题；一次只回答被问的问题。
- 不让判题 agent 读 Lesson Kit 实现源码；它只需要数据要求和输出 schema。
- 人的注意力只用于课程策略、不可逆动作汇总和抽样审计；机器犹豫的个例默认保留并登记。

## 参考

- `references/policy-defaults.md`：默认题型/答案/去重/KP/图片判据
- `references/examples/physics-ii-policy-override.md`：**仅示例**课程 override 写法
- `references/prompt-t1.md`：单题一次调用模板
- `references/sugar.md`：文本糖规范
- `references/example.md`：真实重建/去重例子
- `references/traps-2026-10.md`：实测陷阱与证据
- `scripts/`：机械工具；先跑自检再改
