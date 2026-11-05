# 证据与核对清单

## 检出与时间范围

2026-11-05 核对主检出 main 为 b5054e8d，教学工作树 feat/exam-prep-engine 为 9e640332。后续引用前检查对应检出是否变化。本树同时考察两者，保留合入状态区别。

## 已有证据与限制

- 作者内容镜像 workbench/data/content_mirror.py 当前实体为 kp/problem/relation，Paper 未进入该实体集合。现行 GLOSSARY 将本地镜像与 Git 网络操作分开，扩展前需要确认产品意图。
- 教学分支的检验提交接口在临时 fixture 中接受不存在的选项，同一 check 可多次追加 check.result。属于局部复现，尚未执行真实浏览器验收。
- 教学分支的 guardrails 模块有纯规则与测试，本轮静态搜索未发现生产调用入口。需结合实际事件路径继续核对，暂不宣称全部护栏均未生效。
- ARCHITECTURE 的 Domain 零 IO、Data 不导入 Domain 声明，与 feedback 的事务/Pool 调用及 Data 导入 Domain 规则存在漂移。裁决需登记权威协调，不可仅依代码现状改写规范。
- 活跃 change 中部分任务状态与已有代码覆盖存在差异。每项需核对已实现、已验证、已合入及已上线，禁止只按勾选推断。
- 主目录此前全量检查为 1302 passed、13 failed，失败集中于 Pi 相关测试。开启 PYTHONUTF8 后相关三个套件 125 passed。尚未在该模式重跑全量，编码根因需进一步定位。
- 主目录编译、当前规范 21 项与提取 guard 通过。教学分支三个选定套件 31 passed。以上均不代表真实课程或浏览器交互接受。
- 默认 3081 端口在上次检查时拒绝连接，当前实际运行版本未确认。历史状态文档中的已上线描述不能替代当前运行证据。

## 后续每项证据要求

记录来源位置、检出版本、核对时间、复现步骤、输入范围、观察结果、结论限制及受影响决定。历史审计数字重新核实后才用于工作量或风险估计。
# 2026-11-06 发送恢复补充核对

主检出 workbench/server/static/workbench.js 的 ai 轮询状态处理将 failed 和 cancelled 都通过 aiUpdateOutbox 写成 failed。aiRenderOutbox 将 unknown、rejected、failed 作为可操作恢复记录呈现。这支持所有者关于停止后出现恢复记录的报告。静态证据不证明它会自动重发，也不证明重复消息的根因。

Q025–Q027 已记录新的期望行为及验收门槛，尚未修改产品实现。重复消息须追踪提交身份、接受次数、内容执行和呈现后复现。

## 2026-11-06 学习与复习研究核查

主目录 docs/research/2026-11-02-learning-efficiency-algorithms.md 明确标为研究提案，综合调度、知识追踪、学习科学等分报告并提出分期路线。已读取总提案开头及相关主题索引，本轮未独立重验论文原始结论和数字，不将研究建议自动纳入实施范围。这些研究文件当前为未跟踪资产，规划引用不代表已纳入版本交付，后续交接须解决可获取性。

教学分支 9e640332 的 workbench/domain/session_machine.py 已定义 created、briefing、running、concluding、closed 及 suspended、abandoned 的受控转移。此处是教学会话生命周期，不能直接当作诊断、加强和跨日维护的学习进程。workbench/domain/engine/registry.py 已列出 FSRS、加权选题、时间估计及 Elo 策略；workbench/data/forms.py 已消费薄弱、能力、到期等事实形成候选和原因。存在实现不等于已合入主目录、接通用户目标或通过真实学习验收。

后续需建立研究依据、现行契约、分支实现、入口消费和验收证据的对应关系。先复用已有会话与调度语义，再决定是否存在必须新增的持久目标信息。
