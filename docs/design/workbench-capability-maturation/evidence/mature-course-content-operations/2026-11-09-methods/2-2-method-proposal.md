# WP02 2.2 方法提案：同义复用优先 + 治理新建 + 原题关联

任务原文：> 复用 ingest content-bundle 提炼模型，先查同义已有点；新增点含条件/公式/步骤并自动给适用原题追加关联。8个标注案例覆盖已有点、新模型与反例。

Spec 场景（knowledge-content-operations「Practice-derived method knowledge」）：练习中总结的可复用方法/公式/算法经治理路径入池；等价内容已存在则复用既有身份并扩展关联；分类不确定不创建。

## 实现（复用既有治理路径，不新增第二套写池通道）

`workbench/data/content.py`：

| 函数 | 行为 |
|---|---|
| `normalize_knowledge_title` | 折叠大小写、空白与标点（`casefold` + 非 \w 字符剔除），同义标题比较用 |
| `find_equivalent_kp` | 返回折叠标题相同的既有知识点 |
| `apply_method_proposal` | ① 拒收规则：`knowledge_item`/`body` 必填、`knowledge_type` 必须是 method-modeling / formula-calculation / algorithm-process（**分类不确定即拒收零写入**）、未知题号整体拒收；② 同义命中 1 个 → **复用既有身份**（不改正文），命中多个 → 拒收并点名全部 id（要求人工裁决）；③ 未命中 → 经既有治理路径 `content.create(kp, …)` 新建；④ `problem_ids` 的原题在事务内**追加**该知识点（既有关联全保留，缺号前置校验） |

`METHOD_KNOWLEDGE_TYPES` 是 2.4 后 `KP_TYPES` 的方法类子集；提案不接受 concept-property 等事实类。

入口：`lesson-kit data <工作区> method kp --input <提案.json>`（Agent 面）；文档同步 L2-interfaces、GLOSSARY（新增「方法提案 / Method proposal」）、PRODUCT-MANUAL（方法提案段）、ACTION-GRAPH 2026-11-09 留痕、agent_contracts（"an equivalent knowledge point is reused instead of created, and the classification is never guessed"）。

## 8 个标注案例（`tests/workbench/test_method_proposal.py`，10 passed）

| # | 案例 | 断言 | 用例 |
|---|---|---|---|
| 1 | 模型不在教材标题中 → 治理路径新建 | 返回 `reused=False`，落库行 `knowledge_type=method-modeling`，正文含「适用条件」 | `test_an_absent_model_is_created_through_the_governed_path` |
| 2 | 等价内容已存在（仅大小写/标点/空格不同）→ 复用既有身份 | `reused=True`、同一 `kp_id`、正文未被改写、知识点总数不增 | `test_equivalent_content_reuses_the_existing_identity` |
| 3 | 复用时适用原题自动追加关联 | 原题 `kp_ids` 从 `[kp-001]` 变为 `[kp-001, 新方法]`，`associations_added=1` | `test_reuse_extends_the_applicable_problems` |
| 4 | 关联保留既有关联且重复提案幂等 | 第二次、第三次提案 `associations_added` 1→0，列表不被覆盖 | `test_associations_retain_the_valid_existing_ones` |
| 5 | 分类不确定（无 knowledge_type）→ 拒收零写入 | ValueError "uncertain classification"，知识点总数不变 | `test_an_uncertain_classification_is_not_created` |
| 6 | 反例：concept-property 不是方法提案 | 拒收并要求三类之一 | `test_a_non_method_type_is_refused` |
| 7 | 反例：空正文（无条件/公式/步骤）→ 拒收 | "body" 原因 | `test_an_empty_body_is_refused` |
| 8 | 关联题号不存在 → 整份提案拒收零写入 | ValueError 点名题号，知识点总数不变 | `test_unknown_problems_refuse_the_whole_proposal` |

另两条支撑用例：同义多命中拒收并点名（`test_ambiguous_equivalents_demand_a_decision`）；CLI 端到端（`data method kp --json` 返回 reused/associations_added）。

## 边界

- 同义判定 = 折叠标题精确相等；正文相似度不做启发式（宁可多报 ambiguous 让人裁决，不静默合并）。
- 新建走当前章透镜发号（提案不携带章）；跨章移动用 2.3 的 `data move kp`。
- 部分成功的中间态不存在：关联题号前置校验，拒收发生在任何写入之前。
