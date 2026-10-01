#!/usr/bin/env python3
"""Run the Engineering Team test suite with Python 3.11 or newer."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


if sys.version_info < (3, 11):
    for candidate in ("python3.13", "python3.12", "python3.11"):
        executable = shutil.which(candidate)
        if executable and Path(executable).resolve() != Path(sys.executable).resolve():
            os.execv(executable, [executable, __file__, *sys.argv[1:]])
    print("Python 3.11 or newer is required to run the tests.", file=sys.stderr)
    raise SystemExit(2)

import unittest


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
