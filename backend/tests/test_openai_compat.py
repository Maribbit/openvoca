import httpx
import pytest

from src.integrations.openai_compat import OpenAICompatibleClient, normalize_base_url
from src.integrations.provider import LLMProvider


# Covers: AC-GEN-003-01
@pytest.mark.anyio
async def test_openai_compatible_client_returns_sentence() -> None:
    """The OpenAI-compatible client should extract text from chat completions."""

    def handler(request: httpx.Request) -> httpx.Response:
        # The base URL carries no version prefix here, so the endpoint is reached
        # directly under it.
        assert request.url.path == "/chat/completions"
        import json

        payload = json.loads(request.read().decode("utf-8"))
        assert payload["model"] == "deepseek-chat"
        assert payload["messages"][0]["role"] == "user"
        assert "lantern" in payload["messages"][0]["content"]
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "A lantern flickered softly."}}]},
        )

    transport = httpx.MockTransport(handler)
    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="deepseek-chat",
        api_key="sk-test",
        transport=transport,
    )

    sentence = await client_obj.generate_completion("Use these words: lantern.")
    assert sentence == "A lantern flickered softly."


# Covers: AC-GEN-003-01, AC-GEN-003-08
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        # The version segment comes from the configuration. Hard-coding an
        # absolute /v1/chat/completions turned this into /v1/v1/chat/completions,
        # so the most natural OpenAI value was the one that could not work.
        ("https://api.openai.com/v1", "https://api.openai.com/v1/chat/completions"),
        ("http://localhost:11434/v1", "http://localhost:11434/v1/chat/completions"),
        # DeepSeek documents a base URL with no version segment and serves the
        # endpoint directly beneath it.
        ("https://api.deepseek.com", "https://api.deepseek.com/chat/completions"),
        # A version segment that is not v1, and a path that has to survive.
        (
            "https://open.bigmodel.cn/api/paas/v4",
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        ),
        # Providers that accept /v1 keep working when it is written out.
        ("https://api.deepseek.com/v1", "https://api.deepseek.com/v1/chat/completions"),
        # A full endpoint URL is accepted rather than doubled.
        (
            "https://api.deepseek.com/chat/completions",
            "https://api.deepseek.com/chat/completions",
        ),
        # Trailing slashes are tolerated.
        ("https://example.com/", "https://example.com/chat/completions"),
    ],
)
async def test_request_url_comes_from_the_configured_base_url(
    configured: str, expected: str
) -> None:
    """Every shape a provider documents must reach its own endpoint.

    The request goes through a real transport rather than being inspected with
    build_request, so the assertion covers the URL that is actually requested.
    """
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url=configured,
        model="m",
        transport=httpx.MockTransport(handler),
    )
    try:
        assert await client_obj.generate_completion("hi") == "ok"
    finally:
        await client_obj.aclose()

    assert seen == [expected]


# Covers: AC-GEN-003-05, AC-GEN-003-08
@pytest.mark.anyio
async def test_streaming_requests_the_same_url_as_the_blocking_call() -> None:
    """Both paths are built from one constant, so they cannot drift apart."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        body = b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\ndata: [DONE]\n\n'
        return httpx.Response(
            status_code=200,
            content=body,
            headers={"content-type": "text/event-stream"},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.openai.com/v1",
        model="m",
        transport=httpx.MockTransport(handler),
    )
    try:
        chunks = [chunk async for chunk in client_obj.generate_completion_stream("hi")]
    finally:
        await client_obj.aclose()

    assert chunks == ["hi"]
    assert seen == ["https://api.openai.com/v1/chat/completions"]


# Covers: AC-GEN-003-08
@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("https://api.deepseek.com", "https://api.deepseek.com"),
        ("https://api.deepseek.com/", "https://api.deepseek.com"),
        ("https://api.deepseek.com/chat/completions", "https://api.deepseek.com"),
        ("https://api.deepseek.com/chat/completions/", "https://api.deepseek.com"),
        ("  https://api.deepseek.com  ", "https://api.deepseek.com"),
        # Only the exact suffix is removed, so a path that merely resembles the
        # endpoint keeps its meaning.
        ("https://gateway.example.com/chat", "https://gateway.example.com/chat"),
        ("https://api.openai.com/v1/chat/completions", "https://api.openai.com/v1"),
    ],
)
def test_base_url_normalization(given: str, expected: str) -> None:
    assert normalize_base_url(given) == expected


# Covers: AC-GEN-003-08
def test_normalization_cannot_change_a_url_that_already_works() -> None:
    """Removing the endpoint path is idempotent, and re-appending it is exact.

    That is what makes accepting both forms safe: a value that produced the right
    request before normalization produces the same request after it.
    """
    for given in (
        "https://api.deepseek.com/chat/completions",
        "https://api.openai.com/v1/chat/completions",
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    ):
        once = normalize_base_url(given)
        assert normalize_base_url(once) == once
        assert f"{once}/chat/completions" == given


@pytest.mark.anyio
# Covers: AC-GEN-003-02
async def test_openai_compatible_client_rejects_empty_response() -> None:
    """Should raise ValueError when the API returns no choices."""

    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code=200, json={"choices": []}),
    )
    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        transport=transport,
    )

    with pytest.raises(ValueError, match="choices"):
        await client_obj.generate_completion("test prompt")


# Covers: AC-GEN-003-03
def test_openai_compatible_client_satisfies_provider_protocol() -> None:
    """OpenAICompatibleClient must be a structural subtype of LLMProvider."""
    assert isinstance(
        OpenAICompatibleClient(
            base_url="https://api.example.com",
            model="test",
            api_key="sk-test",
        ),
        LLMProvider,
    )


@pytest.mark.anyio
# Covers: AC-GEN-003-03
async def test_openai_compatible_client_reuses_connection() -> None:
    """The persistent client should handle multiple calls without recreating."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": f"Response {call_count}."}}]},
        )

    transport = httpx.MockTransport(handler)
    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        transport=transport,
    )

    result1 = await client_obj.generate_completion("First call")
    result2 = await client_obj.generate_completion("Second call")

    assert result1 == "Response 1."
    assert result2 == "Response 2."
    assert call_count == 2
    await client_obj.aclose()


