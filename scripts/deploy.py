"""Move a private deployment to a different revision of this repository.

Usage:
    python3 scripts/deploy.py <revision>

The script needs only the standard library, so it runs under the system
interpreter. It does invoke git, uv and pnpm, and those must be on the PATH it
is given: under sudo, PATH is replaced by sudo's own secure_path, which usually
excludes user-installed tools. See docs/DEPLOY.md.

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
      python/                  interpreters, outside every home; see uv_env

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

# Tools the deployment invokes. Checked before any work begins; see require_tools.
_REQUIRED_TOOLS = ("git", "uv", "pnpm")

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

    @property
    def python_dir(self) -> Path:
        """Where uv installs the interpreters this deployment runs on.

        Inside the deployment root rather than under a home directory. The
        reason is in uv_env, and it is not a preference.
        """
        return self.root / "python"

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
    try:
        result = subprocess.run(argv, cwd=cwd, env=merged)
    except FileNotFoundError as error:
        # A missing executable raises FileNotFoundError, which is not a
        # DeployError and would escape the handler in main() -- costing the
        # operator the message telling them the previous revision is still
        # serving, which is the one thing a failed deployment must say.
        raise DeployError(f"{argv[0]} is not on PATH") from error
    if result.returncode != 0:
        raise DeployError(f"{argv[0]} exited with {result.returncode}")


def restart_command() -> str:
    """The command that makes the service pick up a new revision."""
    return os.environ.get("OPENVOCA_RESTART_CMD", f"systemctl restart {SERVICE_NAME}")


def require_tools() -> None:
    """Fail before any work when a tool the deployment needs is unreachable.

    Checking first costs nothing and is the only point at which a toolchain
    problem is free: further in, a release directory has already been created and
    a failed run leaves debris behind for the next one to clean up.

    The PATH that was searched is part of the message because the usual cause is
    not that the tool is absent but that the caller's PATH is not the one the
    tool lives on. sudo replaces PATH with its own secure_path, which normally
    excludes user-installed tools, and the resulting "not found" is otherwise
    indistinguishable from a real absence.
    """
    needed = [*_REQUIRED_TOOLS, restart_command().split()[0]]
    missing = [tool for tool in needed if shutil.which(tool) is None]
    if not missing:
        return

    raise DeployError(
        f"tools not found on PATH: {', '.join(missing)}\n"
        f"  PATH searched: {os.environ.get('PATH', '')}\n"
        '  Under sudo, PATH is replaced by its own secure_path. Re-run with the\n'
        '  PATH that can see these tools, for example:\n'
        '    sudo env "PATH=$PATH" python3 scripts/deploy.py <revision>'
    )


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

    # A unique name rather than one derived from the revision. Deriving it is
    # tempting and wrong: Path("v0.10.3").with_suffix(".tar") is "v0.10.tar",
    # because the last dot-component counts as a suffix, so two revisions
    # differing only in their last part would share one archive path and could
    # clobber each other's export.
    handle, archive_name = tempfile.mkstemp(
        dir=release.parent, prefix=f".{release.name}.", suffix=".tar"
    )
    os.close(handle)
    archive = Path(archive_name)
    try:
        _run(
            ["git", "-C", str(repository), "archive", f"--output={archive}", revision],
            cwd=repository,
        )
        with tarfile.open(archive) as tar:
            tar.extractall(release, filter="data")
    finally:
        archive.unlink(missing_ok=True)


def uv_env(layout: Layout) -> dict[str, str]:
    """Environment that keeps uv's managed interpreter inside the deployment.

    A virtualenv does not contain an interpreter; it references one.
    ``.venv/bin/python`` is a symlink to it and ``pyvenv.cfg`` records the same
    path, so the service starts only if the service user can reach that path.

    uv places managed interpreters under a directory derived from ``HOME``, and
    a deployment runs as root, so the default would be ``/root/.local/share/uv``.
    The unit's ``ProtectHome=true`` makes home directories entirely inaccessible
    to the service -- not read-only, but absent from its namespace -- so the
    interpreter would be unreachable and the service would not start. Dropping
    that hardening would not help either, because /root is mode 0700 and the
    service user cannot traverse it.

    No permission setting fixes this, because the path itself is the problem.
    The deployment therefore decides where interpreters live instead of
    inheriting the answer from whoever happened to invoke it.
    """
    return {"UV_PYTHON_INSTALL_DIR": str(layout.python_dir)}


def install_backend(release: Path, env: Mapping[str, str]) -> None:
    """Install this revision's Python dependencies from its own lock file."""
    _run(["uv", "sync", "--frozen"], cwd=release / "backend", env=env)


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


