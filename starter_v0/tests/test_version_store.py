import json

import pytest

import version_store as store


@pytest.fixture
def snapshots(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "runs")
    folder = store.version_path("v0")
    folder.mkdir(parents=True)
    (folder / "system_prompt.md").write_text("Baseline", encoding="utf-8")
    (folder / "tools.yaml").write_text('''tools:
  - name: clarify
    description: Ask for input
    parameters:
      type: object
      properties:
        question: {type: string}
      required: [question]
''', encoding="utf-8")
    return store.get_version("v0")


def test_create_snapshot_preserves_parent_and_rejects_overwrite(snapshots):
    result = store.create_version("v1", "v0", "New prompt", snapshots["tools_yaml"], "Test hypothesis")
    assert result["parent"] == "v0"
    assert store.get_version("v0")["prompt"] == "Baseline"
    assert result["tools_hash"] == snapshots["tools_hash"]
    with pytest.raises(ValueError, match="Version"):
        store.create_version("v1", "v0", "Changed", snapshots["tools_yaml"], "Other")
    assert store.get_version("v1")["prompt"] == "New prompt"


@pytest.mark.parametrize("name", ["../outside", "/outside", "v1/child", "v1\\child", "", "a" * 49])
def test_unsafe_version_name_cannot_write_outside_versions(snapshots, name):
    with pytest.raises(ValueError):
        store.create_version(name, "v0", "Prompt", snapshots["tools_yaml"], "Hypothesis")
    assert store.list_versions() == ["v0"]


@pytest.mark.parametrize("text", ["[", "tools: []", "tools: [unknown]",
    "tools: [{name: unknown}]", "tools: [{name: clarify, description: test, parameters: {type: array}}]"])
def test_invalid_schema_is_rejected_before_writing(snapshots, text):
    with pytest.raises(ValueError):
        store.create_version("bad", "v0", "Prompt", text, "Hypothesis")
    assert not store.version_path("bad").exists()


def test_scores_require_matching_name_and_both_hashes(snapshots):
    store.RUNS_DIR.mkdir()
    run = {"version": "v0", "prompt_hash": snapshots["prompt_hash"],
           "tools_hash": "stale", "suite": "base", "summary": {"case_accuracy": 1}}
    path = store.RUNS_DIR / "run.json"
    path.write_text(json.dumps(run), encoding="utf-8")
    assert store.matching_runs(snapshots) == []
    assert store.version_rows()[0]["Độ chính xác"] == "—"
    run["tools_hash"] = snapshots["tools_hash"]
    path.write_text(json.dumps(run), encoding="utf-8")
    assert len(store.matching_runs(snapshots)) == 1
    assert store.version_rows()[0]["Độ chính xác"] == "100%"
