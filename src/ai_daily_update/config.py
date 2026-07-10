from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


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

    @property
    def timezone(self) -> str:
        return self.app.get("timezone", "Asia/Shanghai")

    @property
    def markdown_root(self) -> Path:
        return self.root / self.app.get("storage", {}).get("markdown_root", "notes")

    @property
    def sqlite_path(self) -> Path:
        return self.root / self.app.get("storage", {}).get("sqlite_path", "data/kb.sqlite")

    @property
    def manual_urls_path(self) -> Path:
        input_file = (
            self.sources.get("sources", {})
            .get("manual", {})
            .get("input_file", "data/manual_urls.txt")
        )
        return self.root / input_file

    @property
    def review_statuses(self) -> list[str]:
        return self.app.get("review", {}).get(
            "statuses", ["needs-review", "accepted", "later", "rejected"]
        )

    @property
    def max_cards(self) -> int:
        return int(self.app.get("daily", {}).get("max_cards", 5))


def load_settings(root: Path | None = None) -> Settings:
    base = root or Path.cwd()
    load_dotenv(base / ".env")
    config_dir = base / "config"
    return Settings(
        root=base,
        app=load_yaml(config_dir / "app.yaml"),
        topics=load_yaml(config_dir / "topics.yaml"),
        sources=load_yaml(config_dir / "sources.yaml"),
        scoring=load_yaml(config_dir / "scoring.yaml"),
        prompts=load_yaml(config_dir / "prompts.yaml"),
    )
