# consolidate-practice-views 设计

## D1 一个「真正要练的」清单：准备练习列表 = 选区视图

视图收敛的判据：练习之前，无论来自计划还是到期调度，都不是真正要练的；
**只有用户显式选定的才是**。因此练习页只有一张「准备练习」列表：

- 列表 = 当前知识点选区（`wb_kp_selection_{ws}`）直接渲染，行 = 知识点名 +
  清除动作，别无他物；清除 = 取消勾选，与知识点页/图谱勾选双向实时同步；
- 零新存储、零 schema 变化：列表是选区的另一个视图，不是新实体；
- 模式选择（综合/闪卡/判断 + 自评时机）与「开始练习」按钮行为不变，
  选区为空时保持禁用（禁用态样式顺手修复，见 D6）。

## D2 候选按需拉取（计划 ∪ 到期 → 一行一短语）

计划队列与到期调度都是「建议」：按需拉取、绝不常驻。

- 入口：「＋ 加今天要练的（N）」按钮，N = 当前候选数（已选定的知识点
  不计入）；点开才展开候选行，再点收起；
- 行 = `知识点名 · 一个短语 · 加入`；**字段极简是硬约束**——无徽标、
  无日期、无数字、无第二短语；
- 来源与去重：计划队列 ∪ 到期行（`queries.review_overview`），映射到
  知识点级去重；同一知识点同时命中计划与到期时只留一个短语，
  到期短语优先于计划短语；
- 短语表（纯函数，零调度参数外露）：到期逾期 N 天 → `拖了 N 天`；
  今天到期 → `今天到期`；仅计划命中 → 沿用既有计划原因文案（如
  `覆盖仍低`）。取一，不拼接；
- 「加入」= 写入知识点选区（与显式勾选同一条路径），加入后该行从候选
  消失、N 减一；「重算计划」按钮保留在候选区头部；
- 上限：候选行最多渲染 20 行 + 「还有 N 条」；
- 空态：候选为空 → 一句话「今天没有建议」；准备列表为空 → 一句话 +
  一个动作（展开候选 / 去知识点页挑一个）。

## D3 时间安排并列布局

练习页顶部两栏：左 = 学习安排（目标卡 + 准备练习区块），右 = 时间安排
（月历 + 柱状图，宽约 300px）；`@media (max-width: 1023px)` 纵向堆叠。
既有 `.plan-columns` 网格扩展。`/calendar` 端点与渲染逻辑从复习页原样
搬移，不改行为。

## D4 方向卡 UI 全拆（无替代 UI）

所有者确认：真实池中尚无方向调度行，且不需要系统「导向会话」——会话由
用户自己开启。因此提示条、原地卡片流、1–5 评分卡、`start-card-review`
入口全部移除，**不迁移、不留被动入口**。保留的是数据与 API：每方向
独立调度键、`feedback.direction`、`/due` 的 direction 字段。卡片类 UI
待真实使用出现后再议（归档时记 FUTURE-NOTES）。

## D5 移除清单与保留清单

**移除**：`review` 导航项、`_send_page` review 分支、`review_page`、
`card_session_html`、到期日期分组列表、复习页时间区块、`start-card-review`
入口、`workbench.js` 复习页与卡片会话整段、复习页专属 CSS、`pages.py` 中
成对重复的第一套死函数定义（`practice_page`/`_daily_plan`/`kps_page`/
`graph_page` 的前者）。
**保留**：`queries.review_overview`（候选数据源 + 每日规划参考）、`/calendar`、
`pull.include_ids`、`feedback.direction`、micro quiz 全部、徽标/水位等
将复用的通用 CSS。
**搬移**：`time_view_html` 及其 JS 渲染逻辑原样进练习页右栏。

## D6 规格处置与顺手修复

- `review-page` capability 标注 Deprecated（Purpose 顶部声明）；
- include 过滤与方向调度键收编为 review-workbench 的 ADDED 需求；
- 「Directional card practice for memory recall」REMOVED（MODIFIED 语义
  不允许丢场景），代之以 ADDED「Directional schedule entries」：仅调度
  语义——每方向独立调度键、互不推进、不提供卡片页或系统导向会话；
- 三页导航恢复后，`workbench-ui` Purpose 段在归档时同步改写（tasks 列出）；
- 顺手修复：练习页主按钮禁用态样式（既有 UX 清单项，仅用既有令牌）。
