from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "workbench"
    / "server"
    / "static"
    / "practice-flow.js"
).read_text(encoding="utf-8")


def test_previous_problem_review_is_read_only_overlay():
    assert 'cardPrev.textContent = "回看上一题"' in SOURCE
    assert 'cardNext.textContent = "返回当前题"' in SOURCE
    assert "renderDeckItem(practiceDeck.items[practiceDeck.cursor - 1], true);" in SOURCE
    assert "reviewResultHtml(item)" in SOURCE


def test_previous_problem_review_keeps_agent_context_on_visible_problem():
    assert "function contextProblem()" in SOURCE
    assert "currentProblem: contextProblem" in SOURCE
    assert 'if (reviewingPrevious && item) return item.answer_text || "";' in SOURCE
