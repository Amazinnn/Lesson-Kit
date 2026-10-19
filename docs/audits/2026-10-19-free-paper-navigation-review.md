# Paper 自由导航与学生组卷入口清理：交付快照

日期：2026-10-19。实现审计基线 `origin/main=5d02dde6`，最终产品代码 `cd9587ed`。本文是带日期的证据快照，不是当前行为或字段权威。

## 范围与结果

实现 `free-navigation-paper-practice` 与 `remove-learner-manual-paper-selection`。普通题支持任意题导航、两种答案展示方式、模式对应的提交锁定、显式整卷交卷、独立恢复、完成页与答卷往返；学生侧选题组卷及名单顺序编辑退役，Agent/CLI 作者能力保留。旧轮次、临时固定题卷和闪卡保留兼容路径；不修改真实课程库或运行服务。

## 检查证据

| 检查 | 结果 |
|---|---|
| 独立子代理执行 `PYTHONUTF8=1 python -m pytest tests -q` | 1097 passed，274.17s |
| 独立子代理执行全部 `tests/workbench/*.test.js` | 236 passed，0 failed；运行日志时间晚于最终代码提交 |
| `python -m compileall -q lessonkit.py workbench pipeline pool tests` | 子代理及控制器检查通过，退出 0 |
| `openspec validate --all --strict --concurrency 3` | 归档前 24 passed，0 failed |
| `python lessonkit.py guard extract-problems --course dmath --chapter ch06` | PASS |
| `git diff --check` | 通过 |
| Chromium 隔离走查 | 退出 0，见下 |

全量检查日志保存在系统 TEMP 的 `lesson-kit-paper-final-{pytest,node,compileall,dmath_guard,openspec-final}.log`。独立子代理完成上述检查并指出真实 API 回执和兼容容器问题后，因模型额度中断，**未输出完整独立复核结论**；最终问题闭环与收尾由控制器接手，不将这次中断标成独立 ACCEPT。

## 已修复的关键问题

- `/feedback` 首次评分返回变化列表，编辑返回回执，并非反馈事件对象。界面按已确认请求恢复评分/评语，后续使用同轮覆盖；历史 null 评语保留为精确的预期值，避免再次走首次评分而重复学习效果。
- 兼容闪卡委派时显式显示旧容器；完成答卷返回按钮不再随工具栏一起隐藏。
- 试卷切换交给既有停放规则，不额外阻止 A/B 切换；再次练习不依赖同 URL 导航，临时固定题卷也通过原创建接口生成新执行。
- 单选/判断提交保留选项文本；历史 Attempt 缺 choices 时只按已有作答文本恢复显示，不从答案键补造作答。
- 不会标记优先于未改动的旧输入；最终提交不把旧文本重新判成普通答案。新作答可清除可修改标记，但保留曾看答案事实。
- 导航、作答提交与整卷完成分离；已提交题不重复形成 Attempt，最后一题作答不会自动结束新流程。

## 实际浏览器检查

`TEMP/free-paper-navigation-browser.py` 使用 WorkspaceFixture 测试库、隔离注册表与随机端口，未访问真实课程库。覆盖五题前后和圆点往返、两卷切换/暂停/刷新恢复、逐题与统一交卷、未逐题提交内容随交卷提交、锁定和不提前揭示、完成页查看答卷并返回、再练新轮次。两轮共 10 条 Attempt，查看和返回不增加记录。

通过真实 HTTP 接口先自评 3 分再覆盖为 4 分，只有一条关联反馈；覆盖前后的 learner_signals、problem_progress、learning_current_state、review_schedule 快照一致。另验证旧闪卡容器可见、继续后正面可读且可揭示背面。截图为 `TEMP/free-paper-navigation-completed.png`。

## 发布边界

本改动新增 nullable `reveal_timing` 字段；旧池读取和旧调用仍兼容，新模式写入要求显式迁移。测试只迁移测试库，没有授权或执行本轮真实课程库迁移。当前运行服务也未重启，不能将本报告当作 live dashboard 已更新的证明。上线时需协调数据库迁移和前后端服务版本，不能只替换静态文件。
