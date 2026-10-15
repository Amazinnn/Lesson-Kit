from pathlib import Path

entry = Path("docs/ACTION-GRAPH.md")
text = entry.read_text(encoding="utf-8")
old = "  P --> PULL & ANS & REV & PREV & RATE & END\n"
new = "  P --> PAPER & ANS & REV & PREV & RATE & END\n"
if text.count(old) != 1:
    raise SystemExit(f"ACTION-GRAPH stale PULL edge count={text.count(old)}")
entry.write_text(text.replace(old, new, 1), encoding="utf-8")

path = Path("docs/action-graph/L4-workflows.md")
text = path.read_text(encoding="utf-8")
start = text.index("## W1 · Paper → Practice Run 练习回路\n")
end = text.index("\n## W2 · 内容入库", start)
replacement = '''## W1 · Paper → Practice Run 练习回路

```mermaid
flowchart TD
  A[明确 Scope<br/>知识点页/图谱/建议/Agent] --> B[Paper Assembly<br/>来源·难度·薄弱·到期·错题]
  B --> C{组卷有内容?}
  C -- 否 --> C0[诚实空态<br/>调整 Scope/约束后重组] --> B
  C -- 是 --> D[冻结 Paper item 顺序]
  D --> E[开始 / 恢复 Practice Run]
  E --> F{当前 item 形式}
  F -- 闪卡 --> G[回忆→揭示]
  F -- 微题/判断 --> H[点选→本地判定]
  F -- 综合题 --> I[作答→揭示解析]
  F -- 跳过 --> N
  G & H & I --> J{当前自评设置}
  J -- immediate --> K[记录自评/学习结论]
  J -- batch --> L[保留待统一自评状态]
  J -- off --> M[按既有 off 规则结算]
  K & L & M --> N{Paper 还有 pending item?}
  N -- 有 --> F
  N -- 无 --> O{需要 batch 收束?}
  O -- 是 --> P[统一自评收束页] --> Q[归档 Practice Run]
  O -- 否 --> Q
  E -- 提前结束 --> O
  Q --> R{再练同类?}
  R -- 是 --> B2[据结果与 Scope<br/>重新组新 Paper] --> C
  R -- 否 --> S[回练习出发页]
  X1[中途刷新] -.恢复 frozen items + cursor<br/>不重新组卷.-> E
  X2[直接关标签页] -.已落盘结算保留<br/>未提交草稿按既有恢复策略.-> Z[(当前 Paper 不变)]
  X3[网络失败] -.原位报错 + 重试<br/>不换 Paper.-> E
  X4[运行中改 Scope/筛选/章透镜] -.只影响下次组卷.-> B
  X5[练习页发消息问 Agent] -.只带聚焦上下文·零写入.-> Z
```

核心不变量：**Scope 回答想练什么，Paper 回答这次具体做什么，Practice Run 只负责把这张 Paper 做完。**
任何建议、筛选、调度或对话都不得向运行中的 Paper 动态加题；“再练同类”永远组新 Paper。
刷新恢复 frozen items 与游标而不重新组卷；提前结束仍走既有 batch 收束规则；网络失败原位重试；
直接关闭只保留已经落盘的事实。跳过继续保持现有“不凭空写学习证据”的语义。
'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

Path(".github/workflows/one-shot-fix-paper-doc-workflows.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-fix-paper-doc-workflows.py").unlink()
