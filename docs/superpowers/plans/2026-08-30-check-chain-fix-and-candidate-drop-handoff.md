# 交接文档：出题链修复 + 候选物理退役 + 加固批次合并（2026-08-30 晚）

> 新对话开场喂三件套：`AGENTS.md` + `docs/ARCHITECTURE.md` + 本文档。
> Agent 先复述分层铁律、兼容边界、scope 边界，确认后再动手。

## 一、当前状态（一句话版）

`Amazinnn/Lesson-Kit` main = `7c9a39a`（本地同步、树干净、CI 双矩阵绿）。
基线：pytest **357** / node **92** / `openspec validate --specs --strict` 11 通过、
0 active changes、compileall、双 guard 全绿。真实池 `pool/dmath.db`（未被 git
跟踪）：Check schema 已迁移、候选两表已 DROP，66 卡 / 345 题 / 31 KP / 6 信号。

## 二、本轮（2026-08-30 一天）做了什么

1. **14 分支加固批次 #39–#52 评审合并**（所有者侧程序产生）。评审确认非过度
   防御后按序 rebase-merge，零冲突。要点：#41/#49 修复"坏请求无 HTTP 响应
   断连"（400/415/2MiB/遍历）；#42 对话重启恢复+kill 升级；#40 学习写入事务
   化；#43 next_free_ids 改章节前缀范围；#52 回滚持锁+learning_current_state
   阻断；#45 起 CI 强制 openspec strict + compileall + 双 guard；#44 加
   pyproject（`wb` 入口，stdlib-only）。
2. **conv-023 出题链修复**（所有者验收用 Claude 暴露，openspec
   `disclose-ignored-action-blocks`）：桥解析全区块按意图匹配（原来只认第一
   个区块，Claude「选区+manifest」同报丢 manifest）；check_intent 正则补自然
   措辞 `(?:补|加|写|生成)[^。？?]{0,6}(?:闪卡|微题|题|卡)`；被忽略区块从镜像
   剥离并向下一轮上下文披露「未写入任何内容」（封死幻觉申报）。
3. **候选机制物理退役**（openspec `remove-candidate-store`）：`wb data` 的
   candidate 实体与 gate/promote 动作下线、pull 不再输出 candidates、候选证据
   分支删除、新库不再建候选两表、真实池 DROP（备份
   `pool/backups/dmath-pre-candidate-drop-20260830.db`）。learner_signals 为核
   心保留——`ensure_problem_candidate_schema` 是冻结 pipeline 脚本的兼容入口，
   仍负责建 learner_signals（共用了 `_ensure_learner_signals` 助手）。
   ADR 0008 → Superseded；GLOSSARY 候选题条目改退役完成。
4. **真实池 schema 预迁移**（同日早些）：`ensure_workbench_schema` 已在真实池
   应用（备份 `pool/backups/dmath-pre-schema-20260830.db`）——**重启 3081 即
   可验收，无需再迁移**。
5. **方向拷问**（专题 24 + FUTURE-DEVELOPMENT-NOTES）：验收先行 → 综合题×
   真题拟合联合立项等一轮真实使用 → 轻量收尾窗口（界面闭环/codex 延迟治理
   视验收，candidate DROP 已做）→ 教师记忆消费端保持机会主义 → 难度统一评价
   体系后置、具体算法排前端设计之后。新挂名：真题拟合（并入联合立项）、双向
   闪卡——均登记 PENDING-DEFINITIONS。

## 三、已知问题与坑（防复发）

- **flaky**：`test_successful_turn_mirrors_exchange_and_second_turn_resumes`
  在 Windows 下偶发 PermissionError（测试线程读 turn json 时后台线程仍在
  写）。重跑即过；本轮未修（记录待议）。
- **codex sub-agent 用量限额**：当晚耗尽，08-31 02:17 (UTC?) 前不可用。停掉
  的分身必须先核对残留再接手（本轮 lane 把 learner_signals 兼容入口掏空导致
  3 例测试失败，已修）。
- **`wb serve` 无位置参数**：`wb serve --port N` 直接服务注册表活动工作区。
- **content_sequences CHECK 值域仍含 'candidate'**（有意保留避免表重建，无行
  为影响）；`pipeline/scripts/insert-candidates.py` 等成为无调用方退役脚本，
  按分层铁律不删不改。
- **双 3091 幻影**：起 scratch 服务器前必查 `netstat -ano | grep :3091` 杀干
  净；`wb init` 会把 pool/*.db 排序第一者注册为工作区库。
- 所有者上次验收实际发生在**检查页（benchmark 副本 3091）**，不是真实池；真
  实池至今零 Check 写入。

## 四、下一步候选（均未立项，勿主动开工）

1. **所有者重验收**（最优先，所有者动作）：重启 3081 → 四步路径
   （changelog/2026-08-30-harden-check-agent-chain.md）→ 重点复测
   「给 dmath-ch06-kp-XXX 补两张闪卡」：预期结果卡片带批次号、练习页闪卡可
   见、无幻觉申报；若区块不合规，对话内出现「未写入」披露。
2. **轻量收尾窗口**（已获所有者预授权，各自带闸门）：界面闭环（验收确认
   「成果找不回」痛点→做）；codex 延迟治理（验收体感卡→bridges.json
   timeout_s）。
3. **联合立项：综合题配方 × 真题拟合**——等 Check 首期一轮真实使用后启动；
   启动第一步是定义流程（PENDING-DEFINITIONS「真题拟合」条目），评估方法参照
   FUTURE-DEVELOPMENT-NOTES 实验指标 + 池内 difficulty + ADR 0018 归纳/迁移/
   推广目标；难度统一评价体系排前端设计之后（所有者 08-30 新排序）。
4. **前端设计轮**：所有者 08-30 提及「前端设计」先于难度算法——范围未定，
   立项前先拷问（可能与界面闭环合并）。
5. 挂名池（均需先走定义流程）：双向闪卡、cloze 拆卡、教师记忆消费端（机会
   主义）、速成模式视图/批量揭晓/扩展摘要/Obsidian 打包/图形资产工具/CLI 层
   agent 准备。冻结：Scoropic（ADR 0021）、方向卡 UI（待真实使用）。

## 五、纪律（不变 + 本轮强化）

- codex sub-agent ≤2 并行、文件集不交叉；分身中断先核对残留再接手。
- spec 先行：行为变更先落 openspec change（strict 校验）再动代码。
- 验证节奏照 AGENTS.md：pytest / openspec strict / 双 guard，交付前必跑。
- 真实池写入唯一合法通道 = 门禁配方 apply；schema 变更走 ensure_* 增量模式
  且先备份到 `pool/backups/`（gitignored）。
