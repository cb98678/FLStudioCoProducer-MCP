def test_joins(fn):
    f = fn("join_frames")
    assert f([[1, 2], [3], []]).value == [1, 2, 3]
    assert f([]).value == []


def test_rejects_bad_input(fn):
    f = fn("join_frames")
    assert f([[1], 2]).error.code == "E_ARG"
    assert f("x").error.code == "E_ARG"
