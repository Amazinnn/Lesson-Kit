# remove-explain-diagnose 任务

## 1. 规格（PR1）

- [x] ai-teacher-bridge delta：REMOVED ×7（Task lifecycle / Output-contract /
      Explain / Teacher conduct / Diagnose / Bridge artifact locations /
      Practice-page one-click tasks）+ MODIFIED ×4（Purpose 收窄、Provider
      configuration、CLI data interface、Workbench without AI）
- [x] DISCUSSION-RECORD 专题 21 补记（问卷 A1/A3 决定 + 拆除范围）
- [x] `openspec validate remove-explain-diagnose --strict` 通过

## 2. 实现（PR2）

- [x] 任务机五模块删除（runner/teacher/contracts/providers/jobs）+ pool.explain_dir
- [x] API 四路由四 handler 删除；CLI `ai` 子命令删除（bridge add 保留）
- [x] 前端：按钮/状态/结果/门槛与轮询逻辑删除（card-nav 与横幅不涉）
- [x] 测试清理：整删 4 文件 + 方法删（test_api×3、test_cli×3、
      test_conversation_api×1、JS one-click×1）
- [x] `.lessonkit/explain/` 空目录删除
- [x] 文档同步：PRODUCT-MANUAL 8 章、ACTION-GRAPH 各层、GLOSSARY
- [x] pytest + node + validate + guards 全绿；explain/diagnose 残留 grep 为零

## 3. 走查与归档（PR2 内）

- [x] 3091 副本：作答后无讲解/诊断按钮；`/ai/explain`、`/ai/jobs` 404；
      对话面板可用（无 provider 降级文案正确）；四模式冒烟
- [x] 归档 change，`openspec list` 清空
