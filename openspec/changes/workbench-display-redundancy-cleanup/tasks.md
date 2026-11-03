# tasks — workbench-display-redundancy-cleanup

## 1. 术语与文案权威先行（新名词先定义）

- [x] 1.1 在 `docs/GLOSSARY.md` 建条目「注释型字段（annotation-type field）」，给唯一权威定义
- [x] 1.2 在 component-spec `§3.7` 补「零注释型字段」纪律（含：不复述状态、
      不留 provenance 元信息、不堆「字段名: 值」前缀、组标题不带计数、条目不与组名同字、
      显名不显机器 ID）
- [x] 1.3 在 `copy-table.md` 追加**带日期附录**登记受影响文案词条的去留（不重写 §1/§2 存量行，
      避免与 v2 在途定稿冲突）；A6 收窄为「保留答案/过程语义标签」，详见 design 决策 5

## 2. A 组 — 练习页（冗余注释型字段）

- [x] 2.1 A1：移除 `part-practice.js`「详情」文字按钮 + 孤儿 CSS `.part-details`；把"钉住小问
      状态卡"动作迁到弹卡本身（点卡切 pinned、Esc 解除，键盘可达性靠卡的 tabIndex/role 保留）；
      `.paper-dot` 保持 hover/focus 弹卡，不劫持其点击
- [ ] 2.2 A1 验证：手测 hover / focus / 点击钉住 / reduced-motion 四态，pin 能力未丢
- [x] 2.3 A2：删除 `part-practice.js:35` 解析纸 provenance 行「参考来源 / Agent 独立推导」
- [x] 2.4 A3：`part-practice.js:33` 去掉「（Agent 提炼）」括号注释，保留「你的答案」
- [x] 2.5 A4/A6：统一 `paper-practice.js` 与 `practice-flow.js` 判定口径为自然陈述句去「判定：」前缀
      （「回答正确。」）；A6 收窄——`part-practice.js` 状态串「答案：/过程：」是语义标签，
      依 ADDED「SHALL NOT remove underlying data」**保留不删**（见 design 决策 5 / Open Questions）
- [x] 2.6 A5：去「来源：」硬编码前缀（`paper-practice.js:690`、`practice-flow.js:2194`、
      `pages.py:1138`），证据串保留为自然呈现；来源显隐偏好行为不变（相关测试已同步）

## 3. B 组 — 壳层 / 导航

- [x] 3.1 B1：移除 `workbench.js` 右栏会话条目「provider · 日期 · 运行中」meta 行 + 孤儿 CSS
      `.ai-session-entry-meta`；日期由分组标题承载、运行状态由既有通道承载
- [x] 3.2 B2：移除 `pages.py` 左栏「优先回看」组标题旁计数徽标（含 visually-hidden）+ 孤儿 CSS
      `.count-badge`；既有 2 条断言 count-badge 的测试按新 spec「A group heading carries no figure」更新
- [x] 3.3 B3：`pages.py`「设置」条目改具象名「偏好与主题」（对齐靶子 `shell.html:600`），消除与组名同字
- [x] 3.4 B4：`agent-ui.js` 移除里程碑可见状态文字 + 孤儿 CSS `.agent-milestone-state`；状态走
      marker 几何 + 宿主 `aria-label`（已补 `<label>，<status>`）
- [x] 3.5 B5：去「影响：」「试卷：」字段名前缀、「工件 · 试卷」「需要确认」kicker、工作区卡片
      「工作区/lesson-kit」注释型 eyebrow（保留 `_page_header` 复用面包屑 `.context-line`）；工件卡改显
      「N 题」人读信息不显机器 ID `ps-*`（`artifactMeta` 返 null 已双调用点守卫）+ 孤儿 CSS
      `.agent-surface-kicker`

## 4. 文档与契约同步

- [x] 4.1 `docs/PRODUCT-MANUAL.md` 同步（题号预览句：去「详情」按钮，改「点击预览卡钉住」）
- [x] 4.2 `docs/ACTION-GRAPH.md` 登记退役动作（「详情」入口）+ 本波改级概览
- [ ] 4.3 用 `tools/walkthrough/view.py` 出「靶子 | 改前 | 改后」三列对照板，核对 B 组壳层

## 5. 验证

- [x] 5.1 仓库级检查：`python -m pytest tests -q`（1315 passed）、`python -m compileall -q lessonkit.py workbench pipeline pool tests`
- [x] 5.2 `openspec validate --specs --strict`（21/21 passed）、`openspec validate <change> --strict`（valid）
- [ ] 5.3 渲染后逐项核对 specs delta 两条 Requirement 的每个 Scenario 均成立
      （题号格无多余标签、解析纸无 provenance、判定/来源无字段名前缀、会话无 meta 行、
      组标题无计数、设置条目具象名、卡片无 kicker/机器 ID、状态仅几何+aria-label）
- [ ] 5.4 屏幕阅读器/焦点遍历复核：移除可见状态文字后各状态仍可被宣告
