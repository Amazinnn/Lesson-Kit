from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
pages_path = ROOT / "workbench/server/pages.py"
pages = pages_path.read_text(encoding="utf-8")

replacements = [
    (
        "+ f\"<main id='middle'>{_practice_scope_tray(kp_titles)}{middle_html}</main>\"",
        "+ f\"<main id='middle'>{_practice_scope_tray(kp_titles)}{middle_html}{_agent_aux_surfaces()}</main>\"",
    ),
    (
        '"<script src=\'/static/practice-flow.js\'></script>"\n        + "<script src=\'/static/workbench.js\'></script>"',
        '"<script src=\'/static/practice-flow.js\'></script>"\n        + "<script src=\'/static/agent-ui.js\'></script>"\n        + "<script src=\'/static/workbench.js\'></script>"',
    ),
    (
        '"<link rel=\'stylesheet\' href=\'/static/workbench.css\'>"\n        "<link rel=\'stylesheet\' href=\'/static/katex/katex.min.css\'>"',
        '"<link rel=\'stylesheet\' href=\'/static/workbench.css\'>"\n        "<link rel=\'stylesheet\' href=\'/static/agent-ui.css\'>"\n        "<link rel=\'stylesheet\' href=\'/static/katex/katex.min.css\'>"',
    ),
    (
        '"<section id=\'ai-session-controls\' aria-label=\'对话\'>"',
        '"<section id=\'ai-session-controls\' class=\'agent-rail-home\' aria-label=\'对话\'>"',
    ),
    (
        '"<section class=\'ai-conversation\'><div id=\'ai-messages\'></div>"\n        "<p id=\'ai-status\' class=\'muted\' aria-live=\'polite\'></p></section>"\n        "<div id=\'ai-input-row\' class=\'ai-input-row\'>"\n        "<textarea id=\'ai-input\' rows=\'2\' placeholder=\'输入问题\'></textarea>"\n        "<div class=\'ai-send-actions\'><button id=\'ai-stop\' class=\'outline sm hidden\'>停止</button>"\n        "<button id=\'ai-send\' class=\'primary sm\' disabled>发送</button></div>"\n        "</div></section>"',
        '"<section class=\'ai-conversation\'><div id=\'ai-messages\'></div></section>"\n        "<div id=\'ai-context-chips\' class=\'agent-context-chips\' aria-label=\'当前上下文\'></div>"\n        "<div id=\'ai-composer-shell\' class=\'agent-composer-shell\'>"\n        "<div id=\'ai-approval-slot\' class=\'agent-approval-slot hidden\' aria-live=\'polite\'></div>"\n        "<div id=\'ai-input-row\' class=\'ai-input-row\'>"\n        "<textarea id=\'ai-input\' rows=\'2\' placeholder=\'输入问题\'></textarea>"\n        "<div class=\'ai-send-actions\'><button id=\'ai-stop\' class=\'outline sm hidden\'>停止</button>"\n        "<button id=\'ai-send\' class=\'primary sm\' disabled>发送</button></div>"\n        "</div><p id=\'ai-status\' class=\'muted\' aria-live=\'polite\'></p></div></section>"',
    ),
]

for old, new in replacements:
    if old not in pages:
        raise SystemExit(f"expected pages.py fragment missing:\n{old[:160]}")
    pages = pages.replace(old, new, 1)

marker = "\n\ndef _lens_label(workspace, chapter_label, whole_label):\n"
if marker not in pages:
    raise SystemExit("_lens_label marker missing")
aux = r'''


def _agent_aux_surfaces():
    """Transient central surfaces owned by Agent runtime, not permanent page chrome."""
    return (
        "<section id='agent-activity-float' class='agent-activity-float hidden' aria-live='polite'>"
        "<div class='agent-surface-head'><div><p class='agent-surface-kicker'>Agent activity</p>"
        "<h2 class='agent-surface-title'>正在处理</h2></div>"
        "<button class='ghost sm icon-only agent-aux-collapse' type='button' data-agent-aux-collapse "
        "aria-label='收起 Agent 活动'>×</button></div>"
        "<div id='agent-activity-body'></div></section>"
        "<section id='agent-bottom-dock' class='agent-bottom-dock hidden' aria-label='Agent 工作进度'>"
        "<div class='agent-surface-head'><div><p class='agent-surface-kicker'>当前工作</p>"
        "<h2 class='agent-surface-title'>执行进度</h2></div>"
        "<button class='ghost sm icon-only agent-aux-collapse' type='button' data-agent-aux-collapse "
        "aria-label='收起 Agent 工作进度'>×</button></div>"
        "<div id='agent-bottom-dock-body'></div></section>"
        "<aside id='agent-artifact-split' class='agent-artifact-split hidden' aria-label='Agent 工件预览'>"
        "<div class='agent-surface-head'><div><p class='agent-surface-kicker'>Artifact</p>"
        "<h2 id='agent-artifact-title' class='agent-surface-title'>最新工件</h2></div>"
        "<button class='ghost sm icon-only agent-aux-collapse' type='button' data-agent-aux-collapse "
        "aria-label='关闭工件预览'>×</button></div>"
        "<div id='agent-artifact-body'></div>"
        "<div id='agent-artifact-actions'></div></aside>"
    )
'''
pages = pages.replace(marker, aux + marker, 1)
pages_path.write_text(pages, encoding="utf-8")

for dom_id in (
    "agent-activity-float", "agent-bottom-dock", "agent-artifact-split",
    "ai-context-chips", "ai-composer-shell",
):
    needle = "id='" + dom_id + "'"
    if pages.count(needle) != 1:
        raise SystemExit(f"unexpected DOM id count for {dom_id}: {pages.count(needle)}")
for asset in ("/static/agent-ui.css", "/static/agent-ui.js"):
    if pages.count(asset) != 1:
        raise SystemExit(f"unexpected asset count for {asset}: {pages.count(asset)}")

Path(__file__).unlink()
workflow = ROOT / ".github/workflows/one-shot-agent-ui-rail.yml"
if workflow.exists():
    workflow.unlink()
