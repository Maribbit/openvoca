import json
import time
from collections.abc import AsyncGenerator

import httpx

# Requested of whatever base URL is configured. Relative on purpose: httpx
# concatenates a base URL with the request path rather than resolving the path
# against it, so an absolute path here would append a second version segment to
# a base URL that already carries one -- base https://api.openai.com/v1 with a
# "/v1/chat/completions" path becomes /v1/v1/chat/completions.
#
# The version segment belongs to the provider, not to this client. OpenAI uses
# /v1, Ollama exposes its compatibility API under /v1, Zhipu uses /api/paas/v4,
# and DeepSeek serves /chat/completions with no version at all. Appending only
# the endpoint path lets one field describe all of them.
ENDPOINT_PATH = "chat/completions"

# Fields the client sets itself, and whose values the application depends on.
# A configured field that overwrote one of these would break the request in a
# way that looks like a provider problem: "messages" would replace the prompt,
# "model" would route to a different model than the one on screen, and "stream"
# would desynchronise the streaming and non-streaming paths from the parser
# waiting for them. Configured fields are rejected at write time and skipped
# here, so a value that bypassed that gate -- an edited database, a settings
# file from elsewhere -- degrades to "not applied" rather than to a broken
# request.
RESERVED_PAYLOAD_KEYS = frozenset({"model", "messages", "stream"})

# Asked of the model when checking a configuration. Short and unambiguous, so
# the reply is a signal about the connection rather than about the prompt.
PROBE_PROMPT = "Reply with the single word: ok"

# A diagnostic exists to be read, so it must not be able to fill the screen with
# a provider's stack trace. Long enough for a real error body, short enough to
# stay reviewable.
_MAX_PROBE_BODY = 4000


def _extract_usage(response: httpx.Response) -> dict[str, object] | None:
    """Return a provider's token accounting, when it reports any.

    Pulled out of the body rather than left for the reader because these counts
    are often the answer. A reasoning count above zero means the model thought,
    even when the configuration was meant to stop it -- and that is not
    something the visible reply can show, since reasoning is not returned as
    content.
    """
    try:
        data = response.json()
    except ValueError:
        return None
    usage = data.get("usage") if isinstance(data, dict) else None
    return usage if isinstance(usage, dict) else None


def normalize_base_url(base_url: str) -> str:
    """Return *base_url* without the endpoint path, if it was included.

    One field accepts either a base URL or a full endpoint URL, which is what
    provider documentation puts side by side: DeepSeek's guide shows a
    ``base_url`` of ``https://api.deepseek.com`` and a ``curl`` line ending in
    the request path. Stripping the suffix is idempotent, because appending
    ENDPOINT_PATH reproduces exactly the value that was supplied, so this cannot
    alter a URL that was already correct.
    """
    trimmed = base_url.strip().rstrip("/")
    suffix = f"/{ENDPOINT_PATH}"
    if trimmed.endswith(suffix):
        return trimmed[: -len(suffix)]
    return trimmed


class OpenAICompatibleClient:
    """LLM client for any OpenAI-compatible chat completions API.

    Works with OpenRouter, Groq, Together.ai, SiliconFlow, DeepSeek, Zhipu,
    Ollama, and any service that implements POST /chat/completions under some
    base URL. The base URL carries whatever version prefix the provider uses.

    Uses a persistent ``httpx.AsyncClient`` to reuse TCP connections
    across requests, avoiding repeated DNS lookups and TLS handshakes.
    Call ``aclose()`` when the client is no longer needed.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, object] | None = None,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.model = model
        self.api_key = api_key
        self.extra_headers = dict(extra_headers or {})
        self.extra_body = {
            key: value
            for key, value in (extra_body or {}).items()
            if key not in RESERVED_PAYLOAD_KEYS
        }
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    def _build_headers(self) -> dict[str, str]:
        """Merge built-in headers with configured custom headers.

        Custom headers win on conflict so non-Bearer auth schemes and
        provider-specific routing headers can be expressed in configuration.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    async def probe(self, prompt: str = PROBE_PROMPT) -> dict[str, object]:
        """Send one minimal request and report what was sent and what came back.

        Unlike :meth:`generate_completion` this does not raise when the provider
        rejects the request. A provider's error body is usually the only thing
        that says why, and a diagnostic that discards it is not worth running.

        Streaming stays off so the reply arrives as a single JSON document that
        can be shown as it is. Headers are deliberately absent from the result:
        they carry the Authorization value, and a diagnostic is not a reason to
        copy a credential into the interface or into a log.
        """
        payload = self._build_payload(prompt, stream=False)
        url = str(self._client.build_request("POST", ENDPOINT_PATH).url)
        started = time.monotonic()

        try:
            response = await self._client.post(
                ENDPOINT_PATH, json=payload, headers=self._build_headers()
            )
        except httpx.HTTPError as exc:
            # Failing to connect is a result in its own right: it points at the
            # endpoint or the network, which no response body could report.
            return {
                "ok": False,
                "url": url,
                "request": payload,
                "status": None,
                "response": "",
                "elapsedMs": int((time.monotonic() - started) * 1000),
                "error": f"{type(exc).__name__}: {exc}",
                "usage": None,
            }

        body = response.text
        return {
            "ok": response.is_success,
            "url": url,
            "request": payload,
            "status": response.status_code,
            "response": body[:_MAX_PROBE_BODY]
            + ("\n... (truncated)" if len(body) > _MAX_PROBE_BODY else ""),
            "elapsedMs": int((time.monotonic() - started) * 1000),
            "error": "" if response.is_success else f"HTTP {response.status_code}",
            "usage": _extract_usage(response),
        }

    def _build_payload(self, prompt: str, *, stream: bool) -> dict[str, object]:
        """Build the request body, then layer configured fields over it.

        One builder for both paths, so a configured field cannot reach the
        streaming request and miss the blocking one. The version-specific
        settings providers use to control reasoning differ in field name, value
        type and nesting -- from ``reasoning_effort: "none"`` through
        ``thinking: {"type": "disabled"}`` to
        ``chat_template_kwargs: {"enable_thinking": false}`` -- so there is no
        common shape to normalise onto. Passing fields through verbatim covers
        all of them, and any provider that adds another, without this client
        needing to know which provider it is talking to.
        """
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }
        payload.update(self.extra_body)
        return payload

    async def generate_completion(self, prompt: str) -> str:
        headers = self._build_headers()

        response = await self._client.post(
            ENDPOINT_PATH,
            json=self._build_payload(prompt, stream=False),
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError(
                "OpenAI-compatible response has no choices in the payload."
            )

        content = choices[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "OpenAI-compatible response has empty content in the payload."
            )

        return " ".join(content.split())

    async def generate_completion_stream(
        self, prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from the chat completions API.

        Yields individual content deltas as they arrive.
        """
        headers = self._build_headers()

        async with self._client.stream(
            "POST",
            ENDPOINT_PATH,
            json=self._build_payload(prompt, stream=True),
            headers=headers,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[len("data: ") :]
                if data_str.strip() == "[DONE]":
                    break
                chunk = json.loads(data_str)
                # Some providers emit usage-only chunks with an empty choices
                # array; those carry no text and must not break the stream.
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {}).get("content") or ""
                if delta:
                    yield delta
