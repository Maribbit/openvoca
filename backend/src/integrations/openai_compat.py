import json
from collections.abc import AsyncGenerator

import httpx


class OpenAICompatibleClient:
    """LLM client for any OpenAI-compatible chat completions API.

    Works with OpenRouter, Groq, Together.ai, SiliconFlow, DeepSeek,
    and any service that implements POST /v1/chat/completions.

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
        self.base_url = base_url.rstrip("/")
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
            "/v1/chat/completions",
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
            "/v1/chat/completions",
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
