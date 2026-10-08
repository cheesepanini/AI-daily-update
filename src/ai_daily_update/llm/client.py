from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class OpenAIClient:
    model: str
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str | None = None
    reasoning_effort: str | None = None

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
        reasoning = {"reasoning": {"effort": self.reasoning_effort}} if self.reasoning_effort else {}
        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                **reasoning,
            )
            return extract_text(response)
        except Exception as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **({"reasoning_effort": self.reasoning_effort} if self.reasoning_effort else {}),
            )
            return extract_text(response)

    def generate_learning_reply(self, instructions: str, prompt: str) -> str | None:
        if not self.available:
            return None
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv(self.api_key_env), base_url=self.base_url or None, timeout=25.0)
        reasoning = {"reasoning": {"effort": self.reasoning_effort}} if self.reasoning_effort else {}
        try:
            response = client.responses.create(
                model=self.model,
                instructions=instructions,
                input=prompt,
                max_output_tokens=900,
                **reasoning,
            )
        except Exception as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": instructions}, {"role": "user", "content": prompt}],
                max_tokens=900,
                **({"reasoning_effort": self.reasoning_effort} if self.reasoning_effort else {}),
            )
        return extract_text(response)


def extract_text(response: Any) -> str:
    if isinstance(response, str):
        if response.lstrip().startswith("event:"):
            raise RuntimeError(
                "LLM provider returned an event stream instead of plain response text. "
                "Check llm.base_url; AI-Daily-Update expects an OpenAI-compatible API endpoint."
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
