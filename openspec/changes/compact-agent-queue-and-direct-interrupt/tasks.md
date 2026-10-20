## 1. Contract and implementation readiness

- [ ] 1.1 按 design.md 同步受影响的 GLOSSARY / FILE_CONTRACT / ARCHITECTURE / PRODUCT-MANUAL / ACTION-GRAPH；确认 DATA_MODEL 无 SQLite 变更，不机械改写无关文档。
- [ ] 1.2 确认旧会话缺 queue_order 的默认读取、waiting_for_stop 的独立投影、审批时 interrupt 拒绝及前端草稿恢复，先补边界失败用例再实施。

## 2. Bridge and thin API

- [ ] 2.1 在既有 ownership lock 下实现队列显式顺序、旧工件兼容读取和重排 CAS；同步接受、删除、dispatch、恢复时的顺序。
- [ ] 2.2 把 interrupt 从普通排队调度分离：持久接收、捕获旧轮次、停止确认和 worker 释放后直接交接；没有活动轮次时直接运行。
- [ ] 2.3 实现已排队消息的立即发送路由变更，沿用原 turn/上下文/文字；实现重复请求幂等、revision/dispatch 竞态、第二条 interrupt 冲突和已有队列保持暂停。
- [ ] 2.4 待审批时拒绝 interrupt/立即发送，保持草稿或队列原项；显式 queue 仍暂停接收；不改 Paper 写入边界。

## 3. Composer UI

- [ ] 3.1 输入框正上方显示单一紧凑列表，单行预览/完整读取、最多四行高度内部滚动、空队列隐藏、暂停提示只一份；支持窄屏与键盘。
- [ ] 3.2 接入拖动/键盘排序、立即发送、行内编辑和删除，冲突刷新而非覆盖；不替换活动回复或较新草稿。
- [ ] 3.3 waiting_for_stop 只显示独立短状态，已接受 interrupt 不进入列表；失败/未知/拒绝消息集中恢复，取消重复大卡片并保留显式核对与重试。
- [ ] 3.4 刷新/切页/切对话按服务端顺序恢复与身份去重；旧回调不作用新对话。

## 4. Verification and delivery

- [ ] 4.1 Bridge 测试：A 运行、B/C 排队与重排；提升 C；旧工件顺序；无队列的 D 中断；停止竞态/无确认/第二条中断；审批拒绝；去重和原上下文保持。
- [ ] 4.2 UI 测试：列表行和操作顺序、重排409、编辑/删除/立即发送竞态、仅 interrupt 时无队列、四行高度与键盘、恢复摘要去重、草稿不覆盖。
- [ ] 4.3 数据库副本 + 隔离注册表 + 独立端口走查，验证截图所示长恢复卡不再挤满输入区、队列与中断各自行为；不写真实池。
- [ ] 4.4 跑仓库要求的 pytest / compileall / OpenSpec strict / extract-problems guard；按对应产物条件运行 problem-set guard。
- [ ] 4.5 更新交接、完成独立审查和实现验收后再归档；本次提案交付不勾选上述实施任务。

## Proposal handoff — 2026-10-20

本轮仅创建 change 的 proposal / design / delta specs / tasks。未改产品代码、测试、真实会话、数据库或当前职责规范；用户所给第二张截图是紧凑列表参照，第一张截图是待消除的大卡堆叠问题。四项行操作按参照纳入提议；执行默认 FIFO，不按视觉“栈”引入 LIFO。

?????`openspec validate compact-agent-queue-and-direct-interrupt --strict` ???`openspec validate --all --strict --concurrency 3` 26/26????? MODIFIED requirements??? Scenario ????????????????????
