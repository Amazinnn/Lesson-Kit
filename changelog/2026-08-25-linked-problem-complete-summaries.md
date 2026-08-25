# 关联题完整摘要

## 最终行为

- 知识点关联题以短标题为主文本；仅规范化题干超过 300 字时显示完整中文单句摘要。
- 关联题不再运行时截断题干，也不显示原始题目 ID；学生可按需展开完整题干。
- `problems` 与 `candidate_problems` 增加可空 `display_summary`，并由受版本控制的题目展示元数据清单重复回填。
- dmath ch06 清单覆盖 303 道正式题，其中 62 道长题具有摘要；人工抽检 30 道，覆盖全部 9 个摘要主题。

## 验证证据

- `python -m pytest tests -q`：179 passed。
- `node --check workbench/server/static/workbench.js`：通过。
- `openspec validate linked-problem-complete-summaries --strict`：通过。
- `python lessonkit.py guard extract-problems --course dmath --chapter ch06`：PASS。
- `python lessonkit.py guard problem-set --course dmath --chapter ch06`：PASS。
- `:3081` HTTP 冒烟：知识点页面返回 200，显示长题摘要与完整题干入口，关联题区域不显示原始题目 ID。
