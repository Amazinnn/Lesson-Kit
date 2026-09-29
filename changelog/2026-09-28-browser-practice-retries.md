# 浏览器练习写入可安全重试（2026-09-28）

练习页提交作答和保存 1–5 自评时，先在会话中保存稳定 `request_id` 及原请求。服务端把
首次结果与尝试或评分放入同一 SQLite 事务；响应丢失后的原样重发返回首次结果，改写
同一个请求 id 的内容返回 409。自评继续以 `attempt_id` 指向原作答。

旧题库需运行 `python pool/scripts/migrate-progress.py --db <题库路径>` 添加
`practice_request_operations` 表；原有无请求 id 的调用保持兼容。

回归涵盖尝试、评分、迁移、API 冲突、页面刷新后恢复原请求和收束页重试。真实 ADS 题库未
出现在这个 checkout 中，迁移需在实际工作区执行。