def run_preflight(release: Path, data_dir: Path, env: Mapping[str, str]) -> None:
    """Run the new revision's own startup checks against *data_dir*.

    A single call site for both the snapshot and empty-directory cases, so the
    environment uv is given cannot be correct in one and forgotten in the other.
    """
    _run(
        ["uv", "run", "python", "-m", "src.preflight"],
        cwd=release / "backend",
        env={**env, "OPENVOCA_DATA_DIR": str(data_dir)},
    )


def preflight(release: Path, snapshot: Path, env: Mapping[str, str]) -> None:
    """Check a revision against a copy of the snapshot rather than the database.

    Importing the application creates missing tables, so testing against the
    live database would let a revision that is about to be rejected write to
    production data.
    """
    with tempfile.TemporaryDirectory(prefix="openvoca-preflight-") as scratch:
        shutil.copy2(snapshot, Path(scratch) / DATABASE_NAME)
        run_preflight(release, Path(scratch), env)


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
    command = restart_command()
    argv = command.split()
    print(f"   $ {command}", flush=True)
    try:
        result = subprocess.run(argv)
    except FileNotFoundError as error:
        raise DeployError(f"restart failed: {argv[0]} is not on PATH") from error
    if result.returncode != 0:
        raise DeployError(f"restart failed: {command} exited with {result.returncode}")


# The only state in which systemd starts the unit at boot. ``enabled-runtime``
# looks like it but writes the symlink into /run, which a reboot clears, and
# ``static`` means the unit has no [Install] section and cannot be enabled at all.
_BOOT_ENABLED_STATE = "enabled"


def boot_start_state() -> str | None:
    """Whether the service will start at boot, or None when unknowable.

    Returns None for a service manager that is not systemd, because the question
    only has an answer in terms of systemd's enablement. A deployment driven by
    something else is not thereby broken.
    """
    argv = restart_command().split()
    if not argv or Path(argv[0]).name != "systemctl":
        return None

    try:
        result = subprocess.run(
            ["systemctl", "is-enabled", SERVICE_NAME],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return "not determinable (systemctl is not on PATH)"

    lines = result.stdout.strip().splitlines()
    return lines[0].strip() if lines else "not determinable (no answer)"


def report_boot_start(state: str | None) -> None:
    """Warn when the service will not come back after a reboot.

    Nothing else in a deployment reveals this. Enabling is a one-time step when
    the unit is installed, so a missing ``systemctl enable`` leaves a service
    that runs perfectly until the machine next restarts -- possibly weeks later,
    with no recent change to suspect. Reporting it here is the only point at
    which the deployment knows the service is running and can ask whether it
    will still be there tomorrow.
    """
    if state is None or state == _BOOT_ENABLED_STATE:
        return

    print(
        f"WARNING: {SERVICE_NAME} is not set to start at boot "
        f"(systemctl reports '{state}').\n"
        "         It is running now, but it will not come back after a reboot.\n"
        f"         Fix it with: systemctl enable {SERVICE_NAME}",
        file=sys.stderr,
        flush=True,
    )


def run_deploy(revision: str, layout: Layout, repository: Path) -> None:
    """Perform the deployment, in order, stopping at the first failure."""
    release = layout.release(revision)

    _announce("Checking the environment")
    require_tools()
    # Printed rather than left implicit. Whether the service can start depends on
    # the interpreter path, and the failure it causes -- the service refusing to
    # come up, with nothing in the deployment output to explain why -- is the
    # reason this was hard to find in the first place.
    print(f"   Interpreters : {layout.python_dir}", flush=True)
    print(f"   Releases     : {layout.releases}", flush=True)
    print(f"   Data         : {layout.data_dir}", flush=True)

    uv_vars = uv_env(layout)

    _announce(f"Exporting {revision}")
    materialize(repository, revision, release)

    _announce("Installing backend dependencies")
    install_backend(release, uv_vars)

    _announce("Building the interface")
    build_frontend(release)

    _announce("Snapshotting the database")
    snapshot = snapshot_database(
        layout.database, layout.snapshots, time.strftime("%Y%m%d-%H%M%S")
    )

    _announce("Checking the new revision against the data")
    if snapshot is None:
        # Nothing to test against; the revision creates its own schema on first
        # start. Importing it still proves the code loads and the toolchain works.
        with tempfile.TemporaryDirectory(prefix="openvoca-preflight-") as scratch:
            run_preflight(release, Path(scratch), uv_vars)
    else:
        preflight(release, snapshot, uv_vars)

    _announce("Switching")
    switch_symlink(layout.current, release)
    write_revision_env(layout.revision_env, revision, read_release_version(release))

    _announce("Restarting")
    restart()

    print(f"\nOpenVoca now runs {revision}.")
    print(f"Snapshot: {snapshot}" if snapshot else "No snapshot was needed.")
    report_boot_start(boot_start_state())


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
