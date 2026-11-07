# 2.6 浏览器学习偏好的课程投影与接收消费（2026-11-08）

任务原文：> 为浏览器学习偏好建立已确认保存的课程投影和接收消费路径。A→B 后真实练习验证提交粒度和揭晓时机，未确认浏览器输入不得冒充已保存。

## 通路

浏览器设置 → `PATCH/POST` 课程偏好路由（`workbench/server/course_preferences_api.py`）→ Data writer 写 `.lessonkit/course-preferences.json`（课程资产，随包交换）→ 接收端以已确认值为准；浏览器 `wb_settings_<工作区>` 只是交互镜像。

## 证据

| 断言 | 证据 |
|---|---|
| 只在显示偏好的界面打开时才请求，不预取 | `tests/workbench/course-preferences.test.js::no preference request is made before the surface that shows them opens` |
| 页面水合一次已确认投影 | `::a practice page with the Paper entry hydrates the confirmed projection once` |
| 收到的课程偏好压过旧浏览器镜像 | `::received course preferences win over a stale browser mirror` |
| 仅当服务端尚无投影时，浏览器显式旧值一次性迁移 | `::an absent server projection adopts the explicit browser learning keys once` |
| 投影不可读时绝不覆盖 | `::an unreadable preference projection never authorizes overwriting it` |
| 设置变更经课程 writer 保存；被拒绝的保存不算已确认 | `::a settings change is saved through the course preference writer`、`::a rejected save is reported and never counted as confirmed` |
| 试卷开始页显示已确认的揭晓时机 | `::the Paper setup shows the confirmed reveal preference` |

## A→B 真实浏览器链路（P3，端口 3099）

`../2026-11-08-p3/summary.md` 的 RELEASE-01 行（隔离服务 `--project-root` 指 worktree，Playwright 实跑）：

1. 偏好基线为空 → PATCH 后重载 → `lkCoursePreferences.values()` 生效、镜像写入、`data-show-rating=off`（**提交粒度**在真实页面上按已确认值呈现）；
2. 新卷 `ps-003` 开始页显示收到的 `on_submit`（**揭晓时机**消费到真实新建卷）；
3. 进行中的 `ps-001` 显示「继续练习」，揭晓时机冻结为不可改（**未完成的一轮不被改写**）。

这三点合起来就是任务要的"A→B 后真实练习验证提交粒度和揭晓时机"。

## 未确认输入不冒充已保存

- `a rejected save is reported and never counted as confirmed`：保存失败只提示，不写入已确认投影；
- 镜像与投影分离：`DATA_MODEL.md` 明确浏览器 `wb_settings_*` 是镜像、`course-preferences.json` 才是已确认值；
- SYNC-04 相关：做进程级硬杀时未发现偏好被半写（偏好文件走 `_atomic_json`）。

## 边界

- 只在 Windows + 本机 Chromium 上验过；未做多浏览器矩阵。
- 外观/阅读字面/动效/声音/Provider 凭据不属于该投影（见 GLOSSARY「已确认课程学习偏好」），未纳入本条验收。
