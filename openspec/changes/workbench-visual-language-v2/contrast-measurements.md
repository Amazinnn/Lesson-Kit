# 对比度复测表（暖奶油 / 夜纸）

> 产物：`workbench-visual-language-v2` 的 **tasks.md 12.3「对比度复测并出表」**。
> 这张表是**可复跑**的：脚本在 `tools/verify_tokens.py`，本文的每个数字都由它
> 从 `workbench/server/static/workbench.css` 的**实际取值**重算得到，不是手抄的。
>
> **复跑命令**（仓库根目录执行）：
> ```bash
> python tools/verify_tokens.py                          # 默认读仓库内那份 workbench.css
> python tools/verify_tokens.py workbench/server/static/workbench.css   # 显式指定
> ```
> **退出码**：`0` 全部适用配对达标 · `1` 存在低于判定线的配对（可接进 CI 闸门）·
> `2` 脚本自身出错（读不到文件 / 解析不出取值块）。
> 纯标准库（WCAG 2.x 相对亮度公式），无第三方依赖。
>
> **判定线**（权威表 §4.1）：正文 / 次要文字 ≥ 4.5:1 · 三级文字、控件边界与非文本状态标记 ≥ 3:1 ·
> 大字号 ≥ 3:1 · 黄色**面积档**不承载文字，无对比度要求。
>
> **权威出处**：`design-notes/night-paper-tokens.md` §3（值表）/ §4.1（公式）/ §4.2（浅色配对）/
> §4.3（夜纸配对）/ §4.4（不达标项与修正值）。

---

## 0. 夜纸值集核对（tasks.md 12.1）

| 项 | 结果 |
|---|---|
| 权威值 token 数 | **52** |
| 缺失 | **0** |
| 与权威表不一致 | **0** |
| `:root` 值 token 数 / 夜纸块值 token 数 | 156 / 52 |

⇒ 夜纸是**同一套三角色的第二套值**，不是新色系；表面 4 层 + 代码面 + 墨阶 8 个 +
规则线 3 个 + 角色色 11 个 + 面纱 3 个 + 抬升 3 个 + 焦点 5 个 + 骨架 2 个 +
插画 6 个 + 热力 4 个 + UA 1 个，两主题都有值。

---

## 1. 对比度复测表（43 组配对 × 2 主题）

| 配对 | 判定线 | 浅色 | 夜纸 | 浅色结论 | 夜纸结论 |
|---|---|---|---|---|---|
| ink-strong / surface-base | 4.5 | 15.52:1 | 14.92:1 | PASS | PASS |
| ink-strong / surface-card | 4.5 | 16.14:1 | 13.96:1 | PASS | PASS |
| ink-strong / surface-raised | 4.5 | 16.42:1 | 12.88:1 | PASS | PASS |
| ink-body / surface-base | 4.5 | 11.30:1 | 13.12:1 | PASS | PASS |
| ink-body / surface-card | 4.5 | 11.75:1 | 12.28:1 | PASS | PASS |
| ink-body / surface-raised | 4.5 | 11.96:1 | 11.32:1 | PASS | PASS |
| ink-strong / surface-sunken | 4.5 | 13.97:1 | 13.45:1 | PASS | PASS |
| ink-body / surface-sunken | 4.5 | 10.17:1 | 11.83:1 | PASS | PASS |
| ink-muted / surface-sunken | 4.5 | 4.97:1 | 7.98:1 | PASS | PASS |
| ink-faint / surface-sunken | 3.0 | 3.10:1 | 4.79:1 | PASS | PASS |
| ink-body / surface-code　※不适用 | 4.5 | 1.37:1 | 14.12:1 | **不适用** | **不适用** |
| ink-inverse / surface-code | 4.5 | 16.14:1 | 16.06:1 | PASS | PASS |
| ink-muted / surface-base | 4.5 | 5.53:1 | 8.85:1 | PASS | PASS |
| ink-muted / surface-card | 4.5 | 5.75:1 | 8.28:1 | PASS | PASS |
| ink-faint / surface-base | 3.0 | 3.45:1 | 5.31:1 | PASS | PASS |
| ink-faint / surface-card | 3.0 | 3.59:1 | 4.97:1 | PASS | PASS |
| ink-faint / surface-raised | 3.0 | 3.65:1 | 4.58:1 | PASS | PASS |
| ink-disabled / surface-base | 3.0 | 3.59:1 | 3.61:1 | PASS | PASS |
| ink-disabled / surface-card | 3.0 | 3.73:1 | 3.38:1 | PASS | PASS |
| ink-disabled / surface-raised | 3.0 | 3.80:1 | 3.12:1 | PASS | PASS |
| role-blue / surface-base | 4.5 | 4.94:1 | 5.64:1 | PASS | PASS |
| role-blue / surface-card | 4.5 | 5.14:1 | 5.28:1 | PASS | PASS |
| role-blue / surface-raised | 4.5 | 5.23:1 | 4.87:1 | PASS | PASS |
| role-blue / role-blue-wash | 4.5 | 4.60:1 | 4.72:1 | PASS | PASS |
| ink-on-role / role-blue | 4.5 | 5.14:1 | 6.07:1 | PASS | PASS |
| ink-on-role / role-blue-press | 4.5 | 6.94:1 | 8.02:1 | PASS | PASS |
| ink-on-warm / role-yellow | 4.5 | 10.07:1 | 10.61:1 | PASS | PASS |
| role-yellow-deep / surface-base | 3.0 | 4.79:1 | 12.41:1 | PASS | PASS |
| role-yellow-deep / surface-card | 3.0 | 4.98:1 | 11.61:1 | PASS | PASS |
| role-yellow / surface-base　※面积档 | — | 1.54:1 | 9.86:1 | PASS（面积档） | PASS（面积档） |
| role-red / surface-base | 3.0 | 4.58:1 | 5.35:1 | PASS | PASS |
| role-red / surface-card | 3.0 | 4.77:1 | 5.00:1 | PASS | PASS |
| role-red-ink / surface-base | 4.5 | 5.62:1 | 6.59:1 | PASS | PASS |
| role-red-ink / surface-card | 4.5 | 5.85:1 | 6.16:1 | PASS | PASS |
| role-red-ink / role-red-wash | 4.5 | 5.03:1 | 5.39:1 | PASS | PASS |
| rule-control / surface-card | 3.0 | 4.44:1 | 3.48:1 | PASS | PASS |
| rule-control / surface-base | 3.0 | 4.27:1 | 3.72:1 | PASS | PASS |
| rule-control / surface-raised | 3.0 | 4.52:1 | 3.21:1 | PASS | PASS |
| rule-structure / surface-card | 3.0 | 16.14:1 | 12.77:1 | PASS | PASS |
| focus-outer / surface-card | 3.0 | 5.14:1 | 8.57:1 | PASS | PASS |
| focus-outer / surface-base | 3.0 | 4.94:1 | 9.16:1 | PASS | PASS |
| focus-inner / role-blue | 3.0 | 5.14:1 | 6.07:1 | PASS | PASS |
| art-ink / art-paper | 3.0 | 14.78:1 | 12.06:1 | PASS | PASS |

