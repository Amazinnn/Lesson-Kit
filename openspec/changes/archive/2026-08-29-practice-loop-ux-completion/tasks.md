# practice-loop-ux-completion 任务

## 1. 规格（PR1）

- [x] micro-quiz-content delta（batch 判分停留 + 正确项高亮）
- [x] flash-card delta（会话历史回翻）
- [x] ai-teacher-bridge delta（练习页一键任务入口）
- [x] workbench-ui delta（标签完整显示 + 跨表面完整显示）
- [x] `openspec validate practice-loop-ux-completion --strict` 通过

## 2. 实现（PR2）

- [x] practice-deck.js 脊柱 + practice_deck.test.js 单测
- [x] workbench.js 练习段接入牌组（renderDeckItem、session/setCurrent 适配、
      刷新恢复游标与视图状态、SESSION_KEY v2）
- [x] A：batch 判分横幅（settle choices/verdict、高亮正确项、2s 停留 +
      generation token）
- [x] B：闪卡上一张/下一张（状态保留、末尾拉新、补揭示 skipped→unrated）
- [x] C：讲解/诊断入口（job 轮询、结果渲染、无 provider 降级、诊断软门槛）
- [x] D：图谱标签碰撞+折行 / 近期活动去截断 / 日历 chip 折行
- [x] pytest + node 全绿；openspec validate --specs --strict；两条 guard

## 3. 走查与归档（PR2 内）

- [x] scratch 副本走查：4 内容模式 × 2 自评模式全流程、横幅停留+高亮、
      闪卡回翻+收束、回翻中刷新恢复、讲解/诊断（配/不配 provider 两态）、
      图谱/近期活动/日历完整显示
- [x] FUTURE-DEVELOPMENT-NOTES 四条标记已修
- [x] 归档 change，`openspec list` 清空
