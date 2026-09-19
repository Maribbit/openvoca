"""Tests for the process supervision section of docs/specs/private-deployment.md.

Most of these assert directives rather than behaviour, because systemd is what
interprets a unit file and it is not available here. Two things make that a
reasonable substitute: the directives are the whole contract the deployment
depends on, and the one directive that can be exercised -- the command the unit
runs -- is executed for real against the repository, so a unit whose ExecStart
does not actually start the application fails this file rather than the
deployment machine.
"""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
UNIT_PATH = REPO_ROOT / "deploy" / "openvoca.service"

# Values the unit supplies as defaults; the test overrides both.
HOST = "127.0.0.1"


def _parse_unit(path: Path) -> dict[str, dict[str, list[str]]]:
    """Read a systemd unit, keeping repeated keys.

    A minimal reader rather than ``configparser``: systemd units are INI-shaped
    but repeat keys legitimately, which ``configparser`` collapses, and the
    repeated ``Environment=`` lines are exactly what this file asserts on.
    """
    sections: dict[str, dict[str, list[str]]] = {}
    current: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            continue
        if current is None or "=" not in line:
            continue
        key, _, value = line.partition("=")
        sections[current].setdefault(key.strip(), []).append(value.strip())

    return sections


@pytest.fixture(scope="module")
def unit() -> dict[str, dict[str, list[str]]]:
    assert UNIT_PATH.exists(), f"the service unit is missing: {UNIT_PATH}"
    return _parse_unit(UNIT_PATH)


def _one(unit: dict, section: str, key: str) -> str:
    values = unit.get(section, {}).get(key)
    assert values, f"{section}.{key} is not set"
    return values[0]


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return int(probe.getsockname()[1])


def _exec_start(unit: dict, overrides: dict[str, str]) -> list[str]:
    """Resolve ExecStart the way systemd would, then point it at this checkout.

    Two substitutions are needed to run a unit written for the deployment
    machine on a development checkout, and both are asserted rather than assumed:
    the interpreter and the working directory are deployment paths, while the
    command itself is used exactly as the unit writes it.
    """
    environment: dict[str, str] = {}
    for entry in unit.get("Service", {}).get("Environment", []):
        key, _, value = entry.partition("=")
        environment[key] = value
    # systemd applies EnvironmentFile after Environment, so these win.
    environment.update(overrides)

    command = _one(unit, "Service", "ExecStart")
    for key, value in environment.items():
        command = command.replace("${" + key + "}", value)
    assert "${" not in command, f"unexpanded variable in ExecStart: {command}"

    argv = command.split()
    argv[0] = sys.executable
    return argv


# Covers: AC-PRIV-004-01
def test_service_is_restarted_after_it_exits(unit: dict) -> None:
    """A crash or a killed process must not end the service.

    The directive is asserted because systemd interprets it; the deployment
    cannot observe it from here.
    """
    assert _one(unit, "Service", "Restart") in {"always", "on-failure"}
    assert _one(unit, "Service", "RestartSec")


# Covers: AC-PRIV-004-01
def test_a_failing_revision_does_not_restart_forever(unit: dict) -> None:
    """A revision that refuses to start must become visible, not loop.

    The schema check makes "won't start" a normal outcome, and an unbounded
    restart loop would bury the reason it refuses in the journal.
    """
    assert int(_one(unit, "Unit", "StartLimitBurst")) > 0
    assert int(_one(unit, "Unit", "StartLimitIntervalSec")) > 0


# Covers: AC-PRIV-004-02
def test_service_starts_with_the_host(unit: dict) -> None:
    """Enabled units are pulled in by the boot target."""
    assert "multi-user.target" in _one(unit, "Install", "WantedBy")

    # Without the network the service binds nothing and, with a restart limit,
    # does not quietly recover when the interface appears.
    assert "network-online.target" in _one(unit, "Unit", "After")
    assert "network-online.target" in _one(unit, "Unit", "Wants")


