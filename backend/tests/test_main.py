import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app
from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MIN,
    apply_feedback,
    clear_all_words,
    list_all_words,
    tick_cooldowns,
)

from conftest import _in_memory_engine

client = TestClient(app)


# Covers: AC-SHELL-001-01
def test_health_endpoint():
    """Health check endpoint returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "OpenVoca backend is running!",
    }


# Covers: AC-GEN-002-01, AC-TOK-001-01, AC-TOK-001-02
def test_reading_sentence_endpoint_returns_pos_tags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should return POS-tagged tokens with Markdown target markers."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion(prompt: str) -> str:
        assert "harbor" in prompt
        assert "lantern" in prompt
        assert "You MUST mark the target words" in prompt
        return "A *harbor* *lantern* flickered in the rain."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write one sentence with harbor, lantern.",
            "targetWords": ["harbor", "lantern"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sentence"] == "A *harbor* *lantern* flickered in the rain."

    tokens = data["tokens"]
    harbor_tok = next(t for t in tokens if t["text"] == "harbor")
    assert harbor_tok["isWord"] is True
    assert harbor_tok["isTarget"] is True
    assert harbor_tok["pos"] == "NOUN"

    lantern_tok = next(t for t in tokens if t["text"] == "lantern")
    assert lantern_tok["pos"] == "NOUN"

    flickered_tok = next(t for t in tokens if t["text"] == "flickered")
    assert flickered_tok["isWord"] is True
    assert flickered_tok["pos"] == "VERB"

    dot_tok = next(t for t in tokens if t["text"] == ".")
    assert dot_tok["pos"] is None


# Covers: AC-LOOP-004-01
def test_reading_sentence_endpoint_returns_riddle_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Riddle mode should return clue, question, and answer payload fields."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion(prompt: str) -> str:
        assert "All output must be English" in prompt
        assert "single asterisks" in prompt
        return (
            '{"clue":"coastal signal",'
            '"question":"I guide ships through dark water.",'
            '"answer":"a *harbor* *lantern*"}'
        )

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "mode": "riddle",
            "prompt": 'Return only valid JSON with exactly these fields: {"clue": string, "question": string, "answer": string}. All output must be English.',
            "targetWords": ["harbor", "lantern"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "riddle"
    assert data["riddle"]["clue"] == "coastal signal"
    assert data["riddle"]["question"] == "I guide ships through dark water."
    assert data["riddle"]["answer"] == "a *harbor* *lantern*"

    clue_tokens = data["riddle"]["clueTokens"]
    question_tokens = data["riddle"]["questionTokens"]
    answer_tokens = data["riddle"]["answerTokens"]
    assert any(t["text"] == "coastal" and t["isWord"] for t in clue_tokens)
    assert any(t["text"] == "ships" and t["isWord"] for t in question_tokens)
    assert any(t["text"] == "harbor" and t["isTarget"] is True for t in answer_tokens)
    assert any(t["text"] == "lantern" and t["isTarget"] is True for t in answer_tokens)


# Covers: AC-LOOP-004-01, AC-LOOP-005-01
def test_stream_reading_sentence_endpoint_accepts_fenced_riddle_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Streaming riddle mode should accept common fenced JSON model output."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion_stream(prompt: str):  # noqa: ANN202
        assert "All output must be English" in prompt
        for chunk in [
            "```json\n",
            '{"clue":"coastal signal",',
            '"question":"I guide ships through dark water.",',
            '"answer":"a *harbor* *lantern*"}',
            "\n```",
        ]:
            yield chunk

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion_stream",
        fake_generate_completion_stream,
    )

    response = client.post(
        "/api/reading-sentence/next/stream",
        json={
            "mode": "riddle",
            "prompt": 'Return only valid JSON with exactly these fields: {"clue": string, "question": string, "answer": string}. All output must be English.',
            "targetWords": ["harbor", "lantern"],
        },
    )

    assert response.status_code == 200
    assert "event: error" not in response.text
    assert "event: complete" in response.text
    lines = response.text.splitlines()
    complete_index = lines.index("event: complete")
    complete_line = lines[complete_index + 1]
    data = json.loads(complete_line.removeprefix("data: "))
    assert data["mode"] == "riddle"
    assert data["riddle"]["clue"] == "coastal signal"
    assert data["riddle"]["question"] == "I guide ships through dark water."
    assert data["riddle"]["answer"] == "a *harbor* *lantern*"


# Covers: AC-LOOP-004-03
def test_reading_sentence_endpoint_rejects_invalid_riddle_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Riddle mode should fail clearly when the model does not return JSON."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion(prompt: str) -> str:  # noqa: ARG001
        return "The answer is probably a lantern."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "mode": "riddle",
            "prompt": "Return strict JSON with clue, question, and answer.",
            "targetWords": ["lantern"],
        },
    )

    assert response.status_code == 502


# Covers: AC-LOOP-002-01
def test_target_words_endpoint_picks_from_vocabulary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/target-words should tick cooldowns and pick words from the vocabulary."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["meadow"], ["meadow"], "A meadow bloomed.", engine=engine)
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    response = client.get("/api/target-words?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert "meadow" in data["words"]


# Covers: AC-SRS-006-01
def test_delete_vocabulary_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/vocabulary should clear all records and return the count."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["alpha", "beta"], [], "test", engine=engine)
    assert len(list_all_words(engine)) == 2

    response = client.delete("/api/vocabulary")
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    assert len(list_all_words(engine)) == 0


# Covers: AC-GEN-002-03, AC-LOOP-005-02
def test_reading_sentence_returns_502_on_ollama_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The API should return 502 when the LLM is unreachable."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def failing_generate(prompt: str) -> str:
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        failing_generate,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write a sentence with test.",
            "targetWords": ["test"],
        },
    )

    assert response.status_code == 502


# Covers: AC-LOOP-003-02, AC-SRS-001-01
def test_feedback_via_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/feedback endpoint should accept lemma strings."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.post(
        "/api/feedback",
        json={
            "targetWords": ["harbor", "glow"],
            "markedWords": ["harbor"],
            "sentence": "The harbor glowed at dusk.",
        },
    )

    assert response.status_code == 200
    records = {r.lemma: r.level for r in list_all_words(engine)}
    assert records["harbor"] == LEVEL_MIN  # miss
    assert records["glow"] == LEVEL_MIN + 1  # hit


# Covers: AC-SRS-009-01
def test_vocabulary_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/vocabulary endpoint should include level in the response."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["lantern"], [], "The lantern glowed.", engine=engine)

    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    word_data = data["words"][0]
    assert word_data["lemma"] == "lantern"
    assert "pos" not in word_data
    assert word_data["level"] == LEVEL_MIN + 1
    assert word_data["cooldown"] == LEVEL_BASE ** (LEVEL_MIN + 1)


# Covers: AC-GEN-002-02
def test_next_endpoint_ticks_cooldowns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/reading-sentence/next should tick cooldowns each generation cycle."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["harbor"], ["harbor"], "The harbor.", engine=engine)
    for _ in range(LEVEL_BASE**LEVEL_MIN - 1):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1

    async def fake_generate_completion(prompt: str) -> str:
        return "The *harbor* was calm."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write one sentence with harbor.",
            "targetWords": ["harbor"],
        },
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 0


# Covers: AC-LOOP-002-02, AC-GEN-002-02
def test_target_words_endpoint_does_not_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/target-words should NOT tick cooldowns (to avoid burning on refresh)."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["harbor"], ["harbor"], "The harbor.", engine=engine)
    for _ in range(LEVEL_BASE**LEVEL_MIN - 1):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1

    client.get("/api/target-words?limit=3")
    client.get("/api/target-words?limit=3")

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1


# ---------------------------------------------------------------------------
# Composer hints API tests
# ---------------------------------------------------------------------------


# Covers: AC-GEN-001-04, AC-GEN-002-01
def test_next_endpoint_accepts_full_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should accept a fully assembled prompt from the frontend."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    captured_prompts: list[str] = []

    async def fake_generate_completion(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "The sunset was calm."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write a sentence: sunset.\n[Scenario] You are a deadpan news anchor.\n[Difficulty] Use simple vocabulary.\n[Length] The sentence MUST be approximately 40 words long.",
            "targetWords": ["sunset"],
        },
    )

    assert response.status_code == 200
    prompt = captured_prompts[0]
    assert "news anchor" in prompt.lower()
    assert "40" in prompt
    assert "sunset" in prompt


# Covers: AC-GEN-002-01
def test_next_endpoint_works_with_minimal_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should work with just a prompt and target words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion(prompt: str) -> str:
        return "Hello world."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write a sentence with hello.",
            "targetWords": ["hello"],
        },
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Vocabulary CSV export
# ---------------------------------------------------------------------------


# Covers: AC-SRS-008-01
def test_export_vocabulary_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary/export should return a CSV with the correct headers and data."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        ["lantern", "glow"], ["lantern"], "The lantern glowed.", engine=engine
    )

    response = client.get("/api/vocabulary/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "openvoca-vocabulary.csv" in response.headers["content-disposition"]

    lines = response.text.strip().splitlines()
    assert (
        lines[0] == "lemma,level,cooldown,first_seen,last_seen,last_context,seen_count"
    )
    assert len(lines) == 3  # header + 2 words


# Covers: AC-SRS-008-01
def test_export_vocabulary_csv_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary/export should return a CSV with only headers when vocabulary is empty."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.get("/api/vocabulary/export")
    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines == [
        "lemma,level,cooldown,first_seen,last_seen,last_context,seen_count"
    ]


# Covers: AC-SRS-006-02
def test_patch_vocabulary_word(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH /api/vocabulary/{lemma} should update level and cooldown."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["alpha"], ["alpha"], "test", engine=engine)

    response = client.patch(
        "/api/vocabulary/alpha",
        json={"level": 3, "cooldown": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == 3
    assert data["cooldown"] == 0


# Covers: AC-SRS-006-03
def test_patch_vocabulary_word_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH should return 404 for unknown words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.patch(
        "/api/vocabulary/missing",
        json={"level": 2},
    )
    assert response.status_code == 404


# Covers: AC-SRS-006-04
def test_delete_vocabulary_word(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/vocabulary/{lemma} should delete a single word."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["alpha", "beta"], ["alpha"], "test", engine=engine)
    assert len(list_all_words(engine)) == 2

    response = client.delete("/api/vocabulary/alpha")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    assert len(list_all_words(engine)) == 1


# Covers: AC-SRS-006-04
def test_delete_vocabulary_word_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE should return 404 for unknown words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.delete("/api/vocabulary/missing")
    assert response.status_code == 404


# Covers: AC-SRS-006-03
def test_delete_then_patch_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH after DELETE on same word (stale tab) should return 404."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["alpha"], ["alpha"], "test", engine=engine)

    response = client.delete("/api/vocabulary/alpha")
    assert response.status_code == 200

    response = client.patch(
        "/api/vocabulary/alpha",
        json={"level": 3},
    )
    assert response.status_code == 404


# Covers: AC-SRS-009-02
def test_vocabulary_sort_due(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=due returns words by cooldown ASC, level ASC."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["alpha", "beta"], ["alpha"], "Alpha and beta.", engine=engine)
    # alpha: marked (miss) -> level=1, cooldown=2
    # beta: unmarked target (hit) -> level=2, cooldown=4

    response = client.get("/api/vocabulary?sort=due")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    assert lemmas == ["alpha", "beta"]


# Covers: AC-SRS-009-02
def test_vocabulary_sort_familiarity(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=familiarity returns words by level ASC, cooldown ASC."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["easy", "hard"], ["hard"], "Easy and hard.", engine=engine)
    # hard: marked (miss) -> level=1, cooldown=2
    # easy: unmarked target (hit) -> level=2, cooldown=4

    response = client.get("/api/vocabulary?sort=familiarity")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    assert lemmas == ["hard", "easy"]


# Covers: AC-SRS-009-02
def test_vocabulary_sort_recent(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=recent returns words by last_seen DESC."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["first"], [], "First sentence.", engine=engine)
    time.sleep(0.05)
    apply_feedback(["second"], [], "Second sentence.", engine=engine)

    response = client.get("/api/vocabulary?sort=recent")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    assert lemmas == ["second", "first"]


# Covers: AC-SRS-009-02
def test_vocabulary_sort_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=invalid returns 422."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.get("/api/vocabulary?sort=invalid")
    assert response.status_code == 422


# Covers: AC-SRS-009-01
def test_vocabulary_includes_last_seen(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary response includes lastSeen field."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["lantern"], [], "The lantern glowed.", engine=engine)

    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    word_data = response.json()["words"][0]
    assert "lastSeen" in word_data
    assert word_data["lastSeen"] is not None


# ---------------------------------------------------------------------------
# Vocabulary import endpoint
# ---------------------------------------------------------------------------


# Covers: AC-SRS-008-02
def test_import_vocabulary_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/vocabulary/import should accept a CSV and return import summary."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,level,cooldown\nharbor,3,3\nlantern,2,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 3
    assert records["lantern"].level == 2


# Covers: AC-SRS-008-03
def test_import_vocabulary_endpoint_upserts_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing a word that already exists should overwrite it."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)

    csv_content = "lemma,level,cooldown\nharbor,5,16\n"
    response = client.post(
        "/api/vocabulary/import",
        data={"mode": "overwrite"},
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 5
    assert records["harbor"].cooldown == 16


# Covers: AC-SRS-008-04
def test_import_vocabulary_endpoint_skips_invalid_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid CSV rows should be skipped and reported."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,level,cooldown\ngood,2,0\nbad,notanint,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1


# Covers: AC-SRS-008-04
def test_import_vocabulary_endpoint_file_too_large(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Files larger than 1 MB should be rejected with 413."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    large_content = b"lemma,level,cooldown\n" + b"x," * 600_000
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("big.csv", large_content, "text/csv")},
    )

    assert response.status_code == 413


# Covers: AC-SRS-008-04
def test_import_vocabulary_endpoint_non_utf8(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-UTF-8 encoded files should be rejected with 422."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    bad_bytes = b"\xff\xfe" + "harbor,4,0\n".encode("utf-16-le")
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("bad.csv", bad_bytes, "text/csv")},
    )

    assert response.status_code == 422


# Covers: AC-SRS-008-06
def test_export_import_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exported CSV should be importable without any data loss."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        ["harbor", "lantern"], ["harbor"], "The harbor lantern.", engine=engine
    )
    apply_feedback(["glow"], [], "It glows.", engine=engine)
    original = {r.lemma: r for r in list_all_words(engine)}
    assert len(original) == 3

    export_resp = client.get("/api/vocabulary/export")
    assert export_resp.status_code == 200
    csv_bytes = export_resp.content

    clear_all_words(engine)
    assert list_all_words(engine) == []

    import_resp = client.post(
        "/api/vocabulary/import",
        files={"file": ("roundtrip.csv", csv_bytes, "text/csv")},
    )
    assert import_resp.status_code == 200
    data = import_resp.json()
    assert data["imported"] == 3
    assert data["skipped"] == 0
    assert data["errors"] == []

    restored = {r.lemma: r for r in list_all_words(engine)}
    assert len(restored) == 3
    for key, orig in original.items():
        assert key in restored, f"Missing record after roundtrip: {key}"
        rest = restored[key]
        assert rest.level == orig.level, f"{key} level mismatch"
        assert rest.cooldown == orig.cooldown, f"{key} cooldown mismatch"
        assert rest.last_context == orig.last_context, f"{key} last_context mismatch"
        assert rest.seen_count == orig.seen_count, f"{key} seen_count mismatch"
        assert rest.last_seen.isoformat() == orig.last_seen.isoformat(), (
            f"{key} last_seen mismatch"
        )
        assert rest.first_seen.isoformat() == orig.first_seen.isoformat(), (
            f"{key} first_seen mismatch"
        )


# Covers: AC-SRS-008-03
def test_import_vocabulary_endpoint_skip_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default (skip) mode should preserve existing records and only add new ones."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    original_level = list_all_words(engine)[0].level

    csv_content = "lemma,level,cooldown\nharbor,5,16\nlantern,2,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level
    assert records["lantern"].level == 2


# Covers: AC-SRS-008-02
def test_import_vocabulary_endpoint_minimal_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A CSV with only lemma column should import successfully."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma\nharbor\nglow\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


# Covers: AC-SRS-008-05
def test_import_vocabulary_legacy_pos_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy CSV files with a 'pos' column should still import successfully."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,pos,level,cooldown\nharbor,NOUN,3,3\nlantern,NOUN,2,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


# Covers: AC-SRS-008-05
def test_import_vocabulary_endpoint_bom_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A CSV with a UTF-8 BOM (from Excel) should be imported correctly."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "\ufefflemma,level,cooldown\nharbor,3,3\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 0
