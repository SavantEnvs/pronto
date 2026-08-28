#!/usr/bin/python3
"""run_tests.py — RUN pronto's own unittest suite and print a parseable summary.

Invoked via the `/mayhem/pronto-tests` ELF launcher (NOT directly), so the verify-repo
sabotage oracle can neuter the launcher and prove the test oracle is behavioral.

It runs the project's real suite exactly as upstream CI does (`python -m unittest discover`
over tests/ — known-answer cases in tests/test_*.py asserting parsed OBO/OBO-JSON/RDF-XML
ontologies, the entity/term/relationship/synonym/xref data model, the serializers, doctests,
and regression tests for filed issues), then prints one line:

    RUNTESTS tests=<n> passed=<p> failed=<f> skipped=<s>

Exit 0 iff failed == 0. mayhem/test.sh parses that line into a CTRF report.

The suite uses CWD-relative fixture paths (tests/data/*), so we chdir to the repo root first.
"""
from __future__ import annotations

import os
import sys
import unittest

SRC = os.environ.get("SRC", "/mayhem")


def main() -> int:
    os.chdir(SRC)
    # Mirror upstream CI's `python -m unittest discover` run from the repo root: discover from SRC
    # with SRC as the top-level dir so `tests` is importable as a package (its submodules use
    # relative imports like `from . import utils`).
    loader = unittest.TestLoader()
    suite = loader.discover(SRC, top_level_dir=SRC)
    result = unittest.TextTestRunner(verbosity=1).run(suite)

    total = result.testsRun
    failed = (
        len(result.failures)
        + len(result.errors)
        + len(getattr(result, "unexpectedSuccesses", []))
    )
    skipped = len(result.skipped)
    passed = total - failed - skipped

    if total == 0:
        print("RUNTESTS tests=0 passed=0 failed=1 skipped=0")
        return 1

    print(f"RUNTESTS tests={total} passed={passed} failed={failed} skipped={skipped}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
