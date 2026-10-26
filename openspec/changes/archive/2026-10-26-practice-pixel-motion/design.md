## Context

第七版独立试样为视觉定稿；不把模拟题、模拟记录或试样控制台带入产品。现有 Paper controller 提供状态、逐题确认与归档结果；共用 streak 继续拥有连对计数。

## Decisions

- 新增 practice-motion.js / practice-motion.css，浏览器原生 Canvas/SVG 与单一 RAF，零依赖。纯色阶／密度函数可由 Node 检查。
- Paper controller 只向动效传递现有 itemStatus 汇总、确认答对事件和成功交卷事件；显示层不发请求、不落库。
- Paper 内旧 combo 横幅和旧完成装饰让位给定稿；快速练习等其他表面保留既有行为。
- 保留完成页全部真实统计、原有按钮与回看入口，将逐题按钮改为可读结果列表。卡片与结果同一 DOM，无模态焦点陷阱。
- 完成礼炮适用于本次成功交卷，不再使用旧 Paper 仅里程碑礼炮规则；不推断首次章节完成，不新增音效语义。
- 持久字段、CLI/API、manifest 无变化；DATA_MODEL 与 FILE_CONTRACT 无需修改。

## Validation

先加入纯规则与 controller 确认事件测试，再接入；Node suites 归入 pytest。隔离课程池实际 HTTP/浏览器验证答题、交卷、回看、卸载和减少动态，不触碰真实题库。运行仓库四项检查，独立代码审查后提交并合并 main。
