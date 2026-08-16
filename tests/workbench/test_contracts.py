"""Bridge output-contract validation tests (TDD, red first)."""

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


contracts = load_script("wb_contracts", Path("workbench/bridge/contracts.py"))


VALID_EXPLAIN = """# Explain

## 结论

The product rule counts ordered pairs.

## 逐步拆解

Step one: choose the first element. Step two: choose the second.

## 易错点

Forgetting that the choices must be independent.

## 回源指向

Rosen, Discrete Mathematics, §6.1.
"""


class ContractsTests(unittest.TestCase):
    def test_valid_explain_passes(self):
        ok, reasons = contracts.validate("explain", VALID_EXPLAIN)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_missing_section_fails(self):
        text = VALID_EXPLAIN.replace("## 易错点\n\nForgetting that the choices must be independent.\n\n", "")
        ok, reasons = contracts.validate("explain", text)
        self.assertFalse(ok)
        self.assertTrue(any("易错点" in r for r in reasons))

    def test_empty_source_section_fails(self):
        text = VALID_EXPLAIN.replace(
            "Rosen, Discrete Mathematics, §6.1.", ""
        )
        ok, reasons = contracts.validate("explain", text)
        self.assertFalse(ok)
        self.assertTrue(any("回源指向" in r for r in reasons))

    def test_valid_diagnose_passes(self):
        text = """# Diagnose

## 定位

Your step 3 assumes the sets are disjoint.

## 提示

Try the inclusion-exclusion form first.

## 溯源

Rosen, §6.1, Sum Rule.

## 追问

What changes when the sets overlap?
"""
        ok, reasons = contracts.validate("diagnose", text)
        self.assertTrue(ok)

    def test_diagnose_missing_source_fails(self):
        text = """# Diagnose

## 定位

Your step 3 assumes the sets are disjoint.

## 提示

Try the inclusion-exclusion form first.

## 追问

What changes when the sets overlap?
"""
        ok, reasons = contracts.validate("diagnose", text)
        self.assertFalse(ok)
        self.assertTrue(any("溯源" in r for r in reasons))

    def test_unknown_kind_fails(self):
        ok, reasons = contracts.validate("mystery", VALID_EXPLAIN)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
