# STATUS — 本会话（组件形态 / 动效 / 文案 / 走查工具）的交接 + 与 V1 线的对齐

> ## ⚠️ 先看这一段：**本工作现在有两条线，交接文档有三份**
>
> | 文档 | 讲的是哪条线 | 时点 |
> |---|---|---|
> | **`openspec/changes/workbench-v1-baseline-convergence/HANDOFF.md`** ⭐ | **V1 收敛线**（把产品收到 V1 样板图基线）—— **下一会话先读它** | 2026-10-23 |
> | `openspec/changes/workbench-visual-language-v2/HANDOFF.md` | 两条 change 的**范围与操作入口**（旧） | 2026-10-22 |
> | **本文件** | **本会话那条线**（组件形态 / 动效 / 文案 / 走查工具）的成果与遗留，**以及与 V1 线的对齐** | 2026-10-23 |
>
> ⇒ **下一会话的起手顺序**：① 读 V1 线的 HANDOFF → ② 读 `VERSION-V1.md` +
> `design-notes/mockup-baseline/README.md` → ③ 读 `decisions.md` 的 **A-142 / A-143 / A-144**
> → ④ 需要本会话那条线的细节时再读本文件。
>
> ⚠️ **本文件已被另一条线超越的部分，见 §2「已作废的我说过的话」。**

---

## 1. 仓库状态（**2026-10-24 07:45 实测**）

| 项 | 值 |
|---|---|
| 分支 | `feat/workbench-visual-language-v2` |
| HEAD | `bcd3542c`（本会话最后一条提交） |
| `main` | **`fcde1897`** = `merge: 工作台视觉重做（含 V1 基线）进 main` ⇒ **视觉重做已经合并进 main 了** |
| 本分支 vs main | **ahead 10 / behind 0**（另那条线已把主体并入 main） |
| tag | **`v1-mockup-baseline`**（V1 正式基线版本，A-144） |
| 分支归档 | **28 个**已并入 main 的残留分支已归档（`docs/BRANCH-ARCHIVE.md`）；**18 个还有独有未合并提交的分支保留** |
| ⚠️ **工作区** | **不干净**：`workbench/server/static/workbench.css` 有 **15 行未提交改动** —— **那是另一条线的 agent 正在做的活**（抽屉层叠修复），**不是脏数据，别回退** |
| push | **不 push**（所有者指示） |

---

## 2. 与 V1 线的对齐（**我这条线被超越的地方**）

### 2.1 基线换了

| | 我这会话的说法 | **现在的权威** |
|---|---|---|
| 版式的实现目标 | `design-notes/layout-spec.md`（**A-135**） | ⭐ **V1 样板图基线** `design-notes/mockup-baseline/v1.html`（**A-142 / A-143 / A-144**） |
| 样板图在哪 | `tmp/frontend-audit/mockups/`（**不入库、会丢**） | **已提升入库** `design-notes/mockup-baseline/`（8 个源码文件） |
| 组件样式一览 | `tmp/frontend-audit/styleboard-v2/` | **已提升入库** `design-notes/component-versions/styleboard-v2/`（旧方向在 `styleboard-v1-legacy/`） |
| 数值以谁为准 | —— | **A-143 ⭐「靶子优先」：连数值也以靶子为准**（A-142 的「数值以规格为准」**作废**）。所有者原话：「**改后的就是垃圾。样板图就是最理想的。**」 |

⇒ **我的 A-135 已被 A-142 / A-143 取代。**
`layout-spec.md` **没有作废**，但降级为**只读参考**（V1 线只读它的 §2 顶栏 / §3 左栏 / §6 右栏）。

### 2.2 已作废的我说过的话（**别再引用**）

