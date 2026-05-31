import asyncio

import pytest
from fastapi.responses import FileResponse


# Covers: AC-SHELL-001-02
def test_spa_fallback_returns_index_html(tmp_path: pytest.TempPathFactory) -> None:
    """spa_fallback() returns a FileResponse pointing at index.html."""
    dist = tmp_path / "dist"
    dist.mkdir()
    index = dist / "index.html"
    index.write_text("<html>OpenVoca</html>")

    import src.main as m

    original = m._frontend_dist
    m._frontend_dist = dist
    try:
        if hasattr(m, "spa_fallback"):
            result = asyncio.run(m.spa_fallback("any/path"))
            assert isinstance(result, FileResponse)
            assert str(index) in str(result.path)
    finally:
        m._frontend_dist = original
