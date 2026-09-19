from __future__ import annotations

import asyncio
import json
import csv
import io
import os
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.integrations.openai_compat import OpenAICompatibleClient
from src.integrations.provider import LLMProvider
from src.services.prompt_builder import (
    build_sentence_generation_prompt,
)
from src.services.schema_guard import describe_gaps, find_schema_gaps
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    draft_feedback,
    LevelDelta,
    clear_all_words,
    database_path,
    delete_word_record,
    get_engine,
    import_vocabulary,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
    update_word_record,
)
from src.services.settings_store import (
    PROTECTED_NAMESPACES,
    clear_all_settings,
    delete_setting,
    get_all_settings,
    get_namespace,
    init_settings_table,
    upsert_namespace,
    upsert_setting,
)
from src.services.dictionary import lookup as dict_lookup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolved from this file, never from the working directory. The working
# directory is chosen by whatever starts the process, and under a symlink-based
# deployment the path a symlink points at changes between revisions; neither may
# decide whether the interface can be found.
_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"


def frontend_dist() -> Path:
    """Directory the interface is served from."""
    return _frontend_dist


def running_revision() -> str:
    """The revision this process was started from.

    Supplied by the assembly layer rather than derived from the file layout. A
    symlink switch changes the path a file resolves through, so the application
    cannot infer its own revision without also knowing how it was deployed --
    and knowing that is exactly what the distribution contract forbids.
    """
    return os.environ.get("OPENVOCA_REVISION", "").strip()


# ---------------------------------------------------------------------------
# Update check
# ---------------------------------------------------------------------------

_GITHUB_REPO = "Maribbit/openvoca"

_update_info: dict = {
    "checked": False,
    "hasUpdate": False,
    "currentVersion": "",
    "latestVersion": "",
    "url": "",
}


def _version_gt(a: str, b: str) -> bool:
    """Return True if version string a is strictly greater than b."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except ValueError:
        return False


async def _check_for_updates() -> None:
    """Background startup task: query GitHub Releases for a newer version."""
    current = os.environ.get("OPENVOCA_VERSION", "").strip()
    _update_info["currentVersion"] = current
    if not current:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest",
                headers={"User-Agent": f"OpenVoca/{current}"},
            )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            url = data.get("html_url", "")
            _update_info["checked"] = True
            _update_info["latestVersion"] = latest
            _update_info["url"] = url
            _update_info["hasUpdate"] = _version_gt(latest, current)
    except Exception:  # noqa: BLE001
        pass  # network failure is expected in offline / air-gapped environments


def report_startup_paths() -> None:
    """Print the paths this process resolved, before it begins serving.

    A wrong path is the hardest deployment failure to diagnose: the API answers
    normally, every probe passes, and only the interface is blank.
    """
    db_path = database_path()
    print(f"Data directory : {db_path.parent}", flush=True)
    print(f"Database       : {db_path}", flush=True)
    if _frontend_dist.exists():
        print(f"Frontend       : {_frontend_dist}", flush=True)
    else:
        print(
            f"WARNING: no frontend build at {_frontend_dist}. "
            "The API will answer but the interface will not load.",
            file=sys.stderr,
            flush=True,
        )


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ARG001
    """Verify the environment before serving; release the LLM client after."""
    report_startup_paths()

    gaps = find_schema_gaps(get_engine())
    if gaps:
        print(describe_gaps(gaps), file=sys.stderr, flush=True)
        # Raising aborts startup. The process exits without ever accepting a
        # request against a schema it cannot query.
        raise RuntimeError(
            f"refusing to start: {len(gaps)} table(s) do not match the models"
        )

    asyncio.create_task(_check_for_updates())
    yield
    if isinstance(llm, OpenAICompatibleClient):
        await llm.aclose()


app = FastAPI(title="OpenVoca API", lifespan=lifespan)
init_settings_table()

DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_MODEL = ""
PROVIDER_NAMESPACE = "provider"

# Header names must be HTTP tokens; values must not span lines, which would
# allow injecting additional headers.
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_MAX_HEADER_COUNT = 20
_MAX_HEADER_LENGTH = 1000


def _validate_headers(headers: dict[str, str]) -> dict[str, str]:
    """Reject header names or values that cannot be sent safely."""
    if len(headers) > _MAX_HEADER_COUNT:
        raise ValueError(f"at most {_MAX_HEADER_COUNT} custom headers are allowed")
    for name, value in headers.items():
        if not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError(f"invalid header name: {name!r}")
        if any(c in value for c in "\r\n") or _has_control_chars(value):
            raise ValueError(f"invalid value for header {name!r}")
        if len(value) > _MAX_HEADER_LENGTH:
            raise ValueError(f"header {name!r} exceeds {_MAX_HEADER_LENGTH} characters")
    return headers


def _has_control_chars(value: str) -> bool:
    """Return True when the value holds control characters other than tab."""
    return any(ord(c) < 32 and c != "\t" for c in value)


def _encode_headers(headers: dict[str, str]) -> str:
    """Serialise headers for the single-string settings store."""
    return json.dumps(headers, ensure_ascii=False, sort_keys=True)


def _decode_headers(raw: str) -> dict[str, str]:
    """Read back persisted headers, tolerating absent or corrupt values."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {
        k: v for k, v in parsed.items() if isinstance(k, str) and isinstance(v, str)
    }


