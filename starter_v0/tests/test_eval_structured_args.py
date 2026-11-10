from run_eval import compare_subset


def test_source_object_lists_compare_without_sorting_dicts_directly():
    expected = {"items": [{"url": "https://a.example"}, {"url": "https://b.example"}]}
    actual = {"items": list(reversed(expected["items"]))}
    assert compare_subset(expected, actual) == (True, [], 1, 1)


def test_source_object_list_mismatch_is_an_argument_failure():
    expected = {"items": [{"url": "https://a.example"}, {"url": "https://b.example"}]}
    actual = {"items": [{"url": "https://a.example"}]}
    passed, failures, correct, total = compare_subset(expected, actual)
    assert not passed
    assert len(failures) == 1
    assert (correct, total) == (0, 1)
