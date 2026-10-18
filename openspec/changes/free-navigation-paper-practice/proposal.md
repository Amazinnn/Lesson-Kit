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

用户对正式记录写入时机的回答“……”不视为确认。下列问题中涉及已确认的部分以上段为准；逐题判定触发、解析展开、逐题模式改答及空题交卷确认仍待第二轮回答。

- 三按钮是否只约束题目导航区；逐题提交是否退役，以及试卷提交/暂停的固定位置。
- 客观判定的展示时机，以及主观题和无答案键题的呈现。
- “不会”先只改变本轮状态，还是立即创建正式 Attempt；交卷前是否允许改答以及如何处理已看过参考答案的事实。
- 删除开始配置后，从哪里选择/组装 Paper，如何处理闪卡、自评和原有显式知识点范围。
- 状态圆点的含义、跳题行为、提交剩余空题的确认、完成后的回看及再次练习。
