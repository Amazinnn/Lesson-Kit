# 紧急交接：2026-11-07，约15:51（北京时间）

用户因额度要求立即停止继续实现并就地写交接，明确要求不再检查进度。本记录完全基于中断前已知状态；未重新查询Git、进程、worker结果或测试。后台进程可能继续运行，接手者先核对终态，禁止重复派发超过4路。本文不表示任务完成。

## 先读与边界

本文件是最新续跑入口，随后读同目录 STATUS.md、HANDOFF-2026-11-07.md、execution-guide.md、contract-reconciliation.md，以及实际工作树AGENTS.md和docs/ARCHITECTURE.md。用户授权继续实现六个工作包，近期首要任务是完整文件/Git课程同步，仍在WP01；其余工作包没有完成。遵守OpenSpec、Ponytail、Grill With Docs、Ask User Question、lesson-kit-dev、subagent-concurrency。

Shell → Domain → Data，SQLite只在Data；Domain零IO，Bridge只做媒介。保留现有数据、能力和入口，不碰冻结pipeline/pool/lessonkit行为契约。用户明确取消项目审批关卡、默认直接执行；不引入成功批次撤销。UI不加常驻注释，后端不加掩错fallback，不引入新哈希或依赖。不启动本机决策模型。真实模型验收仅免费API；Go worker不是免费验收。

## 实际工作位置与提交

- 实现工作树：`D:\.codex\worktrees\course-sync\lesson-kit`，分支`codex/course-sync`。
- 原工作树：`D:\Projects\Academic Workflow\lesson-kit`，main最后已知`c5a9c642`；未合并、未推送、未切换运行时，editable安装仍指向原main。
- 最新已知HEAD：`cb43e860`。
- 本次续跑新增提交：`d4a01e0a`独立分组JSON编解码模块；`f48e9b44`规范新课程建库模块；`cb43e860`纯Domain引用转换模块。这些模块并不等于已接入完整同步。
- 之前重要提交：`95b1cef6`导出回执详情、`a9953d61`F2字节证据、`d1c9b44f`有界接收事务、`df4118a8`原生任务启动绑定/测试隔离、`9e24990c`多跳附件/删除、`5d11d979`持久接收检查点。
- 未跟踪的`docs/design/workbench-capability-maturation/debug.log`不是本任务产物，勿清理/加入提交。
- 暂存和提交始终指定精确路径，两者均带路径，勿收进并发worker改动。

## 后台代理：最后已知4路，尚未再次检查

全部为外部DeepSeek Harness，OpenCode Go `deepseek-v4.1-flash`，上限4；不要替换成内置GPT代理。权威调度台账`tmp/agent-runs/todo.md`，任务书`tmp/agent-briefs/<ID>.md`。runner为`tmp/agent-runs/run_worker.py`，patch为`tmp/agent-runs/<ID>.patch.yml`。不要读整份stderr/stdout推理转写；优先终态JSON、落盘报告和产物。

|ID|最后会话|所有权/状态|
|---|---|---|
|C05|23841|只读审查core接收事务；仅tmp/C05报告和探测。15:50前仍未见最终报告。**实际core course_sync.py自d1c9b44f保持不动供它审查**。等终态报告后才写实际core，不能中途破坏审查快照。|
|G06|87075|仅`workbench/bridge/git_sync.py`、新`tests/workbench/test_git_sync_tree.py`、G06报告。实现`list_remote_files(repo,commit,directory)`，让Git能发现Tutor仅在files/新增的文件。15:50实际源码与测试已出现，未验收/未见终态。|
|B06|75905|独立只读审查已提交course_bundle编解码；只写tmp报告/探测，不要求core冻结。|
|R06|67993|只读审查操作重放指纹、历史缓存显示编号、判分会话机器绑定；只写tmp报告/探测，不要求core冻结。|

已完成：B04(exit0，15:31)、N05(exit0，15:45:25)、R04(exit0，15:47:07)，代码已分别提交。报告均在tmp/agent-runs。R04/N05都自行跑过全仓，17失败/1500通过；13个Pi子进程环境失败和当时4个协调者故意补的失败回归。不要把“HEAD不存在该测试”说成“该测试在HEAD通过”。最终全仓必须带PYTHONUTF8=1重跑。

Provider最后探测15:40—15:41六次全部HTTP200/有效；之前恢复观察已完成。最后内存采样15:48：总33027448KiB，空闲10194844KiB，约69%使用；均文本任务，无浏览器/GPU。用户指令本次不查进度，因此未更新这些状态。

## 非worker后台命令

- 完整规模**独立草稿**性能诊断会话`73334`：运行`tmp/agent-runs/profile_f2_grouped_draft.py`，输出`tmp/agent-runs/f2-grouped-draft-profile.json`。15:50前仅看到fixture3.616s，其余未知。它通过模块注入测试草稿，不是实际core；不要冒充交付性能。进程可能仍在运行。
- 草稿组合测试会话62101已经退出0：61 passed in34.07s。
- 旧provider探测78821已完成输出6/6；无需重复接收未变化结果。

