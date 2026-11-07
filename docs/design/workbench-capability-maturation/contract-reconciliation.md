# 契约协调清单

状态为规划差异登记。实施者逐项写实际解决提交与证据，未协调项阻止受影响行为上线。

| 编号 | 当前契约或事实 | 批准目标 | 负责包与必须同步的文件 |
|---|---|---|---|
| CR01 | authored mirror 仅部分实体，figure 独立，版本不一致可能拒绝 | 全课程受管理内容与学习状态、文件 CRUD、单侧自动协调 | WP01；file-course-sync delta、DATA_MODEL、FILE_CONTRACT、手册、ACTION-GRAPH、surface |
| CR02 | Paper 与作答/草稿分散存储，序号可能本机分配 | 跨设备新增事实并集、同卷按题合并 | WP01；Attempt/执行身份映射、旧数据库兼容及文件版本矩阵 |
| CR03 | 浏览器偏好不在 SQLite | 非敏感偏好可保存为课程资产并被接收端消费 | WP01；设置 API/浏览器 writer、FILE_CONTRACT、DATA_MODEL、设置 spec |
| CR04 | goals.json 与 plan.json 分离，list_goals 读错返回空 | 目标作为权威课程数据，损坏须报告，缓存按输入失效 | WP01；goals 消费者、目标/计划规范；不能把读错当删除 |
| CR05 | ingest 整批零写入、成功批次可撤销 | 独立有效单元先完成，显式成功批次撤销退役 | WP02，WP01 局部复用；governance、flash-card、micro-quiz、knowledge-figures、Bridge、手册、工件 |
| CR06 | 改卷审批、回滚审批、审批暂停派发 | 原审批默认直接通过，重做和准备后切换无额外批准 | WP03；workbench-ui、Bridge、practice-set-export、提示词、HTTP、会话旧状态、手册 |
| CR07 | 接受排队消息仅队列，失败候选位于输入框上方，队列有排序/立即发送 | 消息长期在对话流，失败不自动入重试，队列仅正文/编辑/删除 | WP04；workbench-ui、Bridge submission 契约、浏览器持久恢复 |
| CR08 | 草稿已有执行和本地出站箱，入口未完整验收 | 未提交试卷无限保留，开始页继续/清除本次进度 | WP05；练习生命周期、DATA_MODEL、动作图、迟到写入规则 |
| CR09 | 标题存在 textContent 及渲染后回读 | 标题 Markdown/LaTeX 且原文保真 | WP05；UI 字段清单、富文本安全、编辑和重命名读取 |
| CR10 | knowledge_type 可缺失，chapter 不在普通可编辑字段内，ID 含章号 | 分类查询、范围内补齐、同课程章节迁移保留记录 | WP02；GLOSSARY、DATA_MODEL、ID/章节归属区分、所有消费者 |
| CR11 | Domain 零 IO 与部分实现/依赖方向不一致 | 被命中规则移入纯规则边界，SQLite 与 IO 归 Data/外层 | 对应包；ARCHITECTURE 实际依赖与测试，不做无关全仓重构 |
| CR12 | 教学分支状态与主检出不同，研究文档不等于接线 | 复用已有教学状态/策略，原始证据与教学判断分离 | WP06；实际分支差异、调用跟踪、接口及 evidence writer/consumer |
| CR13 | V3.1 有默认展示、确认卡、宿主降级和五种掌握词 | 最小展示、无审批、无未批准 fallback，沿用持久语义 | WP01/WP06；协议对照和 Agent 契约；不直接添加状态枚举 |
| CR15 | figure gate 存量规范要求哈希命名，与项目禁止哈希冲突 | 新入口可读顺序命名及源字节核对；旧名称作为不透明路径兼容 | WP02；knowledge-figures delta、FILE_CONTRACT、所有命中 writer，禁止新哈希计算 |
| CR14 | 活跃 change 可能已部分实现但未验收 | 以分支/代码/运行身份核对重叠，再协调 delta | 所有包；json-content-repository-sync、adaptive-paper-content-lifecycle、agent-chat-simplify、显示/渲染及运行 change |

## 解决步骤

复制职责文件的完整相关条款，记录当前可观察行为、批准替代决定、仍保留场景及退出入口。MODIFIED delta 保留所有既有场景名称并更新其结果，退役操作用 REMOVED 和明确迁移说明。跨 change 修改同一 requirement 时按实施依赖合并最新基线后重生成 delta，禁止覆盖先前包的场景。

实施首任务包含实际能力/文件清单，冻结当前 schema 与接口快照。当前规划新增 delta 表达新增能力及目标，涉及 live requirement 的兼容修订必须与代码同 PR 完成。任何遗漏的现行禁止/审批/原子性条款必须在 CR 编号下补齐，不能凭新增 spec 静默压过旧条款。

## WP01 实施协调记录（2026-11-07，未结案）

CR01/CR02：接收先写sidecar再提交SQLite的确认错误已改为同事务的增量单元记录，文件使用可恢复发布意图；并发本地修改受到检查版本保护。新增职责记录见DATA_MODEL/FILE_CONTRACT/ARCHITECTURE及本change设计，证据为2026-11-07-04。可读Git文件的收发、冲突不发布、旧交换文件删除暂存已补回归。

附件A→B→C及显式删除再传播已由9e24990c补齐回归；完整规模700文件逐字节一致。尚未结案：嵌套整数引用与请求缓存（R02）、导出及无变化检查F2性能、原生任务完整配置课验证、真实远端/浏览器验收，以及真实Tutor回写发现的新增文件遗漏。当前不得宣称完整课程交换已闭合。

CR01 followup2026-11-07: real free-model Tutor return exposed a new-file gap: FILE_CONTRACT restricted undeclared readable files even though Q006/Q106 require course-file additions. WP01 now specifies explicit creation by a new safe file under files/, preserving absence protection and invalid-envelope isolation. Implementation and replay acceptance pending.
