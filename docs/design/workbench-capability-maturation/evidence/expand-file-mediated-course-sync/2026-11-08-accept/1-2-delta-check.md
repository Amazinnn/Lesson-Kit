# 1.2 delta 逐条核对（2026-11-08）

任务原文：> 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。

## 本包的 delta 全量清点

| delta 文件 | 操作 | 数量 |
|---|---|---|
| `specs/file-course-sync/spec.md` | ADDED（新能力，live 无该 capability） | 9 requirement |
| `specs/workbench-ui/spec.md` | MODIFIED | 1 requirement |
| 全部 delta | REMOVED / RENAMED | 0 |

新能力 9 条：Complete portable course assets、Governed file CRUD and identity、Reconcile versions and learning facts、Partial completion is recoverable、Git transport and hourly scheduling、External Tutor input and output preserve learning truth、Tutor file additions use the ordinary return path、Retained Paper item history travels with the course、A repeated operation returns its original result。

它们全都是 live 里不存在的**新**能力（`openspec/specs/file-course-sync/` 不存在），因此不存在"覆盖旧 requirement"的风险；归档时整能力并入。

## 唯一 MODIFIED 的核对：`Learner settings in the settings view`

| 项 | 结果 |
|---|---|
| 现行 live 场景 | The preference survives a restart · Off removes every rating surface · On keeps today's behavior · Reenable optional self-rating during a Paper |
| delta 是否保留全部 4 条（名称与内容） | 是，逐条保留，未改名 |
| delta 新增场景 | Received course preferences win over an old browser mirror · Preference persistence fails |
| 是否删改任何 live 场景 | 否 |

结论：MODIFIED 块完整保留旧场景并只做增量，符合"保持原场景名称或明确迁移"。

## 次级引用

- 全仓 `openspec/specs/**` 搜索 `course-preferences`、`reveal_timing`、`揭晓时机` → **无其他 live requirement 引用**该偏好语义，故没有需要同步的次级 spec 引用。
- 该偏好的**职责**落在 `FILE_CONTRACT.md`（`course-preferences.json` 工件）、`DATA_MODEL.md`（已确认投影与浏览器镜像的 writer/consumer）、`PRODUCT-MANUAL.md`（设置页说明）——三项均已在本分支同步，逐条见 `3-1-contract-sync.md`。
- CLI/动作面：`docs/action-graph/L2-interfaces.md` 新增 `course-sync` 命令与两条路由、`L3-actions.md` 新增两条动作（提交 `a5da09bf` 系列）。

## 顺序说明

本包的职责契约（GLOSSARY / DATA_MODEL / FILE_CONTRACT / ARCHITECTURE / PRODUCT-MANUAL / ACTION-GRAPH）在实现提交之前或同一提交内同步，提交序可见：`git log --oneline c5a9c642..HEAD -- docs/DATA_MODEL.md FILE_CONTRACT.md docs/GLOSSARY.md`。本轮补登不改任何 delta 内容，只固化核对结论。
