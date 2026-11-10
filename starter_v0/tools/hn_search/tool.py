from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

# Hacker News search via the public Algolia API (no API key required).
_ENDPOINTS = {
    "relevance": "https://hn.algolia.com/api/v1/search",
    "date": "https://hn.algolia.com/api/v1/search_by_date",
}


def _hit_item(hit: dict[str, Any]) -> dict[str, Any]:
    hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
    url = hit.get("url") or hn_url
    title = hit.get("title") or hit.get("story_title") or ""
    return {
        "title": title,
        "url": url,
        "source": domain(url) or "news.ycombinator.com",
        "summary": (hit.get("story_text") or hit.get("comment_text") or title or "").strip(),
        "date": hit.get("created_at"),
        "points": hit.get("points"),
        "comments": hit.get("num_comments"),
        "hn_url": hn_url,
    }


def hn_search(query: str = "", limit: int = 5, sort: str = "relevance") -> dict[str, Any]:
    try:
        if not (query or "").strip():
            raise ValueError("query is required")
        endpoint = _ENDPOINTS.get((sort or "relevance").strip().lower(), _ENDPOINTS["relevance"])
        capped = min(max(int(limit or 5), 1), 50)
        response = requests.get(
            endpoint,
            params={"query": query, "tags": "story", "hitsPerPage": capped},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
        return {"tool": "hn_search", "query": query, "sort": sort, "items": [_hit_item(hit) for hit in hits[:capped]]}
    except Exception as exc:
        return err("hn_search", exc)
