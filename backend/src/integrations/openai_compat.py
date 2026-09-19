import json
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
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.model = model
        self.api_key = api_key
        self.extra_headers = dict(extra_headers or {})
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

    async def generate_completion(self, prompt: str) -> str:
        headers = self._build_headers()

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        response = await self._client.post(
            ENDPOINT_PATH,
            json=payload,
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

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        async with self._client.stream(
            "POST",
            ENDPOINT_PATH,
            json=payload,
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
