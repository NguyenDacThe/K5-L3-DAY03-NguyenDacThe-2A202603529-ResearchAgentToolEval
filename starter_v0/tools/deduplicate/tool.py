from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tools._shared import err


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Each nonempty URL must be an absolute HTTP(S) URL without credentials")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def deduplicate_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first occurrence of each URL; never merge URL-less records."""
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list of objects")
        unique, seen = [], set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Every item must be an object")
            url = item.get("url")
            if url is not None and not isinstance(url, str):
                raise ValueError("url must be a string or null")
            if url and url.strip():
                key = _canonical_url(url)
                if key in seen:
                    continue
                seen.add(key)
            unique.append(dict(item))
        return {"tool": "deduplicate", "items": unique, "item_count": len(unique),
                "removed_count": len(items) - len(unique)}
    except Exception as exc:
        return err("deduplicate", exc)
