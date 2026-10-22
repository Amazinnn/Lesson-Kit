# IMPL-W3j — 验收关卡的人工判读材料（一页纸，给所有者看的）

> 服务于 `openspec/changes/workbench-visual-language-v2/tasks.md` **第 22 组**的 4 条
> **SEMI / MANUAL** 判据（机器只给数值与证据，**人签字**）。
> **只新建** `openspec/changes/workbench-visual-language-v2/acceptance-manual-review.md`
> 与 `openspec/changes/workbench-visual-language-v2/acceptance-shots/`（**截图索引**）。
> **绝不改产品代码。**

## 背景
第 22 组的第一轮走查跑完了：**G-1…G-8 底线守卫全 PASS**，整体 FAIL 落在清单层。
其中有 **4 条是 SEMI / MANUAL**（机器**只给数值与证据，不替人签字**），
外加 **2 条因数据不足而 PENDING**、**1 条（M-3）缺种子**。

本任务：**把这几条的证据整理成可直接判读的一页纸** —— 每条给出
**判据原文 / 机器测到的数值 / 证据路径 / 建议判定 / 判读时该看什么**。

## 要整理的四条（判据原文在 `design-notes/walkthrough-harness.md` §7.5）

| # | 判据 | 机器给什么 | 人要判什么 |
|---|---|---|---|
| **3.2-3** | 状态**语义**与用户侧措辞一致 | 数值与证据 | 措辞与状态的对应关系**对不对** |
| **3.4-4** | 错误态明确，**红色仅用于失败与阻塞** | 枚举出的全部红色 token 使用点 | 逐点判：**有没有把红色用在非失败/非阻塞的地方** |
| **3.6-2** | 图标与插画在同一套**线宽与圆角**内 | 全部 SVG 的 `stroke-width` 分布 + `rx/ry` 集合 | 人工核：**是否同一套**（机器只能给分布，不能给结论） |
| **3.6-4** | 插画画的是**具象器物**（不是抽象几何块） | 无 | **人看渲染结果**判 |

## 产出要求

### `acceptance-manual-review.md`（**一页纸**，不是长报告）
每条一节，固定五段：
1. **判据原文**（照抄，**不要改写**）
2. **机器测到的数值**（从 `tmp/wt-run-7/evidence/after/probe/<id>.json` 抓真实数据）
3. **证据路径**（probe json / 截图 / 产物文件的**实际路径**，要能点开）
4. **建议判定**（PASS / FAIL / 需你定）+ **理由**
5. **判读时该看什么**（一句话说清人要盯哪个点）

⚠️ **不许代替所有者签字**：最后一节写成「**需要你确认**」，并把**建议**与**依据**分开写。

### `acceptance-shots/`（截图索引）
把 12 张对照截图（`tmp/wt-run-7/evidence/{before,after}/shots/*.png`）整理成
一份**索引 markdown**：每张截图一行 —— 页面 / 视口 / 主题 / before 路径 / after 路径 / 该页的判据。
⚠️ **截图是 `tmp/` 里的产物（gitignore）**，索引里要写**相对路径 + 生成命令**，
让**重新跑一次**的人能重新得到它们。

## 硬约束
- **只新建** `acceptance-manual-review.md` 与 `acceptance-shots/`。
- **绝不改**产品代码（`workbench/` / `pool/` / `pipeline/`）—— **另有 agent 正在并行改**。
- **不要**改 `openspec/changes/workbench-visual-language-v2/` 下的其它文件
  （`decisions.md` / `tasks.md` / `contract-drift.md` / `acceptance.md` / `design-notes/` ——
  **主会话统一维护**）。
- **不要**改 `docs/`。
- ⚠️ **截图是「那一轮代码状态」的产物** —— 走查期间别的 agent 也在改产品代码
  ⇒ 索引里**必须写明那一轮的代码状态**（`git rev-parse HEAD`），
  并在开头写一句「这些数字对应那一轮；后续修复后需要重跑」。
- **不许**为了让判据变绿而改**探针**（判据是判据，不是产品）。
- 判据原文要**逐字抄**，不许顺手「润色」。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate workbench-visual-language-v2 --strict
```
- **自检**：每条引用的证据路径**必须真实存在**（自己 `ls` 核一遍）——
  指向不存在的路径的「证据」等于没有证据。

## 落盘纪律与回报
- **一个文件一个 commit**，只 `git add openspec/changes/workbench-visual-language-v2/acceptance-manual-review.md`
  与 `acceptance-shots/`，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**四条判据各自的建议判定与依据**（逐条）+
**证据路径的可达性核验结果** + **那一轮的代码状态** + 待裁决项。
- 数字一律以**当场从产物里读出来的**为准。
