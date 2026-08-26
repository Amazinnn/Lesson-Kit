"""Run the dependency-free browser interaction checks as part of pytest."""

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_TEST = Path(__file__).with_name("workbench_ui_interactions.test.js")
AGENT_SESSION_NODE_TEST = Path(__file__).with_name("agent_session_ui.test.js")


def test_workbench_browser_interactions():
    result = subprocess.run(
        ["node", "--test", str(NODE_TEST), str(AGENT_SESSION_NODE_TEST)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
