try:
    import httpx2 as httpx
except ImportError:
    import httpx
import openai

from ui_errors import describe_error


def test_connection_failure_is_not_reported_as_invalid_key():
    exc = openai.APIConnectionError(request=httpx.Request("POST", "https://example.test"))
    result = describe_error(exc)
    assert result["error_type"] == "APIConnectionError"
    assert result["http_status"] is None
    assert "Không kết nối" in result["assistant_text"]
    assert "chưa cho biết" in result["assistant_text"]


def test_credit_error_preserves_status_without_raw_body():
    response = httpx.Response(402, request=httpx.Request("POST", "https://example.test"))
    exc = openai.APIStatusError("secret=FAKE_SECRET", response=response, body={"secret": "FAKE_SECRET"})
    result = describe_error(exc)
    assert result["http_status"] == 402
    assert "thiếu credit" in result["assistant_text"]
    assert "FAKE_SECRET" not in str(result)
