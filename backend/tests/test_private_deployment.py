"""Tests for the private-network deployment spec (docs/specs/private-deployment.md).

The distribution contract is about how the application behaves under a different
assembly than the development checkout: a data directory that lives outside the
code tree, static assets located relative to the application file, and a version
supplied by the caller. These properties are what make frequent redeployment
safe, so they are tested rather than assumed.
"""

import asyncio
import json
import types
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

import bundle
import src.main as main_module
from src.main import app
from src.services.settings_store import upsert_setting
from src.services.word_store import _make_engine, apply_feedback

client = TestClient(app)

_EMPTY_UPDATE_INFO = {
    "checked": False,
    "hasUpdate": False,
    "currentVersion": "",
    "latestVersion": "",
    "url": "",
}


class _OfflineClient:
    """Stand-in for ``httpx.AsyncClient`` that records attempts and stays offline.

    The update check is a background convenience, so the tests must neither
    depend on GitHub being reachable nor reach it. Recording the attempts lets a
    test tell "skipped" apart from "tried and failed".
    """

    attempts: list[str] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_OfflineClient":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def get(self, url: str, **kwargs) -> None:
        type(self).attempts.append(url)
        raise httpx.ConnectError("network access is not available in tests")


def _tree(root: Path) -> set[Path]:
    """Every path under *root*, ignoring interpreter bytecode caches.

    ``__pycache__`` contents depend on import order rather than on application
    behaviour, so including them would make the assertions flaky without saying
    anything about where the application writes.
    """
    return {
        path.relative_to(root)
        for path in root.rglob("*")
        if "__pycache__" not in path.parts
    }


def _launcher_env(bundle_dir: Path) -> dict:
    """Run the bundle launcher and capture the environment it hands to uvicorn.

    The launcher ships as a string rather than as an importable module, and its
    whole job is to build an environment and pass it to a child process, so the
    only way to observe that environment without starting a server is to execute
    the shipped source and intercept the spawn. Both ``subprocess`` and ``time``
    are replaced with stand-ins in the launcher's own namespace, so nothing
    outside this test is affected.
    """
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "openvoca.json").write_text(
        json.dumps({"version": "1.2.3", "open_browser": False}),
        encoding="utf-8",
    )

    namespace: dict = {
        "__file__": str(bundle_dir / "start.py"),
        "__name__": "openvoca_launcher",
    }
    exec(compile(bundle._START_PY, "start.py", "exec"), namespace)

    captured: dict = {}

    class _ExitedProcess:
        """A child that has already exited, so the readiness wait ends at once."""

        def __init__(self, argv, cwd=None, env=None) -> None:
            captured["argv"] = argv
            captured["cwd"] = cwd
            captured["env"] = env

        def poll(self):
            return 1

        def terminate(self) -> None:
            pass

        def wait(self) -> int:
            return 1

    namespace["subprocess"] = types.SimpleNamespace(Popen=_ExitedProcess)
    namespace["time"] = types.SimpleNamespace(sleep=lambda _seconds: None)

    # An exited child is reported as a startup failure, which is how main()
    # stops before the health check is ever attempted.
    with pytest.raises(SystemExit):
        namespace["main"]()

    return captured["env"]


# Covers: AC-PRIV-001-01
def test_launcher_keeps_a_caller_supplied_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A deployment may keep its database outside the bundle.

    Otherwise replacing the bundle directory -- which is what an update does --
    would take the database with it.
    """
    external = tmp_path / "var-lib-openvoca"
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(external))

    env = _launcher_env(tmp_path / "bundle")

    assert env["OPENVOCA_DATA_DIR"] == str(external)


# Covers: AC-PRIV-001-01
def test_launcher_defaults_data_dir_inside_the_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without an override the bundle stays self-contained and unpack-and-run."""
    monkeypatch.delenv("OPENVOCA_DATA_DIR", raising=False)
    bundle_dir = tmp_path / "bundle"

    env = _launcher_env(bundle_dir)

    assert env["OPENVOCA_DATA_DIR"] == str(bundle_dir / "data")
    # These two are forced rather than defaulted: the bundle cannot start
    # without PYTHONPATH, and would misreport updates without a version.
    assert env["PYTHONPATH"] == str(bundle_dir / "site-packages")
    assert env["OPENVOCA_VERSION"] == "1.2.3"


