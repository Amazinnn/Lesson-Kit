# Tasks

## 1. Server

- [ ] 1.1 练习页方向 fieldset 收敛为正向/反向两个单选（正向默认），更新辅助文案；删除 ⇄ 按钮标记
- [ ] 1.2 `/pull-cards` 的 `direction_mode` 校验收敛为 `forward | reverse`

## 2. Domain

- [ ] 2.1 `practice_directions` 移除 mixed 分支；`select` 其余行为与方向数据校验不变

## 3. Client

- [ ] 3.1 方向偏好读写全部以 forward 为回退；删除 mixed 引用与 ⇄ 交换处理
- [ ] 3.2 卡片渲染统一为完全重合双牌路径（另一面常驻 DOM、揭示前 `aria-hidden`）
- [ ] 3.3 CSS：揭示编排（上牌逆时针漂移停住、下牌顺时针漂移后下滑全出并轻微倾斜）、删除露边与旧扇开样式、fieldset 两列

## 4. Tests

- [ ] 4.1 更新闪卡 UI 交互用例（方向会话、统一渲染、无交换按钮）
- [ ] 4.2 更新路由断言与域 mixed 用例

## 5. Calendar

- [ ] 5.1 月历去横向滚动：移除 560px 钉死宽度，7 列自适应栏宽

## 6. Validation

- [ ] 6.1 全量基线：pytest / node / openspec strict / compileall / guards
