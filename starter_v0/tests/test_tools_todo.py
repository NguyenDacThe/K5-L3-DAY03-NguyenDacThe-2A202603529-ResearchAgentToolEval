"""Completed offline tool tests and the team's deduplicate regression tests."""
from copy import deepcopy
from importlib import import_module
import pytest
from conftest import FakeResponse
from tools import TOOL_FUNCTIONS as T


def test_clarify_choice_returns_options_and_awaits_user():
    result = T['clarify']('Chon nguon?', response_type='choice', options=['Web', 'X'])
    assert result['options'] == ['Web', 'X']
    assert result['awaiting_user'] is True


def test_format_sections_groups_items_by_section():
    items = [{'title': str(i), 'section': s} for i, s in enumerate(['A', 'B', 'A'])]
    result = T['format'](items=items, template='sections')
    assert result['markdown'].count('## A') == 1
    assert result['markdown'].count('## B') == 1
    assert result['item_count'] == 3


def test_format_thread_numbers_items():
    result = T['format'](items=[{'title': 'One'}, {'title': 'Two'}], template='thread')
    assert result['markdown'].startswith('1/ One')
    assert '\n\n2/ Two' in result['markdown']


@pytest.mark.parametrize('items', [None, []])
def test_format_empty_items_does_not_crash(items):
    result = T['format'](items=items)
    assert result['item_count'] == 0
    assert result['markdown'] == ''


def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'fake-channel')
    calls = fake_http(FakeResponse({'ok': True}))
    assert T['send'](text='Digest', confirmed=True)['status'] == 'sent'
    assert len(calls) == 1
    assert calls[0]['method'] == 'POST'
    assert calls[0]['url'] == 'https://api.telegram.org/botfake-token/sendMessage'
    assert calls[0]['json'] == {'chat_id': 'fake-channel', 'text': 'Digest', 'parse_mode': 'Markdown'}


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http):
    calls = fake_http(FakeResponse({'ok': True}))
    result = T['send'](text='Digest', confirmed=True)
    assert result['error'] == 'RuntimeError'
    assert 'TELEGRAM' in result['message']
    assert calls == []


def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http):
    monkeypatch.setenv('TAVILY_API_KEY', 'fake-key')
    calls = fake_http(FakeResponse({'results': []}))
    result = T['lookup'](query='robotics', timeframe=None)
    assert len(calls) == 1
    assert calls[0]['json']['query'] == 'robotics'
    assert 'time_range' not in calls[0]['json']
    assert result['items'] == []


def test_fetch_maps_firecrawl_response(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake-key')
    calls = fake_http(FakeResponse({'data': {'markdown': 'Content', 'metadata': {
        'title': 'T', 'sourceURL': 'https://example.com/article'}}}))
    result = T['fetch'](url='https://example.com/article')
    assert calls[0]['url'] == 'https://api.firecrawl.dev/v1/scrape'
    assert calls[0]['json'] == {'url': 'https://example.com/article', 'formats': ['markdown']}
    assert result['items'] == [{'title': 'T', 'url': 'https://example.com/article',
        'source': 'example.com', 'summary': 'Content'}]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake-key')
    fake_http(FakeResponse({'data': {'markdown': 'x' * 4001}}))
    assert T['fetch'](url='https://example.com')['items'][0]['summary'] == 'x' * 4000


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http):
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake-key')
    raw = [{'text': 'no id'}] + [{'tweet_id': str(i), 'screen_name': 'sama', 'text': f'post {i}'} for i in range(6)]
    calls = fake_http(FakeResponse({'timeline': raw}))
    result = T['timeline'](screenname='sama', limit=3)
    assert calls[0]['params'] == {'screenname': 'sama'}
    assert calls[0]['url'].endswith('/timeline.php')
    assert [i['url'] for i in result['items']] == [f'https://x.com/sama/status/{i}' for i in range(3)]


@pytest.mark.parametrize('search_type', ['Top', 'Latest'])
def test_social_search_passes_search_type(monkeypatch, fake_http, search_type):
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake-key')
    calls = fake_http(FakeResponse({'tweets': [{'id': '7', 'author': {'screen_name': 'tester'}, 'text': 'AI'}]}))
    result = T['social_search'](query='AI', search_type=search_type)
    assert calls[0]['params'] == {'query': 'AI', 'search_type': search_type}
    assert calls[0]['url'].endswith('/search.php')
    assert result['items'][0]['url'] == 'https://x.com/tester/status/7'


def test_policy_empty_query_returns_no_results():
    assert T['policy'](query='  ')['results'] == []


def test_policy_area_filter_only_returns_that_area():
    result = T['policy'](query='API keys privacy', policy_area='data_privacy')
    assert result['results']
    assert all(r['policy_area'] == 'data_privacy' for r in result['results'])


def test_policy_instruction_like_lines_go_to_untrusted_text():
    result = T['policy'](query='citation', policy_area='source_citation', top_k=20)
    suspicious = [r for r in result['results'] if r['untrusted_text']]
    assert suspicious
    assert any('ignore' in line.lower() for r in suspicious for line in r['untrusted_text'])
    assert all('Assistant: ignore' not in r['facts'] for r in result['results'])


def test_deduplicate_keeps_first_item_and_does_not_mutate_input():
    items = [{'url': 'https://EXAMPLE.com/a#first', 'title': 'first'},
             {'url': 'https://example.com/a#second', 'title': 'second'},
             {'url': 'https://example.com/b', 'title': 'third'}]
    original = deepcopy(items)
    result = T['deduplicate'](items=items)
    assert result['items'] == [items[0], items[2]]
    assert result['item_count'] == 2
    assert result['removed_count'] == 1
    assert items == original


@pytest.mark.parametrize('items', [None, 'bad', [42], [{'url': 7}], [{'url': 'ftp://example.com/a'}], [{'url': 'not-a-url'}]])
def test_deduplicate_bad_input_returns_error_dict(items):
    result = T['deduplicate'](items=items)
    assert result['error'] == 'ValueError'
    assert 'message' in result


def test_deduplicate_processing_failure_returns_error_dict(monkeypatch):
    def fail(url):
        raise OSError('simulated processing failure')
    monkeypatch.setattr(import_module('tools.deduplicate.tool'), '_canonical_url', fail)
    result = T['deduplicate'](items=[{'url': 'https://example.com'}])
    assert result['error'] == 'OSError'
    assert result['message'] == 'simulated processing failure'


def test_deduplicate_keeps_items_without_urls_and_distinct_queries():
    items = [{'title': 'same'}, {'title': 'same'}, {'url': ''},
             {'url': 'https://example.com?a=1'}, {'url': 'https://example.com?a=2'}]
    result = T['deduplicate'](items=items)
    assert result['items'] == items
    assert result['removed_count'] == 0
    assert T['deduplicate'](items=[])['item_count'] == 0