# Covers: AC-PRIV-001-02
def test_runtime_writes_stay_inside_the_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing the application writes may land in the code tree or the cwd."""
    data_dir = tmp_path / "openvoca-data"
    # The assembly layer owns this directory; the application only writes in it.
    data_dir.mkdir()
    work_dir = tmp_path / "elsewhere"
    work_dir.mkdir()
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(data_dir))
    monkeypatch.chdir(work_dir)

    code_dir = Path(main_module.__file__).resolve().parents[1]
    code_before = _tree(code_dir)

    engine = _make_engine()
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr("src.services.word_store._engine", engine)
    apply_feedback(["harbor"], ["harbor"], "A harbor lantern flickered.")
    upsert_setting("interface", "theme", "dark")
    engine.dispose()

    assert (data_dir / "openvoca.db").exists()
    assert _tree(work_dir) == set()
    assert _tree(code_dir) == code_before


# Covers: AC-PRIV-001-03
def test_data_dir_is_independent_of_cwd_and_code_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The data path must be a function of the environment variable alone.

    Resolving it relative to the working directory or the application file would
    tie it to a code revision, so an update could silently start using a fresh,
    empty database while the real one sat untouched.
    """
    data_dir = tmp_path / "openvoca-data"
    data_dir.mkdir()
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(data_dir))

    first = tmp_path / "a"
    first.mkdir()
    monkeypatch.chdir(first)
    from_first = str(_make_engine().url)

    second = tmp_path / "b"
    second.mkdir()
    monkeypatch.chdir(second)
    from_second = str(_make_engine().url)

    assert from_first == from_second
    assert str(data_dir / "openvoca.db") in from_first


# Covers: AC-PRIV-001-04
def test_static_dir_is_derived_from_the_app_file() -> None:
    """A relative path would be resolved against the working directory.

    That directory is chosen by the service unit, and the path it points at
    changes when a symlink is repointed at a new revision, so the location of
    the frontend build must not depend on either.
    """
    dist = Path(main_module._frontend_dist)
    app_file = Path(main_module.__file__).resolve()

    assert dist.is_absolute()
    assert dist == app_file.parents[2] / "frontend" / "dist"


# Covers: AC-PRIV-001-05
def test_injected_version_is_reported_by_the_update_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The version reaches the interface through the environment, not the code."""
    monkeypatch.setenv("OPENVOCA_VERSION", "9.9.9")
    monkeypatch.setattr(main_module, "_update_info", dict(_EMPTY_UPDATE_INFO))
    monkeypatch.setattr(main_module.httpx, "AsyncClient", _OfflineClient)

    asyncio.run(main_module._check_for_updates())

    assert client.get("/api/update-check").json()["currentVersion"] == "9.9.9"


# Covers: AC-PRIV-001-06
def test_absent_version_skips_the_update_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a version there is nothing to compare against.

    The check must be skipped rather than attempted-and-failed, and must not
    disturb any other endpoint.
    """
    monkeypatch.delenv("OPENVOCA_VERSION", raising=False)
    monkeypatch.setattr(main_module, "_update_info", dict(_EMPTY_UPDATE_INFO))
    monkeypatch.setattr(main_module.httpx, "AsyncClient", _OfflineClient)
    _OfflineClient.attempts.clear()

    asyncio.run(main_module._check_for_updates())

    assert _OfflineClient.attempts == []
    assert main_module._update_info["checked"] is False
    assert client.get("/api/health").status_code == 200
