# 交接文档：前端愿景达成，进入真实学习测试（2026-09-02 夜）

> 新对话开场喂三件套：`AGENTS.md` + `docs/ARCHITECTURE.md` + 本文档。

## 一、当前状态（一句话版）

`Amazinnn/Lesson-Kit` main = `15cc2de`（本地同步、树干净、0 开放 PR、CI 双矩阵绿）。
基线：pytest **372**（1 例已知 Windows 并发 flake，重跑即过）/ node **107** /
`openspec validate --specs --strict` 11 通过、0 active changes、compileall、双 guard 全绿。
真实池 `pool/dmath.db`：66 卡 / 345 题 / 31 KP / 6 信号，Check schema 已迁移、候选表已退役。

## 二、本阶段完成的事情（2026-09-01/02 两天）

1. **前端批次 14 PR（#53–#67）合并**：设计契约（DESIGN.md）、目标月历跑道、紧凑
   自评、练习范围托盘、Agent 执行计划、图谱投影动画/状态分群/关系管道、蒙德里安
   基础、排版、14 天趋势线、双向闪卡（数据层 + UI）。合并时按 DESIGN.md §7 把
   学习状态投影统一为**关注优先级**（needs_work 最靠中心）。
2. **三轮所有者走查修订**（直接提交 main）：
   - 闪卡：方向收敛为会话级正向/反向（默认正向、删混合与 ⇄）、统一「完全重合
     双牌」+ 揭示漂移滑出编排（轻微倾斜、reduced-motion 直达终态）。
   - 日历：300px 侧轨 → 全宽区块，最终由 #68 重做（暖灰轻网格、黄/蓝细轨道、
     跨周箭头、单次标题；复习负荷柱顶准确值、总量/峰值/逾期摘要、零日无假柱）。
   - 图谱：定格前标签避让 + 微物理收敛（消除瞬移/离奇重叠）；拖放锚力强化
     （拖哪停哪）；`crowdedPairs` 拥挤自动松弛；聚拢滑杆引斥力联动（spread）；
     指标投影（题量/重要性/状态）**不渲染连线**；工具栏说明改悬浮浮窗；
     基础引力 0.0006 + 斥力 4200/9 修正外散内挤。
3. **演示通道**：scratch 配方（`LESSONKIT_WB_HOME` 隔离 + `%TEMP%\lessonkit-demo-0902`
   副本 + `wbhouse` 注册表 + 3082 端口）已验证可用——曾因注册表 course/chapter
   为空踩坑（所有前缀查询命不中→kp=0/图谱空白），修复后 31 KP/31 节点真实可见。
   演示服务器已停，scratch 目录可丢弃。

## 三、进入真实学习测试前要注意

- **真实服务器 3081 当前未运行**（本会话核实时无监听）。启动方式照 README：
  仓库根目录 `python -m workbench.cli.main serve`（3081 默认由注册表活动工作区
  决定；注册表已含 course=dmath、chapter=ch06）。真实池无需迁移，重启即用。
- **真实池至今零 Check 写入**：真实使用会通过对话出题（Check 门禁）与练习写入
  开始产出；写池唯一合法通道 = 门禁配方 apply（`wb ingest --apply --backup`）。
- **演示种子数据只存在于 scratch**：真实池的双向闪卡仍需真实材料产生
  （Check manifest 的 `directions` 字段），真实池当前卡全部默认为正向。
- 已知 flake：`test_successful_turn_mirrors_exchange_and_second_turn_resumes` /
  `test_successful_turn_restores_coalesced_execution_plan` 在 Windows 偶发
  PermissionError（测试线程读 turn json 时后台线程仍在写），重跑即过，未修。

## 四、真实使用观察清单（下阶段反馈入口）

- 出题链：给 KP 补闪卡/微题的 manifest 字段、批次与回滚、无幻觉申报。
- 目标/日历：目标开始日期、跨周跑道、重日预填的真实使用体验。
- Agent 执行计划：codex/claude 事件归一化在真实对话下的稳定性。
- 图谱：拖放/聚拢/投影的长期使用手感（含「连线只在关系结构」是否符合预期）。

## 五、下一步候选（未立项，勿主动开工）

1. **真实学习测试**（进行中，所有者主导）。
2. 综合题配方 × 真题拟合联合立项（等 Check 首期真实使用后启动，评估方法见
   FUTURE-DEVELOPMENT-NOTES 实验指标 + ADR 0018）。
3. 挂名池（需先走定义流程）：teacher 记忆消费端（机会主义）、速成模式视图、
   批量揭晓、扩展摘要、Obsidian 打包、图形资产工具。冻结：Scoropic（ADR 0021）。

## 六、纪律（不变）

- codex sub-agent ≤2 并行、文件集不交叉；分身中断先核对残留。
- spec 先行：行为变更先落 openspec change（strict）再动代码；新名词先过 GLOSSARY。
- 验证节奏照 AGENTS.md；交付前更新交接文档。
