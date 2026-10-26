## Why

用户已通过七轮独立网页评审，确认深橙到黄到天蓝的像素进度带、斜体连对横幅和归位庆祝卡；现在要求正式接入并合并 main。

## What Changes

- Paper 练习加入像素进度带；进度按已作答／不会状态计算，统一交卷模式按已填写／不会状态计算。
- 客观答对后题目与选项轻弹两次，每五次连对使用定稿横幅和异色波带。
- 仅成功交卷时播放庆祝与彩色礼炮，原卡归位后展示真实逐题结果；历史记录不重播。
- 尊重现有动态偏好、系统减少动态、中栏卸载与页面隐藏；无新增持久字段或接口。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `workbench-ui`: Paper 练习的像素进度、连对和完成展示。

## Impact

只改 workbench/server 的页面壳与静态资源、前端测试和职责文档。不改 Domain/Data、API、schema、真实题库。