| 我的说法 | 处置 |
|---|---|
| 「下一波：照 `layout-spec.md` 实现版式」 | ❌ **作废** —— 下一波是 **V1 收敛 change 的 tasks 第 2–5 组** |
| 「`layout-spec.md` 是版式的唯一权威」 | ❌ **降级**为只读参考；权威是 **V1 靶子**（A-143） |
| 「早期 mockups 在 tmp/ 不入库」 | ❌ **已入库** `design-notes/mockup-baseline/` |
| 「`main` 未合并、未动」 | ❌ **已合并**（`fcde1897`） |
| 「那 4 个 `running` 的 agent 是僵尸」 | ❌ **我说错了 —— 它们活着**（见 §6） |

### 2.3 我这条线**仍然有效**的部分（V1 线没覆盖）

| 成果 | 位置 | 状态 |
|---|---|---|
| **组件形态 24 条**（A-115 的 A 类） | `component-spec.md` §4.30 + `reports/IMPL-C1{,-b,-c}-report.md` | 落地且已验（图谱画布 R-2 = 0） |
| **文案 116 条** | `reports/IMPL-P26{,-b}-report.md` | 落地且已验（文本 585→561 节点，不增） |
| **动效验收 + 四条 FAIL 修复** | `reports/MOTION-VERIFICATION.md` + `reports/IMPL-M1-report.md` | **PASS 11·FAIL 0·PENDING 1**，终态铁律 13/13 |
| **走查工具三处修复** | `reports/IMPL-A114-probe-fix.md` | 3.4-2 / 3.4-3 判据口径定稿；**`g5.py` 的 R-1 假绿缺陷**修好 |
| **版式诊断 D1–D5** | `reports/LAYOUT-DIAGNOSIS.md` | 五类可测缺陷 + 实测基线（**仍是 V1 线的验收尺子**） |
| **评审板** | `tmp/frontend-audit/layout-board/` | 满幅细看 + 样板基线 + DRIFT 一栏 |

---

## 3. 现在的权威源（**按领域**）

| 领域 | 文件 | 备注 |
|---|---|---|
| ⭐ **视觉基线（靶子）** | `workbench-visual-language-v2/VERSION-V1.md` + `design-notes/mockup-baseline/`（`v1.html` + `README.md`） | A-142 / A-143 / A-144 |
| **下一波要做什么** | `workbench-v1-baseline-convergence/`（proposal → design → specs → tasks + **HANDOFF**） | **tasks 第 2–5 组** |
| 组件形态 | `workbench-visual-language-v2/design-notes/component-spec.md` **§4.30** | A-115；V1 线**不动**它 |
| 组件版本地图 | `design-notes/component-versions/README.md` | C-1…C-6 |
| 版式参考（只读） | `design-notes/layout-spec.md` | V1 线只读 §2 / §3 / §6 |
| 动效 | `design-notes/motion-spec.md`（§1.6 硬红线 · §7.2 降级矩阵 · **§11 补钉流程**） | A-116 |
| 文案 | `design-notes/copy-table.md` + `copy-table-gap.md` | 定稿 + 台账 |
| 色彩 / 资产 / 走查口径 | `night-paper-tokens.md` · `asset-spec.md` · `walkthrough-harness.md` | —— |
| 图谱隔离 | `design-notes/graph-isolation.md` | §6.6 / §6.7 已按 A-126 / A-132 同步 |

---

## 4. V1 线留下的、**还没定的两件事**（**下一会话要先定**）

见 `workbench-v1-baseline-convergence/design.md` 的 Open Questions：

1. **顶栏「搜索」接哪条检索通路？**（产品有 `retrieval-evaluation` 能力但未接 UI；
   也许只做「跳到知识图谱搜索」。**不要放假搜索框** —— 不查东西的搜索比没有更糟）
2. **优先回看的状态词表**（到期复习 / 阻塞 / 未开始 的确切措辞）——
   先按 AGENTS.md 纪律 2 落 `docs/GLOSSARY.md`，再落 `copy-table.md` §5 的状态词表。

---

## 5. 我这条线留下的**待裁决**（V1 线之外）

