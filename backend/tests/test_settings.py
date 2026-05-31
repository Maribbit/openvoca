"""Tests for settings storage and API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from src.main import app
from src.services.settings_store import (
    clear_all_settings,
    delete_namespace,
    get_all_settings,
    get_namespace,
    get_setting,
    init_settings_table,
    upsert_namespace,
    upsert_setting,
)

client = TestClient(app)


def _in_memory_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    SQLModel.metadata.create_all(engine)
    return engine


# --- Unit tests for settings_store ---


class TestSettingsStore:
    # Covers: AC-SET-001-01
    def test_upsert_and_get_single_setting(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        assert get_setting("interface", "locale", engine=engine) == "en"

    # Covers: AC-SET-001-01
    def test_get_missing_setting_returns_none(self):
        engine = _in_memory_engine()
        assert get_setting("interface", "locale", engine=engine) is None

    # Covers: AC-SET-001-01
    def test_upsert_overwrites_existing(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_setting("interface", "locale", "zh", engine=engine)
        assert get_setting("interface", "locale", engine=engine) == "zh"

    # Covers: AC-SET-001-02
    def test_get_namespace_returns_all_keys(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_setting("interface", "theme", "dark", engine=engine)
        upsert_setting("reading", "fontSize", "lg", engine=engine)
        ns = get_namespace("interface", engine=engine)
        assert ns == {"locale": "en", "theme": "dark"}

    # Covers: AC-SET-001-02
    def test_get_namespace_empty(self):
        engine = _in_memory_engine()
        assert get_namespace("interface", engine=engine) == {}

    # Covers: AC-SET-001-02
    def test_get_all_settings_grouped(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_setting("reading", "theme", "dark", engine=engine)
        result = get_all_settings(engine=engine)
        assert result == {
            "interface": {"locale": "en"},
            "reading": {"theme": "dark"},
        }

    # Covers: AC-SET-001-02
    def test_upsert_namespace_batch(self):
        engine = _in_memory_engine()
        upsert_namespace(
            "interface",
            {"locale": "en", "theme": "light", "fontSize": "md"},
            engine=engine,
        )
        ns = get_namespace("interface", engine=engine)
        assert ns == {"locale": "en", "theme": "light", "fontSize": "md"}

    # Covers: AC-SET-001-02
    def test_upsert_namespace_updates_existing(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_namespace("interface", {"locale": "zh", "theme": "dark"}, engine=engine)
        ns = get_namespace("interface", engine=engine)
        assert ns == {"locale": "zh", "theme": "dark"}

    # Covers: AC-SET-001-03
    def test_delete_namespace(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_setting("interface", "theme", "dark", engine=engine)
        upsert_setting("reading", "fontSize", "lg", engine=engine)
        count = delete_namespace("interface", engine=engine)
        assert count == 2
        assert get_namespace("interface", engine=engine) == {}
        assert get_namespace("reading", engine=engine) == {"fontSize": "lg"}

    # Covers: AC-SET-001-03
    def test_delete_empty_namespace(self):
        engine = _in_memory_engine()
        count = delete_namespace("nonexistent", engine=engine)
        assert count == 0

    # Covers: AC-SET-001-03
    def test_clear_all_settings(self):
        engine = _in_memory_engine()
        upsert_setting("interface", "locale", "en", engine=engine)
        upsert_setting("reading", "theme", "dark", engine=engine)
        upsert_setting("composer", "topic", "science", engine=engine)
        count = clear_all_settings(engine=engine)
        assert count == 3
        assert get_all_settings(engine=engine) == {}

    # Covers: AC-SET-001-03
    def test_clear_all_settings_empty(self):
        engine = _in_memory_engine()
        count = clear_all_settings(engine=engine)
        assert count == 0


# --- API endpoint tests ---


def _patch_engine(monkeypatch):
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)
    init_settings_table(engine)
    return engine


# Covers: AC-SET-001-04
def test_api_get_all_settings_empty(monkeypatch):
    _patch_engine(monkeypatch)
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert response.json() == {}


# Covers: AC-SET-001-04
def test_api_put_and_get_single_setting(monkeypatch):
    _patch_engine(monkeypatch)
    response = client.put(
        "/api/settings/interface/locale",
        json={"value": "en"},
    )
    assert response.status_code == 200

    response = client.get("/api/settings/interface")
    assert response.status_code == 200
    assert response.json() == {"locale": "en"}


# Covers: AC-SET-001-04
def test_api_put_namespace_batch(monkeypatch):
    _patch_engine(monkeypatch)
    response = client.put(
        "/api/settings/interface",
        json={"locale": "zh", "theme": "dark"},
    )
    assert response.status_code == 200

    response = client.get("/api/settings/interface")
    assert response.json() == {"locale": "zh", "theme": "dark"}


# Covers: AC-SET-001-04
def test_api_get_all_settings_grouped(monkeypatch):
    _patch_engine(monkeypatch)
    client.put("/api/settings/interface/locale", json={"value": "en"})
    client.put("/api/settings/reading/theme", json={"value": "dark"})

    response = client.get("/api/settings")
    assert response.json() == {
        "interface": {"locale": "en"},
        "reading": {"theme": "dark"},
    }


# Covers: AC-SET-001-04
def test_api_put_setting_rejects_empty_value(monkeypatch):
    _patch_engine(monkeypatch)
    response = client.put(
        "/api/settings/interface/locale",
        json={"value": ""},
    )
    assert response.status_code == 422


# Covers: AC-SET-001-04
def test_api_delete_all_settings(monkeypatch):
    _patch_engine(monkeypatch)
    client.put("/api/settings/interface/locale", json={"value": "en"})
    client.put("/api/settings/reading/theme", json={"value": "dark"})
    client.put("/api/settings/composer/topic", json={"value": "science"})

    response = client.delete("/api/settings")
    assert response.status_code == 200
    assert response.json()["deleted"] == 3

    response = client.get("/api/settings")
    assert response.json() == {}


# Covers: AC-SET-001-04
def test_api_delete_all_settings_empty(monkeypatch):
    _patch_engine(monkeypatch)
    response = client.delete("/api/settings")
    assert response.status_code == 200
    assert response.json()["deleted"] == 0
