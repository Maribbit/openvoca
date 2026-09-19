"""Tests for provider configuration and the API-key lifecycle.

These cover the settings-shell contract for key storage: the key is independent
of endpoint/model, has an explicit set/clear lifecycle, and never appears on a
generic settings read path.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import src.main as main_module
from src.main import app
from src.services.settings_store import (
    get_namespace,
    init_settings_table,
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


def _reset_provider(monkeypatch: pytest.MonkeyPatch):
    """Point the stores at a fresh in-memory DB and rebuild the LLM client."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)
    init_settings_table(engine)
    monkeypatch.setattr(main_module, "llm", main_module._load_provider())
    return engine


# --- Read-model: key state is expressed without exposing the key ---


# Covers: AC-SET-005-03
def test_get_provider_reports_key_state_without_exposing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The read model carries a boolean plus an irreversible hint, not the key."""
    _reset_provider(monkeypatch)
    secret = "sk-live-abcdefghijklmnop"
    client.put("/api/provider/key", json={"apiKey": secret})

    response = client.get("/api/provider")

    assert response.status_code == 200
    assert secret not in response.text
    body = response.json()
    assert body["apiKeySet"] is True
    assert body["apiKeyHint"]


# Covers: AC-SET-005-03
def test_get_provider_reports_unset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no stored key the read model reports it as unset and gives no hint."""
    _reset_provider(monkeypatch)

    body = client.get("/api/provider").json()

    assert body["apiKeySet"] is False
    assert body["apiKeyHint"] == ""


# --- Independence: editing endpoint/model must not disturb the key ---


# Covers: AC-SET-005-01
def test_changing_model_and_endpoint_preserves_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Editing endpoint/model leaves the stored key untouched."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-keep-me-123456"})

    response = client.put(
        "/api/provider",
        json={"endpoint": "https://api.example.com", "model": "new-model"},
    )

    assert response.status_code == 200
    assert response.json()["apiKeySet"] is True
    assert get_namespace("provider")["apiKey"] == "sk-keep-me-123456"


# --- Endpoint normalization at the write boundary ---


# Covers: AC-GEN-003-08
def test_a_full_endpoint_url_is_stored_as_its_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider docs show the base URL and a curl example side by side.

    One field accepts either. Normalizing at the write boundary rather than
    inside the client is what keeps the database, the running client and the
    read model in agreement; normalizing in the client would leave the stored
    value differing from the reported one.
    """
    _reset_provider(monkeypatch)

    client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.deepseek.com/chat/completions",
            "model": "deepseek-chat",
        },
    )

    assert get_namespace("provider")["endpoint"] == "https://api.deepseek.com"
    assert client.get("/api/provider").json()["endpoint"] == "https://api.deepseek.com"


# Covers: AC-GEN-003-08
@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("https://api.openai.com/v1", "https://api.openai.com/v1"),
        ("https://api.deepseek.com", "https://api.deepseek.com"),
        (
            "https://open.bigmodel.cn/api/paas/v4",
            "https://open.bigmodel.cn/api/paas/v4",
        ),
        ("https://api.deepseek.com/", "https://api.deepseek.com"),
    ],
)
def test_version_prefixes_are_preserved_verbatim(
    monkeypatch: pytest.MonkeyPatch, given: str, expected: str
) -> None:
    """Normalization removes only the endpoint path; the version segment is the
    provider's and must survive unchanged, whatever it is called."""
    _reset_provider(monkeypatch)

    client.put("/api/provider", json={"endpoint": given, "model": "m"})

    assert get_namespace("provider")["endpoint"] == expected


# Covers: AC-SET-005-02
def test_update_endpoint_keeps_runtime_and_persisted_in_sync(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: an endpoint edit used to wipe the in-memory key while the
    database kept it, so the key only appeared to 'come back' after a restart."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-sync-check-abcdef"})

    client.put(
        "/api/provider",
        json={"endpoint": "https://api.example.com", "model": "m"},
    )

    persisted = get_namespace("provider")["apiKey"]
    runtime = main_module.llm.api_key
    assert runtime == persisted == "sk-sync-check-abcdef"


