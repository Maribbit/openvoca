"""Move a private deployment to a different revision of this repository.

Usage:
    uv run python scripts/deploy.py <revision>

The script is deliberately ignorant. It does not compare versions, decide
whether a migration is needed, or roll back. Each step either succeeds or aborts
the deployment, and because the only irreversible step is the last one, an
aborted run leaves the previous revision serving. That is also why nothing here
branches on the content of what it is installing: logic of that kind drifts out
of step with the application it reasons about, and cannot be tested against the
revision that has not been written yet.

Layout, all overridable through the environment:

    OPENVOCA_ROOT     default /opt/openvoca
      releases/<revision>/     an export of that revision
      current -> releases/<revision>
      revision.env             the revision the service reports

    OPENVOCA_DATA_DIR default /var/lib/openvoca
      openvoca.db              the database, outside every revision
      snapshots/               one SQLite snapshot per deployment
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT = Path("/opt/openvoca")
DEFAULT_DATA_DIR = Path("/var/lib/openvoca")
DATABASE_NAME = "openvoca.db"
SERVICE_NAME = "openvoca"

USAGE = "usage: deploy.py <revision>"


class DeployError(RuntimeError):
    """A step failed. The deployment stops; nothing is undone."""


@dataclass(frozen=True)
class Layout:
    """Where a deployment keeps its code and its data.

    The two are separate roots on purpose. An update replaces a code directory,
    so a database stored inside one would be replaced with it.
    """

    root: Path
    data_dir: Path

    @property
    def releases(self) -> Path:
        return self.root / "releases"

    @property
    def current(self) -> Path:
        return self.root / "current"

    @property
    def revision_env(self) -> Path:
        return self.root / "revision.env"

    @property
    def database(self) -> Path:
        return self.data_dir / DATABASE_NAME

    @property
    def snapshots(self) -> Path:
        return self.data_dir / "snapshots"

    def release(self, revision: str) -> Path:
        return self.releases / revision


def layout_from_env(env: Mapping[str, str] | None = None) -> Layout:
    source = os.environ if env is None else env
    return Layout(
        root=Path(source.get("OPENVOCA_ROOT", DEFAULT_ROOT)),
        data_dir=Path(source.get("OPENVOCA_DATA_DIR", DEFAULT_DATA_DIR)),
    )


def _announce(step: str) -> None:
    print(f"\n== {step}", flush=True)


def _run(argv: list[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> None:
    print(f"   $ {' '.join(argv)}", flush=True)
    merged = dict(os.environ) if env is None else {**os.environ, **env}
    result = subprocess.run(argv, cwd=cwd, env=merged)
    if result.returncode != 0:
        raise DeployError(f"{argv[0]} exited with {result.returncode}")


def materialize(repository: Path, revision: str, release: Path) -> None:
    """Export *revision* from *repository* into *release*.

    An export rather than a checkout: the running revision needs no git metadata,
    and a directory without it cannot be confused for the repository the operator
    pushes to. Whatever put the commit in the repository's object store -- a
    fetch, a push hook, a bundle -- is the transport, and this does not care which.
    """
    release.parent.mkdir(parents=True, exist_ok=True)
    if release.exists():
        shutil.rmtree(release)
    release.mkdir()

    archive = release.with_suffix(".tar")
    try:
        _run(
            ["git", "-C", str(repository), "archive", f"--output={archive}", revision],
            cwd=repository,
        )
        with tarfile.open(archive) as tar:
            tar.extractall(release, filter="data")
    finally:
        archive.unlink(missing_ok=True)


def install_backend(release: Path) -> None:
    """Install this revision's Python dependencies from its own lock file."""
    _run(["uv", "sync", "--frozen"], cwd=release / "backend")


def build_frontend(release: Path) -> None:
    """Produce the interface build this revision serves."""
    frontend = release / "frontend"
    _run(["pnpm", "install", "--frozen-lockfile"], cwd=frontend)
    _run(["pnpm", "run", "build"], cwd=frontend)


def snapshot_database(database: Path, snapshots: Path, stamp: str) -> Path | None:
    """Copy the database using SQLite's own backup mechanism.

    Not a file copy. In rollback-journal mode a write in progress leaves a
    sidecar that a single-file copy does not include, and in WAL mode committed
    data can still live outside the main file entirely, so a copy can be silently
    incomplete rather than visibly broken. SQLite's backup API reads through the
    same locking protocol an ordinary client uses.

    Returns None when there is no database yet, which is what a first deployment
    looks like.
    """
    if not database.exists():
        print("   No database yet; nothing to snapshot.")
        return None

    snapshots.mkdir(parents=True, exist_ok=True)
    destination = snapshots / f"{database.stem}-{stamp}.db"
    source = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    return destination