# Covers: AC-PRIV-004-03
def test_listen_address_and_port_are_supplied_by_the_unit(unit: dict) -> None:
    """Both are expanded by systemd, so the application reads neither.

    The application is handed --host and --port like any other invocation, which
    keeps its configuration surface unchanged and puts the decision in the layer
    that owns how the process is started.
    """
    exec_start = _one(unit, "Service", "ExecStart")

    assert "--host ${OPENVOCA_HOST}" in exec_start
    assert "--port ${OPENVOCA_PORT}" in exec_start

    defaults = dict(
        entry.partition("=")[::2] for entry in unit["Service"]["Environment"]
    )
    assert defaults["OPENVOCA_HOST"]
    assert defaults["OPENVOCA_PORT"].isdigit()


# Covers: AC-PRIV-004-03
def test_defaults_can_be_overridden_without_editing_the_unit(unit: dict) -> None:
    """An override must not require replacing a file the deployment ships.

    A unit that has to be edited to change a port becomes a second thing to keep
    in sync with the repository.
    """
    overrides = [e for e in unit["Service"]["EnvironmentFile"] if e.startswith("-")]

    assert overrides, "no optional override file is loaded"
    # Optional, so a machine without the file still starts.
    assert any("openvoca.conf" in entry for entry in overrides)


# Covers: AC-PRIV-004-03
def test_the_unit_runs_the_service_on_a_port_it_was_given(unit: dict) -> None:
    """Exercises the expansion rather than trusting the syntax.

    The service is started on a port unrelated to the default, so a unit whose
    variables did not expand would be caught here.
    """
    port = _free_port()
    assert port != int(
        dict(e.partition("=")[::2] for e in unit["Service"]["Environment"])[
            "OPENVOCA_PORT"
        ]
    )

    body = _request_health(unit, port)

    assert body["status"] == "ok"


# Covers: AC-PRIV-004-04
def test_the_application_does_not_terminate_tls(unit: dict) -> None:
    """Transport security belongs to the private network, not the application.

    An application holding a certificate is an application that has to be
    restarted when the certificate rotates, and it never terminates TLS here
    anyway.
    """
    service = unit["Service"]

    for section in ("ExecStart", "ExecStartPre"):
        for command in service.get(section, []):
            lowered = command.lower()
            assert "--ssl" not in lowered
            assert "cert" not in lowered

    # Nothing mounts a certificate or key into the service either.
    assert "SSL" not in " ".join(unit.get("Service", {}).keys())


# Covers: AC-PRIV-004-05
def test_health_endpoint_is_served_by_the_unit_s_command(unit: dict) -> None:
    """The command the unit runs must answer the probe a supervisor would use.

    A unit file whose ExecStart cannot start the application is worse than no
    unit file, because it looks like supervision.
    """
    body = _request_health(unit, _free_port())

    assert body["status"] == "ok"
    assert "revision" in body


def _request_health(unit: dict, port: int, timeout: float = 40.0) -> dict:
    """Start the service exactly as the unit does and read its health endpoint."""
    argv = _exec_start(unit, {"OPENVOCA_HOST": HOST, "OPENVOCA_PORT": str(port)})

    # The unit's working directory is the deployment path; the command is run
    # from the checkout instead, which is the only difference that matters here.
    assert _one(unit, "Service", "WorkingDirectory").endswith("current/backend")

    import os

    import tempfile

    with tempfile.TemporaryDirectory(prefix="openvoca-supervision-") as data_dir:
        process = subprocess.Popen(
            argv,
            cwd=BACKEND_DIR,
            env={**os.environ, "OPENVOCA_DATA_DIR": data_dir},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise AssertionError(
                        f"the unit's command exited with {process.returncode}:\n"
                        f"{process.stdout.read()}"
                    )
                try:
                    url = f"http://{HOST}:{port}/api/health"
                    with urllib.request.urlopen(url, timeout=1) as response:
                        return json.load(response)
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    time.sleep(0.25)
            raise AssertionError("the unit's command never became ready")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
