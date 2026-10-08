"""Decorate the knowledge-point page with its optional practice experience."""

import html

from workbench.data import experience
from workbench.server import pages


_LINKED_PROBLEMS_MARKER = "<section class='support-section linked-problems'>"


def kp_page(workspace, workspaces, weak_items, pool, kp_id, kp_titles=None):
    page = pages.kp_page(
        workspace, workspaces, weak_items, pool, kp_id, kp_titles,
    )
    if pool.kp(kp_id) is None:
        return page
    panel = _panel(pool, workspace["name"], kp_id)
    if _LINKED_PROBLEMS_MARKER in page:
        page = page.replace(
            _LINKED_PROBLEMS_MARKER,
            panel + _LINKED_PROBLEMS_MARKER,
            1,
        )
    page = page.replace(
        "</head>",
        "<link rel='stylesheet' href='/static/kp-experience.css'></head>",
        1,
    )
    page = page.replace(
        "</body>",
        "<script src='/static/kp-experience.js'></script></body>",
        1,
    )
    return page


def _panel(pool, workspace_name, kp_id):
    record = experience.get(pool, kp_id)
    revision = record["revision"] if record else ""
    content = record["content"] if record else ""

    if record:
        body = pages._render_markdown(content, workspace_name, kp_id)
        referenced = "".join(
            "<li><span class='experience-problem-title'>"
            + html.escape(_problem_title(pool.problem(problem_id), problem_id))
            + "</span></li>"
            for problem_id in record["problem_ids"]
        )
        read_view = (
            "<div id='experience-read' class='experience-read'>"
            f"<div class='experience-markdown'>{body}</div>"
            + ("<div class='experience-problems'><h3>典型题目</h3><ul>"
               + referenced + "</ul></div>" if referenced else "")
            + "</div>"
        )
        empty = ""
        action_label = "编辑"
    else:
        read_view = ""
        empty = (
            "<p id='experience-empty' class='muted experience-empty'>"
            "暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。"
            "</p>"
        )
        action_label = "新增经验"

    return (
        "<section id='practice-experience' class='support-section practice-experience'"
        f" data-kp-id='{html.escape(kp_id)}' data-revision='{revision}'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>做题沉淀</p><h2>做题经验</h2>"
        "</div><div class='experience-actions'>"
        f"<button id='experience-edit' class='outline sm' type='button'>{action_label}</button>"
        + ("<button id='experience-delete' class='ghost sm' type='button'>删除</button>"
           if record else "")
        + "</div></div>"
        + read_view + empty
        + "<div id='experience-editor' class='experience-editor hidden'>"
        "<label for='experience-content'>经验总结（Markdown）</label>"
        f"<textarea id='experience-content' rows='8'>{html.escape(content)}</textarea>"
        "<fieldset><legend>典型题目（可选）</legend>"
        "<div id='experience-problem-choices'><p class='muted'>进入编辑后载入关联题目。</p></div>"
        "</fieldset>"
        "<p id='experience-error' class='inline-error hidden' aria-live='polite'></p>"
        "<div class='experience-editor-actions'>"
        "<button id='experience-save' class='primary sm' type='button'>保存</button>"
        "<button id='experience-cancel' class='ghost sm' type='button'>取消</button>"
        "</div></div>"
        "</section>"
    )


def _problem_title(problem, fallback):
    if not problem:
        return fallback
    return (
        problem.get("display_title")
        or (problem.get("problem_text") or "")[:80]
        or fallback
    )
