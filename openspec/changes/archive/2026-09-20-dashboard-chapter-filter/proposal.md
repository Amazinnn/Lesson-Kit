# dashboard-chapter-filter 提案

## Why

「整本教材一个 DB，跨章靠 `kp_id` 前缀」是 6 月就定下的池结构
（`pipeline/commands/extract-chapter.md:131`「单库多章」；GLOSSARY「池」条目
把「章节数据库」列为 _Avoid_）。但工作台至今只有一个全局 `active_chapter`
透镜：换章只能跑 CLI（`lesson-kit use`，9-20 刚加），且 hub 卡片口径自相矛盾
——知识点数按当前章、题数与待复习是全池。

所有者即将在一个课程根目录下使用多章内容。需要的是「不要求人类用户记参数」的
章视图：在 dashboard 上就能在「全课程」与「某一章」之间切换，而不是在
`lesson-kit xxxxxx` 之后再加第三个参数。

## What Changes

- Dashboard 顶栏新增**单选章开关**：关闭 = 全课程（不过滤）；开启 = 选定一章。
  切换写注册表 `active_chapter`，与 `lesson-kit use` 是**同一个写口**
  （人面 = 开关，Agent 面 = CLI/注册表）；人面命令不新增参数。
- **章名单从内容 id 派生**（`<course>-<chapter>-<kind>-NNN` 前缀），不建
  courses/chapters 表；新章内容入池后自动出现在开关里。
- **`active_chapter` 空字符串显式定义为「全课程」**：今天前缀会退化成
  `"dmath-"`、`LIKE 'dmath-%'` 恰好匹配全部章——本变更把这个巧合升为契约。
- **视图与练习跟随透镜**：知识点页、图谱页、复习页、练习页的建议范围按当前
  章取数。
- **选区（staged list）不受透镜约束、可跨章**：保留 REQUIREMENTS.md:22
  「考前突击（`--mode all` 跨章节）」与「不锁题/不隐藏」的既有立场。
- hub 卡片四项统计**统一为整课程口径**（修掉 kps 按章、题数/待复习全池的
  不一致）。
- `lesson-kit use` 保留；`review-workbench` 的切换需求改写为双受众措辞。

## Capabilities

### Modified Capabilities

- `review-workbench`：Course and chapter switching 改写为双受众（dashboard 开关
  + CLI，空章 = 全课程）；Workspace registry 的 hub 统计口径改为整课程；新增
  「章名单派生」与「章透镜作用域」两条要求。
- `workbench-ui`：顶栏新增章开关控件（不新增导航页、不显示统计或排序理由）。

## Impact

- 代码：`workbench/server/{pages,api,app,context}.py`（顶栏控件、透镜取数、
  hub 口径）、`workbench/data/queries.py`（`hub_stats` 改全课程口径）、
  `workbench/server/static/{workbench.js,workbench.css}`（开关）、
  `workbench/cli/main.py`（`use` 空章语义与 help 文案）。
- 测试：`tests/workbench/` 增补（章名单派生、开关写注册表、hub 四项口径一致、
  选区跨章不丢、全课程透镜）。
- 文档：GLOSSARY「章」条目（本变更的前置）；PRODUCT-MANUAL「选定范围」章节补
  章开关；ACTION-GRAPH 登记新增/改级动作。
- 无池结构变更、无迁移；不动 `pipeline/`、`pool/scripts/`。
