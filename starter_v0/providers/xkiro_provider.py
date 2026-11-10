from __future__ import annotations

import os

import httpx

from providers.openai_provider import OpenAIProvider


class XKiroProvider(OpenAIProvider):
    """xKiro's OpenAI-compatible Chat Completions gateway."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="XKIRO_API_KEY",
            base_url=os.getenv("XKIRO_BASE_URL") or "https://api.xkiro.com/v1",
            default_model=os.getenv("XKIRO_MODEL", "openai/gpt-5.6-sol"),
            # The inherited shell proxy points at a local closed port (127.0.0.1:9).
            # Use direct TLS for the xKiro API instead of inheriting that stale proxy.
            http_client=httpx.Client(trust_env=False, timeout=60.0),
        )
