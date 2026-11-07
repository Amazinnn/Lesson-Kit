## Context

完整课程交换与外部 Tutor 交接 follows Q002/Q005–Q020/Q080/Q082–Q083/Q097/Q099–Q102/Q105–Q106；S007–S010. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp01.md.

## Goals / Non-Goals

本包目标以 specs/file-course-sync/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 交换与身份

复用已有 mirror 投影与 figure 读取，新增 course_sync 只编排缺少的全课程能力。`domain.course_sync.plan_exchange(base, local, incoming)` 接收纯 Python 投影，返回有序独立单元、冲突和校验结果，不读文件。Data 负责 `export_course(pool, workspace, destination)`、`inspect_exchange(pool, workspace, source)` 和 `apply_exchange(pool, workspace, plan, choices)`，实际签名复用 Pool/字典习惯，在实现前登记 FILE_CONTRACT。

格式 v1 使用 data-exchange-matrix 的 manifest。每个跨端记录使用持久来源身份与原记录号，本机 SQLite 自增 ID 经映射转换。新安装分配一次可读来源标识并与课程来源分开保存，不哈希、不以当前行号误认另一台机器的记录。课程复制保留课程来源，目标安装保留自身安装来源。相同可读内容 ID 的独立新增要按来源区别并报告冲突或明确映射，不覆盖既有历史。

基线保存每资产最近共同投影。比较实际字段/字节，忽略传输元数据造成的伪冲突。单侧自动协调、同改一致自动收敛。作答合并按来源记录身份去重。草稿按执行和题目位置比较，不对整库或整卷取最近时间。学习投影使用原 writer 语义重建/协调，所有评分副作用必须由操作身份去重。

### 内容与文件一致性

按依赖拆独立单元，预检记录所有问题后可执行有效单元。文件写入使用同根临时文件和原子替换，单元内保留失败恢复需要的前值与发布步骤，受同课程写锁保护；写数据库只由 Data 完成。失败补偿仅恢复当前未成功单元的数据一致性，已成功独立单元保留。发布与数据库提交每个边界均注入故障验证，回执记录实际完成边界；再次执行用原操作身份续办，不重新派发已完成的 provider 作业。成功批次无撤销命令。

课程学习文件先用相对路径的原文管理和类型元数据，无需把每种 Markdown 主题拆表。机器路径字段替换为可解析逻辑引用，不能盲目复制旧路径。浏览器偏好建立显式课程持久 writer/reader，CLI 能核对最后保存值，接收端正常入口实际消费。工作区默认继续上次位置，原生 Provider 会话仍单列。

### CLI、Git与定时

在 installed CLI 注册 `course-sync` 扩展，子命令 `export`、`receive`、`check`、`sync`、`status`、`schedule install|remove|enable|disable`。这是拟议新接口，现有 mirror 保留。单课显式 workspace/repo，定时可用 `--all-configured`，接收选择 `--keep local|incoming` 仅作用于真实冲突，也可读逐项 choices JSON。check 只读。统一 JSON 回执，普通脚本无需解析自然语言。

回执顶层 status 为 success/partial/conflict/failed，包含 local/remote 结果、课程来源、资产数、操作身份及逐项变化。退出码0完整成功、2输入或格式错误、3需要冲突选侧、4部分完成或传输失败。遇到多种情况优先返回2、再3、再4，逐项完整结果不丢。单次多课程调度记录各课程退出码，任一受阻总结果非0。每课程仅保留最新完整回执，不建同步历史浏览平台。

Git 使用系统 git 子进程，显式 cwd 和参数数组，只暂存受管理路径。拉取远端、文件协调、提交、推送、远端回读分步记录。网络失败不切换另一种同步实现。平台任务计划调用同一已安装命令和显式配置，标准 Windows 能力实现每小时，通知只针对新待选侧冲突且去重。安装/更新/停用/移除任务必须实操。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 SYNC-01–08、FS-01–11、LP-01/02 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。

### Receive checkpoint correction (2026-11-07)

The sidecar cannot acknowledge rows before their SQLite commit. `course_sync_checkpoint` holds a compacted state baseline, and `course_sync_units` holds per-asset overrides (`identity`, `asset_json`, `mappings_json`, nullable `pending_json`). Each bounded chunk commits only new mappings and acknowledgements with its data; each independent unit has a SQLite savepoint. Reading overlays unit records; compaction writes a full baseline and removes completed overrides atomically, preserving pending file intents. The sidecar is copied at operation boundaries. Local bookkeeping is excluded from course projections. Standalone and installed migration helpers remain independently importable and have a schema parity check.

File changes commit validated publication intents before touching destination bytes. Publication and intent clearing are idempotent across interruption. Unwritable files remain pending and produce partial receipts; independent receive units proceed. Read-only check projects committed pending content without writing it, and reports pending publication. A missing sidecar does not reset lineage. Failed row units discard tentative mappings and block their dependents. Execution header and grouped item acknowledgements share the header transaction; invalid dependent items cannot be acknowledged by another unit.

A receive with conflicts, rejected assets or incomplete dependencies never replaces or publishes the medium package. Git/runtime failures retain truthful receipts and do not stop unrelated configured courses. Managed publication includes readable files and deletions of obsolete tracked envelopes. Remote materialization includes the readable view so Tutor-only file edits travel back. After complete reception, Git fast-forwards media ancestry before export; true Git divergence remains explicit, with no reset or force push. Notification text is process data and resolution re-arms notification.

