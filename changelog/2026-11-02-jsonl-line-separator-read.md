# 2026-11-02 — 对话读取被 Unicode 行分隔符切断（jsonl reader）

所有者在做「高级数据结构与算法分析」练习时，与 Agent 的对话刷新后报
`读取对话失败：internal error: Unterminated string starting at: line 1 column 593`，
且点击会话会落到别的对话。

## 根因

不是文件损坏，是**读端解析 bug**：

- 事件与转写按 JSONL 保存，写入用 `json.dumps(..., ensure_ascii=False)`；
  工具输出里带回的 `U+2028`（行分隔符）、`U+2029`、`U+0085`（下一行）在 JSON 字符串里**合法**，
  因此原样写入文件中。
- 读出时统一用 `str.splitlines()`，而它把上述字符也当换行 → 一条完整记录被切成两半 →
  `json.loads` 报 `Unterminated string` → `GET /ai/sessions/<id>` 500。
- 前端拿到 500 后回退到列表首个会话，表现为"点进去是别的对话"。
- `conversations.events()`、会话组装、`_coalesced_activities`、`_continuity`、
  `_last_check_outcome` 等 8 处读 JSONL 的地方都用 `splitlines()`，全部命中同类风险。

## 修复

- `workbench/bridge/conversations.py` 新增 `_json_lines(path)`：只按 `"\n"` 切分、
  去掉行尾空白与空行；8 处 JSONL 读取统一改用它（事件、转写、连续性、最后检查结果）。
- 测试：`tests/workbench/test_jsonl_line_separators.py` —— 含 `U+2028/U+2029/U+0085`
  的字段经 `_json_lines` 与 `conversations.events()` 读取后内容完整。
- 数据未做任何修复：文件本来就是合法 JSONL，改读端后同一份文件即可读出
  （conv-008 实测 16 条消息、末条"修"）。

## 验收

`python -m pytest tests -q`：1315 passed。daemon 重启后
`GET /api/w/高级数据结构与算法分析/ai/sessions/conv-008` 返回 200。
