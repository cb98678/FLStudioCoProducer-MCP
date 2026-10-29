from hypothesis import given, strategies as st


def test_known_vectors(fn):
    f = fn("split_frames")
    assert f([0, 1, 2, 3, 4], 2).value == [[0, 1], [2, 3], [4]]
    assert f([], 5).value == []
    assert f([1, 2], 5).value == [[1, 2]]
    assert f([1, 2, 3, 4], 4).value == [[1, 2, 3, 4]]


def test_rejects_bad_input(fn):
    f = fn("split_frames")
    assert f([1, 2, 3], 0).error.code == "E_ARG"
    assert f("abc", 2).error.code == "E_ARG"


@given(st.lists(st.integers(0, 127), max_size=200), st.integers(1, 50))
def test_join_restores_input(fn, data, n):
    parts = fn("split_frames")(data, n).value
    assert fn("join_frames")(parts).value == data