def preflight(release: Path, snapshot: Path) -> None:
    """Run the new revision's own startup checks, against a copy of the database.

    Against a copy rather than the live database because importing the
    application creates missing tables. A revision that is about to be rejected
    must not have written anything to the data it was being tested against.
    """
    with tempfile.TemporaryDirectory(prefix="openvoca-preflight-") as scratch:
        shutil.copy2(snapshot, Path(scratch) / DATABASE_NAME)
        _run(
            ["uv", "run", "python", "-m", "src.preflight"],
            cwd=release / "backend",
            env={"OPENVOCA_DATA_DIR": scratch},
        )


def switch_symlink(link: Path, target: Path) -> None:
    """Point *link* at *target* in a single rename.

    Deleting and recreating the link would leave a window in which the link does
    not exist, and a restart landing in that window would find no code at all.
    The rename is the only step in a deployment that changes what is being
    served, and it is indivisible.
    """
    pending = link.with_name(f"{link.name}.pending")
    pending.unlink(missing_ok=True)
    os.symlink(target, pending)
    try:
        os.replace(pending, link)
    except OSError:
        # Leave nothing behind that a later run could mistake for real state.
        pending.unlink(missing_ok=True)
        raise


def read_release_version(release: Path) -> str:
    """Read the version the exported revision declares.

    Transcription, not a decision: the number comes from the revision's own
    VERSION file, the same source the release process treats as the single truth.
    """
    try:
        return (release / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def write_revision_env(path: Path, revision: str, version: str) -> None:
    """Record which revision and version the service should report on restart.

    Written through the same rename, so a restart cannot read a half-written
    file, and only ever names a revision whose code is already in place.

    The version is not decoration: the update check returns early when it is
    unset, so a deployment that omitted it would never offer an update at all.
    """
    pending = path.with_name(f"{path.name}.pending")
    pending.write_text(
        f"OPENVOCA_REVISION={revision}\nOPENVOCA_VERSION={version}\n",
        encoding="utf-8",
    )
    os.replace(pending, path)


def restart() -> None:
    """Restart the service so it picks up the new revision."""
    command = os.environ.get("OPENVOCA_RESTART_CMD", f"systemctl restart {SERVICE_NAME}")
    argv = command.split()
    print(f"   $ {command}", flush=True)
    result = subprocess.run(argv)
    if result.returncode != 0:
        raise DeployError(f"restart failed: {command} exited with {result.returncode}")


def run_deploy(revision: str, layout: Layout, repository: Path) -> None:
    """Perform the deployment, in order, stopping at the first failure."""
    release = layout.release(revision)

    _announce(f"Exporting {revision}")
    materialize(repository, revision, release)

    _announce("Installing backend dependencies")
    install_backend(release)

    _announce("Building the interface")
    build_frontend(release)

    _announce("Snapshotting the database")
    snapshot = snapshot_database(
        layout.database, layout.snapshots, time.strftime("%Y%m%d-%H%M%S")
    )

    _announce("Checking the new revision against the data")
    if snapshot is None:
        # Nothing to test against; the revision creates its own schema on first
        # start. Importing it still proves the code loads.
        with tempfile.TemporaryDirectory(prefix="openvoca-preflight-") as scratch:
            _run(
                ["uv", "run", "python", "-m", "src.preflight"],
                cwd=release / "backend",
                env={"OPENVOCA_DATA_DIR": scratch},
            )
    else:
        preflight(release, snapshot)

    _announce("Switching")
    switch_symlink(layout.current, release)
    write_revision_env(layout.revision_env, revision, read_release_version(release))

    _announce("Restarting")
    restart()

    print(f"\nOpenVoca now runs {revision}.")
    print(f"Snapshot: {snapshot}" if snapshot else "No snapshot was needed.")


def _serving_revision(layout: Layout) -> str:
    """Name of the revision ``current`` points at, or empty when there is none."""
    try:
        return Path(os.readlink(layout.current)).name
    except OSError:
        return ""


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print(USAGE, file=sys.stderr)
        return 2

    revision = arguments[0]
    layout = layout_from_env()
    repository = Path(__file__).resolve().parent.parent

    # Captured before anything runs, because after the switch there is no longer
    # a way to ask what was serving when the deployment started.
    serving = _serving_revision(layout)

    try:
        run_deploy(revision, layout, repository)
    except DeployError as error:
        print(f"\nDeployment failed: {error}", file=sys.stderr)
        if serving and serving != revision:
            # The script must not decide whether to roll back, but leaving the
            # operator to reconstruct the command would be its own failure.
            print(f"Still serving {serving}.", file=sys.stderr)
            print(f"To go back: deploy.py {serving}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
