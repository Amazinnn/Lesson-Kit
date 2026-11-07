# 外部 Tutor 免费真实调用与正式源码重放（SYNC-07 / task 2.10）

## 调用事实

| 项 | 值 |
|---|---|
| Provider / 模型 | `opencode` / `deepseek-v4.1-flash-free`（官方免费模型） |
| 免费依据 | 官方模型文档 + 本机模型元数据：输入/输出/缓存价格均为 0（`https://opencode.ai/docs/console/models/`） |
| 实际调用次数 | **1**（15:18:50），进程退出 0，自报成本 0，耗时 13.501s |
| 输入 | 真实导出的 `handoff.md` 与 `.lessonkit/learning/misconceptions.md`，见 `handoff-sent.md` |
| 输出 | `free-model-response.json`：读取目标、指出未答项 `p-2`、逐字保留原始作答与 choices、给出下一步与一条新的学习笔记，并区分"观察到的证据"与"暂定解释" |

调用方式为**独立对话、无工具**，模型只读两份课程文件。首轮启动曾因 CLI 参数解析错误在模型调用前失败，不计为一次调用，也未记作通过。

## 当时的失败（保留原文，不覆盖）

`original-capture-failed.json`：模型输出本身正确，但当时的接收端对"只存在于 `files/` 明文目录、未改 manifest 的新文件"没有创建路径，CLI 报成功却未落盘（`FileNotFoundError: .../tutor-notes.md`）。这份报告作为原始缺陷证据保留。

## 修复后的重放（0 次新调用）

`replay-against-real-source.json`：

- `status: passed`，`calls: 0`，`identical_model_inputs: true`（夹具导出的 handoff 与源笔记与当初逐字节相同，证明重放吃的就是那次真实调用的同一份输入）；
- `raw_attempts_unchanged: true`：接收后原始作答逐行未改；
- `learning_file_received: true`：新笔记 `.lessonkit/learning/tutor-notes.md` 落到工作区；
- `reverse_export_preserved: true`：再导出时该文件被带出（反向交换成立）。

重放直接使用正式的 `workbench.data.course_sync` 与 CLI，不做模块注入；`handoff-replayed.md` 是重放时重新生成的交接文本，与 `handoff-sent.md` 内容一致。

## 结论与边界

- 满足 task 2.10 要求的四件证据：真免费请求（provider/model/日期/免费依据/次数/延迟）、原文件、模型输出、实际落库与反向交换；没有使用模拟器日志替代。
- 边界：最后一次落库是**同一次真实输出的重放**（0 次新调用），不是第二次 API 往返；如需"两次独立调用都通过"，需要再发起一次免费调用。
- 该证据只覆盖"Tutor 读取 + 回写一条新学习文件"，不覆盖多文件批量回写、冲突选侧或大规模性能。
