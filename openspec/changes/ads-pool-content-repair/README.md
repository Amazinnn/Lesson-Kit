# ADS 题库内容修复

Repair the imported problem bank of the ADS course workspace in place — ids
unchanged, no re-import, no learning records lost — and record the invariants
and acceptance checks the repair is judged by.

This change touches data only. It changes no tool behaviour, so it declares
`skip_specs: true`; the tool-side gaps it exposes are proposed separately in
`content-dedup-and-audit`.

- 工作区：`D:\Documents\Document_In_University\课程\2026-2027 秋冬 大二上\高级数据结构与算法分析`（course `c02`）
- 批次基线：`batch-018` … `batch-032`（2026-09-25 15:44:30Z，896 行）
- 执行记录与脚本：课程目录下 `repair/`
