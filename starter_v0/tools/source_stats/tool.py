from __future__ import annotations

from collections import Counter
from typing import Any
from urllib.parse import urlparse


def summarize_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Count provided research items by source/domain without network access."""
    if not isinstance(items, list):
        return {"tool": "summarize_sources", "item_count": 0, "source_counts": {}, "error": "items must be a list"}
    counts: Counter[str] = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        url = str(item.get("url") or "").strip()
        key = source or (urlparse(url).hostname or "unknown")
        counts[key] += 1
    return {"tool": "summarize_sources", "item_count": sum(counts.values()), "source_counts": dict(counts)}
