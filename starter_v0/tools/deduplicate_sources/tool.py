from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tools._shared import err


def deduplicate_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first source for each URL, ignoring fragments and host casing."""
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list of source objects with HTTP(S) URLs")
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                raise ValueError("Every source must be an object with a string url")
            url = item["url"].strip()
            parts = urlsplit(url)
            if (parts.scheme.lower() not in {"http", "https"} or not parts.hostname
                    or parts.username is not None or parts.password is not None
                    or any(char.isspace() for char in url)):
                raise ValueError("Every url must be an absolute HTTP(S) URL without credentials")
            # Accessing .port validates malformed port numbers as well.
            _ = parts.port
            canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))
            if canonical not in seen:
                seen.add(canonical)
                unique.append(dict(item))
        return {"tool": "deduplicate_sources", "items": unique, "input_count": len(items),
                "item_count": len(unique), "duplicates_removed": len(items) - len(unique)}
    except Exception as exc:
        return err("deduplicate_sources", exc)
