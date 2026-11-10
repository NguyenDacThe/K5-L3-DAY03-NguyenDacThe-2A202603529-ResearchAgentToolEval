"""UI smoke checks without provider or tool HTTP requests."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

import chat
import providers
from providers.base import ModelResponse, ToolCall
from tools import TOOL_FUNCTIONS

APP = Path(__file__).resolve().parents[1] / "app.py"


def fake_provider(monkeypatch, responses):
    complete = Mock(side_effect=responses)
    monkeypatch.setattr(providers, "make_provider", lambda _: SimpleNamespace(
        default_model="offline-test", complete=complete,
    ))
    save = Mock()
    monkeypatch.setattr(chat, "write_transcript", save)
    return complete, save


def test_initial_render_and_eval_filter():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert not app.error
    assert len(app.tabs) == 5
    assert "v1-tool" not in app.selectbox(key="selected_version").options
    if app.toggle:
        app.toggle[0].set_value(False).run()
        assert not app.exception
        assert len(app.dataframe[0].value) >= 1


def test_clarification_then_answer_and_reset(monkeypatch):
    complete, save = fake_provider(monkeypatch, [
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Bạn muốn xem tài khoản nào?", "response_type": "text"})]),
        ModelResponse(text="Đã nhận tài khoản sama."),
    ])
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Lấy tweet mới nhất").run()
    assert not app.exception
    assert app.session_state["turns"][0]["status"] == "waiting_for_user"
    app.chat_input[0].set_value("sama").run()
    assert not app.exception
    messages = complete.call_args.args[0]
    assert any(m["content"] == "Lấy tweet mới nhất" for m in messages)
    assert save.call_count == 2
    assert len(app.session_state["history"]) == 4
    app.button(key="reset_chat").click().run()
    assert app.session_state["history"] == []
    assert app.session_state["turns"] == []


def test_invented_send_is_blocked_before_execution(monkeypatch):
    complete, _ = fake_provider(monkeypatch, [
        ModelResponse(tool_calls=[ToolCall("send", {"text": "test", "confirmed": True})]),
    ])
    send = Mock()
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", send)
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Gửi Telegram").run()
    assert not app.exception
    send.assert_not_called()
    assert app.session_state["turns"][0]["status"] == "provider_error"
    assert all(t["function"]["name"] != "send" for t in complete.call_args.args[1])


def test_switching_version_uses_snapshot_and_clears_chat(monkeypatch):
    complete, save = fake_provider(monkeypatch, [ModelResponse(text="Test response")])
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key="selected_version").select("v1").run()
    app.chat_input[0].set_value("Test").run()
    from version_store import get_version
    assert complete.call_args.args[0][0]["content"].startswith(get_version("v1")["prompt"])
    assert "deduplicate_sources" in [t["function"]["name"] for t in complete.call_args.args[1]]
    assert save.call_args.args[1]["version"] == "v1"
    app.selectbox(key="selected_version").select("v0").run()
    assert not app.exception
    assert app.session_state["history"] == []
    assert app.session_state["turns"] == []
    assert app.metric[0].value == "70%"


def test_create_version_form_saves_snapshot(tmp_path, monkeypatch):
    import shutil
    import version_store
    snapshots = tmp_path / "versions"
    for name in ["v0", "v1"]:
        shutil.copytree(version_store.VERSIONS_DIR / name, snapshots / name)
    monkeypatch.setattr(version_store, "VERSIONS_DIR", snapshots)
    monkeypatch.setattr(version_store, "RUNS_DIR", tmp_path / "runs")
    app = AppTest.from_file(str(APP)).run()
    app.text_input(key="new_version_name").set_value("v2-test")
    app.text_area(key="new_version_hypothesis").set_value("Test a single prompt change")
    app.text_area(key="draft_prompt").set_value("Ask for confirmation before sending.")
    next(b for b in app.button if b.label == "Tạo version").click().run()
    assert not app.exception
    assert not app.error
    saved = version_store.get_version("v2-test")
    assert saved["parent"] == "v1"
    assert saved["prompt"] == "Ask for confirmation before sending."
    assert "v2-test" in app.selectbox(key="selected_version").options
    app.selectbox(key="selected_version").select("v2-test").run()
    assert not app.error
    assert not app.metric  # Unmeasured versions must not inherit v1 scores.


def test_v2_is_available_and_uses_confirmation_prompt(monkeypatch):
    complete, save = fake_provider(monkeypatch, [ModelResponse(text="Draft ready")])
    app = AppTest.from_file(str(APP)).run()
    assert "v2" in app.selectbox(key="selected_version").options
    app.selectbox(key="selected_version").select("v2").run()
    app.chat_input[0].set_value("Prepare a draft").run()
    assert not app.exception
    assert 'response_type="yes_no"' in complete.call_args.args[0][0]["content"]
    assert save.call_args.args[1]["version"] == "v2"


def test_v3_is_available_and_transcript_uses_v3(monkeypatch):
    complete, save = fake_provider(monkeypatch, [ModelResponse(text="Scope refusal")])
    app = AppTest.from_file(str(APP)).run()
    assert app.selectbox(key="selected_version").value == "v3"
    app.chat_input[0].set_value("Explain your scope").run()
    assert not app.exception
    assert "single consistent routing policy" in complete.call_args.args[0][0]["content"]
    assert save.call_args.args[1]["version"] == "v3"


def test_manual_feedback_form_saves_against_selected_version(monkeypatch):
    import feedback_store
    save = Mock()
    monkeypatch.setattr(feedback_store, "save_feedback", save)
    monkeypatch.setattr(feedback_store, "read_feedback", lambda _: [])
    app = AppTest.from_file(str(APP)).run()
    app.text_area(key="feedback_steps").set_value("Use a new account")
    app.text_area(key="feedback_expected").set_value("Ask for its handle")
    app.text_area(key="feedback_actual").set_value("Used the wrong account")
    next(b for b in app.button if b.label == "Lưu phản hồi").click().run()
    assert not app.exception
    assert save.call_args.args[0]["version"] == "v3"
    assert save.call_args.args[1:] == ("Use a new account", "Ask for its handle", "Used the wrong account")
