"""Run the node-based front-end suites as part of pytest.

Why this file exists
--------------------
`AGENTS.md` makes `python -m pytest tests -q` a mandatory pre-merge check.
Several `*.test.js` suites in this directory were **not** reachable from pytest,
so a regression in them (graph physics, page navigation, paper practice, the
Agent rail foundation, the sound cues) would not have been caught by the
mandatory gate — the suites simply never ran.

The other suites already have their own wrapper files (test_graph_physics.py,
test_ui_interactions.py, test_renderer_display_mode.py, test_sfx_assets.py).
This file covers the ones that had none, in one place, so the list stays
readable and a new unwrapped suite is obvious.

Node is optional: if `node` is not on PATH the test is skipped with a reason,
never silently passed.
"""

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

#: node suites that have no dedicated pytest wrapper (see module docstring).
UNWRAPPED_SUITES = [
    "agent_ui_v1.test.js",
    "graph_layout_seed.test.js",
    "graph_physics_runtime.test.js",
    "graph_physics_worker.test.js",
    "graph_renderer.test.js",
    "middle_navigation.test.js",
    "paper_practice.test.js",
    "practice_motion.test.js",
    "practice_deck.test.js",
]

#: suites that already run through another wrapper — listed so that the
#: coverage stays visible and nobody adds a second runner for them.
ALREADY_WRAPPED = {
    "agent_session_ui.test.js": "test_ui_interactions.py",
    "graph_physics.test.js": "test_graph_physics.py",
    "renderer_display_mode.test.js": "test_renderer_display_mode.py",
    "sfx.test.js": "test_sfx_assets.py",
    "workbench_ui_interactions.test.js": "test_ui_interactions.py",
}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
@pytest.mark.parametrize("suite", UNWRAPPED_SUITES)
def test_node_suite_passes(suite):
    script = Path(__file__).with_name(suite)
    assert script.is_file(), f"missing node suite: {suite}"
    result = subprocess.run(
        ["node", "--test", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, f"{suite} failed:\n{output}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_every_node_suite_is_reachable_from_pytest():
    """No node suite may be left outside the pytest gate.

    A suite that is neither listed in UNWRAPPED_SUITES nor documented in
    ALREADY_WRAPPED would never run in CI — fail loudly instead.
    """
    present = {p.name for p in Path(__file__).parent.glob("*.test.js")}
    known = set(UNWRAPPED_SUITES) | set(ALREADY_WRAPPED)
    orphans = sorted(present - known)
    assert not orphans, (
        "node suites with no pytest runner: "
        + ", ".join(orphans)
        + " — add them to UNWRAPPED_SUITES (or to ALREADY_WRAPPED if another "
        "wrapper already runs them)"
    )
