"""Tests for the static interface routes (AC-SHELL-001-02).

The routes are registered by ``register_spa`` rather than as a side effect of the
module importing, so these tests build their own application against a temporary
build directory. The previous version guarded on ``hasattr`` and therefore tested
nothing in CI, where no frontend build exists -- a green test with no coverage.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import register_spa


def _client(dist: object, tmp_path) -> TestClient:
    app = FastAPI()
    assert register_spa(app, tmp_path / "dist") is True
    return TestClient(app)


def _build(tmp_path) -> "object":
    """A minimal frontend build: an index, an asset, and a root-level file."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>OpenVoca</html>")
    (dist / "assets" / "index.js").write_text("console.log('openvoca')")
    (dist / "favicon.svg").write_text("<svg/>")
    return dist


# Covers: AC-SHELL-001-02
def test_spa_fallback_returns_index_html(tmp_path: pytest.TempPathFactory) -> None:
    """A path with no file behind it must serve the interface, not a 404."""
    dist = _build(tmp_path)
    client = _client(dist, tmp_path)

    response = client.get("/any/path")

    assert response.status_code == 200
    assert response.text == "<html>OpenVoca</html>"


# Covers: AC-SHELL-001-02
def test_spa_serves_the_root_index(tmp_path: pytest.TempPathFactory) -> None:
    """The root is the same interface, reached without a path."""
    dist = _build(tmp_path)
    client = _client(dist, tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert response.text == "<html>OpenVoca</html>"


# Covers: AC-SHELL-001-02
def test_spa_serves_real_files_before_falling_back(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """A file that exists is served as itself rather than as the interface."""
    dist = _build(tmp_path)
    client = _client(dist, tmp_path)

    assert client.get("/favicon.svg").text == "<svg/>"
    assert client.get("/assets/index.js").text == "console.log('openvoca')"


# Covers: AC-SHELL-001-02
def test_spa_is_not_registered_without_a_build(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """No build is a normal state in development, not an error.

    Registration reports it rather than raising, so importing the application
    works in a checkout that has never been built.
    """
    app = FastAPI()

    assert register_spa(app, tmp_path / "absent") is False
    assert not [route for route in app.routes if route.path == "/{path:path}"]


# Covers: AC-SHELL-001-02
def test_a_build_without_assets_is_rejected(tmp_path: pytest.TempPathFactory) -> None:
    """A malformed build must fail with a reason, not a directory complaint.

    ``StaticFiles`` would report a missing directory; the operator needs to know
    the build itself is wrong.
    """
    dist = tmp_path / "dist"
    dist.mkdir()

    with pytest.raises(RuntimeError, match="no assets directory"):
        register_spa(FastAPI(), dist)
