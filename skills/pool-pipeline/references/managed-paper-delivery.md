# 正式入库与保存试卷的交付检查

## 先确认交付物

| 用户要什么 | 完成证据 |
|---|---|
| 新题进入题库 | 正式工作区读回全部目标题号，核对题面、答案、出处及入库批次 |
| 保存成页面可见的试卷 | 题目已入库，再取得保存回执，并读回同一工作区的试卷核对数量、顺序 |
| 导出/打印 | 实际生成所要求的学生卷、答案卷；说明这是文件，不宣称已加入组卷列表 |
| 评级卡/评审包 | 指定材料完整；未 apply 的评级不能宣称已评级，也不自动代表存在一份试卷 |

已有题组卷只做选题和保存。新题组卷依次做内容校验/正式入库、取得正式题号、用这些题号保存试卷。只有用户要求的各项交付都核验后才报告完成。

## 命令与正式库定位

先用 `lesson-kit ls --json` 核实注册工作区名称、根目录、数据库和课程，执行 `lesson-kit pull --help`、`lesson-kit papers --help` 核实本机能力。`cd` 不会把已注册工作区改成临时副本；对副本验收必须沿用现有隔离注册流程，且不能把副本的成功算作正式库成功。

新内容沿用现有受治理写通道，不直接 SQL 写库。支持新入口的版本可用：

```bash
lesson-kit ingest "<工作区名>" bundle --help
lesson-kit ingest "<工作区名>" bundle --input bundle.json
lesson-kit ingest "<工作区名>" bundle --input bundle.json --apply
```

上面的 `bundle` 不带 `--apply` 才是真实只读 check；不要与旧 `ingest recipe` 的无 apply 空跑混淆。旧版若没有该入口，使用它已支持的受治理通道，不猜参数、不改产品代码、不以临时库或直接写 SQL 代替。内接教师对话仍遵守自己的 content-bundle 动作契约，不因本 skill 获得额外写入权限。

每条命令单独执行、检查真实退出码和返回的 `ok` / `error`。Apply 后用正式题号读回核验，不只相信“已提交”或批次文件存在：

```bash
lesson-kit data "<工作区名>" get problem <正式题号>
```

## 保存已有题号构成的试卷

输入必须是 FILE_CONTRACT 定义的 `practice-set` 清单，不能把评级卡 JSON、content-bundle 或 `practice-set-selection` 原样交给保存命令。清单示例（题号替换成正式入库后实际取得的题号）：

```json
{
  "kind": "practice-set",
  "title": "本章练习卷",
  "course": "co",
  "request": {},
  "items": [
    {"problem_id": "co-ch02-prob-126", "reason": "manual"},
    {"problem_id": "co-ch02-prob-127", "reason": "manual"}
  ]
}
```

items 逐项保留用户要求的题目和顺序，不重复、不用其他同章题凑数，不把本地临时 key 当正式 ID。非 co 课程须替换 course；无效/未知 ID、课程不符应修正原清单，不能悄悄删题。清单/路径含空格时加引号。

```bash
lesson-kit pull "<工作区名>" --input "plan.json" --check
lesson-kit papers "<工作区名>" save --input "plan.json"
```

保存写的是 `.lessonkit/practice-sets/ps-NNN.json`，不是题目、作答或难度的 SQLite 写入。成功应有退出码 0 和包含 `practice_set_id`、`title`、`count`、`url` 的 JSON 回执；随后在返回的组卷页面展开对应试卷，或用现有只读列表 API 核对记录内的题号、数量和顺序。读回的对象必须与回执编号相同。

`pull --plan`、`--print` 和新 bundle 的 selection/Markdown 输出都不调用 managed-save。只生成它们时，要报告“已导出，尚未保存为页面试卷”。保存失败时保留原题和清单，报告具体未完成项；不得把文件路径当成功回执。

## 重试与排障

- 保存命令每次成功调用都会新建一份试卷，没有自动去重。若响应丢失或上轮声称成功，先按已知编号或标题加有序题号检查现有记录，再决定是否重试。
- 页面看不到卷子：先查同一正式工作区的题号是否存在，再查已保存试卷记录。题目齐全但缺试卷时只补保存；不要重跑入库、覆盖正式库或用旧验收副本替换它。
- 评级卡/评审包只是中间工件。题目已入库但难度为空，应报告“已入库、尚未评级”；这与试卷是否保存是两件独立事项。
- 给单题判定/评级 agent 的任务仍只包含必要数据与输出 schema；由负责正式提交和交付的主 agent 执行这些检查，不让每个判题 agent 重读产品实现。

最终回报分别列明：正式新增/复用题数和批次、试卷编号/标题/题数/链接、导出文件，以及用户要求中尚未完成的评级或其他事项。不把“题目已入库”与“试卷已保存”混成一句“入库完成”。