**低于判定线的配对：0 项**（两主题各 0）。
**不适用配对：1 项** —— `ink-body / surface-code`：权威表 §4.4-11 规定「代码面上的文字
一律用 `--ink-inverse`」，该配对本身不成立；浅色主题的 1.37:1 是**设计上的反白面**，
不是可读性缺陷。实现侧已把全站唯一用到 `--surface-code` 的 `.ai-plan-output pre`
的文字显式改成 `--ink-inverse`（浅 16.14:1 / 夜 16.06:1）。

---

## 2. 逐项判定说明

| 项 | 结论 | 依据 |
|---|---|---|
| 正文 ≥ 4.5:1 | **全部通过**（`--ink-body` / `--ink-strong` 族：浅色最低 **10.17:1**，夜纸最低 **11.32:1**） | 上表 |
| 次要文字 ≥ 4.5:1 | **全部通过**（`--ink-muted` / `--role-blue` / `--role-red-ink` 族：浅色最低 **4.60:1**、夜纸最低 **4.72:1**，两处都是「蓝字 / 蓝洗底」这一对） | 上表 |
| 三级文字 `--ink-faint` ≥ 3:1 | **通过**（浅 3.45:1 / 夜 5.31:1）；⚠️ 浅色只有 3.45 ⇒ **只用于非阅读性的弱化信息**（元信息 / 占位符 / 禁用态），**不得承载需要阅读的句子** | 权威表 §3.2【A-20-4】 |
| 控件边界 `--rule-control` ≥ 3:1 | **通过**（浅 4.27:1 / 夜 3.21:1） | 上表 |
| 非文本状态标记 ≥ 3:1 | **通过**（黄标记档 4.79:1 / 12.41:1；红 4.58:1 / 5.35:1） | 上表 |
| 焦点环 ≥ 3:1 | **通过**（外圈 4.94:1 / 9.16:1；内圈 5.14:1 / 6.07:1） | 上表 |
| 黄色填充 | 两主题都**只承载面积与形状**（`role-yellow` 1.54:1 / 9.86:1 是面积档，无对比度要求）；承载文字一律走标记档 `--role-yellow-deep`（4.79:1 / 12.41:1） | 权威表 §3.4 |
| 沉底层上的墨阶 | **通过**（标题墨 13.97:1 / 13.45:1；正文墨 10.17:1 / 11.83:1；次要 4.97:1 / 7.98:1；三级 3.10:1 / 4.79:1） | 权威表 §4.2 / §4.3 |

## 3. 与权威表 §4.4 的 11 项不达标项的关系

权威表 §4.4 记录的 11 项是**值表起草过程中**实测到并已修正的项，修正值即本表所用的取值
（`--ink-disabled` 浅 `#8a8275` / 夜 `#7a7162`；`--role-blue-wash` 浅 `#f2f0ef` / 夜 `#292929`；
`--role-red-ink` 浅 `#b8331f` / 夜 `#e08878`；`--rule-control` 浅 `#847552` / 夜 `#7d7361`；
黄色状态点改用 `--role-yellow-deep`；焦点环改双环）。
本表复测的是**修正之后**的取值 ⇒ 11 项全部复算通过，与本表的 0 项不达标一致。
