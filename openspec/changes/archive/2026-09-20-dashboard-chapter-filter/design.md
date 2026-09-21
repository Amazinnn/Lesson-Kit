# design — dashboard-chapter-filter

## 上下文

- 池是课程级（GLOSSARY「池」：`pool/<course>.db`，「章节数据库」在 _Avoid_ 中）。
  章今天只以三处形式存在：内容 id 的前缀段（`dmath-ch06-kp-001`）、注册表
  `active_course/active_chapter`、磁盘路径 `{course}/{chapter}/`（figures/output）。
- 服务端每个请求用注册表重建 `Pool(root, db_path, course, chapter)`
  （`workbench/server/api.py:50`）；前缀查询分布在约 10 处，各自手拼
  `f"{course}-{chapter}"`。
- 当 `chapter` 为空串，前缀退化为 `"dmath-"`，`LIKE 'dmath-%'` 恰好匹配所有章
  ——「全课程」在数据层已经能跑，只是从未被当作契约。
- hub 卡片当前口径不一致：`queries.hub_stats` 的 kps 按章，problems/signals/due
  是全池。
- `lesson-kit ls` / 命令侧另有 `prefix = f"{course}-{chapter}"` 的使用（cli/main.py:105）。

## Goals / Non-Goals

**Goals**

- 人面在 dashboard 上一个开关切「全课程 ↔ 某一章」；人面命令零新增参数。
- 章名单来自池内容，不引入第二真源。
- hub 统计四项口径一致（整课程）。

**Non-Goals**

- 不建 courses/chapters 表；不做章显示名、顺序、来源位置。
- 不做多选章范围（开关单选；真实多章同练需求出现前不搭脚手架）。
- 不把透镜变成选区的边界。
- 不改 `pipeline/`、`pool/scripts/`；不动池 schema。

## 决策

### 一、章名单从内容 id 派生

解析三类 id 的章段——`knowledge_points.kp_id`、`problems.problem_id`、
`flash_cards.card_id`——`SELECT DISTINCT` 后按章段排序。判定按**右侧类型段**切
（`^<course>-(.+)-(kp|prob|mq|fc)-\d+$`），不按第一个连字符切，因为章段可能自带
连字符。`workbench/ingest/__init__.py:641` 的 `build_legacy_figure_manifest`
已有同构正则，沿用同一形状；解析不出的行忽略（不猜）。

### 二、空章 = 全课程，从巧合升为契约

`active_chapter = ""` 显式定义为「不过滤」，数据层不需要新代码路径。CLI 侧：
**省略**第二个位置参数仍是用法错误（保留既有 spec 场景）；`lesson-kit use
dmath ""` 才是「切到全课程」，在 help 文案与 PRODUCT-MANUAL 写清。

### 三、开关写注册表，与 `use` 同一个值

切换 = 服务端新端点调 `registry.update_active(name, course, chapter)` + 刷新页面。
人面入口是开关，Agent 面入口是 `use`，值只有一个，跨会话记忆自然成立。
frontend 只做控件与请求，不缓存筛选状态。

### 四、hub 整课程口径

`hub_stats` 的 kps 改为全课程（其余三项保持全池，即现状），四项同口径。hub 卡片
回答的是「这个工作区有什么」，与透镜无关；顶栏的章上下文只出现在工作区内部。

### 五、透镜管「看」，选区管「练」

透镜作用域 = 知识点页 / 图谱页 / 复习页 / 练习建议；选区（staged list）不受约束、
可跨章、切换不丢。想跨章练 = 关掉透镜，或把两章 KP 选进选区。这与
REQUIREMENTS.md:22「考前突击（`--mode all` 跨章节）」及「不锁题/不隐藏」一致。

## Risks / Trade-offs

- 章段解析依赖 id 约定；约定本身由 spec「Readable content sequences」保证
  （`<course>-<chapter>-<kind>-NNN`），解析失败只影响名单，不阻断页面。
- 单开关不覆盖「两章一起看」；判断：真实需求出现前不做，选区已能承担跨章练习。
- 本变更让 **web 侧开始写用户级注册表**（此前只有 CLI 写）。单用户本机场景下
  沿用整文件覆盖的最后写赢（`registry.save_registry`），不引入锁。多进程同时写
  是可接受的已知边界，写入前不回读校验。
- 透镜开启时「复习页之下的 due 总数」会随章变化；与 hub 的课程级数字并存，
  语义分工写进 PRODUCT-MANUAL，避免被读成矛盾。
