# complete-goals-loop 任务

## 1. 规格（PR1）

- [ ] calendar-workload delta：目标生命周期管理（编辑/删除/取消，即时生效）
- [ ] ai-teacher-bridge delta：目标表单助填动作（意图门/字段契约/原位应用/提交留给人）
- [ ] `openspec validate complete-goals-loop --strict` 通过

## 2. 实现（PR2）

- [ ] A 编辑/删除：卡片入口 + 表单复用（PATCH/DELETE）+ 取消编辑 + 即时刷新
- [ ] B 助填：NL 输入→对话轮次（goal_intent）→ prefill_goal_form 校验→
      表单原位填充 + 无 provider/无会话降级
- [ ] conversations：_prompt 双动作说明 + _extract_action 双类型分支
- [ ] context：goal_intent 进服务端上下文
- [ ] C goals CLI：list/add/update/rm（纯数据接口）
- [ ] 测试：context/extract_action/CLI/UI 交互（编辑/删除/助填应用/普通对话不填）
- [ ] 文档：PRODUCT-MANUAL 2.1/5 章、ACTION-GRAPH L2/L3/L4 + 队列③状态

## 3. 走查与归档（PR2 内）

- [ ] 3091 副本：建→改→删全流程；NL 助填（桩 provider 返回动作）原位填充；
      无 provider 降级文案；四模式冒烟
- [ ] 归档 change，`openspec list` 清空
