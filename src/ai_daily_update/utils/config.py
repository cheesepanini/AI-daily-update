from __future__ import annotations

from typing import Any


def section(mapping: dict[str, Any] | None, key: str) -> dict[str, Any]:
    """Read a nested config section that is expected to be a dict.

    YAML represents an empty section (e.g. `sources:` with nothing under
    it, because every sub-key got commented out) as `None`, not a missing
    key. `mapping.get(key, {})` only supplies the `{}` default when `key`
    is absent - if it's present with a `None` value, that None is returned
    as-is and the next chained `.get(...)` call blows up with
    AttributeError. This coerces both "missing" and "present but empty"
    into an empty dict.
    """
    mapping = mapping or {}
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def list_section(mapping: dict[str, Any] | None, key: str) -> list[Any]:
    """Same as `section`, for config values expected to be a list."""
    mapping = mapping or {}
    value = mapping.get(key)
    return value if isinstance(value, list) else []