| # | 事项 | 我的建议 |
|---|---|---|
| **Q-1** | 日历扩散用 `scaleX`（规格字面）还是 `scaleY`（负荷柱的实现）？日历格是高度编码的竖条 | **scaleY**，但探针 `motion_verify.py` 只量 X，改要连着改探针 |
| **Q-5** | 连对横幅**弹入其实看不见**（`lk-combo-out` 的 520ms 回填盖掉了 `lk-combo-in` 的 0%） | 要修，但会影响 M-4 的判据读数 ⇒ 连着复核 |
| **D5 残余** | `knowledge-row` 38px 装 14px 字（比值 **0.37**） | 放大字（14→16px）优于压行（压行牺牲 44px 命中区） |
| **F3** | 右栏无对话时要不要自动收起（`data-ai-collapsed`）？纯布局最多 +60px | 不自动收起；把「还没有对话」做成有分量的空态 |
| **`.sm` 圆角** | 已按「家族一致」裁成 `--r-md`（12px），原为 14px 药丸 | 要小药丸须**先回写 `component-spec.md`** |
| **P24 数据源** | 「最近使用置顶」无现成数据源 | 建议 **C 不做**（registry 加字段 = 持久字段变更） |
| **资产五条** | 画布墨量 / 茶汤面 / 花瓶笔筒 / 圆规 / 第 29 组未勾 | 见资产报告与 `reports/IMPL-C1-report.md` |
| **T-7** | 编号点串的首个宿主（默认会顶掉 **M-J 火苗簇**） | 火苗簇保留；编号点串另找宿主 |
| **DRIFT-1/3/4** | 章节计数 / 数据轨 1120 / 章节中文名 | **DRIFT-3 建议裁 880**；DRIFT-1 建议不显示计数；DRIFT-4 维持载荷原值 |

---

## 6. ⚠️ 关于「有几个 subagent 在跑」的**正确查法**（**我这里出过错**）

### 6.1 没有 list 工具

`Agent`（派发）· `SendMessage`（发消息 / 唤醒）· `TaskStop`（停）· `TaskOutput`（读输出）
—— **没有一个能枚举「当前正在运行的任务」**。

### 6.2 磁盘枚举法（`~/.zcode/cli/agents/<session-id>/agent_*/metadata.json` 的 `status`）

本会话扫到的分布：`completed 115 / failed 11 / stopped 9 / **running 4**`。

⚠️⚠️ **那 4 个 `running` 是活的，不是僵尸 —— 我一开始判断错了。**
- 它们是 **F02 / F04 / F05 / F06 审计 agent**（2026-10-21 创建）；
- 它们的 `updatedAt == createdAt`（**创建后再没更新过**）——
  ⚠️ **这个字段只在「轮次边界」更新，不是心跳** ⇒ **不能拿它判死活**；
- 实证：**其中一个在 2026-10-24 07:39 还在改 `workbench.css`**
  （抽屉层叠修复：窄视口下画布盖住抽屉、导航点不到）。
  ⚠️ 那份改动**至今未提交** —— 就是 §1 里工作区不干净的原因。
- `TaskStop` 对它们报 **`Invalid task ID`** ⇒ 它们**不在本会话的运行时任务表里**，
  但**进程还活着**（属于更早的会话）。

⇒ **纪律**：
1. **磁盘 `metadata.json` 的 `status` 只能当参考**，**`updatedAt` 更不能当心跳**；
2. 权威探活只有三个，各有副作用：
   `SendMessage`（**活着会被唤醒**！）· `TaskStop`（要精确 id；对已完成的会把 status 改写成 `stopped`）·
   `TaskOutput`（**别读 `output.txt`**，那是 transcript，会炸上下文）；
3. **真正的信号是 completion 通知** —— 但「**还没收到通知 ≠ 已完成**」。
   我在这个会话里正因此判断错过一次：C1 还在跑时我按「没收到通知」判定它结束，
   派了 C1b 做**同一批活** ⇒ 两个 agent 同改一个 CSS ⇒ 撞出 `:where()` 那个
   40px→36px、命中区破 44px 的回归（**A-129**）。
   ⇒ **派收尾波之前必须先确认上一棒已结束**（等通知，或用枚举法 + 文件 mtime 交叉验证）。
