from __future__ import annotations

import os
from typing import Any

from providers.base import ModelResponse
from providers.openai_provider import OpenAIProvider


class XkiroProvider(OpenAIProvider):
    """xKiro Chat Completions with an explicitly configured model."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="XKIRO_API_KEY",
            base_url=os.getenv("XKIRO_BASE_URL") or "https://api.xkiro.com/v1",
            default_model=os.getenv("XKIRO_MODEL", "").strip(),
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        if not (model or self.default_model):
            raise RuntimeError("Set XKIRO_MODEL in .env or pass --model with the full vendor/model ID from xKiro.")
        return super().complete(
            messages, tools, model=model, temperature=temperature, tool_choice=tool_choice
        )
