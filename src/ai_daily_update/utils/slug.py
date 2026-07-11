from __future__ import annotations

import hashlib
import re
import unicodedata


def slugify(value: str, fallback: str = "item") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    if slug:
        return slug
    stripped = value.strip()
    if not stripped:
        return fallback
    # Non-ASCII input (e.g. Chinese titles) collapses to an empty slug above,
    # which would make every distinct non-ASCII title collide on the same
    # fallback id. Use a short content hash instead so different titles stay
    # distinct while the same title still maps to the same slug.
    digest = hashlib.sha1(stripped.encode("utf-8")).hexdigest()[:12]
    return f"{fallback}-{digest}"