## 最重要：修复草稿尚未写入实际core

`tmp/agent-runs/core-lock-path-lineage-preview.py`是实际core的完整候选副本。它通过importlib注入`workbench.data.course_sync`后测试；不是正式源码，不能误认为已上线。C05审查结束后先看报告、对照差异，再把通过检查的改动合入实际`workbench/data/course_sync.py`。实际core从上次保持冻结，没有被此轮改写。

草稿已包含：

1. `course_sync_lock.exclusive`原生OS拥有的文件锁，取代O_EXCL遗留标记；进程死亡自动释放，不删稳定锁文件，也不猜PID。新helper本身在实际工作树未提交。
2. `_file_payload(...,db_path=...)`在记录意图和恢复发布前禁止覆盖打开的课程DB。
3. 任何非空且来源未证实的已有课程都必须显式关联，去掉“没有checkpoint表就直接关联”的绕过；显式关联后实际记住包的course origin。
4. 删除资产不再保留/重新写可读明文副本。
5. 分组包接入export/read：<=512项版本1，>512项版本2；分组JSON compact，加载每物理文件一次。布局版本改变即使内容相同也强制新export_id，防止写分组文件时覆盖旧清单引用的逐文件。
6. `files/`普通新增文件自动成为明确`file/<relative>`创建，应用路径/保密/运行文件排除；缺文件不当删除；已声明但无效的信封不能被明文副本绕过。现有编辑副本仍优先使用。
7. inspect携带投影row_identities；apply仅持久化plan unchanged的已确认映射，修复“已存在相同作答、执行导入找不到整数引用”。新增回归已复现实际core失败、草稿通过。
8. R04 typed helper接入已声明JSON列，用writer对应JSON拼写恢复缓存；删除按任意key递归改写的local_nested。执行item小问draft的attempt引用也转换并纳入依赖，原始答案/笔记/判分payload保持原值。

草稿验证：锁/DB路径/来源/删除子集11 passed；分组导出与布局迁移中断2 passed；Tutor handoff4 passed；后续data+execution+receive组合61 passed in34.07s。未做草稿完整全仓。更早组合3失败/63通过已针对修复：旧测试mock需接受indent kwargs、已有目标初次关联要显式输入、已有事实映射缺失；最新61项覆盖相关改动但不是所有前述66项完整重跑。

## 实际工作树尚未提交的协调者工作

最后已知dirty：FILE_CONTRACT.md、docs/ACTION-GRAPH.md、docs/PRODUCT-MANUAL.md、docs/action-graph/L2-interfaces.md、program contract-reconciliation.md、active change design/spec、tests的course_sync_cli/data/receive/tutor_handoff、workbench/cli/course_sync.py；未跟踪course_sync_lock helper/test；G06正写git_sync.py和test_git_sync_tree.py。debug.log另属未知。

CLI改动已经在实际文件：

- `receive 新工作区 --from 包 --to 新目录`：先read_exchange验证，再调用course_workspace.bootstrap规范建库，注册工作区后正常receive；与包目录分离，已注册目标--to必须相同目录。规范脚本不在wheel时明确失败，没有伪schema fallback。
- 接收提交边界OSError/RuntimeError/sqlite3.Error写本次partial回执，operation新ID、local.verification_required=true，不虚报成功也不沿用旧回执。
- 顶层RuntimeError/sqlite错误JSON退出4。
- `_package_paths`改为read_exchange加载一次/取文件、物理路径去重，支持未来分组；materialize wanted路径也去重。
- **还没有把G06新目录枚举接到_materialize**。现在_materialize只取已声明明文副本，因此仍会漏收Git中新增无信封的Tutor文件。等待G06结束后集成：列举固定commit下prefix+files/全部常规文件，读取后写staging；保持路径校验/不跟symlink，随后read_exchange才能发现新文件。

CLI全量24 passed in67.29s发生于新Git-note回归加入之前。该新回归`test_sync_receives_new_tutor_file_from_git_without_envelope_edit`已明确失败（CLI成功但本地文件不存在），待修。不能引用24通过冒充当前CLI全绿。

正式新增回归：
- data::test_large_export_groups_assets_and_reuses_unchanged_files（实际core仍失败，草稿通过）
- data::test_layout_transition_never_overwrites_files_of_published_generation（实际core仍失败，草稿通过）
- receive::test_incoming_file_cannot_replace_the_open_course_database
- receive::test_untracked_nonempty_course_requires_explicit_lineage_association
- receive::test_associated_existing_facts_keep_execution_references（实际core失败，草稿通过）
- receive::test_grouped_execution_waits_for_new_attempt_dependency（现状通过；不是失败复现，勿误述）
- data::test_export_does_not_keep_readable_copy_of_deleted_file
- tutor::test_new_tutor_learning_file_is_received_without_hand_editing_manifest
- lock::test_public_course_lock_releases_after_process_death

## Worker交付模块

