"""Adapt frozen guards to existing legacy and new hidden course artifacts."""

import argparse
import runpy
from dataclasses import replace
from pathlib import Path

from workbench.workspace_layout import hidden_database


def run(workspace, gate, apply=False):
    # A fresh execution namespace keeps the frozen CLI and other callers intact.
    runtime = runpy.run_path(str(Path(__file__).resolve().parents[1] / "lessonkit.py"),
                             run_name="_lessonkit_hidden_guard")
    root = Path(workspace["path"])
    course = workspace.get("active_course", "")
    chapter = workspace.get("active_chapter", "")
    contracts = runtime["CONTRACTS"]
    for name, contract in contracts.items():
        hidden_base = ".lessonkit/" + contract.base
        use_hidden = hidden_database(workspace["db"]) or (
            root / hidden_base.format(course=course, chapter=chapter)
        ).is_dir()
        outputs = tuple(
            ".lessonkit/" + path
            if (root / (".lessonkit/" + path).format(course=course, chapter=chapter)).is_file()
            or not (root / path.format(course=course, chapter=chapter)).is_file()
            else path
            for path in contract.outputs
        )
        contracts[name] = replace(contract, base=hidden_base if use_hidden else contract.base,
                                  outputs=outputs)
    args = argparse.Namespace(command=gate, course=course, chapter=chapter,
                              db=None, apply=apply)
    return runtime["command_guard"](args, root)
