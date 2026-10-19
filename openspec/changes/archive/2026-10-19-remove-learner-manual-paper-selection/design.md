## Context

用户已确认：学生侧所有选题/筛选/组卷控件移除，由 Agent 组卷，页面只管理和练习已有试卷；Agent/CLI 能力保留。现行规范仅禁止逐题手选，却明确允许条件组卷、建议动作与跨页范围托盘；这些许可需正式替换，不声称逐题 picker 必然仍存在。

只读源码证据：`workbench/server/pages.py` 目前包含 scope-tray、practice-mode-choice、practice-rating-choice、start-practice、filter-launch、staged-list 和 suggestion-join；`workbench.js` 绑定范围托盘和相关动作。实现时以当前 main 再定位，不把本设计行号当稳定接口。

## Goals / Non-Goals

清除所有学生可操作的选题组卷路径，包括 Paper 名单/顺序编辑；保留已有 Paper 的阅读、改名、导出、删除容器与开始/继续。清理不改课程内容或历史数据，不移除题目阅读、知识图谱的阅读筛选/搜索/聚焦、章节镜头、Agent/CLI authoring 或相关只读 API。

## Decisions

删除模板入口及其专属绑定，不只是 CSS 隐藏；移除或停用仅为这些入口存在的浏览器状态恢复，旧 localStorage 选区不能再隐式组卷。不为清理添加新持久化或通用迁移框架。

组卷后端、筛选算法、精确题号、save 与已有进度重置审批均保留，Agent 的明确修改仍执行原审批。现有 Paper 题目预览保留，reorder/remove 单题控件移除；删除整卷仍只删除容器，沿用已有记录保留行为。改名/导出不变成重新组卷。

Practice page 的旧 setup block 与自由导航 change 有重叠：本 change 负责禁止学生组卷及跨页渠道，另一 change 负责新开始选项与练习流程。两者可分派，但修改同一模板时须协调；不能以合并顺序恢复旧控件。闪卡作答本身不改，任何旧学生组卷入口也不能以闪卡为名保留。

## Contract reconciliation

- workbench-ui：替换 Practice page，退役 suggestions assembly 与 scope tray；同步 saved Paper 预览和折叠卡上的手动改题控件描述。
- review-workbench：退役 source-filter panel；将组卷引擎、相似题后续组卷和 chapter lens 场景限定为 Agent/CLI authoring，保留过滤语义与只读端点。
- practice-set-export：Paper 执行边界不变，知识点组卷入口改为 Agent/CLI 请求。
- GLOSSARY：实现时协调 Scope/Suggestion 的学生界面描述，不删除 Agent 组卷概念。
- PRODUCT-MANUAL/ACTION-GRAPH：同一实现 PR 删除旧学生操作说明并登记动作退役，保留 Agent/CLI 作者动作。
- DATA_MODEL/FILE_CONTRACT：没有持久字段或工件变化则不机械修改；如实现触及接口归属，同步实际 surface。

## Verification

使用已有渲染/JS 测试核对四个页面无选题、条件组卷、名单/顺序编辑入口；读图筛选与题目预览正常。再验证 Agent/CLI 原有组卷与保存的确定性用例仍通过。用测试库做一次页面巡检，不操作真实课程数据；不增加繁重的额外审批或验证平台。

## Open Questions

无待确认产品问题。仅实现定位与移除死绑定属于执行工作。
