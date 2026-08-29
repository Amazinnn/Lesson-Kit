# 2026-08-29 introduce-flash-card 交接文档

> 给下一个对话的开场材料。读完这一份 + `AGENTS.md` + `openspec/config.yaml`
> 列出的文档，就可以接手。上一阶段交接见
> `docs/superpowers/plans/2026-08-29-consolidate-practice-views-handoff.md`
>（其交付内容已全部进 main，仅历史参考价值）。

## 一、本阶段交付了什么（全部已合并，CI 绿）

变更：**introduce-flash-card**（2026-08-29 定案并交付，已归档于
`openspec/changes/archive/2026-08-29-introduce-flash-card/`）。
三个 PR：**#21** 规格+词表+说明书 → **#22** 实现 → **#23** 内容+走查+归档。

### 1. 正名（所有者 2026-08-29 拍板）

- 旧「闪卡」模式（微题的卡片式渲染）改名 **`micro`（小测）**；
  `flash_card` 这个 mode id 让给新功能。schema 幂等迁移：
  `ensure_workbench_schema` 里 `practice_modes` 值 `"flash_card"`→`"micro"`。
- 练习模式现为四种：`exam` 综合题 / `micro` 小测 / `yes_no` 判断 /
  `flash_card` 闪卡。

### 2. 闪卡（第四种练习模式，新能力 spec `openspec/specs/flash-card`）

- 模型：Anki Note/Card 两层最小版。**知识点 = 唯一事实源（Note）**，
  闪卡 = 从知识点解构出的键值对派生卡（Card）：正面→回忆→揭示背面→
  1–5 自评，**无选项、无判分**。一卡一个原子事实（最小信息原则，
  内容纪律不做程序化度量）。
- 数据：新表 `flash_cards(card_id, kp_id, front, back, source_evidence)`
  恰 5 字段（front ≤100 / back ≤300 字符，来源证据必填）；
  card_id 规则 `^[a-z0-9-]+-fc-\d{3}$`。
- 入池：`wb ingest <ws> recipe flash-card`（kind=`flash-card-patch`，
  确定性门禁 + 备份 + 单事务 apply，与 micro-quiz 配方同构）。
- 练习：`POST /api/w/{name}/pull-cards`（选区 kp 过滤、到期行优先、
  exclude_ids 支持）；JS 会话按 `MODE_KEY='flash_card'` 分支；composer 三态
  `setComposerLayout('card'|'choice'|'text')`。
- 调度：`item_type='card'` 每卡一行独立调度（direction 键留空备用）；
  `/feedback` `item_type='card'` 走既有通道，信号/状态挂到卡的知识点。
  `review_schedule`/`feedback_events` 的 item_type CHECK 已加宽 `'card'`
  （数据保留式重建迁移）。
- **反向卡、leech 闭环、cloze 自动拆卡 = 未来段**，已写进 spec Purpose，
  本期不实现。AI 自动解构知识点成卡属 PENDING-DEFINITIONS 的 generate 桥。

### 3. micro 收敛（所有者定义：微题 = 选择题）

- 题型集收窄：`yes_no / single_choice / multiple_choice`；
  `short_answer / closest_answer` **退役**（门禁显式拒绝）。
- 微题一律点选作答：有选项即隐藏自由文本框；本地判分逻辑不变。
- practice_modes 推导：单/多选 → `["micro"]`，判断 → `["yes_no"]`。

### 4. 会话聚焦（UX 清单项，已修）

任何模式、任何自评时机：点「开始本轮练习」后 `.practice-columns`
（目标卡/准备列表/建议/模式选择/时间视图）整体隐藏，中间栏只留练习流；
耗尽 / 提前结束 / 刷新恢复分支同步恢复或收敛。

### 5. 真实池内容（全走门禁 + `pool/backups/` 备份）

- 312 → **327 题**：3 道 retired short_answer（mq-003/006/009）删除重制为
  单选 mq-010/011/012；**微题第二批 15 道**（mq-013…027，kp-004 除法规则 /
  kp-007 鸽巢推论 1 / kp-029 位串子集 / kp-030 字典序 r-组合 / kp-031 康托
  展开，各 1 单选 + 1 多选 + 1 判断）；**闪卡首批 15 张**（fc-001…015，
  kp-001/004/007/029/031 各 3 张）。
- 备份：`pool/backups/dmath-2026-08-29-pre-flashcard.db`（迁移前全量）+
  三次 apply 各自的 `dmath-2026-08-29-apply-*.db`。

## 二、当前状态

- **远端 main**：PR #23 合并点，11 个 capability specs，**零 active changes**，
  openspec validate 11 passed。pytest 324 全绿、node 78 全绿、guards PASS。
- **真实池**：327 题 / 24 微题（13 micro + 11 yes_no）/ 15 闪卡 / 31 KP
  完好。lesson-kit 工作区（端口 3081）**需要重启才能吃到新代码+新内容**。
- **demo 3082**：本会话后台进程，workspace `demo`（真实池新内容副本，
  写入安全）。会话关闭即消失；重启配方见下。
- **⚠️ 本地仓库未同步**：本机 git→GitHub 通道故障（见 §五），PR2/PR3 是经
  GitHub API 构建进远端的，本地 main 停在 `0c5b5d5`。**下一会话第一件事**：
  ```bash
  git fetch origin && git checkout main && git reset --hard origin/main
  git branch -d feat/introduce-flash-card content/flash-card-first-batch
  ```
  （reset 前确认 `git status` 干净；两分支内容已全部在远端 main 里。）

## 三、走查结论与顺手修复

