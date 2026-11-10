"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
hn_tool = TOOL_FUNCTIONS["hn_search"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(question="Bạn muốn xem tài khoản nào?", response_type="choice", options=["sama", "elonmusk"])
    assert result["options"] == ["sama", "elonmusk"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a", "section": "A"},
        {"title": "b", "section": "B"},
        {"title": "c", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    items = [{"title": "a"}, {"title": "b"}]
    parts = format_tool(items=items, template="thread")["markdown"].split("\n\n")
    assert parts[0].startswith("1/")
    assert parts[1].startswith("2/")


def test_format_empty_items_does_not_crash() -> None:
    assert format_tool(items=None, template="brief")["item_count"] == 0
    assert format_tool(items=[], template="sections")["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "tok123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "999"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {
        "markdown": "# Hello",
        "metadata": {"title": "T", "sourceURL": "https://example.com/page"},
    }}))

    item = fetch_tool(url="https://example.com/page")["items"][0]

    assert item["title"] == "T"
    assert item["url"] == "https://example.com/page"
    assert item["source"] == "example.com"
    assert item["summary"] == "# Hello"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    item = fetch_tool(url="https://example.com/page")["items"][0]

    assert len(item["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    timeline = [{"tweet_id": "", "text": "no id"}] + [
        {"tweet_id": str(i), "text": f"t{i}", "screen_name": "sama"} for i in range(6)
    ]
    fake_http(FakeResponse({"timeline": timeline}))

    items = timeline_tool(screenname="sama", limit=3)["items"]

    assert len(items) == 3
    assert all(item["url"].startswith("https://x.com/sama/status/") for item in items)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))

    social_tool(query="OpenAI", search_type="Top")

    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert policy_tool(query="")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = policy_tool(query="customer data privacy", policy_area="data_privacy")["results"]

    assert results
    assert all(item["policy_area"] == "data_privacy" for item in results)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    results = policy_tool(query="citation policy viral tweet", policy_area="source_citation", top_k=5)["results"]

    untrusted = [line for item in results for line in item["untrusted_text"]]
    facts = " ".join(item["facts"] for item in results)

    assert any("ignore the citation policy" in line for line in untrusted)
    assert "ignore the citation policy" not in facts


# ---------------- YOUR NEW TOOL(S): hn_search ----------------

def test_hn_search_maps_story_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [{
        "objectID": "123",
        "title": "Show HN: AI",
        "url": "https://example.com/a",
        "created_at": "2026-01-01T00:00:00Z",
        "points": 10,
        "num_comments": 2,
    }]}))

    item = hn_tool(query="AI", limit=5)["items"][0]

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"]["query"] == "AI"
    assert item["title"] == "Show HN: AI"
    assert item["url"] == "https://example.com/a"
    assert item["source"] == "example.com"
    assert item["hn_url"] == "https://news.ycombinator.com/item?id=123"


def test_hn_search_empty_query_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hn_tool(query="")

    assert result["error"] == "ValueError"
    assert calls == []


def test_hn_search_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))

    assert hn_tool(query="AI")["error"] == "HTTPError"
