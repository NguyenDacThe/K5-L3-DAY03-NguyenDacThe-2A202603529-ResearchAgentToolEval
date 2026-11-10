import io

from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall


def test_tool_logging_works_with_ascii_windows_console(monkeypatch):
    class FakeProvider:
        def complete(self, *args, **kwargs):
            return ModelResponse(tool_calls=[ToolCall("clarify", {
                "question": "Bạn muốn xem tài khoản nào?", "response_type": "text"})])

    output = io.BytesIO()
    console = io.TextIOWrapper(output, encoding="ascii")
    monkeypatch.setattr("sys.stdout", console)
    result = run_model_tool_loop(provider=FakeProvider(), messages=[], tools=[], model=None, max_tool_rounds=1)
    console.flush()
    assert result["status"] == "waiting_for_user"
    assert result["assistant_text"] == "Bạn muốn xem tài khoản nào?"
    assert b"TOOL" in output.getvalue()