# Covers: AC-SET-005-02
def test_reload_provider_matches_persisted_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runtime client is derived from persisted settings, never the reverse."""
    _reset_provider(monkeypatch)
    client.put(
        "/api/provider",
        json={"endpoint": "https://api.example.com", "model": "m"},
    )
    client.put("/api/provider/key", json={"apiKey": "sk-derived-123456"})

    reloaded = main_module._load_provider()

    assert reloaded.base_url == "https://api.example.com"
    assert reloaded.model == "m"
    assert reloaded.api_key == "sk-derived-123456"


# --- Lifecycle: empty never carries meaning ---


# Covers: AC-SET-005-04
def test_set_key_rejects_empty_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty value is rejected outright rather than treated as 'no change'."""
    _reset_provider(monkeypatch)

    response = client.put("/api/provider/key", json={"apiKey": ""})

    assert response.status_code == 422


# Covers: AC-SET-005-04
def test_empty_key_write_does_not_clear_existing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rejected empty write must leave the stored key intact."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-still-here-1234"})

    client.put("/api/provider/key", json={"apiKey": ""})

    assert get_namespace("provider")["apiKey"] == "sk-still-here-1234"
    assert client.get("/api/provider").json()["apiKeySet"] is True


# Covers: AC-SET-005-05
def test_clear_key_removes_runtime_and_persisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clearing is a distinct operation and removes the key everywhere."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-to-be-removed-9999"})

    response = client.delete("/api/provider/key")

    assert response.status_code == 200
    assert response.json()["apiKeySet"] is False
    assert "apiKey" not in get_namespace("provider")
    assert main_module.llm.api_key == ""


# Covers: AC-SET-005-05
def test_clear_key_then_read_reports_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """After clearing, the read model reports an unset key."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-temp-123456"})
    client.delete("/api/provider/key")

    body = client.get("/api/provider").json()

    assert body["apiKeySet"] is False
    assert body["apiKeyHint"] == ""


# --- Provider config has exactly one write path ---


# Covers: AC-SET-005-06
def test_generic_settings_namespace_write_rejects_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider config cannot be injected through the generic settings API."""
    _reset_provider(monkeypatch)

    response = client.put(
        "/api/settings/provider",
        json={"apiKey": "sk-injected-secret"},
    )

    assert response.status_code == 403
    assert get_namespace("provider") == {}


# Covers: AC-SET-005-06
def test_generic_settings_key_write_rejects_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The single-key settings route is blocked for the provider namespace too."""
    _reset_provider(monkeypatch)

    response = client.put(
        "/api/settings/provider/apiKey",
        json={"value": "sk-injected-secret"},
    )

    assert response.status_code == 403
    assert get_namespace("provider") == {}


# Covers: AC-SET-005-06
def test_clear_all_settings_keeps_provider_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resetting preferences must not silently discard the model configuration."""
    _reset_provider(monkeypatch)
    client.put(
        "/api/provider",
        json={"endpoint": "https://api.example.com", "model": "m"},
    )
    client.put("/api/provider/key", json={"apiKey": "sk-survives-123456"})
    client.put("/api/settings/interface/locale", json={"value": "en"})

    response = client.delete("/api/settings")

    assert response.status_code == 200
    assert response.json()["deleted"] == 1
    assert get_namespace("provider")["apiKey"] == "sk-survives-123456"
    assert get_namespace("provider")["endpoint"] == "https://api.example.com"


# --- Generic settings reads must not carry the key ---


# Covers: AC-SET-004-01
def test_settings_read_excludes_provider_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The generic settings read omits the key rather than masking it."""
    _reset_provider(monkeypatch)
    upsert_setting("provider", "apiKey", "sk-must-not-leak-1234")
    upsert_setting("provider", "endpoint", "https://api.example.com")

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert "sk-must-not-leak-1234" not in response.text
    assert "apiKey" not in response.json().get("provider", {})
    assert response.json()["provider"]["endpoint"] == "https://api.example.com"


# Covers: AC-SET-004-01
def test_settings_namespace_read_excludes_provider_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reading the provider namespace directly also omits the key."""
    _reset_provider(monkeypatch)
    upsert_setting("provider", "apiKey", "sk-namespace-leak-1234")

    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    assert "sk-namespace-leak-1234" not in response.text
    assert "apiKey" not in response.json()


