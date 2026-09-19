"""Tests for the deployment atomicity section of docs/specs/private-deployment.md.

The deployment script is tested end to end rather than function by function,
because what has to hold is a property of the whole run: at no point may it leave
a revision half installed, and a failure at any step must leave the previous
revision serving. Those are claims about a sequence of external commands, so the
commands themselves are real invocations of stand-ins placed on PATH. Nothing
here starts a service or touches the network.
"""

import asyncio
import json
import os
import sqlite3
import stat
import tarfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import deploy
import src.main as main_module
from src.main import app

client = TestClient(app)

_EMPTY_UPDATE_INFO = {
    "checked": False,
    "hasUpdate": False,
    "currentVersion": "",
    "latestVersion": "",
    "url": "",
}


class _OfflineClient:
    """A client that fails, so the update check makes no network request."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_OfflineClient":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def get(self, url: str, **kwargs) -> None:
        raise httpx.ConnectError("network access is not available in tests")


_SOURCE_FILES = (
    "VERSION",
    "backend/pyproject.toml",
    "backend/uv.lock",
    "frontend/package.json",
)

_FAKE_VERSION = "1.2.3"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _fake_git() -> str:
    """A ``git`` that exports a small archive for the requested revision."""
    return f"""#!/usr/bin/env python3
import io, sys, tarfile

names = {list(_SOURCE_FILES)!r}
args = sys.argv[1:]
log = os.environ.get("FAKE_LOG") if (os := __import__("os")) else None

if "archive" in args:
    output = next(a.split("=", 1)[1] for a in args if a.startswith("--output="))
    revision = args[-1]

    def content(name):
        # VERSION holds a version number rather than a placeholder: the
        # deployment reads it to tell the service what it is running.
        if name == "VERSION":
            return b"{_FAKE_VERSION}\\n"
        return f"{{name}}@{{revision}}\\n".encode()

    with tarfile.open(output, "w") as tar:
        for name in names:
            data = content(name)
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    sys.exit(0)
sys.exit(0)
"""


def _fake_recorder(name: str, exit_code: int = 0) -> str:
    """A stand-in that records how it was invoked and then succeeds."""
    return f"""#!/usr/bin/env python3
import json, os, sys

entry = {{
    "tool": {name!r},
    "argv": sys.argv[1:],
    "cwd": os.getcwd(),
    "data_dir": os.environ.get("OPENVOCA_DATA_DIR", ""),
    "uv_python_dir": os.environ.get("UV_PYTHON_INSTALL_DIR", ""),
}}
log = os.environ["FAKE_LOG"]
with open(log, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry) + "\\n")
sys.exit({exit_code})
"""


def _fake_systemctl(enabled_state: str) -> str:
    """A ``systemctl`` that records calls and answers ``is-enabled``.

    Exit codes follow the real tool: a unit that is enabled exits 0 and a
    disabled one exits 1, so a check that trusted the exit code alone would be
    caught here.
    """
    exits_zero = enabled_state in ("enabled", "enabled-runtime", "static")
    return f"""#!/usr/bin/env python3
import json, os, sys

args = sys.argv[1:]
entry = {{
    "tool": "systemctl",
    "argv": args,
    "cwd": os.getcwd(),
    "data_dir": os.environ.get("OPENVOCA_DATA_DIR", ""),
    "uv_python_dir": os.environ.get("UV_PYTHON_INSTALL_DIR", ""),
}}
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry) + "\\n")

if args and args[0] == "is-enabled":
    print({enabled_state!r})
    sys.exit(0 if {exits_zero!r} else 1)
