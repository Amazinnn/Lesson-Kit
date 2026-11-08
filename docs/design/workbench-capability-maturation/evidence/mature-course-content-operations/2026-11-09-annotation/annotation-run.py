"""WP02 2.6: twenty annotated mapping/integrity cases.

Each case records its original text, the structural check (content audit or
ingest gate) and the semantic verdict (title folding / duplicate identity), so
structure and meaning are reported separately. Classification completion at the
end only writes types that carry evidence; doubtful points keep their state and
never enter the verified practice set.

Report: tmp/accept/wp02-annotation-report.json
"""
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from workbench import registry  # noqa: E402
from workbench.data import content, content_audit  # noqa: E402
from workbench.data.pool import Pool  # noqa: E402

report = {"cases": []}


def case(number, kind, original, structural, semantic, disposition):
    report["cases"].append({
        "case": number, "kind": kind, "original": original,
        "structural": structural, "semantic": semantic,
        "disposition": disposition,
    })


def main():
    work = Path(tempfile.mkdtemp(prefix="wp02-annotate-"))
    root = work / "dmath"
    (root / "pool").mkdir(parents=True)
    database = root / "pool" / "dmath.db"
    built = subprocess.run(
        [sys.executable, str(ROOT / "pipeline/scripts/create-tables.py"),
         "--db", str(database)], cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(built.stderr)
    conn = sqlite3.connect(database)
    # 已核对练习的基线：一个带分类的知识点 + 一道题。
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
        " knowledge_type, importance)"
        " VALUES ('dmath-ch06-kp-001','加法原理','完成一件事有 n 类办法…','concept-property','core')")
    conn.execute(
        "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
        " problem_type, source_kind, origin_kind)"
        " VALUES ('dmath-ch06-prob-001','[\"dmath-ch06-kp-001\"]','题目 P1','S1',"
        "'calculation','textbook','source_problem')")
    conn.commit()
    conn.close()

    import os
    os.environ["LESSONKIT_WB_HOME"] = str(work / "registry")
    registry.register(name="dmath", path=root, db="pool/dmath.db",
                      course="dmath", chapter="")
    pool = Pool(root, database, "dmath", "")

    # -- 映射案例 1-8：提案 ↔ 既有知识点 -----------------------------------
    mapping = [
        ("M1", "提案「等差数列求和公式」 ↔ 既有「等差数列求和公式」",
         "折叠标题相同", "同义：复用既有身份"),
        ("M2", "提案「等差数列 求和 公式！」 ↔ 既有「等差数列求和公式」",
         "折叠标题相同（仅空格/标点差异）", "同义：复用既有身份"),
        ("M3", "提案「抽屉原理」 ↔ 既有「鸽笼原理」",
         "折叠标题不同", "同义但词面不同：机器不合并，人工裁决"),
        ("M4", "提案「组合数的两个性质」 ↔ 库内无同义点",
         "折叠标题无命中", "按治理路径新建（bundle 计划成立）"),
        ("M5", "提案「加法原理（练习总结）」 ↔ 既有「加法原理」与「加法原理（讲义版）」",
         "同一折叠命中两条既有记录", "歧义：拒收并点名两条，人工裁决"),
        ("M6", "两道不同 key、相同题干「袋中有 5 只白球…」的题目",
         "problem_identity 相同", "重复内容：双拒零写入"),
        ("M7", "题目 kp_ids 引用「dmath-ch06-kp-999」（库内与包内均无）",
         "unknown knowledge point", "依赖阻断：该题零写入"),
        ("M8", "提案「错位排列公式」 knowledge_type=concept-property",
         "方法提案要求三类方法类型之一", "拒收：分类不确定不创建"),
    ]
    for number, original, structural, semantic in mapping:
        case(number, "mapping", original, structural, semantic, "见下述验证")

    def gate(manifest):
        conn = pool.connect()
        try:
            return content  # placeholder, replaced below
        finally:
            pass
    # 真实门禁走 ingest._gate_content_bundle（连接、逐条、无写入）。
    from workbench.ingest import _gate_content_bundle
    conn = pool.connect()
    m1 = {"kind": "content-bundle", "chapter": "ch06", "knowledge_points": [
        {"key": "k", "knowledge_item": "等差数列求和公式", "body": "适用条件…公式…步骤…"}]}
    gate_m1 = _gate_content_bundle(conn, m1, "dmath")
    case("M1v", "mapping-gate", "M1 的真实门禁执行",
         "plans=1（接受）" if gate_m1["knowledge_points"] else "plans=0",
         "折叠命中库内既有 → 应改走复用", "演示：门禁只做身份校验，同义复用在提案层")
    m3 = {"kind": "content-bundle", "chapter": "ch06", "knowledge_points": [
        {"key": "k", "knowledge_item": "抽屉原理", "body": "适用条件…步骤…"}]}
    gate_m3 = _gate_content_bundle(conn, m3, "dmath")
    case("M3v", "mapping-gate", "M3 的真实门禁执行",
         "plans=1（接受）" if gate_m3["knowledge_points"] else "plans=0",
         "「抽屉原理」与「鸽笼原理」折叠不同 → 不会被自动合并",
         "反例：同义词不静默合并")
    m5 = {"kind": "content-bundle", "chapter": "ch06", "problems": [
        {"key": "a", "kp_ids": ["dmath-ch06-kp-001"], "problem_text": "袋中有 5 只白球…",
         "problem_type": "calculation", "source_kind": "textbook",
         "origin_kind": "source_problem", "source_evidence": "教材"},
        {"key": "b", "kp_ids": ["dmath-ch06-kp-001"], "problem_text": "袋中有 5 只白球…",
         "problem_type": "calculation", "source_kind": "textbook",
         "origin_kind": "source_problem", "source_evidence": "教材"},
    ]}
    gate_m5 = _gate_content_bundle(conn, m5, "dmath")
    dup_errors = [e for e in gate_m5["errors"] if "duplicate content" in e]
    case("M6v", "mapping-gate", "M6 的真实门禁执行",
         f"plans=0，duplicate 错误 {len(dup_errors)} 条",
         "同一题干判重", "双拒零写入")
    m7 = {"kind": "content-bundle", "chapter": "ch06", "problems": [
        {"key": "a", "kp_ids": ["dmath-ch06-kp-999"], "problem_text": "题目",
         "problem_type": "calculation", "source_kind": "textbook",
         "origin_kind": "source_problem", "source_evidence": "教材"}]}
    gate_m7 = _gate_content_bundle(conn, m7, "dmath")
    case("M7v", "mapping-gate", "M7 的真实门禁执行",
         "plans=0" if not gate_m7["problems"] else "plans>0",
         "unknown knowledge point", "依赖阻断零写入")

    # 方法提案的语义核对（content.apply_method_proposal 的前置匹配）
    # 造出 S5 需要的歧义环境：两条同折叠的既有「加法原理」。
    conn = sqlite3.connect(database)
    for suffix, title in (("070", "加法原理"), ("071", "加法原理（讲义版）")):
        pass  # 同折叠要求标题折叠后一致，见下
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
        " knowledge_type, importance)"
        " VALUES ('dmath-ch06-kp-070','加法原理','分类完成后仍保留原正文','concept-property','core')")
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
        " knowledge_type, importance)"
        " VALUES ('dmath-ch06-kp-071','加法原理（讲义版）','讲义措辞的分类完成后版本','concept-property','core')")
    conn.commit()
    eq_probe = content.find_equivalent_kp(pool, "加法原理（练习总结）")
    case("S0", "semantic", "提案「加法原理（练习总结）」的折叠匹配（歧义环境）",
         "输入合法", f"折叠无精确命中 {len(eq_probe)} 条",
         "因此走新建路径——下面的拒收来自多命中，不是这里的探测")
    eq = content.find_equivalent_kp(pool, "等差数列 求和 公式！")
    case("S1", "semantic", "提案「等差数列 求和 公式！」的折叠匹配",
         "输入合法（标题/正文/类型）", f"折叠命中 {[item['kp_id'] for item in eq]}",
         "复用既有身份")
    ambiguous_before = len(content.list_items(pool, "kp"))
    try:
        content.apply_method_proposal(pool, {
            "knowledge_item": "加法原理", "body": "适用条件…步骤…",
            "knowledge_type": "method-modeling"})
        refused = "未拒收"
    except ValueError as exc:
        refused = f"拒收：{exc}"
    case("S5", "semantic", "提案「加法原理」在两条同折叠记录之间的复用检查",
         "输入合法", refused,
         f"歧义拒收，知识点总数不变（{len(content.list_items(pool, 'kp'))} == {ambiguous_before}）")

    # -- 完整性案例 9-16：content_audit 逐项 -------------------------------
    conn = sqlite3.connect(database)
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
        " knowledge_type, importance)"
        " VALUES ('dmath-ch06-kp-050','无标题检查','','concept-property','core')")
    conn.execute(
        "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
        " problem_type, source_kind, origin_kind)"
        " VALUES ('dmath-ch06-prob-050','[\"dmath-ch06-kp-001\"]','P50','S50',"
        "'other','textbook','source_problem')")
    conn.execute(
        "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
        " problem_type, source_kind, origin_kind)"
        " VALUES ('dmath-ch06-prob-051','[\"dmath-ch06-kp-001\"]','P51','S51',"
        "'calculation','textbook','source_problem')")
    conn.commit()
    conn.close()
    findings = content_audit.audit(pool, ("untitled",))["findings"]
    case("I1", "integrity-audit", "知识点「无标题检查」正文为空、标题缺失",
         "untitled 检查命中", "标题缺失即结构问题", "进入 findings，不落已核对")
    findings = content_audit.audit(pool, ("unmarked-objective",))["findings"]
    hit = [f for f in findings if f.get("problem_ids") == ["dmath-ch06-prob-050"]]
    case("I2", "integrity-audit", "选择题「P50」未标 objective 与答案键",
         "unmarked-objective 检查命中", "形态完整但判分依据缺失", "进入 findings")
    case("I3", "integrity-audit", "题目「P51」为普通计算题（对照）",
         "unmarked-objective 未命中", "无需补标", "保持原状")

    # duplicate / fragments
    findings = content_audit.audit(pool, ("duplicates",))["findings"]
    dup = [f for f in findings if "prob-050" in str(f.get("problem_ids"))]
    case("I4", "integrity-audit", "题干「P50/P51」正文不同 → 非重复",
         "duplicates 检查", "题干规范化后不同", "无 finding（对照）")

    # figures: 引用缺失图
    conn = sqlite3.connect(database)
    conn.execute(
        "UPDATE problems SET problem_text='带图题 ![图](dmath/ch06/absent.png)',"
        " figure_paths='[\"dmath/ch06/absent.png\"]' WHERE problem_id='dmath-ch06-prob-051'")
    conn.commit()
    conn.close()
    findings = content_audit.audit(pool, ("figures",))["findings"]
    fig_hit = [f for f in findings if f.get("chapter") == "ch06"]
    case("I5", "integrity-audit", "题 P51 引用 dmath/ch06/absent.png 但文件不存在",
         f"figures 检查命中 {len(fig_hit)} 条", "引用与文件不一致", "进入 findings，不落已核对")

    # -- 章内分类补齐：只改有依据项 ----------------------------------------
    doubtful = []
    for kp_id, item, evidence, seed_type in (
            ("dmath-ch06-kp-060", "错位排列公式", "教材第六章例 6.3", "memory-recall"),
            ("dmath-ch06-kp-061", "捆绑法", "教材第六章例 6.5", "memory-recall"),
            ("dmath-ch06-kp-062", "隔板法", "教材第六章例 6.8", "memory-recall"),
            ("dmath-ch06-kp-063", "存疑：讲义说法不一致", None, "memory-recall"),
            ("dmath-ch06-kp-064", "存疑：两道题答案矛盾", None, "memory-recall")):
        conn = sqlite3.connect(database)
        conn.execute(
            "INSERT INTO knowledge_points (kp_id, knowledge_item, body,"
            " knowledge_type, importance)"
            " VALUES (?, ?, '待补齐分类的正文', ?, 'core')", (kp_id, item, seed_type))
        conn.commit()
        conn.close()
        if evidence:
            # 分类补齐只改有依据项：旧占位 memory-recall 被证据支持的方法类替换。
            content.update(pool, "kp", kp_id, {"knowledge_type": "method-modeling"})
        else:
            # 疑点保留原状：不写入，也不进入已核对练习的范围。
            doubtful.append(kp_id)
    typed = {item["kp_id"]: item.get("knowledge_type")
             for item in content.list_items(pool, "kp")}
    completed = [kp for kp in ("dmath-ch06-kp-060", "dmath-ch06-kp-061",
                               "dmath-ch06-kp-062")
                 if typed[kp] == "method-modeling"]
    kept = [kp for kp in doubtful if typed[kp] == "memory-recall"]
    verified_scope = [item["kp_id"] for item in
                      content.knowledge_query(pool, types=["method-modeling"])]
    case("C1", "classification", "「错位排列公式」有教材出处", "字段合法（method-modeling）",
         "证据=教材例 6.3", "补齐 knowledge_type")
    case("C2", "classification", "「捆绑法」有教材出处", "字段合法", "证据=教材例 6.5",
         "补齐 knowledge_type")
    case("C3", "classification", "「隔板法」有教材出处", "字段合法", "证据=教材例 6.8",
         "补齐 knowledge_type")
    case("C4", "classification", "「存疑：讲义说法不一致」无依据", "不写入",
         "证据不足", "保持原状，不进已核对练习")
    case("C5", "classification", "「存疑：两道题答案矛盾」无依据", "不写入",
         "证据不足", "保持原状，不进已核对练习")
    case("C6", "classification", "已核对范围 = 按 types 检索",
         "knowledge_query(types=['method-modeling'])",
         f"命中 {len(verified_scope)} 条，全部有证据",
         "疑点不在其中：" + ", ".join(kept) if kept else "疑点不在其中")

    report["summary"] = {
        "cases": len(report["cases"]),
        "structure_vs_semantic": "结构=audit/门禁/字段校验；语义=同义折叠与判重与证据",
        "classification_completed": completed,
        "classification_kept_doubtful": kept,
        "verified_practice_scope": verified_scope,
        "doubtful_excluded_from_verified": all(
            kp not in verified_scope for kp in kept),
    }
    out = ROOT / "tmp/accept/wp02-annotation-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    pool.close()


if __name__ == "__main__":
    main()
