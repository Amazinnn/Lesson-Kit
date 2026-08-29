# 2026-08-29 practice-loop-ux-completion 交接文档

> 给下一个对话的开场材料。读完这一份 + `AGENTS.md` + `openspec/config.yaml`
> 列出的文档即可接手。上一阶段交接见
> `docs/superpowers/plans/2026-08-29-introduce-flash-card-handoff.md`。

## 一、本阶段交付了什么（全部已合并，CI 绿）

变更：**practice-loop-ux-completion**（已归档于
`openspec/changes/archive/2026-08-29-practice-loop-ux-completion/`）。
四个 PR：**#24** 规格 → **#25** 实现+走查+归档 → **#26** 手册 8–9 章成文 →
**#27** generate 桥定义。

### 1. 会话牌组（前端脊柱，新静态模块 `practice-deck.js`）

练习会话状态收敛为一处：历史 + 游标 + 每项状态
（作答/选项/判分/揭示/自评态）。SESSION_KEY 存 v2 格式
`{v:2, items, cursor, ended?}`（字段名沿用旧 entries，session-end 页兼容，
v1 数组可读）。`renderDeckItem` 由状态驱动渲染；**刷新恢复升级**：恢复
游标与全部视图状态（含回翻位置、已揭示背面、判分横幅）。batch 队列耗尽
时置 `ended` 标志，回到 practice 页自动重回收束页。

### 2. batch 判分横幅（所有者拍板的新语义）

判分**即时**、自评**延迟**：micro/yes_no 答完立刻显示对/错横幅（答错
高亮正确项、选项禁用），`VERDICT_HOLD_MS=2000` 停留后自动推进
（generation token 防击穿会话结束；期间点「跳到下一道」立刻走、点
讲解/诊断取消定时器）。exam 文本题无判分不停留。横幅纯本地展示，
**不写任何学习记录**（feedback 仍只在收束页）。

### 3. 闪卡回翻

「上一张/下一张」两种自评模式都可用：回看保留揭示/评分状态，immediate
已评卡只读，未揭示的跳过卡可补揭示（skipped→unrated），**历史末尾再按
下一张才拉新卡**（exclude 仍取全部 items）。跳过动作不降级已答/已玩条目。

### 4. 讲解/诊断前端入口（spec "shown in the UI" 的履约）

练习页 problem 项作答后出现「讲解」「诊断」：`POST /ai/{operation}`
（诊断带 `user_answer`，未作答软门槛）→ 轮询 `GET /ai/jobs/{id}` → done
后 `GET /explain/{id}` 渲染分节 markdown 于练习栏；失败显示原因（契约
校验缺节也会如实列出）。**门槛修正**：按钮可用性以 bridges.json 任务
provider 为准（新端点 `GET /ai/task-providers`），不是对话 provider 的
PATH 发现——没配 `wb bridge add` 时按钮禁用 +「暂无可用 Agent」。
任务级停止不存在（仅对话轮次有）。

### 5. 标签完整显示（所有者铁律：不截断、不省略号）

- 图谱：`graph-physics.js` 碰撞半径纳入标签占地（labelLineCount 估行数）
  + `workbench.js` 稳定后跑**标签盒确定性避让**（量 DOM 实际包围盒推开
  节点，40 轮上限）——走查实测 31 标签 0 重叠、全折行完整显示。投影管线
  未动。
- 到期条目：删 `queries.py _item_label` 的 `[:40]`（实测 330 字全长返回）。
- 日历 chip：`.calendar-goal` 折行、格高自适应；38 字标题完整显示
  （格会变很高——命名纪律问题，UI 不兜底）。

### 6. 手册与定义

- PRODUCT-MANUAL 第 8 章（Agent 对话：固定 provider、上下文、一键任务
  与输出契约、任务无停止、降级、范围替换门槛、普通对话不写学习记录）、
  第 9 章（数据安全边界：会写/绝不写/备份/注册表/副本纪律）成文；
  6.2/6.3/6.4/6.5/6.6/6.7 增补。
- **generate 桥定稿**（PENDING-DEFINITIONS 三要素）：AI 产出 recipe
  manifest → 所有者触发既有门禁入池，无逐题人审，AI 永不直写池；
  **批次 id + 整批回滚**为安全网（机制入定义，实现另立项）；题型学为
  桥上显式未定项。GLOSSARY 新增「批次 id」「整批回滚」；
  DISCUSSION-RECORD 专题 20 记录全部拍板。

