"""Adapt frozen artifact guard contracts to a hidden course layout."""

import argparse
import runpy
from dataclasses import replace
from pathlib import Path


def run_hidden(workspace, gate, apply=False):
    # A fresh execution namespace keeps the frozen CLI and other callers intact.
    runtime = runpy.run_path(str(Path(__file__).resolve().parents[1] / "lessonkit.py"),
                             run_name="_lessonkit_hidden_guard")
    root = Path(workspace["path"])
    course = workspace.get("active_course", "")
    chapter = workspace.get("active_chapter", "")
    contracts = runtime["CONTRACTS"]
    for name, contract in contracts.items():
        outputs = tuple(
            path if (root / path.format(course=course, chapter=chapter)).is_file()
            else ".lessonkit/" + path
            for path in contract.outputs
        )
        contracts[name] = replace(contract, base=".lessonkit/" + contract.base,
                                  outputs=outputs)
    args = argparse.Namespace(command=gate, course=course, chapter=chapter,
                              db=None, apply=apply)
    return runtime["command_guard"](args, root)