# --- Custom request headers ---


# Covers: AC-SET-005-08
def test_provider_read_returns_custom_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Headers must be returned in full so the UI can edit them item by item."""
    _reset_provider(monkeypatch)
    headers = {"x-opencode-session": "session-abc", "X-Trace": "on"}

    response = client.put(
        "/api/provider",
        json={
            "endpoint": "https://opencode.ai/zen/go",
            "model": "deepseek-v4-flash",
            "headers": headers,
        },
    )

    assert response.status_code == 200
    assert response.json()["headers"] == headers


# Covers: AC-SET-005-10
def test_provider_update_replaces_headers_wholesale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Saving a new header set replaces the previous one entirely."""
    _reset_provider(monkeypatch)
    client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.example.com",
            "model": "m",
            "headers": {"X-Old": "1"},
        },
    )

    response = client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.example.com",
            "model": "m",
            "headers": {"X-New": "2"},
        },
    )

    assert response.json()["headers"] == {"X-New": "2"}


# Covers: AC-SET-005-10
def test_provider_update_with_empty_headers_clears_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty set unambiguously means 'no custom headers'."""
    _reset_provider(monkeypatch)
    client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.example.com",
            "model": "m",
            "headers": {"X-One": "1"},
        },
    )

    response = client.put(
        "/api/provider",
        json={"endpoint": "https://api.example.com", "model": "m", "headers": {}},
    )

    assert response.json()["headers"] == {}
    assert get_namespace("provider").get("headers", "{}") in ("", "{}")


# Covers: AC-SET-005-01
def test_updating_headers_does_not_disturb_the_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Header edits must leave the stored key untouched, like endpoint/model."""
    _reset_provider(monkeypatch)
    client.put("/api/provider/key", json={"apiKey": "sk-untouched-123456"})

    response = client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.example.com",
            "model": "m",
            "headers": {"X-A": "1"},
        },
    )

    assert response.json()["apiKeySet"] is True
    assert get_namespace("provider")["apiKey"] == "sk-untouched-123456"


# Covers: AC-GEN-004-03
@pytest.mark.parametrize(
    "bad_headers",
    [
        {"bad name": "1"},
        {"bad:name": "1"},
        {"X-Test": "line\nbreak"},
        {"X-Test": "carriage\rreturn"},
        {"": "empty name"},
    ],
)
def test_provider_rejects_invalid_headers(
    monkeypatch: pytest.MonkeyPatch, bad_headers: dict[str, str]
) -> None:
    """Invalid names or values must be rejected before they reach storage."""
    _reset_provider(monkeypatch)

    response = client.put(
        "/api/provider",
        json={
            "endpoint": "https://api.example.com",
            "model": "m",
            "headers": bad_headers,
        },
    )

    assert response.status_code == 422
    assert "headers" not in get_namespace("provider")


# Covers: AC-SET-005-09
def test_settings_read_excludes_custom_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Headers may carry session credentials, so generic reads omit them."""
    _reset_provider(monkeypatch)
    upsert_setting(
        "provider", "headers", '{"x-opencode-session": "secret-session-value"}'
    )

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert "secret-session-value" not in response.text
    assert "headers" not in response.json().get("provider", {})


# Covers: AC-SET-005-08
def test_headers_survive_reload_via_persisted_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The rebuilt client must carry the persisted headers."""
    _reset_provider(monkeypatch)

    client.put(
        "/api/provider",
        json={
            "endpoint": "https://opencode.ai/zen/go",
            "model": "deepseek-v4-flash",
            "headers": {"x-opencode-session": "persisted-session"},
        },
    )

    reloaded = main_module._load_provider()

    assert reloaded.extra_headers == {"x-opencode-session": "persisted-session"}
