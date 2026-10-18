## 1. Remove learner assembly controls

- [ ] 1.1 在当前 main 定位练习、知识点、图谱、试卷页和跨页托盘的所有选题/组卷及名单顺序编辑入口，区分只读图谱筛选。
- [ ] 1.2 删除学生选题/范围/数量/来源难度/建议组卷控件、Paper 单题移除重排控件及专属事件绑定；保留管理、预览和阅读功能。
- [ ] 1.3 清理旧选区状态恢复路径，保证刷新和旧浏览器状态不能恢复被退役入口或隐式组卷；与自由导航开始页改动协调。

## 2. Preserve authoring and reconcile contracts

- [ ] 2.1 确认 Agent/CLI 的 scope、filter、exact-id、save、改卷审批能力及后端接口保留，不改题目和历史数据。
- [ ] 2.2 同一 PR 同步 GLOSSARY、PRODUCT-MANUAL、ACTION-GRAPH 与 OpenSpec 当前规范；实际受影响的 ARCHITECTURE/interface surface 按需更新。

## 3. Verification and handoff

- [ ] 3.1 以现有测试验证四个页面与跨页无学生组卷路径，Paper 管理/预览和图谱阅读仍可用，Agent/CLI authoring 用例通过。
- [ ] 3.2 在测试库完成一次简短页面巡检，记录 focused checks 与 STATUS；不写真实课程库。
- [ ] 3.3 独立验收者执行仓库规定的 pytest（PYTHONUTF8=1）、compileall、OpenSpec strict 与 extract-problems guard，再进行合并/归档。设计文档不代表功能已实现。
