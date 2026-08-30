# 2026-08-30 Check Agent 产出链完整交付交接（队列④收尾）

> 给下一对话的开场材料。读完本份 + `AGENTS.md` + `docs/ACTION-GRAPH.md` 即可
> 接续。上一阶段交接见 `2026-08-29-check-pipeline-handoff.md`（Check 管线本体）
> 与 `2026-08-29-practice-loop-ux-completion-handoff.md`（全景）。

## 一、本轮交付了什么（harden-check-agent-chain，已归档）

接「introduce-check-pipeline 已实现但真 Agent 链没走通」的反馈，按《新项目
开工检查清单》以生产任务标准重做交付（范围问卷
`2026-08-30-check-agent-chain-questionnaire.md`、决策专题 23）：

- **反馈回路**：上一轮 check_ingest 的裁决（成功批次/逐条拒收/区块无效）
  经 `last_check_outcome` 注入下一轮 provider 上下文。
- **提示词契约硬化**：出题一律动作区块、id 规则 + next_free_ids、长度/题型
  白名单、×乘号、source_evidence、3–6 条、正确 item 示例。
- **manifest 完备格式**：题/卡 items 可携带 topic_label（微题另带
  display_title/display_summary），门禁校验；flash_cards additive 增列。
- **`wb ingest batches`**：批次只读清单。
- **裸 manifest 容错**：真 agent 常省略 `"type":"check_ingest"` 包装，
  check_intent 下已接受。

## 二、benchmark 结果（定稿协议与全表见 changelog/2026-08-30-harden-check-agent-chain）

- 闪卡首轮成功率 **8/10=80%**、微题 **10/10=100%**（达标线 60%，判达标）。
- 失败 2 轮均为 codex 超时（300s 默认；agent 会内子流程拖长尾延迟）——
  缓解选项：bridges.json 调 timeout_s。
- 反向用例 4/4 逐条拒收零写入；降级验证如实报错零写入。
- 原始数据 `Temp/check-benchmark/results/`（可删，结论已入 changelog）。

## 三、下一步候选（均未立项，勿主动开工）

1. **所有者真实池验收**（本轮最终验收步骤，见 changelog「所有者最终验收
   路径」四步）。
2. 界面闭环（卡片跳转/批次视图）——问卷未选，显式后续。
3. 综合题出题配方——问卷排除，显式后续。
4. codex 会内子流程延迟治理（超时缓解）。
5. candidate_problems 物理清理（DROP）——观察期后。

## 四、配方与纪律（防复发）

- **双服务器幻影**：起 3091 前必查 `netstat -ano | grep :3091` 杀干净——
  旧服务器会吞掉请求让你调试幻影 bug（本轮再犯一次）。
- `wb init` 会把 pool 目录里排序靠前的 .db 注册为工作区库——副本环境放
  备份 db 前先 init，或 init 后改 workspaces.json 的 db 字段。
- 走查副本迁移：池拷贝后必须手动跑一次 `ensure_workbench_schema`
  （服务端启动不自动迁移），否则新列缺失在 apply 时才炸。
- benchmark 纪律：hold-out 集物理隔离（本轮 dev=kp-001/002/004/007/028，
  hold-out=003/005/006/008/009/010/012/015/020/026）；驱动脚本 Temp/
  check-benchmark/run-benchmark.py（协议在 design.md D6）。
- codex sub-agent ≤2 并行、文件集不交叉（本轮 Lane A/B + 缝合模式再次验证）。
- 基线：pytest 351 / node 90 / 11 specs / 双 guard；git 通道 Git Data API
  recipe（PUT rebase）；中文 JSON 走 `--data-binary @file`。
