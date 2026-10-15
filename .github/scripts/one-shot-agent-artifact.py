from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 1) Agent contract: only receipt-derived Paper identity may become an Artifact.
contracts_path = ROOT / "workbench/bridge/agent_contracts.py"
contracts = contracts_path.read_text(encoding="utf-8")
needle = '''Use only when the learner is asking from the goal-form flow; ordinary chat must not prefill it.\n\nAfter any successful write, summarize the affected objects and user-accessible result in concise Chinese.'''
replacement = '''Use only when the learner is asking from the goal-form flow; ordinary chat must not prefill it.\n\nManaged Paper handoff:\n```lessonkit-action\n{"type":"paper_artifact","practice_set_id":"ps-001","title":"…","item_count":12,"summary":"…"}\n```\nEmit this only after a successful `lesson-kit papers <workspace> save --input <manifest>` command returns exit 0 and a JSON receipt. `practice_set_id`, title, and item count must come from that receipt; do not invent them. Do not include or invent a navigation URL in the action. The Workbench derives its own native destination, and presenting an Artifact must not navigate automatically.\n\nAfter any successful write, summarize the affected objects and user-accessible result in concise Chinese.'''
if needle not in contracts:
    raise SystemExit("actions contract insertion marker missing")
contracts = contracts.replace(needle, replacement, 1)
contracts_path.write_text(contracts, encoding="utf-8")

# 2) Artifact-specific presentation polish. Keep it within existing Soft Mondrian tokens.
css_path = ROOT / "workbench/server/static/agent-ui.css"
css = css_path.read_text(encoding="utf-8")
artifact_css = r'''

/* Artifact = durable result handoff. The chat card is the record; Adaptive Split
   is only the latest-result preview and never performs navigation by itself. */
.agent-artifact-card {
  padding: 11px 12px !important;
  border: 1px solid var(--lk-ink) !important;
  border-left: 4px solid var(--lk-blue) !important;
  border-radius: 10px !important;
  background: var(--lk-paper) !important;
}
.agent-artifact-card-title {
  display: block;
  margin-top: 3px;
  color: var(--lk-ink);
  font-size: 13px;
  line-height: 19px;
}
.agent-artifact-meta {
  margin: 5px 0 0;
  color: var(--dsw-label-tertiary);
  font-family: var(--dsw-font-code);
  font-size: 10px;
}
.agent-artifact-summary {
  margin: 7px 0 0;
  color: var(--dsw-label-secondary);
  font-size: 12px;
  line-height: 18px;
}
.agent-artifact-card-actions,
#agent-artifact-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 11px;
}
.agent-artifact-open {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}
#agent-artifact-body {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--dsw-border-l2);
}
'''
if ".agent-artifact-card-title" not in css:
    css += artifact_css
css_path.write_text(css, encoding="utf-8")

# 3) Reset Artifact card de-duplication when a different conversation is rendered.
ui_path = ROOT / "workbench/server/static/agent-ui.js"
ui = ui_path.read_text(encoding="utf-8")
marker = '''  function resetTurn() {\n    state.userCollapsed = false;'''
insert = '''  function resetConversation() {\n    state.renderedArtifacts = {};\n    state.latestArtifact = null;\n    setHidden(byId("agent-artifact-split"), true);\n    var middle = byId("middle");\n    if (middle && middle.classList) middle.classList.remove("agent-split-open");\n  }\n\n  function resetTurn() {\n    state.userCollapsed = false;'''
if marker not in ui:
    raise SystemExit("agent-ui resetTurn marker missing")
ui = ui.replace(marker, insert, 1)
api_marker = '''    init: init,\n    renderContext: renderContext,\n    resetTurn: resetTurn,'''
api_replacement = '''    init: init,\n    renderContext: renderContext,\n    resetConversation: resetConversation,\n    resetTurn: resetTurn,'''
if api_marker not in ui:
    raise SystemExit("agent-ui API marker missing")
ui = ui.replace(api_marker, api_replacement, 1)
ui_path.write_text(ui, encoding="utf-8")

# 4) Runtime: apply the current Artifact action and restore historical cards without
# replaying navigation or mutable actions.
workbench_path = ROOT / "workbench/server/static/workbench.js"
workbench = workbench_path.read_text(encoding="utf-8")
action_marker = '''  function aiApplyAction(action) {\n    if (!action) return;\n    if (action.type === "replace_practice_selection") {'''
action_replacement = '''  function aiApplyAction(action) {\n    if (!action) return;\n    if (action.type === "paper_artifact") {\n      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {\n        AgentUISurfaces.artifact(action);\n      }\n      return;\n    }\n    if (action.type === "replace_practice_selection") {'''
if action_marker not in workbench:
    raise SystemExit("aiApplyAction marker missing")
workbench = workbench.replace(action_marker, action_replacement, 1)

render_marker = '''  function aiRenderConversation(record) {\n    if (!messages) return;\n    if (aiChatView) aiSetView("chat");\n    messages.innerHTML = "";'''
render_replacement = '''  function aiRenderConversation(record) {\n    if (!messages) return;\n    if (aiChatView) aiSetView("chat");\n    messages.innerHTML = "";\n    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.resetConversation) {\n      AgentUISurfaces.resetConversation();\n    }'''
if render_marker not in workbench:
    raise SystemExit("aiRenderConversation marker missing")
workbench = workbench.replace(render_marker, render_replacement, 1)

old_restore = '''        // A single-action turn records both keys; render the list, and fall back\n        // to the single action only when the list is absent (one card, never two).\n        var actions = message.actions || [];\n        if (actions.length) {\n          actions.forEach(function (restored) {\n            if (restored && restored.type === "check_ingest") aiApplyCheckAction(restored);\n          });\n        } else if (message.action && message.action.type === "check_ingest") {\n          aiApplyCheckAction(message.action);\n        }'''
new_restore = '''        // Restore durable presentational results only. Mutable actions such as\n        // practice selection and goal prefills are never replayed from history.\n        var actions = message.actions || [];\n        actions.forEach(function (restored) {\n          if (!restored) return;\n          if (restored.type === "check_ingest") aiApplyCheckAction(restored);\n          else if (restored.type === "paper_artifact"\n              && typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {\n            AgentUISurfaces.artifact(restored, { restore: true });\n          }\n        });\n        if (message.action && message.action.type === "paper_artifact"\n            && typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.artifact) {\n          AgentUISurfaces.artifact(message.action, { restore: true });\n        } else if (!actions.length && message.action && message.action.type === "check_ingest") {\n          aiApplyCheckAction(message.action);\n        }'''
if old_restore not in workbench:
    raise SystemExit("historical action restore block missing")
workbench = workbench.replace(old_restore, new_restore, 1)
for token in ("paper_artifact", "AgentUISurfaces.artifact", "AgentUISurfaces.resetConversation"):
    if token not in workbench:
        raise SystemExit("Artifact runtime wiring missing: " + token)
workbench_path.write_text(workbench, encoding="utf-8")

# Self-delete migration plumbing before the implementation commit.
Path(__file__).unlink()
workflow = ROOT / ".github/workflows/one-shot-agent-artifact.yml"
if workflow.exists():
    workflow.unlink()