sys.exit(0)
"""


@pytest.fixture
def tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Put stand-ins for every external command on PATH and return (log, path).

    The deployment script invokes real executables, so intercepting them at the
    PATH boundary exercises the same code that runs on the deployment machine
    instead of a mocked-out approximation of it.

    The service manager reports ``enabled`` by default, which is what a correctly
    installed deployment looks like, so tests that are not about boot persistence
    are not also exercising its warning path.
    """
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    _write_executable(binary_dir / "git", _fake_git())
    for tool in ("uv", "pnpm"):
        _write_executable(binary_dir / tool, _fake_recorder(tool))
    _write_executable(binary_dir / "systemctl", _fake_systemctl("enabled"))

    log = tmp_path / "calls.log"
    log.write_text("", encoding="utf-8")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("PATH", f"{binary_dir}{os.pathsep}{os.environ['PATH']}")
    return log, binary_dir


def _calls(log: Path) -> list[dict]:
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def _layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> deploy.Layout:
    layout = deploy.Layout(root=tmp_path / "opt", data_dir=tmp_path / "var")
    monkeypatch.setenv("OPENVOCA_ROOT", str(layout.root))
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(layout.data_dir))
    return layout


def _seed_database(layout: deploy.Layout) -> None:
    layout.data_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(layout.database) as conn:
        conn.execute("CREATE TABLE wordrecord (lemma TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO wordrecord VALUES ('harbor')")


def _serve(layout: deploy.Layout, revision: str) -> Path:
    """Put a previous revision in place, as an earlier deployment would have."""
    previous = layout.release(revision)
    previous.mkdir(parents=True)
    os.symlink(previous, layout.current)
    return previous


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo" / "scripts"
    repository.mkdir(parents=True)
    return repository


# Covers: AC-PRIV-003-03
def test_snapshot_reads_through_the_database_not_the_file(tmp_path: Path) -> None:
    """A copy of the main file is not a backup.

    The live connection stays open and uncheckpointed, which is the state a
    running application is normally in. In WAL mode the committed row is still
    in the ``-wal`` sidecar, so a file copy yields a database with no table in
    it, while SQLite's backup API reads the committed state.
    """
    database = tmp_path / "openvoca.db"
    live = sqlite3.connect(database)
    try:
        live.execute("PRAGMA journal_mode=WAL")
        live.execute("CREATE TABLE wordrecord (lemma TEXT)")
        live.execute("INSERT INTO wordrecord VALUES ('harbor')")
        live.commit()

        # Proves the assertion below distinguishes the two mechanisms rather
        # than passing for any copy at all.
        copied = tmp_path / "copied.db"
        copied.write_bytes(database.read_bytes())
        with pytest.raises(sqlite3.OperationalError):
            sqlite3.connect(copied).execute("SELECT * FROM wordrecord").fetchall()

        snapshot = deploy.snapshot_database(
            database, tmp_path / "snapshots", "20260101-000000"
        )
    finally:
        live.close()

    assert snapshot is not None
    rows = sqlite3.connect(snapshot).execute("SELECT lemma FROM wordrecord").fetchall()
    assert rows == [("harbor",)]


