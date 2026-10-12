# 练习页 Agent 上下文修复 — 2026-10-12

练习页只把已解析的正式题作为页面锚点。前序题仅在可见题属于同一 active practice 时附带，最多四道已结算题；闪卡和未知 id 不形成正式题焦点。明确的上一题/近期题组指代可改变轮次焦点，否定或竞争当前目标时保留页面默认。纯目标规则位于 Domain，Server 负责 Pool 查询与上下文投影。

保留既有 `resolve=False` 活跃练习读取和最多四道前序题加当前题的内容展开上限。上下文生成不移动游标，也不写尝试、反馈、状态或排期。

补充修复：所有既有相对指代均检查相邻的否定操作，允许空格和“再、在、一下”，覆盖“不是刚才那题”“上一题不用解释了”“不要再解释前一道题”“我不是在问刚才那题”；“上一题和这一题有什么区别”保留页面默认。“上一题我不会做”“上一题为什么做不出来”“前几题我都没理解”仍指向前序题。动作登记同时澄清镜像边界：草稿与完整工作载荷不写会话镜像，成功轮次仍保留既有 `context_anchor` 元数据。

Focused context and Domain tests: **23 passed**, following a failing regression for spaced/modifier forms. `python -m compileall -q lessonkit.py workbench pipeline pool tests` passed. `openspec validate --specs --strict` passed (18 specs). `git diff --check` passed. Repository full-suite and independent acceptance review remain with the acceptance runner.