4. ⚠️ **本工作现在是并行双线** ⇒ 开工前先 `git status` + `git log --oneline -5`，
   **别把另一条线的在途改动回退掉**。

---

## 7. 我这条线的坑清单

| # | 坑 | 怎么办 |
|---|---|---|
| **A-39** | pip 里装了 `lesson-kit 0.1.0` ⇒ 仓库根外起服务会解析到 site-packages 快照，**新 token 返回空且不报错** | 仓库根起服务 + 核对**服务字节 == 磁盘字节** |
| **代理** | `http_proxy=127.0.0.1:7890` **吞掉 localhost**（pytest 会假失败） | `env -u http_proxy -u https_proxy -u all_proxy` |
| **A-90** | `git commit` 不带路径会把**别的 agent 暂存的**一起扫进去（已发生 5 次） | `git add -- <路径>` **和** `git commit -- <路径>` 都带 |
| **零特异度是双刃** | `:where()` 特异度 0 **低于**基类 `button`（0,0,1）⇒ 曾把主按钮打成 36px、命中区破 44px | 形态高度留在形态规则里；尺寸修饰符靠**源顺序**取胜 |
| **A-114 / A-132** | 探针**测错对象** / 算术**把结果算没** ⇒ 恒 FAIL 或**假绿** | 改探针的**测法**不改**测什么标准**；改完用**旧 bug 复现一次**自证 |
| **A-85** | 整版重做下**整页像素比**天然 0.81–1.00 ⇒ S-* 不作机械门禁 | 机械比值只管**局部/同源**；**不许**调阈值或改基线凑绿 |
| **A-135 / A-143** ⭐ | **动手前先查「有没有已存在的规格 / 基线」** —— 我这轮就因为没查，把已有的版式规格扔了重造；**那之后又被 A-143 改成「靶子优先」** | 派任何「做 X 的设计」之前，先翻 `design-notes/` 与 `decisions.md` 的**最新编号** |
| **端口** | 避开 3081/3092/3099/3177/3178/3184/3200/3201/3281/3282/3288/3411/3460/3461/3462/3477/3481/3482 | 独立端口 + 池副本 + `LESSONKIT_WB_HOME` |
| **台账抓取** | 台账只扫含中文的串 ⇒ **纯英文界面文案会漏**（漏过 2 条） | 已修（A-120）；人工扫 `textContent` 拼出的英文串 |

---

## 8. 新会话的起手式

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
git status --short && git log --oneline -5        # ⚠️ 预期 workbench.css 有另一条线的未提交改动
env -u http_proxy -u https_proxy -u all_proxy python -m pytest tests -q
env -u http_proxy -u https_proxy -u all_proxy openspec validate --specs --strict
```
**读三份**（顺序）：
1. `openspec/changes/workbench-v1-baseline-convergence/HANDOFF.md`（**下一波做什么**）
2. `openspec/changes/workbench-visual-language-v2/VERSION-V1.md` + `design-notes/mockup-baseline/README.md`（**靶子与权威分工**）
3. `decisions.md` 的 **A-142 / A-143 / A-144**（靶子优先的规矩）

⚠️ **不要**做：改图谱算法 · push · 回退另一条线的未提交改动 ·
把 `layout-spec.md` 当实现目标 · 照 `tmp/` 里的旧脚本行事。

---

## 附：V1 收敛线这一波（2026-10-24）

工作台收敛到 V1 基线的**四组**（顶栏动作区 · 会话按最近分组 · 优先回看状态点 ·
左栏首组「学习」）+ 一次缺陷修复（图谱页窄视口下画布盖住抽屉）已完成。
**详细记录在 V1 收敛线自己的交接文档**：
`openspec/changes/workbench-v1-baseline-convergence/HANDOFF.md` §3
（两个 Open Question 的裁定依据、对照板位置、验收结果、留给所有者的取舍）。
