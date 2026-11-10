import json

import pytest

import feedback_store as store


def test_feedback_keeps_version_hashes_and_hides_api_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "FEEDBACK_DIR", tmp_path)
    monkeypatch.setenv("TEST_API_KEY", "private-test-key")
    version = {"version": "v3", "prompt_hash": "p", "tools_hash": "t"}
    path = store.save_feedback(version, "Enter private-test-key", "Ask", "Sent")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["prompt_hash"] == "p"
    assert record["source"] == "manual_feedback"
    assert record["status"] == "open"
    assert "private-test-key" not in path.read_text(encoding="utf-8")
    assert len(store.read_feedback("v3")) == 1
    assert store.read_feedback("v2") == []


def test_empty_feedback_is_not_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "FEEDBACK_DIR", tmp_path)
    with pytest.raises(ValueError):
        store.save_feedback({"version":"v3"}, "", "Expected", "Actual")
    assert not list(tmp_path.glob("*.json"))