# Covers: AC-PRIV-003-03
def test_snapshot_reports_nothing_to_copy_on_a_first_deployment(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """A first deployment has no database, which is not a failure."""
    result = deploy.snapshot_database(
        tmp_path / "absent" / "openvoca.db", tmp_path / "snapshots", "20260101-000000"
    )

    assert result is None
    assert "nothing to snapshot" in capsys.readouterr().out


# Covers: AC-PRIV-003-02
def test_switch_replaces_the_link_without_a_gap(tmp_path: Path) -> None:
    """The link always resolves, before and after."""
    old = tmp_path / "releases" / "old"
    new = tmp_path / "releases" / "new"
    old.mkdir(parents=True)
    new.mkdir()
    link = tmp_path / "current"
    os.symlink(old, link)

    deploy.switch_symlink(link, new)

    assert Path(os.readlink(link)) == new
    assert link.exists()


# Covers: AC-PRIV-003-05
def test_failed_switch_leaves_the_previous_revision_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupted switch must not be able to produce a half-switched state."""
    old = tmp_path / "releases" / "old"
    new = tmp_path / "releases" / "new"
    old.mkdir(parents=True)
    new.mkdir()
    link = tmp_path / "current"
    os.symlink(old, link)

    def refuse(src, dst):
        raise OSError("interrupted")

    monkeypatch.setattr(deploy.os, "replace", refuse)

    with pytest.raises(OSError):
        deploy.switch_symlink(link, new)

    assert Path(os.readlink(link)) == old
    assert not (tmp_path / "current.pending").exists()


# Covers: AC-PRIV-003-02
def test_switch_writes_the_link_the_service_resolves(tmp_path: Path) -> None:
    """The address the service is configured with must reach the new revision."""
    new = tmp_path / "releases" / "abc"
    new.mkdir(parents=True)
    link = tmp_path / "current"

    deploy.switch_symlink(link, new)

    assert link.resolve() == new.resolve()


# Covers: AC-PRIV-003-01
def test_deployment_accepts_one_revision_and_nothing_else(
    capsys: pytest.CaptureFixture,
) -> None:
    """The interface is a revision, so there is no second argument to get wrong."""
    assert deploy.main([]) == 2
    assert deploy.main(["one", "two"]) == 2
    assert deploy.USAGE in capsys.readouterr().err


# Covers: AC-PRIV-003-01, AC-PRIV-003-04, AC-PRIV-003-07
def test_failed_step_keeps_the_previous_revision_serving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """A failure before the switch must leave what is being served alone.

    The frontend build is made to fail, which happens after the export and the
    dependency install, so the assertion covers the case where work has already
    been done against the new revision.
    """
    log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    previous = _serve(layout, "previous")
    _write_executable(binary_dir / "pnpm", _fake_recorder("pnpm", exit_code=1))

    code = deploy.main(["next"])

    assert code == 1
    assert Path(os.readlink(layout.current)) == previous
    assert not (layout.root / "current.pending").exists()


# Covers: AC-PRIV-003-08
def test_failure_after_the_switch_reports_how_to_go_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """The restart is the one step that cannot be rehearsed, so its failure must
    leave the operator with the exact command that undoes the deployment."""
    log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    _write_executable(
        binary_dir / "systemctl", _fake_recorder("systemctl", exit_code=1)
    )

    code = deploy.main(["next"])
    err = capsys.readouterr().err

    assert code == 1
    assert "Still serving previous." in err
    assert "To go back: deploy.py previous" in err


# Covers: AC-PRIV-003-02, AC-PRIV-003-03, AC-PRIV-003-06
def test_successful_deployment_switches_records_and_restarts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """The happy path: code exported, snapshot taken, link switched, service up.

    The order is asserted because it is the property that makes an aborted run
    safe -- the switch and the restart must come after everything that can fail
    on its own.
    """
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")

    code = deploy.main(["abc123"])

    assert code == 0
    assert Path(os.readlink(layout.current)) == layout.release("abc123")
    assert (layout.release("abc123") / "backend" / "pyproject.toml").exists()
    assert layout.database.exists()

    snapshots = sorted(layout.snapshots.glob("openvoca-*.db"))
    assert len(snapshots) == 1
    rows = sqlite3.connect(snapshots[0]).execute("SELECT * FROM wordrecord").fetchall()
    assert rows == [("harbor",)]

    # The service reports this revision once it restarts, and knows which
    # version to compare against for updates. Without the version the update
    # check returns early, so a deployment that omitted it would never offer an
    # update at all.
    env_file = layout.revision_env.read_text()
    assert "OPENVOCA_REVISION=abc123" in env_file
    assert "OPENVOCA_VERSION=1.2.3" in env_file

    tools_used = [call["tool"] for call in _calls(log)]
    assert tools_used[-1] == "systemctl"
    assert tools_used.index("pnpm") < tools_used.index("systemctl")


# Covers: AC-PRIV-001-05
def test_the_deployment_produces_an_environment_the_update_check_can_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """The version the deployment records must be the one the application reads.

    These live in different files and different processes, so nothing but a test
    ties them together. Left untied, the deployment would look complete while the
    update notice silently never appeared, because the check returns early when
    no version is set.
    """
    _log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    monkeypatch.setattr(main_module, "_update_info", dict(_EMPTY_UPDATE_INFO))
    monkeypatch.setattr(main_module.httpx, "AsyncClient", _OfflineClient)

    assert deploy.main(["abc123"]) == 0

    # Apply exactly what the service manager would load from the file.
    for line in layout.revision_env.read_text().splitlines():
        key, _, value = line.partition("=")
        monkeypatch.setenv(key, value)

    asyncio.run(main_module._check_for_updates())

    assert main_module._update_info["currentVersion"] == _FAKE_VERSION


# Covers: AC-PRIV-003-04
def test_a_missing_executable_becomes_a_deployment_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """subprocess reports an absent executable as a plain FileNotFoundError.

    Left alone it escapes the handler in main(), so the operator gets a traceback
    instead of being told which revision is still serving. Raising DeployError
    keeps every failure on one path.
    """
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))

    with pytest.raises(deploy.DeployError, match="is not on PATH"):
        deploy._run(["uv", "sync"], cwd=tmp_path)


# Covers: AC-PRIV-003-04
def test_missing_tool_stops_the_deployment_before_any_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """An unreachable toolchain must be detected while nothing has been done.

    Failing at the step that needed the tool would leave a half-built release
    directory behind, and the check itself costs nothing. Most often the tool is
    installed but the caller's PATH cannot see it -- sudo replaces PATH with its
    own secure_path -- so the message has to name the PATH that was searched.
    """
    log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    previous = _serve(layout, "previous")
    (binary_dir / "uv").unlink()
    # PATH must contain only the stand-ins. Prepending them would leave the real
    # tools reachable, and the check would pass while the test believed it had
    # removed one.
    monkeypatch.setenv("PATH", str(binary_dir))

    code = deploy.main(["next"])
    err = capsys.readouterr().err

    assert code == 1
    assert "uv" in err
    assert "PATH searched" in err
    # The message points at the invocation that would work.
    assert 'sudo env "PATH=$PATH"' in err
    # Nothing ran, so nothing was left behind.
    assert _calls(log) == []
    assert not layout.release("next").exists()
    assert Path(os.readlink(layout.current)) == previous


# Covers: AC-PRIV-003-08
def test_a_missing_tool_still_reports_the_revision_in_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """Even a failure this early must leave the operator knowing where they are."""
    _log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    (binary_dir / "pnpm").unlink()
    monkeypatch.setenv("PATH", str(binary_dir))

    code = deploy.main(["next"])
    err = capsys.readouterr().err

    assert code == 1
    assert "Still serving previous." in err
    assert "To go back: deploy.py previous" in err


# Covers: AC-PRIV-003-02
def test_two_revisions_do_not_share_a_temporary_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deriving the archive name from the revision collides on the version dots.

    Path("v0.10.3").with_suffix(".tar") is "v0.10.tar", because the last
    dot-component counts as a suffix. Every patch release of a minor version
    would therefore export through the same path, and two deployments running at
    once would clobber each other's archive -- producing a corrupt extraction
    rather than a clear failure.
    """
    repository = tmp_path / "repo"
    repository.mkdir()
    seen: list[Path] = []

    def fake_run(argv, *, cwd, env=None):
        output = next(a.split("=", 1)[1] for a in argv if a.startswith("--output="))
        seen.append(Path(output))
        with tarfile.open(output, "w"):
            pass  # a valid, empty archive

    monkeypatch.setattr(deploy, "_run", fake_run)

    for revision in ("v0.10.3", "v0.10.4"):
        deploy.materialize(repository, revision, tmp_path / "releases" / revision)

    assert len(seen) == 2
    assert seen[0] != seen[1]


# Covers: AC-PRIV-003-02
def test_the_temporary_archive_is_removed_after_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leftover archive would be picked up by nothing, but it is still litter."""
    repository = tmp_path / "repo"
    repository.mkdir()

    def fake_run(argv, *, cwd, env=None):
        output = next(a.split("=", 1)[1] for a in argv if a.startswith("--output="))
        with tarfile.open(output, "w"):
            pass

    monkeypatch.setattr(deploy, "_run", fake_run)

    deploy.materialize(repository, "v0.10.3", tmp_path / "releases" / "v0.10.3")

    leftovers = list((tmp_path / "releases").glob("*.tar"))
    assert leftovers == []


# Covers: AC-PRIV-001-07
@pytest.mark.parametrize("home", [Path.home(), Path("/root"), Path("/home/someone")])
def test_the_interpreter_directory_is_never_under_a_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, home: Path
) -> None:
    """A home directory is the one place the interpreter must not live.

    Not for permission reasons. The unit's ProtectHome makes home directories
    absent from the service's namespace rather than read-only, so an interpreter
    under any home is unreachable no matter what mode it has.
    """
    layout = deploy.Layout(root=tmp_path / "opt", data_dir=tmp_path / "var")

    assert not layout.python_dir.is_relative_to(home)


def _uv_calls(log: Path) -> list[dict]:
    return [call for call in _calls(log) if call["tool"] == "uv"]


# Covers: AC-PRIV-001-08
@pytest.mark.parametrize("with_snapshot", [True, False])
def test_every_uv_invocation_is_told_where_to_manage_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    with_snapshot: bool,
) -> None:
    """Every invocation, not only the install.

    The interpreter is recorded inside the virtualenv, so one invocation falling
    back to the HOME-derived default reintroduces the failure. Both the
    snapshot and the empty-directory paths are covered because they reach
    preflight through different code.
    """
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    if with_snapshot:
        _seed_database(layout)
    _serve(layout, "previous")

    assert deploy.main(["abc123"]) == 0

    uv_calls = _uv_calls(log)
    assert len(uv_calls) >= 2  # the install and the preflight
    for call in uv_calls:
        assert call["uv_python_dir"], f"no interpreter directory for {call['argv']}"
        assert Path(call["uv_python_dir"]) == layout.python_dir
        assert not Path(call["uv_python_dir"]).is_relative_to(Path.home())


# Covers: AC-PRIV-001-08
@pytest.mark.parametrize("root", [Path("/opt/openvoca"), Path("/srv/openvoca")])
def test_the_interpreter_directory_follows_the_deployment_root(
    root: Path,
) -> None:
    """It is derived from the layout, not from the caller's environment.

    A deployment that hard-coded a path would break the moment OPENVOCA_ROOT
    moved, and would leave no way to see where its interpreters went.
    """
    layout = deploy.layout_from_env(
        {"OPENVOCA_ROOT": str(root), "OPENVOCA_DATA_DIR": "/var/lib/openvoca"}
    )

    assert layout.python_dir == root / "python"
    assert deploy.uv_env(layout) == {"UV_PYTHON_INSTALL_DIR": str(root / "python")}


# Covers: AC-PRIV-001-08
def test_the_interpreter_directory_is_outside_home_by_default() -> None:
    """The shipped defaults must already satisfy the constraint.

    A default under the deploying user's home would make the failure the normal
    case rather than something that needs to be configured away.
    """
    layout = deploy.layout_from_env({})

    assert not layout.python_dir.is_relative_to(Path.home())
    assert not str(layout.python_dir).startswith("/root")


# Covers: AC-PRIV-001-07
def test_the_deployment_reports_where_interpreters_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """The location has to be visible, because the service's ability to start
    depends on it and nothing else announces it."""
    _log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")

    assert deploy.main(["abc123"]) == 0

    assert str(layout.python_dir) in capsys.readouterr().out


# Covers: AC-PRIV-004-02
@pytest.mark.parametrize(
    "state", ["disabled", "enabled-runtime", "static", "masked", "not-found"]
)
def test_a_service_that_will_not_survive_a_reboot_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
    state: str,
) -> None:
    """Enablement is checked once at install time and is invisible afterwards.

    ``enabled-runtime`` is included deliberately: it reads like enablement but
    writes its symlink into /run, which a reboot clears. ``static`` means the
    unit has no [Install] section and cannot be enabled at all. Neither would be
    caught by trusting systemctl's exit code, since both exit zero.
    """
    _log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    _write_executable(binary_dir / "systemctl", _fake_systemctl(state))

    assert deploy.main(["abc123"]) == 0
    err = capsys.readouterr().err

    assert "not set to start at boot" in err
    assert state in err
    assert "systemctl enable openvoca" in err


# Covers: AC-PRIV-004-02
def test_an_enabled_service_is_not_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """No warning when the deployment is correctly installed, or it becomes noise."""
    _log, binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    _write_executable(binary_dir / "systemctl", _fake_systemctl("enabled"))

    assert deploy.main(["abc123"]) == 0

    assert "boot" not in capsys.readouterr().err


# Covers: AC-PRIV-004-02
def test_boot_state_is_asked_of_the_service_manager(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """The question must reach systemd, and a definite answer must win over silence."""
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")

    assert deploy.main(["abc123"]) == 0

    asked = [call["argv"] for call in _calls(log) if call["argv"][:1] == ["is-enabled"]]

    assert asked == [["is-enabled", "openvoca"]]


# Covers: AC-PRIV-004-02
def test_boot_state_is_not_guessed_for_another_service_manager(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tools,
    capsys: pytest.CaptureFixture,
) -> None:
    """A non-systemd deployment is not thereby broken.

    Enablement is a systemd concept. Reporting it as a problem for a deployment
    driven by something else would be a false alarm about a configuration the
    script cannot see.
    """
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    monkeypatch.setenv("OPENVOCA_RESTART_CMD", "true")

    assert deploy.main(["abc123"]) == 0

    assert "boot" not in capsys.readouterr().err
    assert [call for call in _calls(log) if call["argv"][:1] == ["is-enabled"]] == []


# Covers: AC-PRIV-003-06
def test_restart_is_what_the_service_is_told_to_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """The service manager is not hard-coded into the deployment flow."""
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")

    assert deploy.main(["abc123"]) == 0

    restart_call = next(call for call in _calls(log) if call["argv"][:1] == ["restart"])
    assert restart_call["tool"] == "systemctl"
    assert restart_call["argv"] == ["restart", "openvoca"]


# Covers: AC-PRIV-003-06
def test_health_reports_the_running_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Which revision answers must be observable from the running application.

    Read from the environment rather than inferred from the file layout: a
    symlink switch changes the path files resolve through, so deriving it would
    mean the application knowing how it was deployed.
    """
    monkeypatch.setenv("OPENVOCA_REVISION", "abc123")

    assert client.get("/api/health").json()["revision"] == "abc123"


# Covers: AC-PRIV-003-06
def test_health_reports_an_empty_revision_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A development run has no revision, which must not be an error."""
    monkeypatch.delenv("OPENVOCA_REVISION", raising=False)

    assert client.get("/api/health").json()["revision"] == ""


# Covers: AC-PRIV-003-03
def test_preflight_runs_against_a_copy_not_the_live_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """A revision being tested must not write to the database it is tested against.

    Importing the application creates missing tables, so testing against the live
    database would let a revision that is about to be rejected modify production
    data.
    """
    log, _binary_dir = tools
    layout = _layout(tmp_path, monkeypatch)
    _seed_database(layout)
    _serve(layout, "previous")
    before = layout.database.read_bytes()

    assert deploy.main(["abc123"]) == 0

    assert layout.database.read_bytes() == before

    preflight = [
        call
        for call in _calls(log)
        if call["tool"] == "uv" and "src.preflight" in call["argv"]
    ]
    assert len(preflight) == 1
    assert preflight[0]["data_dir"] not in ("", str(layout.data_dir))
    assert preflight[0]["cwd"].endswith(str(Path("releases") / "abc123" / "backend"))
