from __future__ import annotations

import json
import os
from typing import Any

from providers.base import ModelResponse, ToolCall


def normalize_tool_call(name: str, args: dict[str, Any], tools: list[dict[str, Any]] | None) -> tuple[str, dict[str, Any]]:
    """Recover an explicit declared action when a gateway puts prose in function.name."""
    declared = {
        item.get("function", {}).get("name")
        for item in (tools or [])
        if item.get("function", {}).get("name")
    }
    if name not in declared and args.get("action") in declared:
        repaired = dict(args)
        normalized_name = str(repaired.pop("action"))
        return normalized_name, repaired
    if name not in declared and args.get("action") == "stop" and "?" in name:
        # Some tool-capable models encode a clarification as a prose function name
        # plus action=stop. Convert that non-side-effecting pause into clarify.
        return "clarify", {"question": name, "response_type": "text"}
    return name, args


class OpenAIProvider:
    """OpenAI Chat Completions provider with normalized tool_calls output."""

    def __init__(
        self,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
        api_key_default: str | None = None,
        http_client: Any | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.api_key_default = api_key_default
        self.base_url = base_url
        self.default_model = default_model
        self.http_client = http_client

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install live provider dependency first: pip install openai") from exc

        api_key = os.getenv(self.api_key_env) or self.api_key_default
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {self.api_key_env}")

        client = OpenAI(api_key=api_key, base_url=self.base_url, http_client=self.http_client)
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        resp = client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        calls: list[ToolCall] = []
        for call in msg.tool_calls or []:
            raw_args = call.function.arguments or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                # Small models often emit malformed JSON. Keep the call so eval grades it
                # as a wrong-argument failure instead of hiding it as provider_error.
                args = {"_invalid_json_arguments": raw_args}
            if not isinstance(args, dict):
                args = {"_invalid_json_arguments": raw_args}
            name, args = normalize_tool_call(call.function.name, args, tools)
            calls.append(ToolCall(name=name, args=args))
        return ModelResponse(text=msg.content, tool_calls=calls, raw=resp)