Initial 1,000-row profiling exposed whole-state-per-unit persistence overhead (30.541s); incremental overrides reduced a subsequent pilot to 9.235s. These concurrent-environment single runs are diagnostic evidence, not the F2 p95 benchmark. Whole-package acceptance still requires the full crash matrix, reference audit, F2 and actual release-entry evidence.

WP01 inspection carries a connection-local SQLite change guard. Apply checks it before writes and under each bounded chunk's write transaction; intervening local edits cannot be overwritten by an inspection snapshot. A stale inspection requires a fresh check, preserving already committed independent units. An unresolved file intent blocks newer changes to the same asset while other identities proceed; there is never more than one durable publication intent per identity. Malformed execution items are isolated during package validation, including content-less tombstones that the execution writer cannot represent.

Received file identities remain managed on subsequent exports without copying device-specific media configuration. Existing source bytes are read from the acknowledged relative path, and an acknowledged explicit tombstone is re-emitted while its entity is absent. Missing live assets are reported before export publication; absence never manufactures a tombstone. This closes multi-hop attachment and explicit-deletion propagation, while local hard-delete writers still need explicit deletion recording under the content-operations reconciliation.

### Native scheduled-task binding correction (2026-11-07)

Task creation uses the standard Windows task XML with an explicit Python executable, module arguments and source working directory. The receipt records these values; a source/import preflight from that directory must succeed before installation. The bridge owns task XML and bounded hidden subprocess execution; CLI retains only orchestration. Media configuration is written only after successful task creation. Global installation requires at least one fully configured course; partial repo/package pairs are invalid. Notification failures are reported as not delivered and cannot erase completed synchronization results. No alternative scheduler or silent runtime substitution is introduced.

### Measured F2 transport correction (2026-11-07)

The full-size diagnostic (run05) failed export/receive/unchanged-inspect gates. Reduce file-system work using grouped JSON for packages above512 assets: format_version2 descriptors retain identity/kind/depends_on and path, adding member=identity. A grouped file is {"assets": {identity: envelope}}. Files target at most256 assets and8MiB serialized payload (one larger envelope remains whole). Small packages continue version1; version1 remains readable regardless of size. This deterministic size choice is serialization, never an error-triggered fallback. No ZIP, compression, hashes, dependencies or opaque binary container is needed. A read caches each grouped file once, validates unique (path,member) pairs, safe relative paths and exact membership, and isolates corrupt/missing groups to their dependent assets. An unchanged version2 image reuses all descriptors/generation; a changed large image writes a fresh generation before manifest publication, then cleans only prior owned files. Readable file views remain unchanged. Git materializes/stages unique physical paths and readable copies rather than treating member as a filesystem path.

Receive throughput uses bounded outer transactions (up to128 independent units), with a native SQLite SAVEPOINT around each unit. Invalid units roll back only their savepoint and block dependents. A chunk's data, identity mappings and acknowledgements commit together before its files publish or its success appears in the receipt. A failed chunk commit acknowledges none of that chunk, while prior committed chunks survive; later independent chunks can proceed. This changes durability grouping, not the retirement of successful-batch undo. Publication-intent clearing can share a transaction after durable atomic publication. The stale-inspection guard is checked under each chunk write lock. Fault tests must cover unit savepoint failure, chunk commit failure, publication failure and retry without duplicate histories before this optimization is accepted.

Receive durability is grouped into bounded chunks of at most128 ordered units. Each unit has a SQLite savepoint; its failed writes and tentative mappings are discarded without undoing valid neighbors. Only a physically committed chunk advances in-memory acknowledgement and success receipts. Commit failure retains prior committed chunks and marks the failed chunk for retry. File units are grouped separately and their durable intents are published before following database units that depend on them; publication failure blocks those dependents. Successfully published intents are cleared together in one transaction, and interrupted clearing safely republishes the same bytes/deletion. No successful-batch undo is introduced.

### Crash-owned lock correction (2026-11-07)

An isolated os._exit probe left the O_EXCL marker behind and made the next exchange permanently refuse. Exchange and installation-origin initialization locks use a held native file lock (Windows msvcrt, POSIX flock) instead of marker-file existence. The OS releases ownership on process death; retained empty lock files carry no ownership and are never unlinked as a recovery heuristic. Busy locks still refuse concurrent writers. No PID liveness guessing, forced deletion, fallback synchronization or extra dependency is introduced.

### Tutor new-file discovery correction (2026-11-07)

A real zero-cost DeepSeek free-model continuation returned a valid new learning note; receive incorrectly reported success without importing it, because only predeclared envelopes were scanned. Q006/Q106 and the Tutor handoff require new files to roundtrip without hand-editing manifests. A newly created ordinary file under the readable files tree explicitly declares a new safe relative-path file identity. Readable absence is never deletion, undeclared files cannot override invalid declared assets, and excluded paths/database bytes are never accepted. Known files retain their existing envelope identities. The prior restriction in FILE_CONTRACT is superseded within WP01; no new user-facing panel or approval is added.

### New-device receive orchestration (2026-11-07)

`course-sync <new-workspace> receive --from <package> --to <new-directory>` validates the package/course identity before creating any target. Data reuses the canonical course initializer; CLI registers the resulting empty course and uses the same inspect/apply path. Existing registered targets reject a mismatching --to path instead of changing the registry. Existing database directories cannot be silently adopted through this creation path. Source and target trees must be separate. Check never initializes or registers. The receive receipt records new registration and any actually required configuration; course media is optional for plain-file handoff. Bootstrap failure remains explicit, with no invented SQL/schema fallback.
