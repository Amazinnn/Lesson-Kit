# 外部 Tutor 与课程文件的正常使用流程

状态为批准目标，命令属于待实现的 course-sync 接口，不能冒充当前已可调用。

## ET-01 已有课程交给外部 Tutor

1. 本地已确认保存课程数据和偏好，调用 `lesson-kit course-sync export <workspace> --out <directory>`。
2. CLI 校验全部受管理课程资产，输出自含 manifest、内容、附件、学习文件和最近回执。缺失项必须真实列入结果。
3. 用户通过宿主实际支持的附件或仓库读取功能给 Tutor 文件。Tutor 读目标、范围、当前位置及必要作答证据，避免再次要求重复已存在的信息。
4. Tutor 讲解、诊断、练习并输出 UTF-8 课程文件或声明版本的更新工件。逐题原始作答、未答、揭晓与不确定附注保持原样。
5. 本地调用 `lesson-kit course-sync receive <workspace> --from <directory>`，自动处理无歧义更新，独立有效项完成，真实冲突给差异及所需选侧输入。
6. 再导出或 `lesson-kit course-sync sync <workspace>` 发布 Git 媒介，实际远端结果分别报告。

## ET-02 新设备接续

收到完整课程文件后，调用 receive 的显式新工作区目标，完成校验、建立与注册。另存或关联身份选择只在课程来源有疑点时需要。课程内容、已确认草稿、学习偏好、目标与续接记录可正常使用。不能要求原机器的磁盘盘符、Provider原生会话或当前浏览器内存。

## ET-03 冲突与部分完成

`check` 只读查看差异。`receive/sync --keep local|incoming` 为本次所有真实冲突指定方向，逐项不同方向使用 `--choices <json-file>`。无歧义项无需此输入。CLI 写入独立有效单元并准确列出其余状态，修正后重试不重复学习事实。

“选哪侧”提供内容结果输入，执行无项目审批卡或再次批准。仅缺文件不能传递删除，用户或 Agent 用显式删除记录表达意图。

## ET-04 日常自动化

课程明确配置媒介后，用 `lesson-kit course-sync schedule install --all-configured` 安装每小时任务。调度与手动复用同一 sync；status 可查看每课程最近结果。成功静默，新冲突一次短系统通知。任务支持 enable/disable/remove 正常入口。

GitHub可用性通过实际宿主/凭据验证。宿主没有仓库工具时，附件文件交接仍是正式使用方式，不能绘制假按钮或声称已经读取/发送。机器级账号凭据不进入课程文件。