- course_bundle.py：B04 codec15项，协调者15 passed3.80s；pack返回format_version/descriptors/files/written/reused，load返回assets/errors。版本2descriptor带member=identity；最多256项/目标8MiB/单大项完整。仅模块已提交。布局变更强制新generation是协调者草稿补的。B06独立审查未回。
- course_workspace.py：N05规范建库，17项；先拒绝已有pool，规范脚本路径缺失则明确RuntimeError，不fallback。CLI编排由协调者完成。并发首次建库第二路明确失败，无内部锁，注册仍CLI所有。
- domain/course_sync_references.py：R04纯转换，33项。完整API和精确writer路径见R04-report.md。只处理声明路径，serialize_json仅在值真的变化时调用。cached display copy IDs/feedback_event_id、fingerprint/batch_fingerprint、grading job机器会话、同attempt同revision冲突仍未解决，R06审查前三类。
- N05/R04合计协调者50 passed in1.42s（随后无改动又重跑1.32s，同样通过，不要据此扩张验收范围）。

## C05已知落盘探测，报告未回，勿先当最终结论

`tmp/agent-runs/C05-results.json`存在；部分结果：
- P1证实unassigned来源绕过；草稿已修。
- P2/P4已存在相同作答映射缺失让执行导入部分失败，重试顺序还可能有分组依赖问题。草稿只已修unchanged映射；必须看C05最终归因再补真正group dependency情况。
- P3 stale guard保留先前128项，后续失败且保护本地更新；P5检查后本地draft修改被拒绝覆盖。
- P6直接传入坏execution_item无position会KeyError并已保存checkpoint；正常read_exchange已拦截，是否属于公共apply校验缺口看最终报告。
- C05-p2-debug.py、C05-parent-compare.py、C05-probe.py都有小型临时探测。不要重做其已证明审查；复核修复针对结论。

## 真实免费Tutor验收与草稿重放

原始真实免费调用仍保存在`tmp/agent-runs/free-tutor/`。模型OpenCode官方free `deepseek-v4.1-flash-free`，实际一请求13.501s、进程0、报告cost0，读目标/未答p-2/原始答案与choices/当前Paper位置正确，生成新笔记并区分事实和推测。但实际core接收返回成功却漏笔记，原报告因此incomplete。第一轮启动CLI参数错发生在模型调用前，不能计作一次真实调用。

不要重跑始终调用API的free_tutor_roundtrip.py。新脚本`tmp/agent-runs/free_tutor_replay.py`使用已保存response.json，确认fresh fixture handoff与源笔记完全相同，调用数0。15:46对**草稿注入**重放通过：原始作答不变、新笔记接收、再导出字节保留。结果`tmp/agent-runs/free-tutor-replay/report.json`已明确标source_under_test=isolated draft。正式源码修复后再跑该重放并保留原始失败证据，不覆盖成最初成功。

## 性能和其他验收边界

最近已提交F2 run07：完整20章节/1000KP/10000题/100卷/10000作答/30未完成/500笔记/100MiB附件，接收15.854s（单次），导出141.822s、无变化检查58.180s均失败；700文件105859984字节全相同、30表计数相同、24790项unchanged。不是20次/p95。新的草稿分组诊断73334结果未知，接手先读落盘JSON。

真实native Task验证run06曾纠正旧测试误建真实Task：已核验、停用删除；新独立命名临时Task做安装/更新/启停/真实隔离CLI运行/移除，无常驻任务。不要再称“从未操作系统任务”。现有任务测试已mock。尚需已配置课程真实调度/通知展示、GitHub专用远端、真实浏览器、旧课程迁移、完整F1/F3/F4/20次p95和独立最终验收。

全仓最后协调者旧中间版本1420 passed449.21s，不是当前最新版。此轮active change strict和compileall在15:42通过。最终完成必须新跑PYTHONUTF8=1 pytest tests -q、compileall、openspec validate --specs --strict、extract-problems guard，必要Node/实际交互；problem-set guard仅有已生成对应输出时跑。

## 下一棒具体顺序

1. 用户本次要求立即停写交接，故本记录后停止；接手获准续跑后先数todo/核终态、读C05/G06/B06/R06最终落盘，不能假定后台已停。
2. C05结束后对照草稿与正式core差异，把已验证修正合入实际core；先解决C05新证明问题。不要直接复制草稿覆盖后来任何他人改动，先看实际diff。
3. G06结束后接入_materialize远端files目录全部文件，跑本地Git无信封新增笔记回归；确保分组物理路径只读一次/暂存一次。
4. 按R06解决操作重放与机器会话绑定，真实已有writer校验接线；同attempt revision冲突、知识点删除保题/解关联（现有_delete_kp仍可能归档失去最后KP的题，违背Q011）、本地显式删除日志仍未完成。
5. 正式source免费输出重放、完整规模性能重测，保存真实证据；不要降低性能门槛。
6. 契约同步职责文件，记录实际当前与尚未实现，精确路径小提交；更新STATUS/handoff。tasks仍2/19，不要依据模块通过就批量勾选。
7. 不自动合并到main、不启动主服务、不动活跃课程。当前隔离实现尚未交付；六个包远未完成。
