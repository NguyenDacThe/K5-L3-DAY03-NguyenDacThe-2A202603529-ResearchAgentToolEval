from pathlib import Path

from run_eval import load_cases


def test_group_contains_five_single_and_five_multiturn_cases():
    path = Path(__file__).resolve().parents[1] / "data/eval_group.json"
    cases = load_cases(path, "B")
    assert len(cases) == 10
    assert sum("turns" in c for c in cases) == 5
    assert len({c["id"] for c in cases}) == 10
    assert all(c.get("metadata", {}).get("what_it_tests") for c in cases)
    assert all(c.get("query") or len(c.get("turns", [])) >= 3 for c in cases)


def test_v2_changes_only_telegram_confirmation_rule():
    from version_store import get_version
    old, new = get_version("v1"), get_version("v2")
    assert old["tools_hash"] == new["tools_hash"]
    before, after = old["prompt"].split("\n\n"), new["prompt"].split("\n\n")
    assert len(before) == len(after)
    changed = [(a, b) for a, b in zip(before, after) if a != b]
    assert len(changed) == 1
    assert 'response_type="yes_no"' in changed[0][1]
