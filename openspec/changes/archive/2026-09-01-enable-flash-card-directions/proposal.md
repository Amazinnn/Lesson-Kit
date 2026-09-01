# enable-flash-card-directions 提案

## Why

现有闪卡只按 front → back 使用，但真实内容有两类：定义、解释等只能单向提问；词汇等内容正反两向都具有教学意义。方向调度复合键早已存在，内容层却没有声明“这张卡允许哪些方向”，拉取也仍把整张卡当作一个动作。

## What Changes

- flash-card manifest 增可选 `directions`，仅接受 `["forward"]` 或 `["forward", "reverse"]`；缺省兼容为单向。
- `flash_cards` 增量保存方向能力，不复制内容卡。
- `/pull-cards` 接受 forward / reverse / mixed 方向偏好，返回具体练习方向；双向卡的两个方向成为不同候选，单向卡始终只产生 forward。
- 拉取按 `(card_id, direction)` 的真实调度行分别做“到期优先”，并接受已见方向键排除；既有 `exclude_ids` 继续兼容。
- 卡片评分继续复用既有 `feedback.direction` 与 `review_schedule` 复合键，不新增调度表。

## Capabilities

### Modified Capabilities

- `flash-card`：内容契约与拉取支持单向/双向能力。

## Impact

增量迁移仅涉及 `pool_schema.py` 的 ensure 模式；Domain 只做字段规则，Data 解析存储值，Shell 只校验请求并编排。旧 manifest、旧卡片与旧拉取调用保持 forward 行为。
