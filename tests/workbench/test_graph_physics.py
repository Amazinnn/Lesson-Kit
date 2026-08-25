"""Run the dependency-free graph physics checks as part of pytest."""

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_TEST = Path(__file__).with_name("graph_physics.test.js")


def test_graph_physics():
    result = subprocess.run(
        ["node", "--test", str(NODE_TEST)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
