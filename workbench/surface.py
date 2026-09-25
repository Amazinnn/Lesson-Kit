"""The declared interface surface: who owns every API route and CLI command.

The readable tables live in `docs/action-graph/L2-interfaces.md`; this module is
the machine authority a test compares against the real argument parser and route
table, so a route or command cannot land without saying which surface owns it —
and a route that claims the Agent can reach it must name the command that does.
A capability that stays browser-only is declared here with its reason instead of
being left unmentioned (2026-09-25 practice-set-export-and-cli-audit).

Audiences: ``agent`` = reachable through the super CLI; ``both`` = a CLI command
serves the same capability; ``browser`` = the page only, with a note saying why;
``human`` = a lifecycle command for a person at the terminal.
"""

BROWSER = "browser"
HUMAN = "human"
AGENT = "agent"
BOTH = "both"
AUDIENCES = (BROWSER, HUMAN, AGENT, BOTH)

# (method, path) -> (audience, commands serving it, note)
ROUTES = {
    ("GET", "/api/hub/workspaces"): (BOTH, ("ls",), ""),
    ("GET", "/api/w/{name}/weak"): (BOTH, ("weak",), ""),
    ("POST", "/api/w/{name}/chapter"): (BOTH, ("use",), ""),
    ("GET", "/api/w/{name}/due"): (BOTH, ("due",), ""),
    ("GET", "/api/w/{name}/calendar"): (
        BROWSER, (),
        "the time view is a page; the same facts are readable as due/schedule rows"),
    ("GET", "/api/w/{name}/plan"): (
        BROWSER, (),
        "the daily plan is built for the practice page and cached in .lessonkit/"),
    ("POST", "/api/w/{name}/plan/recalculate"): (
        BROWSER, (),
        "adjusting today's plan starts from the page's own adjustment input"),
    ("GET", "/api/w/{name}/goals"): (BOTH, ("goals",), ""),
    ("POST", "/api/w/{name}/goals"): (BOTH, ("goals",), ""),
    ("PATCH", "/api/w/{name}/goals/{goal_id}"): (BOTH, ("goals",), ""),
    ("DELETE", "/api/w/{name}/goals/{goal_id}"): (BOTH, ("goals",), ""),
    ("POST", "/api/w/{name}/pull"): (BOTH, ("pull",), ""),
    ("POST", "/api/w/{name}/pull-cards"): (
        BROWSER, (),
        "flash cards are practised in the page; the CLI has no card command yet"),
    ("POST", "/api/w/{name}/practice"): (BOTH, ("practice",), ""),
    ("POST", "/api/w/{name}/feedback"): (BOTH, ("feedback",), ""),
    ("GET", "/api/w/{name}/ingest/batches"): (BOTH, ("ingest",), ""),
    ("POST", "/api/w/{name}/ingest/rollback"): (BOTH, ("ingest",), ""),
    ("GET", "/api/w/{name}/problem/{problem_id}"): (BOTH, ("data",), ""),
    ("GET", "/api/w/{name}/kp/{kp_id}"): (BOTH, ("data",), ""),
    ("GET", "/api/w/{name}/graph/model"): (
        BROWSER, (),
        "the graph model is projected in the browser from pool rows"),
    ("POST", "/api/w/{name}/graph/state"): (BOTH, ("data",), ""),
    ("POST", "/api/w/{name}/graph/kp"): (BOTH, ("data",), ""),
    ("GET", "/api/w/{name}/ai/providers"): (BOTH, ("bridge",), ""),
    ("GET", "/api/w/{name}/ai/sessions"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("POST", "/api/w/{name}/ai/sessions"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("PATCH", "/api/w/{name}/ai/sessions/{conversation_id}"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("DELETE", "/api/w/{name}/ai/sessions/{conversation_id}"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("GET", "/api/w/{name}/ai/sessions/{conversation_id}"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("POST", "/api/w/{name}/ai/sessions/{conversation_id}/turns"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("GET", "/api/w/{name}/ai/sessions/{conversation_id}/turns/{turn_id}"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("POST", "/api/w/{name}/ai/sessions/{conversation_id}/cancel"): (
        BROWSER, (), "conversations are native to the page; the CLI has no session command"),
    ("GET", "/api/w/{name}/graph"): (
        BROWSER, (), "the artifact is rendered by pool/scripts/render-graph-html.py and served to the page"),
}

# command -> (audience, note)
COMMANDS = {
    "init": (HUMAN, ""),
    "use": (HUMAN, ""),
    "ls": (HUMAN, "prints text by default and JSON with --json"),
    "open": (HUMAN, ""),
    "serve": (HUMAN, ""),
    "daemon": (HUMAN, ""),
    "dashboard": (HUMAN, ""),
    "doctor": (HUMAN, ""),
    "bridge": (HUMAN, ""),
    "guard": (HUMAN, "runs a workspace gate through lessonkit.py"),
    "experiment": (HUMAN, "read-only mastery evaluator"),
    "weak": (AGENT, "prints text by default and JSON with --json"),
    "due": (AGENT, "prints text by default and JSON with --json"),
    "schedule": (AGENT, ""),
    "pull": (AGENT, "composes a practice set and can print it"),
    "practice": (AGENT, ""),
    "feedback": (AGENT, ""),
    "goals": (AGENT, ""),
    "attempts": (AGENT, ""),
    "data": (AGENT, ""),
    "difficulty": (AGENT, ""),
    "ingest": (AGENT, ""),
}
