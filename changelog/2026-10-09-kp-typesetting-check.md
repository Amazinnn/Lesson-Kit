# 2026-10-09 正文排版检出实现交接

落实 `kp-text-typesetting-check` 已批准 requirement 与 ADR 0023。正文的共享
纯测量/报告在 `workbench/domain/typesetting.py`；SQLite id/body 读取在
`workbench/data/typesetting.py`。两边只测正文、只报事实，40–300 包含两端，
纯公式/反引号代码的零可见段落不报过短，输入文字不改。

有效 bundle 校验与成功 apply 新增 `typesetting`；batch 和 Bridge 返回白名单
保留它，既有结果字段/门禁/原子性保持。纯 helper 可显式报告无 bundle。
pipeline validator 在旧 schema 提前返回前读可用正文，文本与 JSON 使用相同
报告，连接为 `mode=ro`；旧错误、计数与 0/1/2 退出契约不受检出影响。

边界/代码围栏/零写入/合法 apply/旧拒收/Bridge 镜像/schema 错误与独立子进程
导入路径均有定向 TDD 证据，详见
`openspec/changes/implement-kp-text-typesetting-check/tasks.md` 和任务交接报告。
最终全套、隔离环境验收和 archive 交给独立验收方；没有 push/archive。

原 change 的必需 sections 1–4 与 sections 5–6 分开记录。结构边界识别、
其他字段区间、每课参数与已有正文重写仍延期/范围外；#110、NEW-GAP、DOCTRINE
未实现。真实课程池和注册表未操作，所有写入测试只在临时 fixture 数据库。
