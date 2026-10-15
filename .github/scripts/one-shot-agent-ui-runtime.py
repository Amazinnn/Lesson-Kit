from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "workbench/server/static/workbench.js"
source = path.read_text(encoding="utf-8")

replacements = [
    (
        '''  function aiHandleActivity(activity) {\n    if (aiCurrentProvider === "pi") aiUpsertPiActivity(activity);\n    else aiUpsertActivity(activity);\n  }''',
        '''  function aiHandleActivity(activity) {\n    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.activity) {\n      AgentUISurfaces.activity(activity);\n    }\n    if (aiCurrentProvider === "pi") aiUpsertPiActivity(activity);\n    else aiUpsertActivity(activity);\n  }''',
    ),
    (
        '''  function aiSetRunning(running) {\n    if (aiSend) aiSend.disabled = running || !aiConversation;\n    if (aiStop) aiStop.classList.toggle("hidden", !running);\n    if (aiInput) aiInput.disabled = running;\n  }''',
        '''  function aiSetRunning(running) {\n    if (aiSend) aiSend.disabled = running || !aiConversation;\n    if (aiStop) aiStop.classList.toggle("hidden", !running);\n    // Keep the composer editable while a turn runs. The send button remains\n    // gated until the backend can accept a redirect/queued turn explicitly.\n    if (aiInput) aiInput.disabled = false;\n    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.setRunning) {\n      AgentUISurfaces.setRunning(running);\n    }\n  }''',
    ),
    (
        '''      else if (event.kind === "activity") aiHandleActivity(event);\n      else if (event.kind === "error") aiSetStatus(event.text || "Agent 返回错误");''',
        '''      else if (event.kind === "activity") aiHandleActivity(event);\n      else if (event.kind === "error") {\n        var eventError = event.text || "Agent 返回错误";\n        aiSetStatus(eventError);\n        if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {\n          AgentUISurfaces.failure(eventError);\n        }\n      }''',
    ),
    (
        '''      aiSetStatus("");\n      aiApplyAction(data.turn.action);''',
        '''      aiSetStatus("");\n      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.finishTurn) {\n        AgentUISurfaces.finishTurn();\n      }\n      aiApplyAction(data.turn.action);''',
    ),
    (
        '''      aiSetRunning(false);\n      aiSetStatus("Agent 失败：" + (data.turn.error || "未知错误"));\n    } else if (data.turn.status === "cancelled") {\n      aiTurn = null;\n      aiSetRunning(false);\n      aiSetStatus("本轮已停止。");''',
        '''      aiSetRunning(false);\n      var turnError = "Agent 失败：" + (data.turn.error || "未知错误");\n      aiSetStatus(turnError);\n      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {\n        AgentUISurfaces.failure(turnError);\n      }\n    } else if (data.turn.status === "cancelled") {\n      aiTurn = null;\n      aiSetRunning(false);\n      aiSetStatus("本轮已停止。");\n      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.finishTurn) {\n        AgentUISurfaces.finishTurn();\n      }''',
    ),
    (
        '''    }).catch(function () {\n      aiTurn = null;\n      aiSetRunning(false);\n      aiSetStatus("无法读取 Agent 进度。");\n    });''',
        '''    }).catch(function () {\n      aiTurn = null;\n      aiSetRunning(false);\n      aiSetStatus("无法读取 Agent 进度。");\n      if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {\n        AgentUISurfaces.failure("无法读取 Agent 进度。可检查连接后重新发送。 ");\n      }\n    });''',
    ),
    (
        '''    aiStreamingMessage = null;\n    aiExecutionPlan = null;\n    aiPiActivities = {};\n    aiAddMarkdown(message, "user");''',
        '''    aiStreamingMessage = null;\n    aiExecutionPlan = null;\n    aiPiActivities = {};\n    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.resetTurn) {\n      AgentUISurfaces.resetTurn();\n    }\n    aiAddMarkdown(message, "user");''',
    ),
    (
        '''      }).catch(function (err) {\n        aiSetRunning(false);\n        aiSetStatus("发送失败：" + (err.message || "未知错误"));\n      });''',
        '''      }).catch(function (err) {\n        aiSetRunning(false);\n        var sendError = "发送失败：" + (err.message || "未知错误");\n        aiSetStatus(sendError);\n        if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.failure) {\n          AgentUISurfaces.failure(sendError);\n        }\n      });''',
    ),
]

for old, new in replacements:
    if old not in source:
        raise SystemExit("expected workbench.js fragment missing:\n" + old[:180])
    source = source.replace(old, new, 1)

start = source.find("  function aiRollbackBatch(batchId, button) {")
end = source.find("\n  function aiRecordRecent(type, id) {", start)
if start < 0 or end < 0:
    raise SystemExit("aiRollbackBatch boundaries missing")
rollback = '''  function aiRollbackBatch(batchId, button) {\n    function executeRollback() {\n      button.disabled = true;\n      api("/ingest/rollback", {\n        method: "POST",\n        headers: { "Content-Type": "application/json" },\n        body: JSON.stringify({ batch_id: batchId }),\n      }).then(function (result) {\n        var card = button.closest(".check-card");\n        if (card) {\n          var detail = card.querySelector(".check-card-detail");\n          if (detail) {\n            detail.textContent = "批次 " + batchId + " 已整批回滚（撤销 "\n              + (result && result.deleted != null ? result.deleted : "?") + " 行）。";\n          }\n        }\n        button.remove();\n        aiSetStatus("批次已回滚");\n      }).catch(function (err) {\n        button.disabled = false;\n        aiSetStatus("回滚失败：" + (err && err.message ? err.message : "未知错误"));\n      });\n    }\n\n    var approval = {\n      title: "整批回滚 " + batchId,\n      reason: "这是低可逆性的内容变更，需要你明确确认。",\n      impact: "该批写入的内容会从学习池撤销。",\n      approveLabel: "确认回滚",\n    };\n    if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.confirm\n        && AgentUISurfaces.confirm(approval, executeRollback)) {\n      return;\n    }\n    if (window.confirm && !window.confirm("整批回滚 " + batchId + "？该批全部内容行将从池中撤销。")) return;\n    executeRollback();\n  }\n'''
source = source[:start] + rollback + source[end:]

for token in (
    "AgentUISurfaces.activity", "AgentUISurfaces.confirm", "AgentUISurfaces.resetTurn",
    "AgentUISurfaces.finishTurn", "AgentUISurfaces.failure",
):
    if token not in source:
        raise SystemExit(f"runtime wiring missing: {token}")
if "aiInput.disabled = running" in source:
    raise SystemExit("composer is still disabled while Agent runs")

path.write_text(source, encoding="utf-8")
Path(__file__).unlink()
workflow = ROOT / ".github/workflows/one-shot-agent-ui-runtime.yml"
if workflow.exists():
    workflow.unlink()
