# IMPL-N1 — 夜纸（暗色）主题全站巡检：只出报告，不改产品代码

> 服务于第 22 组验收关卡与「夜纸跟随全站」这一交付承诺。
> **只新建** `openspec/changes/workbench-visual-language-v2/night-sweep-report.md` 与
> `openspec/changes/workbench-visual-language-v2/night-sweep-shots/`。
> **绝不改产品代码。**

## 背景
夜纸值集已落地（`design-notes/night-paper-tokens.md` §3 的 52→53 个值 token），
但**只有少数页面在夜纸下被逐项看过**。本任务做**系统性的夜纸巡检**，
把「夜纸下看不见 / 低对比 / 浅底浅字」的地方**一次找全**。

## 要做什么
1. 起隔离走查服务（`tools/walkthrough/launch.py`：仓库根 cwd、独立端口、池副本 +
   `LESSONKIT_WB_HOME` 隔离注册表），**服务字节数必须等于磁盘字节数**。
2. 逐页在**夜纸**（`<html data-theme="night">`）下渲染并采集：
   工作台 / 练习页（题面 / 解析 / 作答区 / 完成页）/ 知识点列表 + 详情 /
   记录中心（4 视图）/ 练习集 / **设置视图** / 图谱页。
3. 逐项检查（能自动判的用脚本，判不了的配截图）：
   - **不可见元素**：文字色与背景色**同色或极近**（对比度 < 1.2:1）⇒ 元素在夜纸下「消失」；
   - **低对比**：正文/次要文字 < 4.5:1、三级文字 < 3:1、控件边界/非文本 < 3:1
     （用 `tools/verify_tokens.py` 的 WCAG 公式，逐对实测，不许手抄）；
   - **浅底浅字 / 亮块亮字**：夜纸下仍是亮色块配亮字（尤其 `.lk-dot` / `.chip` /
     状态圆点 / 进度带 / 骨架屏 / 图例色块 / 题号格）；
   - **硬编码亮色残留**：夜纸下仍出现 `rgb(2xx,2xx,2xx)` 一类的亮色块（用
     `getComputedStyle` 枚举，不靠看图）；
   - **未跟随主题的元素**：该随主题变的没变（对比同一元素在亮/夜两态的 computed 值）。
4. **图谱页**：夜纸下**取值必须与亮色完全相同**（图谱页冻结块）⇒ 单独核一遍
   （`graph-isolation.md` 的 R-3 口径）。**若发现图谱页在夜纸下变了，那是 P0**，单独列在最前面。

## 硬约束
- **只新建**上面那两个路径。**绝不改**产品代码（`workbench/` / `pool/` / `pipeline/`）——
  **另有几个 agent 正在并行改那些文件**。
- **不要**改 `docs/` / `openspec/` 下其它文件（主会话统一维护）。
- **不写真实池**（`pool/dmath.db` 的 mtime / sha256 / size 全程不变）。
- ⚠️ **不许为了让报告好看而放宽阈值**；判不出来的写「需人工看图」，并给截图路径。
- 截图落 `night-sweep-shots/`（**注意**：`tmp/` 被 gitignore ⇒ 截图若放 `tmp/` 就不会入库；
  ⇒ 放本 change 目录下的 `night-sweep-shots/`，**但**要在回报里说明体积）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```

## 落盘纪律与回报
- 一个 commit（报告 + 截图），只 `git add` 你新建的那两个路径，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**逐页的问题清单**（页面 / 元素 / 实测值 / 建议修法，分 P0/P1/P2）+
**图谱页夜纸与亮色完全相同的证据** + 待裁决项。
