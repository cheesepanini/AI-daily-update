from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values, load_dotenv

from ai_daily_update.utils.config import section


ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _expand_env(data)


@dataclass(frozen=True)
class Settings:
    root: Path
    app: dict[str, Any]
    topics: dict[str, Any]
    sources: dict[str, Any]
    scoring: dict[str, Any]
    prompts: dict[str, Any]
    concepts: dict[str, Any] = field(default_factory=dict)

    @property
    def timezone(self) -> str:
        return self.app.get("timezone", "Asia/Shanghai")

    @property
    def markdown_root(self) -> Path:
        return self.root / section(self.app, "storage").get("markdown_root", "notes")

    @property
    def sqlite_path(self) -> Path:
        return self.root / section(self.app, "storage").get("sqlite_path", "data/kb.sqlite")

    @property
    def manual_urls_path(self) -> Path:
        input_file = section(section(self.sources, "sources"), "manual").get(
            "input_file", "data/manual_urls.txt"
        )
        return self.root / input_file

    @property
    def review_statuses(self) -> list[str]:
        return section(self.app, "review").get(
            "statuses", ["needs-review", "accepted", "later", "rejected"]
        )

    @property
    def max_cards(self) -> int:
        return int(section(self.app, "daily").get("max_cards", 5))


def load_settings(root: Path | None = None) -> Settings:
    base = root or Path.cwd()
    load_dotenv(base / ".env")
    local_model_env = dotenv_values(base / ".env")
    for name in ("AI_DAILY_LLM_MODEL", "DEEPSEEK_API_KEY"):
        if local_model_env.get(name):
            os.environ[name] = local_model_env[name]
    config_dir = base / "config"
    return Settings(
        root=base,
        app=load_yaml(config_dir / "app.yaml"),
        topics=load_yaml(config_dir / "topics.yaml"),
        sources=load_yaml(config_dir / "sources.yaml"),
        scoring=load_yaml(config_dir / "scoring.yaml"),
        prompts=load_yaml(config_dir / "prompts.yaml"),
        concepts=load_yaml(config_dir / "foundational_concepts.yaml"),
    )