def _load_provider() -> OpenAICompatibleClient:
    """Build the LLM client from persisted settings.

    Persisted settings are the single source of truth; the client is a derived
    cache. Never read provider configuration from anywhere else.
    """
    cfg = get_namespace(PROVIDER_NAMESPACE)
    return OpenAICompatibleClient(
        base_url=cfg.get("endpoint", DEFAULT_ENDPOINT),
        model=cfg.get("model", DEFAULT_MODEL),
        api_key=cfg.get("apiKey", ""),
        extra_headers=_decode_headers(cfg.get("headers", "{}")),
    )


llm: LLMProvider = _load_provider()


class ReadingSentenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str = Field(min_length=1, max_length=5000)
    target_words: list[str] = Field(alias="targetWords")
    mode: Literal["sentence", "riddle"] = "sentence"


class ReadingSentenceResponse(BaseModel):
    sentence: str
    words: list[str]
    tokens: list["ReadingSentenceToken"]
    mode: Literal["sentence", "riddle"] = "sentence"
    riddle: ReadingRiddle | None = None


class ReadingRiddle(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    clue: str
    question: str
    answer: str
    clue_tokens: list["ReadingSentenceToken"] = Field(alias="clueTokens")
    question_tokens: list["ReadingSentenceToken"] = Field(alias="questionTokens")
    answer_tokens: list["ReadingSentenceToken"] = Field(alias="answerTokens")


class ReadingSentenceToken(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    is_word: bool = Field(alias="isWord")
    is_target: bool = Field(default=False, alias="isTarget")
    pos: str | None = None
    lemma: str | None = None
    trailing_space: bool = Field(default=True, alias="trailingSpace")


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[str] = Field(alias="targetWords")
    marked_words: list[str] = Field(alias="markedWords")
    sentence: str
    original_targets: list[str] = Field(default_factory=list, alias="originalTargets")


class WordRecordOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lemma: str
    level: int
    cooldown: int
    first_seen: str = Field(alias="firstSeen")
    last_seen: str = Field(alias="lastSeen")
    last_context: str | None = Field(default=None, alias="lastContext")
    seen_count: int = Field(default=0, alias="seenCount")


class VocabularyResponse(BaseModel):
    words: list[WordRecordOut]
    total: int


def _utc_iso(dt: datetime) -> str:
    """Ensure a datetime is serialized with UTC offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _response_tokens(text: str) -> list[ReadingSentenceToken]:
    tokens = tokenize_sentence(text)
    return [
        ReadingSentenceToken(
            text=t.text,
            is_word=t.is_word,
            is_target=t.is_target,
            pos=t.pos,
            lemma=t.lemma,
            trailing_space=t.trailing_space,
        )
        for t in tokens
    ]


def _strip_json_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    stripped = stripped[3:].lstrip()
    if stripped.lower().startswith("json"):
        stripped = stripped[4:].lstrip()
    if stripped.endswith("```"):
        stripped = stripped[:-3].rstrip()
    return stripped.strip()


def _normalize_completion(
    completion: str,
    mode: Literal["sentence", "riddle"],
) -> str:
    if mode == "riddle":
        return completion.strip()
    return " ".join(completion.split())


def _build_generation_prompt(
    prompt: str,
    target_words: list[str],
    mode: Literal["sentence", "riddle"],
) -> str:
    if mode == "sentence":
        return build_sentence_generation_prompt(prompt, target_words)

    final = prompt.strip()
    if not final:
        raise ValueError("A prompt is required to generate a riddle.")

    normalized = [word.strip() for word in target_words if word.strip()]
    if normalized:
        final += (
            "\nMark target words that appear in the question or answer with "
            "single asterisks, like *word*."
        )
    return final


def _parse_riddle_completion(completion: str) -> tuple[str, str, str]:
    try:
        payload = json.loads(_strip_json_code_fence(completion))
    except json.JSONDecodeError as exc:
        raise ValueError("Riddle response must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Riddle response must be a JSON object.")

    fields: dict[str, str] = {}
    for field_name in ("clue", "question", "answer"):
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Riddle response must include a non-empty {field_name}.")
        fields[field_name] = value.strip()

    return fields["clue"], fields["question"], fields["answer"]


def _build_reading_response(
    completion: str,
    words: list[str],
    mode: Literal["sentence", "riddle"],
) -> ReadingSentenceResponse:
    if mode == "riddle":
        clue, question, answer = _parse_riddle_completion(completion)
        clue_tokens = _response_tokens(clue)
        question_tokens = _response_tokens(question)
        answer_tokens = _response_tokens(answer)
        return ReadingSentenceResponse(
            sentence=f"{clue}\n{question}\n{answer}",
            words=words,
            tokens=[*clue_tokens, *question_tokens, *answer_tokens],
            mode="riddle",
            riddle=ReadingRiddle(
                clue=clue,
                question=question,
                answer=answer,
                clue_tokens=clue_tokens,
                question_tokens=question_tokens,
                answer_tokens=answer_tokens,
            ),
        )

    return ReadingSentenceResponse(
        sentence=completion,
        words=words,
        tokens=_response_tokens(completion),
    )


@app.get("/api/health")
def read_root() -> dict[str, str]:
    """Report availability and which revision is answering.

    The revision belongs here because "is it up?" and "is the new code live?"
    are the same question after a deployment, and answering them with two calls
    invites checking only the first.
    """
    return {
        "status": "ok",
        "message": "OpenVoca backend is running!",
        "revision": running_revision(),
    }


@app.get("/api/update-check")
def get_update_check() -> dict:
    """Return the result of the background update check (non-blocking)."""
    return _update_info


def _mask_api_key(key: str) -> str:
    """Return a masked version for safe display."""
    if len(key) <= 8:
        return "••••" if key else ""
    return key[:3] + "••••" + key[-4:]


class ProviderConfig(BaseModel):
    """Endpoint, model and optional custom request headers.

    The API key has its own lifecycle and is never part of this payload.
    """

    model_config = ConfigDict(populate_by_name=True)

    endpoint: str = Field(default=DEFAULT_ENDPOINT, max_length=500)
    model: str = Field(default=DEFAULT_MODEL, max_length=200)
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("headers")
    @classmethod
    def _check_headers(cls, value: dict[str, str]) -> dict[str, str]:
        try:
            return _validate_headers(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class ProviderKeyBody(BaseModel):
    """API key write payload.

    Empty values are rejected rather than interpreted as "clear", so the empty
    string never carries meaning on this path.
    """

    model_config = ConfigDict(populate_by_name=True)

    api_key: str = Field(alias="apiKey", min_length=1, max_length=500)


def _provider_state() -> dict[str, object]:
    """Describe the active provider without exposing the key itself.

    Custom headers are returned in full: unlike the key they must be editable,
    so the client needs their actual contents.
    """
    if isinstance(llm, OpenAICompatibleClient):
        return {
            "endpoint": llm.base_url,
            "model": llm.model,
            "headers": dict(llm.extra_headers),
            "apiKeySet": bool(llm.api_key),
            "apiKeyHint": _mask_api_key(llm.api_key),
        }
    return {
        "endpoint": DEFAULT_ENDPOINT,
        "model": DEFAULT_MODEL,
        "headers": {},
        "apiKeySet": False,
        "apiKeyHint": "",
    }


async def _reload_provider() -> None:
    """Rebuild the LLM client from persisted settings.

    Every provider write goes through here so the runtime configuration cannot
    drift from what is stored.
    """
    global llm
    if isinstance(llm, OpenAICompatibleClient):
        await llm.aclose()
    llm = _load_provider()


@app.get("/api/provider")
def get_provider() -> dict[str, object]:
    """Return endpoint/model plus whether a key is configured (never the key)."""
    return _provider_state()


@app.put("/api/provider")
async def set_provider(config: ProviderConfig) -> dict[str, object]:
    """Update endpoint, model and custom headers, leaving the API key untouched."""
    upsert_namespace(
        PROVIDER_NAMESPACE,
        {
            "endpoint": config.endpoint,
            "model": config.model,
            "headers": _encode_headers(config.headers),
        },
    )
    await _reload_provider()
    return _provider_state()


@app.put("/api/provider/key")
async def set_provider_key(body: ProviderKeyBody) -> dict[str, object]:
    """Store the API key. An empty value is rejected by validation."""
    upsert_setting(PROVIDER_NAMESPACE, "apiKey", body.api_key)
    await _reload_provider()
    return _provider_state()


@app.delete("/api/provider/key")
async def clear_provider_key() -> dict[str, object]:
    """Remove the stored API key. This is the only way to unset it."""
    delete_setting(PROVIDER_NAMESPACE, "apiKey")
    await _reload_provider()
    return _provider_state()


@app.post("/api/provider/test")
async def test_provider() -> dict[str, str | bool]:
    """Send a minimal request to verify the current LLM connection."""
    try:
        result = await llm.generate_completion("Say 'ok' and nothing else.")
        return {"ok": True, "message": result[:200]}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "message": str(exc)[:300]}


async def _generate_reading_response(
    prompt: str, words: list[str], mode: Literal["sentence", "riddle"] = "sentence"
) -> ReadingSentenceResponse:
    """Shared logic: finalize prompt, call LLM, tokenize, return response."""
    try:
        final_prompt = _build_generation_prompt(prompt, words, mode)
        completion = await llm.generate_completion(final_prompt)
        return _build_reading_response(completion, words, mode)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a sentence. Check your model configuration.",
        ) from exc


@app.get("/api/target-words")
def get_target_words(limit: int = 3) -> dict[str, list[str]]:
    """Pick target words that are currently available (cooldown == 0).

    Does NOT tick cooldowns — ticking happens in /api/reading-sentence/next
    to avoid burning through cooldowns on repeated page loads.
    """
    words = pick_target_words(limit=limit)
    return {"words": words}


@app.post("/api/reading-sentence/next", response_model=ReadingSentenceResponse)
async def get_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> ReadingSentenceResponse:
    """Generate a sentence using the target words chosen by the user.

    Ticks cooldowns so that cooling words advance toward availability
    for the next generation cycle.
    """
    tick_cooldowns()
    return await _generate_reading_response(
        request.prompt, request.target_words, request.mode
    )


@app.post("/api/reading-sentence/next/stream")
async def stream_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> StreamingResponse:
    """Generate a sentence with SSE progress events.

    Events:
    - ``progress``: ``{"wordCount": N}`` — running word count
    - ``complete``: full ``ReadingSentenceResponse`` JSON
    - ``error``: ``{"detail": "..."}``
    """
    tick_cooldowns()
    final_prompt = _build_generation_prompt(
        request.prompt, request.target_words, request.mode
    )

    async def event_stream():  # noqa: ANN202
        accumulated = ""
        try:
            async for chunk in llm.generate_completion_stream(final_prompt):
                accumulated += chunk
                word_count = len(accumulated.split())
                yield f"event: progress\ndata: {json.dumps({'wordCount': word_count})}\n\n"
        except (httpx.HTTPError, ValueError) as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)[:300]})}\n\n"
            return
        except Exception as exc:  # noqa: BLE001
            # A dying generator would otherwise end the response with no
            # terminal event, leaving the client waiting indefinitely.
            yield f"event: error\ndata: {json.dumps({'detail': f'Generation failed: {exc}'[:300]})}\n\n"
            return

        completion = _normalize_completion(accumulated, request.mode)
        if not completion:
            yield f"event: error\ndata: {json.dumps({'detail': 'Empty response from model.'})}\n\n"
            return

        try:
            result = _build_reading_response(
                completion, request.target_words, request.mode
            )
        except ValueError as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)[:300]})}\n\n"
            return
        yield f"event: complete\ndata: {result.model_dump_json(by_alias=True)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/feedback/draft", response_model=list[LevelDelta])
def submit_feedback_draft(request: FeedbackRequest) -> list[LevelDelta]:
    """Calculate how vocabulary levels would change without actually updating them."""
    return draft_feedback(
        target_words=request.target_words,
        marked_words=request.marked_words,
        original_targets=request.original_targets,
    )


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=request.target_words,
        marked_words=request.marked_words,
        sentence=request.sentence,
        original_targets=request.original_targets or None,
    )
    return {"status": "ok"}


@app.get("/api/vocabulary", response_model=VocabularyResponse)
def get_vocabulary(
    sort: str = Query(default="due", pattern="^(due|familiarity|recent)$"),
) -> VocabularyResponse:
    records = list_all_words(sort=sort)
    return VocabularyResponse(
        words=[
            WordRecordOut(
                lemma=r.lemma,
                level=r.level,
                cooldown=r.cooldown,
                first_seen=_utc_iso(r.first_seen),
                last_seen=_utc_iso(r.last_seen),
                last_context=r.last_context,
                seen_count=r.seen_count,
            )
            for r in records
        ],
        total=len(records),
    )


@app.delete("/api/vocabulary")
def delete_vocabulary() -> dict[str, int]:
    count = clear_all_words()
    return {"deleted": count}


class WordRecordUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    level: int | None = None
    cooldown: int | None = None


@app.patch("/api/vocabulary/{lemma}", response_model=WordRecordOut)
def patch_vocabulary_word(lemma: str, body: WordRecordUpdate) -> WordRecordOut:
    record = update_word_record(lemma, level=body.level, cooldown=body.cooldown)
    if record is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return WordRecordOut(
        lemma=record.lemma,
        level=record.level,
        cooldown=record.cooldown,
        firstSeen=_utc_iso(record.first_seen),
        lastSeen=_utc_iso(record.last_seen),
        lastContext=record.last_context,
        seenCount=record.seen_count,
    )


@app.delete("/api/vocabulary/{lemma}")
def delete_vocabulary_word(lemma: str) -> dict[str, bool]:
    deleted = delete_word_record(lemma)
    if not deleted:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"deleted": True}


@app.get("/api/vocabulary/export")
def export_vocabulary() -> StreamingResponse:
    """Export the vocabulary as a CSV file."""
    records = list_all_words()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "lemma",
            "level",
            "cooldown",
            "first_seen",
            "last_seen",
            "last_context",
            "seen_count",
        ]
    )
    for r in records:
        writer.writerow(
            [
                r.lemma,
                r.level,
                r.cooldown,
                r.first_seen.isoformat() if r.first_seen else "",
                r.last_seen.isoformat() if r.last_seen else "",
                r.last_context or "",
                r.seen_count,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=openvoca-vocabulary.csv"},
    )


class VocabularyImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@app.post("/api/vocabulary/import")
async def import_vocabulary_endpoint(
    file: UploadFile = File(...),
    mode: str = Form(default="skip"),
) -> VocabularyImportResponse:
    """Import vocabulary from a CSV file.

    mode: "skip" (default) keeps existing records; "overwrite" replaces them.
    """
    if mode not in ("skip", "overwrite"):
        raise HTTPException(
            status_code=422, detail="mode must be 'skip' or 'overwrite'"
        )

    _MAX_BYTES = 1 * 1024 * 1024  # 1 MB
    content = await file.read(_MAX_BYTES + 1)
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 1 MB)")

    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded")

    try:
        rows = list(csv.DictReader(io.StringIO(text_content)))
    except csv.Error as exc:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {exc}")

    result = import_vocabulary(rows, mode=mode)  # type: ignore[arg-type]
    return VocabularyImportResponse(
        imported=result.imported,
        skipped=result.skipped,
        errors=result.errors[:20],
    )


# --- Dictionary ---


@app.get("/api/dictionary/{word}")
def get_definition(word: str) -> dict:
    """Look up a word in the built-in dictionary."""
    entry = dict_lookup(word)
    if entry is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return {
        "word": entry.word,
        "phonetic": entry.phonetic,
        "definition": entry.definition,
        "translation": entry.translation,
        "pos": entry.pos,
        "tag": entry.tag,
        "exchange": entry.exchange,
    }


# --- TTS (Text-to-Speech via Edge TTS) ---

_DEFAULT_VOICE = "en-US-EmmaMultilingualNeural"
_MAX_TTS_LENGTH = 2000


@app.get("/api/tts")
async def get_tts(
    text: str = Query(min_length=1, max_length=_MAX_TTS_LENGTH),
    voice: str = Query(default=_DEFAULT_VOICE, max_length=100),
) -> StreamingResponse:
    """Stream MP3 audio for the given text using Edge TTS."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice)

    async def audio_stream():  # noqa: ANN202
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception:  # noqa: BLE001
            # Edge TTS unavailable — yield nothing so the client gets
            # an empty / truncated response and can fall back to browser TTS.
            return

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "inline",
        },
    )


