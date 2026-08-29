# changelog — micro-quiz 第二批 + 闪卡首批内容（PR3 部分）

日期：2026-08-29　变更：同 `2026-08-29-introduce-flash-card`
内容 PR：content/flash-card-first-batch

## 真实池落库（全走门禁 + 备份）

- 迁移：`flash_cards` 表 + CHECK 加宽 + `practice_modes` 改名，312 题无损。
- 删除 3 道 retired `short_answer`（mq-003/006/009，kp-001/002/028），重制为
  单选题 **mq-010/011/012**（`mq-batch-002a-retype.json`）。
- **微题第二批 15 道**（`mq-batch-002.json`，mq-013…027）：低覆盖知识点
  kp-004 除法规则 / kp-007 鸽巢推论 1 / kp-029 位串生成子集 / kp-030 字典序
  r-组合 / kp-031 康托展开，每个知识点 1 单选 + 1 多选 + 1 判断。
- **闪卡首批 15 张**（`fc-batch-001.json`，fc-001…015）：kp-001 乘法规则 /
  kp-004 / kp-007 / kp-029 / kp-031，每个知识点 3 张键值对卡，一卡一个
  原子事实（最小信息原则），来源证据 = 知识点 source_location + 具体段落。

## 落库后状态

- 题目总数 312 → **327**；微题 24 道（13 标 micro + 11 标 yes_no），
  retired 类型 0 残留；闪卡 15 张；31 个知识点完好。
- 备份：`pool/backups/dmath-2026-08-29-pre-flashcard.db`（迁移前全量）+
  三次 apply 各自的 `dmath-2026-08-29-apply-*.db`。

## 走查（3091 副本，隔离注册表）

四模式可练；改名后空态文案；会话聚焦收敛/恢复；闪卡揭示流（正面→背面→
自评→不重复）；session-end 卡片条目补评分并写调度（due 推进到 09-04）；
重制题 mq-010 点选判分；写入路径全链路（feedback event / schedule row /
kp state / 「可以复习」提醒）。
