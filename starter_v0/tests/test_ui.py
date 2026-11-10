"""Offline checks for multi-turn UI behavior; no real API calls or transcripts."""
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

import chat
import providers
from providers.base import ModelResponse, ToolCall

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_ui_clarification_history_transcript_and_reset(monkeypatch):
    requests, saved = [], []

    class FakeProvider:
        default_model = "offline-test"

        def complete(self, messages, tools, **kwargs):
            requests.append(deepcopy(messages))
            assert "send" not in {t["function"]["name"] for t in tools}
            if len(requests) == 1:
                return ModelResponse(tool_calls=[ToolCall("clarify", {
                    "question": "Bạn muốn xem tài khoản nào?", "response_type": "text"})])
            return ModelResponse(text="Đã nhận tài khoản @sama.")

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    monkeypatch.setattr(chat, "write_transcript", lambda path, value: saved.append(deepcopy(value)))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    app.chat_input[0].set_value("Lấy 3 tweet mới nhất").run()
    assert not app.exception
    assert saved[-1]["turns"][0]["status"] == "waiting_for_user"
    app.chat_input[0].set_value("@sama").run()
    assert not app.exception
    assert any(m["content"] == "Lấy 3 tweet mới nhất" for m in requests[-1])
    assert any(m["content"] == "Bạn muốn xem tài khoản nào?" for m in requests[-1])
    assert len(saved[-1]["turns"]) == 2
    app.selectbox[0].set_value("v0").run()
    assert len(app.chat_message) == 0
    assert app.session_state["transcript"]["version"] == "v0"
    app.button[0].click().run()
    assert len(app.chat_message) == 0


def test_ui_blocks_undeclared_send_and_hides_provider_errors(monkeypatch):
    saved = []

    class FakeProvider:
        default_model = "offline-test"

        def complete(self, *args, **kwargs):
            return ModelResponse(tool_calls=[ToolCall("send", {"text": "blocked", "confirmed": True})])

    def forbidden(*args, **kwargs):
        raise AssertionError("UI must never execute send")

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    monkeypatch.setitem(chat.TOOL_FUNCTIONS, "send", forbidden)
    monkeypatch.setattr(chat, "write_transcript", lambda path, value: saved.append(deepcopy(value)))
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Gửi tin").run()
    assert not app.exception
    assert saved[-1]["turns"][0]["status"] == "provider_error"
    assert saved[-1]["turns"][0]["tool_events"] == []


def test_ui_provider_failure_does_not_save_raw_error(monkeypatch):
    saved = []

    class FakeProvider:
        default_model = "offline-test"

        def complete(self, *args, **kwargs):
            raise RuntimeError("Request failed with secret=FAKE_SECRET_FOR_TEST")

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    monkeypatch.setattr(chat, "write_transcript", lambda path, value: saved.append(deepcopy(value)))
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Tìm tin AI").run()
    assert not app.exception
    assert "FAKE_SECRET_FOR_TEST" not in str(saved)
    assert "FAKE_SECRET_FOR_TEST" not in str([m.value for m in app.markdown])
    assert saved[-1]["turns"][0]["error_type"] == "RuntimeError"