@app.get("/api/tts/voices")
async def get_tts_voices(
    locale: str = Query(default="en", max_length=20),
) -> list[dict[str, str]]:
    """Return available TTS voices filtered by locale prefix."""
    import edge_tts

    all_voices = await edge_tts.list_voices()
    return [
        {
            "name": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
            "friendlyName": v["FriendlyName"],
        }
        for v in all_voices
        if v["Locale"].startswith(locale)
    ]


# --- Settings ---


class SettingValueBody(BaseModel):
    value: str = Field(min_length=1)


def _public_settings(namespace: str, settings: dict[str, str]) -> dict[str, str]:
    """Remove values that are served only by their dedicated endpoint.

    The provider API key and custom headers are served by /api/provider; the
    generic settings read must not carry them, so local caches and exports
    contain no trace of either.
    """
    if namespace != PROVIDER_NAMESPACE:
        return settings
    hidden = {"apiKey", "headers"}
    return {k: v for k, v in settings.items() if k not in hidden}


def _reject_protected_namespace(namespace: str) -> None:
    """Block generic writes to namespaces that have a dedicated write path."""
    if namespace in PROTECTED_NAMESPACES:
        raise HTTPException(
            status_code=403,
            detail=f"The '{namespace}' namespace is managed through /api/provider.",
        )


