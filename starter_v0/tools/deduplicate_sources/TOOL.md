---
name: deduplicate_sources
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, input_count, item_count, duplicates_removed]
side_effect: false
requires_confirmation: false
---

# Deduplicate research sources

Use when the user provides source objects and asks to remove duplicate URLs, or when combining already-fetched results before formatting a digest. This tool does not search, fetch, judge source credibility, or send content.

`items` is a list of objects with an absolute HTTP(S) `url`; title, summary and other metadata are optional. Empty lists return zero counts. Missing/wrong input or malformed URLs return an error dict, not an exception.

The first item for each URL wins, preserving order and metadata. Scheme/host casing and fragment differences are ignored. HTTP and HTTPS, paths, trailing slashes and query strings remain distinct; no tracking parameters are removed. URLs with credentials are rejected. No network or file access is performed, and caller input is not mutated.
