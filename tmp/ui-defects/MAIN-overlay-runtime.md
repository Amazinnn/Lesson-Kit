# 主会话浮层/遮罩「运行时实测」发现（Playwright elementFromPoint + computedStyle）

> 采集人：主会话（唯一浏览器）· 页面 `http://127.0.0.1:3081/w/lesson-kit/practice`（夜间主题）
> 方法：对每个可点元素取中心点 `document.elementFromPoint`，命中非自身/子孙 ⇒ 被遮挡；+ 浮层 `computedStyle`（position/z-index/overflow/transform）+ 祖先链层叠上下文 + 全页 z-index 分布。
> 与 G（静态遮罩/关闭通道）、H（静态 z-index/stacking）互补：本文件是**运行时确证**，G/H 是源码推导。

---

## N-01 · 章节透镜面板被 `main` 遮挡（浮层被遮，实锤）

- 严重度: 高
- 类型: 浮层被遮（层叠上下文未建立）
- 证据: 章透镜面板 `.chapter-lens` 实测 `position: relative; z-index: auto`（未建 stacking context）；面板内 **ch06 选项按钮中心点 `elementFromPoint` 命中 `main`**（而非按钮/子孙）⇒ 按钮被 `main` 盖住。实测 `hasBackdrop:false`、面板无 `role`/`aria-hidden`。
- 为什么是缺陷: 浮层未提升层叠层级（z-index auto + position relative 不建上下文），被后出现/同层更高层的 `main` 遮挡 ⇒ 选项点不到/显示不全。这正是所有者说的「浮窗被遮罩」。
- 建议方向: 给透镜面板建独立 stacking context 并给足 z-index（高于 main）；补 `role`/`aria`。
- 运行时确证: 是（elementFromPoint）

## N-02 · part-preview 浮层位于 `overflow:auto` 容器内，可被裁切

- 严重度: 中
- 类型: 浮层被裁（overflow 裁切）
- 证据: `.part-preview-wrap` 的祖先链中 `.paper-dots` 为 `position:static; overflow:auto`；浮层在其内 ⇒ 浮层超出 `.paper-dots` 可视区的部分会被该滚动容器裁掉。
- 为什么是缺陷: 浮层被 overflow:auto 祖先裁切 ⇒ 多小问时预览卡内容可能显示不全/被截断，需滚动才能看全（浮层本应完整浮在上方）。
- 建议方向: 预览浮层改用 fixed 定位 + 传送到 body 层（脱离 overflow 祖先），或给足空间避免裁切。
- 运行时确证: 是（祖先链 overflow:auto 实测）

## N-03 · part-preview 浮层无关闭按钮，只能 Esc 关闭（关闭通道单一）

- 严重度: 中
- 类型: 关闭通道单一
- 证据: `.part-preview` 实测 `closeChannel: 无关闭按钮`、`escOnly: true`（无 `[aria-label*=关闭]`/`[class*=close]`），仅靠 Escape；且无点击外部关闭。
- 为什么是缺陷: 触屏/鼠标用户无 Esc 概念，浮层只能靠 Esc 关 ⇒ 关闭通道单一，操作不便（与 C-15 同源，此处为运行时确证 + 明确「无关闭按钮」）。
- 建议方向: 补点击外部关闭 + （可选）显式关闭按钮；统一关闭通道。
- 运行时确证: 是

## N-04 · 全站 z-index 值分布混乱，含 9999 magic number

- 严重度: 中
- 类型: z-index 无统一口径
- 证据: 运行时统计当前页 `z-index` 值分布：`0×7, 1×4, 5×2, 9×2, 10×2, 30×6, 50×1, 51×1, 100×2, 9999×1`。散落 0~9999 共 10 种值，无统一阶梯。
- 为什么是缺陷: z-index 无 token 化阶梯、含 9999 magic number ⇒ 浮层层叠关系靠人肉试，极易出现「浮层被遮/互相盖」的回归（N-01 即此根因的实例）。
- 建议方向: 建 z-index token 阶梯（如 overlay/toast/modal 各一档），消灭 magic number。
- 运行时确证: 是（computedStyle 全页统计）

## N-05 · 浮层普遍 `position:relative + z-index:auto`，未建立层叠上下文（根因）

- 严重度: 中
- 类型: 层叠上下文根因
- 证据: `.chapter-lens`（N-01）与 `.part-preview-wrap`（N-02）实测均为 `position: relative; z-index: auto`；`.part-preview` 祖先仅一处 `relative + z-index:1`，其余 static/auto。
- 为什么是缺陷: 浮层容器普遍用 relative+auto，不建 stacking context 也不抬层级 ⇒ 是否被遮取决于 DOM 顺序与邻近元素，脆弱、易被遮（N-01 实例）。
- 建议方向: 浮层容器统一用「建上下文 + 明确 z-index 档位」的浮层基类。
- 运行时确证: 是

---

## 统计
主会话浮层/遮罩运行时确证：**N-01（高）+ N-02/N-03/N-04/N-05（中）共 5 条**（N-01/N-02/N-03/N-05 均为「浮窗被遮罩/被裁/关闭单一」的运行时实锤；N-04 为 z-index 无口径根因）。
注：G/H agent 做静态全量清点，本文件只收**运行时实点确认**的浮层缺陷，二者互补；M-03（lk-switch track 拦截）与 C-15（part-preview Esc）为已知项，N-03 为其运行时确证扩展。
