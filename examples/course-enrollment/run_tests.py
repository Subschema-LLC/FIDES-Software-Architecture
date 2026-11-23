#!/usr/bin/env python3
"""Runs the architecture check, the type check, then every test. Exit 1 on any failure.

This is what the build runs. Run it before you finish any change.
"""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT)]

from arch_check import check, warnings  # noqa: E402

for warning in warnings(ROOT / "src"):
    print(f"arch_check warning: {warning}", file=sys.stderr)
problems = check(ROOT / "src")
if problems:
    print("arch_check FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
    raise SystemExit(1)
print("arch_check OK")

# The type checker is the other half of the build check. The app needs nothing
# outside the standard library, so the check runs when mypy is installed.
try:
    from mypy import api as mypy
except ImportError:
    print("type check skipped: pip install mypy to run it")
else:
    os.environ["MYPYPATH"] = str(ROOT / "src")
    report, errors, status = mypy.run(["--strict", "--explicit-package-bases",
                                       "--cache-dir", str(ROOT / "var" / "mypy"),
                                       str(ROOT / "src"), str(ROOT / "arch_check.py")])
    if status:
        print(f"type check FAILED:\n{report}{errors}", file=sys.stderr)
        raise SystemExit(1)
    print("type check OK")

suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT / "tests"))
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
