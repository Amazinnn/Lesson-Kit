## Why

当前逐题提交、只读回看和继续作答使用不同的导航入口。用户希望改成在整张 Paper 内自由前后浏览，浏览本身不代表作答、不会或完成，并在明确提交整张试卷后结束本次 Practice Run。开始页、作答状态展示和完成页需要随之统一，而非只增加一个上一题入口。

## What Changes

已明确的方向（2026-10-19，需求访谈进行中）：

- 题目使用稳定的“上一题 / 下一题 / 不会”导航，首尾边界禁止越界；前后浏览不把题目自动标为不会。
- 显式点击“不会”展示参考答案并标记本题不会；仍未作答的题目在最终提交整张试卷时才按不会处理。
- 保留暂停操作，按钮从“暂停本轮”改为“暂停练习”；删除左下角“本题未提交的内容只保留在当前会话”提示。
- 移除截图中现有的练习模式、自评时机、题量、开始/保存/来源筛选配置块；替代开始流程需继续确认。
- 练习中增加用颜色圆点显示各题作答情况的小面板；其点击导航、状态语义和配色需继续确认。
- 为明确结束的练习设计完成页；统计、历史查看和再次练习入口需继续确认。

尚未确认的选项不构成已批准的行为契约，也不表示功能已实现。

## Capabilities

### New Capabilities

None at this stage; prefer extending existing Paper and practice capabilities.

### Modified Capabilities

- `practice-review`: replace the separation between current answering and read-only earlier-item navigation with the agreed free-navigation behavior.
- `review-workbench`: reconcile when browser answer state becomes a durable Attempt and how explicit whole-Paper submission completes a run.
- `workbench-ui`: replace the practice start configuration, navigation controls, in-progress status display and completion presentation.
- `practice-set-export`: preserve Paper identity and independent per-Paper progress while coordinating the revised start/pause/submit flow.

## Impact

只做开工前设计。保持 Shell → Domain → Data；复用已有 Paper、Practice Run、草稿、Attempt、判定和自评职责，不在本次访谈写代码、迁移或更改真实课程作答记录。现有保存题序、逐题提交、自动完成轮次和不可重写 Attempt 的契约需要明确协调；不得将草稿保存、题目浏览和学习事实混为一体。

## Open Questions

第一轮已确认：题目导航区只保留“上一题 / 下一题 / 不会”，取消每题提交并自动保存输入；“提交试卷”和“暂停练习”属于试卷级操作。开始时可选择逐题显示或交卷后统一显示答案和判定。后者在交卷前允许改答；新答案清除不会标记，但保留看过参考答案的事实。这与原有自评时机的关系仍需协调。

第二轮已确认：逐题模式的单选和判断选定即显示判定，判定、参考答案和解析一并自动展开；第一次显示结果后，本次答案固定，只能查看。文字题默认直接展开参考答案供自行比对，但何时锁定填写仍待澄清。提交试卷直接将空题记为不会，不再二次确认。

第三轮已解决多选判定冲突：逐题模式仅多选题和文字题提供“提交答案”按钮，作为导航三按钮之外的明确例外。多选不再随勾选判定或因离开题目而提交；点击提交才判定、展开答案与解析并锁定。文字题同样有提交按钮，但其参考答案是进入即展开还是提交后展开，仍待第四轮澄清，不把此前默认展开的描述静默解释为任一方案。

逐题模式显式点击“不会”立即展示参考答案，并锁定本题为不会；统一交卷模式保留交卷前改答规则。状态圆点支持点击任意题号跳转；统一交卷前区分未答、已填、不会，不泄露对错；逐题模式增加正确、错误状态，当前题加边框，同时提供文字说明。此处状态描述不代表引入新的持久字段。

- 文字题参考答案展开时机、自评和锁定边界。
- 删除开始配置后，从哪里选择/组装 Paper，如何处理闪卡、自评和原有显式知识点范围。
- 完成后的回看及再次练习入口和统计。
- 正式 Attempt 与本轮可编辑状态的协调属于待设计项。用户此前回答“……”未确认任何写入方案，不再以数据库写入细节作为产品访谈问题。
