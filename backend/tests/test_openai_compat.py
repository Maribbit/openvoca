import json

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


# Covers: AC-GEN-003-09
@pytest.mark.anyio
async def test_configured_body_fields_are_sent_with_the_request() -> None:
    """Fields the application does not understand travel through unchanged."""
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.read().decode("utf-8")))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="m",
        extra_body={"reasoning_effort": "none"},
        transport=httpx.MockTransport(handler),
    )
    try:
        assert await client_obj.generate_completion("hi") == "ok"
    finally:
        await client_obj.aclose()

    assert seen[0]["reasoning_effort"] == "none"
    # The fields the application owns are still there.
    assert seen[0]["model"] == "m"
    assert seen[0]["stream"] is False
    assert seen[0]["messages"][0]["content"] == "hi"


# Covers: AC-GEN-003-09
@pytest.mark.anyio
async def test_streaming_sends_the_same_configured_body_fields() -> None:
    """Both paths share one payload builder, so they cannot diverge.

    A field reaching only the blocking request would look like a provider that
    ignores the setting at random, since generation normally streams.
    """
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.read().decode("utf-8")))
        body = b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\ndata: [DONE]\n\n'
        return httpx.Response(
            status_code=200,
            content=body,
            headers={"content-type": "text/event-stream"},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="m",
        extra_body={"thinking": {"type": "disabled"}},
        transport=httpx.MockTransport(handler),
    )
    try:
        _ = [chunk async for chunk in client_obj.generate_completion_stream("hi")]
    finally:
        await client_obj.aclose()

    assert seen[0]["thinking"] == {"type": "disabled"}
    assert seen[0]["stream"] is True


# Covers: AC-GEN-003-11
@pytest.mark.anyio
async def test_body_field_types_and_nesting_survive_the_request() -> None:
    """Each provider expects its own shape, so nothing may be coerced.

    A boolean sent as "false" or a nested object flattened to a string would be
    accepted by some providers and rejected by others, which is the kind of
    difference that looks like a model problem rather than a transport one.
    """
    configured = {
        "reasoning_effort": "none",
        "enable_thinking": False,
        "thinking": {"type": "disabled"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.read().decode("utf-8")))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="m",
        extra_body=configured,
        transport=httpx.MockTransport(handler),
    )
    try:
        await client_obj.generate_completion("hi")
    finally:
        await client_obj.aclose()

    for name, value in configured.items():
        assert seen[0][name] == value
        assert type(seen[0][name]) is type(value)


# Covers: AC-GEN-003-10
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("reserved", "value"),
    [("model", "other"), ("messages", []), ("stream", True)],
)
async def test_reserved_fields_are_ignored_by_the_client(
    reserved: str, value: object
) -> None:
    """Defence in depth for values that bypassed validation.

    The write path rejects these, but a hand-edited database or an imported
    settings file never went through it. Silently not applying the field keeps
    the request valid; applying it would replace the prompt or desynchronise the
    parser from the stream.
    """
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.read().decode("utf-8")))
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    client_obj = OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="m",
        extra_body={reserved: value},
        transport=httpx.MockTransport(handler),
    )
    try:
        await client_obj.generate_completion("hi")
    finally:
        await client_obj.aclose()

    sent = seen[0]
    if reserved == "model":
        assert sent["model"] == "m"
    elif reserved == "messages":
        assert sent["messages"][0]["content"] == "hi"
    else:
        assert sent["stream"] is False


# --- Probe: the diagnostic used by the connection test ---


def _probe_client(handler, **kwargs) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        base_url="https://api.example.com",
        model="m",
        api_key="sk-secret-value",
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_reports_the_url_and_body_it_sent() -> None:
    """A configured field can only be confirmed from the outgoing request.

    The stored value proves nothing: what matters is whether it reached the
    provider, and that is what this shows.
    """
    client_obj = _probe_client(
        lambda request: httpx.Response(
            status_code=200, json={"choices": [{"message": {"content": "ok"}}]}
        ),
        extra_body={"thinking": {"type": False}},
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert result["ok"] is True
    assert result["status"] == 200
    assert result["url"] == "https://api.example.com/chat/completions"
    request = result["request"]
    assert request["thinking"] == {"type": False}
    assert request["stream"] is False
    assert isinstance(result["elapsedMs"], int)


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_never_reports_the_authorization_header() -> None:
    """The diagnostic must not become a way for a credential to escape.

    Headers are the one part of the request that carries the key, and the
    interface has no use for them: the URL and the body answer every question a
    connection test is asked.
    """
    client_obj = _probe_client(
        lambda request: httpx.Response(status_code=200, json={"choices": []})
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert "sk-secret-value" not in json.dumps(result)
    assert "Authorization" not in json.dumps(result)
    assert "headers" not in result


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_returns_the_error_body_instead_of_raising() -> None:
    """The rejection reason is the whole value of testing a bad configuration.

    generate_completion raises here, which would discard the one thing that says
    what the provider disliked -- and a field a provider refuses is exactly the
    case a connection test is used to discover.
    """
    client_obj = _probe_client(
        lambda request: httpx.Response(
            status_code=400,
            json={"error": {"message": 'unknown field "thinking"'}},
        )
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert result["ok"] is False
    assert result["status"] == 400
    assert result["error"] == "HTTP 400"
    # The raw body is passed through as the provider wrote it, so quotes inside
    # JSON strings stay escaped. Shown as-is rather than pretty-printed: a
    # diagnostic that reformats can hide the thing being diagnosed.
    assert "unknown field" in result["response"]
    assert "thinking" in result["response"]


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_reports_a_connection_failure_as_a_result() -> None:
    """Nothing came back, which is itself the finding."""

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client_obj = _probe_client(refuse)
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert result["ok"] is False
    assert result["status"] is None
    assert "ConnectError" in result["error"]


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_extracts_nested_token_counts() -> None:
    """Reasoning tokens are the only evidence that thinking actually stopped.

    They are not part of the visible reply, so a diagnostic that showed only the
    content could not answer the question it is most often run to answer.
    """
    client_obj = _probe_client(
        lambda request: httpx.Response(
            status_code=200,
            json={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 40,
                    "completion_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert result["usage"]["completion_tokens_details"]["reasoning_tokens"] == 0


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_reports_absent_usage_as_absent() -> None:
    """A provider that reports nothing must not be shown as reporting zero."""
    client_obj = _probe_client(
        lambda request: httpx.Response(
            status_code=200, json={"choices": [{"message": {"content": "ok"}}]}
        )
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert result["usage"] is None


# Covers: AC-SET-005-11
@pytest.mark.anyio
async def test_probe_truncates_an_enormous_body() -> None:
    """A provider stack trace must not be able to fill the interface."""
    client_obj = _probe_client(
        lambda request: httpx.Response(status_code=500, text="x" * 20000)
    )
    try:
        result = await client_obj.probe()
    finally:
        await client_obj.aclose()

    assert len(result["response"]) < 20000
    assert result["response"].endswith("... (truncated)")


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
