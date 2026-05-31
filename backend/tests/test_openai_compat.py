import httpx
import pytest

from src.integrations.openai_compat import OpenAICompatibleClient
from src.integrations.provider import LLMProvider


@pytest.mark.anyio
# Covers: AC-GEN-003-01
async def test_openai_compatible_client_returns_sentence() -> None:
    """The OpenAI-compatible client should extract text from chat completions."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
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
