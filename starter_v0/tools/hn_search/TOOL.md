---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News (Algolia) public API
requires_env: []
inputs: [query, limit, sort]
outputs: [tool, query, sort, items]
side_effect: false
---
# hn_search

Search Hacker News stories by keyword through the public Algolia API. No API key needed.

- `query`: keyword or topic (e.g. "AI", "OpenAI").
- `limit`: number of results, clamped to 1..50 (default 5).
- `sort`: `relevance` (default) or `date`.

Each item has `title, url, source, summary, date, points, comments, hn_url`.
Empty query returns an error dict; HTTP failures return an error dict instead of raising.
