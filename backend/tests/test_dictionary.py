import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.dictionary import DictionaryEntry, lookup, lookup_custom

client = TestClient(app)


# ---------------------------------------------------------------------------
# Service-layer tests (using the real dictionary.db)
# ---------------------------------------------------------------------------

DICT_DB = Path(__file__).parent.parent / "data" / "dictionary.db"


@pytest.fixture()
def _skip_if_no_dict():
    if not DICT_DB.exists():
        pytest.skip("dictionary.db not found")


@pytest.mark.usefixtures("_skip_if_no_dict")
# Covers: AC-DICT-001-01
def test_lookup_known_word() -> None:
    """lookup should return an entry for a common word."""
    entry = lookup("apple")
    assert entry is not None
    assert entry.word == "apple"
    assert entry.translation  # has Chinese translation
    assert isinstance(entry, DictionaryEntry)


@pytest.mark.usefixtures("_skip_if_no_dict")
# Covers: AC-DICT-001-01
def test_lookup_case_insensitive() -> None:
    """lookup should be case-insensitive."""
    entry = lookup("APPLE")
    assert entry is not None
    assert entry.word == "apple"


@pytest.mark.usefixtures("_skip_if_no_dict")
# Covers: AC-DICT-001-01
def test_lookup_unknown_word() -> None:
    """lookup should return None for words not in the dictionary."""
    entry = lookup("xyzzynotaword")
    assert entry is None


# ---------------------------------------------------------------------------
# Custom database tests (isolated, no dependency on real dict)
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dict_db(tmp_path: Path) -> Path:
    """Create a minimal dictionary database for testing."""
    db_path = tmp_path / "test_dict.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE dictionary (
            word TEXT NOT NULL,
            phonetic TEXT,
            definition TEXT,
            translation TEXT NOT NULL,
            pos TEXT,
            tag TEXT,
            exchange TEXT
        )
    """)
    conn.execute(
        "INSERT INTO dictionary VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "harbor",
            "hɑːrbər",
            "a sheltered port",
            "n. 港口",
            "n:100",
            "cet4",
            "s:harbors",
        ),
    )
    conn.execute("CREATE INDEX idx_dictionary_word ON dictionary (word COLLATE NOCASE)")
    conn.commit()
    conn.close()
    return db_path


# Covers: AC-DICT-001-02
def test_lookup_custom_found(tmp_dict_db: Path) -> None:
    """lookup_custom should find a word in a custom database."""
    entry = lookup_custom("harbor", tmp_dict_db)
    assert entry is not None
    assert entry.word == "harbor"
    assert entry.phonetic == "hɑːrbər"
    assert entry.translation == "n. 港口"
    assert entry.tag == "cet4"


# Covers: AC-DICT-001-02
def test_lookup_custom_not_found(tmp_dict_db: Path) -> None:
    """lookup_custom should return None for missing words."""
    entry = lookup_custom("zzzz", tmp_dict_db)
    assert entry is None


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_skip_if_no_dict")
# Covers: AC-DICT-001-03
def test_api_dictionary_found() -> None:
    """GET /api/dictionary/<word> should return definition for a known word."""
    response = client.get("/api/dictionary/abandon")
    assert response.status_code == 200
    data = response.json()
    assert data["word"] == "abandon"
    assert data["translation"]
    assert data["phonetic"]


@pytest.mark.usefixtures("_skip_if_no_dict")
# Covers: AC-DICT-001-03
def test_api_dictionary_not_found() -> None:
    """GET /api/dictionary/<word> should return 404 for unknown words."""
    response = client.get("/api/dictionary/xyzzynotaword")
    assert response.status_code == 404
