def test_lists_changes(fn):
    f = fn("diff_state_snapshots")
    a = {"tracks": {"1": {"volume": 0.8, "mute": False}}, "tempo": 140.0}
    b = {"tracks": {"1": {"volume": 0.5, "mute": False}, "2": {"volume": 0.1}}, "tempo": 140.0}
    assert f(a, b).value == [
        {"path": "tracks.1.volume", "before": 0.8, "after": 0.5},
        {"path": "tracks.2.volume", "before": None, "after": 0.1}]


def test_equal_snapshots_have_no_changes(fn):
    f = fn("diff_state_snapshots")
    s = {"a": {"b": 1.0}, "c": "x"}
    assert f(s, {"a": {"b": 1.0000000001}, "c": "x"}).value == [] and f({}, {}).value == []