@app.get("/api/settings")
def get_settings_all() -> dict[str, dict[str, str]]:
    return {
        namespace: _public_settings(namespace, values)
        for namespace, values in get_all_settings().items()
    }


@app.get("/api/settings/{namespace}")
def get_settings_namespace(namespace: str) -> dict[str, str]:
    return _public_settings(namespace, get_namespace(namespace))


@app.put("/api/settings/{namespace}/{key}")
def put_setting(namespace: str, key: str, body: SettingValueBody) -> dict[str, str]:
    _reject_protected_namespace(namespace)
    upsert_setting(namespace, key, body.value)
    return {"status": "ok"}


@app.put("/api/settings/{namespace}")
def put_settings_namespace(namespace: str, settings: dict[str, str]) -> dict[str, str]:
    _reject_protected_namespace(namespace)
    upsert_namespace(namespace, settings)
    return {"status": "ok"}


@app.delete("/api/settings")
def delete_all_settings() -> dict[str, int]:
    count = clear_all_settings()
    return {"deleted": count}


# --- Frontend SPA (must be last) ---

if _frontend_dist.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_frontend_dist / "assets"),
        name="static-assets",
    )

    @app.get("/", include_in_schema=False)
    async def serve_root() -> FileResponse:
        return FileResponse(_frontend_dist / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa_fallback(path: str) -> FileResponse:
        # Serve real files (e.g. favicon.svg) from dist root before SPA fallback
        candidate = _frontend_dist / path
        if candidate.is_file() and _frontend_dist in candidate.resolve().parents:
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
