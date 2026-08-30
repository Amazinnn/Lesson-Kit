# 2026-08-30 disclose-ignored-action-blocks

## 验收暴露的出题链断裂（conv-023，provider=Claude）

所有者真实验收第一击：对话里说「给知识点补两张闪卡」，回复带了动作区块，
但既没有结果卡片也没有任何写入，Agent 还在正文里两轮虚构「已写入」。
回放定位出三个叠加缺陷：

1. **解析器只认第一个动作区块**（`re.search`）：回复同时携带「练习选区 +
   出题 manifest」两个区块时，manifest 被首区块挡住，从未被解析。
2. **意图正则不认自然措辞**：`check_intent = /出题|出几道|补池|加题|入库/`
   匹配不了「补两张闪卡」——意图门未开，manifest 按规格被静默忽略。
3. **忽略无声**：区块被忽略后没有任何反馈，Agent 得以宣称写入成功。

## 修复

- `workbench/bridge/conversations.py`：`re.finditer` 遍历全部
  lessonkit-action 区块，按激活意图取第一个匹配区块（此后非匹配区块不再
  遮蔽后续区块）；被忽略时从镜像答案中剥离区块并记 `ignored` 披露，
  `_last_check_outcome` 新增「未被接受」状态——下一轮上下文明确告知
  「未写入任何内容，不要声称已写入」。匹配意图但被字段契约丢弃的动作
  （如无可用标题的目标表单）保持按 spec 静默丢弃。
- `workbench/server/static/workbench.js`：check_intent 正则扩充
  `(?:补|加|写|生成)[^。？?]{0,6}(?:闪卡|微题|题|卡)`，「补两张闪卡」「生成
  几道微题」均触发；「这张闪卡是什么意思」不误伤。

## 验证

- conv-023 回放单测：选区+manifest 双区块 → manifest 被解析应用。
- 忽略披露单测：ignored 交换的下一轮上下文含「未写入任何内容」。
- 浏览器意图测试：正向措辞触发、讨论措辞不触发（node 57 全绿）。
- openspec：`disclose-ignored-action-blocks`（ai-teacher-bridge +1 requirement）。
