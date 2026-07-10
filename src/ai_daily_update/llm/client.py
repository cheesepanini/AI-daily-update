from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class OpenAIClient:
    model: str
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str | None = None

    @property
    def available(self) -> bool:
        return bool(os.getenv(self.api_key_env) and self.model)

    def generate_card_content(self, prompt: str) -> str | None:
        if not self.available:
            return None
        try:
            from openai import OpenAI
        except ImportError:
            return None
        client = OpenAI(api_key=os.getenv(self.api_key_env), base_url=self.base_url or None)
        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
            )
            return extract_text(response)
        except Exception as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return extract_text(response)


def extract_text(response: Any) -> str:
    if isinstance(response, str):
        if response.lstrip().startswith("event:"):
            raise RuntimeError(
                "LLM provider returned an event stream instead of plain response text. "
                "Check OPENAI_BASE_URL; AI-Daily-Update expects an OpenAI-compatible /v1 API endpoint."
            )
        return response
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text
    output = getattr(response, "output", None) or []
    parts: list[str] = []
    for item in output:
        content = getattr(item, "content", None) or []
        for content_item in content:
            text = getattr(content_item, "text", None)
            if text:
                parts.append(text)
    if parts:
        return "\n".join(parts)
    choices = getattr(response, "choices", None) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None)
        if content:
            parts.append(content)
    return "\n".join(parts)