- 3091 副本走查全过：四模式可练、改名空态、聚焦隐藏/恢复、闪卡揭示自评
  全流程、session-end 卡片条目补评分并推进调度、重制批判分、写入路径全链
  （feedback event / schedule row / kp state / 「可以复习」提醒）。
- **走查发现并当场修**：batch 闪卡原本没有收束路径（揭示后无 unrated 标记，
  session-end 永无卡片条目）。修复：batch 下揭示即标 `unrated`、就地评分
  隐藏；`跳到下一道` 对已揭示的卡保留 `unrated`（未揭示仍算跳过）。
- 词表与说明书已同步：GLOSSARY（小测模式改写、闪卡新条目、微题/练习模式/
  门禁条目）、PRODUCT-MANUAL（2.4 四模式、6.3 小测点选、6.5 闪卡节、2.5
  会话聚焦、章内编号顺延）、PENDING-DEFINITIONS（generate 桥加注）。

## 四、未修清单（所有者知情，按需再议）

1. **UX 遗留**（FUTURE-DEVELOPMENT-NOTES「方向卡 UI 与剩余 UX 清单」节）：
   图谱标签重叠/挤压；40 字标签截断无省略号；日历格内目标 chip 只显示
   首字；**新记**：统一自评下微题的即时判分被立即翻页覆盖，对错只能等
   收束页答案（建议 batch 也短暂显示对错再翻页）。
2. **PRODUCT-MANUAL 第 8–9 章仍是骨架**（Agent 对话、数据安全边界）。
3. **微题/闪卡内容缺口**：仅 kp-001/002/004/007/028/029/030/031 有微题或
   闪卡，其余知识点仍只有综合题；继续补内容走 §五的门禁流程即可。
4. 未来段（不要主动提）：反向卡 / leech / cloze 自动拆卡（flash-card spec
   Purpose）；AI 自动解构 = generate 桥（PENDING-DEFINITIONS）；Scoropic
   冻结（ADR 0021）；方向卡 UI 待真实使用；插件生态暂缓。

## 五、操作手册（踩坑防复发）

### 门禁入池（唯一合法写池方式）

```bash
# 1) manifest 写到 pool/ingest/（kind: micro-quiz-patch 或 flash-card-patch）
# 2) 先在副本演练（见下），再对真实池：
python -m workbench.cli.main ingest lesson-kit recipe micro-quiz \
  --input pool/ingest/<file>.json --output .lessonkit/out-xxx \
  --apply --backup pool/backups/<name>.db
python -m workbench.cli.main ingest lesson-kit recipe flash-card ...  # 同构
```
- 门禁拒收重复 id：改题 = 先全池备份 → SQL 删行 → 新 id manifest 重入。
- 微题/闪卡乘号一律用 `×`，裸 `*` 会被 markdown 吃掉。
- schema 迁移是幂等的：任何副本/真实池先跑
  `pool/scripts/pool_schema.py ensure_workbench_schema(conn)`。

### Scratch / demo 配方

- 隔离注册表 `LESSONKIT_WB_HOME=<dir>`；走查 3091、demo 3082；
  **真实 3081 永不碰**。
- 副本只需 `pool/dmath.db` + `wb init <dir> --course dmath --chapter ch06`
  （CLI 是 `python -m workbench.cli.main`）+ schema ensure。
- demo 重启：拷当前 `pool/dmath.db` 到 scratch 工作区 → `wb init` 注册 →
  `python -m workbench.cli.main serve --port 3082`（后台）。
- 僵尸端口：`netstat -ano | grep :309x` + `taskkill //F //PID`。
- 本阶段 scratch 在 `D:/Projects/Academic Workflow/.lessonkit-scratch-fc/`
  （walkfc + demo-home 可留，其余可删）。

### 测试基线（交付前必跑）

```bash
python -m pytest tests -q          # 324 passed
node --test tests/workbench/*.test.js   # 78 passed
openspec validate --specs --strict # 11 passed
python lessonkit.py guard extract-problems --course dmath --chapter ch06
python lessonkit.py guard problem-set --course dmath --chapter ch06
```

### git/代理故障发货路线（本阶段实战验证）

- iKuuu GUI 会换混合端口（git config 钉在 7890，活端口可能是 7891）：
  `clash-control` 技能 `route.ps1 doctor` 检测。
- 若 git 的 TLS 彻底死（schannel/openssl 都失败）而
  `curl -x http://127.0.0.1:7891 https://github.com` 仍 200：走 **Git Data
  API** 发分支——blob（内容必须用 `git cat-file blob HEAD:path` 的 LF 字节，
  工作区可能是 CRLF）→ tree（`base_tree` = 远端 main 完整 40 位 tree sha，
  只放 A/M 条目）→ commit（parent = 远端 main 完整 sha）→ PATCH refs。
  删除条目（sha:null / 目录树）会撞 `GitRPC::BadObjectState`，改用
  **Contents API** 逐文件 DELETE（各成一个提交，可接受）。
  校验：`git rev-parse HEAD^{tree}` 与远端分支 tree sha 必须逐位一致。
  细节已记入 memory（reference-lessonkit-scratch-and-pr-workflow）。

## 六、纪律提醒（不变）

- 名词先定义后使用（GLOSSARY → 未定义进 PENDING → 再写正式文档）；
  功能变更交付时同步补 PRODUCT-MANUAL 对应章节。
- 需求先落 OpenSpec 再动代码；additive schema；不锁题；参数不露学生。
- 冻结：图谱投影算法、Scoropic（ADR 0021）、插件生态、方向卡 UI。
- 验证节奏见 AGENTS.md §开发纪律 4；走查是验收线，测试绿 ≠ 完成。
