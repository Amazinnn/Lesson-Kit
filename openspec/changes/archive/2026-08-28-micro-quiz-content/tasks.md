# micro-quiz-content 任务

## 1. Schema（additive）

- [x] `pool_schema.py`：ensure_columns 追加 `problems.practice_modes TEXT`、
      `problems.micro_quiz TEXT`；真实库迁移幂等。
- [x] `data/pool.py::_problem_row`：解析两列为 dict 字段
      （practice_modes→list，micro_quiz→dict，空值保持 None）。
- [x] fixtures 同步两列（fixtures 与 pool_schema 同构，含 CHECK 教训）。

## 2. 契约与数据层

- [x] `domain/micro_quiz.py`（纯规则）：词表、`validate_payload(payload)`、
      `practice_modes_for(quiz_type)`、`is_objective(quiz_type)`、
      `check_answer(item, submitted)`。
- [x] data 层插入前复验载荷契约（防绕过门禁的直接写）。
- [x] 单元测试：词表、校验、判分（对/错/多选部分对）。

## 3. Ingest 配方

- [x] `ingest.__init__`：`micro-quiz` 进 RECIPE_NAMES；`_gate_micro_quiz`
      确定性门（D3 全部规则 + ID 序号 + 知识点存在性）；apply 备份 + 单事务。
- [x] `cli/main.py`：recipe 子命令接受 micro-quiz（允许 apply）。
- [x] 测试：合格清单入池、坏清单逐条报错且零写入、备份/回滚、accounting。

## 4. Pull 与练习链路

- [x] 确认 `pull._eligible_for_mode` 对解析后的 practice_modes 生效（已有规则，
      补集成测试：闪卡模式拉到微题、exam 模式不受影响、shortage 如实）。
- [x] `wb data get/problem` 输出含 practice_modes/micro_quiz 字段。
- [x] 集成测试：微题完整练习闭环（拉题→作答→评分→attempt 落 reviewing/wrong）。

## 5. UI 渲染

- [x] practice 页：按 quiz_type 渲染作答控件；客观题提交即本地判分提示
      （对/错 + error_reason）；闪卡揭示；文本型走既有作答框。
- [x] 无 micro_quiz 载荷的题目渲染完全不变（回归）。
- [x] Node UI 测试：是/否、单选、多选、揭示、判分提示、无载荷回归。

## 6. 种子内容与验收

- [x] `docs/` 附样例 manifest（2–3 条：1×yes_no、1×single_choice、1×flash_card），
      仅作为格式示例与测试夹具，不入真实库。
- [x] scratch 副本全流程实测：ingest → 闪卡/是否练习各一轮 → 学习记录正确。
- [x] 全量 pytest + Node 测试 + `openspec validate --specs --strict` + CI 绿。
- [x] 更新 FUTURE-DEVELOPMENT-NOTES（micro quiz 条目标记已实现）、
      changelog、归档本变更。
