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
    ("GET", "/api/w/{name}/pull-facets"): (
        BROWSER, (),
        "the filter panel derives its dimensions from the pool; the CLI pull "
        "filters directly by flag"),
    ("GET", "/api/w/{name}/search/problems"): (
        BROWSER, (),
        "the filter panel's search picker; `data search problem` covers the CLI"),
    ("POST", "/api/w/{name}/pull-cards"): (
        BROWSER, (),
        "flash cards are practised in the page; the CLI has no card command yet"),
    ("GET", "/api/w/{name}/practice-sets"): (
        BROWSER, (), "the browser lists reusable saved papers"),
    ("POST", "/api/w/{name}/practice-sets"): (
        BROWSER, (), "the browser saves the current selected problems as a paper"),
    ("GET", "/api/w/{name}/practice-sets/{practice_set_id}"): (
        BROWSER, (), "the browser opens one saved paper"),
    ("PATCH", "/api/w/{name}/practice-sets/{practice_set_id}"): (
        BROWSER, (), "the browser renames or replaces one paper's ordered problems"),
    ("DELETE", "/api/w/{name}/practice-sets/{practice_set_id}"): (
        BROWSER, (), "the browser deletes only the saved paper"),
    ("GET", "/api/w/{name}/practice-sets/{practice_set_id}/render"): (
        BROWSER, (), "the browser reuses the existing student/solution renderer"),
    ("POST", "/api/w/{name}/practice-sets/{practice_set_id}/start"): (
        BROWSER, (), "the browser copies one paper into the single active practice"),
    ("GET", "/api/w/{name}/practice/current"): (
        BROWSER, (), "the browser resumes the workspace's single active practice"),
    ("POST", "/api/w/{name}/practice/current"): (
        BROWSER, (), "the browser starts or explicitly replaces the active practice"),
    ("PATCH", "/api/w/{name}/practice/current"): (
        BROWSER, (), "the browser advances one fixed practice item"),
    ("DELETE", "/api/w/{name}/practice/current"): (
        BROWSER, (), "the browser explicitly clears only execution state"),
    ("POST", "/api/w/{name}/practice/runs/{run_id}/replay"): (
        BROWSER, (), "the browser replays one archived run into the active practice"),
    ("POST", "/api/w/{name}/practice"): (BOTH, ("practice",), ""),
    ("POST", "/api/w/{name}/attempts"): (
        BOTH, ("attempts",),
        "the page submits one attempt per answer; the Agent's attempts apply "
        "records whole manifests through the same table"),
    ("POST", "/api/w/{name}/feedback"): (BOTH, ("feedback",), ""),
    ("GET", "/api/w/{name}/records"): (
        BROWSER, (),
        "the records page is server-rendered; `attempts list`/`data history` "
        "serve the CLI and Agent"),
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
    "data": (AGENT, "reads/writes current content and runs a read-only content audit"),
    "difficulty": (AGENT, ""),
    "ingest": (AGENT, ""),
}
