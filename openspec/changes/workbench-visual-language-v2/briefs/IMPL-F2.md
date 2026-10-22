# IMPL-F2 — 字体资产生产（思源宋体子集化 + 许可入库）

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **5.1 与 5.2**
> （**只做字体资产本身，不改 CSS** —— `@font-face` 由另一个 agent 在 CSS 里加，避免同文件冲突）。

## 必读
1. `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **5.1 / 5.2**（逐条实现）
2. `openspec/changes/workbench-visual-language-v2/design.md` 的 **D-4**（含「体积待核」一节，
   你要**回填实测值**）
3. `openspec/changes/workbench-visual-language-v2/design-notes/asset-spec.md`（字体相关部分）
4. `openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md` 的 §2.3（字号档）

## 硬约束
- **只新建/修改这些路径**：
  - `workbench/server/static/fonts/SourceHanSerifSC-Regular.woff2`
  - `workbench/server/static/fonts/SourceHanSerifSC-SemiBold.woff2`
  - `workbench/server/static/fonts/LICENSE-OFL.txt`
  - `workbench/server/static/fonts/README.md`
  - `openspec/changes/workbench-visual-language-v2/design.md`（**只回填 D-4 的实测体积**这一处）
- **不许**改 `workbench.css`（并行 agent 正在改它）、不许改 `tasks.md`、不许改其它文件。
- 字体许可必须是 **SIL Open Font License 1.1**（思源宋体 / Noto Serif SC 是 OFL，可自由再分发，
  **必须随包附许可全文**）。
- 无构建步骤：产物是**静态文件**，不引入任何运行时依赖。

## 5.1 具体要求
- 字表：GB2312 一级字表 3755 字 + 中文标点 + 数字 + 拉丁 + 常用符号。
- 子集化命令：`pyftsubset SourceHanSerifSC.otf --unicodes-file=gb2312.txt --flavor=woff2`
  （字重 400 / 600 两份）。
- **必须实测体积**：目标 **2 字重合计 ≤ 1.2 MB**。实测值**回填** `design.md` D-4 的「体积待核」一节。
- 超标时**先砍字重（只留 400）而不是砍字表**。

### 现实性预案（按顺序尝试，遇到阻碍就换下一条，别卡住）
1. 本机若已装 `fonttools`（`python -c "import fontTools"`）→ 直接子集化。
2. 没有 fonttools → `pip install fonttools brotli`（**仅本机开发环境**，不写进任何项目依赖；
   `pyproject.toml` **不许改**）。
3. 拿不到 `SourceHanSerifSC.otf` → 试从官方源取（Adobe Source Han Serif / Google Noto Serif SC 的
   OTF/TTF 原件）。下载时**记录确切来源 URL 与版本号**写进 README。
4. 网络不可达 / 全部失败 → **不要伪造**。改为：
   - 把 `@font-face` 需要的**字体栈**按 `design.md` D-4 写成**只用系统衬线栈**
     （`"Noto Serif CJK SC","Source Han Serif SC","Songti SC","SimSun",serif`），
   - 在 `fonts/README.md` 里写明「子集化待网络可达后执行」+ 完整命令，
   - **在最终回报里明确说「本条未完成，原因是 X」**。

**绝对不要**为了凑数交一个不完整的字体文件，也不要下载许可不明的字体。

## 5.2 具体要求
- `LICENSE-OFL.txt`：SIL OFL 1.1 全文。
- `README.md`：来源 URL + 版本号 + **可复跑**的子集化命令行 + 字表清单（怎么生成 `gb2312.txt`）+ 体积实测。

## 验证
- 两个 woff2 存在、合计 ≤ 1.2 MB（或按预案降级并说明）。
- `README.md` 里的命令行**可直接复跑**（自己跑一遍验证）。
- 许可文件写明 SIL OFL。

## 落盘纪律与回报
2 分钟内先落目录与 README 骨架（即使字体还没下好），再逐步推进。
最终回报必须复述：**已落盘路径 + 每个文件的大小** + **字表覆盖（多少字）** +
**体积实测值 + 是否达标** + **来源 URL 与版本** + **design.md 回填了什么** +
若降级则**明确说明「本条未完成 + 原因」**。