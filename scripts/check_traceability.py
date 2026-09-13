"""Verify that every acceptance criterion is either covered by a test or deferred.

A specs-first workflow writes criteria before implementing them, so the gate must
be able to separate "planned, not built yet" from "built, but the test went
missing". Criteria listed in ``docs/specs/deferred.txt`` are the former; anything
else without a test reference is a failure.

The deferred list is self-cleaning: listing a criterion that already has tests is
itself an error, so entries cannot be left behind after the work lands.
"""

import os
import re
import sys

AC_DEFINITION = re.compile(r"^\s*-\s+\*\*(AC-[A-Z0-9]+-\d{3}-\d{2})\*\*", re.MULTILINE)
AC_REFERENCE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}-\d{2}\b")


def _load_deferred(path):
    """Read the deferred criterion IDs, ignoring comments and blank lines."""
    if not os.path.exists(path):
        return set()
    deferred = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            entry = line.split("#", 1)[0].strip()
            if entry:
                deferred.add(entry)
    return deferred


def _collect_defined(spec_dir):
    defined = set()
    for filename in sorted(os.listdir(spec_dir)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
        with open(os.path.join(spec_dir, filename), encoding="utf-8") as handle:
            defined.update(AC_DEFINITION.findall(handle.read()))
    return defined


def _collect_referenced(test_dirs):
    referenced = set()
    for directory in test_dirs:
        for root_dir, _, files in os.walk(directory):
            for filename in files:
                if not filename.endswith((".py", ".ts")):
                    continue
                with open(os.path.join(root_dir, filename), encoding="utf-8") as handle:
                    referenced.update(AC_REFERENCE.findall(handle.read()))
    return referenced


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec_dir = os.path.join(root, "docs", "specs")
    test_dirs = [
        os.path.join(root, "backend", "tests"),
        os.path.join(root, "frontend", "tests"),
    ]

    defined = _collect_defined(spec_dir)
    referenced = _collect_referenced(test_dirs)
    deferred = _load_deferred(os.path.join(spec_dir, "deferred.txt"))

    missing = sorted(defined - referenced - deferred)
    stale = sorted(referenced - defined)
    unknown_deferred = sorted(deferred - defined)
    obsolete_deferred = sorted(deferred & referenced)

    if missing or stale or unknown_deferred or obsolete_deferred:
        if missing:
            print("Missing test coverage for:")
            for ac in missing:
                print(f"  - {ac}")
            print("  (Add tests, or list the criterion in docs/specs/deferred.txt.)")
        if stale:
            print("Unknown ACs referenced in tests:")
            for ac in stale:
                print(f"  - {ac}")
        if unknown_deferred:
            print("Deferred list references criteria that no spec defines:")
            for ac in unknown_deferred:
                print(f"  - {ac}")
        if obsolete_deferred:
            print("Deferred criteria already have tests; remove them from the list:")
            for ac in obsolete_deferred:
                print(f"  - {ac}")
        sys.exit(1)

    covered = len(defined) - len(deferred)
    print(f"Traceability check passed: {covered} acceptance criteria covered.")
    if deferred:
        print(f"{len(deferred)} criteria deferred (see docs/specs/deferred.txt).")
    sys.exit(0)


if __name__ == "__main__":
    main()
