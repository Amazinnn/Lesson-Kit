## Why

已经批准的显示偏好提交尚未合并，来源默认值与当前题重新开启自评/来源的行为尚未兑现。计算机组成还存在清题后未同步清理的旧执行引用，需要按用户新指示做一次题目级数据清理。

## What Changes

- 题目来源默认隐藏，保留显式偏好；来源和普通 Paper 自评在当前题即时双向显隐。
- 同步左栏、设置页以及同工作区标签页的开关值。
- 将设置提交 rebase、验证后合入 main 并更新 3081；计算机组成清理不存在题目的引用，保留试卷容器，旧答案不绑定到替换题。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `workbench-ui`: 显示偏好在当前普通 Paper 即时生效；来源默认隐藏。

## Impact

浏览器显示逻辑、现行 workbench-ui 规格和受影响的在途 delta、产品手册、动作图及交接记录。无 schema、后端接口或 frozen-layer 行为改动。数据清理使用现有 Data 读写边界，单独备份与审计。