@pytest.mark.anyio
# Covers: AC-GEN-003-04
async def test_openai_compatible_client_aclose() -> None:
    """aclose() should cleanly shut down the HTTP client."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        ),
    )
    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        transport=transport,
    )
    await client_obj.aclose()


@pytest.mark.anyio
# Covers: AC-GEN-003-06
async def test_stream_ignores_chunks_without_choices() -> None:
    """Usage-only tail chunks (empty choices) must not abort the stream.

    Providers such as OpenCode Zen emit a final chunk carrying usage with an
    empty choices array before [DONE]; indexing it blindly raises IndexError.
    """
    sse_body = (
        'data: {"choices":[{"delta":{"content":"Rain"}}]}\n\n'
        'data: {"choices":[],"usage":{"total_tokens":10}}\n\n'
        'data: {"choices":[{"delta":{"content":" falls"}}]}\n\n'
        'data: {"choices":[],"cost":"0"}\n\n'
        "data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=sse_body.encode(),
            headers={"content-type": "text/event-stream"},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        transport=httpx.MockTransport(handler),
    )

    chunks = [c async for c in client_obj.generate_completion_stream("prompt")]
    await client_obj.aclose()

    assert chunks == ["Rain", " falls"]


@pytest.mark.anyio
# Covers: AC-GEN-003-06
async def test_stream_ignores_reasoning_only_deltas() -> None:
    """Reasoning traces must not leak into the generated text."""
    sse_body = (
        'data: {"choices":[{"delta":{"reasoning_content":"Let me think"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        "data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=sse_body.encode(),
            headers={"content-type": "text/event-stream"},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        transport=httpx.MockTransport(handler),
    )

    chunks = [c async for c in client_obj.generate_completion_stream("prompt")]
    await client_obj.aclose()

    assert chunks == ["Hello"]


@pytest.mark.anyio
# Covers: AC-GEN-003-05
async def test_openai_compatible_client_streams_chunks() -> None:
    """generate_completion_stream should yield content deltas from SSE chunks."""

    sse_body = (
        'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"."}}]}\n\n'
        "data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=sse_body.encode(),
            headers={"content-type": "text/event-stream"},
        )

    transport = httpx.MockTransport(handler)
    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        transport=transport,
    )

    chunks: list[str] = []
    async for chunk in client_obj.generate_completion_stream("test prompt"):
        chunks.append(chunk)

    assert chunks == ["Hello", " world", "."]
    await client_obj.aclose()


@pytest.mark.anyio
# Covers: AC-GEN-004-01
async def test_custom_headers_applied_to_generate_and_stream() -> None:
    """Extra headers must reach both the non-streaming and streaming request."""
    seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.headers))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    async def stream_handler(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.headers))
        return httpx.Response(
            status_code=200,
            content=b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\ndata: [DONE]\n\n',
            headers={"content-type": "text/event-stream"},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        extra_headers={"x-opencode-session": "session-abc"},
        transport=httpx.MockTransport(handler),
    )
    await client_obj.generate_completion("hello")
    await client_obj.aclose()

    stream_client = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        extra_headers={"x-opencode-session": "session-abc"},
        transport=httpx.MockTransport(stream_handler),
    )
    async for _ in stream_client.generate_completion_stream("hello"):
        pass
    await stream_client.aclose()

    assert len(seen) == 2
    for headers in seen:
        assert headers.get("x-opencode-session") == "session-abc"


@pytest.mark.anyio
# Covers: AC-GEN-004-02
async def test_custom_headers_override_builtin_headers() -> None:
    """An explicitly configured header must win over the built-in default."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.headers))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-ignored",
        extra_headers={"Authorization": "Custom scheme-value"},
        transport=httpx.MockTransport(handler),
    )
    await client_obj.generate_completion("hello")
    await client_obj.aclose()

    assert captured.get("authorization") == "Custom scheme-value"


@pytest.mark.anyio
# Covers: AC-GEN-004-01
async def test_absent_custom_headers_leave_requests_unchanged() -> None:
    """Without extra headers the request keeps the built-in header set."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.headers))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="test",
        api_key="sk-test",
        transport=httpx.MockTransport(handler),
    )
    await client_obj.generate_completion("hello")
    await client_obj.aclose()

    assert captured.get("authorization") == "Bearer sk-test"
    assert "x-opencode-session" not in captured