## 二、当前状态

- **远端 main**：`e9aa651`（PR #27 合并点）。本地已同步、工作区干净。
  11 个 capability specs，**0 active changes**，openspec validate 11 passed。
- **测试基线**：pytest **326** 全绿、node **87** 全绿、guards PASS。
  （JS 侧新增 practice_deck.test.js 9 条 + 交互套件扩到 52 条。）
- **3081（真实工作台）已重启吃新代码**；3091 走查服务已停。
- 走查 scratch 在 `D:/Projects/Academic Workflow/.lessonkit-scratch-ux/`
  （wsux 工作区 + stub_provider.py 桩，可整体删除）。

## 三、走查结论（3091 副本，全部实测过）

- micro batch：错答横幅+正确项高亮+fieldset 禁用 → 2s 自动翻页 → 拉空
  耗尽自动进收束页 → 评分写入（schedule 行 repetitions=1、due 次日）。
- 闪卡 batch：揭示→unrated；跳到下一道拉新；回翻状态保留；**回翻中刷新
  恢复同位**；前进不重拉、末尾拉新；收束页卡片评分 → `item_type='card'`
  调度写入。
- exam immediate：作答→按钮出现；讲解任务端到端（桩 provider 写契约
  合规四节 → done → 渲染 → 状态清空）；诊断对 explain 形状产出正确
  判失败并列出缺失分节；无 bridges.json 时按钮禁用+提示。
- 图谱 31 标签 0 重叠全显示；日历 chip 38 字完整折行；到期条目 330 字
  全长。截图证据：走查会话内（未入库）。

## 四、未修清单 / 下一步候选（所有者知情）

1. ~~内容缺口~~ **已补齐（2026-08-29 夜，coverage batch）**：23 个缺口 KP 全补——闪卡 51 张
   （fc-016…066，概念/公式/算法类）+ 微题 18 道（mq-028…045，方法/模型类）；
   池现为 345 题（42 微题）/ 66 卡 / 31/31 覆盖。manifest：
   `pool/ingest/fc-batch-002.json`、`pool/ingest/mq-batch-003.json`；备份：
   `pool/backups/dmath-2026-08-29-pre-coverage-batch.db` + 两个 apply 备份。
2. **generate 桥实现**：定义已定稿，批次 id / 整批回滚 / AI manifest
   产出链待立项（未来段，勿主动开工）。
3. 3082 demo 进程是上一会话的，随机器消亡；重启配方见旧交接。
4. 未来段不变：反向卡 / leech / cloze 自动拆卡；Scoropic 冻结；
   方向卡 UI 待真实使用；插件生态暂缓。
5. 后续内容加深（每 KP 超过 3 条、题型扩展）仍走 §五门禁流程。

## 五、操作备忘（增量）

- 前端改动的测试网：`tests/workbench/workbench_ui_interactions.test.js`
  用 vm 跑真 `workbench.js`；新增页面元素必须 null-guard；vm 上下文需注入
  `PracticeDeck`（两个测试文件的装载器都要）。
- batch 停留测试法：`setTimeoutFn: (cb, delay) => timers.push({cb, delay})`
  收集后手动 fire `delay === 2000` 的回调。
- 讲解任务 E2E 桩：scratch 里 `stub_provider.py`（读 stdin、写
  LESSONKIT_OUTPUT_PATH 四节）+ `wb bridge add stub --command python
  --args <script>`。
- API 发 PR：中文 JSON 必须走 `--data-binary @file`（内联 `-d` 会解析
  失败）；merge 用 PUT + rebase。
- git 通道本阶段全程健康（push/PR 均正常）。
- **⚠️ 已知异常（防复发）**：会话末发现本地 `intermediate/.../00_source/images/`
  121 个文件被从磁盘删除（git 历史完好，`git checkout -- intermediate/`
  已恢复，双 guard 复验通过）。触发源未定位，最可疑的是 `wb init <副本>
  --course/--chapter`（在仓库根 CWD 运行）或某 pytest 用例触碰真实路径。
  **下次跑 init/测试后顺手 `git status` 查一眼**；若复现，先锁定再修。

## 六、纪律提醒（不变）

名词先定义后使用；需求先落 OpenSpec 再动代码；additive schema；
不锁题；参数不露学生。冻结：投影管线、Scoropic（ADR 0021）、插件生态、
方向卡 UI。走查是验收线，测试绿 ≠ 完成。
