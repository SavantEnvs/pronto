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


# Tests that need the network. The oracle must run air-gapped (SPEC §6.2 item 16 runs it under
# `docker run --network none`), so these are deselected rather than left to fail.
#
# `Ontology.from_obo_library`'s doctest fetches http://purl.obolibrary.org/obo/apo.obo.
# tests/test_doctest.py already shims from_obo_library to prefer a vendored copy under tests/data/,
# but apo.obo is not one of the 15 fixtures upstream ships, so the shim falls through to the real
# download and the doctest fails with no network. Nothing else in the suite reaches out.
NETWORK_TESTS = ("pronto.ontology.Ontology.from_obo_library",)


def _drop_network_tests(suite):
    """Rebuild `suite` without the NETWORK_TESTS entries, preserving its nesting."""
    out = unittest.TestSuite()
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            out.addTest(_drop_network_tests(t))
        elif not any(n in t.id() for n in NETWORK_TESTS):
            out.addTest(t)
    return out


def main() -> int:
    os.chdir(SRC)
    # Mirror upstream CI's `python -m unittest discover` run from the repo root: discover from SRC
    # with SRC as the top-level dir so `tests` is importable as a package (its submodules use
    # relative imports like `from . import utils`).
    loader = unittest.TestLoader()
    suite = loader.discover(SRC, top_level_dir=SRC)
    suite = _drop_network_tests(suite)
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
