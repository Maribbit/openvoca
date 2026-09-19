"""Decide whether this revision can serve, before a deployment switches to it.

A deployment has exactly one irreversible moment: repointing the ``current``
symlink at a new revision. Everything that can be checked must therefore be
checked before it. Running the checks afterwards would require the deployment
script to decide whether to roll back, and that decision is exactly the kind of
logic which drifts out of step with the application it is meant to reason about.

Importing the application is itself most of the value here: a revision with a
syntax error, a missing dependency or a broken import fails at this point rather
than at the restart, when the previous revision has already been replaced.
"""

from __future__ import annotations

import sys

from src.main import frontend_dist
from src.main import report_startup_paths
from src.services.schema_guard import describe_gaps, find_schema_gaps
from src.services.word_store import get_engine


def run_checks() -> int:
    """Return 0 when this revision can serve, otherwise 1."""
    report_startup_paths()

    gaps = find_schema_gaps(get_engine())
    if gaps:
        print(describe_gaps(gaps), file=sys.stderr)
        return 1

    dist = frontend_dist()
    if not dist.exists():
        print(
            f"ERROR: no interface build at {dist}. Switching to this revision "
            "would serve an API with a blank page.",
            file=sys.stderr,
        )
        return 1

    print("Preflight passed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_checks())
